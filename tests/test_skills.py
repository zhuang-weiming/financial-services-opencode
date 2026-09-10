"""Per-skill business tests.

For each of the 146 skills:
- SKILL.md file exists
- Valid YAML frontmatter
- Has name + description
- Description is meaningful (≥30 chars)
- Body has substantial content (≥50 chars for simple skills)
- No references to deprecated tooling
"""

import time
import re
from pathlib import Path
from typing import List
from . import (
    SKILLS_DIR, list_skills, read_skill_frontmatter,
    TestResult, TestSuite, print_header, colorize,
)

MIN_DESCRIPTION_LEN = 30
MIN_BODY_LEN = 50

# Skills that need extra description length
COMPLEX_SKILLS = {
    "earnings-analysis", "dcf-model", "lbo-model", "merger-model",
    "pitch-deck", "datapack-builder", "ic-memo", "initiating-coverage",
    "thesis-tracker", "investment-proposal", "value-creation-plan",
    "client-report", "client-review", "financial-plan",
    "competitive-analysis", "comps-analysis",
}


def test_skill_file_exists(name: str) -> TestResult:
    """SKILL.md file exists."""
    skill_file = SKILLS_DIR / name / "SKILL.md"
    if not skill_file.exists():
        return TestResult(
            name=f"skill file exists: {name}",
            status="FAIL",
            severity="critical",
            message=f"Missing: {skill_file}",
        )
    return TestResult(
        name=f"skill file exists: {name}",
        status="PASS",
        message=f"Found",
    )


def test_skill_yaml_valid(name: str) -> TestResult:
    """YAML frontmatter is valid."""
    fm = read_skill_frontmatter(name)
    if fm is None:
        return TestResult(
            name=f"skill yaml valid: {name}",
            status="FAIL",
            severity="critical",
            message="Missing or invalid YAML frontmatter",
        )

    issues = []
    if "name" not in fm:
        issues.append("missing 'name'")
    if "description" not in fm:
        issues.append("missing 'description'")

    if issues:
        return TestResult(
            name=f"skill yaml valid: {name}",
            status="FAIL",
            severity="major",
            message="; ".join(issues),
        )
    return TestResult(
        name=f"skill yaml valid: {name}",
        status="PASS",
        message=f"name={fm.get('name')}",
    )


def test_skill_description(name: str) -> TestResult:
    """Skill description is meaningful and non-trivial."""
    fm = read_skill_frontmatter(name)
    if fm is None or "description" not in fm:
        return TestResult(
            name=f"skill description: {name}",
            status="FAIL",
            severity="major",
            message="No description",
        )

    desc = str(fm.get("description", ""))
    if len(desc) < MIN_DESCRIPTION_LEN:
        return TestResult(
            name=f"skill description: {name}",
            status="FAIL",
            severity="major",
            message=f"Too short ({len(desc)} chars < {MIN_DESCRIPTION_LEN})",
            details={"description": desc},
        )
    return TestResult(
        name=f"skill description: {name}",
        status="PASS",
        message=f"Length: {len(desc)} chars",
    )


def test_skill_body(name: str) -> TestResult:
    """Skill body has meaningful content."""
    skill_file = SKILLS_DIR / name / "SKILL.md"
    if not skill_file.exists():
        return TestResult(
            name=f"skill body: {name}",
            status="FAIL",
            severity="critical",
            message="No file",
        )

    text = skill_file.read_text()
    parts = text.split("---", 2)
    body = parts[2].strip() if len(parts) >= 3 else ""

    if len(body) < MIN_BODY_LEN:
        return TestResult(
            name=f"skill body: {name}",
            status="FAIL",
            severity="major",
            message=f"Body too short ({len(body)} chars < {MIN_BODY_LEN})",
        )
    return TestResult(
        name=f"skill body: {name}",
        status="PASS",
        message=f"Body: {len(body)} chars",
    )


def test_skill_no_broken_imports(name: str) -> TestResult:
    """Skill must not reference agent.src.tools (Vibe-Trading internal)."""
    skill_file = SKILLS_DIR / name / "SKILL.md"
    if not skill_file.exists():
        return TestResult(
            name=f"skill no broken imports: {name}",
            status="FAIL",
            severity="critical",
            message="No file",
        )

    text = skill_file.read_text()
    # Look for actual code patterns, not prose
    # Real import patterns: "from agent.X import Y" or "import agent.X" in code blocks
    bad_patterns = [
        r"^from\s+agent\s+import",
        r"^from\s+agent\.\w+\s+import",
        r"^import\s+agent\.\w+",
        r"`from\s+agent\.",
        r"`import\s+agent\.",
    ]
    found = []
    for line in text.split("\n"):
        for pattern in bad_patterns:
            if re.search(pattern, line):
                found.append(line.strip()[:80])
                break
    if found:
        return TestResult(
            name=f"skill no broken imports: {name}",
            status="WARN",
            severity="minor",
            message=f"References internal imports: {len(found)}",
            details={"lines": found[:5]},
        )
    return TestResult(
        name=f"skill no broken imports: {name}",
        status="PASS",
        message="No broken internal imports",
    )


