"""alpha_engine.py — V21 alpha strategy backtest engine.

V21 alpha strategy: LazyBear WaveTrend momentum (85%) + 12-month rolling
volatility anomaly (15%), top-10 monthly rebalance long-only A-share portfolio.
Released 2026-07-09 as the canonical A-share alpha reference.

This module is adapted from the original V21.0 release at
``22_Alpha投资框架/02_大陆用户版/v21/alpha_engine_common.py``. Adaptations:

  * Hardcoded absolute paths replaced with environment-variable / config-driven
    lookup (see ``data_loader.py``).
  * ``BacktestConfig.transaction_cost`` defaults to True (production honesty —
    V21.0 had TC=off as a research-design simplification that we now consider
    inappropriate for a published skill).
  * Alternative scoring functions (``score_v8`` / ``v31`` / ``v32`` / long-window
    factor variants) removed; only ``score_v30`` (V21) is exposed.
  * Honest statistical tests moved out to ``statistical_tests.py``; this module
    only contains the backtest loop, filters, and scoring.

Path resolution: HDF5 data is loaded by ``data_loader.load_v21_data()`` which
respects ``V21_DATA_H5`` env var → ``config/v21_config.json`` ``data_h5`` field
→ default ``<skill_root>/data/data_v20.h5``.

References:
  * WaveTrend: LazyBear, TradingView community indicator (public domain).
  * DSR: López de Prado, *Advances in Financial Machine Learning* (2018).
"""
import warnings

warnings.filterwarnings("ignore")

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Set

import numpy as np
import pandas as pd

HIST_WINDOW = 24
DEFAULT_HIST_WINDOW = 24
MIN_HISTORY = 4
DEFAULT_OB_BASE = 53
DEFAULT_OB_CAP_ADJ = 40
DEFAULT_BAD_RET = 0.40


# ==============================================================================
# Dataclasses
# ==============================================================================


@dataclass
class BacktestConfig:
    """V21 backtest configuration.

    Attributes:
        n_hold: Number of stocks held each month (default 10).
        max_per_ind: Maximum stocks per SW1 industry (default 3).
        liq_filter_mcap: Liquidity floor in CNY (default 2e9).
        ob_filter: Whether to apply adaptive overbought filter (default True).
        ob_base: Base overbought threshold for large caps (default 53).
        ob_cap_adj: Adaptive adjustment range for small caps (default 40).
        bad_return_threshold: |return| above this in last month excludes a
            stock from the candidate pool (default 0.40).
        warmup: Skip first N months (no trades, NAV flat at 1.0).
        hist_window: Lookback window in months for score computation.
        transaction_cost: Apply commission + stamp tax + impact modelling.
            **Default True** — overrides V21.0's research-default of False
            for production honesty.
        name: Strategy label (default "V21").
    """

    n_hold: int = 10
    max_per_ind: int = 3
    liq_filter_mcap: float = 2e9
    ob_base: float = DEFAULT_OB_BASE
    ob_cap_adj: float = DEFAULT_OB_CAP_ADJ
    warmup: int = 4
    ob_filter: bool = True
    bad_return_threshold: float = DEFAULT_BAD_RET
    hist_window: int = DEFAULT_HIST_WINDOW
    transaction_cost: bool = True
    name: str = "V21"


@dataclass
class BacktestResult:
    """Container for a completed V21 backtest."""

    metrics: Dict
    equity: pd.Series
    trades: List[Dict]
    cash_months: int = 0


# ==============================================================================
# Lookups
# ==============================================================================


def _wt_at(wt_df: pd.DataFrame, target_date: pd.Timestamp) -> Optional[pd.Timestamp]:
    """Return the latest wt_df index ≤ target_date, or None."""
    valid = wt_df.index[wt_df.index <= target_date]
    return valid[-1] if len(valid) > 0 else None


def mcap_at(mcdf: pd.DataFrame, prev_date: pd.Timestamp) -> Optional[pd.Timestamp]:
    """Return the latest mcdf index ≤ prev_date, or None."""
    valid = mcdf.index[mcdf.index <= prev_date]
    return valid[-1] if len(valid) > 0 else None


# ==============================================================================
# Filters
# ==============================================================================


def build_universe(
    pdf: pd.DataFrame,
    wt1_df: pd.DataFrame,
    universe_exclude: Set[str] = None,
) -> List[str]:
    """Build the eligible stock universe.

    Excludes: 510300-CN (CSI 300 ETF), ``universe_exclude`` set, and stocks
    not present in ``wt1_df``. Returns sorted list.
    """
    if universe_exclude is None:
        universe_exclude = set()
    avail_all = sorted(
        [
            c
            for c in pdf.columns
            if c != "510300-CN" and c not in universe_exclude
        ]
    )
    wt_stocks = set(wt1_df.columns) & set(avail_all)
    return sorted(wt_stocks)


