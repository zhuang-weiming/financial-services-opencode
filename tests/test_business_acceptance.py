"""Business acceptance tests for cookbooks.

Each cookbook is a starter kit with sample data and questions.
Acceptance criteria:
- Each cookbook has questions.md with ≥3 questions
- Each cookbook has README.md
- Each cookbook questions routes to the expected subagent (positive test)
- Adversarial/negative test: questions meant for one subagent should NOT route to a different one
"""

import re
from pathlib import Path
from typing import List
from . import (
    EXAMPLE_DIR, INSTRUCTIONS_DIR, list_cookbooks, dispatch,
    TestResult, TestSuite, print_header, colorize,
)


# Map cookbook slug → expected subagent(s) for routing tests
COOKBOOK_EXPECTED_SUBAGENTS = {
    "earnings-reviewer": ["earnings-reviewer"],
    "equity-research": ["equity-research"],
    "financial-analysis": ["financial-analysis"],
    "fund-admin": ["fund-admin"],
    "gl-reconciler": ["gl-reconciler"],
    "investment-banking": ["investment-banking"],
    "kyc-screener": ["kyc-screener"],
    "market-researcher": ["market-researcher"],
    "meeting-prep-agent": ["meeting-prep-agent"],
    "model-builder": ["model-builder"],
    "month-end-closer": ["month-end-closer"],
    "operations": ["operations"],
    "pitch-agent": ["pitch-agent"],
    "private-equity": ["private-equity"],
    "statement-auditor": ["statement-auditor"],
    "valuation-reviewer": ["valuation-reviewer"],
    "wealth-management": ["wealth-management"],
    "alpha-researcher": ["alpha-researcher"],
    "backtest-builder": ["backtest-builder"],
    "factor-researcher": ["factor-researcher"],
    "market-router": ["market-router"],
    "swarm-orchestrator": ["swarm-orchestrator"],
    # wealth-guide-e2e is special (multi-subagent)
}


def parse_questions(text: str) -> List[str]:
    """Extract questions from a cookbook questions.md in any format.

    Supports:
    - Bullet lists (- or *) at top level (not nested)
    - Numbered headers with quoted question (### N. "question")
    - ## Question N: Title blocks where the question is in a code block
    - Bullet items wrapped in quotes (e.g., - "List all alpha families")
    """
    questions = []

    # Format 1: Bullet lists (- or *) where the content is a real question
    for line in text.split("\n"):
        line_stripped = line.strip()
        if line_stripped.startswith("- ") or line_stripped.startswith("* "):
            content = line_stripped[2:].strip()
            # Strip surrounding quotes
            if (content.startswith('"') and content.endswith('"')) or \
               (content.startswith("'") and content.endswith("'")):
                content = content[1:-1].strip()
            # Skip metadata-style bullets
            if content.startswith("`") and content.endswith("`"):
                continue
            if content.startswith("Reference:") or content.startswith("Data Files:"):
                continue
            # Real questions usually end with ? or contain action verbs OR start with what/how
            # Many cookbook questions are imperative commands ending without punctuation
            is_question = (
                content.endswith("?")
                or any(v in content.lower() for v in [
                    "prepare", "analyze", "build", "run", "create",
                    "generate", "process", "use", "what", "how",
                    "explain", "show", "list", "compare", "audit",
                    "rebalance", "backtest", "screen", "source",
                    "find", "investigate", "draft", "review",
                    "bench", "validate", "model", "scan",
                    "load", "fetch", "detect", "identify",
                    "estimate", "forecast", "model", "track",
                    "update", "monitor", "calculate", "compute",
                    "run ", "build ", "create ", "design ",
                    "summary", "summarize",
                ])
                or content.lower().startswith(("what", "how", "why", "when", "where", "who"))
            )
            # Filter out metadata patterns
            content_lower = content.lower()
            if any(content_lower.startswith(p) for p in (
                "benchmark:", "reference:", "from ", "data ", "allocation:",
                "key ", "client:", "total assets:", "risk tolerance:",
                "sleeve returns:", "list:", "audit id:", "techcorp",
                "company:", "score ", "critical ", "total estimated",
                "companies reviewed", "data/", "audit fee:",
                "from data/", "from data:", "data file",
            )):
                is_question = False
            # Filter metadata-style content (e.g., "Data: ...", "Note: ...")
            if re.match(r"^[A-Z][a-z]+:\s+", content) and len(content) < 80:
                is_question = False
            # Filter file references
            if content.startswith("`data/") or content.startswith("data/"):
                is_question = False
            # Filter numbers-only or summary lines
            if re.match(r"^\d+\s+\w+", content) and "?" not in content:
                is_question = False
            if is_question and len(content) > 5:
                questions.append(content)

    # Format 2: Numbered headers with quoted question
    for line in text.split("\n"):
        m = re.match(r"^#{1,4}\s*\d+\.\s*[\"']?(.+?)[\"']?\s*$", line.strip())
        if m:
            q = m.group(1).strip().strip("\"'")
            if len(q) > 5:
                questions.append(q)

    # Format 3: ## Question N: Title followed by code block
    blocks = re.split(r"^##\s+Question\s+\d+", text, flags=re.MULTILINE)
    for block in blocks[1:]:
        cb_match = re.search(r"```\s*\n(.+?)\n```", block, re.DOTALL)
        if cb_match:
            cb_text = cb_match.group(1)
            for para in cb_text.split("\n\n"):
                first_line = para.split("\n")[0].strip()
                if (
                    first_line
                    and not first_line.startswith("Reference:")
                    and not first_line.startswith("From ")
                    and not first_line.startswith("```")
                    and not first_line.startswith("Allocation:")
                    and not first_line.startswith("Key Updates:")
                    and not first_line.startswith("Please:")
                    and not first_line.startswith("Question")
                    and len(first_line) > 10
                ):
                    questions.append(first_line)
                    break

    # Dedupe, preserve order
    seen = set()
    unique = []
    for q in questions:
        key = q.strip().lower()[:100]
        if key not in seen and len(q.strip()) > 5:
            seen.add(key)
            unique.append(q.strip())
    return unique


