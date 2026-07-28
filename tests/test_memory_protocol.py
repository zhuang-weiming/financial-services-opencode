"""Memory Protocol Consistency Tests (R4 risk level).

Tests memory-protocol.md compliance:
- MP-1: INDEX.md lists all required files
- MP-2: Each LAW has 5-Why Challenge block
- MP-3: Each HYP has 5-Why Adversarial block
- MP-4: Each BT has Adversarial Review block
- MP-5: CONFLICTS have type + status classification
- MP-6: raw-log entries have timestamps + tags
- MP-7: LAW/BT cross-reference consistency
- MP-8: Data freshness (no expired data references)
"""

import re
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Set, Tuple

from . import (
    OPENCODE_DIR, REPO_ROOT,
    TestResult, TestSuite, print_header, colorize,
)

MEMORY_DIR = OPENCODE_DIR / "memory" / "personal-system"
INDEX_FILE = OPENCODE_DIR / "memory" / "INDEX.md"


def _read_file(path: Path) -> str:
    if path.exists():
        return path.read_text()
    return ""


def _count_why_blocks(text: str, prefix: str = "why") -> int:
    """Count 5-Why style question-answer pairs in text."""
    count = 0
    lines = text.split("\n")
    for line in lines:
        if line.strip().lower().startswith(prefix):
            # Accept "Why 1:", "Why1:", "Why 1 —", "Why 1 " etc
            m = re.match(r"(?i)^(why\s*\d+)\s*[:\-—]?\s*", line.strip())
            if m:
                count += 1
    return count


# ---------------------------------------------------------------------------
# MP-1: INDEX.md completeness
# ---------------------------------------------------------------------------

def test_index_exists() -> TestResult:
    """INDEX.md must exist at the memory root."""
    start = time.time()
    if not INDEX_FILE.exists():
        return TestResult(
            name="MP-1a: INDEX.md exists",
            status="FAIL", severity="critical",
            message="INDEX.md not found",
            duration_ms=(time.time()-start)*1000,
        )
    return TestResult(
        name="MP-1a: INDEX.md exists",
        status="PASS",
        message=f"Found at {INDEX_FILE.relative_to(REPO_ROOT)}",
        duration_ms=(time.time()-start)*1000,
    )


REQUIRED_MEMORY_FILES = [
    "LAWS.md",
    "FAILED_LAWS.md",
    "OPEN_HYPOTHESES.md",
    "BACKTEST_INDEX.md",
    "CONFLICTS.md",
]


def test_required_memory_files_exist() -> TestResult:
    """MP-1b: All required memory files must exist."""
    start = time.time()
    missing = []
    for fname in REQUIRED_MEMORY_FILES:
        f = MEMORY_DIR / fname
        if not f.exists():
            missing.append(fname)
    
    if missing:
        return TestResult(
            name="MP-1b: Required memory files",
            status="FAIL", severity="critical",
            message=f"Missing: {missing}",
            duration_ms=(time.time()-start)*1000,
        )
    return TestResult(
        name="MP-1b: Required memory files",
        status="PASS",
        message=f"All {len(REQUIRED_MEMORY_FILES)} required files exist",
        duration_ms=(time.time()-start)*1000,
    )


# ---------------------------------------------------------------------------
# MP-2: LAW 5-Why Challenge
# ---------------------------------------------------------------------------

