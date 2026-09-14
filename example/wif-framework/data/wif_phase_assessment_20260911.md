# WIF v5.9 五层读数 — 2026-09-11

> 由 `out/hedge_fund_backtest/wif_assessment.py` 自动生成（可复跑）。
> 数据：`_merged_prices_20260911.csv`（4966×10，2007-01-03 → 2026-09-11）+ Tier-1 MCP 宏观读数。

| 层 | 指标 | 现值 | 阈值 / 判据 | 状态 |
| --- | --- | --- | --- | --- |
| ① 硬触发 | F29（BAA10Y） | **151 bp**（09-10） | >500bp → EMERGENCY | 🟢 未触发（距线 349bp） |
| ① | VIX + 10日涨幅 | **15.84 / +9.2%** | VIX>40 且 >+100% | 🟢 未触发 |
| ② CSI | Z(VIXTERM_60d) | **+0.14** ×0.35 = **+0.048** | — | 🟢 |
| ② | −Z(SPY/GLD 20日相关) | **-1.65** ×0.20 = **-0.329** | — | 🟢 无断裂 |
| ② | Z(F29_60d) ×0.45 | **算不出** | 需 60 日每日序列 | ⚠️ 缺口 |
| ② | **CSI 合计** | **-0.281**（仅 55% 权重） | >2 EMERGENCY / >1 WARNING / <1 HEALTHY | 🟢 **HEALTHY** |
| ③ 象限 | SPY 126d 动量 60日均值 | **+12.1%** | >0 = Rising | 🟢 |
| ③ | TLT 126d 动量 60日均值 | **-4.2%** | >0 = Rising | 🟠 |
| ③ | **宏观象限** | **Q2 Overheat（过熟/晚周期）** | 股涨 + 债涨 | 🟠 晚周期 |
| ④ 相位 | Phase1_status | **HEALTHY** | 连 3 日确认才切换 | 🟢 维持 |
| ④ | **最终相位** | **Phase 1 · Rising（上升期）** | 权益 65-75% / 固收 10-15% / 实物 15-25% | 🟢 **risk-on** |
| ⑤ 再平衡 | 相位切换 | **无** | 切换→次日收盘；常规→每 15 交易日；MCI<+5→VTI-only | ⚪ 无需动作 |

## 辅助印证（FRED 实测，0 credit）

| 指标 | 值 | 日期 | 源 |
|---|---:|---|---|
| vix_spot | 15.84 | 2026-09-11 | ^VIX via llmquant-data |
| us10y | 4.95 | 2026-09-10 | FRED DGS10 |
| us30y | 5.37 | 2026-09-10 | FRED DGS30 |
| us2y | 4.62 | 2026-09-10 | FRED DGS2 (implied 10y-2y=+0.33) |
| curve_10y_2y | 0.33 | 2026-09-11 | FRED T10Y2Y |
| breakeven_10y | 2.36 | 2026-09-11 | FRED T10YIE |
| real_10y | 2.59 | 2026-09-11 | computed 4.95 - 2.36 |
| nfci | -0.56 | 2026-08-28 | FRED NFCI |
| stl_fin_stress | -0.7884 | 2026-09-04 | FRED STLFSI4 |
| dxy_broad | 118.0732 | 2026-09-04 | FRED DTWEXBGS |
| wti | 97.26 | 2026-09-09 | FRED DCOILWTICO |
| fed_funds | 3.63 | 2026-08-01 | FRED FEDFUNDS |
| brent | 101.21 | 2026-09-09 | 记忆库 4.2（新华社） |
| fear_greed | 57 | 2026-09-14 | Alternative.me F&G via vibe-trading |

## ★ 跨市场背离（本轮最值得记）

| 线 | 方向 | 最新 | 趋势 |
|---|---|---|---|
| 企业信用 Corporate credit (F29) | 改善 | 151 bp | 165 → 159 → 151 bp |
| 主权信用 Sovereign credit (US30Y) | 恶化 | 5.37% | 2007 年以来新高 |
| 权益/波动 Equity / vol | 平静 | VIX 15.84 | SPY 126d +20.9% |

## F29 历史锚点

| 日期 | F29 (bp) | 源 |
|---|---:|---|
| 2026-05-08 | 165 | CreditSpread_BAA_1986_2026.csv |
| 2026-07-16 | 159 | wif_phase_assessment_20260717.json |
| 2026-09-10 | 151 | FRED BAA10Y |

## ⚠️ 缺口与效力声明

- **CSI 仅 55% 权重**：本地矩阵无 F29 列，`compute_csi` 明写「缺失分量按 0 计且不重缩放」
- **不可与 WIF 历史业绩对照**：Sharpe 1.01 是用 100% CSI 回测的
- **BAA10Y 是投资级利差**，可能不覆盖 AI 相关杠杆（ORCL D/E 3.63 / CRWV D/E 8.94）
- 补 Z(F29_60d)：需 60 日每日 BAA10Y（`macro_indicator_history` 或 FRED CSV）