def adaptive_ob_keep(
    wt1_df: pd.DataFrame,
    mcdf: pd.DataFrame,
    target_date: pd.Timestamp,
    avail: List[str],
    ob_base: float = DEFAULT_OB_BASE,
    ob_cap_adj: float = DEFAULT_OB_CAP_ADJ,
) -> pd.Series:
    """Adaptive overbought filter — large caps use strict threshold (53),
    small caps relax toward 93. WT1 > threshold → exclude.

    A-share convention: WT1 > 60 is typically overbought, > 80 is extreme.
    V21's adaptive design prevents dropping small-cap momentum prematurely.
    """
    mcap_lookup = mcap_at(mcdf, target_date)
    if mcap_lookup is None or mcap_lookup not in mcdf.index:
        return pd.Series(True, index=avail)
    mc = mcdf.loc[mcap_lookup]
    mcap_p = 1.0 - mc.rank(pct=True)
    wt_idx = _wt_at(wt1_df, target_date)
    if wt_idx is None:
        return pd.Series(True, index=avail)
    wt1_s = wt1_df.loc[wt_idx].reindex(avail)
    result = pd.Series(True, index=avail)
    for c in avail:
        w = wt1_s.get(c)
        if pd.isna(w):
            continue
        p = mcap_p.get(c, 0.5)
        if pd.isna(p):
            p = 0.5
        threshold = ob_base + ob_cap_adj * p
        if w > threshold:
            result[c] = False
    return result


def mcap_filter(
    avail: List[str],
    mcdf: pd.DataFrame,
    prev_date: pd.Timestamp,
    liq_filter_mcap: float,
) -> Set[str]:
    """Liquidity filter — keep stocks with mcap >= liq_filter_mcap.

    Stocks with NaN mcap at prev_date are kept (V21 baostock-fix convention:
    NaN means data-quality unknown, not necessarily illiquid).
    """
    if liq_filter_mcap <= 0:
        return set(avail)
    lookup = mcap_at(mcdf, prev_date)
    if lookup is None or lookup not in mcdf.index:
        return set(avail)
    mc = mcdf.loc[lookup]
    return {
        c
        for c in avail
        if c not in mc.index or pd.isna(mc[c]) or mc[c] >= liq_filter_mcap
    }


def bad_returns_filter(
    avail: List[str],
    exec_prices: pd.DataFrame,
    bad_mask: Optional[pd.DataFrame],
    i_global: int,
    bad_return_threshold: float,
) -> Set[str]:
    """Anti-look-ahead quality filter.

    Looks at LAST MONTH's return (i_global-2 → i_global-1) to decide if a
    candidate should be excluded. **Never** looks at the current month's
    return — that would be a look-ahead bias.
    """
    if bad_return_threshold <= 0:
        return set(avail)
    result = set(avail)
    if i_global > 1:
        for c in avail:
            p_curr = exec_prices.iloc[i_global - 1].get(c)
            p_prev = exec_prices.iloc[i_global - 2].get(c)
            if (
                pd.notna(p_curr)
                and pd.notna(p_prev)
                and p_prev > 0
            ):
                r = p_curr / p_prev - 1
                if abs(r) > bad_return_threshold:
                    result.discard(c)
    if bad_mask is not None and i_global < len(exec_prices):
        date = exec_prices.index[i_global]
        if date in bad_mask.index:
            for c in avail:
                if c in bad_mask.columns and bad_mask.loc[date, c]:
                    result.discard(c)
    return result


# ==============================================================================
# Selection
# ==============================================================================


def select_top_n(
    score: pd.Series,
    valid: list,
    ind_map: Dict[str, str],
    n_hold: int = 10,
    max_per_ind: int = 3,
) -> list:
    """Select top-N by score, subject to max_per_ind industry cap."""
    vs = score.reindex(valid).dropna().sort_values(ascending=False)
    sel = []
    ic = {}
    for s in vs.index:
        ind = ind_map.get(s, "Unknown")
        if ic.get(ind, 0) >= max_per_ind:
            continue
        sel.append(s)
        ic[ind] = ic.get(ind, 0) + 1
        if len(sel) >= n_hold:
            break
    return sel


# ==============================================================================
# Transaction Costs
# ==============================================================================


