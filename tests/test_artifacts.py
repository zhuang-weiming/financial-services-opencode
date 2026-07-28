"""Artifact Output Tests (R3 risk level).

Tests output directory and file generation:
- AR-1: `out/` directory exists and is gitignored
- AR-2: Report files follow naming conventions
- AR-3: No stale/redundant files in out/
- AR-4: Out directory size limits
- AR-5: README present in out/ if populated
"""

import os
import time
import re
from pathlib import Path

from . import (
    REPO_ROOT,
    TestResult, TestSuite, print_header, colorize,
)

OUT_DIR = REPO_ROOT / "out"


# ---------------------------------------------------------------------------
# AR-1: out/ directory
# ---------------------------------------------------------------------------

def test_out_dir_exists():
    """AR-1a: out/ directory must exist."""
    start = time.time()
    exists = OUT_DIR.exists()
    
    if not exists:
        return TestResult(
            name="AR-1a: out/ directory exists",
            status="WARN", severity="minor",
            message="out/ directory does not exist",
            duration_ms=(time.time()-start)*1000,
        )
    return TestResult(
        name="AR-1a: out/ directory exists",
        status="PASS",
        message=f"Found at {OUT_DIR}",
        duration_ms=(time.time()-start)*1000,
    )


def test_out_dir_gitignored():
    """AR-1b: out/ must be in .gitignore."""
    start = time.time()
    
    gitignore = REPO_ROOT / ".gitignore"
    if not gitignore.exists():
        return TestResult(
            name="AR-1b: out/ gitignored",
            status="WARN", severity="minor",
            message=".gitignore not found",
            duration_ms=(time.time()-start)*1000,
        )
    
    text = gitignore.read_text()
    has_out = "/out" in text or "/out/" in text or "out/" in text or "out" in text.split("\n")
    
    if not has_out:
        return TestResult(
            name="AR-1b: out/ gitignored",
            status="FAIL", severity="major",
            message="out/ not found in .gitignore",
            duration_ms=(time.time()-start)*1000,
        )
    return TestResult(
        name="AR-1b: out/ gitignored",
        status="PASS",
        message="out/ is in .gitignore",
        duration_ms=(time.time()-start)*1000,
    )


# ---------------------------------------------------------------------------
# AR-2: Naming conventions
# ---------------------------------------------------------------------------

def test_naming_conventions():
    """AR-2: Check file naming conventions in out/."""
    start = time.time()
    if not OUT_DIR.exists():
        return TestResult(
            name="AR-2: File naming conventions",
            status="SKIP",
            message="out/ directory not found",
            duration_ms=(time.time()-start)*1000,
        )
    
    issues = []
    # Allowed patterns
    allowed_patterns = [
        r'^[a-zA-Z0-9_-]+\.(md|txt|csv|xlsx|pdf|docx|pptx|json|html|png)$',
        r'^[a-zA-Z0-9_-]+/\d{4}-\d{2}-\d{2}/',
    ]
    
    for f in OUT_DIR.rglob("*"):
        if f.is_dir():
            continue
        rel = str(f.relative_to(OUT_DIR))
        if not any(re.match(p, rel) for p in allowed_patterns):
            # Check if it's within a dated dir
            if not re.match(r'^\d{4}-\d{2}-\d{2}/', rel):
                issues.append(f"Non-standard naming: {rel}")
    
    if issues:
        return TestResult(
            name="AR-2: File naming conventions",
            status="WARN", severity="minor",
            message=f"{len(issues)} files with non-standard names",
            details={"issues": issues[:5]},
            duration_ms=(time.time()-start)*1000,
        )
    return TestResult(
        name="AR-2: File naming conventions",
        status="PASS",
        message="All files follow standard naming",
        duration_ms=(time.time()-start)*1000,
    )


# ---------------------------------------------------------------------------
# AR-3: No stale files
# ---------------------------------------------------------------------------

