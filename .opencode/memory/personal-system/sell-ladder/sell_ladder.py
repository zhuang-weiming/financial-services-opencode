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
    'trend_break': {'name': '趋势破坏', 'trigger': 'EMA(12) 跌破 + ADX<20 + ichimoku 跌穿云'},
    'momentum_reversal': {'name': '动量反转', 'trigger': 'WT1<-20 + RSI<30 持续 + 20d 动量<-10%'},
    'volume_divergence': {'name': '量能背离', 'trigger': 'OBV 下降 + 价格新高 (5 日)'},
    'structure_break': {'name': '结构破坏', 'trigger': 'smc ChoCH + chanlun 顶分型 + ichimoku 跌穿云'},
    'volatility_drop': {'name': '波动率突变', 'trigger': 'HV 100% → 30% (30 日内)'},
}

# ============================================================
# 1. 数据加载
# ============================================================
def load_data(ticker: str) -> pd.DataFrame:
    """加载日线数据 (任意股票: 本地查找 → Sina API fallback → 永久落盘)"""
    if not ticker.isdigit():
        raise ValueError(f"代码必须是数字: {ticker}")

    # 1. 本地查找 (优先级: data/raw → data/tech-pool → data/cross-data)
    local_candidates = [
        DATA_DIR / f"raw_daily_{ticker}.csv",
    ]
    import glob
    for g in [f"{DATA_DIR}/tech-pool/{ticker}_*.csv", f"{CROSS_DIR}/{ticker}_*.csv"]:
        local_candidates += [Path(p) for p in glob.glob(g)]

    for path in local_candidates:
        if path.exists():
            df = pd.read_csv(path)
            return _standardize(df, ticker)

    # 2. Fallback: Sina API (轻量, 永不被封) → 永久落盘
    print(f"  ⚠️ 本地无 {ticker} 数据, 改用 Sina API 下载...")
    df = _sina_download(ticker)
    df = _standardize(df, ticker)
    path = DATA_DIR / f"raw_daily_{ticker}.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    df[['date', 'code', 'open', 'close', 'high', 'low', 'volume']].to_csv(path, index=False)
    print(f"  ✅ 已保存到 {path}")
    return df


def _standardize(df: pd.DataFrame, ticker: str) -> pd.DataFrame:
    """标准化列名 + 类型 (兼容本地中文列名 / Sina API 英文列名)"""
    rename = {'日期': 'date', '股票代码': 'code', '开盘': 'open', '收盘': 'close',
              '最高': 'high', '最低': 'low', '成交量': 'volume', '成交额': 'amount',
              '涨跌幅': 'chg_pct'}
    df = df.rename(columns={k: v for k, v in rename.items() if k in df.columns})
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'])
    # Sina 返回字符串列 → 转数值
    for col in ['open', 'close', 'high', 'low', 'volume']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    if 'code' not in df.columns:
        df['code'] = ticker
    return df.sort_values('date').reset_index(drop=True)


def _sina_download(code: str) -> pd.DataFrame:
    """Sina 历史 K 线 (fallback)"""
    import time
    full_code = f'sz{code}' if code.startswith(('0', '3')) else f'sh{code}'
    if code.startswith(('1', '5')):
        full_code = f'sh{code}'
    url = 'https://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData'
    params = {'symbol': full_code, 'scale': 240, 'ma': 'no', 'datalen': 900}
    r = __import__('requests').get(url, params=params, timeout=10,
                                    headers={'User-Agent': 'Mozilla/5.0'})
    df = pd.DataFrame(r.json())
    df = df.rename(columns={'day': 'date', 'open': 'open', 'high': 'high',
                            'low': 'low', 'close': 'close', 'volume': 'volume'})
    df['date'] = pd.to_datetime(df['date'])
    return df


