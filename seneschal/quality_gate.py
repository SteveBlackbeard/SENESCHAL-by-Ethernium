"""Cheap response quality checks after a model call."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from .prompt_firewall import classify_text


@dataclass(frozen=True)
class QualityReport:
    ok: bool
    score: int
    findings: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "score": self.score,
            "findings": list(self.findings),
        }


def evaluate_response(objective: str, response_text: str) -> QualityReport:
    findings: list[str] = []
    stripped = response_text.strip()
    if not stripped:
        findings.append("empty-response")
    if len(stripped) < 20:
        findings.append("very-short-response")
    if re.search(r"\b(as an ai|i cannot help|i can't help|i am unable)\b", stripped, re.IGNORECASE):
        findings.append("likely-refusal-or-evasion")

    risk = classify_text(stripped, source="generated")
    if risk.blocked:
        findings.append("generated-output-risk")

    objective_terms = _terms(objective)
    if objective_terms and not (objective_terms & _terms(stripped)):
        findings.append("low-objective-overlap")

    score = max(0, 100 - (len(findings) * 25))
    return QualityReport(ok=score >= 75, score=score, findings=tuple(findings))


def _terms(text: str) -> set[str]:
    return {item for item in re.findall(r"[a-zA-Z0-9_]{4,}", text.lower()) if item not in {"this", "that", "with", "from", "your", "para", "como"}}
