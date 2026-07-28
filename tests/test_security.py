"""Security & Compliance tests (R0—R2 risk level).

Mandatory checks per backtest-discipline.md and quant-research.md:
- No live-trade instructions (R0 block)
- No API keys, secrets, PII in repo
- No dangerous shell patterns (rm -rf, curl|sh, eval)
- KYC/PII compliance
- MCP OAuth consistency
- Example questions don't contain dangerous patterns
"""

import re
import time
import json
from pathlib import Path
from typing import List, Tuple

from . import (
    REPO_ROOT, OPENCODE_DIR, AGENTS_DIR, SKILLS_DIR, EXAMPLE_DIR,
    TestResult, TestSuite, print_header, colorize,
)


# ---------------------------------------------------------------------------
# SC-1: No hardcoded API keys in repo
# ---------------------------------------------------------------------------

SENSITIVE_PATTERNS: List[Tuple[str, str, List[str]]] = [
    # (pattern description, regex, exemption strings)
    ("API key", r"(?i)(MORNINGSTAR_API_KEY|FACTSET_API_KEY|TUSHARE_TOKEN)=\s*['\"][^'\"]+['\"]",
     ["placeholder", "your_key", "XXXXX", "getenv", "os.environ"]),
    ("Private key", r"(?i)-----BEGIN\s+(RSA|EC|DSA|OPENSSH)\s+PRIVATE\s+KEY-----",
     []),
    ("Auth token literal", r"(?i)(token|apikey|api_key|secret)\s*[:=]\s*['\"][A-Za-z0-9_\-]{20,}['\"]",
     ["placeholder", "example", "test", "xxxxx", "getenv"]),
]


def test_no_hardcoded_keys() -> TestResult:
    """SC-1: No hardcoded API keys, tokens, or secrets in the repo."""
    start = time.time()
    
    scan_dirs = [OPENCODE_DIR, EXAMPLE_DIR, REPO_ROOT / "tests"]
    scan_extensions = [".py", ".md", ".json", ".yaml", ".yml", ".toml", ".cfg", ".ini", ".env.example"]
    
    issues = []
    for scan_dir in scan_dirs:
        if not scan_dir.exists():
            continue
        for ext in scan_extensions:
            for f in scan_dir.rglob(f"*{ext}"):
                # Skip __pycache__ and node_modules
                if "__pycache__" in str(f) or "node_modules" in str(f):
                    continue
                try:
                    text = f.read_text(errors="ignore")
                    for desc, pattern, exemptions in SENSITIVE_PATTERNS:
                        for match in re.finditer(pattern, text):
                            matched_text = match.group(0)
                            # Check exemptions
                            exempted = any(ex in matched_text.lower() for ex in exemptions)
                            if not exempted:
                                rel_path = f.relative_to(REPO_ROOT)
                                # Mask the value, show only the key name
                                masked = re.sub(r"['\"][^'\"]+['\"]", "'***MASKED***'", matched_text[:60])
                                issues.append(f"{rel_path}: {masked}")
                                break  # one issue per file per pattern type
                except (IOError, UnicodeDecodeError):
                    continue
    
    if issues:
        return TestResult(
            name="SC-1: No hardcoded API keys",
            status="FAIL",
            severity="critical",
            message=f"{len(issues)} potential secrets found",
            details={"issues": issues[:15]},
            duration_ms=(time.time() - start) * 1000,
        )
    return TestResult(
        name="SC-1: No hardcoded API keys",
        status="PASS",
        message=f"Scanned {len(scan_dirs)} dirs, no hardcoded secrets",
        duration_ms=(time.time() - start) * 1000,
    )


# ---------------------------------------------------------------------------
# SC-2: No dangerous shell patterns
# ---------------------------------------------------------------------------

DANGEROUS_PATTERNS: List[Tuple[str, str, List[str]]] = [
    ("rm -rf (destructive)", r"\brm\s+-rf\b", ["example", "never", "do not", "caution"]),
    ("curl pipe to shell", r"curl\s+.*\|\s*(bash|sh)", ["example", "never", "do not"]),
    ("eval()", r"\beval\s*\(", ["example", "never", "do not", "ast\.literal_eval"]),
    ("exec()", r"\bexec\s*\(", ["example", "never", "do not"]),
    ("subprocess shell=True", r"shell\s*=\s*True", ["example", "never", "do not", "False"]),
    ("os.system call", r"os\.system\s*\(", ["example", "never", "do not"]),
]


