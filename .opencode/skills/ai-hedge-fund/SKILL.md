---
name: ai-hedge-fund
description: AI Hedge Fund (ai-hedge-fund / aihf) 框架总入口。多智能体对冲基金模拟器——5 位投资人 persona (Buffett/Munger/Graham/Lynch/Druckenmiller) + PEAD 系统模型，按 FUND > STRATEGY > MODEL 三层组合成 mandate，产出 Signal (conviction ∈ [-1,+1] + reasoning)。当用户问"**投资大佬**"、"**各位大佬**"、"**投资大师**"、"投资人视角"、"gurus"、"用 ai-hedge-fund 分析"、"多智能体对冲基金"、"aihf"、"fund mandate"、"desk 模拟"时加载。单独的投资人视角请用 ai-hedge-fund-buffett / -munger / -graham / -lynch / -druckenmiller；具体 mandate 用 ai-hedge-fund-deep-value / -earnings-drift / -fundamental-ls / -inflections。
category: analysis
---

# AI Hedge Fund — 多智能体对冲基金框架

> 上游：`github.com/virattt/ai-hedge-fund`（本地 `~/Documents/source_code/ai-hedge-fund`）
> 性质：研究/模拟。**不构成投资建议**；persona 是对公开投资哲学的**风格化近似**，不是本人、非背书。

## 一、三层架构

```
FUND      = 资本切片 over STRATEGIES（master risk 作用于净额账本）
  └─ STRATEGY = 混合策略 over MODELS（一个"pod"）
       └─ MODEL = alpha model → Signal
```

| 层 | 定义 | 本仓位置 |
|---|---|---|
| **FUND** | capital / risk / rebalance cadence / benchmark | `fund/*.yaml`（mandate）|
| **STRATEGY** | models + blend policy（conviction_weighted / market_neutral）| `strategies/*.yaml` |
| **MODEL** | 产生 Signal 的 alpha model | `signals/*.py` |

**两种 MODEL：**
- **LLM investor AGENT**（discretionary pod）— 身份 = 谁在 desk（persona system prompt）
- **Quant MODEL**（systematic pod）— 身份 = 它收割的 edge（纯数学）

## 二、Signal 契约

所有 alpha model 实现同一接口，产出 `Signal`：

```python
class Signal(BaseModel):
    model_name: str      # 'pead' / 'buffett' / ...
    ticker: str
    date: str            # as-of（YYYY-MM-DD），必须 point-in-time
    value: float         # conviction ∈ [-1.0, +1.0]
    reasoning: str | None
    metadata: dict       # signal / confidence / model / abstained / ...
```

**关键纪律：**
- **Point-in-time**：只能用 date ≤ as_of 的数据（无 lookahead）
- **Abstain**：数据不足 → `value=0.0, metadata.abstained=True`（不猜）
- **数据层错误 propagate**（fail loud），不静默变 neutral

## 三、5 位投资人 persona（各自 skill）

| persona | 流派 | 核心判据 | Skill |
|---|---|---|---|
| **Buffett** | 长期生意所有者 | 护城河 / 管理层资本配置 / 低负债 / 公允价格 | `ai-hedge-fund-buffett` |
| **Munger** | 质量 + 公允价格（严苛）| 反向思考 / 多年一致性 / 太难堆 | `ai-hedge-fund-munger` |
| **Graham** | 安全边际（防御型）| P/E≤15-20 / P/B / 流动比率>1.5 / 盈利稳定 | `ai-hedge-fund-graham` |
| **Lynch** | GARP | 分类（fast grower/stalwart/…）/ PEG / 故事清晰 | `ai-hedge-fund-lynch` |
| **Druckenmiller** | 拐点 + 不对称 | 营收/利润率的**变化率** / 定价了什么 / 只在下重注时出手 | `ai-hedge-fund-druckenmiller` |

## 四、4 个 mandate（各自 skill）

