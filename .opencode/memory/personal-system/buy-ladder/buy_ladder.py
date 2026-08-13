#!/usr/bin/env python3
"""
BUY_LADDER v3.0 — 16 Skill 信号驱动的买入框架 (LazyBear + Vibe-Trading canonical)

用法:
  python3 buy_ladder.py --ticker 300725
  python3 buy_ladder.py --ticker 300725 --cost 36.62 --shares 10000 --held
  python3 buy_ladder.py --ticker 600519
  python3 buy_ladder.py --ticker 300725 --force-regime-unlock

功能:
  1. Layer 0: regime 闸门检查 (沪深300 MA60 / WIF MCI / 国家队)
  2. Layer 1: 选股 5 道筛子 (估值/基本面/ST/市值/板块)
  3. Layer 2: 择时 16 信号 + 6 transition + 4 新增 (复用 sell_ladder calc_*)
  4. 输出 4 阶段 (击球/观察/回调/禁入) + 5 确认 + 5 否决

依赖:
  复用 sell_ladder.py (16 calc_* 函数, 已实现, 不修改)
"""
import argparse
import json
import re
import sys
import warnings
from datetime import datetime, date
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings('ignore')

BUY_LADDER_DIR = Path(__file__).resolve().parent
SELL_LADDER_DIR = BUY_LADDER_DIR.parent / "sell-ladder"
RUNS_DIR = BUY_LADDER_DIR / "runs"
REPO_ROOT = BUY_LADDER_DIR.parent.parent.parent.parent  # 仓库根 (data/, example/ 均在此)

sys.path.insert(0, str(SELL_LADDER_DIR))
import sell_ladder as sl

LAYER0_MA60_THRESHOLD = -0.07
LAYER0_MCI_THRESHOLD = 0.50
LAYER0_NATIONALTEAM_PCT_THRESHOLD = -3.0

LAYER1_PE_PB_PERCENTILE_MAX = 0.50
LAYER1_PEG_MAX = 1.5
LAYER1_ROE_MIN = 0.08
LAYER1_MARKET_CAP_MIN_YI = 300
LAYER1_SECTOR_ETF_RET_20D_MIN = 0.0

BUY_CONFIRM_SIGNALS = {
    'wt1_sweet_zone': 'WT1 甜区穿越 [20, 40]',
    'trend_launch': '趋势启动 transition (ADX+EMA+云上)',
    'volume_price_resonance': '量价共振 (底部吸筹+AD线+量比)',
    'structure_complete': '结构完成 (三买+BOS+candlestick)',
    'fundamental_inflection': '基本面拐点 (ROE/营收增速)',
}

BUY_VETO_SIGNALS = {
    'downtrend_unbroken': '下跌趋势未破 (ADX>25 且未收敛)',
    'volume_price_divergence': '量价背离 (缩量反弹)',
    'fundamental_deteriorate': '基本面恶化 (ROE<5% 或加速下滑)',
    'sector_weak': '板块弱势 (20d<-5% 或 MA60 下行)',
    'valuation_high': '估值过高 (PE/PB 分位>70%)',
}

# v3.1 数据驱动积分 (BT-015/016 回测定案: 2024-10~2026-08, 200 池真实数据)
#   信号集 = 4 个独立事件研究验证正 α 的信号:
#   - technical_basic: 2026 α60=+5.18% (t=4.23) | 全期 α60=+0.65%
#   - alpha_zoo:       2026 α60=+3.67% (t=4.49) | 2025 α60=+0.67% (跨年双显著)
#   - candlestick:     2026 α60=+1.05% (t=2.77)
#   - ad_line:         2026 α60=+1.05% (t=2.31)
#   权重 = α60 近似比例 (2/2/1/1), 总分 0~6
#   绝对阈值 (W_B 扫描最优): score>=4 → 击球区 (全期 α60=+1.26% p<1e-4; 2026 α60=+4.80%)
#                            score>=3 → 观察区 (全期 α60=+1.22%)
#   被移除信号 (回测证据): chanlun/volatility/harmonic/ml_strategy/turnover_anomaly 显著负 α;
#                          smc/pair_trading/factor_research/multi_factor/sector_relative 缓存零
#                          (multi_factor 生产实测活跃 31.6% 正, 列为待验证候补, 不入计票)
BUY_SCORE_WEIGHTS = {'technical_basic': 2, 'alpha_zoo': 2, 'candlestick': 1, 'ad_line': 1}
MAX_BUY_SCORE = sum(BUY_SCORE_WEIGHTS.values())  # 6

# 展示全集 (计票仅用 BUY_SCORE_WEIGHTS; 以下保留用于诊断输出/否决/确认)
BUY_EVENT_SIGNALS = ['chanlun', 'turnover_anomaly', 'valuation_percentile', 'fundamental_inflection',
                      'volume_price_resonance', 'structure_complete']
BUY_TREND_SIGNALS = ['alpha_engine_v21', 'technical_basic', 'ichimoku', 'smc', 'alpha_zoo',
                     'multi_factor', 'ml_strategy', 'sector_relative']

W_BUY_EVENT = 2
W_BUY_TREND = 1

V21_OB_BASE = 53
V21_OB_CAP_ADJ = 40

SECTOR_FOR_HOLDING = {
    '601788': '512000', '600030': '512000', '601696': '512000',
    '601688': '512000', '601995': '512000', '601990': '512000',
    '601901': '512000', '512000': '512000',
    '600643': '512000',
    '600050': '159915',
    '601633': '515030',
    '601919': '513180',
    '002601': '512010',
    '300003': '512010', '300142': '512010', '300725': '512010',
    '600570': '512760',
    '601669': '512800',
}