# ============================================================
# 2. 14 Skill 信号计算
# ============================================================
def calc_alpha_engine_v21(df, ticker='300725'):
    """alpha-engine-v21: LazyBear WaveTrend (任意 ticker: 本地 wt CSV 优先, 否则现场计算)"""
    import glob
    wt_paths = glob.glob(str(DATA_DIR / f"wt_daily_{ticker}.csv")) + \
               glob.glob(str(DATA_DIR / f"tech-pool/wt_{ticker}.csv"))
    wt_path = wt_paths[0] if wt_paths else None
    if wt_path:
        wt = pd.read_csv(wt_path)
        wt_cols = {c: c for c in wt.columns}
        if '日期' in wt.columns:
            wt = wt.rename(columns={'日期': 'date', 'wt1': 'wt1', 'wt2': 'wt2'})
        wt['date'] = pd.to_datetime(wt['date'])
        df = df.merge(wt[['date', 'wt1', 'wt2']], on='date', how='left')
    elif 'wt1' not in df.columns:
        # 现场计算 (通用)
        df = _compute_wt(df)
    last = df.iloc[-1]
    wt1, wt2 = last.get('wt1', 0), last.get('wt2', 0)
    
    if pd.isna(wt1): wt1 = 0
    if pd.isna(wt2): wt2 = 0
    
    if wt1 >= 60: zone = "OB≥60"
    elif wt1 >= 40: zone = "H 40-60"
    elif wt1 >= 20: zone = "M+ 20-40"
    elif wt1 >= 0: zone = "N+ 0-20"
    elif wt1 >= -20: zone = "N- -20-0"
    elif wt1 >= -40: zone = "M- -40-20"
    elif wt1 >= -60: zone = "L -60-40"
    else: zone = "OS≤-60"
    
    return {'wt1': float(wt1), 'wt2': float(wt2), 'zone': zone, 'signal': 0, 'healthy': True}


def _compute_wt(df, n1=10, n2=21):
    """LazyBear WaveTrend (简化版, EMA-based)"""
    c = df['close']
    h = df['high']
    l = df['low']
    esa = ((h + l) / 2).ewm(span=n1, adjust=False).mean()
    d = ((((h + l) / 2) - esa).abs()).ewm(span=n1, adjust=False).mean()
    ci = (((h + l) / 2) - esa) / (0.015 * d.replace(0, np.nan))
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

    # 5 单 K 线
    hammer = ((lower_shadow >= 2 * body) & (upper_shadow <= body) & (body_pct < 0.4))
    inv_hammer = ((upper_shadow >= 2 * body) & (lower_shadow <= body) & (body_pct < 0.4))
    doji = (body_pct < 0.1) & (rng > 0)
    spinning = (body_pct < 0.3) & (upper_shadow > body) & (lower_shadow > body)

    # 双日
    po, pc = df.shift(1)['open'], df.shift(1)['close']
    pbody = (pc - po).abs()
    bull_engulf = (pc < po) & (c > o) & (o <= pc) & (c >= po) & (body > pbody)
    bear_engulf = (pc > po) & (c < o) & (o >= pc) & (c <= po) & (body > pbody)
    bull_harami = (pc < po) & (c > o) & (o >= pc) & (c <= po) & (body < pbody)
    bear_harami = (pc > po) & (c < o) & (o <= pc) & (c >= po) & (body < pbody)
    piercing = (pc < po) & (c > o) & (c > (po + pc) / 2) & (o < pc)
    dark_cloud = (pc > po) & (c < o) & (c < (po + pc) / 2) & (o > pc)

    # 三日
    ppo, ppc = df.shift(2)['open'], df.shift(2)['close']
    morning = (ppc < ppo) & (body.shift(1) < body) & (c > o) & (c > (ppo + pc) / 2)
    evening = (ppc > ppo) & (body.shift(1) < body) & (c < o) & (c < (ppo + pc) / 2)
    three_white = (c > o) & (c.shift(1) > df.shift(1)['open']) & (c.shift(2) > df.shift(2)['open']) & (c > c.shift(1)) & (c.shift(1) > c.shift(2))
    three_black = (c < o) & (c.shift(1) < df.shift(1)['open']) & (c.shift(2) < df.shift(2)['open']) & (c < c.shift(1)) & (c.shift(1) < c.shift(2))

    BULL = ['Hammer', 'InvertedHammer', 'BullishEngulfing', 'BullishHarami', 'PiercingLine', 'MorningStar', 'ThreeWhite']
    BEAR = ['BearishEngulfing', 'BearishHarami', 'DarkCloudCover', 'EveningStar', 'ThreeBlackCrows']
    all_pats = {'Hammer': hammer, 'InvertedHammer': inv_hammer, 'Doji': doji, 'SpinningTop': spinning,
                'BullishEngulfing': bull_engulf, 'BearishEngulfing': bear_engulf, 'BullishHarami': bull_harami,
                'BearishHarami': bear_harami, 'PiercingLine': piercing, 'DarkCloudCover': dark_cloud,
                'MorningStar': morning, 'EveningStar': evening, 'ThreeWhite': three_white, 'ThreeBlackCrows': three_black}

    score_20 = 0
    for p in BULL:
        score_20 += int(all_pats[p].iloc[-20:].sum())
    for p in BEAR:
        score_20 -= int(all_pats[p].iloc[-20:].sum())

    return {'score_20': score_20, 'signal': 1 if score_20 > 0 else (-1 if score_20 < 0 else 0), 'healthy': True}


