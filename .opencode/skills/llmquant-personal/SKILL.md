---
name: llmquant-personal
description: Read-only access to the user's saved LLMQuant Dashboard profile (risk preference, horizon, base currency, notes) and holdings (symbols, quantities, market value, cost basis). Use to personalize analysis, compute mark-to-market against the user's portfolio, or check whether the user has any saved context before asking redundant questions.
category: data-source
---

# llmquant-personal

Read-only access to whatever the user has saved in their **LLMQuant Dashboard → Profile**. Two tools: profile (risk preference + horizon + currency + free-form notes), holdings (positions across asset classes).

> Pair with `llmquant-data` master for cross-cutting concerns. This skill is tool-by-tool usage.

## When to use

- Personalize a recommendation based on user's risk tolerance / horizon
- Compute mark-to-market by combining `personal_holdings` with `llmquant-market-data` prices
- Check whether the user has saved holdings before asking "what do you own?"
- Read free-form notes the user has saved for context

## When NOT to use

- **Live brokerage data** → this is read-only profile data the user typed in; not a brokerage feed
- **Trading / order placement** → this repo is research-only; no live trading
- **Detailed holdings from non-LLMQuant sources** → user needs to add them to their profile first

## Tools

### `personal_profile`

Returns the user's saved financial profile.

**Returns** (when set):

```json
{
  "data": {
    "risk_preference": "moderate",
    "investment_horizon": "10y",
    "base_currency": "USD",
    "extra_notes": "..."
  }
}
```

**Returns** (when unset):

```json
{
  "data": null
}
```

**Cost**: 0 credits.

```python
profile = personal_profile()
if profile["data"]:
    risk = profile["data"]["risk_preference"]
    horizon = profile["data"]["investment_horizon"]
    currency = profile["data"]["base_currency"]
    notes = profile["data"]["extra_notes"]
else:
    # Empty profile — user hasn't saved anything yet; treat as default risk profile
```

**Field semantics** (free-form — values may vary by user input):

| Field | Typical values | Use in analysis |
|---|---|---|
| `risk_preference` | `conservative` / `moderate` / `aggressive` / free text | Adjust position-sizing recommendations |
| `investment_horizon` | `1y` / `5y` / `10y` / `30y` / free text | Discount-rate / liquidity preference |
| `base_currency` | `USD` / `EUR` / `CNY` / etc. | FX context for returns |
| `extra_notes` | free text | User context — anything from "I work in tech" to "no crypto please" |

### `personal_holdings`

Returns the user's saved positions.

| Param | Type | Required | Notes |
|---|---|---|---|
| `asset_class` | enum | no | `equity` / `etf` / `crypto` / `cash` / `fund` / `bond` / `other` |
| `limit` | int | no | 1–50, default 30 |

**Returns** (when set):

```json
{
  "data": {
    "total_count": 7,
    "holdings": [
      {
        "symbol": "AAPL",
        "name": "Apple Inc.",
        "asset_class": "equity",
        "quantity": 100.5,
        "market_value": 31250.00,
        "cost_basis": 22000.00,
        "currency": "USD",
        "as_of_date": "2026-08-20"
      },
      ...
    ]
  }
}
```

**Returns** (when unset):

```json
{
  "data": {"total_count": 0, "holdings": []}
}
```

**Cost**: 0 credits.

**Important caveats**:

1. **Values are what the user typed**, not live market quotes. `market_value` may be days/weeks stale — always cross-check against `llmquant-market-data` snapshots before any portfolio analysis.
2. `cost_basis` is the **aggregate** total cost the user entered, not per-share. Per-share average = `cost_basis / quantity`. But trust the user's input as-is unless they ask for a derived view.
3. `symbol` is whatever the user typed. Could be `AAPL`, `BRK.B`, `BTC-USD`, `510300.SH`, or even free-text. Normalize before joining with market data.

## Patterns

### Mark-to-market vs live prices

```python
profile = personal_profile()
holdings = personal_holdings()["data"]["holdings"]
base_ccy = profile["data"]["base_currency"] if profile["data"] else "USD"

for h in holdings:
    if h["asset_class"] == "equity":
        px = equity_historical_prices(h["symbol"], limit=1)
        latest_px = px["prices"][-1]["close"] if px["prices"] else None
        mtm = h["quantity"] * latest_px if latest_px else h["market_value"]
        print(f"{h['symbol']}: qty={h['quantity']}, latest_px=${latest_px}, MTM=${mtm:.2f}")
    elif h["asset_class"] == "crypto":
        snap = crypto_snapshot(h["symbol"])  # e.g. BTC-USD
        mtm = h["quantity"] * snap["price"]
        # ...
```

### Concentration check

```python
holdings = personal_holdings()["data"]["holdings"]
total = sum(h["market_value"] for h in holdings)
for h in sorted(holdings, key=lambda x: -x["market_value"]):
    pct = h["market_value"] / total * 100
    print(f"{h['symbol']:8s} {pct:5.1f}% (${h['market_value']:,.0f})")
```

### Risk-aware recommendation

```python
profile = personal_profile()["data"]
if profile and profile["risk_preference"] == "conservative":
    # bias recommendations toward lower-vol names / larger caps
    ...
```

### Free-form notes as context

```python
profile = personal_profile()["data"]
if profile and "no crypto" in (profile["extra_notes"] or "").lower():
    # skip crypto recommendations
    ...
```

## Edge cases

| Situation | Behavior |
|---|---|
| No profile saved | `data: null` for `personal_profile`; `total_count: 0` for `personal_holdings` |
| Empty holdings | Same — empty list, no error |
| Stale `market_value` | Cross-check with `llmquant-market-data` snapshots; cite both |
| Custom symbols (e.g. `BRK.B` → `BRK-B`) | Normalize before joining with market data (server normalizes for known tickers) |
| Multi-currency holdings | Filter by `currency` field; don't assume USD |

## Output size

Both tools return small JSON (< 5 KB typical). Safe in any batch.

## Privacy & permissions

These tools return **only the user's own** data. They cannot see anyone else's portfolio or read a live brokerage. The user explicitly adds data via the LLMQuant Dashboard. The tools are credit-free precisely because the data is the user's own.

If the user has not added anything, every call returns the empty-profile shape — do **not** interpret this as an error, just adapt the response.

## See also

- `llmquant-market-data` — for live prices to refresh stale `market_value`
- `llmquant-funds` — for ETF underlying analysis when portfolio has ETF positions
- `llmquant-data` master — for credit / pagination / error handling