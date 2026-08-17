# probability-objectification-2026 — 剧本概率客观化（三算法 + 蒙特卡洛）

> **来源迁移**：2026-08-17 从 `out/probability_objectification/`（临时工作目录，用户将删除 `out/`）迁入本目录。全部 16 个文件为**唯一权威副本**。
> **服务对象**：报告 `reports/ai-bubble-inflation-historical-analogues-2026-08-13.md` §5.3/§5.3.1/§5.3.2/§5.4.1/§5.7
> **质控记录**：`raw-log/2026-08-17-probability-objectification.md`（5-Why：MODERATE 置信度 + 3 caveat）

---

## 1. 算法定位

| 组件 | 角色 | 输出 |
|------|------|------|
| `prepare_anchor_data.py` | Step 0：从本地真实数据构建锚点特征表 | `anchor_features.csv`（4 锚点 × 7 特征）+ `current_snapshot.csv` + `anchor_source_notes.json` |
| `alg1_signal_scoring.py` | **Alg1 信号计分**：报告 4 变量 X1-X4 状态概率加权 | `alg1_signal_scoring.json` |
| `alg2_bayesian_update.py` | **Alg2 贝叶斯更新**：主观先验 × 真实数据似然 → 后验 | `alg2_bayesian_update.json` |
| `alg3_historical_similarity.py` | **Alg3 历史相似**：当前宏观态 vs 4 锚点距离 → 相似度 → 映射矩阵 | `alg3_historical_similarity.json` |
| `consolidate.py` | 汇总三算法 + 原主观概率 → 三法均值 → 表格 | `final_consolidated.json` + `final_table.md` |
| `alg4_monte_carlo.py` | **Alg4 蒙特卡洛（不确定性层）**：扰动输入 ×3000 次重算 → CI/头号概率/稳健性 | `alg4_monte_carlo.json` |
| `alg4_sigma2x_sensitivity.json` | σ×2 敏感性测试（seed 999）：扰动分布加倍是否翻盘 | 稳健性证据 |

**一句话**：Alg1-3 是三个独立点估计方法，`consolidate` 取三者均值；**Alg4 不是第 4 个点估计**，而是包裹 Alg1-3 的稳健性层，回答"输入微调后结论翻不翻盘"。

## 2. 重跑方法

```bash
# 前提：数据依赖存在（见 §3），Python 3.10+，pandas/numpy
cd .opencode/memory/personal-system/research/probability-objectification-2026/

# 0) 重建锚点特征表（如 FRED CSV 更新后）
python3 prepare_anchor_data.py

# 1) 三算法（按序）
python3 alg1_signal_scoring.py
python3 alg2_bayesian_update.py
python3 alg3_historical_similarity.py

# 2) 汇总
python3 consolidate.py          # 重写 final_consolidated.json + final_table.md

# 3) 蒙特卡洛（种子 20260817，3000 iters，约 1-2 分钟）
python3 alg4_monte_carlo.py
```

> **说明**：所有脚本的 `OUT` 均已改为 `Path(__file__).resolve().parent`（自定位）——迁移自 `out/` 时修复了 6 处硬编码绝对路径。**从任何位置拷贝本目录到别处均可直接重跑，不会写回 `out/`。**

## 3. 数据依赖（本地真实数据，全部在仓库内）

| 数据 | 位置 | 用途 |
|------|------|------|
| FRED 批量下载 | `.opencode/memory/personal-system/research/historical-devaluation-events/_shared/fred/` — CPIAUCSL / DGS10 / FEDFUNDS / DCOILWTICO / REAINTRATREARAT10Y / SP500 | 锚点窗口 1947-2015 |
| WIF 框架 tickers | `example/wif-framework/data/tickers_20260716/` — DGS10_2007_2026 / T10YIE_2007_2026 / CreditSpread_BAA_1986_2026 | 补 2016-2026 缺口 + 利差 |
| 报告 §5.1 快照 | 报告正文（2026-08-16：CPI 3.4% / 10Y 4.63% / FFR 3.63% / WTI 82.55 / 黄金 4391.80） | `current_snapshot.csv` |
| 4.2 五信号表 | 报告 §4.2（2026-08-04 触发性概率） | Alg1/Alg2 的 X1 状态概率 |

锚点窗口：1971.8（Nixon Shock / stage-2 起点）、2000.3（dot-com 顶）、2007.10（GFC 前顶）、2021.6-2022.6（mini 滞胀）。

## 4. 结果摘要（2026-08-17 生成）

### 三法均值 vs 原主观（`final_table.md`）

| 剧本 | 原主观 | 三法均值 | Δ |
|:-----|:---:|:---:|:---:|
| A 老剧本 | 30.0% | **16.3%** | -13.7pp |
| B AI 化解 | 30.0% | **29.0%** | -1.0pp |
| C 滞胀失控 | 15.0% | **15.4%** | +0.4pp |
| D 通缩破裂 | 25.0% | **39.3%** | **+14.3pp** |

### 蒙特卡洛（`alg4_monte_carlo.json`，3000 iters, seed 20260817）

- D 95% CI **[31.5, 44.2]%**，头号概率 **91.7%**
- A P(A>25%) = **0.0%**（A 被客观数据排除）
- B CI 最宽 [21.3, 34.7]%，8.3% 可反超 D
- 配置建议取 **MC 中位数（D≈37%）** 而非点估计 39.3%
- **σ×2 敏感性**（seed 999）：A>25% → 1.6%，D 头号 → 85.2%，D CI → [29.9, 44.4]% —— 核心排序结论稳健

## 5. 已知限制（5-Why 质控 caveat）

1. **Alg3 锚点→剧本映射矩阵**是人为设定（5-Why 标记为最脆弱组件）——MC 已对该矩阵加扰动，结论仍稳健。
2. **Alg3 z-score 样本小**（4 锚点 + 当前 = 5 行），距离度量仅作相似度参考。
3. **1971.8 锚点缺 3 特征**（real10/wti/credit），其相似度可靠性低于其他锚点。
4. 黄金锚点值来自报告 §2.1 / WGC 史（`[UNSOURCED-local]`），非 FRED 直接数据。
5. 蒙特卡洛输入扰动分布（WTI σ4.0 / FFR σ0.25 / CPI σ0.30 / 信号 σ0.08）是**模型选择**，非真实不确定性度量。

## 6. 关联文件

- 报告：`reports/ai-bubble-inflation-historical-analogues-2026-08-13.md`（§5.3.1 三算法 / §5.3.2 MC 通俗版 / §5.4.1 敏感性 / §5.7 #1 边界）
- 质控：`raw-log/2026-08-17-probability-objectification.md`
- 上游数据：`research/historical-devaluation-events/_shared/fred/`、`example/wif-framework/data/tickers_20260716/`
