---
name: ai-hedge-fund-fundamental-ls
description: ai-hedge-fund "Fundamental L/S" mandate（旗舰，5 位 agent 全员，市场中性多空）。buffett + munger + graham + lynch + druckenmiller 对 universe 排名，做多最受青睐、做空最不受青睐。当用户问"fundamental long short"、"市场中性基本面"、"多空组合"、"5 位投资人投票"时加载。
category: analysis
---

# Fundamental L/S — ai-hedge-fund mandate

> 来源：`ai-hedge-fund/hedge_fund/strategies/fundamental-ls.yaml`
> **风格化近似** —— 非本人、非背书。仅研究用途。

## Mandate 定义

```yaml
# Fundamental long/short — the flagship discretionary pod.
# All five agents rank the universe; the sleeve is market-neutral: long the
# names the desk likes most relative to the rest, short the least liked.
# Edge claimed: collective judgment ranks names better than the market
# prices them.
name: fundamental-ls
display_name: Fundamental L/S
models:
  - name: buffett
  - name: munger
  - name: graham
  - name: lynch
  - name: druckenmiller
blend:
  method: conviction_weighted
  gross_target: 1.0
  market_neutral: true
```

## 组合构成

| model | weight | 备注 |
|---|---:|---|
| `buffett` | 1.0 |  |
| `munger` | 1.0 |  |
| `graham` | 1.0 |  |
| `lynch` | 1.0 |  |
| `druckenmiller` | 1.0 |  |

**Blend 方法：** `conviction_weighted`，`gross_target: 1.0`
**中性说明：** **市场中性**（market_neutral: true）—— 多空对冲，暴露于 alpha 而非 beta

## 何时用 / 何时不用

| ✅ 适合 | ❌ 不适合 |
|---|---|
| 多空组合 / 市场中性 / 需要多视角投票 / universe 排名（≥10 只标的）。 | 单一标的（无 cross-section）/ 纯多头 / 方向性择时。 |

**Edge claimed：** 集体判断对标的的排名优于市场定价

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
