# Distillation Log

> 每次把 raw-log 蒸馏到 LAWS / FAILED / HYPOTHESES / BACKTEST_INDEX / CONFLICTS 的事件
> **不删，仅追加**

---

## 格式

```markdown
### YYYY-MM-DD HH:MM Distillation #NNN
- **输入:** raw-log 中 N 条未蒸馏条目 (列出来源文件)
- **产物:**
  - LAWS.md 新增 LAW-XXX (描述)
  - FAILED_LAWS.md 新增 FAILED-XXX (描述)
  - HYPOTHESES.md 状态变化
  - BACKTEST_INDEX.md 新增
  - CONFLICTS.md 新增
- **依据:** 为什么这样蒸馏
- **未采纳的想法:** 为什么舍弃某些 raw-log 条目
```

---

## 历史

（暂无 - 蒸馏协议已建立，等待首次触发）

---

### 2026-07-30 14:00 Distillation #001 — Cross-Market Daily Debrief 后框架更新

- **输入:** raw-log/2026-07-30.md（6 条新认知：Entry 1-6）
- **触发:** 用户问"分析昨日真实市场（A 股 + 美股），是否有新发现或超越 hypothesis/memory 的内容？需要 swarm 协助。"
- **执行:** wealth-guide 路由 → swarm-orchestrator（global equities desk 预设）+ market-router 平行 dispatch → 5-why-adversary skill 应用反方质控 → 用户确认"更新框架"后正式蒸馏

- **产物:**
  - **HYPOTHESES.md:**
    - HYP-002 v4.1 CANDIDATE（盈利型 vs 吞噬型 AI 维度）— **未升级为正式 v4.1**，因单日证据不足（5-Why 反驳）
    - HYP-005 新增约束（META Q2 miss + Q3 guide soft）
    - HYP-011 v2 扩展（6→8 信号矩阵；新增 S7 US30Y + S8 Brent/地缘）
    - HYP-013 维持 UNVERIFIED（5-Why 反驳"CONTRADICTED"初判）
    - HYP-016 更新 MSFT $175B capex（实际数字替代估算）
    - **新增 HYP-017**（US30Y 长端利率估值压缩独立信号）
    - **新增 HYP-018**（油价跳升 → 通胀 → 长端上行的 self-reinforcing 链条）
  - **CONFLICTS.md:**
    - **新增 CONFLICT-BLINDSPOT-001**（HYP-011 6 信号矩阵未涵盖长端利率断裂 + 地缘风险溢价；新类型 METHOD_BIAS / BLINDSPOT）
  - **LAWS.md:** 无变更（数据不足以升级为 LAW）
  - **FAILED_LAWS.md:** 无变更（无新失败证据）
  - **BACKTEST_INDEX.md:** 无变更（无新回测）

- **依据:**
  1. **HYP-013 维持 UNVERIFIED**：单日 S&P -1.54% 不构成"contradicted"；HYP-013 明确要求 3 层宏观确认，目前仍部分满足；维持 UNVERIFIED 等数据
  2. **HYP-002 v4.1 CANDIDATE 而非 v4.1 正式**：memory-protocol 要求 ≥2 独立证据升级 HYP；现有 (a) MSFT vs META 单日股价反应 [correlated] (b) GOOGL Cloud +82% [已被 v4 引用] (c) MSFT Azure +43% Q4 [单季度] — 严格意义上仅 1 个独立证据
  3. **HYP-011 v2 扩展**：2026-07-29 US30Y 5.20% + USO +7.32% 是 HYP-011 v1 6 信号矩阵的盲点事件；v2 扩展为 8 信号是合理补充；但保留 v1 baseline，v2 作为 pilot
  4. **HYP-017 / HYP-018 新增**：两个新维度（长端利率 + 油价传导）有独立理论支撑 + 1 个数据点（2026-07-29）；首次记录为 OPEN HYPOTHESIS，符合协议
  5. **CONFLICT-BLINDSPOT-001 新增**：HYP-011 盲点是结构性框架缺陷（非逻辑矛盾），需要新冲突类型 BLINDSPOT 记录

- **5-Why 反方驳回记录（重要）:**
  - **驳回 HYP-013 CONTRADICTED**：1 天证据 ≠ 7 月趋势；CONTRADICTED 是过度反应
  - **驳回 HYP-002 → v4.1 立即升级**：单日 + 1 季度 ≠ 多季度验证；evidence threshold 不达
  - **驳回 HYP-011 v2 完全替代 v1**：v1 经过多次蒸馏已稳定；v2 仅 1 个数据点驱动，应作 pilot 而非替代

- **未采纳的想法:**
  - ❌ "把 30Y 5.20% 直接归入 HYP-003（美债危机 2028）证据"——过早合并；先在 HYP-017 单独记录
  - ❌ "把 30Y 5.20% 等同于 2022 年情形"——2022 是实际利率主导（+1.6% real yield），当前 30Y 5.20% 分解未明；不能直接套用
  - ❌ "建议因 30Y 突破立即减仓 AI 主题"——未达阈值（需持续 1 周 > 5.0% 才 S7=+1）；当前不触发

- **下次检查:**
  - 2026-08-06：监控 US30Y 是否持续 > 5.0%（S7 阈值确认）
  - 2026-08-13：监控 Iran 紧张是否演变为军事行动 + 油价是否持续 > $90（S8 阈值确认）
  - 2026-10-XX：NVDA Q3 FY26 财报（HYP-015 验证窗口）
  - 2026-Q3/Q4：HYP-011 v2 历史回测（1994/2007/2022 长端峰值期验证 v2 vs v1 领先性）

- **输出文件:**
  - raw-log/2026-07-30.md（已写入）
  - HYPOTHESES.md（已更新；875 行；新增 HYP-017/HYP-018）
  - CONFLICTS.md（已更新；新增 CONFLICT-BLINDSPOT-001）
