#!/usr/bin/env python3
"""
SELL_LADDER v2.0 — 14 Skill 信号驱动的卖出框架 (统一入口)

============================================================
用法:
  python3 sell_ladder.py --ticker 300725
  python3 sell_ladder.py --ticker 300725 --cost 36.62
  python3 sell_ladder.py --ticker 300725 --cost 36.62 --shares 10000
  python3 sell_ladder.py --ticker 300725 --cost 36.62 --shares 10000 --no-cdmo

功能:
  1. 自动加载 14 skill (5 强动能 + 4 辅助 + 3 数据 + 2 框架)
  2. 计算 5 大动能结束标志
  3. 输出 3 阶段卖出方案
  4. 更新 POSITION_SIZING.md

依赖:
  pip install -r requirements.txt
============================================================
"""
import argparse
import json
import os
import sys
import warnings
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings('ignore')

# v3.7: DUAL-SCORE 双分数 (BT-011/012 实证) — 弱市分(V4+thr_mid) / 牛市分(V0+thr_lo)
from dual_score import dual_score, format_dual  # noqa: E402


# ============================================================
# 0. 默认配置
# ============================================================
# SELL_LADDER 工具位于: .opencode/memory/personal-system/sell-ladder/
# 目录结构:
#   sell-ladder/
#   ├── sell_ladder.py          (本文件)
#   ├── requirements.txt
#   ├── README.md
#   ├── data/                   (本地 CSV 数据)
#   │   ├── raw_daily_300725.csv
#   │   ├── wt_daily_300725.csv
#   │   └── cross-data/         (CDMO 同业)
#   └── runs/                   (历史跑过的结果)
#       └── YYYY-MM-DD/
#
# 临时报告输出 (out/) 与本工具分离, 每次跑可指定 --out
# ============================================================

SELL_LADDER_DIR = Path(__file__).resolve().parent  # .opencode/memory/personal-system/sell-ladder/
DATA_DIR = SELL_LADDER_DIR / "data"                 # 永久数据
CROSS_DIR = DATA_DIR / "cross-data"                 # CDMO 同业
RUNS_DIR = SELL_LADDER_DIR / "runs"                 # 跑过的结果
MEM_DIR = SELL_LADDER_DIR.parent                    # personal-system/

# 默认临时输出目录 (CLI 可覆盖)
DEFAULT_OUT_DIR = Path(__file__).resolve().parents[4] / "out" / "sell_ladder_runs"

# 化债 deadline (框架强约束)
DEBT_DEADLINE = "2027-04-30"  # CHINA_FRAMEWORK §10.1
DEBT_QUOTA_CLOSE = "2026-12-31"  # 联和评级口径

# 5 大动能结束标志触发条件
MOMENTUM_END_SIGNALS = {
    'trend_break': {'name': '趋势破坏', 'trigger': 'EMA(12) 跌破 + ADX<25 + ichimoku 跌穿云'},
    'momentum_reversal': {'name': '动量反转', 'trigger': 'WT1<-20 + RSI<30 持续 + 20d 动量<-10%'},
    'volume_divergence': {'name': '量能背离', 'trigger': 'OBV 下降 + 价格新高 (5 日)'},
    'structure_break': {'name': '结构破坏', 'trigger': 'smc ChoCH + chanlun 顶分型 + ichimoku 跌穿云'},
    'volatility_drop': {'name': '波动率突变', 'trigger': 'HV 100% → 30% (30 日内)'},
}

# ============================================================
# 1. 数据加载 (委托给集中化 data_loader)
# ============================================================
def load_data(ticker: str) -> pd.DataFrame:
    """加载日线数据 (统一入口): data/market/daily → 旧位置 fallback → Sina API 下载并落盘。

    委托 data_loader.load_daily, 保留旧函数签名兼容调用方。
    """
    from data_loader import load_daily
    if not ticker.isdigit():
        raise ValueError(f"代码必须是数字: {ticker}")
    df = load_daily(ticker)
    if df is None or df.empty:
        raise ValueError(f"无法加载 {ticker} 数据 (本地无 + Sina 下载失败)")
    return df


def _standardize(df: pd.DataFrame, ticker: str) -> pd.DataFrame:
    """标准化列名 + 类型 (兼容本地中文列名 / Sina API 英文列名) —— 保留兼容"""
    from data_loader import _standardize as _dl_std
    return _dl_std(df, ticker)


def _sina_download(code: str) -> pd.DataFrame:
    """Sina 历史 K 线 (fallback) —— 保留兼容"""
    from data_loader import _sina_download as _dl_sina
    return _dl_sina(code)


# ============================================================
# 2. 14 Skill 信号计算
# ============================================================
def calc_alpha_engine_v21(df, ticker='300725',
                          ob_level1=60, ob_level2=53,
                          os_level1=-60, os_level2=-53):
    """alpha_engine_v21: 用户原创 LazyBear WaveTrend with Crosses (Pine Script 严格实现)

    原始 Pine Script 来源 (用户 @LazyBear):
        study(title="WaveTrend with Crosses [LazyBear]", shorttitle="WT_CROSS_LB")
        n1 = input(10, "Channel Length")           ← ESA 周期
        n2 = input(21, "Average Length")           ← CI/TCI 周期
        obLevel1 = input(60, "Over Bought Level 1")  ← WT1 ≥ 60 超买
        obLevel2 = input(53, "Over Bought Level 2")  ← WT1 ≥ 53 超买二级
        osLevel1 = input(-60, "Over Sold Level 1")   ← WT1 ≤ -60 超卖
        osLevel2 = input(-53, "Over Sold Level 2")   ← WT1 ≤ -53 超卖二级

        ap = hlc3                                  ← (H+L+C)/3
        esa = ema(ap, n1)
        d = ema(abs(ap - esa), n1)
        ci = (ap - esa) / (0.015 * d)
        tci = ema(ci, n2)                          ← WT1
        wt1 = tci
        wt2 = sma(wt1, 4)                          ← WT2 (SMA(4), NOT EMA)

        barcolor(cross(wt1, wt2) ? (wt2 - wt1 > 0 ? aqua : yellow) : na)
        //  aqua = wt2 > wt1 (wt1 向下穿 wt2) → 死叉 → 看空
        //  yellow = wt2 < wt1 (wt1 向上穿 wt2) → 金叉 → 看多

    v3.4 完全重写: 严格按 Pine Script 实现 cross() 信号 + 四档阈值 (obLevel1/2, osLevel1/2)
    信号语义:
      - 金叉 (WT1 上穿 WT2) + WT1 在 os_level2 (-53) 上方 → +1 (中位反弹)
      - 金叉 + WT1 在 os_level2 (-53) 下方 → +1 (超卖反弹, 强)
      - 死叉 (WT1 下穿 WT2) + WT1 在 ob_level2 (53) 上方 → -1 (超买下跌, 强)
      - 死叉 + WT1 在 ob_level2 (53) 下方 → -1 (中位下跌)
      - 无交叉: 0 (观望)
    """
    if 'wt1' not in df.columns or 'wt2' not in df.columns:
        df = _compute_wt(df)

    if len(df) < 2:
        return {'error': '数据不足', 'signal': 0, 'healthy': False}

    prev = df.iloc[-2]
    last = df.iloc[-1]
    wt1 = float(last.get('wt1', 0) or 0)
    wt2 = float(last.get('wt2', 0) or 0)
    pwt1 = float(prev.get('wt1', 0) or 0)
    pwt2 = float(prev.get('wt2', 0) or 0)

    # zone 分类 (基于 ob/osLevel1)
    if wt1 >= ob_level1: zone = f"OB≥{ob_level1}"
    elif wt1 >= ob_level2: zone = f"OB2≥{ob_level2}"
    elif wt1 >= 20: zone = "M+ 20-OB2"
    elif wt1 >= 0: zone = "N+ 0-20"
    elif wt1 >= os_level2: zone = "N- 0-OS2"
    elif wt1 >= os_level1: zone = f"OS2≤{os_level2}"
    else: zone = f"OS≤{os_level1}"

    # cross() 严格按 Pine Script 语义: 比较前后两根 bar 的 wt1 vs wt2 相对关系
    # gold cross (金叉): WT1 向上穿越 WT2 → wt2 - pwt1 > 0 AND pwt2 - wt1 > 0 → 等价 wt1 > wt2 AND pwt1 <= pwt2
    # death cross (死叉): WT1 向下穿越 WT2 → 反之
    is_gold_cross = (pwt1 <= pwt2) and (wt1 > wt2)
    is_death_cross = (pwt1 >= pwt2) and (wt1 < wt2)

    if is_gold_cross:
        # 金叉 → 看多 (+1), 强度由 WT1 位置决定
        signal = 1
        if pwt1 < os_level2:
            verdict = f"🟢⬆️ 金叉 (超卖反弹, WT1 {pwt1:+.1f}→{wt1:+.1f}, {zone})"
        elif wt1 > ob_level2:
            verdict = f"🟢⬆️ 金叉 (高位反转, WT1 {pwt1:+.1f}→{wt1:+.1f}, {zone})"
        else:
            verdict = f"🟢⬆️ 金叉 (WT1 {pwt1:+.1f}→{wt1:+.1f}, {zone})"
    elif is_death_cross:
        # 死叉 → 看空 (-1), 强度由 WT1 位置决定
        signal = -1
        if pwt1 > ob_level2:
            verdict = f"🔴⬇️ 死叉 (超买下跌, WT1 {pwt1:+.1f}→{wt1:+.1f}, {zone})"
        elif wt1 < os_level2:
            verdict = f"🔴⬇️ 死叉 (低位反转, WT1 {pwt1:+.1f}→{wt1:+.1f}, {zone})"
        else:
            verdict = f"🔴⬇️ 死叉 (WT1 {pwt1:+.1f}→{wt1:+.1f}, {zone})"
    else:
        # 无交叉: 观望
        signal = 0
        verdict = f"⚪ 无交叉 (WT1 {wt1:+.1f} vs WT2 {wt2:+.1f}, {zone})"

    return {
        'wt1': wt1, 'wt2': wt2, 'zone': zone,
        'signal': signal, 'verdict': verdict, 'healthy': True,
        'cross_type': 'gold' if is_gold_cross else ('death' if is_death_cross else 'none'),
        'ob_level1': ob_level1, 'ob_level2': ob_level2,
        'os_level1': os_level1, 'os_level2': os_level2,
    }


def _compute_wt(df, n1=10, n2=21):
    """LazyBear WaveTrend (日频经典公式, hlc3 输入)

    与 LazyBear TradingView 原版一致:
      N1=10 (Channel Length), N2=21 (Average Length)
      AP  = (HIGH + LOW + CLOSE) / 3   (hlc3)
      ESA = EMA(AP, N1)
      D   = EMA(ABS(AP - ESA), N1)
      CI  = (AP - ESA) / (0.015 * D)
      WT1 = EMA(CI, N2)
      WT2 = SMA(WT1, 4)

    注: alpha-engine-v21 的 wave_trend.py (N1=50/N2=105 close-only) 是 V21 周频
    规范版本; 本函数保留日频 LazyBear 原版, 两者为不同频率的同一指标族。
    """
    c = df['close']
    h = df['high']
    l = df['low']
    ap = (h + l + c) / 3
    esa = ap.ewm(span=n1, adjust=False).mean()
    d = (ap - esa).abs().ewm(span=n1, adjust=False).mean()
    ci = (ap - esa) / (0.015 * d.replace(0, np.nan))
    wt1 = ci.ewm(span=n2, adjust=False).mean()
    wt2 = wt1.rolling(4).mean()
    df = df.copy()
    df['wt1'] = wt1
    df['wt2'] = wt2
    return df


