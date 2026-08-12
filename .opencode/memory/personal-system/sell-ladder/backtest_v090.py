#!/usr/bin/env python3
"""
SELL_LADDER v2.2.1 — 完整持仓曲线 Walk-Forward 回测 (BT-009)

============================================================
目的 (回答 3 个 P2 方法论问题):
  P2-8: 样本扩展 (7 → 20 标的, 跨板块)
  P2-9: 加交易成本 (印花税/佣金/滑点)
  P2-10: 加 benchmark (买入持有 + 20% 移动止盈)

方法:
  - 标的池: 20 只 (科技 7 + 金融 4 + 消费 5 + 医药 2 + 新能源 2)
  - 评估点: 每周五 walk-forward (无未来函数)
  - 每个评估点用截至当日全部历史重算 13 信号 + 5 动能结束标志 + v2.2.1 阶段判定
  - 完整持仓曲线: 阶段1=100%, 阶段2.5=减30%, 阶段3=减80%
  - 交易成本: 印花税 0.05% + 佣金 0.025% (双边) + 滑点 0.1%
  - 双基准: 买入持有 (BH) + 20% 移动止盈 (MT20)

用法:
  python3 backtest_v090.py [--start 2026-01-01] [--weekday 4] [--tickers ...]

输出:
  - 每标的 weekly CSV (runs/<date>/backtest_v221_<ticker>.csv)
  - 资金曲线 JSON (含 v2.2.1 / BH / MT20 三条曲线对比)
  - 汇总报告 stdout
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
                         calc_volatility, calc_harmonic, calc_pair_trading,
                         calc_turnover_anomaly, calc_sector_relative,
                         calc_ad_line)

# 20 标的跨板块池
TICKER_POOL_20 = {
    # 科技 7 (tech-pool 已有)
    '688256': '寒武纪', '688981': '中芯国际', '002371': '北方华创',
    '300308': '中际旭创', '688041': '海光信息', '603501': '韦尔股份',
    '300725': '药石科技',
    # 金融 4 (raw_daily 已有或通用化下载)
    '601318': '中国平安', '600036': '招商银行', '601628': '中国人寿', '000001': '平安银行',
    # 消费 5
    '600519': '贵州茅台', '000858': '五粮液', '600887': '伊利股份',
    '000333': '美的集团', '603288': '海天味业',
    # 医药 2
    '600276': '恒瑞医药', '000538': '云南白药',
    # 新能源 2
    '300750': '宁德时代', '002594': '比亚迪',
}

# v2.3 板块 ETF 映射 (每个标的对应一个板块 ETF)
SECTOR_ETF_MAP = {
    '688256': ('159995', '半导体ETF'),  # 寒武纪
    '688981': ('159995', '半导体ETF'),  # 中芯国际
    '002371': ('159995', '半导体ETF'),  # 北方华创
    '300308': ('159995', '半导体ETF'),  # 中际旭创
    '688041': ('159995', '半导体ETF'),  # 海光信息
    '603501': ('159995', '半导体ETF'),  # 韦尔股份
    '300725': ('512010', '医药ETF'),    # 药石科技 (CDMO/医药)
    '601318': ('512800', '银行ETF'),    # 中国平安 (保险金融, 用银行ETF代理)
    '600036': ('512800', '银行ETF'),    # 招商银行
    '601628': ('512800', '银行ETF'),    # 中国人寿 (代理)
    '000001': ('512800', '银行ETF'),    # 平安银行
    '600519': ('510630', '消费ETF'),    # 贵州茅台
    '000858': ('510630', '消费ETF'),    # 五粮液
    '600887': ('510630', '消费ETF'),    # 伊利股份
    '000333': ('510630', '消费ETF'),    # 美的集团
    '603288': ('510630', '消费ETF'),    # 海天味业
    '600276': ('512010', '医药ETF'),    # 恒瑞医药
    '000538': ('512010', '医药ETF'),    # 云南白药
    '300750': ('515030', '新能源ETF'),  # 宁德时代
    '002594': ('515030', '新能源ETF'),  # 比亚迪
}

# 交易成本参数
STAMP_TAX = 0.0005       # 印花税 0.05% (单边卖出)
COMMISSION = 0.00025     # 佣金 0.025% (双边)
SLIPPAGE = 0.001         # 滑点 0.1% (双边)
COST_PER_TRADE = STAMP_TAX + COMMISSION * 2 + SLIPPAGE * 2  # ≈ 0.00275 单次完整买卖

# 阶段 → 仓位映射 (基于 SKILL.md v2.2.1)
STAGE_POSITION = {
    1: 1.00,   # 强动能: 持有 100%
    2: 0.70,   # 衰减: 减 30%
    2.5: 0.60, # 阶段2.5 观察: 减 40% (保守)
    3: 0.20,   # 结束: 减 80% (留 20% 试探)
}


def score_v22_1(signals: dict, w_event: int = 2, w_trend: int = 1) -> tuple:
    """v2.5 分级计票 (max=14: 3 事件 ×2 + 8 趋势 ×1, 移除 ad_line 回到 v2.3 状态)
    v2.5 调整说明: ad_line 移除, max=14, stage 2 阈值 0.42*14=5.88
    阶段 1 阈值仍 0.65*14=9.1 (v2.4 改善保留)
    """
    EVENT_SIGNALS = ['candlestick', 'chanlun', 'turnover_anomaly']
    TREND_SIGNALS = ['alpha_engine_v21', 'technical_basic', 'ichimoku', 'smc',
                     'alpha_zoo', 'multi_factor', 'ml_strategy', 'sector_relative']
    event_pos = sum(1 for k in EVENT_SIGNALS if signals.get(k, {}).get('signal', 0) > 0)
    event_neg = sum(1 for k in EVENT_SIGNALS if signals.get(k, {}).get('signal', 0) < 0)
    trend_pos = sum(1 for k in TREND_SIGNALS if signals.get(k, {}).get('signal', 0) > 0)
    max_score = len(EVENT_SIGNALS) * w_event + len(TREND_SIGNALS) * w_trend  # v2.5: 6 + 8 = 14
    score = w_event * event_pos + w_trend * trend_pos - w_event * event_neg
    return score, max_score, event_pos, event_neg, trend_pos


def stage_v22_1(score: int, max_score: int, end_count: int) -> tuple:
    """v2.4 阶段判定 (含阶段 2.5 兜底, 阈值 0.75→0.65)"""
    thr1 = 0.65 * max_score  # v2.4: 阶段1更可达
    thr2 = 0.42 * max_score
    if score >= thr1 and end_count <= 1:
        return 1, '强动能期'
    elif score >= thr2 and end_count <= 2:
        return 2, '动能衰减期'
    elif score < thr2 and end_count >= 3:
        return 3, '动能结束期'
    elif score < thr2 and end_count < 3:
        return 2.5, '阶段2.5-得分触底未共振'  # 兜底: 不恐慌清仓
    else:
        return 2, '动能衰减期'


def compute_at_v22_1(df: pd.DataFrame, cut: int, ticker: str, variant: str = 'v2.3',
                     w_event: int = 2, w_trend: int = 1, sector_df: pd.DataFrame = None) -> dict:
    """在 cut 截断点重算全部信号 (无未来函数)
    v2.3 新增: turnover_anomaly (事件) + sector_relative (趋势, 需 sector_df)
    """
    d = df.iloc[:cut + 1].copy().reset_index(drop=True)
    if len(d) < 80:
        return None

    sector_d = None
    if sector_df is not None and len(sector_df) > 0:
        sector_d = sector_df.iloc[:cut + 1].copy().reset_index(drop=True) if cut + 1 <= len(sector_df) else sector_df.copy()

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
            'turnover_anomaly': calc_turnover_anomaly(d),
            'sector_relative': calc_sector_relative(d, sector_d),
            'ad_line': calc_ad_line(d),
        }
    except Exception as e:
        return {'error': str(e)}

    end = check_momentum_end_signals(s, d)  # v2.2.1+: 传入 df 让 OBV 真参与
    end_count = sum(1 for v in end.values() if v)
    end_signals_list = [k for k, v in end.items() if v]

    score, mscore, ev_pos, ev_neg, tr_pos = score_v22_1(s, w_event=w_event, w_trend=w_trend)
    stage, stage_name = stage_v22_1(score, mscore, end_count)

    return {
        'score_v221': score,
        'max_score': mscore,
        'event_pos': ev_pos, 'event_neg': ev_neg, 'trend_pos': tr_pos,
        'end_count': end_count,
        'end_signals': end_signals_list,
        'stage': stage,
        'stage_name': stage_name,
        'adx': s['technical_basic'].get('adx'),
        'rsi': s['technical_basic'].get('rsi'),
        'wt1': s['alpha_engine_v21'].get('wt1'),
        'smc_signal': s['smc'].get('signal'),
        'turnover_signal': s['turnover_anomaly'].get('signal'),
        'sector_relative_signal': s['sector_relative'].get('signal'),
        'ad_line_signal': s['ad_line'].get('signal'),
        'close': float(d.iloc[-1]['close']),
    }


def load_ticker_data(ticker: str, name: str) -> pd.DataFrame:
    """加载日线: 集中化 data/market/daily → 旧位置 fallback → Sina 下载落盘"""
    return load_data(ticker)


def load_sector_data(ticker: str) -> pd.DataFrame:
    """v2.3: 加载板块 ETF 数据 (用于 calc_sector_relative)"""
    if ticker not in SECTOR_ETF_MAP:
        return pd.DataFrame()
    etf_code, etf_name = SECTOR_ETF_MAP[ticker]
    print(f"  [{ticker}] 加载板块 ETF {etf_code} {etf_name}...", flush=True)
    try:
        return load_data(etf_code)
    except Exception as e:
        print(f"  ⚠️ 板块 ETF {etf_code} 加载失败: {e}")
        return pd.DataFrame()


def backtest_ticker_with_position_curve(ticker: str, name: str, start: str, weekday: int,
                                        variant: str = 'v2.3',
                                        w_event: int = 2, w_trend: int = 1) -> dict:
    """回测单标的，返回:
    - df_weekly: 每周评估点 + 阶段判定
    - nav_v221: v2.3 持仓曲线 (NAV)
    - nav_bh: 买入持有 NAV
    - nav_mt20: 20% 移动止盈 NAV
    """
    df = load_ticker_data(ticker, name)
    if df is None or len(df) < 100:
        return {'error': '数据加载失败', 'ticker': ticker, 'name': name}
    df = df[df['date'] >= '2022-06-01'].reset_index(drop=True)
    if len(df) < 100:
        return {'error': '数据不足 (warmup < 100 bars)', 'ticker': ticker, 'name': name}

    # v2.3: 加载板块 ETF 数据 (个股 vs 板块强弱判定用)
    sector_df = load_sector_data(ticker)
    if sector_df.empty:
        print(f"  [{ticker}] 板块数据空, sector_relative 将退化为中性 0", flush=True)

    dates = df['date']
    eval_mask = (dates >= pd.Timestamp(start)) & (dates.dt.weekday == weekday)
    eval_idx = df.index[eval_mask].tolist()

    rows = []
    for i in eval_idx:
        cut = df.index.get_loc(i)
        row = compute_at_v22_1(df, cut, ticker, variant, w_event, w_trend, sector_df)
        if row is None or 'error' in row:
            continue
        # 未来收益 (仅评估用)
        fut = df.iloc[cut + 1: cut + 21]
        f5 = (fut.iloc[4]['close'] / row['close'] - 1) if len(fut) >= 5 else np.nan
        f10 = (fut.iloc[9]['close'] / row['close'] - 1) if len(fut) >= 10 else np.nan
        f20 = (fut.iloc[19]['close'] / row['close'] - 1) if len(fut) >= 20 else np.nan
        row.update({
            'date': df.iloc[cut]['date'].date(),
            'fwd_5d': f5, 'fwd_10d': f10, 'fwd_20d': f20,
        })
        rows.append(row)

    if not rows:
        return {'error': '无评估点', 'ticker': ticker, 'name': name}

    df_weekly = pd.DataFrame(rows)

    # ----- 资金曲线模拟 -----
    # 时间窗: start 之后的所有交易日
    df_fut = df[df['date'] >= pd.Timestamp(start)].reset_index(drop=True)
    if len(df_fut) < 2:
        return {'error': '未来数据不足', 'ticker': ticker, 'name': name}

    # v2.2.1 策略: 每周评估日触发再平衡, 仓位按 STAGE_POSITION 映射
    pos_v221 = np.ones(len(df_fut))  # 默认 100%
    eval_dates = set(pd.Timestamp(r['date']) for r in rows)
    last_stage = 1  # 默认阶段1
    last_eval_idx = -1
    for j in range(len(df_fut)):
        dt = df_fut.iloc[j]['date']
        if dt in eval_dates:
            row_match = next((r for r in rows if pd.Timestamp(r['date']) == dt), None)
            if row_match is not None:
                last_stage = row_match['stage']
                last_eval_idx = j
        pos_v221[j] = STAGE_POSITION.get(last_stage, 0.6)

    # 计算每周调仓收益 (signal-driven rebalance)
    # 假设每周评估日把仓位调到目标值 (差值交易付成本)
    ret = df_fut['close'].pct_change().fillna(0).values
    nav_v221 = np.ones(len(df_fut))
    target_pos = pos_v221.copy()
    for j in range(1, len(df_fut)):
        # 收益 = 仓位 × 当日收益
        nav_v221[j] = nav_v221[j-1] * (1 + target_pos[j-1] * ret[j])
        # 调仓成本 (如果本周是评估日, 仓位变化 → 交易成本)
        if j > 0 and target_pos[j] != target_pos[j-1]:
            trade_size = abs(target_pos[j] - target_pos[j-1])
            nav_v221[j] *= (1 - trade_size * COST_PER_TRADE)

    # BH (买入持有)
    nav_bh = np.ones(len(df_fut))
    for j in range(1, len(df_fut)):
        nav_bh[j] = nav_bh[j-1] * (1 + ret[j])

    # MT20 (20% 移动止盈)
    nav_mt20 = np.ones(len(df_fut))
    peak = df_fut.iloc[0]['close']
    in_market = True
    pos_mt = 1.0
    for j in range(1, len(df_fut)):
        price = df_fut.iloc[j]['close']
        if in_market:
            nav_mt20[j] = nav_mt20[j-1] * (1 + ret[j])
            peak = max(peak, price)
            if price <= peak * 0.80:  # 跌破高点 20% → 清仓
                nav_mt20[j] *= (1 - 0.0015)  # 卖出成本
                in_market = False
                pos_mt = 0.0
        else:
            nav_mt20[j] = nav_mt20[j-1]  # 现金状态
            # 简化: 不再回补 (避免 lookahead)

    # 阶段 3 误杀率 (信号触发后 fwd20d 为正的占比)
    s3_rows = df_weekly[df_weekly['stage'] == 3]
    s3_miss_rate = float((s3_rows['fwd_20d'] > 0).mean()) if len(s3_rows) > 0 else None

    # 阶段 1 持有质量 (期间 fwd20d 中位)
    s1_rows = df_weekly[df_weekly['stage'] == 1]
    s1_hold_med = float(s1_rows['fwd_20d'].median()) if len(s1_rows) > 0 else None

    return {
        'ticker': ticker,
        'name': name,
        'df_weekly': df_weekly,
        'nav_v221_final': float(nav_v221[-1]),
        'nav_bh_final': float(nav_bh[-1]),
        'nav_mt20_final': float(nav_mt20[-1]),
        'n_eval': len(df_weekly),
        'n_s1': int((df_weekly['stage'] == 1).sum()),
        'n_s2': int((df_weekly['stage'] == 2).sum()),
        'n_s25': int((df_weekly['stage'] == 2.5).sum()),
        'n_s3': int((df_weekly['stage'] == 3).sum()),
        's3_miss_rate': s3_miss_rate,
        's1_hold_med': s1_hold_med,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--start', default='2026-01-01')
    ap.add_argument('--weekday', type=int, default=4, help='4=周五')
    ap.add_argument('--variant', default='v2.2.1')
    ap.add_argument('--w-event', type=int, default=2)
    ap.add_argument('--w-trend', type=int, default=1)
    ap.add_argument('--tickers', default=None, help='逗号分隔; 默认 20 标的池')
    ap.add_argument('--out-tag', default='BT-009')
    args = ap.parse_args()

    if args.tickers:
        tickers = {t.strip(): TICKER_POOL_20.get(t.strip(), t.strip())
                   for t in args.tickers.split(',') if t.strip()}
    else:
        tickers = TICKER_POOL_20

    run_date = datetime.now().date()
    run_dir = RUNS_DIR / str(run_date)
    run_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 80)
    print(f"🔬 BT-009 SELL_LADDER v2.2.1 完整持仓曲线回测 ({run_date})")
    print(f"   标的池: {len(tickers)} 只  |  评估日: 周{args.weekday}  |  起始: {args.start}")
    print(f"   阶段仓位: {STAGE_POSITION}")
    print(f"   交易成本: 印花税{STAMP_TAX*100:.2f}% + 佣金{COMMISSION*100:.2f}%×2 + 滑点{SLIPPAGE*100:.1f}%×2 = {COST_PER_TRADE*100:.3f}%/次")
    print("=" * 80)

    summary_rows = []
    for t, name in tickers.items():
        print(f"\n→ {t} {name} ...", flush=True)
        res = backtest_ticker_with_position_curve(t, name, args.start, args.weekday,
                                                  args.variant, args.w_event, args.w_trend)
        if 'error' in res:
            print(f"  ❌ {res['error']}")
            summary_rows.append({'ticker': t, 'name': name, 'error': res['error']})
            continue

        df_w = res['df_weekly']
        out_csv = run_dir / f"backtest_{args.out_tag}_{t}_{args.variant}.csv"
        df_w.to_csv(out_csv, index=False)

        v221_ret = (res['nav_v221_final'] - 1) * 100
        bh_ret = (res['nav_bh_final'] - 1) * 100
        mt_ret = (res['nav_mt20_final'] - 1) * 100
        s3_miss = f"{res['s3_miss_rate']*100:.0f}%" if res['s3_miss_rate'] is not None else "N/A"
        s1_med = f"{res['s1_hold_med']*100:+.1f}%" if res['s1_hold_med'] is not None else "N/A"

        print(f"  ✅ 评估点 {res['n_eval']}  阶段 1/2/2.5/3: {res['n_s1']}/{res['n_s2']}/{res['n_s25']}/{res['n_s3']}")
        print(f"     阶段3 误杀率: {s3_miss}  阶段1 持有 fwd20d 中位: {s1_med}")
        print(f"     NAV (区间收益): v2.2.1={v221_ret:+.1f}%  BH={bh_ret:+.1f}%  MT20={mt_ret:+.1f}%")

        summary_rows.append({
            'ticker': t, 'name': name, 'n_eval': res['n_eval'],
            's1': res['n_s1'], 's2': res['n_s2'], 's25': res['n_s25'], 's3': res['n_s3'],
            's3_miss_rate': res['s3_miss_rate'], 's1_hold_med': res['s1_hold_med'],
            'nav_v221_final': res['nav_v221_final'],
            'nav_bh_final': res['nav_bh_final'],
            'nav_mt20_final': res['nav_mt20_final'],
        })

    # 汇总
    print("\n" + "=" * 80)
    print("📊 BT-009 汇总 (完整持仓曲线模拟)")
    print("=" * 80)
    df_sum = pd.DataFrame(summary_rows)
    # 排除 error 行
    valid = df_sum[df_sum['nav_v221_final'].notna()].copy()
    if len(valid) > 0:
        valid['v221_vs_bh'] = (valid['nav_v221_final'] - valid['nav_bh_final']) * 100
        valid['v221_vs_mt20'] = (valid['nav_v221_final'] - valid['nav_mt20_final']) * 100
        print(valid[['ticker', 'name', 's1', 's3', 's3_miss_rate', 's1_hold_med',
                     'nav_v221_final', 'nav_bh_final', 'nav_mt20_final',
                     'v221_vs_bh', 'v221_vs_mt20']].to_string(index=False))

        print("\n🏆 平均:")
        print(f"  v2.2.1 收益: {valid['nav_v221_final'].mean()*100-100:+.2f}%")
        print(f"  BH   收益: {valid['nav_bh_final'].mean()*100-100:+.2f}%")
        print(f"  MT20 收益: {valid['nav_mt20_final'].mean()*100-100:+.2f}%")
        # v2.2.1 跑赢 BH 的占比
        win_rate_bh = (valid['v221_vs_bh'] > 0).mean() * 100
        win_rate_mt = (valid['v221_vs_mt20'] > 0).mean() * 100
        print(f"  v2.2.1 跑赢 BH 的标的占比: {win_rate_bh:.0f}%")
        print(f"  v2.2.1 跑赢 MT20 的标的占比: {win_rate_mt:.0f}%")

    # 保存 JSON
    out_json = run_dir / f"backtest_summary_{args.out_tag}_{args.variant}.json"
    with open(out_json, 'w', encoding='utf-8') as f:
        json.dump({'date': str(run_date), 'variant': args.variant, 'start': args.start,
                   'stage_position': STAGE_POSITION, 'cost_per_trade': COST_PER_TRADE,
                   'summary': json.loads(df_sum.to_json(orient='records'))},
                  f, ensure_ascii=False, indent=2)
    print(f"\n✅ 结果已保存: {run_dir}/")


if __name__ == "__main__":
    main()