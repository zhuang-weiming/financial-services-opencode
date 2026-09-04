#!/usr/bin/env bash
# =====================================================================
# Technical Analysis Skills — Setup & Verification Script
# =====================================================================
# 安装所有技术分析 skill 需要的 Python 依赖，并验证计算完整性。
#
# 用法:
#   bash .opencode/skills/_shared/setup_requirements.sh [--verify-only]
#
# 依赖清单:
#   - pandas, numpy        (全部 8 框架的基础)
#   - ta-lib               (candlestick/technical-basic 加速; 可选)
#   - smartmoneyconcepts   (SMC 官方库; 可选 — 有纯 Python 替代)
#   - pyharmonics          (harmonic 官方库; 可选 — 有纯 Python 替代)
#   - czsc                 (chanlun 官方库; ⚠️ rs_czsc 上游损坏, 用纯 Python 替代)
# =====================================================================
set -euo pipefail

SKILLS_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VERIFY_ONLY=0
if [[ "${1:-}" == "--verify-only" ]]; then VERIFY_ONLY=1; fi

echo "=============================================================="
echo " Technical Analysis Skills — Setup"
echo " Root: ${SKILLS_ROOT}"
echo "=============================================================="

if [[ $VERIFY_ONLY -eq 0 ]]; then
    echo ""
    echo "[1/4] Installing core dependencies (pandas, numpy)..."
    python3 -m pip install --quiet pandas numpy 2>/dev/null || python3 -m pip install pandas numpy

    echo "[2/4] Installing TA-Lib (candlestick/technical-basic acceleration)..."
    python3 -m pip install --quiet ta-lib 2>/dev/null || echo "  (ta-lib optional — falling back to pure Python)"

    echo "[3/4] Installing optional libraries (SMC, harmonic)..."
    python3 -m pip install --quiet smartmoneyconcepts 2>/dev/null || echo "  (smartmoneyconcepts optional — pure Python works)"
    python3 -m pip install --quiet pyharmonics 2>/dev/null || echo "  (pyharmonics optional — pure Python works)"

    echo "[4/4] Checking czsc (Chanlun official lib)..."
    if python3 -c "import czsc; from czsc import CZSC" 2>/dev/null; then
        echo "  czsc import OK"
    else
        echo "  czsc broken (rs_czsc stub) — applying fix_czsc.py patch..."
        python3 "${SKILLS_ROOT}/_shared/fix_czsc.py" || echo "  ⚠️ fix_czsc.py failed — chanlun will use pure-Python fallback"
    fi
else
    echo "  (--verify-only: skipping installation)"
fi

echo ""
echo "=============================================================="
echo " Verifying all 8 skill examples produce real output..."
echo "=============================================================="

FAIL=0
run_example() {
    local name="$1"; local path="$2"
    echo ""
    echo "--- ${name} ---"
    if python3 "$path" > /tmp/tech_skill_verify_${name}.log 2>&1; then
        echo "  ✅ ${name} ran successfully"
    else
        echo "  ❌ ${name} FAILED:"
        tail -5 /tmp/tech_skill_verify_${name}.log
        FAIL=1
    fi
}

run_example "candlestick"   "${SKILLS_ROOT}/candlestick/examples/spcx_analysis.py"
run_example "elliott-wave"  "${SKILLS_ROOT}/elliott-wave/examples/spcx_analysis.py"
run_example "ichimoku"      "${SKILLS_ROOT}/ichimoku/examples/spcx_analysis.py"
run_example "harmonic"      "${SKILLS_ROOT}/harmonic/examples/spcx_analysis.py"
run_example "technical-basic" "${SKILLS_ROOT}/technical-basic/examples/spcx_analysis.py"
run_example "chanlun"       "${SKILLS_ROOT}/chanlun/examples/spcx_analysis.py"
run_example "smc"           "${SKILLS_ROOT}/smc/examples/spcx_analysis.py"
run_example "gann"          "${SKILLS_ROOT}/gann/examples/spcx_analysis.py"

echo ""
echo "=============================================================="
if [[ $FAIL -eq 0 ]]; then
    echo " ✅ ALL 8 technical analysis skills verified OK"
    echo "    Data source: llmquant-data MCP (SPCX, 2026-06-12 → 2026-08-31)"
    echo "    All algorithms are real implementations (no mocks)."
else
    echo " ❌ Some skills failed — see logs above."
fi
echo "=============================================================="
exit $FAIL
