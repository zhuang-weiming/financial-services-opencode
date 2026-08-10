---
name: sell-ladder
description: SELL_LADDER v2.2 卖出判定框架——14 skill 信号矩阵（事件×2/趋势×1 分级计票）、5 大动能结束标志、3 阶段卖出判定、5 维触发矩阵。当用户问"是否止盈/减持/卖出/清仓/动能是否结束/卖出梯子/SELL_LADDER/该不该卖"时加载。这是协议层，实际工具在 .opencode/memory/personal-system/sell-ladder/。
---

# SELL_LADDER v2.2 — 协议层

> **本 skill 是协议层，不存数据、不存算法。**
> 实际工具在 `.opencode/memory/personal-system/sell-ladder/`：
> - `sell_ladder.py` — 统一入口（已内联 14 skill 核心算法，确定性计算，不依赖加载外部 skill；**支持任意股票**）
> - `data/` — 本地 CSV（raw_daily_300725.csv + cross-data/ CDMO 同业 + tech-pool/ 科技股池 + 任意新标的自动下载）
> - `data/mcp/YYYY-MM-DD/` — MCP 数据落盘（Morningstar/FactSet 补充数据必须落盘）
> - `runs/YYYY-MM-DD/` — 每次运行结果 JSON 快照
> - `backtest_seed_2026.py` — walk-forward 回测脚本（验证方法有效性）

---

## 加载协议（任何 subagent 调用时执行）

### 运行命令

```bash
# 单标的判定（含 4 只 CDMO 同业配对）— 任意股票均可
python3 .opencode/memory/personal-system/sell-ladder/sell_ladder.py --ticker 300725 --cost 36.62

# 不带同业（加速，无 pair_trading/factor-research 截面）
python3 .opencode/memory/personal-system/sell-ladder/sell_ladder.py --ticker 688256 --no-cdmo

# 任意新标的（自动 Sina 下载 900 bars → data/raw_daily_<code>.csv，永久缓存；可指定同业池）
python3 .opencode/memory/personal-system/sell-ladder/sell_ladder.py --ticker 601318 --peers 601628,601601

# v2.2 权重覆盖（默认事件×2/趋势×1，BT-008 回测最优）
python3 .opencode/memory/personal-system/sell-ladder/sell_ladder.py --ticker 300725 --w-event 2 --w-trend 1

# 回测验证（2026 年初科技股行情有效性；--variant v2.0/v2.1/v2.2，--w-event 权重扫描）
python3 .opencode/memory/personal-system/sell-ladder/backtest_seed_2026.py --variant v2.2 --w-event 2 --w-trend 1
```

### 数据来源（data-priority 分层）

| 标的池 | 位置 | 来源 |
|--------|------|------|
| 300725 药石科技 | `data/raw_daily_300725.csv` | Sina API（本地缓存永久化） |
| CDMO 同业 002821/603259/300759/300363 | `data/cross-data/` | Sina API |
| 科技股池 688256/688981/002371/300308/688041/603501 | `data/tech-pool/` | Sina API |
| 任意新标的（通用化） | `data/raw_daily_<code>.csv` | Sina API 自动下载（本地无则联网，落盘后永久缓存） |
| MCP 补充（Morningstar 估值/研究/FactSet） | **`data/mcp/YYYY-MM-DD/` 必须落盘** | MCP 调用结果快照（JSON/MD），密钥/原始响应不落盘 |

> 所有行情数据经 Sina API 下载后**永久保存在本地**，此后运行不再联网。
> **MCP 数据落盘纪律（用户 2026-08-10 明确要求）:** 任何从 Morningstar/FactSet MCP 获得的数据点，必须写入 `data/mcp/YYYY-MM-DD/<ticker>_<source>.json` 保存证据链，不得只存在于对话上下文。

### 输出解读（14 skill 信号矩阵）

每行 = 一个 skill 的当前信号：

| 信号 | 含义 |
|------|------|
| 🟢 +1 | 看多/动能延续 |
| ⚪ 0 | 中性/不参与判定 |
| 🔴 -1 | 看空/动能反转 |

**v2.2 分级计票信号**（决定阶段，BT-008 回测定案：事件×2/趋势×1）：

| 级别 | 信号 | 权重 |
|------|------|:---:|
| 事件信号（明确买卖点） | `candlestick`、`chanlun`、`ml_strategy` | **×2 票** |
| 趋势信号（方向判定） | `alpha_engine_v21`、`technical_basic`、`ichimoku`、`smc`、`alpha_zoo`、`multi_factor` | ×1 票 |
| 辅助观察（不参与计票） | `harmonic`、`pair_trading`、`volatility`、`factor_research` | 0 票 |

