"""
Test utilities for financial-services-opencode validation.

Provides:
- RepoWalking: find agents, skills, cookbooks
- YAML parsing helpers
- Routing matrix loader
- Test result aggregation
"""

import os
import re
import json
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from datetime import datetime


REPO_ROOT = Path(__file__).parent.parent
OPENCODE_DIR = REPO_ROOT / ".opencode"
AGENTS_DIR = OPENCODE_DIR / "agents"
SKILLS_DIR = OPENCODE_DIR / "skills"
INSTRUCTIONS_DIR = OPENCODE_DIR / "instructions"
MCP_DIR = OPENCODE_DIR / "mcp"
EXAMPLE_DIR = REPO_ROOT / "example"
PYTHON_PKG = OPENCODE_DIR / "python" / "vibe-trading-quanta"


@dataclass
class TestResult:
    name: str
    status: str  # "PASS" | "FAIL" | "SKIP" | "WARN"
    duration_ms: float = 0.0
    message: str = ""
    severity: str = "normal"  # "critical" | "major" | "normal" | "minor"
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TestSuite:
    name: str
    results: List[TestResult] = field(default_factory=list)

    def add(self, result: TestResult):
        self.results.append(result)

    @property
    def passed(self) -> int:
        return sum(1 for r in self.results if r.status == "PASS")

    @property
    def failed(self) -> int:
        return sum(1 for r in self.results if r.status == "FAIL")

    @property
    def warnings(self) -> int:
        return sum(1 for r in self.results if r.status == "WARN")

    @property
    def skipped(self) -> int:
        return sum(1 for r in self.results if r.status == "SKIP")


def parse_yaml_frontmatter(text: str) -> Optional[Dict[str, Any]]:
    """Parse YAML frontmatter from a markdown file."""
    if not text.startswith("---"):
        return None
    parts = text.split("---", 2)
    if len(parts) < 3:
        return None
    try:
        return yaml.safe_load(parts[1])
    except yaml.YAMLError:
        return None


def list_agents() -> List[str]:
    """Return sorted list of all agent slugs (directories)."""
    if not AGENTS_DIR.exists():
        return []
    slugs = []
    for p in AGENTS_DIR.iterdir():
        if p.is_dir() and not p.name.startswith("."):
            agent_file = p / "agents" / f"{p.name}.md"
            if agent_file.exists():
                slugs.append(p.name)
    return sorted(slugs)


def list_skills() -> List[str]:
    """Return sorted list of all skill names."""
    if not SKILLS_DIR.exists():
        return []
    names = []
    for p in SKILLS_DIR.iterdir():
        if p.is_dir() and not p.name.startswith(".") and p.name != "INDEX.md":
            if (p / "SKILL.md").exists():
                names.append(p.name)
    return sorted(names)


def list_cookbooks() -> List[str]:
    """Return sorted list of all cookbook slugs."""
    if not EXAMPLE_DIR.exists():
        return []
    names = []
    for p in EXAMPLE_DIR.iterdir():
        if p.is_dir() and not p.name.startswith("."):
            names.append(p.name)
    return sorted(names)


def read_agent_file(slug: str) -> Optional[Dict[str, Any]]:
    """Read and parse the YAML frontmatter of an agent file."""
    agent_file = AGENTS_DIR / slug / "agents" / f"{slug}.md"
    if not agent_file.exists():
        return None
    return parse_yaml_frontmatter(agent_file.read_text())


def read_skill_frontmatter(name: str) -> Optional[Dict[str, Any]]:
    """Read and parse the YAML frontmatter of a SKILL.md file."""
    skill_file = SKILLS_DIR / name / "SKILL.md"
    if not skill_file.exists():
        return None
    return parse_yaml_frontmatter(skill_file.read_text())


def get_agent_body(slug: str) -> str:
    """Return the markdown body of an agent file (after YAML frontmatter)."""
    agent_file = AGENTS_DIR / slug / "agents" / f"{slug}.md"
    if not agent_file.exists():
        return ""
    text = agent_file.read_text()
    parts = text.split("---", 2)
    if len(parts) >= 3:
        return parts[2].strip()
    return text


def load_routing_matrix() -> Dict[str, Any]:
    """Parse the wealth-guide-router.md into a routing dict."""
    router_file = INSTRUCTIONS_DIR / "wealth-guide-router.md"
    if not router_file.exists():
        return {}
    text = router_file.read_text()
    return {"raw": text}


