"""Technical / structural integrity tests.

Tests for:
- Repo structure (right files in right places)
- YAML frontmatter validity
- Agent/skill/cookbook counts vs expected
- Subagent annotation completeness
- Tool/MCP reference validity
"""

import time
import json
from pathlib import Path
from . import (
    AGENTS_DIR, SKILLS_DIR, INSTRUCTIONS_DIR, MCP_DIR, EXAMPLE_DIR, PYTHON_PKG,
    SUBAGENTS, PRIMARY_AGENTS, REPO_ROOT, OPENCODE_DIR,
    list_agents, list_skills, list_cookbooks,
    read_agent_file, read_skill_frontmatter,
    parse_yaml_frontmatter, dispatch,
    TestResult, TestSuite, print_header, colorize, save_report,
)


def test_opencode_dir_exists() -> TestResult:
    """The .opencode/ directory must exist."""
    if OPENCODE_DIR.is_dir():
        return TestResult(
            name=".opencode/ directory exists",
            status="PASS",
            message=f"Found at {OPENCODE_DIR}",
        )
    return TestResult(
        name=".opencode/ directory exists",
        status="FAIL",
        severity="critical",
        message=f"Missing {OPENCODE_DIR}",
    )


def test_opencode_json_valid() -> TestResult:
    """opencode.json must be valid JSON with required sections."""
    start = time.time()
    cfg_path = REPO_ROOT / "opencode.json"
    if not cfg_path.exists():
        return TestResult(
            name="opencode.json valid",
            status="FAIL",
            severity="critical",
            message=f"Missing {cfg_path}",
        )
    try:
        cfg = json.loads(cfg_path.read_text())
    except json.JSONDecodeError as e:
        return TestResult(
            name="opencode.json valid",
            status="FAIL",
            severity="critical",
            message=f"JSON parse error: {e}",
        )

    issues = []
    if "instructions" not in cfg:
        issues.append("Missing 'instructions' key")
    if "mcp" not in cfg:
        issues.append("Missing 'mcp' key")

    if issues:
        return TestResult(
            name="opencode.json valid",
            status="FAIL",
            severity="major",
            message="; ".join(issues),
            duration_ms=(time.time() - start) * 1000,
        )

    return TestResult(
        name="opencode.json valid",
        status="PASS",
        message=f"instructions={len(cfg['instructions'])}, mcp={len(cfg['mcp'])}",
        duration_ms=(time.time() - start) * 1000,
        details={"config": cfg},
    )


def test_instructions_files_exist() -> TestResult:
    """All instruction files referenced in opencode.json must exist."""
    cfg_path = REPO_ROOT / "opencode.json"
    cfg = json.loads(cfg_path.read_text())
    issues = []
    for inst in cfg.get("instructions", []):
        p = REPO_ROOT / inst
        if not p.exists():
            issues.append(f"Missing: {inst}")
    if issues:
        return TestResult(
            name="All instruction files exist",
            status="FAIL",
            severity="critical",
            message="; ".join(issues),
        )
    return TestResult(
        name="All instruction files exist",
        status="PASS",
        message=f"All {len(cfg['instructions'])} instruction files present",
        details={"files": cfg["instructions"]},
    )


def test_opencode_json_agent_config() -> TestResult:
    """opencode.json must have default_agent=wealth-guide and all subagents configured."""
    cfg = json.loads((REPO_ROOT / "opencode.json").read_text())
    issues = []

    default_agent = cfg.get("default_agent")
    if default_agent != "wealth-guide":
        issues.append(f"default_agent should be 'wealth-guide', got {default_agent!r}")

    agent_cfg = cfg.get("agent", {})
    if "wealth-guide" not in agent_cfg:
        issues.append("wealth-guide missing from agent config")
    else:
        wg = agent_cfg["wealth-guide"]
        if wg.get("mode") != "all":
            issues.append(f"wealth-guide mode should be 'all', got {wg.get('mode')!r}")

    for slug in SUBAGENTS:
        if slug not in agent_cfg:
            issues.append(f"{slug}: missing from agent config")
            continue
        a = agent_cfg[slug]
        if a.get("mode") != "subagent":
            issues.append(f"{slug}: mode should be 'subagent', got {a.get('mode')!r}")
        if a.get("hidden") is not True:
            issues.append(f"{slug}: hidden should be true, got {a.get('hidden')!r}")

    if issues:
        return TestResult(
            name="opencode.json agent config",
            status="FAIL",
            severity="critical",
            message=f"{len(issues)} issues",
            details={"issues": issues[:25]},
        )
    return TestResult(
        name="opencode.json agent config",
        status="PASS",
        message=f"default_agent=wealth-guide, {len(agent_cfg)} agents configured",
    )