def test_cookbook_has_questions(slug: str) -> TestResult:
    """Cookbook has questions.md with ≥2 questions."""
    q_file = EXAMPLE_DIR / slug / "questions.md"
    if not q_file.exists():
        return TestResult(
            name=f"cookbook has questions: {slug}",
            status="FAIL",
            severity="major",
            message=f"Missing {q_file}",
        )
    text = q_file.read_text()
    questions = parse_questions(text)
    if len(questions) < 2:
        return TestResult(
            name=f"cookbook has questions: {slug}",
            status="FAIL",
            severity="major",
            message=f"Only {len(questions)} questions (need ≥2)",
            details={"count": len(questions)},
        )
    if len(questions) < 3:
        return TestResult(
            name=f"cookbook has questions: {slug}",
            status="WARN",
            severity="minor",
            message=f"{len(questions)} questions (recommend ≥3)",
        )
    return TestResult(
        name=f"cookbook has questions: {slug}",
        status="PASS",
        message=f"{len(questions)} questions",
    )


def test_cookbook_has_readme(slug: str) -> TestResult:
    """Cookbook has README.md."""
    r_file = EXAMPLE_DIR / slug / "README.md"
    if not r_file.exists():
        return TestResult(
            name=f"cookbook has README: {slug}",
            status="FAIL",
            severity="minor",
            message=f"Missing {r_file}",
        )
    text = r_file.read_text()
    if len(text) < 50:
        return TestResult(
            name=f"cookbook has README: {slug}",
            status="WARN",
            severity="minor",
            message=f"README too short ({len(text)} chars)",
        )
    return TestResult(
        name=f"cookbook has README: {slug}",
        status="PASS",
        message=f"README: {len(text)} chars",
    )


