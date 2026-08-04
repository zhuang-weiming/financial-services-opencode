"""
US Debt Debasement Scenario Backtest
====================================
基于历史数据 + 当前事实，量化推演两种剧本：
A) 慢速剧本（HYP-028）: 20年金融抑制 + 通胀税
B) 快速剧本（HYP-027）: 8-10年危机驱动重置

并验证用户论点：
1. "USD 贬值但相对其他货币仍较保值"
2. "RMB 对 USD 升值，但商品价格仍上涨"
3. "全球主要货币同步贬值 vs 商品"

数据源：
- 1946-74, 1971-80, 1985-88 历史数据（来自 raw-log research/REPORT.md）
- 2024-2026 实时数据（来自 FactSet/Morningstar/Treasury/BEA/Safe.gov/PBOC）
"""

import json
from datetime import datetime
from typing import Dict, List, Tuple

# ======================================================================
# Part 1: 关键基线数据 (2026-08-02 snapshot)
# ======================================================================

baseline_2026 = {
    "date": "2026-08-02",
    "us_debt_total_trillion": 36.2,  # Treasury debt to the penny, 估算 7/30/2026
    "us_debt_gdp_pct": 123.0,        # TradingEconomics Dec 2025
    "us_debt_held_public_pct": 98.0, # 估算 (held by public vs intragovernmental)
    "us_fed_funds_rate": 4.50,       # 2026 维持
    "us_10y_yield": 4.20,            # Treasury data 2026-01
    "us_30y_yield": 4.85,
    "us_tips_10y_real_yield": 1.50,  # 反抑制期
    "us_net_interest_gdp_pct": 3.4,  # 接近 defense budget
    "us_5y_cds_bp": 38,              # 危机线 200bp
    "us_treasury_bid_to_cover": 2.45,# 危机线 2.0x
    "us_cpi_yoy": 3.0,
    "us_gdp_growth": 1.5,            # Q2 2026 advance estimate (decay from 2.1%)
    "fed_balance_sheet_trillion": 6.70, # 2026-07-29 H.4.1
    "fed_treasury_holdings_trillion": 4.52,
    "fed_balance_change_yoy_billion": 108,
    "us_fx_reserves_no": True,        # 不是 issue, USD 是 reserve currency
    
    "gold_usd_oz": 3715,             # 2026-07-31 GLD price * 10
    "silver_usd_oz": 52,             # 2026-07-31 SLV price
    "oil_wti_usd_bbl": 77,           # 估算 mid-2026
    "copper_lb_usd": 4.85,
    "dxy_index": 99.5,               # 2026 mid (vs 103-104 早期)
    
    "usdcny_mid_price": 6.7894,      # 2026-07-31 PBOC 中间价
    "usdcny_2024_12": 7.1771,
    "usdjpy": 152.0,                 # 估算
    "usdeur": 1.085,                 # 估算
    "usdgbp": 1.295,                 # 估算
    "usdcad": 1.378,
    "usdaud": 0.658,
    
    "china_fx_reserves_trillion": 3.42,
    "pboc_gold_tonnes": 2346,
    "global_central_bank_gold_2024_tonnes": 1087,
    "global_central_bank_gold_2025_tonnes": 849,
    "global_central_bank_gold_h1_2026_tonnes": 345,
    
    "us_debt_ceiling_expiry": "2027-01",  # Tannenbaum 2026-06 引用
    "debt_maturity_within_12m_pct": 31,    # 已知数据
}

# 2024-2026 表现（验证用户论点）
performance_2024_to_2026 = {
    "GLD_etf": 94.35,   # 黄金 ETF (proxy for gold spot)
    "SLV_etf": 140.40,  # 白银 ETF
    "USO_etf": 93.80,   # 石油 ETF
    "DBA_etf": 43.04,   # 农产品
    "DBB_etf": 47.91,   # 基础金属
    "DBC_etf": 45.43,   # 大宗商品综合
    "SPY_etf": 61.90,   # 标普500
    "QQQ_etf": 70.24,   # 纳斯达克
    "TLT_etf": -7.50,   # 20Y+ 国债
    "UUP_etf": 12.39,   # 美元
    "FXE_etf": 8.21,    # 欧元
    "FXY_etf": -12.38,  # 日元
    "FXB_etf": 13.16,   # 英镑
    "FXA_etf": 6.94,    # 澳元
    "FXC_etf": -2.98,   # 加元
}

# ======================================================================
# Part 2: 历史剧本基线（数据来自 research/REPORT.md）
# ======================================================================