# Routing decision engine (Python-replica of the LLM routing logic)
# Order matters: longer/more-specific keywords are matched first.
ROUTING_TABLE = {
    "based on the coverage universe": ["equity-research"],
    "portfolio performance across": ["private-equity", "operations"],
    "operating-partner-playbook": ["operations"],
    "operating-partner playbook": ["operations"],
    "competitive landscape deck": ["financial-analysis"],
    "screen against watchlists": ["kyc-screener"],
    "machine learning strategy": ["swarm-orchestrator"],
    "income statement variance": ["month-end-closer"],
    "technical analysis panel": ["swarm-orchestrator"],
    "mergers and acquisitions": ["investment-banking"],
    "football field valuation": ["pitch-agent", "financial-analysis"],
    "performance attribution": ["factor-researcher"],
    "management-meeting-prep": ["operations"],
    "management meeting prep": ["operations"],
    "information-coefficient": ["factor-researcher"],
    "information coefficient": ["factor-researcher"],
    "due-diligence procedure": ["kyc-screener", "private-equity"],
    "due diligence procedure": ["kyc-screener", "private-equity"],
    "use valuation-reviewer": ["valuation-reviewer"],
    "use swarm-orchestrator": ["swarm-orchestrator"],
    "use meeting-prep-agent": ["meeting-prep-agent"],
    "use investment-banking": ["investment-banking"],
    "use financial-analysis": ["financial-analysis"],
    "sentiment-intelligence": ["swarm-orchestrator"],
    "sentiment intelligence": ["swarm-orchestrator"],
    "enhanced due diligence": ["kyc-screener"],
    "audit my lp statements": ["statement-auditor"],
    "use wealth-management": ["wealth-management"],
    "use statement-auditor": ["statement-auditor"],
    "use market-researcher": ["market-researcher"],
    "use factor-researcher": ["factor-researcher"],
    "use earnings-reviewer": ["earnings-reviewer"],
    "three-statement model": ["model-builder"],
    "statistical-arbitrage": ["swarm-orchestrator"],
    "statistical arbitrage": ["swarm-orchestrator"],
    "pre-earnings analysis": ["meeting-prep-agent", "earnings-reviewer"],
    "pre earnings analysis": ["meeting-prep-agent", "earnings-reviewer"],
    "portfolio performance": ["operations", "valuation-reviewer"],
    "model for consistency": ["statement-auditor", "model-builder"],
    "geopolitical-war-room": ["swarm-orchestrator"],
    "geopolitical war room": ["swarm-orchestrator"],
    "fundamental screening": ["market-researcher"],
    "competitive landscape": ["market-researcher"],
    "analyze the portfolio": ["private-equity", "operations"],
    "ai-deployment-roadmap": ["operations"],
    "ai deployment roadmap": ["operations"],
    "validate the accrual": ["month-end-closer", "fund-admin"],
    "validate assumptions": ["model-builder"],
    "use month-end-closer": ["month-end-closer"],
    "use backtest-builder": ["backtest-builder"],
    "use alpha-researcher": ["alpha-researcher"],
    "quarterly valuations": ["valuation-reviewer"],
    "net-dollar-retention": ["operations"],
    "net dollar retention": ["operations"],
    "investment committee": ["swarm-orchestrator"],
    "infrastructure comps": ["valuation-reviewer", "pitch-agent"],
    "global equities desk": ["swarm-orchestrator"],
    "fundamental-research": ["swarm-orchestrator"],
    "fundamental research": ["swarm-orchestrator"],
    "equity research team": ["swarm-orchestrator"],
    "earnings review with": ["meeting-prep-agent", "earnings-reviewer"],
    "competitive-analysis": ["financial-analysis"],
    "competitive analysis": ["financial-analysis"],
    "comparables analysis": ["pitch-agent", "model-builder"],
    "cloud infrastructure": ["valuation-reviewer", "pitch-agent"],
    "cash-flow projection": ["fund-admin"],
    "cash flow projection": ["fund-admin"],
    "attribution analysis": ["factor-researcher"],
    "ai-operating-partner": ["operations"],
    "ai operating partner": ["operations"],
    "variance commentary": ["month-end-closer"],
    "valuation-reporting": ["valuation-reviewer"],
    "valuation challenge": ["valuation-reviewer"],
    "use equity-research": ["equity-research"],
    "stress test the dcf": ["valuation-reviewer", "financial-analysis"],
    "set up pre-earnings": ["meeting-prep-agent", "earnings-reviewer"],
    "set up pre earnings": ["meeting-prep-agent", "earnings-reviewer"],
    "rollover valuations": ["valuation-reviewer"],
    "retirement planning": ["wealth-management"],
    "rebalance portfolio": ["wealth-management"],
    "portfolio-companies": ["operations"],
    "portfolio rebalance": ["wealth-management"],
    "portfolio companies": ["operations"],
    "performance metrics": ["backtest-builder"],
    "op-partner-playbook": ["operations"],
    "op partner playbook": ["operations"],
    "merger consequences": ["financial-analysis"],
    "investment-proposal": ["wealth-management"],
    "investment proposal": ["wealth-management"],
    "initiating coverage": ["market-researcher", "equity-research"],
    "fund administration": ["fund-admin"],
    "earnings transcript": ["earnings-reviewer"],
    "diligence-checklist": ["operations"],
    "diligence checklist": ["operations"],
    "customer-references": ["operations"],
    "customer references": ["operations"],
    "customer onboarding": ["kyc-screener"],
    "coverage initiation": ["market-researcher"],
    "consensus estimates": ["earnings-reviewer"],
    "comparable analysis": ["equity-research", "market-researcher", "model-builder"],
    "challenge valuation": ["valuation-reviewer"],
    "auditing statements": ["statement-auditor"],
    "valuation-rollover": ["valuation-reviewer"],
    "valuation rollover": ["valuation-reviewer"],
    "use private-equity": ["private-equity"],
    "upcoming catalysts": ["market-researcher"],
    "technical-analysis": ["swarm-orchestrator"],
    "show me the sharpe": ["backtest-builder"],
    "shanghai composite": ["market-router"],
    "sector comparables": ["financial-analysis", "market-researcher"],
    "screen against our": ["private-equity"],
    "return attribution": ["factor-researcher"],
    "recession scenario": ["financial-analysis"],
    "quarterly earnings": ["earnings-reviewer"],
    "prepare for client": ["meeting-prep-agent"],
    "portfolio holdings": ["operations"],
    "performance across": ["operations", "valuation-reviewer"],
    "operating-playbook": ["operations"],
    "operating playbook": ["operations"],
    "lp statement batch": ["statement-auditor"],
    "investor reporting": ["valuation-reviewer"],
    "investment-banking": ["investment-banking"],
    "ic-memo-operations": ["operations"],
    "ic memo operations": ["operations"],
    "fundamental factor": ["alpha-researcher", "factor-researcher"],
    "financial planning": ["wealth-management"],
    "factor performance": ["factor-researcher"],
    "factor correlation": ["factor-researcher"],
    "factor combination": ["factor-researcher"],
    "customer-reference": ["operations"],
    "customer reference": ["operations"],
    "compare valuations": ["valuation-reviewer"],
    "commodity-research": ["swarm-orchestrator"],
    "commodity research": ["swarm-orchestrator"],
    "against our thesis": ["private-equity"],
    "accretion-dilution": ["financial-analysis"],
    "accretion dilution": ["financial-analysis"],
    "what's the market": ["market-router"],
    "variance analysis": ["month-end-closer"],
    "valuations across": ["valuation-reviewer"],
    "valuation package": ["valuation-reviewer"],
    "validate forecast": ["model-builder"],
    "use model-builder": ["model-builder"],
    "use market-router": ["market-router"],
    "use gl-reconciler": ["gl-reconciler"],
    "transition update": ["market-researcher", "equity-research"],
    "trading-multiples": ["financial-analysis"],
    "trading multiples": ["financial-analysis"],
    "strategy-generate": ["backtest-builder"],
    "strategy generate": ["backtest-builder"],
    "strategy backtest": ["backtest-builder"],
    "spreadsheet-audit": ["financial-analysis"],
    "spreadsheet audit": ["financial-analysis"],
    "sell-side process": ["investment-banking"],
    "sector allocation": ["market-researcher", "equity-research"],
    "screen new client": ["kyc-screener"],
    "screen deals from": ["private-equity"],
    "review valuations": ["valuation-reviewer"],
    "quarterly results": ["earnings-reviewer"],
    "private-placement": ["investment-banking"],
    "private placement": ["investment-banking"],
    "prepare for apple": ["meeting-prep-agent", "earnings-reviewer"],
    "portfolio-company": ["operations"],
    "portfolio company": ["operations"],
    "portco valuations": ["valuation-reviewer"],
    "operating-partner": ["operations"],
    "operating partner": ["operations"],
    "onboarding packet": ["kyc-screener"],
    "model consistency": ["statement-auditor", "model-builder"],
    "market-researcher": ["market-researcher"],
    "investment thesis": ["market-researcher"],
    "initiation report": ["market-researcher", "equity-research"],
    "initiate coverage": ["equity-research"],
    "industry overview": ["market-researcher"],
    "global-allocation": ["swarm-orchestrator"],
    "global allocation": ["swarm-orchestrator"],
    "generate strategy": ["backtest-builder"],
    "earnings revision": ["earnings-reviewer"],
    "earnings analysis": ["earnings-reviewer"],
    "diligence-meeting": ["operations"],
    "diligence meeting": ["operations"],
    "covenant-tracking": ["operations"],
    "covenant tracking": ["operations"],
    "consistency check": ["statement-auditor", "model-builder"],
    "compare snowflake": ["market-researcher", "equity-research"],
    "closing the books": ["month-end-closer"],
    "client onboarding": ["kyc-screener"],
    "check 3-statement": ["statement-auditor", "model-builder"],
    "catalyst calendar": ["market-researcher"],
    "buy-side-advisory": ["investment-banking"],
    "buy-side advisory": ["investment-banking"],
    "analyze portfolio": ["operations"],
    "ai-readiness-scan": ["operations"],
    "ai readiness scan": ["operations"],
    "3-statement model": ["model-builder"],
    "whats the market": ["market-router"],
    "valuation review": ["valuation-reviewer"],
    "validate accrual": ["month-end-closer", "fund-admin"],
    "use kyc-screener": ["kyc-screener"],
    "trade date recon": ["gl-reconciler"],
    "stress dcf model": ["valuation-reviewer", "financial-analysis"],
    "strategy metrics": ["backtest-builder"],
    "screen this week": ["private-equity"],
    "screen for ideas": ["market-researcher"],
    "sanctions screen": ["kyc-screener"],
    "quick comparable": ["equity-research", "market-researcher"],
    "quarterly update": ["earnings-reviewer"],
    "preparation pack": ["meeting-prep-agent"],
    "portfolio-review": ["swarm-orchestrator"],
    "portfolio review": ["private-equity", "operations", "swarm-orchestrator"],
    "portco valuation": ["valuation-reviewer"],
    "multi-agent team": ["swarm-orchestrator"],
    "monthly-tracking": ["operations"],
    "monthly tracking": ["operations"],
    "fund performance": ["private-equity"],
    "factor-committee": ["swarm-orchestrator"],
    "factor committee": ["swarm-orchestrator"],
    "extract strategy": ["backtest-builder"],
    "expert-call-prep": ["operations"],
    "expert call prep": ["operations"],
    "earnings results": ["earnings-reviewer"],
    "earnings preview": ["earnings-reviewer"],
    "derivatives-desk": ["swarm-orchestrator"],
    "derivatives desk": ["swarm-orchestrator"],
    "datapack-builder": ["pitch-agent", "investment-banking"],
    "convertible-bond": ["swarm-orchestrator"],
    "convertible bond": ["swarm-orchestrator"],
    "cash-flow review": ["fund-admin"],
    "cash flow review": ["fund-admin"],
    "audit statements": ["statement-auditor"],
    "asset-allocation": ["wealth-management"],
    "asset allocation": ["wealth-management"],
    "analyze holdings": ["private-equity", "operations"],
    "accrual schedule": ["fund-admin", "month-end-closer"],
    "accrual analysis": ["fund-admin"],
    "variance report": ["month-end-closer"],
    "value-investing": ["swarm-orchestrator"],
    "value investing": ["swarm-orchestrator"],
    "value committee": ["swarm-orchestrator"],
    "use pitch-agent": ["pitch-agent"],
    "three-statement": ["model-builder", "financial-analysis"],
    "three statement": ["financial-analysis"],
    "stress-test the": ["valuation-reviewer", "financial-analysis"],
    "stock screening": ["market-researcher"],
    "statement audit": ["statement-auditor"],
    "shadow backtest": ["backtest-builder"],
    "sector-rotation": ["swarm-orchestrator"],
    "sector rotation": ["swarm-orchestrator"],
    "sector overview": ["market-researcher"],
    "screen incoming": ["private-equity"],
    "review holdings": ["private-equity", "operations"],
    "revenue-quality": ["operations"],
    "revenue quality": ["operations"],
    "retirement plan": ["wealth-management"],
    "research report": ["equity-research"],
    "quarterly close": ["month-end-closer"],
    "portfolio drift": ["wealth-management"],
    "morning meeting": ["earnings-reviewer"],
    "month-end-close": ["month-end-closer"],
    "month-end close": ["month-end-closer"],
    "month end close": ["month-end-closer"],
    "market overview": ["market-researcher"],
    "macro sentiment": ["factor-researcher"],
    "macro committee": ["swarm-orchestrator"],
    "lbo sensitivity": ["financial-analysis", "model-builder"],
    "investment bank": ["investment-banking"],
    "industry report": ["market-researcher"],
    "industry primer": ["market-researcher"],
    "idea-generation": ["market-researcher"],
    "idea generation": ["market-researcher"],
    "guidance update": ["earnings-reviewer"],
    "gross-retention": ["operations"],
    "gross retention": ["operations"],
    "gl vs subledger": ["gl-reconciler"],
    "for consistency": ["statement-auditor", "model-builder"],
    "financial-model": ["financial-analysis"],
    "financial model": ["financial-analysis"],
    "factor-research": ["factor-researcher"],
    "factor-analysis": ["factor-researcher"],
    "factor research": ["factor-researcher"],
    "factor families": ["alpha-researcher", "factor-researcher"],
    "factor exposure": ["factor-researcher"],
    "factor analysis": ["factor-researcher"],
    "estate planning": ["wealth-management"],
    "equity research": ["equity-research"],
    "equity coverage": ["equity-research"],
    "earnings update": ["earnings-reviewer"],
    "earnings season": ["earnings-reviewer"],
    "dd-meeting-prep": ["operations"],
    "dd meeting prep": ["operations"],
    "crypto-research": ["swarm-orchestrator"],
    "crypto research": ["swarm-orchestrator"],
    "credit-research": ["swarm-orchestrator"],
    "credit research": ["swarm-orchestrator"],
    "coverage update": ["market-researcher", "equity-research"],
    "coverage report": ["equity-research"],
    "company-profile": ["investment-banking"],
    "company profile": ["investment-banking"],
    "close the books": ["month-end-closer"],
    "check the model": ["statement-auditor", "model-builder"],
    "capital account": ["fund-admin", "statement-auditor"],
    "across holdings": ["operations"],
    "year-end close": ["month-end-closer"],
    "value-creation": ["operations"],
    "value creation": ["operations"],
    "validate model": ["model-builder"],
    "use operations": ["operations"],
    "use fund-admin": ["fund-admin"],
    "unit-economics": ["operations"],
    "unit economics": ["operations"],
    "thesis-tracker": ["market-researcher"],
    "thesis tracker": ["market-researcher"],
    "stock coverage": ["equity-research"],
    "start coverage": ["market-researcher"],
    "shadow-account": ["backtest-builder"],
    "shadow account": ["backtest-builder"],
    "screen inbound": ["private-equity"],
    "scan portfolio": ["operations"],
    "run a backtest": ["backtest-builder"],
    "risk-committee": ["swarm-orchestrator"],
    "risk committee": ["swarm-orchestrator"],
    "review the dcf": ["valuation-reviewer"],
    "prospect pitch": ["wealth-management"],
    "process-update": ["investment-banking"],
    "process-letter": ["pitch-agent", "investment-banking"],
    "process update": ["investment-banking"],
    "process letter": ["pitch-agent", "investment-banking"],
    "payback-period": ["operations"],
    "payback period": ["operations"],
    "operating-plan": ["operations"],
    "operating plan": ["operations"],
    "monthly-report": ["operations"],
    "monthly report": ["operations"],
    "monitor thesis": ["market-researcher"],
    "mark-to-market": ["valuation-reviewer"],
    "mark to market": ["valuation-reviewer"],
    "macro-strategy": ["swarm-orchestrator"],
    "macro strategy": ["swarm-orchestrator"],
    "macro analysis": ["factor-researcher"],
    "harvest losses": ["wealth-management"],
    "fund-selection": ["swarm-orchestrator"],
    "fund valuation": ["valuation-reviewer"],
    "fund selection": ["swarm-orchestrator"],
    "football-field": ["pitch-agent", "financial-analysis"],
    "football field": ["pitch-agent", "financial-analysis"],
    "financial plan": ["wealth-management"],
    "etf-allocation": ["swarm-orchestrator"],
    "etf allocation": ["swarm-orchestrator"],
    "education plan": ["wealth-management"],
    "deal screening": ["private-equity"],
    "crypto-trading": ["swarm-orchestrator"],
    "crypto trading": ["swarm-orchestrator"],
    "coverage notes": ["equity-research"],
    "covenant-check": ["operations"],
    "covenant check": ["operations"],
    "comps analysis": ["pitch-agent", "model-builder"],
    "company update": ["equity-research"],
    "company report": ["equity-research"],
    "company primer": ["equity-research"],
    "client meeting": ["wealth-management", "meeting-prep-agent"],
    "build strategy": ["backtest-builder"],
    "analyst report": ["equity-research"],
    "ai-opportunity": ["operations"],
    "ai opportunity": ["operations"],
    "against thesis": ["private-equity"],
    "accrual review": ["fund-admin", "month-end-closer"],
    "trading comps": ["pitch-agent", "model-builder"],
    "thesis update": ["market-researcher"],
    "strip-profile": ["investment-banking"],
    "strip profile": ["investment-banking"],
    "sector report": ["market-researcher"],
    "sector primer": ["market-researcher"],
    "screen stocks": ["market-researcher"],
    "saas coverage": ["equity-research", "market-researcher"],
    "run month end": ["month-end-closer"],
    "rollover fund": ["valuation-reviewer"],
    "review portco": ["valuation-reviewer"],
    "research desk": ["swarm-orchestrator"],
    "ramp-modeling": ["operations"],
    "ramp-analysis": ["operations"],
    "ramp modeling": ["operations"],
    "ramp analysis": ["operations"],
    "post-earnings": ["earnings-reviewer"],
    "pep procedure": ["kyc-screener"],
    "pairs-trading": ["swarm-orchestrator"],
    "pairs trading": ["swarm-orchestrator"],
    "out-of-sample": ["backtest-builder"],
    "out of sample": ["backtest-builder"],
    "net-retention": ["operations"],
    "net retention": ["operations"],
    "monthly close": ["month-end-closer"],
    "market primer": ["market-researcher"],
    "lp statements": ["statement-auditor"],
    "kyc-screening": ["kyc-screener"],
    "kyc screening": ["kyc-screener"],
    "inbound deals": ["private-equity"],
    "growth-equity": ["pitch-agent"],
    "growth equity": ["pitch-agent"],
    "factor-debate": ["swarm-orchestrator"],
    "factor family": ["alpha-researcher", "factor-researcher"],
    "factor debate": ["swarm-orchestrator"],
    "equity-report": ["equity-research"],
    "edd procedure": ["kyc-screener"],
    "ebitda-bridge": ["operations"],
    "ebitda bridge": ["operations"],
    "earnings note": ["earnings-reviewer"],
    "earnings miss": ["earnings-reviewer"],
    "earnings call": ["earnings-reviewer"],
    "earnings beat": ["earnings-reviewer"],
    "due-diligence": ["private-equity"],
    "due diligence": ["private-equity"],
    "detect market": ["market-router"],
    "deal-pipeline": ["investment-banking"],
    "deal sourcing": ["private-equity"],
    "deal pipeline": ["investment-banking"],
    "data-cleaning": ["financial-analysis"],
    "data cleaning": ["financial-analysis"],
    "currency pair": ["market-router"],
    "coverage list": ["market-researcher"],
    "comp analysis": ["equity-research", "market-researcher", "model-builder"],
    "close package": ["month-end-closer"],
    "client review": ["wealth-management"],
    "client report": ["wealth-management"],
    "challenge the": ["valuation-reviewer"],
    "challenge dcf": ["valuation-reviewer"],
    "capital-raise": ["investment-banking"],
    "capital raise": ["investment-banking"],
    "broker report": ["equity-research"],
    "briefing pack": ["meeting-prep-agent"],
    "audit results": ["statement-auditor"],
    "aml screening": ["kyc-screener"],
    "alpha trading": ["kyc-screener"],
    "ai deployment": ["operations"],
    "walk-forward": ["backtest-builder"],
    "walk forward": ["backtest-builder"],
    "validate the": ["model-builder"],
    "track thesis": ["market-researcher"],
    "thesis check": ["market-researcher"],
    "swarm-preset": ["swarm-orchestrator"],
    "swarm preset": ["swarm-orchestrator"],
    "strategy-dev": ["backtest-builder"],
    "strategy dev": ["backtest-builder"],
    "stock screen": ["market-researcher"],
    "source deals": ["private-equity"],
    "social-alpha": ["swarm-orchestrator"],
    "social alpha": ["swarm-orchestrator"],
    "screen deals": ["private-equity"],
    "saas-metrics": ["operations"],
    "saas metrics": ["operations"],
    "roll-forward": ["fund-admin"],
    "risk profile": ["wealth-management"],
    "review model": ["valuation-reviewer"],
    "review comps": ["valuation-reviewer"],
    "reconcile gl": ["gl-reconciler"],
    "rates and fx": ["swarm-orchestrator"],
    "q4 cash flow": ["fund-admin"],
    "q3 cash flow": ["fund-admin"],
    "q2 cash flow": ["fund-admin"],
    "pre-earnings": ["earnings-reviewer"],
    "new coverage": ["market-researcher"],
    "morning-note": ["earnings-reviewer"],
    "morning note": ["earnings-reviewer"],
    "model errors": ["statement-auditor"],
    "merger-model": ["financial-analysis"],
    "merger model": ["financial-analysis"],
    "meeting-prep": ["meeting-prep-agent"],
    "meeting prep": ["meeting-prep-agent"],
    "max drawdown": ["backtest-builder"],
    "lp statement": ["statement-auditor", "fund-admin"],
    "lp reporting": ["valuation-reviewer"],
    "lbo analysis": ["model-builder"],
    "kpi-tracking": ["operations"],
    "kpi tracking": ["operations"],
    "icir between": ["alpha-researcher", "factor-researcher"],
    "gdp scenario": ["financial-analysis"],
    "fund returns": ["private-equity"],
    "factor decay": ["factor-researcher"],
    "event-driven": ["swarm-orchestrator"],
    "event driven": ["swarm-orchestrator"],
    "ed procedure": ["kyc-screener"],
    "do month end": ["month-end-closer"],
    "dd-checklist": ["operations"],
    "dd checklist": ["private-equity", "operations"],
    "dcf analysis": ["model-builder"],
    "compare icir": ["alpha-researcher", "factor-researcher"],
    "company deep": ["equity-research"],
    "briefing-pad": ["meeting-prep-agent"],
    "audit the lp": ["statement-auditor"],
    "audit my lps": ["statement-auditor"],
    "audit errors": ["statement-auditor"],
    "analyze fund": ["private-equity"],
    "ai-readiness": ["operations"],
    "ai readiness": ["operations"],
    "100-day-plan": ["operations"],
    "100-day plan": ["operations"],
    "what market": ["market-router"],
    "transaction": ["investment-banking"],
    "tie-out nav": ["fund-admin"],
    "tie out nav": ["fund-admin"],
    "tech growth": ["statement-auditor"],
    "stress-test": ["valuation-reviewer", "financial-analysis"],
    "stress test": ["valuation-reviewer", "financial-analysis"],
    "stock pitch": ["market-researcher"],
    "signal test": ["backtest-builder"],
    "sector deep": ["market-researcher"],
    "screen this": ["private-equity"],
    "saas-cohort": ["operations"],
    "saas cohort": ["operations"],
    "rollforward": ["fund-admin"],
    "pre-meeting": ["meeting-prep-agent"],
    "pre meeting": ["meeting-prep-agent"],
    "portco mark": ["valuation-reviewer"],
    "op playbook": ["operations"],
    "nav tie-out": ["fund-admin"],
    "nav tie out": ["fund-admin"],
    "multi-agent": ["swarm-orchestrator"],
    "multi agent": ["swarm-orchestrator"],
    "model-audit": ["financial-analysis"],
    "model error": ["statement-auditor"],
    "model audit": ["financial-analysis"],
    "ml-strategy": ["swarm-orchestrator"],
    "ml strategy": ["swarm-orchestrator"],
    "macro-rates": ["swarm-orchestrator"],
    "macro rates": ["swarm-orchestrator"],
    "macro forum": ["swarm-orchestrator"],
    "lbo returns": ["financial-analysis", "model-builder"],
    "ir analysis": ["factor-researcher"],
    "ic analysis": ["factor-researcher"],
    "ib-workflow": ["investment-banking"],
    "ib-practice": ["investment-banking"],
    "ib-pipeline": ["investment-banking"],
    "ib-coverage": ["investment-banking"],
    "ib workflow": ["investment-banking"],
    "ib practice": ["investment-banking"],
    "ib pipeline": ["investment-banking"],
    "ib coverage": ["investment-banking"],
    "gp packages": ["valuation-reviewer"],
    "fundraising": ["investment-banking"],
    "fama-french": ["factor-researcher"],
    "fama french": ["factor-researcher"],
    "estate plan": ["wealth-management"],
    "designation": ["kyc-screener"],
    "deal source": ["private-equity"],
    "data-packet": ["pitch-agent"],
    "data packet": ["pitch-agent"],
    "crypto-desk": ["swarm-orchestrator"],
    "crypto desk": ["swarm-orchestrator"],
    "comps table": ["financial-analysis"],
    "competitive": ["market-researcher"],
    "cloud comps": ["valuation-reviewer", "pitch-agent"],
    "close books": ["month-end-closer"],
    "check model": ["statement-auditor", "model-builder"],
    "build pitch": ["pitch-agent"],
    "build a lbo": ["model-builder"],
    "build a dcf": ["model-builder"],
    "bench alpha": ["alpha-researcher"],
    "auditing lp": ["statement-auditor"],
    "audit-model": ["financial-analysis"],
    "audit model": ["statement-auditor", "financial-analysis"],
    "audit batch": ["statement-auditor"],
    "analyst day": ["market-researcher"],
    "alpha-bench": ["alpha-researcher"],
    "alpha bench": ["alpha-researcher"],
    "acquisition": ["investment-banking"],
    "3-statement": ["model-builder"],
    "-200bps gdp": ["financial-analysis"],
    "vs. budget": ["month-end-closer"],
    "transcript": ["earnings-reviewer"],
    "trade idea": ["earnings-reviewer"],
    "swarm team": ["swarm-orchestrator"],
    "sub-ledger": ["gl-reconciler"],
    "stress dcf": ["valuation-reviewer", "financial-analysis"],
    "stock idea": ["market-researcher"],
    "sharpe and": ["backtest-builder"],
    "screen the": ["private-equity"],
    "screen for": ["private-equity"],
    "review dcf": ["valuation-reviewer"],
    "retirement": ["wealth-management"],
    "quick take": ["earnings-reviewer"],
    "q4 results": ["earnings-reviewer"],
    "q3 results": ["earnings-reviewer"],
    "q2 results": ["earnings-reviewer"],
    "q1 results": ["earnings-reviewer"],
    "pitch-deck": ["pitch-agent"],
    "pitch deck": ["pitch-agent"],
    "op-partner": ["operations"],
    "op partner": ["operations"],
    "onboarding": ["kyc-screener"],
    "nav-tieout": ["fund-admin"],
    "nav tieout": ["fund-admin"],
    "make pitch": ["pitch-agent"],
    "lp capital": ["statement-auditor", "fund-admin"],
    "ib-mandate": ["investment-banking"],
    "ib mandate": ["investment-banking"],
    "harborview": ["kyc-screener"],
    "gp package": ["valuation-reviewer"],
    "fund-admin": ["fund-admin"],
    "fund admin": ["fund-admin"],
    "fair-value": ["valuation-reviewer"],
    "fair value": ["valuation-reviewer"],
    "detect for": ["market-router"],
    "clean-data": ["financial-analysis"],
    "clean data": ["financial-analysis"],
    "buyer-list": ["pitch-agent"],
    "buyer list": ["pitch-agent"],
    "arr-cohort": ["operations"],
    "arr cohort": ["operations"],
    "watchlist": ["kyc-screener"],
    "vs budget": ["month-end-closer"],
    "subledger": ["gl-reconciler"],
    "snowflake": ["equity-research"],
    "sentiment": ["factor-researcher"],
    "sell-side": ["equity-research", "investment-banking"],
    "sell side": ["investment-banking"],
    "review my": ["valuation-reviewer"],
    "rebalance": ["wealth-management"],
    "quarterly": ["earnings-reviewer"],
    "pro-forma": ["financial-analysis"],
    "pro forma": ["financial-analysis"],
    "portco-ai": ["operations"],
    "portco ai": ["operations"],
    "pep check": ["kyc-screener"],
    "month-end": ["month-end-closer"],
    "month end": ["month-end-closer"],
    "lp report": ["valuation-reviewer"],
    "lbo model": ["model-builder"],
    "high-risk": ["kyc-screener"],
    "high risk": ["kyc-screener"],
    "deep-dive": ["market-researcher"],
    "deep dive": ["market-researcher"],
    "dcf model": ["model-builder"],
    "data-pack": ["pitch-agent"],
    "data pack": ["pitch-agent", "investment-banking"],
    "build lbo": ["model-builder"],
    "build dcf": ["model-builder"],
    "back-test": ["backtest-builder"],
    "audit-xls": ["financial-analysis"],
    "audit xls": ["financial-analysis"],
    "audit the": ["statement-auditor"],
    "audit lps": ["statement-auditor"],
    "audit for": ["statement-auditor"],
    "aml check": ["kyc-screener"],
    "alpha-zoo": ["alpha-researcher"],
    "alpha zoo": ["alpha-researcher"],
    "ai-deploy": ["operations"],
    "war-room": ["swarm-orchestrator"],
    "war room": ["swarm-orchestrator"],
    "tax-loss": ["wealth-management"],
    "tax loss": ["wealth-management"],
    "stat-arb": ["swarm-orchestrator"],
    "stat arb": ["swarm-orchestrator"],
    "shenzhen": ["market-router"],
    "screen a": ["private-equity"],
    "recon gl": ["gl-reconciler"],
    "rates-fx": ["swarm-orchestrator"],
    "monthend": ["month-end-closer"],
    "ml-quant": ["swarm-orchestrator"],
    "ml quant": ["swarm-orchestrator"],
    "industry": ["market-researcher"],
    "gl-recon": ["gl-reconciler"],
    "gl recon": ["gl-reconciler"],
    "ethereum": ["market-router"],
    "earnings": ["earnings-reviewer"],
    "drawdown": ["backtest-builder"],
    "datapack": ["pitch-agent", "investment-banking"],
    "buy-side": ["equity-research"],
    "briefing": ["meeting-prep-agent"],
    "backtest": ["backtest-builder"],
    "audit lp": ["statement-auditor"],
    "apple q1": ["meeting-prep-agent", "earnings-reviewer"],
    "accruals": ["fund-admin"],
    "rank-ic": ["factor-researcher"],
    "rank ic": ["factor-researcher"],
    "portcos": ["operations"],
    "m and a": ["investment-banking"],
    "ltv/cac": ["operations"],
    "ltv-cac": ["operations"],
    "ltv cac": ["operations"],
    "lps for": ["statement-auditor"],
    "ic-memo": ["private-equity"],
    "ic memo": ["private-equity"],
    "ib-team": ["investment-banking"],
    "ib-deck": ["investment-banking"],
    "ib team": ["investment-banking"],
    "ib deck": ["investment-banking"],
    "gtja191": ["alpha-researcher"],
    "fx rate": ["market-router"],
    "fx pair": ["market-router"],
    "eur/usd": ["market-router"],
    "elastic": ["equity-research"],
    "edd for": ["kyc-screener"],
    "datadog": ["equity-research"],
    "csi-300": ["market-router"],
    "csi 300": ["market-router"],
    "bitcoin": ["market-router"],
    "alpha因子": ["alpha-researcher", "factor-researcher"],
    "airline": ["financial-analysis"],
    "accrual": ["fund-admin"],
    "a-share": ["market-router"],
    "上证": ["market-router"],
    "a股": ["market-router"],
    "a share": ["market-router"],
    "usdjpy": ["market-router"],
    "usdcad": ["market-router"],
    "teaser": ["pitch-agent"],
    "set up": ["meeting-prep-agent"],
    "sector": ["market-researcher"],
    "portco": ["operations"],
    "merger": ["investment-banking"],
    "gbpusd": ["market-router"],
    "quantile": ["factor-researcher", "alpha-researcher"],
    "factor": ["factor-researcher"],
    "eurusd": ["market-router"],
    "csi300": ["market-router"],
    "crypto": ["market-router"],
    "audusd": ["market-router"],
    "ashare": ["market-router"],
    "600519": ["market-router"],
    "300750": ["market-router"],
    "000858": ["market-router"],
    "000001": ["market-router"],
    "沪深300": ["market-router"],
    "swarm": ["swarm-orchestrator"],
    "setup": ["meeting-prep-agent"],
    "recon": ["gl-reconciler"],
    "pitch": ["pitch-agent"],
    "ic/ir": ["factor-researcher"],
    "ic ir": ["factor-researcher"],
    "forex": ["market-router"],
    "delta": ["financial-analysis"],
    "comps": ["pitch-agent", "model-builder"],
    "alpha": ["alpha-researcher"],
    "行业研究": ["market-researcher"],
    "收益报告": ["earnings-reviewer"],
    "投资标的": ["private-equity"],
    "季度报告": ["wealth-management"],
    "因子分析": ["factor-researcher", "alpha-researcher"],
    "回测策略": ["backtest-builder"],
    "合规审查": ["kyc-screener"],
    "估值模型": ["model-builder"],
    "usdt": ["market-router"],
    "ubos": ["kyc-screener"],
    "scan": ["operations"],
    "peps": ["kyc-screener"],
    "icir": ["factor-researcher"],
    "doge": ["market-router"],
    "ddog": ["equity-research"],
    "比特币": ["market-router"],
    "xrp": ["market-router"],
    "ubo": ["kyc-screener"],
    "sol": ["market-router"],
    "ndr": ["operations"],
    "mtm": ["valuation-reviewer"],
    "m&a": ["investment-banking"],
    "lbo": ["model-builder"],
    "kyc": ["kyc-screener"],
    "ipo": ["investment-banking"],
    "eth": ["market-router"],
    "dcf": ["model-builder"],
    "cim": ["pitch-agent"],
    "btc": ["market-router"],
    "bnb": ["market-router"],
    "aml": ["kyc-screener"],
    "汇率": ["market-router"],
    "回测": ["backtest-builder"],
    "北向": ["market-router"],
    "q4": ["earnings-reviewer"],
    "q3": ["earnings-reviewer"],
    "q2": ["earnings-reviewer"],
    "q1": ["earnings-reviewer"],
    "fx": ["market-router"],
}


