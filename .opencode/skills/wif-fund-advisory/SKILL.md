---
name: wif-fund-advisory
description: >
  WIF (Wealth Investment Framework) v5.9 fund advisory methodology for US market.
  Covers 5-phase market timing system (Rising/Panic/Fall/Recover/Transition) using
  FFR/F29/VIX/VIXTERM macro indicators, 40-ETF multi-asset universe, historical
  backtest (2007-2026, +1332.4%, Sharpe 1.00, MDD -21.1%), and rebalancing engine.
  Triggers on "WIF", "wealth investment framework", "fund advisory methodology",
  "asset allocation portfolio", "portfolio health status", "phase assessment",
  "WIF phase", "F29 indicator", "VIXTERM", or "rebalancing recommendation".
---

# WIF Fund Advisory (Wealth Investment Framework v5.9)

## Overview

WIF v5.9 is a quantitative **multi-asset portfolio allocation methodology** for US-market fund advisory. It determines the current **market phase** (1-5) from three macro indicators, then maps each phase to a target ETF portfolio from a 40-ticker universe.

### Key Metrics (2007-2026 Backtest)

| Metric | v5.9 (with friction) | SPY Buy-Hold |
|--------|:---:|:---:|
| Cumulative Return | **+1332.4%** | +1283.0% |
| Sharpe Ratio | **1.00** | 0.61 |
| Max Drawdown | **-21.1%** | -55.2% |
| Trades | **4** | — |
| Total Cost | $113,888 | — |

### Data Location

All data files live at `example/wif-framework/data/`:
- `_merged_prices_20260716.csv` – 4926×10 merged price matrix (2007-01-03 to 2026-07-16)
- `tickers_20260716/` – 48 individual ticker CSVs
- `WIF_v59_Backtest.py` – Full backtest engine (reference implementation)
- `WIF_v59_nav_20260716.csv` – Historical NAV series
- `WIF_v59_trade_log_20260716_HSCBC.csv` – 35-trade log
- `WIF_v59_Report_20260716.html` – HTML backtest report

Python library interface: `.opencode/python/wif-framework/`

---

## Core Methodology

### Phase Detection (Three Indicators → Phase 1-5)

WIF uses a **three-layer cascade** to determine market phase:

#### Layer 1: CSI (Composite Stress Index)
The primary driver combining three sub-components:

```
CSI = 0.45 × Z(F29_60d) + 0.35 × Z(VIXTERM_60d) + 0.20 × Z(Correlation_Breakdown)

CSI > 2.0  → EMERGENCY
CSI > 1.0  → WARNING
CSI < 1.0  → HEALTHY
```

- **F29_60d Z-score** (45% weight): 60-day rolling Z-score of credit spread (BAA - 10Y Treasury, in bp)
- **VIXTERM_60d Z-score** (35% weight): 60-day rolling Z-score of VIX term structure (VIX spot - VIX3M)
- **Correlation_Breakdown Z-score** (20% weight): Measure of cross-asset correlation breakdown
- **Hard Triggers**: F29 > 500bp → EMERGENCY (independent override); VIX > 40 and VIX 10d > 100% → EMERGENCY (F33b)

#### Layer 2: Macro Quadrant (Economic Regime)

Four-quadrant mapping from Real Rate (DFII10) and Breakeven Inflation (T10YIE):

| Quadrant | Real Rate | Inflation | Label |
|:--------:|:---------:|:---------:|:------|
| 1 | Falling | Falling | **Recession** (defensive) |
| 2 | Falling | Rising | **Recovery** (risk-on) |
| 3 | Rising | Rising | **Stagflation** (commodities) |
| 4 | Rising | Falling | **Overheat** (late-cycle) |

#### Layer 3: MCI (Market Condition Index)

Combines Layer 1 + 2 with continuous fine-tuning:

```
MCI = MCI_layer1 + MCI_layer2 + MCI_layer3

MCI_layer1: Phase1 status × Macro Quadrant (base score -20 to +30)
MCI_layer2: Continuous adjustment from delta_F29, delta_rates, delta_VIX (each ±5)
MCI_layer3: CSI threshold adjustments (WARNING zone penalty, exit confirmation bonus)
```

