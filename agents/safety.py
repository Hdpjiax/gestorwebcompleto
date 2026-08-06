"""Shared safety helpers for local agent stubs."""

from __future__ import annotations

from dataclasses import dataclass


BLOCKED_TERMS = (
    "bypass",
    "credential theft",
    "exfiltrate",
    "steal cookies",
    "malware",
    "ransomware",
    "phishing",
    "persistence",
    "evade detection",
    "evasion",
)


@dataclass(frozen=True)
class SafetyReview:
    allowed: bool
    notes: list[str]


def review_objective(objective: str, scope: str = "") -> SafetyReview:
    text = f"{objective} {scope}".lower()
    matched = [term for term in BLOCKED_TERMS if term in text]
    if matched:
        return SafetyReview(
            allowed=False,
            notes=[
                "Objective contains terms associated with unauthorized or evasive activity.",
                f"Matched terms: {', '.join(matched)}.",
                "Offer a controlled lab, defensive checklist, or compliance-oriented alternative.",
            ],
        )

    if not scope.strip():
        return SafetyReview(
            allowed=True,
            notes=[
                "No explicit scope was provided.",
                "Before sensitive execution, require authorization, asset list, dates, and owner.",
            ],
        )

    return SafetyReview(
        allowed=True,
        notes=[
            "Objective is acceptable for planning or documentation.",
            "Keep execution limited to the documented authorized scope.",
        ],
    )
