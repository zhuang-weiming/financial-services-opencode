#!/usr/bin/env python3
"""
build_artifacts_manifest.py — 数据产物清单（**只存指针，不复制数值**）

设计原则（2026-09-15 用户裁定，方案 B）
----------------------------------------
memory 里**不再复制任何数值**。memory 只记录：

    artifact_id · 绝对路径 · sha256 · as_of · 用途 · 产出脚本 · 依赖

理由：复制件会与原件的**静默漂移**——若转录错一位，memory 反而会制造
"看似权威的错误"，且没有任何机制能发现。指针 + 哈希则把"漂移"变成可检测事件。

用法
----
    python3 .opencode/scripts/build_artifacts_manifest.py            # 重新生成清单
    python3 .opencode/scripts/build_artifacts_manifest.py --check     # 校验哈希是否漂移

`--check` 在任一文件哈希不匹配、或路径缺失时返回非零退出码（可接 CI）。
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone

REPO = "/Users/weimingzhuang/Documents/source_code/financial-services-opencode"
OUT = os.path.join(REPO, ".opencode/memory/personal-system/data/"
                         "artifacts_manifest.json")

# 注册表：**这里只有路径，没有数值**
REGISTRY = [
    # ---- 上游只读输入（deglitch 依赖它，必须可验） ----
    dict(id="wif-matrix-base-20260716",
         path="example/wif-framework/data/_merged_prices_20260716.csv",
         as_of="2026-07-16", role="upstream_input",
         note="官方矩阵（**自带 2026-06-09 口径断裂**，见 data_defects）；read-only"),
    dict(id="wif-credit-baa-1986-2026",
         path="example/wif-framework/data/tickers_20260716/CreditSpread_BAA_1986_2026.csv",
         as_of="2026-05-08", role="upstream_input",
         note="信用利差历史（只到 2026-05-08，故 Z(F29_60d) 算不出）"),
    dict(id="ashare-macro-pmi",
         path="example/wif-ashare/data/macro_pmi.csv",
         as_of="2026-08", role="upstream_input", note="PMI 月度（仓内 2026-09-01 更新）"),
    dict(id="ashare-macro-m2m1",
         path="example/wif-ashare/data/macro_m2_m1_spread.csv",
         as_of="2026-06", role="upstream_input",
         note="M2/M1 剪刀差（**滞后 2 个月**，占 MCI 一半权重）"),

    # ---- 本轮抓取的原始增量 ----
    dict(id="wif-increment-prices-20260912",
         path="example/wif-framework/data/_increments/wif_update_20260912.csv",
         as_of="2026-09-11", role="fetch",
         note="9 标的 × 41 交易日（原始收盘价，故需比例拼接）"),
    dict(id="wif-increment-vix-20260912",
         path="example/wif-framework/data/_increments/vix_window_20260912.csv",
         as_of="2026-09-11", role="fetch", note="^VIX 42 个交易日"),
    dict(id="ashare-increment-hs300-20260911",
         path="example/wif-ashare/data/_increments/hs300_tencent_20260911.csv",
         as_of="2026-09-11", role="fetch", note="HS300 85 个交易日（Tier-1 Tencent）"),

    # ---- 加工产物（可复跑） ----
    dict(id="wif-matrix-extended-20260911",
         path="example/wif-framework/data/_merged_prices_20260911.csv",
         as_of="2026-09-11", role="derived",
         producer="example/wif-framework/scripts/wif_now.py",
         note="deglitch + 比例拼接后的矩阵（4966×10；SPY 2007=99.06 / 2026-09=1394.74）"),
    dict(id="wif-phase-assessment-20260911",
         path="example/wif-framework/data/wif_phase_assessment_20260911.json",
         as_of="2026-09-11", role="derived",
         producer="example/wif-framework/scripts/wif_assessment.py",
         note="WIF v5.9 五层读数（相位/象限/CSI/硬触发）"),
    dict(id="wif-phase-assessment-20260911-md",
         path="example/wif-framework/data/wif_phase_assessment_20260911.md",
         as_of="2026-09-11", role="derived",
         producer="example/wif-framework/scripts/wif_assessment.py", note="人读版"),
    dict(id="wif-verify-signals-20260911",
         path="example/wif-framework/data/verify_signals_20260911.json",
         as_of="2026-09-11", role="derived",
         producer="example/wif-framework/scripts/verify_signals.py",
         note="29 项核验明细（含 A4：文档 +1283% 被证伪）"),
    dict(id="wif-other-signals-20260911",
         path="example/wif-framework/data/other_signals_20260911.json",
         as_of="2026-09-11", role="derived",
         producer="example/wif-framework/scripts/other_signals.py",
         note="非 WIF 择时 skill（Markov/VaR/波动/相关/相对强弱）"),
    dict(id="wif-timing-dashboard-20260911",
         path="example/wif-framework/data/timing_dashboard_20260911.md",
         as_of="2026-09-11", role="report", note="美方择时总表 + 数据质量声明"),
    dict(id="wif-f29-anchors-20260911",
         path="example/wif-framework/data/F29_anchors_20260911.csv",
         as_of="2026-09-10", role="derived",
         producer="example/wif-framework/scripts/wif_now.py",
         note="F29 三个锚点 165/159/151 bp"),

    dict(id="ashare-assessment-20260911",
         path="example/wif-ashare/data/ashare_assessment_20260911.json",
         as_of="2026-09-11", role="derived",
         producer="example/wif-ashare/scripts/ashare_now.py",
         note="WIF v2.7：MCI 0.3444 → Q3；五资产目标权重"),
    dict(id="ashare-dashboard-20260911",
         path="example/wif-ashare/data/ashare_dashboard_20260911.md",
         as_of="2026-09-11", role="report", note="A股择时总表"),

    # ---- 工具（可复跑入口） ----
    dict(id="script-wif-now", path="example/wif-framework/scripts/wif_now.py",
         as_of="2026-09-15", role="tool", note="矩阵重建（含 deglitch + 比例拼接）"),
    dict(id="script-wif-assessment", path="example/wif-framework/scripts/wif_assessment.py",
         as_of="2026-09-15", role="tool", note="相位评估生成器"),
    dict(id="script-other-signals", path="example/wif-framework/scripts/other_signals.py",
         as_of="2026-09-15", role="tool", note="其他择时 skill"),
    dict(id="script-verify-signals", path="example/wif-framework/scripts/verify_signals.py",
         as_of="2026-09-15", role="tool", note="29 项核验（含 Tier-1 地面真值）"),
    dict(id="script-ashare-now", path="example/wif-ashare/scripts/ashare_now.py",
         as_of="2026-09-15", role="tool", note="A股读数（用 ashare.py 原函数）"),
]


def sha256_of(path: str) -> str | None:
    if not os.path.exists(path):
        return None
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def build() -> dict:
    arts = []
    for r in REGISTRY:
        ap = os.path.join(REPO, r["path"])
        arts.append({**r, "exists": os.path.exists(ap), "sha256": sha256_of(ap),
                     "bytes": os.path.getsize(ap) if os.path.exists(ap) else None})
    return {
        "generated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "convention": "POINTERS_ONLY — memory stores paths + sha256, never values. "
                      "Values live in the artifacts themselves; re-run the producer "
                      "scripts to rebuild. See data/README.md.",
        "repo_root": REPO,
        "artifact_count": len(arts),
        "artifacts": arts,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true",
                    help="verify hashes have not drifted; non-zero exit on drift")
    args = ap.parse_args()

    if not args.check:
        os.makedirs(os.path.dirname(OUT), exist_ok=True)
        m = build()
        with open(OUT, "w", encoding="utf-8") as f:
            json.dump(m, f, indent=2, ensure_ascii=False)
        print(f"WROTE {OUT}  ({m['artifact_count']} artifacts, pointers only)")
        return 0

    if not os.path.exists(OUT):
        print(f"FAIL manifest missing: {OUT}"); return 1
    old = {a["id"]: a for a in json.load(open(OUT, encoding="utf-8"))["artifacts"]}
    bad = []
    for r in REGISTRY:
        ap2 = os.path.join(REPO, r["path"])
        cur = sha256_of(ap2)
        prev = old.get(r["id"], {}).get("sha256")
        if cur is None:
            bad.append((r["id"], "MISSING", prev, None))
        elif prev and cur != prev:
            bad.append((r["id"], "DRIFT", prev, cur))
    if bad:
        print(f"❌ {len(bad)} artifact(s) drifted / missing:")
        for i, why, a, b in bad:
            print(f"   {why:8s} {i}  {str(a)[:12]} -> {str(b)[:12]}")
        return 1
    print(f"✅ all {len(REGISTRY)} artifacts match the manifest (no drift)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
