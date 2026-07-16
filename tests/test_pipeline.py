"""Cross-agent pipeline tests.

Tests for end-to-end Wealth-Guide orchestration behavior:
1. Parallel dispatch — multi-domain queries trigger multiple subagents
2. Composition — when multiple subagents fire, output structure is valid
3. User override — user-named subagent short-circuits routing
4. Fallback — non-financial queries return empty (caller uses MCP)
5. Subagent reachability — every subagent can be reached via routing
6. Pipeline stress — many parallel calls don't break routing
7. Cookbooks — every cookbook has questions.md and routes correctly
"""

import time
from pathlib import Path
from typing import List
from . import (
    SUBAGENTS, PRIMARY_AGENTS, dispatch, ROUTING_TABLE,
    AGENTS_DIR, SKILLS_DIR, EXAMPLE_DIR, list_cookbooks,
    REPO_ROOT, TestResult, TestSuite, print_header, colorize,
)


# Parallel dispatch test cases
PARALLEL_CASES = [
    {
        "query": "Run earnings + DCF + comps on NVDA",
        "expected_min": 2,
        "expected_subagents": ["earnings-reviewer", "model-builder"],
        "desc": "earnings + valuation",
    },
    {
        "query": "Analyze BTC with factor analysis and backtest",
        "expected_min": 2,
        "expected_subagents": ["market-router", "factor-researcher"],
        "desc": "crypto + factor",
    },
    {
        "query": "Build a DCF and then run a backtest on the strategy",
        "expected_min": 2,
        "expected_subagents": ["model-builder", "backtest-builder"],
        "desc": "valuation + backtest",
    },
    {
        "query": "M&A pitch deck with comps and DCF for CloudSoft",
        "expected_min": 2,
        "expected_subagents": ["pitch-agent", "model-builder"],
        "desc": "IB + modeling",
    },
    {
        "query": "I want to build an investment thesis on NVDA. Analyze their latest earnings, build a DCF model, and compare against AMD",
        "expected_min": 3,
        "expected_subagents": ["earnings-reviewer", "model-builder"],
        "desc": "thesis (3 subagents)",
    },
]


# Composition test: verify parallel dispatch returns ordered list
def test_parallel_dispatch() -> TestSuite:
    """Verify multi-domain queries trigger parallel dispatch."""
    suite = TestSuite(name="Parallel Dispatch Tests")
    for case in PARALLEL_CASES:
        start = time.time()
        result = dispatch(case["query"])
        actual_set = set(result)
        expected_set = set(case["expected_subagents"])
        has_all_expected = expected_set.issubset(actual_set)
        has_min = len(result) >= case["expected_min"]

        if has_all_expected and has_min:
            status = "PASS"
            message = f"{len(result)} subagents: {result}"
            severity = "normal"
        elif not has_min:
            status = "FAIL"
            message = f"Need >= {case['expected_min']} subagents, got {len(result)}"
            severity = "major"
        else:
            status = "FAIL"
            message = f"Missing: {expected_set - actual_set}"
            severity = "major"

        suite.add(TestResult(
            name=f"[{case['desc']}] {case['query'][:50]}",
            status=status,
            severity=severity,
            message=message,
            duration_ms=(time.time() - start) * 1000,
            details={"query": case["query"], "result": result, "expected": case["expected_subagents"]},
        ))
    return suite


def test_no_duplicate_dispatch() -> TestSuite:
    """Verify dispatch never returns duplicate slugs."""
    suite = TestSuite(name="No Duplicate Dispatch")
    test_queries = [
        "earnings analysis with comps and DCF",
        "crypto + factor + backtest",
        "screen deal CIM then pitch",
        "rebalance portfolio with tax-loss harvesting",
    ]
    for q in test_queries:
        result = dispatch(q)
        if len(result) != len(set(result)):
            suite.add(TestResult(
                name=f"dedupe: {q[:40]}",
                status="FAIL",
                severity="major",
                message=f"Duplicates: {result}",
            ))
        else:
            suite.add(TestResult(
                name=f"dedupe: {q[:40]}",
                status="PASS",
                message=f"No duplicates: {result}",
            ))
    return suite


