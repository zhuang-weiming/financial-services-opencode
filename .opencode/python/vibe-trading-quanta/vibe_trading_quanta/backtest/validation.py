"""Statistical validation for backtest results.

Four independent tools:
  - Monte Carlo permutation test: is the strategy significantly better than random?
  - Bootstrap Sharpe CI: how stable is the risk-adjusted return?
  - Walk-Forward analysis: is performance consistent across time windows?
  - Deflated Sharpe Ratio (López de Prado 2018): corrects Sharpe for the
    number of configurations tried before declaring a winner.

Usage: called automatically by BaseEngine.run_backtest when config[\"validation\"]
is present, or invoked directly on backtest outputs.
"""

from __future__ import annotations

import json
import math
from numbers import Integral, Real
from pathlib import Path
from typing import Any, Dict, List

import numpy as np
import pandas as pd

from backtest.models import TradeRecord


# ─── Monte Carlo Permutation Test ───


def monte_carlo_test(
    trades: List[TradeRecord],
    initial_capital: float,
    n_simulations: int = 1000,
    seed: int = 42,
) -> Dict[str, Any]:
    """Shuffle trade PnL order to test path significance.

    Null hypothesis: the observed Sharpe / max-drawdown is no better than
    a random ordering of the same trades.

    Args:
        trades: Completed round-trip trades from backtest.
        initial_capital: Starting capital.
        n_simulations: Number of random permutations.
        seed: Random seed for reproducibility.

    Returns:
        Dict with actual_sharpe, p_value_sharpe, actual_max_dd,
        p_value_max_dd, simulated_sharpes (percentiles).
    """
    if isinstance(n_simulations, bool) or not isinstance(n_simulations, Integral) or n_simulations < 1:
        return {
            "error": f"n_simulations must be >= 1, got {n_simulations}",
            "p_value_sharpe": 1.0,
        }
    if isinstance(seed, bool) or not isinstance(seed, Integral) or seed < 0:
        return {"error": f"seed must be >= 0, got {seed}", "p_value_sharpe": 1.0}
    if len(trades) < 3:
        return {"error": "need at least 3 trades", "p_value_sharpe": 1.0}

    pnls = np.array([t.pnl for t in trades])
    actual = _path_metrics(pnls, initial_capital)

    rng = np.random.default_rng(seed)
    sharpe_count = 0
    dd_count = 0
    sim_sharpes = []

    for _ in range(n_simulations):
        shuffled = rng.permutation(pnls)
        sim = _path_metrics(shuffled, initial_capital)
        sim_sharpes.append(sim["sharpe"])
        if sim["sharpe"] >= actual["sharpe"]:
            sharpe_count += 1
        if sim["max_dd"] >= actual["max_dd"]:  # less negative = "better"
            dd_count += 1

    sim_arr = np.array(sim_sharpes)
    return {
        "actual_sharpe": round(actual["sharpe"], 4),
        "actual_max_dd": round(actual["max_dd"], 4),
        "p_value_sharpe": round(sharpe_count / n_simulations, 4),
        "p_value_max_dd": round(dd_count / n_simulations, 4),
        "simulated_sharpe_mean": round(float(sim_arr.mean()), 4),
        "simulated_sharpe_std": round(float(sim_arr.std()), 4),
        "simulated_sharpe_p5": round(float(np.percentile(sim_arr, 5)), 4),
        "simulated_sharpe_p95": round(float(np.percentile(sim_arr, 95)), 4),
        "n_simulations": n_simulations,
        "n_trades": len(trades),
    }


def _path_metrics(pnls: np.ndarray, initial_capital: float) -> Dict[str, float]:
    """Compute Sharpe and max drawdown from a PnL sequence."""
    equity = initial_capital + np.cumsum(pnls)
    returns = np.diff(equity) / equity[:-1] if len(equity) > 1 else np.array([0.0])
    std = returns.std()
    sharpe = float(returns.mean() / (std + 1e-10) * np.sqrt(252))
    peak = np.maximum.accumulate(equity)
    dd = (equity - peak) / np.where(peak > 0, peak, 1.0)
    max_dd = float(dd.min())
    return {"sharpe": sharpe, "max_dd": max_dd}