def calc_wt1_sweet_zone_transition(df, lookback=30):
    """
    v3.0 LazyBear 经典 WT1 甜区穿越 (恢复 v1.0 经典阈值)

    经典公式 (LazyBear):
      N1=10, N2=21, OBLEVEL1=60, OSLEVEL1=-60
      AP = (H+L+C)/3 (hlc3)
      ESA = EMA(AP, 10)
      D = EMA(ABS(AP-ESA), 10)
      CI = (AP-ESA) / (0.015 * D)
      WT1 = EMA(CI, 21)
      WT2 = SMA(WT1, 4)

    v21 adaptive OB filter (Vibe-Trading V21 文档):
      ob_base = 53, ob_cap_adj = 40
      threshold = ob_base + ob_cap_adj * mcap_pctile
      (大市值 OB 阈值高, 小市值 OB 阈值低)

    buy 触发:
      - WT1 sweet zone = [40, ob_threshold] (40 是经验下界, 允许从小负值回暖)
      - WT1 从 < 0 (OS 区) 30 天前上升到 sweet zone
      - 这是动量启动, 不是反转 (WT1 必须从 OS 上来, 不接受从 -60 直接穿 0)

    返回:
      signal=1: WT1 从 OS 区上升到 sweet zone
      signal=0: 已超 OB 阈值 / 仍在 OS 区 / 其他
    """
    if 'wt1' not in df.columns:
        df = sl._compute_wt(df)
    if len(df) < 252 + 5:
        return {'signal': 0, 'healthy': False, 'note': f'数据不足 (需 ≥ 252 天)'}

    cur_wt1 = float(df['wt1'].iloc[-1])
    past_wt1 = float(df['wt1'].iloc[-lookback])

    ob_threshold = 60

    sweet_low = 40
    sweet_high = ob_threshold

    in_sweet_zone = sweet_low <= cur_wt1 <= sweet_high
    came_from_below = past_wt1 < 0

    if in_sweet_zone and came_from_below:
        signal = 1
        verdict = f"🟢 WT1 sweet zone 穿越 (LazyBear, cur={cur_wt1:+.2f} in [{sweet_low},{sweet_high}], past={past_wt1:+.2f})"
    elif cur_wt1 > sweet_high:
        signal = 0
        verdict = f"⚪ WT1 超 OB (LazyBear 60/-60, cur={cur_wt1:+.2f} > {sweet_high}, 等回调)"
    elif cur_wt1 < sweet_low:
        signal = 0
        verdict = f"⚪ WT1 未到 sweet zone (cur={cur_wt1:+.2f} < {sweet_low}, 等拐点)"
    else:
        signal = 0
        verdict = f"⚪ WT1 中性 (cur={cur_wt1:+.2f}, 等 sweet zone 触发)"

    return {
        'cur_wt1': cur_wt1,
        'past_wt1': past_wt1,
        'sweet_low': sweet_low,
        'sweet_high': sweet_high,
        'ob_threshold': ob_threshold,
        'in_sweet_zone': in_sweet_zone,
        'came_from_below': came_from_below,
        'signal': signal,
        'verdict': verdict,
        'healthy': True,
    }


def calc_trend_launch_transition(df, lookback=30):
    """
    v3.0 经典阈值趋势启动 transition (恢复 Vibe-Trading canonical 参数)

    三重 transition 同向 = 趋势启动:
      ① ADX 从 < 18 上升到 > 25 (canonical 经典阈值)
      ② EMA12 上穿 EMA26 (canonical)
      ③ 价格穿越 ichimoku 云上 (canonical — 来自下方突破)

    Vibe-Trading technical-basic 标准:
      adx_threshold = 25 (我们之前用 20, 现修正为 25)
    """
    if len(df) < 252 + 50:
        return {'signal': 0, 'healthy': False, 'note': f'数据不足 (需 ≥ 252 天)'}

    c = df['close']

    plus_dm = df['high'].diff()
    minus_dm = -df['low'].diff()
    plus_dm = plus_dm.where((plus_dm > minus_dm) & (plus_dm > 0), 0)
    minus_dm = minus_dm.where((minus_dm > plus_dm) & (minus_dm > 0), 0)
    tr = pd.concat([df['high'] - df['low'],
                    (df['high'] - c.shift()).abs(),
                    (df['low'] - c.shift()).abs()], axis=1).max(axis=1)
    atr = tr.ewm(alpha=1/14, adjust=False).mean()
    plus_di = 100 * plus_dm.ewm(alpha=1/14, adjust=False).mean() / atr
    minus_di = 100 * minus_dm.ewm(alpha=1/14, adjust=False).mean() / atr
    dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di)
    adx_series = dx.ewm(alpha=1/14, adjust=False).mean()

    cur_adx = float(adx_series.iloc[-1])
    past_adx = float(adx_series.iloc[-lookback])

    adx_threshold = 25
    adx_launch = cur_adx > adx_threshold and past_adx < 18

    ema12 = c.ewm(span=12, adjust=False).mean()
    ema26 = c.ewm(span=26, adjust=False).mean()
    cur_ema_bullish = ema12.iloc[-1] > ema26.iloc[-1]
    past_ema_bear = ema12.iloc[-lookback] < ema26.iloc[-lookback]
    ema_cross = cur_ema_bullish and past_ema_bear

    h, l = df['high'], df['low']
    tenkan = (h.rolling(9).max() + l.rolling(9).min()) / 2
    kijun = (h.rolling(26).max() + l.rolling(26).min()) / 2
    senkou_a = ((tenkan + kijun) / 2).shift(26)
    senkou_b = ((h.rolling(52).max() + l.rolling(52).min()) / 2).shift(26)
    cur_close = float(c.iloc[-1])
    cur_cloud_top = max(float(senkou_a.iloc[-1]), float(senkou_b.iloc[-1]))
    past_close = float(c.iloc[-lookback])
    past_cloud_top = max(float(senkou_a.iloc[-lookback]), float(senkou_b.iloc[-lookback]))
    cloud_breakout = cur_close > cur_cloud_top and past_close <= past_cloud_top

    n_transitions = sum([adx_launch, ema_cross, cloud_breakout])

    if n_transitions >= 2:
        signal = 1
        verdict = f"🟢 趋势启动 ({n_transitions}/3 transition: ADX > 25 + EMA金叉 + 云上突破)"
    elif n_transitions == 1:
        signal = 0
        verdict = f"⚪ 部分 transition ({n_transitions}/3, 等待确认)"
    else:
        signal = -1
        verdict = f"🔴 趋势未启动 (0/3 transition)"

    return {
        'cur_adx': cur_adx,
        'past_adx': past_adx,
        'adx_launch': adx_launch,
        'ema_cross': ema_cross,
        'cloud_breakout': cloud_breakout,
        'n_transitions': n_transitions,
        'signal': signal,
        'verdict': verdict,
        'healthy': True,
    }