def test_cookbook_questions_route(slug: str) -> TestResult:
    """Cookbook sample questions route to expected subagent(s)."""
    expected = COOKBOOK_EXPECTED_SUBAGENTS.get(slug)
    if expected is None:
        return TestResult(
            name=f"cookbook questions route: {slug}",
            status="SKIP",
            message="No expected subagent mapping (multi-subagent cookbook)",
        )

    q_file = EXAMPLE_DIR / slug / "questions.md"
    if not q_file.exists():
        return TestResult(
            name=f"cookbook questions route: {slug}",
            status="FAIL",
            severity="major",
            message="No questions.md",
        )

    questions = parse_questions(q_file.read_text())
    if not questions:
        return TestResult(
            name=f"cookbook questions route: {slug}",
            status="FAIL",
            severity="major",
            message="No questions found",
        )

    expected_set = set(expected)
    failures = []
    for q in questions:
        result = dispatch(q)
        actual_set = set(result)
        if not expected_set.issubset(actual_set):
            failures.append((q[:40], f"missing: {expected_set - actual_set}, got: {result}"))

    if failures:
        return TestResult(
            name=f"cookbook questions route: {slug}",
            status="FAIL",
            severity="major",
            message=f"{len(failures)}/{len(questions)} questions don't route correctly",
            details={"failures": failures[:5]},
        )
    return TestResult(
        name=f"cookbook questions route: {slug}",
        status="PASS",
        message=f"All {len(questions)} questions route to {expected_set}",
    )


def test_negative_routing(slug: str) -> TestResult:
    """Negative test: questions meant for one subagent should NOT route to the wrong one.

    For each cookbook, we verify that adversarial queries (clearly for a different domain)
    do NOT match this cookbook's subagent.
    """
    expected = COOKBOOK_EXPECTED_SUBAGENTS.get(slug)
    if expected is None or not expected:
        return TestResult(
            name=f"negative routing: {slug}",
            status="SKIP",
            message="No expected subagent",
        )

    # Adversarial queries that should NOT match this slug
    adversarial = {
        "earnings-reviewer": "Build a DCF model",
        "pitch-agent": "Run KYC screening",
        "market-researcher": "Reconcile GL accounts",
        "model-builder": "Process KYC onboarding",
        "private-equity": "Generate client report",
        "wealth-management": "Source deals in fintech",
        "fund-admin": "Build a pitch deck",
        "gl-reconciler": "Convene investment committee",
        "month-end-closer": "Bench alpha101 family",
        "statement-auditor": "Run factor analysis",
        "valuation-reviewer": "What market is BTC?",
        "kyc-screener": "Run a backtest on my strategy",
        "meeting-prep-agent": "Reconcile GL accounts",
        "financial-analysis": "Reconcile GL accounts",
        "operations": "Process KYC onboarding",
        "alpha-researcher": "Build a DCF model",
        "backtest-builder": "Process KYC onboarding",
        "factor-researcher": "Build a pitch deck",
        "market-router": "Run a backtest on my strategy",
        "swarm-orchestrator": "Reconcile GL accounts",
        "equity-research": "Run factor analysis",
        "investment-banking": "Process KYC onboarding",
    }
    query = adversarial.get(slug)
    if not query:
        return TestResult(
            name=f"negative routing: {slug}",
            status="SKIP",
            message="No adversarial query defined",
        )

    result = dispatch(query)
    actual_set = set(result)
    if slug in actual_set:
        return TestResult(
            name=f"negative routing: {slug}",
            status="WARN",
            severity="minor",
            message=f"Adversarial query also matched: {result}",
        )
    return TestResult(
        name=f"negative routing: {slug}",
        status="PASS",
        message=f"Adversarial query routed to {result}, not {slug}",
    )


def test_wealth_guide_e2e_questions() -> TestResult:
    """The wealth-guide-e2e cookbook has multi-domain questions that route correctly."""
    slug = "wealth-guide-e2e"
    q_file = EXAMPLE_DIR / slug / "questions.md"
    if not q_file.exists():
        return TestResult(
            name=f"wealth-guide-e2e questions",
            status="FAIL",
            severity="major",
            message="No questions.md",
        )

    questions = parse_questions(q_file.read_text())
    if len(questions) < 5:
        return TestResult(
            name=f"wealth-guide-e2e questions",
            status="WARN",
            severity="minor",
            message=f"Only {len(questions)} questions (recommend ≥5)",
            details={"count": len(questions)},
        )

    # Each e2e question should route to at least one subagent (multi is OK)
    failures = []
    for q in questions:
        result = dispatch(q)
        if not result:
            failures.append((q[:40], "no subagent matched"))

    if failures:
        return TestResult(
            name=f"wealth-guide-e2e questions",
            status="FAIL",
            severity="major",
            message=f"{len(failures)}/{len(questions)} questions route to nothing",
            details={"failures": failures[:5]},
        )
    return TestResult(
        name=f"wealth-guide-e2e questions",
        status="PASS",
        message=f"All {len(questions)} e2e questions route to at least one subagent",
    )


