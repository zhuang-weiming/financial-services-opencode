# Skill Manifest — 全量 skill 自动清单

> **自动生成，请勿手工编辑。** 重新生成：`python3 .opencode/scripts/gen_skill_manifest.py`
> 共 **194** 个 skill（vibe-trading 90 / llmquant 25 / 其他 79）（另有 1 个损坏/无 SKILL.md 目录未计入）

## 使用方式（给 wealth-guide 及 subagent）

**用户不需要记住 skill 名。** 路由流程：
1. 用户表达**意图**（如「分析这只股票的趋势」「查一下 FRED 的 CPI」）
2. wealth-guide 按意图匹配下方清单的 `description` → 选定 subagent
3. subagent 用 `skill("<name>")` 加载对应 skill

> 本清单是**发现层**（有什么可用）；`wealth-guide-router.md` 是**决策层**（意图 → subagent 的权威映射）。两者互补：清单保证零遗漏，路由表保证高质量。

---

## Vibe-Trading Skills (90)

| skill | description |
|---|---|
| `vibe-trading-adr-hshare` | ADR/H-share/A-share cross-listing premium analysis — track pricing gaps between US-listed ADRs, HK-listed H-shares, and A-shares for arbitrage signals, dual-... |
| `vibe-trading-akshare` | AKShare financial data aggregator (18k+ stars). Free, no API key. Covers A-shares, US, HK, futures, macro, forex. Primary fallback for tushare and yfinance. |
| `vibe-trading-alpha-zoo` | Browse and bench the bundled alpha zoos — prebuilt cross-sectional factor libraries (Kakushadze 101, GTJA 191, Qlib 158, Fama-French / Carhart). Use when the... |
| `vibe-trading-ashare-pre-st-filter` | A 股 ST/*ST 风险预测框架 — 基于最新中报/三季报或业绩预告/快报，预测下一财年是否会因营收、利润、净资产、分红不达标而被风险警示，并将新浪监管处罚记录作为独立证据面纳入风险等级。仅适用于 A 股，不预测财务造假。 |
| `vibe-trading-asset-allocation` | Asset allocation theory and optimizer usage — MPT / Black-Litterman / risk budgeting / all-weather strategy, including guides for 5 optimizers and rebalancin... |
| `vibe-trading-backtest-diagnose` | Diagnose failed or underperforming backtests, locate the root cause, and fix the issue |
| `vibe-trading-behavioral-finance` | Behavioral finance applications: theories of overreaction and underreaction, behavioral explanations for momentum and reversal, investor sentiment cycles, co... |
| `vibe-trading-bottleneck-hunter` | Supply-chain bottleneck arbitrage. Given a super-trend (AI infra, energy transition, defense, semiconductor reshoring, space economy), decompose its physical... |
| `vibe-trading-candlestick` | Candlestick pattern recognition engine, pure pandas vectorized implementation of 15 classic candlestick patterns (5 single-candle + 5 double-candle + 4 tripl... |
| `vibe-trading-ccxt` | CCXT unified crypto exchange library (100+ exchanges). Free public market data. Fallback when OKX is unavailable. |
| `vibe-trading-chanlun` | 基于缠论（缠中说禅）的形态识别引擎，使用czsc库自动检测K线分型、笔、中枢，并生成一买/一卖/二买/二卖/三买/三卖等买卖点信号。支持多周期分析和形态分类（3/5/7/9/11笔形态）。 |
| `vibe-trading-commodity-analysis` | Commodity analysis (oil supply-demand balance / gold pricing / copper as an economic predictor / inventory cycles / futures premium-discount structure / seas... |
| `vibe-trading-convertible-bond` | A股可转债分析——转股/纯债/期权三维估值、下修/强赎/回售博弈、双低策略与转债轮动选债框架 |
| `vibe-trading-corporate-events` | 公司事件驱动分析：并购套利价差计算、大股东增减持信号、股权激励解读、定增配股影响评估、A股ST/退市预警 |
| `vibe-trading-correlation-analysis` | Correlation and cointegration analysis — co-movement discovery, deep return-correlation analysis, sector clustering, realized correlation, Engle-Granger / Jo... |
| `vibe-trading-correlation-regime` | Correlation-regime detection and crisis attribution — edge-density regime states with hysteresis, causal (no look-ahead) smoothing, regime-aware exposure con... |
| `vibe-trading-credit-analysis` | 固收与信用分析：信用债评级、利差分析、违约风险评估、城投债研究、可转债定价与策略。 |
| `vibe-trading-cross-market-strategy` | Write signal_engine.py for portfolios spanning multiple markets (A-shares + crypto, equity + forex, etc.) |
| `vibe-trading-crypto-derivatives` | Crypto-derivatives strategies — perpetual funding-rate arbitrage, futures term-structure contango/backwardation trading, and option volatility-smile / Greeks... |
| `vibe-trading-data-routing` | The single ROUTER for every data need. Load this skill BEFORE any backtest, data-fetch, or research task to pick the best available source/tool, honour auth ... |
| `vibe-trading-deep-company-series` | Write a publication-grade 8-part deep-dive series on a single company (~120k words total): cognitive reset / moat / profit engine / hidden assets / era varia... |
| `vibe-trading-defi-yield` | DeFi yield analysis and optimization — lending rates, LP yields, staking returns, yield farming strategies, risk-adjusted yield comparison, and protocol-leve... |
| `vibe-trading-dividend-analysis` | Dividend stock analysis for income, dividend-growth, and shareholder-return strategies, including yield quality, payout sustainability, ex-dividend mechanics... |
| `vibe-trading-doc-reader` | Read any common document/data file — PDF, Word (.docx), Excel (.xlsx/.xls), PowerPoint (.pptx), images (OCR), CSV/TSV, plain text, JSON/YAML/TOML, HTML/XML, ... |
| `vibe-trading-earnings-forecast` | 盈利预测与一致预期分析（自上而下/自下而上预测法/SUE/PEAD/分析师预期修正），捕捉业绩超预期交易机会。 |
| `vibe-trading-earnings-revision` | Earnings estimate revisions, guidance analysis, and post-earnings drift (PEAD) — track analyst consensus changes, earnings surprise patterns, and management ... |
| `vibe-trading-eastmoney` | 东方财富（Eastmoney）免费免鉴权数据接口，覆盖资金流向、龙虎榜、融资融券、大宗交易、股东户数、限售解禁、行业概念板块、券商研报、财经新闻、A股/港股三大报表+主要指标、全市场选股与代码搜索；美股财报由 get_financial_statements 转 SEC EDGAR。东财请求经共享 IP 限速层节... |
| `vibe-trading-edgar-sec-filings` | SEC EDGAR filing analysis — 10-K, 10-Q, 8-K, proxy statements, insider Form 4. Extract key financials, risk factors, management discussion, and generate inve... |
| `vibe-trading-elliott-wave` | Elliott Wave Theory signal engine. Detects swing points through Zigzag, matches 5-wave impulse and 3-wave corrective structures, validates them with Fibonacc... |
| `vibe-trading-etf-analysis` | ETF分析：产品筛选、费率对比、跟踪误差、流动性评估、策略应用与中国市场ETF量化配置框架。 |
| `vibe-trading-event-driven` | Event-driven strategy based on sentiment-scored signals from news, announcements, and macro events. The LLM acts as the NLP engine, and event data follows a ... |
| `vibe-trading-execution-model` | Trade execution modeling (backtest only) — slippage formulas (linear / square-root impact), VWAP/TWAP execution logic, market-impact cost estimation, and exe... |
| `vibe-trading-factor-research` | Factor research framework with IC/IR analysis, quantile backtesting, and factor combination. Suitable for cross-sectional factor evaluation across multiple i... |
| `vibe-trading-financial-statement` | 财报三表深度解读——三表勾稽关系、盈利质量(应计vs现金流)分析、杜邦分解、10+财务造假红旗指标 |
| `vibe-trading-fund-analysis` | 基金分析与筛选：晨星评级/夏普比率/信息比率、Sharpe风格箱分析、风格漂移检测、基金经理评价、FOF组合构建、ETF选择 |
| `vibe-trading-fundamental-filter` | Fundamental factor screening — filter stocks by PE/PB/ROE, financial statement fields, and other metrics for value or growth selection. Supports A-shares (vi... |
| `vibe-trading-gann` | 江恩理论 (W.D. Gann) 分析引擎 — 角度线(1×1/2×1/1×2)、Square of 9 (价格平方根增量)、时间价格正方 (Time-Price Squaring)、7 规则周期、50% 法则。纯 pandas/math 实现，适用于任意 OHLCV。当用户问"江恩"/"Gann"/"角度线"/... |
| `vibe-trading-geopolitical-risk` | Geopolitical risk analysis: quantify crisis signals, identify precursors, and build event-driven strategies for war, sanctions, and supply disruption scenarios. |
| `vibe-trading-global-macro` | Global macro analysis framework (central bank policy transmission / FX forecasting / geopolitical risk / capital flows), used to build macro factor signals t... |
| `vibe-trading-harmonic` | Harmonic Patterns signal engine. Identifies XABCD five-point structures such as Gartley/Bat/Butterfly/Crab based on Fibonacci geometry, and generates trading... |
| `vibe-trading-hedging-strategy` | Hedging strategy design (beta hedge / option protection / tail risk / cross-asset hedging), including hedge-ratio calculation and cost evaluation. |
| `vibe-trading-hk-connect-flow` | Stock Connect (Shanghai/Shenzhen-Hong Kong) fund flow analysis — Northbound (foreign into A-shares), Southbound (mainland into HK), sector allocation trackin... |
| `vibe-trading-ichimoku` | Ichimoku Kinko Hyo five-line system signal engine. A standalone Japanese technical-analysis school that generates trading signals from Tenkan/Kijun crossover... |
| `vibe-trading-investor-lenses` | Named investor reasoning frameworks packaged as reusable analytical lenses — 12 lenses (deep value, quality franchise, inversion, scuttlebutt growth, GARP, c... |
| `vibe-trading-liquidation-heatmap` | Liquidation level analysis and heatmap interpretation — identify leveraged position concentration, liquidation cascades, stop-hunt zones, and use liquidation... |
| `vibe-trading-macro-analysis` | Macroeconomic cycle positioning and central-bank policy interpretation, including GDP/CPI/PMI/rates/FX analysis, with output in the form of major-asset alloc... |
| `vibe-trading-management-deep-dive` | Deep management assessment — the 'buying a stock is buying a person' layer. For a company or a named executive, evaluate integrity (promise-vs-delivery track... |
| `vibe-trading-market-microstructure` | Market microstructure: bid-ask spread analysis, order-flow toxicity metrics (VPIN / Kyle lambda), liquidity measures (Amihud / Roll), price-impact models, li... |
| `vibe-trading-minute-analysis` | Minute-level data analysis and backtesting. Retrieves minute candlesticks through OKX/Tushare/yfinance and can be used both for analysis and as input to the ... |
| `vibe-trading-ml-strategy` | Machine-learning predictive strategy based on sklearn walk-forward training, feature engineering, and signal generation. Suitable for any OHLCV data. |
| `vibe-trading-mootdx` | Mootdx A-share market data via TCP-direct 通达信 servers. Free, no API key, no IP rate limits. Use as the stable A-share OHLCV fallback when akshare's East Mone... |
| `vibe-trading-multi-factor` | Multi-factor cross-sectional stock ranking. Combines factor standardization, equal-weight or IC-weighted scoring, and TopN portfolio construction. Suitable f... |
| `vibe-trading-okx-market` | OKX cryptocurrency market data interface. Uses the OKX V5 REST API to retrieve spot, derivatives, index, and other crypto market data, including real-time pr... |
| `vibe-trading-onchain-analysis` | On-chain data analysis — active addresses / whale tracking / TVL / DEX liquidity, interpretation and signal generation using on-chain valuation metrics such ... |
| `vibe-trading-options-advanced` | Advanced options strategies: volatility-surface modeling (SABR / Local Vol), dynamic Greeks rebalancing, calendar spreads, volatility arbitrage and skew trad... |
| `vibe-trading-options-payoff` | Option P&L analysis methodology: payoff diagrams, breakeven calculation, multi-leg strategy visualization, and Greeks-based scenario analysis. |
| `vibe-trading-options-strategy` | Options strategy framework supporting Black-Scholes pricing, Greeks analysis, and multi-leg backtesting. Suitable for cryptocurrency and equity options. |
| `vibe-trading-pair-trading` | Pair trading strategy. Trades mean reversion using the spread/ratio Z-score of two correlated instruments. Requires at least two instruments. |
| `vibe-trading-performance-attribution` | Performance attribution analysis — Brinson sector/stock-selection attribution, factor alpha/beta decomposition, market-timing evaluation, and benchmark compa... |
| `vibe-trading-perp-funding-basis` | Perpetual futures funding rate analysis and cash-carry basis trading — funding rate regimes, annualized basis signals, carry trade construction, and funding ... |
| `vibe-trading-pine-script` | Export backtest strategies to indicator/strategy code for major trading platforms — TradingView, 通达信, 同花顺, 东方财富, MT5. |
| `vibe-trading-private-company-research` | Deep research framework for pre-IPO / private companies (Ant Group, SpaceX, Stripe, ByteDance...). Six analyst lenses — business model, financial forensics, ... |
| `vibe-trading-quant-statistics` | Quantitative statistical methods: ADF unit-root / cointegration tests, GARCH volatility modeling, regression diagnostics (heteroskedasticity / autocorrelatio... |
| `vibe-trading-qveris` | Paid capability marketplace for global multi-asset data; use it when free Vibe-Trading sources lack coverage, depth, or provider quality, and keep free sourc... |
| `vibe-trading-regulatory-knowledge` | 金融监管知识库：A股涨跌停/ST退市新规/融券、港股T+0/做空机制、美股PDT/熔断、加密监管政策、跨境税务基础 |
| `vibe-trading-report-generate` | Professional financial research report generation — standard structure (summary / views / main body / risks / recommendation), Markdown formatting standards,... |
| `vibe-trading-research-discipline` | A short self-bias checklist to run at the START of any investment research task (stock screen / sector study / company deep-dive). Four biases that systemati... |
| `vibe-trading-research-goal` | Goal-driven finance research workflow: attach a research-only objective, track criteria, and add evidence while avoiding live trading execution. |
| `vibe-trading-risk-analysis` | Risk measurement and stress testing — VaR/CVaR/max drawdown calculation, Monte Carlo simulation, extreme-value tail-risk analysis, and historical scenario st... |
| `vibe-trading-seasonal` | Seasonal/calendar-effect strategy. Generates trading signals from time-based patterns such as month-of-year effects and day-of-week effects. Suitable for any... |
| `vibe-trading-sec-edgar` | U.S. SEC EDGAR fetch interface — resolve a ticker to its CIK, list recent filings (10-K / 10-Q / 8-K and friends) with primary-document URLs, and pull XBRL c... |
| `vibe-trading-sector-rotation` | 行业轮动分析——申万行业景气度评分、行业动量排名、产业链传导、估值/盈利/资金流多维比较框架 |
| `vibe-trading-sentiment-analysis` | 市场情绪分析——恐贪指数/Put-Call Ratio/融资融券/北向资金信号解读、社交媒体舆情量化框架 |
| `vibe-trading-shadow-account` | Shadow Account — 从用户交割单提炼盈利模式（3-5 条人话规则）→ 跨 A股/港股/美股/crypto 多市场回测 → 差值归因 → 8-section PDF 报告。叙事：你的影子，没有情绪噪音。 |
| `vibe-trading-smc` | Smart Money Concepts (ICT) signal engine. Uses the smartmoneyconcepts library to implement institutional-trading-school analysis of BOS, ChoCH, FVG, and orde... |
| `vibe-trading-social-media-intelligence` | Social media intelligence: financial signal extraction from Twitter/X, Telegram, Discord, and Reddit for sentiment-driven trading strategies. |
| `vibe-trading-stablecoin-flow` | Stablecoin supply and flow analysis — USDT/USDC mint-burn signals, exchange stablecoin reserves, on-chain stablecoin velocity, and capital rotation indicator... |
| `vibe-trading-strategy-dev-manager` | Strategy Development Manager: convert academic papers and research reports into validated factors and strategies with automated backtesting, persistent stora... |
| `vibe-trading-strategy-discovery` | Strategy Discovery: evidence-gated facade over Alpha Zoo + the SDM strategy store — answers what strategies exist and what state they are in, with per-regime... |
| `vibe-trading-strategy-generate` | Create, modify, and optimize quantitative trading strategies, then backtest and evaluate them. |
| `vibe-trading-technical-basic` | Core technical indicator collection (trend EMA/ADX + mean-reversion BB/RSI + volume-price OBV/volume ratio), generates a composite signal via three-dimension... |
| `vibe-trading-token-unlock-treasury` | Token unlock schedule analysis and project treasury tracking — vesting cliffs, linear unlocks, team/investor/ecosystem token releases, treasury diversificati... |
| `vibe-trading-trade-journal` | Analyze a user's trade journal (CSV/Excel broker export). Parses 同花顺/东方财富/富途/generic formats, produces a trading profile and 4 behavior diagnostics (disposit... |
| `vibe-trading-tushare` | tushare是一个财经数据接口包，拥有丰富的数据内容，如股票、基金、期货、数字货币等行情数据，公司财务、基金经理等基本面数据。该模块通过标准化API方式统一了数据资产的对外服务方式，以帮助有需要的技术用户更实时、简洁、轻量的使用相关数据。 |
| `vibe-trading-us-etf-flow` | US ETF fund flow analysis, sector rotation breadth, and style factor flows — track institutional capital movement via ETF creation/redemption, sector breadth... |
| `vibe-trading-valuation-model` | Valuation methodology — absolute valuation with DCF / DDM / SOTP, relative valuation with PE-Band / PB-ROE / EV-EBITDA, sensitivity analysis, and valuation-t... |
| `vibe-trading-vnpy-export` | Export a Vibe-Trading backtest strategy to a runnable vnpy CtaTemplate Python class — supports A-share equities, futures, and crypto via BarGenerator + Array... |
| `vibe-trading-volatility` | Volatility strategy. Trades mean reversion based on percentile ranking of historical volatility (HV). Suitable for any OHLCV data. |
| `vibe-trading-web-reader` | Read web pages, articles, and document links by converting URLs into Markdown text. Use the `read_url` tool directly, without bash. Sends the full URL to the... |
| `vibe-trading-yfinance` | yfinance global market data interface — retrieve OHLCV and research data for US, HK, and Canadian stocks, ETFs, and indices via Yahoo Finance. Free, no API k... |

## LLMQuant Skills (25)

| skill | description |
|---|---|
| `llmquant-commodities` | Router skill for LLMQuant commodities workflows. Use when the user needs commodity spot, futures curve, inventory, roll yield, or macro linkage analysis. |
| `llmquant-credit` | Router skill for LLMQuant credit workflows. Use when the user needs issuer credit review, spread regime analysis, high-yield stress monitoring, default risk,... |
| `llmquant-crypto` | Router skill for LLMQuant crypto workflows. Use when the user needs crypto market regime analysis, token research, perpetual funding, basis, leverage, liquid... |
| `llmquant-data` | llmquant-data MCP — Tier-1 institutional data layer covering US equity OHLCV (stocks + crypto), ETF holdings (SEC N-PORT), FRED macro indicators, AI-summariz... |
| `llmquant-equities` | Router skill for LLMQuant equities workflows. Use when the user needs stock analysis, equity comparison, research memos, merger-arb memos, or sell/take-profi... |
| `llmquant-equity-derivatives` | Router skill for LLMQuant equity derivatives workflows. Use when the user needs single-stock derivative, convertible, warrant, structured payoff, or hybrid s... |
| `llmquant-etfs` | Router skill for LLMQuant ETFs workflows. Use when the user needs ETF holdings, overlap, concentration, issuer snapshot, or theme exposure analysis. |
| `llmquant-events` | Router skill for LLMQuant event workflows. Use when the user needs earnings event briefs, M&A tracking, regulatory risk, catalysts, event calendars, or cross... |
| `llmquant-funds` | ETF fund identity + holdings via the llmquant-data MCP. Fund lookup (issuer, AUM, expense, top-10) and full holdings (SEC N-PORT, latest quarterly snapshot).... |
| `llmquant-investor-lenses` | Router skill for LLMQuant investor-lens workflows. Use when the user wants an investor-style reasoning overlay grounded in LLMQuant Data evidence. |
| `llmquant-macro` | FRED-backed macro indicator data via the llmquant-data MCP. Search ~50 curated U.S. series (CPI, Fed Funds, unemployment, NFCI, yield curve, PCE, …), fetch l... |
| `llmquant-market-data` | Crypto spot + US equity OHLCV via the llmquant-data MCP. Crypto snapshots (BTC/ETH/SOL/…), crypto daily/4h/1h/1w klines, US equity daily bars, US equity 1h i... |
| `llmquant-market-intelligence` | Router skill for LLMQuant market-intelligence workflows. Use when the user needs macro views, market sentiment dashboards, or event probability signals. |
| `llmquant-news` | AI-summarized company announcements (earnings, M&A, guidance, leadership, etc.) via the llmquant-data MCP. Browse by ticker, event type, or topic. Use for po... |
| `llmquant-options` | Router skill for LLMQuant options workflows. Use when the user needs IV rank, option scoring, strategy construction, Greeks, P&L simulation, volatility surfa... |
| `llmquant-personal` | Read-only access to the user's saved LLMQuant Dashboard profile (risk preference, horizon, base currency, notes) and holdings (symbols, quantities, market va... |
| `llmquant-polymarket` | Polymarket finance-scoped prediction markets via the llmquant-data MCP. Search events, browse by tag/status, read event cards, read individual markets, fetch... |
| `llmquant-portfolio` | Router skill for LLMQuant portfolio workflows. Use when the user needs company profiles, thesis tracking, theme research, watchlist monitoring, or alert mana... |
| `llmquant-portfolio-lab` | Router skill for LLMQuant portfolio-lab workflows. Use when the user needs portfolio exposure maps, what-if simulations, scenario states, or virtual portfoli... |
| `llmquant-prediction-markets` | Router skill for LLMQuant prediction-market workflows. Use when the user needs event odds, settlement criteria, probability gaps, cross-market pricing, or pr... |
| `llmquant-rates-fx` | Router skill for LLMQuant rates and FX workflows. Use when the user needs yield curve, duration, central-bank divergence, FX carry, real-rate, dollar, or cro... |
| `llmquant-research` | Knowledge bases for finance methodology — arxiv papers (English, structured by section) and a zh-leaning finance concept wiki. Use for "find a paper on X", "... |
| `llmquant-risk` | Router skill for LLMQuant risk workflows. Use when the user needs fear scoring, VIX regime, hedge design, or research health checks. |
| `llmquant-sec` | SEC institutional ownership (13F) + filing text extraction (10-K / 10-Q / 8-K) via the llmquant-data MCP. Top-1,000 manager rosters, per-ticker holders lists... |
| `llmquant-strategies` | Router skill for LLMQuant hedge-fund and PM strategy workflows. Use when the user needs equity long/short, long-biased, event-driven, macro, quant, or multi-... |

## Repo-local / Anthropic Skills (80)

| skill | description |
|---|---|
| `3-statement-model` | Complete, populate and fill out 3-statement financial model templates (Income Statement, Balance Sheet, Cash Flow Statement) . Use when asked to fill out mod... |
| `5-why-adversary` | \| |
| `_shared` | ⚠️ 无 SKILL.md（损坏）|
| `accrual-schedule` | Build the period-end accrual schedule — for each accrual, compute the entry, cite the support, and draft the JE. Use during month-end close; the JE is a draf... |
| `ai-hedge-fund` | AI Hedge Fund (ai-hedge-fund / aihf) 框架总入口。多智能体对冲基金模拟器——5 位投资人 persona (Buffett/Munger/Graham/Lynch/Druckenmiller) + PEAD 系统模型，按 FUND > STRATEGY > MODEL 三层组合... |
| `ai-hedge-fund-buffett` | Warren Buffett 投资人视角 (ai-hedge-fund persona)。护城河 / 管理层资本配置 / 财务稳健 / 公允价格 / 10 年持有意愿。当用户问"巴菲特会怎么看 X"、"用巴菲特视角分析"、"Buffett lens"、"护城河/长期持有"时加载。 |
| `ai-hedge-fund-deep-value` | ai-hedge-fund "Deep Value" mandate（Graham 主导的长期偏多 discretionary pod）。graham(2.0) + buffett + munger，conviction_weighted 混合。当用户问"deep value 分析"、"深度价值策略"、"格雷厄姆... |
| `ai-hedge-fund-druckenmiller` | Stanley Druckenmiller 投资人视角 (ai-hedge-fund persona)。营收/利润率的**变化率** / EPS 动能 / 定价了什么 / 只在下重注时出手。注意：该 persona 仅用基本面数据（无宏观/利率/价格）。当用户问"德鲁肯米勒会怎么看 X"、"用德鲁肯米勒视角分析"... |
| `ai-hedge-fund-earnings-drift` | ai-hedge-fund "Earnings Drift" mandate（PEAD 系统化 pod，事件时间）。单模型 pead——EPS BEAT 后做多、MISS 后做空，赌市场对意外反应不足。当用户问"earnings drift"、"PEAD"、"财报后漂移"、"盈利意外策略"时加载。 |
| `ai-hedge-fund-fundamental-ls` | ai-hedge-fund "Fundamental L/S" mandate（旗舰，5 位 agent 全员，市场中性多空）。buffett + munger + graham + lynch + druckenmiller 对 universe 排名，做多最受青睐、做空最不受青睐。当用户问"fundament... |
| `ai-hedge-fund-graham` | Benjamin Graham 投资人视角 (ai-hedge-fund persona)。安全边际 / P/E≤15-20 / 流动比率>1.5 / 盈利稳定 / 怀疑增长溢价。当用户问"格雷厄姆会怎么看 X"、"用格雷厄姆视角分析"、"Graham lens"、"安全边际/防御型投资"时加载。 |
| `ai-hedge-fund-inflections` | ai-hedge-fund "Inflections" mandate（基本面变化率多空）。druckenmiller + lynch 在倍数重定价之前捕捉加速与恶化。当用户问"inflections"、"拐点策略"、"基本面加速/恶化"、"变化率交易"时加载。 |
| `ai-hedge-fund-lynch` | Peter Lynch 投资人视角 (ai-hedge-fund persona)。分类（fast grower/stalwart/slow grower/turnaround）/ PEG 测试 / 故事清晰 / 盈利驱动。当用户问"林奇会怎么看 X"、"用林奇视角分析"、"Lynch lens"、"PEG/成长... |
| `ai-hedge-fund-munger` | Charlie Munger 投资人视角 (ai-hedge-fund persona)。反向思考 / 多年质量一致性 / 激励与资本配置 / "太难堆"。当用户问"芒格会怎么看 X"、"用芒格视角分析"、"Munger lens"、"反向思考/太难堆"时加载。 |
| `ai-readiness` | Scan the portfolio for the highest-leverage AI opportunities and rank where to deploy operating-partner time. Ingests quarterly updates and financials across... |
| `alpha-engine-v21` | \| |
| `audit-xls` | Audit a spreadsheet for formula accuracy, errors, and common mistakes. Scopes to a selected range, a single sheet, or the entire model (including financial-m... |
| `break-trace` | Root-cause a reconciliation break to its source transaction or posting — follow the audit trail from the break row back to the originating entry on each side... |
| `buy-ladder` | BUY_LADDER v3.1 数据驱动买入判定框架——4 个回测验证正α信号加权计票 (technical_basic×2 + alpha_zoo×2 + candlestick×1 + ad_line×1) + 绝对阈值 (≥4/6 击球区, ≥3/6 观察区)。BT-015 信号级事件研究 + BT-016... |
| `buyer-list` | Build and organize a universe of potential acquirers for sell-side M&A processes. Identifies strategic and financial buyers, assesses fit, and prioritizes ou... |
| `catalyst-calendar` | Build and maintain a calendar of upcoming catalysts across a coverage universe — earnings dates, conferences, product launches, regulatory decisions, and mac... |
| `cim-builder` | Structure and draft a Confidential Information Memorandum for sell-side M&A processes. Organizes company information into a professional, investor-ready docu... |
| `clean-data-xls` | Clean up messy spreadsheet data — trim whitespace, fix inconsistent casing, convert numbers-stored-as-text, standardize dates, remove duplicates, and flag mi... |
| `client-report` | Generate professional client-facing performance reports with portfolio returns, allocation breakdowns, and market commentary. Suitable for quarterly or annua... |
| `client-review` | Prepare for client review meetings with portfolio performance summary, allocation analysis, talking points, and action items. Pulls together account data int... |
| `competitive-analysis` | Framework for building competitive landscape decks — market positioning, competitor deep-dives, comparative analysis, strategic synthesis. Use when the user ... |
| `comps-analysis` | Build institutional-grade comparable company analyses with operating metrics, valuation multiples, and statistical benchmarking in Excel/spreadsheet format. |
| `datapack-builder` | Build professional financial services data packs from various sources including CIMs, offering memorandums, SEC filings, web search, or MCP servers. Extract,... |
| `dcf-model` | Real DCF (Discounted Cash Flow) model creation for equity valuation. Retrieves financial data from SEC filings and analyst reports, builds comprehensive cash... |
| `dd-checklist` | Generate and track comprehensive due diligence checklists tailored to the target company's sector, deal type, and complexity. Covers all major workstreams wi... |
| `dd-meeting-prep` | Prepare for due diligence meetings — management presentations, expert network calls, customer references, and advisor sessions. Generates targeted question l... |
| `deal-screening` | Quickly screen inbound deal flow — CIMs, teasers, and broker materials — against the fund's investment criteria. Extracts key deal metrics, runs a pass/fail ... |
| `deal-sourcing` | PE deal sourcing workflow — discover target companies, check CRM for existing relationships, and draft personalized founder outreach emails. Use when sourcin... |
| `deal-tracker` | Track multiple live deals with milestones, deadlines, action items, and status updates. Maintains a deal pipeline view and surfaces upcoming deadlines and ov... |
| `deck-refresh` | Updates a presentation with new numbers — quarterly refreshes, earnings updates, comp rolls, rebased market data. Use whenever the user asks to "update the d... |
| `docx` | Use this skill whenever the user wants to create, read, edit, or manipulate Word documents (.docx files). Triggers include: any mention of 'Word doc', 'word ... |
| `earnings-analysis` | Create professional equity research earnings update reports (8-12 pages, 3,000-5,000 words) analyzing quarterly results for companies already under coverage.... |
| `earnings-preview` | Build pre-earnings analysis with estimate models, scenario frameworks, and key metrics to watch. Use before a company reports quarterly earnings to prepare p... |
| `financial-plan` | Build or update a comprehensive financial plan covering retirement projections, education funding, estate planning, and cash flow analysis. Use for new clien... |
| `gl-recon` | Reconcile general ledger to subledger for a trade date or period — match at the position or transaction level, surface breaks, and classify each break by lik... |
| `ib-check-deck` | Investment banking presentation quality checker. Reviews a pitch deck or client-ready presentation for (1) number consistency across slides, (2) data-narrati... |
| `ic-memo` | Draft a structured investment committee memo for PE deal approval. Synthesizes due diligence findings, financial analysis, and deal terms into a professional... |
| `idea-generation` | Systematic stock screening and investment idea sourcing. Combines quantitative screens, thematic research, and pattern recognition to surface new long and sh... |
| `initiating-coverage` | Create institutional-quality equity research initiation reports through a 5-task workflow. Tasks must be executed individually with verified prerequisites - ... |
| `investment-proposal` | Create professional investment proposals for prospective clients. Covers the firm's approach, proposed allocation, expected outcomes, and fee structure. Use ... |
| `kyc-doc-parse` | Parse an investor or client onboarding packet into structured KYC fields — identity, ownership, control, source of funds, and document inventory. Use as the ... |
| `kyc-rules` | Apply the firm's KYC/AML rules grid to a parsed onboarding record — assign a risk rating, list every rule outcome with the rule cited, and flag what's missin... |
| `lbo-model` | This skill should be used when completing LBO (Leveraged Buyout) model templates in Excel for private equity transactions, deal materials, or investment comm... |
| `merger-model` | Build accretion/dilution analysis for M&A transactions. Models pro forma EPS impact, synergy sensitivities, and purchase price allocation. Use when evaluatin... |
| `model-update` | Update financial models with new data — quarterly earnings, management guidance, macro changes, or revised assumptions. Adjusts estimates, recalculates valua... |
| `morning-note` | Draft concise morning meeting notes summarizing overnight developments, trade ideas, and key events for coverage stocks. Designed for the 7am morning meeting... |
| `nav-tieout` | Tie an LP statement to the fund's NAV pack — recompute the LP's capital account from the NAV components and flag any line that doesn't agree. Use before LP s... |
| `non-price-evidence` | 非价格证据层 (4 维度)。当需要为趋势/估值结论做**独立验证**（超越价格类算法的"伪共识"）时加载。四维 = 成交量结构(换手/量比/OBV/AD/量价分布) + 资金流向(A股两融/股东户数/龙虎榜/大宗/解禁/北向 + 美股13F/Form4 + Crypto链上) + 基本面(财务指标/一致预期/三大... |
| `pdf` | Use this skill whenever the user wants to do anything with PDF files. This includes reading or extracting text/tables from PDFs, combining or merging multipl... |
| `personal-trading-system` | 加载用户的个人交易系统 - 累积的法则、失效案例、待验证假设、回测索引。任何 subagent 在做投资判断前必须加载此 skill。它是"协议层"，实际数据在 .opencode/memory/personal-system/。当用户提到"我的法则/规则/仓位/卖出梯子/个人交易系统/交易系统/我的系统"时加载。 |
| `pitch-deck` | Populates investment banking pitch deck templates with data from source files. Use when: user provides a PowerPoint template to fill in, user has source data... |
| `portfolio-monitoring` | Track and analyze portfolio company performance against plan. Ingests monthly/quarterly financial packages (Excel, PDF), extracts KPIs, flags variances to bu... |
| `portfolio-rebalance` | Analyze portfolio allocation drift and generate rebalancing trade recommendations across accounts. Considers tax implications, transaction costs, and wash sa... |
| `ppt-template-creator` | Creates self-contained PPT template SKILLS (not presentations) from user-provided PowerPoint templates. Use ONLY when a user wants to create a reusable skill... |
| `pptx` | Use this skill any time a .pptx file is involved in any way — as input, output, or both. This includes: creating slide decks, pitch decks, or presentations; ... |
| `pptx-author` | Produce a .pptx file on disk (headless) instead of driving a live PowerPoint document — for managed-agent sessions with no open Office app. |
| `process-letter` | Draft process letters and bid instructions for sell-side M&A processes. Covers initial indication of interest (IOI) instructions, final bid procedures, and m... |
| `returns-analysis` | Build quick IRR/MOIC sensitivity tables for PE deal evaluation. Models returns across entry multiple, leverage, exit multiple, growth, and hold period scenar... |
| `roll-forward` | Build a roll-forward schedule for a balance-sheet account — beginning balance plus activity less reversals equals ending balance, with each component tied to... |
| `sector-overview` | Create comprehensive industry and sector landscape reports covering market dynamics, competitive positioning, key players, and thematic trends. Use for clien... |
| `sell-ladder` | SELL_LADDER v2.5 卖出判定框架——16 skill 信号矩阵（事件×2/趋势×1 分级计票）、5 大动能结束标志、3 阶段卖出判定（含阶段 2.5 兜底）、5 维触发矩阵。当用户问"是否止盈/减持/卖出/清仓/动能是否结束/卖出梯子/SELL_LADDER/该不该卖"时加载。这是协议层，实际工具在... |
| `skill-creator` | Guide for creating effective skills. This skill should be used when users want to create a new skill (or update an existing skill) that extends Claude's capa... |
| `stock-deep-dive` | 标准化个股深度分析流程 - 强制走"多 skill 综合"路径（估值模型 + 技术分析 + 资金流向 + 舆情政策 + 国际市场对比 + V21 WT1 + 个人交易系统检查）。任何涉及"现在该不该买/卖/加仓/减仓 X"的问题必须走这个流程。当用户提到"分析 600519/000001/某只股票/个股分析/股票... |
| `fsi-strip-profile` | \| |
| `tax-loss-harvesting` | Identify tax-loss harvesting opportunities across taxable accounts. Finds positions with unrealized losses, suggests replacement securities, and tracks wash ... |
| `teaser` | Draft anonymous one-page company teasers for sell-side M&A processes. Creates a compelling summary without revealing the company's identity, designed to gaug... |
| `thesis-tracker` | Buy-side discipline system. For each holding, maintain a written investment thesis — core thesis in 5 sentences, falsifiable assumptions, red lines, valuatio... |
| `trend-analysis-multi-algo` | 多算法趋势分析协议 (10 算法强制启动)。当用户要求对某只股票/资产做趋势分析 / 技术分析 / 走势判断 / 该不该买 / 该不该卖 / 形态分析 / 波浪分析 / 缠论分析 / 蜡烛图分析 / 支撑压力时加载。一次性启动 动量层(WaveTrend V21 + 技术三维投票) + 形态层(蜡烛图/缠论/艾略... |
| `unit-economics` | Analyze unit economics for PE targets — ARR cohorts, LTV/CAC, net retention, payback periods, revenue quality, and margin waterfall. Essential for software/S... |
| `value-creation-plan` | Structure post-acquisition value creation plans with revenue, cost, and operational levers mapped to an EBITDA bridge. Includes 100-day priorities, KPI targe... |
| `variance-commentary` | Write flux commentary for every P&L and balance-sheet line over threshold — current vs prior period and vs budget, with the driver explained from underlying ... |
| `wif-ashare-advisory` | > |
| `wif-fund-advisory` | > |
| `xlsx` | Use this skill any time a spreadsheet file is the primary input or output. This means any task where the user wants to: open, read, edit, or fix an existing ... |
| `xlsx-author` | Produce a .xlsx file on disk (headless) instead of driving a live Excel workbook — for managed-agent sessions with no open Office app. |
