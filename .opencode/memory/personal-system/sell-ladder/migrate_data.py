#!/usr/bin/env python3
"""迁移 sell-ladder/data/ 的 A 股日线数据到集中化 data/market/daily/。

设计原则 (data/README.md):
  - 小 + 多 subagent 共享 + 高频 → data/market/daily/
  - 统一命名: <code>_<name>.csv
  - 生成 INDEX.md 清单
  - 删除遗留 wt_daily_* (现场均实时计算)

用法:
  python3 migrate_data.py [--dry-run]
"""
from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Dict, Optional

import requests

SELL_LADDER_DIR = Path(__file__).resolve().parent
SRC_DIR = SELL_LADDER_DIR / "data"
WORKSPACE_ROOT = Path(__file__).resolve().parents[4]  # 仓库根 (data/ 所在层)
MARKET_DIR = WORKSPACE_ROOT / "data" / "market"
DST_DIR = MARKET_DIR / "daily"
LEGACY_WT = ["wt_daily_300725.csv", "wt_daily_300725_last60.csv"]

# 本地已有人类可读名称 (最高优先级, 不依赖网络)
KNOWN_NAMES: Dict[str, str] = {
    "002821": "凯莱英", "300363": "博腾股份", "300759": "康龙化成", "603259": "药明康德",
}

def _exchange_prefix(code: str) -> str:
    if code.startswith(("0", "3")):
        return f"sz{code}"
    return f"sh{code}"  # 6, 688, 5(ETF), 1(基金)

def fetch_names(codes: list[str]) -> Dict[str, str]:
    """从 Sina 行情接口批量拉证券名 (每次 50 个)。"""
    names: Dict[str, str] = {}
    codes = list(dict.fromkeys(codes))
    for i in range(0, len(codes), 50):
        chunk = codes[i:i + 50]
        symbols = ",".join(_exchange_prefix(c) for c in chunk)
        url = f"https://hq.sinajs.cn/list={symbols}"
        try:
            r = requests.get(url, headers={
                "Referer": "https://finance.sina.com.cn",
                "User-Agent": "Mozilla/5.0",
            }, timeout=10)
            r.encoding = "gbk"
            for sym, code in zip(symbols.split(","), chunk):
                m = re.search(rf'{sym}="([^,]*),', r.text)
                if m and m.group(1):
                    names[code] = m.group(1)
                else:
                    names[code] = ""
        except Exception as e:
            print(f"  ⚠️ Sina 批量拉取失败 ({chunk}): {e}", file=sys.stderr)
            for c in chunk:
                names[c] = ""
    return names

def collect_sources() -> Dict[str, Optional[str]]:
    """扫描本地所有日线 CSV, 返回 {code: 源路径}。tech-pool/cross-data 已有的中文名文件直接读取文件名"""
    found: Dict[str, Optional[str]] = {}

    # 1. 中文名文件 (cross-data / tech-pool): 从文件名拿 name
    for sub in ["cross-data", "tech-pool"]:
        for f in (SRC_DIR / sub).glob("*.csv"):
            m = re.match(r"(\d{6})_(.+)\.csv$", f.name)
            if m:
                code = m.group(1)
                KNOWN_NAMES.setdefault(code, m.group(2).strip())
                found.setdefault(code, str(f))

    # 2. raw_daily_<code>.csv
    for f in SRC_DIR.glob("raw_daily_*.csv"):
        m = re.match(r"raw_daily_(\d{6})\.csv$", f.name)
        if m:
            found.setdefault(m.group(1), str(f))

    # tech-pool 里的 wt_ 文件由 wt 加载器单独处理 (不在本次迁移范围)
    return found

