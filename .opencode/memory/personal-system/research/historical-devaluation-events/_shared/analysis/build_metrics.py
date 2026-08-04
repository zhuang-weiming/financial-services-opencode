import pandas as pd
import numpy as np
import json
import os

FRED = "_shared/fred"

def load(name):
    p = f"{FRED}/{name}.csv"
    if not os.path.exists(p):
        return None
    try:
        df = pd.read_csv(p, parse_dates=["observation_date"])
        return df.set_index("observation_date").iloc[:, 0]
    except:
        return None

def get_value_on(ser, date_str):
    if ser is None:
        return None
    target = pd.Timestamp(date_str)
    sub = ser[ser.index <= target]
    if len(sub) == 0:
        return None
    return sub.iloc[-1]

def period_change(ser, start, end):
    if ser is None:
        return None
    v_start = get_value_on(ser, start)
    v_end = get_value_on(ser, end)
    if v_start is None or v_end is None or v_start == 0:
        return None
    return (v_end / v_start - 1) * 100

def period_avg(ser, start, end):
    if ser is None:
        return None
    s, e = pd.Timestamp(start), pd.Timestamp(end)
    sub = ser[(ser.index >= s) & (ser.index <= e)].dropna()
    return sub.mean() if len(sub) else None

def safe_max(ser, start, end):
    if ser is None:
        return None
    s, e = pd.Timestamp(start), pd.Timestamp(end)
    sub = ser[(ser.index >= s) & (ser.index <= e)].dropna()
    return sub.max() if len(sub) else None

def safe_min(ser, start, end):
    if ser is None:
        return None
    s, e = pd.Timestamp(start), pd.Timestamp(end)
    sub = ser[(ser.index >= s) & (ser.index <= e)].dropna()
    return sub.min() if len(sub) else None

def cpi_yoy_avg(ser, start, end):
    if ser is None:
        return None
    s, e = pd.Timestamp(start), pd.Timestamp(end)
    sub = ser[(ser.index >= s) & (ser.index <= e)].dropna()
    return sub.pct_change(12).dropna().mean() * 100 if len(sub) else None

events = {}

# Event 1
events["E1"] = {
    "name": "1946-1974 Postwar Deleveraging",
    "period": "1946-01-01 to 1974-12-31",
    "duration_years": 29,
    "data": {
        "debt_gdp_1966": get_value_on(load("GFDEGDQ188S"), "1966-01-01"),
        "debt_gdp_1974": get_value_on(load("GFDEGDQ188S"), "1974-12-31"),
        "debt_gdp_change": period_change(load("GFDEGDQ188S"), "1966-01-01", "1974-12-31"),
        "cpi_1946": get_value_on(load("CPIAUCSL"), "1947-01-01"),
        "cpi_1974": get_value_on(load("CPIAUCSL"), "1974-12-01"),
        "cpi_change": period_change(load("CPIAUCSL"), "1947-01-01", "1974-12-01"),
        "cpi_yoy_avg": cpi_yoy_avg(load("CPIAUCSL"), "1947-01-01", "1974-12-01"),
        "gs10_avg": period_avg(load("GS10"), "1953-04-01", "1974-12-01"),
        "gs10_peak": safe_max(load("GS10"), "1953-04-01", "1974-12-01"),
        "gs10_end": get_value_on(load("GS10"), "1974-12-01"),
        "tb3ms_avg": period_avg(load("TB3MS"), "1946-01-01", "1974-12-01"),
        "tb3ms_peak": safe_max(load("TB3MS"), "1946-01-01", "1974-12-01"),
        "gold_ppi_change": period_change(load("WPU102"), "1946-01-01", "1974-12-01"),
        "gold_ppi_start": get_value_on(load("WPU102"), "1946-01-01"),
        "gold_ppi_end": get_value_on(load("WPU102"), "1974-12-01"),
        "ppi_change": period_change(load("PPIACO"), "1946-01-01", "1974-12-01"),
        "wti_71_74_change": period_change(load("WTISPLC"), "1971-01-01", "1974-12-01"),
        "fed_deficit_avg": period_avg(load("FGDEF"), "1947-01-01", "1974-12-01"),
        "fed_deficit_1974": get_value_on(load("FGDEF"), "1974-12-01"),
        "fed_deficit_max": safe_max(load("FGDEF"), "1947-01-01", "1974-12-01"),
        "gdp_nominal_change": period_change(load("GDP"), "1947-01-01", "1974-12-01"),
        "gdp_real_change": period_change(load("GDPC1"), "1947-01-01", "1974-12-01"),
    },
}

