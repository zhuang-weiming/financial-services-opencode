#!/usr/bin/env python3
"""factor_research peer 池构建器 v1.0

解决 calc_factor_research 的 peer_dfs=None 死灯问题。

策略:
  1. 板块 ETF 映射 (硬编码 + 申万行业兜底)
     - 用户已知持仓: 券商→512000, 医药→512010, 半导体→159995, 通信→159915, ...
  2. 板块 ETF 成分股 → 自动关联同行股票
  3. 持久化到 data/sector_pool.json (一次性构建, 反复重用)

输出: data/sector_pool.json
  { "601788": ["600030", "601688", "601995", ...], ... }

用法:
  from data.sector_pool import get_peer_dfs, load_sector_pool
  peer_dfs = get_peer_dfs("601788", n_peers=8)
"""
import json
import os
import re
import sys
from collections import defaultdict
from pathlib import Path

import pandas as pd

# ============================================================
# 板块 ETF + 代码段 → sector 映射 (申万一级行业近似)
# ============================================================
PREFIX_SECTOR = {
    # 券商 (28 家 A 股上市券商)
    ('601066', '601099', '601128', '601162', '601198', '601211', '601236', '601375',
     '601377', '601456', '601555', '601595', '601658', '601688', '601696', '601788',
     '601838', '601881', '601901', '601990', '601995', '002736', '002673', '002500',
     '600030', '600061', '600109', '600369', '600621', '600837', '600864', '600909',
     '600958', '600999', '000166', '000686', '000712', '000728', '000750', '000776',
     '000783'): 'securities',
    # 半导体 / 科技
    ('002129', '002185', '002371', '300316', '300373', '300458', '300474', '300661',
     '300672', '300782', '688008', '688012', '688018', '688036', '688041',
     '688256', '600460', '600584', '603290', '603501', '603893', '603160',
     '002049', '002180', '300613', '300077', '002241', '688126', '688981',
     '688041', '688012', '002371', '300346'): 'semiconductor',
    # 医药
    ('000538', '000661', '000963', '000999', '002007', '002422', '300003', '300015',
     '300122', '300142', '300347', '300601', '300677', '300725', '600085', '600276',
     '600436', '600867', '600998', '603127', '603883', '600196', '000028'): 'pharma',
    # 银行
    ('600000', '600015', '600016', '600036', '601009', '601166', '601169', '601288',
     '601328', '601398', '601658', '601818', '601939', '601988', '601998',
     '002142', '002948', '002958', '600919', '601128'): 'bank',
    # 白酒 / 食品饮料
    ('000858', '000568', '000596', '000729', '000860', '002304', '002507', '002714',
     '600519', '600600', '600809', '603027', '603288', '603369', '600887', '600438',
     '603517', '603719', '000895', '000876', '002557', '002568', '000869'): 'consumer',
    # 钢铁
    ('600010', '600019', '600022', '600231', '600507', '600581', '600782', '600808',
     '601003', '601005', '000708', '000932', '002075', '000825', '002110', '000959',
     '600117', '601003'): 'steel',
    # 化工
    ('600028', '600188', '600346', '600583', '600871', '601808', '002648', '002493',
     '300054', '002539', '300196', '002601', '600160', '002493', '600309', '600352'): 'chemical',
    # 基建/建筑
    ('601669', '601800', '601186', '601618', '601390', '600820', '601668',
     '601186', '002081', '002541'): 'infra',
    # 通信
    ('600050', '600522', '002179', '600487', '600776', '002446', '002281',
     '600487', '002465', '300628'): 'telecom',
    # 军工
    ('600118', '600151', '600316', '600391', '600435', '600677', '600760', '600879',
     '600893', '600967', '601989', '002025', '002389', '002465', '002544',
     '300045', '300397', '300581', '300722', '300775'): 'defense',
    # 汽车 / 新能源车
    ('601633', '600104', '600166', '600418', '600609', '601238', '601777',
     '600006', '601127', '000550', '000625', '000800', '000927', '002048', '002460',
     '002594', '002920', '300750'): 'auto',
    # 保险
    ('601318', '601628', '601336', '601601'): 'insurance',
    # 航运
    ('601919', '601866', '601872', '600018', '601008', '600026', '600428', '601333'): 'shipping',
}

# 展平为 ticker → sector 查询表
TICKER_SECTOR = {}
for codes, sector in PREFIX_SECTOR.items():
    for c in codes:
        TICKER_SECTOR[c] = sector


def load_sector_pool(force_rebuild=False):
    """加载 sector_pool.json (或重新构建)"""
    cache_path = Path("data/sector_pool.json")
    if cache_path.exists() and not force_rebuild:
        return json.loads(cache_path.read_text())
    return _build_sector_pool()


def _build_sector_pool():
    """从 data/market/daily/ 已有 CSV 自动聚类同行"""
    daily_dir = Path("data/market/daily")
    if not daily_dir.exists():
        return {}

    all_codes = []
    for f in daily_dir.glob("*.csv"):
        m = re.match(r"^(\d{6})", f.name)
        if m:
            all_codes.append(m.group(1))
    all_codes = sorted(set(all_codes))
    print(f"数据池: {len(all_codes)} 只 A 股")

    # 按 sector 分组
    sector_to_codes = defaultdict(list)
    for code in all_codes:
        sector = TICKER_SECTOR.get(code)
        if sector is None:
            sector = 'unknown'
        sector_to_codes[sector].append(code)

    # ticker → peer 列表
    pool = {}
    for ticker in all_codes:
        sector = TICKER_SECTOR.get(ticker, 'unknown')
        if sector == 'unknown':
            # 兜底: 用同 3 位前缀段
            prefix3 = ticker[:3]
            same_prefix = [c for c in all_codes if c.startswith(prefix3) and c != ticker][:8]
            pool[ticker] = same_prefix
        else:
            peers = [c for c in sector_to_codes[sector] if c != ticker][:8]
            pool[ticker] = peers

    out_path = Path("data/sector_pool.json")
    out_path.write_text(json.dumps(pool, indent=2))
    print(f"sector_pool 已写入 {out_path} ({len(pool)} 只股票)")
    return pool


def get_peer_dfs(ticker, n_peers=8):
    """返回 {peer_code: df} 字典, 用于 calc_factor_research 的 peer_dfs 参数"""
    pool = load_sector_pool()
    peers = pool.get(ticker, [])[:n_peers]
    dfs = {}
    for p in peers:
        matches = list(Path("data/market/daily").glob(f"{p}*.csv"))
        if not matches:
            continue
        try:
            df = pd.read_csv(matches[0])
            if len(df) > 60:
                dfs[p] = df
        except Exception:
            pass
    return dfs


if __name__ == "__main__":
    pool = load_sector_pool(force_rebuild="--rebuild" in sys.argv)
    user_18 = ['601788', '600030', '601696', '601688', '601995', '601990',
               '601901', '512000', '600643', '600050', '601633', '601919',
               '002601', '300003', '300725', '600570', '300142', '601669']
    print("\n用户 18 只持仓 peer 池规模:")
    for t in user_18:
        peers = pool.get(t, [])
        sector = TICKER_SECTOR.get(t, 'unknown')
        print(f"  {t} [{sector}]: {len(peers)} 只同行 → {peers[:5]}...")