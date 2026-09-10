---
name: ai-hedge-fund-inflections
description: ai-hedge-fund "Inflections" mandate（基本面变化率多空）。druckenmiller + lynch 在倍数重定价之前捕捉加速与恶化。当用户问"inflections"、"拐点策略"、"基本面加速/恶化"、"变化率交易"时加载。
category: analysis
---

# Inflections — ai-hedge-fund mandate

> 来源：`ai-hedge-fund/hedge_fund/strategies/inflections.yaml`
> **风格化近似** —— 非本人、非背书。仅研究用途。

## Mandate 定义

```yaml
# Inflections — discretionary long/short on fundamentals rate-of-change.
# Druckenmiller and Lynch hunt acceleration and deterioration before the
# multiple reprices it.
name: inflections
display_name: Inflections
models:
  - name: druckenmiller
  - name: lynch
blend:
  method: conviction_weighted
  gross_target: 1.0
```

## 组合构成

| model | weight | 备注 |
|---|---:|---|
| `druckenmiller` | 1.0 | 拐点 |
| `lynch` | 1.0 | 分类/GARP |

**Blend 方法：** `conviction_weighted`，`gross_target: 1.0`
**中性说明：** **多空**（未声明 market_neutral，但含做空能力）

## 何时用 / 何时不用

| ✅ 适合 | ❌ 不适合 |
|---|---|
| 拐点捕捉 / 基本面加速或恶化 / 多空 / 中短线（倍数重定价前）。 | 稳定成熟期公司（无拐点）/ 纯价值（Graham 不在场）。 |

**Edge claimed：** 在倍数重定价之前捕捉基本面的加速/恶化

## 混合规则（conviction_weighted）

```
sleeve_score(ticker) = Σ [ weight_i × value_i(ticker) ] / Σ weight_i
                      （仅对 value_i ≠ 0 的模型求和，abstain 的模型不计）
```

- 每个 model 产 `value ∈ [-1,+1]`（见各 persona skill）
- `gross_target: 1.0` = 有观点时 |weights| 之和目标为 1.0（无杠杆）
- `market_neutral: true` → 多空对冲（仅 fundamental-ls）

## 如何应用（无需 aihf）

1. **逐 persona 打分**：对每只标的，加载对应 persona skill，用 `build_snapshot.py` 的快照打分
2. **加权混合**：按上表权重算 `sleeve_score`
3. **排序**（多空 mandate）：`fundamental-ls` / `inflections` 做多 top、做空 bottom
4. **注意**：单一标的无 cross-section 时，多空 mandate 退化为主观判断

## 诚实边界
- persona 是风格化近似，非本人意见
- 快照仅 TTM 基本面（无宏观/新闻/技术）
- **输出 view 非交易指令**；仓位由组合构建决定

## 相关
- master：`ai-hedge-fund`
- 成员 persona：见上表各 `ai-hedge-fund-<persona>`
