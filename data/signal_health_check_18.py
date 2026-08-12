#!/usr/bin/env python3
"""16 信号 × 18 只持仓 独立信号质量体检"""
import sys
import json
import importlib.util
from pathlib import Path
from collections import defaultdict

ROOT = Path("/Users/weimingzhuang/Documents/source_code/financial-services-opencode")
sys.path.insert(0, str(ROOT / ".opencode/memory/personal-system/sell-ladder"))

spec_sl = importlib.util.spec_from_file_location(
    "sl", str(ROOT / ".opencode/memory/personal-system/sell-ladder/sell_ladder.py"))
sl = importlib.util.module_from_spec(spec_sl); spec_sl.loader.exec_module(sl)

# 16 信号函数字典 (与 sell_ladder 中 run_sell_ladder 完全一致)
SIGNAL_FUNCS = {
    'alpha_engine_v21': sl.calc_alpha_engine_v21,
    'candlestick': sl.calc_candlestick,
    'ml_strategy': sl.calc_ml_strategy,
    'chanlun': sl.calc_chanlun,
    'technical_basic': sl.calc_technical_basic,
    'ichimoku': sl.calc_ichimoku,
    'smc': sl.calc_smc,
    'alpha_zoo': sl.calc_alpha_zoo,
    'factor_research': sl.calc_factor_research,
    'multi_factor': sl.calc_multi_factor,
    'volatility': sl.calc_volatility,
    'harmonic': sl.calc_harmonic,
    'pair_trading': sl.calc_pair_trading,
    'turnover_anomaly': sl.calc_turnover_anomaly,
    'sector_relative': sl.calc_sector_relative,
    'ad_line': sl.calc_ad_line,
}

# 分类 (与 sell_ladder EVENT_SIGNALS / TREND_SIGNALS 一致)
EVENT_SIGNALS = {'candlestick', 'chanlun', 'turnover_anomaly', 'multi_factor'}
TREND_SIGNALS = {'alpha_engine_v21', 'technical_basic', 'ichimoku', 'smc',
                 'alpha_zoo', 'factor_research', 'ml_strategy', 'sector_relative',
                 'volatility', 'harmonic', 'pair_trading', 'ad_line'}

HOLDINGS = [
    ('601788', '光大证券'), ('600030', '中信证券'), ('601696', '中银证券'),
    ('601688', '华泰证券'), ('601995', '中金公司'), ('601990', '南京证券'),
    ('601901', '方正证券'), ('512000', '券商ETF'), ('600643', '爱建集团'),
    ('600050', '中国联通'), ('601633', '长城汽车'), ('601919', '中远海控'),
    ('002601', '龙佰集团'), ('300003', '乐普医疗'), ('300725', '药石科技'),
    ('600570', '恒生电子'), ('300142', '沃森生物'), ('601669', '中国电建'),
]


def evaluate_signal(sig_name, sig_func, df):
    """单只股票单信号完整评估"""
    try:
        s = sig_func(df)
        if not isinstance(s, dict):
            return {'error': f'非 dict 返回: {type(s).__name__}'}
        if not s.get('healthy', True):
            return {'error': s.get('error', 'not healthy')}

        sig = s.get('signal', 0)
        result = {
            'signal': sig,
            'healthy': True,
            'detail': {k: v for k, v in s.items() if k not in ['signal'] and isinstance(v, (str, int, float, bool))},
        }
        # 截取关键指标
        for k in ['wt1', 'wt2', 'zone', 'wt1_sweet', 'cur_wt1',
                  'adx', 'rsi', 'bb_pos', 'hv_annual', 'hv_pct',
                  'composite', 'f2_ic', 'verdict', 'ret_20d', 'pos_20d',
                  'ml_score', 'prob_up', 'above_cloud_pct', 'tk_bullish',
                  'score_20', 'n_transitions']:
            if k in s:
                result['detail'][k] = s[k]
        return result
    except Exception as e:
        return {'error': str(e)[:100]}


