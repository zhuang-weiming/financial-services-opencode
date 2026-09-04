---
name: 5-why-adversary
description: |
  Adversarial quality-control system for subagent output validation.
  Any subagent MUST load this skill before outputting a directional judgment,
  rating, or position recommendation. Enforces a 5-Why Protocol: challenge
  every conclusion 5 times before it is spoken — find hidden assumptions,
  identify falsification conditions, invert the conclusion, check
  confirmation bias, and state the framework's weakest point.
  Integrates with 1.LAWS.md, 6.CONFLICTS.md, regime_shift_detector.py,
  and the memory-protocol.md adversarial review workflow.
category: quality-control
---

# 5-Why Adversary — 反方质控系统

> **加载条件:** 任何 subagent 在产出结论（方向性判断/评级/仓位建议）**之前**，必须先加载此 skill，对自己即将输出的结论执行一次 5-Why 反方质控。
>
> **核心原则:** 每个结论在说出之前，必须被自己挑战 5 次。

---

## 1. 如果你只记住一句话

**对一个不确定的方向性判断，输出前反问自己最多 5 次"它为什么可能是错的"，每问必须比上一问更深——直到找到那个最薄弱的点。不是为了凑满 5 层，而是为了逼近根因。**

---

## 1.1 使用边界（防形式化 —— 2026-09-04 用户裁定）

**5-Why 只用于"不确定的方向性/评级/仓位/框架结论"。以下情况不需要 5-Why：**

| 不需要 5-Why 的情形 | 例子 | 替代 |
|---|---|---|
| 事实/数据陈述 | "NVDA Q2 营收 $96.22B" | 直接给数据 + 来源 |
| 复核确认 | "MCP 复核后数字一致" | 给复核结果即可 |
| 纯操作阈值/规则 | "WTI >$120 持续 3 月 → 警戒" | 写进监控阈值清单 |
| 低风险例行回答 | 一般信息性问题 | 直接回答 |

**5-Why 是过程，不是凭据。** 禁止以"经过 5-Why / 已通过 5-Why / 5-Why 已完成"作为内容可信度的盖章——引用时必须给出**具体的 Why 5 最薄弱点或证伪条件**，而不是只声明"做过"。

**5-Why 不是标签。** 禁止把普通监控阈值、例行结论、背景说明冠以"5-Why Why X"之名；只有真正执行了该层追问链的内容才能带 5-Why 标记。

## 1.2 Drill-down 质量标准（层间必须加深）

一次合格的 5-Why 追问链必须满足：

1. **每层回答必须比上一层更深**——Why N+1 在 Why N 的答案上继续追问根因，而不是换句话重复同一根因。
2. **如果连续两层指向同一根因 → 停止或合并**。真正深入时常常 3 层就触底，凑满 5 层是形式主义（≤5 层都是有效结果，重点是层与层有推进）。
3. **Why 5 必须是一句可操作的薄弱点**——能指出"什么条件下本结论失效/反转"，而不是复述结论本身。
4. **Why 1 挖前提，Why 2 给证伪条件，Why 3 描述反转后的具体形态，Why 4 做诚实的 bias 自检（无证据不乱猜用户心理），Why 5 收束到最脆弱处**——四者缺一不可；做不到其中某一层时说明原因而不是硬编。

## 1.3 输出纪律（回复 vs 记录分离 —— 2026-09-04 修正）

- **用户回复中只附 Why 5 最薄弱点一句话**（或经得起挑战后的"本结论最弱处：…"），不贴完整 5 行表。
- **完整 5-Why 追问链只写入 raw-log / 记忆文档**，供日后引用与复盘。
- 若结论被 5-Why 推翻 → 在回复里直接说明"原结论因 X 被修正为 Y"，不需要展示追问过程。
- 若结论是事实/数据/例行回答 → 完全不带 5-Why 摘要。

---

## 2. 执行流程

