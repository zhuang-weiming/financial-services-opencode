"""
Unified data loader for technical analysis skills — works with ANY ticker.

Supported sources (in priority order, per `data-priority.md`):
  1. llmquant-data MCP (US equities / crypto) — Tier 1
  2. yfinance (US / global equities, ETFs, indices) — Tier 2
  3. akshare (A-shares, HK, global) — Tier 2
  4. tushare (A-shares, needs token) — Tier 2
  5. mootdx (A-shares, TCP direct, never banned) — Tier 2
  6. Local CSV — fallback

Output is always a normalized DataFrame with columns:
    [date, open, high, low, close, volume]

Usage:
    from data_loader import load_ohlcv
    df = load_ohlcv("AAPL")          # US equity via llmquant-data/yfinance
    df = load_ohlcv("600519", market="cn")  # A-share via akshare/mootdx
    df = load_ohlcv("BTC-USD", market="crypto")  # crypto
    df = load_ohlcv("data.csv")      # local CSV

Ticker normalization:
    US: AAPL, MSFT, BRK.B → auto
    A-share: 600519, 000001 → auto-prefix sh/sz/bj
    HK: 00700 → HK prefix
    Crypto: BTC-USD, ETH-USD
"""
import os
from pathlib import Path
import pandas as pd


def _normalize_cn_symbol(symbol: str) -> str:
    """A-share symbol normalization: 600519 → sh600519, 000001 → sz000001."""
    s = symbol.strip()
    if s.startswith(("sh", "sz", "bj")):
        return s
    digits = "".join(c for c in s if c.isdigit())
    if len(digits) == 6:
        code = digits
        if code.startswith(("600", "601", "603", "605", "688", "689")):
            return f"sh{code}"
        elif code.startswith(("000", "001", "002", "003", "300", "301", "200")):
            return f"sz{code}"
        elif code.startswith(("8", "4", "9")):
            return f"bj{code}"
        return f"sh{code}"  # default
    return s


def load_from_yfinance(symbol: str, period: str = "1y", **kwargs) -> pd.DataFrame:
    """Load OHLCV from Yahoo Finance (US/global/HK/crypto)."""
    import yfinance as yf
    t = yf.Ticker(symbol)
    df = t.history(period=period, auto_adjust=False)
    if df is None or df.empty:
        raise ValueError(f"yfinance returned no data for {symbol}")
    df = df.reset_index()
    df.columns = [str(c).lower() for c in df.columns]
    # Normalize date column
    date_col = "date" if "date" in df.columns else df.columns[0]
    df["date"] = pd.to_datetime(df[date_col])
    keep = ["date", "open", "high", "low", "close", "volume"]
    df = df[[c for c in keep if c in df.columns]]
    return df


def load_from_mcp(symbol: str, limit: int = 500, **kwargs) -> pd.DataFrame:
    """Load OHLCV from llmquant-data MCP (Tier 1 — US equities + crypto).

    Priority source per data-priority.md. Calls the MCP tool via a thin
    shim: this works when the tool is available in the agent runtime.
    Fallback to yfinance if the MCP is unreachable.
    """
    # Try llmquant-data MCP equity_historical_prices
    try:
        import json
        import subprocess
        import sys

        # Preferred: direct MCP tool call (available in agent runtime)
        # We detect it by checking if a helper exists, else use CLI.
        # Simple approach: attempt to read from a local cache or call MCP.
        # The MCP tool returns {data: {prices: [{time, open, high, low, close, volume}]}}
        mcp_tool = kwargs.get("mcp_tool")
        if mcp_tool is not None:
            result = mcp_tool(ticker=symbol, limit=limit)
            prices = result.get("data", {}).get("prices", [])
            if prices:
                df = pd.DataFrame(prices)
                df = df.rename(columns={"time": "date"})
                df["date"] = pd.to_datetime(df["date"])
                for c in ["open", "high", "low", "close", "volume"]:
                    if c not in df.columns:
                        raise ValueError(f"MCP response missing {c}")
                keep = ["date", "open", "high", "low", "close", "volume"]
                df = df[keep].tail(limit)
                return df
        raise ValueError("MCP tool not provided via mcp_tool kwarg")
    except Exception as e:
        raise ValueError(f"llmquant-data MCP unavailable: {e}")


