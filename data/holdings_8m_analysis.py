#!/usr/bin/env python3
"""18 只持仓 sell_ladder + buy_ladder 自动分析 - 不删除任何信号"""
import sys
import json
import time
import io
import re
from contextlib import redirect_stdout
from pathlib import Path

ROOT = Path("/Users/weimingzhuang/Documents/source_code/financial-services-opencode")
sys.path.insert(0, str(ROOT / ".opencode/memory/personal-system/sell-ladder"))
sys.path.insert(0, str(ROOT / ".opencode/memory/personal-system/buy-ladder"))

import importlib.util
import pandas as pd

# 加载 sell_ladder
spec_sl = importlib.util.spec_from_file_location(
    "sl", str(ROOT / ".opencode/memory/personal-system/sell-ladder/sell_ladder.py"))
sl = importlib.util.module_from_spec(spec_sl); spec_sl.loader.exec_module(sl)

# 加载 buy_ladder
spec_bl = importlib.util.spec_from_file_location(
    "bl", str(ROOT / ".opencode/memory/personal-system/buy-ladder/buy_ladder.py"))
bl = importlib.util.module_from_spec(spec_bl); spec_bl.loader.exec_module(bl)

HOLDINGS = [
    ('601788', '光大证券'),
    ('600030', '中信证券'),
    ('601696', '中银证券'),
    ('601688', '华泰证券'),
    ('601995', '中金公司'),
    ('601990', '南京证券'),
    ('601901', '方正证券'),
    ('512000', '券商ETF'),
    ('600643', '爱建集团'),
    ('600050', '中国联通'),
    ('601633', '长城汽车'),
    ('601919', '中远海控'),
    ('002601', '龙佰集团'),
    ('300003', '乐普医疗'),
    ('300725', '药石科技'),
    ('600570', '恒生电子'),
    ('300142', '沃森生物'),
    ('601669', '中国电建'),
]

# 加载最近 8 个月数据并截取
def load_8m(ticker):
    df = sl.load_data(ticker).copy()
    # 确保 date 列为 datetime
    df['date'] = pd.to_datetime(df['date'])
    last_date = df['date'].iloc[-1]
    cutoff = last_date - pd.DateOffset(months=8)
    df_8m = df[df['date'] >= cutoff].reset_index(drop=True)
    # 确保至少 120 bars
    if len(df_8m) < 120:
        df_8m = df.iloc[-160:].reset_index(drop=True)
    return df, df_8m


def parse_signal_from_output(out_text):
    """从 sell_ladder 输出中提取每个信号的 +-"""
    sigs = {}
    for line in out_text.split('\n'):
        # 形如 "  alpha_engine_v21       🟢 +1     WT1=..."  或 "  smc                  ❌ 错误:..."
        m = re.match(r'^\s+(\w+)\s+(🟢|🔴|⚪|❌)\s+([+\-0-9N/A]+)\s*(.*)', line)
        if m:
            sig_name = m.group(1)
            emoji = m.group(2)
            sig_val = m.group(3)
            detail = m.group(4)
            if sig_name in ['alpha_engine_v21', 'candlestick', 'ml_strategy', 'chanlun',
                            'technical_basic', 'ichimoku', 'smc', 'alpha_zoo',
                            'factor_research', 'multi_factor', 'volatility', 'harmonic',
                            'pair_trading', 'turnover_anomaly', 'sector_relative', 'ad_line']:
                sigs[sig_name] = {'emoji': emoji, 'signal': sig_val, 'detail': detail[:80]}
    return sigs


def parse_stage_from_output(out_text):
    """从 sell_ladder 输出提取阶段和动作"""
    stage = None
    action = None
    end_count = None
    strong_healthy = None
    for line in out_text.split('\n'):
        m = re.match(r'.*?\[4\] 5 强动能信号健康数: (\d+)/5', line)
        if m:
            strong_healthy = int(m.group(1))
        m = re.match(r'.*?5 动能结束标志触发: (\d+)/5', line)
        if m:
            end_count = int(m.group(1))
        m = re.match(r'^\s+(阶段 [\d.]+: .*)$', line)
        if m:
            stage = m.group(1).strip()
        if '建议:' in line:
            action = line.split('建议:')[1].strip()
    return stage, action, end_count, strong_healthy


