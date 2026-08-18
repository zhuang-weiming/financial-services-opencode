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
| `1.LAWS.md` | 已验证生效的法则（每条含 5-Why Challenge） | 静态（蒸馏后） | ✅ 3/3 已填充 |
| `1.1.FAILED_LAWS.md` | 已失效/未支持的规则 | 静态（蒸馏后） | ✅ 1/1 已填充 |
| `2.HYPOTHESES.md` | 待验证的猜想（每条含 5-Why Adversarial） | 静态 | ✅ **2026-08-04 Tier 分类精简后 20 活跃 + 1 OBSERVATION（HYP-019）+ 1 SUSPENDED（HYP-010）+ 1 元评估（HYP-025）**；HYP-001 标记归档至 FAILED；HYP-008 不存在；**HYP-031 已合并入 HYP-027 v3**；Tier 1：HYP-016/015/006/026/021/029；Tier 2：HYP-002/014/028/011/020/024/017/030；Tier 3：HYP-027/003/004/022/018/023；**三剧本概率重分配：HYP-029 50-55% 主导 / HYP-028 30-40% 辅助 / HYP-027 10-15% 尾部风险**；**HYP-027 v3 = 庄家式过山车剧本（已降为尾部风险情景）**；**HYP-028 v3 = 有效时长 8-12 年**；**HYP-029 v2 = 中国反向操作 + 通胀排序 中<美<欧（Tier 1 主导）**）；**概率更新规则见 `2.3.HYP_UPDATE_RULES.md`（2026-08-04 评论驱动方案 B 实施）**） |
| `2.3.HYP_UPDATE_RULES.md` | **概率更新规则 + 截止日 + 反向条件（评论驱动方案 B 实施）** — 显式信号→概率变化表，覆盖 Tier 1 + 化债三剧本（7 条 HYP）；区间中位 + Brier 可校准；与 2.HYPOTHESES.md 描述解耦 | 静态（季度复审） | ✅ 2026-08-04 创建（HYP-016/015/006/002/029/028/027 全部含上修/下修信号+反向截止）|
| `decision-journal/` | **概率性决策日志 + Brier 季度校准** — `YYYY-MM-DD.md` 登记每条预测；`brier-quarterly/YYYY-QN.md` 季度评分；Brier < 0.15 = 框架在加值；连续 2 季度 > 0.20 触发 5-Why 蒸馏 | **强时序** | ✅ 2026-08-04 创建（首批 7 条预测登记：HYP-029/028/027/016/015/002 + HYP-006 触发器状态）|
| `2.1.HYP-UNUSED.md` | 归档假设库（ARCHIVED / RETIRED 完整正文 + 5-Why，2026-08-04 从 2.HYPOTHESES.md 迁出） | 静态（远期回溯用） | ✅ 已创建（HYP-031 RETIRED + HYP-005/007/012/013 ARCHIVED；含恢复条件；原位置指针防断链） |
| `5.BACKTEST_INDEX.md` | 回测台账（每条含 Adversarial Review） | 静态（追加） | ✅ 15 主体 + v2.x 系归档（BT-001~008, 010~016）|
| `6.CONFLICTS.md` | 冲突记录（回溯/逻辑/Regime） | 静态 | ✅ 12条已记录（**5 OPEN + 7 RESOLVED**；CONFLICT-LOGIC-008 已合并入 HYP-027 v3；**CONFLICT-LOGIC-009 化债收官口径 2026-08-04 用户裁决 RESOLVED**；**CONFLICT-BLINDSPOT-002 ⭐ 2026-08-07 部分 RESOLVED** — 4.2 v5.1 §三.3 新增供应链领先层 + 时间窗前移 6-12→6-9 月；剩余 OPEN 子项 (a) "3-6 月 vs 6-9 月" 阈值未定 (b) hyperscaler -20% 触发 (c) SK Hynix -50% 是 capex 见顶 vs HBM 周期） |
| `7.SELL_LADDER.md` | 卖出梯子规则 v2.5 | 静态 | ✅ 已填充（16 信号矩阵 + 5 动能结束标志 + 3 阶段）|
| `7.1.POSITION_SIZING.md` | 仓位管理 | 静态 | 已填充 |
| `8.BUY_LADDER.md` | 买入梯子规则 **v3.1**（BT-015/016 回测定案：4 信号 2/2/1/1 积分 + 绝对阈值 ≥4 击球/≥3 观察；Layer 0/1 咨询性；判定链 = ST → 否决 → 积分）| 静态 | ✅ v3.1（2026-08-13，数据驱动积分）|
| **`buy-ladder/`** | **BUY_LADDER v3.1 能力**（`buy_ladder.py` 积分计票；`runs/` 历史结果；判定链 = ST 红牌 → 5 否决 → 积分绝对阈值）| **可执行** | **v3.1（2026-08-13）** |
| `4.BROKER_OBSERVATION.md` | 券商板块观察指标体系 | 静态 | 已创建 + **v1.4 CDS 双层阈值修订 2026-08-04**（触发 5 降级为复核；触发 6 新增 100bp 清仓） |
| `4.1.NATIONAL_TEAM_OBSERVATION.md` | 国家队全口径资金监测 | 动态（月度更新） | ✅ 已创建 |
| `4.2.AI_BUBBLE_TRACKING.md` | **AI 泡沫跟踪与撤退策略**（**2026-08-07 v5.1** — v5.1 升级：新增 §三.3 供应链领先层真实数据 + §三.4 中国 LLM API 价格；时间窗 "6-12 月" → "**6-9 月**" 置信度下调；含 5 信号 + 联动规则 + 对冲工具） | 静态（季度更新） | ✅ **v5.1 升级**（2026-08-07）+ market-researcher subagent 反方验证 |
| `raw-log/YYYY-MM-DD.md` | 每日原始记录（**强时序，保留全部** — 用于证据回溯；已蒸馏的认知标注归档关系） | **强时序** | 16 文件（截至 2026-08-04，含当日 2 次追加：P0 编辑 + 二次复核） |
| `3.1.CHINA_FRAMEWORK.md` | **A 股独立投资框架 v1.4**（化债市总纲/国家机器/退出纪律/反方章节/借通胀窗口/**v1.4 CDS 阈值拆分 2026-08-04**；与 3.US_FRAMEWORK.md 平级，跨市场协调见 3.US_FRAMEWORK.md §九）| 静态 | v1.4 升级（**CDS 双层阈值**：30bp 预警 / 50bp 复核 / 100bp 清仓——与 US 对齐；§1.3 + §3.2 + §4.3 + §6.2 + §10.1 + §10.2 + §10.3 + §11 总览 + §13 反方 共 13 处同步；含 HYP-029 v2 中国反向操作；§10.3 月度检查清单 CDS 与 §10.1 一致化；§11.B 沪指/沪深300 实时刷新；§13.6 HYP-029 v2 触发状态标记 2/5）|
| `3.US_FRAMEWORK.md` | **美股独立投资框架 v2.1**（总纲/观察/配置/双剧本联动/反方章节/**§1.3 双剧本观察表更新为中选后 6-9 月触发窗口 / §2.2.1 summary 表 v3 修正数据 2026-08-04**；与 3.1.CHINA_FRAMEWORK.md 平级，跨市场协调见其"九、总组合协调层"）| 静态 | v2.1 升级（HYP-027 v3 + HYP-028 v3 + HYP-029 v2 整合；**§2.2.1 summary 表修正**：旧估算~150-180% / 估算~320%+ 已替换为 v3 整体指标 34.9% / 22.7% / 18.4% + META 35.1% 警示红旗；数据缺口"精确 Capex/Revenue 比值"行删除（已解决））|
| `2.2.HYP-027-V3-DETAILS.md` | **HYP-027 v3 完整证据库 + 配置矩阵（合并文件，与 2.HYPOTHESES.md / 3.1.CHINA_FRAMEWORK.md 等同级）** — **三部分结构**：① **数学敏感性**（模型一/二/三 + 123→80% 所需资产重估 + 5-Why 最薄弱） ② **机制工具扩展**（政治工具 P1-P12 + 瞒天过海 5 条路径 + 主动发行 P13-P17 即 2008 CDS 模板升级版 + 石油 vs 黄金品种选择 + 工具组合优先级 + 阶段应用） ③ **阶段 × 国家 × 资产 配置矩阵**（阶段 0-6 各自国家/货币 + 资产类型多空判断 + 跨阶段对冲组合） | 静态（随阶段演进更新）| 2026-08-04 创建（v3 合并版：原 REPORT.md 数学 + 原 asset-matrix.md 配置合并到一处；v3.1 扩展：政治工具 + 瞒天过海 + 主动发行），保留 Python 复现代码 `research/asset-blowdown-takeover-2026/blowdown_takeover_model.py` |
| `distillation-log/YYYY-MM-DD_NNN.md` | 蒸馏事件 | **强时序** | 1 文件 |
| `backtests/BT-XXX/` | 每个回测一个目录 (BT-001~016) | 静态 | 16 目录（BT-009-v2x 已归档清理，记录在 INDEX）|
| `theses/<code>_<name>.md` | 个股研究论 | 静态 | 1 文件 |
| **`sell-ladder/`** | **SELL_LADDER v2.0 能力** (14 skill 信号矩阵 + 5 动能结束标志 + 3 阶段框架; `sell_ladder.py` 可重跑; `data/` 永久数据; `runs/` 历史结果) | **可执行** | **1 目录 (2026-08-10 新建)** |

---

## 2. market-regime/

- 暂未填充（2026-Q2.md 暂未创建 — 待 regime 分析师决定季度节奏）

---

## 3. skill-changelog/

- `2026-07-22_added-personal-trading-system.md` - skill 创建记录
- 暂未填充

---

## 当前活跃内容

**最后更新:** 2026-08-10 19:00 (**BT-008 入库 — SELL_LADDER v2.0 有效性回测**: 2026 科技股行情 walk-forward, 7 标的 × 28 周 = 196 评估点, 发现 **factor_research 死灯 BUG** (f2_ic>0.5 数学不可达 → v2.0 阶段 1 永不触发, 已修复 v2.1 multi_factor 补位) + **阶段 3 阈值过敏感** (超前实际顶 64-115 交易日, 4/7 标的踏空; 建议 v2.2 连续确认)。BT-008 存放在 backtests/, 工具更新: sell_ladder.py calc_multi_factor 补 strong_momentum + backtest_seed_2026.py --variant) | 上一轮: SELL_LADDER v2.0 落地 (14 skill 矩阵 + 5 动能结束标志 + 3 阶段框架, 工具永久存放 `personal-system/sell-ladder/`, 药石 300725: 4/5 强动能 + 0/5 结束 → 阶段 2 动能衰减期; 详见 `sell-ladder/README.md` + `7.1.POSITION_SIZING.md §5.5`)
**回测总数:** 8 (BT-001~008; BT-008 = SELL_LADDER v2.0 有效性 2026-08-10)
**本轮追加 (2026-08-06 19:00):** **personal-system/ 文件命名重构** — 14 个文件 git mv + 1 个新文件 + 70+ 个引用批量更新。编号体系：**1.** 法则（1.LAWS / 1.1.FAILED_LAWS）/ **2.** 假设（2.HYPOTHESES / 2.1.HYP-UNUSED / 2.2.HYP-027-V3-DETAILS / 2.3.HYP_UPDATE_RULES）/ **3.** 框架（3.US_FRAMEWORK / 3.1.CHINA_FRAMEWORK）/ **4.** 观察（4.BROKER_OBSERVATION / 4.1.NATIONAL_TEAM_OBSERVATION / 4.2.AI_BUBBLE_TRACKING）/ **5.** 回测 / **6.** 冲突 / **7.** 操作（7.SELL_LADDER / 7.1.POSITION_SIZING）。git history 完整保留（14 个 rename + 1 个 new file + 5 个 modified due to 引用更新）。详见 raw-log 19:00 段。
**本轮追加 (2026-08-07):** **4.2 v5.1 升级** — 用户质询 "美国是浪潮控制人，韩国/中国是 follower" → 加载 skills (research-discipline/data-routing/bottleneck-hunter/quant-statistics/personal-trading-system) → Morningstar MCP 拉 7 家公司真实数据 (TSMC/Samsung/SK Hynix/Micron/中际旭创/Coherent/Lumentum) → DDG 全 blocked 触发派 market-researcher subagent (4200 字反方报告) → 5-Why 终极反方拒绝 "3-6 月" 激进断言 → v5 → v5.1 写回 9 个编辑：(1) §三.1 时间窗 6-12 月 → **6-9 月**置信度下调 (2) §三.3 新增供应链领先层（SK Hynix -49.95% / Micron P/FV 1.04 / Lumentum -11.7% op margin 等 7 家真实数据 + 反方裁决）(3) §三.4 新增中国 LLM API 价格（Kimi K3 ¥20/¥100 不是 commodity，HSBC 8-03 验证）(4) §八.2 月度监控追加 7 个新触发器 (5) §九.2 终极判定 v5.1 修正 (6) §十 风险披露 v5.1 数据空缺 (7-9) §十一 版本/触发/空缺更新。同时：6.CONFLICTS.md 新增 **CONFLICT-BLINDSPOT-002** 部分 RESOLVED；decision-journal/2026-08-07.md 新增 4 条 v5.1 预测登记。
**本轮追加 (2026-08-06 17:00):** **AI 泡沫跟踪文件 v5 迁入 memory** — 原 `out/ai-bubble-report-20260806.md` 已删除，迁入 `personal-system/4.2.AI_BUBBLE_TRACKING.md`（命名风格参照 `4.BROKER_OBSERVATION.md` / `4.1.NATIONAL_TEAM_OBSERVATION.md`）。用户三轮反问带来 4 个根本性修正：(1) "避风港"→"减震器/真避风港"三分类；(2) 跷跷板逻辑修正（港股科技不是避风港）；(3) 删除"软/硬着陆"二分；(4) 4 级阶梯与减仓次序联动规则（5 信号触发数 → 综合减仓）。**US_FRAMEWORK 新增 §十二·附录** 整合上述 4 项修正。raw-log 17:00 段记录完整决策历史。
**本轮追加 (2026-08-04 下午):** 评论驱动方案 B 实施 — 新增 `2.3.HYP_UPDATE_RULES.md`（7 条 HYP 显式上修/下修信号+反向截止）+ `decision-journal/`（首批 7 条预测登记 + 季度 Brier 评分模板）；2.HYPOTHESES.md 零新增；详细登记见 `decision-journal/2026-08-04.md`
**本轮追加 (2026-08-04 晚):** P0 编辑 + memory 全扫描修复 — (1) US_FRAMEWORK §2.2.1 summary 表脏数据修正（估算~150-180% → 34.9%；估算~320%+ → 22.7% + META 警示红旗）(2) CDS 阈值 v1.4 双层拆分（30bp 预警 / 50bp 复核 / 100bp 清仓）覆盖 5 个文件 20+ 处；INDEX 版本号同步
**活跃法则数:** 3 (LAW-001~003，全部含 5-Why Challenge；LAW-004 → HYP-013；**USER_RULE 候选 LAW-005 — 用户偏好硬约束 ≥300亿+非A字型+真正未启动**)
**失效法则数:** 1 (FAILED-001 — 券商原假设)
**开放假设数:** **20 活跃 + 1 OBSERVATION（HYP-019）+ 1 SUSPENDED（HYP-010）+ 1 元评估（HYP-025）+ 1 RETIRED（HYP-031）+ 4 ARCHIVED（HYP-005/007/012/013 → 2.1.HYP-UNUSED.md）**（2026-08-04 Tier 1-4 分类精简：Tier 1 = HYP-016/015/006/026/021/029；Tier 2 = HYP-002/014/028/011/020/024/017/030；Tier 3 = HYP-027/003/004/022/018/023；HYP-009 已并入 HYP-016；HYP-001 已归档至 FAILED-001；HYP-008 不存在；**归档正文统一存放于 2.1.HYP-UNUSED.md**；**三剧本概率重分配：HYP-029 50-55% 主导 / HYP-028 30-40% 辅助 / HYP-027 10-15% 尾部风险（2026-08-04 用户分级）**；HYP-027 v3 庄家式过山车剧本（降为尾部风险）；HYP-028 v3 有效时长 8-12 年；HYP-029 v2 触发状态 2/5（已更新））
**开放冲突数:** 5 (CONFLICT-REGIME-001, CONFLICT-LOGIC-002, CONFLICT-BLINDSPOT-001, CONFLICT-LOGIC-007, **CONFLICT-BLINDSPOT-002 部分 RESOLVED — 4.2 v5.1 §三.3 供应链领先层；剩余 OPEN 子项 (a) "3-6 vs 6-9 月" 阈值 (b) hyperscaler -20% 触发 (c) SK Hynix -50% 信号归属**；CONFLICT-LOGIC-008 已合并入 HYP-027 v3；CONFLICT-LOGIC-009 RESOLVED)
**已解决冲突数:** 10 (LOGIC-001/003/004/005/006/008/009, REGIME-002, METHOD-001/002)
**5-Why 系统:** ✅ 已集成
**国家队 regime:** 🔴 净卖出（FactSet 数据确认，持续监控）
**框架版本:** `personal-system/3.1.CHINA_FRAMEWORK.md` v1.4（A 股独立框架，含"借通胀窗口"章节 + **CDS 双层阈值拆分** 2026-08-04）| `personal-system/3.US_FRAMEWORK.md` v2.1（美股独立框架，2026-08-03 化债双剧本 v3 完整重做 + **§2.2.1 summary 表 v3 修正数据** 2026-08-04 + **§十二·附录 AI 泡沫 5 信号联动规则 2026-08-06**）
**数据架构:** `data/` 集中数据仓库已建立（market/earnings/factors/cache 四子目录）

### 当前 out/ 内容（清理后）

| 报告 | 文件 | 时间 |
|:-----|:-----|:----:|
| 跨市场 debrief | `out/daily-debrief-20260729/` | 2026-07-29 |
| HSBC vs framework Q3 verdict | `out/hsbc-vs-framework-verdict-q3-20260728.md` | 2026-07-28 |
| 市场 debrief | `out/market-debrief-20260805/` | 2026-08-05 |
| AI 泡沫×通胀历史类比报告 | `personal-system/reports/ai-bubble-inflation-historical-analogues-2026-08-13.md` | 2026-08-13 |
| **AI 泡沫×通胀阶段 × 30+ 大类资产 × 巴菲特操作** | `personal-system/reports/ai-bubble-inflation-stages-deep-2026-08-18.md` (**新**) | 2026-08-18 |
| 剧本概率客观化（三算法） | ✅ 已迁入 `personal-system/research/probability-objectification-2026/`（alg1 信号计分 / alg2 贝叶斯 / alg3 历史相似 + consolidate 汇总，三法均值 16.3/29.0/15.4/39.3；README 含重跑方法） | 2026-08-17 |
| 剧本概率蒙特卡洛层 | ✅ 已迁入 `personal-system/research/probability-objectification-2026/`（alg4_monte_carlo.py, 3000 iters — ensemble 95% CI: D [31.5,44.2]% 头号 91.7%, A>25% 仅 0.0%; + alg4_sigma2x_sensitivity.json） | 2026-08-17 |

> **2026-08-06 清理：** `out/ai-bubble-report-20260806.md` 已删除，内容迁入 `personal-system/4.2.AI_BUBBLE_TRACKING.md`（长期跟踪文件）

### 历史 one-off 报告（已清理）

> 2026-07-31 清理：删除 GWM/COSCO/ChinaUnicom/Hundsun 公司 deep-dive × 7、datapack × 3、portfolio × 3、HSBC 对比 × 3、backtest × 5、临时数据 × 6 — 共 27 项已移出 `out/`，迁移至 memory 或删除。

---

## 检索指南

| 想找什么 | 怎么找 |
|---------|--------|
| "我有没有关于 X 的回测？" | `grep -i "X" personal-system/5.BACKTEST_INDEX.md` |
| "我的法则说什么" | `grep "X" personal-system/1.LAWS.md` |
| "X 假设是否被验证" | `grep "X" personal-system/2.HYPOTHESES.md` |
| "X 假设被推翻了吗" | `grep "X" personal-system/1.1.FAILED_LAWS.md` |
| "今天学到了什么" | `cat personal-system/raw-log/2026-07-23.md`（或查看最近的 raw-log） |
| "上周的回测" | `ls personal-system/backtests/ | grep BT-` |
| **"LAW-XXX 的 5-Why 吗？"** | `grep "5-Why Challenge" personal-system/1.LAWS.md -A 20` |
| **"HYP-XXX 的 5-Why？"** | `grep "5-Why Adversarial" personal-system/2.HYPOTHESES.md -A 20` |
| **"BT-XXX 的 Adversarial Review？"** | `grep "Adversarial Review" personal-system/5.BACKTEST_INDEX.md -A 10` |
| **"框架内有什么冲突？"** | `grep "CONFLICT-LOGIC\|CONFLICT-REGIME" personal-system/6.CONFLICTS.md` |
| **"HYP-XXX 的概率更新规则？"** | `grep "HYP-XXX\|上修信号\|下修信号" personal-system/2.3.HYP_UPDATE_RULES.md -A 30` |
| **"我预测了什么/最近评分？"** | `ls -t personal-system/decision-journal/ \| head` 或 `cat personal-system/decision-journal/brier-quarterly/2026-QN.md` |
| **"某 HYP 当前概率 + 置信度？"** | `grep "HYP-XXX" personal-system/decision-journal/YYYY-MM-DD.md -A 8` |

---

## 1.5 raw-log 归档状态（2026-08-04 更新）

| raw-log 文件 | 主要内容 | 已蒸馏到 |
|------------|---------|---------|
| 2026-07-22.md | 框架建立 + 初始 LAW/HYP 候选 | 1.LAWS.md (LAW-001/002/003 雏形) + 1.1.FAILED_LAWS.md (FAILED-001 雏形) + 2.HYPOTHESES.md (HYP-001~007 雏形) |
| 2026-07-23.md | 当日认知 | 部分归档到 LAWS-002 + HYPOTHESES |
| 2026-07-28.md | 当日认知 | 部分归档到 5.BACKTEST_INDEX.md |
| 2026-07-29.md | 当日认知 | 精简待归档（短文件，19 行）|
| 2026-07-30.md | 当日认知 | 部分归档到 HYPOTHESES (HYP-013~018) |
| 2026-07-31.md | Cross-Market Validation | 关键结论已蒸馏到 HYPOTHESES (HYP-002 v4) + 4.BROKER_OBSERVATION.md |
| 2026-07-31-oligarch-rotation-4th-pushback.md | 寡头轮换 4th pushback | 关键机制已蒸馏到 HYPOTHESES (HYP-027 v3) |
| 2026-07-31-us-debt-250-year-historical-analysis.md | 化债 250 年历史 | 关键洞察已蒸馏到 HYPOTHESES (HYP-028 v3) + 3.US_FRAMEWORK.md §1.3 |
| 2026-07-31-us-debt-resolution-theory-5-agent-review.md | 化债 5 agent 评审 | 关键洞察已蒸馏到 HYPOTHESES (HYP-027~028 v3) |
| 2026-07-31-us-debt-resolution-theory-revised.md | 化债理论修正 | 同上 |
| 2026-08-02.md / round2~round4 | Round 2-4 资产拉爆机制 | 关键洞察已蒸馏到 HYPOTHESES (HYP-027/028 v3) + HYP-029 |
| 2026-08-03.md | Round 6-9 + 券商诊断 + regime 分析 | 当日认知已蒸馏到 HYPOTHESES (HYP-029 v2) + 4.BROKER_OBSERVATION.md + BROKER 诊断报告 + 6.CONFLICTS.md (CONFLICT-LOGIC-009) |
| 2026-08-04.md | BT-006 + 机制解释 + 保险研究 + **用户裁决 + USER_RULE 候选 LAW-005 + memory 冗余 log 清理** | 当日认知已蒸馏到 5.BACKTEST_INDEX.md (BT-006) + 2.HYPOTHESES.md (HYP-029 v2 触发状态) + 6.CONFLICTS.md (CONFLICT-LOGIC-009 RESOLVED) + US_FRAMEWORK/BROKER/CHINA_FRAMEWORK/HYP-027-V3-DETAILS/POSITION_SIZING 清理 |

**保留原因**：raw-log 是"原始事件证据"，保留以备：(1) 5-Why Adversarial 引用 ② 框架重大变更回溯 ③ 用户决策历史审计。
**清理策略**：永不删除；如体积过大，单文件 > 100KB 时考虑归档到 .opencode/memory/personal-system/raw-log/archive/ 子目录（**当前未触发**，所有文件 < 50KB）。

