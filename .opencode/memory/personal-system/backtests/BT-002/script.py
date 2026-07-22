#!/usr/bin/env python3
"""
BT-002: Walk-forward ML Prediction for 中远海控 (601919)
=========================================================
Uses RandomForestRegressor to predict future 5-day return from
engineered features. Walk-forward validation with ~1-year sliding
training windows.

Target    : future 5-day return (regression)
Features  : momentum, volume, RSI, volatility, MA deviation
Model     : sklearn RandomForestRegressor
Validation: sliding walk-forward, ~252-day train windows
"""

import os, json, warnings, sys
import numpy as np
import pandas as pd
from pathlib import Path

from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score, mean_squared_error
from sklearn.preprocessing import StandardScaler

warnings.filterwarnings("ignore")

# ── paths ────────────────────────────────────────────────────────────
OUT = Path(__file__).resolve().parent
DATA_DIR = OUT / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# ── 1. data fetch ────────────────────────────────────────────────────
def fetch_data() -> pd.DataFrame:
    """Fetch 601919 daily OHLCV from Sina Finance API."""
    import requests, json
    url = (
        "https://vip.stock.finance.sina.com.cn/quotes_service/api/"
        "json_v2.php/CN_MarketData.getKLineData"
        "?symbol=sh601919&scale=240&ma=no&datalen=4000"
    )
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://finance.sina.com.cn",
    }
    resp = requests.get(url, headers=headers, timeout=30)
    data = resp.json()
    df = pd.DataFrame(data)
    # rename
    col_map = {
        "day": "date", "open": "open", "high": "high",
        "low": "low", "close": "close", "volume": "volume",
    }
    df = df.rename(columns=col_map)
    df["date"] = pd.to_datetime(df["date"])
    for c in ["open", "high", "low", "close", "volume"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df = df.sort_values("date").reset_index(drop=True)
    # filter to 2015+
    df = df[df["date"] >= "2015-01-01"].reset_index(drop=True)
    # add turnover placeholder (not available from Sina)
    df["turnover"] = 0.0
    df.to_parquet(DATA_DIR / "601919_raw.parquet")
    print(f"       {len(df)} rows  {df['date'].min().date()} → {df['date'].max().date()}")
    return df


# ── 2. feature engineering ──────────────────────────────────────────
def build_features(df: pd.DataFrame) -> pd.DataFrame:
    """Build feature matrix from OHLCV data.

    Features:
      ret_5d, ret_10d, ret_20d, ret_60d      — past returns
      vol_change_5d, _10d, _20d, _60d         — volume change rate
      rsi_14, rsi_21                           — relative strength index
      vol_20d                                  — 20d rolling volatility
      volume_ratio                             — volume / 20d MA volume
      price_ma20, price_ma60                   — price / MA - 1
    """
    c = df["close"]
    v = df["volume"]
    ret = c.pct_change()

    feat = pd.DataFrame(index=df.index)

    # momentum
    feat["ret_5d"]   = c.pct_change(5)
    feat["ret_10d"]  = c.pct_change(10)
    feat["ret_20d"]  = c.pct_change(20)
    feat["ret_60d"]  = c.pct_change(60)

    # volume change rate
    feat["vol_change_5d"]  = v.pct_change(5)
    feat["vol_change_10d"] = v.pct_change(10)
    feat["vol_change_20d"] = v.pct_change(20)
    feat["vol_change_60d"] = v.pct_change(60)

    # RSI
    for period in [14, 21]:
        delta = c.diff()
        gain = delta.clip(lower=0).rolling(period).mean()
        loss = (-delta.clip(upper=0)).rolling(period).mean()
        rs = gain / loss.replace(0, np.nan)
        feat[f"rsi_{period}"] = 100 - (100 / (1 + rs))

    # 20d volatility
    feat["vol_20d"] = ret.rolling(20).std()

    # volume ratio (current / 20d avg)
    feat["volume_ratio"] = v / v.rolling(20).mean()

    # price deviation from MA
    feat["price_ma20"] = c / c.rolling(20).mean() - 1
    feat["price_ma60"] = c / c.rolling(60).mean() - 1

    # extra helpers
    feat["high_low_ratio"] = (df["high"] - df["low"]) / c
    feat["close_open_ratio"] = (c - df["open"]) / df["open"].replace(0, np.nan)
    feat["turnover"] = df["turnover"]

    # sanitize
    feat = feat.replace([np.inf, -np.inf], np.nan)
    return feat


# ── 3. walk-forward with RandomForestRegressor ──────────────────────
def walk_forward_rf(
    features: pd.DataFrame,
    target: pd.Series,
    train_window: int = 252,       # ~1 year
    step: int = 63,                # ~3 months between retrain
    model_params: dict = None,
) -> dict:
    """Sliding walk-forward regression.

    Returns dict with OOS predictions, true values, fold info, feature
    importances, and model objects per fold.
    """
    if model_params is None:
        model_params = {"n_estimators": 200, "max_depth": 7,
                        "min_samples_leaf": 10, "random_state": 42}

    n = len(features)
    oos_preds = np.full(n, np.nan)
    oos_true  = np.full(n, np.nan)
    fold_info = []
    importances_list = []
    models = []

    fold_id = 0
    start = 0
    while start + train_window + step <= n:
        train_end = start + train_window
        test_end  = min(train_end + step, n)

        X_train = features.iloc[start:train_end].values
        y_train = target.iloc[start:train_end].values
        X_test  = features.iloc[train_end:test_end].values
        y_test  = target.iloc[train_end:test_end].values

        # drop NaN rows from training
        train_valid = ~(np.isnan(X_train).any(axis=1) | np.isnan(y_train))
        X_tv = X_train[train_valid]
        y_tv = y_train[train_valid]

        if len(X_tv) < 100:
            start += step
            continue

        # standardize
        scaler = StandardScaler()
        X_tv_s = scaler.fit_transform(X_tv)
        X_test_s = scaler.transform(X_test)

        # train
        model = RandomForestRegressor(**model_params)
        model.fit(X_tv_s, y_tv)

        # predict (OOS)
        preds = model.predict(X_test_s)
        oos_preds[train_end:test_end] = preds
        oos_true[train_end:test_end]  = y_test

        # feature importance
        imp = pd.Series(model.feature_importances_, index=features.columns)
        importances_list.append(imp)

        models.append(model)
        fold_info.append({
            "fold": fold_id,
            "train_start": features.index[start].strftime("%Y-%m-%d"),
            "train_end":   features.index[train_end-1].strftime("%Y-%m-%d"),
            "test_start":  features.index[train_end].strftime("%Y-%m-%d"),
            "test_end":    features.index[test_end-1].strftime("%Y-%m-%d") if test_end > train_end else "N/A",
            "train_rows":  int(train_valid.sum()),
            "test_rows":   len(X_test),
        })

        fold_id += 1
        start += step

    # validity mask
    valid = ~np.isnan(oos_preds)

    # average importance across folds
    avg_importance = pd.concat(importances_list, axis=1).mean(axis=1).sort_values(ascending=False)

    return {
        "oos_preds": oos_preds,
        "oos_true": oos_true,
        "fold_info": fold_info,
        "avg_importance": avg_importance,
        "models": models,
    }


# ── 4. metrics ──────────────────────────────────────────────────────
def compute_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict:
    """Regression + directional + signal metrics."""
    valid = ~(np.isnan(y_true) | np.isnan(y_pred))
    yt = y_true[valid]
    yp = y_pred[valid]

    if len(yt) < 5:
        return {"error": "too few valid observations"}

    # regression
    r2 = r2_score(yt, yp)
    rmse = np.sqrt(mean_squared_error(yt, yp))
    mae = np.mean(np.abs(yt - yp))

    # directional accuracy (sign match)
    dir_acc = np.mean((yt > 0) == (yp > 0))

    # signal: long when pred > 0
    long_returns = yt[yp > 0]
    short_returns = yt[yp < 0]
    n_long = len(long_returns)
    n_short = len(short_returns)

    if len(long_returns) > 1:
        sharpe_long = np.sqrt(252/5) * long_returns.mean() / long_returns.std()
    else:
        sharpe_long = np.nan

    if len(short_returns) > 1:
        sharpe_short = np.sqrt(252/5) * short_returns.mean() / short_returns.std()
    else:
        sharpe_short = np.nan

    # overall strategy (long when pred>0, short when pred<0, skip when pred=0)
    strat_returns = np.where(yp > 0, yt, np.where(yp < 0, -yt, 0))
    strat_returns = strat_returns[strat_returns != 0]
    if len(strat_returns) > 1:
        sharpe_strat = np.sqrt(252/5) * strat_returns.mean() / strat_returns.std()
    else:
        sharpe_strat = np.nan

    return {
        "n_obs": int(valid.sum()),
        "r2": round(r2, 4),
        "rmse": round(rmse, 6),
        "mae": round(mae, 6),
        "directional_accuracy": round(dir_acc, 4),
        "mean_pred_return": round(yt.mean(), 6),
        "n_long_signals": int(n_long),
        "n_short_signals": int(n_short),
        "sharpe_long": round(sharpe_long, 4) if not np.isnan(sharpe_long) else None,
        "sharpe_short": round(sharpe_short, 4) if not np.isnan(sharpe_short) else None,
        "sharpe_strategy": round(sharpe_strat, 4) if not np.isnan(sharpe_strat) else None,
    }


# ── 5. residual diagnostics ─────────────────────────────────────────
def residual_diagnostics(y_true: np.ndarray, y_pred: np.ndarray) -> dict:
    """Residual analysis."""
    valid = ~(np.isnan(y_true) | np.isnan(y_pred))
    yt = y_true[valid]
    yp = y_pred[valid]
    resid = yt - yp

    return {
        "resid_mean": round(float(np.mean(resid)), 6),
        "resid_std": round(float(np.std(resid)), 6),
        "resid_skew": round(float(pd.Series(resid).skew()), 4),
        "resid_kurtosis": round(float(pd.Series(resid).kurtosis()), 4),
        "resid_q1": round(float(np.percentile(resid, 25)), 6),
        "resid_q3": round(float(np.percentile(resid, 75)), 6),
        "resid_outliers_pct": round(float(np.mean(np.abs(resid) > 2 * np.std(resid)) * 100), 2),
    }


# ── 6. main ─────────────────────────────────────────────────────────
def main():
    print("=" * 60)
    print("BT-002: Walk-forward ML  中远海控 (601919)")
    print("=" * 60)

    # 1. data
    print("\n[1/5] Fetching data ...")
    df = fetch_data()
    print(f"       {len(df)} rows  {df['date'].min().date()} → {df['date'].max().date()}")

    # 2. features
    print("[2/5] Building features ...")
    features = build_features(df)
    # assign date index
    features.index = df["date"]
    print(f"       {features.shape[1]} features  {features.shape[0]} rows")

    # 3. target: future 5-day return
    print("[3/5] Creating target (future 5d return) ...")
    target = df["close"].pct_change(5).shift(-5)
    target.index = df["date"]
    # drop rows where target or features are all NaN
    valid_idx = target.notna() & features.notna().any(axis=1)
    features = features[valid_idx]
    target = target[valid_idx]
    print(f"       Target range: {target.min():.4f} ~ {target.max():.4f}")
    print(f"       Up samples: {(target > 0).sum()}  Down samples: {(target <= 0).sum()}")

    # 4. walk-forward
    print("[4/5] Running walk-forward (sliding 252d train, 63d step) ...")
    # two model configs for comparison
    configs = {
        "RF_shallow": {"n_estimators": 200, "max_depth": 5,
                       "min_samples_leaf": 15, "random_state": 42},
        "RF_deep":    {"n_estimators": 300, "max_depth": 9,
                       "min_samples_leaf": 5, "random_state": 42},
    }

    all_results = {}
    for name, params in configs.items():
        print(f"   ├─ {name}: {params}")
        result = walk_forward_rf(features, target, model_params=params)
        metrics = compute_metrics(result["oos_true"], result["oos_preds"])
        resid   = residual_diagnostics(result["oos_true"], result["oos_preds"])
        all_results[name] = {
            "metrics": metrics,
            "resid": resid,
            "fold_info": result["fold_info"],
            "importance": result["avg_importance"],
            "oos_preds": result["oos_preds"],
            "oos_true": result["oos_true"],
        }
        print(f"   │  R²={metrics['r2']}  RMSE={metrics['rmse']}  DirAcc={metrics['directional_accuracy']}  Sharpe(long)={metrics['sharpe_long']}")
        print(f"   └─ folds: {len(result['fold_info'])}")

    # 5. pick best by R², report in detail
    best_name = max(all_results, key=lambda n: all_results[n]["metrics"]["r2"])
    best = all_results[best_name]
    print(f"\n[5/5] Best model: {best_name}")

    # ── save objects ─────────────────────────────────────────────
    # combine OOS predictions into a DataFrame
    oos_df = pd.DataFrame({
        "date": features.index[:len(best["oos_true"])],
        "true_return": best["oos_true"],
        "pred_return": best["oos_preds"],
    })
    oos_df = oos_df.dropna(subset=["true_return"])
    oos_df.to_csv(OUT / "results.csv", index=False)

    # feature importance
    best["importance"].to_csv(OUT / "feature_importance.csv")

    # fold info
    pd.DataFrame(best["fold_info"]).to_csv(OUT / "fold_info.csv", index=False)

    # full metrics JSON
    with open(OUT / "results.json", "w") as f:
        json.dump({name: {"metrics": all_results[name]["metrics"],
                          "resid": all_results[name]["resid"]}
                   for name in all_results}, f, indent=2)

    # ── summary ─────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    m = best["metrics"]
    i = best["importance"]
    r = best["resid"]
    fld = best["fold_info"]

    print(f"""
  Best Model          : {best_name}
  Walk-forward folds  : {len(fld)}
  OOS observations    : {m['n_obs']}

  ── Regression ──
  R²                  : {m['r2']}
  RMSE                : {m['rmse']}
  MAE                 : {m['mae']}

  ── Directional ──
  Directional Acc.    : {m['directional_accuracy']}
  Long signals        : {m['n_long_signals']}
  Short signals       : {m['n_short_signals']}

  ── Signal Performance ──
  Sharpe (long only)  : {m['sharpe_long']}
  Sharpe (short only) : {m['sharpe_short']}
  Sharpe (strategy)   : {m['sharpe_strategy']}

  ── Residuals ──
  Mean                : {r['resid_mean']}
  Std                 : {r['resid_std']}
  Skew                : {r['resid_skew']}
  Outliers (>2σ)      : {r['resid_outliers_pct']}%

  ── Top 5 Features ──
""")
    for feat, imp in i.head(5).items():
        print(f"     {feat:20s}  {imp:.4f}")

    print(f"\n  ── Fold Timeline ──")
    for fld_i in fld[:3]:
        print(f"     Fold {fld_i['fold']}: train {fld_i['train_start']}–{fld_i['train_end']}  "
              f"test {fld_i['test_start']}–{fld_i['test_end']}  "
              f"({fld_i['train_rows']} train / {fld_i['test_rows']} test rows)")
    if len(fld) > 3:
        print(f"     ... ({len(fld)} folds total)")

    print(f"\n  Files saved to: {OUT}/")
    print(f"    - results.csv (OOS predictions)")
    print(f"    - feature_importance.csv")
    print(f"    - fold_info.csv")
    print(f"    - results.json (full metrics)")
    print(f"    - script.py (this file)")
    print(f"    - data/601919_raw.parquet (raw data)")
    print()

    # return key stats
    return {
        "r2": m["r2"],
        "directional_accuracy": m["directional_accuracy"],
        "sharpe_strategy": m["sharpe_strategy"],
        "top3_features": i.head(3).to_dict(),
    }


if __name__ == "__main__":
    stats = main()
    # Print the 3 key stats for the agent
    print("\n★★★ 3 KEY STATISTICS ★★★")
    print(f"1. R² (OOS)           = {stats['r2']}")
    print(f"2. Directional Acc.   = {stats['directional_accuracy']}")
    print(f"3. Sharpe (strategy)  = {stats['sharpe_strategy']}")
    print(f"Top-3 Features:")
    for k, v in stats["top3_features"].items():
        print(f"   {k}: {v:.4f}")
