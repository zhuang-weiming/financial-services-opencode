from __future__ import annotations

from typing import Optional

import numpy as np
import pandas as pd

CSI_COMPONENTS = {
    "F29_weight": 0.45,
    "VIXTERM_weight": 0.35,
    "correlation_weight": 0.20,
}

F29_EMERGENCY_THRESHOLD_BP = 500
F33B_VIX_THRESHOLD = 40
F33B_VIX_10D_RETURN = 1.0


def _cap(s: pd.Series) -> pd.Series:
    return np.sign(s) * np.minimum(np.abs(s), 5.0)


def _zscore(s: pd.Series, window: int = 60) -> pd.Series:
    ma = s.rolling(window).mean()
    std = s.rolling(window).std().replace(0, np.nan)
    return ((s - ma) / std).replace([np.inf, -np.inf], np.nan).fillna(0.0)


def _has_coverage(s: Optional[pd.Series], minimum_observations: int) -> bool:
    return isinstance(s, pd.Series) and int(s.notna().sum()) >= minimum_observations


def compute_csi(prices: pd.DataFrame, minimum_observations: int = 60) -> pd.Series:
    """Compute the v5.9 Composite Stress Index using fixed component weights.

    Missing components contribute zero and are *not* rescaled. This preserves the
    documented 0.45/0.35/0.20 coefficients and prevents one- or two-component
    datasets from being artificially amplified.
    """

    csi = pd.Series(0.0, index=prices.index, dtype=float)

    f29 = prices.get("F29_bp", prices.get("F29", None))
    if _has_coverage(f29, minimum_observations):
        csi = csi.add(CSI_COMPONENTS["F29_weight"] * _zscore(f29), fill_value=0.0)

    vixt = prices.get("VIXTERM", None)
    if _has_coverage(vixt, minimum_observations):
        csi = csi.add(CSI_COMPONENTS["VIXTERM_weight"] * _zscore(vixt), fill_value=0.0)

    if {"SPY", "GLD"}.issubset(prices.columns):
        pair = prices[["SPY", "GLD"]]
        if pair.notna().all(axis=1).sum() >= minimum_observations + 20:
            returns = pair.pct_change(fill_method=None)
            corr_20d = returns["SPY"].rolling(20).corr(returns["GLD"])
            correlation_stress = -_zscore(corr_20d, window=60)
            csi = csi.add(
                CSI_COMPONENTS["correlation_weight"] * correlation_stress,
                fill_value=0.0,
            )

    return csi.replace([np.inf, -np.inf], np.nan).fillna(0.0)


def phase1_status(
    prices: pd.DataFrame,
    csi: Optional[pd.Series] = None,
    initial_status: str = "HEALTHY",
) -> pd.Series:
    """Return the confirmed Phase 1 state without future backfilling.

    F29 and F33b are immediate, independent EMERGENCY overrides. Soft CSI entry
    requires three consecutive observations; recovery requires five consecutive
    observations below 1.0. Until a confirmed transition occurs, the prior state
    is retained. The pre-signal portion is explicitly initialized as HEALTHY by
    default rather than backfilled from a future state.
    """

    valid_states = {"HEALTHY", "WARNING", "EMERGENCY"}
    if initial_status not in valid_states:
        raise ValueError(f"initial_status must be one of {sorted(valid_states)}")

    if csi is None:
        csi = compute_csi(prices)
    csi = csi.reindex(prices.index).fillna(0.0)

    soft_emergency = csi.gt(2.0)
    soft_warning = csi.gt(1.0) & csi.le(2.0)
    healthy = csi.lt(1.0)

    soft_emergency_3d = soft_emergency.rolling(3, min_periods=3).sum().eq(3)
    soft_warning_3d = soft_warning.rolling(3, min_periods=3).sum().eq(3)
    healthy_5d = healthy.rolling(5, min_periods=5).sum().eq(5)

    f29 = prices.get("F29_bp", prices.get("F29", None))
    if isinstance(f29, pd.Series):
        f29_hard_trigger = f29.reindex(prices.index).gt(F29_EMERGENCY_THRESHOLD_BP).fillna(False)
    else:
        f29_hard_trigger = pd.Series(False, index=prices.index)

    if "VIX" in prices.columns:
        vix = prices["VIX"].reindex(prices.index)
        vix_10d_return = vix.pct_change(10, fill_method=None)
        f33b_hard_trigger = (
            vix.gt(F33B_VIX_THRESHOLD)
            & vix_10d_return.gt(F33B_VIX_10D_RETURN)
        ).fillna(False)
    else:
        f33b_hard_trigger = pd.Series(False, index=prices.index)

    states: list[str] = []
    state = initial_status
    for i in range(len(prices.index)):
        if bool(f29_hard_trigger.iloc[i]) or bool(f33b_hard_trigger.iloc[i]):
            state = "EMERGENCY"
        elif bool(soft_emergency_3d.iloc[i]):
            state = "EMERGENCY"
        elif state == "EMERGENCY":
            if bool(healthy_5d.iloc[i]):
                state = "HEALTHY"
        elif bool(soft_warning_3d.iloc[i]):
            state = "WARNING"
        elif bool(healthy_5d.iloc[i]):
            state = "HEALTHY"
        states.append(state)

    return pd.Series(states, index=prices.index, name="Phase1_status", dtype="object")


