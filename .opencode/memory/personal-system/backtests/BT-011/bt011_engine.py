#!/usr/bin/env python3
"""BT-011 — SELL_LADDER 16信号计票规则回归测试 (2026年日K, 200只A股)

目标: 回归 Vibe-Trading 原版后, 验证 SELL_LADDER v2.5 分级计票规则
      (EVENT×2 + TREND×1, max=14) 在 2026 行情中是否依然有效,
      并通过变体对比"定案积分的方式和算法"。

方法:
  - 200 只股票 (持仓15 + 科技主线50 + 7月大跌75 + 随机60)
  - 2026-01-05 → 2026-08-10 逐日 (最后共同交易日 8/10)
  - 每日计算 16 信号 → score_v22 → stage_v22 → 目标仓位 (T+1 生效, 无前视)
  - 变体对比: v2.5现状 / 全等权 / 含trend_neg扣分 / 只事件加权 / 阈值敏感性
  - 指标: 超额收益, 最大回撤, 7月大跌期损失, 减仓正确率

性能策略 (已 benchmark):
  - 14 个轻信号 (<10ms): 逐日重算
  - ml_strategy (1.5s/次): 每20日重训 (与生产 retrain_freq=20 一致)
  - chanlun (0.16s/次): 每5日重算
"""
from __future__ import annotations
import sys, os, json, time, warnings
from datetime import datetime
from collections import defaultdict

import numpy as np
import pandas as pd

sys.path.insert(0, '.opencode/memory/personal-system/sell-ladder')
from data_loader import load_daily
import sell_ladder as sl

warnings.filterwarnings('ignore')

BT_DIR = os.path.dirname(os.path.abspath(__file__))
POOL_FILE = os.path.join(BT_DIR, 'pool_200.json')
OUT_DIR = os.path.join(BT_DIR, 'results')
os.makedirs(OUT_DIR, exist_ok=True)

START = '2026-01-05'
END = '2026-08-10'   # 200 只全部覆盖的最后共同日

# 信号分组 (与 sell_ladder.py:1523 一致)
EVENT_SIGNALS = list(sl.EVENT_SIGNALS)
TREND_SIGNALS = list(sl.TREND_SIGNALS)
AUX = ['harmonic', 'pair_trading', 'volatility', 'factor_research', 'ad_line']

# 5 大动能结束标志依赖的信号
END_SIGNAL_KEYS = list(sl.MOMENTUM_END_SIGNALS.keys())


# ---------------------------------------------------------------- 信号序列计算
WARMUP_START = '2024-10-01'   # 预热的 16 信号所需历史起点 (ml 需 267+, 留足缓冲)


