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

# 向后兼容 (旧路径, 用于读取已存在的数据)
OUT_DIR = SELL_LADDER_DIR / "_legacy_out"  # 旧数据迁移后, 此目录可删除

# 默认临时输出目录 (CLI 可覆盖)
DEFAULT_OUT_DIR = Path(__file__).resolve().parents[3] / "out" / "sell_ladder_runs"

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
def calc_alpha_engine_v21(df, ticker='300725'):
    """alpha-engine-v21: LazyBear WaveTrend (任意 ticker, 现场计算, 确定性)

    v2.3 修复: 原实现 signal 恒 0 (只输出 zone 诊断, 从不投票), 导致该信号
    在计票中永远弃权。现按 LazyBear WaveTrend 经典语义投票:
      - 金叉: WT1 上穿 WT2 且 WT1 从负区/低位回升 → +1 (看多)
      - 死叉: WT1 下穿 WT2 且 WT1 从正区/高位回落 → -1 (看空)
      - 无交叉时: 趋势同向 (WT1 > WT2 且 WT1 > 0 → +1; WT1 < WT2 且 WT1 < 0 → -1)
      - 其余 → 0 (观望)
    阈值为 V21 惯用 zone 分界 (WT1=±20 强弱区, ±60 超买超卖区)。
    """
    if 'wt1' not in df.columns or 'wt2' not in df.columns:
        df = _compute_wt(df)
    # 取最近两根确认交叉, 避免仅看最后一根误判
    prev = df.iloc[-2] if len(df) >= 2 else df.iloc[-1]
    last = df.iloc[-1]
    wt1, wt2 = last.get('wt1', 0), last.get('wt2', 0)
    pwt1, pwt2 = prev.get('wt1', 0), prev.get('wt2', 0)

    for k in ('wt1', 'wt2'):
        if pd.isna(locals().get(k)): pass
    if pd.isna(wt1): wt1 = 0
    if pd.isna(wt2): wt2 = 0
    if pd.isna(pwt1): pwt1 = 0
    if pd.isna(pwt2): pwt2 = 0

    if wt1 >= 60: zone = "OB≥60"
    elif wt1 >= 40: zone = "H 40-60"
    elif wt1 >= 20: zone = "M+ 20-40"
    elif wt1 >= 0: zone = "N+ 0-20"
    elif wt1 >= -20: zone = "N- -20-0"
    elif wt1 >= -40: zone = "M- -40-20"
    elif wt1 >= -60: zone = "L -60-40"
    else: zone = "OS≤-60"

    # 金叉/死叉判定
    cross_up = (pwt1 <= pwt2) and (wt1 > wt2)
    cross_down = (pwt1 >= pwt2) and (wt1 < wt2)

    # 经典 LazyBear 语义: 低位金叉看多, 高位死叉看空
    if cross_up and pwt1 < 20:
        signal = 1
        verdict = f"🟢 WT金叉 (WT1 {pwt1:.1f}→{wt1:.1f}, {zone})"
    elif cross_down and pwt1 > -20:
        signal = -1
        verdict = f"🔴 WT死叉 (WT1 {pwt1:.1f}→{wt1:.1f}, {zone})"
    elif wt1 > wt2 and wt1 > 0:
        signal = 1
        verdict = f"🟢 WT多头趋势 (WT1 {wt1:.1f} > WT2 {wt2:.1f}, {zone})"
    elif wt1 < wt2 and wt1 < 0:
        signal = -1
        verdict = f"🔴 WT空头趋势 (WT1 {wt1:.1f} < WT2 {wt2:.1f}, {zone})"
    else:
        signal = 0
        verdict = f"⚪ WT观望 (WT1 {wt1:.1f}, WT2 {wt2:.1f}, {zone})"

    return {'wt1': float(wt1), 'wt2': float(wt2), 'zone': zone,
            'signal': signal, 'verdict': verdict, 'healthy': True}


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
    """candlestick: 完整 15 形态 (近 20 日评分)"""
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

    BULL = ['Hammer', 'InvertedHammer', 'BullishEngulfing', 'BullishHarami', 'PiercingLine', 'MorningStar', 'ThreeWhite']
    BEAR = ['ShootingStar', 'BearishEngulfing', 'BearishHarami', 'DarkCloudCover', 'EveningStar', 'ThreeBlackCrows']
    all_pats = {'Hammer': hammer, 'InvertedHammer': inv_hammer, 'ShootingStar': shooting_star,
                'Doji': doji, 'SpinningTop': spinning,
                'BullishEngulfing': bull_engulf, 'BearishEngulfing': bear_engulf, 'BullishHarami': bull_harami,
                'BearishHarami': bear_harami, 'PiercingLine': piercing, 'DarkCloudCover': dark_cloud,
                'MorningStar': morning, 'EveningStar': evening, 'ThreeWhite': three_white, 'ThreeBlackCrows': three_black}

    score_20 = 0
    for p in BULL:
        score_20 += int(all_pats[p].iloc[-20:].sum())
    for p in BEAR:
        score_20 -= int(all_pats[p].iloc[-20:].sum())

    return {'score_20': score_20, 'signal': 1 if score_20 > 0 else (-1 if score_20 < 0 else 0), 'healthy': True}


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


