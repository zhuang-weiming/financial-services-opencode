from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from wif_framework.ashare import (
    COST,
    DEFAULT_DATA_DIR,
    EM_WEIGHTS,
    QW,
    TREND_DOWN,
    TREND_UP,
    apply_tech_replacement,
    compute_mci,
    effective_quadrant,
    get_em_weight,
    load_data,
    mci_to_quadrant,
    normalize_weights,
    run_backtest,
)


# ── MCI Calculations ────────────────────────────────────────────────────────

class TestMCI:
    def test_pmi_55_m2_10_above_q1_threshold(self):
        mci = compute_mci(55, 10)
        assert mci >= 0.53

    def test_pmi_52_m2_7_5_between_thresholds(self):
        mci = compute_mci(52, 7.5)
        assert 0.47 <= mci < 0.53

    def test_pmi_45_m2_4_below_q3_threshold(self):
        mci = compute_mci(45, 4)
        assert mci <= 0.47

    def test_pmi_norm_clamped_to_0(self):
        mci = compute_mci(30, 5)
        assert mci == 0.0

    def test_pmi_norm_clamped_to_1(self):
        mci = compute_mci(70, 30)
        assert mci == pytest.approx(0.5 * 1 + 0.5 * 1)


class TestQuadrant:
    def test_q1(self):
        assert mci_to_quadrant(0.53) == 1
        assert mci_to_quadrant(0.60) == 1

    def test_q2(self):
        assert mci_to_quadrant(0.50) == 2
        assert mci_to_quadrant(0.48) == 2

    def test_q3(self):
        assert mci_to_quadrant(0.47) == 3
        assert mci_to_quadrant(0.40) == 3


class TestEffectiveQuadrant:
    def test_trend_up_forces_q1(self):
        assert effective_quadrant(3, 0.10) == 1

    def test_trend_down_forces_q3(self):
        assert effective_quadrant(1, -0.10) == 3

    def test_mci_kept_when_near_zero(self):
        assert effective_quadrant(2, 0.0) == 2
        assert effective_quadrant(1, 0.05) == 1
        assert effective_quadrant(3, -0.05) == 3

    def test_boundaries(self):
        assert effective_quadrant(2, TREND_UP + 0.001) == 1
        assert effective_quadrant(2, TREND_DOWN - 0.001) == 3
        assert effective_quadrant(2, TREND_UP - 0.001) == 2
        assert effective_quadrant(2, TREND_DOWN + 0.001) == 2


class TestEMWeights:
    def test_l3_triggers(self):
        lv, w = get_em_weight(-0.25)
        assert lv == "L3"
        assert abs(sum(w.values()) - 1.0) < 1e-10

    def test_l2_triggers(self):
        lv, w = get_em_weight(-0.15)
        assert lv == "L2"

    def test_l1_triggers(self):
        lv, w = get_em_weight(-0.10)
        assert lv == "L1"

    def test_no_em_when_above_threshold(self):
        lv, w = get_em_weight(-0.05)
        assert lv is None

    def test_l3_weight_has_high_gold(self):
        _, w = get_em_weight(-0.25)
        assert w["gold"] >= 0.70

    def test_em_weights_sum_to_one(self):
        for lv in ["L1", "L2", "L3"]:
            assert abs(sum(EM_WEIGHTS[lv].values()) - 1.0) < 1e-10


class TestQW:
    def test_qw_weights_sum_to_one(self):
        for q, w in QW.items():
            assert abs(sum(w.values()) - 1.0) < 1e-4, f"Q{q} sums to {sum(w.values())}"

    def test_q1_has_no_bond_or_cash(self):
        assert QW[1].get("bond", 0) == 0.0
        assert QW[1].get("cash", 0) == 0.0

    def test_q3_has_cash(self):
        assert QW[3].get("cash", 0) > 0

    def test_q1_stock_weight_is_90_9_percent(self):
        stock = sum(v for k, v in QW[1].items() if k in ("hs300", "csi500", "cyb"))
        assert stock == pytest.approx(0.909, abs=0.001)

    def test_csi500_is_30_percent_of_hs300(self):
        for q, w in QW.items():
            expected = round(w["hs300"] / (1 - 0.30) * 0.30, 4) if w["hs300"] > 0 else 0
            assert w["csi500"] == pytest.approx(expected, abs=0.001) or q == 2


# ── Normalize Weights ───────────────────────────────────────────────────────

class TestNormalize:
    def test_normalize_sums_to_one(self):
        w = normalize_weights({"a": 1.0, "b": 2.0, "c": 3.0})
        assert abs(sum(w.values()) - 1.0) < 1e-10

    def test_normalize_symmetry(self):
        w = normalize_weights({"x": 10, "y": 10})
        assert w["x"] == w["y"] == 0.5


class TestDataLoading:
    def test_load_data_returns_dataframe(self):
        df = load_data()
        assert isinstance(df, pd.DataFrame)
        assert len(df) > 3000
        assert "MCI" in df.columns
        assert "Q" in df.columns
        assert "trend" in df.columns
        assert "R20" in df.columns

    def test_data_covers_full_period(self):
        df = load_data()
        assert df["Date"].iloc[0] <= pd.Timestamp("2013-07-30")
        assert df["Date"].iloc[-1] >= pd.Timestamp("2026-04-22")

    def test_mci_in_valid_range(self):
        df = load_data()
        assert df["MCI"].between(0, 1).all()

    def test_quadrant_is_1_2_or_3(self):
        df = load_data()
        assert df["Q"].dropna().isin([1, 2, 3]).all()


class TestBacktest:
    def test_run_backtest_returns_result(self):
        result = run_backtest()
        assert "stats" in result
        assert "nav_series" in result
        assert "diagnostics" in result

    def test_backtest_nav_is_positive(self):
        result = run_backtest()
        navs = result["nav_series"]
        assert navs[-1] > navs[0] > 0

    def test_backtest_v27_stats_match_expected(self):
        result = run_backtest()
        s = result["stats"]
        # Compare with v27_stats.json: cumulative=796.3%, sharpe=1.233, mdd=-18.4%
        # Allow tolerance due to chip data approximation (399303 proxy)
        assert s["cumulative"] > 700, f"Cumulative return {s['cumulative']}% too low"
        assert s["sharpe"] > 1.0, f"Sharpe {s['sharpe']} too low"
        assert s["mdd"] > -25, f"MDD {s['mdd']}% too deep"
        assert s["nav_end"] > 6.0, f"NAV {s['nav_end']} too low"

    def test_backtest_diagnostics_sensible(self):
        result = run_backtest()
        d = result["diagnostics"]
        assert d["trend_up_days"] > 200
        assert d["trend_dn_days"] > 50
        assert d["override_q1_days"] > 100
        assert 50 <= result["rebal_count"] <= 500


class TestCostConstant:
    def test_cost_reasonable(self):
        assert 0.001 <= COST <= 0.01


class TestTechReplacement:
    def test_tech_replacement_reduces_cyb(self):
        w = {"hs300": 0.4, "cyb": 0.2, "csi500": 0.15, "gold": 0.15, "bond": 0.10}
        result = apply_tech_replacement(w, 1, pd.Timestamp("2020-06-01"), False)
        assert result["cyb"] < w["cyb"]
        assert result.get("tech399", 0) > 0
