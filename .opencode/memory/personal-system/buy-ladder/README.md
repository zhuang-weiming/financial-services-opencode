# BUY_LADDER — 16 Skill 信号驱动的买入框架 (v3.0)

> **状态:** v3.0 实施完成 (2026-08-11, 对齐 LazyBear + Vibe-Trading canonical), BT-010 回测已首跑
> **位置:** `.opencode/memory/personal-system/buy-ladder/` (永久能力)
> **协议层:** `.opencode/skills/buy-ladder/SKILL.md` (subagent 加载入口)
> **核心:** 用 sell-ladder 16 信号矩阵 + 6 个 transition 函数 + Layer 0 regime 闸门 + Layer 1 5 道筛子 + 4 阶段 + 3 模式实现"不预测底部 + 让趋势自己启动"的买入哲学
> **有效性:** BT-010 已首跑 (C2 V21 OB NAV 13.46, 待用户批准最终结论)

---

## 目录结构

```
.opencode/memory/personal-system/buy-ladder/
├── README.md                       ← 本文件 (使用说明)
├── buy_ladder.py                  ← 统一入口脚本 (993 行)
├── batch_v11_holdings.py          ← 18 持仓批量验证
├── combo_layer.py                 ← buy + sell 联合调度 (Phase 5)
├── runs/                           ← 历史跑过的结果
│   └── 2026-08-11/
│       ├── buy_ladder_<ticker>_2026-08-11.json
│       └── v11_holdings_2026-08-11.json
└── (待 P1) BT-010 回测脚本
```

---

## 一键运行

```bash
# 单标的判定
python3 .opencode/memory/personal-system/buy-ladder/buy_ladder.py --ticker 300725

# 已持仓标的 (启用 sell-buyer 闭环模式 B)
python3 .opencode/memory/personal-system/buy-ladder/buy_ladder.py \
    --ticker 300725 --cost 36.62 --shares 10000 --held

# 强制解锁 Layer 0 (调试用, 不推荐)
python3 .opencode/memory/personal-system/buy-ladder/buy_ladder.py \
    --ticker 300725 --force-regime-unlock

# 18 持仓批量验证 (默认 regime 锁定下, 全部应进入禁入区)
python3 .opencode/memory/personal-system/buy-ladder/batch_v11_holdings.py

# 单标的 buy + sell 联合判定
python3 .opencode/memory/personal-system/buy-ladder/combo_layer.py \
    --ticker 300725 --cost 36.62 --shares 10000
```

---

## 输出

每次运行输出:
- Layer 0: regime 闸门 3 条件 (沪深300 MA60 / WIF MCI / 国家队)
- Layer 1: 5 道筛子 (估值/基本面/ST/市值/板块景气)
- Layer 2: 16 复用信号 + 6 个 transition (含 calc_wt1_sweet_zone_transition / calc_trend_launch_transition / calc_volume_price_resonance / calc_structure_complete)
- 5 大买入确认 + 5 大买入否决
- 4 阶段 (击球/观察/回调/禁入) + 3 模式 (A 突破 / B 回调 / C 禁入)

**双保存:**
- 永久: `runs/YYYY-MM-DD/buy_ladder_<ticker>_<date>.json` (历史记录)
- 临时: (本工具暂用永久保存, 不另存临时副本)

---

## 16 信号矩阵 (复用 sell-ladder) + 6 新增

### A. 16 sell-ladder 复用 (零修改)