def calc_signal_series(code: str, df: pd.DataFrame) -> pd.DataFrame:
    """对单只股票计算 16 信号逐日序列。

    返回 DataFrame: index=date, columns=16 信号名 (signal ∈ {-1,0,1})。
    降频策略: ml_strategy 每20日, chanlun 每5日, 其余逐日。
    """
    df = df[df['date'] >= WARMUP_START].reset_index(drop=True)
    dates = df['date'].dt.strftime('%Y-%m-%d').values
    n = len(df)
    sig = defaultdict(lambda: pd.Series(0, index=range(n)))

    def run_at(i, name, fn):
        """在 df[:i+1] 上运行信号函数, 返回 (signal 标量, 子字段 dict)"""
        sub = df.iloc[:i + 1].reset_index(drop=True)
        try:
            r = fn(sub)
            if isinstance(r, dict):
                return int(r.get('signal', 0)), r
            return 0, {}
        except Exception:
            return 0, {}

    # 轻信号: 逐日 (同时收集 5 大动能结束标志所需的子字段)
    light = {
        'alpha_engine_v21': lambda i: run_at(i, 'a', lambda d: sl.calc_alpha_engine_v21(d, code)),
        'candlestick': lambda i: run_at(i, 'c', sl.calc_candlestick),
        'technical_basic': lambda i: run_at(i, 't', sl.calc_technical_basic),
        'ichimoku': lambda i: run_at(i, 'i', sl.calc_ichimoku),
        'smc': lambda i: run_at(i, 's', sl.calc_smc),
        'alpha_zoo': lambda i: run_at(i, 'z', sl.calc_alpha_zoo),
        'volatility': lambda i: run_at(i, 'v', sl.calc_volatility),
        'harmonic': lambda i: run_at(i, 'h', sl.calc_harmonic),
        'turnover_anomaly': lambda i: run_at(i, 'to', sl.calc_turnover_anomaly),
        'ad_line': lambda i: run_at(i, 'al', sl.calc_ad_line),
    }
    # 退化信号 (无 peer 时恒 0, 与 no_cdmo 一致)
    zero = {'factor_research', 'multi_factor', 'pair_trading', 'sector_relative'}

    # 子字段数组 (默认值与原版 .get() 一致)
    wt1_arr = np.zeros(n); adx_arr = np.full(n, 50.0); rsi_arr = np.full(n, 50.0)
    cloud_arr = np.full(n, 50.0); ret20_arr = np.zeros(n); hv_arr = np.full(n, 100.0)

    for name, fn in light.items():
        vals = []
        for i in range(n):
            s, r = fn(i)
            vals.append(s)
            if name == 'alpha_engine_v21':
                wt1_arr[i] = r.get('wt1', 0)
            elif name == 'technical_basic':
                adx_arr[i] = r.get('adx', 50); rsi_arr[i] = r.get('rsi', 50)
            elif name == 'ichimoku':
                cloud_arr[i] = r.get('above_cloud_pct', 50)
            elif name == 'alpha_zoo':
                ret20_arr[i] = r.get('ret_20d', 0)
            elif name == 'volatility':
                hv_arr[i] = r.get('hv_pct', 100)
        sig[name] = pd.Series(vals, index=range(n))

    # ml_strategy: 每 20 日重训
    ml_vals = [0] * n
    for i in range(n):
        if i % 20 == 0 or i == n - 1:
            sub = df.iloc[:i + 1].reset_index(drop=True)
            try:
                ml_vals[i] = int(sl.calc_ml_strategy(sub).get('signal', 0))
            except Exception:
                ml_vals[i] = 0
        else:
            ml_vals[i] = ml_vals[i - 1]
    sig['ml_strategy'] = pd.Series(ml_vals, index=range(n))

    # chanlun: 每 5 日重算
    cl_vals = [0] * n
    for i in range(n):
        if i % 5 == 0 or i == n - 1:
            sub = df.iloc[:i + 1].reset_index(drop=True)
            try:
                cl_vals[i] = int(sl.calc_chanlun(sub, code).get('signal', 0))
            except Exception:
                cl_vals[i] = 0
        else:
            cl_vals[i] = cl_vals[i - 1]
    sig['chanlun'] = pd.Series(cl_vals, index=range(n))

    for name in zero:
        sig[name] = pd.Series(0, index=range(n))

    # ---------------------------------------------------------------- 精确 5 大动能结束标志 (v2.2.1 check_momentum_end_signals)
    close = df['close'].values
    volume = df['volume'].values
    direction = np.zeros(n)
    direction[1:] = ((np.diff(close) > 0).astype(int) - (np.diff(close) < 0).astype(int))
    obv = np.cumsum(direction * volume)
    vol_div = np.zeros(n, dtype=bool)
    for t in range(10, n):
        obv_ref = abs(obv[t - 6]) if abs(obv[t - 6]) > 0 else 1.0
        obv_5d_slope = (obv[t] - obv[t - 6]) / obv_ref
        price_5d_high = close[t - 4:t + 1].max() >= close[t - 9:t - 4].max()
        vol_div[t] = bool(obv_5d_slope < 0 and price_5d_high)

    trend_break = (adx_arr < 25) & (cloud_arr < 0)
    momentum_reversal = (wt1_arr < -20) & (rsi_arr < 30) & (ret20_arr < -0.10)
    structure_break = (sig['smc'].values == -1) & (cloud_arr < 0)
    volatility_drop = hv_arr < 30
    end_count = (trend_break.astype(int) + momentum_reversal.astype(int) + vol_div.astype(int) +
                 structure_break.astype(int) + volatility_drop.astype(int))

    out = pd.DataFrame({k: sig[k] for k in
                        ['alpha_engine_v21', 'candlestick', 'ml_strategy', 'chanlun',
                         'technical_basic', 'ichimoku', 'smc', 'alpha_zoo',
                         'factor_research', 'multi_factor', 'volatility', 'harmonic',
                         'pair_trading', 'turnover_anomaly', 'sector_relative', 'ad_line']})
    out['end_count'] = end_count
    out['date'] = dates
    return out


