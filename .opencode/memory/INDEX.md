# INDEX — 集中化记忆系统全局索引

> 主入口。任何 subagent 在做投资判断前必读本文件。
> **⚠️ 协议修订（2026-08-25 用户清理令）:** 原 memory-protocol 的"raw-log 永不删除 / 归档保留指针"条款废止——无效、低可能性、过时、log、版本记录、归档内容一律物理删除；全部历史快照由 git 历史兜底可溯。

---

## 目录结构

```
.opencode/memory/
└── personal-system/
    ├── 法则层
    │   └── 1.LAWS.md                        # 已验证法则（含 5-Why Challenge，失效法则已内化于 LAW-003）
    ├── 假设层
    │   ├── 2.HYPOTHESES.md                  # 全部活跃假设（含各 HYP 上修/下修信号）
    │   └── 2.2.HYP-027-V3-DETAILS.md        # 快剧本完整证据库+配置矩阵
    ├── 决策链
    │   └── decision-journal/                # 概率预测登记 + 季度 Brier 评分（勿删）
    ├── 框架层
    │   ├── 3.US_FRAMEWORK.md                # 美股独立框架 v2.1（含监控指标）
    │   ├── 3.1.CHINA_FRAMEWORK.md           # A股独立框架 v1.4
    │   └── 3.2.未来5年的预判2026～2030.md    # 5年全景预判（框架一致性 + 7 预判）
    ├── 观察层
    │   ├── 4.BROKER_OBSERVATION.md          # 券商板块指标体系 v1.4
    │   ├── 4.1.NATIONAL_TEAM_OBSERVATION.md # 国家队资金监测
    │   └── 4.2.AI_BUBBLE_TRACKING.md        # AI 泡沫跟踪 v5.1
    ├── 操作层
    │   ├── 5.BACKTEST_INDEX.md              # 回测台账 BT-001~018
    │   ├── 6.CONFLICTS.md                   # 开放/已解决冲突登记
    │   ├── 7.SELL_LADDER.md                 # 卖出梯子 v2.x
    │   ├── 7.1.POSITION_SIZING.md           # 仓位管理
    │   └── 8.BUY_LADDER.md                  # 买入梯子 v3.1
    ├── 可执行能力
    │   ├── sell-ladder/ · buy-ladder/       # 判定引擎 + runs 历史
    │   ├── research/                        # 概率客观化算法 alg1-4 + 化债模型 py
    │   └── backtests/                       # BT-001~018 完整回测资产
    ├── 现行报告 reports/（**当前 16 个文件：15 .md + 1 目录**）
    │   ├── **AI 巨头估值与债务研究线**
    │   │   ├── ai_valuation_thresholds.md                # 【主】AI 巨头估值+泡沫阈值（五方法双情景，2026-09-07 最新）
    │   │   ├── tech_giants_corporate_debt.md             # AI 巨头企业债全面画像（债务姊妹篇）
    │   │   ├── ai-bubble-bank-indicators-consolidated-2026-08-19.md  # 投行 AI 泡沫指标
    │   │   ├── ai-bubble-inflation-stages-deep-2026-08-18.md         # 危机×通胀×大类资产回报数据集
    │   │   ├── nvda-q2fy27-deep-dive-2026-09-07.md                    # NVDA Q2 FY27 深度
    │   │   ├── googl-q2-2026-deep-dive-2026-09-07.md                  # GOOGL Q2 深度（含非经营重估污染）
    │   │   ├── multi-hyperscaler-ai-loop-network-2026-09-07.md        # 多巨头 AI 内循环网络
    │   │   └── ai-network/                                            # AI 网络配套资产
    │   ├── **SPCX (SpaceX) 主报告**（2026-09-01 五维合并版）
    │   │   └── SPCX-master-2026-09-01.md                 # 评级/目标价/红线/催化剂（Q2财报+估值+技术+竞争合并）
    │   ├── global-relay-debt-monetization-scenario-map-v3-2026-08-25.md  # 终版情景图（HYP-032 配套）
    │   ├── fed-warsh-debt-monetization-hyp-reevaluation-2026-09-10.md   # Warsh hawkish-hold 重估（HYP-020/026）
    │   ├── china-silicon-wafer-landscape-2026-08-25.md               # 中国半导体硅片厂商竞争格局
    │   ├── 稳定币全景研究_发布版v3-fixed.md 2026-08-26                 # 稳定币政策/储备/赛道全图
    │   ├── aihf-masters-crisis-backtest-2026-09-14.md                # 【新】8 大师危机全周期回测（真实数据；REINFORCEMENT）
    │   └── **timing-dashboard-us-cn-2026-09-11.md**                   # 【新】择时总表（美 WIF v5.9 + 中 WIF v2.7）；含 2 处官方数据缺陷
    ├── 数据层 data/  【2026-09-15 新建 · **只存指针，不复制数值**】
    │   ├── **artifacts_manifest.json**   # 21 项产物：绝对路径 + sha256 + 用途 + 产出脚本
    │   └── README.md                     # 指针约定说明
    │       └─ 数值住在 example/wif-framework/data/ 与 example/wif-ashare/data/
    │          漂移检查：python3 .opencode/scripts/build_artifacts_manifest.py --check
    └── theses/
```

