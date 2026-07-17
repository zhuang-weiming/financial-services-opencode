from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

import pandas as pd

DATA_DIR = (
    Path(os.environ.get("WIF_DATA_DIR", ""))
    or Path(__file__).resolve().parents[4] / "example" / "wif-framework" / "data"
)


def price_path(ticker: str, data_dir: Optional[Path] = None) -> Path:
    base = data_dir or DATA_DIR
    ticker_dir = base / "tickers_20260716"
    matches = list(ticker_dir.glob(f"{ticker}_*.csv"))
    if not matches:
        raise FileNotFoundError(f"No CSV found for {ticker} in {ticker_dir}")
    return sorted(matches)[-1]


def load_ticker(ticker: str, column: Optional[str] = None, data_dir: Optional[Path] = None) -> pd.Series:
    fp = price_path(ticker, data_dir)
    df = pd.read_csv(fp, parse_dates=["Date"], index_col="Date")
    if column is None:
        if "Adj Close" in df.columns:
            column = "Adj Close"
        elif "Close" in df.columns:
            column = "Close"
        elif "VIX" in df.columns:
            column = "VIX"
        elif "VIXTERM" in df.columns:
            column = "VIXTERM"
        elif "CreditSpread_bp" in df.columns:
            column = "CreditSpread_bp"
        else:
            column = df.columns[0]
    return df[column].ffill()


def load_prices(data_dir: Optional[Path] = None) -> pd.DataFrame:
    base = data_dir or DATA_DIR
    merged = base / "_merged_prices_20260716.csv"
    if merged.exists():
        df = pd.read_csv(merged, parse_dates=["Date"], index_col="Date")
        return df

    csvs = sorted(base.glob("_merged_prices_*.csv"))
    if not csvs:
        raise FileNotFoundError(f"No _merged_prices_*.csv found in {base}")
    return pd.read_csv(csvs[-1], parse_dates=["Date"], index_col="Date")