def test_no_stale_files():
    """AR-3: Check for stale (>90 days old without modification) files in out/."""
    start = time.time()
    if not OUT_DIR.exists():
        return TestResult(
            name="AR-3: Stale file check",
            status="SKIP",
            message="out/ directory not found",
            duration_ms=(time.time()-start)*1000,
        )
    
    import time as _time
    now = _time.time()
    threshold = 90 * 24 * 60 * 60  # 90 days in seconds
    
    stale = []
    for f in OUT_DIR.rglob("*"):
        if f.is_file():
            age = now - f.stat().st_mtime
            if age > threshold:
                stale.append(f"{f.name} ({age/86400:.0f} days)")
    
    if stale:
        return TestResult(
            name="AR-3: Stale file check",
            status="WARN", severity="minor",
            message=f"{len(stale)} files older than 90 days",
            details={"stale": stale[:5]},
            duration_ms=(time.time()-start)*1000,
        )
    return TestResult(
        name="AR-3: Stale file check",
        status="PASS",
        message="No stale files in out/",
        duration_ms=(time.time()-start)*1000,
    )


# ---------------------------------------------------------------------------
# AR-4: Size limits
# ---------------------------------------------------------------------------

def test_out_dir_size():
    """AR-4: Check out/ directory total size < 100MB."""
    start = time.time()
    if not OUT_DIR.exists():
        return TestResult(
            name="AR-4: Directory size",
            status="SKIP",
            message="out/ directory not found",
            duration_ms=(time.time()-start)*1000,
        )
    
    total_size = 0
    for f in OUT_DIR.rglob("*"):
        if f.is_file():
            total_size += f.stat().st_size
    
    size_mb = total_size / (1024 * 1024)
    limit_mb = 100
    
    if size_mb > limit_mb:
        return TestResult(
            name="AR-4: Directory size",
            status="WARN", severity="minor",
            message=f"out/ size {size_mb:.1f}MB exceeds {limit_mb}MB limit",
            details={"size_mb": round(size_mb, 1)},
            duration_ms=(time.time()-start)*1000,
        )
    return TestResult(
        name="AR-4: Directory size",
        status="PASS",
        message=f"out/ size: {size_mb:.1f}MB (limit: {limit_mb}MB)",
        duration_ms=(time.time()-start)*1000,
    )


# ---------------------------------------------------------------------------
# AR-5: README
# ---------------------------------------------------------------------------

def test_out_readme():
    """AR-5: If out/ has files, it should have a README.md."""
    start = time.time()
    if not OUT_DIR.exists():
        return TestResult(
            name="AR-5: out/ README",
            status="SKIP",
            message="out/ directory not found",
            duration_ms=(time.time()-start)*1000,
        )
    
    has_files = any(OUT_DIR.rglob("*")) and any(f.is_file() for f in OUT_DIR.rglob("*"))
    if not has_files:
        return TestResult(
            name="AR-5: out/ README",
            status="SKIP",
            message="out/ is empty, no README needed",
            duration_ms=(time.time()-start)*1000,
        )
    
    readme = OUT_DIR / "README.md"
    if not readme.exists():
        return TestResult(
            name="AR-5: out/ README",
            status="WARN", severity="minor",
            message="out/ has files but no README.md",
            duration_ms=(time.time()-start)*1000,
        )
    return TestResult(
        name="AR-5: out/ README",
        status="PASS",
        message="README.md present in out/",
        duration_ms=(time.time()-start)*1000,
    )


# ---------------------------------------------------------------------------
# Run all artifact tests
# ---------------------------------------------------------------------------

def run_all() -> TestSuite:
    suite = TestSuite(name="Artifact Output")
    suite.add(test_out_dir_exists())
    suite.add(test_out_dir_gitignored())
    suite.add(test_naming_conventions())
    suite.add(test_no_stale_files())
    suite.add(test_out_dir_size())
    suite.add(test_out_readme())
    return suite


if __name__ == "__main__":
    print_header("ARTIFACT OUTPUT TESTS")
    suite = run_all()
    for r in suite.results:
        status_color = {"PASS": "green", "FAIL": "red", "WARN": "yellow", "SKIP": "cyan"}[r.status]
        print(f"  [{colorize(r.status, status_color)}] {r.name}: {r.message}")
    print(f"\n  Total: {len(suite.results)}, Passed: {suite.passed}, Failed: {suite.failed}, Warnings: {suite.warnings}")
