#!/usr/bin/env python3
"""批量下载 A 股日线数据池 (mootdx, 2020-2026) → data/market/daily/

数据源: mootdx (通达信 TCP, 免费无 IP 限制, A股首选)
覆盖: alpha-engine-v21 HDF5 的 3060 只 A 股 (3047 只可下载)
历史: 2020-01 至今 (约 4×800 bars 分段拉取)
格式: date,code,open,close,high,low,volume (与现有 94 只一致)
断点续传: 已存在的 csv 跳过; 支持 --batch 分批跑
用法:
    python3 data/download_ashare_daily.py                # 全量
    python3 data/download_ashare_daily.py --batch 0 5    # 第 0/5 批
"""
import argparse
import h5py
import os
import re
import sys
import time

import pandas as pd
from mootdx.quotes import Quotes

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(BASE_DIR, "data", "market", "daily")
H5_PATH = os.path.join(
    BASE_DIR, ".opencode", "skills", "alpha-engine-v21", "data", "data_v20.h5"
)

A_SHARE_RE = re.compile(r"^(60|00|30|68|601|603|605|688|000)\d{4}$")
SEGMENTS = 4  # 4×800 bars ≈ 2020-01 → 2026-08
BATCH_SIZE = 300


def get_universe():
    with h5py.File(H5_PATH, "r") as h5:
        codes = [
            (c.decode() if isinstance(c, bytes) else c).replace("-CN", "")
            for c in h5["prices/axis0"][:]
        ]
    return [c for c in codes if A_SHARE_RE.match(c)]


def download_one(client, code, out_path):
    """分段拉取 2020-2026 日线并保存; 成功返回 bars 数, 失败返回 0"""
    frames = []
    for seg in range(SEGMENTS):
        try:
            df = client.bars(symbol=code, frequency=9, offset=800, start=seg * 800)
        except Exception:
            time.sleep(0.5)
            try:
                df = client.bars(symbol=code, frequency=9, offset=800, start=seg * 800)
            except Exception:
                return 0
        if df is None or len(df) == 0:
            break
        frames.append(df)
    if not frames:
        return 0
    df = pd.concat(frames)
    df = df[~df.index.duplicated(keep="last")].sort_index()
    df = df[df.index >= "2020-01-01"]
    if len(df) < 100:
        return 0
    out = pd.DataFrame({
        "date": df.index.strftime("%Y-%m-%d"),
        "code": code,
        "open": df["open"].astype(float),
        "close": df["close"].astype(float),
        "high": df["high"].astype(float),
        "low": df["low"].astype(float),
        "volume": df["volume"].astype(float),
    })
    out.to_csv(out_path, index=False)
    return len(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--batch", type=int, nargs=2, default=None,
                    help="batch_idx batch_total — 只处理第 batch_idx/batch_total 批")
    ap.add_argument("--only", type=str, default=None, help="只下载单个代码 (调试)")
    args = ap.parse_args()

    universe = get_universe()
    if args.only:
        universe = [args.only]
    elif args.batch:
        idx, total = args.batch
        universe = universe[idx::total]
        print(f"[batch {idx}/{total}] {len(universe)} 只")

    # 过滤已存在
    os.makedirs(OUT_DIR, exist_ok=True)
    existing = {f[:6] for f in os.listdir(OUT_DIR) if f.endswith(".csv")}
    todo = [c for c in universe if c not in existing]
    print(f"待下载 {len(todo)} 只 (已存在 {len(universe)-len(todo)})")

    client = Quotes.factory(market="std")
    ok, fail, t0 = 0, 0, time.time()
    for i, code in enumerate(todo):
        out_path = os.path.join(OUT_DIR, f"{code}.csv")
        n = download_one(client, code, out_path)
        if n:
            ok += 1
        else:
            fail += 1
            if os.path.exists(out_path):
                os.remove(out_path)
        if (i + 1) % 100 == 0:
            el = time.time() - t0
            print(f"  [{i+1}/{len(todo)}] ok={ok} fail={fail} elapsed={el:.0f}s")
    el = time.time() - t0
    print(f"完成: ok={ok} fail={fail} elapsed={el:.0f}s ({el/max(len(todo),1):.2f}s/只)")


if __name__ == "__main__":
    main()