# ─── Bootstrap Sharpe CI ───


def bootstrap_sharpe_ci(
    equity_curve: pd.Series,
    n_bootstrap: int = 1000,
    confidence: float = 0.95,
    bars_per_year: int = 252,
    seed: int = 42,
) -> Dict[str, Any]:
    """Resample daily returns to estimate Sharpe confidence interval.

    Args:
        equity_curve: Equity time series.
        n_bootstrap: Number of bootstrap samples.
        confidence: Confidence level (e.g. 0.95 for 95% CI).
        bars_per_year: Annualisation factor.
        seed: Random seed.

    Returns:
        Dict with observed_sharpe, ci_lower, ci_upper, median_sharpe,
        prob_positive (fraction of samples with Sharpe > 0).
    """
    if isinstance(n_bootstrap, bool) or not isinstance(n_bootstrap, Integral) or n_bootstrap < 1:
        return {"error": f"n_bootstrap must be >= 1, got {n_bootstrap}"}
    if (
        isinstance(confidence, bool)
        or not isinstance(confidence, Real)
        or not math.isfinite(float(confidence))
        or not 0.0 < confidence < 1.0
    ):
        return {"error": f"confidence must be in (0, 1), got {confidence}"}
    if isinstance(seed, bool) or not isinstance(seed, Integral) or seed < 0:
        return {"error": f"seed must be >= 0, got {seed}"}

    returns = equity_curve.pct_change().dropna().values
    if len(returns) < 5:
        return {"error": "need at least 5 return observations"}

    observed = _sharpe(returns, bars_per_year)

    rng = np.random.default_rng(seed)
    boot_sharpes = []
    for _ in range(n_bootstrap):
        sample = rng.choice(returns, size=len(returns), replace=True)
        boot_sharpes.append(_sharpe(sample, bars_per_year))

    arr = np.array(boot_sharpes)
    alpha = (1 - confidence) / 2
    lower = float(np.percentile(arr, alpha * 100))
    upper = float(np.percentile(arr, (1 - alpha) * 100))
    prob_pos = float(np.mean(arr > 0))

    return {
        "observed_sharpe": round(observed, 4),
        "ci_lower": round(lower, 4),
        "ci_upper": round(upper, 4),
        "median_sharpe": round(float(np.median(arr)), 4),
        "prob_positive": round(prob_pos, 4),
        "confidence": confidence,
        "n_bootstrap": n_bootstrap,
    }


def _sharpe(returns: np.ndarray, bars_per_year: int = 252) -> float:
    std = returns.std()
    return float(returns.mean() / (std + 1e-10) * np.sqrt(bars_per_year))


# ─── Walk-Forward Analysis ───