def calc_ml_strategy(df):
    """ml-strategy: 简化 (5d forward 方向)"""
    c = df['close']
    ret_5d = c.pct_change(5).iloc[-1]
    return {'ret_5d': float(ret_5d), 'signal': 1 if ret_5d > 0.02 else (-1 if ret_5d < -0.02 else 0), 'healthy': True}


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
        'signal': 1 if (adx > 20 and ema12 > ema26) else 0,
        'healthy': True,
        'strong_momentum': adx > 20,  # 5 强信号之一
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
    tk_bullish = tenkan.iloc[-1] > kijun.iloc[-1]
    
    return {
        'tenkan': float(tenkan.iloc[-1]), 'kijun': float(kijun.iloc[-1]),
        'cloud_top': float(cloud_top), 'cloud_bot': float(cloud_bot),
        'above_cloud_pct': float((last / cloud_top - 1) * 100),
        'tk_bullish': tk_bullish,
        'signal': 1 if (above_cloud and tk_bullish) else 0,
        'healthy': True,
        'strong_momentum': above_cloud,  # 5 强信号之一
    }


def calc_smc(df):
    """smc: Smart Money Concepts (BOS/ChoCH)"""
    # 简化: 20 日高/低 vs 前 20 日
    recent_20 = df.iloc[-20:]
    prev_20 = df.iloc[-40:-20]
    bos_bullish = recent_20['high'].max() > prev_20['high'].max()
    bos_bearish = recent_20['low'].min() < prev_20['low'].min()
    
    if bos_bullish and not bos_bearish:
        signal, verdict = 1, "BOS 上升结构"
    elif bos_bearish and not bos_bullish:
        signal, verdict = -1, "BOS 下降结构"
    else:
        signal, verdict = 0, "震荡"
    
    return {'verdict': verdict, 'signal': signal, 'healthy': True,
            'strong_momentum': signal == 1}  # 5 强信号之一


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
    c = df['close']
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
    
    # 截面 IC (如果有同业数据) - 用近 5 日的 5d 涨幅 vs 后续 5d 涨幅 (n=5 个标的)
    if peer_dfs:
        try:
            data_5d_ret = []  # 5d 涨幅
            data_5d_fwd = []  # 后续 5d 涨幅
            for code, peer_df in peer_dfs.items():
                pc = peer_df.set_index('date')['close']
                aligned = pd.concat([c, pc], axis=1, join='inner').dropna()
                aligned.columns = ['A', 'B']
                if len(aligned) > 30:
                    data_5d_ret.append(aligned['A'].pct_change(5).iloc[-1])
                    data_5d_fwd.append(aligned['A'].pct_change(5).shift(-5).iloc[-1])
            if len(data_5d_ret) >= 3:
                ic_cross, _ = spearmanr(data_5d_ret, data_5d_fwd)
            else:
                ic_cross = 0
        except:
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


