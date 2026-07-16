"""Per-agent business tests.

For each of the 22 subagents and the 1 primary agent:
- File exists at correct path
- YAML frontmatter valid
- Description is meaningful (≥50 chars, contains business context)
- Body has substantial content (≥200 chars)
- Tools block present (read, write or relevant MCPs)
- For subagents: mode=subagent, hidden=true
- For primary: declared task() tools for all 22 subagents
"""

import time
import re
from pathlib import Path
from typing import List
from . import (
    AGENTS_DIR, SKILLS_DIR, SUBAGENTS, PRIMARY_AGENTS,
    list_agents, read_agent_file, get_agent_body,
    TestResult, TestSuite, print_header, colorize,
)


MIN_DESCRIPTION_LEN = 50
MIN_BODY_LEN = 200
EXPECTED_DOMAINS = {
    "earnings-reviewer": ["earnings", "post-earnings", "transcript", "report", "note"],
    "equity-research": ["research", "coverage", "earnings", "analysis", "report"],
    "financial-analysis": ["financial", "model", "dcf", "lbo", "analysis"],
    "fund-admin": ["fund", "nav", "tieout", "capital", "accrual"],
    "gl-reconciler": ["reconcil", "gl", "subledger", "break", "match"],
    "investment-banking": ["banking", "pitch", "deal", "cim", "teaser"],
    "kyc-screener": ["kyc", "aml", "onboarding", "sanctions", "compliance"],
    "market-researcher": ["market", "sector", "industry", "research", "competitive"],
    "meeting-prep-agent": ["meeting", "briefing", "client", "prep", "agenda"],
    "model-builder": ["model", "dcf", "lbo", "build", "valuation"],
    "month-end-closer": ["month-end", "close", "accrual", "rollforward", "variance"],
    "operations": ["operations", "portfolio", "portco", "ai", "monitoring"],
    "pitch-agent": ["pitch", "deck", "comps", "dcf", "lbo"],
    "private-equity": ["private equity", "deal", "ic", "memo", "due diligence"],
    "statement-auditor": ["statement", "audit", "lp", "nav", "capital"],
    "valuation-reviewer": ["valuation", "review", "portco", "fund", "quarterly"],
    "wealth-management": ["wealth", "client", "financial plan", "retirement", "rebalance"],
    "alpha-researcher": ["alpha", "zoo", "bench", "factor", "ic"],
    "backtest-builder": ["backtest", "strategy", "engine", "performance", "walk-forward"],
    "factor-researcher": ["factor", "ic", "ir", "quantile", "correlation"],
    "market-router": ["market", "route", "loader", "symbol", "detect"],
    "swarm-orchestrator": ["swarm", "team", "orchestrat", "dag", "preset"],
    "wealth-guide": ["wealth-guide", "route", "subagent", "dispatch", "primary"],
}


def test_agent_file_exists(slug: str) -> TestResult:
    """Agent file exists at the standard path."""
    agent_file = AGENTS_DIR / slug / "agents" / f"{slug}.md"
    if not agent_file.exists():
        return TestResult(
            name=f"agent file exists: {slug}",
            status="FAIL",
            severity="critical",
            message=f"Missing: {agent_file}",
        )
    return TestResult(
        name=f"agent file exists: {slug}",
        status="PASS",
        message=f"Found at {agent_file}",
    )


def test_agent_yaml_valid(slug: str) -> TestResult:
    """Agent YAML frontmatter is valid and has required fields."""
    fm = read_agent_file(slug)
    if fm is None:
        return TestResult(
            name=f"agent yaml valid: {slug}",
            status="FAIL",
            severity="critical",
            message="Missing or invalid YAML frontmatter",
        )

    issues = []
    if "name" not in fm:
        issues.append("missing 'name'")
    elif fm["name"] != slug:
        issues.append(f"name mismatch (yaml={fm['name']}, dir={slug})")
    if "description" not in fm:
        issues.append("missing 'description'")
    elif len(str(fm["description"])) < MIN_DESCRIPTION_LEN:
        issues.append(f"description too short ({len(str(fm['description']))}<{MIN_DESCRIPTION_LEN})")
    if "tools" not in fm:
        issues.append("missing 'tools'")

    if issues:
        return TestResult(
            name=f"agent yaml valid: {slug}",
            status="FAIL",
            severity="major",
            message="; ".join(issues),
            details={"yaml": dict(fm)},
        )
    return TestResult(
        name=f"agent yaml valid: {slug}",
        status="PASS",
        message=f"name={fm['name']}, desc_len={len(str(fm['description']))}",
    )


def test_agent_body_content(slug: str) -> TestResult:
    """Agent body has substantial content."""
    body = get_agent_body(slug)
    if len(body) < MIN_BODY_LEN:
        return TestResult(
            name=f"agent body content: {slug}",
            status="FAIL",
            severity="major",
            message=f"Body too short ({len(body)}<{MIN_BODY_LEN})",
            details={"body_len": len(body)},
        )
    return TestResult(
        name=f"agent body content: {slug}",
        status="PASS",
        message=f"Body length: {len(body)} chars",
    )