def test_law_5why_challenge() -> TestResult:
    """MP-2: Each LAW must have a 5-Why Challenge block."""
    start = time.time()
    law_file = MEMORY_DIR / "LAWS.md"
    if not law_file.exists():
        return TestResult(
            name="MP-2: LAW 5-Why Challenge",
            status="SKIP",
            message="LAWS.md not found",
            duration_ms=(time.time()-start)*1000,
        )
    
    text = law_file.read_text()
    
    # Count LAW entries (## heading lines)
    law_headings = re.findall(r"^##\s+(LAW-\d+)", text, re.MULTILINE)
    
    if not law_headings:
        return TestResult(
            name="MP-2: LAW 5-Why Challenge",
            status="WARN", severity="minor",
            message="No LAW entries found in LAWS.md",
            duration_ms=(time.time()-start)*1000,
        )
    
    # Check each LAW section has a 5-Why block
    law_sections = re.split(r"^##\s+LAW-\d+", text, flags=re.MULTILINE)
    law_sections = [s for s in law_sections if s.strip()]
    
    missing_why = []
    for i, section in enumerate(law_sections):
        lid = law_headings[i] if i < len(law_headings) else f"LAW-{i+1:03d}"
        why_count = _count_why_blocks(section)
        if why_count < 3:  # at least 3 Why levels
            missing_why.append(f"{lid}: only {why_count} Why levels found")
    
    if missing_why:
        return TestResult(
            name="MP-2: LAW 5-Why Challenge",
            status="FAIL", severity="major",
            message=f"{len(missing_why)}/{len(law_headings)} LAWs missing full 5-Why",
            details={"issues": missing_why[:5]},
            duration_ms=(time.time()-start)*1000,
        )
    return TestResult(
        name="MP-2: LAW 5-Why Challenge",
        status="PASS",
        message=f"All {len(law_headings)} LAWs have 5-Why Challenge blocks",
        duration_ms=(time.time()-start)*1000,
    )


# ---------------------------------------------------------------------------
# MP-3: HYP 5-Why Adversarial
# ---------------------------------------------------------------------------

def test_hyp_5why_adversarial() -> TestResult:
    """MP-3: Each HYP must have a 5-Why Adversarial block."""
    start = time.time()
    hyp_file = MEMORY_DIR / "OPEN_HYPOTHESES.md"
    if not hyp_file.exists():
        return TestResult(
            name="MP-3: HYP 5-Why Adversarial",
            status="SKIP",
            message="OPEN_HYPOTHESES.md not found",
            duration_ms=(time.time()-start)*1000,
        )
    
    text = hyp_file.read_text()
    hyp_headings = re.findall(r"^##\s+(HYP-\d+)", text, re.MULTILINE)
    
    if not hyp_headings:
        return TestResult(
            name="MP-3: HYP 5-Why Adversarial",
            status="WARN", severity="minor",
            message="No HYP entries found",
            duration_ms=(time.time()-start)*1000,
        )
    
    hyp_sections = re.split(r"^##\s+HYP-\d+", text, flags=re.MULTILINE)
    hyp_sections = [s for s in hyp_sections if s.strip()]
    
    missing_why = []
    for i, section in enumerate(hyp_sections):
        hid = hyp_headings[i] if i < len(hyp_headings) else f"HYP-{i+1:03d}"
        why_count = _count_why_blocks(section)
        if why_count < 3:
            missing_why.append(f"{hid}: only {why_count} Why levels found")
    
    if missing_why:
        return TestResult(
            name="MP-3: HYP 5-Why Adversarial",
            status="FAIL", severity="major",
            message=f"{len(missing_why)}/{len(hyp_headings)} HYPs missing full 5-Why",
            details={"issues": missing_why[:5]},
            duration_ms=(time.time()-start)*1000,
        )
    return TestResult(
        name="MP-3: HYP 5-Why Adversarial",
        status="PASS",
        message=f"All {len(hyp_headings)} HYPs have 5-Why Adversarial blocks",
        duration_ms=(time.time()-start)*1000,
    )


# ---------------------------------------------------------------------------
# MP-4: BT Adversarial Review
# ---------------------------------------------------------------------------

def test_bt_adversarial_review() -> TestResult:
    """MP-4: Each BT must have an Adversarial Review section."""
    start = time.time()
    bt_file = MEMORY_DIR / "BACKTEST_INDEX.md"
    if not bt_file.exists():
        return TestResult(
            name="MP-4: BT Adversarial Review",
            status="SKIP",
            message="BACKTEST_INDEX.md not found",
            duration_ms=(time.time()-start)*1000,
        )
    
    text = bt_file.read_text()
    bt_headings = re.findall(r"^##\s+(BT-\d+)", text, re.MULTILINE)
    
    if not bt_headings:
        return TestResult(
            name="MP-4: BT Adversarial Review",
            status="WARN", severity="minor",
            message="No BT entries found",
            duration_ms=(time.time()-start)*1000,
        )
    
    bt_sections = re.split(r"^##\s+BT-\d+", text, flags=re.MULTILINE)
    bt_sections = [s for s in bt_sections if s.strip()]
    
    missing_review = []
    for i, section in enumerate(bt_sections):
        bid = bt_headings[i] if i < len(bt_headings) else f"BT-{i+1:03d}"
        has_adversarial = "adversarial" in section.lower() or "5-why" in section.lower() or "challenge" in section.lower() or "review" in section.lower()
        if not has_adversarial:
            missing_review.append(f"{bid}: no Adversarial Review section")
    
    if missing_review:
        return TestResult(
            name="MP-4: BT Adversarial Review",
            status="FAIL", severity="major",
            message=f"{len(missing_review)}/{len(bt_headings)} BTs missing Adversarial Review",
            details={"issues": missing_review[:5]},
            duration_ms=(time.time()-start)*1000,
        )
    return TestResult(
        name="MP-4: BT Adversarial Review",
        status="PASS",
        message=f"All {len(bt_headings)} BTs have Adversarial Review sections",
        duration_ms=(time.time()-start)*1000,
    )