def macro_quadrant_real_rate_fallback(prices: pd.DataFrame) -> pd.Series:
    """Explicit fallback using 60-day real-rate and breakeven changes."""

    if "DFII10" in prices.columns:
        real = prices["DFII10"]
    elif {"DGS10", "T10YIE"}.issubset(prices.columns):
        real = prices["DGS10"] - prices["T10YIE"]
    else:
        raise ValueError("real-rate fallback requires DFII10 or DGS10 + T10YIE")

    if "T10YIE" not in prices.columns:
        raise ValueError("real-rate fallback requires T10YIE")
    inflation = prices["T10YIE"]

    real_delta = real.diff(60)
    inflation_delta = inflation.diff(60)
    quadrant = np.select(
        [
            real_delta.lt(0) & inflation_delta.lt(0),
            real_delta.lt(0) & inflation_delta.ge(0),
            real_delta.ge(0) & inflation_delta.ge(0),
            real_delta.ge(0) & inflation_delta.lt(0),
        ],
        [1, 2, 3, 4],
        default=1,
    )
    return pd.Series(quadrant, index=prices.index, name="macro_quadrant").astype(int)


def macro_quadrant(prices: pd.DataFrame, fallback: Optional[str] = None) -> pd.Series:
    """Compute the international v5.9 SPY/TLT momentum quadrant.

    The default matches the reference backtest: 126-day momentum followed by a
    60-day rolling mean. The former real-rate implementation remains available
    only through ``fallback="real_rate"`` and is never selected silently.
    """

    if {"SPY", "TLT"}.issubset(prices.columns):
        spy_momentum = prices["SPY"].pct_change(126, fill_method=None).rolling(60).mean().fillna(0.0)
        tlt_momentum = prices["TLT"].pct_change(126, fill_method=None).rolling(60).mean().fillna(0.0)
        quadrant = np.select(
            [
                spy_momentum.gt(0) & tlt_momentum.lt(0),
                spy_momentum.gt(0) & tlt_momentum.gt(0),
                spy_momentum.lt(0) & tlt_momentum.lt(0),
                spy_momentum.lt(0) & tlt_momentum.gt(0),
            ],
            [2, 4, 3, 1],
            default=1,
        )
        return pd.Series(quadrant, index=prices.index, name="macro_quadrant").astype(int)

    if fallback == "real_rate":
        return macro_quadrant_real_rate_fallback(prices)
    if fallback is not None:
        raise ValueError("fallback must be None or 'real_rate'")
    raise ValueError("macro_quadrant requires SPY and TLT; use fallback='real_rate' explicitly")


def current_phase(prices: pd.DataFrame) -> dict:
    p1 = phase1_status(prices)
    quadrant = macro_quadrant(prices)
    latest_p1 = p1.iloc[-1]
    latest_quadrant = int(quadrant.iloc[-1])

    phase_map = {
        ("HEALTHY", 2): 1,
        ("HEALTHY", 4): 1,
        ("EMERGENCY", None): 2,
        ("HEALTHY", 1): 3,
        ("HEALTHY", 3): 3,
        ("WARNING", None): 4,
    }
    phase = phase_map.get((latest_p1, latest_quadrant), phase_map.get((latest_p1, None), 5))

    result = {
        "phase": phase,
        "phase1_status": latest_p1,
        "macro_quadrant": latest_quadrant,
        "date": str(prices.index[-1].date()) if hasattr(prices.index[-1], "date") else str(prices.index[-1]),
    }

    for col in ("F29_bp", "F29", "VIX", "VIXTERM", "DGS10", "T10YIE"):
        if col in prices.columns:
            raw = prices[col].iloc[-1]
            result[col.lower()] = round(float(raw), 2) if pd.notna(raw) else None
    return result
