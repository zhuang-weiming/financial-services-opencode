#!/usr/bin/env python3
"""
v2.5 持仓批量分析 — 18 只持仓的 SELL_LADDER 判定
执行: python3 batch_v25_holdings.py
输出: runs/<date>/v25_holdings_summary.json + stdout
"""
import sys
import os
import json
import time
from io import StringIO
import contextlib
from pathlib import Path
from datetime import datetime

sys.path.insert(0, '/Users/weimingzhuang/Documents/source_code/financial-services-opencode/.opencode/memory/personal-system/sell-ladder')
import sell_ladder as sl

# 用户持仓 (v2.5 完整列表)
HOLDINGS = [
    # 券商 7 只
    ('601788', '光大证券', '601990,601901,601696,512000'),
    ('600030', '中信证券', '601995,601688,601788,512000'),
    ('601696', '中银证券', '600030,601688,601995,601788'),
    ('601688', '华泰证券', '601995,601788,600030,512000'),
    ('601995', '中金公司', '601688,601788,600030,512000'),
    ('601990', '南京证券', '601788,601901,600030,512000'),
    ('601901', '方正证券', '601788,600030,601688,512000'),
    # 券商 ETF
    ('512000', '券商ETF', '600030,601688,601995,601788'),
    # 多元金融
    ('600643', '爱建集团', '600030,601688,601995'),
    # 通信
    ('600050', '中国联通', '600941,601728'),
    # 汽车
    ('601633', '长城汽车', '002594,601238,600104'),
    # 航运
    ('601919', '中远海控', '601872,600026'),
    # 化工/钛白粉
    ('002601', '龙佰集团', '002145,002978,600219'),
    # 医药
    ('300003', '乐普医疗', '002382,688108'),
    ('300142', '沃森生物', '300122,300601'),
    ('300725', '药石科技', '002821,603259,300759,300363'),
    # 软件
    ('600570', '恒生电子', '600446,603383,600588'),
    # 建筑
    ('601669', '中国电建', '601800,601618,601390'),
]

# 板块 ETF 映射 (复用 SECTOR_ETF_MAP_LOCAL 但添加券商/医药/通信等)
SECTOR_FOR_HOLDING = {
    '601788': '512000', '600030': '512000', '601696': '512000',
    '601688': '512000', '601995': '512000', '601990': '512000',
    '601901': '512000', '512000': '512000',  # 券商类 → 券商 ETF
    '600643': '512000',  # 爱建集团 → 券商/金融 ETF
    '600050': '159915',  # 中国联通 → 信息ETF
    '601633': '515030',  # 长城汽车 → 新能源车
    '601919': '513180',  # 中远海控 → 航运ETF
    '002601': '512010',  # 龙佰集团 → 化工/医药
    '300003': '512010',  # 乐普医疗 → 医药ETF
    '300142': '512010',  # 沃森生物 → 医药ETF
    '300725': '512010',  # 药石科技 → 医药ETF
    '600570': '512760',  # 恒生电子 → 软件ETF
    '601669': '512800',  # 中国电建 → 金融代理
}


def run_one(code, peers):
    """跑一次 sell-ladder v2.5, 返回 (stage, stage_name, score, max_score, end_count,
    event_pos, event_neg, trend_pos, signals_summary)"""
    peer_codes = [p.strip() for p in peers.split(',') if p.strip()]
    try:
        df = sl.load_data(code)
        last_close = float(df.iloc[-1]['close'])
        last_date = df.iloc[-1]['date'].date() if hasattr(df.iloc[-1]['date'], 'date') else str(df.iloc[-1]['date'])

        # 加载板块 ETF (新增 sector_relative 需要)
        sector_code = SECTOR_FOR_HOLDING.get(code)
        sector_df = pd.DataFrame() if not sector_code else sl.load_data(sector_code)

        # 计算各信号
        sector_d = sector_df if not sector_df.empty else None
        signals = {
            'alpha_engine_v21': sl.calc_alpha_engine_v21(df, code),
            'candlestick': sl.calc_candlestick(df),
            'ml_strategy': sl.calc_ml_strategy(df),
            'chanlun': sl.calc_chanlun(df, code),
            'technical_basic': sl.calc_technical_basic(df),
            'ichimoku': sl.calc_ichimoku(df),
            'smc': sl.calc_smc(df),
            'alpha_zoo': sl.calc_alpha_zoo(df),
            'factor_research': sl.calc_factor_research(df, None),
            'multi_factor': sl.calc_multi_factor(df, None),
            'volatility': sl.calc_volatility(df),
            'harmonic': sl.calc_harmonic(df),
            'pair_trading': sl.calc_pair_trading(df, {}, code),
            'turnover_anomaly': sl.calc_turnover_anomaly(df),
            'sector_relative': sl.calc_sector_relative(df, sector_d),
            'ad_line': sl.calc_ad_line(df),
        }

        # 计算得分和阶段
        score, mscore, ev_pos, ev_neg, tr_pos = sl.score_v22(signals, w_event=2, w_trend=1)

        # 动能结束标志 (在 stage 判定之前)
        end_signals = sl.check_momentum_end_signals(signals, df)
        end_count = sum(1 for v in end_signals.values() if v)

        # 阶段判定 (含 2.5 兜底)
        stage, stage_name = sl.stage_v22(score, mscore, end_count)

        return {
            'code': code,
            'last_close': last_close,
            'last_date': str(last_date),
            'sector_etf': sector_code,
            'stage': stage,
            'stage_name': stage_name,
            'score': score,
            'max_score': mscore,
            'event_pos': ev_pos,
            'event_neg': ev_neg,
            'trend_pos': tr_pos,
            'end_count': end_count,
            'end_signals': [k for k, v in end_signals.items() if v],
            'signals_fired': {k: v.get('signal', 0) for k, v in signals.items()},
        }
    except Exception as e:
        return {'code': code, 'error': f"{type(e).__name__}: {e}"}