def walk_forward_analysis(
    equity_curve: pd.Series,
    trades: List[TradeRecord],
    n_windows: int = 5,
    bars_per_year: int = 252,
) -> Dict[str, Any]:
    """Split backtest into sequential windows, check consistency.

    Each window is evaluated independently (returns normalised to window start).

    Args:
        equity_curve: Equity time series.
        trades: Completed trades.
        n_windows: Number of non-overlapping windows.
        bars_per_year: Annualisation factor.

    Returns:
        Dict with per_window stats, consistency metrics.
    """
    if isinstance(n_windows, bool) or not isinstance(n_windows, Integral) or n_windows < 1:
        return {"error": f"n_windows must be >= 1, got {n_windows}"}
    if len(equity_curve) < n_windows * 2:
        return {"error": f"need at least {n_windows * 2} bars for {n_windows} windows"}

    indices = equity_curve.index
    window_size = len(indices) // n_windows
    windows = []

    for i in range(n_windows):
        start_idx = i * window_size
        end_idx = (i + 1) * window_size if i < n_windows - 1 else len(indices)
        win_eq = equity_curve.iloc[start_idx:end_idx]
        win_start = indices[start_idx]
        win_end = indices[end_idx - 1]

        # Per-window trades
        win_trades = [t for t in trades if win_start <= t.entry_time <= win_end]

        # Per-window metrics
        ret = float(win_eq.iloc[-1] / win_eq.iloc[0] - 1) if win_eq.iloc[0] > 0 else 0.0
        win_returns = win_eq.pct_change().dropna().values
        sharpe = _sharpe(win_returns, bars_per_year) if len(win_returns) > 1 else 0.0

        peak = win_eq.cummax()
        dd = (win_eq - peak) / peak.replace(0, 1)
        max_dd = float(dd.min())

        win_pnls = [t.pnl for t in win_trades]
        win_rate = len([p for p in win_pnls if p > 0]) / len(win_pnls) if win_pnls else 0.0

        windows.append(
            {
                "window": i + 1,
                "start": str(win_start.date()) if hasattr(win_start, "date") else str(win_start),
                "end": str(win_end.date()) if hasattr(win_end, "date") else str(win_end),
                "return": round(ret, 6),
                "sharpe": round(sharpe, 4),
                "max_dd": round(max_dd, 6),
                "trades": len(win_trades),
                "win_rate": round(win_rate, 4),
            }
        )

    # Consistency metrics
    returns_list = [w["return"] for w in windows]
    sharpes_list = [w["sharpe"] for w in windows]
    profitable_windows = sum(1 for r in returns_list if r > 0)

    return {
        "n_windows": n_windows,
        "windows": windows,
        "profitable_windows": profitable_windows,
        "consistency_rate": round(profitable_windows / n_windows, 4),
        "return_mean": round(float(np.mean(returns_list)), 6),
        "return_std": round(float(np.std(returns_list)), 6),
        "sharpe_mean": round(float(np.mean(sharpes_list)), 4),
        "sharpe_std": round(float(np.std(sharpes_list)), 4),
    }


# ─── Deflated Sharpe Ratio (López de Prado 2018, Eqs 12.7-12.8) ───