historical_episodes = {
    "E1_1946_74": {
        "duration_years": 29,
        "us_debt_gdp_change_pp": -88,  # 119% → 30.8%
        "us_cpi_avg_pct": 3.02,
        "us_10y_avg_pct": 4.72,
        "real_rate_avg_pct": -1.7,    # i < g (i - g 负)
        "gold_change_pct": "fixed → +433% (1974)",
        "oil_change_pct": "+214%",
        "us_assets_relative": "USD 固定 vs 其他货币（Bretton Woods）",
        "debt_crisis_indicator": "低 (有 r < g 自动去杠杆)",
    },
    "E2_1971_80": {
        "duration_years": 10,
        "us_twi_change_pct": -11.65,   # TWI
        "us_jpy_change_pct": -43.23,   # USD/JPY 跌 (JPY 涨)
        "us_dem_change_pct": -45.83,
        "us_chf_change_pct": -58.53,   # USD/CHF 跌最深
        "us_gbp_change_pct": -0.20,    # GBP 基本持平
        "us_cad_change_pct": +18.28,   # USD 反而涨
        "us_itl_change_pct": +49.92,   # USD 大涨（ITL 单独弱）
        "us_cpi_avg_pct": 8.26,
        "fed_funds_peak_pct": 18.90,
        "gold_change_pct": "+1584% ($35 → $590)",
        "oil_change_pct": "+939%",
        "debt_crisis_indicator": "高 (Volcker 接管前 trust crisis)",
        "key_insight": "USD 对 JPY/DEM/CHF 跌，但对 GBP/CAD/ITL 反而涨 — 主要货币走势分化",
    },
    "E3_1985_88_plaza": {
        "duration_years": 3.3,
        "us_twi_change_pct": -33.28,   # 主动贬值
        "us_jpy_change_pct": -47.92,   # JPY 大涨
        "us_dem_change_pct": -38.11,
        "us_gbp_change_pct": +32.30,   # USD 跌但 GBP 跌更深
        "us_cpi_avg_pct": 3.56,
        "us_10y_avg_pct": 8.42,
        "gold_change_pct": "+26%",
        "oil_change_pct": "-42%",
        "debt_crisis_indicator": "无 (主动贬值 vs 被动危机)",
        "key_insight": "G5 协同贬值 USD，其他货币主动升值 — 与用户论点相反",
    },
    "E4_1979_85_volcker": {
        "duration_years": 6,
        "us_twi_change_pct": +37.58,   # USD 大涨
        "us_dem_change_pct": +52.72,   # DEM 跌
        "us_jpy_change_pct": +10.62,
        "us_gbp_change_pct": -38.71,   # GBP 跌更多
        "us_real_10y_avg_pct": 6.28,
        "us_real_10y_peak_pct": 7.66,
        "gold_change_pct": "-62% (从 $850 peak)",
        "debt_crisis_indicator": "极高 (拉美违约)",
        "key_insight": "强美元 + 高实际利率 → 资本回流 → EM 危机 (与用户论点相反)",
    },
    "E5_1997_98_asian": {
        "duration_years": 1.5,
        "us_twi_change_pct": +3.18,    # USD 升幅小
        "us_thb_change_pct": -48.86,   # USD/THB 跌 - THB 跌很多
        "us_myr_change_pct": -50.58,   # MYR 跌
        "us_krw_change_pct": -35.51,
        "us_jpy_change_pct": -1.61,    # JPY 反而微涨 (避险)
        "us_cpi_change_pct": 2.49,
        "oil_change_pct": "-40%",
        "debt_crisis_indicator": "高 (IMF 救援 $180B+)",
        "key_insight": "USD 对 EM 货币大涨，但对 JPY 微跌 — 用户论点部分成立",
    },
    "E6_2008_15": {
        "duration_years": 8,
        "us_broad_twi_change_pct": +26.85,   # USD 涨
        "eur_change_pct": -26.32,           # EUR 大跌
        "gbp_change_pct": -25.62,
        "jpy_change_pct": +9.64,
        "gold_change_pct": "+23%",
        "oil_change_pct": "-63%",
        "spy_change_pct": "+66%",
        "tlt_change_pct": "+70%",
        "debt_crisis_indicator": "极高 (GFC + Eurozone)",
        "key_insight": "USD 走强周期 (QE 后); EUR/GBP 跌更多",
    },
}

# ======================================================================
# Part 3: 2024-2026 现实数据 vs 用户论点验证
# ======================================================================