def load_from_akshare(symbol: str, market: str = "cn", period: str = "daily",
                      limit: int = 500, **kwargs) -> pd.DataFrame:
    """Load from AKShare (A-shares / HK / global)."""
    import akshare as ak
    if market == "cn":
        sym = _normalize_cn_symbol(symbol)
        if "hfq" in kwargs and kwargs["hfq"]:
            df = ak.stock_zh_a_hist(symbol=sym[2:], period=period,
                                    start_date=kwargs.get("start", "20200101"),
                                    end_date=kwargs.get("end", "20991231"),
                                    adjust="hfq")
        else:
            df = ak.stock_zh_a_hist(symbol=sym[2:], period=period,
                                    start_date=kwargs.get("start", "20200101"),
                                    end_date=kwargs.get("end", "20991231"),
                                    adjust="qfq")
        df = df.rename(columns={
            "日期": "date", "开盘": "open", "最高": "high",
            "最低": "low", "收盘": "close", "成交量": "volume"
        })
        df["date"] = pd.to_datetime(df["date"])
        df = df[[c for c in ["date", "open", "high", "low", "close", "volume"] if c in df.columns]]
        return df.tail(limit)
    elif market == "hk":
        sym = _normalize_cn_symbol(symbol)
        df = ak.stock_hk_daily(symbol=f"0{sym[-4:]}" if len(sym) < 6 else sym)
        df = df.rename(columns={"date": "date", "open": "open", "high": "high",
                                "low": "low", "close": "close", "volume": "volume"})
        df["date"] = pd.to_datetime(df["date"])
        return df.tail(limit)
    else:
        raise ValueError(f"akshare unsupported market: {market}")


def load_from_tushare(symbol: str, market: str = "cn", **kwargs) -> pd.DataFrame:
    """Load from Tushare (needs token in TUSHARE_TOKEN env)."""
    import tushare as ts
    token = os.getenv("TUSHARE_TOKEN")
    if not token:
        raise ValueError("TUSHARE_TOKEN env not set")
    ts.set_token(token)
    pro = ts.pro_api()
    if market == "cn":
        sym = _normalize_cn_symbol(symbol)
        df = pro.daily(ts_code=f"{sym[2:]}.{'SH' if sym.startswith('sh') else 'SZ'}",
                       start_date=kwargs.get("start", "20200101"),
                       end_date=kwargs.get("end", "20991231"))
        df = df.rename(columns={"trade_date": "date", "vol": "volume"})
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date")
        keep = ["date", "open", "high", "low", "close", "volume"]
        return df[[c for c in keep if c in df.columns]]
    raise ValueError(f"tushare unsupported market: {market}")


def load_from_mootdx(symbol: str, **kwargs) -> pd.DataFrame:
    """Load A-share daily bars via mootdx (TCP direct, never IP-banned)."""
    from mootdx.quotes import Quotes
    sym = _normalize_cn_symbol(symbol)
    client = Quotes.factory(market="std")
    df = client.bars(symbol=sym[2:], frequency=9, offset=kwargs.get("limit", 500))
    if df is None or df.empty:
        raise ValueError(f"mootdx returned no data for {symbol}")
    df = df.rename(columns={"datetime": "date", "vol": "volume"})
    df["date"] = pd.to_datetime(df["date"])
    keep = ["date", "open", "high", "low", "close", "volume"]
    return df[[c for c in keep if c in df.columns]]


def load_from_local_csv(path: str, **kwargs) -> pd.DataFrame:
    """Load OHLCV from a local CSV file."""
    df = pd.read_csv(path)
    df.columns = [str(c).strip().lower() for c in df.columns]
    # Auto-detect date column
    for c in df.columns:
        if c in ("date", "datetime", "time", "日期", "trade_date"):
            df[c] = pd.to_datetime(df[c])
            df = df.rename(columns={c: "date"})
            break
    keep = ["date", "open", "high", "low", "close", "volume"]
    for c in keep:
        if c not in df.columns:
            # Chinese column fallback
            cn_map = {"open": "开盘", "high": "最高", "low": "最低",
                      "close": "收盘", "volume": "成交量"}
            if cn_map.get(c) in df.columns:
                df = df.rename(columns={cn_map[c]: c})
    df = df[[c for c in keep if c in df.columns]]
    return df


