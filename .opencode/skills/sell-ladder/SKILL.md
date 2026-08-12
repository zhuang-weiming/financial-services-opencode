---
name: sell-ladder
description: SELL_LADDER v2.5 卖出判定框架——16 skill 信号矩阵（事件×2/趋势×1 分级计票）、5 大动能结束标志、3 阶段卖出判定（含阶段 2.5 兜底）、5 维触发矩阵。当用户问"是否止盈/减持/卖出/清仓/动能是否结束/卖出梯子/SELL_LADDER/该不该卖"时加载。这是协议层，实际工具在 .opencode/memory/personal-system/sell-ladder/。
---

# SELL_LADDER v2.5 — 协议层

> **本 skill 是协议层，不存数据、不存算法。**
> 实际工具在 `.opencode/memory/personal-system/sell-ladder/`：
> - `sell_ladder.py` — 统一入口（已内联 16 skill 核心算法，确定性计算，不依赖加载外部 skill；**支持任意股票**）
> - `data_loader.py` — 统一日线加载器（搜索 `data/market/daily/` → 旧位置 fallback → Sina 下载落盘）
> - `data/` — 仅 MCP 补充证据落盘 `data/mcp/YYYY-MM-DD/`（Morningstar/FactSet）
> - `runs/YYYY-MM-DD/` — 每次运行结果 JSON 快照
> - `backtest_seed_2026.py` / `backtest_v090.py` — walk-forward 回测脚本（验证方法有效性）
> - **日线行情已集中化**: `<workspace>/data/market/daily/<code>_<name>.csv`（见该目录 INDEX.md），所有 subagent 共享

---

## 加载协议（任何 subagent 调用时执行）

### 运行命令

```bash
# 单标的判定（含 4 只 CDMO 同业配对）— 任意股票均可
python3 .opencode/memory/personal-system/sell-ladder/sell_ladder.py --ticker 300725 --cost 36.62

# 不带同业（加速，无 pair_trading/factor-research 截面）
python3 .opencode/memory/personal-system/sell-ladder/sell_ladder.py --ticker 688256 --no-cdmo

# 任意新标的（自动 Sina 下载 900 bars → data/market/daily/<code>.csv，永久缓存；可指定同业池）
python3 .opencode/memory/personal-system/sell-ladder/sell_ladder.py --ticker 601318 --peers 601628,601601

# v2.5 权重覆盖（默认事件×2/趋势×1）
python3 .opencode/memory/personal-system/sell-ladder/sell_ladder.py --ticker 300725 --w-event 2 --w-trend 1

# 回测验证（--variant v2.0/v2.1/v2.2/v2.3/v2.4/v2.5，--w-event 权重扫描）
python3 .opencode/memory/personal-system/sell-ladder/backtest_v090.py --variant v2.5 --w-event 2 --w-trend 1
```

### 数据来源（data-priority 分层）

| 标的池 | 位置 | 来源 |
|--------|------|------|
| 任意 A 股/ETF（通用化，集中共享） | `<workspace>/data/market/daily/<code>_<name>.csv` | Sina API 自动下载（本地无则联网，落盘后永久缓存；全量清单见 `INDEX.md`） |
| 全量清单 code→名称→日期范围 | `<workspace>/data/market/daily/INDEX.md` | 迁移/加载时自动生成 |
| 旧位置 fallback（历史遗留，只读） | `.opencode/memory/personal-system/sell-ladder/data/` | 无需维护，加载器自动回退 |
| MCP 补充（Morningstar 估值/研究/FactSet） | **`data/mcp/YYYY-MM-DD/` 必须落盘** | MCP 调用结果快照（JSON/MD），密钥/原始响应不落盘 |

> 所有行情数据经 Sina API 下载后**永久保存在本地**，此后运行不再联网。
> **MCP 数据落盘纪律（用户 2026-08-10 明确要求）:** 任何从 Morningstar/FactSet MCP 获得的数据点，必须写入 `data/mcp/YYYY-MM-DD/<ticker>_<source>.json` 保存证据链，不得只存在于对话上下文。

### 输出解读（16 skill 信号矩阵）

每行 = 一个 skill 的当前信号：

| 信号 | 含义 |
|------|------|
| 🟢 +1 | 看多/动能延续 |
| ⚪ 0 | 中性/不参与判定 |
| 🔴 -1 | 看空/动能反转 |

**v2.5 分级计票信号**（决定阶段，BT-008 + BT-009 + BT-009-v25 回测定案：max=14）：

| 级别 | 信号 | 权重 |
|------|------|:---:|
| 事件信号（明确买卖点） | `candlestick`、`chanlun`、`turnover_anomaly` | **×2 票** |
| 趋势信号（方向判定） | `alpha_engine_v21`、`technical_basic`、`ichimoku`、`smc`、`alpha_zoo`、`multi_factor`、`ml_strategy`、`sector_relative` | ×1 票 |
| 辅助观察（不参与计票） | `harmonic`、`pair_trading`、`volatility`、`factor_research`、`ad_line` | 0 票 |

