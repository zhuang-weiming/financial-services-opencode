#!/usr/bin/env python3
"""
COMBO_LAYER — buy + sell 联合调度 (Phase 5 原型)

输入: 用户持仓列表 (ticker + cost + shares)
输出: 每个标的的 (buy_action, sell_action, source_priority)

6 种组合全部有明确动作（详见 8.BUY_LADDER.md §六）

用法:
  python3 combo_layer.py
  python3 combo_layer.py --ticker 300725 --cost 36.62 --shares 10000
"""
import sys
import json
from datetime import datetime
from pathlib import Path

sys.path.insert(0, '/Users/weimingzhuang/Documents/source_code/financial-services-opencode/.opencode/memory/personal-system/sell-ladder')
sys.path.insert(0, '/Users/weimingzhuang/Documents/source_code/financial-services-opencode/.opencode/memory/personal-system/buy-ladder')
import sell_ladder as sl
import buy_ladder as bl


DEFAULT_HOLDINGS = [
    {'code': '601788', 'name': '光大证券', 'cost': 14.80, 'shares': 10000},
    {'code': '600030', 'name': '中信证券', 'cost': 28.43, 'shares': 5000},
    {'code': '601696', 'name': '中银证券', 'cost': 11.83, 'shares': 8000},
    {'code': '601688', 'name': '华泰证券', 'cost': 19.62, 'shares': 6000},
    {'code': '601995', 'name': '中金公司', 'cost': 35.32, 'shares': 4000},
    {'code': '601990', 'name': '南京证券', 'cost': 6.84, 'shares': 15000},
    {'code': '601901', 'name': '方正证券', 'cost': 7.10, 'shares': 12000},
    {'code': '512000', 'name': '券商ETF', 'cost': 0.529, 'shares': 100000},
    {'code': '600643', 'name': '爱建集团', 'cost': 4.11, 'shares': 20000},
    {'code': '600050', 'name': '中国联通', 'cost': 4.46, 'shares': 15000},
    {'code': '601633', 'name': '长城汽车', 'cost': 16.81, 'shares': 5000},
    {'code': '601919', 'name': '中远海控', 'cost': 15.63, 'shares': 6000},
    {'code': '002601', 'name': '龙佰集团', 'cost': 16.38, 'shares': 8000},
    {'code': '300003', 'name': '乐普医疗', 'cost': 13.07, 'shares': 8000},
    {'code': '300142', 'name': '沃森生物', 'cost': 30.00, 'shares': 3000},
    {'code': '300725', 'name': '药石科技', 'cost': 36.62, 'shares': 10000},
    {'code': '600570', 'name': '恒生电子', 'cost': 22.92, 'shares': 6000},
    {'code': '601669', 'name': '中国电建', 'cost': 5.00, 'shares': 20000},
]

STAGE_POSITION = {
    1: 1.00,
    2: 0.70,
    2.5: 0.60,
    3: 0.20,
}


def _quick_sell(ticker):
    """快速跑 sell-ladder, 返回 (stage, score, end_count)"""
    try:
        df = sl.load_data(ticker)
        sector_code = bl.SECTOR_FOR_HOLDING.get(ticker)
        sector_df = sl.load_data(sector_code) if sector_code else pd.DataFrame()

        signals = {
            'alpha_engine_v21': sl.calc_alpha_engine_v21(df, ticker),
            'candlestick': sl.calc_candlestick(df),
            'ml_strategy': sl.calc_ml_strategy(df),
            'chanlun': sl.calc_chanlun(df, ticker),
            'technical_basic': sl.calc_technical_basic(df),
            'ichimoku': sl.calc_ichimoku(df),
            'smc': sl.calc_smc(df),
            'alpha_zoo': sl.calc_alpha_zoo(df),
            'factor_research': sl.calc_factor_research(df, None),
            'multi_factor': sl.calc_multi_factor(df, None),
            'volatility': sl.calc_volatility(df),
            'harmonic': sl.calc_harmonic(df),
            'pair_trading': sl.calc_pair_trading(df, {}, ticker),  # v3.0 removed (signal 恒 0) — 占位返回 0
            'turnover_anomaly': sl.calc_turnover_anomaly(df),
            'sector_relative': sl.calc_sector_relative(df, sector_df if not sector_df.empty else None),
            'ad_line': sl.calc_ad_line(df),
        }
        score, mscore, ev_pos, ev_neg, tr_pos = sl.score_v22(signals)
        end_signals = sl.check_momentum_end_signals(signals, df)
        end_count = sum(1 for v in end_signals.values() if v)
        stage, stage_name = sl.stage_v22(score, mscore, end_count)
        return stage, stage_name, score, mscore, end_count
    except Exception as e:
        return None, str(e), None, None, None