**已删除（清理记录）：**
- **2026-08-25 清理令:** `raw-log/`（17 文件）、`distillation-log/`、`skill-changelog/`、`market-regime/`、`2.1.HYP-UNUSED.md`（归档库）、假设库内 13 个失效/归档/Tier3 低价值条目（HYP-001/003/004/005/007/009/010/012/013/018/019/022/023/031）、reports/ 内 11 个过程稿与被取代版本。→ git 历史可恢复。
- **2026-08-27 清理令:** `/out/` 8 个文件全部处理——`china-silicon-wafer-landscape-20260825.md` 入库至 reports/（唯一非冗余），其余 7 个（bank-indicator-registry-20260824.md / bank-views-synthesis-20260824.md / institutional-methodology-review-20260824.md / methodology-deep-dive-20260824.md / methodology-review-final-20260824.md / peer-review-round-5-2026-08-19.md / crisis-playbook/scripts/chain_consistency_check.py）= 已被 reports/ 内 MCP-backed 版本取代的过程稿；/out/ 目录清空。→ git 历史可恢复。
- **2026-08-30 独立性清理令:** 删除 3 个冗余文档——`1.1.FAILED_LAWS.md`（FAILED-001 已被 LAW-003 完整吸收）、`2.3.HYP_UPDATE_RULES.md`（Brier 规则已内化于 decision-journal/README.md，量化信号已分散到 2.HYPOTHESES.md 各 HYP）、`regime-watch.md`（监控指标已分散到 3.US_FRAMEWORK §1.3 + 4.2.AI_BUBBLE_TRACKING，零引用）。新增 `3.2.未来5年的预判2026～2030.md`。→ git 历史可恢复。
- **2026-09-07 报告合并清理令:** `reports/ai_bubble_analysis.md`（2026-09-06 版，数据已被多轮审查修正）→ 被 `reports/ai_valuation_thresholds.md`（2026-09-07 五方法版）取代。独有价值内容（§5 泡沫触发链、煤矿金丝雀、破裂情景）已并入主报告新 §8；旧文件物理删除（备份 /tmp/report-backup-20260907/）。`ai-bubble-inflation-stages-deep` 头部关联声明更新（原 companion 已于 08-25 删，现自足）。INDEX reports 树同步为 11 个有效文件。→ git 历史可恢复。
- **2026-09-07 SPCX 五维合并令:** `reports/SPCX-*` 五份（Q2财报/股价/估值压力/技术/竞争叙事，共 2,573 行）→ 合并压缩为 **`SPCX-master-2026-09-01.md`**（1 份主报告：评级 1-star AVOID、FV $50/65/90、红线/催化剂/监控指标统一）。五份原始文件物理删除（备份 /tmp/report-backup-20260907/）。INDEX reports 树更新为 8 个有效文件。→ git 历史可恢复。

