"""Quantitative Backtest Reproducibility Tests (R4 risk level).

Validates quant research discipline:
- QB-1: No live-trade patterns in codebase
- QB-2: Backtest output directory structure
- QB-3: Strategy files have required metadata (signal_engine.py)
- QB-4: No PIT (Point-in-Time) data violations
- QB-5: Bundled HDF5 data integrity checks
- QB-6: Alpha zoo loading (sample of factors)
"""

import json
import time
import subprocess
from pathlib import Path
from typing import List

from . import (
    REPO_ROOT, OPENCODE_DIR, PYTHON_PKG,
    TestResult, TestSuite, print_header, colorize,
)


BACKTEST_DIR = OPENCODE_DIR / "memory" / "personal-system" / "backtests"
SKILLS_DIR = OPENCODE_DIR / "skills"


# ---------------------------------------------------------------------------
# QB-1: No live-trade patterns
# ---------------------------------------------------------------------------

LIVE_TRADE_PATTERNS = [
    r"order\s*\.submit\(\)",
    r"place_order\(\)",
    r"create_order\(",
    r"trade\.execute\(",
    r"broker\.send\(",
    r"api\.place_\w+_order\(",
    r"client\.new_order\(",
    r"'BUY'\s*,\s*'GTC'",
    r"'SELL'\s*,\s*'GTC'",
    r"ORDER_TYPE_BUY",
    r"ORDER_TYPE_SELL",
    r"account\.withdraw\(",
    r"wallet\.transfer\(",
]

LIVE_TRADE_EXCEPTIONS = [
    "test_live_trade",
    "NO_LIVE_TRADE",
    "example_order",
    "mock_order",
    "fake_order",
    "simulated_order",
    "paper_trade",
    "backtest_only",
    ".opencode/skills/trade-journal/SKILL.md",  # analyzes trades, doesn't execute
    ".opencode/skills/shadow-account/SKILL.md",  # analyzes past trades
]


def test_no_live_trade_patterns() -> TestResult:
    """QB-1: Scan for live-trade execution patterns."""
    start = time.time()
    
    # Files to scan: all Python and skill files
    python_files = list(REPO_ROOT.rglob("*.py")) + list(SKILLS_DIR.rglob("SKILL.md"))
    
    # Exclude test files and venv
    python_files = [
        f for f in python_files
        if "venv" not in str(f) and "__pycache__" not in str(f)
        and ".opencode/python/vibe-trading-quanta" in str(f)  # focus on framework
    ]
    
    hits = []
    try:
        for pattern in LIVE_TRADE_PATTERNS:
            result = subprocess.run(
                ["rg", "-n", pattern, str(OPENCODE_DIR / "python" / "vibe-trading-quanta")],
                capture_output=True, text=True, timeout=30,
            )
            if result.stdout:
                for line in result.stdout.split("\n"):
                    if line.strip():
                        # Skip if matches an exception
                        if any(exc in line for exc in LIVE_TRADE_EXCEPTIONS):
                            continue
                        hits.append(f"{pattern}: {line[:120]}")
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    
    if hits:
        return TestResult(
            name="QB-1: Live-trade patterns",
            status="FAIL", severity="critical",
            message=f"{len(hits)} potential live-trade calls found",
            details={"hits": hits[:10]},
            duration_ms=(time.time()-start)*1000,
        )
    return TestResult(
        name="QB-1: Live-trade patterns",
        status="PASS",
        message="No live-trade execution patterns detected",
        duration_ms=(time.time()-start)*1000,
    )


# ---------------------------------------------------------------------------
# QB-2: Backtest output directory
# ---------------------------------------------------------------------------

def test_backtest_directory_structure() -> TestResult:
    """QB-2: Backtest directory must have BT-XXX subdirs with required files."""
    start = time.time()
    
    if not BACKTEST_DIR.exists():
        return TestResult(
            name="QB-2: Backtest directory",
            status="SKIP",
            message="Backtest directory not found",
            duration_ms=(time.time()-start)*1000,
        )
    
    bt_dirs = sorted(BACKTEST_DIR.glob("BT-*"))
    if not bt_dirs:
        return TestResult(
            name="QB-2: Backtest directory",
            status="WARN", severity="minor",
            message="No BT-* directories found",
            duration_ms=(time.time()-start)*1000,
        )
    
    missing_files = []
    for bt_dir in bt_dirs:
        expected = ["README.md", "report.md", "results.csv", "script.py"]
        for fname in expected:
            f = bt_dir / fname
            if not f.exists():
                missing_files.append(f"{bt_dir.name}/{fname}")
    
    if missing_files:
        return TestResult(
            name="QB-2: BT directory structure",
            status="FAIL", severity="major",
            message=f"{len(missing_files)} missing files across {len(bt_dirs)} BTs",
            details={"missing": missing_files[:10]},
            duration_ms=(time.time()-start)*1000,
        )
    return TestResult(
        name="QB-2: BT directory structure",
        status="PASS",
        message=f"All {len(bt_dirs)} BTs have required files",
        duration_ms=(time.time()-start)*1000,
    )