def load_ohlcv(symbol: str, market: str = "auto", period: str = "1y",
               limit: int = 500, **kwargs) -> pd.DataFrame:
    """Load OHLCV for ANY symbol with automatic fallback.

    Args:
        symbol: ticker (AAPL / 600519 / 00700 / BTC-USD / path-to-csv)
        market: "auto" | "us" | "cn" | "hk" | "crypto"
        period: yfinance period string (us/crypto): 1y, 6mo, 3mo, 1mo
        limit: max rows to keep
        kwargs: source="yfinance"|"akshare"|"tushare"|"mootdx" forces a source

    Returns:
        DataFrame with [date, open, high, low, close, volume]
    """
    # Local CSV shortcut
    if symbol.endswith(".csv") and Path(symbol).exists():
        return load_from_local_csv(symbol, **kwargs)

    # Infer market
    if market == "auto":
        if "-" in symbol and symbol.split("-")[1].upper() in ("USD", "USDT", "USDC"):
            market = "crypto"
        elif symbol[0].isdigit() and len(symbol) == 6:
            market = "cn"
        elif symbol.startswith(("sh", "sz", "bj")):
            market = "cn"
        elif symbol.startswith(("0", "1", "2", "3", "5", "6", "9")) and symbol.endswith((".HK", ".T", ".L")):
            market = "hk"
        else:
            market = "us"

    source = kwargs.get("source", "auto")
    errors = []

    if market == "us":
        # Tier 1: llmquant-data MCP (passed in by the agent runtime)
        if source in ("auto", "mcp"):
            try:
                mcp_tool = kwargs.pop("mcp_tool", None)
                if mcp_tool is not None:
                    return load_from_mcp(symbol, limit=limit, mcp_tool=mcp_tool, **kwargs)
            except Exception as e:
                errors.append(f"mcp: {e}")
        if source in ("auto", "yfinance"):
            try:
                return load_from_yfinance(symbol, period=period, **kwargs).tail(limit)
            except Exception as e:
                errors.append(f"yfinance: {e}")
        if source == "yfinance":
            raise ValueError(f"all sources failed for {symbol}: {errors}")
        raise ValueError(f"no US data source available for {symbol}: {errors}")

    elif market == "cn":
        for src in (["mootdx", "akshare", "tushare"] if source == "auto" else [source]):
            try:
                if src == "mootdx":
                    return load_from_mootdx(symbol, limit=limit, **kwargs)
                elif src == "akshare":
                    return load_from_akshare(symbol, market="cn", limit=limit, **kwargs)
                elif src == "tushare":
                    return load_from_tushare(symbol, market="cn", **kwargs)
            except Exception as e:
                errors.append(f"{src}: {e}")
        raise ValueError(f"all CN sources failed for {symbol}: {errors}")

    elif market == "hk":
        if source in ("auto", "akshare"):
            try:
                return load_from_akshare(symbol, market="hk", limit=limit, **kwargs)
            except Exception as e:
                errors.append(f"akshare: {e}")
        raise ValueError(f"all HK sources failed for {symbol}: {errors}")

    elif market == "crypto":
        if source in ("auto", "yfinance"):
            try:
                return load_from_yfinance(symbol, period=period, **kwargs).tail(limit)
            except Exception as e:
                errors.append(f"yfinance: {e}")
        raise ValueError(f"all crypto sources failed for {symbol}: {errors}")

    raise ValueError(f"unsupported market: {market}")


def infer_market(symbol: str) -> str:
    """Infer market from symbol without loading data."""
    if "-" in symbol and symbol.split("-")[1].upper() in ("USD", "USDT", "USDC"):
        return "crypto"
    if symbol[0].isdigit() and len(symbol) == 6:
        return "cn"
    if symbol.startswith(("sh", "sz", "bj")):
        return "cn"
    return "us"


if __name__ == "__main__":
    import sys
    ticker = sys.argv[1] if len(sys.argv) > 1 else "AAPL"
    df = load_ohlcv(ticker)
    print(f"Loaded {ticker}: {len(df)} rows, {df['date'].iloc[0].date()} → {df['date'].iloc[-1].date()}")
    print(df.tail(3))