### Phase → Allocation Mapping

WIF v5.9 defines **5 market phases** mapped from (Phase1_status + Macro Quadrant + MCI):

| Phase | Name | Typical Regime | Equity | Fixed Income | Real Assets |
|:-----:|:----:|:--------------:|:-----:|:------------:|:-----------:|
| 1 | **Rising** | HEALTHY + Quadrant 2/4 (Recovery/Overheat) | 65-75% | 10-15% | 15-25% |
| 2 | **Panic** | EMERGENCY (any quadrant) | 15% | 55% | 30% |
| 3 | **Fall** | HEALTHY + Quadrant 1/3 (Recession/Stagflation) | 30% | 20-45% | 25-50% |
| 4 | **Recover** | WARNING → HEALTHY transition | 20-50% | 20-50% | 25-30% |
| 5 | **Transition** | HEALTHY + MCI moderate | 50-65% | 10-30% | 15-25% |

### 40-ETF Universe

| Category | Tickers |
|:---------|:--------|
| **US Equity Core** | VTI, SPY, QQQ, IWM, VB, SPY |
| **US Equity Factor** | MTUM, QUAL, MOAT, USMV, SPLV, VIG, NOBL, HDV, SCHD, VYM |
| **US Equity Sector** | VGT, XLE, XLF, XLB, XLP, XLU, XLV, XLRE |
| **International Equity** | EFA, VEA, EEM, VWO |
| **Fixed Income** | BND, TLT, IEF, SHV, AGG, LQD, HYG |
| **Real Assets & Commodities** | GLD, SLV, PDBC, VNQ |
| **US Equity Size** | IJH, IJR |

### Rebalancing Logic

- **Phase switches** (Phase1_status change): Rebalance at next close
- **Regular rebalancing**: Every 3 weekends (15 trading days) via factor scoring
- **MCI gate**: MCI < +5 forces VTI-only position (no factor selection)
- **WARNING defense**: BND momentum < 0 triggers defensive rotation
- **HSBC channel costs**: 0.03% equity, 0.02% bond/commodity, 0.03% switch

---

## Workflow

### Step 1: Load Data

```python
from wif_framework import load_prices, current_phase

prices = load_prices()  # loads _merged_prices_20260716.csv
phase  = current_phase(prices)
```

### Step 2: Assess Current Phase

Check latest indicators:

| Indicator | Value | Status |
|-----------|:-----:|:------:|
| F29 (BAA - DGS10) | **182 bp** | ✅ < 500 healthy |
| VIX spot | **15.67** | ✅ < 40 calm |
| VIXTERM | **+1.43** | ✅ contango normal |
| Phase 1 | **HEALTHY** | ⬆️ Risk-on |

### Step 3: Generate Allocation

```python
from wif_framework import target_allocation

alloc = target_allocation(phase_status='HEALTHY', macro_quadrant=2)
# Returns dict: {eq: 0.75, fi: 0.10, ra: 0.15}
```

### Step 4: Produce Advisory Report

Provide client-facing output addressing:
1. Current market phase with supporting evidence
2. Target allocation vs current allocation
3. Rebalancing recommendations (if any)
4. Risk regime flags (credit spread, VIX, yield curve)
5. Backtest-informed narrative (2007-2026 track record)

---

## Guardrails

- **Never present backtest results as future returns** — past performance disclaimer required
- **VIX3M is a proxy** (uses VIXM ETF, not CBOE ^VIX3M index)
- **BAA is monthly data** — interpolated; flag when used for precision decisions
- **FRED T+1 lag** — latest VIX/DGS10 may be from prior trading day; state this
- **Phase detection requires 3-day confirmation** — one-day outliers don't trigger switches
- **No live trading** — all outputs are advisory drafts for human review

## References

- Data spec: `example/wif-framework/data/DATA_SPECIFICATION.md`
- Update procedure: `example/wif-framework/data/DATA_UPDATE_PROCEDURE.md`
- Python interface: `.opencode/python/wif-framework/`
- Backtest engine: `example/wif-framework/data/WIF_v59_Backtest.py`
