import numpy as np
import pandas as pd
import pytest

import wif_framework.phase as phase_module
from wif_framework.allocation import PHASE_ALLOCATION, calc_v68b, target_allocation, triple_track_v59
from wif_framework.phase import compute_csi, macro_quadrant, phase1_status


def _index(n=240):
    return pd.date_range("2000-01-03", periods=n, freq="B")


def test_csi_fixed_weights_three_components_equal_point_six_not_three(monkeypatch):
    """All three Z-scores mocked to 1.0. CSI = 0.45 + 0.35 - 0.20 = 0.60.

    The correlation component is negated (``correlation_stress = -Z(corr)``),
    so a positive Z-score for SPY-GLD correlation (more correlated than normal)
    REDUCES CSI — intuitively correct because elevated correlation is not crisis
    behavior. The test's original assertion of 1.0 was incorrect.
    """
    idx = _index(160)
    prices = pd.DataFrame(
        {
            "F29_bp": np.linspace(100, 300, len(idx)),
            "VIXTERM": np.linspace(-2, 3, len(idx)),
            "SPY": np.linspace(100, 180, len(idx)),
            "GLD": np.linspace(80, 130, len(idx)) ** 1.01,
        },
        index=idx,
    )
    monkeypatch.setattr(phase_module, "_zscore", lambda series, window=60: pd.Series(1.0, index=series.index))
    result = compute_csi(prices)
    assert np.allclose(result, 0.60), f"Expected 0.60, got {result.iloc[-1]}"


def test_csi_missing_components_are_not_rescaled(monkeypatch):
    idx = _index(100)
    monkeypatch.setattr(phase_module, "_zscore", lambda series, window=60: pd.Series(1.0, index=series.index))

    two_components = pd.DataFrame(
        {"F29_bp": np.arange(len(idx), dtype=float), "VIXTERM": np.arange(len(idx), dtype=float)},
        index=idx,
    )
    one_component = pd.DataFrame({"F29_bp": np.arange(len(idx), dtype=float)}, index=idx)

    assert np.allclose(compute_csi(two_components), 0.80)
    assert np.allclose(compute_csi(one_component), 0.45)


def test_csi_correlation_matches_spy_gld_20d_correlation_60d_zscore():
    idx = _index(240)
    rng = np.random.default_rng(7)
    spy_returns = rng.normal(0.0004, 0.012, len(idx))
    gld_returns = 0.4 * spy_returns + rng.normal(0.0002, 0.01, len(idx))
    prices = pd.DataFrame(
        {
            "SPY": 100 * np.cumprod(1 + spy_returns),
            "GLD": 90 * np.cumprod(1 + gld_returns),
        },
        index=idx,
    )

    returns = prices.pct_change(fill_method=None)
    corr_20d = returns["SPY"].rolling(20).corr(returns["GLD"])
    expected = -0.20 * phase_module._zscore(corr_20d, window=60)
    pd.testing.assert_series_equal(compute_csi(prices), expected, check_names=False)


@pytest.mark.parametrize(
    "spy_growth,tlt_growth,expected",
    [
        (-0.001, 0.001, 1),
        (0.001, -0.001, 2),
        (-0.001, -0.001, 3),
        (0.001, 0.001, 4),
    ],
)
def test_macro_quadrant_four_classes(spy_growth, tlt_growth, expected):
    idx = _index(300)
    prices = pd.DataFrame(
        {
            "SPY": 100 * np.exp(np.arange(len(idx)) * spy_growth),
            "TLT": 100 * np.exp(np.arange(len(idx)) * tlt_growth),
        },
        index=idx,
    )
    assert int(macro_quadrant(prices).iloc[-1]) == expected


def test_macro_quadrant_does_not_silently_default_without_market_data():
    idx = _index(100)
    with pytest.raises(ValueError, match="requires SPY and TLT"):
        macro_quadrant(pd.DataFrame({"DGS10": 4.0, "T10YIE": 2.0}, index=idx))


def test_f29_hard_trigger_is_immediate_even_when_csi_above_two_for_one_day():
    idx = _index(20)
    csi = pd.Series(0.0, index=idx)
    csi.iloc[10] = 3.0
    prices = pd.DataFrame({"F29_bp": 100.0}, index=idx)
    prices.iloc[10, 0] = 600.0
    status = phase1_status(prices, csi=csi)
    assert status.iloc[9] == "HEALTHY"
    assert status.iloc[10] == "EMERGENCY"


def test_f33b_hard_trigger_is_immediate_even_when_csi_above_two_for_one_day():
    idx = _index(25)
    csi = pd.Series(0.0, index=idx)
    csi.iloc[15] = 3.0
    vix = pd.Series(20.0, index=idx)
    vix.iloc[15] = 50.0
    status = phase1_status(pd.DataFrame({"VIX": vix}, index=idx), csi=csi)
    assert status.iloc[14] == "HEALTHY"
    assert status.iloc[15] == "EMERGENCY"


def test_phase1_has_explicit_initial_state_and_no_future_backfill():
    idx = _index(12)
    csi = pd.Series([0.0] * 5 + [1.5] * 3 + [0.0] * 4, index=idx)
    status = phase1_status(pd.DataFrame(index=idx), csi=csi)
    assert list(status.iloc[:5]) == ["HEALTHY"] * 5
    assert status.iloc[7] == "WARNING"
    assert status.iloc[0] != status.iloc[7]


def test_allocation_weights_sum_to_one():
    for phase1 in ("HEALTHY", "WARNING", "EMERGENCY"):
        for quadrant in (1, 2, 3, 4):
            assert sum(triple_track_v59(phase1, quadrant)) == pytest.approx(1.0)
            for mci in (-20.0, 0.0, 20.0, 100.0):
                assert sum(calc_v68b(phase1, mci, quadrant).values()) == pytest.approx(1.0)

    for phase in PHASE_ALLOCATION:
        allocation = target_allocation(phase)
        assert allocation["equity"] + allocation["fixed_income"] + allocation["real_assets"] == pytest.approx(1.0)