**阶段判定规则（v2.2 分级计票，max=12）：**

| 条件 | 阶段 | 建议 |
|------|------|------|
| 得分 ≥ 9 (0.75·max) 且 动能结束标志 ≤1 | 阶段 1: 强动能期 | 🟢 持有 100% |
| 得分 ≥ 5 (0.42·max) 且 结束标志 ≤2 | 阶段 2: 动能衰减期 | 🟡 分批止盈 (减 20-40%) |
| 得分 < 5 且 动能结束标志 ≥3 共振 | 阶段 3: 动能结束期 | 🔴 大幅减仓 (减 70-100%) |
| 得分 < 5 但 结束标志 <3 | 阶段 2.5: 得分触底未共振 | 🟠 减 20-40% 观察（不恐慌清仓） |

**5 大动能结束标志**（任何命中都是反转预警）：

| # | 标志 | 触发条件 |
|---|------|----------|
| ① | 趋势破坏 | EMA(12) 跌破 + ADX<20 + ichimoku 跌穿云 |
| ② | 动量反转 | WT1<-20 + RSI<30 持续 + 20d 动量<-10% |
| ③ | 量能背离 | OBV 下降 + 价格新高 (5 日) |
| ④ | 结构破坏 | smc ChoCH + chanlun 顶分型 + ichimoku 跌穿云 |
| ⑤ | 波动率突变 | HV 100% → 30% (30 日内) |

**判定纪律（重要，来自用户多次纠错）：**
- 强趋势（ADX>25、HV 高分位、涨幅大）中 HV 高/RSI 高是**健康特征，不是卖出信号**
- 单信号（如只有一个 skill 翻空）**不触发卖出**，必须多信号共振
- 5 动能结束标志 3+ 触发才允许"大幅减仓"
- 化债 deadline 是硬约束：2026-12-31 减至 50%、2027-04-30 减至 30%、2027-07-01 清仓

---

## 写回协议

| 场景 | 写到哪里 |
|------|----------|
| 每次运行结果 | 自动存 `runs/YYYY-MM-DD/sell_ladder_<ticker>_<date>.json`（脚本自动） |
| 新认知/判定结论 | `raw-log/YYYY-MM-DD.md` (append，永不修改历史) |
| 卖出决策争议 | `6.CONFLICTS.md`（如回测与 SELL_LADDER 法则矛盾） |
| 正式回测 | `backtests/BT-XXX/` + 更新 `5.BACKTEST_INDEX.md` |

---

## 与其他组件协作

| 组件 | 协作 |
|------|------|
| `personal-trading-system` | 先读本 skill 再读它；本 skill 是 sell-ladder 工具入口，它是全系统协议层 |
| `7.SELL_LADDER.md` | 方法论文档（信号矩阵设计 + 5 标志定义 + 3 阶段框架） |
| `7.1.POSITION_SIZING.md` | §5.5 存放 SELL_LADDER 最近一次运行输出 |
| `backtest-builder` | 新回测前必读 runs/ 历史，避免重复 |
| `wealth-management` | "我的仓位怎么办" → 加载本 skill 跑判定 |
| `alpha-researcher` | 信号有效性验证 → 用 backtest_seed_2026.py |

---

## 当前状态 (2026-08-10)

- sell_ladder.py **v2.2 定案** ✅：14 skill 内联 + v2.2 分级计票（score_v22/stage_v22 内联，--w-event/--w-trend CLI）
  - **v2.1 修复 (BT-008):** factor_research strong_momentum 阈值 f2_ic>0.5 数学不可达（全样本 max +0.10）→ 5 强集合改用 multi_factor 补位
  - **v2.2 定案 (权重网格扫描):** 事件信号 ×2/趋势 ×1 最优点（踏空代价 7.03% → 1.71%，-76%）；×3 过度（持有质量崩至 0.68%）
  - **阶段 3 防误杀:** 需 end_count ≥3 共振才大幅减仓，否则阶段 2.5 观察
- **通用化 ✅:** 任意股票可跑（本地无数据自动 Sina 下载 900 bars → data/raw_daily_<code>.csv，已验证 601318）
- 数据: 300725 (2118 bars) + 4 CDMO 同业 (cross-data/) + 6 科技股池 (tech-pool/) + 601318 (raw_daily_601318.csv)
- runs/: 2026-08-10 (300725 + 601318 + 权重扫描 CSV)
- 回测: BT-008 ✅ (2026 科技股 walk-forward, v2.0 REJECTED / v2.1 PARTIALLY_SUPPORTED / **v2.2 SUPPORTED 定案**)

---

*End of SKILL.md*