| mandate | 组合 | 特征 | Skill |
|---|---|---|---|
| **deep-value** | graham(2.0) + buffett + munger | 长期偏多，Graham 主导 | `ai-hedge-fund-deep-value` |
| **earnings-drift** | pead | 系统化，事件时间 | `ai-hedge-fund-earnings-drift` |
| **fundamental-ls** | 全部 5 位 | 旗舰，市场中性多空 | `ai-hedge-fund-fundamental-ls` |
| **inflections** | druckenmiller + lynch | 基本面变化率多空 | `ai-hedge-fund-inflections` |

## 五、数据契约（FundamentalsSnapshot）

persona 只吃一个 point-in-time 快照（`features/snapshot.py`）：

| 字段 | 含义 |
|---|---|
| `ticker` / `as_of` / `sector` / `industry` | 标的 + 时点 |
| `periods[]` | 每期 TTM：market_cap / P/E / ROE / gross_margin / operating_margin / net_margin / D/E / current_ratio / revenue_growth / EPS / BVPS / FCF-share |
| 派生 | `roe_avg` / `net_margin_avg` / `gross_margin_trend` / `bvps_cagr` / `debt_to_equity_latest` / `market_cap_latest` |

**最少 4 期**（`MIN_PERIODS=4`）否则 `InsufficientData`。

**本地数据适配器 v2**（无需 aihf / API key）：
```bash
python3 scripts/build_snapshot.py --code 601788 --market sh --render   # A股 (东财 165 字段)
python3 scripts/build_snapshot.py --code 601788 --market sh --cumulative  # 累计口径 (默认 TTM)
python3 scripts/build_snapshot.py --code 601788 --json-out /tmp/s.json
```
输出格式与上游 `FundamentalsSnapshot.render()` 一致，可直接喂给 persona。

**v2 vs v1（2026-09-10 升级）：**
| | v1 | **v2** |
|---|---|---|
| 数据源 | `RPT_LICO_FN_CPD` (37 字段) | **`RPT_F10_FINANCE_MAINFINADATA` (165 字段)** |
| 口径 | 累计 (YTD) | **TTM (滚动 12 月)** |
| 映射字段 | ~18 | **36** |
| `debt_to_equity` | ❌ n/a | ✅ `CQBL` (产权比率) |
| `price_to_book` | ❌ n/a | ✅ 计算 |
| `market_cap` | ⚠️ 间歇 (push2) | ✅ `TOTAL_SHARE × 最新价` |
| `operating_margin` | ❌ n/a | ✅ `OPERATE_PROFIT_PK / 收入` |
| 单季度动能 | ❌ | ✅ `DJD_*` (Druckenmiller 拐点) |
| 金融企业专属 | ❌ | ✅ 资本杠杆率/LCR/净稳定资金率 |

**口径纪律（重要）：** v1 用累计 EPS 算 P/E（H1 的 0.44）会把 P/E 高估一倍（32.68）；v2 用 TTM EPS（0.85）得 16.94 —— **对 Graham 的 P/E≤20 判据是决定性的**。

## 六、CLI 用法（如已装 aihf）

```bash
pipx install aihf          # 或 uv tool install aihf
aihf                       # 交互式 app
aihf ~/.hedge-fund/mandates/example.yaml --tickers AAPL,MSFT            # 跑一轮
aihf ~/.hedge-fund/mandates/example.yaml --tickers AAPL,MSFT --backtest # 回测
```

**API keys**（首次需要时提示，存 `~/.hedge-fund/.env`）：
- Financial Datasets API key（价格/基本面/财报）
- 一个 LLM API key（Anthropic / OpenAI / DeepSeek / Google / xAI / Kimi）

> ⚠️ 本仓当前 **未安装 aihf**。没有 key 时，用 §五 的本地适配器 + persona skill 直接应用（agent 自身即 LLM）。

## 六·五、★「投资大佬」聚合工作流（最易用入口）

> **用户说「投资大佬」「各位大佬」「投资大师」「投资人视角」时 → 一次性给出全部 5 位观点。**

**三步：**

1. **构建一次快照**（5 位 persona 共享同一 `FundamentalsSnapshot`，只需一次）
   ```bash
   python3 scripts/build_snapshot.py --code <code> --market <sh|sz> --render
   ```