def compute_tc_with_impact(
    nt: int,
    n_hold: int,
    mcdf: pd.DataFrame,
    prev_date: pd.Timestamp,
    holdings: list,
    threshold_small: float = 5e9,
    threshold_impact: float = 1e10,
) -> float:
    """Compute transaction cost with small-cap impact surcharge.

    Default bilateral rate 0.18% (A-share commission 万2.5 bilateral ≈ 0.05%
    + stamp tax 0.05% sell + transfer fee 0.001%*2 ≈ 0.1%). Small-cap
    (mcap < 5e9) holdings get a 0.5%*2 surcharge to model market-impact
    and slippage in less-liquid names.

    Returns the per-period TC (decimal, not percent).
    """
    tc = 0.0018 * 2  # base bilateral rate
    lookup = mcap_at(mcdf, prev_date)
    if lookup is not None and lookup in mcdf.index:
        mc = mcdf.loc[lookup]
        n_small = sum(
            1
            for h in holdings
            if h in mc.index
            and not pd.isna(mc[h])
            and mc[h] < threshold_small
        )
        if n_small > 0:
            small_ratio = n_small / max(len(holdings), 1)
            tc = 0.0018 * 2 * (1 - small_ratio) + 0.005 * 2 * small_ratio
    return nt / n_hold * tc


# ==============================================================================
# V21 Scoring Function
# ==============================================================================


def score_v21(
    pd_,
    avail,
    h,
    wt1_df,
    wt2_df,
    mcdf,
    ind_map,
    lv_w: float = 0.15,
    wt_w: float = 0.85,
) -> pd.Series:
    """V21 alpha score: lv(lv_w) + wt_mom(wt_w).

    Both factors are ranked cross-sectionally within the post-filter valid pool
    (NOT the full A-share universe) using ``rank(pct=True, na_option='keep')``
    to (0, 1) range, then weighted-summed.

    Args:
        pd_: Selection date (timestamp).
        avail: Valid tickers after OB + liquidity + bad-return filters.
        h: Historical prices for the valid tickers (last 24 months).
        wt1_df: Pre-computed WT1 monthly panel (LazyBear oscillator level).
        wt2_df: Pre-computed WT2 monthly panel (4-month SMA of WT1, unused
            in V21 but kept for backward compat).
        mcdf: Monthly market-cap panel.
        ind_map: Ticker → SW1 industry name mapping.
        lv_w: Low-volatility factor weight (default 0.15).
        wt_w: WaveTrend momentum factor weight (default 0.85).

    Returns:
        pd.Series of composite scores indexed by ticker.
    """
    idx = _wt_at(wt1_df, pd_)
    wt_v = (
        wt1_df.loc[idx].reindex(avail)
        if idx is not None
        else pd.Series(np.nan, index=avail)
    )
    rets = h.pct_change()
    lv_v = -rets.rolling(12).std().iloc[-1]
    return (
        lv_v.rank(pct=True, na_option="keep").fillna(0.5) * lv_w
        + wt_v.rank(pct=True, na_option="keep").fillna(0.5) * wt_w
    )


# Alias for backward compatibility with V20-era research scripts.
score_v30 = score_v21


# ==============================================================================
# Backtest Engine
# ==============================================================================