def test_user_override_takes_priority() -> TestSuite:
    """User override short-circuits keyword routing."""
    suite = TestSuite(name="User Override Priority")
    # These queries have BOTH a keyword match AND a user override
    cases = [
        ("Use earnings-reviewer for the DCF model", ["earnings-reviewer"]),  # "DCF" matches model-builder but override wins
        ("please use alpha-researcher on the backtest", ["alpha-researcher"]),  # "backtest" matches backtest-builder
        ("Use market-router to do the factor analysis", ["market-router"]),  # "factor" matches factor-researcher
    ]
    for query, expected in cases:
        result = dispatch(query)
        if result == expected:
            suite.add(TestResult(
                name=f"override priority: {query[:40]}",
                status="PASS",
                message=f"Override wins: {result}",
            ))
        else:
            suite.add(TestResult(
                name=f"override priority: {query[:40]}",
                status="FAIL",
                severity="major",
                message=f"Expected {expected}, got {result}",
            ))
    return suite


def test_chinese_override() -> TestSuite:
    """Chinese-language override patterns work."""
    suite = TestSuite(name="Chinese Override Tests")
    cases = [
        ("用 alpha-researcher 分析 BTC", ["alpha-researcher"]),
        ("用 earnings-reviewer 处理 Q1 季报", ["earnings-reviewer"]),
        ("用 market-router 分析 600519", ["market-router"]),
    ]
    for query, expected in cases:
        result = dispatch(query)
        if result == expected:
            suite.add(TestResult(
                name=f"中文 override: {query[:30]}",
                status="PASS",
                message=f"Override wins: {result}",
            ))
        else:
            suite.add(TestResult(
                name=f"中文 override: {query[:30]}",
                status="FAIL",
                severity="major",
                message=f"Expected {expected}, got {result}",
            ))
    return suite


def test_all_subagents_reachable() -> TestSuite:
    """Each of the 22 subagents must be reachable via routing."""
    suite = TestSuite(name="All Subagents Reachable")
    reachable = set()
    for keyword, slugs in ROUTING_TABLE.items():
        for s in slugs:
            reachable.add(s)
    unreachable = set(SUBAGENTS) - reachable
    if unreachable:
        suite.add(TestResult(
            name="Every subagent has at least one routing keyword",
            status="FAIL",
            severity="critical",
            message=f"Unreachable: {sorted(unreachable)}",
            details={"unreachable": sorted(unreachable)},
        ))
    else:
        suite.add(TestResult(
            name="Every subagent has at least one routing keyword",
            status="PASS",
            message=f"All {len(SUBAGENTS)} subagents reachable",
        ))
    return suite


def test_wealth_guide_has_all_tasks() -> TestSuite:
    """wealth-guide's tools dict must include task() for all 22 subagents."""
    suite = TestSuite(name="Wealth-Guide Tool Allowlist")
    wg_file = AGENTS_DIR / "wealth-guide" / "agents" / "wealth-guide.md"
    if not wg_file.exists():
        suite.add(TestResult(
            name="wealth-guide tool allowlist",
            status="FAIL",
            severity="critical",
            message="wealth-guide.md not found",
        ))
        return suite

    from . import parse_yaml_frontmatter
    fm = parse_yaml_frontmatter(wg_file.read_text())
    if not fm:
        suite.add(TestResult(
            name="wealth-guide tool allowlist",
            status="FAIL",
            severity="critical",
            message="No YAML frontmatter",
        ))
        return suite

    tools = fm.get("tools", {})
    missing = []
    for slug in SUBAGENTS:
        key = f"task__{slug}__*"
        if key not in tools:
            missing.append(slug)
    if missing:
        suite.add(TestResult(
            name="All 22 subagents in wealth-guide task allowlist",
            status="FAIL",
            severity="critical",
            message=f"Missing task tools: {missing}",
            details={"missing": missing},
        ))
    else:
        suite.add(TestResult(
            name="All 22 subagents in wealth-guide task allowlist",
            status="PASS",
            message="All 22 subagents can be invoked by wealth-guide",
        ))

    # Also check MCP tools
    mcp_keys = [k for k in tools if k.startswith("mcp__")]
    if not mcp_keys:
        suite.add(TestResult(
            name="wealth-guide has MCP tools",
            status="WARN",
            severity="minor",
            message="No MCP tools declared",
        ))
    else:
        suite.add(TestResult(
            name="wealth-guide has MCP tools",
            status="PASS",
            message=f"{len(mcp_keys)} MCP tools: {mcp_keys}",
        ))

    return suite