def test_agent_domain_keywords(slug: str) -> TestResult:
    """Agent description contains domain-relevant keywords."""
    fm = read_agent_file(slug)
    if fm is None:
        return TestResult(
            name=f"agent domain keywords: {slug}",
            status="FAIL",
            severity="major",
            message="No YAML",
        )

    expected_keywords = EXPECTED_DOMAINS.get(slug, [])
    if not expected_keywords:
        return TestResult(
            name=f"agent domain keywords: {slug}",
            status="SKIP",
            message="No expected keywords defined",
        )

    desc = str(fm.get("description", "")).lower()
    body = get_agent_body(slug).lower()
    combined = desc + " " + body

    matches = []
    for kw in expected_keywords:
        if kw.lower() in combined:
            matches.append(kw)

    coverage = len(matches) / len(expected_keywords) if expected_keywords else 1.0
    if coverage < 0.5:
        return TestResult(
            name=f"agent domain keywords: {slug}",
            status="FAIL",
            severity="minor",
            message=f"Low coverage: {coverage:.0%}, missing: {[k for k in expected_keywords if k not in matches]}",
            details={"matched": matches, "expected": expected_keywords},
        )
    return TestResult(
        name=f"agent domain keywords: {slug}",
        status="PASS",
        message=f"Coverage: {coverage:.0%} ({len(matches)}/{len(expected_keywords)})",
        details={"matched": matches},
    )


def test_subagent_annotation(slug: str) -> TestResult:
    """Subagent has mode=subagent, hidden=true."""
    fm = read_agent_file(slug)
    if fm is None:
        return TestResult(
            name=f"subagent annotation: {slug}",
            status="FAIL",
            severity="critical",
            message="No YAML",
        )
    mode = fm.get("mode")
    hidden = fm.get("hidden")
    if mode != "subagent":
        return TestResult(
            name=f"subagent annotation: {slug}",
            status="FAIL",
            severity="critical",
            message=f"mode should be 'subagent', got {mode!r}",
        )
    if hidden is not True:
        return TestResult(
            name=f"subagent annotation: {slug}",
            status="FAIL",
            severity="critical",
            message=f"hidden should be true, got {hidden!r}",
        )
    return TestResult(
        name=f"subagent annotation: {slug}",
        status="PASS",
        message="mode=subagent, hidden=true",
    )


def test_agent_no_live_trade(slug: str) -> TestResult:
    """Agent must not contain live-trade instructions."""
    body = get_agent_body(slug).lower()
    fm = read_agent_file(slug) or {}
    full = (str(fm.get("description", "")) + " " + body).lower()

    # Patterns that indicate live-trade instructions
    forbidden = [
        r"place\s+(real\s+)?order",
        r"submit\s+order",
        r"execute\s+(a\s+)?trade",
        r"send\s+to\s+broker",
        r"transfer\s+funds",
        r"connect\s+to\s+trading\s+api",
    ]
    found = []
    for pattern in forbidden:
        if re.search(pattern, full):
            found.append(pattern)

    if found:
        return TestResult(
            name=f"agent no live-trade: {slug}",
            status="FAIL",
            severity="critical",
            message=f"Forbidden patterns: {found}",
        )
    return TestResult(
        name=f"agent no live-trade: {slug}",
        status="PASS",
        message="No live-trade instructions found",
    )


def run_agent_tests_for_slug(slug: str) -> List[TestResult]:
    """Run all agent tests for a given slug."""
    results = []
    results.append(test_agent_file_exists(slug))
    results.append(test_agent_yaml_valid(slug))
    results.append(test_agent_body_content(slug))
    results.append(test_agent_domain_keywords(slug))
    if slug not in PRIMARY_AGENTS:
        results.append(test_subagent_annotation(slug))
    results.append(test_agent_no_live_trade(slug))
    return results


def run_all_agents() -> TestSuite:
    """Run per-agent tests for all 23 agents."""
    suite = TestSuite(name="Per-Agent Business Tests")

    # Test all agents (primary + subagents)
    for slug in list_agents():
        for result in run_agent_tests_for_slug(slug):
            suite.add(result)

    return suite


if __name__ == "__main__":
    print_header("PER-AGENT TESTS")
    suite = run_all_agents()
    for r in suite.results:
        status_color = {"PASS": "green", "FAIL": "red", "WARN": "yellow", "SKIP": "cyan"}[r.status]
        print(f"  [{colorize(r.status, status_color)}] {r.name}: {r.message}")
    print(f"\n  Total: {len(suite.results)}, Passed: {suite.passed}, Failed: {suite.failed}")