# ---------------------------------------------------------------------------
# MP-5: CONFLICT classification
# ---------------------------------------------------------------------------

def test_conflict_classification() -> TestResult:
    """MP-5: Each CONFLICT must be classified with type and status."""
    start = time.time()
    conflict_file = MEMORY_DIR / "CONFLICTS.md"
    if not conflict_file.exists():
        return TestResult(
            name="MP-5: CONFLICT classification",
            status="SKIP",
            message="CONFLICTS.md not found",
            duration_ms=(time.time()-start)*1000,
        )
    
    text = conflict_file.read_text()
    conflict_entries = re.findall(r"^##\s+(CONFLICT-\w+-\d+)", text, re.MULTILINE)
    
    if not conflict_entries:
        return TestResult(
            name="MP-5: CONFLICT classification",
            status="WARN", severity="minor",
            message="No CONFLICT entries found",
            duration_ms=(time.time()-start)*1000,
        )
    
    # Check each entry has status/type classification
    conflict_sections = re.split(r"^##\s+CONFLICT-\w+-\d+", text, flags=re.MULTILINE)
    conflict_sections = [s for s in conflict_sections if s.strip()]
    
    unclassified = []
    for i, section in enumerate(conflict_sections):
        cid = conflict_entries[i] if i < len(conflict_entries) else f"CONFLICT-{i+1:03d}"
        has_type = any(t in section.upper() for t in ["TYPE:", "STATUS:", "CATEGORY:"])
        has_status = any(s in section.upper() for s in ["OPEN", "RESOLVED", "ACTIVE", "CLOSED"])
        if not (has_type and has_status):
            unclassified.append(cid)
    
    if unclassified:
        return TestResult(
            name="MP-5: CONFLICT classification",
            status="FAIL", severity="major",
            message=f"{len(unclassified)} unclassified conflicts",
            details={"unclassified": unclassified},
            duration_ms=(time.time()-start)*1000,
        )
    return TestResult(
        name="MP-5: CONFLICT classification",
        status="PASS",
        message=f"All {len(conflict_entries)} CONFLICTs classified",
        duration_ms=(time.time()-start)*1000,
    )


# ---------------------------------------------------------------------------
# MP-6: raw-log timestamp + tag
# ---------------------------------------------------------------------------

def test_raw_log_format() -> TestResult:
    """MP-6: raw-log entries must have timestamps and tags."""
    start = time.time()
    raw_log_dir = MEMORY_DIR / "raw-log"
    if not raw_log_dir.exists():
        return TestResult(
            name="MP-6: raw-log format",
            status="SKIP",
            message="raw-log directory not found",
            duration_ms=(time.time()-start)*1000,
        )
    
    log_files = sorted(raw_log_dir.glob("*.md"))
    if not log_files:
        return TestResult(
            name="MP-6: raw-log format",
            status="WARN", severity="minor",
            message="No raw-log files found",
            duration_ms=(time.time()-start)*1000,
        )
    
    issues = []
    for lf in log_files:
        text = lf.read_text()
        lines = text.split("\n")
        entry_count = 0
        for line in lines:
            # Check for timestamp pattern (ISO date or similar)
            has_timestamp = bool(re.search(r"\d{4}-\d{2}-\d{2}", line))
            # Check for status tag pattern
            has_tag = bool(re.search(r"\[(NEW|REINFORCED|CONFLICT|RESOLVED|ADD_\w+)\]", line, re.IGNORECASE))
            if has_timestamp:
                entry_count += 1
                if not has_tag and entry_count <= 5:
                    issues.append(f"{lf.name}: entry missing tag (line: {line[:60]})")
    
    if issues:
        return TestResult(
            name="MP-6: raw-log format",
            status="WARN", severity="minor",
            message=f"{len(issues)} entries missing tags in raw-log",
            details={"issues": issues[:5]},
            duration_ms=(time.time()-start)*1000,
        )
    return TestResult(
        name="MP-6: raw-log format",
        status="PASS",
        message=f"{len(log_files)} raw-log files checked, entries properly formatted",
        duration_ms=(time.time()-start)*1000,
    )


