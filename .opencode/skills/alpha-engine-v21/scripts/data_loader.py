"""data_loader.py — V21 HDF5 data loader with path resolution.

Resolution order (highest priority first):

  1. ``path`` argument (programmatic callers)
  2. ``V21_DATA_H5`` environment variable (deployment / CI overrides)
  3. ``config/v21_config.json`` ``data_h5`` field (skill-level config)
  4. ``<skill_root>/data/data_v20.h5`` (bundled default)

HDF5 structure (validated on load — raises ``FileNotFoundError`` or
``ValueError`` if a required dataset is missing):

  /prices              (n_dates × n_tickers)  monthly close prices
  /market_cap          (n_dates × n_tickers)  monthly market cap
  /industry            (JSON attr)            ticker → SW1 industry name
  /stock_names         (JSON attr)            ticker → Chinese name
  /universe_exclude    (JSON attr, optional)  data-quality / B-share excludes
  /wt/wt1_monthly      (n_dates × n_tickers)  LazyBear WT1 monthly level
  /wt/wt2_monthly      (n_dates × n_tickers)  WT2 = SMA(WT1, 4)
  /close_7d            (n_dates × n_tickers, optional)  execution-price panel
  /bad_returns_mask    (n_dates × n_tickers, optional)  data-quality flags

``sys_corrupt_months`` is hardcoded to an empty set in V21.0 — the H5
labelling was inconsistent (months with 2.5% NaN flagged corrupt while
months with 87% NaN traded freely), so V21 trades all months normally.
"""
import json
import os
from pathlib import Path
from typing import Dict, Optional

import h5py
import pandas as pd

SKILL_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_H5 = SKILL_ROOT / "data" / "data_v20.h5"
CONFIG_PATH = SKILL_ROOT / "config" / "v21_config.json"

REQUIRED_DATASETS = (
    "prices",
    "market_cap",
    "industry",
    "stock_names",
    "wt/wt1_monthly",
)


def resolve_data_path(cli_path: Optional[str] = None) -> Path:
    """Resolve the HDF5 path using the documented priority order.

    Resolution rules:

      * If ``cli_path`` is provided, **it must exist** — caller has explicitly
        asked for a path and a missing one is a configuration error.
      * If ``V21_DATA_H5`` env var is set, **it must exist** — overriding the
        default via env var is an explicit choice, and silent fallback to
        bundled data would mask misconfigured deployments.
      * If ``config/v21_config.json`` has a ``data_h5`` field, that path is
        tried (relative to the skill root). Missing is OK here because the
        config is shipped with a path that may have been customised; fall
        through to the bundled default.
      * Bundled default ``<skill_root>/data/data_v20.h5`` is the last resort.
    """
    candidates = []

    if cli_path:
        p = Path(cli_path).expanduser()
        if not p.exists():
            raise FileNotFoundError(
                f"--data-path / path= argument '{p}' does not exist"
            )
        return p.resolve()

    env_path = os.environ.get("V21_DATA_H5")
    if env_path:
        p = Path(env_path).expanduser()
        if not p.exists():
            raise FileNotFoundError(
                f"$V21_DATA_H5='{p}' does not exist. "
                "Unset the env var to fall back to bundled data."
            )
        return p.resolve()

    if CONFIG_PATH.exists():
        try:
            cfg_h5 = json.loads(CONFIG_PATH.read_text(encoding="utf-8")).get(
                "data_h5"
            )
            if cfg_h5:
                cfg_p = (SKILL_ROOT / cfg_h5).expanduser()
                if cfg_p.exists():
                    return cfg_p.resolve()
        except (json.JSONDecodeError, OSError):
            pass

    if DEFAULT_H5.exists():
        return DEFAULT_H5.resolve()
    raise FileNotFoundError(
        f"Bundled HDF5 not found at {DEFAULT_H5}. "
        "Set V21_DATA_H5 or pass path= to point at your data."
    )


def _decode_tickers(raw) -> list:
    """H5 stores tickers as bytes — normalise to str with -CN suffix."""
    out = []
    for x in raw:
        s = x.decode() if isinstance(x, bytes) else str(x)
        if not s.endswith("-CN"):
            s = s + "-CN"
        out.append(s)
    return out