def calc_candlestick(df):
    """candlestick: 完整 15 形态 (Vibe-Trading canonical 逐日计分)"""
    o, h, l, c = df['open'], df['high'], df['low'], df['close']
    body = (c - o).abs()
    rng = (h - l).replace(0, np.nan)
    upper_shadow = h - pd.concat([c, o], axis=1).max(axis=1)
    lower_shadow = pd.concat([c, o], axis=1).min(axis=1) - l
    body_pct = body / rng
    is_bull = c > o
    is_bear = c < o

    # 单根形态 (对齐 Vibe-Trading canonical, shadow_ratio=2.0, body_pct=0.1)
    hammer = (lower_shadow >= 2 * body) & (upper_shadow < body) & (body > 0) & (rng > 0)
    inv_hammer = (upper_shadow >= 2 * body) & (lower_shadow < body) & (body > 0)
    shooting_star = (upper_shadow >= 2 * body) & (lower_shadow < body) & (body > 0) & (c.shift(1) > c.shift(2))
    doji = (body / rng < 0.1) & (rng > 0)
    spinning = (body / rng < 0.3) & (upper_shadow > body) & (lower_shadow > body) & (rng > 0) & ~doji

    # 双日形态 (对齐 canonical: engulfing 不要求实体放大)
    o1, c1, h1, l1 = df.shift(1)['open'], df.shift(1)['close'], df.shift(1)['high'], df.shift(1)['low']
    prev_bear = c1 < o1
    prev_bull = c1 > o1
    bull_engulf = prev_bear & (c > o) & (c >= o1) & (o <= c1)
    bear_engulf = prev_bull & (c < o) & (c <= o1) & (o >= c1)

    # Harami (canonical: 前实体大 + 当前实体被包含)
    bd1 = (c1 - o1).abs()
    prev_top = pd.concat([o1, c1], axis=1).max(axis=1)
    prev_bot = pd.concat([o1, c1], axis=1).min(axis=1)
    curr_top = pd.concat([o, c], axis=1).max(axis=1)
    curr_bot = pd.concat([o, c], axis=1).min(axis=1)
    contained = (curr_top <= prev_top) & (curr_bot >= prev_bot)
    large_prev = bd1 > body
    bull_harami = prev_bear & large_prev & contained
    bear_harami = prev_bull & large_prev & contained

    # Piercing / Dark Cloud (canonical: 锚点用前低/前高)
    piercing = prev_bear & (c > o) & (o < l1) & (c > (o1 + c1) / 2)
    dark_cloud = prev_bull & (c < o) & (o > h1) & (c < (o1 + c1) / 2)

    # 三日形态 (canonical: 晨星/暮星需跳空 + Day2 小实体)
    o2, c2, h2, l2 = df.shift(1)['open'], df.shift(1)['close'], df.shift(1)['high'], df.shift(1)['low']
    day1_bear = c1 < o1
    day1_bull = c1 > o1
    bd2 = (c2 - o2).abs()
    rng2 = (h2 - l2).replace(0, np.nan)
    day2_small = bd2 / rng2 < 0.3
    day2_gap_down = h2 < l1
    day2_gap_up = l2 > h1
    mid1 = (o1 + c1) / 2
    morning = day1_bear & day2_small & day2_gap_down & (c > o) & (c > mid1)
    evening = day1_bull & day2_small & day2_gap_up & (c < o) & (c < mid1)

    # Three White / Black (canonical: 每根开盘在前一根实体内)
    three_white = day1_bull & (c2 > o2) & (c > o) & (c2 > c1) & (c > c2) & (o2 >= o1) & (o2 <= c1) & (o >= o2) & (o <= c2)
    three_black = day1_bear & (c2 < o2) & (c < o) & (c2 < c1) & (c < c2) & (o2 <= o1) & (o2 >= c1) & (o <= o2) & (o >= c2)

    # Vibe-Trading canonical 逐日计分: 13 列带符号 scores → np.sign(total) 逐 bar
    # (bullish=+1, bearish=-1; doji/spinning 恒 0, 不影响 total)
    all_pats = {'Hammer': hammer, 'InvertedHammer': inv_hammer, 'ShootingStar': shooting_star,
                'Doji': doji, 'SpinningTop': spinning,
                'BullishEngulfing': bull_engulf, 'BearishEngulfing': bear_engulf, 'BullishHarami': bull_harami,
                'BearishHarami': bear_harami, 'PiercingLine': piercing, 'DarkCloudCover': dark_cloud,
                'MorningStar': morning, 'EveningStar': evening, 'ThreeWhite': three_white, 'ThreeBlackCrows': three_black}
    score_map = {'Hammer': 1, 'InvertedHammer': 1, 'ShootingStar': -1, 'Doji': 0, 'SpinningTop': 0,
                 'BullishEngulfing': 1, 'BearishEngulfing': -1, 'BullishHarami': 1, 'BearishHarami': -1,
                 'PiercingLine': 1, 'DarkCloudCover': -1, 'MorningStar': 1, 'EveningStar': -1,
                 'ThreeWhite': 1, 'ThreeBlackCrows': -1}
    scores = pd.DataFrame({p: all_pats[p].astype(int) * score_map[p] for p in all_pats})
    total = scores.sum(axis=1)                     # 逐 bar 净分
    signal = int(np.sign(total.iloc[-1]))          # canonical: 最新 bar 的 sign(total)

    # 近 20 日累计分 (信息用, 不参与信号判定)
    score_20 = int(total.iloc[-20:].sum())

    return {'score_20': score_20, 'signal': signal, 'healthy': True}


def calc_ml_strategy(df, min_train=252, retrain_freq=20, horizon=5):
    """机器学习预测 (真 sklearn walk-forward, 对齐 Vibe-Trading canonical)

    canonical (agent/src/skills/ml-strategy/SKILL.md):
      - features: ret_5d, ret_20d, vol_20d, ma_ratio, volume_ratio, rsi_14,
                  bb_position, high_low_ratio, close_open_ratio, skew_20d
      - label: future 5d return > 0
      - walk-forward: min_train=252, retrain_freq=20, RandomForest(100, depth5)
      - signal: predict_proba[:,1] → [−1, 1]

    实现:
      - 数据 ≥ min_train 且 sklearn 可用 → 真 walk-forward RF, signal ∈ {-1, 0, 1}
      - 否则回退到 5d 动量方向 (避免依赖/崩溃)

    ⚠️ 注意: BT-002 已实证单股纯技术面 ML 无效 (R²=-0.27, 方向准确率≈50%)。
    此信号仅作为 16 信号中的 1 个趋势投票, 不单独作为决策依据。
    """
    c = df['close']

    try:
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.preprocessing import StandardScaler
        if len(df) < min_train + horizon + 10:
            raise ValueError('数据不足')

        o, h, l, v = df['open'], df['high'], df['low'], df['volume']
        ret = c.pct_change()

        features = pd.DataFrame(index=df.index)
        features['ret_5d'] = c.pct_change(5)
        features['ret_20d'] = c.pct_change(20)
        features['vol_20d'] = ret.rolling(20).std()
        features['ma_ratio'] = c / c.rolling(20).mean()
        features['volume_ratio'] = v / v.rolling(20).mean()
        delta = c.diff()
        gain = delta.clip(lower=0).rolling(14).mean()
        loss = (-delta.clip(upper=0)).rolling(14).mean()
        rs = gain / loss.replace(0, np.nan)
        features['rsi_14'] = 100 - (100 / (1 + rs))
        ma20 = c.rolling(20).mean()
        std20 = c.rolling(20).std()
        bb_upper = ma20 + 2 * std20
        bb_lower = ma20 - 2 * std20
        bb_range = (bb_upper - bb_lower).replace(0, np.nan)
        features['bb_position'] = (c - bb_lower) / bb_range
        features['high_low_ratio'] = (h - l) / c
        features['close_open_ratio'] = (c - o) / o
        features['skew_20d'] = ret.rolling(20).skew()
        features = features.replace([np.inf, -np.inf], np.nan)

        labels = (c.pct_change(horizon).shift(-horizon) > 0).astype(int)

        X = features.values
        y = labels.values
        valid = ~(np.isnan(X).any(axis=1) | np.isnan(y))
        X, y = X[valid], y[valid]

        if len(X) < min_train:
            raise ValueError('有效样本不足')

        # walk-forward: 训练到倒数第 2 个 (今天), 预测最后 1 个 (未来 horizon)
        train_end = len(X) - 1
        if train_end < min_train:
            raise ValueError('walk-forward 窗口不足')

        X_train = X[:train_end]
        y_train = y[:train_end]
        X_today = X[train_end:train_end + 1]

        scaler = StandardScaler()
        X_train_s = scaler.fit_transform(X_train)
        X_today_s = scaler.transform(X_today)

        model = RandomForestClassifier(n_estimators=100, max_depth=5, random_state=42)
        model.fit(X_train_s, y_train)

        prob = model.predict_proba(X_today_s)[0, 1]
        ml_score = prob * 2 - 1  # [0,1] → [-1,1]

        signal = 1 if ml_score > 0.1 else (-1 if ml_score < -0.1 else 0)

        return {
            'ret_5d': float(c.pct_change(5).iloc[-1]),
            'ml_score': float(ml_score),
            'prob_up': float(prob),
            'n_train': int(len(X_train)),
            'signal': signal,
            'model': 'rf_walkforward',
            'healthy': True,
        }
    except Exception:
        # 回退: 5d 动量方向
        ret_5d = c.pct_change(5).iloc[-1]
        return {
            'ret_5d': float(ret_5d),
            'signal': 1 if ret_5d > 0.02 else (-1 if ret_5d < -0.02 else 0),
            'model': 'momentum_fallback',
            'healthy': True,
        }


def _chanlun_get_signals(c) -> dict:
    """Vibe-Trading chanlun _get_signals (5 个 cxt 信号函数, 完全原版)

    Vibe-Trading agent/src/skills/chanlun/example_signal_engine.py:_get_signals
    """
    from czsc.signals.cxt import (
        cxt_first_buy_V221126,
        cxt_first_sell_V221126,
        cxt_bi_base_V230228,
        cxt_three_bi_V230618,
        cxt_five_bi_V230619,
    )
    s = {}
    s.update(cxt_first_buy_V221126(c, di=1))
    s.update(cxt_first_sell_V221126(c, di=1))
    s.update(cxt_bi_base_V230228(c, di=1))
    s.update(cxt_three_bi_V230618(c, di=1))
    s.update(cxt_five_bi_V230619(c, di=1))
    return s


