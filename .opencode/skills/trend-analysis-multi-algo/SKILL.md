---
name: trend-analysis-multi-algo
description: 多算法趋势分析协议 (10 算法强制启动)。当用户要求对某只股票/资产做趋势分析 / 技术分析 / 走势判断 / 该不该买 / 该不该卖 / 形态分析 / 波浪分析 / 缠论分析 / 蜡烛图分析 / 支撑压力时加载。一次性启动 动量层(WaveTrend V21 + 技术三维投票) + 形态层(蜡烛图/缠论/艾略特波浪/谐波/图表形态) + 结构层(SMC/ICT + 一目均衡表 + 江恩)，输出信号矩阵 + 分歧分析 + 时间尺度分层 + 独立性质检。配套层(强烈建议同时跑) 为 non-price-evidence(成交量结构/资金流向/基本面/宏观 4 维度) 与 ai-hedge-fund-* 投资大佬视角(巴菲特/芒格/格雷厄姆/林奇/德鲁肯米勒 5 persona)——趋势是价格层，大佬是基本面层，两层交叉才能避免伪共识。禁止只跑单一算法(WaveTrend)就下结论。
category: strategy
---

# 多算法趋势分析协议 (trend-analysis-multi-algo)

## 为什么需要这个协议

单一趋势算法（如仅 WaveTrend 或仅均线）会系统性遗漏其它维度的信号。历史教训：2026-09-10 对光大证券的分析初版只跑了 WaveTrend + 均线，遗漏了缠论顶分型、SMC 的 BOS 熊、蜡烛图看空吞没 —— 结论偏差。

**铁律：趋势分析必须同时启动全部 10 种算法，任何单一算法的结论都不构成趋势判断。**

## 快速使用

```bash
python3 scripts/trend_analysis.py --code 601788 --market sh --start 2024-01-01
python3 scripts/trend_analysis.py --code 600519 --market sh --json-out /tmp/trend.json
python3 scripts/trend_analysis.py --csv prices.csv          # 本地数据 (date,open,high,low,close,volume)
```

| 参数 | 说明 |
|---|---|
| `--code` | 股票代码（如 601788）|
| `--market` | `sh` / `sz` / `bj` |
| `--start` / `--end` | 起止日期（默认 2024-01-01 → 今天）|
| `--csv` | 本地 CSV 路径（替代在线获取）|
| `--json-out` | 输出 JSON 路径 |

**数据源优先级：** 腾讯行情（默认，无鉴权）→ akshare → mootdx。**注意：** 腾讯 API 最多返回 ~640 根日线，WT1 会因此有约 2 点偏差（已在输出中标注）；如需精确 V21 口径，用 `--csv` 传入上市日至今的完整历史。

## 10 算法矩阵

### A. 动量层

| # | 算法 | 时间尺度 | 核心读数 | 实现 |
|---|---|---|---|---|
| A1 | **WaveTrend** | 日线(短) + 月度(长) | WT1/WT2 交叉；WT1 分位 | alpha-engine-v21 口径 **N1=50, N2=105**（周线等价），日线计算后按月采样 |
| A2 | **技术三维投票** | 中 | 趋势(EMA12/26+ADX) + 均值回归(BB+RSI) + 量价(OBV+量比) | 三维各 -1/0/+1，合成 -3~+3 |

> ⚠️ **WaveTrend 完整历史原则**：WT1 必须从上市日全历史计算，EMA 结构（N2=105）依赖长上下文。禁止截断为"最近 12 个月"。详见 `references/algorithms.md`。

### B. 形态层

| # | 算法 | 时间尺度 | 核心读数 | 实现 |
|---|---|---|---|---|
| B1 | **蜡烛图** | 短 | 15 形态（锤子/吞没/启明星/三白兵…）| TA-Lib `CDL*` 函数 |
| B2 | **缠论** | 短-中 | 分型 / 笔 / 中枢 / 买卖点 | czsc `CZSC`（分型→笔→中枢）|
| B3 | **艾略特波浪** | 中 | Zigzag swing + 5 浪推动 + 斐波那契 | 纯 pandas（滚动窗口极值 + 三大铁律）|
| B4 | **谐波形态** | 中 | XABCD（Gartley/Bat/Butterfly/Crab）| 斐波那契比率匹配 |
| B5 | **图表形态** | 中 | 头肩/双顶底/三角/楔形/通道 | **MCP `pattern_recognition`**（需 run_dir，不在脚本内）|

### C. 结构层

| # | 算法 | 时间尺度 | 核心读数 | 实现 |
|---|---|---|---|---|
| C1 | **SMC/ICT** | 短 | BOS(延续) / ChoCH(反转) / FVG(回补) / OB(机构挂单区) | smartmoneyconcepts |
| C2 | **一目均衡表** | 中 | 五线 + 云位置 + 云方向 + TK 交叉 | 纯 pandas |
| C3 | **江恩理论** | 中 | 角度线 / Square of 9 / 时间价格正方 / 7 规则 / 50% 法则 | `vibe-trading-gann` skill（`analyze_gann`）|

### D. 汇总裁决（脚本自动输出）

1. **信号矩阵**：每算法方向（▲多/▼空/―中）+ 强度（0-1）
2. **信号统计**：偏多 N / 中性 N / 偏空 N → 共识定性
3. **加权分数**：Σ(direction × strength)，>0 偏多 <0 偏空
4. **时间尺度分层**：short / mid / long 各自的净方向（避免把不同尺度的分歧误读为矛盾）
5. **独立性质检**：标注 N/N 算法均基于同一 OHLCV 序列 —— **这是同一数据的多种变换，不是独立证据**

## 与 `non-price-evidence` 交叉验证（解决伪共识）