| Skill | 复用方式 | 解读方向反转 |
|:---|:---|:---|
| alpha-engine-v21 | 状态量 (WT1 zone) | signal=+1 = 看多 |
| candlestick | 形态评分 | 反弹形态 score>0 |
| chanlun | 三买候选 | signal=+1 |
| ml_strategy | 5d 动量 | signal=+1 if ret>0.02 |
| technical-basic | EMA/ADX | ADX>20 + EMA12>EMA26 |
| ichimoku | 云层 | 云上 + TK 金叉 |
| smc | BOS/ChoCH | bullish BOS |
| alpha-zoo | 20d 动量 | ret_20d > +10% |
| factor-research | f2 IC | f2 IC > 0.5 |
| multi-factor | 综合分 | composite > 0.05 |
| volatility | HV 百分位 | pct > 80 (强趋势) |
| harmonic | XABCD | 形态匹配 |
| pair-trading | 配对 Z-score | Z<-2 (超跌) |
| turnover_anomaly | 量比+位置 | 底部吸筹 (+1) |
| sector_relative | 个股 vs 板块 | 跑赢 (+1) |
| ad_line | 累积派发线 | 底部背离 (+1) |

### B. 6 个新增 (transition 函数 + 2 占位符)

| 函数 | 用途 | 实现状态 |
|:---|:---|:---:|
| `calc_wt1_sweet_zone_transition` | WT1 进入甜区 [20, 40] | ✅ |
| `calc_trend_launch_transition` | ADX/EMA/ichimoku 三重 transition | ✅ |
| `calc_volume_price_resonance` | 量价共振 (复用 turnover + ad_line + 量比) | ✅ |
| `calc_structure_complete` | 结构完成 (复用 chanlun + smc + candlestick) | ✅ |
| `calc_valuation_percentile` | PE/PB 历史分位 | ⏸ 占位符 (待 tushare) |
| `calc_fundamental_inflection` | ROE/营收增速拐点 | ⏸ 占位符 (待 tushare) |

---

## Layer 0 regime 闸门 (3/3 必须通过)

| # | 条件 | 数据源 | 当前 (2026-08-11) | 解锁? |
|:---|:---|:---|:---:|:---:|
| 1 | 沪深300 MA60 > -7% | Sina 510300 或 CHINA_FRAMEWORK 兜底 | -2.66% | ✅ |
| 2 | WIF MCI > 0.5 | wif-ashare-advisory 或 CHINA_FRAMEWORK 兜底 | 0.386 | 🔒 |
| 3 | 国家队净买入 (> -3% 月环比) | national_team_obs | -89% vs 峰值 | 🔒 |

**当前综合：2/3 锁定 → buy-ladder 默认关闭** ✅ 正确状态

---

## Layer 1 5 道筛子 (任一不通过 → 不进入观察池)

| # | 筛子 | 阈值 | 实现状态 |
|:---|:---|:---|:---:|
| 1 | 估值安全 | PE/PB 历史5Y 分位 < 50% OR PEG < 1.5 | ⏸ 占位符 |
| 2 | 基本面健康 | ROE > 8% + 营收/利润增速 ≥ 0 | ⏸ 占位符 |
| 3 | 非 ST 风险 | ashare-pre-st-filter | ⏸ 占位符 |
| 4 | 市值门槛 | ≥ 300 亿 (USER_RULE LAW-005) | ⏸ 占位符 |
| 5 | 板块景气 | 板块 ETF 20d收益 > 0 + MA60 趋势向上 | ✅ 复用 sector_relative |

---

## 5 大买入确认 (3+/5 = 真启动)

| # | 标志 | 触发条件 | 验证状态 |
|:---|:---|:---|:---:|
| ① | WT1 甜区穿越 | WT1 从 N-/-L 上升到 M+ [20, 40] | ✅ BT-007 实证 |
| ② | 趋势启动 transition | ADX 30 日前 < 18 → 当前 > 22 + EMA 金叉 + 云上突破 | ✅ |
| ③ | 量价共振 | turnover_anomaly=底部吸筹 + AD line=底部背离 + 5d 量比 > 1.3 | ✅ |
| ④ | 结构完成 | chanlun=三买 + smc=bullish BOS + candlestick 首次转正 | ✅ |
| ⑤ | 基本面拐点 | ROE 季环比拐点 OR 营收增速季环比 > +5pp | ⏸ 待接入 |

---