---

## 当前活跃内容

**最后更新:** **2026-09-15（数据层定型为「**只存指针，不复制数值**」—— `data/artifacts_manifest.json` 21 项（路径+sha256），配套 `.opencode/scripts/build_artifacts_manifest.py --check` 做漂移检测；**已实测**：故意改 1 字节 → DRIFT 退出码 1；重跑 5 个产出脚本 → 零漂移。美 WIF v5.9 / 中 WIF v2.7 读数已写入 3.US/3.1/4.2/2.HYP-011；发现 2 处官方数据缺陷）**

> 前次：2026-09-14（ai-hedge-fund 8 大师危机全周期回测 — 真实数据；新增 `reports/aihf-masters-crisis-backtest-2026-09-14.md`；reports 树补齐至 15 项；核心为 REINFORCEMENT 不入 LAW/HYP，新增待验证项"capex/收入比 35% 阈值缺回测"→ 建议 BT-020）**

> 前次：2026-09-14（视频核查蒸馏 — 新增 HYP-033「G7 长端国债买家坍缩 → 期限溢价新常态 + 黄金重估」+ CONFLICT-LOGIC-011「剧烈通胀 vs 驯服通胀」；活跃假设 16 → 17）

| 项目 | 状态 |
|------|------|
| **活跃法则** | 3 条（LAW-001~003，全含 5-Why Challenge；失效法则 FAILED-001 已内化于 LAW-003） |
| **活跃假设** | **17 个**：Tier 1 ⭐ = HYP-006/015/016/021/026/029 + **HYP-032（G2双人舞×接力式化债×驯服通胀，细化层）** + **HYP-033（G7 长端买家坍缩 → 期限溢价新常态 + 黄金重估，结构层父框架）**；Tier 2 = HYP-002/011/014/017/020/024/028/030；Tier 3 = HYP-027（γ父框架）。另 HYP-025 元评估 |
| **三剧本概率账本（v3.2, 2026-09-10 Bridgewater 视角修正）** | **α=HYP-029 接力化债 51%**（原 52.5% ↓）/ **β=HYP-028 慢速金融抑制 35%**（不上调）/ **γ=HYP-027 快剧本 14%**（原 12.5% 微↑，Warsh hawkish-hold 而非立即加息 → 阶段 1 启动条件保留）；δ（AI 无痛路径）3-5% 为制度性反方 |
| **HYP-011 危机分** | **1 → 2-3 分（边缘）**：S7 US30Y 5.24% 持续触发（+1 分）；**S8 Brent $101.21 9/9 首次突破 $100，即将 +1 分** → 9/23 复审节点；逼近 L2 减仓 30% 预备区 |
| **HYP-006 触发距离** | META Capex/Rev 35.1% **🔴 已触发**（减仓 AI 基础设施/云至 50%）；MSFT 34.9% 临界（0.1pp）；NVDA Q/Q +17.9% 健康（+7.9pp 距 <10%）|
| **决策链** | decision-journal 登记预测挂 HYP 编号，季度 Brier 评分运行中（更新规则已并入 2.HYPOTHESES.md） |
| **国家队 regime** | 🔴 净卖出（持续监控） |
| **框架版本** | CHINA v1.4（CDS 双层阈值）· US v2.1（双剧本联动+AI附录）· **五年预判 v2（新增 3.2）** |
| **回测总数** | 18（BT-001~018，最新 BT-018 = 信号持续期持有口径下信心缩放 vs 均匀 50% 验证） |
| **新增触发器（T-NEW）** | T-NEW-1 NVDA AR/Q Revenue / T-NEW-2 NVDA Long-term debt / T-NEW-3 NVDA Equity securities / T-NEW-4 GOOGL CapEx/OCF / T-NEW-5 GOOGL Equity Securities / T-NEW-6 GOOGL Q2 净利润公允价值占比 / T-NEW-7 AI 内/外循环 GMV 比 / T-NEW-8 hyperscaler CapEx/AI ARR — **T-NEW-4/5/6/7 已硬触发** |
| **OPEN 冲突数** | 9 个（含 **CONFLICT-USER-WARSH 部分 RESOLVED** —— 我第一轮误读"鹰派 hold = 鹰派 hike"，Bridgewater 视角纠正后：Warsh 是 data-dependent hawkish-hold，9/15-16 FOMC 维持当前 60% / 加息 25bp 30-35%；9/15-16 强制复审。**+ CONFLICT-LOGIC-011 NEW** —— HYP-033「通胀必然可怕」vs HYP-032「驯服的通胀」= 时间尺度混淆，OPEN） |
| **HYP 文档压缩** | **2026-09-10 执行：2.HYPOTHESES.md 1258 → 570 行（-54.7%）** —— 采纳用户裁定"不能只增加不减少"，删除 v1-v3 历史版本 / 重复证据库 / Round 3 独立子标题；目标 <1000 行已达成 |

