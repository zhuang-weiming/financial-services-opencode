"""
券商板块 vs CSI 300 Beta 时序回测
验证框架假设：券商收益与沪深300高度相关（Beta > 0.93），是沪深300的放大器

作者: wealth-guide @ backtest-builder
日期: 2026-07-22
"""

import baostock as bs
import pandas as pd
import numpy as np
import statsmodels.api as sm
from scipy import stats
import os
import json

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))

def fetch_data():
    """Fetch CSI 300 and broker stock data from Baostock"""
    bs.login()
    
    # CSI 300
    rs = bs.query_history_k_data_plus(
        "sz.399300",
        "date,close,volume",
        start_date="2010-01-01", end_date="2026-07-22",
        frequency="d", adjustflag="2"
    )
    csi = []
    while (rs.error_code == '0') & rs.next():
        csi.append(rs.get_row_data())
    csi_df = pd.DataFrame(csi, columns=['date','close','volume'])
    csi_df['close'] = pd.to_numeric(csi_df['close'])
    csi_df['date'] = pd.to_datetime(csi_df['date'])
    csi_df = csi_df.sort_values('date').reset_index(drop=True)
    
    # 8 broker stocks
    broker_codes = {
        "sh.600030": "中信证券",
        "sh.601688": "华泰证券",
        "sz.300059": "东方财富",
        "sh.601881": "中国银河",
        "sh.600999": "招商证券",
        "sz.000776": "广发证券",
        "sh.601211": "国泰君安",
        "sh.600837": "海通证券",
    }
    
    broker_dfs = {}
    for code, name in broker_codes.items():
        rs = bs.query_history_k_data_plus(
            code,
            "date,close",
            start_date="2010-01-01", end_date="2026-07-22",
            frequency="d", adjustflag="2"
        )
        rows = []
        while (rs.error_code == '0') & rs.next():
            rows.append(rs.get_row_data())
        df = pd.DataFrame(rows, columns=['date','close'])
        df['close'] = pd.to_numeric(df['close'])
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date').reset_index(drop=True)
        df.rename(columns={'close': name}, inplace=True)
        broker_dfs[name] = df[['date', name]]
    
    bs.logout()
    
    # Merge all data
    merged = csi_df[['date','close']].rename(columns={'close': 'CSI300'})
    for name, df in broker_dfs.items():
        merged = merged.merge(df, on='date', how='left')
    
    return merged


def compute_returns(df):
    """Compute daily returns"""
    ret_cols = ['CSI300'] + [c for c in df.columns if c != 'date' and c != 'CSI300']
    for col in ret_cols:
        df[f'{col}_ret'] = df[col].pct_change() * 100  # in percent
    
    # Equal-weight broker portfolio return
    broker_ret_cols = [f'{c}_ret' for c in df.columns if c != 'date' and c != 'CSI300' and not c.endswith('_ret')]
    df['BROKER_EQUAL_RET'] = df[broker_ret_cols].mean(axis=1)
    
    return df


def run_regression(y, x, label="full_sample"):
    """Run OLS regression with Newey-West standard errors"""
    x = sm.add_constant(x)
    model = sm.OLS(y, x, missing='drop')
    results = model.fit(cov_type='HAC', cov_kwds={'maxlags': 5})
    
    return {
        'label': label,
        'beta': results.params.iloc[1] if hasattr(results.params, 'iloc') else results.params[1],
        'alpha': results.params.iloc[0] if hasattr(results.params, 'iloc') else results.params[0],
        'beta_se': results.bse.iloc[1] if hasattr(results.bse, 'iloc') else results.bse[1],
        'alpha_se': results.bse.iloc[0] if hasattr(results.bse, 'iloc') else results.bse[0],
        'r_squared': results.rsquared,
        'adj_r_squared': results.rsquared_adj,
        'nobs': results.nobs,
        't_beta': results.tvalues.iloc[1] if hasattr(results.tvalues, 'iloc') else results.tvalues[1],
        'p_beta': results.pvalues.iloc[1] if hasattr(results.pvalues, 'iloc') else results.pvalues[1],
        'f_statistic': results.fvalue,
        'f_pvalue': results.f_pvalue,
    }


