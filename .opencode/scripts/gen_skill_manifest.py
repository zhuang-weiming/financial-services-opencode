#!/usr/bin/env python3
"""
gen_skill_manifest.py — 从所有 SKILL.md frontmatter 自动生成 skill 清单。

解决的问题：184 个 skill 不可能手工逐条路由注册。本脚本把每个 SKILL.md 的
frontmatter（name + description + category）解析出来，生成统一清单
`.opencode/instructions/skill-manifest.md`，供 wealth-guide 及其 subagent 按
意图语义匹配（而非要求用户记住 skill 名）。

用法:
    python3 .opencode/scripts/gen_skill_manifest.py            # 生成清单
    python3 .opencode/scripts/gen_skill_manifest.py --check    # 仅检查覆盖率(CI)

覆盖率检查逻辑:
    - 每个 skill 是否在 manifest 中 (应 100%)
    - 每个 skill 是否在任一 agent/instruction 文件中被引用 (routing coverage)
    - 未覆盖的 skill 会被列出并分类 (可路由 / 工具类 / 无 frontmatter)
"""
from __future__ import annotations
import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]          # repo root
SKILLS_DIR = ROOT / ".opencode" / "skills"
OUT = ROOT / ".opencode" / "instructions" / "skill-manifest.md"

# 非路由目标（工具/元 skill）—— 不计入 routing coverage 缺口
TOOL_SKILLS = {
    "docx", "pdf", "xlsx", "pptx", "clean-data-xls", "ppt-template-creator",
    "skill-creator", "customize-opencode", "xlsx-author", "pptx-author",
    "vibe-trading-doc-reader", "vibe-trading-web-reader",
}
# 已知损坏 / 无 SKILL.md
KNOWN_BROKEN = {"_shared"}   # _shared = 内部共享资源目录(非 skill)


def parse_frontmatter(path: Path) -> dict:
    txt = path.read_text(errors="ignore")
    m = re.match(r"^---\n(.*?)\n---", txt, re.DOTALL)
    if not m:
        return {}
    fm = {}
    for line in m.group(1).splitlines():
        mm = re.match(r"^([a-zA-Z_]+):\s*(.*)$", line)
        if mm:
            fm[mm.group(1)] = mm.group(2).strip().strip('"\'')
    return fm


def collect_skills() -> list[dict]:
    rows = []
    for d in sorted(SKILLS_DIR.iterdir()):
        if not d.is_dir():
            continue
        sk = d / "SKILL.md"
        if not sk.exists():
            rows.append({"dir": d.name, "name": d.name, "desc": "", "category": "",
                         "broken": True})
            continue
        fm = parse_frontmatter(sk)
        rows.append({
            "dir": d.name,
            "name": fm.get("name", d.name),
            "desc": fm.get("description", ""),
            "category": fm.get("category", ""),
            "broken": False,
        })
    return rows


def routing_coverage(rows: list[dict]) -> tuple[list, list]:
    """检查每个 skill 是否在 agent/instruction 中被引用。"""
    targets = []
    for pat in [".opencode/instructions/*.md", ".opencode/agents/**/*.md",
                "opencode.json", "README.md"]:
        targets += list(ROOT.glob(pat))
    text = ""
    for t in targets:
        try:
            text += t.read_text(errors="ignore")
        except Exception:
            pass
    covered, uncovered = [], []
    for r in rows:
        # 同时匹配目录名与 frontmatter name
        names = {r["dir"], r["name"]}
        hit = any(re.search(r"(?<![a-z0-9-])" + re.escape(n) + r"(?![a-z0-9-])", text)
                  for n in names if n)
        (covered if hit else uncovered).append(r)
    return covered, uncovered


def classify(rows: list[dict]) -> dict:
    buckets = {"vibe-trading": [], "llmquant": [], "bare": []}
    for r in rows:
        d = r["dir"]
        if d.startswith("vibe-trading-"):
            buckets["vibe-trading"].append(r)
        elif d.startswith("llmquant-"):
            buckets["llmquant"].append(r)
        else:
            buckets["bare"].append(r)
    return buckets