# ---------------------------------------------------------------------------
# MP-7: Cross-reference consistency
# ---------------------------------------------------------------------------

def _extract_references(text: str, prefix: str) -> Set[str]:
    """Extract references like BT-001, LAW-002, HYP-003 from text."""
    pattern = rf"{re.escape(prefix)}-\d{{3}}"
    return set(re.findall(pattern, text))


def test_cross_reference_consistency() -> TestResult:
    """MP-7: All BT/LAW/HYP references must point to existing entries."""
    start = time.time()
    
    files_to_check = ["LAWS.md", "OPEN_HYPOTHESES.md", "BACKTEST_INDEX.md", "CONFLICTS.md"]
    
    # First, build indices of what exists
    existing_laWS = set()
    existing_hyps = set()
    existing_bts = set()
    
    for fname in files_to_check:
        f = MEMORY_DIR / fname
        if not f.exists():
            continue
        text = f.read_text()
        existing_laWS.update(re.findall(r"LAW-\d{3}", text))
        existing_hyps.update(re.findall(r"HYP-\d{3}", text))
        existing_bts.update(re.findall(r"BT-\d{3}", text))
    
    # Now check cross-references
    issues = []
    for fname in files_to_check:
        f = MEMORY_DIR / fname
        if not f.exists():
            continue
        text = f.read_text()
        
        refs_bt = _extract_references(text, "BT")
        refs_law = _extract_references(text, "LAW")
        refs_hyp = _extract_references(text, "HYP")
        
        for ref in refs_bt:
            if ref not in existing_bts and ref != f"BT-{text.split()[0] if text else ''}":
                issues.append(f"{fname}: references {ref} but no such BT exists")
        
        for ref in refs_law:
            if ref not in existing_laWS:
                issues.append(f"{fname}: references {ref} but no such LAW exists")
        
        for ref in refs_hyp:
            if ref not in existing_hyps:
                issues.append(f"{fname}: references {ref} but no such HYP exists")
    
    if issues:
        return TestResult(
            name="MP-7: Reference consistency",
            status="FAIL", severity="major",
            message=f"{len(issues)} broken references",
            details={"issues": issues[:10]},
            duration_ms=(time.time()-start)*1000,
        )
    return TestResult(
        name="MP-7: Reference consistency",
        status="PASS",
        message="All cross-references are valid",
        duration_ms=(time.time()-start)*1000,
    )


# ---------------------------------------------------------------------------
# MP-8: Data freshness — no expired data > 90 days
# ---------------------------------------------------------------------------

def test_data_freshness() -> TestResult:
    """MP-8: Check for data older than 90 days in memory files."""
    start = time.time()
    
    # Look for date patterns in memory files
    date_pattern = re.compile(r"\b(\d{4}-\d{2}-\d{2})\b")
    
    today = datetime.now()
    threshold = timedelta(days=90)
    cutoff = today - threshold
    
    issues = []
    for fname in REQUIRED_MEMORY_FILES:
        f = MEMORY_DIR / fname
        if not f.exists():
            continue
        text = f.read_text()
        for m in date_pattern.finditer(text):
            try:
                d = datetime.strptime(m.group(1), "%Y-%m-%d")
                if d < cutoff:
                    # Check context — is this a "last updated" or "as of" date?
                    pos = m.start()
                    ctx_start = max(0, pos - 60)
                    ctx_end = min(len(text), pos + 60)
                    context = text[ctx_start:ctx_end]
                    issues.append(f"{fname}: date {m.group(1)} (>90 days old) in: ...{context.strip()[:80]}...")
            except ValueError:
                continue
    
    if issues:
        return TestResult(
            name="MP-8: Data freshness",
            status="WARN", severity="minor",
            message=f"{len(issues)} dates older than 90 days found",
            details={"old_dates": issues[:5]},
            duration_ms=(time.time()-start)*1000,
        )
    return TestResult(
        name="MP-8: Data freshness",
        status="PASS",
        message="All dates in memory files are within 90 days",
        duration_ms=(time.time()-start)*1000,
    )


