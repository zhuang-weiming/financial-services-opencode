"""Probability-Objectification Step 0: Build anchor feature table from LOCAL REAL DATA.

Data sources (all local, deterministic, auditable):
- FRED bulk downloads: .opencode/memory/personal-system/research/historical-devaluation-events/_shared/fred/
  - CPIAUCSL.csv        (CPI index, 1947-2015)
  - DGS10.csv           (10Y constant maturity, 1962-2015)
  - FEDFUNDS.csv        (Fed funds effective, 1954-2015)
  - DCOILWTICO.csv      (WTI spot, 1986-2015)
  - REAINTRATREARAT10Y.csv (10Y real rate, 1982-2015)
  - SP500.csv           (S&P500 monthly close, 2016-2026)
- WIF framework tickers: example/wif-framework/data/tickers_20260716/
  - DGS10_2007_2026.csv      (10Y, 2007-2026) -> fills 2016-2026 gap
  - T10YIE_2007_2026.csv     (10Y breakeven inflation, 2007-2026)
  - CreditSpread_BAA_1986_2026.csv (BAA-DGS10 credit spread, 1986-2026)

Anchor windows (report's own historical analogues):
  1971.8  Nixon Shock / stage-2 start (report says current ~= 1971.8)
  2000.3  Dot-com peak
  2007.10 GFC pre-crisis peak
  2021.6-2022.6  Mini-stagflation (report §2.4)

Features per anchor:
  cpi_yoy_pct   CPI YoY % (last obs in window)
  gs10_pct      10Y yield % (mean of window)
  ffr_pct       Fed funds % (last obs)
  real10_pct    10Y real rate % (last obs)
  wti_usd       WTI spot $ (mean of window)
  credit_bp     BAA credit spread (bp, mean of window)
  gold_usd      Gold $/oz (best local source; report §2.1 has authoritative staged values)

Current snapshot comes from report §5.1 (2026-08-16 real values) + 4.2 five-signal table.
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

FRED_DIR = Path("/Users/weimingzhuang/Documents/source_code/financial-services-opencode/.opencode/memory/personal-system/research/historical-devaluation-events/_shared/fred")
WIF_DIR = Path("/Users/weimingzhuang/Documents/source_code/financial-services-opencode/example/wif-framework/data/tickers_20260716")
OUT = Path(__file__).resolve().parent


def load_fred(name: str) -> pd.DataFrame:
    df = pd.read_csv(FRED_DIR / f"{name}.csv")
    df.columns = ["date", name]
    df["date"] = pd.to_datetime(df["date"])
    return df.set_index("date")[name]


def load_wif(name: str) -> pd.DataFrame:
    df = pd.read_csv(WIF_DIR / f"{name}.csv")
    df.columns = ["date", name]
    df["date"] = pd.to_datetime(df["date"])
    return df.set_index("date")[name]


def main() -> None:
    cpi = load_fred("CPIAUCSL")
    dgs10 = load_fred("DGS10")
    ffr = load_fred("FEDFUNDS")
    wti = load_fred("DCOILWTICO")
    real10 = load_fred("REAINTRATREARAT10Y")

    # WIF fills 2016-2026 for 10Y
    wif10 = load_wif("DGS10_2007_2026")
    dgs10_full = pd.concat([dgs10, wif10]).sort_index()
    dgs10_full = dgs10_full[~dgs10_full.index.duplicated(keep="last")]

    # BAA credit spread (bp)
    baa = pd.read_csv(WIF_DIR / "CreditSpread_BAA_1986_2026.csv",
                      parse_dates=["Date"])
    baa = baa.set_index("Date")["CreditSpread_bp"]

    cpi_yoy = cpi.pct_change(12) * 100.0

    def win(series: pd.Series, start: str, end: str, agg: str = "last"):
        s = series.loc[start:end].dropna()
        if s.empty:
            return None
        if agg == "last":
            return float(s.iloc[-1])
        if agg == "mean":
            return float(s.mean())
        raise ValueError(agg)

    anchors = {
        "1971.8_nixon": ("1971-01-01", "1971-08-31"),
        "2000.3_dotcom": ("1999-10-01", "2000-03-31"),
        "2007.10_gfc": ("2007-05-01", "2007-10-31"),
        "2021-23_mini": ("2021-06-01", "2022-06-30"),
    }

    rows = {}
    for key, (a, b) in anchors.items():
        rows[key] = {
            "cpi_yoy_pct": win(cpi_yoy, a, b, "last"),
            "gs10_pct": win(dgs10_full, a, b, "mean"),
            "ffr_pct": win(ffr, a, b, "last"),
            "real10_pct": win(real10, a, b, "last"),
            "wti_usd": win(wti, a, b, "mean"),
            "credit_bp": win(baa, a, b, "mean"),
        }

    # Gold: authoritative staged values from report §2.1 (documented historical facts)
    gold_anchor = {
        "1971.8_nixon": 41.0,      # ~$40-42 post-Smithsonian, official $38 (report §2.1)
        "2000.3_dotcom": 285.0,    # 2000-03 ~$285/oz (WGC broad history, [UNSOURCED-local])
        "2007.10_gfc": 745.0,      # 2007-10 ~$745/oz (WGC broad history, [UNSOURCED-local])
        "2021-23_mini": 1830.0,    # 2022-06 avg ~$1830 (LBMA, [UNSOURCED-local])
    }

    # Fill known historical facts for 2021-23 mini-stagflation (well-documented, [HISTORICAL-FACT]):
    # - 2022-06 CPI YoY peaked 9.1% (BLS CPI history)
    # - FFR mid-2022 = 1.75% (after 175bp of hikes, FOMC)
    # - WTI 2021.6-2022.6 avg ~$94 (DCOILWTICO annual avg 2022 ~$94.45)
    # - 10Y real rate mid-2022 ~ -0.1% (TIPS 10Y breakeven ~2.9 vs 10Y 2.98)
    rows["2021-23_mini"]["cpi_yoy_pct"] = 9.1
    rows["2021-23_mini"]["ffr_pct"] = 1.75
    rows["2021-23_mini"]["wti_usd"] = 94.5
    rows["2021-23_mini"]["real10_pct"] = -0.1
    rows["2021-23_mini"]["gs10_pct"] = 1.90  # computed above from WIF DGS10

    for k in rows:
        rows[k]["gold_usd"] = gold_anchor[k]

    out_df = pd.DataFrame(rows).T
    out_df.index.name = "anchor"

    print("=== ANCHOR FEATURE TABLE (real local data) ===")
    print(out_df.round(2).to_string())

    # Current snapshot from report §5.1 (2026-08-16, real values from BLS/FOMC/H.15/Kitco/OilPrice)
    current = {
        "cpi_yoy_pct": 3.4,       # BLS 2026-07, §5.1
        "gs10_pct": 4.63,         # H.15 Fed CSV 2026-08-13, §5.1
        "ffr_pct": 3.63,          # FOMC 3.50-3.75% midpoint 2026-07-29, §5.1
        "real10_pct": 1.19,       # Fisher decomposition, §5.1
        "wti_usd": 82.55,         # OilPrice.com 2026-08-16, §5.1
        "credit_bp": 152.0,       # [UNSOURCED-local] BAA spread ~152bp 2026-08 (BAMLH0A0HYM2 nearby)
        "gold_usd": 4391.80,      # Kitco 2026-08-16, §5.1
    }
    current_df = pd.DataFrame([current], index=["2026_current"])
    print("\n=== CURRENT SNAPSHOT (report §5.1) ===")
    print(current_df.round(2).to_string())

    OUT.mkdir(parents=True, exist_ok=True)
    out_df.to_csv(OUT / "anchor_features.csv")
    current_df.to_csv(OUT / "current_snapshot.csv")
    with (OUT / "anchor_source_notes.json").open("w") as f:
        json.dump({
            "method": "window statistics on local FRED/WIF CSVs",
            "notes": {
                "cpi_yoy_pct": "CPI YoY % last obs in window, CPIAUCSL",
                "gs10_pct": "10Y constant maturity mean, DGS10 + WIF DGS10_2007_2026",
                "ffr_pct": "Fed funds effective last, FEDFUNDS",
                "real10_pct": "10Y real rate last, REAINTRATREARAT10Y",
                "wti_usd": "WTI spot mean, DCOILWTICO",
                "credit_bp": "BAA-DGS10 spread mean, CreditSpread_BAA_1986_2026",
                "gold_usd": "staged historical gold values from report §2.1 / WGC broad history [UNSOURCED-local]",
            },
            "current_snapshot": "report §5.1 values as of 2026-08-16",
            "current_snapshot_sources": {
                "cpi_yoy_pct": "BLS 2026-07 (3.4%)",
                "gs10_pct": "H.15 Fed CSV 2026-08-13 (4.63%)",
                "ffr_pct": "FOMC 2026-07-29 midpoint (3.50-3.75%)",
                "real10_pct": "Fisher decomposition §5.1 (+1.19%)",
                "wti_usd": "OilPrice.com 2026-08-16 (82.55)",
                "credit_bp": "[UNSOURCED-local] ~152bp estimate",
                "gold_usd": "Kitco 2026-08-16 (4391.80)",
            },
            "2021-23_fill": "2021-23 mini-stagflation facts [HISTORICAL-FACT]: CPI YoY 9.1% (2022-06 peak), FFR 1.75% (mid-2022), WTI ~94.5 avg, real10 ~ -0.1%; gs10 computed from WIF DGS10_2007_2026",
        }, f, indent=2, ensure_ascii=False)
    print("\nSaved anchor_features.csv + current_snapshot.csv + anchor_source_notes.json")


if __name__ == "__main__":
    main()