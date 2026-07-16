#!/usr/bin/env python3
"""
Standalone test runner for financial-services-opencode.

Runs all test suites and produces a summary report.

Usage:
    python tests/run_all.py
    python tests/run_all.py --suite structural
    python tests/run_all.py --output report.json
"""

import sys
import os
import argparse
import time
from pathlib import Path

# Make sure we can import from tests/
REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT))

from tests import print_header, colorize, save_report, TestSuite
from tests.test_structural import run_all as run_structural
from tests.test_routing import run_all as run_routing
from tests.test_agents import run_all_agents
from tests.test_skills import run_all_skills
from tests.test_pipeline import run_all as run_pipeline
from tests.test_business_acceptance import run_all as run_business_acceptance
from tests.test_integration import run_all as run_integration


def main():
    parser = argparse.ArgumentParser(description="Run all tests")
    parser.add_argument(
        "--suite",
        choices=["all", "structural", "routing", "agents", "skills", "pipeline", "business", "integration"],
        default="all",
    )
    parser.add_argument("--output", default=None, help="Path to save JSON report")
    args = parser.parse_args()

    print_header("financial-services-opencode TEST RUNNER", "=")
    print(f"Repo: {REPO_ROOT}")
    print(f"Suite: {args.suite}")
    print(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")

    all_suites = []

    if args.suite in ("all", "structural"):
        suite = run_structural()
        all_suites.append(suite)

    if args.suite in ("all", "routing"):
        suites = run_routing()
        all_suites.extend(suites)

    if args.suite in ("all", "agents"):
        suite = run_all_agents()
        all_suites.append(suite)

    if args.suite in ("all", "skills"):
        suite = run_all_skills()
        all_suites.append(suite)

    if args.suite in ("all", "pipeline"):
        suites = run_pipeline()
        all_suites.extend(suites)

    if args.suite in ("all", "business"):
        suites = run_business_acceptance()
        all_suites.extend(suites)

    if args.suite in ("all", "integration"):
        suites = run_integration()
        all_suites.extend(suites)

    # Print detailed results
    for suite in all_suites:
        print_header(f"SUITE: {suite.name}", "-")
        for r in suite.results:
            status_color = {"PASS": "green", "FAIL": "red", "WARN": "yellow", "SKIP": "cyan"}[r.status]
            duration = f" ({r.duration_ms:.1f}ms)" if r.duration_ms > 0 else ""
            severity = f" [{r.severity}]" if r.severity != "normal" else ""
            print(f"  [{colorize(r.status, status_color)}] {r.name}{severity}: {r.message}{duration}")

    # Summary
    print_header("SUMMARY", "=")
    total_pass = sum(s.passed for s in all_suites)
    total_fail = sum(s.failed for s in all_suites)
    total_warn = sum(s.warnings for s in all_suites)
    total_skip = sum(s.skipped for s in all_suites)
    total_tests = sum(len(s.results) for s in all_suites)

    # Categorize failures by severity
    critical_fails = []
    major_fails = []
    minor_fails = []
    for s in all_suites:
        for r in s.results:
            if r.status == "FAIL":
                if r.severity == "critical":
                    critical_fails.append(r)
                elif r.severity == "major":
                    major_fails.append(r)
                else:
                    minor_fails.append(r)

    print(f"  Total tests:  {total_tests}")
    print(f"  {colorize('Passed:', 'green')}    {total_pass}")
    print(f"  {colorize('Failed:', 'red')}    {total_fail}")
    print(f"  Warnings:  {total_warn}")
    print(f"  Skipped:   {total_skip}")
    print()
    print(f"  Critical failures: {len(critical_fails)}")
    print(f"  Major failures:    {len(major_fails)}")
    print(f"  Minor failures:    {len(minor_fails)}")

    if critical_fails:
        print()
        print_header("CRITICAL FAILURES", "!")
        for r in critical_fails:
            print(f"  - {r.name}: {r.message}")
            if r.details:
                for k, v in r.details.items():
                    if isinstance(v, list) and len(v) > 5:
                        print(f"      {k}: {v[:5]} ... (and {len(v)-5} more)")
                    else:
                        print(f"      {k}: {v}")

    if major_fails:
        print()
        print_header("MAJOR FAILURES", "!")
        for r in major_fails:
            print(f"  - {r.name}: {r.message}")

    # Save report
    if args.output:
        report_path = REPO_ROOT / "tests" / "reports" / args.output
        report_path.parent.mkdir(exist_ok=True)
        save_report(all_suites, report_path)
        print(f"\n  Report saved: {report_path}")

    # Exit code
    sys.exit(0 if total_fail == 0 else 1)


if __name__ == "__main__":
    main()