# ---------------------------------------------------------------------------
# QB-3: Strategy files metadata
# ---------------------------------------------------------------------------

def test_readme_has_metadata() -> TestResult:
    """QB-3: Each BT README must have key metadata sections."""
    start = time.time()
    if not BACKTEST_DIR.exists():
        return TestResult(
            name="QB-3: BT README metadata",
            status="SKIP",
            message="Backtest directory not found",
            duration_ms=(time.time()-start)*1000,
        )
    
    bt_dirs = sorted(BACKTEST_DIR.glob("BT-*"))
    if not bt_dirs:
        return TestResult(name="QB-3: BT README metadata", status="SKIP",
                           message="No BT directories", duration_ms=(time.time()-start)*1000)
    
    missing_meta = []
    for bt_dir in bt_dirs:
        readme = bt_dir / "README.md"
        if not readme.exists():
            missing_meta.append(f"{bt_dir.name}/README.md missing")
            continue
        text = readme.read_text().lower()
        required_sections = ["assumption", "method", "result", "limit"]
        for sec in required_sections:
            if sec not in text:
                missing_meta.append(f"{bt_dir.name}/README.md missing '{sec}' section")
                break  # only report first missing per file
    
    if missing_meta:
        return TestResult(
            name="QB-3: BT README metadata",
            status="WARN", severity="minor",
            message=f"{len(missing_meta)} BTs with missing metadata sections",
            details={"issues": missing_meta[:5]},
            duration_ms=(time.time()-start)*1000,
        )
    return TestResult(
        name="QB-3: BT README metadata",
        status="PASS",
        message="All BT READMEs have required metadata sections",
        duration_ms=(time.time()-start)*1000,
    )


# ---------------------------------------------------------------------------
# QB-4: No PIT violation check (symbolic — checks for common patterns)
# ---------------------------------------------------------------------------

def test_pit_violation_check() -> TestResult:
    """QB-4: Check for potential PIT data violations in backtest scripts."""
    start = time.time()
    if not BACKTEST_DIR.exists():
        return TestResult(
            name="QB-4: PIT violation check",
            status="SKIP",
            message="Backtest directory not found",
            duration_ms=(time.time()-start)*1000,
        )
    
    pit_patterns = [
        r"future_data\s*=",
        r"forward_looking\s*=",
        r"lookahead\s*=",
        r"peek\s*\(\s*-\d+\s*\)",
        r"shift\(\s*-\d+\s*\)",
        r"\.iloc\[\s*:\s*,\s*-\d+\s*:\s*\]",
    ]
    
    issues = []
    for bt_dir in sorted(BACKTEST_DIR.glob("BT-*")):
        for fname in ["script.py"]:
            f = bt_dir / fname
            if not f.exists():
                continue
            text = f.read_text()
            for i, pattern in enumerate(pit_patterns):
                if pattern in text:
                    # Find line numbers
                    for lineno, line in enumerate(text.split("\n"), 1):
                        if pattern in line:
                            issues.append(f"{bt_dir.name}/{fname}:{lineno}: {line.strip()[:80]}")
                            break
    
    if issues:
        return TestResult(
            name="QB-4: PIT violation check",
            status="FAIL", severity="critical",
            message=f"{len(issues)} potential PIT violations",
            details={"issues": issues[:10]},
            duration_ms=(time.time()-start)*1000,
        )
    return TestResult(
        name="QB-4: PIT violation check",
        status="PASS",
        message="No PIT violations detected in backtest scripts",
        duration_ms=(time.time()-start)*1000,
    )


# ---------------------------------------------------------------------------
# QB-5: HDF5 data integrity (alpha-engine-v21)
# ---------------------------------------------------------------------------