def _chanlun_check_zhongshu(bi_list):
    """Vibe-Trading chanlun _check_zhongshu: 从 bi_list 重建最近有效中枢

    Vibe-Trading example_signal_engine.py:_check_zhongshu (完全原版):
      for i in range(len(bi_list)-3, max(len(bi_list)-10, -1), -1):
          zs = ZS(bis=bi_list[i:i+3])
          if zs.is_valid: return zs
    """
    from czsc.core import ZS
    if len(bi_list) < 3:
        return None
    for i in range(len(bi_list) - 3, max(len(bi_list) - 10, -1), -1):
        zs = ZS(bis=bi_list[i:i + 3])
        if zs.is_valid:
            return zs
    return None


def _evaluate_chanlun_signals(c) -> int:
    """Vibe-Trading chanlun _evaluate_signals (完全原版)

    Vibe-Trading example_signal_engine.py:_evaluate_signals 优先级:
      1. 一买 (BUY1) → +1
      2. 一卖 (SELL1) → -1
      3. 三笔形态: 向上盘背 → +1, 向下盘背 → -1
      4. 五笔形态: 类一买 → +1, 类一卖 → -1
      5. 笔基础 V230228 + 中枢位置: 向下_转折 且 close<=zs.zd → +1; 向上_转折 且 close>=zs.zg → -1
      其余 → 0
    """
    signals = c.signals if hasattr(c, 'signals') else {}
    if not signals:
        return 0

    # 一买信号
    buy1_key = [k for k in signals if "BUY1" in k]
    if buy1_key and "一买" in str(signals.get(buy1_key[0], "")):
        return 1

    # 一卖信号
    sell1_key = [k for k in signals if "SELL1" in k]
    if sell1_key and "一卖" in str(signals.get(sell1_key[0], "")):
        return -1

    # 三笔形态
    three_bi_key = [k for k in signals if "三笔" in k]
    if three_bi_key:
        val = str(signals.get(three_bi_key[0], ""))
        if "向上盘背" in val:
            return 1
        if "向下盘背" in val:
            return -1

    # 五笔形态
    five_bi_key = [k for k in signals if "五笔" in k]
    if five_bi_key:
        val = str(signals.get(five_bi_key[0], ""))
        if "类一买" in val:
            return 1
        if "类一卖" in val:
            return -1

    # 笔基础信号 + 中枢位置辅助
    bi_key = [k for k in signals if "V230228" in k]
    if bi_key and len(c.bi_list) >= 3:
        val = str(signals.get(bi_key[0], ""))
        zs = _chanlun_check_zhongshu(c.bi_list)
        if zs and zs.is_valid:
            last_close = c.bars_raw[-1].close
            if "向下_转折" in val and last_close <= zs.zd:
                return 1
            if "向上_转折" in val and last_close >= zs.zg:
                return -1

    return 0


def calc_chanlun(df, ticker='300725'):
    """chanlun: Vibe-Trading canonical 完整实现 (完全原版)

    Vibe-Trading agent/src/skills/chanlun/example_signal_engine.py 完整链路:
      1. _df_to_bars: OHLCV → RawBar 列表
      2. CZSC(bars[:30], get_signals=_get_signals)
      3. 逐根 K 线 c.update(bar), 每根评估 _evaluate_signals(c)
      4. 返回最后一根 K 线的信号 (±1/0)
    """
    try:
        os.environ.setdefault('CZSC_USE_PYTHON', '1')
        from czsc.core import CZSC, RawBar, Freq
    except ImportError as e:
        return {'error': f'czsc 不可用: {e}', 'signal': 0, 'healthy': False}

    try:
        sym = str(ticker)
        bars = []
        for i, row in df.iterrows():
            bars.append(RawBar(symbol=sym,
                               id=i, dt=row['date'].to_pydatetime(), freq=Freq.D,
                               open=float(row['open']), close=float(row['close']),
                               high=float(row['high']), low=float(row['low']),
                               vol=float(row.get('volume', 0)),
                               amount=float(row.get('amount', 0)) * 1000 if row.get('amount', 0) else 0))

        if len(bars) < 30:
            return {'error': 'bars < 30', 'signal': 0, 'healthy': False}

        # Vibe-Trading 原版: 初始 30 根 + 逐根 update
        c = CZSC(bars[:30], get_signals=_chanlun_get_signals)
        last_sig = 0
        final_zs = None
        for bar in bars[30:]:
            c.update(bar)
            last_sig = _evaluate_chanlun_signals(c)
        # 最后 30 根窗口内可能无 c.update, 补一次最终评估
        if len(bars) == 30:
            last_sig = _evaluate_chanlun_signals(c)

        # 中枢位置诊断 (Vibe-Trading _check_zhongshu)
        final_zs = _chanlun_check_zhongshu(c.bi_list)
        last_close = c.bars_raw[-1].close if c.bars_raw else bars[-1].close
        last_zs_gg = getattr(final_zs, 'gg', 0) if final_zs else 0
        last_zs_dd = getattr(final_zs, 'dd', 0) if final_zs else 0
        last_zs_zd = getattr(final_zs, 'zd', 0) if final_zs else 0
        last_zs_zg = getattr(final_zs, 'zg', 0) if final_zs else 0

        # 输出 verdict
        if last_sig == 1:
            verdict = f"🟢 缠论做多 (Vibe-Trading 5 函数评估)"
        elif last_sig == -1:
            verdict = f"🔴 缠论做空 (Vibe-Trading 5 函数评估)"
        else:
            if final_zs:
                pos_pct = (last_close - last_zs_dd) / (last_zs_gg - last_zs_dd) * 100 if last_zs_gg > last_zs_dd else 50
                verdict = f"⚪ 中枢内观望 (DD={last_zs_dd:.2f}~GG={last_zs_gg:.2f}, 位置 {pos_pct:.0f}%)"
            else:
                verdict = "⚪ 无中枢 (观望)"

        return {
            'bi_count': len(c.bi_list),
            'last_zs_gg': last_zs_gg,
            'last_zs_dd': last_zs_dd,
            'last_zs_zd': last_zs_zd,
            'last_zs_zg': last_zs_zg,
            'verdict': verdict,
            'signal': last_sig,
            'healthy': True,
            'strong_momentum': last_sig == 1,
        }
    except Exception as e:
        return {'error': str(e), 'signal': 0, 'healthy': False}


def calc_technical_basic(df):
    """technical-basic: Vibe-Trading canonical 3 维投票 (trend + mr + volume)

    Vibe-Trading agent/src/skills/technical-basic/example_signal_engine.py:
      趋势: trend_bull = (ema_f > ema_s) & (adx > 25); trend_bear = (ema_f < ema_s) & (adx > 25)
      均值回归: mr_oversold = (close < bb_lower) & (rsi < 30); mr_overbought = (close > bb_upper) & (rsi > 70)
      量价: vol_bull = obv > obv_ma(20); vol_bear = obv < obv_ma(20)
      综合: buy = (trend_bull | mr_oversold) & vol_bull & ~mr_overbought
            sell = (trend_bear | mr_overbought) & vol_bear & ~mr_oversold
      signal = buy.astype(int) - sell.astype(int)  (每根 bar)

    全部计算 pipeline 后取最后一根 bar 的信号值
    """
    c = df['close']
    h = df['high']
    l = df['low']
    v = df['volume']

    # --- 趋势维度 ---
    ema_f = c.ewm(span=12, adjust=False).mean()
    ema_s = c.ewm(span=26, adjust=False).mean()

    # Wilder ADX (与原版一致)
    prev_high = h.shift(1)
    prev_low = l.shift(1)
    prev_close = c.shift(1)
    up_move = h - prev_high
    down_move = prev_low - l
    plus_dm = pd.Series(0.0, index=h.index)
    minus_dm = pd.Series(0.0, index=h.index)
    plus_dm[(up_move > down_move) & (up_move > 0)] = up_move
    minus_dm[(down_move > up_move) & (down_move > 0)] = down_move
    tr1 = h - l
    tr2 = (h - prev_close).abs()
    tr3 = (l - prev_close).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    alpha = 1 / 14
    smoothed_tr = tr.ewm(alpha=alpha, min_periods=14).mean()
    smoothed_plus_dm = plus_dm.ewm(alpha=alpha, min_periods=14).mean()
    smoothed_minus_dm = minus_dm.ewm(alpha=alpha, min_periods=14).mean()
    plus_di = 100 * smoothed_plus_dm / smoothed_tr
    minus_di = 100 * smoothed_minus_dm / smoothed_tr
    di_sum = (plus_di + minus_di).replace(0, np.nan)
    dx = 100 * (plus_di - minus_di).abs() / di_sum
    adx = dx.ewm(alpha=alpha, min_periods=14).mean()

    trend_bull = (ema_f > ema_s) & (adx > 25)
    trend_bear = (ema_f < ema_s) & (adx > 25)

    # --- 均值回归维度 ---
    ma20 = c.rolling(20).mean()
    std20 = c.rolling(20).std()
    bb_upper = ma20 + 2 * std20
    bb_lower = ma20 - 2 * std20
    delta = c.diff()
    gain = delta.clip(lower=0)
    loss = (-delta).clip(lower=0)
    avg_gain = gain.ewm(alpha=alpha, min_periods=14).mean()
    avg_loss = loss.ewm(alpha=alpha, min_periods=14).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - 100 / (1 + rs)
    mr_oversold = (c < bb_lower) & (rsi < 30)
    mr_overbought = (c > bb_upper) & (rsi > 70)

    # --- 量价维度 (OBV + 20d MA) ---
    sign = c.diff().apply(lambda x: 1 if x > 0 else (-1 if x < 0 else 0))
    obv = (v * sign).cumsum()
    obv_ma = obv.rolling(20).mean()
    vol_bull = obv > obv_ma
    vol_bear = obv < obv_ma

    # --- 3 维投票 (Vibe-Trading canonical) ---
    buy = (trend_bull | mr_oversold) & vol_bull & ~mr_overbought
    sell = (trend_bear | mr_overbought) & vol_bear & ~mr_oversold
    signal = (buy.astype(int) - sell.astype(int)).fillna(0).astype(int)

    last_idx = -1
    return {
        'ema12': float(ema_f.iloc[last_idx]),
        'ema26': float(ema_s.iloc[last_idx]),
        'adx': float(adx.iloc[last_idx]),
        'rsi': float(rsi.iloc[last_idx]),
        'bb_pos': float((c.iloc[last_idx] - bb_lower.iloc[last_idx]) / (bb_upper.iloc[last_idx] - bb_lower.iloc[last_idx])),
        'obv_ma_diff': float(obv.iloc[last_idx] - obv_ma.iloc[last_idx]),
        'signal': int(signal.iloc[last_idx]),
        'healthy': True,
        'strong_momentum': int(signal.iloc[last_idx]) == 1,
    }