本协议的 10 个算法全部读同一 OHLCV 序列 —— 共识度是**伪独立**。真正独立的验证来自
**`non-price-evidence` skill**（成交量结构 / 资金流向 / 基本面 / 宏观）。

```
价格分歧 + 非价格一致 → 非价格可能是领先信号
价格同向 + 非价格同向 → 提高置信度
价格同向 + 非价格矛盾 → 标注"未决"，不下结论
```

用法：`python3 .opencode/skills/non-price-evidence/scripts/fetch_evidence.py --code <code> --market <sh|sz>`

## 配套层：投资大佬基本面视角（`ai-hedge-fund-*`）

**趋势是价格层（短/中期结构），大佬是基本面层（长期质地）—— 两层互补。**

| 层 | Skill | 回答什么 | 时间尺度 |
|---|---|---|---|
| **价格层** | `trend-analysis-multi-algo`（本 skill）| 走势方向 / 支撑压力 / 形态 | 短-中 |
| **独立证据层** | `non-price-evidence` | 量能 / 资金 / 基本面数 / 宏观 | 中 |
| **基本面判断层** | `ai-hedge-fund-{buffett,munger,graham,lynch,druckenmiller}` | 生意质量 / 估值 / 拐点 | 长 |

**三层组合输出模板：**

```markdown
# <标的> 三层分析

## 一、价格层（10 算法）
<信号矩阵 + 共识/分歧 + 时间尺度>

## 二、独立证据层（4 维度）
<量能/资金/基本面数/宏观>

## 三、投资大佬层（5 persona）
| 大佬 | signal | conf | 论据 |
|---|---|---|---|

## 四、★ 三层交叉
- 价格层 X + 大佬层 Y → <结论>
- 例：价格短期偏空 + 大佬长期看空 = 一致（高置信）
- 例：价格短期偏空 + 大佬长期看多 = 分歧（回调 vs 价值，需判断哪个主导）
```

**何时跑全三层：**
- 用户说「**综合分析**」「**全栈分析**」「**投资大佬 + 趋势**」「**这家公司怎么样**」
- 单次决策涉及"买/卖/持有"且金额较大

**何时只跑价格层：**
- 用户明确只要「技术分析」「走势判断」「支撑压力」

## 输出解读规则

### 分歧 ≠ 噪声，也 ≠ 共识

- **时间尺度分层**：短期偏空 + 中期偏多 = "回调中的上升趋势"，不是矛盾
- **独立性质检**：9 个算法都读同一价格序列 → 共识度高只说明"价格结构在某方向清晰"，**不代表预测可靠**。真正的独立验证需成交量/资金流/基本面/宏观等非价格维度。

### 与个人交易系统的衔接

| 系统文件 | 衔接点 |
|---|---|
| `1.LAWS.md` LAW-001 | WT1 ≥+60 动量延续 / ≤-60 低 WT1 非反转 —— **只在极端区提供信号**，灰色区间（-60~+60）不触发 |
| `7.SELL_LADDER.md` | 缠论顶分型 + SMC ChoCH + 蜡烛图看空 = 卖出梯子的"动能结束"证据 |
| `8.BUY_LADDER.md` | 缠论底分型 + SMC 看涨 OB + 艾略特 5 浪完成 = 买入梯子的"击球区"证据 |
| `4.BROKER_OBSERVATION.md` | 券商股需额外查板块指标（中信 PB / 两融 / 成交量）|
| `memory-protocol.md` | 方向性结论必须做 5-Why 反方；回复只附 Why 5 一句 |

## 依赖

```bash
pip install pandas numpy requests
pip install TA-Lib            # 蜡烛图 (CDL*)
pip install czsc              # 缠论
pip install smartmoneyconcepts # SMC
pip install pyharmonics       # 谐波 (可选, 脚本内含 fallback)
# 江恩: 复用 .opencode/skills/vibe-trading-gann/examples/spcx_analysis.py (无额外依赖)
pip install akshare mootdx    # 数据源 fallback
```

## 常见陷阱

1. **索引类型**：脚本内部 df 用 RangeIndex，所有日期访问走 `df["date"]`，不要假设 index 是 datetime
2. **月度 WT 口径**：V21 是"日线算 WT 后按月采样"，**不是**在月线序列上重算 —— 后者会因 EMA 长度不足产生 980 之类的失真值
3. **腾讯 640 根上限**：长历史会截断，WT1 有 ~2 点偏差；精确场景用 `--csv`
4. **czsc API 版本**：0.10.x 的 `ZS(bis)` 返回**单个**中枢对象（非列表），脚本用"3 笔重叠"手动检测
5. **图表形态 B5**：脚本不含，需另行调用 MCP `pattern_recognition`（要求 `run_dir/artifacts/ohlcv_*.csv`）
6. **谐波形态**：多数时候无当前形态（这是正常的，不是 bug）

## 输出示例

```
信号统计: 偏多 2 / 中性 5 / 偏空 2  →  中性/分歧
加权分数: -0.27   时间尺度: {'short': -1, 'long': 0, 'mid': 1}

[―中] WaveTrend 日线   wt1: -31.26  wt2: -31.35  金叉/多头
[▲多] 艾略特波浪       看跌推动浪完成 (5浪下跌 → 潜在见底)
[▼空] 缠论            顶分型 @ 2026-09-04 (14.78); 中枢内 [14.15, 14.78]
[▼空] SMC/ICT        last_bos: 2026-07-27 bear @ 14.15
[―中] 一目均衡表       价格云内; 云带 bull; TK bull
```

## 完整算法细节

见 `references/algorithms.md` — 每个算法的公式、参数、信号逻辑、失效条件。
