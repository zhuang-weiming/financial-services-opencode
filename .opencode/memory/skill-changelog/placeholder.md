# Skill Changelog

> skill 自身升级历史
> 当修改 .opencode/skills/ 下任何 skill 时追加一条

---

## 格式

```markdown
### YYYY-MM-DD HH:MM
- **Skill:** <name>
- **变更类型:** [NEW / MAJOR_REVISION / MINOR_REVISION / BUGFIX]
- **变更内容:** 简述
- **原因:** 为什么改
- **影响:** 谁需要重新加载
```

---

## 历史

### 2026-07-22 12:30
- **Skill:** personal-trading-system
- **变更类型:** NEW
- **变更内容:** 创建新 skill。这是协议层 (薄)，实际数据在 .opencode/memory/personal-system/
- **原因:** 用户提出"无回测无方向性判断" + "memory 应该是时序的、跨 skill 共享的"
- **影响:** 所有 subagent 现在需要在投资判断前加载此 skill

### 2026-07-22 12:30
- **Skill:** stock-deep-dive
- **变更类型:** NEW
- **变更内容:** 创建新 skill。强制走"7 维综合"分析流程
- **原因:** 用户的"针对个股的判断需要更多 skill 能力"反馈
- **影响:** wealth-management、market-researcher、valuation-reviewer 在做个股分析时应加载此 skill

### 2026-07-22 14:30
- **Skill:** (no skill change)
- **变更类型:** BUGFIX (used in BT-001)
- **变更内容:** 在使用 `data_v20.h5` 的 `bad_returns_mask` 时，`astype(bool).fillna(False)` 会因 Python 的 `bool(NaN)=True` 规则把空值错误当成"坏样本"，应先 `fillna(False)` 再 `astype(bool)`。此外 prices 表索引在 2010-2014 与 2015-2025 跨格式（月初 vs 月末），需用 `pd.offsets.MonthEnd(0)` 重新归一。
- **原因:** BT-001 第一次跑时空事件分析失败（绝大多数月度组合为 NaN）；定位到 NaN→bool 转换 + 时间戳不一致两个 bug
- **影响:** 后续使用 alpha-engine-v21 数据的所有 subagent 应参考 BT-001/script.py 的对齐方式

