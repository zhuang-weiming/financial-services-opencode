#!/usr/bin/env python3
"""
BUY_LADDER v3.0 — 18 持仓批量验证

执行: python3 batch_v11_holdings.py
预期: 当前 regime 下, 全部 18 持仓 = 全部进入 "禁入区-Layer0锁定"

Layer 0 锁定 (国家队净卖出 + MCI Q3) → buy-ladder 默认关闭
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
    print(f"🎯 BUY_LADDER v3.0 批量验证 — {today}")
    print(f"   持仓: {len(HOLDINGS)} 只")
    print(f"   预期: 全部进入 '禁入区-Layer0锁定' (当前 regime 不支持买入)")
    print("=" * 80)

    results = []
    n_locked = 0
    n_unlocked = 0
    n_error = 0

    for code, name in HOLDINGS:
        t0 = time.time()
        try:
            r = bl.run_buy_ladder(ticker=code, cost=None, shares=None, held=False,
                                   force_regime_unlock=False)
            elapsed = time.time() - t0

            layer0_locked = not r.get('layer0', {}).get('unlocked', False)
            stage = r.get('stage', 4)
            stage_name = r.get('stage_name', '')

            if layer0_locked:
                n_locked += 1
                icon = '🔒'
            else:
                n_unlocked += 1
                icon = {1: '🟢', 2: '🟡', 4: '🔴'}.get(stage, '⚪')

            print(f"\n{icon} {code} {name}: 阶段{stage} ({stage_name[:30]}) ({elapsed:.1f}s)")

            results.append({
                'code': code, 'name': name,
                'layer0_unlocked': r.get('layer0', {}).get('unlocked', False),
                'stage': stage, 'stage_name': stage_name,
                'elapsed_sec': round(elapsed, 1),
            })
        except Exception as e:
            n_error += 1
            print(f"\n❌ {code} {name}: {type(e).__name__}: {e}")
            results.append({'code': code, 'name': name, 'error': str(e)})

    print("\n" + "=" * 80)
    print("📊 批量验证汇总")
    print("=" * 80)
    print(f"总持仓: {len(HOLDINGS)}")
    print(f"Layer 0 锁定 (预期): {n_locked}/{len(HOLDINGS)}")
    print(f"Layer 0 解锁 (意外): {n_unlocked}/{len(HOLDINGS)}")
    print(f"错误: {n_error}/{len(HOLDINGS)}")

    if n_locked == len(HOLDINGS) - n_error:
        print("\n✅ 验证通过 — 所有可运行持仓都正确进入 '禁入区-Layer0锁定'")
        print("   Layer 0 闸门工作正常, 当前 regime 不支持 buy 操作")
    elif n_unlocked > 0:
        print("\n⚠️ 意外解锁 — 需检查 Layer 0 数据/阈值")
        for r in results:
            if r.get('layer0_unlocked'):
                print(f"   {r['code']} {r['name']}: 阶段{r['stage']} ({r['stage_name']})")

    out_dir = Path('/Users/weimingzhuang/Documents/source_code/financial-services-opencode/.opencode/memory/personal-system/buy-ladder/runs') / str(today)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f'v11_holdings_{today}.json'
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump({
            'date': str(today),
            'variant': 'v3.0',
            'total_holdings': len(HOLDINGS),
            'n_locked': n_locked,
            'n_unlocked': n_unlocked,
            'n_error': n_error,
            'results': results,
        }, f, ensure_ascii=False, indent=2)
    print(f"\n✅ 结果已保存: {out_path}")


if __name__ == "__main__":
    main()