def write_manifest(rows: list[dict]):
    buckets = classify(rows)
    broken = [r for r in rows if r.get("broken")]
    real = len(rows) - len(broken)
    note = f"（另有 {len(broken)} 个损坏/无 SKILL.md 目录未计入）" if broken else ""
    lines = [
        "# Skill Manifest — 全量 skill 自动清单",
        "",
        "> **自动生成，请勿手工编辑。** 重新生成：`python3 .opencode/scripts/gen_skill_manifest.py`",
        f"> 共 **{real}** 个 skill（vibe-trading {len(buckets['vibe-trading'])} / "
        f"llmquant {len(buckets['llmquant'])} / 其他 {len(buckets['bare']) - len(broken)}）{note}",
        "",
        "## 使用方式（给 wealth-guide 及 subagent）",
        "",
        "**用户不需要记住 skill 名。** 路由流程：",
        "1. 用户表达**意图**（如「分析这只股票的趋势」「查一下 FRED 的 CPI」）",
        "2. wealth-guide 按意图匹配下方清单的 `description` → 选定 subagent",
        "3. subagent 用 `skill(\"<name>\")` 加载对应 skill",
        "",
        "> 本清单是**发现层**（有什么可用）；`wealth-guide-router.md` 是**决策层**"
        "（意图 → subagent 的权威映射）。两者互补：清单保证零遗漏，路由表保证高质量。",
        "",
        "---",
        "",
    ]
    for bucket, label in [("vibe-trading", "Vibe-Trading Skills"),
                          ("llmquant", "LLMQuant Skills"),
                          ("bare", "Repo-local / Anthropic Skills")]:
        lines.append(f"## {label} ({len(buckets[bucket])})")
        lines.append("")
        lines.append("| skill | description |")
        lines.append("|---|---|")
        for r in buckets[bucket]:
            if r.get("broken"):
                lines.append(f"| `{r['dir']}` | ⚠️ 无 SKILL.md（损坏）|")
                continue
            desc = r["desc"].replace("|", "\\|").replace("\n", " ")
            if len(desc) > 160:
                desc = desc[:157] + "..."
            lines.append(f"| `{r['name']}` | {desc} |")
        lines.append("")
    OUT.write_text("\n".join(lines))
    return len(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="仅检查覆盖率，不写文件")
    args = ap.parse_args()

    rows = collect_skills()
    covered, uncovered = routing_coverage(rows)

    print(f"总 skill: {len(rows)}")
    print(f"路由已覆盖: {len(covered)}")
    print(f"未覆盖: {len(uncovered)}")

    actionable = [r for r in uncovered
                  if r["dir"] not in TOOL_SKILLS and r["dir"] not in KNOWN_BROKEN
                  and not r.get("broken")]
    tool = [r for r in uncovered if r["dir"] in TOOL_SKILLS]
    broken = [r for r in rows if r.get("broken")]

    print(f"\n  ├─ 可路由但未注册: {len(actionable)}")
    print(f"  ├─ 工具/元 skill (豁免): {len(tool)}")
    print(f"  └─ 损坏/无 SKILL.md: {len(broken)}")

    if actionable:
        print("\n=== 可路由但未注册 (建议补入 wealth-guide-router.md) ===")
        for r in actionable:
            print(f"  {r['dir']:45s} | {r['desc'][:70]}")

    if broken:
        print("\n=== 损坏 (无 SKILL.md) ===")
        for r in broken:
            print(f"  {r['dir']}")

    if not args.check:
        n = write_manifest(rows)
        print(f"\n✅ manifest 已写入 {OUT.relative_to(ROOT)} "
              f"({n - len(broken)} skills, {len(broken)} broken excluded)")

    # CI 模式：可路由未注册 > 0 则非零退出
    if args.check and actionable:
        print(f"\n❌ routing coverage 缺口: {len(actionable)} 个可路由 skill 未注册")
        sys.exit(1)
    if args.check:
        print("\n✅ routing coverage OK")
    sys.exit(0)


if __name__ == "__main__":
    main()