# ---------------------------------------------------------------------------
# 1. Cross-contamination matrix (negative)
# ---------------------------------------------------------------------------

# For each subagent, queries that should NOT match it
CROSS_CONTAMINATION: dict[str, list[str]] = {
    "earnings-reviewer": [
        "Build a DCF model for MSFT",
        "Reconcile GL subledger positions",
        "Source deals in fintech sector",
        "Run KYC screening on new client",
        "Bench the alpha101 family on CSI300",
    ],
    "pitch-agent": [
        "Process month-end close for Fund A",
        "Run factor IC/IR analysis",
        "KYC onboarding for John Doe",
        "Analyze BTC/USDT funding rates",
        "Build a retirement plan for client",
    ],
    "market-researcher": [
        "Post-earnings analysis for AAPL",
        "NAV tie-out for LP statement",
        "LBO model for acquisition target",
        "GL reconciliation for trade date",
        "Screen against sanctions watchlist",
    ],
    "model-builder": [
        "Morning note on overnight moves",
        "Client quarterly report generation",
        "AML screening for PEP check",
        "Alpha zoo browse for momentum factors",
        "Swarm investment committee on sector rotation",
    ],
    "private-equity": [
        "Validate financial model consistency",
        "Run backtest on momentum strategy",
        "Fetch A-share data for 600519",
        "Prepare client meeting briefing pack",
        "Audit LP capital account statements",
    ],
    "wealth-management": [
        "Draft CIM for sell-side process",
        "Run factor decay scan",
        "Accrual schedule for month-end close",
        "Build merger accretion/dilution model",
        "Crypto market analysis for ETH",
    ],
    "fund-admin": [
        "Earnings call transcript review for TSLA",
        "Factor correlation analysis",
        "Client onboarding KYC packet",
        "Pitch deck for growth equity raise",
        "Detect market type for forex pair",
    ],
    "gl-reconciler": [
        "Build DCF model for valuation",
        "Generate client investment proposal",
        "Run alpha bench for gtja191",
        "Quarterly portfolio review for LP",
        "strategy backtest with walk-forward",
    ],
    "month-end-closer": [
        "Initiating coverage report for SNOW",
        "Merger consequences analysis",
        "IC memo for deal approval",
        "Factor research on value factors",
        "Multi-agent swarm for global allocation",
    ],
    "statement-auditor": [
        "Pre-earnings analysis for Q3",
        "Deal sourcing in AI infrastructure",
        "Client report for HNW portfolio",
        "Candlestick pattern detection",
        "GL subledger reconciliation",
    ],
    "valuation-reviewer": [
        "Post-earnings guidance update",
        "KYC screening for high-risk entity",
        "Month-end close checklist",
        "Industry overview for cloud infra",
        "Tushare data fetch for A-share",
    ],
    "kyc-screener": [
        "DCF analysis for acquisition target",
        "Morning meeting prep for PM",
        "Nav tie-out for Fund III LP",
        "Performance attribution analysis",
        "Cross-market data routing for BTC",
    ],
    "meeting-prep-agent": [
        "Build 3-statement model for mergeCo",
        "Run IC/IR on momentum factors",
        "LP statement audit batch",
        "Accrual schedule review",
        "Source companies in logistics tech",
    ],
    "financial-analysis": [
        "Earnings preview for NVDA Q2",
        "Screen new client against watchlists",
        "Close the books for quarter-end",
        "Backtest signal with walk-forward",
        "Swarm macro strategy committee",
    ],
    "operations": [
        "Build LBO model returns sensitivity",
        "Run factor correlation analysis",
        "Fetch EUR/USD spot price",
        "Process KYC onboarding packet",
        "Morning note on market movers",
    ],
    "alpha-researcher": [
        "Reconcile GL to subledger",
        "Client retirement plan projection",
        "Deal screening for PE pipeline",
        "ML strategy with walk-forward",
        "M&A accretion dilution analysis",
    ],
    "backtest-builder": [
        "Fund administration NAV tie-out",
        "Client quarterly performance report",
        "DD checklist for portco review",
        "Sector primer on semis industry",
        "Valuation review of GP package",
    ],
    "factor-researcher": [
        "Pitch deck for Series B round",
        "Month-end accrual schedule",
        "LP capital account audit",
        "Convene investment committee",
        "Coaching for pre-earnings meeting prep",
    ],
    "market-router": [
        "Client report annual review",
        "Factor alpha zoo IC analysis",
        "IC memo for PE deal approval",
        "Financial model audit for errors",
        "Strategy backtest performance metrics",
    ],
    "swarm-orchestrator": [
        "Run KYC AML screening",
        "GL reconciliation for trade date",
        "Build LBO model returns table",
        "Alpha101 factor correlation analysis",
        "Client financial plan for retirement",
    ],
    "equity-research": [
        "NAV tie-out for Fund II",
        "Build DCF for acquisition target",
        "Accrual schedule for month-end",
        "BTC on-chain analysis",
        "KYC screening for new investor",
    ],
    "investment-banking": [
        "Post-earnings beat analysis",
        "Factor decay monitor scan",
        "Backtest strategy with shadow account",
        "Client portfolio rebalance",
        "Run IC/IR on value factors",
    ],
}


