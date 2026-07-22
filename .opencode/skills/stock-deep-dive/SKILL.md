---
name: stock-deep-dive
description: 标准化个股深度分析流程 - 强制走"多 skill 综合"路径（估值模型 + 技术分析 + 资金流向 + 舆情政策 + 国际市场对比 + V21 WT1 + 个人交易系统检查）。任何涉及"现在该不该买/卖/加仓/减仓 X"的问题必须走这个流程。当用户提到"分析 600519/000001/某只股票/个股分析/股票基本面/股票技术面"时加载。
---

# Stock Deep Dive — 个股深度分析标准流程

> 任何个股分析必须走这个流程，**禁止在没有 7 维数据时直接给方向性结论**。

---

## 触发条件

用户问以下问题之一时自动加载：
- "分析 600519 / 000001 / [任何股票代码]"
- "X 现在能买吗 / 能卖吗 / 该加仓吗 / 该减仓吗"
- "X 估值怎么样 / 贵不贵 / 便宜不便宜"
- "X 走势如何 / 技术面怎么样 / 资金在流入吗"
- "X 跟 Y 怎么比较"
- "X 行业怎么样 / 龙头是谁"

---

## 强制 7 维分析 (每次必走)

### 维度 1: 估值模型 (Valuation)
- 加载 skill: `valuation-model` 或 subagent: `financial-analysis`
- 必输出: PE, PB, PS, EV/EBITDA, DCF 估算 (如有)
- 必须标注假设 (增长率, 折现率, 终值)
- 可以做"偏低/合理/偏高"的判断，但必须标注假设

### 维度 2: 技术分析 (Technical)
- 加载 skill: `alpha-engine-v21` (V21 WT1/WT2)
- 可选: `technical-basic`, `candlestick`, `elliott-wave`
- 必输出: WT1, WT2, 当前百分位, 信号状态
- 可以给出信号解读（如"WT1 高位，历史上动量延续"），需引用回测

### 维度 3: 资金流向 (Fund Flow)
- 加载 skill: `eastmoney` (fund flow, northbound, margin, block trades)
- 必输出: 北向资金 5/20/60日累计, 融资余额变化, 龙虎榜数据 (如有)
- 可以做"资金面偏正/负"的判断，标数据源

### 维度 4: 舆情 / 政策 / 新闻 (Sentiment)
- 加载 skill: `sentiment-analysis` + web search
- 必输出: 最近 30 天重要新闻分类 (业绩/政策/行业/公司)
- 可以给出舆情整体判断，标注来源

### 维度 5: 国际市场对比 (International Peers)
- 加载 subagent: `market-router`
- 必输出: 同行业海外可比公司估值/表现
- 可以给出"相对贵/便宜"的判断，标注可比公司

### 维度 6: 行业地位 (Industry Position)
- 加载 skill: `sector-overview` 或 `competitive-analysis`
- 必输出: 行业排名, 市场份额, 龙头 vs 跟随者
- 可以给出行业判断

### 维度 7: 个人交易系统检查 (Personal System Check)
- 加载 skill: `personal-trading-system`
- **必查:**
  - LAWS.md 中是否有相关法则
  - FAILED_LAWS.md 中是否有相关失效案例
  - OPEN_HYPOTHESES.md 中是否有相关待验证假设
  - BACKTEST_INDEX.md 中是否有相关历史回测
- 必输出: 引用相关条目 (如有)，并结合到综合判断中

---

## 报告结构

```
## 1. 标的识别
[代码 / 名称 / 行业 / 市值]

## 2. 综合判断
[买入/卖出/观望 + 信心水平 + 关键依据 + 主要风险]

## 3. 七维分析 (7 sections)
[每维一段：结论 + 支撑数据 + 标注边界]

## 4. 个人交易系统检查结果
[引用 LAWS / FAILED_LAWS / OPEN_HYPOTHESES / BACKTEST_INDEX 中的相关条目]

## 5. 风险提示
[不可忽略的风险因素]
```

---

## 质控纪律

### 严格禁止
- ❌ 在没有 7 维数据时直接给方向性结论
- ❌ 跳过任何一维 (即使数据不可得, 也要标注"数据缺失")
- ❌ 编造数据或指标
- ❌ 隐瞒 LAWS.md 中相关的失效法则
- ❌ 用绝对化语言（"一定涨"、"肯定跌"）
- ❌ 省略免责声明

### 允许
- ✅ 基于数据直接给结论（如"估值偏高"、"动量正信号"、"资金流偏负"）
- ✅ 结合 7 维做综合判断（如"短期谨慎，中期看好"）
- ✅ 给出评级（买入/持有/卖出）和信心水平
- ✅ 给出仓位建议
- ✅ 引用 LAWS.md / FAILED_LAWS.md 中的相关条目
- ✅ 标注数据缺失或异常

---

## 关联 skill / subagent

| 维度 | 首选 skill | 备选 subagent |
|------|-----------|--------------|
| 估值 | valuation-model, dcf-model | financial-analysis, model-builder |
| 技术 | alpha-engine-v21 | alpha-researcher, market-researcher |
| 资金 | eastmoney, hk-connect-flow | market-router |
| 舆情 | sentiment-analysis, web search | - |
| 国际 | yfinance, market-router | market-router |
| 行业 | sector-overview, competitive-analysis | market-researcher |
| 个人 | personal-trading-system | - |

---

## 当前状态 (2026-07-22)

- 7 维框架已建立
- 实战测试：已完成（光大证券 thesis 作为示范）
- 输出风格：Vibe-Trading 风格，分析师式结论

---

*End of SKILL.md*