def run_skill_tests_for(name: str) -> List[TestResult]:
    """Run all skill tests for a given skill name."""
    return [
        test_skill_file_exists(name),
        test_skill_yaml_valid(name),
        test_skill_description(name),
        test_skill_body(name),
        test_skill_no_broken_imports(name),
    ]


# ---------------------------------------------------------------------------
# Routing coverage — every routable skill must appear in router/agent files
# ---------------------------------------------------------------------------

def test_skill_routing_coverage() -> TestResult:
    """Assert 0 routable-but-unregistered skills (see gen_skill_manifest.py)."""
    import re
    from tests import SKILLS_DIR
    # Tool/meta skills exempt from routing; _shared is an internal resource dir
    TOOL_SKILLS = {
        "docx", "pdf", "xlsx", "pptx", "clean-data-xls", "ppt-template-creator",
        "skill-creator", "customize-opencode", "xlsx-author", "pptx-author",
        "vibe-trading-doc-reader", "vibe-trading-web-reader",
    }
    INTERNAL = {"_shared"}
    repo = SKILLS_DIR.parent.parent
    targets = []
    for pat in [".opencode/instructions/*.md", ".opencode/agents/**/*.md",
                "opencode.json", "README.md"]:
        targets += list(repo.glob(pat))
    text = ""
    for t in targets:
        try:
            text += t.read_text(errors="ignore")
        except Exception:
            pass

    skills = [d.name for d in SKILLS_DIR.iterdir() if d.is_dir()]
    actionable = []
    for name in skills:
        if name in TOOL_SKILLS or name in INTERNAL:
            continue
        if not (SKILLS_DIR / name / "SKILL.md").exists():
            continue
        if not re.search(r"(?<![a-z0-9-])" + re.escape(name) + r"(?![a-z0-9-])", text):
            actionable.append(name)

    if actionable:
        return TestResult(
            name="routing_coverage",
            status="FAIL",
            message=f"{len(actionable)} routable skill(s) not registered: "
                    + ", ".join(actionable[:8]) + ("..." if len(actionable) > 8 else ""),
        )
    return TestResult(
        name="routing_coverage",
        status="PASS",
        message=f"all {len(skills)} skills routable (0 unregistered)",
    )


def test_skill_manifest_fresh() -> TestResult:
    """Assert skill-manifest.md exists and covers all skills."""
    import re
    from tests import SKILLS_DIR
    manifest = SKILLS_DIR.parent / "instructions" / "skill-manifest.md"
    if not manifest.exists():
        return TestResult(name="skill_manifest", status="FAIL", message="skill-manifest.md missing")
    txt = manifest.read_text(errors="ignore")
    n_skills = len([d for d in SKILLS_DIR.iterdir()
                    if d.is_dir() and (d / "SKILL.md").exists()])
    m = re.search(r"共 \*\*(\d+)\*\* 个 skill", txt)
    if not m:
        return TestResult(name="skill_manifest", status="WARN", message="count line not found in manifest")
    n_doc = int(m.group(1))
    if n_doc != n_skills:
        return TestResult(name="skill_manifest", status="FAIL",
                          message=f"manifest stale: {n_doc} documented vs {n_skills} on disk")
    return TestResult(name="skill_manifest", status="PASS", message=f"{n_doc} skills documented")


def run_all_skills() -> TestSuite:
    """Run per-skill tests for all 146 skills."""
    suite = TestSuite(name="Per-Skill Business Tests")
    suite.add(test_skill_routing_coverage())
    suite.add(test_skill_manifest_fresh())
    for name in list_skills():
        for result in run_skill_tests_for(name):
            suite.add(result)
    return suite


if __name__ == "__main__":
    print_header("PER-SKILL TESTS")
    suite = run_all_skills()
    for r in suite.results[:50]:  # show first 50
        status_color = {"PASS": "green", "FAIL": "red", "WARN": "yellow", "SKIP": "cyan"}[r.status]
        print(f"  [{colorize(r.status, status_color)}] {r.name}: {r.message}")
    print(f"\n  ... ({len(suite.results) - 50} more)")
    print(f"\n  Total: {len(suite.results)}, Passed: {suite.passed}, Failed: {suite.failed}")