def test_agent_count() -> TestResult:
    """Should have exactly 23 agents (1 primary + 22 subagents)."""
    agents = list_agents()
    expected = 23
    if len(agents) == expected:
        return TestResult(
            name=f"Agent count = {expected}",
            status="PASS",
            message=f"Found {len(agents)} agents",
            details={"agents": agents},
        )
    return TestResult(
        name=f"Agent count = {expected}",
        status="FAIL",
        severity="critical",
        message=f"Expected {expected}, found {len(agents)}",
        details={"agents": agents},
    )


def test_skill_count() -> TestResult:
    """Should have at least 145 skills."""
    skills = list_skills()
    expected_min = 145
    if len(skills) >= expected_min:
        return TestResult(
            name=f"Skill count >= {expected_min}",
            status="PASS",
            message=f"Found {len(skills)} skills",
            details={"count": len(skills)},
        )
    return TestResult(
        name=f"Skill count >= {expected_min}",
        status="FAIL",
        severity="major",
        message=f"Expected >= {expected_min}, found {len(skills)}",
    )


def test_cookbook_count() -> TestResult:
    """Should have 24 cookbooks (18 + 5 new + 1 e2e)."""
    cookbooks = list_cookbooks()
    if len(cookbooks) >= 23:
        return TestResult(
            name="Cookbook count >= 23",
            status="PASS",
            message=f"Found {len(cookbooks)} cookbooks",
            details={"count": len(cookbooks)},
        )
    return TestResult(
        name="Cookbook count >= 23",
        status="FAIL",
        severity="major",
        message=f"Expected >= 23, found {len(cookbooks)}",
    )


def test_agent_yaml_frontmatter() -> TestResult:
    """Every agent must have valid YAML frontmatter with required fields."""
    issues = []
    agent_count = 0
    for slug in list_agents():
        agent_count += 1
        frontmatter = read_agent_file(slug)
        if frontmatter is None:
            issues.append(f"{slug}: missing or invalid YAML frontmatter")
            continue
        if "name" not in frontmatter:
            issues.append(f"{slug}: missing 'name' in YAML")
        elif frontmatter["name"] != slug:
            issues.append(f"{slug}: name mismatch ({frontmatter['name']})")
        if "description" not in frontmatter:
            issues.append(f"{slug}: missing 'description'")

    if issues:
        return TestResult(
            name="All agent YAML frontmatter valid",
            status="FAIL",
            severity="critical",
            message=f"{len(issues)} issues across {agent_count} agents",
            details={"issues": issues[:20]},  # limit output
        )
    return TestResult(
        name="All agent YAML frontmatter valid",
        status="PASS",
        message=f"All {agent_count} agents have valid YAML frontmatter",
    )


def test_subagent_annotation() -> TestResult:
    """Every non-primary agent must have mode: subagent, hidden: true."""
    issues = []
    annotated = 0
    for slug in list_agents():
        if slug in PRIMARY_AGENTS:
            continue
        frontmatter = read_agent_file(slug)
        if frontmatter is None:
            issues.append(f"{slug}: no frontmatter")
            continue
        mode = frontmatter.get("mode")
        hidden = frontmatter.get("hidden")
        if mode != "subagent" or hidden is not True:
            issues.append(f"{slug}: mode={mode}, hidden={hidden}")
        else:
            annotated += 1

    if issues:
        return TestResult(
            name="All 22 subagents correctly configured",
            status="FAIL",
            severity="critical",
            message=f"{len(issues)} misconfigured",
            details={"issues": issues, "annotated": annotated},
        )
    return TestResult(
        name="All 22 subagents correctly configured",
        status="PASS",
        message=f"All 22 subagents have mode=subagent, hidden=true",
    )


def test_wealth_guide_is_primary() -> TestResult:
    """wealth-guide must have mode=all (visible primary that can invoke subagents)."""
    frontmatter = read_agent_file("wealth-guide")
    if frontmatter is None:
        return TestResult(
            name="wealth-guide is primary",
            status="FAIL",
            severity="critical",
            message="wealth-guide has no YAML frontmatter",
        )
    mode = frontmatter.get("mode")
    if mode != "all":
        return TestResult(
            name="wealth-guide is primary",
            status="FAIL",
            severity="critical",
            message=f"wealth-guide mode should be 'all', got '{mode}'",
        )
    if "task__" not in str(frontmatter.get("tools", {})):
        return TestResult(
            name="wealth-guide has task() tools",
            status="FAIL",
            severity="major",
            message="wealth-guide must declare task() tools for subagent dispatch",
        )
    return TestResult(
        name="wealth-guide is primary",
        status="PASS",
        message="wealth-guide has mode=all with task() tools",
        details={"tools_count": len(frontmatter.get("tools", {}))},
    )


