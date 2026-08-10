#!/usr/bin/env python3
"""
SELL_LADDER v2.0 — Walk-Forward 回测 (2026 年初科技股行情)

============================================================
目的:
  验证 sell-ladder 方法的有效性/可用性:
  1. 上涨期: 阶段 1 是否保持持有 (不误杀上涨)
  2. 见顶回撤: 阶段降级/动能结束标志是否提前预警
  3. 下跌期: 是否持续给卖出信号

方法:
  - 标的高: 6 只科技股 (tech-pool/) + 300725 药石
  - 评估点: 每周五 (walk-forward, 无未来函数)
  - 每个评估点用截至当日的全部历史数据重算 13 信号 + 5 动能结束标志 + 阶段判定
  - 对照: 信号给出后未来 5/10/20 个交易日的实际收益

用法:
  python3 backtest_seed_2026.py [--start 2026-01-01] [--weekday 4] [--out BT-XXX]

输出:
  - 每标的时间线 CSV (runs/<date>/backtest_<ticker>.csv)
  - 汇总报告 (stdout)
============================================================
"""
import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

SELL_LADDER_DIR = Path(__file__).resolve().parent
DATA_DIR = SELL_LADDER_DIR / "data"
TECH_DIR = DATA_DIR / "tech-pool"
RUNS_DIR = SELL_LADDER_DIR / "runs"

sys.path.insert(0, str(SELL_LADDER_DIR))
from sell_ladder import (check_momentum_end_signals, load_data, calc_alpha_engine_v21,
                         calc_candlestick, calc_ml_strategy, calc_chanlun,
                         calc_technical_basic, calc_ichimoku, calc_smc,
                         calc_alpha_zoo, calc_factor_research, calc_multi_factor,
                         calc_volatility, calc_harmonic, calc_pair_trading)

TECH_POOL = ['688256', '688981', '002371', '300308', '688041', '603501']
STRONG_SIGNALS = ['technical_basic', 'ichimoku', 'smc', 'alpha_zoo', 'factor_research']


def stage_of(strong_healthy: int, end_count: int) -> tuple:
    if strong_healthy >= 5 and end_count <= 1:
        return 1, '强动能期'
    elif strong_healthy >= 3 and end_count <= 2:
        return 2, '动能衰减期'
    else:
        return 3, '动能结束期'


def strong_signals_of(variant: str) -> list:
    """5 强动能信号集合 (按变体)
    - v2.0: 原始定义 (factor_research 阈值 ic>0.5, 实测不可达 → 死灯)
    - v2.1: 修复 — factor_research 移出 5 强, multi_factor 补位 (点亮率 57%)
    """
    base = ['technical_basic', 'ichimoku', 'smc', 'alpha_zoo']
    if variant == 'v2.1':
        return base + ['multi_factor']
    return base + ['factor_research']


# ============================================================
# v2.2 信号分级: 事件信号 ×2 / 趋势信号 ×1 / 辅助观察 0 票
#   - 事件信号 (明确买卖点): candlestick, chanlun, ml_strategy → 2 票
#   - 趋势信号 (方向判定):  alpha_engine_v21, technical_basic, ichimoku,
#                           smc, alpha_zoo, multi_factor → 1 票
#   - 辅助观察 (0 票):       harmonic (反转形态), pair_trading (相对强弱),
#                           volatility (状态描述), factor_research (截面)
# 加权总分 max = 3×2 + 6×1 = 12
#   - 阶段 1 (强动能): score ≥ 9/12
#   - 阶段 2 (衰减):   5/12 ≤ score < 9/12
#   - 阶段 3 (结束):   score < 5/12
# ============================================================
EVENT_SIGNALS = ['candlestick', 'chanlun', 'ml_strategy']
TREND_SIGNALS = ['alpha_engine_v21', 'technical_basic', 'ichimoku', 'smc', 'alpha_zoo', 'multi_factor']


def score_v22(signals: dict, w_event: int = 2, w_trend: int = 1) -> tuple:
    """v2.2 分级计票 → (score, max_score, event_pos, event_neg, trend_pos)
    w_event: 事件信号 (candlestick/chanlun/ml_strategy) 权重
    w_trend: 趋势信号权重
    max_score = 3*w_event + 6*w_trend; 阶段1 ≥ 0.75*max, 阶段2 ≥ 0.42*max
    """
    event_pos = sum(1 for k in EVENT_SIGNALS if signals[k].get('signal', 0) > 0)
    event_neg = sum(1 for k in EVENT_SIGNALS if signals[k].get('signal', 0) < 0)
    trend_pos = sum(1 for k in TREND_SIGNALS if signals[k].get('signal', 0) > 0)
    max_score = 3 * w_event + 6 * w_trend
    score = w_event * event_pos + w_trend * trend_pos - w_event * event_neg
    return score, max_score, event_pos, event_neg, trend_pos


