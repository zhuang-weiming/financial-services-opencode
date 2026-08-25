# INDEX — 集中化记忆系统全局索引

> 主入口。任何 subagent 在做投资判断前必读本文件。
> **⚠️ 协议修订（2026-08-25 用户清理令）:** 原 memory-protocol 的"raw-log 永不删除 / 归档保留指针"条款废止——无效、低可能性、过时、log、版本记录、归档内容一律物理删除；全部历史快照由 git 历史兜底可溯。

---

## 目录结构

```
.opencode/memory/
└── personal-system/
    ├── 法则层
    │   ├── 1.LAWS.md                        # 已验证法则（含 5-Why Challenge）
    ├── 假设层
    │   ├── 2.HYPOTHESES.md                  # 全部活跃假设（16 活跃 + 1 元评估）
    │   ├── 2.2.HYP-027-V3-DETAILS.md        # 快剧本完整证据库+配置矩阵
    │   └── 2.3.HYP_UPDATE_RULES.md          # 概率更新规则（Brier 校准挂钩）
    ├── 决策链
    │   └── decision-journal/                # 概率预测登记 + 季度 Brier 评分（勿删）
    ├── 框架层
    │   ├── 3.US_FRAMEWORK.md                # 美股独立框架 v2.1
    │   └── 3.1.CHINA_FRAMEWORK.md           # A股独立框架 v1.4
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
    ├── 现行报告 reports/（仅存 3 个有效版本）
    │   ├── global-relay-debt-monetization-scenario-map-v3-2026-08-25.md  ⭐ 终版情景图（HYP-032 配套）
    │   ├── ai-bubble-inflation-stages-deep-2026-08-18.md               # AI泡沫×通胀阶段×大类资产
    │   └── ai-bubble-bank-indicators-consolidated-2026-08-19.md        # 银行指标合并
    ├── theses/ · data/ · regime-watch.md
```

**已删除（2026-08-25 清理令）:** `raw-log/`（17 文件）、`distillation-log/`、`skill-changelog/`、`market-regime/`、`2.1.HYP-UNUSED.md`（归档库）、假设库内 13 个失效/归档/Tier3 低价值条目（HYP-001/003/004/005/007/009/010/012/013/018/019/022/023/031）、reports/ 内 11 个过程稿与被取代版本。→ git 历史可恢复。

---

## 当前活跃内容

**最后更新:** 2026-08-25 23:10（结构大清理 + HYP-032 入库）

| 项目 | 状态 |
|------|------|
| **活跃法则** | 3 条（LAW-001~003，全含 5-Why Challenge） |
| **活跃假设** | **16 个**：Tier 1 ⭐ = HYP-006/015/016/021/026/029 + **HYP-032（G2双人舞×接力式化债×驯服通胀，细化层，概率继承三剧本账本）**；Tier 2 = HYP-002/011/014/017/020/024/028/030；Tier 3 = HYP-027（γ父框架）。另 HYP-025 元评估 |
| **三剧本概率账本** | α=HYP-029 接力化债 **52.5%** / β=HYP-028 慢速金融抑制 **35%** / γ=HYP-027 快剧本 **12.5%**（基差四警报任二响起 → 上修 25%+）；δ（AI 无痛路径）3-5% 为制度性反方 |
| **决策链** | decision-journal 登记预测挂 HYP 编号，季度 Brier 评分运行中 |
| **国家队 regime** | 🔴 净卖出（持续监控） |
| **框架版本** | CHINA v1.4（CDS 双层阈值）· US v2.1（双剧本联动+AI附录） |
| **回测总数** | 16（BT-001~016，最新 BT-015/016 = BUY_LADDER v3.1 定案） |

---

## 关键机制备忘（2026-08-25 蒸馏结论）

1. **化债终局机制已改写**: 解决债务的不是剧烈通胀（1970s 实验：CPI 13.5%、债务/GDP 不动），而是**驯服的通胀+金融抑制**（Reinhart-Sbrancia -2~3pp GDP/年 × 十年）；Warsh 重谈 1951 协定 = 制度种子。
2. **中美 = 双人舞非合唱**: 交易协调✅ / 宏观默契⚠️ / 化债同盟❌；中国跟随宽松的动机是汇率自卫（防广场协定式急升），形式为滞后接力。
3. **γ 新增前置触发器**: 基差交易四警报（repo利差走阔 / 期货保证金上调 / dealer认购>15% / MOVE>150）——任二出现即把"危机时点"从 2027H2-2028 压缩至 6 个月内。
4. **主事件日历**: 9·24习特会 → 11·10休战到期 → 12月FOMC → 2027春夏 $41.1T上限 → **2027H2-2028 衰退∩X-date = 主触发窗**。

---

## 检索指南

| 想找什么 | 怎么找 |
|---------|--------|
| 我的法则 | `grep "关键词" personal-system/1.LAWS.md` |
| 某假设是否活跃/概率 | `grep "HYP-XXX" personal-system/2.HYPOTHESES.md` |
| 概率怎么更新 | `grep "HYP-XXX" personal-system/2.3.HYP_UPDATE_RULES.md -A 20` |
| 我预测了什么/评分 | `ls -t personal-system/decision-journal/` |
| 有哪些冲突未解决 | `grep "OPEN" personal-system/6.CONFLICTS.md` |
| 某回测详情 | `grep "BT-XXX" personal-system/5.BACKTEST_INDEX.md -A 10` |
| 化债终局推演全文 | `personal-system/reports/global-relay-debt-monetization-scenario-map-v3-2026-08-25.md` |

---

## 已知遗留事项

- 6.CONFLICTS.md / 5.BACKTEST_INDEX.md 中部分段落引用已删除的 raw-log 路径——仅路径悬空，结论本身完好，下次蒸馏时顺带修复。
- HYP-025 元评估（化债理论可信度 40-50/100）写于 HYP-032 之前，下次复审时应并入重估。