def decide_combined_action(held: bool, sell_stage, buy_stage, sell_buyer_loop=False):
    """
    6 种组合动作表 (8.BUY_LADDER.md §六.3)

    输入:
      held: 是否已持仓
      sell_stage: 1/2/2.5/3 (None = 错误)
      buy_stage: 1/2/4 (None = 错误)
      sell_buyer_loop: 是否触发模式 B 回调买入

    返回: (action_icon, action_desc, position_change)
    """
    if not held:
        if buy_stage == 1:
            return '🟢', '建仓 50% (Layer 0/1 已通过 + Buy Stage 1)', 0.50
        elif buy_stage == 2:
            return '🟡', '观察池, 等 buy stage 升级', 0.0
        else:
            return '🔴', '不买 (regime 锁定 / Layer 1 不通过 / 触发否决)', 0.0
    else:
        if sell_stage == 3:
            return '🔴', '大幅减仓 80% (sell stage 3, 优先级 sell > buy)', -0.80
        elif sell_stage in (2, 2.5):
            return '🟡', f'减仓 {int((1 - STAGE_POSITION.get(sell_stage, 0.60)) * 100)}% (sell stage {sell_stage})', -(1 - STAGE_POSITION.get(sell_stage, 0.60))
        elif sell_stage == 1:
            if sell_buyer_loop:
                return '🟢', '加仓 20% (sell stage 1 + sell-buyer 闭环模式 B)', 0.20
            elif buy_stage == 1:
                return '🟢', '加仓 20% (sell stage 1 + buy stage 1)', 0.20
            else:
                return '⚪', '持有 (sell stage 1 强动能, buy 未触发)', 0.0
        else:
            return '⚪', '持有 (默认)', 0.0