def calc_multi_factor(df, peer_data=None):
    """multi-factor: Z-score 综合 (5 因子, 如果没同业数据, 用绝对分数)"""
    c, v = df['close'], df['volume']
    f1 = c.pct_change(20).iloc[-1]  # 20d 动量
    f2 = c.pct_change(5).iloc[-1]   # 5d 反转
    f3 = c.pct_change().rolling(20).std().iloc[-1]  # 波动
    f4 = (v / v.rolling(20).mean()).iloc[-1]  # 量比
    f5 = ((c - df['low'].rolling(20).min()) / (df['high'].rolling(20).max() - df['low'].rolling(20).min())).iloc[-1]
    
    # 简化: 综合分 = (f1 + f5 - f2 - f3) / 4
    composite = (f1 + f5 - abs(f2) - f3) / 4
    return {'composite': float(composite),
            'signal': 1 if composite > 0.05 else 0, 'healthy': True,
            'strong_momentum': bool(composite > 0.05),  # 2026-08-10: 补位 5 强信号 (v2.1 修复)
            'note': 'no peer data' if peer_data is None else 'with peer'}


def calc_volatility(df):
    """volatility: HV 百分位"""
    ret = df['close'].pct_change()
    hv = ret.rolling(20).std() * np.sqrt(252)
    pct = hv.rolling(120).rank(pct=True) * 100
    cur_hv = float(hv.iloc[-1] * 100)
    cur_pct = float(pct.iloc[-1])
    
    # 顶部信号: HV 骤降
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
    """harmonic: 简化 XABCD 检测"""
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
    D_retr = abs(D - X) / XA if XA > 0 else 0
    
    if 0.55 < B_retr < 0.68 and 0.72 < D_retr < 0.85:
        verdict = "🟢 Gartley (D 0.786)"
        signal = 1
    elif 0.72 < B_retr < 0.85 and 1.15 < D_retr < 1.40:
        verdict = "🟢 Butterfly (D 1.27)"
        signal = 1
    else:
        verdict = f"⚪ B={B_retr*100:.0f}%, D={D_retr*100:.0f}%"
        signal = 0
    
    return {'verdict': verdict, 'signal': signal, 'healthy': True}


def calc_pair_trading(df, peer_dfs=None, ticker='300725'):
    """pair-trading: 与参考标的的配对 Z-score"""
    if not peer_dfs:
        return {'verdict': '无配对', 'signal': 0, 'healthy': True}
    
    c = df.set_index('date')['close']
    results = []
    for peer_name, peer_df in peer_dfs.items():
        if peer_name == ticker:  # 跳过自己
            continue
        peer_c = peer_df.set_index('date')['close']
        aligned = pd.concat([c, peer_c], axis=1, join='inner').dropna()
        aligned.columns = ['A', 'B']
        if len(aligned) < 60:
            continue
        ratio = aligned['A'] / aligned['B']
        mean = ratio.rolling(60).mean()
        std = ratio.rolling(60).std()
        z_cur = (ratio - mean).iloc[-1] / std.iloc[-1] if std.iloc[-1] > 0 else 0
        if not pd.isna(z_cur):
            results.append((peer_name, float(z_cur)))
    
    if not results:
        return {'verdict': '无有效配对', 'signal': 0, 'healthy': True}
    
    results.sort(key=lambda x: abs(x[1]), reverse=True)
    top = results[0]
    if abs(top[1]) > 2:
        return {'verdict': f'⚠️ {top[0]} 配对 Z={top[1]:+.2f}', 'signal': 0, 'healthy': True,
                'top_pair': top[0], 'top_z': top[1]}
    else:
        return {'verdict': f'⚪ {top[0]} Z={top[1]:+.2f}', 'signal': 0, 'healthy': True,
                'top_pair': top[0], 'top_z': top[1]}


