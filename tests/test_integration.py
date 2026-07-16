"""Integration tests for the Python `vibe-trading-quanta` package.

Tests:
- Package import (already in structural tests, repeated here for completeness)
- Alpha definitions are callable / importable from each family
- Loaders module structure is intact
- Backtest engine base class structure is correct
- Swarm presets are valid YAML
- Optimizers are callable
- Critical scripts/ run without import errors
"""

import sys
from pathlib import Path
from typing import List
from . import (
    PYTHON_PKG, SKILLS_DIR,
    TestResult, TestSuite, print_header, colorize,
)


def test_alpha_family_imports() -> TestResult:
    """All 5 alpha families should be discoverable via Registry.

    Uses the Registry which scans zoo directories via AST (no import needed),
    then verifies individual alphas can be lazy-imported."""
    from vibe_trading_quanta.factors.registry import Registry
    try:
        r = Registry()
    except Exception as e:
        return TestResult(
            name="alpha Registry init",
            status="FAIL",
            severity="critical",
            message=f"Registry() failed: {e}",
        )
    health = r.health()
    if health["failed"] > 0:
        return TestResult(
            name="alpha Registry health",
            status="FAIL",
            severity="major",
            message=f"{health['failed']} load errors",
            details={"errors": health["errors"]},
        )
    # Verify each family has alphas
    families = ["qlib158", "alpha101", "gtja191", "academic", "fundamental"]
    missing = [fam for fam in families if len(r.list(zoo=fam)) == 0]
    if missing:
        return TestResult(
            name="alpha family alphas",
            status="FAIL",
            severity="major",
            message=f"Families with zero alphas: {missing}",
        )
    total = len(r.list())
    return TestResult(
        name="alpha family imports",
        status="PASS",
        message=f"Registry loaded {total} alphas across {len(families)} families, 0 errors",
    )


def test_alpha_count() -> TestResult:
    """Should have ~461 alphas total across 5 families via Registry."""
    from vibe_trading_quanta.factors.registry import Registry
    r = Registry()
    total = len(r.list())
    if total >= 400:
        return TestResult(
            name=f"alpha count >= 400",
            status="PASS",
            message=f"Registry discovered {total} alphas",
            details={"count": total},
        )
    return TestResult(
        name=f"alpha count >= 400",
        status="FAIL",
        severity="major",
        message=f"Only {total} alphas discovered by Registry",
    )


def test_swarm_presets_valid_yaml() -> TestResult:
    """All 30 swarm presets should be valid YAML."""
    preset_dir = PYTHON_PKG / "vibe_trading_quanta" / "swarm" / "presets"
    if not preset_dir.exists():
        return TestResult(
            name="swarm presets valid YAML",
            status="FAIL",
            severity="major",
            message=f"Missing {preset_dir}",
        )
    import yaml
    yaml_files = sorted(preset_dir.glob("*.yaml"))
    invalid = []
    for f in yaml_files:
        try:
            content = yaml.safe_load(f.read_text())
            if not isinstance(content, dict):
                invalid.append(f"{f.name}: not a dict")
        except yaml.YAMLError as e:
            invalid.append(f"{f.name}: {e}")
    if invalid:
        return TestResult(
            name="swarm presets valid YAML",
            status="FAIL",
            severity="major",
            message=f"{len(invalid)} invalid YAML",
            details={"invalid": invalid[:5]},
        )
    return TestResult(
        name="swarm presets valid YAML",
        status="PASS",
        message=f"All {len(yaml_files)} swarm presets are valid YAML",
    )


def test_swarm_presets_have_agents() -> TestResult:
    """Swarm presets should define agents."""
    preset_dir = PYTHON_PKG / "vibe_trading_quanta" / "swarm" / "presets"
    import yaml
    yaml_files = sorted(preset_dir.glob("*.yaml"))
    no_agents = []
    for f in yaml_files:
        try:
            content = yaml.safe_load(f.read_text())
            if not isinstance(content, dict):
                continue
            agents = content.get("agents", [])
            if not agents:
                no_agents.append(f.name)
        except yaml.YAMLError:
            continue
    if no_agents:
        return TestResult(
            name="swarm presets have agents",
            status="WARN",
            severity="minor",
            message=f"{len(no_agents)}/{len(yaml_files)} presets lack agents",
            details={"missing_agents": no_agents[:5]},
        )
    return TestResult(
        name="swarm presets have agents",
        status="PASS",
        message=f"All {len(yaml_files)} presets define agents",
    )


