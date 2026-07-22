# INDEX — 集中化记忆系统的全局索引

> 这是 `.opencode/memory/` 的主入口
> 任何 subagent 在做投资判断前必须读本文件
> 创建: 2026-07-22

---

## 目录结构

```
.opencode/memory/
├── INDEX.md                            ← 本文件
├── personal-system/                    ← 个人交易系统
├── market-regime/                      ← 宏观/市场环境笔记
└── skill-changelog/                    ← Skill 自身升级历史
```

---

## 1. personal-system/

| 文件 | 作用 | 时序性 | 状态 |
|------|------|--------|------|
| 文件 | 作用 | 时序性 | 5-Why 状态 |
|------|------|--------|:----------:|
| `LAWS.md` | 已验证生效的法则（每条含 5-Why Challenge） | 静态（蒸馏后） | ✅ 3/3 已填充 |
| `FAILED_LAWS.md` | 已失效/未支持的规则 | 静态（蒸馏后） | 空 |
| `OPEN_HYPOTHESES.md` | 待验证的猜想（每条含 5-Why Adversarial） | 静态 | ✅ 7/7 已填充 |
| `BACKTEST_INDEX.md` | 回测台账（每条含 Adversarial Review） | 静态（追加） | ✅ 4/4 已填充 |
| `CONFLICTS.md` | 冲突记录（回溯/逻辑/Regime） | 静态 | ✅ 4条已记录 |
| `SELL_LADDER.md` | 卖出梯子规则 | 静态 | 待补 |
| `POSITION_SIZING.md` | 仓位管理 | 静态 | 已填充 |
| `BROKER_OBSERVATION.md` | 券商板块观察指标体系 | 静态 | 已创建 |
| `NATIONAL_TEAM_OBSERVATION.md` | 国家队全口径资金监测 | 动态（月度更新） | ✅ 已创建 |
| `raw-log/YYYY-MM-DD.md` | 每日原始记录 | **强时序** | 1 文件 |
| `distillation-log/YYYY-MM-DD_NNN.md` | 蒸馏事件 | **强时序** | 空 |
| `backtests/BT-XXX/` | 每个回测一个目录 | 静态 | 2 目录 |
| `theses/<code>_<name>.md` | 个股研究论 | 静态 | 1 文件 |

---

## 2. market-regime/

- `2026-Q2.md` - 季度宏观环境笔记
- 暂未填充

---

## 3. skill-changelog/

- `2026-07-22_added-personal-trading-system.md` - skill 创建记录
- 暂未填充

---

## 当前活跃内容

**最后更新:** 2026-07-22 (v4 — 国家队监测系统上线 + FactSet 数据源验证)
**回测总数:** 5 (BT-001~BT-005)
**活跃法则数:** 3 (全部含 5-Why Challenge 区块)
**开放假设数:** 7 (全部含 5-Why Adversarial 区块)
**开放冲突数:** 4 (3 LOGICAL_CONTRADICTION + 1 REGIME_SHIFT — 其中1条已获FactSet数据确认)
**5-Why 系统:** ✅ 已集成（skill/script/模板全部就绪）
**国家队 regime:** 🔴 净卖出（FactSet 数据确认，详见 NATIONAL_TEAM_OBSERVATION.md）
**新增数据源验证:** FactSet FundsETF ✅ | Morningstar Data ✅

---

## 检索指南

| 想找什么 | 怎么找 |
|---------|--------|
| "我有没有关于 X 的回测？" | `grep -i "X" personal-system/BACKTEST_INDEX.md` |
| "我的法则说什么" | `grep "X" personal-system/LAWS.md` |
| "X 假设是否被验证" | `grep "X" personal-system/OPEN_HYPOTHESES.md` |
| "X 假设被推翻了吗" | `grep "X" personal-system/FAILED_LAWS.md` |
| "今天学到了什么" | `cat personal-system/raw-log/2026-07-22.md` |
| "上周的回测" | `ls personal-system/backtests/ | grep BT-` |
| **"LAW-XXX 的 5-Why 吗？"** | `grep "5-Why Challenge" personal-system/LAWS.md -A 20` |
| **"HYP-XXX 的 5-Why？"** | `grep "5-Why Adversarial" personal-system/OPEN_HYPOTHESES.md -A 20` |
| **"BT-XXX 的 Adversarial Review？"** | `grep "Adversarial Review" personal-system/BACKTEST_INDEX.md -A 10` |
| **"框架内有什么冲突？"** | `grep "CONFLICT-LOGIC\|CONFLICT-REGIME" personal-system/CONFLICTS.md` |