# All known subagent slugs (must match agents/* directory)
SUBAGENTS = [
    "earnings-reviewer", "equity-research", "financial-analysis", "fund-admin",
    "gl-reconciler", "investment-banking", "kyc-screener", "market-researcher",
    "meeting-prep-agent", "model-builder", "month-end-closer", "operations",
    "pitch-agent", "private-equity", "statement-auditor", "valuation-reviewer",
    "wealth-management", "alpha-researcher", "backtest-builder", "factor-researcher",
    "market-router", "swarm-orchestrator",
]

PRIMARY_AGENTS = ["wealth-guide"]


def dispatch(query: str) -> List[str]:
    """Replicate Wealth-Guide routing logic. Returns list of subagent slugs to invoke.

    Strategy:
    1. User override check: 'use X' or '用 X' or 'please use X'
    2. Keyword scoring — match against ROUTING_TABLE, longest keyword first
    3. Cross-domain detection: if multiple domains detected, dispatch all
    4. Fallback: empty list (caller uses Tier-1 MCP data)
    """
    q = query.lower()

    # User override: "use X", "用 X", "please use X"
    override_patterns = [
        r"use\s+([a-z][a-z0-9-]+)",
        r"用\s+([\w-]+)",
        r"please use\s+([a-z][a-z0-9-]+)",
        r"route to\s+([a-z][a-z0-9-]+)",
    ]
    for pat in override_patterns:
        m = re.search(pat, q)
        if m:
            slug = m.group(1)
            if slug in SUBAGENTS:
                return [slug]

    # Score keywords — sort by length (longest first) so specific phrases win
    matched = []
    seen_slugs = set()
    keywords_by_length = sorted(ROUTING_TABLE.keys(), key=len, reverse=True)
    for keyword in keywords_by_length:
        if keyword.lower() in q:
            for slug in ROUTING_TABLE[keyword]:
                if slug not in seen_slugs:
                    seen_slugs.add(slug)
                    matched.append(slug)

    return matched


def colorize(text: str, color: str) -> str:
    colors = {
        "red": "\033[91m",
        "green": "\033[92m",
        "yellow": "\033[93m",
        "blue": "\033[94m",
        "cyan": "\033[96m",
        "reset": "\033[0m",
    }
    return f"{colors.get(color, '')}{text}{colors['reset']}"


def print_header(text: str, char: str = "=", width: int = 70):
    print()
    print(char * width)
    print(text)
    print(char * width)


def save_report(suites: List[TestSuite], path: Path):
    """Save test results to a JSON file."""
    report = {
        "timestamp": datetime.now().isoformat(),
        "repo_root": str(REPO_ROOT),
        "suites": [
            {
                "name": s.name,
                "passed": s.passed,
                "failed": s.failed,
                "warnings": s.warnings,
                "skipped": s.skipped,
                "results": [asdict(r) for r in s.results],
            }
            for s in suites
        ],
        "totals": {
            "passed": sum(s.passed for s in suites),
            "failed": sum(s.failed for s in suites),
            "warnings": sum(s.warnings for s in suites),
            "skipped": sum(s.skipped for s in suites),
            "total": sum(len(s.results) for s in suites),
        },
    }
    path.write_text(json.dumps(report, indent=2, default=str))
    return report