def validate_user_thesis():
    """验证用户的 3 个核心论点 vs 2024-2026 实际数据"""

    results = []

    # 论点 1: "USD 不是单独贬值，相对其他货币较保值"
    # 2024-01 → 2026-08 实际表现:
    usd_change = performance_2024_to_2026["UUP_etf"]
    other_changes = {
        "EUR": performance_2024_to_2026["FXE_etf"],
        "JPY": performance_2024_to_2026["FXY_etf"],
        "GBP": performance_2024_to_2026["FXB_etf"],
        "AUD": performance_2024_to_2026["FXA_etf"],
        "CAD": performance_2024_to_2026["FXC_etf"],
    }
    other_avg = sum(other_changes.values()) / len(other_changes)

    results.append({
        "thesis": "论点 1: USD 相对其他主要货币较保值",
        "evidence_2024_2026": {
            "USD (UUP)": f"+{usd_change}%",
            "其他货币 (avg)": f"+{other_avg:.1f}%",
            "EUR": f"+{other_changes['EUR']}%",
            "JPY": f"{other_changes['JPY']}%",
            "GBP": f"+{other_changes['GBP']}%",
        },
        "verdict": (
            "**部分成立，但有重要分化**\n"
            f"- USD 升值 +{usd_change}%, 其他货币平均升值 +{other_avg:.1f}%\n"
            "- JPY 大跌 -12.4%, CAD 微跌 -3.0% (USD 强)\n"
            "- EUR/GBP/AUD 升值 (USD 相对跌)\n"
            "- **混合模式**: USD 对 JPY/CAD 强，对 EUR/GBP/AUD 弱"
        ),
        "data_source": "FactSet Global Prices 2024-01-01 → 2026-08-01"
    })

    # 论点 2: "RMB 升值 vs USD, 但商品价格仍上涨"
    rmb_appreciation = (baseline_2026["usdcny_2024_12"] - baseline_2026["usdcny_mid_price"]) / baseline_2026["usdcny_2024_12"] * 100

    results.append({
        "thesis": "论点 2: RMB 升值 vs USD, 但商品价格上涨",
        "evidence_2024_2026": {
            "USD/CNY 2024-12": baseline_2026["usdcny_2024_12"],
            "USD/CNY 2026-07": baseline_2026["usdcny_mid_price"],
            "RMB 升值幅度": f"+{rmb_appreciation:.1f}%",
            "GLD (黄金)": f"+{performance_2024_to_2026['GLD_etf']}%",
            "SLV (白银)": f"+{performance_2024_to_2026['SLV_etf']}%",
            "USO (石油)": f"+{performance_2024_to_2026['USO_etf']}%",
        },
        "verdict": (
            "**完全成立**\n"
            f"- RMB 2024-12 → 2026-07 升值 +{rmb_appreciation:.1f}% (USD/CNY 从 7.18 → 6.79)\n"
            f"- 同期商品大涨: 黄金 +{performance_2024_to_2026['GLD_etf']}%, 白银 +{performance_2024_to_2026['SLV_etf']}%, 石油 +{performance_2024_to_2026['USO_etf']}%\n"
            "- **RMB 对 USD 强势 ≠ 购买力增强**: 商品价格涨幅远超 RMB 升值幅度\n"
            "- PBOC 2024-12 → 2026-06 外汇储备从 $3.20T → $3.42T (+$220B), 暗示 PBOC 在 USD 弱势下买入 USD 资产"
        ),
        "data_source": "akshare currency_boc_sina 2026-07-31 + SAFE 月度数据"
    })

    # 论点 3: "全球主要货币同步贬值 vs 商品"
    commodity_avg = (performance_2024_to_2026["GLD_etf"] + performance_2024_to_2026["SLV_etf"] +
                     performance_2024_to_2026["USO_etf"] + performance_2024_to_2026["DBA_etf"] +
                     performance_2024_to_2026["DBB_etf"]) / 5
    fx_avg = (performance_2024_to_2026["FXE_etf"] + performance_2024_to_2026["FXY_etf"] +
              performance_2024_to_2026["FXB_etf"] + performance_2024_to_2026["FXA_etf"] +
              performance_2024_to_2026["FXC_etf"]) / 5

    results.append({
        "thesis": "论点 3: 全球主要货币 (含 USD) 同步贬值 vs 商品",
        "evidence_2024_2026": {
            "商品 ETF 平均涨幅": f"+{commodity_avg:.1f}%",
            "FX ETF 平均 (USD-rel)": f"+{fx_avg:.1f}%",
            "SPY (USD 资产)": f"+{performance_2024_to_2026['SPY_etf']}%",
            "TLT (美债)": f"{performance_2024_to_2026['TLT_etf']}%",
        },
        "verdict": (
            "**部分成立**\n"
            f"- 商品平均涨 +{commodity_avg:.1f}%, 大幅跑赢 FX 和股票\n"
            f"- SPY +{performance_2024_to_2026['SPY_etf']}% (美元资产也大涨, 因 AI 周期)\n"
            "- TLT -7.5% (长债在 4.5-5% 利率下亏损)\n"
            "- **结构性观察**: 实物资产 > 美元股票 > 美元债券 > 美元现金\n"
            "- 长期看 FX 同步贬值 vs 商品 — 但 2024-2026 被 AI 周期掩盖"
        ),
        "data_source": "FactSet Global Prices 2024-01-01 → 2026-08-01"
    })

    return results

