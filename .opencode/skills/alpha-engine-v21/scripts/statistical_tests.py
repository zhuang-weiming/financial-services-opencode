"""statistical_tests.py — V21 statistical battery.

Combines the Deflated Sharpe Ratio (delegated to
``src.quantlib.multipletesting.deflated_sharpe_ratio``) with V21's
own monthly-frequency-specific tests: Z-test (IID), Z-test (Newey-West HAC),
Bonferroni multiple-testing correction, and a 12-month-block bootstrap CI.

All non-DSR tests are kept here rather than in ``validation.py`` because:

  * They use a hardcoded ``block_size=12`` matching monthly-bar A-share
    research (US-equity workflows need a different block size — that's a
    separate validation concern).
  * They live next to the V21 strategy, so a future V22 / V23 release can
    evolve the battery without touching the core engine.

Output schema preserves V21.0's original field names (``sharpe``, ``sharpe_annual``,
``p_iid``, ``p_nw``, ``p_bonferroni``, ``bootstrap_ci_95``, ``bootstrap_p_positive``,
``dsr``, ``skewness``, ``kurtosis_total``, ``n_months``) for byte-level
backward compatibility with V21.0's published JSON outputs.
"""
import warnings

warnings.filterwarnings("ignore")

from typing import Dict

import numpy as np
import pandas as pd


def _resolve_dsr():
    """Locate the canonical DSR function in the vendored vibe-trading-ai tree.

    v0.1.15 consolidated the Quant Library: the Deflated Sharpe Ratio now lives
    in ``src.quantlib.multipletesting`` (was ``backtest.validation`` pre-0.1.15).
    The v0.1.15 signature takes pre-computed statistics rather than a returns
    series, so the caller below derives ``trial_sharpe_std`` the same way the
    old ``backtest.validation`` implementation did.
    """
    try:
        from src.quantlib.multipletesting import deflated_sharpe_ratio  # type: ignore

        return deflated_sharpe_ratio
    except ImportError:
        return None


def honest_statistical_tests(
    returns: pd.Series,
    n_configs: int = 5,
    rf_annual: float = 0.02,
) -> Dict[str, float]:
    """V21 statistical battery — 11 metrics + DSR.

    Args:
        returns: Monthly returns Series (V21 is monthly-frequency).
        n_configs: Number of strategy configurations tried before declaring
            the V21 winner (default 5). Feeds the Bonferroni correction and
            the DSR multiple-test benchmark.
        rf_annual: Annualised risk-free rate (default 0.02).

    Returns:
        Dict with V21.0-compatible keys:
            sharpe (monthly), sharpe_annual, n_months, skewness, kurtosis_total,
            z_iid, p_iid, z_nw, p_nw, p_bonferroni, bootstrap_ci_95,
            bootstrap_p_positive, dsr.
    """
    from scipy import stats as sp_stats

    rf_monthly = rf_annual / 12
    sr_monthly = (returns.mean() - rf_monthly) / returns.std()
    sr_annual = sr_monthly * np.sqrt(12)
    n = len(returns)
    skew = returns.skew()
    kurt = returns.kurtosis() + 3

    z_iid = sr_monthly * np.sqrt(n)
    p_iid = 1 - sp_stats.norm.cdf(z_iid)

    nw_lags = int(n ** 0.25)
    auto_cov = np.array(
        [returns.autocorr(lag=i) for i in range(1, nw_lags + 1)]
    )
    w = 1 - np.arange(1, nw_lags + 1) / (nw_lags + 1)
    adjustment = (
        1 + 2 * np.sum(w * auto_cov) if len(auto_cov) > 0 else 1
    )
    se_nw = (
        returns.std() / np.sqrt(n) * np.sqrt(adjustment)
        if adjustment > 0
        else returns.std() / np.sqrt(n)
    )
    z_nw = (returns.mean() - rf_monthly) / se_nw
    p_nw = 1 - sp_stats.norm.cdf(z_nw)

    p_bonferroni = min(p_iid * n_configs, 1.0)

    np.random.seed(42)
    block_size = 12
    n_blocks = int(np.ceil(n / block_size))
    boot_srs = np.zeros(10000)
    for b in range(10000):
        blocks = np.random.choice(n - block_size + 1, n_blocks)
        idx = np.concatenate(
            [np.arange(s, s + block_size) for s in blocks]
        )[:n]
        boot_srs[b] = (
            returns.iloc[idx].mean()
            / returns.iloc[idx].std()
            * np.sqrt(12)
        )
    p_bootstrap = (boot_srs <= 0).mean()
    ci_lower = np.percentile(boot_srs, 2.5)
    ci_upper = np.percentile(boot_srs, 97.5)

    dsr_fn = _resolve_dsr()
    dsr_val = float("nan")
    if dsr_fn is not None:
        try:
            # v0.1.15 signature (src.quantlib.multipletesting): pre-computed stats.
            # Derive trial_sharpe_std the way the pre-0.1.15 implementation did:
            #   var_sr_raw = 1 - skew*SR + (kurt-1)/4 * SR^2 ; V_SR = var_sr_raw/(n-1)
            var_sr_raw = max(
                1e-9,
                1.0 - float(skew) * float(sr_annual)
                + (float(kurt) - 1.0) / 4.0 * float(sr_annual) ** 2,
            )
            trial_sharpe_std = float(np.sqrt(var_sr_raw / (n - 1)))
            dsr_result = dsr_fn(
                observed_sharpe=float(sr_monthly),
                n_trials=int(n_configs),
                n_observations=int(n),
                trial_sharpe_std=trial_sharpe_std,
                skew=float(skew),
                kurtosis=float(kurt),
            )
            dsr_val = float(getattr(dsr_result, "deflated_sharpe_ratio", float("nan")))
        except TypeError:
            # Legacy signature (pre-0.1.15 backtest.validation): returns series.
            try:
                dsr_result = dsr_fn(
                    returns, n_configs=n_configs, rf_annual=rf_annual, bars_per_year=12
                )
                dsr_val = float(dsr_result.get("dsr", float("nan")))
            except Exception:
                dsr_val = float("nan")
        except Exception:
            dsr_val = float("nan")
    if not np.isfinite(dsr_val):
        dsr_val = 0.0

    return {
        "sharpe":                round(float(sr_monthly), 3),
        "sharpe_annual":         round(float(sr_annual), 3),
        "n_months":              n,
        "skewness":              round(float(skew), 3),
        "kurtosis_total":        round(float(kurt), 3),
        "z_iid":                 round(float(z_iid), 3),
        "p_iid":                 round(float(p_iid), 4),
        "z_nw":                  round(float(z_nw), 3),
        "p_nw":                  round(float(p_nw), 4),
        "p_bonferroni":          round(float(p_bonferroni), 4),
        "bootstrap_ci_95":       [round(float(ci_lower), 3), round(float(ci_upper), 3)],
        "bootstrap_p_positive":  round(float(1 - p_bootstrap), 4),
        "dsr":                   round(float(dsr_val), 4),
    }