**v2.5 新增/重要指标:**
- **`turnover_anomaly`** (事件×2): 量比 > 1.5 + 位置 > 80% + 5d 滞涨 = 高位放量滞涨 (-1); 底部放量吸筹 (+1)
- **`sector_relative`** (趋势×1): 个股 20d 收益 vs 板块 ETF 20d 收益的差值, 持续跑输 -10%/-5%/+5% 三档 → -1/-1/0/+1
- **`ad_line`** (0 票 辅助观察): A/D Line 累积派发线, 因加权稀释主信号故降为辅助

**阶段判定规则（v2.5，max=14，含阶段 2.5 兜底）：**

| 条件 | 阶段 | 建议 |
|------|------|------|
| 得分 ≥ 9.1 (0.65·max) 且 动能结束标志 ≤1 | 阶段 1: 强动能期 | 🟢 持有 100% |
| 得分 ≥ 5.88 (0.42·max) 且 结束标志 ≤2 | 阶段 2: 动能衰减期 | 🟡 分批止盈 (减 30%) |
| 得分 < 5.88 且 动能结束标志 ≥3 共振 | 阶段 3: 动能结束期 | 🔴 大幅减仓 (减 80%) |
| 得分 < 5.88 但 结束标志 <3 | 阶段 2.5: 得分触底未共振 | 🟠 减 40% 观察（不恐慌清仓） |

**5 大动能结束标志**（任何命中都是反转预警；v2.2.1 起全部真实计算）：

| # | 标志 | 触发条件 | 实现状态 |
|---|------|----------|:---:|
| ① | 趋势破坏 | EMA(12) 跌破 + ADX<20 + ichimoku 跌穿云 | ✅ |
| ② | 动量反转 | WT1<-20 + RSI<30 持续 + 20d 动量<-10% | ✅ |
| ③ | 量能背离 | **OBV 5 日下行 + 价格 5 日新高/平台** | ✅ v2.2.1 (修复前硬编码 False) |
| ④ | 结构破坏 | smc 看空 + ichimoku 跌穿云 | ✅ |
| ⑤ | 波动率突变 | HV 100% → 30% (30 日内) | ✅ |

**判定纪律（重要，来自用户多次纠错）：**
- 强趋势（ADX>25、HV 高分位、涨幅大）中 HV 高/RSI 高是**健康特征，不是卖出信号**
- 单信号（如只有一个 skill 翻空）**不触发卖出**，必须多信号共振
- 5 动能结束标志 3+ 触发才允许"大幅减仓"（否则阶段 2.5 兜底）
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
| `alpha-researcher` | 信号有效性验证 → 用 backtest_v090.py |

---

## 当前状态 (2026-08-11)
- sell_ladder.py **v2.5 ✅**（推荐生产版本）
  - **P0 修复:** `run_sell_ladder()` 加入全部 16 信号 + `score_v22()` 防御性 + `max_score` 动态计算
  - **Stage 1 阈值 0.65·max** = 9.1（让阶段 1 可达，4/20 触发）
  - **Stage 2.5 兜底**（score<thr2 且 end<3 = 减 40% 观察，避免恐慌清仓）
  - **turnover_anomaly + sector_relative** 入事件/趋势位
  - **ad_line** 降为辅助观察（加权稀释主信号）
- **v2.5 回测 (BT-009-v25):** 20 标的跨板块完整持仓曲线
  - 区间收益: v2.5 **+0.51%** vs BH -1.15% vs MT20 -3.47%
  - **跑赢 BH 占比 75% (15/20)**；**跑赢 MT20 占比 80% (16/20)**
  - Stage 1 触发: **4/20**（v2.3 是 0/20）
  - **SUPPORTED** — v2.5 = v2.3 收益 + Stage 1 改善 + 生产可用
- **版本演进 (历史):**
  - v2.5 (BT-009-v25): SUPPORTED — 当前推荐生产版本
  - v2.4 (BT-009-v24): MIXED — P0 修复成功但 ad_line 加权稀释退步，已回退
  - v2.3 (BT-009-v23): SUPPORTED — 加 turnover + sector_relative, 无 Stage 2.5 兜底
  - v2.2 (BT-008): SUPPORTED — 7 标的 fwd20d 信号质量
  - v2.1 (BT-008): PARTIALLY_SUPPORTED — multi_factor 补位
  - v2.0 (BT-008): REJECTED — factor_research 阈值不可达
- **通用化 ✅:** 任意股票可跑（18 只持仓批量验证已通过）
- 数据: 89 个 A 股/ETF 日线集中共享在 `data/market/daily/`（300725 + 4 CDMO + 7 科技 + 金融/消费/医药/新能源 + 5 个板块 ETF）
- runs/: 2026-08-10 (BT-008~BT-009-v25) + 2026-08-11 (18 持仓批量)
- 回测: BT-008 ✅ / BT-009 ✅ / BT-009-v23 ✅ / BT-009-v24 ✅ / **BT-009-v25 ✅** (推荐)

---

*End of SKILL.md*
