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
| `HYPOTHESES.md` | 待验证的猜想（每条含 5-Why Adversarial） | 静态 | ✅ **2026-08-04 Tier 分类精简后 20 活跃 + 1 OBSERVATION（HYP-019）+ 1 SUSPENDED（HYP-010）+ 1 元评估（HYP-025）**；HYP-001 标记归档至 FAILED；HYP-008 不存在；**HYP-031 已合并入 HYP-027 v3**；Tier 1：HYP-016/015/006/026/021/029；Tier 2：HYP-002/014/028/011/020/024/017/030；Tier 3：HYP-027/003/004/022/018/023；**三剧本概率重分配：HYP-029 50-55% 主导 / HYP-028 30-40% 辅助 / HYP-027 10-15% 尾部风险**；**HYP-027 v3 = 庄家式过山车剧本（已降为尾部风险情景）**；**HYP-028 v3 = 有效时长 8-12 年**；**HYP-029 v2 = 中国反向操作 + 通胀排序 中<美<欧（Tier 1 主导）**）；**概率更新规则见 `HYP_UPDATE_RULES.md`（2026-08-04 评论驱动方案 B 实施）**） |
| `HYP_UPDATE_RULES.md` | **概率更新规则 + 截止日 + 反向条件（评论驱动方案 B 实施）** — 显式信号→概率变化表，覆盖 Tier 1 + 化债三剧本（7 条 HYP）；区间中位 + Brier 可校准；与 HYPOTHESES.md 描述解耦 | 静态（季度复审） | ✅ 2026-08-04 创建（HYP-016/015/006/002/029/028/027 全部含上修/下修信号+反向截止）|
| `decision-journal/` | **概率性决策日志 + Brier 季度校准** — `YYYY-MM-DD.md` 登记每条预测；`brier-quarterly/YYYY-QN.md` 季度评分；Brier < 0.15 = 框架在加值；连续 2 季度 > 0.20 触发 5-Why 蒸馏 | **强时序** | ✅ 2026-08-04 创建（首批 7 条预测登记：HYP-029/028/027/016/015/002 + HYP-006 触发器状态）|
| `HYP-UNUSED.md` | 归档假设库（ARCHIVED / RETIRED 完整正文 + 5-Why，2026-08-04 从 HYPOTHESES.md 迁出） | 静态（远期回溯用） | ✅ 已创建（HYP-031 RETIRED + HYP-005/007/012/013 ARCHIVED；含恢复条件；原位置指针防断链） |
| `BACKTEST_INDEX.md` | 回测台账（每条含 Adversarial Review） | 静态（追加） | ✅ 6/6 已填充 |
| `CONFLICTS.md` | 冲突记录（回溯/逻辑/Regime） | 静态 | ✅ 11条已记录（**4 OPEN + 7 RESOLVED**；CONFLICT-LOGIC-008 已合并入 HYP-027 v3；**CONFLICT-LOGIC-009 化债收官口径 2026-08-04 用户裁决 RESOLVED — 保持 2027-06-30**） |
| `SELL_LADDER.md` | 卖出梯子规则 | 静态 | 待补 |
| `POSITION_SIZING.md` | 仓位管理 | 静态 | 已填充 |
| `BROKER_OBSERVATION.md` | 券商板块观察指标体系 | 静态 | 已创建 + **v1.4 CDS 双层阈值修订 2026-08-04**（触发 5 降级为复核；触发 6 新增 100bp 清仓） |
| `NATIONAL_TEAM_OBSERVATION.md` | 国家队全口径资金监测 | 动态（月度更新） | ✅ 已创建 |
| `raw-log/YYYY-MM-DD.md` | 每日原始记录（**强时序，保留全部** — 用于证据回溯；已蒸馏的认知标注归档关系） | **强时序** | 14 文件（截至 2026-08-04） |
| `CHINA_FRAMEWORK.md` | **A 股独立投资框架 v1.4**（化债市总纲/国家机器/退出纪律/反方章节/借通胀窗口/**v1.4 CDS 阈值拆分 2026-08-04**；与 US_FRAMEWORK.md 平级，跨市场协调见 US_FRAMEWORK.md §九）| 静态 | v1.4 升级（**CDS 双层阈值**：30bp 预警 / 50bp 复核 / 100bp 清仓——与 US 对齐；§1.3 + §3.2 + §4.3 + §6.2 + §10.1 + §10.2 + §10.3 + §11 总览 + §13 反方 共 13 处同步；含 HYP-029 v2 中国反向操作；§10.3 月度检查清单 CDS 与 §10.1 一致化；§11.B 沪指/沪深300 实时刷新；§13.6 HYP-029 v2 触发状态标记 2/5）|
| `US_FRAMEWORK.md` | **美股独立投资框架 v2.1**（总纲/观察/配置/双剧本联动/反方章节/**§1.3 双剧本观察表更新为中选后 6-9 月触发窗口 / §2.2.1 summary 表 v3 修正数据 2026-08-04**；与 CHINA_FRAMEWORK.md 平级，跨市场协调见其"九、总组合协调层"）| 静态 | v2.1 升级（HYP-027 v3 + HYP-028 v3 + HYP-029 v2 整合；**§2.2.1 summary 表修正**：旧估算~150-180% / 估算~320%+ 已替换为 v3 整体指标 34.9% / 22.7% / 18.4% + META 35.1% 警示红旗；数据缺口"精确 Capex/Revenue 比值"行删除（已解决））|
| `HYP-027-V3-DETAILS.md` | **HYP-027 v3 完整证据库 + 配置矩阵（合并文件，与 HYPOTHESES.md / CHINA_FRAMEWORK.md 等同级）** — **三部分结构**：① **数学敏感性**（模型一/二/三 + 123→80% 所需资产重估 + 5-Why 最薄弱） ② **机制工具扩展**（政治工具 P1-P12 + 瞒天过海 5 条路径 + 主动发行 P13-P17 即 2008 CDS 模板升级版 + 石油 vs 黄金品种选择 + 工具组合优先级 + 阶段应用） ③ **阶段 × 国家 × 资产 配置矩阵**（阶段 0-6 各自国家/货币 + 资产类型多空判断 + 跨阶段对冲组合） | 静态（随阶段演进更新）| 2026-08-04 创建（v3 合并版：原 REPORT.md 数学 + 原 asset-matrix.md 配置合并到一处；v3.1 扩展：政治工具 + 瞒天过海 + 主动发行），保留 Python 复现代码 `research/asset-blowdown-takeover-2026/blowdown_takeover_model.py` |
| `distillation-log/YYYY-MM-DD_NNN.md` | 蒸馏事件 | **强时序** | 1 文件 |
| `backtests/BT-XXX/` | 每个回测一个目录 | 静态 | 6 目录 |
| `theses/<code>_<name>.md` | 个股研究论 | 静态 | 1 文件 |

---

## 2. market-regime/

- 暂未填充（2026-Q2.md 暂未创建 — 待 regime 分析师决定季度节奏）

---

## 3. skill-changelog/

- `2026-07-22_added-personal-trading-system.md` - skill 创建记录
- 暂未填充

---

## 当前活跃内容

**最后更新:** 2026-08-04 (memory 全面整理与一致性核查)（券商 50% 集中度论点 4 路对抗检验全部完成：委员会辩论韧性 4/10 + 蓝海扫描 + 七前提验证 2/5 触发 + BT-006；用户 8 问全部回答；**用户裁决 CONFLICT-LOGIC-009 RESOLVED（化债保持 2027-06-30 不变）**；**新增 USER_RULE 候选 LAW-005（≥300亿市值 + 非 A 字型 + 真正未启动）**；**框架修正**：CHINA_FRAMEWORK §10.3 CDS 与 §10.1 一致化、§11.B 沪指/沪深300 实时刷新、§13.6 HYP-029 v2 触发状态 2/5；HYPOTHESES HYP-029 v2 触发状态已更新；INDEX 各项计数同步；**本轮实施**：POSITION_SIZING 持仓快照 2026-07-21→2026-08-03（17 只股票 + 券商 ETF）；NATIONAL_TEAM 4 只 ETF 份额刷新（510300 数据补全）；SELL_LADDER 整理归档（Tier 3 已被 BT-005/006 否定，改为信号触发 + 时间触发）；**HYP-027 v3 详情文件**：原 asset-matrix.md + REPORT.md + 用户 4 个深度问题（政治工具/瞒天过海/主动发行/品种选择）合并到 `HYP-027-V3-DETAILS.md` 三部分结构；**文件重命名**：OPEN_HYPOTHESES.md → HYPOTHESES.md（核心文件 33 处 active 引用同步更新）；**memory 整理 13 项**：CONFLICTS.md 重复段落清理、BACKTEST_INDEX.md 5 条→6 条、INDEX.md 已解决数 9→10、LAWS.md 5-Why 强制检查日期补全等；**本轮清理**：HYPOTHESES 全部 HYP 删除冗余版本修正 log（v1/v2/v3 轨迹块、v3 重大修正标注、已订正注脚），保留版本号标识与 5-Why/审计事实，HYP-016 修正说明块保留为正文；US_FRAMEWORK/BROKER_OBSERVATION/CHINA_FRAMEWORK/HYP-027-V3-DETAILS/POSITION_SIZING 同步净化；审计痕迹保留于 raw-log/2026-08-04.md）
**回测总数:** 6 (BT-001~006)
**本轮追加 (2026-08-04 下午):** 评论驱动方案 B 实施 — 新增 `HYP_UPDATE_RULES.md`（7 条 HYP 显式上修/下修信号+反向截止）+ `decision-journal/`（首批 7 条预测登记 + 季度 Brier 评分模板）；HYPOTHESES.md 零新增；详细登记见 `decision-journal/2026-08-04.md`
**本轮追加 (2026-08-04 晚):** P0 编辑 + memory 全扫描修复 — (1) US_FRAMEWORK §2.2.1 summary 表脏数据修正（估算~150-180% → 34.9%；估算~320%+ → 22.7% + META 警示红旗）(2) CDS 阈值 v1.4 双层拆分（30bp 预警 / 50bp 复核 / 100bp 清仓）覆盖 5 个文件 20+ 处；INDEX 版本号同步
**活跃法则数:** 3 (LAW-001~003，全部含 5-Why Challenge；LAW-004 → HYP-013；**USER_RULE 候选 LAW-005 — 用户偏好硬约束 ≥300亿+非A字型+真正未启动**)
**失效法则数:** 1 (FAILED-001 — 券商原假设)
**开放假设数:** **20 活跃 + 1 OBSERVATION（HYP-019）+ 1 SUSPENDED（HYP-010）+ 1 元评估（HYP-025）+ 1 RETIRED（HYP-031）+ 4 ARCHIVED（HYP-005/007/012/013 → HYP-UNUSED.md）**（2026-08-04 Tier 1-4 分类精简：Tier 1 = HYP-016/015/006/026/021/029；Tier 2 = HYP-002/014/028/011/020/024/017/030；Tier 3 = HYP-027/003/004/022/018/023；HYP-009 已并入 HYP-016；HYP-001 已归档至 FAILED-001；HYP-008 不存在；**归档正文统一存放于 HYP-UNUSED.md**；**三剧本概率重分配：HYP-029 50-55% 主导 / HYP-028 30-40% 辅助 / HYP-027 10-15% 尾部风险（2026-08-04 用户分级）**；HYP-027 v3 庄家式过山车剧本（降为尾部风险）；HYP-028 v3 有效时长 8-12 年；HYP-029 v2 触发状态 2/5（已更新））
**开放冲突数:** 4 (CONFLICT-REGIME-001, CONFLICT-LOGIC-002, CONFLICT-BLINDSPOT-001, CONFLICT-LOGIC-007；CONFLICT-LOGIC-008 已合并入 HYP-027 v3；CONFLICT-LOGIC-009 RESOLVED)
**已解决冲突数:** 10 (LOGIC-001/003/004/005/006/008/009, REGIME-002, METHOD-001/002)
**5-Why 系统:** ✅ 已集成
**国家队 regime:** 🔴 净卖出（FactSet 数据确认，持续监控）
**框架版本:** `personal-system/CHINA_FRAMEWORK.md` v1.4（A 股独立框架，含"借通胀窗口"章节 + **CDS 双层阈值拆分** 2026-08-04）| `personal-system/US_FRAMEWORK.md` v2.1（美股独立框架，2026-08-03 化债双剧本 v3 完整重做 + **§2.2.1 summary 表 v3 修正数据** 2026-08-04）
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
| "X 假设是否被验证" | `grep "X" personal-system/HYPOTHESES.md` |
| "X 假设被推翻了吗" | `grep "X" personal-system/FAILED_LAWS.md` |
| "今天学到了什么" | `cat personal-system/raw-log/2026-07-23.md`（或查看最近的 raw-log） |
| "上周的回测" | `ls personal-system/backtests/ | grep BT-` |
| **"LAW-XXX 的 5-Why 吗？"** | `grep "5-Why Challenge" personal-system/LAWS.md -A 20` |
| **"HYP-XXX 的 5-Why？"** | `grep "5-Why Adversarial" personal-system/HYPOTHESES.md -A 20` |
| **"BT-XXX 的 Adversarial Review？"** | `grep "Adversarial Review" personal-system/BACKTEST_INDEX.md -A 10` |
| **"框架内有什么冲突？"** | `grep "CONFLICT-LOGIC\|CONFLICT-REGIME" personal-system/CONFLICTS.md` |
| **"HYP-XXX 的概率更新规则？"** | `grep "HYP-XXX\|上修信号\|下修信号" personal-system/HYP_UPDATE_RULES.md -A 30` |
| **"我预测了什么/最近评分？"** | `ls -t personal-system/decision-journal/ \| head` 或 `cat personal-system/decision-journal/brier-quarterly/2026-QN.md` |
| **"某 HYP 当前概率 + 置信度？"** | `grep "HYP-XXX" personal-system/decision-journal/YYYY-MM-DD.md -A 8` |

---

## 1.5 raw-log 归档状态（2026-08-04 更新）

| raw-log 文件 | 主要内容 | 已蒸馏到 |
|------------|---------|---------|
| 2026-07-22.md | 框架建立 + 初始 LAW/HYP 候选 | LAWS.md (LAW-001/002/003 雏形) + FAILED_LAWS.md (FAILED-001 雏形) + HYPOTHESES.md (HYP-001~007 雏形) |
| 2026-07-23.md | 当日认知 | 部分归档到 LAWS-002 + HYPOTHESES |
| 2026-07-28.md | 当日认知 | 部分归档到 BACKTEST_INDEX.md |
| 2026-07-29.md | 当日认知 | 精简待归档（短文件，19 行）|
| 2026-07-30.md | 当日认知 | 部分归档到 HYPOTHESES (HYP-013~018) |
| 2026-07-31.md | Cross-Market Validation | 关键结论已蒸馏到 HYPOTHESES (HYP-002 v4) + BROKER_OBSERVATION.md |
| 2026-07-31-oligarch-rotation-4th-pushback.md | 寡头轮换 4th pushback | 关键机制已蒸馏到 HYPOTHESES (HYP-027 v3) |
| 2026-07-31-us-debt-250-year-historical-analysis.md | 化债 250 年历史 | 关键洞察已蒸馏到 HYPOTHESES (HYP-028 v3) + US_FRAMEWORK.md §1.3 |
| 2026-07-31-us-debt-resolution-theory-5-agent-review.md | 化债 5 agent 评审 | 关键洞察已蒸馏到 HYPOTHESES (HYP-027~028 v3) |
| 2026-07-31-us-debt-resolution-theory-revised.md | 化债理论修正 | 同上 |
| 2026-08-02.md / round2~round4 | Round 2-4 资产拉爆机制 | 关键洞察已蒸馏到 HYPOTHESES (HYP-027/028 v3) + HYP-029 |
| 2026-08-03.md | Round 6-9 + 券商诊断 + regime 分析 | 当日认知已蒸馏到 HYPOTHESES (HYP-029 v2) + BROKER_OBSERVATION.md + BROKER 诊断报告 + CONFLICTS.md (CONFLICT-LOGIC-009) |
| 2026-08-04.md | BT-006 + 机制解释 + 保险研究 + **用户裁决 + USER_RULE 候选 LAW-005 + memory 冗余 log 清理** | 当日认知已蒸馏到 BACKTEST_INDEX.md (BT-006) + HYPOTHESES.md (HYP-029 v2 触发状态) + CONFLICTS.md (CONFLICT-LOGIC-009 RESOLVED) + US_FRAMEWORK/BROKER/CHINA_FRAMEWORK/HYP-027-V3-DETAILS/POSITION_SIZING 清理 |

**保留原因**：raw-log 是"原始事件证据"，保留以备：(1) 5-Why Adversarial 引用 ② 框架重大变更回溯 ③ 用户决策历史审计。
**清理策略**：永不删除；如体积过大，单文件 > 100KB 时考虑归档到 .opencode/memory/personal-system/raw-log/archive/ 子目录（**当前未触发**，所有文件 < 50KB）。

