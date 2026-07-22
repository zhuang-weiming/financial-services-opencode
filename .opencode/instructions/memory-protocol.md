# Memory Protocol — 跨 Skill 共享记忆协议

> **生效日期 (Effective):** 2026-07-22
> **适用 (Applies to):** wealth-guide 及其所有 24 个 subagent
> **优先级:** 必须在 `backtest-discipline.md` 之后阅读

---

## 核心规则

### 任何 subagent 在做投资判断前：

1. **必读** `.opencode/memory/INDEX.md` 了解全局
2. **必读** `.opencode/memory/personal-system/` 下的关键文件:
   - `LAWS.md` (已验证法则 — 每条含 5-Why Challenge 区块)
   - `FAILED_LAWS.md` (失效法则)
   - `OPEN_HYPOTHESES.md` (待验证假设 — 每条含 5-Why Adversarial)
   - `BACKTEST_INDEX.md` (回测台账 — 每条含 Adversarial Review)
   - `CONFLICTS.md` (开放冲突 — 含逻辑矛盾 + Regime 冲突)
   - `SELL_LADDER.md` (卖出梯子)
   - `POSITION_SIZING.md` (仓位管理)
3. **必查**: grep 用户当前问题中的关键词，找到相关条目
4. **必引**: 如果命中，必须在回答中引用
5. **必反**: 引用任何 LAW/HYP/BT 前，必须读其 5-Why Challenge / Adversarial / Review 区块。每次使用都是一次"价值观边界的确认"——条件变了，结论可能失效。

### 任何 subagent 在产出结论前（新增——"反方输出协议"）：

1. **加载** 5-why-adversary skill（`skill("5-why-adversary")`）
2. **执行** 5-Why Protocol 对将要输出的结论：
   - Why 1: 此结论依赖的隐藏前提？
   - Why 2: 这个前提可能错吗？
   - Why 3: 错了结论会反转成什么？
   - Why 4: 我为什么想相信这个结论？（确认偏误检查）
   - Why 5: 一句话——这个结论最薄弱的地方
3. **记录** 5-Why 结果到 `raw-log/YYYY-MM-DD.md`（状态标签 ADD_5WHY）
4. **IF** 5-Why 发现框架矛盾 → 写入 `CONFLICTS.md`（类型 LOGICAL_CONTRADICTION）
5. **IF** 5-Why 怀疑 regime 变化 → 运行 `regime_shift_detector.py` + 更新 CONFLICTS.md
6. **IF** 5-Why 未推翻结论 → 输出结论时**必须附上** 5-Why 摘要

### 任何 subagent 在产生新认知后：

1. **写入** raw-log：append 到 `.opencode/memory/personal-system/raw-log/YYYY-MM-DD.md`
2. **触发回测**: 如果是关于"X 假设对不对"，必须触发 `backtest-builder` 跑回测
3. **触发更新**: 如果回测完成，按回测结果更新:
   - SUPPORTED + 多个证据 → 蒸馏到 LAWS.md
   - REJECTED → 写入 FAILED_LAWS.md
   - 部分支持 → 维持 OPEN_HYPOTHESES.md
   - 与现有 LAW 矛盾 → 写入 CONFLICTS.md
4. **记录回测**: 创建 `backtests/BT-XXX/` 目录，更新 BACKTEST_INDEX.md
5. **5-Why 蒸馏**: 新认知写入后，加载 `5-why-adversary` skill 对整条新认知做一遍 5-Why Protocol（见 §2.2），确保"被记录的知识"在被信任前已经过了反方质控

---

## 协议详情

### 读 (Read) 协议

```
subagent 收到用户问题
    ↓
1. 读 INDEX.md 知道有什么可查
    ↓
2. 根据问题类型决定读哪些文件:
   - 涉及具体股票 → 读 theses/<code>_<name>.md (如有)
   - 涉及仓位 → 读 POSITION_SIZING.md
   - 涉及规则 → 读 LAWS.md, FAILED_LAWS.md
   - 涉及未来走势 → 读 OPEN_HYPOTHESES.md, BACKTEST_INDEX.md
    ↓
3. grep 用户问题关键词
    ↓
4. ⚠️ 5-Why 检查: 对命中的 LAW/HYP/BT，读其 5-Why Challenge / Adversarial /
   Review 区块。确认条件未变，结论仍然适用。
    ↓
5. 把相关条目嵌入回答（如果条件已变，在回答中标注）
```

### 写 (Write) 协议

```
subagent 完成回答
    ↓
1. 自检: 本次回答是否产生了新认知？
   - 用户表达了新偏好/规则 → YES
   - 跑出了新回测 → YES
   - 发现与现有法则矛盾 → YES
   - 回答纯事实问题 → NO
    ↓
2. 如 YES，追加到 raw-log/YYYY-MM-DD.md:
   - 时间戳
   - 触发事件
   - 上下文
   - 内容
   - 状态标签 (NEW/REINFORCED/CONFLICTS/RESOLVED)
    ↓
3. 如果是回测完成:
   - 创建 backtests/BT-XXX/ 目录
   - 复制代码、数据、报告
   - 更新 BACKTEST_INDEX.md
    ↓
4. 如果是冲突:
   - 写入 CONFLICTS.md
   - 通知用户
```

### 蒸馏 (Distillation) 协议