def run_combo(holdings=None, force_regime_unlock=False):
    """运行 combo_layer (buy + sell 联合判定)"""
    import pandas as pd

    if holdings is None:
        holdings = DEFAULT_HOLDINGS

    today = datetime.now().date()
    print(f"🔗 COMBO_LAYER v0.1 — {today}")
    print(f"   持仓: {len(holdings)} 只")
    print(f"   regime 闸门: {'🔧 强制解锁' if force_regime_unlock else '🔒 锁定 (默认)'}")
    print("=" * 80)

    results = []
    layer0 = bl.check_layer0_regime(force_unlock=force_regime_unlock)
    layer0_unlocked = layer0['unlocked']

    print(f"\n[Layer 0 综合]")
    print(f"  沪深300 MA60: {layer0.get('ma60_pct', 'N/A')}% → {'🟢' if layer0['ma60_ok'] else '🔴'}")
    print(f"  WIF MCI: {layer0.get('mci_value', 'N/A')} → {'🟢' if layer0['mci_ok'] else '🔴'}")
    print(f"  国家队: {layer0.get('nt_pct', 'N/A')}% vs 峰值 → {'🟢' if layer0['national_team_ok'] else '🔴'}")
    print(f"  → {'🟢 解锁' if layer0_unlocked else '🔒 锁定'}")

    print(f"\n[标的逐个判定]")
    total_cash_released = 0.0
    total_cash_needed = 0.0

    for h in holdings:
        code = h['code']
        name = h['name']
        cost = h.get('cost', 0)
        shares = h.get('shares', 0)

        sell_stage, sell_stage_name, sell_score, sell_mscore, sell_end_count = _quick_sell(code)

        buy_result = bl.run_buy_ladder(
            ticker=code,
            cost=cost if shares > 0 else None,
            shares=shares if shares > 0 else None,
            held=(shares > 0),
            force_regime_unlock=force_regime_unlock,
        )

        buy_stage = buy_result.get('stage', 4)
        sell_buyer_loop = False
        if shares > 0 and sell_stage == 1 and buy_stage != 4:
            sell_buyer_loop = True

        action_icon, action_desc, pos_change = decide_combined_action(
            held=(shares > 0),
            sell_stage=sell_stage,
            buy_stage=buy_stage,
            sell_buyer_loop=sell_buyer_loop,
        )

        if shares > 0 and pos_change < 0:
            cash_released = abs(pos_change) * cost * shares
            total_cash_released += cash_released
        elif shares == 0 and pos_change > 0:
            pass

        print(f"\n{action_icon} {code} {name} ({shares}股 @ {cost})")
        print(f"   sell: stage {sell_stage} ({sell_stage_name}) score={sell_score}")
        print(f"   buy:  stage {buy_stage} ({buy_result.get('stage_name', 'N/A')})")
        print(f"   → {action_desc}")

        results.append({
            'code': code, 'name': name, 'cost': cost, 'shares': shares,
            'sell_stage': sell_stage, 'sell_score': sell_score, 'sell_end_count': sell_end_count,
            'buy_stage': buy_stage, 'buy_stage_name': buy_result.get('stage_name', ''),
            'sell_buyer_loop': sell_buyer_loop,
            'action_icon': action_icon, 'action_desc': action_desc,
            'pos_change': pos_change,
        })

    print(f"\n" + "=" * 80)
    print(f"📊 COMBO_LAYER 汇总")
    print("=" * 80)
    n_buy = sum(1 for r in results if r['pos_change'] > 0)
    n_sell = sum(1 for r in results if r['pos_change'] < 0)
    n_hold = sum(1 for r in results if r['pos_change'] == 0)
    print(f"  加仓: {n_buy}")
    print(f"  减仓: {n_sell}")
    print(f"  持有: {n_hold}")

    if n_sell == 0 and n_buy == 0:
        print(f"\n  💤 当前 regime 下无任何操作建议 — sell 维持 + buy 关闭")
        print(f"     这是正确状态: 国家队净卖出 + MCI Q3 + 化债 < 8 月 = 不调整")

    out_dir = Path('/Users/weimingzhuang/Documents/source_code/financial-services-opencode/.opencode/memory/personal-system/buy-ladder/runs') / str(today)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f'combo_v01_{today}.json'
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump({
            'date': str(today),
            'variant': 'combo_v0.1',
            'layer0': layer0,
            'results': results,
        }, f, ensure_ascii=False, indent=2)
    print(f"\n✅ 结果已保存: {out_path}")
    return results


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--ticker', help='单标的测试 (--cost --shares 可选)')
    parser.add_argument('--cost', type=float)
    parser.add_argument('--shares', type=int)
    parser.add_argument('--force-regime-unlock', action='store_true')
    args = parser.parse_args()

    if args.ticker:
        if not args.cost or not args.shares:
            print("❌ 单标的测试需要 --cost 和 --shares")
            sys.exit(1)
        holdings = [{'code': args.ticker, 'name': 'TEST', 'cost': args.cost, 'shares': args.shares}]
        run_combo(holdings=holdings, force_regime_unlock=args.force_regime_unlock)
    else:
        run_combo(force_regime_unlock=args.force_regime_unlock)