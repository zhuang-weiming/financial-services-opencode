#!/bin/zsh
# run_all.sh — 一键全流程（与 fund_db.sqlite v1.4 契约一致）
# 用法: ./run_all.sh --regions us,eu,cnhk
set -e
cd "$(dirname "$0")"

REGIONS="us,eu,cnhk"
[[ "$1" == "--regions" ]] && REGIONS="$2"

echo "=== [0/5] QA 基线 ==="
python3 validate.py || { echo "基线未通过，中止"; exit 1; }

IFS="," read -r A B C <<< "${REGIONS// /}"
for R in $A $B $C; do
  [[ -z "$R" ]] && continue
  echo "=== [1/5] screener: $R ==="
  python3 s1_build_universe.py --regions "$R"

  echo "=== [2/5] master pull: $R ==="
  python3 s2_pull_fund_master.py --region "$R"

  echo "=== [3/5] holdings: $R ==="
  python3 s3_pull_holdings.py --region "$R"

  OUT=$(ls -dt ../ingest_raw/phase2_current/master_* | head -1)
  HOL=$(ls -dt ../ingest_raw/phase2_current/holdings_* | head -1)
  echo "=== [4/5] ingest: $R ==="
  python3 s4_ingest.py --region "$R" \
      --master "$OUT/$(basename $OUT | sed 's/master_/master_/' )".json 2>/dev/null || \
      python3 s4_ingest.py --region "$R" --master "$(ls $OUT/master_*.json 2>/dev/null | head -1)"
  python3 s4_ingest.py --holdings "$(ls $HOL/holdings_*.json 2>/dev/null | head -1)"
done

echo "=== [5/5] finalize + QA ==="
python3 s5_finalize.py
python3 validate.py
echo "✅ run_all 完成"
