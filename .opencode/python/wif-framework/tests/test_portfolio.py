import pytest

from wif_framework.portfolio import PortfolioLedger, select_rebalance_assets


def test_no_fill_leaves_holdings_unchanged():
    ledger = PortfolioLedger(1.0)
    ledger.rebalance({"A": 0.6, "B": 0.4})
    before_positions = dict(ledger.positions)
    before_nav = ledger.nav

    result = ledger.rebalance(
        {"A": 0.5, "B": 0.5},
        selected_assets=set(),
    )

    assert result.fills == ()
    assert ledger.positions == before_positions
    assert ledger.nav == pytest.approx(before_nav)


def test_threshold_skip_does_not_change_exposure_or_following_pnl():
    ledger = PortfolioLedger(1.0)
    ledger.rebalance({"A": 0.6, "B": 0.4})
    ledger.apply_returns({"A": 0.10, "B": -0.05})

    weights = ledger.weights()
    assert weights["A"] == pytest.approx(0.6346153846153846)
    assert weights["B"] == pytest.approx(0.36538461538461536)

    selected = select_rebalance_assets(weights, {"A": 0.6, "B": 0.4}, 0.05)
    assert selected == set()
    before_positions = dict(ledger.positions)
    ledger.rebalance({"A": 0.6, "B": 0.4}, selected_assets=selected)
    assert ledger.positions == before_positions

    nav_before = ledger.nav
    ledger.apply_returns({"A": 0.10, "B": 0.0})
    expected = before_positions["A"] * 1.10 + before_positions["B"]
    assert ledger.nav == pytest.approx(expected)
    assert ledger.nav / nav_before - 1 == pytest.approx(weights["A"] * 0.10)


def test_fill_changes_weights_and_only_then_changes_pnl():
    ledger = PortfolioLedger(1.0)
    ledger.rebalance({"A": 1.0})
    ledger.apply_returns({"A": 0.10, "B": 0.50})
    assert ledger.nav == pytest.approx(1.10)

    selected = select_rebalance_assets(ledger.weights(), {"A": 0.0, "B": 1.0}, 0.0, force=True)
    result = ledger.rebalance({"A": 0.0, "B": 1.0}, selected_assets=selected)
    assert {fill.ticker for fill in result.fills} == {"A", "B"}

    nav_before = ledger.nav
    ledger.apply_returns({"A": 0.10, "B": 0.05})
    assert ledger.nav / nav_before - 1 == pytest.approx(0.05)


def test_fee_enters_nav_exactly_once():
    ledger = PortfolioLedger(1.0)
    result = ledger.rebalance(
        {"A": 1.0},
        fee_rate=lambda _ticker, action: 0.10 if action == "BUY" else 0.0,
    )

    assert len(result.fills) == 1
    assert result.total_fee == pytest.approx(1.0 / 11.0)
    assert ledger.total_fees == pytest.approx(result.total_fee)
    assert ledger.nav == pytest.approx(1.0 - result.total_fee)
    assert ledger.positions["A"] == pytest.approx(1.0 / 1.1)

    nav_after_fill = ledger.nav
    ledger.apply_returns({"A": 0.0})
    assert ledger.nav == pytest.approx(nav_after_fill)
    assert ledger.total_fees == pytest.approx(result.total_fee)


def test_forced_selection_ignores_band_but_not_zero_difference():
    selected = select_rebalance_assets(
        {"A": 0.6, "B": 0.4},
        {"A": 0.5, "B": 0.5},
        {"A": 0.2, "B": 0.2},
        force=True,
    )
    assert selected == {"A", "B"}