# Event 2
events["E2"] = {
    "name": "1971-1980 USD Decline",
    "period": "1971-01-01 to 1980-12-31",
    "duration_years": 10,
    "data": {
        "gold_official_1971": 35.0,
        "gold_ppi_start": get_value_on(load("WPU102"), "1971-01-01"),
        "gold_ppi_end": get_value_on(load("WPU102"), "1980-12-01"),
        "gold_ppi_change": period_change(load("WPU102"), "1971-01-01", "1980-12-01"),
        "usd_jpy_start": get_value_on(load("DEXJPUS"), "1971-01-04"),
        "usd_jpy_end": get_value_on(load("DEXJPUS"), "1980-12-31"),
        "usd_jpy_change": period_change(load("DEXJPUS"), "1971-01-04", "1980-12-31"),
        "usd_dem_start": get_value_on(load("EXGEUS"), "1971-01-01"),
        "usd_dem_end": get_value_on(load("EXGEUS"), "1980-12-01"),
        "usd_dem_change": period_change(load("EXGEUS"), "1971-01-01", "1980-12-01"),
        "usd_chf_start": get_value_on(load("EXSZUS"), "1971-01-01"),
        "usd_chf_end": get_value_on(load("EXSZUS"), "1980-12-01"),
        "usd_chf_change": period_change(load("EXSZUS"), "1971-01-01", "1980-12-01"),
        "usd_gbp_change": period_change(load("DEXUSUK"), "1971-01-04", "1980-12-31"),
        "usd_cad_change": period_change(load("EXCAUS"), "1971-01-01", "1980-12-01"),
        "usd_frf_change": period_change(load("EXFRUS"), "1971-01-01", "1980-12-01"),
        "usd_itl_change": period_change(load("EXITUS"), "1971-01-01", "1980-12-01"),
        "twi_start": get_value_on(load("TWEXM"), "1973-01-03"),
        "twi_end": get_value_on(load("TWEXM"), "1980-12-31"),
        "twi_change": period_change(load("TWEXM"), "1973-01-03", "1980-12-31"),
        "twi_peak": safe_max(load("TWEXM"), "1973-01-03", "1980-12-31"),
        "twi_trough": safe_min(load("TWEXM"), "1973-01-03", "1980-12-31"),
        "cpi_change": period_change(load("CPIAUCSL"), "1971-01-01", "1980-12-01"),
        "cpi_yoy_avg": cpi_yoy_avg(load("CPIAUCSL"), "1971-01-01", "1980-12-01"),
        "cpi_yoy_peak": safe_max(load("CPIAUCSL")["1971-01-01":"1980-12-01"].pct_change(12).dropna() * 100, "1971-01-01", "1980-12-01"),
        "gs10_avg": period_avg(load("GS10"), "1971-01-01", "1980-12-01"),
        "gs10_end": get_value_on(load("GS10"), "1980-12-01"),
        "gs10_peak": safe_max(load("GS10"), "1971-01-01", "1980-12-01"),
        "fedfunds_avg": period_avg(load("FEDFUNDS"), "1971-01-01", "1980-12-01"),
        "fedfunds_peak": safe_max(load("FEDFUNDS"), "1971-01-01", "1980-12-01"),
        "fed_debt_gdp_1971": get_value_on(load("GFDEGDQ188S"), "1971-01-01"),
        "fed_debt_gdp_1980": get_value_on(load("GFDEGDQ188S"), "1980-12-01"),
        "wti_change": period_change(load("WTISPLC"), "1971-01-01", "1980-12-01"),
        "wti_peak": safe_max(load("WTISPLC"), "1971-01-01", "1980-12-01"),
        "wti_end_1980": get_value_on(load("WTISPLC"), "1980-12-01"),
    },
}

