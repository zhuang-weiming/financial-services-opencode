#!/usr/bin/env python3
"""
BT-015 — BUY_LADDER 信号级独立事件研究 (积分权重数据基础)

对所有缓存非零信号做独立事件研究 (同 BT-013/014 方法):
  事件 = 当日 sig>0 且代码在 200 池 → 未来 20/60 日 log 收益 vs 当日同池截面基准
  输出每信号 2025牛/2026弱/全期的 α20/α60/win20/触发数/t/p

目的: 定 buy ladder 积分信号集与权重 (数据驱动, 非拍脑袋)
"""
import pandas as pd, numpy as np, json, glob, warnings, os
warnings.filterwarnings('ignore')
from scipy import stats

ROOT='/Users/weimingzhuang/Documents/source_code/financial-services-opencode'
CACHE=f'{ROOT}/.opencode/memory/personal-system/backtests/BT-011/results/signal_cache_v2.parquet'
POOL=f'{ROOT}/.opencode/memory/personal-system/backtests/BT-011/pool_200.json'
DAILY=f'{ROOT}/data/market/daily'
OUT=os.path.dirname(os.path.abspath(__file__))+'/results'
os.makedirs(OUT, exist_ok=True)

SIGS=['alpha_engine_v21','candlestick','ml_strategy','chanlun','technical_basic','ichimoku',
      'alpha_zoo','volatility','harmonic','turnover_anomaly','ad_line']
ZERO_SIGS=['smc','factor_research','multi_factor','pair_trading','sector_relative']

pool=json.load(open(POOL)); codes=[p['code'] for p in pool]
df=pd.read_parquet(CACHE); df['date']=pd.to_datetime(df['date']); df['year']=df['date'].dt.year

rows=[]  # 收益表 (同 BT-014)
for c in codes:
    g=glob.glob(f'{DAILY}/{c}*.csv')
    if not g: continue
    try:
        d=pd.read_csv(g[0]); d['date']=pd.to_datetime(d['date'])
        d=d.drop_duplicates('date').set_index('date')['close'].astype(float).sort_index()
        n=len(d)
        if n<60: continue
        s=np.log(d.to_numpy()); idx=d.index
        r20=pd.Series(np.nan,index=idx); r60=pd.Series(np.nan,index=idx)
        r20.iloc[:-21]=s[21:]-s[:-21]; r60.iloc[:-61]=s[61:]-s[:-61]
        rows.append(pd.DataFrame({'r20':r20,'r60':r60,'code':c}).reset_index())
    except Exception: pass
ret=pd.concat(rows,ignore_index=True); ret['date']=pd.to_datetime(ret['date'])
b20=ret.groupby('date')['r20'].mean().rename('b20'); b60=ret.groupby('date')['r60'].mean().rename('b60')
ret=ret.merge(b20,left_on='date',right_index=True).merge(b60,left_on='date',right_index=True)
ret['alpha20']=ret['r20']-ret['b20']; ret['alpha60']=ret['r60']-ret['b60']
full=df[['code','date','year']+SIGS].merge(ret[['code','date','alpha20','alpha60']],on=['code','date'],how='left')

out=[]
for sig in SIGS:
    for lab,ym in [('2025',2025),('2026',2026),('all',None)]:
        sub=full if ym is None else full[full['year']==ym]
        ev=sub[sub[sig]>0].dropna(subset=['alpha20'])
        n=len(ev); nc=sub['code'].nunique(); ny=2 if lab=='all' else 1
        if n<5: continue
        a20=ev['alpha20'].mean(); a60=ev['alpha60'].dropna().mean()
        win=(ev['alpha20']>0).mean(); t,p=stats.ttest_1samp(ev['alpha20'],0)
        out.append({'signal':sig,'period':lab,'n':n,'freq_per_stock_y':round(n/nc/ny,2),
                    'alpha20':round(a20,4),'alpha60':round(a60,4),'win20':round(win,3),
                    't20':round(t,2),'p20':round(p,4)})
res=pd.DataFrame(out)
res.to_csv(f'{OUT}/signal_level_bt015.csv',index=False)
pd.set_option('display.float_format',lambda x:f'{x:.4f}')
for lab in ['2025','2026','all']:
    print(f"\n=== {lab} ===")
    m=res[res['period']==lab].sort_values('alpha60',ascending=False)
    print(m.to_string(index=False))
print('\n零信号(缓存口径):', ZERO_SIGS)
