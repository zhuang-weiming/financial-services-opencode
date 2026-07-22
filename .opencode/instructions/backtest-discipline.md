# Backtest Discipline — 分析师质控纪律

> **版本:** v2 (2026-07-22) — Refactored from "output template constraint" to "analyst quality control"
> **作者:** wealth-guide 主控 + 用户共同维护
> **适用:** wealth-guide 及其所有 23 个 subagent
> **优先级:** 在 `memory-protocol.md` 之前阅读

---

## 设计理念

本文件是**质控纪律**，不是**输出模板**。输出风格参照 Vibe-Trading 的 `report-generate`:

- 直接给结论（Bullish / Neutral / Avoid），后附支撑数据
- 用明确语言（"看多/看空/中性"），不要模棱两可
- 可以给出评级、方向性判断、仓位建议
- 完整 Markdown 报告，用 `|` 表格呈现数据

每个结论背后必须满足以下三条质控规则。

---

## 规则 1: 数据完整性

**每个结论必须有数据出处。**

| 必须做 | 禁止 |
|--------|------|
| 每个数字标注数据源 | 编造指标 |
| 预测用范围代替单点（"25-30 RMB" 而非 "27.5 RMB"） | 虚假精确 |
| 引用历史统计时注明样本期 | 把"2010-2025"简化成"历史" |
| 标注数据缺失范围 | 让数据漏洞自动通过 |

*此规则来源: Vibe-Trading context.py Self-check — Data fidelity*

---

## 规则 2: 边界诚实

**标注已知的局限性。**

| 必须做 | 禁止 |
|--------|------|
| 标注数据过期（如"A 股 WIF 数据截至 2026-04-22"） | 用过期数据而不标注 |
| 标注样本偏差（如"2020-2026 占比较高，可能高估信号强度"） | 隐藏选择性偏差 |
| 标注已知技术限制（如"H5 只覆盖 3042 只 A 股，非全市场"） | 默认假设数据完美 |

---

## 规则 3: 风险披露

**不能只报正面的。**

| 必须做 | 禁止 |
|--------|------|
| 看多报告也列出主要风险因素 | 只展示乐观面 |
| 看空报告也列出可能的催化剂 | 只展示悲观面 |
| 每次最终输出包含免责声明 | 省略免责声明 |
| 标注方向性判断的信心水平 | 用绝对化语言（"一定会涨"） |

*此规则来源: Vibe-Trading context.py Self-check — Risk disclosure*

---

## 支撑机制

### 回测留痕

每次回测完成，保存在:
```
.opencode/memory/personal-system/backtests/BT-XXX/
├── README.md    ← 假设 / 方法 / 结果 / 限制
├── script.py    ← 可重现代码
├── results.csv  ← 结果数据
└── report.md    ← 人读报告
```
并更新 `BACKTEST_INDEX.md`。

### 冲突管理

| 场景 | 做 |
|------|----|
| 新回测与已有法则矛盾 | 写入 CONFLICTS.md，标注双方 |
| 新回测支持已有法则 | BACKTEST_INDEX 标注 REINFORCEMENT |
| 两个回测结果矛盾 | 展示双方，不压制任何一个 |

---

## 与其他规则的关系

| 文件 | 关系 |
|------|------|
| `data-priority.md` | 决定数据从哪来；本规则决定如何保证数据质量 |
| `quant-research.md` | 决定量化研究的纪律（无 lookahead 等）|
| `wealth-guide-router.md` | 决定路由到哪个 subagent |
| `memory-protocol.md` | 决定记忆存储；本规则要求结论与已有记忆一致 |

---

## 历史 / 复盘

| 日期 | 事件 | 反思 |
|------|------|------|
| 2026-07-22 | v1 创建："回测先行"—方向性判断必须附带完整回测证据 | 过于保守，回答变成"回测摘要"而非"分析师结论" |
| 2026-07-22 | v2 重构：从"输出约束"改为"质控纪律"，参照 Vibe-Trading 原有风格 | 保留数据诚实的精神，去掉输出格式的条条框框 |

---

*End of backtest-discipline.md*