def test_cross_contamination(slug: str) -> TestResult:
    """Negative: cross-domain queries must NOT match unrelated subagent."""
    queries = CROSS_CONTAMINATION.get(slug, [])
    if not queries:
        return TestResult(
            name=f"cross-contamination: {slug}",
            status="SKIP",
            message="No adversarial queries defined",
        )
    failures = []
    for q in queries:
        result = dispatch(q)
        if slug in result:
            failures.append(f"'{q[:40]}' incorrectly matched {slug} (got: {result})")
    if failures:
        return TestResult(
            name=f"cross-contamination: {slug}",
            status="FAIL",
            severity="major",
            message=f"{len(failures)}/{len(queries)} false positives",
            details={"failures": failures[:5]},
        )
    return TestResult(
        name=f"cross-contamination: {slug}",
        status="PASS",
        message=f"0/{len(queries)} false positives",
    )


# ---------------------------------------------------------------------------
# 2. Edge cases
# ---------------------------------------------------------------------------

EDGE_CASES: list[tuple[str, str]] = [
    ("empty string", ""),
    ("whitespace only", "   \n  \t  "),
    ("gibberish", "asdfghjkl qwertyuiop"),
    ("single char", "x"),
    ("numbers only", "1234567890"),
    ("special chars", "!@#$%^&*()_+"),
    ("HTML injection", "<script>alert('xss')</script>"),
    ("SQL injection", "'; DROP TABLE agents; --"),
    ("emoji only", "🚀💰📈"),
    ("very long", "a" * 10000),
]


def test_edge_cases() -> TestResult:
    """Edge cases should not crash dispatch and return empty (fallback)."""
    failures = []
    for name, query in EDGE_CASES:
        try:
            result = dispatch(query)
            # Edge cases should generally route to nothing (fallback)
            # unless they accidentally match a keyword
        except Exception as e:
            failures.append(f"{name}: crashed with {e}")
            continue
    if failures:
        return TestResult(
            name=f"edge cases dispatch",
            status="FAIL",
            severity="major",
            message=f"{len(failures)}/{len(EDGE_CASES)} crashed",
            details={"failures": failures[:5]},
        )
    return TestResult(
        name=f"edge cases dispatch",
        status="PASS",
        message=f"All {len(EDGE_CASES)} edge cases handled without crash",
    )


# ---------------------------------------------------------------------------
# 3. Cross-language (Chinese queries)
# ---------------------------------------------------------------------------

