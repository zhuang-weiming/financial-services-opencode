---
name: ai-hedge-fund-deep-value
description: ai-hedge-fund "Deep Value" mandate（Graham 主导的长期偏多 discretionary pod）。graham(2.0) + buffett + munger，conviction_weighted 混合。当用户问"deep value 分析"、"深度价值策略"、"格雷厄姆式选股"、"安全边际组合"时加载。
category: analysis
---

# Deep Value — ai-hedge-fund mandate

> 来源：`ai-hedge-fund/hedge_fund/strategies/deep-value.yaml`
> **风格化近似** —— 非本人、非背书。仅研究用途。

## Mandate 定义

```yaml
# Deep value — discretionary, long-biased, quarterly horizon.
# Graham leads (double blend weight); Buffett and Munger keep quality in
# the mix. Edge claimed: mispriced quality with a margin of safety.
name: deep-value
display_name: Deep Value
models:
  - name: graham
    weight: 2.0
  - name: buffett
  - name: munger
blend:
  method: conviction_weighted
  gross_target: 1.0
```

## 组合构成

| model | weight | 备注 |
|---|---:|---|
| `graham` | 2.0 | 主导（双倍权重） |
| `buffett` | 1.0 |  |
| `munger` | 1.0 |  |

**Blend 方法：** `conviction_weighted`，`gross_target: 1.0`
**中性说明：** **非市场中性** —— 长期偏多（long-biased），gross_target 1.0

## 何时用 / 何时不用

| ✅ 适合 | ❌ 不适合 |
|---|---|
| 深度价值 / 安全边际优先 / 长期偏多 / 季度持有期。适合：低估值蓝筹、破净股、周期底部。 | 成长股 / 高估值科技 / 短线 / 需要快速兑现的主题。 |

**Edge claimed：** 被错误定价的高质量 + 安全边际

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