import pandas as pd

def main():
    today = datetime.now().date()
    print(f"🔬 SELL_LADDER v2.5 持仓批量分析 — {today}")
    print(f"   持仓: {len(HOLDINGS)} 只")
    print(f"   框架: max=14, Stage1阈值=9.1, Stage2阈值=5.88")
    print("=" * 80)

    results = []
    for code, name, peers in HOLDINGS:
        t0 = time.time()
        r = run_one(code, peers)
        elapsed = time.time() - t0

        if 'error' in r:
            print(f"\n❌ {code} {name}: {r['error']} ({elapsed:.1f}s)")
            results.append({'code': code, 'name': name, 'error': r['error']})
            continue

        # 提取关键信息
        stage = r['stage']
        stage_name = r['stage_name']
        score = r['score']
        max_score = r['max_score']
        ep = r['event_pos']
        en = r['event_neg']
        tp = r['trend_pos']
        ec = r['end_count']

        # 阶段图标
        icon = {1: '🟢', 2: '🟡', 2.5: '🟠', 3: '🔴'}.get(stage, '⚪')

        # 建议
        advice = {
            1: '持有 100%',
            2: '减仓 30%',
            2.5: '减仓 40% 观察',
            3: '大幅减仓 80%'
        }.get(stage, 'N/A')

        # 信号汇总 (只列出非 0 的)
        signals_summary = []
        for k, v in r['signals_fired'].items():
            if v != 0:
                sig_icon = '🟢' if v > 0 else '🔴'
                signals_summary.append(f"{sig_icon}{k}={v:+d}")

        sig_str = ' '.join(signals_summary[:6]) if signals_summary else '⚪ 无信号触发'
        if len(signals_summary) > 6:
            sig_str += f" ... +{len(signals_summary)-6} more"

        print(f"\n{icon} {code} {name}")
        print(f"   最新价: {r['last_close']:.2f} ({r['last_date']})")
        print(f"   阶段 {stage} ({stage_name}): score={score}/{max_score} ({score/max_score*100:.0f}%)")
        print(f"   信号分布: ev={ep}+/{en}- | tr={tp}+ | end_count={ec} {r['end_signals']}")
        print(f"   建议: {advice}")
        print(f"   板块 ETF: {r['sector_etf'] or '无'}")
        print(f"   信号: {sig_str}")

        results.append({
            'code': code, 'name': name,
            'last_close': r['last_close'], 'last_date': r['last_date'],
            'sector_etf': r['sector_etf'],
            'stage': stage, 'stage_name': stage_name, 'advice': advice,
            'score': score, 'max_score': max_score, 'score_pct': round(score/max_score*100, 1),
            'event_pos': ep, 'event_neg': en, 'trend_pos': tp, 'end_count': ec,
            'end_signals': r['end_signals'],
            'signals_fired': r['signals_fired'],
            'elapsed_sec': round(elapsed, 1),
        })

    # 汇总表
    print("\n" + "=" * 80)
    print("📊 18 只持仓汇总 (按 stage 排序)")
    print("=" * 80)
    valid = [r for r in results if 'error' not in r]
    valid.sort(key=lambda x: x['stage'])

    print(f"{'code':<8} {'name':<8} {'stage':<6} {'score':<10} {'ep':<3} {'tp':<3} {'ec':<3} {'建议':<14} {'价格':<8}")
    for r in valid:
        print(f"{r['code']:<8} {r['name']:<8} {r['stage']:<6} {r['score']:>2}/{r['max_score']:<3} ({r['score_pct']:>4.0f}%) {r['event_pos']:<3} {r['trend_pos']:<3} {r['end_count']:<3} {r['advice']:<14} {r['last_close']:>7.2f}")

    # 阶段分布
    print()
    print("阶段分布:")
    for s in [1, 2, 2.5, 3]:
        cnt = sum(1 for r in valid if r['stage'] == s)
        names = ', '.join([f"{r['code']}" for r in valid if r['stage'] == s])
        print(f"  Stage {s}: {cnt} 只 ({names or '无'})")

    # 保存 JSON
    out_dir = Path('/Users/weimingzhuang/Documents/source_code/financial-services-opencode/.opencode/memory/personal-system/sell-ladder/runs') / str(today)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f'v25_holdings_{today}.json'
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump({
            'date': str(today),
            'variant': 'v2.5',
            'holdings': HOLDINGS,
            'results': results,
        }, f, ensure_ascii=False, indent=2)
    print(f"\n✅ 结果保存: {out_path}")


if __name__ == "__main__":
    main()