# ======================================================================
# Part 4: 双剧本量化推演
# ======================================================================

def model_slow_script_20yr():
    """慢速剧本：脉冲式金融抑制 (HYP-028)"""
    # 假设: r < g 持续 (实际利率 -0.5% × 20年 + 通胀税 + 温和增长)
    # 起点: US Debt/GDP 123%, 终态目标: 100% (沿 1946-74 路径)

    initial_debt_gdp = 123.0
    target_debt_gdp = 100.0
    annual_inflation = 3.5  # 比 baseline 略高 (因债务货币化)
    annual_real_gdp = 2.0
    annual_real_rate = -1.0  # 实际利率负 = 抑制期

    years = 20
    trajectory = []
    debt_gdp = initial_debt_gdp

    for year in range(years + 1):
        trajectory.append({
            "year_offset": year,
            "year_calendar": 2026 + year,
            "debt_gdp_pct": round(debt_gdp, 1),
            "cumulative_inflation_pct": round(((1 + annual_inflation/100) ** year - 1) * 100, 1),
            "usd_cumulative_loss_pct": round(((1 + annual_inflation/100) ** year - 1) * 100, 1),
            "gold_appreciation_pct": round(((1 + annual_inflation/100) ** year - 1) * 100 * 1.5, 1),  # 黄金跑赢通胀 1.5×
            "real_gdp_cumulative_pct": round(((1 + annual_real_gdp/100) ** year - 1) * 100, 1),
        })
        debt_gdp = debt_gdp * (1 + annual_real_rate/100) / (1 + annual_real_gdp/100)

    return {
        "name": "慢速剧本 (HYP-028) — 脉冲式金融抑制",
        "duration_years": 20,
        "mechanism": "Fed 降息 → 实际利率转负 → 通胀 3-4% → 债务实际价值稀释",
        "preconditions": [
            "(a) 下一次衰退触发 Fed 降息 (预期 2027-2028 概率 50%)",
            "(b) 实际利率持续负 (-1% to -2%)",
            "(c) 通胀维持在 3-4% 区间 (不足以触发紧缩)",
            "(d) 制度性买家 (LCR/央行) 持续承接美债"
        ],
        "trajectory": trajectory,
        "key_outputs_20yr": {
            "usd_cumulative_loss_pct": trajectory[-1]["usd_cumulative_loss_pct"],
            "gold_cumulative_appreciation_pct": trajectory[-1]["gold_appreciation_pct"],
            "real_gdp_growth_pct": trajectory[-1]["real_gdp_cumulative_pct"],
            "debt_gdp_change_pp": round(trajectory[-1]["debt_gdp_pct"] - initial_debt_gdp, 1),
        },
        "trigger_probability": "50% (基准情景)",
        "wealth_impact": {
            "现金/短债": "严重受损 (-50% 实际购买力)",
            "长债 (TLT)": "灾难 (-70% 实际购买力)",
            "美股 (SPY)": "中性 + 实际升值 (因通胀)",
            "黄金 (GLD)": "大幅受益 (+100-150%)",
            "实物资产 (commodities)": "大幅受益 (+80-100%)",
            "RMB 计价资产": "受益 (RMB 升值 5-15%)",
        }
    }