def calc_chanlun(df, ticker='300725'):
    """chanlun: 完整版 czsc 库"""
    try:
        from czsc import CZSC, RawBar, Freq
        # 强制 str (修复 int64 报错)
        sym = str(ticker)
        bars = []
        for i, row in df.iterrows():
            bars.append(RawBar(symbol=sym,
                               id=i, dt=row['date'].to_pydatetime(), freq=Freq.D,
                               open=float(row['open']), close=float(row['close']),
                               high=float(row['high']), low=float(row['low']),
                               vol=float(row['volume']) / 100 if 'volume' in row else 0,
                               amount=float(row['amount']) * 1000 if 'amount' in row else 0))
        c = CZSC(bars)
        last_close = bars[-1].close
        if c.zs_list:
            last_zs = c.zs_list[-1]
            gg = getattr(last_zs, 'gg', 0)
            dd = getattr(last_zs, 'dd', 0)
            zg = getattr(last_zs, 'zg', 0)
            if last_close > gg:
                signal = 1
                verdict = f"⭐ 三买候选 (中枢 GG={gg:.2f}, 现价 {last_close:.2f}, 突破 {((last_close/gg-1)*100):.1f}%)"
            elif last_close < dd:
                signal = -1
                verdict = f"🔻 三卖 (中枢 DD={dd:.2f})"
            else:
                pos_pct = (last_close - dd) / (gg - dd) * 100 if gg > dd else 50
                signal = 0
                verdict = f"↔️ 中枢内 (DD={dd:.2f}~GG={gg:.2f}, 位置 {pos_pct:.0f}%)"
        else:
            signal = 0
            verdict = "无中枢"
        return {'bi_count': len(c.bi_list), 'zs_count': len(c.zs_list),
                'last_zs_gg': getattr(c.zs_list[-1], 'gg', 0) if c.zs_list else 0,
                'last_zs_dd': getattr(c.zs_list[-1], 'dd', 0) if c.zs_list else 0,
                'verdict': verdict, 'signal': signal, 'healthy': True}
    except Exception as e:
        return {'error': str(e), 'signal': 0, 'healthy': False}