def test_no_dangerous_patterns() -> TestResult:
    """SC-2: No dangerous shell/exec patterns in agent/skill files."""
    start = time.time()
    scan_dirs = [AGENTS_DIR, SKILLS_DIR]
    
    issues = []
    for scan_dir in scan_dirs:
        for f in scan_dir.rglob("*.md"):
            if "node_modules" in str(f) or "__pycache__" in str(f):
                continue
            try:
                text = f.read_text()
                for desc, pattern, exemptions in DANGEROUS_PATTERNS:
                    for match in re.finditer(pattern, text):
                        line_start = max(0, match.start() - 60)
                        line_end = min(len(text), match.end() + 60)
                        context = text[line_start:line_end].lower()
                        if any(ex in context for ex in exemptions):
                            continue
                        rel_path = f.relative_to(REPO_ROOT)
                        issues.append(f"{rel_path}: {desc}")
                        break
            except (IOError, UnicodeDecodeError):
                continue
    
    if issues:
        return TestResult(
            name="SC-2: No dangerous shell patterns",
            status="FAIL",
            severity="critical",
            message=f"{len(issues)} dangerous patterns found",
            details={"issues": issues[:10]},
            duration_ms=(time.time() - start) * 1000,
        )
    return TestResult(
        name="SC-2: No dangerous shell patterns",
        status="PASS",
        message=f"Scanned agents+skills, no dangerous patterns",
        duration_ms=(time.time() - start) * 1000,
    )


# ---------------------------------------------------------------------------
# SC-3: Live-trade deep scan (enhanced from test_integration)
# ---------------------------------------------------------------------------

LIVE_TRADE_PATTERNS: List[Tuple[str, List[str], List[str]]] = [
    # (regex, positive-context exemptions, negative-context keywords that flip meaning)
    (r"place\s+(real\s+)?order",
     ["call auction", "never place", "do not place", "forbidden"],
     ["not", "never", "don't", "do not", "禁止", "严禁"]),
    (r"submit\s+(real\s+)?order",
     ["never submit", "do not submit"],
     ["not", "never", "don't", "do not"]),
    (r"execute\s+(a\s+)?trade",
     ["never execute", "do not execute", "for research only", "not allowed"],
     ["not", "never", "don't", "do not", "does not"]),
    (r"send\s+to\s+broker",
     ["never send", "do not send"],
     ["not", "never", "don't", "do not"]),
    (r"transfer\s+funds",
     ["never transfer", "do not transfer"],
     ["not", "never", "don't", "do not"]),
    (r"connect\s+to\s+(trading|broker)",
     ["never connect", "do not connect"],
     ["not", "never", "don't", "do not"]),
    (r"live\s+trade",
     ["no live", "never", "do not", "research only", "not allowed"],
     ["not", "never", "don't", "do not", "does not"]),
    (r"real\s+money",
     ["not real", "never use", "paper", "simulated"],
     ["not", "never", "don't", "do not"]),
]


def test_live_trade_deep_scan() -> TestResult:
    """SC-3: Deep scan all agent + skill files for live-trade instructions."""
    start = time.time()
    
    scan_targets = []
    for f in AGENTS_DIR.glob("*/agents/*.md"):
        scan_targets.append(f)
    for f in SKILLS_DIR.glob("*/SKILL.md"):
        scan_targets.append(f)
    # Also check instructions
    for f in (OPENCODE_DIR / "instructions").glob("*.md"):
        scan_targets.append(f)
    
    issues = []
    for f in scan_targets:
        try:
            text = f.read_text().lower()
            for pat, pos_exemptions, neg_exemptions in LIVE_TRADE_PATTERNS:
                for match in re.finditer(pat, text):
                    line_start = max(0, match.start() - 100)
                    line_end = min(len(text), match.end() + 100)
                    context = text[line_start:line_end]
                    # Check positive exemptions (explicit safe words in context)
                    if any(ex in context for ex in pos_exemptions):
                        continue
                    # Check negation context — if a negation keyword appears within
                    # 80 chars before the match, the match is a prohibition/disclaimer
                    pre_context = text[max(0, match.start() - 80):match.start()]
                    if any(neg in pre_context for neg in neg_exemptions):
                        continue
                    rel_path = f.relative_to(REPO_ROOT)
                    issues.append(f"{rel_path}: {pat}")
                    break  # one issue per file per pattern
        except (IOError, UnicodeDecodeError):
            continue
    
    if issues:
        return TestResult(
            name="SC-3: Live-trade deep scan",
            status="FAIL",
            severity="critical",
            message=f"{len(issues)} live-trade patterns found",
            details={"issues": issues[:10]},
            duration_ms=(time.time() - start) * 1000,
        )
    return TestResult(
        name="SC-3: Live-trade deep scan",
        status="PASS",
        message=f"Scanned {len(scan_targets)} files, no live-trade patterns",
        duration_ms=(time.time() - start) * 1000,
    )


