# BUY_LADDER — 数据驱动积分买入框架 (v3.1)

> **状态:** v3.1 (2026-08-13 — **积分方案由真实回测定案**: BT-015 信号级事件研究 + BT-016 权重×阈值扫描, 200 池 2024-10~2026-08 真实数据)
> **位置:** `.opencode/memory/personal-system/buy-ladder/` (永久能力)
> **协议层:** `.opencode/skills/buy-ladder/SKILL.md` (subagent 加载入口)
> **核心:** 不看 Layer0/Layer1 硬闸 (结构性牛市无法可靠判定 regime), 只看 **signal 结果与积分** — 4 个回测验证正 α 信号加权计票 + 绝对阈值 → 击球/观察/禁入
>
> **⚠️ v3.1 关键变更 (相对 v3.0):**
> - **计票信号只剩 4 个** (BT-015 验证): `technical_basic×2 + alpha_zoo×2 + candlestick×1 + ad_line×1`, 总分 0~6
> - **删除动态阈值** `0.65/0.42×max` (两年锁死根源) → **绝对阈值**: `≥4/6 击球` `≥3/6 观察`
> - **移出计票**: chanlun/volatility/harmonic/ml_strategy/turnover_anomaly (**回测显著负 α**); smc/pair/factor_research/multi_factor/sector_relative (**缓存零或断链, 不可测**)
> - **Layer 0/Layer 1 降为咨询性** (仅 ST 红牌为硬否决) — 判定链 = 否决 → 积分
> - **multi_factor** 生产实测活跃 (31.6% 正票) — 列为待验候补, 缓存重建后纳入

---

## 目录结构

