#!/usr/bin/env python3
"""标准化 data/market/daily/ 下的所有 CSV 为统一英文表头:
   date,code,open,close,high,low,volume
"""
import os
import sys

import pandas as pd

DAILY_DIR = "data/market/daily"

# 中文 → 英文 列名映射
COL_MAP = {
    '日期': 'date', '股票代码': 'code',
    '开盘': 'open', '收盘': 'close', '最高': 'high', '最低': 'low',
    '成交量': 'volume', '成交额': 'amount',
    '换手率': 'turnover',
}

# 标准列顺序
STANDARD_COLS = ['date', 'code', 'open', 'close', 'high', 'low', 'volume']


def fix_one(path):
    """修复单文件为英文表头, 返回是否已修复"""
    df = pd.read_csv(path)
    if 'date' in df.columns and 'close' in df.columns:
        return False  # 已经是英文
    if '日期' not in df.columns and '股票代码' not in df.columns:
        return False
    df = df.rename(columns=COL_MAP)
    if 'volume' not in df.columns and '成交量' not in df.columns:
        # 兜底: 没有 volume 列
        if 'volume' not in df.columns:
            df['volume'] = 0
    keep = [c for c in STANDARD_COLS if c in df.columns]
    df = df[keep]
    # code 列填充
    if 'code' not in df.columns:
        import re
        m = re.match(r'^(\d{6})', os.path.basename(path))
        if m:
            df['code'] = m.group(1)
        else:
            return False
    # 补齐缺列
    for c in STANDARD_COLS:
        if c not in df.columns:
            df[c] = 0
    df = df[STANDARD_COLS]
    df.to_csv(path, index=False)
    return True


def main():
    files = sorted([f for f in os.listdir(DAILY_DIR) if f.endswith('.csv')])
    fixed = 0
    for f in files:
        p = os.path.join(DAILY_DIR, f)
        try:
            if fix_one(p):
                fixed += 1
        except Exception as e:
            print(f"FAIL {f}: {e}")
    print(f"修复完成: {fixed}/{len(files)} 个文件")


if __name__ == "__main__":
    main()