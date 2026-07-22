---
name: personal-trading-system
description: 加载用户的个人交易系统 - 累积的法则、失效案例、待验证假设、回测索引。任何 subagent 在做投资判断前必须加载此 skill。它是"协议层"，实际数据在 .opencode/memory/personal-system/。当用户提到"我的法则/规则/仓位/卖出梯子/个人交易系统/交易系统/我的系统"时加载。
---

# Personal Trading System — 协议层

> **本 skill 是协议层，不存数据。**
> 实际数据在 `.opencode/memory/personal-system/`。
> 这个 skill 的作用是描述"如何读写那些数据"。

---

## 加载协议（任何 subagent 调用时执行）

### 必读文件（按此顺序）

1. `.opencode/memory/INDEX.md` — 全局入口
2. `.opencode/memory/personal-system/LAWS.md` — 活跃法则
3. `.opencode/memory/personal-system/FAILED_LAWS.md` — 失效法则
4. `.opencode/memory/personal-system/OPEN_HYPOTHESES.md` — 待验证假设
5. `.opencode/memory/personal-system/BACKTEST_INDEX.md` — 回测台账
6. `.opencode/memory/personal-system/CONFLICTS.md` — 开放冲突
7. `.opencode/memory/personal-system/SELL_LADDER.md` — 卖出梯子
8. `.opencode/memory/personal-system/POSITION_SIZING.md` — 仓位管理

### 检索

在用户当前问题中提取关键概念（股票代码、概念词、风险敞口），
在以上 8 个文件中 grep 关键词，找到相关条目。
把相关条目嵌入到回答中。

### 触发条件

| 用户说 | subagent 必须做的 |
|--------|-----------------|
| "600519 现在能买吗" | grep 600519 → 看是否有 law/回测/thesis |
| "我的仓位是不是太集中" | 读 POSITION_SIZING.md |
| "成交量上升时券商怎么走" | grep 券商/成交量 → 看是否有回测 |
| "我之前说过的" | grep raw-log 历史 |
| "X 假设验证过吗" | 查 OPEN_HYPOTHESES + BACKTEST_INDEX |

---

## 写回协议（任何回答产生新认知时执行）

### 什么时候写

| 场景 | 写到哪里 |
|------|----------|
| 用户提出新假设 | OPEN_HYPOTHESES.md (新增 HYP-XXX) |
| 跑出新回测 | backtests/BT-XXX/ 目录 + BACKTEST_INDEX.md (新增 BT-XXX) |
| 回测推翻假设 | FAILED_LAWS.md (新增 FAILED-XXX) |
| 回测支持假设 → 转法则 | LAWS.md (新增 LAW-XXX) |
| 出现矛盾 | CONFLICTS.md (新增 CONFLICT-XXX) |
| 任何认知/对话洞察 | raw-log/YYYY-MM-DD.md (append) |

### 写回时序

- **raw-log** 永远 append，永不修改
- **LAWS / FAILED / OPEN_HYPOTHESES** 通过 distillation 流程更新
- **BACKTEST_INDEX** 可直接 append 新回测
- **CONFLICTS** 可直接追加

### 蒸馏（Distillation）协议

**触发条件：**
- 累计 ≥3 条未蒸馏的 raw-log 条目
- 或 距上次蒸馏 ≥30 天
- 或 用户明确要求

**执行步骤：**
1. 读 raw-log/ 最近所有未蒸馏的文件
2. 提取"反复出现的主题"→ 候选法则
3. 读现有 LAWS.md / FAILED_LAWS.md / OPEN_HYPOTHESES.md
4. 决定每条新认知应该：
   - 提升为 LAW（如已被 3+ 个证据支持）
   - 归入 FAILED_LAW（如被回测明确否定）
   - 维持 OPEN_HYPOTHESIS（如有 1-2 个证据但未确认）
   - 标记 CONFLICT（如与现有法则矛盾）
5. 写一条 distillation-log 记录依据
6. 任何把"待验证"提升为"已验证"必须 **引用至少 2 个独立证据**

**禁止：**
- 单次回测就提升为 LAW
- 在 CONFLICTS 没解决时修改被挑战的 LAW
- 删除 raw-log 内容

---

## 与其他 skill 的协作

| Skill | 协作 |
|-------|------|
| `alpha-engine-v21` | 跑回测，写到 backtests/BT-XXX/，更新 BACKTEST_INDEX.md |
| `stock-deep-dive` | 个股分析时必须先读 personal-system，检查是否与现有法则冲突 |
| `vibe-thesis-tracker` | 单股论追踪 → 写入 theses/<code>_<name>.md |
| `trade-journal` | 实际交易结果 → 用于验证/推翻 LAWS.md |
| `backtest-diagnose` | 回测异常 → 可能产生 FAILED-XXX 条目 |
| `factor-research` | 因子检验 → 如显著可转为 HYP-XXX |

---

## 与 subagent 的对接

| Subagent | 调用场景 |
|----------|---------|
| `wealth-management` | 客户报告 / 财务规划前必读 LAWS + SELL_LADDER + POSITION_SIZING |
| `market-researcher` | 行业 / 标的研究前必读 FAILED_LAWS + OPEN_HYPOTHESES |
| `model-builder` | 估值建模前必读 OPEN_HYPOTHESES（避免重复计算） |
| `valuation-reviewer` | 估值审查前必读 LAWS（避免重复错误） |
| `backtest-builder` | 新回测前必读 BACKTEST_INDEX（避免重复回测） |
| `alpha-researcher` | Alpha 研究前必读 OPEN_HYPOTHESES + FAILED_LAWS |
| `factor-researcher` | 因子研究前必读 BACKTEST_INDEX + OPEN_HYPOTHESES |

---

## 当前状态 (2026-07-22)

- INDEX.md: 已建立
- LAWS.md: 2 条（LAW-001: WT1 动量延续, LAW-002: mean/median 尾部分布）
- FAILED_LAWS.md: 空
- OPEN_HYPOTHESES.md: 空
- BACKTEST_INDEX.md: 2 条（BT-001 WT1 极值信号, BT-002 ML 单股预测）
- CONFLICTS.md: 空
- SELL_LADDER.md: 已填
- POSITION_SIZING.md: 已填
- raw-log/: 2026-07-22.md 多条记录
- distillation-log/: 空
- backtests/: BT-001, BT-002
- theses/: 601788_光大证券.md

---

*End of SKILL.md*