## 5 大买入否决 (任 1 触发 = 不买)

| # | 标志 | 触发条件 | 实现状态 |
|:---|:---|:---|:---:|
| ① | 下跌趋势未破 | EMA12<EMA26 + ADX > 25 且 5 日前 ADX 更高 | ✅ |
| ② | 量价背离 | 5d 量比 < 0.7 + 5d 价涨 | ✅ |
| ③ | 基本面恶化 | ROE < 5% OR 营收/利润 加速下滑 | ⏸ 待接入 |
| ④ | 板块弱势 | 板块 ETF 20d < -5% OR MA60 下行 | ✅ |
| ⑤ | 估值过高 | PE/PB 历史 5Y 分位 > 70% | ⏸ 待接入 |

---

## 4 阶段 + 3 模式

| 阶段 | 条件 | 动作 |
|:---|:---|:---|
| **1 击球区** | score ≥ 0.65·max + 确认 ≥ 3/5 + 否决 = 0 + Layer 0/1 通过 | 🟢 分批建仓 50% |
| **2 观察区** | score ≥ 0.42·max + 确认 ≥ 1/5 + 否决 = 0 | 🟡 放入观察池 |
| **3 回调买入区** | sell Stage 1 + 价格回调 ≤ 5% + 量缩 + 否决 = 0 | 🟢 加仓 20% (sell闭环) |
| **4 禁入区** | score < 0.42·max OR 否决 ≥ 1 OR Layer 0 锁定 OR Layer 1 不通过 | 🔴 不买 |

| 模式 | 描述 | 触发条件 |
|:---|:---|:---|
| **A 突破买入** | 动量启动 → 建仓 | Layer 0/1 通过 + Stage 1 |
| **B 回调买入** | sell-buyer 闭环加仓 | sell Stage 1 + 回调 5% + 量缩 |
| **C 禁入** | Layer 0 锁定强制关闭 | 国家队净卖出 + MCI Q3 + 化债 < 6 月 |

---

## 与 SELL_LADDER v2.5 的关系

| Sell-Ladder 元素 | Buy-Ladder v3.0 处理 |
|:---|:---|
| 16 信号矩阵 | ✅ 直接复用 calc_* 函数（零修改）|
| 5 动能结束标志 | 反向应用为 5 买入确认标志 (signal=+1 解读为动量启动) |
| 3 阶段框架 | 改造为 4 阶段 + 3 模式（含 sell-buyer 闭环）|
| 化债 deadline | ✅ 复用 (Layer 0 兜底) |
| 时间触发 (2026-12-31 / 2027-04-30) | ✅ 复用（Layer 0 锁定 buy 操作）|
| regime 监测 (MCI / MA60) | ✅ 复用（Layer 0 闸门）|
| 5 动能结束标志判定函数 | ✅ 复用 (sell-buyer 闭环模式 B 中判定 sell Stage) |

---

## 卖出的艺术 vs 买入的艺术

| 维度 | Sell-Ladder v2.5 | Buy-Ladder v3.0 |
|:---|:---|:---|
| 哲学 | "让利润奔跑 + 多信号共振 + 时间兜底" | "不预测底部 + 让趋势自己启动 + sell-buyer 闭环 + regime 闸门" |
| 核心约束 | LAW-002 (重尾分布) | LAW-001 (A 股动量延续) |
| 触发逻辑 | 检测动能结束 | 检测动量启动 (WT1 甜区穿越, 非零穿越) |
| 错误代价 | 踏空（机会成本）| 套牢（资本损失）|
| 与对偶关系 | n/a | sell Stage 1 + 回调 = 模式 B 加仓 |

---

## 待办