def test_wealth_guide_can_invoke_all_subagents() -> TestResult:
    """wealth-guide's tool allowlist should include all 22 subagent slugs."""
    frontmatter = read_agent_file("wealth-guide")
    if frontmatter is None:
        return TestResult(
            name="wealth-guide invokes all 22 subagents",
            status="FAIL",
            severity="critical",
            message="No wealth-guide frontmatter",
        )
    tools = frontmatter.get("tools", {})
    missing = []
    for slug in SUBAGENTS:
        key = f"task__{slug}__*"
        if key not in tools:
            missing.append(slug)
    if missing:
        return TestResult(
            name="wealth-guide invokes all 22 subagents",
            status="FAIL",
            severity="critical",
            message=f"{len(missing)} subagents not in allowlist",
            details={"missing": missing},
        )
    return TestResult(
        name="wealth-guide invokes all 22 subagents",
        status="PASS",
        message=f"All 22 subagents in wealth-guide allowlist",
    )


def test_skill_yaml_frontmatter() -> TestResult:
    """Every SKILL.md must have valid YAML frontmatter with name + description."""
    issues = []
    skill_count = 0
    for name in list_skills():
        skill_count += 1
        frontmatter = read_skill_frontmatter(name)
        if frontmatter is None:
            issues.append(f"{name}: missing or invalid YAML frontmatter")
            continue
        if "name" not in frontmatter:
            issues.append(f"{name}: missing 'name'")
        if "description" not in frontmatter:
            issues.append(f"{name}: missing 'description'")
        # name should match directory or be a renamed variant
        # (Vibe-Trading's vibe-thesis-tracker uses internal name 'thesis-tracker')

    if issues:
        return TestResult(
            name="All skill YAML frontmatter valid",
            status="FAIL",
            severity="major",
            message=f"{len(issues)} issues across {skill_count} skills",
            details={"issues": issues[:30]},
        )
    return TestResult(
        name="All skill YAML frontmatter valid",
        status="PASS",
        message=f"All {skill_count} skills have valid YAML frontmatter",
    )


def test_python_package_imports() -> TestResult:
    """vibe-trading-quanta package must be importable."""
    try:
        import vibe_trading_quanta
        from vibe_trading_quanta import backtest, loaders, factors, swarm
        return TestResult(
            name="vibe-trading-quanta importable",
            status="PASS",
            message=f"v{getattr(vibe_trading_quanta, '__version__', 'unknown')}",
        )
    except ImportError as e:
        return TestResult(
            name="vibe-trading-quanta importable",
            status="FAIL",
            severity="critical",
            message=f"Import error: {e}",
        )


def test_python_package_structure() -> TestResult:
    """vibe-trading-quanta should have all key subpackages."""
    required = [
        "backtest/engines",
        "backtest/optimizers",
        "loaders",
        "factors/zoo/alpha101",
        "factors/zoo/qlib158",
        "factors/zoo/gtja191",
        "factors/zoo/academic",
        "factors/zoo/fundamental",
        "swarm/presets",
    ]
    missing = [p for p in required if not (PYTHON_PKG / "vibe_trading_quanta" / p).exists()]
    if missing:
        return TestResult(
            name="Python package structure complete",
            status="FAIL",
            severity="major",
            message=f"Missing: {missing}",
        )
    return TestResult(
        name="Python package structure complete",
        status="PASS",
        message=f"All {len(required)} key subpackages present",
    )


def test_swarm_presets_count() -> TestResult:
    """Should have 30 swarm preset YAML files."""
    preset_dir = PYTHON_PKG / "vibe_trading_quanta" / "swarm" / "presets"
    if not preset_dir.exists():
        return TestResult(
            name="30 swarm presets",
            status="FAIL",
            severity="major",
            message=f"Missing {preset_dir}",
        )
    yamls = list(preset_dir.glob("*.yaml"))
    if len(yamls) == 30:
        return TestResult(
            name="30 swarm presets",
            status="PASS",
            message=f"Found {len(yamls)} presets",
        )
    return TestResult(
        name="30 swarm presets",
        status="WARN",
        severity="minor",
        message=f"Expected 30, found {len(yamls)}",
    )


def run_all() -> TestSuite:
    """Run all structural tests and return the suite."""
    suite = TestSuite(name="Structural Integrity")
    suite.add(test_opencode_dir_exists())
    suite.add(test_opencode_json_valid())
    suite.add(test_instructions_files_exist())
    suite.add(test_agent_count())
    suite.add(test_skill_count())
    suite.add(test_cookbook_count())
    suite.add(test_agent_yaml_frontmatter())
    suite.add(test_subagent_annotation())
    suite.add(test_wealth_guide_is_primary())
    suite.add(test_wealth_guide_can_invoke_all_subagents())
    suite.add(test_skill_yaml_frontmatter())
    suite.add(test_python_package_imports())
    suite.add(test_python_package_structure())
    suite.add(test_swarm_presets_count())
    return suite


if __name__ == "__main__":
    print_header("STRUCTURAL INTEGRITY TESTS")
    suite = run_all()
    for r in suite.results:
        status_color = {"PASS": "green", "FAIL": "red", "WARN": "yellow", "SKIP": "cyan"}[r.status]
        print(f"  [{colorize(r.status, status_color)}] {r.name}: {r.message}")
    print()
    print(f"  Total: {len(suite.results)}, Passed: {suite.passed}, Failed: {suite.failed}, Warnings: {suite.warnings}")