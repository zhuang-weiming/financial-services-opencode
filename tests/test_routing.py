"""Routing capability tests for Wealth-Guide dispatch logic.

Tests that the Python-replica dispatch() function correctly routes:
- Single-domain queries to the correct subagent
- Cross-domain queries to multiple subagents
- User overrides (use X) short-circuit routing
- Fallback (empty list) when no match
- Negative cases (irrelevant queries don't route)
"""

import time
from typing import List
from . import dispatch, SUBAGENTS, TestResult, TestSuite, print_header, colorize


# Routing test cases: (query, expected_subagents, description)
POSITIVE_CASES = [
    # Single-domain: earnings
    ("Run earnings analysis on AAPL", ["earnings-reviewer"], "earnings keyword"),
    ("Q1 2024 earnings results for NVDA", ["earnings-reviewer"], "Q1 + earnings"),
    ("Post-earnings update for TSLA", ["earnings-reviewer"], "post-earnings"),
    ("Pre-earnings preview for AMZN", ["earnings-reviewer"], "pre-earnings"),
    ("Q3 quarterly update on META", ["earnings-reviewer"], "Q3 + quarterly"),

    # Single-domain: modeling
    ("Build a DCF for MSFT", ["model-builder"], "DCF"),
    ("Run an LBO analysis", ["model-builder"], "LBO"),
    ("Create 3-statement model", ["model-builder"], "3-statement"),

    # Single-domain: IB
    ("Build a pitch deck for CloudSoft", ["pitch-agent"], "pitch deck"),
    ("Draft a CIM for the acquisition", ["pitch-agent"], "CIM"),
    ("Create an anonymous teaser", ["pitch-agent"], "teaser"),
    ("Build a buyer list", ["pitch-agent"], "buyer list"),

    # Single-domain: PE
    ("Write an IC memo for Fund III", ["private-equity"], "IC memo"),
    ("Source deals in fintech", ["private-equity"], "deal sourcing"),
    ("Screen this CIM for our thesis", ["private-equity"], "deal screening"),

    # Single-domain: WM
    ("Generate client report for Smith family", ["wealth-management"], "client report"),
    ("Build retirement plan", ["wealth-management"], "retirement"),
    ("Rebalance my portfolio", ["wealth-management"], "rebalance"),

    # Single-domain: Fund admin
    ("Run GL recon for trade date 2025-01-15", ["gl-reconciler"], "GL recon"),
    ("Do NAV tie-out", ["fund-admin"], "NAV tie-out"),
    ("Close the books for March", ["month-end-closer"], "month-end close"),

    # Single-domain: KYC
    ("Run KYC screening for new client", ["kyc-screener"], "KYC"),
    ("Process AML check for onboarding", ["kyc-screener"], "AML"),

    # Single-domain: Quant
    ("Bench alpha101 family", ["alpha-researcher"], "alpha"),
    ("Run factor analysis on momentum", ["factor-researcher"], "factor"),
    ("Run a backtest on my strategy", ["backtest-builder"], "backtest"),

    # Single-domain: Market router
    ("What market is BTC?", ["market-router"], "BTC"),
    ("Analyze ETH/USD", ["market-router"], "ETH"),
    ("Get data on EURUSD", ["market-router"], "EURUSD"),

    # Single-domain: Swarm
    ("Convene investment committee", ["swarm-orchestrator"], "investment committee"),
    ("Run swarm analysis on portfolio", ["swarm-orchestrator"], "swarm"),

    # Single-domain: Meeting prep
    ("Meeting prep for Smith client", ["meeting-prep-agent"], "meeting prep"),

    # Single-domain: Statement audit
    ("Audit LP statement batch", ["statement-auditor"], "statement audit"),

    # Single-domain: Valuation review
    ("Review GP package", ["valuation-reviewer"], "GP package"),

    # Cross-domain (multiple)
    ("Earnings + DCF + comps for NVDA",
     ["earnings-reviewer", "model-builder", "pitch-agent"],
     "earnings+DCF+comps parallel"),
    ("Run ICIR on alpha101, then backtest",
     ["alpha-researcher", "factor-researcher", "backtest-builder"],
     "alpha + ICIR + backtest"),
]