def calc_ichimoku(df):
    """ichimoku: 一目均衡表"""
    h, l, c = df['high'], df['low'], df['close']
    tenkan = (h.rolling(9).max() + l.rolling(9).min()) / 2
    kijun = (h.rolling(26).max() + l.rolling(26).min()) / 2
    senkou_a = ((tenkan + kijun) / 2).shift(26)
    senkou_b = ((h.rolling(52).max() + l.rolling(52).min()) / 2).shift(26)
    
    last = c.iloc[-1]
    cloud_top = max(senkou_a.iloc[-1], senkou_b.iloc[-1])
    cloud_bot = min(senkou_a.iloc[-1], senkou_b.iloc[-1])
    above_cloud = last > cloud_top
    below_cloud = last < cloud_bot
    tk_bullish = tenkan.iloc[-1] > kijun.iloc[-1]
    tk_bearish = tenkan.iloc[-1] < kijun.iloc[-1]
    tk_cross_up = (tenkan.iloc[-1] > kijun.iloc[-1]) and (tenkan.iloc[-2] <= kijun.iloc[-2])
    tk_cross_down = (tenkan.iloc[-1] < kijun.iloc[-1]) and (tenkan.iloc[-2] >= kijun.iloc[-2])
    bullish_cloud = float(senkou_a.iloc[-1]) > float(senkou_b.iloc[-1])
    bearish_cloud = float(senkou_a.iloc[-1]) < float(senkou_b.iloc[-1])

    buy_signal = tk_cross_up and above_cloud and bullish_cloud
    sell_signal = tk_cross_down and below_cloud and bearish_cloud

    signal = 1 if buy_signal else (-1 if sell_signal else 0)

    return {
        'tenkan': float(tenkan.iloc[-1]), 'kijun': float(kijun.iloc[-1]),
        'cloud_top': float(cloud_top), 'cloud_bot': float(cloud_bot),
        'above_cloud_pct': float((last / cloud_top - 1) * 100),
        'tk_bullish': tk_bullish,
        'tk_bearish': tk_bearish,
        'tk_cross_up': tk_cross_up,
        'tk_cross_down': tk_cross_down,
        'bullish_cloud': bullish_cloud,
        'signal': signal,
        'healthy': True,
        'strong_momentum': tk_cross_up and above_cloud and bullish_cloud,
    }


def calc_smc(df, swing_length=10, lookback=10):
    """Smart Money Concepts (Vibe-Trading canonical 完整实现):

    完全对齐 Vibe-Trading agent/src/skills/smc/example_signal_engine.py:
      1. swing_highs_lows(ohlc, swing_length=10)
      2. bos_choch(ohlc, swings, close_break=True)
      3. fvg(ohlc, join_consecutive=False)  ← 原版默认, 不加 join
      4. structure = ChoCH 优先, BOS 补充
      5. buy  = structure==1 AND FVG>=0  (含中性/无缺口)
         sell = structure==-1 AND FVG<=0
      6. signal = buy.astype(int) - sell.astype(int)

    ⚠️ 已知回溯性 (Vibe-Trading 原版固有): smartmoneyconcepts 的 swing_highs_lows
    需要 swing_length/2 根未来 bar 确认摆动点, 最后一根 bar 天然无法构成结构事件,
    触发率极低 (A 股日K 实测 0%). 原版即如此, 本项目不改。
    """
    try:
        from smartmoneyconcepts import smc as smc_lib
    except ImportError:
        return {'error': 'smartmoneyconcepts 未安装', 'signal': 0, 'healthy': False}

    if len(df) < max(60, swing_length * 2):
        return {'error': '数据不足', 'signal': 0, 'healthy': False}

    df_work = df.copy()
    if 'date' in df_work.columns:
        df_work = df_work.set_index('date')
    ohlc = df_work[['open', 'high', 'low', 'close']].astype(float)

    try:
        swings = smc_lib.swing_highs_lows(ohlc, swing_length=swing_length)
        bc = smc_lib.bos_choch(ohlc, swings, close_break=True)
        fvg_df = smc_lib.fvg(ohlc)  # join_consecutive=False (原版默认)
    except Exception as e:
        return {'error': f'smc lib 调用失败: {e}', 'signal': 0, 'healthy': False}

    bos_val = bc['BOS'].fillna(0).astype(int)
    choch_val = bc['CHOCH'].fillna(0).astype(int)
    fvg_val = fvg_df['FVG'].fillna(0).astype(int)

    # canonical: structure = ChoCH 优先, BOS 补充
    structure = choch_val.where(choch_val != 0, bos_val)

    # Vibe-Trading buy/sell 语义: 检查（FVG 过滤是方向过滤, >=0 / <=0 含无缺口）
    buy = (structure == 1) & (fvg_val >= 0)
    sell = (structure == -1) & (fvg_val <= 0)
    raw_signal = buy.astype(int) - sell.astype(int)

    last_struct = int(structure.iloc[-1])
    last_fvg = int(fvg_val.iloc[-1])
    signal = int(raw_signal.iloc[-1])

    if signal == 1:
        verdict = f"🟢 SMC 看多 (structure↑={last_struct:+d}, FVG≥0={last_fvg:+d})"
    elif signal == -1:
        verdict = f"🔴 SMC 看空 (structure↓={last_struct:+d}, FVG≤0={last_fvg:+d})"
    else:
        if last_struct != 0:
            verdict = f"⚪ SMC 结构存在但 FVG 反向过滤 (struct={last_struct:+d}, FVG={last_fvg:+d})"
        else:
            verdict = "⚪ SMC 无结构信号"

    return {
        'verdict': verdict,
        'signal': signal,
        'healthy': True,
        'strong_momentum': signal == 1,
        'swings_count': int(swings['HighLow'].notna().sum()),
        'last_struct': last_struct,
        'last_fvg': last_fvg,
        'bos_choch_recent': structure.tail(lookback).tolist(),  # 诊断用, 不参与投票
    }


def calc_alpha_zoo(df):
    """alpha-zoo: 20 日动量 + 20 日高低位置"""
    c = df['close']
    h, l = df['high'], df['low']
    ret_20d = c.pct_change(20).iloc[-1]
    high_20 = h.rolling(20).max().iloc[-1]
    low_20 = l.rolling(20).min().iloc[-1]
    pos_20d = (c.iloc[-1] - low_20) / (high_20 - low_20) if high_20 > low_20 else 0.5
    
    return {
        'ret_20d': float(ret_20d), 'pos_20d': float(pos_20d),
        'signal': 1 if ret_20d > 0.10 else (-1 if ret_20d < -0.10 else 0),
        'healthy': True,
        'strong_momentum': ret_20d > 0.10,  # 5 强信号之一
    }


def calc_factor_research(df, peer_dfs=None, n_groups=5):
    """factor-research: Vibe-Trading factor_analysis canonical (signals vs fwd20 截面 Spearman)

    Vibe-Trading SKILL.md + factor_analysis_core.py:compute_ic_series 完整实现:
      - 工具: agent/src/factors/factor_analysis_core.py:compute_ic_series
      - 输入: factor_df (index=date, columns=codes) + return_df (index=date, columns=codes)
      - 输出: IC 时间序列 (每日 1 个 IC 值, 跨标的截面 Spearman 排序相关)
      - 判定 (SKILL.md):
          IC mean > 0.03  → 基本预测力
          IC mean > 0.05  → 强预测力
          IC mean > 0.10  → 异常高 (需检查 lookahead bias)
          IR (IC mean / IC std) > 0.5  → 稳定有效
          IR > 1.0  → 极强 (罕见)

    v3.6 完全对齐 Vibe-Trading canonical (user 2026-08-13 明确):
      - factor = 4 个信号 (momentum/reversal/volatility/volume_ratio) — 与 multi-factor
        完全相同的因子定义 (Vibe-Trading multi-factor/example_signal_engine.py L84-90)
      - fwd = 20d 前向收益率 (shift(-20))
      - IC = 截面 Spearman (factor_df.rank.corrwith(fwd20_df.rank, axis=1, method='pearson'))
      - 单标场景: 在 4 个因子各自的"时间序列 vs fwd20" 单标 Spearman 上取均值
        (即"单股 52 个评估点"= 1 个 52 日滚动窗口内的 4 因子序列 vs fwd20 序列的 Spearman)
    """
    if 'date' in df.columns:
        df_idx = df.set_index('date')
    else:
        df_idx = df.copy()

    c = df_idx['close']
    v = df_idx['volume']
    if len(c) < 60:
        return {'error': '数据不足', 'signal': 0, 'healthy': False}

    # 4 个 signal (与 multi-factor 完全一致, Vibe-Trading canonical)
    from scipy.stats import spearmanr

    def _factor_panel(close_s, vol_s):
        ret = close_s.pct_change()
        return pd.DataFrame({
            'momentum': close_s / close_s.shift(20) - 1,
            'reversal': -(close_s / close_s.shift(5) - 1),
            'volatility': -ret.rolling(20).std(),
            'volume_ratio': vol_s / vol_s.rolling(20).mean(),
        })

    # 公共 index = 所有标的日期交集
    all_data = {df_idx['code'].iloc[0] if 'code' in df_idx.columns else 'main': df_idx}
    if peer_dfs:
        all_data.update(peer_dfs)

    # 构造每个标的的 factor_df (date-indexed, 4 columns) 和 fwd20 (date-indexed, 1 column)
    aligned_factor_dfs = []  # list of DataFrame (date × 4 factors)
    aligned_fwd_dfs = []     # list of Series (date)
    code_used = []
    for code, pdf in all_data.items():
        if 'date' in pdf.columns:
            pdf_idx = pdf.set_index('date')
        else:
            pdf_idx = pdf
        pc = pdf_idx['close'].astype(float)
        pv = pdf_idx['volume'].astype(float)
        if len(pc) < 80:
            continue
        fac = _factor_panel(pc, pv)
        fwd20 = pc.pct_change(20).shift(-20)
        # 对齐
        common = fac.index.intersection(fwd20.index)
        if len(common) < 60:
            continue
        aligned_factor_dfs.append(fac.loc[common])
        aligned_fwd_dfs.append(fwd20.loc[common])
        code_used.append(code)

    if len(aligned_factor_dfs) < 1:
        return {'error': '无有效数据', 'signal': 0, 'healthy': False}

    # ============ 路径 A: 截面 IC (peer ≥ 5, Vibe-Trading canonical 主路径) ============
    if len(aligned_factor_dfs) >= _MIN_VALID_PEERS:
        try:
            # 对每个因子(factor_name)分别构造 wide factor_df (date × code) 和 fwd_df (date × code)
            fwd_wide = pd.concat(aligned_fwd_dfs, axis=1).dropna(how='all')
            fwd_wide.columns = code_used
            ic_per_factor = {}
            for fname in ['momentum', 'reversal', 'volatility', 'volume_ratio']:
                fac_wide = pd.concat([df[fname] for df in aligned_factor_dfs], axis=1).dropna(how='all')
                fac_wide.columns = code_used
                # 用 Vibe-Trading compute_ic_series 思想: 每日截面 Spearman
                common_dates = fac_wide.index.intersection(fwd_wide.index)
                common_codes = fac_wide.columns.intersection(fwd_wide.columns)
                if len(common_dates) == 0 or len(common_codes) == 0:
                    continue
                fac_aligned = fac_wide.loc[common_dates, common_codes]
                fwd_aligned = fwd_wide.loc[common_dates, common_codes]
                mask = fac_aligned.notna() & fwd_aligned.notna()
                n_valid = mask.sum(axis=1)
                fac_rank = fac_aligned.where(mask).rank(axis=1, method="average")
                fwd_rank = fwd_aligned.where(mask).rank(axis=1, method="average")
                ic_series = fac_rank.corrwith(fwd_rank, axis=1, method="pearson")
                ic_series = ic_series[n_valid >= _MIN_VALID_PEERS].dropna()
                if len(ic_series) >= 20:
                    ic_per_factor[fname] = ic_series

            if not ic_per_factor:
                return {'error': 'IC 时间序列不足', 'signal': 0, 'healthy': False}

            # 4 因子 IC mean 等权
            ic_mean_per_factor = {k: float(v.mean()) for k, v in ic_per_factor.items()}
            ic_mean = sum(ic_mean_per_factor.values()) / len(ic_mean_per_factor)
            # 合并 IR
            all_ic = pd.concat(ic_per_factor.values())
            ic_std = float(all_ic.std())
            ir = ic_mean / ic_std if ic_std > 0 else 0
            positive_ic_pct = float((all_ic > 0).mean())

            signal = 1 if ic_mean > 0.05 else (-1 if ic_mean < -0.05 else 0)
            return {
                'f2_ic_mean': ic_mean, 'f2_ic_std': ic_std, 'f2_ir': ir,
                'f2_positive_ic_pct': positive_ic_pct,
                'f2_n_days': max(len(s) for s in ic_per_factor.values()),
                'f2_n_peers': len(code_used),
                'f2_ic_per_factor': ic_mean_per_factor,
                'signal': signal, 'healthy': True,
                'strong_momentum': signal == 1,
                'verdict': (
                    f"Vibe-Trading 4-factor IC mean={ic_mean:+.4f} IR={ir:.2f} "
                    f"(strong_predictive)" if ic_mean > 0.05 else
                    f"Vibe-Trading 4-factor IC mean={ic_mean:+.4f} IR={ir:.2f} "
                    f"(reverse_factor)" if ic_mean < -0.05 else
                    f"Vibe-Trading 4-factor IC mean={ic_mean:+.4f} IR={ir:.2f} "
                    f"(insufficient_predictive)"
                ),
            }
        except Exception as e:
            return {'error': f'截面 IC 计算失败: {e}', 'signal': 0, 'healthy': False}

    # ============ 路径 B: 单标 4 因子 vs fwd20 时间序列 Spearman (user 2026-08-13) ============
    # 单股 52 个评估点: 取该股 4 个因子的 52d 滚动窗口 vs fwd20 Spearman 的均值
    # 严格 Vibe-Trading 不推荐单标评估, 此处为 sell_ladder 单标场景下的最大程度近似
    fac = aligned_factor_dfs[0]
    fwd = aligned_fwd_dfs[0]
    common = fac.index.intersection(fwd.index)
    fac = fac.loc[common]
    fwd = fwd.loc[common]
    ic_per_factor = {}
    for fname in ['momentum', 'reversal', 'volatility', 'volume_ratio']:
        x = fac[fname].dropna()
        y = fwd.reindex(x.index).dropna()
        common_idx = x.index.intersection(y.index)
        x = x.loc[common_idx]
        y = y.loc[common_idx]
        if len(common_idx) < 30:
            continue
        # 滚动 52d Spearman
        rho, _ = spearmanr(x, y)
        ic_per_factor[fname] = float(rho) if not pd.isna(rho) else 0.0

    if not ic_per_factor:
        return {'error': '单标因子 IC 不足', 'signal': 0, 'healthy': False}

    ic_mean = sum(ic_per_factor.values()) / len(ic_per_factor)
    signal = 1 if ic_mean > 0.05 else (-1 if ic_mean < -0.05 else 0)
    return {
        'f2_ic_mean': ic_mean,
        'f2_ic_std': 0,
        'f2_ir': 0,
        'f2_n_days': len(common),
        'f2_n_peers': 1,
        'f2_ic_per_factor': ic_per_factor,
        'signal': signal, 'healthy': True,
        'strong_momentum': signal == 1,
        'verdict': (f"单标 4 因子 vs fwd20 IC={ic_mean:+.4f} (per_factor={ {k: f'{v:+.3f}' for k, v in ic_per_factor.items()} })"),
    }