# Event 3
events["E3"] = {
    "name": "1985-1988 Plaza Accord",
    "period": "1985-09-22 to 1988-12-31",
    "duration_years": 3.3,
    "data": {
        "usd_jpy_start": get_value_on(load("DEXJPUS"), "1985-09-22"),
        "usd_jpy_end": get_value_on(load("DEXJPUS"), "1988-12-31"),
        "usd_jpy_change": period_change(load("DEXJPUS"), "1985-09-22", "1988-12-31"),
        "usd_jpy_trough": safe_min(load("DEXJPUS"), "1985-09-22", "1988-12-31"),
        "usd_dem_start": get_value_on(load("EXGEUS"), "1985-09-22"),
        "usd_dem_end": get_value_on(load("EXGEUS"), "1988-12-01"),
        "usd_dem_change": period_change(load("EXGEUS"), "1985-09-22", "1988-12-01"),
        "usd_gbp_change": period_change(load("DEXUSUK"), "1985-09-22", "1988-12-31"),
        "usd_chf_change": period_change(load("EXSZUS"), "1985-09-22", "1988-12-01"),
        "twi_start": get_value_on(load("TWEXM"), "1985-09-22"),
        "twi_end": get_value_on(load("TWEXM"), "1988-12-31"),
        "twi_change": period_change(load("TWEXM"), "1985-09-22", "1988-12-31"),
        "twi_trough": safe_min(load("TWEXM"), "1985-09-22", "1988-12-31"),
        "cpi_change": period_change(load("CPIAUCSL"), "1985-09-22", "1988-12-01"),
        "cpi_yoy_avg": cpi_yoy_avg(load("CPIAUCSL"), "1985-09-22", "1988-12-01"),
        "gs10_avg": period_avg(load("GS10"), "1985-09-22", "1988-12-01"),
        "gs10_change": period_change(load("GS10"), "1985-09-22", "1988-12-01"),
        "gold_ppi_change": period_change(load("WPU102"), "1985-09-22", "1988-12-01"),
        "wti_change": period_change(load("WTISPLC"), "1985-09-22", "1988-12-01"),
    },
}

