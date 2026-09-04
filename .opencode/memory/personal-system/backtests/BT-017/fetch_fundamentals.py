#!/usr/bin/env python3
"""
BT-017 — fundamentals fetch (ROE / debt / PB percentile inputs) for the 200-pool.

Sources (Tier-2, akshare):
  - ROE (净资产收益率) + 资产负债率: stock_financial_abstract (annual reports)
  - PB history: stock_zh_valuation_baidu (市净率, 近三年)

PIT convention: an event on date T uses the latest ANNUAL report whose
publication deadline has passed (A-share annual reports due by Apr 30 of the
following year):
  - T <= 2025-04-30  -> FY2023 annual
  - 2025-05-01..2026-04-30 -> FY2024
  - T >= 2026-05-01  -> FY2025

Output: results/fundamentals.parquet (per code: roe_by_fy, debt_by_fy,
pb_series). Cached so the main script is reproducible without re-fetching.
"""
import akshare as ak
import pandas as pd
import numpy as np
import json, os, time, sys, traceback

ROOT = '/Users/weimingzhuang/Documents/source_code/financial-services-opencode'
POOL = f'{ROOT}/.opencode/memory/personal-system/backtests/BT-011/pool_200.json'
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'results')
os.makedirs(OUT, exist_ok=True)
OUT_PQ = f'{OUT}/fundamentals.parquet'
OUT_META = f'{OUT}/fundamentals_fetch_meta.json'

pool = json.load(open(POOL))
codes = [p['code'] for p in pool]

# fiscal-year columns present in stock_financial_abstract (annual reports end 1231)
ANNUAL_COLS = [c for c in ['20231231', '20241231', '20251231']]

def extract_roe_debt(code: str):
    """Return dict {fy: {'roe': float|None, 'debt': float|None}} for annual FYs."""
    df = ak.stock_financial_abstract(symbol=code)
    if df is None or len(df) == 0:
        return {}
    # 净资产收益率(ROE) rows: pick the '加权' style first occurrence (row index 11 style);
    # robust: take the first row whose 指标 contains 净资产收益率(ROE)
    roe_rows = df[df['指标'].astype(str).str.contains('净资产收益率\(ROE\)')]
    debt_rows = df[df['指标'].astype(str).str.contains('资产负债率')]
    out = {}
    for fy in ANNUAL_COLS:
        roe = None
        debt = None
        if len(roe_rows):
            v = roe_rows[fy].dropna()
            if len(v):
                roe = float(v.iloc[0])
        if len(debt_rows):
            v = debt_rows[fy].dropna()
            if len(v):
                debt = float(v.iloc[0])
        if roe is not None or debt is not None:
            out[fy] = {'roe': roe, 'debt': debt}
    return out

def fetch_pb(code: str):
    """Return DataFrame(date, pb) or None."""
    try:
        df = ak.stock_zh_valuation_baidu(symbol=code, indicator='市净率', period='近三年')
        if df is None or len(df) == 0:
            return None
        df = df.rename(columns={'date': 'date', 'value': 'pb'})
        df['date'] = pd.to_datetime(df['date'])
        df['pb'] = pd.to_numeric(df['pb'], errors='coerce')
        df = df.dropna(subset=['pb']).sort_values('date')
        return df[['date', 'pb']] if len(df) else None
    except Exception:
        return None

# ---------------- main fetch ----------------
records = {}
meta = {'codes_total': len(codes), 'ok': [], 'fail': [], 'start': time.strftime('%Y-%m-%d %H:%M:%S')}
t0 = time.time()
for i, c in enumerate(codes):
    rec = {'code': c}
    try:
        fy = extract_roe_debt(c)
        rec['roe_debt_by_fy'] = fy
        if fy:
            meta['ok'].append(c)
        else:
            meta['fail'].append((c, 'abstract_empty'))
    except Exception as e:
        meta['fail'].append((c, f'abstract:{type(e).__name__}:{str(e)[:60]}'))
        rec['roe_debt_by_fy'] = {}
    try:
        pb = fetch_pb(c)
        if pb is not None:
            rec['pb'] = pb.to_dict('list')
        else:
            rec['pb'] = None
            if c not in [x[0] for x in meta['fail']]:
                meta['fail'].append((c, 'pb_empty'))
    except Exception as e:
        meta['fail'].append((c, f'pb:{type(e).__name__}:{str(e)[:60]}'))
        rec['pb'] = None
    records[c] = rec
    if (i + 1) % 20 == 0:
        print(f"  [{i+1}/{len(codes)}] elapsed {time.time()-t0:.0f}s", flush=True)
    # polite pacing
    time.sleep(0.15)

meta['elapsed_s'] = round(time.time() - t0, 1)
meta['end'] = time.strftime('%Y-%m-%d %H:%M:%S')
meta['ok_count'] = len(meta['ok'])

with open(f'{OUT}/fundamentals_raw.json', 'w') as f:
    json.dump(records, f, ensure_ascii=False, default=str)
with open(OUT_META, 'w') as f:
    json.dump(meta, f, ensure_ascii=False, indent=1)

print(f"\nDone. elapsed={meta['elapsed_s']}s ok={len(meta['ok'])} fail={len(meta['fail'])}")
for c, why in meta['fail'][:20]:
    print('  FAIL', c, why)