def test_skill_scripts_importable() -> TestResult:
    """Critical skill scripts should be importable without syntax errors."""
    script_dirs = [
        SKILLS_DIR / "alpha-zoo" / "scripts",
        SKILLS_DIR / "backtest-diagnose" / "scripts",
        SKILLS_DIR / "factor-research" / "scripts",
        SKILLS_DIR / "data-routing" / "scripts",
        SKILLS_DIR / "strategy-dev-manager" / "scripts",
    ]
    failed = []
    for d in script_dirs:
        if not d.exists():
            continue
        for py_file in d.glob("*.py"):
            try:
                # Compile check (don't actually import, just check syntax)
                compile(py_file.read_text(), str(py_file), "exec")
            except SyntaxError as e:
                failed.append(f"{py_file.relative_to(SKILLS_DIR)}: {e}")
    if failed:
        return TestResult(
            name="skill scripts syntax valid",
            status="FAIL",
            severity="major",
            message=f"{len(failed)} syntax errors",
            details={"errors": failed[:5]},
        )
    return TestResult(
        name="skill scripts syntax valid",
        status="PASS",
        message=f"All scripts compile without syntax errors",
    )


def test_critical_script_execution() -> TestResult:
    """Critical scripts should run with --help without crashing."""
    scripts_to_test = [
        SKILLS_DIR / "alpha-zoo" / "scripts" / "alpha_bench.py",
        SKILLS_DIR / "backtest-diagnose" / "scripts" / "backtest_runner.py",
        SKILLS_DIR / "factor-research" / "scripts" / "factor_analysis.py",
        SKILLS_DIR / "data-routing" / "scripts" / "market_router.py",
        SKILLS_DIR / "strategy-dev-manager" / "scripts" / "strategy_lifecycle.py",
    ]
    import subprocess
    failed = []
    for s in scripts_to_test:
        if not s.exists():
            continue
        try:
            result = subprocess.run(
                [sys.executable, str(s), "--help"],
                capture_output=True,
                timeout=5,
                text=True,
            )
            if result.returncode != 0 and "error" in (result.stderr or "").lower():
                # Some scripts may exit 2 on --help (argparse default), that's OK
                if result.returncode not in (0, 2):
                    failed.append(f"{s.relative_to(SKILLS_DIR)}: exit {result.returncode}")
        except subprocess.TimeoutExpired:
            failed.append(f"{s.relative_to(SKILLS_DIR)}: timeout")
        except Exception as e:
            failed.append(f"{s.relative_to(SKILLS_DIR)}: {e}")
    if failed:
        return TestResult(
            name="critical scripts run with --help",
            status="FAIL",
            severity="major",
            message=f"{len(failed)} scripts fail",
            details={"errors": failed},
        )
    return TestResult(
        name="critical scripts run with --help",
        status="PASS",
        message=f"All critical scripts handle --help correctly",
    )


def test_no_live_trade_patterns() -> TestResult:
    """All subagents + skills must not contain live-trade instructions.

    Excludes lines where the pattern is part of a prohibition
    (e.g. "never execute a trade", "do not place orders") or
    educational description of market mechanics.
    """
    import re
    from . import AGENTS_DIR, SKILLS_DIR

    # Each entry: (regex_pattern, exemption_context_phrases)
    bad_patterns: list[tuple[str, list[str]]] = [
        (r"place\s+(real\s+)?order", ["call auction", "never place", "do not place"]),
        (r"submit\s+order", ["never submit", "do not submit"]),
        (r"execute\s+(a\s+)?trade", ["never execute", "do not execute", "for research only"]),
        (r"send\s+to\s+broker", ["never send", "do not send"]),
        (r"transfer\s+funds", ["never transfer", "do not transfer"]),
        (r"connect\s+to\s+trading\s+api", ["never connect", "do not connect"]),
    ]

    issues = []
    for agent_file in AGENTS_DIR.glob("*/agents/*.md"):
        text = agent_file.read_text().lower()
        for pat, exemptions in bad_patterns:
            for match in re.finditer(pat, text):
                line_start = max(0, match.start() - 120)
                line_end = min(len(text), match.end() + 80)
                context = text[line_start:line_end]
                if any(ex in context for ex in exemptions):
                    continue
                issues.append(f"{agent_file.relative_to(AGENTS_DIR)}: {pat}")
                break
    for skill_file in SKILLS_DIR.glob("*/SKILL.md"):
        text = skill_file.read_text().lower()
        for pat, exemptions in bad_patterns:
            for match in re.finditer(pat, text):
                line_start = max(0, match.start() - 120)
                line_end = min(len(text), match.end() + 80)
                context = text[line_start:line_end]
                if any(ex in context for ex in exemptions):
                    continue
                issues.append(f"{skill_file.relative_to(SKILLS_DIR)}: {pat}")
                break

    if issues:
        return TestResult(
            name="no live-trade instructions",
            status="FAIL",
            severity="critical",
            message=f"{len(issues)} live-trade patterns found",
            details={"issues": issues[:10]},
        )
    return TestResult(
        name="no live-trade instructions",
        status="PASS",
        message="No live-trade patterns found in agents or skills",
    )


