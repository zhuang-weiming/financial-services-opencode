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
