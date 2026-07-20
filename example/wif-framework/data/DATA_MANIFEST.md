# WIF US v5.9 Data Manifest

## Usage

Data is auto-discovered by `wif_framework.data` module via relative path from the
package. Override with `WIF_DATA_DIR` environment variable:

```bash
WIF_DATA_DIR=/path/to/data python3 my_script.py
```

## Core Files

### Merged Price Matrix

| File | Rows | Date Range | Description |
|------|------|-----------|-------------|
| `_merged_prices_20260716.csv` | 4927 (incl. header) | 2007-01-03 ~ 2026-07-16 | 10-asset merged OHLCV (SPY/BND/GLD/TLT/VTI/QQQ/IEF/VNQ/XLP/GSG) |

### Individual Ticker CSVs (`tickers_20260716/`)

49 files covering 46 tickers + 3 FRED series + 1 metadata JSON.

**FRED Macro Series (full history)**

| File | Rows | Date Range | Source |
|------|------|-----------|--------|
| `CreditSpread_BAA_1986_2026.csv` | 10089 | 1986-01-02 ~ 2026-05-08 | FRED (BAA - 10Y) |
| `DGS10_2007_2026.csv` | 4839 | 2007-01-02 ~ 2026-05-04 | FRED DGS10 |
| `T10YIE_2007_2026.csv` | 4840 | 2007-01-02 ~ 2026-05-05 | FRED T10YIE |
| `BAMLH0A0HYM2_2007_2026.csv` | 38 | 2007-01-02 ~ 2026-07-15 | FRED HY OAS (not in merged matrix) |

**Equity ETFs (26d history, 2026-06-09 ~ 2026-07-16)**

SPY, QQQ, VTI, VEA, EEM, EFA, VWO, IWM, IJH, IJR, VB, VGT, XLF, XLE, XLV,
XLP, XLU, XLB, XLRE, VNQ, VYM, HDV, SCHD, NOBL, QUAL, VIG, MTUM, USMV, SPLV,
MOAT — all limited to 26d.

> **Why only 26 days?** These factor ETFs (QUAL, VIG, MOAT, etc.) are used by
> the v6.8.1 factor-routing layer only. They are not in the merged price matrix
> and do not affect v5.9 strategy execution. Full history requires a data vendor
> subscription.

**Commodity/Currency ETFs (26d)**

GLD, SLV, PDBC

**Fixed Income ETFs (26d)**

AGG, BND, HYG, IEF, LQD, SHV, TLT

**VIX Derivatives (26d)**

VIX_spot, VIX3M_proxy_VIXM, VIXTERM

### Backtest Script

| File | Lines | Purpose |
|------|-------|---------|
| `WIF_v59_Backtest.py` | 1833 | Full backtest engine (runs v5.9 + v6.8.1 combined) |

### Backtest Outputs

| File | Size | Description |
|------|------|-------------|
| `WIF_v59_nav_20260716.csv` | 1.3 MB | Daily NAV series (4926 rows) |
| `WIF_v59_trade_log_20260716_HSCBC.csv` | 120 KB | All rebalance events (v5.9 + v6.8.1) |
| `WIF_v59_Report_20260716.html` | 250 KB | HTML performance report |

## Data Loading

```python
from wif_framework.data import load_prices, load_fred_series, load_ticker

df = load_prices()                         # 4926 × 10 merged matrix
fred = load_fred_series()                  # DGS10, T10YIE, F29_bp
spy = load_ticker("SPY")                   # individual ticker
```

## Known Limitations

1. **Factor ETFs have only 26 days** — full history not available in repo.
   v6.8.1 factor selection will not work for backtesting before 2026-06-09.
2. **BAMLH0A0HYM2 has only 37 rows** — not used as primary credit spread
   source (CreditSpread_BAA is the canonical F29 source).
3. **CreditSpread_BAA stops 2026-05-08** — last 2 months of backtest use
   forward-filled values.
4. **No minute-level data** — daily frequency only.