def calc_valuation_percentile(ticker):
    """
    PE/PB 历史 5 年分位 (需 tushare daily_basic)
    当前 v3.0: 占位符, 返回 signal=0, healthy=False
    后续计划: 接入 tushare daily_basic 接口
    """
    return {
        'signal': 0,
        'healthy': False,
        'note': '待接入 tushare daily_basic (Layer 1 筛子)',
    }


def calc_fundamental_inflection(ticker):
    """
    ROE / 营收增速 季环比拐点 (需 tushare fina_indicator)
    当前 v3.0: 占位符, 返回 signal=0, healthy=False
    后续计划: 接入 tushare fina_indicator
    """
    return {
        'signal': 0,
        'healthy': False,
        'note': '待接入 tushare fina_indicator',
    }


def calc_volume_price_resonance(df):
    """
    v3.0 量价共振 (经典阈值, 与 sell_ladder 复用)

    三个维度共振 (v1.0 经典):
      ① turnover_anomaly=底部吸筹 (sell_ladder 内置)
      ② ad_line=底部背离 (5 日上行 + 价格 5 日新低/平台)
      ③ 5d 量比 > 1.3 (经典阈值)

    返回:
      signal=1: ≥ 2/3 共振
    """
    turnover = sl.calc_turnover_anomaly(df)
    ad_line = sl.calc_ad_line(df)

    if len(df) < 25 or 'volume' not in df.columns:
        return {'signal': 0, 'healthy': False, 'note': '数据不足'}

    vol_5d_avg = df['volume'].iloc[-5:].mean()
    vol_20d_avg = df['volume'].iloc[-20:].mean()
    vol_ratio_5d = float(vol_5d_avg / vol_20d_avg) if vol_20d_avg > 0 else 1.0

    turnover_pos = turnover.get('signal', 0) > 0
    ad_line_pos = ad_line.get('signal', 0) > 0
    vol_ratio_high = vol_ratio_5d > 1.3

    n_resonance = sum([turnover_pos, ad_line_pos, vol_ratio_high])

    if n_resonance >= 2:
        signal = 1
        verdict = f"🟢 量价共振 ({n_resonance}/3: turnover={turnover_pos}, ad_line={ad_line_pos}, vol_ratio={vol_ratio_5d:.2f})"
    elif n_resonance == 1:
        signal = 0
        verdict = f"⚪ 部分共振 (1/3)"
    else:
        signal = -1
        verdict = f"🔴 无共振 (0/3)"

    return {
        'turnover_pos': turnover_pos,
        'ad_line_pos': ad_line_pos,
        'vol_ratio_5d': vol_ratio_5d,
        'n_resonance': n_resonance,
        'signal': signal,
        'verdict': verdict,
        'healthy': True,
    }


def calc_structure_complete(df):
    """
    v3.0 结构完成 (恢复 v1.0 经典, 不再过度细化 chanlun/smc)

    三个维度 (复用 sell_ladder):
      ① chanlun=三买候选 (突破中枢上沿)
      ② smc=bullish BOS (结构突破)
      ③ candlestick 20d 形态 score>0

    返回:
      signal=1: ≥ 2/3 完成
    """
    chanlun = sl.calc_chanlun(df)
    smc = sl.calc_smc(df)
    candlestick = sl.calc_candlestick(df)

    chanlun_pos = chanlun.get('signal', 0) > 0
    smc_pos = smc.get('signal', 0) > 0
    candlestick_pos = candlestick.get('signal', 0) > 0

    n_struct = sum([chanlun_pos, smc_pos, candlestick_pos])

    if n_struct >= 2:
        signal = 1
        verdict = f"🟢 结构完成 ({n_struct}/3: chanlun={chanlun_pos}, smc={smc_pos}, candle={candlestick_pos})"
    elif n_struct == 1:
        signal = 0
        verdict = f"⚪ 部分结构 (1/3)"
    else:
        signal = -1
        verdict = f"🔴 结构未成 (0/3)"

    return {
        'chanlun_pos': chanlun_pos,
        'smc_pos': smc_pos,
        'candlestick_pos': candlestick_pos,
        'n_struct': n_struct,
        'signal': signal,
        'verdict': verdict,
        'healthy': True,
    }


