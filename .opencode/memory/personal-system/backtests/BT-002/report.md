# BT-002 Extended Report: Walk-forward ML on 中远海控 (601919)

## 1. Overview

- **Ticker**: 601919.SH (中远海控 / COSCO Shipping Holdings)
- **Method**: Walk-forward Random Forest regression
- **Horizon**: Predict next 5 trading days' return
- **Period**: 2015–2026 (11.5 years)
- **Folds**: 38 sliding windows (252-day train, 63-day step)

## 2. Feature Importance (Top 10)

| Rank | Feature | Importance | Interpretation |
|------|---------|-----------|----------------|
| 1 | **vol_20d** | 0.1740 | 20-day rolling volatility — highest predictive signal |
| 2 | **ret_60d** | 0.1351 | 60-day momentum — captures medium-term trend |
| 3 | **price_ma60** | 0.1093 | Price deviation from 60-day MA — trend confirmation |
| 4 | rsi_21 | 0.0993 | 21-period RSI — overbought/oversold |
| 5 | ret_20d | 0.0770 | 20-day momentum |
| 6 | price_ma20 | 0.0734 | Price vs 20-day MA |
| 7 | rsi_14 | 0.0631 | 14-period RSI |
| 8 | volume_ratio | 0.0550 | Volume vs 20-day average |
| 9 | ret_10d | 0.0483 | 10-day momentum |
| 10 | ret_5d | 0.0400 | 5-day momentum |

**Key insight**: Medium-term features (volatility at 20d, momentum at 60d) dominate. Very short-term features (5d return, volume change) contribute little. This suggests that if any signal exists, it operates on a 1-3 month horizon rather than days.

## 3. Residual Diagnostics (RF_shallow)

| Metric | Value |
|--------|-------|
| Mean residual | -0.00166 |
| Std residual | 0.06952 |
| Skew | 0.053 |
| Kurtosis | 1.24 |
| Q1 | -0.043 |
| Q3 | 0.039 |
| Outliers (>2σ) | 6.56% |

- Residuals are approximately symmetric (skew ≈ 0) with moderate kurtosis
- 6.56% outliers is slightly above the 5% expected under normality, indicating fat tails
- No systematic bias (mean ≈ 0)

## 4. Walk-forward Fold Analysis

- **Total folds**: 38
- **Average training rows**: ~252
- **Average test rows**: ~63
- **Date range**: First fold trains on 2015-01→2016-06, last fold tests on 2025-07→2026-07

The walk-forward structure ensures the model never sees future data. However, the rolling 1-year window may be too short to capture full market regimes (e.g., 2021 shipping boom, 2023 normalization).

## 5. Signal Distribution

| Signal | Count | Mean true return | Std true return |
|--------|-------|-----------------|-----------------|
| Long (pred > 0) | 1,260 | 0.0029 | 0.0361 |
| Short (pred < 0) | 1,134 | -0.0048 | 0.0368 |
| Total OOS | 2,394 | -0.0006 | 0.0617 |

The model's long signals have a *slightly* positive average return (0.29%), while short signals have a negative average (-0.48%). The short side signal is marginally stronger, consistent with the higher short-side Sharpe ratio.

## 6. Comparison of Model Configurations

| Aspect | RF_shallow (max_depth=5) | RF_deep (max_depth=9) |
|--------|------------------------|----------------------|
| OOS R² | -0.274 | -0.423 |
| OOS RMSE | 0.0695 | 0.0735 |
| Dir Acc | 49.25% | 50.33% |
| Sharpe(long) | 0.355 | 0.290 |
| Sharpe(short) | 0.579 | 0.514 |

The shallower model is less overfit and performs slightly better OOS, though both are weak. This is consistent with the known difficulty of predicting single-stock returns.

## 7. Why Such Poor Results?

1. **Efficient market for liquid large-caps**: 中远海控 is a large-cap A-share stock (part of SSE 50 / CSI 300). Simple technical features rarely predict short-term returns for such stocks.

2. **Single-stock vs cross-sectional**: Most quant strategies work with *relative* signals across hundreds of stocks. A single-stock time-series model removes that comparative advantage.

3. **No fundamental / macro features**: Shipping stocks are driven by freight rates (BDI, CCFI), fuel costs, global trade volumes — none captured here.

4. **5-day horizon is very short**: The noise component dominates at such horizons. Longer horizons (21-60 days) often yield slightly better signal quality.

## 8. Recommendations for Improvement

- Add **macro features**: BDI index, CCFI container freight index, oil prices
- Add **fundamental features**: PE, PB, revenue growth trends
- Try **cross-sectional approach**: model relative returns vs sector/benchmark
- Try **longer horizon**: 21-day forward return instead of 5-day
- Try **ensemble of horizons**: combine signals from 5/10/21-day models
- Use **regime detection**: separate bull/bear/range-bound regimes