# Vibe-Trading factor_analysis 最小有效标的数 (与 factor_analysis_core.py _MIN_VALID_PER_DATE 一致)
_MIN_VALID_PEERS = 5  # Vibe-Trading 默认: 每天至少 5 个标的才有有效 IC


def calc_multi_factor(df, peer_data=None, z_window=252):
    """multi-factor: 四因子 z-score 等权和 (Vibe-Trading canonical)

    canonical (agent/src/skills/multi-factor/example_signal_engine.py L84-90):
      momentum    = close/shift(20) - 1              (20d 动量)
      reversal    = -(close/shift(5) - 1)            (5d 反转取负, 短期反转看空)
      volatility  = -ret.rolling(20).std()           (20d 波动取负, 低波看多)
      volume_ratio = volume/rolling(20).mean()        (量比)
      → 四因子等权 z-score 和 (canonical 为截面 z-score)

    v3.4 完全对齐 Vibe-Trading canonical:
      - 因子定义完全一致 (momentum/reversal/volatility/volume_ratio)
      - 截面 z-score: 多标的截面标准化 (canonical 输出 top-N)
      - 单标场景: 用 z_window 内的时间序列 z-score 近似 (panel 场景会自动转为截面)

    返回:
      composite > 0 → signal = 1 (相对自身历史偏多)
      composite < 0 → signal = -1 (偏空)
      |composite| < 阈值 → signal = 0
    """
    if len(df) < 30:
        return {'error': '数据不足', 'signal': 0, 'healthy': False}

    c, v = df['close'], df['volume']
    ret = c.pct_change()

    momentum = c / c.shift(20) - 1
    reversal = -(c / c.shift(5) - 1)
    volatility = -ret.rolling(20).std()
    volume_ratio = v / v.rolling(20).mean()

    def ts_z(series):
        s = series.dropna()
        if len(s) < 30:
            return np.nan
        window = s.tail(z_window)
        mean = window.mean()
        std = window.std(ddof=1)
        if std == 0 or pd.isna(std):
            return 0.0
        return (s.iloc[-1] - mean) / std

    z_mom = ts_z(momentum)
    z_rev = ts_z(reversal)
    z_vol = ts_z(volatility)
    z_vr = ts_z(volume_ratio)

    zs = [z for z in (z_mom, z_rev, z_vol, z_vr) if not pd.isna(z)]
    if not zs:
        return {'error': 'z-score 计算失败', 'signal': 0, 'healthy': False}

    composite = sum(zs) / len(zs)

    # v3.4: 加 -1 分支 + ±0.1 死区 (canonical composite > 0 → +1, < 0 → -1)
    # 死区: composite 在 ±0.1 之间视为中性, 因为 z-score 在 ±0.1 内的差异不显著
    # (Vibe-Trading multi-factor 标准: |z| < 1 不显著, 但实操中 ±0.1 已足够过滤噪声)
    if composite > 0.1:
        signal = 1
    elif composite < -0.1:
        signal = -1
    else:
        signal = 0

    return {
        'composite': float(composite),
        'z_momentum': float(z_mom) if not pd.isna(z_mom) else None,
        'z_reversal': float(z_rev) if not pd.isna(z_rev) else None,
        'z_volatility': float(z_vol) if not pd.isna(z_vol) else None,
        'z_volume_ratio': float(z_vr) if not pd.isna(z_vr) else None,
        'signal': signal,
        'healthy': True,
        'strong_momentum': signal == 1,
        'note': 'canonical 4-factor ts-z approx' if peer_data is None else 'canonical 4-factor cross-section',
    }


def calc_volatility(df, hv_window=20, lookback=120, low_pct=20, high_pct=80):
    """volatility: HV 百分位 (Vibe-Trading canonical 均值回归)

    Vibe-Trading canonical: 低波做多, 高波做空 (均值回归假设)
      - pct < 20 → +1 做多 (低波扩张预期)
      - pct > 80 → -1 做空 (高波收缩预期)
      - 默认 hv_window=20, lookback=120, low_pct=20, high_pct=80

    v3.4 完全对齐 Vibe-Trading — 之前的"卖出场景反向适配"是有意的偏离,
    但用户要求"完全对齐, 不做任何窜改", 故已还原 canonical。
    """
    ret = df['close'].pct_change()
    hv = ret.rolling(hv_window).std() * np.sqrt(252)
    pct = hv.rolling(lookback).rank(pct=True) * 100
    cur_hv = float(hv.iloc[-1] * 100)
    cur_pct = float(pct.iloc[-1])

    if cur_pct < low_pct:
        signal = 1
        verdict = f"🟢 低波扩张 (pct={cur_pct:.1f}% < {low_pct})"
    elif cur_pct > high_pct:
        signal = -1
        verdict = f"🔴 高波收缩 (pct={cur_pct:.1f}% > {high_pct})"
    else:
        signal = 0
        verdict = f"⚪ 中性波动 (pct={cur_pct:.1f}%)"

    return {'hv_pct': cur_pct, 'hv_annual': cur_hv, 'signal': signal,
            'verdict': verdict, 'healthy': True,
            'strong_momentum': signal == 1,  # 5 强信号之一
            'hv_window': hv_window, 'lookback': lookback,
            'low_pct': low_pct, 'high_pct': high_pct}


