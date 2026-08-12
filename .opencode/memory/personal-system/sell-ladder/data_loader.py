#!/usr/bin/env python3
"""统一日线数据加载器 (A 股 / ETF)。

集中化数据存放: <workspace>/data/market/daily/<code>_<name>.csv
  - 统一命名 `<code>_<name>.csv` (见 data/market/daily/INDEX.md)
  - 加载顺序: data/market/daily/ → 旧位置 (sell-ladder/data) fallback → Sina API 下载并落盘
  - 兼容中文列名 / Sina 英文列名

用法 (任意脚本):
  import sys; sys.path.insert(0, '.opencode/memory/personal-system/sell-ladder')
  from data_loader import load_daily, get_name
  df = load_daily('300725')
"""
from __future__ import annotations

import re
import time
from pathlib import Path
from typing import Optional

import pandas as pd

SELL_LADDER_DIR = Path(__file__).resolve().parent
WORKSPACE_ROOT = Path(__file__).resolve().parents[4]   # 仓库根 (data/ 所在层)
DATA_DIR = SELL_LADDER_DIR / "data"                    # 旧位置 (fallback)
LEGACY_DIRS = [DATA_DIR / "tech-pool", DATA_DIR / "cross-data"]
MARKET_DAILY_DIR = WORKSPACE_ROOT / "data" / "market" / "daily"

RENAME = {
    '日期': 'date', '股票代码': 'code', '开盘': 'open', '收盘': 'close',
    '最高': 'high', '最低': 'low', '成交量': 'volume', '成交额': 'amount',
    '涨跌幅': 'chg_pct',
}


def _standardize(df: pd.DataFrame, ticker: str) -> pd.DataFrame:
    df = df.rename(columns={k: v for k, v in RENAME.items() if k in df.columns})
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'])
    elif df.index.name == 'date':
        df = df.reset_index()
        df['date'] = pd.to_datetime(df['date'])
    for col in ['open', 'close', 'high', 'low', 'volume']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    if 'code' not in df.columns:
        df['code'] = ticker
    return df.sort_values('date').reset_index(drop=True)


def _sina_download(code: str) -> pd.DataFrame:
    """Sina 历史 K 线 (轻量, 永不被封)

    A 股交易所前缀 (含 ETF):
      sz: 0 / 3 开头 (深市股票) + 15 开头 (深市 ETF, 如 159915)
      sh: 5 / 6 开头 (沪市股票 + 沪市 ETF, 如 512000/510300) + 688 (科创板)
    """
    full_code = f'sz{code}' if code.startswith(('0', '3', '15')) else f'sh{code}'
    url = 'https://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData'
    params = {'symbol': full_code, 'scale': 240, 'ma': 'no', 'datalen': 900}
    r = __import__('requests').get(url, params=params, timeout=10,
                                   headers={'User-Agent': 'Mozilla/5.0'})
    df = pd.DataFrame(r.json())
    df = df.rename(columns={'day': 'date'})
    df['date'] = pd.to_datetime(df['date'])
    return df


def _find_local(ticker: str) -> Optional[Path]:
    """按优先级找本地文件: data/market/daily → tech-pool → cross-data → raw_daily"""
    if not ticker.isdigit():
        return None
    # 1. 集中化目录 (统一命名)
    for p in MARKET_DAILY_DIR.glob(f"{ticker}_*.csv"):
        return p
    # 2. 旧 tech-pool / cross-data (中文名文件)
    for d in LEGACY_DIRS:
        for p in d.glob(f"{ticker}_*.csv"):
            return p
    # 3. 旧 raw_daily
    p = DATA_DIR / f"raw_daily_{ticker}.csv"
    return p if p.exists() else None


def load_daily(ticker: str) -> Optional[pd.DataFrame]:
    """加载任意标的日线。本地无 → Sina 下载 → 落盘到集中化目录。失败返回 None。"""
    local = _find_local(ticker)
    if local:
        try:
            df = pd.read_csv(local)
            return _standardize(df, ticker)
        except Exception:
            pass

    if not ticker.isdigit():
        return None
    try:
        print(f"  ⚠️ 本地无 {ticker} 数据, 改用 Sina API 下载...")
        df = _sina_download(ticker)
        df = _standardize(df, ticker)
        # 落盘到集中化目录
        name = get_name(ticker)
        MARKET_DAILY_DIR.mkdir(parents=True, exist_ok=True)
        dst = MARKET_DAILY_DIR / (f"{ticker}_{name}.csv" if name else f"{ticker}.csv")
        df[['date', 'code', 'open', 'close', 'high', 'low', 'volume']].to_csv(dst, index=False)
        print(f"  ✅ 已保存到 {dst}")
        return df
    except Exception as e:
        print(f"  ❌ 加载 {ticker} 失败: {e}")
        return None


def get_name(ticker: str) -> str:
    """从文件名/INDEX 解析证券名 (失败返回空串)"""
    local = _find_local(ticker)
    if local:
        m = re.match(r"\d{6}_(.+)\.csv$", local.name)
        if m:
            return m.group(1).strip()
    # 尝试从 INDEX.md 解析
    idx = MARKET_DAILY_DIR / "INDEX.md"
    if idx.exists():
        for line in idx.read_text(encoding='utf-8').splitlines():
            if line.startswith(f"| {ticker} "):
                parts = [p.strip() for p in line.split('|')]
                if len(parts) > 2 and parts[2] != '-':
                    return parts[2]
    return ""


def list_universe() -> pd.DataFrame:
    """返回 data/market/daily 全量清单 (code, name, start, end, bars)。"""
    rows = []
    for p in MARKET_DAILY_DIR.glob("*_*.csv"):
        m = re.match(r"(\d{6})_(.+)\.csv$", p.name)
        if not m:
            continue
        code, name = m.group(1), m.group(2)
        try:
            df = pd.read_csv(p)
            rows.append({
                'code': code, 'name': name,
                'start': str(df.iloc[0]['date'])[:10],
                'end': str(df.iloc[-1]['date'])[:10],
                'bars': len(df),
            })
        except Exception:
            rows.append({'code': code, 'name': name, 'start': '-', 'end': '-', 'bars': 0})
    return pd.DataFrame(rows)


if __name__ == '__main__':
    t = '300725'
    df = load_daily(t)
    print(f"加载 {t} ({get_name(t)}): {len(df)} bars, {df['date'].iloc[0]} → {df['date'].iloc[-1]}")