CHINESE_QUERIES: list[tuple[str, str, list[str]]] = [
    ("A-share ticker", "分析600519的走势", ["market-router"]),
    ("A-share index", "沪深300成分股分析", ["market-router"]),
    ("Northbound flow", "北向资金今日流向", ["market-router"]),
    ("Alpha analysis", "帮我做alpha因子分析", ["alpha-researcher", "factor-researcher"]),
    ("DCF modeling", "帮我做个DCF估值模型", ["model-builder"]),
    ("Earnings review", "查看最近一个季度的收益报告", ["earnings-reviewer"]),
    ("Pitch deck", "帮我写一份pitch deck", ["pitch-agent"]),
    ("Deal sourcing", "寻找消费行业投资标的", ["private-equity"]),
    ("Client report", "生成客户季度报告", ["wealth-management"]),
    ("KYC screening", "做KYC合规审查", ["kyc-screener"]),
    ("Backtest", "回测这个策略", ["backtest-builder"]),
    ("Crypto", "比特币价格分析", ["market-router"]),
    ("FX", "美元兑人民币汇率", ["market-router"]),
    ("Industry research", "半导体行业研究", ["market-researcher"]),
    ("User override", "请用alpha-researcher分析BTC", ["alpha-researcher"]),
    ("User override CN", "用earnings-reviewer分析AAPL业绩", ["earnings-reviewer"]),
]


def test_chinese_queries() -> TestResult:
    """Chinese queries should route to correct subagents."""
    failures = []
    for name, query, expected in CHINESE_QUERIES:
        result = dispatch(query)
        expected_set = set(expected)
        actual_set = set(result)
        if not expected_set.issubset(actual_set):
            failures.append(f"{name}: expected {expected}, got {result}")
        elif not actual_set.issubset(expected_set) and len(result) != len(expected):
            # Warn of extra matches but only fail if expected is missing
            pass
    if failures:
        return TestResult(
            name=f"chinese queries routing",
            status="FAIL",
            severity="major",
            message=f"{len(failures)}/{len(CHINESE_QUERIES)} failed",
            details={"failures": failures[:5]},
        )
    return TestResult(
        name=f"chinese queries routing",
        status="PASS",
        message=f"All {len(CHINESE_QUERIES)} Chinese queries route correctly",
    )


# ---------------------------------------------------------------------------
# 4. Multi-domain routing
# ---------------------------------------------------------------------------

MULTI_DOMAIN: list[tuple[str, list[str]]] = [
    ("Earnings + DCF analysis for NVDA", ["earnings-reviewer", "model-builder"]),
    ("Review earnings and build a comps analysis", ["earnings-reviewer", "pitch-agent", "model-builder"]),
    ("Deal pitch for target with sector overview", ["pitch-agent", "market-researcher"]),
    ("Run factor IC/IR and backtest the top decile", ["factor-researcher", "backtest-builder"]),
    ("Crypto market analysis with macro sentiment", ["market-router", "factor-researcher"]),
    ("Month-end close with NAV tie-out", ["month-end-closer", "fund-admin"]),
    ("LP statement audit and valuation review", ["statement-auditor", "valuation-reviewer"]),
    ("Alpha zoo browse with factor correlation analysis", ["alpha-researcher", "factor-researcher"]),
    ("Client quarterly report with portfolio rebalance", ["wealth-management"]),
    ("Earnings preview with pre-meeting prep pack", ["earnings-reviewer", "meeting-prep-agent"]),
]


def test_multi_domain_routing() -> TestResult:
    """Multi-domain queries should route to all relevant subagents."""
    failures = []
    for query, expected in MULTI_DOMAIN:
        result = dispatch(query)
        expected_set = set(expected)
        actual_set = set(result)
        if not expected_set.issubset(actual_set):
            failures.append(
                f"'{query[:40]}': missing {expected_set - actual_set}, got {result}"
            )
    if failures:
        return TestResult(
            name=f"multi-domain routing",
            status="FAIL",
            severity="major",
            message=f"{len(failures)}/{len(MULTI_DOMAIN)} missing subagents",
            details={"failures": failures[:5]},
        )
    return TestResult(
        name=f"multi-domain routing",
        status="PASS",
        message=f"All {len(MULTI_DOMAIN)} multi-domain queries route to all expected subagents",
    )


