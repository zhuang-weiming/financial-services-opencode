---
name: buy-ladder
description: BUY_LADDER v1.1 买入判定框架——Layer 0 regime 闸门 + Layer 1 选股 5 道筛子 + Layer 2 16 信号矩阵（sell-ladder 复用 + 6 transition）+ 4 阶段 + 3 模式（含 sell-buyer 闭环）。当用户问"是否买入/建仓/加仓/可不可以买/买入信号/买入梯子/BUY_LADDER/该不该买"时加载。这是协议层，实际工具在 .opencode/memory/personal-system/buy-ladder/。
---

# BUY_LADDER v1.1 — 协议层

> **本 skill 是协议层，不存数据、不存算法。**
> 实际工具在 `.opencode/memory/personal-system/buy-ladder/`：
> - `buy_ladder.py` — 统一入口（已内联 sell_ladder 16 calc_* + 4 个新增 calc_，确定性计算）
> - `data_loader.py` — 复用 sell-ladder/data_loader.py（集中化 data/market/daily/）
> - `runs/YYYY-MM-DD/` — 每次运行结果 JSON 快照
> - `BT-010/` — buy-ladder 回测目录（计划中）

---

## 加载协议（任何 subagent 调用时执行）

### 运行命令

```bash
# 单标的判定（任意股票 + 任意板块 ETF）
python3 .opencode/memory/personal-system/buy-ladder/buy_ladder.py --ticker 300725

# 带持仓状态（已有持仓 → 启用 sell-buyer 闭环）
python3 .opencode/memory/personal-system/buy-ladder/buy_ladder.py --ticker 300725 --cost 36.62 --shares 10000 --held

# 任意新标的
python3 .opencode/memory/personal-system/buy-ladder/buy_ladder.py --ticker 600519

# Layer 0 强制覆盖（不推荐，仅调试）
python3 .opencode/memory/personal-system/buy-ladder/buy_ladder.py --ticker 300725 --force-regime-unlock

# 18 只持仓批量运行（仿照 sell-ladder batch_v25_holdings.py）
python3 .opencode/memory/personal-system/buy-ladder/batch_v11_holdings.py
```

### 数据来源（复用 sell-ladder data-priority 分层）

| 标的池 | 位置 | 来源 |
|--------|------|------|
| 任意 A 股/ETF（复用 sell-ladder） | `<workspace>/data/market/daily/<code>_<name>.csv` | Sina API 自动下载（本地无则联网）|
| Layer 1 估值/基本面（待接入）| tushare daily_basic + fina_indicator | token-gated, 高质量 |
| Layer 0 regime（MCI/国家队/MA60）| wif-ashare-advisory + national_team_obs | 已存在 |
| MCP 补充（Morningstar/FactSet）| `data/mcp/YYYY-MM-DD/` 必须落盘 | 与 sell-ladder 一致 |

### 输出解读

每行 = 一个 layer / signal 的当前状态：

| 信号 | 含义 |
|------|------|
| 🟢 +1 | 通过 / 看多 / 触发 |
| ⚪ 0 | 中性 / 不参与判定 |
| 🔴 -1 | 不通过 / 看空 / 触发否决 |

**3 层架构输出：**

```
Layer 0: REGIME FILTER
  ├── 沪深300 MA60: -2.66% [⚪ 未触发 (> -7% 但 < 0%)]
  ├── WIF MCI: 0.386 [🔴 锁定 (Q3 防御)]
  └── 国家队: 净卖出 [🔴 锁定]
  → Layer 0 综合: 🔒 锁定 (2/3 不通过)

Layer 1: SELECTION FILTER (5 道筛子)
  ├── 估值安全: ⚪ 待接入
  ├── 基本面健康: ⚪ 待接入
  ├── 非 ST 风险: ⚪ 待接入
  ├── 市值门槛: ⚪ 待接入
  └── 板块景气: ⚪ 待接入
  → Layer 1 综合: ⏸ 跳过 (regime 已锁定, 不进入)

Layer 2: TIMING ENGINE
  → 禁用（Layer 0 锁定）
```

**Buy Stage 4 阶段判定：**

| 条件 | 阶段 | 建议 |
|------|------|------|
| Layer 0 解锁 + Layer 1 5/5 通过 + score ≥ 0.65·max + 确认 ≥ 3/5 + 否决 = 0 | 阶段 1: 击球区 | 🟢 分批建仓 50% |
| score ≥ 0.42·max + 确认 ≥ 1/5 + 否决 = 0 | 阶段 2: 观察区 | 🟡 放入观察池 |
| sell-ladder Stage 1 + 回调 ≤ 5% + 量缩 + 否决 = 0 | 阶段 3: 回调买入区 | 🟢 加仓 20% (sell闭环) |
| score < 0.42·max OR 否决 ≥ 1 OR Layer 0 锁定 OR Layer 1 不通过 | 阶段 4: 禁入区 | 🔴 不买 |