# ============================================================
# 3. 5 大动能结束标志
# ============================================================
def check_momentum_end_signals(signals):
    """检查 5 大动能结束标志"""
    end_signals = {}
    
    # ① 趋势破坏
    tb = (signals.get('technical_basic', {}).get('adx', 50) < 20 and
          signals.get('ichimoku', {}).get('above_cloud_pct', 50) < 0)
    end_signals['trend_break'] = bool(tb)
    
    # ② 动量反转
    mr = (signals.get('alpha_engine_v21', {}).get('wt1', 0) < -20 and
          signals.get('technical_basic', {}).get('rsi', 50) < 30 and
          signals.get('alpha_zoo', {}).get('ret_20d', 0) < -0.10)
    end_signals['momentum_reversal'] = bool(mr)
    
    # ③ 量能背离 (简化: OBV 5 日下降 + 价格 5 日新高)
    end_signals['volume_divergence'] = False  # 简化, 需要 OBV 计算
    
    # ④ 结构破坏
    sb = (signals.get('smc', {}).get('signal', 0) == -1 and
          signals.get('ichimoku', {}).get('above_cloud_pct', 50) < 0)
    end_signals['structure_break'] = bool(sb)
    
    # ⑤ 波动率突变
    vd = signals.get('volatility', {}).get('hv_pct', 100) < 30
    end_signals['volatility_drop'] = bool(vd)
    
    return end_signals


# ============================================================
# 3.5 v2.2 分级计票 (BT-008 回测实证: 事件信号 ×2 最优)
#   事件信号 (明确买卖点): candlestick, chanlun, ml_strategy → w_event 票
#   趋势信号 (方向判定):   alpha_engine_v21, technical_basic, ichimoku,
#                          smc, alpha_zoo, multi_factor → w_trend 票
#   辅助观察 (0 票):       harmonic, pair_trading, volatility, factor_research
# ============================================================
EVENT_SIGNALS = ['candlestick', 'chanlun', 'ml_strategy']
TREND_SIGNALS = ['alpha_engine_v21', 'technical_basic', 'ichimoku', 'smc', 'alpha_zoo', 'multi_factor']


def score_v22(signals, w_event=2, w_trend=1):
    """分级计票 → (score, max_score, event_pos, event_neg, trend_pos)"""
    event_pos = sum(1 for k in EVENT_SIGNALS if signals[k].get('signal', 0) > 0)
    event_neg = sum(1 for k in EVENT_SIGNALS if signals[k].get('signal', 0) < 0)
    trend_pos = sum(1 for k in TREND_SIGNALS if signals[k].get('signal', 0) > 0)
    max_score = 3 * w_event + 6 * w_trend
    score = w_event * event_pos + w_trend * trend_pos - w_event * event_neg
    return score, max_score, event_pos, event_neg, trend_pos


def stage_v22(score, max_score):
    """分级计票阶段判定 (BT-008 阈值: 0.75/0.42)"""
    if score >= 0.75 * max_score:
        return 1, '强动能期'
    elif score >= 0.42 * max_score:
        return 2, '动能衰减期'
    else:
        return 3, '动能结束期'


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
    
    # 3. 跑 14 skill
    print(f"\n[2] 14 Skill 信号计算...")
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
        'pair_trading': calc_pair_trading(df, peer_dfs if not no_cdmo else None, ticker),
    }
    
    # 4. 5 强动能信号健康数
    strong_signals = ['technical_basic', 'ichimoku', 'smc', 'alpha_zoo', 'factor_research']
    strong_healthy = sum(1 for s in strong_signals if signals[s].get('strong_momentum', False))
    
    # 5. 5 大动能结束标志
    end_signals = check_momentum_end_signals(signals)
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
                detail = f"5d ret={s['ret_5d']*100:+.2f}%"
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
    s22_stage, s22_name = stage_v22(score, mscore)
    print(f"\n[5] SELL_LADDER v2.2 阶段判定 (分级计票: 事件×{w_event} + 趋势×{w_trend}, max={mscore}):")
    print(f"    事件信号: {ev_pos}正 / {ev_neg}负 (candlestick+chanlun+ml_strategy)   趋势信号: {tr_pos}/6 正")
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