def deflated_sharpe_ratio(
    returns: pd.Series,
    n_configs: int = 5,
    rf_annual: float = 0.02,
    bars_per_year: int = 12,
    seed: int = 42,
) -> Dict[str, Any]:
    """Deflated Sharpe Ratio per López de Prado (2018) Eq 12.7-12.8.

    Multiple-testing correction: when you tried N strategy variants before
    declaring a "winner", even an excellent Sharpe may be an overfit extreme.
    DSR compares the observed Sharpe to the benchmark ``sr_star`` — the
    Sharpe you would expect under N IID trials by pure luck — and returns
    P(observed SR > sr_star) as the deflated significance.

    Args:
        returns: Periodic returns. Frequency must match ``bars_per_year``.
                 Monthly returns → ``bars_per_year=12``; daily returns → 252;
                 crypto → 365.
        n_configs: Number of independent strategy configurations tried
                   before declaring "winner". Default 5.
        rf_annual: Annualised risk-free rate. Default 0.02.
        bars_per_year: Return-frequency → annualisation factor. 12 (monthly,
                       A-share research default), 252 (daily, US/HK equity
                       default), 365 (crypto).
        seed: Reserved for future stochastic DSR variants. Current closed-form
              implementation is deterministic.

    Returns:
        Dict with keys (all numeric rounded to 4 decimals):
          - dsr           (float, [0,1])   Deflated Sharpe Ratio — probability
                                          that observed SR exceeds the
                                          multiple-test benchmark.
          - sr_observed   (float)          Annualised Sharpe of input returns.
          - sr_benchmark  (float, >=0)     sr_star — "would-be-lucky" Sharpe
                                          threshold under n_configs trials.
                                          If sr_observed <= sr_benchmark the
                                          strategy is likely overfit.
          - skewness      (float)          Pearson skewness of returns.
          - kurtosis      (float)          Pearson total kurtosis (excess + 3).
          - n_obs         (int)            Number of return observations.
          - n_configs     (int)            Echo of input.
          - bars_per_year (int)            Echo of input.
          - rf_annual     (float)          Echo of input.

    Examples:
        >>> dsr = deflated_sharpe_ratio(monthly_returns, n_configs=5)
        >>> dsr['dsr']
        0.873

        >>> dsr = deflated_sharpe_ratio(daily_returns, n_configs=10,
        ...                              bars_per_year=252)

    References:
        López de Prado, M. (2018). *Advances in Financial Machine Learning*.
        Chapter 14, Section 14.7 (The Deflated Sharpe Ratio), Eqs 12.7-12.8.
    """
    if (
        isinstance(n_configs, bool)
        or not isinstance(n_configs, Integral)
        or n_configs < 1
    ):
        return {
            "error": f"n_configs must be >= 1, got {n_configs}",
            "dsr": float("nan"),
        }
    if (
        isinstance(bars_per_year, bool)
        or not isinstance(bars_per_year, Integral)
        or bars_per_year < 1
    ):
        return {
            "error": f"bars_per_year must be >= 1, got {bars_per_year}",
            "dsr": float("nan"),
        }
    if isinstance(seed, bool) or not isinstance(seed, Integral) or seed < 0:
        return {
            "error": f"seed must be >= 0, got {seed}",
            "dsr": float("nan"),
        }
    if (
        isinstance(rf_annual, bool)
        or not isinstance(rf_annual, Real)
        or not math.isfinite(float(rf_annual))
        or float(rf_annual) < 0.0
    ):
        return {
            "error": f"rf_annual must be >= 0, got {rf_annual}",
            "dsr": float("nan"),
        }

    rets = returns.dropna()
    if len(rets) < 5:
        return {
            "error": "need at least 5 return observations for skew/kurtosis",
            "dsr": float("nan"),
        }

    n = len(rets)
    rf_periodic = float(rf_annual) / float(bars_per_year)
    sr_periodic = (rets.mean() - rf_periodic) / rets.std()
    sr_annual = float(sr_periodic * np.sqrt(float(bars_per_year)))
    skew = float(rets.skew())
    kurt = float(rets.kurtosis() + 3.0)

    try:
        from scipy import stats as sp_stats

        e_max_z = sp_stats.norm.ppf(1.0 - 1.0 / (n_configs + 1))
        var_sr_raw = max(
            1e-9,
            1.0 - skew * sr_annual + (kurt - 1.0) / 4.0 * sr_annual ** 2,
        )
        V_SR = var_sr_raw / (n - 1)
        # LdP 2018 Eq 12.8: sr_star has two terms. The second term blows up when
        # n_configs=1 (e_max_z=0); we treat that degenerate case as "no second
        # term" since with a single trial the correction reduces to the standard
        # SR p-value. The sr_star clamp below further absorbs any residual sign.
        if e_max_z > 1e-9:
            sr_star = (
                e_max_z * np.sqrt(V_SR)
                + (e_max_z ** 2 - 1.0) * V_SR / 2.0 / e_max_z
            )
        else:
            sr_star = e_max_z * np.sqrt(V_SR)
        sr_star = max(float(sr_star), 0.0)
        dsr_val = sp_stats.norm.cdf(
            (sr_annual - sr_star) * np.sqrt(n - 1) / np.sqrt(var_sr_raw)
        )
        dsr_val = float(np.clip(dsr_val, 0.0, 1.0))
    except Exception as exc:
        return {"error": f"DSR computation failed: {exc}", "dsr": float("nan")}

    return {
        "dsr":           round(dsr_val, 4),
        "sr_observed":   round(sr_annual, 4),
        "sr_benchmark":  round(sr_star, 4),
        "skewness":      round(skew, 4),
        "kurtosis":      round(kurt, 4),
        "n_obs":         int(n),
        "n_configs":     int(n_configs),
        "bars_per_year": int(bars_per_year),
        "rf_annual":     round(float(rf_annual), 6),
    }


