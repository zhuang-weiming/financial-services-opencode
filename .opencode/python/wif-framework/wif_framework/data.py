from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

import pandas as pd

_env_path = os.environ.get("WIF_DATA_DIR", "")
DATA_DIR = (
    Path(_env_path).expanduser().resolve() if _env_path
    else Path(__file__).resolve().parents[4] / "example" / "wif-framework" / "data"
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
    else:
        csvs = sorted(base.glob("_merged_prices_*.csv"))
        if not csvs:
            raise FileNotFoundError(f"No _merged_prices_*.csv found in {base}")
        df = pd.read_csv(csvs[-1], parse_dates=["Date"], index_col="Date")

    ticker_dir = base / "tickers_20260716"
    extra_sources = {
        "DGS10": ("DGS10", "Close"),
        "T10YIE": ("T10YIE", "Close"),
        "BAMLH0A0HYM2": ("BAMLH0A0HYM2", "Close"),
    }
    for col_name, (prefix, col) in extra_sources.items():
        fp = ticker_dir / f"{prefix}_*.csv"
        matches = list(ticker_dir.glob(f"{prefix}_*.csv"))
        if matches:
            src = pd.read_csv(sorted(matches)[-1], parse_dates=["Date"], index_col="Date")
            df[col_name] = src[col].reindex(df.index).ffill()

    credit_path = ticker_dir / "CreditSpread_BAA_1986_2026.csv"
    if credit_path.exists():
        cred = pd.read_csv(credit_path, parse_dates=["Date"], index_col="Date")
        df["F29_bp"] = cred["CreditSpread_bp"].reindex(df.index).ffill()

    return df
