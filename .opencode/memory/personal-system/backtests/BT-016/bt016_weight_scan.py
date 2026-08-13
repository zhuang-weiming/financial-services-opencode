#!/usr/bin/env python3
"""
BT-016 — 积分权重与绝对阈值扫描 (BUY_LADDER v3.1 数据驱动积分定案)

信号集 = 4 个 BT-015 验证正α信号 (technical_basic, alpha_zoo, candlestick, ad_line)
对比权重方案 × 绝对阈值扫描, 事件研究同 BT-014 (未来 20/60 日 vs 当日全池截面基准)

方案:
  W_A 等权 1/1/1/1           (BT-014 score_w 已验证基线)
  W_B 独立α驱动 2/2/1/1      (tech+alpha×2, candle+ad×1)
  W_C 双核 3/0/0/0           (只 top 信号 — 对照组, 证明多信号协同>单信号)

输出: 每方案 × 阈值 × 年期的 α20/α60/win/月触发/统计显著性
结论: 最优权重 + 最优绝对阈值 (观察/击球两档)
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

SIG_W = {'technical_basic':2,'alpha_zoo':2,'candlestick':1,'ad_line':1}
pool=json.load(open(POOL)); codes=[p['code'] for p in pool]
df=pd.read_parquet(CACHE); df['date']=pd.to_datetime(df['date']); df['year']=df['date'].dt.year

rows=[]
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

SIGS=list(SIG_W.keys())
def wsum(row,w): return sum(w[s]*(row[s]>0) for s in SIGS)
df['W_A']=[sum(r>0 for r in row) for _,row in df[SIGS].iterrows()]
df['W_B']=[wsum(row,SIG_W) for _,row in df[SIGS].iterrows()]
df['W_C']=(df['technical_basic']>0).astype(int)*3 + (df['alpha_zoo']>0)*0  # 仅 top 信号强度3
full=df[['code','date','year','W_A','W_B','W_C']].merge(ret[['code','date','alpha20','alpha60']],on=['code','date'],how='left')

out=[]
for wlab in ['W_A','W_B','W_C']:
    for lab,ym in [('2025',2025),('2026',2026),('all',None)]:
        sub=full if ym is None else full[full['year']==ym]
        nc=sub['code'].nunique(); ny=2 if lab=='all' else 1
        for thr in [1,2,3,4,5,6]:
            ev=sub[sub[wlab]>=thr].dropna(subset=['alpha20'])
            n=len(ev)
            if n<10: continue
            a20=ev['alpha20'].mean(); a60=ev['alpha60'].dropna().mean()
            win=(ev['alpha20']>0).mean(); t,p=stats.ttest_1samp(ev['alpha20'],0)
            out.append({'weight':wlab,'period':lab,'thr':thr,'n':n,
                        'per_stock_mo':round(n/nc/ny/12,2),
                        'alpha20':round(a20,4),'alpha60':round(a60,4),'win20':round(win,3),
                        't20':round(t,2),'p20':round(p,4)})
res=pd.DataFrame(out)
res.to_csv(f'{OUT}/weight_scan_bt016.csv',index=False)
print("=== BT-016 权重×阈值 扫描 ===")
for wlab in ['W_A','W_B','W_C']:
    print(f"\n--- {wlab}: {'1/1/1/1 等权' if wlab=='W_A' else '2/2/1/1 α驱动' if wlab=='W_B' else '3/0/0/0 单核对照'} ---")
    for lab in ['2026','2025','all']:
        m=res[(res['weight']==wlab)&(res['period']==lab)].sort_values('thr')
        if len(m):
            print(f"  {lab}: " + " | ".join(f"thr{t}h{a['n']:.0f}pt={a['alpha60']:+.2%}" for _,a in m.iterrows()))
# 落到最终推荐: 找到 2026+all 都显著且月触发 1-30 的最佳
print("\n=== 候选推荐 (2026 与所有年份 α60 均>0, 月触发 1~30) ===")
rec=res[(res['period']=='all')&(res['alpha60']>0)]
for _,a in rec.sort_values('alpha60',ascending=False).iterrows():
    y=res[(res['weight']==a['weight'])&(res['thr']==a['thr'])&(res['period']=='2026')]
    if len(y) and y.iloc[0]['alpha60']>0 and 1<=a['per_stock_mo']<=30:
        print(f"  {a['weight']} thr={a['thr']}: 全期α60={a['alpha60']:+.2%}(p={a['p20']}) 月{a['per_stock_mo']}次 | 2026α60={y.iloc[0]['alpha60']:+.2%} 2026月{y.iloc[0]['per_stock_mo']}次")