```
.opencode/memory/personal-system/buy-ladder/
├── README.md                       ← 本文件 (使用说明)
├── buy_ladder.py                  ← 统一入口脚本 (v3.1)
├── batch_v11_holdings.py          ← 18 持仓批量验证 (调用 run_buy_ladder, 兼容 v3.1)
├── combo_layer.py                 ← buy + sell 联合调度
├── runs/                           ← 历史跑过的结果
│   └── 2026-08-13/
│       ├── buy_ladder_<ticker>_2026-08-13.json
│       └── v11_holdings_2026-08-13.json
└── 回测证据 → backtests/BT-015/ (信号级), BT-016/ (权重阈值) [buy 积分定案]
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

# 18 持仓批量验证 (v3.1: 按积分/否决分流, 601919=击球区 300725=观察区)
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

## 积分方案 (v3.1 — BT-015/BT-016 回测定案)

### 计票信号 (只有这 4 个进积分, 权重 α60 近似比例)

| 信号 | 权重 | BT-015 证据 (2026 α60) | 触发条件 |
|:---|:---:|:---:|:---|
| `technical_basic` | ×2 | **+5.18%** (t=4.23) | EMA12>EMA26 + ADX>20 |
| `alpha_zoo` | ×2 | **+3.67%** (t=4.49, 跨年双显著) | 20d 动量 ret>+10% |
| `candlestick` | ×1 | **+1.05%** (t=2.77) | 形态 score>0 |
| `ad_line` | ×1 | **+1.05%** (t=2.31) | 底部背离 |

总分 0~6。**绝对阈值** (BT-016 W_B 扫描, 替代锁死的 0.65/0.42×max):

| 分数 | 阶段 | 全期 α60 | 2026 弱市 α60 |
|:---:|:---|:---:|:---:|
| **≥4/6** | **1 击球区** | +1.26% (p<1e-4) | **+4.80%** |
| **≥3/6** | **2 观察区** | +1.22% | +4.59% |
| <3/6 | 4 禁入区-得分不足 | — | — |

### 判定链 (v3.1)

```
ST 红牌 (硬否决) → 5 大否决 veto → 积分绝对阈值 → 阶段/动作
```

Layer 0 regime / Layer 1 5 道筛子 = **咨询性展示, 不阻断** (结构性牛市无法可靠判定 regime; 估值/基本面筛子仍为占位符)

### 为什么删掉的信号 (回测证据)

| 信号 (移出计票) | 证据 |
|:---|:---|
| chanlun / volatility / harmonic / ml_strategy / turnover_anomaly | 2026 事件研究 **显著负 α**: −3.36% / −3.34% / −1.29% / −0.77% / −12.31% |
| smc / pair_trading / factor_research | 缓存口径恒 0 (smc 还带 lookahead) |
| sector_relative | 生产断链 (调用丢 ticker + 映射表仅 20 代码), 缓存恒 0 |
| multi_factor | 生产实测活跃 (31.6% 正票) 但缓存零无法事件研究 → **待验候补** |
| ichimoku | 触发极稀有 (<1 次/年/池), 无统计量 |

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

## Layer 0 regime 闸门 (v3.1 咨询性 — 不阻断)

| # | 条件 | 数据源 | 当前 (2026-08-11) | 参考 |
|:---|:---|:---|:---:|:---:|
| 1 | 沪深300 MA60 > -7% | Sina 510300 或 CHINA_FRAMEWORK 兜底 | -2.66% | ✅ |
| 2 | WIF MCI > 0.5 | wif-ashare-advisory 或 CHINA_FRAMEWORK 兜底 | 0.386 | 🔒 |
| 3 | 国家队净买入 (> -3% 月环比) | national_team_obs | -89% vs 峰值 | 🔒 |

**v3.1: 仅展示。** 结构性牛市无法可靠判定 regime → 不回退/不阻断判定。最终动作由积分决定。

---

## Layer 1 5 道筛子 (v3.1 咨询性 — 仅 ST 硬否决)

| # | 筛子 | 阈值 | 实现状态 |
|:---|:---|:---|:---:|
| 1 | 估值安全 | PE/PB 历史5Y 分位 < 50% OR PEG < 1.5 | ⏸ 占位符 |
| 2 | 基本面健康 | ROE > 8% + 营收/利润增速 ≥ 0 | ⏸ 占位符 |
| 3 | 非 ST 风险 | ashare-pre-st-filter | ⏸ 占位符 (**唯一硬否决**) |
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

## 4 阶段 + 3 模式 (v3.1)

| 阶段 | 条件 | 动作 |
|:---|:---|:---|
| **1 击球区** | score ≥ 4/6 + 否决 = 0 | 🟢 分批建仓 50% |
| **2 观察区** | score ≥ 3/6 + 否决 = 0 | 🟡 放入观察池 |
| **3 回调买入区** | sell Stage 1 + 价格回调 ≤ 5% + 量缩 + 否决 = 0 | 🟢 加仓 20% (sell闭环) |
| **4 禁入区** | score < 3/6 OR 否决 ≥ 1 OR ST 红牌 | 🔴 不买 |

| 模式 | 描述 | 触发条件 |
|:---|:---|:---|
| **A 突破买入** | 动量启动 → 建仓 | 积分 ≥4 + 否决 = 0 |
| **B 回调买入** | sell-buyer 闭环加仓 | sell Stage 1 + 回调 5% + 量缩 |
| **C 禁入** | 得分不足/否决/ST | 不满足 A/B |

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
- [ ] **P1:** multi_factor 生产序列入缓存后候补验证 (BT-015 断链未测)
- [ ] **P1:** 板块 ETF 覆盖扩展 (akshare 行业查询接口)
- [ ] **P1:** Layer 1 估值/基本面数据源接入 (tushare daily_basic + fina_indicator) — v3.1 咨询级, 仅 ST 硬否决
- [x] **P1:** Layer 0 数据自动刷新机制 (v3.0.1: MA60 实时 / MCI 公式实时 / 国家队 md 解析 + Morningstar 月度刷新)
- [ ] **P2:** 组合级含成本净值复测 (买入分 → 实际组合收益, 200 池)
- [ ] **P2:** 5-Why 阈值参数网格扫描 (回调幅度 [3%/5%/7%/10%] / 量缩阈值)
- [ ] **P3:** 每月 5-Why Challenge 重审 (结构性牛市 regime 变化时)
- [ ] **P3:** 与 sell-ladder 的 v2.6 协同升级 (sell-buyer 闭环在 sell 端的对称改造)

> **注:** BT-010 (LazyBear canonical 买入信号回测, NAV 13.46) 为 v3.0 时代验证; **买入积分判定以 BT-015/BT-016 为准**。

---

## 关联文件

| 文件 | 关系 |
|:---|:---|
| `sell_ladder.py` | calc_* 函数 + score_v22 + stage_v22 (复用, 零修改) |
| `data_loader.py` | 复用 sell-ladder/data_loader.py (集中化 data/market/daily/) |
| `8.BUY_LADDER.md` | 完整方法论文档 (v3.1) |
| `.opencode/skills/buy-ladder/SKILL.md` | 协议层 (subagent 加载入口) |
| `personal-system/backtests/BT-015/README.md` | 买入信号级事件研究 (v3.1 信号筛) |
| `personal-system/backtests/BT-016/README.md` | 权重×阈值扫描 (v3.1 积分定案) |
| `personal-system/backtests/BT-014/README.md` | 买入分原型回测 (v3.1 上游) |
| `personal-system/backtests/BT-011/results/signal_cache_v2.parquet` | 200 池信号缓存 (BT-011~016 数据源) |

---

## 当前状态 (2026-08-13)

- ✅ **v3.1 数据驱动积分** (BT-015 + BT-016 回测定案): 4 信号加权 (2/2/1/1) + 绝对阈值 (≥4 击球 / ≥3 观察)
- ✅ 判定链重构: Layer0/Layer1 → 咨询性; 仅 ST 硬否决 + 5 否决 + 积分
- ✅ 死灯复核: multi_factor 生产活跃 (候补); smc/pair/sector_relative 移出计票
- ✅ 18 持仓实测: 601919 score 5/6 击球区, 300725 3/6 观察区, 其余按积分/否决分流
- ✅ BT-015/BT-016 留痕 (README + INDEX Adversarial + raw-log)
- ⏸ multi_factor 生产序列入缓存后的候补验证 (P1)
- ⏸ 组合级含成本净值复测 (P2)

---

*End of README — 2026-08-11*

*版本沿革: v1.0 是"反转式触发"，v1.1 是"动量延续 + 安全边际 + regime 闸门"，v1.2 草案是"per-stock 自适应阈值"（被反方质控否决），v3.0 回滚到经典 LazyBear/V21 公式，v3.1 改为**数据驱动积分**（BT-015/016 回测定案，当前版）。*
*买入的艺术 = 不预测底部 + 让趋势自己启动 + 让 sell-ladder 告诉你何时加仓。*