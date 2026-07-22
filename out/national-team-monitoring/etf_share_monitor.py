"""
国家队 ETF 份额监控脚本
追踪四大沪深300ETF份额变化，判断国家队净买入/净卖出 regime

用法: python etf_share_monitor.py
数据源: AKShare fund_etf_spot_em (东方财富)
输出: 当前份额 + 30/60/90日变化 + regime判断
"""

import akshare as ak
import pandas as pd
from datetime import datetime, timedelta
import json

# 四大国家队核心 ETF
TARGET_ETFS = {
    "510300": "华泰柏瑞沪深300ETF",
    "510050": "华夏上证50ETF", 
    "510310": "易方达沪深300ETF",
    "159919": "嘉实沪深300ETF",
}

def fetch_etf_data():
    """获取 ETF 日线数据（含份额）"""
    all_data = {}
    
    for code, name in TARGET_ETFS.items():
        try:
            df = ak.fund_etf_hist_em(
                symbol=code,
                period="daily",
                start_date="20260101",
                end_date="20260722",
                adjust=""
            )
            if df is not None and len(df) > 0:
                df['代码'] = code
                df['名称'] = name
                df['日期'] = pd.to_datetime(df['日期'])
                all_data[code] = df
                print(f"  ✅ {code} {name}: {len(df)} 行")
            else:
                print(f"  ⚠️ {code} {name}: 无数据")
        except Exception as e:
            print(f"  ❌ {code} {name}: {e}")
    
    return all_data


def analyze_share_change(data_dict, windows=[30, 60, 90]):
    """分析份额变化"""
    results = []
    
    for code, df in data_dict.items():
        if df is None or len(df) < max(windows):
            continue
        
        df = df.sort_values('日期')
        latest = df.iloc[-1]
        latest_share = latest.get('基金份额', 0) or latest.get('份额', 0) or 0
        
        row = {
            '代码': code,
            '名称': TARGET_ETFS.get(code, ''),
            '最新份额(亿)': round(float(latest_share) / 100000000, 2) if latest_share > 1e8 else round(float(latest_share), 2),
            '最新日期': latest['日期'],
        }
        
        for w in windows:
            if len(df) > w:
                prev = df.iloc[-w]
                prev_share = prev.get('基金份额', 0) or prev.get('份额', 0) or 0
                change = (latest_share - prev_share) / prev_share * 100 if prev_share != 0 else 0
                row[f'{w}d变化(%)'] = round(float(change), 2)
        
        results.append(row)
    
    return pd.DataFrame(results)


def determine_regime(summary_df):
    """根据四大ETF综合变化判断 regime"""
    if summary_df.empty:
        return "❓ 数据不足"
    
    # 计算总变化方向
    total_30d = summary_df['30d变化(%)'].sum() if '30d变化(%)' in summary_df.columns else 0
    
    if total_30d > 2:
        return "🟢 净买入 (国家队可能在场) [2024年模式]"
    elif total_30d < -2:
        return "🔴 净卖出 (国家队在结构调整) [2026H1模式]"
    else:
        return "🟡 中性 (国家队未明显干预)"


def main():
    print("=" * 60)
    print("国家队 ETF 份额监控")
    print(f"运行时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 60)
    
    print("\n[1/2] 获取 ETF 数据...")
    etf_data = fetch_etf_data()
    
    print("\n[2/2] 分析份额变化...")
    summary = analyze_share_change(etf_data)
    
    if not summary.empty:
        print(f"\n{'='*60}")
        print("四大 ETF 份额变化汇总")
        print(f"{'='*60}")
        print(summary.to_string(index=False))
        
        regime = determine_regime(summary)
        print(f"\n{'='*60}")
        print(f"综合判断: {regime}")
        print(f"{'='*60}")
        
        # 保存结果
        summary.to_csv("etf_share_summary.csv", index=False)
        print("\n✅ 结果已保存到 etf_share_summary.csv")
    else:
        print("\n❌ 未能获取有效数据。AKShare 可能被限流，稍后重试。")


if __name__ == "__main__":
    main()
