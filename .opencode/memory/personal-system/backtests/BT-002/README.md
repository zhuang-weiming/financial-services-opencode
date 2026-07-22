# BT-002: Walk-forward ML Prediction — 中远海控 (601919)

## Objective

Build a **Random Forest regression model** to predict the **future 5-day return** of COSCO Shipping Holdings (601919.SH) using technical features derived from daily OHLCV data. Validated via walk-forward (sliding window) to avoid look-ahead bias.

## Data

- **Source**: Sina Finance API (`vip.stock.finance.sina.com.cn`)
- **Period**: 2015-01-05 → 2026-07-21 (2,662 trading days)
- **Fields**: open, high, low, close, volume (unadjusted prices)
- **Note**: 中远海控 underwent major restructuring (China COSCO → COSCO Shipping Holdings) in 2016, which creates structural breaks in the price series.

## Feature Engineering (17 features)

| Category | Features |
|----------|----------|
| Momentum | `ret_5d`, `ret_10d`, `ret_20d`, `ret_60d` |
| Volume | `vol_change_5d`, `vol_change_10d`, `vol_change_20d`, `vol_change_60d`, `volume_ratio` |
| Volatility | `vol_20d` |
| Overbought/Oversold | `rsi_14`, `rsi_21` |
| Trend Deviation | `price_ma20`, `price_ma60` |
| Intraday | `high_low_ratio`, `close_open_ratio` |
| Activity | `turnover` |

## Target

`close.pct_change(5).shift(-5)` — continuous future 5-day return (regression).

## Model

**RandomForestRegressor** — two configurations:

| Config | n_estimators | max_depth | min_samples_leaf |
|--------|-------------|-----------|-----------------|
| RF_shallow (best) | 200 | 5 | 15 |
| RF_deep | 300 | 9 | 5 |

## Walk-forward Design

- **Window**: Sliding, 252 trading days (~1 year) for training
- **Step**: 63 trading days (~3 months) between retrain
- **Folds**: 38 total folds spanning 2015–2026
- **Standardization**: Fit scaler on each training fold only (no leakage)
- **OOS predictions**: Combined across all folds = 2,394 observations

## Key Results

| Metric | RF_shallow | RF_deep |
|--------|-----------|---------|
| R² (OOS) | **-0.274** | -0.423 |
| RMSE | 0.0695 | 0.0735 |
| MAE | 0.0485 | 0.0518 |
| Directional Accuracy | 49.25% | 50.33% |
| Sharpe (long signals) | 0.355 | 0.290 |
| Sharpe (short signals) | 0.579 | 0.514 |
| Sharpe (strategy) | -0.013 | -0.029 |

## Interpretation

1. **R² negative**: The model cannot out-predict a constant (mean) forecast. Single-stock short-term return prediction is notoriously difficult — the signal-to-noise ratio is extremely low.
2. **Directional accuracy ~50%**: Essentially random on direction. The market's 5-day moves for this stock show no consistent technical pattern that a shallow tree ensemble can exploit.
3. **Sharpe (strategy) ≈ 0**: A long/short strategy based on predictions yields no edge.
4. **Short-side Sharpe > Long-side**: The model is slightly better at identifying down-moves than up-moves, though both are weak.

## Top-3 Features (by importance)

1. **vol_20d** (17.4%) — 20-day rolling volatility
2. **ret_60d** (13.5%) — 60-day momentum
3. **price_ma60** (10.9%) — Price vs 60-day MA deviation

These capture medium-term volatility and trend regimes, but their predictive power for 5-day forward returns is limited.

## Limitations

- Single-stock models suffer from low signal-to-noise; cross-sectional models (many stocks) typically perform better
- Unadjusted prices may have small distortions at dividend/ex-dividend dates
- No fundamental or macro features (e.g., BDI index, container freight rates) which could be more relevant for a shipping stock
- The 2016 restructuring creates a structural break that a rolling window handles only partially

## Files

| File | Description |
|------|-------------|
| `script.py` | Full reproducible pipeline |
| `results.csv` | OOS predictions vs true returns |
| `results.json` | All metrics for both model configs |
| `feature_importance.csv` | Average feature importance across folds |
| `fold_info.csv` | Per-fold train/test splits |
| `report.md` | Extended analysis report |
| `data/601919_raw.parquet` | Raw OHLCV data |