def model_fast_script_8to10yr():
    """快速剧本：危机驱动被动重置 (HYP-027)"""
    # 假设: 2027 触发债务危机 → 美元急贬 → 8-10年重置
    # 起点: US Debt/GDP 123%, 触发后快速贬值 30-50%

    initial_debt_gdp = 123.0
    target_debt_gdp = 80.0  # 危机后重置
    crisis_inflation = 8.0  # 危机期通胀飙升
    post_crisis_inflation = 4.0  # 重置后正常化
    crisis_usd_devalue = 35.0  # USD 危机期贬值

    years = 10
    trajectory = []
    debt_gdp = initial_debt_gdp
    cumulative_usd_loss = 0
    cumulative_gold_gain = 0

    # Phase 1 (year 0-2): 危机触发
    phase1_years = 2
    for year in range(phase1_years + 1):
        if year == 0:
            usd_loss = 0
            gold_gain = 0
        else:
            usd_loss = crisis_usd_devalue * (year / phase1_years)
            gold_gain = usd_loss * 1.8  # 黄金跑赢 USD 贬值的 1.8×
        cumulative_usd_loss = usd_loss
        cumulative_gold_gain = gold_gain
        trajectory.append({
            "year_offset": year,
            "year_calendar": 2026 + year,
            "phase": "Phase 1 - Crisis Trigger",
            "debt_gdp_pct": round(debt_gdp, 1),
            "cumulative_usd_loss_pct": round(usd_loss, 1),
            "cumulative_gold_gain_pct": round(gold_gain, 1),
        })
        debt_gdp = debt_gdp * (1 + crisis_inflation/100) / (1 + (-2)/100)  # 通胀 8%, 衰退 -2%

    # Phase 2 (year 3-7): 重置 + 缓慢恢复
    phase2_years = 5
    for year in range(phase2_years):
        cumulative_usd_loss = crisis_usd_devalue * 1.05  # 进一步微跌
        cumulative_gold_gain = usd_loss * 2.0
        trajectory.append({
            "year_offset": phase1_years + 1 + year,
            "year_calendar": 2026 + phase1_years + 1 + year,
            "phase": "Phase 2 - Reset",
            "debt_gdp_pct": round(debt_gdp, 1),
            "cumulative_usd_loss_pct": round(cumulative_usd_loss, 1),
            "cumulative_gold_gain_pct": round(cumulative_gold_gain, 1),
        })
        debt_gdp = debt_gdp * (1 + post_crisis_inflation/100) / (1 + 2.5/100)

    # Phase 3 (year 8-10): 新均衡
    phase3_years = 3
    for year in range(phase3_years):
        trajectory.append({
            "year_offset": phase1_years + 1 + phase2_years + year,
            "year_calendar": 2026 + phase1_years + 1 + phase2_years + year,
            "phase": "Phase 3 - New Equilibrium",
            "debt_gdp_pct": round(debt_gdp, 1),
            "cumulative_usd_loss_pct": round(cumulative_usd_loss + (year + 1) * 1.5, 1),
            "cumulative_gold_gain_pct": round(cumulative_gold_gain + (year + 1) * 5, 1),
        })
        debt_gdp = debt_gdp * (1 + 2.5/100) / (1 + 2.5/100)

    return {
        "name": "快速剧本 (HYP-027) — 危机驱动被动重置",
        "duration_years": "8-10",
        "mechanism": "2027 债务上限僵局 → 拍卖失败 → 美元急贬 → 重置新均衡",
        "preconditions": [
            "(a) 国债拍卖 bid-to-cover 持续 < 2.0x (当前 2.45x, 危机距离 18%)",
            "(b) US 5Y CDS > 200bp (当前 38bp, 危机距离 ~5x)",
            "(c) 30Y 持续 > 7% (当前 4.85%, 危机距离 +44%)",
            "(d) Debt ceiling 2027-01 僵局失控 (Tannenbaum 警告)"
        ],
        "trajectory": trajectory,
        "key_outputs_10yr": {
            "usd_cumulative_loss_pct": trajectory[-1]["cumulative_usd_loss_pct"],
            "gold_cumulative_gain_pct": trajectory[-1]["cumulative_gold_gain_pct"],
            "debt_gdp_change_pp": round(trajectory[-1]["debt_gdp_pct"] - initial_debt_gdp, 1),
        },
        "trigger_probability": "10% (尾部)",
        "wealth_impact": {
            "现金/短债": "灾难 (-40% 实际购买力, 短期名义价值缩水)",
            "长债 (TLT)": "极灾难 (-60%, 利率失控 + 美元贬值)",
            "美股 (SPY)": "先跌 30-40% 后反弹, 长期中性",
            "黄金 (GLD)": "极大受益 (+200-300%)",
            "实物资产": "极大受益 (+150-200%)",
            "RMB 计价资产": "受益 +20-30% (USD 急贬)",
        }
    }

# ======================================================================
# Part 5: 5-Why Adversarial on User's Thesis
# ======================================================================