### 🔴 强制复审节点（2026-09-10 更新）

```
[关键事件] 09-15/16 FOMC ← 关键（维持当前 60% / 加息 25bp 30-35%）
[关键事件] 09-23 Brent 是否持续 $100 复审（HYP-011 S8 触发节点）
[继续] 09-24 习特会（HYP-032 G2 层强制复审）
[继续] 10-15 Q3 财报披露窗口前 2 周（仓位审计）
[继续] 10-31 AMZN/MSFT/GOOGL Q3（Capex/Rev 突破 + AI 内循环首次公开）
[继续] 11-10 休战到期 + 中期选举 + 再融资声明
[继续] 11 月底 NVDA Q3 FY27（Q/Q 走向预测 +12-13%）
[继续] 12 月 FOMC（2026 最后议息）
[继续] 2027 春夏 $41.1T 上限
[继续] 2027H2-2028 衰退∩X-date = 主触发窗
```

---

## 关键机制备忘（2026-08-25 蒸馏结论 + 2026-09-10 补充）

1. **化债终局机制已改写**: 解决债务的不是剧烈通胀（1970s 实验：CPI 13.5%、债务/GDP 不动），而是**驯服的通胀+金融抑制**（Reinhart-Sbrancia -2~3pp GDP/年 × 十年）；Warsh 重谈 1951 协定 = 制度种子。**2026-09-10 补充 + Bridgewater 修正**：Warsh 8/28 Jackson Hole 是 **data-dependent hawkish-hold**（条件性"if 内生通胀不回落 then 行动"）+ Waller 支持维持当前水平；市场定价 ~2 次加息（累计 50bp，Q4 2026-2027Q1 分布）；HYP-020/026 论据获双向支撑 → 化债 Stage 4（自损贬值）更不可行。
2. **中美 = 双人舞非合唱**: 交易协调✅ / 宏观默契⚠️ / 化债同盟❌；中国跟随宽松的动机是汇率自卫（防广场协定式急升），形式为滞后接力。**2026-09-10 补充**：中国 8月 CPI +0.8% YoY 距反向操作 2% 触发线差 1.2pp；Brent $101.21 + 10Y Breakeven 2.37% ↑ → 通胀传导链条重新激活。
3. **γ 新增前置触发器**: 基差交易四警报（repo利差走阔 / 期货保证金上调 / dealer认购>15% / MOVE>150）——任二出现即把"危机时点"从 2027H2-2028 压缩至 6 个月内。**2026-09-10 v3.2 修正**：γ 概率 12.5% → **14%**（Warsh hawkish-hold 而非立即加息 → 阶段 1 启动条件保留，γ 不再下调），3-6 月窗口收窄（Brent + 30Y 拍卖 + AI 内循环 三重累积）。
4. **主事件日历**: 9·24习特会 → 11·10休战到期 → 12月FOMC → 2027春夏 $41.1T上限 → **2027H2-2028 衰退∩X-date = 主触发窗**。**2026-09-10 补充**：9/15-16 FOMC（维持 60% / 加息 30-35%）→ 9/23 Brent $100 持续复审 → 9/24 习特会 已升级为强制复审锚点。
5. **2026 习特会管理台湾**（8-30 补充）: 习特会模糊确认"一个中国" + 维持现状 → 台湾灰色地带危机概率 **40-50% → 20-30%**（推迟到 2028-2030 远期）；**2028 准战争主触发点从台湾转移到伊朗/霍尔木兹**（35-45%）；日本是台湾冲突的"自动第二玩家"（被拖入概率 60-70%），但中日双边热战仅 5-10%。**2026-09-10 补充**：Brent $101.21 主要驱动是 7/7 撤销 General License X（伊朗制裁）→ "制裁驱动"vs"货币驱动"商品长牛 = **可逆性差异** = HYP-029 证据质量下调（9/6 raw-log 已记录）。
6. **🔴 AI 泡沫现状（2026-09-10 新增）**: NVDA Q/Q +17.9% 健康（Q3 指引 $108B 维持 + FY28 ~70% 增长）；**MSFT Capex/Rev 34.9% 临界（差 0.1pp）**；**META 35.1% 已超警示线 → HYP-006 减仓 AI 基础设施/云至 50% 条件性启动**；GOOGL 单季 37.5% + CapEx/OCF 95% + Q2 净利润 88% 来自公允价值重估 → T-NEW-4/5/6 触发；AI 内/外循环 GMV 8-12x → T-NEW-7 触发。位置：阶段 1.5 → 阶段 2 过渡区间（3-6 个月缓冲期）。
7. **🆕 长端国债需求结构（2026-09-14 新增 — HYP-033）**: 全球长端利率抬升的**结构原因** = DB 养老金（久期匹配型、监管驱动型买家）系统性撤退 → 价格敏感型买家（DC/外资/对冲基金）接盘 + 创纪录供给 → **期限溢价新常态**。德国债务/GDP 仅 63.5% 却长端创 15 年新高 = 超越"债务水平"的结构证据。**⚠️ 视频原文 3 处口径错误已备案，不得重复引用**（DB 80%→14% 口径混淆 / 美国 12 个月滚动改写成"发达到 2027" / 企业杠杆贷款到期墙塞进主权债）。**⚠️ 与 HYP-032「驯服通胀」张力 → CONFLICT-LOGIC-011（OPEN）**。