2. **对同一快照应用 5 个 persona**（各自 skill 内含逐字 system prompt + 判据）
   | persona | skill | 首要判据 |
   |---|---|---|
   | Buffett | `ai-hedge-fund-buffett` | 护城河 / 管理层 / 公允价格 |
   | Munger | `ai-hedge-fund-munger` | 反向思考 / 多年一致性 / 太难堆 |
   | Graham | `ai-hedge-fund-graham` | 安全边际 / P/E≤20 / 财务强度 |
   | Lynch | `ai-hedge-fund-lynch` | 分类 / PEG / 故事清晰 |
   | Druckenmiller | `ai-hedge-fund-druckenmiller` | 变化率 / 拐点 / 不对称 |
3. **输出共识/分歧表**（关键交付物）

**输出模板：**

```markdown
# 投资大佬视角：<标的>（<代码>）
> 数据快照：<TTM 口径> | P/E <x> | P/B <x> | ROE <x>% | D/E <x>

| 大佬 | signal | conf | 一句话论据 |
|---|---:|---:|---|
| 巴菲特 | bullish/bearish/neutral | 0-100 | ... |
| 芒格 | ... | ... | ... |
| 格雷厄姆 | ... | ... | ... |
| 林奇 | ... | ... | ... |
| 德鲁肯米勒 | ... | ... | ... |

## 共识
<N 位看多 / N 位看空 / N 位中性> — <共同点>

## 分歧（★ 最有价值）
<谁 vs 谁，分歧点是什么> → 精确定位决策依赖的假设

## 组合 mandate 视角
- deep-value (graham×2+buffett+munger): <sleeve_score>
- inflections (druckenmiller+lynch): <sleeve_score>
```

**为什么分歧最有价值：** 两位 persona 给出相反信号**不是 bug** —— 它告诉你"这个决策依赖哪个假设成立"。例如价值派看空（低 ROE、无护城河）而拐点派看多（营收/净利率加速）→ 你面对的是"**基本面在改善但质地平庸**"的标的，决策取决于你赌"改善能否持续"。

## 七、如何用（无 aihf 时）

1. **构建快照**：`python3 scripts/build_snapshot.py --code <code> --market <sh|sz> --render`
2. **选 persona 或 mandate**：见 §三/§四
3. **应用**：加载对应 skill，把快照喂给 persona system prompt，产出 `{signal, confidence, reasoning}`
4. **组合**（mandate）：按 mandate 的 models + weights 混合，`conviction_weighted` 加权

## 七·五、配套层：趋势 + 独立证据（反向交叉）

**大佬是基本面层（长期），趋势是价格层（短/中期）—— 两层互补。**

| 层 | Skill | 回答 |
|---|---|---|
| 基本面层 | 本 skill（`ai-hedge-fund-*`）| 生意质量 / 估值 / 拐点 |
| 价格层 | `trend-analysis-multi-algo` | 走势 / 支撑压力 / 形态 |
| 独立证据层 | `non-price-evidence` | 量能 / 资金 / 宏观 |

**组合用法：** 用户说「综合分析」「全栈分析」「投资大佬 + 趋势」时，三层都跑。

**★ 最有价值的输出是分歧：**
- 大佬看多（基本面改善）+ 趋势看空（价格弱势）→ "改善未被市场认知" 或 "价格领先基本面恶化"，需判断
- 大佬看空（质地平庸）+ 趋势看多（价格强势）→ "情绪驱动的反弹" vs "拐点确认"

## 八、诚实边界

- persona 是**风格化近似**（VISION.md 明示非本人、非背书）
- Druckenmiller persona **只有基本面数据**（无宏观/利率/价格）—— 它自己在 prompt 里承认
- 快照是 **TTM 基本面**，不含新闻/情绪/技术面
- **不产生交易指令** —— 只产 Signal（view），仓位由组合构建决定

## 九、references

- `references/personas.md` — 5 位 persona 完整 system prompt + 判据对照
- `references/mandates.md` — 4 个 mandate 完整 spec + 混合规则
