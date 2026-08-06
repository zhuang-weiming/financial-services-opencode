# g_nominal vs i Mechanism — 月度监控表

> **目的**: 每月填入实际 FRED 数据, 验证化债机制是否在运行
> **使用频率**: 每月 1 号（与 US_FRAMEWORK 月度检查同步）
> **配套脚本**: `g_nominal_vs_i_mechanism.py` (重新运行并比较)

---

## 月度监控表（模板）

| 月份 | GS10 (%) | CPI YoY (%) | Real GDP Growth (%) | g_nominal (%) | i - g_nominal (pp) | Primary Deficit (% GDP) | ΔDebt/GDP (actual, pp) | ΔDebt/GDP (model, pp) | 误差 | 情境判断 |
|:----:|:--------:|:-----------:|:-------------------:|:-------------:|:------------------:|:----------------------:|:---------------------:|:---------------------:|:----:|:---------|
| 2026-08 | 4.20 | 3.00 | 1.80 | 4.80 | -0.60 | +6.50 | +0.32 (月化) | +0.32 | 0.00 | S1 基线 |
| 2026-09 | | | | | | | | | | | |
| 2026-10 | | | | | | | | | | | |
| 2026-11 | | | | | | | | | | | |
| ... | | | | | | | | | | | |

---

## 决策规则（何时升级行动）

### 规则 1: 慢剧本启动 (HYP-028 真正激活)
**触发条件**: i - g_nominal < 0 持续 6 月 AND primary_deficit < 5%

**当前状态**: 
- i - g_nominal = -0.60pp (符合负数条件)
- primary_deficit = +6.5% (不符合 < 5% 条件)
- **结论**: 慢剧本**未激活**，但 rate effect 已轻微帮化债

**激活后行动**:
- 增加黄金配置至 20%（当前 15-20%）
- 维持美股 AI 利润股 (MSFT/GOOGL/META)
- 减少长债 (TLT) 至 0%

### 规则 2: 危机被动 (HYP-027 触发)
**触发条件**: 任一满足
- GS10 > 7% 持续 1 月
- 国债拍卖 bid-to-cover < 2.0x 持续
- US 5Y CDS > 200bp
- Debt ceiling 2027-01 僵局恶化

**当前状态**:
- GS10 = 4.20% (远低于 7%)
- 拍卖 ~2.45x (高于 2.0x)
- CDS ~38bp (远低于 200bp)
- **结论**: **未触发**，但 2027-01 是关键观察窗

**触发后行动**:
- 全面撤离美股 → 现金 + 黄金 100%
- 8-10 年等待「价值重置」完成
- A 股仓位不受影响

### 规则 3: 增长消化剧本胜出
**触发条件**: GDPC1 > 4% 持续 4 季度 AND primary_deficit < 4%

**当前状态**:
- GDPC1 = 1.8% (远低于 4%)
- primary_deficit = +6.5% (远高于 4%)
- **结论**: 未触发

**触发后行动**:
- 维持美股 + 黄金 (无需快速重置)
- HYP-027 tail hedge 解除

### 规则 4: 漂移失效 (慢剧本数学失败)
**触发条件**: GDPC1 < 1% 持续 + i - g_nominal > 0 (慢剧本无法工作)

**当前状态**:
- GDPC1 = 1.8% (接近临界)
- i - g_nominal = -0.60pp (慢剧本仍微弱工作)
- **结论**: **未触发**，但需密切监控

**触发后行动**:
- 增加 HYP-027 tail hedge 至 5-10%
- 关注 2027-01 债务上限
- 准备执行紧急预案

---

## 关键 FRED 系列追踪

| FRED ID | 名称 | 当前 | URL | 更新频率 |
|:--------|:-----|:----:|:----|:--------:|
| **GS10** | 10Y Treasury | 4.20% | https://fred.stlouisfed.org/series/GS10 | 月 |
| **CPIAUCSL** | CPI YoY | 3.00% | https://fred.stlouisfed.org/series/CPIAUCSL | 月 |
| **GDPC1** | Real GDP | 1.80% | https://fred.stlouisfed.org/series/GDPC1 | 季度 |
| **GDP** | Nominal GDP | — | https://fred.stlouisfed.org/series/GDP | 季度 |
| **GFDEGDQ188S** | Debt/GDP | 123% | https://fred.stlouisfed.org/series/GFDEGDQ188S | 季度 |
| **FGDEF** | Federal Deficit | -6.5% GDP | https://fred.stlouisfed.org/series/FGDEF | 季度 |

---

## 季度观察补充

每季度（1/4/7/10 月 1 日）补充以下数据：