# ---------------------------------------------------------------------------
# SC-4: KYC/PII check — no PII in agent prompts
# ---------------------------------------------------------------------------

# A-share tickers are 6 digits (SSE) or start with 0/3/002 (SZSE)
ASHARE_TICKER_PATTERN = re.compile(r"\b[036]\d{5}\b")


def _is_ashare_ticker(match_str: str) -> bool:
    """Check if a numeric string is a known A-share stock ticker."""
    return bool(ASHARE_TICKER_PATTERN.match(match_str))


PII_PATTERNS = [
    (r"\b\d{3}-\d{2}-\d{4}\b", "US SSN"),
    (r"\b\d{5,9}\b(?=\s*[-:\]])", "potential numeric ID"),  # too broad, use with care
    (r"credit\s*card\s*number", "credit card reference"),
]


def test_no_pii_in_prompts() -> TestResult:
    """SC-4: No PII (SSN, credit card, personal ID) in agent prompts."""
    start = time.time()
    issues = []
    
    for f in AGENTS_DIR.glob("*/agents/*.md"):
        try:
            text = f.read_text()
            for pat, desc in PII_PATTERNS:
                for match in re.finditer(pat, text):
                    matched_str = match.group(0)
                    # Skip A-share stock tickers (6-digit codes starting with 0/3/6)
                    if desc == "potential numeric ID" and _is_ashare_ticker(matched_str):
                        continue
                    rel_path = f.relative_to(REPO_ROOT)
                    issues.append(f"{rel_path}: potential {desc}")
                    break
        except (IOError, UnicodeDecodeError):
            continue
    
    if issues:
        return TestResult(
            name="SC-4: No PII in agent prompts",
            status="FAIL",
            severity="critical",
            message=f"{len(issues)} potential PII found",
            details={"issues": issues[:10]},
            duration_ms=(time.time() - start) * 1000,
        )
    return TestResult(
        name="SC-4: No PII in agent prompts",
        status="PASS",
        message=f"No PII patterns in agent prompts",
        duration_ms=(time.time() - start) * 1000,
    )


# ---------------------------------------------------------------------------
# SC-5: MCP OAuth consistency
# ---------------------------------------------------------------------------

def test_mcp_config_consistency() -> TestResult:
    """SC-5: MCP servers.json must be consistent with opencode.json."""
    start = time.time()
    
    opencode_json = REPO_ROOT / "opencode.json"
    servers_json = OPENCODE_DIR / "mcp" / "servers.json"
    
    if not servers_json.exists():
        return TestResult(
            name="SC-5: MCP config consistency",
            status="WARN",
            severity="minor",
            message="servers.json not found (may use separate config)",
            duration_ms=(time.time() - start) * 1000,
        )
    
    try:
        oc = json.loads(opencode_json.read_text())
        sj = json.loads(servers_json.read_text())
    except (json.JSONDecodeError, IOError) as e:
        return TestResult(
            name="SC-5: MCP config consistency",
            status="FAIL",
            severity="major",
            message=f"Config parse error: {e}",
            duration_ms=(time.time() - start) * 1000,
        )
    
    mcp_names_in_oc = set(oc.get("mcp", {}).keys())
    mcp_names_in_sj = set(sj.keys()) if isinstance(sj, dict) else set()
    
    only_in_oc = mcp_names_in_oc - mcp_names_in_sj
    only_in_sj = mcp_names_in_sj - mcp_names_in_oc
    
    issues = []
    if only_in_oc:
        issues.append(f"In opencode.json but not servers.json: {only_in_oc}")
    if only_in_sj:
        issues.append(f"In servers.json but not opencode.json: {only_in_sj}")
    
    if issues:
        return TestResult(
            name="SC-5: MCP config consistency",
            status="WARN",
            severity="minor",
            message="; ".join(issues),
            duration_ms=(time.time() - start) * 1000,
        )
    
    return TestResult(
        name="SC-5: MCP config consistency",
        status="PASS",
        message=f"MCP configs consistent: {mcp_names_in_oc} in opencode.json",
        duration_ms=(time.time() - start) * 1000,
    )


# ---------------------------------------------------------------------------
# SC-6: out/ directory security — no sensitive files in output
# ---------------------------------------------------------------------------