def check_layer0_regime(force_unlock=False):
    """
    Layer 0: regime 闸门
    3 重条件: 沪深300 MA60 + WIF MCI + 国家队 regime
    任一不通过 → 锁定
    当前 2026-08-11: 2/3 锁定 (MCI Q3 + 国家队净卖出)
    """
    if force_unlock:
        return {
            'ma60_ok': True,
            'mci_ok': True,
            'national_team_ok': True,
            'unlocked': True,
            'forced': True,
        }

    ma60_ok = False
    mci_ok = False
    national_team_ok = False

    # ---------- 1. 沪深300 MA60 (集中数据 data/market/daily/510300*.csv) ----------
    # v3.0.1: glob 修复为 510300*.csv (匹配 510300.csv 与 510300_<name>.csv)
    try:
        hu_shen_300_csv = REPO_ROOT / "data" / "market" / "daily"
        hs300_files = sorted(hu_shen_300_csv.glob("510300*.csv"))
        if hs300_files:
            hs300_df = pd.read_csv(hs300_files[0])
            hs300_df['date'] = pd.to_datetime(hs300_df['date'])
            hs300_df = hs300_df.sort_values('date')
            ma60 = float(hs300_df['close'].iloc[-60:].mean())
            cur = float(hs300_df['close'].iloc[-1])
            ma60_pct = (cur / ma60 - 1) * 100
            ma60_ok = ma60_pct > LAYER0_MA60_THRESHOLD * 100
            ma60_source = f"data/510300 (bar {str(hs300_df['date'].iloc[-1].date())})"
        else:
            raise FileNotFoundError("510300*.csv 缺失")
    except Exception as e:
        ma60_pct = -2.66
        ma60_ok = ma60_pct > LAYER0_MA60_THRESHOLD * 100
        ma60_source = f'CHINA_FRAMEWORK §11 (fallback: {e})'

    # ---------- 2. WIF MCI (PMI + M2 按 WIF v2.7 公式实时计算) ----------
    # v3.0.1: 原代码读 pmi_df['mci'] 但 macro_pmi.csv 无 mci 列 → 永远 fallback
    # 现在按 WIF 官方公式: MCI = PMI_norm×0.5 + M2_norm×0.5
    #   PMI_norm = clamp((PMI-47)/6, 0, 1); M2_norm = clamp((M2-6)/9, 0, 1)
    mci_value = None
    mci_month = None
    try:
        repo_root = REPO_ROOT
        pmi_csv = repo_root / "example" / "wif-ashare" / "data" / "macro_pmi.csv"
        m2_csv = repo_root / "example" / "wif-ashare" / "data" / "macro_m2_m1_spread.csv"
        if not (pmi_csv.exists() and m2_csv.exists()):
            raise FileNotFoundError("macro_pmi.csv / macro_m2_m1_spread.csv 缺失")
        pmi_df = pd.read_csv(pmi_csv)
        m2_df = pd.read_csv(m2_csv)
        pmi_df['月份'] = pd.to_datetime(pmi_df['月份'])
        m2_df['月份'] = pd.to_datetime(m2_df['月份'])
        macro = pd.merge(pmi_df[['月份', 'PMI']], m2_df[['月份', 'M2_YoY']], on='月份', how='inner')
        macro = macro.sort_values('月份')
        last = macro.iloc[-1]
        pmi_norm = max(0.0, min(1.0, (float(last['PMI']) - 47.0) / 6.0))
        m2_norm = max(0.0, min(1.0, (float(last['M2_YoY']) - 6.0) / 9.0))
        mci_value = round(0.5 * pmi_norm + 0.5 * m2_norm, 4)
        mci_month = str(last['月份'].date())
        mci_ok = mci_value > LAYER0_MCI_THRESHOLD
        mci_source = f"WIF v2.7 公式实时计算 (PMI={last['PMI']} M2={last['M2_YoY']} @{mci_month})"
    except Exception as e:
        mci_value = 0.386
        mci_ok = mci_value > LAYER0_MCI_THRESHOLD
        mci_source = f'CHINA_FRAMEWORK §11 (fallback: {e})'

    # ---------- 3. 国家队 regime (4.1.NATIONAL_TEAM_OBSERVATION.md 解析) ----------
    # v3.0.1: 原代码硬编码 -89.0; 现在从 md 解析 510050 vs 2025-12 峰值变化
    nt_pct = None
    national_team_ok = False
    try:
        nt_obs = BUY_LADDER_DIR.parent / "4.1.NATIONAL_TEAM_OBSERVATION.md"
        if nt_obs.exists():
            nt_text = nt_obs.read_text(encoding='utf-8')
            m = re.search(r'510050\s*(-?\d+(?:\.\d+)?)%', nt_text)
            if m:
                nt_pct = float(m.group(1))
                national_team_ok = nt_pct > LAYER0_NATIONALTEAM_PCT_THRESHOLD
                nt_source = 'md 510050 vs-2025-12峰值 (Morningstar 月度份额)'
            else:
                raise ValueError("md 未找到 '510050 -NN%' 模式")
        else:
            raise FileNotFoundError("4.1.NATIONAL_TEAM_OBSERVATION.md 缺失")
    except Exception as e:
        nt_pct = -89.0
        national_team_ok = nt_pct > LAYER0_NATIONALTEAM_PCT_THRESHOLD
        nt_source = f'fallback -89.0 ({e})'

    unlocked = ma60_ok and mci_ok and national_team_ok

    return {
        'ma60_pct': ma60_pct,
        'ma60_source': ma60_source,
        'ma60_ok': ma60_ok,
        'mci_value': mci_value,
        'mci_month': mci_month,
        'mci_source': mci_source,
        'mci_ok': mci_ok,
        'nt_pct': nt_pct,
        'nt_source': nt_source,
        'national_team_ok': national_team_ok,
        'unlocked': unlocked,
        'forced': False,
    }


def check_layer1_selection(ticker, sector_df=None):
    """
    Layer 1: 5 道筛子 (v3.1 起咨询性 — 仅 ST 红牌由 stage_buy 作硬否决)
    估值/基本面占位符 (恒 True), 只检查市值/ST/板块景气, 均不再阻断判定
    """
    market_cap_yi = None
    pe_ttm = None
    pb_mrq = None
    roe = None
    is_st = False

    try:
        daily_basic_csv = None
        candidate_dirs = [
            BUY_LADDER_DIR.parent.parent.parent / "data" / "fundamentals",
        ]
        for d in candidate_dirs:
            cand = list(d.glob(f"{ticker}_*.csv")) if d.exists() else []
            if cand:
                daily_basic_csv = cand[0]
                break

        if daily_basic_csv:
            df = pd.read_csv(daily_basic_csv)
            if 'total_mv' in df.columns:
                market_cap_yi = float(df['total_mv'].iloc[-1]) / 1e8
            if 'pe_ttm' in df.columns:
                pe_ttm = float(df['pe_ttm'].iloc[-1])
            if 'pb_mrq' in df.columns:
                pb_mrq = float(df['pb_mrq'].iloc[-1])
    except Exception:
        pass

    valuation_pass = True
    fundamental_pass = True
    st_pass = not is_st
    market_cap_pass = market_cap_yi is None or market_cap_yi >= LAYER1_MARKET_CAP_MIN_YI

    sector_pass = True
    if sector_df is not None and len(sector_df) >= 25:
        cur = float(sector_df['close'].iloc[-1])
        ret_20d = (cur / float(sector_df['close'].iloc[-21]) - 1) if len(sector_df) >= 21 else 0
        sector_ma60 = float(sector_df['close'].iloc[-60:].mean()) if len(sector_df) >= 60 else cur
        sector_ma60_pct = (cur / sector_ma60 - 1) * 100
        sector_pass = ret_20d > LAYER1_SECTOR_ETF_RET_20D_MIN and sector_ma60_pct > -5
    else:
        sector_pass = True

    n_pass = sum([valuation_pass, fundamental_pass, st_pass, market_cap_pass, sector_pass])

    return {
        'market_cap_yi': market_cap_yi,
        'pe_ttm': pe_ttm,
        'pb_mrq': pb_mrq,
        'roe': roe,
        'is_st': is_st,
        'valuation_pass': valuation_pass,
        'fundamental_pass': fundamental_pass,
        'st_pass': st_pass,
        'market_cap_pass': market_cap_pass,
        'sector_pass': sector_pass,
        'n_pass': n_pass,
        'n_total': 5,
        'all_pass': n_pass == 5,
    }