# ─── Runner integration ───


def run_validation(
    config: Dict[str, Any],
    equity_curve: pd.Series,
    trades: List[TradeRecord],
    initial_capital: float,
    bars_per_year: int = 252,
) -> Dict[str, Any]:
    """Run configured validation checks.

    Reads from config["validation"]:
      - monte_carlo: {n_simulations, seed}
      - bootstrap: {n_bootstrap, confidence, seed}
      - walk_forward: {n_windows}
      - deflated_sharpe: {n_configs, rf_annual, seed}

    Args:
        config: Backtest config (must contain "validation" key).
        equity_curve: Equity time series.
        trades: Completed trades.
        initial_capital: Starting capital.
        bars_per_year: Annualisation factor.

    Returns:
        Dict keyed by validation type with results.
    """
    v_cfg = config.get("validation", {})
    results: Dict[str, Any] = {}

    if "monte_carlo" in v_cfg:
        mc_cfg = v_cfg["monte_carlo"] if isinstance(v_cfg["monte_carlo"], dict) else {}
        results["monte_carlo"] = monte_carlo_test(
            trades,
            initial_capital,
            n_simulations=mc_cfg.get("n_simulations", 1000),
            seed=mc_cfg.get("seed", 42),
        )

    if "bootstrap" in v_cfg:
        bs_cfg = v_cfg["bootstrap"] if isinstance(v_cfg["bootstrap"], dict) else {}
        results["bootstrap"] = bootstrap_sharpe_ci(
            equity_curve,
            bars_per_year=bars_per_year,
            n_bootstrap=bs_cfg.get("n_bootstrap", 1000),
            confidence=bs_cfg.get("confidence", 0.95),
            seed=bs_cfg.get("seed", 42),
        )

    if "walk_forward" in v_cfg:
        wf_cfg = v_cfg["walk_forward"] if isinstance(v_cfg["walk_forward"], dict) else {}
        results["walk_forward"] = walk_forward_analysis(
            equity_curve,
            trades,
            n_windows=wf_cfg.get("n_windows", 5),
            bars_per_year=bars_per_year,
        )

    if "deflated_sharpe" in v_cfg:
        ds_cfg = (
            v_cfg["deflated_sharpe"]
            if isinstance(v_cfg["deflated_sharpe"], dict)
            else {}
        )
        results["deflated_sharpe"] = deflated_sharpe_ratio(
            equity_curve.pct_change().dropna(),
            n_configs=ds_cfg.get("n_configs", 5),
            rf_annual=ds_cfg.get("rf_annual", 0.02),
            bars_per_year=bars_per_year,
            seed=ds_cfg.get("seed", 42),
        )

    return results


# ─── Standalone CLI ───


def _load_equity(run_dir: Path) -> pd.Series:
    """Load equity curve from artifacts/equity.csv."""
    path = run_dir / "artifacts" / "equity.csv"
    df = pd.read_csv(path, index_col=0, parse_dates=True)
    return df["equity"]


def _load_trades(run_dir: Path) -> List[TradeRecord]:
    """Load trades from artifacts/trades.csv and convert to TradeRecord list."""
    path = run_dir / "artifacts" / "trades.csv"
    df = pd.read_csv(path)
    if df.empty:
        return []

    # trades.csv has entry+exit row pairs; extract exit rows (they have pnl != 0)
    trades = []
    exit_rows = df[df["pnl"] != 0].reset_index(drop=True)
    for _, row in exit_rows.iterrows():
        trades.append(
            TradeRecord(
                symbol=str(row.get("code", "")),
                direction=1 if row.get("side") == "sell" else -1,
                entry_price=0.0,
                exit_price=float(row.get("price", 0)),
                entry_time=pd.Timestamp(row.get("timestamp", "2000-01-01")),
                exit_time=pd.Timestamp(row.get("timestamp", "2000-01-01")),
                size=float(row.get("qty", 0)),
                leverage=1.0,
                pnl=float(row.get("pnl", 0)),
                pnl_pct=float(row.get("return_pct", 0)),
                exit_reason=str(row.get("reason", "signal")),
                holding_bars=int(row.get("holding_days", 0)),
                commission=0.0,
            )
        )
    return trades