**5 大买入确认标志（3+/5 触发）：**

| # | 标志 | 触发条件 | 状态 |
|---|------|----------|:---:|
| ① | WT1 甜区穿越 | WT1 从 N-/-L 上升到 M+ [20, 40] | ✅ |
| ② | 趋势启动 transition | ADX 30 日前 < 18 → 当前 > 22 + EMA 金叉 + 云上突破 | ✅ |
| ③ | 量价共振 | turnover_anomaly=底部吸筹 + AD line=底部背离 + 5d 量比 > 1.3 | ✅ |
| ④ | 结构完成 | chanlun=三买 + smc=bullish BOS + candlestick 首次转正 | ✅ |
| ⑤ | 基本面拐点 | ROE 季环比拐点 OR 营收增速季环比 > +5pp | ⏸ 待接入 |

**5 大买入否决标志（任 1 触发 = 不买）：**

| # | 标志 | 触发条件 |
|---|------|----------|
| ① | 下跌趋势未破 | EMA12< EMA26 + ADX > 25 **且 5 日前 ADX 更高（未收敛）** |
| ② | 量价背离 | 5d 量比 < 0.7 + 5d 价涨 |
| ③ | 基本面恶化 | ROE < 5% OR 营收/利润 加速下滑 |
| ④ | 板块弱势 | 板块 ETF 20d 收益 < -5% OR 板块 ETF MA60 下行 |
| ⑤ | 估值过高 | PE/PB 历史 5Y 分位 > 70% |

---

## 写回协议

| 场景 | 写到哪里 |
|------|----------|
| 每次运行结果 | 自动存 `runs/YYYY-MM-DD/buy_ladder_<ticker>_<date>.json` |
| 新认知/判定结论 | `raw-log/YYYY-MM-DD.md` (append, 永不修改历史) |
| buy 决策争议 | `6.CONFLICTS.md` (如回测与 BUY_LADDER 法则矛盾) |
| 正式回测 | `backtests/BT-010/` + 更新 `5.BACKTEST_INDEX.md` |

---

## 与其他组件协作

| 组件 | 协作 |
|------|------|
| `sell-ladder` | 同一数据源 + 16 calc_* 复用 + Stage 3 模式 B 闭环 |
| `personal-trading-system` | 先读本 skill 再读它；本 skill 是 buy-ladder 工具入口 |
| `8.BUY_LADDER.md` | 方法论文档（5-Why Challenge + 4 阶段 + 3 模式）|
| `wif-ashare-advisory` | Layer 0 MCI 数据源 |
| `national-team-observation` | Layer 0 国家队 regime 数据源 |
| `stock-deep-dive` | "分析 600519/某只股票" → 加载本 skill 跑买入判定 |
| `backtest-builder` | BT-010 buy-ladder 回测 |

---

## 当前状态 (2026-08-11)

- ✅ **v1.1 设计文档完成** (`8.BUY_LADDER.md`)：4 个 5-Why Challenge + 4 阶段 + 3 模式 + 6 个 buy/sell 冲突仲裁
- ✅ **协议层 SKILL.md 完成**（本文件）
- ⏳ **buy_ladder.py 实现** (P1 阻塞: 4 个新增 calc_ 函数 + 主函数 + run 接口)
- ⏳ **批量验证** (P1: 对 17 持仓 + 1 ETF 跑一次, 默认全部应进入"禁入区")
- ⏳ **combo_layer.py** (P2: buy + sell 联合调度)
- ⏳ **BT-010 回测** (P2: 用 alpha-engine-v21 HDF5 反演 buy 信号有效性)
- ⏳ **Layer 1 数据源接入** (P2: tushare daily_basic + fina_indicator)

---

## 与 SELL_LADDER 的关键差异

| 维度 | Sell-Ladder v2.5 | Buy-Ladder v1.1 |
|:---|:---|:---|
| 触发逻辑 | 检测动能结束 | **检测动量启动** |
| 信号方向 | 反向（高位逃）| **正向（低位追）但必须 sweet zone 非反转** |
| 核心约束 | 让利润奔跑 | **不预测底部** |
| LAW 依据 | LAW-002 | **LAW-001**（动量延续）|
| Regime 角色 | 仅化债 deadline 兜底 | **Layer 0 闸门 3/3 必须通过** |
| 与对偶关系 | n/a | sell-buyer 闭环（模式 B）|

---

*End of SKILL.md*

*买入的艺术 = 不预测底部 + 让趋势自己启动 + 让 sell-ladder 告诉你何时加仓。*