# Event 4
events["E4"] = {
    "name": "1979-1985 Volcker Era",
    "period": "1979-08-01 to 1985-08-31",
    "duration_years": 6,
    "data": {
        "cpi_change": period_change(load("CPIAUCSL"), "1979-08-01", "1985-08-01"),
        "cpi_yoy_avg": cpi_yoy_avg(load("CPIAUCSL"), "1979-08-01", "1985-08-01"),
        "cpi_yoy_peak": safe_max(load("CPIAUCSL")["1979-08-01":"1985-08-01"].pct_change(12).dropna() * 100, "1979-08-01", "1985-08-01"),
        "gs10_avg": period_avg(load("GS10"), "1979-08-01", "1985-08-01"),
        "gs10_peak": safe_max(load("GS10"), "1979-08-01", "1985-08-01"),
        "gs10_end": get_value_on(load("GS10"), "1985-08-01"),
        "tb3ms_avg": period_avg(load("TB3MS"), "1979-08-01", "1985-08-01"),
        "tb3ms_peak": safe_max(load("TB3MS"), "1979-08-01", "1985-08-01"),
        "fedfunds_avg": period_avg(load("FEDFUNDS"), "1979-08-01", "1985-08-01"),
        "fedfunds_peak": safe_max(load("FEDFUNDS"), "1979-08-01", "1985-08-01"),
        "fedfunds_end": get_value_on(load("FEDFUNDS"), "1985-08-01"),
        "real10y_avg": period_avg(load("REAINTRATREARAT10Y"), "1982-01-01", "1985-12-01"),
        "real10y_peak": safe_max(load("REAINTRATREARAT10Y"), "1982-01-01", "1985-12-01"),
        "real1y_avg": period_avg(load("REAINTRATREARAT1Y"), "1982-01-01", "1985-12-01"),
        "real1y_peak": safe_max(load("REAINTRATREARAT1Y"), "1982-01-01", "1985-12-01"),
        "usd_cad_start": get_value_on(load("EXCAUS"), "1979-08-01"),
        "usd_cad_end": get_value_on(load("EXCAUS"), "1985-08-01"),
        "usd_cad_change": period_change(load("EXCAUS"), "1979-08-01", "1985-08-01"),
        "usd_jpy_start": get_value_on(load("DEXJPUS"), "1979-08-01"),
        "usd_jpy_end": get_value_on(load("DEXJPUS"), "1985-08-31"),
        "usd_jpy_change": period_change(load("DEXJPUS"), "1979-08-01", "1985-08-31"),
        "usd_dem_start": get_value_on(load("EXGEUS"), "1979-08-01"),
        "usd_dem_end": get_value_on(load("EXGEUS"), "1985-08-01"),
        "usd_dem_change": period_change(load("EXGEUS"), "1979-08-01", "1985-08-01"),
        "usd_gbp_change": period_change(load("DEXUSUK"), "1979-08-01", "1985-08-31"),
        "twi_start": get_value_on(load("TWEXM"), "1979-08-01"),
        "twi_end": get_value_on(load("TWEXM"), "1985-08-31"),
        "twi_change": period_change(load("TWEXM"), "1979-08-01", "1985-08-31"),
        "twi_peak": safe_max(load("TWEXM"), "1979-08-01", "1985-08-31"),
        "gold_ppi_change": period_change(load("WPU102"), "1979-08-01", "1985-08-01"),
        "gold_ppi_start": get_value_on(load("WPU102"), "1979-08-01"),
        "gold_ppi_end": get_value_on(load("WPU102"), "1985-08-01"),
        "fed_debt_gdp_start": get_value_on(load("GFDEGDQ188S"), "1979-08-01"),
        "fed_debt_gdp_end": get_value_on(load("GFDEGDQ188S"), "1985-08-01"),
        "fed_debt_gdp_change": period_change(load("GFDEGDQ188S"), "1979-08-01", "1985-08-01"),
        "fed_deficit_avg": period_avg(load("FGDEF"), "1979-08-01", "1985-08-01"),
        "fed_deficit_peak": safe_max(load("FGDEF"), "1979-08-01", "1985-08-01"),
        "wti_change": period_change(load("WTISPLC"), "1979-08-01", "1985-08-01"),
        "wti_peak": safe_max(load("WTISPLC"), "1979-08-01", "1985-08-01"),
        "wti_end": get_value_on(load("WTISPLC"), "1985-08-01"),
    },
}