```
触发: 累计 3+ 条未蒸馏 raw-log 条目 OR 距上次蒸馏 30 天 OR 用户要求
    ↓
1. 读所有未蒸馏的 raw-log/YYYY-MM-DD.md
    ↓
2. 读现有 LAWS.md, FAILED_LAWS.md, OPEN_HYPOTHESES.md, BACKTEST_INDEX.md
    ↓
3. 对每条新认知分类:
   - 支持现有 LAW (新证据) → 不动 LAW，在 BACKTEST_INDEX.md 标注 REINFORCEMENT
   - 反对现有 LAW → 写入 CONFLICTS.md (不修改 LAW)
   - 全新主题 (有 2+ 独立证据) → 提升为 LAW
   - 全新主题 (1 个证据) → 写入 OPEN_HYPOTHESES.md
   - 已被回测否定 → 写入 FAILED_LAWS.md
    ↓
4. 写一条 distillation-log 记录:
   - 时间
   - 输入 (哪些 raw-log 条目)
   - 产物 (新增/修改了哪些 LAW/HYP/FAILED/CONFLICT)
   - 依据
    ↓
5. 任何把"待验证"提升为"已验证"必须引用 ≥2 个独立证据
```

---

## 与 backtest-discipline.md 的关系

| backtest-discipline.md (规则) | memory-protocol.md (协议) |
|-------------------------------|--------------------------|
| 决定**判断的质控标准** | 决定**记忆如何被存储** |
| 确保每个方向性判断有数据支撑、诚实标注边界、披露风险 | 确保"有回测就要写入 memory" |
| 规范 subagent 的分析质量 | 规范 subagent 的读写行为 |

两者必须同时遵守：判断前查 memory（找到现有法则）→ 判断时遵守 backtest-discipline 的质控标准 → 判断后写回 memory。

## 5-Why 系统文件关系

| 文件/组件 | 在协议中的角色 |
|-----------|--------------|
| `skills/5-why-adversary/SKILL.md` | 所有 subagent 在输出结论前加载，执行 5-Why Protocol |
| `scripts/regime_shift_detector.py` | 怀疑 regime 变化时运行，输出结构断点检测结果 |
| `memory/personal-system/CONFLICTS.md` | 5-Why 发现 LOGICAL_CONTRADICTION 或 REGIME_SHIFT 时写入 |
| `memory/personal-system/LAWS.md` (5-Why 区块) | 每次引用 LAW 前必读其 5-Why Challenge——判断条件是否已变 |
| `memory/personal-system/OPEN_HYPOTHESES.md` (5-Why 区块) | 每次引用 HYP 前必读其 5-Why Adversarial——判断置信度是否仍合理 |
| `memory/personal-system/BACKTEST_INDEX.md` (Adversarial Review) | 每次引用 BT 前读其 Adversarial Review——判断 regime 是否适用 |

---

## 触发示例

### 例 1: 用户问"中芯国际能买吗"
```
subagent: alpha-researcher (调 alpha-engine-v21)
1. 读 INDEX.md → 知道有 theses/ 和 personal-system/
2. grep "中芯国际" → 没有现成 thesis，但 OPEN_HYPOTHESES.md 里有相关 HYP
3. 读 HYP-XXX "WT1 92% 半导体是否回调"
4. 调 alpha-engine-v21 跑 WT1 历史分布回测
5. 输出回测结果
6. 写回 raw-log + backtests/BT-XXX/ + 更新 BACKTEST_INDEX + OPEN_HYPOTHESES
```

### 例 2: 用户问"我的仓位是不是太集中"
```
subagent: wealth-management
1. 读 POSITION_SIZING.md → 知道用户当前是 50% 券商集中
2. 读 LAWS.md → 没有相关法则
3. 读 FAILED_LAWS.md → 没有相关失效案例
4. 读 raw-log/2026-07-22.md → 发现 11:30 提到"成交量暴涨+券商+50-70%"已被回测否定
5. ⚠️ 5-Why 反方（新增 — 加载 5-why-adversary skill）:
   Why 1: "50% 券商集中度=风险"这个结论依赖"券商修复持续"的前提
   Why 2: 如果 AI 板块在 2026H2 带动市场上涨，券商作为 Beta 弹性最大的板块反而可能跑赢
   Why 3: 如果前提不成立→反转结论→高集中度可能不是风险而是"集中押注有效Beta"
   Why 4: 我想相信这个结论因为保守风格 + 不想被批评"没提醒风险"
   Why 5: 最薄弱的是：LAW-003 显示券商已脱离成交量驱动，目前驱动主要靠 CSI 300 Beta。如果 CSI 300 不涨，集中度就是纯风险
6. 输出: 你已集中 50% 券商 + 核心假设有回测证据不支持 + 附 5-Why 摘要
7. 写回 raw-log (新认知: 用户的集中度问题 + 5-Why 记录)
```

### 例 3: 用户说"我之前说过的"
```
任何 subagent
1. 读 raw-log/ 所有文件 (或近 30 天)
2. grep 用户提到的关键词
3. 找到相关记录
4. 输出: 你的历史认知是 X，发生在 Y 时间，结论是 Z
5. 无新认知，不写回
```

---

## 当前状态 (2026-07-22)

- 协议已建立
- 5-Why 系统: ✅ 已集成（3 条 LAW + 7 条 HYP + 4 条 BT 全部完成 5-Why 填充）
- CONFLICTS.md: ✅ 升级完成（含 4 条可执行冲突：3 LOGICAL_CONTRADICTION + 1 REGIME_SHIFT）
- regime_shift_detector.py: ✅ 已创建（Chow test + CUSUM + 滚动检测）
- 5-why-adversary skill: ✅ 已创建（可在每次输出结论前加载）
- 实际数据: 仅 raw-log/2026-07-22.md 有 5 条
- 下次蒸馏触发条件: 累计 3 条新 raw-log
- 实际触发: 每次对话产生新认知时自动追加

---

*End of memory-protocol.md*
