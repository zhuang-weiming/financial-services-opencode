---
name: ai-hedge-fund-earnings-drift
description: ai-hedge-fund "Earnings Drift" mandate（PEAD 系统化 pod，事件时间）。单模型 pead——EPS BEAT 后做多、MISS 后做空，赌市场对意外反应不足。当用户问"earnings drift"、"PEAD"、"财报后漂移"、"盈利意外策略"时加载。
category: analysis
---

# Earnings Drift — ai-hedge-fund mandate

> 来源：`ai-hedge-fund/hedge_fund/strategies/earnings-drift.yaml`
> **风格化近似** —— 非本人、非背书。仅研究用途。

## Mandate 定义

```yaml
# Earnings drift — systematic, event-time.
# Post-earnings announcement drift: the market underreacts to surprises for
# days. The model is the strategy; no one is pretending it has opinions.
name: earnings-drift
display_name: Earnings Drift
models:
  - name: pead
blend:
  method: conviction_weighted
  gross_target: 1.0
```

## 组合构成

| model | weight | 备注 |
|---|---:|---|
| `pead` | 1.0 | 唯一模型 |

**Blend 方法：** `conviction_weighted`，`gross_target: 1.0`
**中性说明：** **纯系统化** —— "模型即策略，无人假装它有观点"

## 何时用 / 何时不用

| ✅ 适合 | ❌ 不适合 |
|---|---|
| 财报季 / 事件驱动 / 系统化（无主观）/ 短线（信号窗 4 天）。 | 无财报事件时（模型 abstain）/ 需要基本面深度判断时。 |

**Edge claimed：** 市场对盈利意外的**反应不足**（PEAD 异象）

## PEAD 模型逻辑（`signals/pead.py`）

| 参数 | 默认 | 说明 |
|---|---|---|
| `earnings_limit` | 8 | 取最近 8 条财报记录 |
| `signal_window_days` | 4 | 财报 filed 后 **4 天内**才发信号 |

**信号：**
- EPS **BEAT** → `value = +1.0`（做多）
- EPS **MISS** → `value = -1.0`（做空）
- 无合格事件 / 事件过期 → `value = 0.0`（无观点）

**数据清洗（关键）：**
1. **45 天回溯过滤**：`filing_date - report_period ≥ 45 天` 的记录丢弃（提取器常从当前 8-K 误解析上一季度对比数据）
2. **来源优先级**：`8-K (0) > 10-Q (1) > 10-K (2) > 20-F (3)` —— 同一报告期保留最高优先级（8-K = 最早的公告）
3. **每报告期一个事件**（去重）

**时点纪律：** 只用 `filing_date ≤ date` 的记录（无 lookahead）

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
