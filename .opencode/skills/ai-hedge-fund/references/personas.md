# 5 位投资人 persona 对照

> 来源：`ai-hedge-fund/hedge_fund/signals/*.py`。风格化近似，非本人、非背书。

| persona | 流派 | 首要判据 | 最看重的数 | 会否决什么 | confidence 高位条件 |
|---|---|---|---|---|---|
| **buffett** | 长期生意所有者 | 护城河 + 公允价格 | 持续高 ROE / 稳定利润率 / 低 D/E / 账面价值复利 | 要求完美定价的价格；弱或恶化生意 | 强且持久 + 合理价格 |
| **munger** | 质量 + 公允价格（严苛）| 反向思考 + 多年一致性 | 全历史 ROE 一致性 / 真实 FCF 增长 | 平庸生意 / 数字可疑 / 愚蠢价格 | 罕见、明显、质量与价格同时对齐 |
| **graham** | 安全边际（防御型）| 价格 vs 已证实价值 | P/E / P/B / 流动比率 / 盈利稳定 | 弱资产负债表（直接否决）/ 高估本身即看空 | 每项判据都清晰的量化案例 |
| **lynch** | GARP | 分类 + PEG | 盈利增速 / PEG / EPS 逐季上行 | 溢价倍数下的减速 / 热门故事价格 | 经典设置、增长便宜且可见 |
| **druckenmiller** | 拐点 + 不对称 | 变化率（非水平）| 营收/利润率**加速或滚落** / EPS 动能 | 基本面恶化 + 杠杆（空或放弃，绝不持有）| 无可错认的拐点 + 不对称设置 |

## 信号 → value 映射（所有 persona 通用）

```
value = {bullish: +1.0, neutral: 0.0, bearish: -1.0} × confidence / 100
```

## 判据冲突时的处理

两位 persona 对同一标的给出相反信号是**正常产物**（不是 bug）—— 它定位了决策所依赖的假设：
- Graham vs Lynch：价值 vs 成长
- Buffett/Munger vs Druckenmiller：长期质量 vs 近期变化率
- Munger 的"太难堆"（neutral）常出现在数据不清晰时

## 数据需求（共用）

所有 persona 吃同一个 `FundamentalsSnapshot`（见 master §五）：
`ticker / sector / industry / periods[]`（P/E, ROE, gross/net margin, D/E, current_ratio, revenue_growth, EPS, BVPS, FCF/share）+ 派生聚合。

**最少 4 期**，否则 `InsufficientData`（persona 应 abstain 而非猜）。
