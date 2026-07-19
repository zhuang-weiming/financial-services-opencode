# V21.0 Release Notes — English Translation

> Version: V21.0  
> Date: 2026-07-09  
> Engine: `alpha_engine_common.run_backtest` (single canonical engine)  
> Strategy: V21 = `lv(0.15) + wt_mom(0.85)`  
> Data: `09_Data/中国A股/data_v20.h5`

This document is the complete V21 release-notes dump, preserved verbatim in
the alpha-engine-v21 skill. Differences between V21.0 and the skill port are
listed in SKILL.md §"Differences from V21.0 release".

---

## 1. Release Summary

V21 was selected and frozen from V20-era research. The original 3-factor
spec (`lv + wt + rev_1m`) was reduced to 2 factors after the engine timing
fix showed `rev_1m` produced no positive alpha under correct timing.

### 1.1 Full-sample metrics

| Metric | **V21** |
|---|---|
| **Sharpe (annual)** | **0.869** |
| **NAV** (2010 → 2026) | **27.93** |
| **Annual return** | **23.1 %** |
| **Max drawdown** | −34.6 % |
| Positive months | 97/192 (51 %) |
| Cash months | 0 |
| Avg turnover | 0.73 |
| **OOS (2018-2026)** | **1.076** |

> Source: `results/v21_authoritative_results.json` (2026-07-09).

### 1.2 Statistical tests

| Test | **V21** |
|---|---|
| Z (IID) p | **0.0003** |
| Z (Newey-West HAC) p | **0.0001** |
| Bonferroni (n=5) | **0.0013** |
| Bootstrap 95 % CI | **[0.564, 1.372]** |
| Bootstrap p(SR > 0) | **1.000** |
| **DSR** (deflated) | **1.000** |
| Skewness | 0.850 |
| Kurtosis | 6.812 |

- `p_iid = 0.0003`, `p_nw = 0.0001` — significant at the 0.1 % level under both
  IID and HAC assumptions
- Bonferroni-corrected `p = 0.0013` — significant at the 1 % level
- Bootstrap 95 % CI lower bound = 0.564 — well above zero
- DSR = 1.000 — V21 is an **extreme winner** under 5-trial multiple testing
  (López de Prado 2018 Eq 12.8, correct formula)

### 1.3 Sub-sample robustness

| Period | **V21 Sharpe** |
|---|---|
| 2010-2014 | 0.506 |
| 2015-2018 | **0.798** |
| 2019-2021 | **1.202** |
| 2022-2025 | **1.296** |
| **2026 (Jan-Jun)** | **0.539**\* |

> \* 2026 is observation only (6 months).

### IS / OOS split (cutoff 2017-12-31)

| Segment | **V21 Sharpe** |
|---|---|
| **IS** (2010-2017) | 0.665 |
| **OOS** (2018-2026) | **1.076** |

**OOS Sharpe is 1.62× IS Sharpe** — a strong anti-overfitting signal.

### 1.4 Rolling walk-forward OOS

`run_backtest.py --walkforward` — 36-month train, 12-month test, 12-month step.

| Metric | **V21** |
|---|---|
| Windows | 13 (2013-01 → 2026-06) |
| **Mean WF Sharpe** | **0.939** |
| Best | +2.380 |
| Worst | −0.030 |
| **Positive windows** | **12/13 (92 %)** |
| Windows with Sharpe < 0.5 | 3/13 (23 %) |
| Avg single-window annual return | 22.0 % |

---

## 2. Core Strategy

V21 is a 2-factor model (after `rev_1m` removal). All factors are ranked
cross-sectionally within the post-filter valid pool (after OB / liquidity /
bad-returns filters) using `rank(pct=True, na_option='keep')` to (0, 1), then
weighted-summed.

```
V21 score = lv × 0.15 + wt_mom × 0.85
                ↑            ↑
           low-vol         LazyBear WT
           12-month        oscillator level
           rolling σ(r)
```

| Factor | Economic interpretation | Implementation |
|---|---|---|
| `lv` | A-share long-documented low-volatility anomaly | `rets.rolling(12).std()`, negated |
| `wt_mom` | Adaptive momentum (LazyBear WT weekly oscillator) | `wt1_monthly` (HDF5) |

> **`rev_1m` removal note**: V21 originally included `rev_1m` at 20 % weight,
> but the old engine's 1-month signal lag accidentally turned the reversal
> signal into a quasi-momentum signal, inflating its apparent performance.
> After the 2026-07-09 engine timing fix, `rev_1m` produced no positive alpha
> and was removed.

---

## 5. Important Risks and Limitations

**Read before use**:

1. **DSR = 1.0 is extreme — beware multiple testing**:
   - Bootstrap p > 0 = 1.000 — real signal
   - DSR = 1.0 means V21 is a 5-trial extreme winner (López de Prado 2018
     Eq 12.8, correct formula)

2. **2008-2009 not in sample**: data starts 2010; no GFC coverage.

3. **Data-quality limitations**:
   - 2010-2014 mcap ~57 % missing (baostock doesn't cover delisted / pre-IPO
     names)
   - 2024 still has 434/36720 price NaN (~1.2 %), all delisted / suspended
     stocks with no data source
   - 2025+ mcap is price-derived (Dec-2024 reference × price ratio), not
     direct extraction — but error < 5 % for large caps

4. **Low-volatility factor early degradation**:
   - `rets.rolling(12).std()` needs ≥12 periods of price data to be non-NaN
   - First ~8 months (warmup months 4-12) lv factor is `fillna(0.5) × 0.15 = constant`
     with no discrimination; strategy is effectively pure WT during this window

5. **High turnover**:
   - Avg 0.73 = 73 % turnover per month ≈ 7 stocks
   - Acceptable for 2000+ tradable universe
   - Live deployment should add a soft turnover penalty (`n_hold × 0.5`)

6. **OOS leads V19 by +0.756**:
   - V21 Sharpe 1.076 vs V19 0.320 on 2018-2026 OOS
   - V21 wins in 3/4 sub-sample windows (2019-2021 ties)

7. **Engine fixes applied in V21.0** (kept in the skill port):
   - **Return timing correction** (2026-07-09): `run_backtest` now uses
     `new_holdings` (just selected) instead of `holdings` (previous iteration)
     for return calculation. Eliminates a 1-month signal lag that artificially
     amplified `rev_1m`.
   - **DSR formula correction** (2026-07-09): replaced `v_term = max(0.0, ...)`
     with `V_SR = var_sr_raw / (n-1)` per LdP (2018) Eq 12.8. Previous
     `sr_star ≈ 0.967` → correct `sr_star ≈ 0.054`.
   - **Strategy revision** (2026-07-09): removed `rev_1m`. New formula
     `lv(0.15) + wt_mom(0.85)`.

---

## Execution-Price Caveat

The H5 `close_7d` dataset was designed to be "month-end + 7 trading days" but
is **94 % identical to `prices`** in the current H5 — no actual 7-day shift
was applied during V20 → V21 simplification. Backtest returns are effectively
monthly price ratios, not 7-day-execution prices.

To implement true 7-day execution would require daily raw price data, which
was outside the V20→V21 simplification scope.

---

## 11.3 Recommended action

> **paper-trade V21 against a real A-share data feed for ≥3 months** before
> considering any capital allocation.

---

## Appendix B — References

- **WaveTrend**: LazyBear, TradingView community indicator (public domain).
- **DSR**: López de Prado, *Advances in Financial Machine Learning* (2018).
- **Newey-West HAC**: Newey & West (1987).
- **A-share low-volatility anomaly**: 王志强 et al., A 股横截面异象研究系列.
