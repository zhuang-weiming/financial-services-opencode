# 4 个 mandate 对照

> 来源：`ai-hedge-fund/hedge_fund/strategies/*.yaml`

| mandate | 成员 (weight) | 类型 | 中性 | Edge claimed | Skill |
|---|---|---|---|---|---|
| **deep-value** | graham(2.0) + buffett + munger | discretionary 长期偏多 | ❌ long-biased | 被错误定价的高质量 + 安全边际 | `ai-hedge-fund-deep-value` |
| **earnings-drift** | pead | systematic 事件时间 | — | 市场对盈利意外反应不足（PEAD）| `ai-hedge-fund-earnings-drift` |
| **fundamental-ls** | 全部 5 位 (各 1.0) | discretionary 旗舰 | ✅ market_neutral | 集体判断排名优于市场定价 | `ai-hedge-fund-fundamental-ls` |
| **inflections** | druckenmiller + lynch | discretionary 多空 | 多空（未声明中性）| 倍数重定价前捕捉加速/恶化 | `ai-hedge-fund-inflections` |

## 混合规则（conviction_weighted）

```
sleeve_score(ticker) = Σ [ weight_i × value_i ] / Σ weight_i
                       （仅对 value_i ≠ 0 的模型；abstain 不计）
```

- `gross_target: 1.0` = 无杠杆，有观点时 |weights| 之和目标 1.0
- `market_neutral: true` = 多空对冲（fundamental-ls）

## FUND 层（mandate 之上的资本切片）

```yaml
name: example-fund
strategies:
  - name: deep-value
    weight: 0.6          # 资本切片
    models: [...]        # 可覆盖 strategy 默认
  - name: earnings-drift
    weight: 0.4
risk:
  max_position_pct: 0.25 # 单一标的 ≤25% 权益
  max_gross_exposure: 1.0 # 无杠杆
capital: 100000
rebalance: weekly        # daily | weekly | monthly
benchmark: SPY
```

> **mandate 从不点名 ticker** —— 它是 desk（策略/人员/风险/资本/节奏）；`--tickers` 是运行时输入。

## 两种 pod 的性格

- **discretionary pod**（LLM agents）—— 身份 = 谁在 desk（persona）
- **systematic pod**（quant models）—— 身份 = 它收割的 edge（PEAD）

同 spec 形状、同 engine 槽位；类型是**推导**的，从不声明。
