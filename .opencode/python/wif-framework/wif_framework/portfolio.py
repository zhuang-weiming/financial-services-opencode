from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Mapping, Optional


@dataclass(frozen=True)
class Fill:
    ticker: str
    action: str
    notional: float
    fee_rate: float
    fee: float
    weight_change: float
    pre_weight: float
    target_weight: float


@dataclass(frozen=True)
class RebalanceResult:
    fills: tuple[Fill, ...] = ()
    skipped: Mapping[str, str] = field(default_factory=dict)
    total_fee: float = 0.0
    nav_before: float = 0.0
    nav_after: float = 0.0


class PortfolioLedger:
    """Lightweight close-to-close portfolio ledger for research backtests.

    Positions are stored as marked market values in normalized NAV units. They
    drift with realized asset returns and only change when an actual fill is
    applied. Cash pays fees exactly once.
    """

    def __init__(self, initial_nav: float = 1.0) -> None:
        if initial_nav <= 0:
            raise ValueError("initial_nav must be positive")
        self.initial_nav = float(initial_nav)
        self.cash = float(initial_nav)
        self.positions: dict[str, float] = {}
        self.total_fees = 0.0

    @property
    def nav(self) -> float:
        return self.cash + sum(self.positions.values())

    def weights(self) -> dict[str, float]:
        nav = self.nav
        if nav <= 0:
            return {ticker: 0.0 for ticker in self.positions}
        return {ticker: value / nav for ticker, value in self.positions.items() if abs(value) > 1e-15}

    def apply_returns(self, returns: Mapping[str, float]) -> None:
        for ticker in list(self.positions):
            value = self.positions[ticker]
            realized_return = float(returns.get(ticker, 0.0))
            if realized_return <= -1.0:
                raise ValueError(f"return for {ticker} must be greater than -100%")
            self.positions[ticker] = value * (1.0 + realized_return)

    def rebalance(
        self,
        target_weights: Mapping[str, float],
        *,
        selected_assets: Optional[set[str]] = None,
        fee_rate: Optional[Callable[[str, str], float]] = None,
        minimum_trade_value: float = 0.0,
        capital_scale: float = 1.0,
    ) -> RebalanceResult:
        target = {ticker: float(weight) for ticker, weight in target_weights.items()}
        if any(weight < -1e-12 for weight in target.values()):
            raise ValueError("target weights cannot be negative")
        if abs(sum(target.values()) - 1.0) > 1e-8:
            raise ValueError("target weights must sum to 1.0")

        fee_rate = fee_rate or (lambda _ticker, _action: 0.0)
        nav_before = self.nav
        pre_weights = self.weights()
        all_assets = set(self.positions) | set(target)
        selected = all_assets if selected_assets is None else set(selected_assets) & all_assets

        desired_values = {ticker: target.get(ticker, 0.0) * nav_before for ticker in all_assets}
        deltas = {ticker: desired_values[ticker] - self.positions.get(ticker, 0.0) for ticker in all_assets}

        skipped: dict[str, str] = {}
        tradable: set[str] = set()
        for ticker in selected:
            delta = deltas[ticker]
            if abs(delta) <= 1e-12:
                continue
            if abs(delta) * capital_scale < minimum_trade_value:
                skipped[ticker] = "below_minimum_trade_value"
                continue
            tradable.add(ticker)

        fills: list[Fill] = []
        total_fee = 0.0

        # Sells create cash before buys. A sell fee, if configured, is paid once.
        for ticker in sorted(tradable):
            delta = deltas[ticker]
            if delta >= 0:
                continue
            current_value = self.positions.get(ticker, 0.0)
            sell_notional = min(-delta, current_value)
            rate = max(0.0, float(fee_rate(ticker, "SELL")))
            fee = sell_notional * rate
            self.positions[ticker] = current_value - sell_notional
            self.cash += sell_notional - fee
            total_fee += fee
            fills.append(
                Fill(
                    ticker=ticker,
                    action="SELL",
                    notional=sell_notional,
                    fee_rate=rate,
                    fee=fee,
                    weight_change=-sell_notional / nav_before,
                    pre_weight=pre_weights.get(ticker, 0.0),
                    target_weight=target.get(ticker, 0.0),
                )
            )

        requested_buys: list[tuple[str, float, float]] = []
        required_cash = 0.0
        for ticker in sorted(tradable):
            delta = deltas[ticker]
            if delta <= 0:
                continue
            rate = max(0.0, float(fee_rate(ticker, "BUY")))
            requested_buys.append((ticker, delta, rate))
            required_cash += delta * (1.0 + rate)

        buy_scale = 1.0 if required_cash <= self.cash + 1e-15 else max(0.0, self.cash / required_cash)
        for ticker, requested_notional, rate in requested_buys:
            buy_notional = requested_notional * buy_scale
            if buy_notional <= 1e-15:
                skipped[ticker] = "insufficient_cash"
                continue
            fee = buy_notional * rate
            self.positions[ticker] = self.positions.get(ticker, 0.0) + buy_notional
            self.cash -= buy_notional + fee
            total_fee += fee
            fills.append(
                Fill(
                    ticker=ticker,
                    action="BUY",
                    notional=buy_notional,
                    fee_rate=rate,
                    fee=fee,
                    weight_change=buy_notional / nav_before,
                    pre_weight=pre_weights.get(ticker, 0.0),
                    target_weight=target.get(ticker, 0.0),
                )
            )

        self.total_fees += total_fee
        if abs(self.cash) < 1e-14:
            self.cash = 0.0
        for ticker in list(self.positions):
            if abs(self.positions[ticker]) < 1e-14:
                del self.positions[ticker]

        nav_after = self.nav
        if abs((nav_before - total_fee) - nav_after) > 1e-10:
            raise AssertionError("portfolio ledger does not reconcile after rebalance")

        return RebalanceResult(
            fills=tuple(fills),
            skipped=skipped,
            total_fee=total_fee,
            nav_before=nav_before,
            nav_after=nav_after,
        )


def select_rebalance_assets(
    current_weights: Mapping[str, float],
    target_weights: Mapping[str, float],
    bands: Mapping[str, float] | float,
    *,
    force: bool = False,
    tolerance: float = 1e-12,
) -> set[str]:
    selected: set[str] = set()
    for ticker in set(current_weights) | set(target_weights):
        difference = abs(float(target_weights.get(ticker, 0.0)) - float(current_weights.get(ticker, 0.0)))
        if difference <= tolerance:
            continue
        band = float(bands.get(ticker, 0.0)) if isinstance(bands, Mapping) else float(bands)
        if force or difference > band:
            selected.add(ticker)
    return selected