def run_one(ticker, name):
    """跑一只股票 - sell_ladder + buy_ladder"""
    print(f"\n{'='*72}")
    print(f"分析 {ticker} {name} - {time.strftime('%H:%M:%S')}")
    print(f"{'='*72}")

    # 加载 8 个月数据
    df_full, df_8m = load_8m(ticker)
    last_close = float(df_8m['close'].iloc[-1])
    start_close = float(df_8m['close'].iloc[0])
    ret_8m = last_close / start_close - 1
    print(f"  8m 数据: {len(df_8m)} bars ({df_8m.iloc[0]['date'].date()} → {df_8m.iloc[-1]['date'].date()})")
    print(f"  起末: {start_close:.2f} → {last_close:.2f}  涨跌: {ret_8m*100:+.2f}%")

    # ------- sell_ladder -------
    sell_out = io.StringIO()
    with redirect_stdout(sell_out):
        try:
            sell_result = sl.run_sell_ladder(ticker, no_cdmo=True, w_event=2, w_trend=1)
        except Exception as e:
            sell_result = {'error': str(e)}
    sell_text = sell_out.getvalue()
    sell_sigs = parse_signal_from_output(sell_text)
    sell_stage, sell_action, end_count, strong_healthy = parse_stage_from_output(sell_text)

    # ------- buy_ladder (force unlock) -------
    buy_out = io.StringIO()
    with redirect_stdout(buy_out):
        try:
            buy_result = bl.run_buy_ladder(ticker, no_cdmo=True, force_regime_unlock=True)
        except Exception as e:
            buy_result = {'error': str(e)}
    buy_text = buy_out.getvalue()
    buy_sigs = parse_signal_from_output(buy_text)

    # 提取 buy_ladder 关键信息
    buy_score = buy_result.get('score', 'N/A')
    buy_max = buy_result.get('max_score', 'N/A')
    buy_stage = buy_result.get('stage', 'N/A')
    buy_stage_name = buy_result.get('stage_name', 'N/A')
    buy_action = buy_result.get('action', 'N/A')
    n_veto = buy_result.get('veto_result', {}).get('n_veto', 'N/A')
    n_confirm = buy_result.get('n_confirm', 'N/A')
    layer1_pass = buy_result.get('layer1', {}).get('n_pass', 'N/A')

    return {
        'ticker': ticker,
        'name': name,
        'last_close': last_close,
        'start_close_8m': start_close,
        'ret_8m_pct': round(ret_8m * 100, 2),
        'n_bars_8m': len(df_8m),
        'sell': {
            'stage': sell_stage,
            'action': sell_action,
            'end_count': end_count,
            'strong_healthy': strong_healthy,
            'signals': sell_sigs,
        },
        'buy': {
            'score': buy_score,
            'max_score': buy_max,
            'stage': buy_stage,
            'stage_name': buy_stage_name,
            'action': buy_action,
            'n_veto': n_veto,
            'n_confirm': n_confirm,
            'layer1_pass': layer1_pass,
        }
    }


def main():
    results = []
    for ticker, name in HOLDINGS:
        try:
            r = run_one(ticker, name)
            results.append(r)
        except Exception as e:
            print(f"  ⚠️ {ticker} 失败: {e}")
            results.append({'ticker': ticker, 'name': name, 'error': str(e)})

    # 保存
    out_path = ROOT / "out" / "holdings_8m_analysis.json"
    out_path.write_text(json.dumps(results, ensure_ascii=False, indent=2, default=str))
    print(f"\n\n结果保存: {out_path}")

    # ============ 汇总输出 ============
    print(f"\n{'='*72}")
    print(f"📊 18 只持仓 8 个月走势 + sell/buy ladder 汇总")
    print(f"{'='*72}")
    print(f"{'代码':<8} {'名称':<8} {'8m涨跌':<8} {'sell阶段':<24} {'buy得分':<10} {'buy阶段':<12} {'综合建议'}")
    print("-" * 130)

    for r in results:
        if 'error' in r:
            print(f"{r['ticker']:<8} {r['name']:<8} {'ERR':<8} {r.get('error', '')[:60]}")
            continue

        ret = r['ret_8m_pct']
        ret_str = f"{ret:+.2f}%"

        sell_stage = r['sell']['stage'] or 'N/A'
        sell_action = r['sell']['action'] or 'N/A'
        buy_score = f"{r['buy']['score']}/{r['buy']['max_score']}" if r['buy']['score'] != 'N/A' else 'N/A'
        buy_stage = f"{r['buy']['stage']}:{r['buy']['stage_name']}"[:20]

        # 综合：sell 偏空 + buy 偏空 = 减持
        sell_bear = sell_action and ('🔴' in sell_action or '减' in sell_action)
        buy_bear = r['buy']['score'] != 'N/A' and isinstance(r['buy']['score'], (int, float)) and r['buy']['score'] < 0
        if sell_bear and buy_bear:
            verdict = '🔴 强烈减持/清仓'
        elif sell_bear or buy_bear:
            verdict = '🟡 观望/减仓'
        elif r['sell']['action'] and '🟢' in r['sell']['action']:
            verdict = '🟢 持有'
        else:
            verdict = '⚪ 中性'

        print(f"{r['ticker']:<8} {r['name']:<8} {ret_str:<8} {sell_stage[:24]:<24} {buy_score:<10} {buy_stage:<12} {verdict}")


if __name__ == "__main__":
    main()