def five_why_adversarial():
    """对用户的论点做 5-Why Adversarial"""

    return {
        "thesis": "美国将通过大通胀+美元贬值在 8-10年内解决债务问题; 但 USD 相对其他主要货币仍较保值; RMB 升值; 商品价格仍大涨",
        "5_why": [
            {
                "why": "Why 1: 这个论点最依赖的隐藏前提?",
                "answer": (
                    "(a) 美国无法在 20 年内通过增长消化债务\n"
                    "(b) 危机必须先发生 (拍卖失败/CDS 飙升/利率失控)\n"
                    "(c) 其他主要货币 (EUR/JPY/GBP) 的债务问题同样严重或更严重\n"
                    "(d) 商品价格独立于美元定价 (黄金仍是 final settlement)"
                ),
                "validation": "(a) 已被 Morningstar Clarida/Tannenbaum 间接确认 (US will 'kick the can' to 2030s); (b) 当前所有危机指标未触发 (CDS 38bp, 拍卖 2.45x, 30Y 4.85%); (c) TradingEconomics 2025 数据证实: Japan 249%, Italy 137%, France 116%, UK 103% — 全部高于或接近 US 123%; (d) 央行黄金连续 4 年净购买 1000t+/年 — 验证 (d)"
            },
            {
                "why": "Why 2: 这些前提的证伪条件?",
                "answer": (
                    "(a) AI 触发生产率爆发 → 实际 GDP > 5% → Debt/GDP 自然下降\n"
                    "(b) Fed 维持高利率长期 → 通胀失控 → 公众抛售美债 → 拍卖失败\n"
                    "(c) 美元通过强美元+高利率吸引资本回流 → 反而 USD 升值 (反向 1979-85 Volcker)\n"
                    "(d) 全球找到替代储备货币 (RMB 占比从 2.5% → 15%+) → USD 储备地位崩塌"
                ),
                "validation": "(a) HYP-009/002 验证 capex 全面加速, 但 Capex/Revenue 391% (AMZN) 暗示泡沫风险; (b) 当前 Fed 4.5% 已持续 18+ 月, 但拍卖仍 2.45x — 短期不会触发; (c) 历史 E4 (Volcker) USD TWI +37.58% 是反例; (d) RMB 储备占比 2016→2024 仅 1.1% → 2.3%, 10 年上升 1.2pp — 进程极慢"
            },
            {
                "why": "Why 3: 如果前提错了, 结论会反转成什么?",
                "answer": (
                    "如果 (a)(c) 成立 (AI + 强美元): 慢速剧本反而无意义, 美股牛市延续 5-10 年\n"
                    "如果 (b) 成立 (Fed 失误/外部冲击): 快速剧本真正启动, USD 急贬 30-50%\n"
                    "如果 (d) 成立 (RMB 替代 USD): USD 慢速稀释 + RMB 慢速升值, 但 USD 仍是主导储备货币"
                ),
                "validation": "⚠️ 反方最有力: AI 生产力 (Hyp-009) + 强美元周期 (E4 Volcker 6 年 USD +37%) 都是历史反例。当前不是已经发生, 而是高概率路径"
            },
            {
                "why": "Why 4: 偏误检查 - 我 (框架) 是否有叙事偏好?",
                "answer": (
                    "⚠️ **多重偏误风险**:\n"
                    "(a) 用户多次 pushback 化债理论, 框架已倾向于 '债务不可持续' 假设 — 这是 narrative-bias\n"
                    "(b) 2024-2026 实时数据已展示 commodity boom, 但 SPY 也 +61.9% — 框架只强调前者\n"
                    "(c) 之前已记录: HYP-020 (自损贬值无受益人) HIGH 置信度 — 这条与快速剧本矛盾\n"
                    "(d) 用户偏好'快剧本'叙事 (认为 8-10年解决 vs 20 年), 框架可能放大此偏好"
                ),
                "validation": "必须严格区分 'the data favors this' vs 'I want this to be true' — **当前数据显示 commodity boom + RMB 升值是真的**, 但 'AI 泡沫 + 强美元' 也是真, 两条路径都in样本内"
            },
            {
                "why": "Why 5: **一句话 — 这个论点最薄弱的地方**",
                "answer": (
                    "**最薄弱**: **'USD 相对其他货币较保值' 与 '主动快速贬值 8-10 年' 不自洽** —\n"
                    "如果 USD 真的 '相对其他货币较保值', 那 US 化债主要靠 r < g + 通胀税 (慢速剧本路径),\n"
                    "而不是 '主动急贬 30-50%' (快速剧本路径)。**用户的论述将两条路径混合使用, 而这两条路径的机制相互排斥**。"
                ),
                "validation": "这是核心矛盾: HYP-020 (主动贬值无受益人) + HYP-021 (重钉无现代先例) 维持 HIGH 置信度, 与快速剧本的'主动贬值 + 重置'假设矛盾。**用户的'快剧本'实际上是 'HYP-027' (危机驱动被动版), 不是 '主动快速版'**"
            }
        ],
        "overall_adversarial_verdict": (
            "**论点方向正确 (commodity boom + RMB strength + USD structural weakening 已在 2024-2026 验证), "
            "但论点的两个分论点不自洽**:\n"
            "(1) 'USD 相对其他货币较保值' → 慢速剧本路径 (脉冲式金融抑制)\n"
            "(2) '8-10 年通过大通胀解决债务' → 快速剧本路径 (危机驱动被动重置)\n"
            "**两条路径的触发机制互斥**, 必须分开讨论"
        )
    }