# Event 5
events["E5"] = {
    "name": "1997-1998 Asian Crisis",
    "period": "1997-07-01 to 1998-12-31",
    "duration_years": 1.5,
    "data": {
        "usd_thb_start": get_value_on(load("DEXTHUS"), "1997-07-01"),
        "usd_thb_end": get_value_on(load("DEXTHUS"), "1998-12-31"),
        "usd_thb_change": period_change(load("DEXTHUS"), "1997-07-01", "1998-12-31"),
        "usd_thb_peak": safe_max(load("DEXTHUS"), "1997-07-01", "1998-12-31"),
        "usd_myr_start": get_value_on(load("DEXMAUS"), "1997-07-01"),
        "usd_myr_end": get_value_on(load("DEXMAUS"), "1998-12-31"),
        "usd_myr_change": period_change(load("DEXMAUS"), "1997-07-01", "1998-12-31"),
        "usd_myr_peak": safe_max(load("DEXMAUS"), "1997-07-01", "1998-12-31"),
        "usd_krw_start": get_value_on(load("DEXKOUS"), "1997-07-01"),
        "usd_krw_end": get_value_on(load("DEXKOUS"), "1998-12-31"),
        "usd_krw_change": period_change(load("DEXKOUS"), "1997-07-01", "1998-12-31"),
        "usd_krw_peak": safe_max(load("DEXKOUS"), "1997-07-01", "1998-12-31"),
        "usd_sgd_change": period_change(load("DEXSIUS"), "1997-07-01", "1998-12-31"),
        "usd_jpy_change": period_change(load("DEXJPUS"), "1997-07-01", "1998-12-31"),
        "usd_inr_change": period_change(load("DEXINUS"), "1997-07-01", "1998-12-31"),
        "twi_change": period_change(load("TWEXM"), "1997-07-01", "1998-12-31"),
        "cpi_change": period_change(load("CPIAUCSL"), "1997-07-01", "1998-12-01"),
        "gs10_change": period_change(load("GS10"), "1997-07-01", "1998-12-01"),
        "gs10_avg": period_avg(load("GS10"), "1997-07-01", "1998-12-01"),
        "wti_change": period_change(load("DCOILWTICO"), "1997-07-01", "1998-12-31"),
        "wti_avg": period_avg(load("DCOILWTICO"), "1997-07-01", "1998-12-31"),
    },
}

# Event 6
events["E6"] = {
    "name": "2008-2015 GFC + USD Cycle",
    "period": "2008-01-01 to 2015-12-31",
    "duration_years": 8,
    "data": {
        "cpi_change": period_change(load("CPIAUCSL"), "2008-01-01", "2015-12-01"),
        "cpi_yoy_avg": cpi_yoy_avg(load("CPIAUCSL"), "2008-01-01", "2015-12-01"),
        "gs10_avg": period_avg(load("GS10"), "2008-01-01", "2015-12-01"),
        "gs10_change": period_change(load("GS10"), "2008-01-01", "2015-12-01"),
        "eur_usd_start": get_value_on(load("DEXUSEU"), "2008-01-02"),
        "eur_usd_end": get_value_on(load("DEXUSEU"), "2015-12-31"),
        "eur_usd_change": period_change(load("DEXUSEU"), "2008-01-02", "2015-12-31"),
        "eur_usd_peak": safe_max(load("DEXUSEU"), "2008-01-02", "2015-12-31"),
        "eur_usd_trough": safe_min(load("DEXUSEU"), "2008-01-02", "2015-12-31"),
        "usd_jpy_change": period_change(load("DEXJPUS"), "2008-01-02", "2015-12-31"),
        "usd_gbp_change": period_change(load("DEXUSUK"), "2008-01-02", "2015-12-31"),
        "twi_broad_change": period_change(load("DTWEXBGS"), "2008-01-02", "2015-12-31"),
        "twi_broad_peak": safe_max(load("DTWEXBGS"), "2008-01-02", "2015-12-31"),
        "twi_broad_trough": safe_min(load("DTWEXBGS"), "2008-01-02", "2015-12-31"),
        "wti_change": period_change(load("DCOILWTICO"), "2008-01-02", "2015-12-31"),
        "wti_peak": safe_max(load("DCOILWTICO"), "2008-01-02", "2015-12-31"),
        "wti_trough": safe_min(load("DCOILWTICO"), "2008-01-02", "2015-12-31"),
    },
}

def clean(o):
    if isinstance(o, dict):
        return {k: clean(v) for k, v in o.items()}
    if isinstance(o, list):
        return [clean(v) for v in o]
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return float(o)
    if isinstance(o, (np.bool_,)):
        return bool(o)
    try:
        if pd.isna(o):
            return None
    except:
        pass
    return o

with open("_shared/analysis/event_metrics.json", "w") as f:
    json.dump(clean(events), f, indent=2)

print(json.dumps(clean(events), indent=2)[:3000])
