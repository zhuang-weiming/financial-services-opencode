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


def compute_csi(prices: pd.DataFrame) -> pd.Series:
    f29 = prices.get("F29_bp", prices.get("F29", None))
    if f29 is None:
        raise ValueError("prices must contain 'F29_bp' or 'F29' column")
    z_f29 = (f29 - f29.rolling(60).mean()) / f29.rolling(60).std().replace(0, np.nan)

    vixt = prices.get("VIXTERM", None)
    if vixt is None:
        raise ValueError("prices must contain 'VIXTERM' column")
    z_vixt = (vixt - vixt.rolling(60).mean()) / vixt.rolling(60).std().replace(0, np.nan)

    corr_cols = [c for c in prices.columns if c in ("SPY", "BND", "GLD", "TLT")]
    if len(corr_cols) >= 2:
        returns = prices[corr_cols].pct_change()
        pairwise_corrs = []
        for i in range(len(corr_cols)):
            for j in range(i + 1, len(corr_cols)):
                pairwise_corrs.append(returns[corr_cols[i]].rolling(60).corr(returns[corr_cols[j]]))
        avg_corr = pd.concat(pairwise_corrs, axis=1).mean(axis=1) if pairwise_corrs else pd.Series(0, index=prices.index)
    else:
        avg_corr = pd.Series(0, index=prices.index)
    z_corr = (avg_corr - avg_corr.rolling(60).mean()) / avg_corr.rolling(60).std().replace(0, np.nan)

    csi = (0.45 * z_f29.fillna(0) + 0.35 * z_vixt.fillna(0) + 0.20 * z_corr.fillna(0))
    return csi.fillna(0)


def phase1_status(prices: pd.DataFrame, csi: pd.Series | None = None) -> pd.Series:
    if csi is None:
        csi = compute_csi(prices)
    df = prices.copy()
    df["CSI"] = csi

    df["CSI_EMERGENCY"] = (df["CSI"] > 2.0).astype(int)
    df["CSI_WARNING"] = ((df["CSI"] > 1.0) & (df["CSI"] <= 2.0)).astype(int)
    df["CSI_below_1"] = (df["CSI"] < 1.0).astype(int)
    df["CSI_exit_count"] = df["CSI_below_1"].rolling(5).sum()
    df["CSI_healthy_5d"] = (df["CSI_exit_count"] == 5).astype(int)
    df["EMERGENCY_persist"] = df["CSI_EMERGENCY"].rolling(3).sum()
    df["WARNING_persist"] = df["CSI_WARNING"].rolling(3).sum()
    df["EMERGENCY_3d"] = (df["EMERGENCY_persist"] == 3).astype(int)
    df["WARNING_3d"] = (df["WARNING_persist"] == 3).astype(int)

    vixt = df.get("VIXTERM", pd.Series(0, index=df.index))
    df["VIX_10d_return"] = df["VIX"].pct_change(10).fillna(0) if "VIX" in df.columns else 0
    df["F33b_trigger"] = ((df["VIX"] > F33B_VIX_THRESHOLD) & (df["VIX_10d_return"] > F33B_VIX_10D_RETURN)).astype(int) if "VIX" in df.columns else 0
    df["F33b_EMERGENCY_override"] = ((df["CSI"] <= 2.0) & (df["F33b_trigger"] == 1)).astype(int)

    f29 = df.get("F29_bp", df.get("F29", pd.Series(0, index=df.index)))
    if isinstance(f29, pd.Series):
        df["F29_hard_trigger"] = (f29 > F29_EMERGENCY_THRESHOLD_BP).astype(int)
    else:
        df["F29_hard_trigger"] = 0
    df["F29_EMERGENCY_override"] = ((df["CSI"] <= 2.0) & (df["F29_hard_trigger"] == 1)).astype(int)

    df["Phase1_candidate"] = np.select(
        [
            (df["EMERGENCY_3d"] == 1) | (df["F33b_EMERGENCY_override"] == 1) | (df["F29_EMERGENCY_override"] == 1),
            df["WARNING_3d"] == 1,
            df["CSI_healthy_5d"] == 1,
        ],
        ["EMERGENCY", "WARNING", "HEALTHY"],
        default=None,
    )
    result = df["Phase1_candidate"].ffill().bfill()
    return result


def macro_quadrant(prices: pd.DataFrame) -> pd.Series:
    has_real = "DFII10" in prices.columns or ("DGS10" in prices.columns and "T10YIE" in prices.columns)
    if has_real:
        real = prices.get("DFII10", prices["DGS10"] - prices["T10YIE"])
    else:
        real = pd.Series(0, index=prices.index)
    inf = prices.get("T10YIE", pd.Series(2.5, index=prices.index))
    real_delta = real.diff(60)
    inf_delta = inf.diff(60)
    quad = np.select(
        [
            (real_delta < 0) & (inf_delta < 0),
            (real_delta < 0) & (inf_delta >= 0),
            (real_delta >= 0) & (inf_delta >= 0),
            (real_delta >= 0) & (inf_delta < 0),
        ],
        [1, 2, 3, 4],
        default=2,
    )
    return pd.Series(quad, index=prices.index).ffill().bfill().astype(int)


def current_phase(prices: pd.DataFrame) -> dict:
    p1 = phase1_status(prices)
    quad = macro_quadrant(prices)
    latest_p1 = p1.iloc[-1]
    latest_quad = int(quad.iloc[-1])

    phase_map = {
        ("HEALTHY", 2): 1,
        ("HEALTHY", 4): 1,
        ("EMERGENCY", None): 2,
        ("HEALTHY", 1): 3,
        ("HEALTHY", 3): 3,
        ("WARNING", None): 4,
    }
    phase = phase_map.get((latest_p1, latest_quad), phase_map.get((latest_p1, None), 5))

    result = {
        "phase": phase,
        "phase1_status": latest_p1,
        "macro_quadrant": latest_quad,
        "date": str(prices.index[-1].date()) if hasattr(prices.index[-1], "date") else str(prices.index[-1]),
    }

    for col in ("F29_bp", "F29", "VIX", "VIXTERM", "DGS10", "T10YIE"):
        if col in prices.columns:
            result[col.lower()] = round(float(prices[col].iloc[-1]), 2) if pd.notna(prices[col].iloc[-1]) else None
    return result