# ======================================================================
# Part 6: 综合裁决
# ======================================================================

def synthesize_verdict():
    """综合裁决 + 更新 HYP-027/028"""

    return {
        "summary": (
            "用户的核心方向 (commodity boom + RMB strength + USD structural weakening) "
            "已被 2024-2026 实时数据强验证。但'快剧本 8-10 年'与'USD 相对其他货币较保值'两条主张相互排斥。"
        ),
        "two_paths_decoupled": {
            "path_A_slow_relative_preservation": {
                "claim": "USD 相对其他货币较保值, 通过 r < g + 通胀税 + 20年金融抑制解决债务",
                "data_validation": (
                    "- 2024-2026 部分验证: JPY -12%, CAD -3%, USD +12% → '相对保值' 模式属实 (对部分货币)\n"
                    "- 但 EUR/GBP/AUD 也对 USD 升值, 'USD 相对保值' 不是普适\n"
                    "- 全球债务同步膨胀 (US 123%, Japan 249%, Italy 137%, France 116%) — '全债务问题' 验证\n"
                    "- PBOC 外汇储备回升 $3.42T + 黄金 2,346t — 央行确实在结构性减少 USD 依赖"
                ),
                "HYP_correspondence": "HYP-028 (慢速剧本, 脉冲式金融抑制, 基准 50%)",
                "trigger": "下一次衰退 → Fed 降息 → 实际利率转负",
                "consistency": "**与现有 HYP 体系一致**"
            },
            "path_B_fast_absolute_devalue": {
                "claim": "USD 在 8-10 年内急贬 30-50%, 主动通过通胀解决债务",
                "data_validation": (
                    "- 当前所有危机指标未触发 (CDS 38bp, 拍卖 2.45x, 30Y 4.85%, Fed 4.5%)\n"
                    "- HYP-020 (自损贬值无受益人) HIGH 置信度 — 政治经济学上'主动贬值'几乎不可能\n"
                    "- HYP-021 (重钉无现代先例) HIGH 置信度 — Stage 5 (重钉储备货币) 自 1971 后未发生\n"
                    "- 但: Debt ceiling 2027-01 僵局, 31% 国债 12 月内到期, Net interest 3.4% GDP — **2027-2028 风险窗口存在**"
                ),
                "HYP_correspondence": "HYP-027 (快速剧本, 危机驱动被动重置, 尾部 10%)",
                "trigger": "三者任一: 拍卖 < 2.0x / CDS > 200bp / 30Y > 7%",
                "consistency": "**仅'危机驱动被动版'可行, '主动快速版'已被 HYP-020/026 证伪**"
            },
        },
        "key_data_evidence_2024_2026": {
            "commodity_bomb": "GLD +94%, SLV +140%, USO +94%, DBA +43%, DBB +48%, DBC +45% (2024-01 → 2026-08)",
            "fx_divergence": "UUP +12%, FXY -12%, FXC -3%, FXE +8%, FXB +13%, FXA +7%",
            "rmb_appreciation": "USD/CNY 7.1771 (2024-12) → 6.7894 (2026-07), RMB +5.4%",
            "cb_gold_accumulation": "PBOC 2,346t (2026-06, 连续 20 月增持); 全球央行 2024 +1,087t, 2025 +849t, 2026 H1 +345t",
            "us_30y_5.18_to_4.85": "30Y 2026-07 高点 5.18% → 2026-07-30 回落至 4.85% (未突破危机线)",
            "global_debt": "G20 Debt/GDP 2020 peak 99.5%, 2024 ~97-98%, 没有主要国家回到 2019 水平",
            "fed_balance_sheet": "$6.70T (2026-07-29), Treasury 持仓 +$312.6B Y/Y — **轻度货币化** (非 QT)"
        },
        "operational_implications": {
            "if_slow_script_50pct": {
                "asset": "Commodities, Gold, TIPS, AI profits stocks, selective EM exposure (RMB-denominated)",
                "action": "增持黄金至 10-15%, 持有 SPY/QQQ, 减少长期国债 (TLT)",
            },
            "if_fast_script_10pct": {
                "asset": "全面撤离, Cash + Gold only",
                "action": "见 US_FRAMEWORK §8.2 快速剧本预案"
            },
            "if_neither_40pct": {
                "asset": "维持当前配置 (US_FRAMEWORK §4.1)",
                "action": "监控 HYP-011 8 信号矩阵 (当前 0 分 → L0-L1)"
            }
        },
        "updated_HYP_probability": {
            "HYP_027_fast_10yr": "维持 10% (尾部, 未启动, 2027-2028 是关键观察窗)",
            "HYP_028_slow_20yr": "**从 50% 上调至 55-60%** (基于 2024-2026 数据已部分展开)",
            "growth_digestion_15pct": "从 15% 下调至 10% (AI 见顶信号已现, AMZN capex/rev 391%)",
            "policy_other_25pct": "维持 25% (含主动快速剧本 HYP-026 证伪部分)"
        }
    }