def calc_technical_basic(df):
    """technical-basic: EMA/ADX/BB/RSI/OBV"""
    c = df['close']
    ema12 = c.ewm(span=12, adjust=False).mean().iloc[-1]
    ema26 = c.ewm(span=26, adjust=False).mean().iloc[-1]
    
    # ADX
    h, l = df['high'], df['low']
    plus_dm = h.diff()
    minus_dm = -l.diff()
    plus_dm = plus_dm.where((plus_dm > minus_dm) & (plus_dm > 0), 0)
    minus_dm = minus_dm.where((minus_dm > plus_dm) & (minus_dm > 0), 0)
    tr = pd.concat([h - l, (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(axis=1)
    atr = tr.ewm(alpha=1/14, adjust=False).mean()
    plus_di = 100 * plus_dm.ewm(alpha=1/14, adjust=False).mean() / atr
    minus_di = 100 * minus_dm.ewm(alpha=1/14, adjust=False).mean() / atr
    dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di)
    adx = dx.ewm(alpha=1/14, adjust=False).mean().iloc[-1]
    
    # RSI
    delta = c.diff()
    gain = delta.clip(lower=0).ewm(alpha=1/14, adjust=False).mean()
    loss = (-delta.clip(upper=0)).ewm(alpha=1/14, adjust=False).mean()
    rs = gain / loss.replace(0, np.nan)
    rsi = (100 - 100 / (1 + rs)).iloc[-1]
    
    # BB
    ma20 = c.rolling(20).mean().iloc[-1]
    std20 = c.rolling(20).std().iloc[-1]
    bb_pos = (c.iloc[-1] - (ma20 - 2*std20)) / (4*std20)
    
    return {
        'ema12': float(ema12), 'ema26': float(ema26),
        'adx': float(adx), 'rsi': float(rsi), 'bb_pos': float(bb_pos),
        'signal': 1 if (adx > 25 and ema12 > ema26) else 0,
        'healthy': True,
        'strong_momentum': adx > 25,  # 5 强信号之一 (v3.0 Vibe-Trading canonical)
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
    """Smart Money Concepts (canonical 单 bar 事件):

    对齐 Vibe-Trading canonical (smartmoneyconcepts 库默认):
      - swing_length = 10 (canonical 默认)
      - close_break = True
      - structure = ChoCH 优先, BOS 补充
      - buy  = bullish ChoCH/BOS + bullish FVG exists (last_fvg > 0)
      - sell = bearish ChoCH/BOS + bearish FVG exists (last_fvg < 0)
      - stand aside: 无结构信号或方向冲突

    v3.3 canonical 修正: 去掉 v3.2 加的 lookback 聚合 (canonical 是单 bar 事件),
    FVG 同向判断改为严格匹配 (buy=last_fvg>0, sell=last_fvg<0)。
    lookback 参数保留仅用于回传最近 N bar 结构序列 (诊断用), 不参与投票。
    """
    try:
        from smartmoneyconcepts import smc as smc_lib
    except ImportError:
        return {'error': 'smartmoneyconcepts 未安装', 'signal': 0, 'healthy': False}

    if len(df) < max(60, swing_length + 10):
        return {'error': '数据不足', 'signal': 0, 'healthy': False}

    df_work = df.copy()
    if 'date' in df_work.columns:
        df_work = df_work.set_index('date')
    ohlc = df_work[['open', 'high', 'low', 'close']].astype(float)

    try:
        swings = smc_lib.swing_highs_lows(ohlc, swing_length=swing_length)
        bc = smc_lib.bos_choch(ohlc, swings, close_break=True)
        fvg_df = smc_lib.fvg(ohlc, join_consecutive=True)
    except Exception as e:
        return {'error': f'smc lib 调用失败: {e}', 'signal': 0, 'healthy': False}

    bos_val = bc['BOS'].fillna(0).astype(int)
    choch_val = bc['CHOCH'].fillna(0).astype(int)
    fvg_val = fvg_df['FVG'].fillna(0).astype(int)

    # canonical: structure = ChoCH 优先, BOS 补充
    structure = choch_val.where(choch_val != 0, bos_val)

    # canonical buy/sell 严格语义: 单 bar 结构事件 + FVG 同向
    last_struct = int(structure.iloc[-1])
    last_fvg = int(fvg_val.iloc[-1])

    if last_struct == 1 and last_fvg > 0:
        signal = 1
        verdict = f"🟢 SMC 看多 (ChoCH/BOS↑ + FVG↑={last_fvg:+d})"
    elif last_struct == -1 and last_fvg < 0:
        signal = -1
        verdict = f"🔴 SMC 看空 (ChoCH/BOS↓ + FVG↓={last_fvg:+d})"
    else:
        signal = 0
        if last_struct != 0 or last_fvg != 0:
            verdict = f"⚪ SMC 结构/FVG 不一致 (struct={last_struct:+d}, FVG={last_fvg:+d})"
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


def calc_factor_research(df, peer_dfs=None):
    """factor-research: f2_rev_5d IC (基于截面或自相关)"""
    from scipy.stats import spearmanr
    # v3.0 修复: df['close'] 返回 RangeIndex Series, 与 peer_df.set_index('date') 的
    # DatetimeIndex 无法对齐 → aligned 为空 → ic_cross=0. 现统一用 date 索引
    if 'date' in df.columns:
        df_idx = df.set_index('date')
    else:
        df_idx = df.copy()
    c = df_idx['close']
    fwd_5d = c.pct_change(5).shift(-5).dropna()
    rev_5d = c.pct_change(5).dropna()
    
    # 自相关 IC (全样本 Spearman)
    if len(c) > 60:
        # 取最近 252 日
        common_idx = rev_5d.index.intersection(fwd_5d.index)
        common_idx = common_idx[-252:] if len(common_idx) > 252 else common_idx
        if len(common_idx) > 30:
            ic_self, _ = spearmanr(rev_5d[common_idx], fwd_5d[common_idx])
        else:
            ic_self = 0
    else:
        ic_self = 0
    
    # 截面 IC (如果有同业数据) - peer 5d 涨幅 vs peer 后续 5d 涨幅 (横截面回归)
    # v3.0 修复: 原版误用 aligned['A'] (主标的自己), 所有 peer 都贡献同一行 → IC=0
    # 应改为同行业横截面 5d 动量延续性: peer_ret[i] vs peer_fwd[i]
    if peer_dfs:
        try:
            data_5d_ret = []
            data_5d_fwd = []
            for code, peer_df in peer_dfs.items():
                pc = peer_df.set_index('date')['close']
                # 取最近 60 个截面 (过去 60 天的横截面)
                aligned = pd.concat([c, pc], axis=1, join='inner').dropna()
                aligned.columns = ['A', 'B']
                if len(aligned) > 30:
                    # 横截面: peer (B) 当天的 5d 涨幅 vs 5d 后涨幅
                    b_ret = aligned['B'].pct_change(5).dropna()
                    b_fwd = aligned['B'].pct_change(5).shift(-5).dropna()
                    common = b_ret.index.intersection(b_fwd.index)
                    if len(common) >= 20:
                        data_5d_ret.extend(b_ret[common].tail(20).tolist())
                        data_5d_fwd.extend(b_fwd[common].tail(20).tolist())
            if len(data_5d_ret) >= 10:
                ic_cross, _ = spearmanr(data_5d_ret, data_5d_fwd)
            else:
                ic_cross = 0
        except Exception:
            ic_cross = 0
    else:
        ic_cross = 0
    
    # 综合 IC
    ic_self = 0 if pd.isna(ic_self) else float(ic_self)
    ic_cross = 0 if pd.isna(ic_cross) else float(ic_cross)
    ic = ic_cross if peer_dfs and abs(ic_cross) > 0.1 else ic_self
    
    return {'f2_ic_self': ic_self, 'f2_ic_cross': ic_cross, 'f2_ic': ic,
            'signal': 1 if ic > 0.5 else 0, 'healthy': True,
            'strong_momentum': ic > 0.5}


def calc_multi_factor(df, peer_data=None, z_window=252):
    """multi-factor: 四因子 z-score 等权和 (对齐 Vibe-Trading canonical)

    canonical (agent/src/skills/multi-factor/example_signal_engine.py L84-90):
      momentum    = close/shift(20) - 1              (20d 动量)
      reversal    = -(close/shift(5) - 1)            (5d 反转取负, 短期反转看空)
      volatility  = -ret.rolling(20).std()           (20d 波动取负, 低波看多)
      volume_ratio = volume/rolling(20).mean()        (量比)
      → 四因子等权 z-score 和 (canonical 为截面 z, 单标的场景用时间序列 z 近似)

    返回:
      signal=1: composite z > 0 (相对自身历史偏多)
      signal=0: composite z <= 0
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

    return {
        'composite': float(composite),
        'z_momentum': float(z_mom) if not pd.isna(z_mom) else None,
        'z_reversal': float(z_rev) if not pd.isna(z_rev) else None,
        'z_volatility': float(z_vol) if not pd.isna(z_vol) else None,
        'z_volume_ratio': float(z_vr) if not pd.isna(z_vr) else None,
        'signal': 1 if composite > 0 else 0,
        'healthy': True,
        'strong_momentum': bool(composite > 0),
        'note': 'canonical 4-factor ts-z' if peer_data is None else 'canonical 4-factor with peer',
    }


def calc_volatility(df):
    """volatility: HV 百分位 (卖出场景反向适配)

    ⚠️ 与 Vibe-Trading canonical 的方向相反:
      canonical: pct<20 → +1 做多 (低波扩张预期), pct>80 → -1 做空
      本函数:    pct<30 → -1 卖出 (HV 骤降 = 顶部信号), 用于卖出场景

    这是有意的业务适配 (卖出框架只看空波动收缩), 非 canonical 同步错误。
    canonical 的做多/做空双向逻辑已保留在 buy_ladder 上下文。
    """
    ret = df['close'].pct_change()
    hv = ret.rolling(20).std() * np.sqrt(252)
    pct = hv.rolling(120).rank(pct=True) * 100
    cur_hv = float(hv.iloc[-1] * 100)
    cur_pct = float(pct.iloc[-1])

    # 顶部信号: HV 骤降 (卖出场景)
    if cur_pct < 30:
        signal = -1
        verdict = "🔴 HV 骤降 (顶部信号)"
    elif cur_pct > 80:
        signal = 0  # 高波动是强趋势特征, 不是卖出
        verdict = "⚪ 高波动 (强趋势特征)"
    else:
        signal = 0
        verdict = "⚪ 中性"

    return {'hv_pct': cur_pct, 'hv_annual': cur_hv, 'signal': signal,
            'verdict': verdict, 'healthy': True}


def calc_harmonic(df):
    """harmonic: XABCD 检测 (对齐 Vibe-Trading canonical)

    canonical 公式:
      XA = |A - X|
      B_retr = |B - A| / XA     (AB/XA)
      D_retr = |D - A| / XA     (AD/XA, 锚点 A 而非 X)
      BC = |C - B|, CD = |D - C|
      Gartley:   B(0.55,0.68) D(0.72,0.84)
      Bat:       B(0.33,0.55) D(0.82,0.94)
      Butterfly: B(0.72,0.84) D(1.20,1.38)
      Crab:      B(0.33,0.68) D(1.52,1.72)
    """
    c = df['close']
    window = 10
    swings = []
    for i in range(window, len(c) - window):
        if c.iloc[i] == c.iloc[i-window:i+window+1].max():
            swings.append((i, float(c.iloc[i]), 'H'))
        elif c.iloc[i] == c.iloc[i-window:i+window+1].min():
            swings.append((i, float(c.iloc[i]), 'L'))

    if len(swings) < 5:
        return {'verdict': '数据不足', 'signal': 0, 'healthy': True}

    recent_5 = swings[-5:]
    X, A, B, C, D = [s[1] for s in recent_5]
    XA = abs(A - X)
    B_retr = abs(B - A) / XA if XA > 0 else 0
    D_retr = abs(D - A) / XA if XA > 0 else 0

    if 0.55 < B_retr < 0.68 and 0.72 < D_retr < 0.84:
        verdict = "🟢 Gartley (D 0.786)"
        signal = 1
    elif 0.33 < B_retr < 0.55 and 0.82 < D_retr < 0.94:
        verdict = "🟢 Bat"
        signal = 1
    elif 0.72 < B_retr < 0.84 and 1.20 < D_retr < 1.38:
        verdict = "🟢 Butterfly (D 1.27)"
        signal = 1
    elif 0.33 < B_retr < 0.68 and 1.52 < D_retr < 1.72:
        verdict = "🟢 Crab"
        signal = 1
    else:
        verdict = f"⚪ B={B_retr*100:.0f}%, D={D_retr*100:.0f}%"
        signal = 0

    return {'verdict': verdict, 'signal': signal, 'healthy': True}


def calc_pair_trading(df, peer_dfs=None, ticker='300725'):
    """pair-trading REMOVED in v3.0 — signal 恒 0 (仅返回 verdict), 死灯。

    删于 2026-08-12 (实盘验证): 用户确认 pair_trading 是对冲工具, 而 ladder 是
    方向性信号, 用法不匹配; 且原实现所有分支 signal=0, 在计票中永远弃权,
    增加计算成本不增加信号价值。删除可减少 ~15ms/ticker 与 14 个读取槽位。

    占位函数保留以防历史回测 (BT-008/009) 的 import 引用, 返回 dict 但 signal=0。
    """
    return {'verdict': 'pair_trading 已移除 (v3.0)', 'signal': 0, 'healthy': True, 'removed': True}


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
    """v3.3 实装: 自动加载 ticker 对应的板块 ETF 日线数据

    优先级:
      1. SECTOR_ETF_MAP_LOCAL[ticker]  → 加载 data/market/daily/{code}*.csv
      2. data/sector_pool.py 的 TICKER_SECTOR 反查 → 找该 sector 的代表 ETF
         (sector_pool 数据池中 6xxxxx 板块 ETF 代码)
      3. 失败: 返回 None
    """
    import os
    import re
    from pathlib import Path

    # 优先级 1: SECTOR_ETF_MAP_LOCAL
    etf_code = SECTOR_ETF_MAP_LOCAL.get(ticker)

    # 优先级 2: 从 sector_pool 反查 sector, 再找该 sector 的 ETF
    if not etf_code:
        try:
            import sys
            sp_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data')
            if sp_path not in sys.path:
                sys.path.insert(0, sp_path)
            from sector_pool import TICKER_SECTOR, load_sector_pool
            sector = TICKER_SECTOR.get(ticker)
            if sector:
                # 找该 sector 中代码以 51 开头 (板块 ETF) 的代表
                pool = load_sector_pool()
                sector_codes = TICKER_SECTOR  # 反向索引: sector → [codes]
                # 简单实现: 直接用板块 ETF 映射表 (sector → 51xxxx ETF)
                SECTOR_TO_ETF = {
                    'securities': '512000', 'semiconductor': '159995',
                    'pharma': '512010', 'bank': '512800', 'consumer': '510630',
                    'steel': '512810', 'chemical': '512010',  # 化工用医药ETF兜底
                    'infra': '512800', 'telecom': '159915',
                    'defense': '512760', 'auto': '515030',
                    'insurance': '512800', 'shipping': '513180',
                }
                etf_code = SECTOR_TO_ETF.get(sector)
        except Exception:
            pass

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
    
    # ④ 结构破坏
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
                detail = f"f2 IC={s['f2_ic']:+.2f}"
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