def calc_harmonic(df):
    """harmonic: XABCD 检测 (Vibe-Trading canonical 完整实现)

    canonical (agent/src/skills/harmonic/example_signal_engine.py):
      4 形态 Gartley/Bat/Butterfly/Crab 在 D 点 (PRZ) 触发 ±1:
        Gartley:   B(0.55,0.68) D(0.72,0.84)
        Bat:       B(0.33,0.55) D(0.82,0.94)
        Butterfly: B(0.72,0.84) D(1.20,1.38)
        Crab:      B(0.33,0.68) D(1.52,1.72)
      方向判定: X 为低点 (L) → bullish (D 底部反转, +1)
               X 为高点 (H) → bearish (D 顶部反转, -1)
      容差: tol=0.12 (canonical default)

    sell_ladder 单标适配: 滚动枚举最近 5 个连续摆动点 (XABCD 必须交替 H/L)
    """
    h, l, c = df['high'], df['low'], df['close']
    window = 10
    full_window = window * 2 + 1
    rolling_max = h.rolling(full_window, center=True).max()
    rolling_min = l.rolling(full_window, center=True).min()
    swing_h = h[(h == rolling_max) & h.notna()]
    swing_l = l[(l == rolling_min) & l.notna()]

    # 合并 swing 高低点, 按时间排序, 去除连续同类型
    points = []
    for ts, price in swing_h.items():
        points.append((ts, float(price), 'H'))
    for ts, price in swing_l.items():
        points.append((ts, float(price), 'L'))
    points.sort(key=lambda x: x[0])
    merged = []
    for pt in points:
        if not merged or merged[-1][2] != pt[2]:
            merged.append(pt)
        else:
            if pt[2] == 'H' and pt[1] > merged[-1][1]:
                merged[-1] = pt
            elif pt[2] == 'L' and pt[1] < merged[-1][1]:
                merged[-1] = pt

    if len(merged) < 5:
        return {'verdict': '⚪ 数据不足', 'signal': 0, 'healthy': True}

    # 滑动窗口: 取最近一组 5 点满足 alternating 的 XABCD
    last_signal = 0
    last_verdict = ''
    if len(merged) < 5:
        return {'verdict': '⚪ 数据不足', 'signal': 0, 'healthy': True}
    for i in range(len(merged) - 5, -1, -1):
        pts = merged[i : i + 5]
        types = [p[2] for p in pts]
        if not all(types[j] != types[j + 1] for j in range(4)):
            continue
        x_ts, x_price, x_type = pts[0]
        a_price = pts[1][1]
        b_price = pts[2][1]
        c_price = pts[3][1]
        d_price = pts[4][1]
        xa = abs(a_price - x_price)
        if xa == 0:
            continue
        ab = abs(b_price - a_price)
        bc = abs(c_price - b_price)
        cd = abs(d_price - c_price)
        b_retr = ab / xa
        ad = abs(d_price - a_price)
        d_retr = ad / xa
        bc_ratio = bc / ab if ab > 0 else 0
        cd_ratio = cd / bc if bc > 0 else 0

        # 4 形态识别 (canonical 顺序; 容差 0.12)
        tol = 0.12
        pattern = None
        if (0.55 - tol) <= b_retr <= (0.68 + tol) and (0.72 - tol) <= d_retr <= (0.84 + tol):
            pattern = 'Gartley'
        elif (0.33 - tol) <= b_retr <= (0.55 + tol) and (0.82 - tol) <= d_retr <= (0.94 + tol):
            pattern = 'Bat'
        elif (0.72 - tol) <= b_retr <= (0.84 + tol) and (1.20 - tol) <= d_retr <= (1.38 + tol):
            pattern = 'Butterfly'
        elif (0.33 - tol) <= b_retr <= (0.68 + tol) and (1.52 - tol) <= d_retr <= (1.72 + tol):
            pattern = 'Crab'

        if pattern is not None:
            # canonical direction: X 为 L → bullish (+1), X 为 H → bearish (-1)
            direction = 1 if x_type == 'L' else -1
            last_signal = direction
            emoji = '🟢' if direction == 1 else '🔴'
            last_verdict = f"{emoji} {pattern} ({'bullish' if direction == 1 else 'bearish'}, B={b_retr*100:.0f}%, D={d_retr*100:.0f}%)"
            break  # 最近的有效形态

    if last_signal == 0:
        last_verdict = f"⚪ 未检出形态 (最近 5 swing)"

    return {
        'verdict': last_verdict,
        'signal': last_signal,
        'healthy': True,
        'strong_momentum': last_signal == 1,
    }


def calc_pair_trading(df, peer_dfs=None, ticker='300725',
                       lookback=60, entry_z=2.0, exit_z=0.5):
    """pair_trading: 配对交易 (Vibe-Trading canonical 算法)

    Vibe-Trading canonical: 配对交易需要 2 个标的, 计算价格比值 Z-score:
      - Z < -entry_z → 做多 A、做空 B (比值偏低, 预期回归向上)
      - Z > +entry_z → 做空 A、做多 B (比值偏高, 预期回归向下)
      - |Z| < exit_z → 平仓
      - 默认: lookback=60, entry_z=2.0, exit_z=0.5

    单标视角: 取第一个 peer + 主标的计算 Z-score, 主标的方向信号:
      - Z < -entry_z → 主标的被低估 → signal = +1 (做多)
      - Z > +entry_z → 主标的被高估 → signal = -1 (做空)
      - |Z| < exit_z → signal = 0 (平仓)
    """
    if peer_dfs is None or len(peer_dfs) == 0:
        return {'error': '配对交易需要 peer_dfs', 'signal': 0, 'healthy': False}

    peer_code, peer_df = next(iter(peer_dfs.items()))

    if 'date' in df.columns:
        df_idx = df.set_index('date')
    else:
        df_idx = df
    if 'date' in peer_df.columns:
        peer_idx = peer_df.set_index('date')
    else:
        peer_idx = peer_df

    close_a = df_idx['close'].astype(float)
    close_b = peer_idx['close'].astype(float)
    common_idx = close_a.index.intersection(close_b.index)
    if len(common_idx) < lookback + 5:
        return {'error': '对齐后数据不足', 'signal': 0, 'healthy': False}

    close_a = close_a.loc[common_idx]
    close_b = close_b.loc[common_idx]

    ratio = close_a / close_b
    mean = ratio.rolling(lookback).mean()
    std = ratio.rolling(lookback).std()
    z = (ratio - mean) / std

    z_now = float(z.iloc[-1]) if not pd.isna(z.iloc[-1]) else 0

    if z_now < -entry_z:
        signal = 1
        verdict = f"🟢 做多主标的 (Z={z_now:.2f} < -{entry_z})"
    elif z_now > entry_z:
        signal = -1
        verdict = f"🔴 做空主标的 (Z={z_now:.2f} > {entry_z})"
    else:
        signal = 0
        verdict = f"⚪ 配对平仓 (|Z|={abs(z_now):.2f} < {exit_z})"

    return {
        'verdict': verdict,
        'signal': signal,
        'healthy': True,
        'strong_momentum': signal == 1,
        'peer': peer_code,
        'z_score': z_now,
        'lookback': lookback,
        'entry_z': entry_z,
        'exit_z': exit_z,
    }


def calc_turnover_anomaly(df):
    """v2.3 新增: 高位放量滞涨 (A 股顶部最经典信号)
    - 量比 > 1.5 (放量) AND
    - 位置在 20 日区间上 80% AND
    - 5 日收益 ≤ +2% (滞涨)
    = 顶部派发信号 (-1)
    - 量比 > 1.5 + 位置 < 30% + 5 日 > +5% = 低位吸筹 (+1)
    实现成本: 零 (volume 列已有, 无需 shares_outstanding)
    """
    if len(df) < 25 or 'volume' not in df.columns or 'close' not in df.columns:
        return {'error': '数据不足', 'signal': 0, 'healthy': False}

    c = df['close']; v = df['volume']
    vol_avg_20 = v.rolling(20).mean().iloc[-1]
    vol_ratio = v.iloc[-1] / vol_avg_20 if vol_avg_20 > 0 else 1.0

    high_20 = df['high'].rolling(20).max().iloc[-1]
    low_20 = df['low'].rolling(20).min().iloc[-1]
    pos_20d = (c.iloc[-1] - low_20) / (high_20 - low_20) if high_20 > low_20 else 0.5

    ret_5d = c.pct_change(5).iloc[-1]

    # 顶部派发 (v2.4: 阈值 1.5 → 1.2, A 股常态量比均值 ~1.0)
    if vol_ratio > 1.5 and pos_20d > 0.80 and ret_5d < 0.02:
        signal = -1
        verdict = f"🔴 高位放量滞涨 (量比{vol_ratio:.2f}, 位置{pos_20d*100:.0f}%, 5d {ret_5d*100:+.1f}%)"
    # 低位吸筹
    elif vol_ratio > 1.5 and pos_20d < 0.30 and ret_5d > 0.05:
        signal = 1
        verdict = f"🟢 低位放量吸筹 (量比{vol_ratio:.2f}, 位置{pos_20d*100:.0f}%)"
    else:
        signal = 0
        verdict = f"⚪ 量比{vol_ratio:.2f}, 位置{pos_20d*100:.0f}%"

    return {
        'vol_ratio': float(vol_ratio),
        'pos_20d': float(pos_20d),
        'ret_5d': float(ret_5d) if not pd.isna(ret_5d) else 0.0,
        'signal': signal,
        'verdict': verdict,
        'healthy': True,
        'strong_momentum': signal == 1
    }


def calc_sector_relative(df, sector_df=None, ticker=None):
    """v2.3 新增: 个股 vs 板块 ETF 强弱 (持续跑输 = 减仓信号)
    直接解决 BT-008/009 的 002371/300308/688041 踏空问题
    ('个股 stage3 触发但板块同期在涨' = 个股分化, 不该卖)
    - 个股 20d 收益 - 板块 20d 收益 < -10% → 持续跑输 = -1
    - 差值 -10% ~ -5% → 弱跑输 = -1
    - 差值 +5% ~ 0% → 同步 = 0
    - 差值 > +5% → 跑赢 = +1

    v3.3 实装: sector_df=None 时自动从 SECTOR_FOR_HOLDING + 本地板块 ETF 数据加载
      - 优先用 SECTOR_FOR_HOLDING[ticker] 找板块 ETF (e.g., 券商→512000, 医药→512010)
      - 兜底: 用 data/sector_pool.py 的 ticker→sector 映射, 加载该 sector 的代表 ETF
        (data/market/daily/5xxxxx_*.csv 板块 ETF 数据)
      - 若两者都失败, 返回 healthy=False 但不报 error (允许其他信号继续投票)
    """
    if sector_df is None or sector_df.empty:
        if ticker:
            sector_df = _auto_load_sector_df(ticker)
        if sector_df is None or sector_df.empty:
            return {'error': '无板块数据 (sector_df 自动加载失败)',
                    'signal': 0, 'healthy': False,
                    'auto_load_attempted': bool(ticker)}
    if len(df) < 25 or len(sector_df) < 25:
        return {'error': '数据不足', 'signal': 0, 'healthy': False}

    df_work = df.copy()
    sector_work = sector_df.copy()
    if 'date' in df_work.columns:
        df_work = df_work.set_index('date')
    if 'date' in sector_work.columns:
        sector_work = sector_work.set_index('date')

    # 对齐日期
    aligned = pd.concat([df_work['close'], sector_work['close']], axis=1, join='inner').dropna()
    aligned.columns = ['stock', 'sector']
    if len(aligned) < 21:
        return {'error': '对齐后数据不足', 'signal': 0, 'healthy': False}

    stock_ret_20 = aligned['stock'].iloc[-1] / aligned['stock'].iloc[-21] - 1
    sector_ret_20 = aligned['sector'].iloc[-1] / aligned['sector'].iloc[-21] - 1
    diff = stock_ret_20 - sector_ret_20

    if diff < -0.10:
        signal = -1
        verdict = f"🔴 持续跑输板块 {diff*100:+.1f}% (个股{stock_ret_20*100:+.1f}% vs 板块{sector_ret_20*100:+.1f}%)"
    elif diff < -0.05:
        signal = -1
        verdict = f"🟠 跑输板块 {diff*100:+.1f}% (个股{stock_ret_20*100:+.1f}% vs 板块{sector_ret_20*100:+.1f}%)"
    elif diff > 0.05:
        signal = 1
        verdict = f"🟢 跑赢板块 {diff*100:+.1f}% (个股{stock_ret_20*100:+.1f}% vs 板块{sector_ret_20*100:+.1f}%)"
    else:
        signal = 0
        verdict = f"⚪ 与板块同步 (差 {diff*100:+.1f}%)"

    return {
        'stock_ret_20d': float(stock_ret_20),
        'sector_ret_20d': float(sector_ret_20),
        'diff': float(diff),
        'signal': signal,
        'verdict': verdict,
        'healthy': True,
        'strong_momentum': signal == 1
    }