---

## 检索指南

| 想找什么 | 怎么找 |
|---------|--------|
| 我的法则 | `grep "关键词" personal-system/1.LAWS.md` |
| 某假设是否活跃/概率 | `grep "HYP-XXX" personal-system/2.HYPOTHESES.md` |
| 概率怎么更新 | `grep "HYP-XXX" personal-system/2.HYPOTHESES.md -A 20`（上修/下修信号已并入各 HYP） |
| 5 年全景预判 | `personal-system/3.2.未来5年的预判2026～2030.md` |
| 我预测了什么/评分 | `ls -t personal-system/decision-journal/` |
| 有哪些冲突未解决 | `grep "OPEN" personal-system/6.CONFLICTS.md` |
| 某回测详情 | `grep "BT-XXX" personal-system/5.BACKTEST_INDEX.md -A 10` |
| 化债终局推演全文 | `personal-system/reports/global-relay-debt-monetization-scenario-map-v3-2026-08-25.md` |

---

## 已知遗留事项

- 6.CONFLICTS.md / 5.BACKTEST_INDEX.md 中部分段落引用已删除的 raw-log 路径——仅路径悬空，结论本身完好，下次蒸馏时顺带修复。
- HYP-025 元评估（化债理论可信度 40-50/100）写于 HYP-032 之前，下次复审时应并入重估。
- **3.2 五年预判待补**: (1) "中日关系"作为预判 3 的独立事件行（中日军备竞赛 30% / 日本被拖入台湾 20%）；(2) "日本核武装"作为尾部风险（5% 概率，2030+）。当前中日分析已在 8-30 对话中完成，待合并入 3.2。