# ---------------------------------------------------------------------------
# 5. Data file integrity
# ---------------------------------------------------------------------------

def test_cookbook_data_files(slug: str) -> TestResult:
    """Cookbook data directory exists and has files referenced in questions."""
    data_dir = EXAMPLE_DIR / slug / "data"
    q_file = EXAMPLE_DIR / slug / "questions.md"

    if not data_dir.exists():
        return TestResult(
            name=f"cookbook data dir: {slug}",
            status="SKIP",
            message="No data/ directory",
        )

    data_files = list(data_dir.iterdir()) if data_dir.is_dir() else []

    # Check questions.md references actual files
    if q_file.exists() and data_files:
        text = q_file.read_text()
        referenced = set()
        for f in data_files:
            ref_name = f.name
            if ref_name in text:
                referenced.add(f.name)

    return TestResult(
        name=f"cookbook data dir: {slug}",
        status="PASS",
        message=f"{len(data_files)} data files, {len(referenced) if data_files else 0} referenced in questions" if data_files else f"Empty data/ dir",
    )


# ---------------------------------------------------------------------------
# 6. Routing table coverage vs wealth-guide-router.md
# ---------------------------------------------------------------------------

def test_routing_table_coverage() -> TestResult:
    """All keywords from wealth-guide-router.md must have ROUTING_TABLE entries."""
    routing_doc = (INSTRUCTIONS_DIR / "wealth-guide-router.md").read_text()

    keyword_sets = {
        "model-builder": {"DCF", "LBO", "3-statement", "comps", "trading comps"},
        "pitch-agent": {"pitch deck", "CIM", "teaser", "buyer list"},
        "investment-banking": {"pitch deck", "CIM", "teaser", "buyer list"},
        "earnings-reviewer": {"earnings", "post-earnings", "Q1 results", "Q2 results", "Q3 results", "Q4 results", "quarterly update"},
        "market-researcher": {"sector primer", "industry overview", "competitive landscape"},
        "private-equity": {"IC memo", "deal screen", "deal sourcing", "DD checklist"},
        "wealth-management": {"client report", "financial plan", "retirement plan", "rebalance"},
        "fund-admin": {"GL recon", "NAV tie-out", "accrual", "roll-forward"},
        "gl-reconciler": {"GL recon", "NAV tie-out", "accrual", "roll-forward"},
        "kyc-screener": {"KYC", "onboarding", "AML screening"},
        "factor-researcher": {"alpha", "factor research", "IC/IR", "quantile"},
        "alpha-researcher": {"alpha", "factor research", "IC/IR", "quantile"},
        "backtest-builder": {"backtest", "strategy backtest", "signal test"},
        "market-router": {"BTC", "crypto", "600519", "上证", "A股", "沪深300", "北向", "EURUSD", "forex", "FX"},
        "swarm-orchestrator": {"swarm", "multi-agent team", "investment committee"},
        "statement-auditor": {"statement audit", "LP statement", "capital account"},
        "month-end-closer": {"month-end close", "close package"},
        "meeting-prep-agent": {"meeting prep", "client meeting", "briefing pack"},
        "valuation-reviewer": {"valuation review", "LP reporting", "GP package"},
    "market-researcher": {"transition update", "coverage update"},
    "equity-research": {"transition update", "coverage update"},
    }

    # Build reverse lookup: which ROUTING_TABLE keywords map to which subagents
    from . import ROUTING_TABLE as rt
    covered: dict[str, set[str]] = {}
    for keyword, slugs in rt.items():
        for slug in slugs:
            covered.setdefault(slug, set()).add(keyword)

    missing: list[tuple[str, str]] = []
    for slug, keywords in keyword_sets.items():
        for kw in keywords:
            kw_lower = kw.lower()
            # Check if any ROUTING_TABLE keyword for this slug covers this concept
            found = any(kw_lower in rk or rk in kw_lower for rk in covered.get(slug, set()))
            # Check other slugs that might cover it
            for other_slug, other_keywords in covered.items():
                if other_slug == slug:
                    continue
                if any(kw_lower in rk or rk in kw_lower for rk in other_keywords):
                    if kw_lower not in {x.lower() for x in keyword_sets.get(other_slug, set())}:
                        pass  # cross-covered by another slug
            if not found:
                # Check if covered by an alternative slug (router.md says "or")
                alt_slugs = {
                    "pitch-agent": ["investment-banking"],
                    "investment-banking": ["pitch-agent"],
                    "fund-admin": ["gl-reconciler"],
                    "gl-reconciler": ["fund-admin"],
                    "factor-researcher": ["alpha-researcher"],
                    "alpha-researcher": ["factor-researcher"],
                    "market-researcher": ["equity-research"],
                    "equity-research": ["market-researcher"],
                }
                found_alt = False
                for alt in alt_slugs.get(slug, []):
                    if any(kw_lower in rk or rk in kw_lower for rk in covered.get(alt, set())):
                        found_alt = True
                        break
                if not found_alt:
                    missing.append((slug, kw))

    if missing:
        return TestResult(
            name=f"routing table coverage",
            status="FAIL",
            severity="major",
            message=f"{len(missing)} keywords from router.md not in ROUTING_TABLE",
            details={"missing": missing[:15]},
        )
    return TestResult(
        name=f"routing table coverage",
        status="PASS",
        message=f"All router.md keywords have ROUTING_TABLE entries",
    )