# ---------------------------------------------------------------- 计票变体
def make_variants():
    """计票变体定义: (名称, 说明, 计票函数(score, max_score, ev_pos, ev_neg, tr_pos, tr_neg))"""
    def v_v25(w_event=2, w_trend=1, penalize_trend=False):
        def f(score, mscore, ev_pos, ev_neg, tr_pos, tr_neg):
            s = w_event * ev_pos + w_trend * tr_pos - w_event * ev_neg
            if penalize_trend:
                s -= w_trend * tr_neg
            return s, w_event * 3 + w_trend * 8
        return f
    return {
        'V0_v25_current': v_v25(2, 1, False),
        'V1_equal_weight': v_v25(1, 1, False),
        'V2_penalize_trend_neg': v_v25(2, 1, True),
        'V3_equal_penalize_neg': v_v25(1, 1, True),
        'V4_event_only': v_v25(2, 0, False),
    }


# ---------------------------------------------------------------- 回测主循环
def backtest_one(code: str, name: str, df: pd.DataFrame, sig: pd.DataFrame,
                 variant_fn, stage_rule: dict) -> dict:
    """单股票回测: 逐日计票 → 阶段 → 目标仓位 (T+1) → 净值 vs BH"""
    df = df.reset_index(drop=True)
    d = df['date'].dt.strftime('%Y-%m-%d').values
    close = df['close'].values

    # sig 按 date 对齐 df (warmup 裁剪后 sig 是 df 的子集, 但行序一致)
    # 只回放 2026 区间
    mask = (d >= START) & (d <= END)
    idx = np.where(mask)[0]
    if len(idx) < 20:
        return None

    # 从 sig 中按相同 date 位置取信号 (sig 与 df 行序一致)
    sig_dates = sig['date'].values
    sig_lookup = {}
    for j, sd in enumerate(sig_dates):
        sig_lookup[sd] = sig.iloc[j]
    pos_series = []       # 目标仓位 (T 日收盘决策 → T+1 生效)
    for t in idx:
        row = sig_lookup.get(d[t])
        if row is None:
            pos_series.append(1.0)
            continue
        ev_pos = ev_neg = tr_pos = tr_neg = 0
        for k in EVENT_SIGNALS:
            v = row[k]
            if v > 0: ev_pos += 1
            elif v < 0: ev_neg += 1
        for k in TREND_SIGNALS:
            v = row[k]
            if v > 0: tr_pos += 1
            elif v < 0: tr_neg += 1
        score, mscore = variant_fn(0, 0, ev_pos, ev_neg, tr_pos, tr_neg)
        # 阶段 (精确 5 大动能结束标志, 来自 check_momentum_end_signals)
        end_count = int(row['end_count'])
        st, _ = sl.stage_v22(score, mscore, end_count)
        pos_series.append(stage_rule.get(st, 1.0))

    pos = np.array(pos_series)
    # T+1 生效: 第 0 天决策从第 1 天开始
    eff_pos = np.concatenate([[1.0], pos[:-1]])

    rets = np.diff(close[idx]) / close[idx[:-1]] * eff_pos[1:]
    bh_rets = np.diff(close[idx]) / close[idx[:-1]]
    nav = np.cumprod(1 + rets)
    bh_nav = np.cumprod(1 + bh_rets)

    # 指标
    def drawdown(nav_):
        peak = np.maximum.accumulate(nav_)
        return float((nav_ / peak - 1).min())

    # 7月区间 (7/1-7/31)
    jul_mask = (d[idx] >= '2026-07-01') & (d[idx] <= '2026-07-31')
    jul_idx = np.where(jul_mask)[0]

    # 减仓正确率: 阶段2/2.5/3 决策后 5 日收益 < 0 的比例
    stage_idx = [i for i in range(1, len(idx)) if pos[i - 1] < 1.0]
    correct = 0; total = 0
    for i in stage_idx:
        if i + 5 < len(idx):
            total += 1
            fwd = (close[idx[i + 5]] / close[idx[i]] - 1)
            if fwd < 0:
                correct += 1
    acc = correct / total if total > 0 else np.nan

    return {
        'code': code, 'name': name,
        'nav_final': float(nav[-1]), 'bh_final': float(bh_nav[-1]),
        'excess': float(nav[-1] / bh_nav[-1] - 1),
        'dd': drawdown(nav), 'bh_dd': drawdown(bh_nav),
        'jul_strat': float(np.prod(1 + rets[jul_idx]) - 1) if len(jul_idx) > 1 else 0.0,
        'jul_bh': float(np.prod(1 + bh_rets[jul_idx]) - 1) if len(jul_idx) > 1 else 0.0,
        'trim_acc': acc, 'trim_n': total,
        'ann_ret_strat': float(np.prod(1 + rets) ** (252 / len(rets)) - 1) if len(rets) else 0.0,
        'ann_ret_bh': float(np.prod(1 + bh_rets) ** (252 / len(bh_rets)) - 1) if len(bh_rets) else 0.0,
    }


