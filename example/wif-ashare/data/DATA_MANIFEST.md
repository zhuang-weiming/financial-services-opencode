# WIF A-Share v2.7 Data Manifest

## Usage

Data is auto-discovered by `wif_framework.ashare` module via relative path from the
package. Override with `WIF_ASHARE_DATA_DIR` environment variable:

```bash
WIF_ASHARE_DATA_DIR=/path/to/data python3 my_script.py
```

## File Inventory

| File | Rows | Date Range | Source | Description |
|------|------|-----------|--------|-------------|
| `etf_prices_new.csv` | 3096 | 2013-07-29 ~ 2026-04-22 | 腾讯 ifzq API (前复权) | 4 ETF daily: hs300, cyb, gold, bond |
| `index_csi500_daily.csv` | 4328 | 2008-06-30 ~ 2026-04-21 | 09_Data (原 baostock) | 中证500指数日线 (close) |
| `index_tech_399303_daily.csv` | 2935 | 2014-03-28 ~ 2026-04-22 | baostock sz.399303 | 国证科技指数日线 (close) |
| `macro_pmi.csv` | 220 | 2008-01 ~ 2026-04 | AKShare | PMI 月度数据 |
| `macro_m2_m1_spread.csv` | 220 | 2008-01 ~ 2026-04 | AKShare | M2/M1/YoY 月度数据 |
| `macro_chip_daily.csv` | 43 | 2022-11 ~ 2026-04 | 399303 近似替代 | 科创芯片588200 月收益 (approximated) |

## Data Loading

```python
from wif_framework.ashare import load_data, run_backtest

df = load_data()        # 3095 × 24 preprocessed DataFrame
result = run_backtest() # returns stats + NAV series
```

## Known Limitations

1. **macro_chip_daily.csv uses 399303 proxy** — the original 588200 ETF
   monthly returns could not be fetched (East Money rate limit). The chip
   overlay only activates from 2022-11-01. NAV impact ~5% (8.48 vs 8.97
   canonical). To regenerate with accurate data:
   ```python
   import akshare as ak
   df = ak.fund_etf_hist_em(symbol='588200', period='daily',
       start_date='20221001', end_date='20260422', adjust='qfq')
   # convert to monthly returns and save as macro_chip_daily.csv
   ```
2. **Tech index starts 2014-03-28** — tech replacement mechanism activates
   from 2019-01-01, so the earlier gap does not affect the strategy.
3. **ETF data is adjusted forward (前复权)** — suitable for total return
   calculation. Not suitable for unadjusted price analysis.
4. **No minute-level data** — daily frequency only.

## Original Source Mapping

| File | Original Path |
|------|-------------|
| All data | `/Users/hello/WorkBuddy/20260423204955/data/` (original machine) |
| ETF prices | `09_Data/Adj Close/China/etf_prices_new.csv` |
| CSI500 | `09_Data/Adj Close/China/csi500_idx.csv` |
| PMI/M2 | `09_Data/Adj Close/China/macro_pmi.csv`, `macro_m2_m1_spread.csv` |