def _validate_structure(f: h5py.File) -> None:
    """Raise ValueError if any required dataset is missing."""
    missing = [k for k in REQUIRED_DATASETS if k not in f]
    if missing:
        raise ValueError(
            f"HDF5 missing required datasets: {missing}. "
            f"Expected schema: {REQUIRED_DATASETS}"
        )


def load_v21_data(path: Optional[str] = None) -> Dict:
    """Load the V21 HDF5 into an in-memory dict.

    Args:
        path: Optional override for the HDF5 location. If None, falls through
            to the standard resolution chain (env var → config → bundled default).

    Returns:
        Dict with keys: prices, market_cap, industry, stock_names,
        universe_exclude, sys_corrupt_months, wt1_monthly, wt2_monthly (opt),
        close_7d (opt), bad_returns_mask (opt).
    """
    h5_path = resolve_data_path(cli_path=path)
    out: Dict = {}

    with h5py.File(str(h5_path), "r") as f:
        _validate_structure(f)

        g = f["prices"]
        tickers = _decode_tickers(g["axis0"][:])
        ts = pd.to_datetime(g["axis1"][:], unit="s")
        out["prices"] = pd.DataFrame(
            g["block0_values"][:], index=ts, columns=tickers, dtype=float
        )

        g = f["market_cap"]
        mc_tickers = _decode_tickers(g["axis0"][:])
        mc_ts = pd.to_datetime(g["axis1"][:], unit="s")
        out["market_cap"] = pd.DataFrame(
            g["block0_values"][:], index=mc_ts, columns=mc_tickers, dtype=float
        )

        out["industry"] = json.loads(f["industry"].attrs["mapping"])
        out["stock_names"] = json.loads(f["stock_names"].attrs["mapping"])

        if "universe_exclude" in f:
            out["universe_exclude"] = set(
                json.loads(f["universe_exclude"].attrs["stocks"])
            )
        else:
            out["universe_exclude"] = set()

        out["sys_corrupt_months"] = set()

        for name in ("wt1_monthly", "wt2_monthly"):
            ds_path = f"wt/{name}"
            if ds_path in f:
                g = f[ds_path]
                wt_tickers = _decode_tickers(g["axis0"][:])
                wt_ts = pd.to_datetime(g["axis1"][:], unit="s")
                out[name] = pd.DataFrame(
                    g["block0_values"][:], index=wt_ts, columns=wt_tickers, dtype=float
                )

        if "close_7d" in f:
            g = f["close_7d"]
            d7_tickers = _decode_tickers(g["axis0"][:])
            d7_ts = pd.to_datetime(g["axis1"][:], unit="s")
            out["close_7d"] = pd.DataFrame(
                g["block0_values"][:], index=d7_ts, columns=d7_tickers, dtype=float
            )
        else:
            out["close_7d"] = None

        if "bad_returns_mask" in f:
            g = f["bad_returns_mask"]
            bm_tickers = _decode_tickers(g["axis0"][:])
            bm_ts = pd.to_datetime(g["axis1"][:], unit="s")
            out["bad_returns_mask"] = pd.DataFrame(
                g["block0_values"][:].astype(bool),
                index=bm_ts,
                columns=bm_tickers,
            )
        else:
            out["bad_returns_mask"] = None

    return out


def health_check(path: Optional[str] = None) -> Dict[str, object]:
    """Diagnostic dump — verify the bundled H5 is loadable.

    Returns dict with keys: path, exists, size_mb, n_dates, n_tickers,
    has_wt1, has_wt2, has_close_7d, has_bad_mask, n_universe_exclude.
    """
    h5_path = resolve_data_path(cli_path=path)
    info = {
        "path": str(h5_path),
        "exists": True,
        "size_mb": round(h5_path.stat().st_size / 1024 / 1024, 2),
    }
    with h5py.File(str(h5_path), "r") as f:
        _validate_structure(f)
        prices = f["prices"]
        info["n_dates"] = int(prices["axis1"].shape[0])
        info["n_tickers"] = int(prices["axis0"].shape[0])
        info["has_wt1"] = "wt/wt1_monthly" in f
        info["has_wt2"] = "wt/wt2_monthly" in f
        info["has_close_7d"] = "close_7d" in f
        info["has_bad_mask"] = "bad_returns_mask" in f
        if "universe_exclude" in f:
            info["n_universe_exclude"] = len(
                json.loads(f["universe_exclude"].attrs["stocks"])
            )
        else:
            info["n_universe_exclude"] = 0
    return info
