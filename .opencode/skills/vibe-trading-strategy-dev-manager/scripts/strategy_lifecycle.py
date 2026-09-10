#!/usr/bin/env python3
"""Strategy development lifecycle manager."""

import argparse
import json
from pathlib import Path
from datetime import datetime

OUTPUT_DIR = Path("out")
OUTPUT_DIR.mkdir(exist_ok=True)

VALID_STAGES = ["idea", "paper", "factor", "backtest", "monitoring", "decayed", "disabled"]


def get_lifecycle_strategy(name=None):
    """Get or create a strategy tracking entry."""
    strategies_file = OUTPUT_DIR / "strategies.json"
    if strategies_file.exists():
        strategies = json.loads(strategies_file.read_text())
    else:
        strategies = {}

    if name:
        if name not in strategies:
            strategies[name] = {
                "stage": "idea",
                "created": datetime.now().isoformat(),
                "updated": datetime.now().isoformat(),
                "notes": [],
            }
        return {name: strategies[name]}
    return strategies


def advance_stage(name, new_stage, note=None):
    """Advance a strategy to the next lifecycle stage."""
    strategies_file = OUTPUT_DIR / "strategies.json"
    if strategies_file.exists():
        strategies = json.loads(strategies_file.read_text())
    else:
        strategies = {}

    if name not in strategies:
        strategies[name] = {"stage": "idea", "created": datetime.now().isoformat(), "notes": []}

    old_stage = strategies[name]["stage"]
    if new_stage not in VALID_STAGES:
        return {"error": f"Invalid stage: {new_stage}. Valid: {VALID_STAGES}"}

    strategies[name]["stage"] = new_stage
    strategies[name]["updated"] = datetime.now().isoformat()
    if note:
        strategies[name]["notes"].append({"timestamp": datetime.now().isoformat(), "note": note})

    strategies_file.write_text(json.dumps(strategies, indent=2))
    return {"name": name, "old_stage": old_stage, "new_stage": new_stage, "note": note}


def main():
    parser = argparse.ArgumentParser(description="Strategy lifecycle manager")
    parser.add_argument("action", choices=["list", "create", "advance"])
    parser.add_argument("--name", default=None)
    parser.add_argument("--stage", default="idea")
    parser.add_argument("--note", default=None)
    parser.add_argument("--output", default=None)
    args = parser.parse_args()

    if args.action == "list":
        result = get_lifecycle_strategy()
    elif args.action == "create":
        if not args.name:
            result = {"error": "--name required for create"}
        else:
            result = get_lifecycle_strategy(args.name)
    elif args.action == "advance":
        if not args.name or not args.stage:
            result = {"error": "--name and --stage required for advance"}
        else:
            result = advance_stage(args.name, args.stage, args.note)
    else:
        result = {"error": "Unknown action"}

    output = json.dumps(result, indent=2, default=str)
    if args.output:
        path = OUTPUT_DIR / args.output
        path.write_text(output)
        print(f"Written to {path}")
    else:
        print(output)


if __name__ == "__main__":
    main()