def stage_v22(score: int, max_score: int) -> tuple:
    thr1 = 0.75 * max_score   # 阶段 1 门槛 (强动能)
    thr2 = 0.42 * max_score   # 阶段 3 门槛 (动能结束)
    if score >= thr1:
        return 1, '强动能期'
    elif score >= thr2:
        return 2, '动能衰减期'
    else:
        return 3, '动能结束期'


def compute_at(df: pd.DataFrame, cut: int, ticker: str, peer_dfs: dict, variant: str = 'v2.0',
               w_event: int = 2, w_trend: int = 1) -> dict:
    """在 cut 截断点重算全部信号 (无未来函数)"""
    d = df.iloc[:cut + 1].copy().reset_index(drop=True)
    if len(d) < 80:
        return None

    try:
        s = {
            'alpha_engine_v21': calc_alpha_engine_v21(d, ticker),
            'candlestick': calc_candlestick(d),
            'ml_strategy': calc_ml_strategy(d),
            'chanlun': calc_chanlun(d, ticker),
            'technical_basic': calc_technical_basic(d),
            'ichimoku': calc_ichimoku(d),
            'smc': calc_smc(d),
            'alpha_zoo': calc_alpha_zoo(d),
            'factor_research': calc_factor_research(d, None),
            'multi_factor': calc_multi_factor(d, None),
            'volatility': calc_volatility(d),
            'harmonic': calc_harmonic(d),
            'pair_trading': calc_pair_trading(d, {}, ticker),
        }
    except Exception:
        return None

    strong_ss = strong_signals_of(variant)
    strong_healthy = sum(1 for k in strong_ss if s[k].get('strong_momentum', False))
    end = check_momentum_end_signals(s)
    end_count = sum(1 for v in end.values() if v)

    if variant == 'v2.2':
        score, mscore, ev_pos, ev_neg, tr_pos = score_v22(s, w_event=w_event, w_trend=w_trend)
        stage, stage_name = stage_v22(score, mscore)
        return {
            'strong_healthy': strong_healthy,
            'score_v22': score,
            'event_pos': ev_pos, 'event_neg': ev_neg, 'trend_pos': tr_pos,
            'end_count': end_count,
            'end_signals': [k for k, v in end.items() if v],
            'stage': stage,
            'stage_name': stage_name,
            'adx': s['technical_basic'].get('adx'),
            'rsi': s['technical_basic'].get('rsi'),
            'wt1': s['alpha_engine_v21'].get('wt1'),
            'close': float(d.iloc[-1]['close']),
        }

    stage, stage_name = stage_of(strong_healthy, end_count)

    return {
        'strong_healthy': strong_healthy,
        'end_count': end_count,
        'end_signals': [k for k, v in end.items() if v],
        'stage': stage,
        'stage_name': stage_name,
        'adx': s['technical_basic'].get('adx'),
        'rsi': s['technical_basic'].get('rsi'),
        'wt1': s['alpha_engine_v21'].get('wt1'),
        'close': float(d.iloc[-1]['close']),
    }


def load_tech(ticker: str) -> pd.DataFrame:
    """加载任意股票日线 (tech-pool 优先, 否则 local data / Sina fallback)"""
    import glob
    rename = {'日期': 'date', '股票代码': 'code', '开盘': 'open', '收盘': 'close',
              '最高': 'high', '最低': 'low', '成交量': 'volume', '成交额': 'amount',
              '涨跌幅': 'chg_pct'}
    for f in glob.glob(str(TECH_DIR / f"{ticker}_*.csv")):
        df = pd.read_csv(f)
        df = df.rename(columns={k: v for k, v in rename.items() if k in df.columns})
        df['date'] = pd.to_datetime(df['date'])
        return df.sort_values('date').reset_index(drop=True)
    return load_data(ticker)


