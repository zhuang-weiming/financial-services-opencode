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

| 文件 | 作用 | 时序性 | 5-Why 状态 |
|------|------|--------|:----------:|
| `LAWS.md` | 已验证生效的法则（每条含 5-Why Challenge） | 静态（蒸馏后） | ✅ 3/3 已填充 |
| `FAILED_LAWS.md` | 已失效/未支持的规则 | 静态（蒸馏后） | ✅ 1/1 已填充 |
| `OPEN_HYPOTHESES.md` | 待验证的猜想（每条含 5-Why Adversarial） | 静态 | ✅ 26/26 活跃 HYP 已填充（HYP-001 标记归档至 FAILED；HYP-008 不存在；HYP-019/020/021 新增于 2026-08-01；HYP-027/028 双剧本新增于 2026-07-31） |
| `BACKTEST_INDEX.md` | 回测台账（每条含 Adversarial Review） | 静态（追加） | ✅ 5/5 已填充 |
| `CONFLICTS.md` | 冲突记录（回溯/逻辑/Regime） | 静态 | ✅ 11条已记录（3 OPEN + 8 RESOLVED） |
| `SELL_LADDER.md` | 卖出梯子规则 | 静态 | 待补 |
| `POSITION_SIZING.md` | 仓位管理 | 静态 | 已填充 |
| `BROKER_OBSERVATION.md` | 券商板块观察指标体系 | 静态 | 已创建 |
| `NATIONAL_TEAM_OBSERVATION.md` | 国家队全口径资金监测 | 动态（月度更新） | ✅ 已创建 |
| `raw-log/YYYY-MM-DD.md` | 每日原始记录 | **强时序** | 10 文件 |
| `CHINA_FRAMEWORK.md` | **A 股独立投资框架 v1.2**（化债市总纲/国家机器/退出纪律/反方章节；与 US_FRAMEWORK.md 平级，跨市场协调见 US_FRAMEWORK.md §九）| 静态 | 已创建 |
| `US_FRAMEWORK.md` | **美股独立投资框架 v2.0**（总纲/观察/配置/双剧本联动/反方章节；与 CHINA_FRAMEWORK.md 平级，跨市场协调见其"九、总组合协调层"）| 静态 | 已创建 |
| `distillation-log/YYYY-MM-DD_NNN.md` | 蒸馏事件 | **强时序** | 1 文件 |
| `backtests/BT-XXX/` | 每个回测一个目录 | 静态 | 5 目录 |
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

**最后更新:** 2026-07-31（data/ 架构建立 + out/ 清理 + 化债双剧本 HYP-027/028 入库 + 框架拆分：FRAMEWORK.md → CHINA_FRAMEWORK.md v1.2（瘦身）+ US_EQUITY_FRAMEWORK.md → US_FRAMEWORK.md v2.0（独立升级）；用户裁决：thesis 改"剧本判定中"、删除资金迁移规则、否决增长消化分支、清仓执行日不考虑延期）
**回测总数:** 5 (BT-001~005)
**活跃法则数:** 3 (LAW-001~003，全部含 5-Why Challenge；LAW-004 → HYP-013)
**失效法则数:** 1 (FAILED-001 — 券商原假设)
**开放假设数:** 26 (HYP-002~007, 009~028 — HYP-001 已归档至 FAILED-001；HYP-008 不存在；HYP-019~026 化债理论系列；**HYP-027/028 双剧本 2026-07-31 新增**)
**开放冲突数:** 3 (CONFLICT-REGIME-001, CONFLICT-LOGIC-002, CONFLICT-BLINDSPOT-001)
**已解决冲突数:** 8 (LOGIC-001/003/004/005/006, REGIME-002, METHOD-001/002)
**5-Why 系统:** ✅ 已集成
**国家队 regime:** 🔴 净卖出（FactSet 数据确认，持续监控）
**框架版本:** `personal-system/CHINA_FRAMEWORK.md` v1.2（A 股独立框架，2026-07-31 瘦身改名）| `personal-system/US_FRAMEWORK.md` v2.0（美股独立框架，2026-07-31 升级）
**数据架构:** `data/` 集中数据仓库已建立（market/earnings/factors/cache 四子目录）

### 当前 out/ 内容（清理后）

| 报告 | 文件 | 时间 |
|:-----|:-----|:----:|
| 跨市场 debrief | `out/daily-debrief-20260729/` | 2026-07-29 |
| HSBC vs framework Q3 verdict | `out/hsbc-vs-framework-verdict-q3-20260728.md` | 2026-07-28 |

### 历史 one-off 报告（已清理）

> 2026-07-31 清理：删除 GWM/COSCO/ChinaUnicom/Hundsun 公司 deep-dive × 7、datapack × 3、portfolio × 3、HSBC 对比 × 3、backtest × 5、临时数据 × 6 — 共 27 项已移出 `out/`，迁移至 memory 或删除。

---

## 检索指南

| 想找什么 | 怎么找 |
|---------|--------|
| "我有没有关于 X 的回测？" | `grep -i "X" personal-system/BACKTEST_INDEX.md` |
| "我的法则说什么" | `grep "X" personal-system/LAWS.md` |
| "X 假设是否被验证" | `grep "X" personal-system/OPEN_HYPOTHESES.md` |
| "X 假设被推翻了吗" | `grep "X" personal-system/FAILED_LAWS.md` |
| "今天学到了什么" | `cat personal-system/raw-log/2026-07-23.md`（或查看最近的 raw-log） |
| "上周的回测" | `ls personal-system/backtests/ | grep BT-` |
| **"LAW-XXX 的 5-Why 吗？"** | `grep "5-Why Challenge" personal-system/LAWS.md -A 20` |
| **"HYP-XXX 的 5-Why？"** | `grep "5-Why Adversarial" personal-system/OPEN_HYPOTHESES.md -A 20` |
| **"BT-XXX 的 Adversarial Review？"** | `grep "Adversarial Review" personal-system/BACKTEST_INDEX.md -A 10` |
| **"框架内有什么冲突？"** | `grep "CONFLICT-LOGIC\|CONFLICT-REGIME" personal-system/CONFLICTS.md` |