- [x] **Phase 0:** 读 sell_ladder.py / data_loader.py / batch_v25_holdings.py / backtest_v090.py 确定复用接口
- [x] **Phase 1:** `8.BUY_LADDER.md` 设计文档
- [x] **Phase 2:** `.opencode/skills/buy-ladder/SKILL.md` 协议层
- [x] **Phase 3:** `buy_ladder.py` 实现 (993 行, 6 新增函数)
- [x] **Phase 4:** `batch_v11_holdings.py` 18 持仓批量验证 (18/18 Layer 0 锁定)
- [x] **Phase 5:** `combo_layer.py` v0.1 (buy+sell 联合调度)
- [x] **Phase 6:** BT-010 计划文档 + raw-log 写入

### 遗留 (P1/P2)
- [ ] **P0 (阻塞 sell-ladder):** sell_ladder `calc_alpha_engine_v21` 内部 `_compute_wt` 不回传 bug → buy_ladder 已绕过 (显式调用 `sl._compute_wt(df)`)，但应修复 sell_ladder 让所有 subagent 受益
- [ ] **P1:** 板块 ETF 覆盖扩展 (akshare 行业查询接口)
- [ ] **P1:** Layer 1 估值/基本面数据源接入 (tushare daily_basic + fina_indicator)
- [x] **P1:** Layer 0 数据自动刷新机制 (v3.0.1: MA60 实时 / MCI 公式实时 / 国家队 md 解析 + Morningstar 月度刷新)
- [ ] **P2:** BT-010 buy-ladder 回测 (alpha-engine-v21 HDF5 + 自建 buy 信号反演)
- [ ] **P2:** 5-Why 阈值参数网格扫描 (ADX 收敛天数 / 回调幅度 [3%/5%/7%/10%] / 量缩阈值)
- [ ] **P3:** 每月 5-Why Challenge 重审 (regime 变化时)
- [ ] **P3:** 与 sell-ladder 的 v2.6 协同升级 (sell-buyer 闭环在 sell 端的对称改造)

---

## 关联文件

| 文件 | 关系 |
|:---|:---|
| `sell_ladder.py` | 16 calc_* 函数 + score_v22 + stage_v22 + check_momentum_end_signals (全部复用, 零修改) |
| `data_loader.py` | 复用 sell-ladder/data_loader.py (集中化 data/market/daily/) |
| `batch_v25_holdings.py` | sell-ladder 批量模式, buy-ladder batch_v11_holdings.py 仿照此模式 |
| `backtest_v090.py` | sell-ladder 回测模式, BT-010 计划仿照此模式 |
| `8.BUY_LADDER.md` | 完整方法论文档 (5-Why Challenge + 4 阶段 + 3 模式) |
| `.opencode/skills/buy-ladder/SKILL.md` | 协议层 (subagent 加载入口) |
| `personal-system/backtests/BT-007/report.md` | deep-recovery 17% 胜率 = v1.0 反方质控核心证据 |
| `personal-system/backtests/BT-010/README.md` | BT-010 回测计划 (待启动) |

---

## 当前状态 (2026-08-11)

- ✅ v3.0 设计文档 + 协议层 + 实现代码 (993 行, 对齐 LazyBear + Vibe-Trading canonical)
- ✅ 18 持仓批量验证 (18/18 Layer 0 锁定, 符合预期)
- ✅ 300725 单标的 force-unlock 测试 (WT1=44.07 已超甜区, 阶段 2 观察区)
- ✅ combo_layer v0.1 联合调度 (300725 = sell stage 1 + buy stage 4 = 持有)
- ✅ raw-log 写入 (NEW 标签)
- ⏸ BT-010 回测 (计划阶段, 待用户批准)
- ⏸ Layer 1 数据源接入 (P1)

---

*End of README — 2026-08-11*

*版本沿革: v1.0 是"反转式触发"，v1.1 是"动量延续 + 安全边际 + regime 闸门"，v1.2 草案是"per-stock 自适应阈值"（被反方质控否决），v3.0 完全回滚到经典 LazyBear/V21 公式 + Vibe-Trading canonical（当前版）。*
*买入的艺术 = 不预测底部 + 让趋势自己启动 + 让 sell-ladder 告诉你何时加仓。*