def test_out_dir_no_sensitive_files() -> TestResult:
    """SC-6: out/ directory must not contain API keys or PII files."""
    start = time.time()
    out_dir = REPO_ROOT / "out"
    if not out_dir.exists():
        return TestResult(
            name="SC-6: out/ dir security",
            status="SKIP",
            message="out/ directory does not exist",
            duration_ms=(time.time() - start) * 1000,
        )
    
    suspicious_extensions = [".pem", ".key", ".env", ".cred", ".secret"]
    issues = []
    for ext in suspicious_extensions:
        for f in out_dir.rglob(f"*{ext}"):
            issues.append(str(f.relative_to(REPO_ROOT)))
    
    if issues:
        return TestResult(
            name="SC-6: out/ dir security",
            status="FAIL",
            severity="critical",
            message=f"Sensitive files in out/: {issues}",
            duration_ms=(time.time() - start) * 1000,
        )
    return TestResult(
        name="SC-6: out/ dir security",
        status="PASS",
        message="No sensitive file extensions in out/",
        duration_ms=(time.time() - start) * 1000,
    )


# ---------------------------------------------------------------------------
# SC-7: Verify "no real execution" disclaimer exists in key files
# ---------------------------------------------------------------------------

DISCLAIMER_KEYWORDS = ["no live trading", "for research only", "not financial advice",
                       "do not execute", "research only", "not investment advice"]


def test_disclaimer_present() -> TestResult:
    """SC-7: Key instruction files must contain disclaimer about no live trading."""
    start = time.time()
    instruction_files = [
        OPENCODE_DIR / "instructions" / "quant-research.md",
        OPENCODE_DIR / "instructions" / "backtest-discipline.md",
    ]
    
    missing = []
    for f in instruction_files:
        if not f.exists():
            missing.append(f.name)
            continue
        text = f.read_text().lower()
        if not any(kw in text for kw in DISCLAIMER_KEYWORDS):
            missing.append(f.name)
    
    if missing:
        return TestResult(
            name="SC-7: Disclaimer presence check",
            status="WARN",
            severity="minor",
            message=f"Missing disclaimer in: {missing}",
            duration_ms=(time.time() - start) * 1000,
        )
    return TestResult(
        name="SC-7: Disclaimer presence check",
        status="PASS",
        message="All key instruction files have disclaimer",
        duration_ms=(time.time() - start) * 1000,
    )


# ---------------------------------------------------------------------------
# SC-8: Version consistency
# ---------------------------------------------------------------------------

def test_version_consistency() -> TestResult:
    """SC-8: Version strings should be consistent across key files."""
    start = time.time()
    
    # Check README version
    readme = REPO_ROOT / "README.md"
    pyproject = OPENCODE_DIR / "python" / "vibe-trading-quanta" / "pyproject.toml"
    
    issues = []
    if readme.exists():
        readme_text = readme.read_text()
        m = re.search(r"v(\d+\.\d+\.\d+)", readme_text)
        readme_ver = m.group(1) if m else None
    else:
        readme_ver = None
    
    if pyproject.exists():
        pyproject_text = pyproject.read_text()
        m = re.search(r'version\s*=\s*["\'](\d+\.\d+\.\d+)["\']', pyproject_text)
        pyproject_ver = m.group(1) if m else None
    else:
        pyproject_ver = None
    
    if readme_ver and pyproject_ver and readme_ver != pyproject_ver:
        issues.append(f"README says v{readme_ver}, pyproject.toml says v{pyproject_ver}")
    
    if issues:
        return TestResult(
            name="SC-8: Version consistency",
            status="WARN",
            severity="minor",
            message="; ".join(issues),
            duration_ms=(time.time() - start) * 1000,
        )
    return TestResult(
        name="SC-8: Version consistency",
        status="PASS",
        message=f"README={readme_ver or 'N/A'}, pyproject={pyproject_ver or 'N/A'}",
        duration_ms=(time.time() - start) * 1000,
    )


# ---------------------------------------------------------------------------
# Run all security tests
# ---------------------------------------------------------------------------

def run_all() -> TestSuite:
    suite = TestSuite(name="Security & Compliance")
    suite.add(test_no_hardcoded_keys())
    suite.add(test_no_dangerous_patterns())
    suite.add(test_live_trade_deep_scan())
    suite.add(test_no_pii_in_prompts())
    suite.add(test_mcp_config_consistency())
    suite.add(test_out_dir_no_sensitive_files())
    suite.add(test_disclaimer_present())
    suite.add(test_version_consistency())
    return suite


if __name__ == "__main__":
    print_header("SECURITY & COMPLIANCE TESTS")
    suite = run_all()
    for r in suite.results:
        status_color = {"PASS": "green", "FAIL": "red", "WARN": "yellow", "SKIP": "cyan"}[r.status]
        print(f"  [{colorize(r.status, status_color)}] {r.name}: {r.message}")
    print(f"\n  Total: {len(suite.results)}, Passed: {suite.passed}, Failed: {suite.failed}, Warnings: {suite.warnings}")