def check_buy_veto(signals, df, sector_df=None):
    """
    5 大买入否决 (任 1 触发 = 不买, 一票否决)
    """
    vetoes = {}

    tech = signals.get('technical_basic', {})
    ema12 = tech.get('ema12', 0)
    ema26 = tech.get('ema26', 0)
    adx = tech.get('adx', 0)
    if len(df) >= 6:
        adx_5d_ago = tech.get('adx', 0)
        cur_close = float(df['close'].iloc[-1])
        past_close = float(df['close'].iloc[-6])
        c = df['close']
        h = df['high']
        l = df['low']
        plus_dm = h.diff()
        minus_dm = -l.diff()
        plus_dm = plus_dm.where((plus_dm > minus_dm) & (plus_dm > 0), 0)
        minus_dm = minus_dm.where((minus_dm > plus_dm) & (minus_dm > 0), 0)
        tr = pd.concat([h - l, (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(axis=1)
        atr = tr.ewm(alpha=1/14, adjust=False).mean()
        plus_di = 100 * plus_dm.ewm(alpha=1/14, adjust=False).mean() / atr
        minus_di = 100 * minus_dm.ewm(alpha=1/14, adjust=False).mean() / atr
        dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di)
        adx_series = dx.ewm(alpha=1/14, adjust=False).mean()
        adx_5d_ago = float(adx_series.iloc[-6])
        downtrend_unbroken = ema12 < ema26 and adx > 25 and adx > adx_5d_ago
    else:
        downtrend_unbroken = ema12 < ema26 and adx > 25
    vetoes['downtrend_unbroken'] = {
        'triggered': bool(downtrend_unbroken),
        'note': f'EMA12<EMA26:{ema12<ema26}, ADX>25:{adx>25}, 未收敛:{adx > adx_5d_ago if len(df) >= 6 else "N/A"}'
    }

    if len(df) >= 6:
        ret_5d = float(df['close'].iloc[-1] / df['close'].iloc[-6] - 1)
        vol_5d_avg = df['volume'].iloc[-5:].mean()
        vol_20d_avg = df['volume'].iloc[-20:].mean() if len(df) >= 20 else vol_5d_avg
        vol_ratio = float(vol_5d_avg / vol_20d_avg) if vol_20d_avg > 0 else 1.0
        volume_price_divergence = ret_5d > 0.01 and vol_ratio < 0.7
    else:
        volume_price_divergence = False
    vetoes['volume_price_divergence'] = {
        'triggered': bool(volume_price_divergence),
        'note': '缩量反弹 (<0.7 量比 + 价涨)'
    }

    fundamental_deteriorate = False
    vetoes['fundamental_deteriorate'] = {
        'triggered': fundamental_deteriorate,
        'note': '待接入 tushare fina_indicator (占位)'
    }

    sector_weak = False
    if sector_df is not None and len(sector_df) >= 25:
        cur = float(sector_df['close'].iloc[-1])
        ret_20d = (cur / float(sector_df['close'].iloc[-21]) - 1) if len(sector_df) >= 21 else 0
        ma60 = float(sector_df['close'].iloc[-60:].mean()) if len(sector_df) >= 60 else cur
        ma60_pct = (cur / ma60 - 1) * 100
        sector_weak = ret_20d < -0.05 or ma60_pct < 0
    vetoes['sector_weak'] = {
        'triggered': bool(sector_weak),
        'note': f'板块 ETF 20d<-5% 或 MA60 下行 (当前 {("禁用" if sector_df is None else "计算中")})'
    }

    valuation_high = False
    vetoes['valuation_high'] = {
        'triggered': valuation_high,
        'note': '待接入 tushare daily_basic (占位)'
    }

    n_veto = sum(1 for v in vetoes.values() if v['triggered'])

    return {
        'vetoes': vetoes,
        'n_veto': n_veto,
        'any_veto': n_veto > 0,
    }


def calc_v21_ob_threshold(mcap_series, ticker, ob_base=V21_OB_BASE, ob_cap_adj=V21_OB_CAP_ADJ):
    """
    Vibe-Trading V21 自适应 OB 阈值 (经典公式)

    公式: threshold = ob_base + ob_cap_adj * mcap_pctile
      - ob_base = 53 (默认基础阈值)
      - ob_cap_adj = 40 (按市值分位调整)
      - mcap_pctile = market cap 在截面中的分位 (0=最小, 1=最大)
      - 小市值股票: threshold ≈ 53 (低阈值)
      - 大市值股票: threshold ≈ 93 (高阈值)

    输入:
      mcap_series: pd.Series of market caps (index=tickers)
      ticker: 当前股票代码
      ob_base: 基础阈值 (默认 53, V21 文档)
      ob_cap_adj: 市值调整系数 (默认 40)

    返回:
      ob_threshold: 自适应 OB 阈值 (53-93 之间)
      mcap_pctile: 当前 ticker 的市值分位
    """
    if mcap_series is None or len(mcap_series) < 10:
        return 60, 0.5

    mcap_pctile = mcap_series.rank(pct=True).get(ticker, 0.5)
    if pd.isna(mcap_pctile):
        mcap_pctile = 0.5

    threshold = ob_base + ob_cap_adj * mcap_pctile
    return float(threshold), float(mcap_pctile)


def adaptive_ob_keep(wt1_series, mcap_series, ob_base=V21_OB_BASE, ob_cap_adj=V21_OB_CAP_ADJ):
    """
    Vibe-Trading V21 自适应 OB 过滤函数 (批量用)

    输入:
      wt1_series: pd.Series WT1 值 (index=tickers)
      mcap_series: pd.Series 市值 (index=tickers)
      ob_base, ob_cap_adj: V21 参数

    返回:
      pd.Series bool: True = 通过 OB 过滤, False = 超 OB 阈值被过滤
    """
    if wt1_series is None or mcap_series is None:
        return pd.Series(True, index=mcap_series.index if mcap_series is not None else [])

    mcap_pctile = mcap_series.rank(pct=True)
    thresholds = ob_base + ob_cap_adj * mcap_pctile

    result = pd.Series(True, index=wt1_series.index)
    for t in wt1_series.index:
        w = wt1_series.get(t)
        th = thresholds.get(t)
        if pd.isna(w) or pd.isna(th):
            continue
        if w > th:
            result[t] = False
    return result


def score_buy(signals, w_event=W_BUY_EVENT, w_trend=W_BUY_TREND):
    """
    Buy-Ladder v3.1 数据驱动积分 (BT-015/016 回测定案)
    计票信号 (4 个, 全部经 2024-10~2026-08 200 池事件研究验证正 α):
      technical_basic ×2 / alpha_zoo ×2 / candlestick ×1 / ad_line ×1  (总分 0~6)
    其余信号保留在 veto/confirmation 层, 不再进入积分 (负 α 或缓存为零未验证)
    """
    score = sum(w * (signals.get(k, {}).get('signal', 0) > 0) for k, w in BUY_SCORE_WEIGHTS.items())
    # 兼容旧字段: event_pos/trend_pos 仍输出, 但不再参与计分
    event_pos = sum(1 for k in BUY_EVENT_SIGNALS if signals.get(k, {}).get('signal', 0) > 0)
    event_neg = sum(1 for k in BUY_EVENT_SIGNALS if signals.get(k, {}).get('signal', 0) < 0)
    trend_pos = sum(1 for k in BUY_TREND_SIGNALS if signals.get(k, {}).get('signal', 0) > 0)
    return score, MAX_BUY_SCORE, event_pos, event_neg, trend_pos


def stage_buy(score, max_score, n_veto, layer0_unlocked, layer1_pass):
    """
    Buy-Ladder v3.1 阶段判定 (绝对阈值, BT-016 定案):
      score >= 4/6 → 击球区   (全期 α60=+1.26%, 2026 弱市 α60=+4.80%)
      score >= 3/6 → 观察区   (全期 α60=+1.22%)
      其余 → 禁入区-得分不足
    Layer 0 自 v3.1 起为咨询性 (结构性牛市无法可靠判定 regime), 不阻断;
    Layer 1 自 v3.1 起仅 ST 风险为硬否决 (layer1_pass = not is_st), 其余筛子咨询性;
    判定链 = ST 红牌 → veto 否决 → 积分阈值
    """
    if not layer1_pass:
        return 4, '禁入区-ST风险红牌'
    if n_veto > 0:
        return 4, '禁入区-触发否决'

    if score >= 4:
        return 1, '击球区'
    elif score >= 3:
        return 2, '观察区'
    else:
        return 4, '禁入区-得分不足'


def count_buy_confirmations(signals):
    """
    5 大买入确认 (3+/5 = 真启动)
    """
    confirmations = {}

    wt1_sw = signals.get('wt1_sweet_zone', {})
    confirmations['wt1_sweet_zone'] = wt1_sw.get('signal', 0) > 0

    trend_launch = signals.get('trend_launch', {})
    confirmations['trend_launch'] = trend_launch.get('signal', 0) > 0

    vol_res = signals.get('volume_price_resonance', {})
    confirmations['volume_price_resonance'] = vol_res.get('signal', 0) > 0

    struct = signals.get('structure_complete', {})
    confirmations['structure_complete'] = struct.get('signal', 0) > 0

    fund = signals.get('fundamental_inflection', {})
    confirmations['fundamental_inflection'] = fund.get('signal', 0) > 0

    n_confirm = sum(1 for v in confirmations.values() if v)
    return confirmations, n_confirm


def run_buy_ladder(ticker, cost=None, shares=None, held=False,
                   peer_codes=None, no_cdmo=False, force_regime_unlock=False,
                   w_event=W_BUY_EVENT, w_trend=W_BUY_TREND):
    """运行 BUY_LADDER v3.0 (任意股票)"""
    print("=" * 72)
    print(f"🎯 BUY_LADDER v3.0 — {ticker} ({datetime.now().date()})")
    print("=" * 72)

    print("\n[Layer 0] REGIME FILTER (v3.1 咨询性 — 结构性牛市无法可靠判定 regime, 不阻断判定链)")
    layer0 = check_layer0_regime(force_unlock=force_regime_unlock)
    if not layer0['forced']:
        print(f"  沪深300 MA60: {layer0.get('ma60_pct', 'N/A'):.2f}% → {'🟢' if layer0['ma60_ok'] else '🔴'}  [{layer0.get('ma60_source', '?')}]")
        print(f"  WIF MCI: {layer0.get('mci_value', 'N/A')} → {'🟢' if layer0['mci_ok'] else '🔴'}  [{layer0.get('mci_source', '?')}]")
        print(f"  国家队: {layer0.get('nt_pct', 'N/A')}% vs 峰值 → {'🟢' if layer0['national_team_ok'] else '🔴'}  [{layer0.get('nt_source', '?')}]")
    else:
        print(f"  沪深300 MA60: 🔧 强制解锁")
        print(f"  WIF MCI: 🔧 强制解锁")
        print(f"  国家队: 🔧 强制解锁")
    print(f"  综合: {'🟢 解锁' if layer0['unlocked'] else '🔒 锁定'} ({'强制' if layer0['forced'] else 'normal'}) — 仅展示, v3.1 不据此阻断")

    print("\n[1] 数据加载...")
    df = sl.load_data(ticker)
    last_close = float(df.iloc[-1]['close'])
    last_date = df.iloc[-1]['date'].date() if hasattr(df.iloc[-1]['date'], 'date') else str(df.iloc[-1]['date'])
    print(f"  {len(df)} bars ({df.iloc[0]['date'].date()} → {last_date}), 收盘={last_close}")
    if cost:
        pnl = (last_close - cost) / cost * 100
        print(f"  成本={cost}, 浮盈={pnl:+.2f}%")
    if held:
        print(f"  持仓={shares}股 (sell-buyer 闭环模式 B 候选)")

    sector_code = SECTOR_FOR_HOLDING.get(ticker)
    sector_df = pd.DataFrame()
    if sector_code:
        try:
            sector_df = sl.load_data(sector_code)
            print(f"  板块 ETF: {sector_code} ({len(sector_df)} bars)")
        except Exception as e:
            print(f"  ⚠️ 板块 ETF {sector_code} 加载失败: {e}")

    print("\n[Layer 1] SELECTION FILTER (v3.1 咨询性 — 估值/基本面待接入; 仅 ST 风险为硬否决)")
    layer1 = check_layer1_selection(ticker, sector_df)
    print(f"  市值: {layer1.get('market_cap_yi', 'N/A')}亿 → {'🟢' if layer1['market_cap_pass'] else '🔴'} (门槛 {LAYER1_MARKET_CAP_MIN_YI}亿)")
    print(f"  估值: {'🟢' if layer1['valuation_pass'] else '🔴'} (待接入)")
    print(f"  基本面: {'🟢' if layer1['fundamental_pass'] else '🔴'} (待接入)")
    print(f"  ST 风险: {'🟢' if layer1['st_pass'] else '🔴'}")
    print(f"  板块景气: {'🟢' if layer1['sector_pass'] else '🔴'}")
    print(f"  通过: {layer1['n_pass']}/{layer1['n_total']} (咨询 — 不阻断, 仅 ST 风险为硬否决)")

    print("\n[Layer 2] TIMING ENGINE (16 信号 + 4 新增)")
    sector_d = sector_df if not sector_df.empty else None
    signals = {
        'alpha_engine_v21': sl.calc_alpha_engine_v21(df, ticker),
        'candlestick': sl.calc_candlestick(df),
        'ml_strategy': sl.calc_ml_strategy(df),
        'chanlun': sl.calc_chanlun(df, ticker),
        'technical_basic': sl.calc_technical_basic(df),
        'ichimoku': sl.calc_ichimoku(df),
        'smc': sl.calc_smc(df),
        'alpha_zoo': sl.calc_alpha_zoo(df),
        'factor_research': sl.calc_factor_research(df, None),
'multi_factor': sl.calc_multi_factor(df, None),
         'volatility': sl.calc_volatility(df),
         'harmonic': sl.calc_harmonic(df),
         'pair_trading': sl.calc_pair_trading(df, {}, ticker),  # v3.0 removed (signal 恒 0) — 占位返回 0
        'turnover_anomaly': sl.calc_turnover_anomaly(df),
        'sector_relative': sl.calc_sector_relative(df, sector_d),
        'ad_line': sl.calc_ad_line(df),
        'wt1_sweet_zone': calc_wt1_sweet_zone_transition(df),
        'trend_launch': calc_trend_launch_transition(df),
        'volume_price_resonance': calc_volume_price_resonance(df),
        'structure_complete': calc_structure_complete(df),
        'valuation_percentile': calc_valuation_percentile(ticker),
        'fundamental_inflection': calc_fundamental_inflection(ticker),
    }

    print(f"\n[2] 16 复用信号 + 6 新增:")
    for name, s in signals.items():
        if s.get('healthy'):
            if name in ('alpha_engine_v21', 'wt1_sweet_zone'):
                detail = f"cur_wt1={s.get('cur_wt1', s.get('wt1', 0)):+.2f}"
            elif name == 'technical_basic':
                detail = f"ADX={s.get('adx', 0):.1f}, RSI={s.get('rsi', 0):.1f}"
            elif name == 'ichimoku':
                detail = f"云上{s.get('above_cloud_pct', 0):+.1f}%"
            elif name == 'alpha_zoo':
                detail = f"20d={s.get('ret_20d', 0)*100:+.1f}%"
            elif name == 'trend_launch':
                detail = f"{s.get('n_transitions', 0)}/3 transitions"
            elif name in ('volume_price_resonance', 'structure_complete'):
                detail = s.get('verdict', '')[:60]
            elif name in ('valuation_percentile', 'fundamental_inflection'):
                detail = s.get('note', '待接入')
            else:
                detail = s.get('verdict', '')[:60] if s.get('verdict') else ''

            emoji = "🟢" if s.get('signal', 0) > 0 else ("🔴" if s.get('signal', 0) < 0 else "⚪")
            print(f"  {name:<28} {emoji} {s.get('signal', 0):+d}     {detail}")
        else:
            note = s.get('note', '?')
            print(f"  {name:<28} ⚪ N/A   {note}")

    print(f"\n[3] 5 买入否决:")
    veto_result = check_buy_veto(signals, df, sector_d)
    for name, v in veto_result['vetoes'].items():
        emoji = "🔴" if v['triggered'] else "⚪"
        print(f"  {emoji} {name}: {v['note']}")
    print(f"  否决触发: {veto_result['n_veto']}/5")

    print(f"\n[4] 5 买入确认:")
    confirmations, n_confirm = count_buy_confirmations(signals)
    for name, triggered in confirmations.items():
        emoji = "🟢" if triggered else "⚪"
        print(f"  {emoji} {name}")
    print(f"  确认触发: {n_confirm}/5 (3+ = 真启动)")

    score, mscore, ev_pos, ev_neg, tr_pos = score_buy(signals, w_event, w_trend)
    print(f"\n[5] BUY-LADDER v3.1 数据驱动积分 (BT-015/016 回测定案):")
    print(f"  计票信号: {' + '.join(f'{k}×{w}' for k,w in BUY_SCORE_WEIGHTS.items())}")
    pos_detail = ' | '.join(f"{k}={'🟢' if signals.get(k,{}).get('signal',0)>0 else '⚪'}" for k in BUY_SCORE_WEIGHTS)
    print(f"  {pos_detail}")
    print(f"  加权得分: {score}/{mscore} (绝对阈值: ≥4 击球 / ≥3 观察)")

    layer1_pass = not layer1.get('is_st', False)   # v3.1: Layer 1 仅 ST 红牌为硬否决, 其余筛子咨询性
    stage, stage_name = stage_buy(score, mscore, veto_result['n_veto'],
                                   layer0['unlocked'], layer1_pass)

    if stage == 1:
        action = "🟢 分批建仓 50% → 1-2 周确认增至 4/5 加 30% → sell-buyer 闭环加 20%"
    elif stage == 2:
        action = "🟡 放入观察池, 等待确认增至 3+/5"
    else:
        if layer1.get('is_st', False):
            action = "🔴 不买 (ST 风险一票否决)"
        elif veto_result['n_veto'] > 0:
            action = f"🔴 不买 (触发 {veto_result['n_veto']}/5 否决)"
        else:
            action = "🔴 不买 (得分不足)"

    print(f"\n[6] 阶段判定:")
    print(f"  阶段 {stage}: {stage_name}")
    print(f"  建议: {action}")

    if held and stage != 4:
        print(f"\n[7] sell-buyer 闭环检测 (模式 B 回调买入):")
        sell_result = _check_sell_buyer_loop(df, signals)
        print(f"  sell stage: {sell_result['sell_stage']} ({sell_result['sell_stage_name']})")
        print(f"  回调幅度: {sell_result['pullback_pct']:+.2f}%")
        print(f"  量缩: {'是' if sell_result['vol_shrink'] else '否'}")
        print(f"  模式 B 可触发: {'🟢 是' if sell_result['mode_b_trigger'] else '⚪ 否'}")

    result = {
        'ticker': ticker,
        'date': str(last_date),
        'last_close': last_close,
        'cost': cost,
        'pnl_pct': (last_close - cost) / cost * 100 if cost else None,
        'held': held,
        'shares': shares,
        'layer0': layer0,
        'layer1': layer1,
        'signals': {k: v for k, v in signals.items()},
        'veto_result': veto_result,
        'confirmations': confirmations,
        'n_confirm': n_confirm,
        'score': score,
        'max_score': mscore,
        'event_pos': ev_pos,
        'event_neg': ev_neg,
        'trend_pos': tr_pos,
        'stage': stage,
        'stage_name': stage_name,
        'action': action,
    }

    _save_run_result(result)
    return result


def _check_sell_buyer_loop(df, signals):
    """检测 sell-buyer 闭环 (模式 B 回调买入)
    条件: sell stage=1 (强动能) + 价格回调≥5% + 量缩企稳
    """
    sell_result = sl.score_v22(signals)
    sell_score = sell_result[0]
    sell_mscore = sell_result[1]
    end_signals = sl.check_momentum_end_signals(signals, df)
    end_count = sum(1 for v in end_signals.values() if v)
    sell_stage, sell_stage_name = sl.stage_v22(sell_score, sell_mscore, end_count)

    if len(df) < 25:
        return {
            'sell_stage': sell_stage,
            'sell_stage_name': sell_stage_name,
            'pullback_pct': 0,
            'vol_shrink': False,
            'mode_b_trigger': False,
        }

    cur = float(df['close'].iloc[-1])
    high_5d = float(df['close'].iloc[-5:].max())
    pullback_pct = (cur / high_5d - 1) * 100

    vol_5d = float(df['volume'].iloc[-5:].mean())
    vol_10d = float(df['volume'].iloc[-10:].mean())
    vol_shrink = vol_5d < vol_10d

    ema12 = signals['technical_basic'].get('ema12', cur)
    near_support = cur >= ema12 * 0.98

    mode_b_trigger = (
        sell_stage == 1
        and pullback_pct <= -5
        and vol_shrink
        and near_support
    )

    return {
        'sell_stage': sell_stage,
        'sell_stage_name': sell_stage_name,
        'pullback_pct': pullback_pct,
        'vol_shrink': vol_shrink,
        'near_support': near_support,
        'mode_b_trigger': mode_b_trigger,
    }


def _save_run_result(result):
    """保存到 runs/YYYY-MM-DD/buy_ladder_<ticker>_<date>.json
    v3.0.1: 目录用运行日 (datetime.now), result['date'] 保留数据最后日期"""
    run_date = str(datetime.now().date())
    run_dir = RUNS_DIR / run_date
    run_dir.mkdir(parents=True, exist_ok=True)
    out_path = run_dir / f"buy_ladder_{result['ticker']}_{run_date}.json"
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2, default=str)
    print(f"\n[结果保存] {out_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='BUY_LADDER v3.0 — 买入判定框架')
    parser.add_argument('--ticker', required=True, help='股票代码 (如 300725)')
    parser.add_argument('--cost', type=float, help='持仓成本 (用于 sell-buyer 闭环)')
    parser.add_argument('--shares', type=int, help='持仓数量')
    parser.add_argument('--held', action='store_true', help='已持仓 (启用 sell-buyer 闭环)')
    parser.add_argument('--force-regime-unlock', action='store_true', help='强制解锁 Layer 0 (调试用)')
    parser.add_argument('--w-event', type=int, default=W_BUY_EVENT)
    parser.add_argument('--w-trend', type=int, default=W_BUY_TREND)
    args = parser.parse_args()

    run_buy_ladder(
        ticker=args.ticker,
        cost=args.cost,
        shares=args.shares,
        held=args.held,
        force_regime_unlock=args.force_regime_unlock,
        w_event=args.w_event,
        w_trend=args.w_trend,
    )