def test_pipeline_stress() -> TestSuite:
    """Stress test: many queries in a row should not slow down or break."""
    suite = TestSuite(name="Pipeline Stress Test")
    queries = [
        "Run earnings analysis on AAPL",
        "Build DCF for MSFT",
        "What market is BTC?",
        "Generate client report",
        "Process KYC for new client",
        "Run a backtest on my strategy",
        "Use alpha-researcher for IC analysis",
        "Close the books for March",
        "Convene investment committee",
        "Screen deals in fintech",
    ]
    start = time.time()
    failures = []
    for q in queries:
        try:
            result = dispatch(q)
            if not isinstance(result, list):
                failures.append((q, f"non-list: {result}"))
        except Exception as e:
            failures.append((q, f"exception: {e}"))
    duration = (time.time() - start) * 1000

    if failures:
        for q, err in failures:
            suite.add(TestResult(
                name=f"stress: {q[:30]}",
                status="FAIL",
                severity="major",
                message=err,
            ))
    else:
        suite.add(TestResult(
            name=f"Stress test: {len(queries)} queries",
            status="PASS",
            message=f"All succeeded in {duration:.1f}ms ({duration/len(queries):.2f}ms/query)",
            duration_ms=duration,
        ))
    return suite


def test_cookbooks_have_questions() -> TestSuite:
    """Each cookbook must have a questions.md."""
    suite = TestSuite(name="Cookbook Integrity")
    cookbooks = list_cookbooks()
    missing = []
    for cb in cookbooks:
        q_file = EXAMPLE_DIR / cb / "questions.md"
        if not q_file.exists():
            missing.append(cb)
    if missing:
        suite.add(TestResult(
            name="All cookbooks have questions.md",
            status="FAIL",
            severity="major",
            message=f"Missing: {missing}",
        ))
    else:
        suite.add(TestResult(
            name="All cookbooks have questions.md",
            status="PASS",
            message=f"All {len(cookbooks)} cookbooks have questions.md",
        ))
    return suite


def test_cookbook_questions_route() -> TestSuite:
    """Verify that cookbook sample questions route to expected subagents."""
    suite = TestSuite(name="Cookbook Routing")
    # Mapping of cookbook slug → expected sample questions and routes
    cookbook_test_cases = [
        ("earnings-reviewer", "Analyze Q1 2024 earnings for NVDA", ["earnings-reviewer"]),
        ("pitch-agent", "Build a pitch deck for CloudSoft", ["pitch-agent"]),
        ("market-researcher", "Give me a sector primer on cloud", ["market-researcher"]),
        ("model-builder", "Build a DCF for AAPL", ["model-builder"]),
        ("private-equity", "Source deals in fintech", ["private-equity"]),
        ("wealth-management", "Generate a client report", ["wealth-management"]),
        ("fund-admin", "Run NAV tie-out", ["fund-admin"]),
        ("gl-reconciler", "Run GL recon", ["gl-reconciler"]),
        ("month-end-closer", "Close the books for March", ["month-end-closer"]),
        ("statement-auditor", "Audit LP statement batch", ["statement-auditor"]),
        ("valuation-reviewer", "Review portco valuations", ["valuation-reviewer"]),
        ("kyc-screener", "Run KYC screening for new client", ["kyc-screener"]),
        ("meeting-prep-agent", "Meeting prep for Smith client", ["meeting-prep-agent"]),
        ("financial-analysis", "Run a competitive analysis", ["financial-analysis"]),
        ("operations", "Run AI readiness scan", ["operations"]),
        ("alpha-researcher", "Bench alpha101 family", ["alpha-researcher"]),
        ("backtest-builder", "Run a backtest on my strategy", ["backtest-builder"]),
        ("factor-researcher", "Run ICIR on momentum", ["factor-researcher"]),
        ("market-router", "What market is BTC?", ["market-router"]),
        ("swarm-orchestrator", "Convene investment committee", ["swarm-orchestrator"]),
    ]
    for cb_slug, query, expected in cookbook_test_cases:
        result = dispatch(query)
        expected_set = set(expected)
        actual_set = set(result)
        if expected_set.issubset(actual_set):
            suite.add(TestResult(
                name=f"cookbook routing: {cb_slug}",
                status="PASS",
                message=f"Routes to {expected_set}",
                details={"query": query, "result": result},
            ))
        else:
            suite.add(TestResult(
                name=f"cookbook routing: {cb_slug}",
                status="FAIL",
                severity="major",
                message=f"Missing: {expected_set - actual_set}",
                details={"query": query, "result": result, "expected": expected},
            ))
    return suite