def _parse_run_dir(argv: List[str]) -> Path:
    """Validate CLI input and return a usable run directory path."""
    if len(argv) < 2:
        raise SystemExit("Usage: python -m backtest.validation <run_dir>")

    raw_run_dir = argv[1]
    if not raw_run_dir.strip():
        raise SystemExit("run_dir must be a non-empty path")
    if "\0" in raw_run_dir:
        raise SystemExit("Invalid run_dir path: embedded NUL byte")

    try:
        run_dir = Path(raw_run_dir).expanduser()
        exists = run_dir.exists()
        is_dir = run_dir.is_dir() if exists else False
    except (OSError, RuntimeError, ValueError) as exc:
        raise SystemExit(f"Invalid run_dir path: {exc}") from exc

    if not exists:
        raise SystemExit(f"run_dir does not exist: {run_dir}")
    if not is_dir:
        raise SystemExit(f"run_dir is not a directory: {run_dir}")
    return run_dir


def _json_safe(value: Any) -> Any:
    """Return a JSON-strict copy of validation results."""
    if isinstance(value, np.ndarray):
        return [_json_safe(item) for item in value.tolist()]
    if isinstance(value, np.generic):
        return _json_safe(value.item())
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    return value


def write_validation_json(path: Path, results: Dict[str, Any]) -> Dict[str, Any]:
    """Write validation results to ``path`` as strict, RFC-8259 JSON.

    A validation metric can be non-finite (e.g. a Sharpe computed from a path
    whose equity touches zero), and ``json.dumps`` emits bare ``NaN`` /
    ``Infinity`` tokens for those by default (``allow_nan=True``) — tokens that
    strict parsers reject. Sanitize with :func:`_json_safe` (non-finite → null)
    and serialize with ``allow_nan=False`` so every writer of
    ``artifacts/validation.json`` produces the same valid JSON. Returns the
    sanitized payload that was written.
    """
    safe_results = _json_safe(results)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(safe_results, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    return safe_results


def main(run_dir: Path) -> Dict[str, Any]:
    """Run all four validations on existing backtest artifacts.

    Reads equity.csv, trades.csv, and config.json from run_dir.

    Args:
        run_dir: Directory with artifacts/ subdirectory.

    Returns:
        Validation results dict.
    """
    # Load config for initial_cash and bars_per_year
    config_path = run_dir / "config.json"
    if config_path.exists():
        config = json.loads(config_path.read_text(encoding="utf-8"))
    else:
        config = {}
    initial_capital = config.get("initial_cash", 1_000_000)
    bars_per_year = config.get("bars_per_year", 252)

    equity = _load_equity(run_dir)
    trades = _load_trades(run_dir)

    results = {
        "monte_carlo":     monte_carlo_test(trades, initial_capital),
        "bootstrap":       bootstrap_sharpe_ci(equity, bars_per_year=bars_per_year),
        "walk_forward":    walk_forward_analysis(equity, trades, bars_per_year=bars_per_year),
        "deflated_sharpe": deflated_sharpe_ratio(
            equity.pct_change().dropna(), bars_per_year=bars_per_year
        ),
    }

    out = run_dir / "artifacts" / "validation.json"
    safe_results = write_validation_json(out, results)

    print(json.dumps(safe_results, indent=2, allow_nan=False))
    return safe_results


if __name__ == "__main__":
    import sys

    main(_parse_run_dir(sys.argv))