def main() -> int:
    dry_run = "--dry-run" in sys.argv
    if not dry_run:
        DST_DIR.mkdir(parents=True, exist_ok=True)

    sources = collect_sources()
    codes = sorted(sources.keys())
    print(f"发现 {len(codes)} 个标的日线数据源")

    names = fetch_names(codes)
    # 本地已知名称优先级最高
    for c, n in KNOWN_NAMES.items():
        if n:
            names[c] = n
    for c in codes:
        if not names.get(c):
            names[c] = KNOWN_NAMES.get(c, "")
    # 清理名称中空格 (如 Sina 返回 "五 粮 液")
    for c in codes:
        names[c] = re.sub(r"\s+", "", names.get(c, ""))

    missing = [c for c in codes if not names.get(c)]
    if missing:
        print(f"  ⚠️ 无法获取名称: {missing} (将只用代码命名)")

    rows = []
    for code in codes:
        src = Path(sources[code])
        name = names.get(code) or ""
        dst_name = f"{code}_{name}.csv" if name else f"{code}.csv"
        dst = DST_DIR / dst_name
        rows.append((code, name, src.name, dst_name))

    # 生成 INDEX.md 前先统计每只的 bars 范围 (从源文件读)
    index_lines = []
    index_lines.append("# A 股日线数据 INDEX")
    index_lines.append("")
    index_lines.append("> 集中化存放 (data/market/daily/)，统一命名 `<code>_<name>.csv`。")
    index_lines.append("> 来源: Sina API (本地永久缓存)。加载: `sell-ladder/data_loader.py`。")
    index_lines.append("")
    index_lines.append("| 代码 | 名称 | 起始→结束 | bars | 源文件 |")
    index_lines.append("|------|------|----------|------|--------|")
    for code, name, src_name, dst_name in sorted(rows):
        # bars / 日期范围
        try:
            lines = Path(src).read_text(encoding="utf-8", errors="ignore").splitlines()
            header = lines[0]
            n = len(lines) - 1
            if len(lines) > 1:
                first = lines[1].split(",")[0]
                last = lines[-1].split(",")[0]
            else:
                first = last = "-"
        except Exception:
            n, first, last = 0, "-", "-"
        index_lines.append(f"| {code} | {name or '-'} | {first}→{last} | {n} | {src_name} |")

    if dry_run:
        print(f"\n[dry-run] 将迁移 {len(rows)} 个文件到 {DST_DIR}/，并生成 INDEX.md({len(index_lines)} 行)")
        for code, name, src, dst in rows:
            print(f"  {src:40s} -> {dst}")
        return 0

    # 执行迁移 (copy 而非 move, 保留源以便回滚; 确认后源可删)
    copied = 0
    for code, name, src_name, dst_name in sorted(rows):
        src = SRC_DIR / src_name if not Path(src_name).parent.name else Path(src_name)
        if not src.exists():
            # 可能来自 cross-data/tech-pool 子目录
            for sub in ["cross-data", "tech-pool"]:
                cand = SRC_DIR / sub / src_name
                if cand.exists():
                    src = cand
                    break
        dst = DST_DIR / dst_name
        if src.exists():
            import shutil
            data = src.read_bytes()
            if dst.exists() and dst.read_bytes() == data:
                pass
            else:
                dst.write_bytes(data)
            copied += 1

    # 生成 INDEX.md
    (DST_DIR / "INDEX.md").write_text("\n".join(index_lines) + "\n", encoding="utf-8")
    print(f"✅ 已迁移 {copied}/{len(rows)} 个文件到 {DST_DIR}/，并生成 INDEX.md")

    # 删除遗留 wt 文件
    for w in LEGACY_WT:
        p = SRC_DIR / w
        if p.exists():
            p.unlink()
            print(f"🗑  删除遗留 {w}")

    # 清理旧命名的目标文件 (命名规范变化后残留)
    stale = [p for p in DST_DIR.glob("*.csv") if re.search(r"\s", p.name)]
    for p in stale:
        p.unlink()
        print(f"🗑  删除带空格旧名 {p.name}")
    print(f"\n下一步 (确认迁移无误后): 修改 sell_ladder.py/backtest_v090.py 用 data_loader, 然后可删除 data/ 源文件。")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