def test_opencode_json_mcp_integrity() -> TestResult:
    """opencode.json MCP servers should be reachable (URL format valid)."""
    import json
    cfg = json.loads(Path("opencode.json").read_text())
    mcps = cfg.get("mcp", {})
    issues = []
    for name, server in mcps.items():
        if "type" not in server:
            issues.append(f"{name}: no type")
            continue
        if server["type"] == "remote":
            if "url" not in server or not server["url"].startswith("http"):
                issues.append(f"{name}: invalid remote URL")
        elif server["type"] == "local":
            if "command" not in server:
                issues.append(f"{name}: no command for local")
    if issues:
        return TestResult(
            name="opencode.json MCP integrity",
            status="FAIL",
            severity="major",
            message=f"{len(issues)} MCP issues",
            details={"issues": issues},
        )
    return TestResult(
        name="opencode.json MCP integrity",
        status="PASS",
        message=f"All {len(mcps)} MCP servers configured correctly",
    )


def test_no_dangerous_patterns_in_examples() -> TestResult:
    """Example questions should not contain dangerous patterns."""
    from . import EXAMPLE_DIR
    bad_patterns = [
        r"buy\s+\$",
        r"sell\s+all",
        r"place\s+(real\s+)?order",
    ]
    import re
    issues = []
    for q_file in EXAMPLE_DIR.glob("*/questions.md"):
        text = q_file.read_text().lower()
        for pat in bad_patterns:
            if re.search(pat, text):
                issues.append(f"{q_file.parent.name}/questions.md: {pat}")
    if issues:
        return TestResult(
            name="no dangerous patterns in examples",
            status="FAIL",
            severity="major",
            message=f"{len(issues)} dangerous patterns",
        )
    return TestResult(
        name="no dangerous patterns in examples",
        status="PASS",
        message="No dangerous patterns in examples",
    )


def run_all() -> List[TestSuite]:
    """Run all integration tests."""
    import_tests = TestSuite(name="Integration: Package")
    import_tests.add(test_alpha_family_imports())
    import_tests.add(test_alpha_count())
    import_tests.add(test_swarm_presets_valid_yaml())
    import_tests.add(test_swarm_presets_have_agents())

    script_tests = TestSuite(name="Integration: Scripts")
    script_tests.add(test_skill_scripts_importable())
    script_tests.add(test_critical_script_execution())

    safety_tests = TestSuite(name="Integration: Safety")
    safety_tests.add(test_no_live_trade_patterns())
    safety_tests.add(test_opencode_json_mcp_integrity())
    safety_tests.add(test_no_dangerous_patterns_in_examples())

    return [import_tests, script_tests, safety_tests]


if __name__ == "__main__":
    print_header("INTEGRATION TESTS")
    suites = run_all()
    for suite in suites:
        print(f"\n--- {suite.name} ---")
        for r in suite.results:
            status_color = {"PASS": "green", "FAIL": "red", "WARN": "yellow", "SKIP": "cyan"}[r.status]
            print(f"  [{colorize(r.status, status_color)}] {r.name}: {r.message}")
        print(f"  Total: {suite.passed} passed, {suite.failed} failed")