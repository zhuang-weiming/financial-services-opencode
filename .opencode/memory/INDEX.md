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
    │   ├── 5.BACKTEST_INDEX.md              # 回测台账 BT-001~016
    │   ├── 6.CONFLICTS.md                   # 开放/已解决冲突登记
    │   ├── 7.SELL_LADDER.md                 # 卖出梯子 v2.x
    │   ├── 7.1.POSITION_SIZING.md           # 仓位管理
    │   └── 8.BUY_LADDER.md                  # 买入梯子 v3.1
    ├── 可执行能力
    │   ├── sell-ladder/ · buy-ladder/       # 判定引擎 + runs 历史
    │   ├── research/                        # 概率客观化算法 alg1-4 + 化债模型 py
    │   └── backtests/                       # BT-001~016 完整回测资产
    ├── 现行报告 reports/（**5 个有效版本**）
    │   ├── global-relay-debt-monetization-scenario-map-v3-2026-08-25.md  # 终版情景图（HYP-032 配套）
    │   ├── ai-bubble-inflation-stages-deep-2026-08-18.md               # AI泡沫×通胀阶段×大类资产
    │   ├── ai-bubble-bank-indicators-consolidated-2026-08-19.md        # 银行指标合并
    │   ├── china-silicon-wafer-landscape-2026-08-25.md               # 中国半导体硅片厂商竞争格局
    │   └── 稳定币全景研究_发布版v3-fixed.md 2026-08-26                 # 稳定币政策/储备/赛道全图
    └── theses/ · data/
```

**已删除（清理记录）：**
- **2026-08-25 清理令:** `raw-log/`（17 文件）、`distillation-log/`、`skill-changelog/`、`market-regime/`、`2.1.HYP-UNUSED.md`（归档库）、假设库内 13 个失效/归档/Tier3 低价值条目（HYP-001/003/004/005/007/009/010/012/013/018/019/022/023/031）、reports/ 内 11 个过程稿与被取代版本。→ git 历史可恢复。
- **2026-08-27 清理令:** `/out/` 8 个文件全部处理——`china-silicon-wafer-landscape-20260825.md` 入库至 reports/（唯一非冗余），其余 7 个（bank-indicator-registry-20260824.md / bank-views-synthesis-20260824.md / institutional-methodology-review-20260824.md / methodology-deep-dive-20260824.md / methodology-review-final-20260824.md / peer-review-round-5-2026-08-19.md / crisis-playbook/scripts/chain_consistency_check.py）= 已被 reports/ 内 MCP-backed 版本取代的过程稿；/out/ 目录清空。→ git 历史可恢复。
- **2026-08-30 独立性清理令:** 删除 3 个冗余文档——`1.1.FAILED_LAWS.md`（FAILED-001 已被 LAW-003 完整吸收）、`2.3.HYP_UPDATE_RULES.md`（Brier 规则已内化于 decision-journal/README.md，量化信号已分散到 2.HYPOTHESES.md 各 HYP）、`regime-watch.md`（监控指标已分散到 3.US_FRAMEWORK §1.3 + 4.2.AI_BUBBLE_TRACKING，零引用）。新增 `3.2.未来5年的预判2026～2030.md`。→ git 历史可恢复。

---

## 当前活跃内容

**最后更新:** **2026-08-30（新增 3.2 五年预判 + 删除 3 个冗余文档 + 波动率放大修正）**

| 项目 | 状态 |
|------|------|
| **活跃法则** | 3 条（LAW-001~003，全含 5-Why Challenge；失效法则 FAILED-001 已内化于 LAW-003） |
| **活跃假设** | **16 个**：Tier 1 ⭐ = HYP-006/015/016/021/026/029 + **HYP-032（G2双人舞×接力式化债×驯服通胀，细化层，概率继承三剧本账本）**；Tier 2 = HYP-002/011/014/017/020/024/028/030；Tier 3 = HYP-027（γ父框架）。另 HYP-025 元评估 |
| **三剧本概率账本** | α=HYP-029 接力化债 **52.5%** / β=HYP-028 慢速金融抑制 **35%** / γ=HYP-027 快剧本 **12.5%**（基差四警报任二响起 → 上修 25%+）；δ（AI 无痛路径）3-5% 为制度性反方 |
| **决策链** | decision-journal 登记预测挂 HYP 编号，季度 Brier 评分运行中（更新规则已并入 2.HYPOTHESES.md） |
| **国家队 regime** | 🔴 净卖出（持续监控） |
| **框架版本** | CHINA v1.4（CDS 双层阈值）· US v2.1（双剧本联动+AI附录）· **五年预判 v2（新增 3.2）** |
| **回测总数** | 16（BT-001~016，最新 BT-015/016 = BUY_LADDER v3.1 定案） |

---

## 关键机制备忘（2026-08-25 蒸馏结论）

1. **化债终局机制已改写**: 解决债务的不是剧烈通胀（1970s 实验：CPI 13.5%、债务/GDP 不动），而是**驯服的通胀+金融抑制**（Reinhart-Sbrancia -2~3pp GDP/年 × 十年）；Warsh 重谈 1951 协定 = 制度种子。
2. **中美 = 双人舞非合唱**: 交易协调✅ / 宏观默契⚠️ / 化债同盟❌；中国跟随宽松的动机是汇率自卫（防广场协定式急升），形式为滞后接力。
3. **γ 新增前置触发器**: 基差交易四警报（repo利差走阔 / 期货保证金上调 / dealer认购>15% / MOVE>150）——任二出现即把"危机时点"从 2027H2-2028 压缩至 6 个月内。
4. **主事件日历**: 9·24习特会 → 11·10休战到期 → 12月FOMC → 2027春夏 $41.1T上限 → **2027H2-2028 衰退∩X-date = 主触发窗**。
5. **2026 习特会管理台湾**（8-30 补充）: 习特会模糊确认"一个中国" + 维持现状 → 台湾灰色地带危机概率 **40-50% → 20-30%**（推迟到 2028-2030 远期）；**2028 准战争主触发点从台湾转移到伊朗/霍尔木兹**（35-45%）；日本是台湾冲突的"自动第二玩家"（被拖入概率 60-70%），但中日双边热战仅 5-10%。

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