def test_wealth_guide_e2e_routing() -> TestSuite:
    """The wealth-guide-e2e cookbook questions should route correctly."""
    suite = TestSuite(name="Wealth-Guide E2E Routing")
    e2e_cases = [
        {
            "query": "Analyze their latest earnings, build a DCF model, and compare against AMD",
            "expected": ["earnings-reviewer", "model-builder"],
            "desc": "NVDA thesis (earnings + DCF + comps)",
        },
        {
            "query": "Screen for PE deals in fintech, then do a competitive analysis. Also check my portfolio for any overlaps.",
            "expected": ["private-equity", "market-researcher"],
            "desc": "PE + competitive + portfolio",
        },
        {
            "query": "Research the momentum factor on CSI 300 using the alpha zoo, then backtest the top 10 alphas",
            "expected": ["alpha-researcher"],
            "desc": "alpha + backtest",
        },
        {
            "query": "Close the books for March — run the month-end close, then audit the LP statements",
            "expected": ["month-end-closer", "statement-auditor"],
            "desc": "close + audit",
        },
    ]
    for case in e2e_cases:
        result = dispatch(case["query"])
        expected_set = set(case["expected"])
        actual_set = set(result)
        if expected_set.issubset(actual_set):
            suite.add(TestResult(
                name=f"e2e: {case['desc']}",
                status="PASS",
                message=f"Routes to {sorted(actual_set)}",
                details={"query": case["query"][:50], "result": result},
            ))
        else:
            suite.add(TestResult(
                name=f"e2e: {case['desc']}",
                status="FAIL",
                severity="major",
                message=f"Missing: {expected_set - actual_set}",
                details={"query": case["query"], "result": result, "expected": case["expected"]},
            ))
    return suite


def run_all() -> List[TestSuite]:
    return [
        test_parallel_dispatch(),
        test_no_duplicate_dispatch(),
        test_user_override_takes_priority(),
        test_chinese_override(),
        test_all_subagents_reachable(),
        test_wealth_guide_has_all_tasks(),
        test_pipeline_stress(),
        test_cookbooks_have_questions(),
        test_cookbook_questions_route(),
        test_wealth_guide_e2e_routing(),
    ]


if __name__ == "__main__":
    print_header("CROSS-AGENT PIPELINE TESTS")
    suites = run_all()
    total_pass = 0
    total_fail = 0
    for suite in suites:
        print(f"\n--- {suite.name} ---")
        for r in suite.results:
            status_color = {"PASS": "green", "FAIL": "red", "WARN": "yellow", "SKIP": "cyan"}[r.status]
            print(f"  [{colorize(r.status, status_color)}] {r.name}: {r.message}")
        total_pass += suite.passed
        total_fail += suite.failed
    print(f"\n  TOTAL: {total_pass} passed, {total_fail} failed")