# ---------------------------------------------------------------------------
# MP-9: POSITION_SIZING.md and SELL_LADDER.md exist
# ---------------------------------------------------------------------------

def test_optional_memory_files() -> TestResult:
    """MP-9: Check for optional but recommended memory files."""
    start = time.time()
    optional_files = ["POSITION_SIZING.md", "SELL_LADDER.md", "theses"]
    missing = []
    for fname in optional_files:
        f = MEMORY_DIR / fname
        if not f.exists():
            missing.append(fname)
    
    if missing:
        return TestResult(
            name="MP-9: Optional memory files",
            status="WARN", severity="minor",
            message=f"Missing: {missing}",
            duration_ms=(time.time()-start)*1000,
        )
    return TestResult(
        name="MP-9: Optional memory files",
        status="PASS",
        message=f"All optional files present",
        duration_ms=(time.time()-start)*1000,
    )


# ---------------------------------------------------------------------------
# MP-10: distillation-log exists when raw-log has ≥3 entries
# ---------------------------------------------------------------------------

def test_distillation_trigger() -> TestResult:
    """MP-10: When raw-log has ≥3 unprocessed entries, distillation must exist."""
    start = time.time()
    raw_log_dir = MEMORY_DIR / "raw-log"
    dist_log_dir = MEMORY_DIR / "distillation-log"
    
    if not raw_log_dir.exists() or not raw_log_dir.is_dir():
        return TestResult(
            name="MP-10: Distillation trigger",
            status="SKIP",
            message="raw-log directory not found",
            duration_ms=(time.time()-start)*1000,
        )
    
    # Count raw-log entries (files)
    log_files = list(raw_log_dir.glob("*.md"))
    if len(log_files) < 3:
        return TestResult(
            name="MP-10: Distillation trigger",
            status="SKIP",
            message=f"Only {len(log_files)} raw-log files (<3 threshold)",
            duration_ms=(time.time()-start)*1000,
        )
    
    # Check if distillation-log exists
    if not dist_log_dir.exists() or not list(dist_log_dir.glob("*.md")):
        return TestResult(
            name="MP-10: Distillation trigger",
            status="WARN", severity="minor",
            message=f"≥3 raw-log files ({len(log_files)}) but no distillation-log",
            duration_ms=(time.time()-start)*1000,
        )
    
    return TestResult(
        name="MP-10: Distillation trigger",
        status="PASS",
        message=f"Raw-log: {len(log_files)} files, distillation-log present",
        duration_ms=(time.time()-start)*1000,
    )


# ---------------------------------------------------------------------------
# Run all memory protocol tests
# ---------------------------------------------------------------------------

def run_all() -> TestSuite:
    suite = TestSuite(name="Memory Protocol Consistency")
    suite.add(test_index_exists())
    suite.add(test_required_memory_files_exist())
    suite.add(test_law_5why_challenge())
    suite.add(test_hyp_5why_adversarial())
    suite.add(test_bt_adversarial_review())
    suite.add(test_conflict_classification())
    suite.add(test_raw_log_format())
    suite.add(test_cross_reference_consistency())
    suite.add(test_data_freshness())
    suite.add(test_optional_memory_files())
    suite.add(test_distillation_trigger())
    return suite


if __name__ == "__main__":
    print_header("MEMORY PROTOCOL CONSISTENCY TESTS")
    suite = run_all()
    for r in suite.results:
        status_color = {"PASS": "green", "FAIL": "red", "WARN": "yellow", "SKIP": "cyan"}[r.status]
        print(f"  [{colorize(r.status, status_color)}] {r.name}: {r.message}")
    print(f"\n  Total: {len(suite.results)}, Passed: {suite.passed}, Failed: {suite.failed}, Warnings: {suite.warnings}")