| 季度指标 | 数据源 | 当前 | 重要性 |
|:--------|:-------|:----:|:------:|
| Fed Balance Sheet Treasury 持仓 | FRED 或 Federal Reserve H.4.1 | $4.52T | 监测货币化 |
| TIC 海外持有美债 | Treasury TIC 月度 | 约 $7T | 监测资本外流 |
| US 5Y CDS | USGV5YUSAB=R | 38bp | 监测信用 |
| 国债拍卖 bid-to-cover | Treasury Direct | 2.45x | 监测需求 |
| 央行黄金购买 (WGC) | WGC Quarterly | +849t (2025) | 监测去美元化 |

---

## 历史对比快查表

| 时期 | i (10Y) | π (CPI) | Real Rate | g_real | g_nom | i - g_nom | primary | Δ/yr Debt/GDP |
|:-----|:-------:|:-------:|:---------:|:------:|:-----:|:---------:|:-------:|:-------------:|
| **1946-74** | 4.72% | 3.02% | **+1.70%** | 4.00% | 7.02% | **-2.30pp** | -1.44% | **-3.15pp/年** |
| 2020-26 | 3.50% | 4.20% | -0.70% | 2.00% | 6.20% | -2.70pp | +6.84% | **+3.83pp/年** |
| **2026 baseline** | 4.20% | 3.00% | **+1.20%** | 1.80% | 4.80% | -0.60pp | +6.50% | **+5.83pp/年** (估) |
| 慢剧本触发条件 | < 4.0% | 维持 3-4% | < 0 | ≥ 2.5% | ≥ 6% | < -2pp | < 5% | < 0 |

---

## 重新运行脚本的步骤

```bash
cd /Users/weimingzhuang/Documents/source_code/financial-services-opencode/.opencode/memory/personal-system/research/g-nominal-vs-i-mechanism

# 1. 更新 PERIOD_2020_26 和 BASELINE_2026 的数据
# 2. 编辑 g_nominal_vs_i_mechanism.py 修改以下字段:
#    - PERIOD_2020_26: gs10_avg_pct, cpiaucsl_avg_pct, real_gdp_growth_avg_pct, debt_gdp_*, primary_deficit
#    - BASELINE_2026: gs10_pct, cpi_yoy_pct, real_gdp_growth_pct
# 3. 运行脚本
python3 g_nominal_vs_i_mechanism.py

# 4. 检查输出:
#    - 1946-74 model_OK: True (验证模型仍有效)
#    - 2020-26 model_OK: True (验证模型仍有效)
#    - 5 场景预测 vs 上月变化
# 5. 更新 report.md 附录 (实际 vs 预测)
# 6. 检查 4 条决策规则 (规则 1-4)
# 7. 记录到 raw-log/YYYY-MM-DD.md (如有重大变化)
```

---

## 关联 HYP 与 CONFLICT

| 项目 | 关联 | 关联强度 |
|:-----|:----|:--------:|
| **HYP-028** (慢剧本) | 核心监控 | HIGH |
| **HYP-027** (危机被动) | tail hedge | MEDIUM |
| **HYP-029** (全球去美元化) | 补充 Path B | MEDIUM |
| **CONFLICT-LOGIC-007** | 慢剧本经济基线 vs 政治现实基线 | HIGH |
| **3.US_FRAMEWORK.md §1.3** | 化债双剧本观察表 | HIGH |
| **3.US_FRAMEWORK.md §5** | 月度检查清单 | HIGH |

---

## 关键启示（最后一遍）

> **1946-74 化债不是靠「金融抑制」(实际利率为负)。**
>
> **是靠 g_nominal (7%) > i (4.72%)，差距 -2.30pp。**
>
> **真正驱动是 g_real = 4%（婴儿潮 + 战后重建）。**
>
> **2026 同机制可运行但 g_real 仅 2%。**
>
> **完成 -88pp 需要 ~110 年（vs 1946-74 的 28 年）。**
>
> **慢剧本在政治可观察周期（4-8 年）内不可见。**
>
> **这意味着：** 您的「快剧本必要」论点**数学上正确**，但**AI 不能执行**（Waller 2026-02-24）。
>
> **真正的快速路径：** AI 见顶 → g_real 跌至 1% → 慢剧本数学失败 → HYP-027 危机被动触发。
>
> **操作：** 监控 g_real（GDPC1）而非 i（GS10）；黄金 + 商品超配；HYP-027 tail hedge 2-3%。

---

*模板生成: 2026-08-02*  
*配套脚本: `g_nominal_vs_i_mechanism.py`*  
*配套报告: `report.md`*  
*数据输出: `analysis_output.json`*