```
subagent 形成初步结论
    ↓
判断：这是不确定的方向性判断吗？（§1.1）
  │
  ├─ 否（事实/数据/确认/低风险）→ 直接输出，不做 5-Why
  │
  └─ 是 → 加载本 skill → 执行 5-Why Protocol（见 §3，层间必须加深，触底即停）
       ↓
记录完整追问链到 raw-log（ADD_5WHY）
    ↓
IF 5-Why 未推翻结论 AND 结论为方向性判断 → 输出结论（回复只附 Why-5 一句）
IF 5-Why 发现框架矛盾 → 写入 6.CONFLICTS.md + 修正结论
IF 5-Why 怀疑 regime 变化 → 运行 regime_shift_detector.py + 更新 6.CONFLICTS.md
```

---

## 3. 5-Why Protocol（标准追问链）

对于任意结论 C，按以下 5 层反问：

### Why 1 — 前提追问
> "结论 C 最依赖的假设 A 是什么？"

找出结论的**隐含前提**。每个结论至少包含一个必须成立的前提。

### Why 2 — 前提证伪条件
> "什么情况下假设 A 不成立？"

列出 A 的**证伪条件**。如果这个条件发生了，A 就垮了。

### Why 3 — 结论反转方向
> "如果 A 不成立，结论 C 会变成什么？"

不是简单地说"结论错误"，而是**具体描述反转后的结论**。

### Why 4 — 确认偏误核查
> "我们（用户或框架）有没有因为某个原因而希望 C 成立？"

找出持有 bias。这是最难但最重要的层级。

### Why 5 — 框架偏差总结
> "这个结论 C 最脆弱的地方在哪里？一句话"

最终输出——一条清晰的、对后续判断有指导意义的薄弱点陈述。

---

## 4. 输出格式

### 对 LAW 的 5-Why Challenge

```
### LAW-XXX 5-Why 检查 {date}

| 层级 | 追问 | 回答 |
|:-----|:-----|:-----|
| Why 1 | [前提追问] | [前提 A] |
| Why 2 | [证伪条件] | [A 的证伪条件] |
| Why 3 | [反转方向] | [如果 A 不成立] |
| Why 4 | [确认偏误] | [self-bias check] |
| Why 5 | **框架偏差** | [最脆弱点] |

**5-Why 结论:** LAW 仍然有效/需要修正/已失效
**置信度:** HIGH / MODERATE / LOW
**下次检查:** YYYY-MM-DD
```

### 对 HYP 的 5-Why Adversarial

```
### HYP-XXX 5-Why 检查 {date}

| 层级 | 追问 | 回答 |
|:-----|:-----|:-----|
| Why 1 | [前提追问] | [前提 X] |
| Why 2 | [证伪条件] | [X 的证伪条件] |
| Why 3 | [反转方向] | [如果 X 不成立] |
| Why 4 | [确认偏误] | [self-bias check] |
| Why 5 | **框架偏差** | [最脆弱点] |

**5-Why 结论:** 假设置信度从 X→Y
**置信度:** HIGH / MODERATE / LOW
```

### 对回测结果的 Adversarial Review

```
### BT-XXX Adversarial Review

- **回测最可能出错的方面:** [方法偏差/数据偏差/幸存者偏差]
- **最容易被误读的方式:** [用户容易得出什么错误结论]
- **Regime 变化检测:** [什么条件变了会反转结论]
- **推荐重跑频率:** [每月/每季/每年/仅此一次]
- **分拆验证建议:** [子部分验证]
```

### 对框架整体结论的 5-Why（输出前必做 · 完整表入 raw-log，回复只附 Why 5 一句）

```
### 本次输出 5-Why 检查（raw-log 记录版）

初步结论: [我即将说出的结论]

| 层级 | 追问 | 回答 |
|:-----|:-----|:-----|
| Why 1 | 这个结论依赖的隐藏前提？ | [前提] |
| Why 2 | 这个前提可能错吗？ | [证伪条件] |
| Why 3 | 错了结论会反转成什么？ | [反转版本] |
| Why 4 | 我为什么想相信这个结论？ | [bias check] |
| Why 5 | **一句话：这个结论最薄弱的地方** | [薄弱点] |
```