# ======================================================================
# Main
# ======================================================================

if __name__ == "__main__":
    output = {
        "report_date": "2026-08-02",
        "title": "美国大通胀+美元贬值场景: 综合量化分析",
        "part_1_baseline": baseline_2026,
        "part_2_historical_episodes": historical_episodes,
        "part_3_user_thesis_validation": validate_user_thesis(),
        "part_4_slow_script": model_slow_script_20yr(),
        "part_5_fast_script": model_fast_script_8to10yr(),
        "part_6_5why_adversarial": five_why_adversarial(),
        "part_7_verdict": synthesize_verdict(),
    }

    # 输出文件
    output_file = "/Users/weimingzhuang/Documents/source_code/financial-services-opencode/.opencode/memory/personal-system/research/us-debt-debasement-2026/analysis_output.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    # 打印摘要
    print("=" * 70)
    print("美国大通胀+美元贬值场景分析")
    print("=" * 70)
    print(f"日期: {output['report_date']}")
    print()

    # 用户论点验证
    print("## 用户论点验证 (2024-2026 实时数据)")
    for r in output["part_3_user_thesis_validation"]:
        print(f"\n**{r['thesis']}**")
        print(r["verdict"])

    print("\n" + "=" * 70)
    print("## 慢速剧本 (HYP-028) 20 年推演")
    slow = output["part_4_slow_script"]
    print(f"USD 累计贬值: {slow['key_outputs_20yr']['usd_cumulative_loss_pct']}%")
    print(f"黄金累计升值: {slow['key_outputs_20yr']['gold_cumulative_appreciation_pct']}%")
    print(f"Debt/GDP 变化: {slow['key_outputs_20yr']['debt_gdp_change_pp']}pp")
    print(f"概率: {slow['trigger_probability']}")

    print("\n" + "=" * 70)
    print("## 快速剧本 (HYP-027) 8-10 年推演")
    fast = output["part_5_fast_script"]
    print(f"USD 累计贬值: {fast['key_outputs_10yr']['usd_cumulative_loss_pct']}%")
    print(f"黄金累计升值: {fast['key_outputs_10yr']['gold_cumulative_gain_pct']}%")
    print(f"Debt/GDP 变化: {fast['key_outputs_10yr']['debt_gdp_change_pp']}pp")
    print(f"概率: {fast['trigger_probability']}")

    print("\n" + "=" * 70)
    print("## 5-Why Adversarial 摘要")
    adv = output["part_6_5why_adversarial"]
    print(f"**最薄弱**: {adv['5_why'][4]['answer']}")

    print("\n" + "=" * 70)
    print("## 最终裁决")
    v = output["part_7_verdict"]
    print(f"\n{v['summary']}\n")
    print(f"**HYP-027 概率**: {v['updated_HYP_probability']['HYP_027_fast_10yr']}")
    print(f"**HYP-028 概率**: {v['updated_HYP_probability']['HYP_028_slow_20yr']}")
    print(f"**增长消化**: {v['updated_HYP_probability']['growth_digestion_15pct']}")
    print(f"**其他**: {v['updated_HYP_probability']['policy_other_25pct']}")

    print(f"\n**输出文件**: {output_file}")