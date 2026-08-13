#!/usr/bin/env python3
"""DUAL-SCORE — SELL_LADDER 双分数输出 (v3.7, 2026-08-13, BT-011/BT-012 实证结论落地)

背景: BT-011 (2026 弱市) 最优 = V4 纯事件计票 + thr_mid 绝对阈值;
      BT-012 (2025 牛市) 最优 = V0 原版计票 + thr_lo 绝对阈值。
      两个回归中没有一个算法在所有 regime 都最优 → 双分数并列输出,
      用户根据大盘 (510300 vs MA60 ±7%) 决定采用哪个分数的建议仓位。

两个分数:
  weak_score (弱市震荡分): V4 计票 — score = 2·ev_pos − 2·ev_neg        (∈[-6,+6])
                           阈值 thr_mid 3.0/2.0 → 阶段 → 仓位
  bull_score (牛市上涨分): V0 计票 — score = 2·ev_pos + 1·tr_pos − 2·ev_neg (∈[-6,+14])
                           阈值 thr_lo 2.0/1.0 → 阶段 → 仓位
  (两个分数都受 end_count 5 大动能结束标志守门, 与 v2.5 阶段规则一致)

仓位映射: 阶段1 → 1.0 / 阶段2 → 0.7 / 阶段2.5 → 0.8 / 阶段3 → 0.2 (T+1 生效)

regime 标签: 510300 (沪深300 ETF) 收盘 vs MA60:
  close > MA60 × 1.07 → 牛市 (建议采用 bull_score)
  close < MA60 × 0.93 → 弱市 (建议采用 weak_score)
  |偏离| ≤ 7%          → 模糊区 (两个分数都参考, 用波动/趋势辅判)
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

_SELL_DIR = Path(__file__).resolve().parent
if str(_SELL_DIR) not in sys.path:
    sys.path.insert(0, str(_SELL_DIR))

from data_loader import load_daily  # noqa: E402

# 与 sell_ladder.py 保持一致
EVENT_SIGNALS = ['candlestick', 'chanlun', 'turnover_anomaly']
TREND_SIGNALS = ['alpha_engine_v21', 'technical_basic', 'ichimoku', 'smc',
                 'alpha_zoo', 'multi_factor', 'ml_strategy', 'sector_relative']

STAGE_POS = {1: 1.0, 2: 0.7, 2.5: 0.8, 3: 0.2}

# BT-011/BT-012 实证阈值
WEAK_THR = (3.0, 2.0)   # thr_mid — 2026 弱市最优
BULL_THR = (2.0, 1.0)   # thr_lo  — 2025 牛市最优 (excess 亏最少)

REGIME_ETF = '510300'   # 沪深300 ETF
MA60_WINDOW = 60
REGIME_BAND = 0.07      # ±7% 模糊带


def _counts(signals):
    """从 signals dict 解析 ev_pos / ev_neg / tr_pos / tr_neg (与 score_v22 同口径)"""
    ev_pos = sum(1 for k in EVENT_SIGNALS if signals.get(k, {}).get('signal', 0) > 0)
    ev_neg = sum(1 for k in EVENT_SIGNALS if signals.get(k, {}).get('signal', 0) < 0)
    tr_pos = sum(1 for k in TREND_SIGNALS if signals.get(k, {}).get('signal', 0) > 0)
    tr_neg = sum(1 for k in TREND_SIGNALS if signals.get(k, {}).get('signal', 0) < 0)
    return ev_pos, ev_neg, tr_pos, tr_neg


def score_v4(ev_pos, ev_neg):
    """弱市分: V4 纯事件计票 (趋势不参与)"""
    return 2 * ev_pos - 2 * ev_neg, 6


def score_v0(ev_pos, ev_neg, tr_pos):
    """牛市分: V0 原版 v2.5 计票 (趋势负票不扣分)"""
    return 2 * ev_pos + 1 * tr_pos - 2 * ev_neg, 14


def stage_from_thr(score, thr1, thr2, end_count):
    """绝对阈值阶段判定 (与 thr_scan / bt012 一致)"""
    if score >= thr1 and end_count <= 1:
        return 1, '强动能期'
    elif score >= thr2 and end_count <= 2:
        return 2, '动能衰减期'
    elif score < thr2 and end_count >= 3:
        return 3, '动能结束期'
    elif score < thr2 and end_count < 3:
        return 2.5, '阶段2.5-得分触底未共振'
    else:
        return 2, '动能衰减期'


def dual_score(signals, end_count):
    """计算双分数 → dict (JSON 友好)

    signals:    sell_ladder 16 skill 信号 dict ({name: {'signal': ±1/0, ...}})
    end_count:  5 大动能结束标志触发数 (0-5, 由 check_momentum_end_signals 得到)
    """
    ev_pos, ev_neg, tr_pos, tr_neg = _counts(signals)

    w_score, w_max = score_v4(ev_pos, ev_neg)
    w_thr1, w_thr2 = WEAK_THR
    w_stage, w_name = stage_from_thr(w_score, w_thr1, w_thr2, end_count)

    b_score, b_max = score_v0(ev_pos, ev_neg, tr_pos)
    b_thr1, b_thr2 = BULL_THR
    b_stage, b_name = stage_from_thr(b_score, b_thr1, b_thr2, end_count)

    return {
        'weak': {
            'label': '弱市震荡得分 (V4 纯事件 + thr_mid)',
            'formula': '2·ev_pos − 2·ev_neg',
            'ev_pos': ev_pos, 'ev_neg': ev_neg,
            'score': w_score, 'max': w_max,
            'threshold': (w_thr1, w_thr2),
            'end_count': end_count,
            'stage': w_stage, 'stage_name': w_name,
            'position': STAGE_POS.get(w_stage, 1.0),
        },
        'bull': {
            'label': '牛市上涨得分 (V0 原版 + thr_lo)',
            'formula': '2·ev_pos + 1·tr_pos − 2·ev_neg',
            'ev_pos': ev_pos, 'ev_neg': ev_neg, 'tr_pos': tr_pos,
            'score': b_score, 'max': b_max,
            'threshold': (b_thr1, b_thr2),
            'end_count': end_count,
            'stage': b_stage, 'stage_name': b_name,
            'position': STAGE_POS.get(b_stage, 1.0),
        },
        'regime': regime_label(),
    }


def regime_label(etf_code: str = REGIME_ETF, window: int = MA60_WINDOW,
                 band: float = REGIME_BAND):
    """大盘 regime 标签: 510300 收盘 vs MA60 (±7%)

    本地无 ETF 数据时返回 indeterminate (不阻塞 dual_score)。
    """
    try:
        df = load_daily(etf_code)
        if df is None or len(df) < window + 5:
            return {'status': 'indeterminate', 'reason': f'{etf_code} 数据不足'}
        close = df['close'].values
        ma60 = float(pd.Series(close).rolling(window).mean().iloc[-1])
        px = float(close[-1])
        dev = (px / ma60 - 1) * 100
        if dev > band * 100:
            mode, rec = '牛市', '采用 bull_score (牛市上涨分)'
        elif dev < -band * 100:
            mode, rec = '弱市', '采用 weak_score (弱市震荡分)'
        else:
            mode, rec = '模糊区', '两分并列参考, 方向性判断看 trend_break/动量'
        return {
            'status': 'ok', 'etf': etf_code, 'close': px, 'ma60': ma60,
            'dev_pct': round(dev, 2), 'mode': mode, 'recommend': rec,
        }
    except Exception as e:
        return {'status': 'indeterminate', 'reason': str(e)}


def format_dual(ds: dict) -> str:
    """终端展示 (人类可读)"""
    r = ds['regime']
    lines = [f"┌─ DUAL-SCORE 双分数 (BT-011/012 实证: 无单一算法通吃, 按大盘 regime 选用) ─┐"]
    if r.get('status') == 'ok':
        lines.append(f"│ 大盘: {r['etf']} {r['close']:.2f} vs MA60 {r['ma60']:.2f} "
                     f"({r['dev_pct']:+.1f}%) → {r['mode']} │")
        lines.append(f"│ 建议: {r['recommend']} │")
    else:
        lines.append(f"│ 大盘: 无法判定 ({r.get('reason', '?')}) — 手动判断 regime │")
    w, b = ds['weak'], ds['bull']
    lines.append("├───────────────────────────────────────────────────────────────────────────┤")
    lines.append(f"│ ① 弱市震荡分 (V4): score={w['score']:+.0f}/{w['max']} "
                 f"(ev {w['ev_pos']}正/{w['ev_neg']}负)  thr={w['threshold'][0]}/{w['threshold'][1]} │")
    lines.append(f"│    → 阶段{w['stage']} ({w['stage_name']}) → 建议仓位 {w['position']*100:.0f}% │")
    lines.append(f"│ ② 牛市上涨分 (V0): score={b['score']:+.0f}/{b['max']} "
                 f"(ev {b['ev_pos']}正/{b['ev_neg']}负 + tr {b['tr_pos']}正)  thr={b['threshold'][0]}/{b['threshold'][1]} │")
    lines.append(f"│    → 阶段{b['stage']} ({b['stage_name']}) → 建议仓位 {b['position']*100:.0f}% │")
    lines.append(f"└───────────────────────────────────────────────────────────────────────────┘")
    return "\n".join(lines)


if __name__ == '__main__':
    # 自测: 构造一个 signals dict
    test = {k: {'signal': 0} for k in EVENT_SIGNALS + TREND_SIGNALS}
    test['candlestick'] = {'signal': 1}
    test['turnover_anomaly'] = {'signal': 1}
    test['alpha_engine_v21'] = {'signal': 1}
    ds = dual_score(test, end_count=0)
    print(format_dual(ds))