**回复版（只给用户看这一行）:** `本结论最弱处：<Why 5 一句>；若 <证伪条件> 发生则结论反转。`

---

## 5. 与现有系统的关系

| 系统组件 | 关系 |
|:---------|:-----|
| `6.CONFLICTS.md` | 5-Why 发现的逻辑矛盾 → 写入 LOGICAL_CONTRADICTION |
| `1.LAWS.md` | 每条 LAW 已嵌入 5-Why Challenge 区块 → 每次使用前检查 |
| `OPEN_2.HYPOTHESES.md` | 每条 HYP 已嵌入 5-Why Adversarial → 每次引用前检查 |
| `5.BACKTEST_INDEX.md` | 每条 BT 已嵌入 Adversarial Review |
| `regime_shift_detector.py` | 当 5-Why 怀疑 regime 变化时 → 运行检测脚本 |
| `backtest-discipline.md` | 5-Why 是 backtest-discipline 规则 2（边界诚实）的执行方法 |
| `memory-protocol.md` | 5-Why 是"读"协议的一部分——读 LAW/HYP 时即触发反方质控 |

---

## 6. 系统初始化（2026-09-04 刷新）

> 数量随记忆演化会继续变化——引用前以各文件实际为准，本节只是"已嵌入"的事实声明，不是最新计数源。

| 组件 | 状态 |
|:-----|:------|
| 6.CONFLICTS.md（含 CONFLICT-LAW001-LAW004 等 OPEN 冲突） | ✅ 已嵌入 5-Why 根因 |
| 1.LAWS.md（LAW-001~004 全部含 5-Why Challenge） | ✅ 已嵌入 |
| 2.HYPOTHESES.md（活跃 HYP 全部含压缩版 5-Why Adversarial） | ✅ 已嵌入 |
| 5.BACKTEST_INDEX.md（BT 主体全部含 Adversarial Review） | ✅ 已嵌入 |
| regime_shift_detector.py | ✅ 已完成 |
| **本 skill（§1.1/§1.2/§1.3 使用边界与纪律）** | ✅ 2026-09-04 修订 |
| memory-protocol.md（反方输出协议已按使用边界修订） | ✅ 2026-09-04 同步 |

---

## 7. 常见"反方追问"示例

**示例 1：用户问"XX 股票能买吗"**
```
初步结论：中性偏多，目标价 XX
5-Why Why 1：依赖"XX 股票 2026E PE 处于历史低位"（如果盈利下滑 PE 会变高）
5-Why Why 2：盈利下滑风险——2026Q1 营收增速已放缓
5-Why Why 3：如果盈利下滑→PE 从 15x 变 25x→不便宜→结论从"偏多"变"中性"
5-Why Why 4：用户已持有该股票→可能高估利好、低估风险
5-Why Why 5：这个结论最弱的地方：用静态 PE 做估值，忽略了盈利下行风险
→ 修正：改为"中性，需等 Q2 财报确认盈利趋势"
```

**示例 2：回测结果输出前**
```
初步结论：BT-003 回测显示成交量与券商 PB 负相关
5-Why Why 1：依赖"月度频率"的采样（如果换了周度/季度频率可能不同）
5-Why Why 2：月度频率可能平滑掉日内/周度的短期关系
5-Why Why 3：如果换日度频率→r 可能变正或不变→结论需要加"月度频率"前缀
5-Why Why 4：回测是用户做的，用户希望修正"成交量驱动券商"的框架→可能高估了脱钩的显著性
5-Why Why 5：最薄弱——样本期内 8 只券商中混入了东方财富（互联网券商），需要分拆验证
→ 修正：输出前加"东财需分拆验证"的 caveat
```
