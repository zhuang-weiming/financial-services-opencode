# Market-Router Agent — Example Questions

> **Routing trigger keywords:** BTC, crypto, BTC/USDT, ETH, 600519, 上证, A股, 沪深300, 北向, EURUSD, forex, FX, USD/JPY, multi-market data

**Data Files:**
- `data/instrument_list.csv` — Instrument universe with market codes
- `data/market_data_sample.json` — Sample OHLCV data

---

## Question 1: Identify Market for Various Instruments
```
Identify which market and data source to use for these instruments:
- 600519 (A-share)
- AAPL (US stock)
- BTC/USDT (crypto)
- EURUSD (forex)
- 000300 (index)

Reference: data/instrument_list.csv

Please:
1) Detect the market for each instrument
2) Recommend the optimal data loader
3) Show fallback chain if primary source fails
4) Note any API key or rate-limit requirements
```

## Question 2: Load BTC/USDT Data
```
Load the last year of hourly BTC/USDT data for analysis.

Reference: data/market_data_sample.json

Please:
1) Route to the correct exchange data source (OKX or CCXT)
2) Fetch 1-year hourly OHLCV
3) Show summary statistics (mean, std, min, max, volume)
4) Check for data quality issues (gaps, outliers)
```

## Question 3: Fetch EURUSD forex data
```
Fetch daily EURUSD forex data from 2024 for a macro research project.

Reference: data/market_data_sample.json

Please:
1) Route to the appropriate forex data loader
2) Fetch daily OHLCV from 2024-01-01 to present
3) Calculate key technical indicators (SMA 50/200, RSI)
4) Output a data summary with date range and observation count
```

## Question 4: Premier 多市场统一持仓看板
```
请为我的跨市场投资组合生成一份统一的持仓看板。

Reference: data/premier_multi_market_holdings.csv

From data/premier_multi_market_holdings.csv:
- A 股：贵州茅台、招商银行、长江电力（3 只）
- 港股：腾讯、阿里巴巴（2 只）
- 美股：苹果、微软、英伟达（3 只）
- Crypto：比特币、以太坊（2 个）
- 所有 Value 已折算为人民币

Please:
1) 按市场分类汇总持仓市值和盈亏
2) 计算各市场在总组合中的占比
3) 按币种分组（CNY/HKD/USD），计算汇率风险敞口
4) 生成行业穿透视图（实际投资了什么行业、各行业占比）
5) 识别是否存在集中度风险（单只/单个行业/单个市场超 20% 者需标注）
6) 建议如何优化跨市场配置以降低相关性风险
7) 针对加密货币部分，给出适合 Premier 投资者的风险控制建议
```

## Question 5: 全球主要资产类别收益率/波动率/相关性分析
```
请帮我分析当前全球主要资产类别的收益-风险特征，为跨市场配置提供依据。

Reference: data/premier_multi_market_holdings.csv

我需要了解以下资产类别的最新数据：
- A 股（沪深 300）
- 港股（恒生指数）
- 美股（标普 500）
- 美债（10 年期国债）
- 黄金
- 比特币

Please:
1) 获取各资产近 1 年/3 年/5 年的年化收益率
2) 计算各资产的年化波动率和最大回撤
3) 构建资产间相关性矩阵，标记高相关性对（>0.7）
4) 标注当前各资产所处的估值分位（历史百分位）
5) 推荐一个分散化的 Premier 跨市场配置方案
6) 标注当前市场环境中需要警惕的尾部风险
```