def main():
    print("="*80)
    print(f"🔬 16 信号 × 18 只持仓 独立信号质量体检 (8m 数据, 161 bars)")
    print("="*80)

    all_results = {}
    for ticker, name in HOLDINGS:
        try:
            df = sl.load_data(ticker)
            df_8m = df.iloc[-161:].reset_index(drop=True).copy()
        except Exception as e:
            print(f"⚠️ {ticker} {name} 加载失败: {e}")
            continue

        stock_results = {}
        for sig_name, sig_func in SIGNAL_FUNCS.items():
            stock_results[sig_name] = evaluate_signal(sig_name, sig_func, df_8m)
        all_results[ticker] = {'name': name, 'sigs': stock_results}

    # ============ 信号触发率汇总 ============
    print(f"\n{'信号':<22} {'类别':<8} {'健康':<8} {'触发率':<8} {'+1':<6} {'-1':<6} {'0':<6} {'平均分':<8}")
    print("-"*88)

    summary = {}
    for sig_name, sig_func in SIGNAL_FUNCS.items():
        trigger_count = 0
        healthy_count = 0
        plus_count = 0
        minus_count = 0
        zero_count = 0
        sig_sum = 0
        errors = []
        for ticker, info in all_results.items():
            r = info['sigs'][sig_name]
            if 'error' in r:
                errors.append(ticker)
                continue
            healthy_count += 1
            sig = r['signal']
            if sig != 0:
                trigger_count += 1
            if sig > 0:
                plus_count += 1
            elif sig < 0:
                minus_count += 1
            else:
                zero_count += 1
            sig_sum += sig

        n = len(all_results)
        trigger_rate = trigger_count / n if n else 0
        sig_avg = sig_sum / healthy_count if healthy_count else 0
        cat = '🟢事件' if sig_name in EVENT_SIGNALS else '🔵趋势'
        summary[sig_name] = {
            'cat': 'event' if sig_name in EVENT_SIGNALS else 'trend',
            'healthy': healthy_count,
            'trigger_rate': round(trigger_rate, 3),
            'plus': plus_count,
            'minus': minus_count,
            'zero': zero_count,
            'avg_signal': round(sig_avg, 3),
            'errors': errors,
        }

        print(f"{sig_name:<22} {cat:<8} {healthy_count:>2}/{n:<5} {trigger_rate:>6.1%}   {plus_count:>3}   {minus_count:>3}   {zero_count:>3}   {sig_avg:>+.3f}")

    # ============ 按信号排序：质量最重要 ============
    print("\n" + "="*80)
    print("📈 信号质量排名 (按触发率 × 平均分)")
    print("="*80)
    print(f"{'排名':<5} {'信号':<22} {'类别':<8} {'触发率':<8} {'均分':<8} {'+:-':<8} {'判断'}")
    print("-"*88)

    # 排序: 健康 > 触发率 > 平均分
    ranked = sorted(summary.items(),
                    key=lambda x: (-x[1]['healthy']/len(all_results), -x[1]['trigger_rate'], -x[1]['avg_signal']))
    for i, (sig_name, info) in enumerate(ranked, 1):
        ratio = f"{info['plus']}:{info['minus']}" if info['minus'] else f"{info['plus']}:0"
        cat = '🟢事件' if info['cat'] == 'event' else '🔵趋势'

        # 判定
        if info['healthy'] == 0:
            verdict = '❌ 全部失败'
        elif info['trigger_rate'] == 0:
            verdict = '🟡 0 触发 (无效)'
        elif info['trigger_rate'] < 0.1:
            verdict = '🟡 极少触发'
        elif info['avg_signal'] > 0:
            verdict = '✅ 正向贡献'
        elif info['avg_signal'] < 0:
            verdict = '🔴 负向贡献'
        else:
            verdict = '⚪ 中性'

        print(f"{i:<5} {sig_name:<22} {cat:<8} {info['trigger_rate']:>6.1%}   {info['avg_signal']:>+.3f}   {ratio:<8} {verdict}")

    # ============ 信号矩阵详细 (18 只 × 16 信号) ============
    print("\n" + "="*80)
    print("📊 18 只 × 16 信号 完整矩阵 (signal 值)")
    print("="*80)

    sig_names = list(SIGNAL_FUNCS.keys())
    print(f"{'股票':<14} " + " ".join(f"{s[:8]:<9}" for s in sig_names))
    print("-" * (14 + 10 * len(sig_names)))

    for ticker, info in all_results.items():
        row = f"{ticker} {info['name']:<8}"
        for sig_name in sig_names:
            r = info['sigs'][sig_name]
            if 'error' in r:
                row += f" {'ERR':<9}"
            else:
                sig = r['signal']
                marker = '🟢' if sig > 0 else ('🔴' if sig < 0 else '·')
                row += f" {marker}{sig:>+3d}    "
        print(row)

    # ============ 质量体检总结 ============
    print("\n" + "="*80)
    print("🎯 质量体检总结")
    print("="*80)

    zero_trigger = [s for s, info in summary.items() if info['trigger_rate'] == 0 and info['healthy'] > 0]
    low_trigger = [s for s, info in summary.items() if 0 < info['trigger_rate'] < 0.2]
    high_use = [s for s, info in summary.items() if info['trigger_rate'] >= 0.5]

    print(f"\n✅ 触发率 ≥ 50% 的信号 ({len(high_use)} 个):")
    for s in high_use:
        print(f"   {s:<22} 触发率 {summary[s]['trigger_rate']:.1%}  均分 {summary[s]['avg_signal']:+.3f}")

    print(f"\n🟡 触发率 0% 的信号 ({len(zero_trigger)} 个):")
    for s in zero_trigger:
        print(f"   {s:<22} 全部 0 触发")

    print(f"\n🟡 触发率低 (0-20%) 的信号 ({len(low_trigger)} 个):")
    for s in low_trigger:
        print(f"   {s:<22} 触发率 {summary[s]['trigger_rate']:.1%}")

    print(f"\n⚠️ 出错的信号 (部分股票 unhealthy):")
    for s, info in summary.items():
        if info['errors']:
            print(f"   {s:<22} {len(info['errors'])}/{len(all_results)} 只失败: {info['errors'][:5]}")

    # 保存
    out_path = ROOT / "out" / "signal_health_check_18holdings.json"
    out_path.write_text(json.dumps({
        'summary': summary,
        'all_results': all_results,
    }, ensure_ascii=False, indent=2, default=str))
    print(f"\n详细结果: {out_path}")


if __name__ == "__main__":
    main()
