#!/usr/bin/env python3
"""CrewAI-style planning stub with safe defaults."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from safety import review_objective


def build_plan(objective: str, scope: str) -> dict:
    review = review_objective(objective, scope)
    if not review.allowed:
        return {
            "agent": "crewai-stub",
            "status": "blocked",
            "objective": objective,
            "scope": scope,
            "safety_notes": review.notes,
            "safe_alternative": [
                "Define a local lab or owned staging target.",
                "Document authorization and permitted assets.",
                "Run defensive checks and produce a remediation report.",
            ],
        }

    return {
        "agent": "crewai-stub",
        "status": "planned",
        "objective": objective,
        "scope": scope or "scope-required-before-sensitive-execution",
        "crew": [
            {
                "role": "scope-coordinator",
                "task": "Confirm authorization, assets, dates, and stop conditions.",
            },
            {
                "role": "defensive-analyst",
                "task": "Prepare checklist, expected evidence, and risk controls.",
            },
            {
                "role": "report-writer",
                "task": "Summarize findings, limitations, and remediation steps.",
            },
        ],
        "safety_notes": review.notes,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Safe CrewAI-style agent stub.")
    parser.add_argument("--objective", required=True)
    parser.add_argument("--scope", default="")
    args = parser.parse_args()

    print(json.dumps(build_plan(args.objective, args.scope), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