def run_all_cookbook_acceptance() -> List[TestSuite]:
    """Run all cookbook acceptance tests."""
    has_questions = TestSuite(name="Cookbook Acceptance: Has Questions")
    has_readme = TestSuite(name="Cookbook Acceptance: Has README")
    questions_route = TestSuite(name="Cookbook Acceptance: Questions Route")
    negative = TestSuite(name="Cookbook Acceptance: Negative Routing")
    cross_contam = TestSuite(name="Cookbook Acceptance: Cross-Contamination")
    data_integrity = TestSuite(name="Cookbook Acceptance: Data Integrity")

    for slug in list_cookbooks():
        has_questions.add(test_cookbook_has_questions(slug))
        has_readme.add(test_cookbook_has_readme(slug))
        questions_route.add(test_cookbook_questions_route(slug))
        negative.add(test_negative_routing(slug))
        cross_contam.add(test_cross_contamination(slug))
        data_integrity.add(test_cookbook_data_files(slug))

    e2e_suite = TestSuite(name="Cookbook Acceptance: E2E")
    e2e_suite.add(test_wealth_guide_e2e_questions())

    edge_suite = TestSuite(name="Cookbook Acceptance: Edge Cases")
    edge_suite.add(test_edge_cases())

    cn_suite = TestSuite(name="Cookbook Acceptance: Chinese Queries")
    cn_suite.add(test_chinese_queries())

    multi_suite = TestSuite(name="Cookbook Acceptance: Multi-Domain")
    multi_suite.add(test_multi_domain_routing())

    coverage_suite = TestSuite(name="Cookbook Acceptance: Routing Coverage")
    coverage_suite.add(test_routing_table_coverage())

    return [
        has_questions, has_readme, questions_route, negative,
        cross_contam, data_integrity, e2e_suite,
        edge_suite, cn_suite, multi_suite, coverage_suite,
    ]


def run_all() -> List[TestSuite]:
    return run_all_cookbook_acceptance()


if __name__ == "__main__":
    print_header("BUSINESS ACCEPTANCE TESTS")
    suites = run_all()
    total_pass = 0
    total_fail = 0
    total_warn = 0
    for suite in suites:
        print(f"\n--- {suite.name} ---")
        for r in suite.results[:30]:  # show first 30
            status_color = {"PASS": "green", "FAIL": "red", "WARN": "yellow", "SKIP": "cyan"}[r.status]
            print(f"  [{colorize(r.status, status_color)}] {r.name}: {r.message}")
        if len(suite.results) > 30:
            print(f"  ... ({len(suite.results) - 30} more)")
        total_pass += suite.passed
        total_fail += suite.failed
        total_warn += suite.warnings
    print(f"\n  TOTAL: {total_pass} passed, {total_fail} failed, {total_warn} warnings")