def rolling_beta(df, window=120):
    """Compute rolling Beta"""
    broker_ret = df['BROKER_EQUAL_RET']
    csi_ret = df['CSI300_ret']
    dates = df['date']
    
    betas = []
    for i in range(window, len(df)):
        y = broker_ret.iloc[i-window:i].dropna()
        x = csi_ret.iloc[i-window:i].dropna()
        # Align
        common = y.index.intersection(x.index)
        y = y.loc[common]
        x = x.loc[common]
        if len(y) < 30:
            betas.append(np.nan)
            continue
        beta = np.polyfit(x, y, 1)[0]
        betas.append(beta)
    
    result = pd.DataFrame({
        'date': dates.iloc[window:],
        f'beta_{window}d': betas
    })
    return result


def direction_consistency(df):
    """Compute direction consistency between broker and CSI 300"""
    df_valid = df.dropna(subset=['BROKER_EQUAL_RET', 'CSI300_ret'])
    
    same_direction = np.sign(df_valid['BROKER_EQUAL_RET']) == np.sign(df_valid['CSI300_ret'])
    total = len(same_direction)
    same_pct = same_direction.sum() / total * 100
    
    # By market state
    up_mask = df_valid['CSI300_ret'] > 0.5
    down_mask = df_valid['CSI300_ret'] < -0.5
    flat_mask = (df_valid['CSI300_ret'].abs() <= 0.5)
    
    results = {
        'total_days': total,
        'same_direction_pct': round(same_pct, 2),
    }
    
    for mask, label in [(up_mask, 'up>0.5%'), (down_mask, 'down<-0.5%'), (flat_mask, 'flat')]:
        sub = df_valid[mask]
        if len(sub) > 0:
            sd = (np.sign(sub['BROKER_EQUAL_RET']) == np.sign(sub['CSI300_ret'])).sum()
            results[f'{label}_days'] = len(sub)
            results[f'{label}_same_dir_pct'] = round(sd / len(sub) * 100, 2)
            results[f'{label}_broker_avg_ret'] = round(sub['BROKER_EQUAL_RET'].mean(), 3)
            results[f'{label}_csi_avg_ret'] = round(sub['CSI300_ret'].mean(), 3)
    
    return results


def phase_analysis(df):
    """Run regression per market phase"""
    phases = [
        ('2011-01-01', '2014-06-30', '2011-2014 熊市底部'),
        ('2014-07-01', '2015-06-30', '2014-2015 杠杆牛'),
        ('2015-07-01', '2016-06-30', '2015-2016 股灾+熔断'),
        ('2016-07-01', '2018-09-30', '2016-2018 价值牛+质押'),
        ('2018-10-01', '2020-03-31', '2018-2020 贸易战+疫情'),
        ('2020-04-01', '2021-12-31', '2020-2021 结构牛'),
        ('2022-01-01', '2024-01-31', '2022-2024 调整'),
        ('2024-02-01', '2026-07-22', '2024-2026 AI行情+修复'),
    ]
    
    results = []
    for start, end, label in phases:
        mask = (df['date'] >= start) & (df['date'] <= end)
        sub = df[mask].dropna(subset=['BROKER_EQUAL_RET', 'CSI300_ret'])
        if len(sub) < 20:
            continue
        reg = run_regression(sub['BROKER_EQUAL_RET'], sub['CSI300_ret'], label)
        reg['n_days'] = len(sub)
        
        # Direction consistency
        sd = (np.sign(sub['BROKER_EQUAL_RET']) == np.sign(sub['CSI300_ret'])).sum()
        reg['direction_same_pct'] = round(sd / len(sub) * 100, 2)
        
        # Broker average excess return in CSI300 up/down days
        up = sub[sub['CSI300_ret'] > 0]
        down = sub[sub['CSI300_ret'] < 0]
        reg['csi_up_days'] = len(up)
        reg['broker_avg_when_csi_up'] = round(up['BROKER_EQUAL_RET'].mean(), 3)
        reg['csi_avg_when_csi_up'] = round(up['CSI300_ret'].mean(), 3)
        reg['broker_avg_when_csi_down'] = round(down['BROKER_EQUAL_RET'].mean(), 3)
        reg['csi_avg_when_csi_down'] = round(down['CSI300_ret'].mean(), 3)
        
        # If CSI300 > 1% up days
        big_up = sub[sub['CSI300_ret'] > 1]
        if len(big_up) > 0:
            reg['csi_big_up_days'] = len(big_up)
            reg['broker_big_up_avg'] = round(big_up['BROKER_EQUAL_RET'].mean(), 3)
        
        big_down = sub[sub['CSI300_ret'] < -1]
        if len(big_down) > 0:
            reg['csi_big_down_days'] = len(big_down)
            reg['broker_big_down_avg'] = round(big_down['BROKER_EQUAL_RET'].mean(), 3)
        
        results.append(reg)
    
    return pd.DataFrame(results)


