#!/usr/bin/env python3
"""AutoGen-style deterministic conversation stub."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from safety import review_objective


def build_conversation(objective: str, scope: str) -> dict:
    review = review_objective(objective, scope)
    messages = [
        {
            "speaker": "requester",
            "message": f"Objective: {objective}",
        },
        {
            "speaker": "safety-reviewer",
            "message": "Authorized scope must be documented before sensitive actions.",
        },
    ]

    if review.allowed:
        messages.append(
            {
                "speaker": "technical-planner",
                "message": "Proceed with a defensive plan, evidence checklist, and rollback criteria.",
            }
        )
        status = "planned"
    else:
        messages.append(
            {
                "speaker": "technical-planner",
                "message": "Decline unsafe execution and redirect to a controlled lab or defensive checklist.",
            }
        )
        status = "blocked"

    return {
        "agent": "autogen-stub",
        "status": status,
        "scope": scope or "scope-required-before-sensitive-execution",
        "messages": messages,
        "safety_notes": review.notes,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Safe AutoGen-style agent stub.")
    parser.add_argument("--objective", required=True)
    parser.add_argument("--scope", default="")
    args = parser.parse_args()

    print(json.dumps(build_conversation(args.objective, args.scope), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