# Override test cases: should short-circuit to named subagent
OVERRIDE_CASES = [
    ("Please use alpha-researcher for BTC analysis", ["alpha-researcher"]),
    ("use earnings-reviewer to process Q4", ["earnings-reviewer"]),
    ("用 market-router 分析 600519", ["market-router"]),
    ("route to factor-researcher for IC analysis", ["factor-researcher"]),
]


# Negative cases: queries that should NOT route to any specific subagent (fallback)
FALLBACK_CASES = [
    ("Hello, how are you today?", "general greeting"),
    ("What is the weather like?", "non-financial query"),
    ("Explain quantum entanglement", "physics query"),
    ("", "empty query"),
]


def run_positive_cases() -> TestSuite:
    """Test that expected subagents are reachable from each query.

    Wealth-Guide is designed for parallel dispatch: if a query is ambiguous
    (e.g., "Screen this CIM" matches both private-equity and pitch-agent),
    dispatching both is a feature, not a bug. So we test that all expected
    subagents are present in the result (set membership), not exact equality.
    """
    suite = TestSuite(name="Routing Positive Cases")
    for query, expected, desc in POSITIVE_CASES:
        start = time.time()
        result = dispatch(query)
        result_set = set(result)
        expected_set = set(expected)
        passed = expected_set.issubset(result_set)
        if not passed:
            missing = expected_set - result_set
            message = f"Expected {expected} ⊆ {result}, missing: {sorted(missing)}"
        else:
            extra = result_set - expected_set
            if extra:
                message = f"OK (with extra dispatch: {sorted(extra)})"
            else:
                message = f"Exact match: {expected}"
        suite.add(TestResult(
            name=f"[{desc}] {query[:50]}",
            status="PASS" if passed else "FAIL",
            severity="major" if not passed else "normal",
            message=message,
            duration_ms=(time.time() - start) * 1000,
            details={"query": query, "expected": expected, "actual": result},
        ))
    return suite


def run_override_cases() -> TestSuite:
    """Test user overrides. Override is exact: returns single named subagent."""
    suite = TestSuite(name="Routing Override Cases")
    for query, expected in OVERRIDE_CASES:
        start = time.time()
        result = dispatch(query)
        passed = result == expected
        suite.add(TestResult(
            name=f"override: {query[:50]}",
            status="PASS" if passed else "FAIL",
            severity="major" if not passed else "normal",
            message=f"Expected {expected}, got {result}",
            duration_ms=(time.time() - start) * 1000,
            details={"query": query, "expected": expected, "actual": result},
        ))
    return suite


def run_negative_cases() -> TestSuite:
    """Negative cases: should return empty list (fallback to MCP)."""
    suite = TestSuite(name="Routing Negative Cases (Fallback)")
    for query, desc in FALLBACK_CASES:
        start = time.time()
        result = dispatch(query)
        passed = result == []
        suite.add(TestResult(
            name=f"[{desc}] {query[:30]}",
            status="PASS" if passed else "FAIL",
            severity="major" if not passed else "normal",
            message=f"Expected [], got {result}",
            duration_ms=(time.time() - start) * 1000,
            details={"query": query, "actual": result},
        ))
    return suite


def run_coverage_test() -> TestSuite:
    """Test that every subagent is reachable via at least one keyword."""
    suite = TestSuite(name="Routing Coverage Test")

    # Each subagent slug must appear in the routing table for at least one keyword
    from . import ROUTING_TABLE
    reachable = set()
    for keyword, slugs in ROUTING_TABLE.items():
        for s in slugs:
            reachable.add(s)

    unreachable = set(SUBAGENTS) - reachable
    if unreachable:
        suite.add(TestResult(
            name="All subagents reachable via keywords",
            status="FAIL",
            severity="critical",
            message=f"{len(unreachable)} unreachable",
            details={"unreachable": sorted(unreachable)},
        ))
    else:
        suite.add(TestResult(
            name="All subagents reachable via keywords",
            status="PASS",
            message=f"All {len(SUBAGENTS)} subagents reachable",
        ))
    return suite


def run_all() -> List[TestSuite]:
    return [
        run_positive_cases(),
        run_override_cases(),
        run_negative_cases(),
        run_coverage_test(),
    ]


if __name__ == "__main__":
    print_header("ROUTING TESTS")
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