def backtest_ticker(ticker: str, start: str, weekday: int, variant: str = 'v2.0',
                    w_event: int = 2, w_trend: int = 1) -> pd.DataFrame:
    df = load_tech(ticker)
    df = df[df['date'] >= '2022-06-01'].reset_index(drop=True)
    last_close = float(df.iloc[-1]['close'])

    dates = df['date']
    eval_mask = (dates >= pd.Timestamp(start)) & (dates.dt.weekday == weekday)
    eval_idx = df.index[eval_mask].tolist()

    rows = []
    for i in eval_idx:
        cut = df.index.get_loc(i)
        row = compute_at(df, cut, ticker, {}, variant, w_event, w_trend)
        if row is None:
            continue
        # 未来收益 (用真实未来数据, 仅评估用)
        fut = df.iloc[cut + 1: cut + 21]
        f5 = fut.iloc[4]['close'] / row['close'] - 1 if len(fut) >= 5 else np.nan
        f10 = fut.iloc[9]['close'] / row['close'] - 1 if len(fut) >= 10 else np.nan
        f20 = fut.iloc[19]['close'] / row['close'] - 1 if len(fut) >= 20 else np.nan
        row.update({'date': df.iloc[cut]['date'].date(), 'fwd_5d': f5, 'fwd_10d': f10, 'fwd_20d': f20})
        rows.append(row)

    return pd.DataFrame(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--start', default='2026-01-01')
    ap.add_argument('--weekday', type=int, default=4, help='评估日 (4=周五)')
    ap.add_argument('--variant', default='v2.2', choices=['v2.0', 'v2.1', 'v2.2'],
                    help='v2.0=原始 (factor_research 死灯), v2.1=修复 (multi_factor 补位), v2.2=分级计票')
    ap.add_argument('--w-event', type=int, default=2, help='v2.2 事件信号权重 (candlestick/chanlun/ml_strategy)')
    ap.add_argument('--w-trend', type=int, default=1, help='v2.2 趋势信号权重')
    ap.add_argument('--tickers', default=None, help='标的池, 逗号分隔 (默认: 科技股池+药石)')
    ap.add_argument('--out', default=None, help='输出目录名, 如 BT-001')
    args = ap.parse_args()

    tickers = ([t.strip() for t in args.tickers.split(',') if t.strip()]
               if args.tickers else TECH_POOL + ['300725'])
    summary = []
    run_date = datetime.now().date()
    run_dir = RUNS_DIR / str(run_date)
    run_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 76)
    print(f"🔬 SELL_LADDER Walk-Forward 回测 — 2026 科技股行情 ({run_date}) 变体: {args.variant} (w_event={args.w_event}, w_trend={args.w_trend})")
    print(f"   评估点: {args.start} 起 每周{['一','二','三','四','五','六','日'][args.weekday]}  | 数据: 本地 tech-pool + 药石")
    print("=" * 76)

    for t in tickers:
        df_t = backtest_ticker(t, args.start, args.weekday, args.variant, args.w_event, args.w_trend)
        if df_t.empty:
            print(f"\n{t}: 无评估点")
            continue
        out_csv = run_dir / f"backtest_{t}_{args.variant}_we{args.w_event}_wt{args.w_trend}.csv"
        df_t.to_csv(out_csv, index=False)

        # 统计
        n = len(df_t)
        st1 = (df_t['stage'] == 1).sum()
        st2 = (df_t['stage'] == 2).sum()
        st3 = (df_t['stage'] == 3).sum()
        # 阶段 3 触发后 20d 收益 (预警质量: 负得越多 = 预警越值钱)
        s3 = df_t[df_t['stage'] == 3]
        s3_20 = s3['fwd_20d'].dropna()
        # 阶段 1 期间的 20d 收益 (不误杀: 应显著为正)
        s1 = df_t[df_t['stage'] == 1]
        s1_20 = s1['fwd_20d'].dropna()
        last = df_t.iloc[-1]

        print(f"\n{t}  ({last['date']}, 收盘 {last['close']:.2f})")
        print(f"  评估点: {n}  |  阶段1: {st1} ({st1/n*100:.0f}%)  阶段2: {st2} ({st2/n*100:.0f}%)  阶段3: {st3} ({st3/n*100:.0f}%)")
        if len(s1_20) > 0:
            print(f"  阶段1 期间 fwd20d: 均值 {s1_20.mean()*100:+.1f}%  中位 {s1_20.median()*100:+.1f}%  (正值=不误杀上涨)")
        if len(s3_20) > 0:
            print(f"  阶段3 触发后 fwd20d: 均值 {s3_20.mean()*100:+.1f}%  中位 {s3_20.median()*100:+.1f}%  (负值=预警值钱)")

        summary.append({
            'ticker': t, 'n': n, 'stage1': st1, 'stage2': st2, 'stage3': st3,
            's1_fwd20_mean': float(s1_20.mean() * 100) if len(s1_20) else None,
            's1_fwd20_med': float(s1_20.median() * 100) if len(s1_20) else None,
            's3_fwd20_mean': float(s3_20.mean() * 100) if len(s3_20) else None,
            's3_fwd20_med': float(s3_20.median() * 100) if len(s3_20) else None,
            'last_stage': int(last['stage']),
            'last_strong': int(last['strong_healthy']),
            'last_end': int(last['end_count']),
        })

    # 汇总
    print("\n" + "=" * 76)
    print("📊 汇总")
    print("=" * 76)
    s = pd.DataFrame(summary)
    print(s.to_string(index=False))

    out_json = run_dir / f"backtest_summary_{args.variant}_we{args.w_event}_wt{args.w_trend}.json"
    with open(out_json, 'w', encoding='utf-8') as f:
        json.dump({'date': str(run_date), 'start': args.start, 'variant': args.variant,
                   'w_event': args.w_event, 'w_trend': args.w_trend,
                   'summary': json.loads(s.to_json(orient='records'))},
                  f, ensure_ascii=False, indent=2)
    print(f"\n✅ 结果已保存: {run_dir}/backtest_*_{args.variant}_we{args.w_event}_wt{args.w_trend}.csv + backtest_summary_{args.variant}_we{args.w_event}_wt{args.w_trend}.json")


if __name__ == "__main__":
    main()