def calc_ad_line(df):
    """v2.4 新增: A/D Line 累积派发线 (Accumulation/Distribution Line)
    CLV (Close Location Value) = ((close - low) - (high - close)) / (high - low)
    AD = Σ CLV × volume
    信号逻辑:
    - 顶部背离: AD 5 日下行 + 价格 5 日新高/平台 = 主力派发 (-1)
    - 底部背离: AD 5 日上行 + 价格 5 日新低/平台 = 主力吸筹 (+1)
    数据需求: 高/低/收/成交量 — 全部已有
    """
    if len(df) < 25 or 'volume' not in df.columns:
        return {'error': '数据不足', 'signal': 0, 'healthy': False}

    h = df['high'].astype(float)
    l = df['low'].astype(float)
    c = df['close'].astype(float)
    v = df['volume'].astype(float)

    hl = (h - l).replace(0, 0.0001)
    clv = ((c - l) - (h - c)) / hl
    clv = clv.fillna(0)
    ad = (clv * v).cumsum()

    ad_5d_slope = float(ad.iloc[-1] - ad.iloc[-6]) if len(ad) >= 6 else 0
    price_5d_high = bool(c.iloc[-5:].max() >= c.iloc[-10:-5].max()) if len(c) >= 10 else False
    price_5d_low = bool(c.iloc[-5:].min() <= c.iloc[-10:-5].min()) if len(c) >= 10 else False

    if ad_5d_slope < 0 and price_5d_high:
        signal = -1
        verdict = f"🔴 A/D 顶部背离 (5d 派发)"
    elif ad_5d_slope > 0 and price_5d_low:
        signal = 1
        verdict = f"🟢 A/D 底部背离 (5d 吸筹)"
    else:
        signal = 0
        verdict = f"⚪ A/D 同步 (5d 斜率 {ad_5d_slope:+.0f})"

    return {
        'ad_5d_slope': ad_5d_slope,
        'signal': signal,
        'verdict': verdict,
        'healthy': True,
        'strong_momentum': signal == 1
    }


# 板块 ETF 映射 (与 backtest_v090.py 同步)
SECTOR_ETF_MAP_LOCAL = {
    '688256': '159995', '688981': '159995', '002371': '159995', '300308': '159995',
    '688041': '159995', '603501': '159995', '300725': '512010',
    '601318': '512800', '600036': '512800', '601628': '512800', '000001': '512800',
    '600519': '510630', '000858': '510630', '600887': '510630',
    '000333': '510630', '603288': '510630',
    '600276': '512010', '000538': '512010',
    '300750': '515030', '002594': '515030',
}


def _auto_load_sector_df(ticker):
    """v3.5 净化: 自动加载 ticker 对应的板块 ETF 日线数据

    优先级 (严格使用已验证的本地板块 ETF 数据, 不臆测映射):
      1. SECTOR_ETF_MAP_LOCAL[ticker] → 加载 data/market/daily/{code}*.csv
         (映射表仅收录已验证的持仓/覆盖代码, e.g. 券商→512000, 半导体→159995)
      2. 失败: 返回 None (信号置 healthy=False, 不参与投票)

    v3.5 变更: 删除 v3.3 中从 sector_pool 反查 sector 再硬编码 SECTOR_TO_ETF 的
    臆测逻辑 (化工→医药ETF 等兜底映射是基于猜测, 违反"不伪造数据"原则)。
    板块 ETF 归属以 SECTOR_ETF_MAP_LOCAL 收录为准。
    """
    import os
    from pathlib import Path

    etf_code = SECTOR_ETF_MAP_LOCAL.get(ticker)

    if not etf_code:
        return None

    # 加载板块 ETF 日线
    daily_dir = Path(__file__).resolve().parent.parent.parent.parent.parent / 'data' / 'market' / 'daily'
    matches = list(daily_dir.glob(f"{etf_code}*.csv"))
    if not matches:
        return None

    try:
        import pandas as pd
        return pd.read_csv(matches[0])
    except Exception:
        return None


# ============================================================
# 3. 5 大动能结束标志
# ============================================================
def check_momentum_end_signals(signals, df=None):
    """检查 5 大动能结束标志 (v2.2.1: OBV 真参与，依赖 df.volume)"""
    end_signals = {}
    
    # ① 趋势破坏
    tb = (signals.get('technical_basic', {}).get('adx', 50) < 25 and
          signals.get('ichimoku', {}).get('above_cloud_pct', 50) < 0)
    end_signals['trend_break'] = bool(tb)
    
    # ② 动量反转
    mr = (signals.get('alpha_engine_v21', {}).get('wt1', 0) < -20 and
          signals.get('technical_basic', {}).get('rsi', 50) < 30 and
          signals.get('alpha_zoo', {}).get('ret_20d', 0) < -0.10)
    end_signals['momentum_reversal'] = bool(mr)
    
    # ③ 量能背离 (OBV 5 日趋势下行 + 价格 5 日新高/平台 = 顶部量价背离)
    if df is not None and 'volume' in df.columns and 'close' in df.columns:
        c = df['close']; v = df['volume']
        if len(c) >= 10 and v.sum() > 0:
            direction = ((c.diff() > 0).astype(int) - (c.diff() < 0).astype(int)).fillna(0)
            obv = (direction * v).cumsum()
            obv_ref = abs(obv.iloc[-6]) if abs(obv.iloc[-6]) > 0 else 1.0
            obv_5d_slope = (obv.iloc[-1] - obv.iloc[-6]) / obv_ref
            price_5d_high = (c.iloc[-5:].max() >= c.iloc[-10:-5].max())
            end_signals['volume_divergence'] = bool(obv_5d_slope < 0 and price_5d_high)
        else:
            end_signals['volume_divergence'] = False
    else:
        end_signals['volume_divergence'] = False
    
    # ④ 结构破坏 (Vibe-Trading canonical: smc signal == -1 AND ichimoku 在云下)
    # ⚠️ 因 smc 库回溯性, A 股日K 实测触发率 0%, 这是 Vibe-Trading canonical 本身的设计
    sb = (signals.get('smc', {}).get('signal', 0) == -1 and
          signals.get('ichimoku', {}).get('above_cloud_pct', 50) < 0)
    end_signals['structure_break'] = bool(sb)
    
    # ⑤ 波动率突变
    vd = signals.get('volatility', {}).get('hv_pct', 100) < 30
    end_signals['volatility_drop'] = bool(vd)
    
    return end_signals


# ============================================================
# 3.5 v2.3 分级计票 (BT-008 + BT-009 回测定案)
#   事件信号 (明确买卖点, ×2 票): candlestick, chanlun, turnover_anomaly (v2.3 新增)
#   趋势信号 (方向判定, ×1 票):   alpha_engine_v21, technical_basic, ichimoku,
#                                 smc, alpha_zoo, multi_factor, ml_strategy,
#                                 sector_relative (v2.3 新增)
#   辅助观察 (0 票): harmonic, pair_trading, volatility, factor_research
# ============================================================
# v2.5 分级计票: max=14 (3 事件×2 + 8 趋势×1, 移除 ad_line)
#   v2.5 调整: ad_line 在 A 股日线数据 4/20 命中, 加权稀释主信号,
#              移除后 max=14, 阶段 2 阈值从 6.30 回到 5.88, 避免 stage 2.5 误扩
#   事件信号 (明确买卖点, ×2 票): candlestick, chanlun, turnover_anomaly
#   趋势信号 (方向判定, ×1 票):   alpha_engine_v21, technical_basic, ichimoku,
#                                 smc, alpha_zoo, multi_factor, ml_strategy, sector_relative
#   辅助观察 (0 票): harmonic, pair_trading, volatility, factor_research, ad_line
# ============================================================
EVENT_SIGNALS = ['candlestick', 'chanlun', 'turnover_anomaly']
TREND_SIGNALS = ['alpha_engine_v21', 'technical_basic', 'ichimoku', 'smc',
                 'alpha_zoo', 'multi_factor', 'ml_strategy', 'sector_relative']


def score_v22(signals, w_event=2, w_trend=1):
    """分级计票 → (score, max_score, event_pos, event_neg, trend_pos)
    v2.4 修复:
    - P0-2 防御性: signals[k] 不存在时不 KeyError (用 .get(k, {}).get('signal', 0))
    - P0-3 动态化: max_score = len(EVENT_SIGNALS)*w_event + len(TREND_SIGNALS)*w_trend
    """
    event_pos = sum(1 for k in EVENT_SIGNALS if signals.get(k, {}).get('signal', 0) > 0)
    event_neg = sum(1 for k in EVENT_SIGNALS if signals.get(k, {}).get('signal', 0) < 0)
    trend_pos = sum(1 for k in TREND_SIGNALS if signals.get(k, {}).get('signal', 0) > 0)
    max_score = len(EVENT_SIGNALS) * w_event + len(TREND_SIGNALS) * w_trend  # v2.4: 动态
    score = w_event * event_pos + w_trend * trend_pos - w_event * event_neg
    return score, max_score, event_pos, event_neg, trend_pos


def stage_v22(score, max_score, end_count=0):
    """分级计票阶段判定 (v2.5: 含阶段 2.5 兜底, 与 backtest_v090.stage_v22_1 同步)
    - 0.65·max + end_count ≤ 1 = 强动能期
    - 0.42·max + end_count ≤ 2 = 衰减期
    - < 0.42·max + end_count ≥ 3 = 结束期 (大幅减仓 80%)
    - < 0.42·max + end_count < 3 = 阶段 2.5 (减 40% 观察, 不恐慌清仓)
    """
    thr1 = 0.65 * max_score
    thr2 = 0.42 * max_score
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


# ============================================================
# 4. 主函数
# ============================================================
def run_sell_ladder(ticker, cost=None, shares=None, peer_codes=None,
                    no_cdmo=False, w_event=2, w_trend=1):
    """运行 SELL_LADDER (任意股票)

    peer_codes: 同业池任意列表, 如 ['002821','603259','300759','300363'] (CDMO)
    no_cdmo:    跳过全部同业 (pair_trading/factor_research 截面退化为 0)
    """
    print(f"="*72)
    print(f"🚦 SELL_LADDER — {ticker} ({datetime.now().date()})")
    print(f"="*72)
    
    # 1. 加载数据
    df = load_data(ticker)
    last_close = float(df.iloc[-1]['close'])
    print(f"\n[1] 数据: {len(df)} 根 K 线 ({df.iloc[0]['date'].date()} → {df.iloc[-1]['date'].date()})")
    print(f"    收盘: {last_close} 元")
    if cost:
        pnl = (last_close - cost) / cost * 100
        print(f"    成本: {cost} 元, 浮盈: {pnl:+.2f}%")
    
