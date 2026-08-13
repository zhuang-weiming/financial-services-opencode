---
name: buy-ladder
description: BUY_LADDER v3.1 数据驱动买入判定框架——4 个回测验证正α信号加权计票 (technical_basic×2 + alpha_zoo×2 + candlestick×1 + ad_line×1) + 绝对阈值 (≥4/6 击球区, ≥3/6 观察区)。BT-015 信号级事件研究 + BT-016 权重阈值扫描定案 (200 池 2024-10~2026-08 真实数据)。Layer 0 regime / Layer 1 5 道筛子在结构性牛市不可靠, 降为咨询性 (仅 ST 红牌硬否决)。判定链 = ST否决 → 5 大否决 → 积分阈值。当用户问"是否买入/建仓/加仓/可不可以买/买入信号/买入梯子/BUY_LADDER/该不该买"时加载。这是协议层, 实际工具在 .opencode/memory/personal-system/buy-ladder/。
---

# BUY_LADDER v3.1 — 协议层

> **本 skill 是协议层，不存数据、不存算法。**
> 实际工具在 `.opencode/memory/personal-system/buy-ladder/`：
> - `buy_ladder.py` — 统一入口（已内联 sell_ladder 16 calc_* + 4 个新增 calc_，确定性计算）
> - `data_loader.py` — 复用 sell-ladder/data_loader.py（集中化 data/market/daily/）
> - `runs/YYYY-MM-DD/` — 每次运行结果 JSON 快照
> - `BT-015/BT-016/` — 积分信号 + 权重阈值回测定案（数据驱动基础）

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

**v3.1 输出形态（Layer 0/1 咨询性 + 积分判定）：**

```
[Layer 0] REGIME FILTER (v3.1 咨询性 — 结构性牛市无法可靠判定 regime, 不阻断判定链)
  ├── 沪深300 MA60: -2.66% [🔴]
  ├── WIF MCI: 0.386 [🔴]
  └── 国家队: 净卖出 [🔴]
  → 综合: 🔒 锁定 — 仅展示, v3.1 不据此阻断

[Layer 1] SELECTION FILTER (v3.1 咨询性 — 估值/基本面待接入; 仅 ST 风险为硬否决)
  → 通过: 4/5 (咨询 — 不阻断)

[Layer 2] TIMING ENGINE (v3.1 积分计票)
  → 计票信号: technical_basic×2 + alpha_zoo×2 + candlestick×1 + ad_line×1
  → 加权得分: score/6 (绝对阈值: ≥4 击球 / ≥3 观察)
```

**Buy Stage 4 阶段判定（v3.1 绝对阈值，BT-016 定案）：**

| 条件 | 阶段 | 建议 |
|------|------|------|
| score ≥ 4/6 + 否决 = 0 + 非 ST | 阶段 1: 击球区 | 🟢 分批建仓 50%（全期 α60 +1.26%, 2026 弱市 +4.80%）|
| score ≥ 3/6 + 否决 = 0 + 非 ST | 阶段 2: 观察区 | 🟡 放入观察池 |
| sell-ladder Stage 1 + 回调 ≤ 5% + 量缩 + 否决 = 0 | 阶段 3: 回调买入区 | 🟢 加仓 20% (sell闭环) |
| score < 3/6 OR 否决 ≥ 1 OR ST 红牌 | 阶段 4: 禁入区 | 🔴 不买 |

> **v3.1 计票信号（BT-015 验证）**: technical_basic(+5.18% α60) / alpha_zoo(+3.67%, 跨年双显著) / candlestick(+1.05%) / ad_line(+1.05%) ×权重 2/2/1/1。
> **移出计票（回测负α或不可测）**: chanlun/volatility/harmonic/ml_strategy/turnover_anomaly（显著负）; smc/pair/factor_research/multi_factor/sector_relative（缓存零/断链）。multi_factor 为待验候补。

> **v3.1 计票信号定义（4 个，替代旧 5 大买入确认标志）:**

| 计票信号 | 权重 | 触发条件（方向） | 状态 |
|---|:---:|------|:---:|
| technical_basic | ×2 | EMA12>EMA26 趋势 + ADX 上升 | ✅ 在计票 |
| alpha_zoo | ×2 | 20d 动量 > 0（跨年显著）| ✅ 在计票 |
| candlestick | ×1 | 20d 形态 score > 0 | ✅ 在计票 |
| ad_line | ×1 | 底部背离 signal=+1 | ✅ 在计票 |
| _（旧事件类信号）_ | _0_ | _chanlun/smc/结构/基本面拐点 — 回测负α 或不可测_ | ⏸ 移出 |

**5 大买入否决标志（任 1 触发 = 不买，ST 红牌另计）：**

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
| 正式回测 | `backtests/BT-015/`、`backtests/BT-016/` (积分定案) + 更新 `5.BACKTEST_INDEX.md` |

---

## 与其他组件协作

| 组件 | 协作 |
|------|------|
| `sell-ladder` | 同一数据源 + 16 calc_* 复用 + Stage 3 模式 B 闭环 |
| `personal-trading-system` | 先读本 skill 再读它；本 skill 是 buy-ladder 工具入口 |
| `8.BUY_LADDER.md` | 方法论文档（5-Why Challenge + 4 阶段 + 3 模式）|
| `wif-ashare-advisory` | Layer 0 MCI 数据源 (咨询性) |
| `national-team-observation` | Layer 0 国家队 regime 数据源 (咨询性) |
| `stock-deep-dive` | "分析 600519/某只股票" → 加载本 skill 跑买入判定 |
| `backtest-builder` | BT-015/016 buy-ladder 积分回测 |

---

## 当前状态 (2026-08-13)

- ✅ **v3.1 数据驱动积分定案** (BT-015 信号级事件研究 + BT-016 权重×阈值扫描): 4 信号 2/2/1/1 + 绝对阈值 ≥4 击球 / ≥3 观察
- ✅ **判定链重构**: Layer 0/Layer 1 → 咨询性 (结构性牛市无法可靠判定 regime, 用户指令), 仅 ST 红牌硬否决 + 5 否决 + 积分
- ✅ **死灯复核**: multi_factor 生产活跃 (候补待验); smc/volatility/chanlun 等移出计票 (死灯或显著负 α)
- ✅ **真实数据验证**: 18 持仓实测 601919=击球区(5/6), 300725=观察区(3/6)
- ⏳ **组合级含成本净值复测** (P2)

---

## 与 SELL_LADDER 的关键差异

| 维度 | Sell-Ladder v2.5 | Buy-Ladder v3.1 |
|:---|:---|:---|
| 触发逻辑 | 检测动能结束 | **检测动量启动** |
| 信号方向 | 反向（高位逃）| **正向（低位追）但必须 sweet zone 非反转** |
| 核心约束 | 让利润奔跑 | **不预测底部** |
| LAW 依据 | LAW-002 | **LAW-001**（动量延续）|
| Regime 角色 | 仅化债 deadline 兜底 | **v3.1 咨询性** (结构性牛市不判 regime, 只看积分) |
| 积分依据 | v2.5 16 信号矩阵 | **BT-015/016 回测验证的 4 信号 2/2/1/1 + 绝对阈值** |
| 与对偶关系 | n/a | sell-buyer 闭环（模式 B）|

---

*End of SKILL.md*

*买入的艺术 = 不预测底部 + 让趋势自己启动 + 让 sell-ladder 告诉你何时加仓。*