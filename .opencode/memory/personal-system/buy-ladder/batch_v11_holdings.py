#!/usr/bin/env python3
"""
BUY_LADDER v3.1 — 18 持仓批量验证

执行: python3 batch_v11_holdings.py
判定链 (v3.1): ST 红牌 → 5 否决 → 积分绝对阈值 (score ≥4/6 击球 / ≥3/6 观察 / <3 禁入)
Layer 0/1 为咨询性，不再作为锁定依据 (结构性牛市无法可靠判定 regime)。
"""
import sys
import os
import json
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, '/Users/weimingzhuang/Documents/source_code/financial-services-opencode/.opencode/memory/personal-system/sell-ladder')
sys.path.insert(0, '/Users/weimingzhuang/Documents/source_code/financial-services-opencode/.opencode/memory/personal-system/buy-ladder')
import buy_ladder as bl

HOLDINGS = [
    ('601788', '光大证券'), ('600030', '中信证券'), ('601696', '中银证券'),
    ('601688', '华泰证券'), ('601995', '中金公司'), ('601990', '南京证券'),
    ('601901', '方正证券'), ('512000', '券商ETF'),
    ('600643', '爱建集团'), ('600050', '中国联通'),
    ('601633', '长城汽车'), ('601919', '中远海控'),
    ('002601', '龙佰集团'),
    ('300003', '乐普医疗'), ('300142', '沃森生物'), ('300725', '药石科技'),
    ('600570', '恒生电子'), ('601669', '中国电建'),
]


def main():
    today = datetime.now().date()
    print(f"🎯 BUY_LADDER v3.1 批量验证 — {today}")
    print(f"   持仓: {len(HOLDINGS)} 只")
    print(f"   判定: 积分 score/6 (≥4 击球 / ≥3 观察 / <3 禁入) + 否决 + ST 红牌")
    print("=" * 80)

    results = []
    n_hit, n_watch, n_forbid, n_error = 0, 0, 0, 0

    for code, name in HOLDINGS:
        t0 = time.time()
        try:
            r = bl.run_buy_ladder(ticker=code, cost=None, shares=None, held=False,
                                   force_regime_unlock=False)
            elapsed = time.time() - t0

            stage = r.get('stage', 4)
            stage_name = r.get('stage_name', '')
            score = r.get('score', r.get('score_buy', [0, 6])[0] if isinstance(r.get('score_buy'), list) else 0)
            layer0 = r.get('layer0', {}).get('unlocked', False)

            if stage == 1:
                n_hit += 1; icon = '🟢'
            elif stage == 2:
                n_watch += 1; icon = '🟡'
            else:
                n_forbid += 1; icon = '🔴'

            print(f"\n{icon} {code} {name}: 阶段{stage} ({stage_name[:36]}) | score={score}/6 | Layer0咨询={'解锁' if layer0 else '锁定'}(不阻断) | {elapsed:.1f}s")

            results.append({
                'code': code, 'name': name,
                'score': score,
                'stage': stage, 'stage_name': stage_name,
                'layer0_unlocked': layer0,
                'elapsed_sec': round(elapsed, 1),
            })
        except Exception as e:
            n_error += 1
            print(f"\n❌ {code} {name}: {type(e).__name__}: {e}")
            results.append({'code': code, 'name': name, 'error': str(e)})

    print("\n" + "=" * 80)
    print("📊 批量验证汇总 (v3.1)")
    print("=" * 80)
    print(f"总持仓: {len(HOLDINGS)}")
    print(f"击球区 (score≥4): {n_hit}")
    print(f"观察区 (score≥3): {n_watch}")
    print(f"禁入区 (score<3/否决/ST): {n_forbid}")
    print(f"错误: {n_error}")

    out_dir = Path('/Users/weimingzhuang/Documents/source_code/financial-services-opencode/.opencode/memory/personal-system/buy-ladder/runs') / str(today)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f'v11_holdings_{today}.json'
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump({
            'date': str(today),
            'variant': 'v3.1',
            'total_holdings': len(HOLDINGS),
            'n_hit': n_hit, 'n_watch': n_watch, 'n_forbid': n_forbid, 'n_error': n_error,
            'results': results,
        }, f, ensure_ascii=False, indent=2)
    print(f"\n✅ 结果已保存: {out_path}")


if __name__ == "__main__":
    main()