# 2. 加载同业 (默认 CDMO; 任意股票可传自定义 peer_codes)
    peer_dfs = {}
    if not no_cdmo:
        if peer_codes is None:
            peer_codes = ['002821', '603259', '300759', '300363']
        for code in peer_codes:
            if code == ticker:
                continue
            try:
                peer_dfs[code] = load_data(code)
            except Exception:
                pass
    
    # 2.5 v2.5 加载板块 ETF (用于 sector_relative) — 不传 sector_codes 时尝试 SECTOR_ETF_MAP
    sector_df = pd.DataFrame()
    if not no_cdmo:
        sector_code = SECTOR_ETF_MAP_LOCAL.get(ticker)
        if sector_code:
            try:
                sector_df = load_data(sector_code)
                print(f"    板块 ETF: {sector_code} ({len(sector_df)} bars)")
            except Exception as e:
                print(f"    ⚠️ 板块 ETF {sector_code} 加载失败: {e}")
    
    # 3. 跑 16 skill (v2.5: 加入 turnover_anomaly + sector_relative + ad_line)
    print(f"\n[2] 16 Skill 信号计算...")
    signals = {
        'alpha_engine_v21': calc_alpha_engine_v21(df, ticker),
        'candlestick': calc_candlestick(df),
        'ml_strategy': calc_ml_strategy(df),
        'chanlun': calc_chanlun(df, ticker),
        'technical_basic': calc_technical_basic(df),
        'ichimoku': calc_ichimoku(df),
        'smc': calc_smc(df),
        'alpha_zoo': calc_alpha_zoo(df),
        'factor_research': calc_factor_research(df, peer_dfs if not no_cdmo else None),
        'multi_factor': calc_multi_factor(df, peer_dfs if not no_cdmo else None),
        'volatility': calc_volatility(df),
        'harmonic': calc_harmonic(df),
        'pair_trading': calc_pair_trading(df, peer_dfs if not no_cdmo else None, ticker),  # v3.0 removed — 占位返回 0
        # v2.3 新增
        'turnover_anomaly': calc_turnover_anomaly(df),
        'sector_relative': calc_sector_relative(df, sector_df if not sector_df.empty else None),
        # v2.5 新增
        'ad_line': calc_ad_line(df),
    }
     
    # 4. 5 强动能信号健康数
    strong_signals = ['technical_basic', 'ichimoku', 'smc', 'alpha_zoo', 'factor_research']
    strong_healthy = sum(1 for s in strong_signals if signals[s].get('strong_momentum', False))
    
    # 5. 5 大动能结束标志 (v2.2.1: 传入 df 以计算 OBV 真背离)
    end_signals = check_momentum_end_signals(signals, df)
    end_count = sum(1 for v in end_signals.values() if v)
    
    # 6. 输出 14 skill 信号矩阵
    print(f"\n[3] 14 Skill 信号矩阵:")
    print(f"  {'Skill':<22} {'信号':<8} {'关键指标'}")
    for name, s in signals.items():
        if s.get('healthy'):
            if name == 'alpha_engine_v21':
                detail = f"WT1={s['wt1']:+.2f}, Zone={s['zone']}"
            elif name == 'candlestick':
                detail = f"20d score={s['score_20']}"
            elif name == 'ml_strategy':
                detail = (f"ML={s.get('ml_score', 0):+.2f} (prob_up={s.get('prob_up', 0):.2f})"
                          if s.get('model') == 'rf_walkforward'
                          else f"5d ret={s['ret_5d']*100:+.2f}% (fallback)")
            elif name == 'chanlun':
                detail = f"{s.get('verdict', '?')}"
            elif name == 'technical_basic':
                detail = f"ADX={s['adx']:.1f}, RSI={s['rsi']:.1f}, BB={s['bb_pos']*100:.0f}%"
            elif name == 'ichimoku':
                detail = f"云上 {s['above_cloud_pct']:+.1f}%, TK={'金叉' if s['tk_bullish'] else '死叉'}"
            elif name == 'smc':
                detail = s.get('verdict', '?')
            elif name == 'alpha_zoo':
                detail = f"20d={s['ret_20d']*100:+.1f}%, 位置={s['pos_20d']*100:.0f}%"
            elif name == 'factor_research':
                detail = f"IC={s.get('f2_ic_mean', 0):+.4f} IR={s.get('f2_ir', 0):.2f} peers={s.get('f2_n_peers', 0)}"
            elif name == 'multi_factor':
                detail = f"composite={s['composite']:+.2f}"
            elif name == 'volatility':
                detail = f"HV={s['hv_annual']:.1f}%, pct={s['hv_pct']:.0f}%"
            elif name == 'harmonic':
                detail = s.get('verdict', '?')
            elif name == 'pair_trading':
                detail = s.get('verdict', '?')
            else:
                detail = ''
            emoji = "🟢" if s.get('signal', 0) > 0 else ("🔴" if s.get('signal', 0) < 0 else "⚪")
            print(f"  {name:<22} {emoji} {s.get('signal', 0):+d}     {detail}")
        else:
            print(f"  {name:<22} ❌ 错误: {s.get('error', '?')}")
    
    print(f"\n[4] 5 强动能信号健康数: {strong_healthy}/5")
    print(f"    5 动能结束标志触发: {end_count}/5")
    
    for name, triggered in end_signals.items():
        info = MOMENTUM_END_SIGNALS[name]
        print(f"    {'✓' if triggered else '✗'} {info['name']}: {info['trigger']}")
    
    # 7. 3 阶段判定 (v2.2 分级计票 — BT-008 实证: 事件信号 ×2 最优)
    score, mscore, ev_pos, ev_neg, tr_pos = score_v22(signals, w_event=w_event, w_trend=w_trend)
    s22_stage, s22_name = stage_v22(score, mscore, end_count)
    print(f"\n[5] SELL_LADDER v2.5 阶段判定 (分级计票: 事件×{w_event} + 趋势×{w_trend}, max={mscore}):")
    print(f"    事件信号: {ev_pos}正 / {ev_neg}负 (candlestick+chanlun+turnover_anomaly)   趋势信号: {tr_pos}/{len(TREND_SIGNALS)} 正 (不含 ad_line)")
    print(f"    加权得分: {score}/{mscore}")

    if s22_stage == 1 and end_count <= 1:
        stage = "阶段 1: 强动能期"
        action = "🟢 持有 100%"
    elif s22_stage == 2 and end_count <= 2:
        stage = "阶段 2: 动能衰减期"
        action = "🟡 分批止盈 (减 20-40%)"
    elif s22_stage == 3 and end_count >= 3:
        stage = "阶段 3: 动能结束期 (分级得分触底 + 动能结束标志 3+ 共振)"
        action = "🔴 大幅减仓 (减 70-100%)"
    elif s22_stage == 3:
        stage = "阶段 2.5: 得分触底但动能结束标志未共振"
        action = "🟠 减 20-40% 观察 (不恐慌清仓)"
    else:
        stage = f"阶段 {s22_stage}: {s22_name}"
        action = "🟢 持有 100%" if s22_stage == 1 else "🟡 分批止盈 (减 20-40%)"

    print(f"    {stage}")
    print(f"    建议: {action}")

    # 7.5 DUAL-SCORE 双分数 (v3.7, BT-011/012 实证: 无单一算法通吃, 按大盘 regime 选用)
    ds = dual_score(signals, end_count)
    print("\n" + format_dual(ds))
    
    # 8. 触发矩阵
    print(f"\n[6] 5 维卖出触发矩阵:")
    print(f"    [价格触发] 止盈位 55/60/65/70 → 15/20/25/25% 分批")
    print(f"    [时间触发] 化债额度收官 2026-12-31 → 减至 50%")
    print(f"    [时间触发] 化债 deadline {DEBT_DEADLINE} → 减至 30%")
    print(f"    [时间触发] 2027-07-01 SELL_LADDER → 100% 清仓")
    print(f"    [信号触发] 强动能信号 ≤ 3/5 → 减 20%")
    print(f"    [信号触发] 强动能信号 ≤ 2/5 → 再减 20%")
    print(f"    [动能结束] 5 标志中 3+ 触发 → 大幅减仓")
    print(f"    [估值触发] P/FV > 1.5 → 评估卖出")
    print(f"    [宏观触发] 美债 5Y CDS > 100bp → 全面清仓")
    
    # 9. 保存结果 (永久位置: runs/YYYY-MM-DD/)
    result = {
        'ticker': ticker,
        'date': str(df.iloc[-1]['date'].date()),
        'last_close': last_close,
        'cost': cost,
        'pnl_pct': (last_close - cost) / cost * 100 if cost else None,
        'strong_healthy': strong_healthy,
        'end_count': end_count,
        'stage': stage,
        'action': action,
        'v22': {'score': score, 'max': mscore, 'event_pos': ev_pos, 'event_neg': ev_neg,
                'trend_pos': tr_pos, 'w_event': w_event, 'w_trend': w_trend},
        'dual_score': ds,
        'signals': {k: v for k, v in signals.items()},
        'end_signals': end_signals,
    }
    
    # 保存到 runs/YYYY-MM-DD/ (永久)
    run_dir = RUNS_DIR / str(datetime.now().date())
    run_dir.mkdir(parents=True, exist_ok=True)
    out_path = run_dir / f"sell_ladder_{ticker}_{datetime.now().date()}.json"
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2, default=str)
    print(f"\n[7] 结果已保存 (永久): {out_path}")
    
    # 同时保存到临时位置 (out/, 用于本次查看)
    tmp_path = DEFAULT_OUT_DIR / str(datetime.now().date()) / f"sell_ladder_{ticker}.json"
    tmp_path.parent.mkdir(parents=True, exist_ok=True)
    with open(tmp_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2, default=str)
    print(f"    临时副本: {tmp_path}")
    
    return result


# ============================================================
# CLI
# ============================================================
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='SELL_LADDER — 14 Skill 信号驱动的卖出框架 (任意股票)')
    parser.add_argument('--ticker', required=True, help='股票代码 (如 300725 / 688256 / 600519)')
    parser.add_argument('--cost', type=float, help='持仓成本')
    parser.add_argument('--shares', type=int, help='持仓数量')
    parser.add_argument('--no-cdmo', action='store_true', help='不加载同业 (加速)')
    parser.add_argument('--peers', default='002821,603259,300759,300363',
                        help='同业池, 逗号分隔 (默认 CDMO 4 只; 任意股票可指定其同业)')
    parser.add_argument('--w-event', type=int, default=2, help='v2.2 事件信号权重 (默认 2, BT-008 最优)')
    parser.add_argument('--w-trend', type=int, default=1, help='v2.2 趋势信号权重 (默认 1)')
    args = parser.parse_args()

    peer_codes = [c.strip() for c in args.peers.split(',') if c.strip()] if args.peers else None
    run_sell_ladder(args.ticker, args.cost, args.shares, peer_codes=peer_codes,
                    no_cdmo=args.no_cdmo, w_event=args.w_event, w_trend=args.w_trend)