def _compute_one(p):
    """单只信号计算 (用于多进程)"""
    code = p['code']
    try:
        df = load_daily(code)
        if df is None or df.empty:
            return code, None
        sig = calc_signal_series(code, df)
        sig['code'] = code
        return code, sig
    except Exception as e:
        return code, None


# ---------------------------------------------------------------- 主入口
def main():
    import multiprocessing as mp
    pool = json.load(open(POOL_FILE))
    print(f'股票池: {len(pool)} 只 | 区间: {START} → {END}')
    t_all = time.time()

    # 预计算信号 (每只一次, 多进程)
    cache_file = os.path.join(OUT_DIR, 'signal_cache_v2.parquet')
    signal_cache = {}
    if os.path.exists(cache_file):
        try:
            print('加载信号缓存...')
            cache_df = pd.read_parquet(cache_file)
            for code, g in cache_df.groupby('code'):
                signal_cache[code] = g
            print(f'缓存: {len(signal_cache)} 只')
        except Exception as e:
            print(f'缓存加载失败: {e}')
            signal_cache = {}

    todo = [p for p in pool if p['code'] not in signal_cache]
    print(f'待计算信号: {len(todo)} 只')
    if todo:
        n_proc = min(8, mp.cpu_count())
        print(f'多进程: {n_proc} workers')
        with mp.Pool(n_proc) as p:
            for k, (code, sig) in enumerate(p.imap_unordered(_compute_one, todo)):
                if sig is not None:
                    signal_cache[code] = sig
                if (k + 1) % 20 == 0:
                    print(f'  信号 {k+1}/{len(todo)} ({time.time()-t_all:.0f}s)')
    # 存缓存
    try:
        all_df = pd.concat(signal_cache.values(), ignore_index=True)
        all_df.to_parquet(cache_file)
        print(f'信号缓存已保存: {len(all_df)} 行, {len(signal_cache)} 只')
    except Exception as e:
        print(f'缓存保存失败: {e}')

    # 回测所有变体
    stage_rule = {1: 1.0, 2: 0.7, 2.5: 0.8, 3: 0.2}   # 阶段→仓位 (v2.5: 2减30%, 2.5减20-40%, 3清仓80%)
    variants = make_variants()
    results = {name: [] for name in variants}

    for p in pool:
        code = p['code']
        if code not in signal_cache:
            continue
        try:
            df = load_daily(code)
            sig = signal_cache[code]
        except Exception:
            continue
        for vname, vfn in variants.items():
            r = backtest_one(code, p['name'], df, sig, vfn, stage_rule)
            if r:
                results[vname].append(r)

    # 汇总
    print('\n' + '=' * 90)
    print('BT-011 计票变体对比 (200只 × 2026-01-05→08-10)')
    print('=' * 90)
    rows = []
    for vname, rs in results.items():
        n = len(rs)
        if n == 0:
            continue
        excess = np.mean([r['excess'] for r in rs])
        win = np.mean([1 if r['excess'] > 0 else 0 for r in rs])
        dd = np.mean([r['dd'] for r in rs])
        bh_dd = np.mean([r['bh_dd'] for r in rs])
        jul_s = np.mean([r['jul_strat'] for r in rs])
        jul_b = np.mean([r['jul_bh'] for r in rs])
        trim_acc = np.nanmean([r['trim_acc'] for r in rs])
        ann_s = np.mean([r['ann_ret_strat'] for r in rs])
        ann_b = np.mean([r['ann_ret_bh'] for r in rs])
        rows.append({
            'variant': vname, 'n': n,
            'avg_excess_pct': excess * 100, 'win_rate': win * 100,
            'avg_dd_pct': dd * 100, 'bh_dd_pct': bh_dd * 100,
            'jul_strat_pct': jul_s * 100, 'jul_bh_pct': jul_b * 100,
            'trim_acc_pct': trim_acc * 100,
            'ann_ret_strat_pct': ann_s * 100, 'ann_ret_bh_pct': ann_b * 100,
        })
    res_df = pd.DataFrame(rows)
    print(res_df.to_string(index=False, float_format=lambda x: f'{x:8.2f}'))

    res_df.to_csv(os.path.join(OUT_DIR, 'variant_summary.csv'), index=False)
    # 每只股票的明细
    for vname, rs in results.items():
        pd.DataFrame(rs).to_csv(os.path.join(OUT_DIR, f'detail_{vname}.csv'), index=False)

    print(f'\n耗时: {time.time()-t_all:.0f}s')
    print(f'输出: {OUT_DIR}/')


if __name__ == '__main__':
    main()