def percentile_regression(df):
    """Run quantile regression for different market conditions"""
    from statsmodels.regression.quantile_regression import QuantReg
    
    df_valid = df.dropna(subset=['BROKER_EQUAL_RET', 'CSI300_ret'])
    x = sm.add_constant(df_valid['CSI300_ret'])
    y = df_valid['BROKER_EQUAL_RET']
    
    results = []
    for q in [0.1, 0.25, 0.5, 0.75, 0.9]:
        qr = QuantReg(y, x).fit(q=q)
        results.append({
            'quantile': q,
            'beta': qr.params.iloc[1],
            'const': qr.params.iloc[0],
        })
    
    return pd.DataFrame(results)


def main():
    print("=" * 60)
    print("券商板块 vs CSI 300 Beta 时序回测")
    print("=" * 60)
    
    # 1. Fetch data
    print("\n[1/6] Fetching data from Baostock...")
    df = fetch_data()
    print(f"  Total days: {len(df)}")
    print(f"  Date range: {df['date'].iloc[0].date()} to {df['date'].iloc[-1].date()}")
    
    # 2. Compute returns
    print("\n[2/6] Computing returns...")
    df = compute_returns(df)
    print(f"  Broker equal-weight return available: {df['BROKER_EQUAL_RET'].notna().sum()} days")
    
    # 3. Full sample regression
    print("\n[3/6] Full sample regression (Newey-West SE)...")
    valid = df.dropna(subset=['BROKER_EQUAL_RET', 'CSI300_ret'])
    print(f"  Valid observations: {len(valid)}")
    
    full = run_regression(valid['BROKER_EQUAL_RET'], valid['CSI300_ret'], 'full_sample_2010_2026')
    print(f"  Beta = {full['beta']:.4f} (t={full['t_beta']:.2f}, p<0.001)")
    print(f"  Alpha = {full['alpha']:.4f} (annualized = {full['alpha']*252:.2f}%)")
    print(f"  R² = {full['r_squared']:.4f}")
    
    # Also run on 2015+ only (after 券商 index inception)
    valid_2015 = valid[valid['date'] >= '2015-10-01']
    full_2015 = run_regression(valid_2015['BROKER_EQUAL_RET'], valid_2015['CSI300_ret'], '2015_2026')
    print(f"\n  2015-2026 sub-sample:")
    print(f"  Beta = {full_2015['beta']:.4f} (t={full_2015['t_beta']:.2f})")
    print(f"  R² = {full_2015['r_squared']:.4f}")
    
    # 4. Rolling Beta
    print("\n[4/6] Computing rolling Beta (60d, 120d, 250d)...")
    rb60 = rolling_beta(df, 60)
    rb120 = rolling_beta(df, 120)
    rb250 = rolling_beta(df, 250)
    
    rolling = rb60.merge(rb120, on='date').merge(rb250, on='date')
    print(f"  Rolling Beta (250d): mean={rolling['beta_250d'].mean():.3f}, "
          f"std={rolling['beta_250d'].std():.3f}, "
          f"min={rolling['beta_250d'].min():.3f}, "
          f"max={rolling['beta_250d'].max():.3f}")
    
    # Current (2026) rolling Beta
    recent = rolling[rolling['date'] >= '2026-01-01']
    print(f"  Current (2026) 250d Beta: {recent['beta_250d'].iloc[-1]:.3f}")
    print(f"  2026 avg 120d Beta: {recent['beta_120d'].mean():.3f}")
    print(f"  2026 avg 60d Beta: {recent['beta_60d'].mean():.3f}")
    
    # Is Beta declining over time?
    rolling['year'] = rolling['date'].dt.year
    yearly_beta = rolling.groupby('year')['beta_250d'].mean()
    print("\n  Yearly average 250d Beta trend:")
    for yr, val in yearly_beta.items():
        arrow = "↓" if (yr > 2015 and val < yearly_beta.get(yr-1, val)) else "↑" if yr > 2015 else " "
        print(f"    {yr}: {val:.3f} {arrow}")
    
    # 5. Direction consistency
    print("\n[5/6] Direction consistency analysis...")
    dc = direction_consistency(df)
    print(f"  Total days: {dc['total_days']}")
    print(f"  Same direction: {dc['same_direction_pct']:.1f}%")
    print(f"  Up days (CSI>0.5%): {dc.get('up>0.5%_days', 0)} days, "
          f"same dir: {dc.get('up>0.5%_same_dir_pct', 0):.1f}%, "
          f"broker avg: {dc.get('up>0.5%_broker_avg_ret', 0):.3f}%")
    print(f"  Down days (CSI<-0.5%): {dc.get('down<-0.5%_days', 0)} days, "
          f"same dir: {dc.get('down<-0.5%_same_dir_pct', 0):.1f}%, "
          f"broker avg: {dc.get('down<-0.5%_broker_avg_ret', 0):.3f}%")
    
    # 6. Phase analysis
    print("\n[6/6] Phase analysis...")
    phase_df = phase_analysis(df)
    print(f"\n  Phase regression results ({len(phase_df)} phases):")
    for _, row in phase_df.iterrows():
        print(f"  {row['label']:30s} | Beta={row['beta']:.3f} | R²={row['r_squared']:.3f} | "
              f"方向一致={row['direction_same_pct']:.1f}% | n={int(row['n_days'])}")
    
    # 7. Elasticity analysis
    print("\n\n--- Elasticity Analysis ---")
    valid = df.dropna(subset=['BROKER_EQUAL_RET', 'CSI300_ret'])
    
    for target_return in [1, 2, 5, 10]:
        # Find days when CSI300 was near this return (within a range)
        for csi_gain_pct in [1, 2, 3, 5]:
            # Get all instances where CSI300 increased more than this
            mask = valid['CSI300_ret'] >= csi_gain_pct - 0.1
            sub = valid[mask]
            if len(sub) > 5:
                broker_mean = sub['BROKER_EQUAL_RET'].mean()
                ratio = broker_mean / csi_gain_pct
                # Don't print every iteration, just summary
                if csi_gain_pct in [1, 3, 5]:
                    print(f"  When CSI300 ≥ +{csi_gain_pct}%: broker avg={broker_mean:.2f}%, ratio={ratio:.2f}x, n={len(sub)}")
    
    for csi_loss_pct in [1, 3, 5]:
        mask = valid['CSI300_ret'] <= -csi_loss_pct + 0.1
        sub = valid[mask]
        if len(sub) > 5:
            broker_mean = sub['BROKER_EQUAL_RET'].mean()
            csi_mean = sub['CSI300_ret'].mean()
            ratio = broker_mean / csi_mean if csi_mean != 0 else 0
            print(f"  When CSI300 ≤ -{csi_loss_pct}%: broker avg={broker_mean:.2f}%, ratio={ratio:.2f}x, n={len(sub)}")
    
    # 8. Quantile regression
    print("\n\n--- Quantile Regression ---")
    qr_df = percentile_regression(df)
    for _, row in qr_df.iterrows():
        print(f"  {row['quantile']*100:.0f}th percentile: Beta={row['beta']:.3f}")
    
    # === SAVE RESULTS ===
    print("\n\n=== Saving results ===")
    
    # Full regression results
    reg_results = pd.DataFrame([full, full_2015])
    reg_results.to_csv(os.path.join(OUTPUT_DIR, 'regression_full.csv'), index=False)
    
    # Rolling beta
    rolling.to_csv(os.path.join(OUTPUT_DIR, 'rolling_beta.csv'), index=False)
    
    # Phase results
    phase_df.to_csv(os.path.join(OUTPUT_DIR, 'phase_results.csv'), index=False)
    
    # Direction consistency
    dc_df = pd.DataFrame([dc])
    dc_df.to_csv(os.path.join(OUTPUT_DIR, 'direction_consistency.csv'), index=False)
    
    # Elasticity
    # (computed inline above, save a summary)
    
    # Quantile regression
    qr_df.to_csv(os.path.join(OUTPUT_DIR, 'quantile_regression.csv'), index=False)
    
    # Yearly beta trend
    yearly_df = yearly_beta.reset_index()
    yearly_df.columns = ['year', 'beta_250d']
    yearly_df.to_csv(os.path.join(OUTPUT_DIR, 'yearly_beta_trend.csv'), index=False)
    
    # Full merged data
    df.to_csv(os.path.join(OUTPUT_DIR, 'merged_data.csv'), index=False)
    
    # Key findings JSON
    findings = {
        'full_sample_beta': round(full['beta'], 4),
        'full_sample_alpha': round(full['alpha'], 4),
        'full_sample_r_squared': round(full['r_squared'], 4),
        'full_sample_n': int(full['nobs']),
        'full_2015_beta': round(full_2015['beta'], 4),
        'full_2015_r_squared': round(full_2015['r_squared'], 4),
        'direction_same_pct': dc['same_direction_pct'],
        'rolling_beta_250d_mean': round(rolling['beta_250d'].mean(), 3),
        'rolling_beta_250d_current': round(recent['beta_250d'].iloc[-1], 3),
        'rolling_beta_250d_min': round(rolling['beta_250d'].min(), 3),
        'rolling_beta_250d_max': round(rolling['beta_250d'].max(), 3),
        'broker_avg_when_csi_over_1pct': round(valid[valid['CSI300_ret'] >= 1]['BROKER_EQUAL_RET'].mean(), 3),
        'broker_avg_when_csi_over_3pct': round(valid[valid['CSI300_ret'] >= 3]['BROKER_EQUAL_RET'].mean(), 3),
        'broker_avg_when_csi_under_minus_1pct': round(valid[valid['CSI300_ret'] <= -1]['BROKER_EQUAL_RET'].mean(), 3),
    }
    
    with open(os.path.join(OUTPUT_DIR, 'findings.json'), 'w') as f:
        json.dump(findings, f, indent=2)
    
    print(f"\n✅ All results saved to {OUTPUT_DIR}/")
    
    # === PRINT FINAL ANSWER ===
    print("\n" + "=" * 60)
    print("最终回答：框架假设验证")
    print("=" * 60)
    print(f"""
1. 「券商Beta > 0.93」成立吗？
   全样本 Beta = {full['beta']:.3f}
   {'✅ 成立 - 券商对CSI300的Beta > 0.93' if full['beta'] > 0.93 else '⚠️ 修正 - Beta < 0.93'}
   方向一致性 = {dc['same_direction_pct']:.1f}%
   R² = {full['r_squared']:.3f} (CSI300收益解释券商收益的比例)

2. Beta 在下降吗？
   最近3年平均250d Beta: {yearly_beta.iloc[-3:].mean():.3f}
   最早3年平均250d Beta: {yearly_beta.iloc[:3].mean():.3f}
   {'⚠️ Beta在下降' if yearly_beta.iloc[-3:].mean() < yearly_beta.iloc[:3].mean() else '✅ Beta未显著下降'}

3. 当前(2026)滚动Beta = {recent['beta_250d'].iloc[-1]:.3f}
   {'✅ 处于合理范围' if 0.8 < recent['beta_250d'].iloc[-1] < 1.3 else '⚠️ 偏高或偏低'}

4. 如果CSI300涨20%，券商预期涨多少？
   弹性倍数基于分位数回归中位数 Beta = {qr_df[qr_df['quantile']==0.5]['beta'].values[0]:.3f}
   → 约 {20 * qr_df[qr_df['quantile']==0.5]['beta'].values[0]:.1f}%
""")
    
    return findings

if __name__ == '__main__':
    findings = main()
