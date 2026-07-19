"""statistical_tests.py — V21 statistical battery.

Combines the Deflated Sharpe Ratio (delegated to
``vibe_trading_quanta.backtest.validation.deflated_sharpe_ratio``) with V21's
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
    """Locate the canonical DSR function in vibe-trading-quanta.

    The ``vibe_trading_quanta.backtest.validation`` module internally uses
    ``from backtest.models import TradeRecord`` (absolute-style imports). Those
    imports only resolve when the package's inner directory is on ``sys.path``,
    not the outer one. So we try three strategies in order:

      1. ``backtest.validation`` already importable → use it.
      2. Inject the inner package dir onto ``sys.path`` and try again.
      3. Fall back to ``vibe_trading_quanta.backtest.validation`` (works if the
         caller has set up the editable install correctly).
    """
    try:
        from backtest.validation import deflated_sharpe_ratio  # type: ignore

        return deflated_sharpe_ratio
    except ImportError:
        pass

    try:
        import os
        import vibe_trading_quanta as _pkg  # noqa: F401

        pkg_root = os.path.dirname(os.path.abspath(_pkg.__file__))
        if pkg_root not in __import__("sys").path:
            __import__("sys").path.insert(0, pkg_root)
        from backtest.validation import deflated_sharpe_ratio  # type: ignore

        return deflated_sharpe_ratio
    except ImportError:
        pass

    from vibe_trading_quanta.backtest.validation import deflated_sharpe_ratio  # type: ignore

    return deflated_sharpe_ratio


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

    deflated_sharpe_ratio = _resolve_dsr()
    dsr_result = deflated_sharpe_ratio(
        returns,
        n_configs=n_configs,
        rf_annual=rf_annual,
        bars_per_year=12,
    )
    dsr_val = dsr_result.get("dsr", float("nan"))
    if isinstance(dsr_val, float) and np.isnan(dsr_val):
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
