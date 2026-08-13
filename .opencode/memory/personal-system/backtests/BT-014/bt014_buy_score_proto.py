#!/usr/bin/env python3
"""
BT-014 — BUY_LADDER 买入分原型回测 (绝对阈值 V_W 弱市分 / V_B 牛市分)

设计 (数据驱动, 基于 BT-013 事件研究):
  弱市买入分 score_w = Σ I(sig>0) for {alpha_zoo, technical_basic, candlestick, ad_line}
                        (2026 弱市全部显著正 α 的信号; 等权, 简单可解释)
  牛市买入分 score_b = 2·I(alpha_zoo>0) + I(technical_basic>0)
                        (2025 牛市仅 alpha_zoo 显著正 α; 双权)

事件研究 (同 BT-013 方法):
  触发日 (code,date) 且 score>=thr → 未来 20/60 交易日 log 收益 vs 当日同池截面基准
  α = 触发组均值 − 当日全池均值; 分 2025牛/2026弱; 阈值扫描 thr ∈ {1,2,3,4}

校验:
  1) 可达性: 触发数/年/池 — 不能锁死(如旧 0.65/0.42×max), 也不能过稀(无统计量)
  2) 有效性: α20/α60 显著正 + 高于单信号最优 (alpha_zoo 单独)
  3) 单调性: alpha60 > alpha20 (>0 表示效应延续)

用法: python3 bt014_buy_score_proto.py
输出: results/proto_bt014.csv
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

pool=json.load(open(POOL)); codes=[p['code'] for p in pool]
df=pd.read_parquet(CACHE); df['date']=pd.to_datetime(df['date']); df['year']=df['date'].dt.year

# ---- 未来收益表 (向量化) ----
rows=[]
for c in codes:
    g=glob.glob(f'{DAILY}/{c}*.csv')
    if not g: continue
    try:
        d=pd.read_csv(g[0]); d['date']=pd.to_datetime(d['date'])
        d=d.drop_duplicates('date').set_index('date')['close'].astype(float).sort_index()
        n=len(d)
        if n<60: continue
        s=np.log(d.to_numpy())
        r20=pd.Series(np.nan,index=d.index); r60=pd.Series(np.nan,index=d.index)
        r20.iloc[:-21]=s[21:]-s[:-21]; r60.iloc[:-61]=s[61:]-s[:-61]
        rows.append(pd.DataFrame({'r20':r20,'r60':r60,'code':c}).reset_index())
    except Exception: pass
ret=pd.concat(rows,ignore_index=True); ret['date']=pd.to_datetime(ret['date'])
b20=ret.groupby('date')['r20'].mean().rename('b20'); b60=ret.groupby('date')['r60'].mean().rename('b60')
ret=ret.merge(b20,left_on='date',right_index=True).merge(b60,left_on='date',right_index=True)
ret['alpha20']=ret['r20']-ret['b20']; ret['alpha60']=ret['r60']-ret['b60']
print(f"收益表: {ret.shape} | 覆盖 {ret['date'].min().date()}~{ret['date'].max().date()}")

# ---- 双分数 ----
S_W=['alpha_zoo','technical_basic','candlestick','ad_line']
df['score_w']=(df[S_W]>0).sum(axis=1)
df['score_b']=2*(df['alpha_zoo']>0).astype(int)+(df['technical_basic']>0).astype(int)

trig_ev = df[['code','date','year','score_w','score_b']].merge(
    ret[['code','date','alpha20','alpha60']], on=['code','date'], how='left')

rows=[]
for ylab,ym in [('all',None),('2025',2025),('2026',2026)]:
    sub=trig_ev if ym is None else trig_ev[trig_ev['year']==ym]
    tot=len(sub)
    for nm,scol in [('score_w', 'score_w'), ('score_b', 'score_b')]:
        for thr in [1,2,3,4]:
            t2=sub[sub[scol]>=thr].dropna(subset=['alpha20'])
            n=len(t2)
            if n < 5: continue
            a20=t2['alpha20'].mean(); a60=t2['alpha60'].dropna().mean()
            win=(t2['alpha20']>0).mean()
            tt,pp=stats.ttest_1samp(t2['alpha20'],0)
            rows.append({'score':nm,'period':ylab,'thr':thr,'n':n,
                         'n_per_stock_y':round(n/(sub['code'].nunique()* (1 if ym else 2)),2),
                         'alpha20':round(a20,4),'alpha60':round(a60,4),'win20':round(win,3),
                         't20':round(tt,2),'p20':round(pp,4)})
res=pd.DataFrame(rows)
res.to_csv(f'{OUT}/proto_bt014.csv',index=False)
pd.set_option('display.float_format',lambda x:f'{x:.4f}')
for lab in ['','2025','2026']:
    mask=res['period']==lab
    print(f"\n=== {lab or '全期'} ===")
    print(res[mask].sort_values(['score','thr']).to_string(index=False))
print(f"\n已存 {OUT}/proto_bt014.csv")