def run_backtest(
    data: Dict,
    score_fn: Callable,
    config: BacktestConfig,
    start_idx: int = 0,
    end_idx: Optional[int] = None,
) -> BacktestResult:
    """Run the V21 monthly-rebalance backtest.

    Args:
        data: Dict returned by ``data_loader.load_v21_data()`` — must contain
            prices, market_cap, industry, wt1_monthly, close_7d (optional),
            bad_returns_mask (optional), universe_exclude (optional),
            sys_corrupt_months (optional).
        score_fn: Callable with signature
            ``(prev_date, valid, hist_valid, wt1_df, wt2_df, mcdf, ind_map) -> pd.Series``.
            Use ``score_v21`` for the canonical V21 strategy.
        config: ``BacktestConfig`` instance.
        start_idx: Starting index in the prices panel (default 0).
        end_idx: Ending index (default len(prices)).

    Returns:
        ``BacktestResult`` with metrics, equity curve, trade records, cash-month count.
    """
    pdf = data["prices"]
    close_7d = data.get("close_7d", None)
    exec_prices = close_7d if close_7d is not None else pdf
    mcdf = data["market_cap"]
    ind_map = data["industry"]
    bad_mask = data.get("bad_returns_mask", None)
    universe_exclude = data.get("universe_exclude", set())
    sys_corrupt = data.get("sys_corrupt_months", set())
    wt1_df = data["wt1_monthly"]
    wt2_df = data.get("wt2_monthly", None)

    avail = build_universe(pdf, wt1_df, universe_exclude)
    all_dates = pdf.index
    n_all = len(all_dates)
    if end_idx is None:
        end_idx = n_all
    end_idx = min(end_idx, n_all)
    start_idx = max(0, int(start_idx))

    eq = pd.Series(1.0, index=all_dates[start_idx:end_idx])
    holdings: list = []
    trades: list = []
    cash_months = 0

    for i_local in range(end_idx - start_idx):
        i_global = start_idx + i_local

        if i_local < config.warmup:
            eq.iloc[i_local] = 1.0
            continue
        if i_global == 0:
            continue

        prev_date = all_dates[i_global - 1]
        date = all_dates[i_global]

        if date in sys_corrupt:
            holdings = []
            cash_months += 1
            eq.iloc[i_local] = eq.iloc[i_local - 1] if i_local > 0 else 1.0
            continue

        hist_start = max(0, i_global - config.hist_window)
        hist = pdf[avail].iloc[hist_start:i_global]
        if len(hist) < MIN_HISTORY:
            holdings = []
            cash_months += 1
            eq.iloc[i_local] = eq.iloc[i_local - 1] if i_local > 0 else 1.0
            continue

        if config.ob_filter:
            ob_keep = adaptive_ob_keep(
                wt1_df, mcdf, prev_date, avail, config.ob_base, config.ob_cap_adj
            )
        else:
            ob_keep = pd.Series(True, index=avail)
        liq_pass = mcap_filter(avail, mcdf, prev_date, config.liq_filter_mcap)
        bad_pass = bad_returns_filter(
            avail, exec_prices, bad_mask, i_global, config.bad_return_threshold
        )

        valid = [
            c
            for c in avail
            if ob_keep.get(c, False) and c in liq_pass and c in bad_pass
        ]

        hist_valid = hist[valid]
        try:
            score = score_fn(prev_date, valid, hist_valid, wt1_df, wt2_df, mcdf, ind_map)
        except Exception:
            score = pd.Series(np.nan, index=valid)

        score = score.reindex(valid)

        valid = [c for c in valid if pd.notna(score.get(c))]

        if len(valid) < config.n_hold:
            holdings = []
            cash_months += 1
            eq.iloc[i_local] = eq.iloc[i_local - 1] if i_local > 0 else 1.0
            continue

        new_holdings = select_top_n(
            score, valid, ind_map, config.n_hold, config.max_per_ind
        )
        if not new_holdings:
            holdings = []
            cash_months += 1
            eq.iloc[i_local] = eq.iloc[i_local - 1] if i_local > 0 else 1.0
            continue

        pr = 0.0
        vh = [
            h
            for h in new_holdings
            if not pd.isna(exec_prices.iloc[i_global].get(h))
            and not pd.isna(exec_prices.iloc[i_global - 1].get(h))
        ]
        if vh:
            pr = (
                exec_prices.iloc[i_global][vh]
                / exec_prices.iloc[i_global - 1][vh]
                - 1
            ).mean()

        if holdings:
            nt = len(set(new_holdings) - set(holdings))
        else:
            nt = len(new_holdings)

        if config.transaction_cost and nt > 0:
            tc = compute_tc_with_impact(
                nt, config.n_hold, mcdf, prev_date, new_holdings
            )
            pr -= tc

        sells = [s for s in holdings if s not in new_holdings] if holdings else []
        buys = [b for b in new_holdings if b not in (holdings or [])]
        trades.append(
            dict(
                selection_date=str(prev_date.date()),
                rebalance_month=str(date.date()),
                n_held=len(new_holdings),
                n_sold=len(sells),
                n_bought=len(buys),
                sells="|".join(sells),
                buys="|".join(buys),
                return_pct=round(pr * 100, 2),
                traded_count=nt,
            )
        )

        eq.iloc[i_local] = (
            eq.iloc[i_local - 1] * (1 + pr) if i_local > 0 else 1.0
        )
        holdings = new_holdings

    ret = eq.pct_change().dropna()
    if len(ret) < 2:
        metrics = dict(
            sharpe=0,
            annual=0,
            max_dd=0,
            nav=1.0,
            n_months=0,
            positive_months=0,
            negative_months=0,
            avg_turnover=0,
            total_return_pct=0.0,
            cash_months=cash_months,
        )
        return BacktestResult(metrics=metrics, equity=eq, trades=trades, cash_months=cash_months)

    total = eq.iloc[-1] - 1
    ann = (1 + total) ** (12 / max(len(ret), 1)) - 1
    sharpe = (ret.mean() - 0.02 / 12) / ret.std() * np.sqrt(12)
    dd = (eq / eq.cummax() - 1).min()
    n_turnover = sum(t.get("n_sold", 0) for t in trades) if trades else 0
    avg_turnover = n_turnover / config.n_hold / max(len(ret), 1) if len(ret) > 0 else 0

    metrics = dict(
        sharpe=round(float(sharpe), 3),
        annual=round(float(ann), 4),
        max_dd=round(float(dd), 4),
        nav=round(float(eq.iloc[-1]), 4),
        n_months=len(ret),
        positive_months=int((ret > 0).sum()),
        negative_months=int((ret <= 0).sum()),
        avg_turnover=round(float(avg_turnover), 3),
        total_return_pct=round(float(total * 100), 2),
        cash_months=cash_months,
    )
    return BacktestResult(
        metrics=metrics, equity=eq, trades=trades, cash_months=cash_months
    )