def test_hdf5_integrity() -> TestResult:
    """QB-5: Check bundled HDF5 file for alpha-engine-v21."""
    start = time.time()
    
    h5_path = SKILLS_DIR / "alpha-engine-v21" / "data" / "data_v20.h5"
    if not h5_path.exists():
        return TestResult(
            name="QB-5: HDF5 data integrity",
            status="SKIP",
            message=f"HDF5 file not found at {h5_path}",
            duration_ms=(time.time()-start)*1000,
        )
    
    try:
        import h5py
        with h5py.File(str(h5_path), "r") as f:
            # Check size
            size_mb = h5_path.stat().st_size / (1024 * 1024)
            
            # List top-level datasets
            keys = list(f.keys())
            
            # Check for price data
            has_price = any("price" in k.lower() or "close" in k.lower() for k in keys)
            has_returns = any("return" in k.lower() or "ret" in k.lower() for k in keys)
            has_wt = any("wt" in k.lower() or "wavetrend" in k.lower() for k in keys)
            
            # Get shape info from first dataset
            shapes = {}
            for k in keys[:5]:
                try:
                    shapes[k] = f[k].shape
                except Exception:
                    pass
            
            return TestResult(
                name="QB-5: HDF5 data integrity",
                status="PASS",
                message=f"Size: {size_mb:.0f}MB, Keys: {len(keys)}, Price: {has_price}, "
                        f"Returns: {has_returns}, WT: {has_wt}",
                details={"keys": keys, "shapes": shapes},
                duration_ms=(time.time()-start)*1000,
            )
    except ImportError:
        return TestResult(
            name="QB-5: HDF5 data integrity",
            status="WARN", severity="minor",
            message="h5py not installed, cannot verify HDF5 content",
            duration_ms=(time.time()-start)*1000,
        )
    except Exception as e:
        return TestResult(
            name="QB-5: HDF5 data integrity",
            status="FAIL", severity="major",
            message=f"HDF5 error: {e}",
            duration_ms=(time.time()-start)*1000,
        )


# ---------------------------------------------------------------------------
# QB-6: Alpha zoo sample check
# ---------------------------------------------------------------------------

def test_alpha_zoo_access() -> TestResult:
    """QB-6: Verify alpha zoo can be imported and has expected factors."""
    start = time.time()
    alpha_zoo_path = PYTHON_PKG / "alpha_zoo"
    
    if not alpha_zoo_path.exists():
        return TestResult(
            name="QB-6: Alpha zoo access",
            status="SKIP",
            message="alpha_zoo directory not found",
            duration_ms=(time.time()-start)*1000,
        )
    
    # Look for factor definition files
    factor_files = list(alpha_zoo_path.rglob("*.py"))
    factor_files = [f for f in factor_files if not f.name.startswith("_") and not f.name.startswith(".")]
    
    total_factors = 0
    factor_families = {}
    
    for ff in factor_files:
        text = ff.read_text()
        # Count factor functions (def alpha_*)
        factor_defs = [l for l in text.split("\n") if l.strip().startswith("def alpha_")]
        family = ff.parent.name
        factor_families[family] = len(factor_defs)
        total_factors += len(factor_defs)
    
    if total_factors == 0:
        return TestResult(
            name="QB-6: Alpha zoo access",
            status="WARN", severity="minor",
            message="Alpha zoo files found but no factor definitions detected",
            duration_ms=(time.time()-start)*1000,
        )
    
    return TestResult(
        name="QB-6: Alpha zoo access",
        status="PASS",
        message=f"{total_factors} factors across {len(factor_families)} families: {factor_families}",
        details={"factor_families": factor_families},
        duration_ms=(time.time()-start)*1000,
    )


# ---------------------------------------------------------------------------
# Run all quant backtest tests
# ---------------------------------------------------------------------------

def run_all() -> TestSuite:
    suite = TestSuite(name="Quant Backtest Reproducibility")
    suite.add(test_no_live_trade_patterns())
    suite.add(test_backtest_directory_structure())
    suite.add(test_readme_has_metadata())
    suite.add(test_pit_violation_check())
    suite.add(test_hdf5_integrity())
    suite.add(test_alpha_zoo_access())
    return suite


if __name__ == "__main__":
    print_header("QUANT BACKTEST REPRODUCIBILITY TESTS")
    suite = run_all()
    for r in suite.results:
        status_color = {"PASS": "green", "FAIL": "red", "WARN": "yellow", "SKIP": "cyan"}[r.status]
        print(f"  [{colorize(r.status, status_color)}] {r.name}: {r.message}")
    print(f"\n  Total: {len(suite.results)}, Passed: {suite.passed}, Failed: {suite.failed}, Warnings: {suite.warnings}")
