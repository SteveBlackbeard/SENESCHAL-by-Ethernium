"""Lightweight defensive prompt-risk classifier."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


INJECTION_MARKERS = (
    "ignore previous instructions",
    "ignore all previous",
    "disregard previous instructions",
    "disregard all prior",
    "prior rules",
    "override the system",
    "system prompt",
    "developer message",
    "reveal your instructions",
    "reveal hidden",
    "hidden policy",
    "print the hidden",
    "do not tell the user",
    "run this command",
    "exfiltrate",
    "tool call",
    "send the contents",
)

ZERO_WIDTH = ("\u200b", "\u200c", "\u200d", "\ufeff")
TEXT_SUFFIXES = {".md", ".txt", ".json", ".toml", ".yaml", ".yml", ".py", ".ts", ".tsx", ".js", ".jsx", ".css"}
IGNORED_DIRS = {
    ".git",
    ".venv",
    ".seneschal",
    "__pycache__",
    ".pytest_cache",
    "node_modules",
    "dist",
    "build",
    ".next",
}
SECRET_PATTERNS = (
    ("private key block", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("openai-like key", re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b")),
    ("github token", re.compile(r"\b(?:ghp|gho|github_pat)_[A-Za-z0-9_]{20,}\b")),
    ("aws access key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("generic api key assignment", re.compile(r"(?i)\b(api[_-]?key|secret[_-]?key|token)\s*[:=]\s*['\"]?[A-Za-z0-9_./+=-]{12,}")),
)


@dataclass(frozen=True)
class PromptRisk:
    source: str
    trust: str
    score: int
    findings: tuple[str, ...]

    @property
    def blocked(self) -> bool:
        return self.score >= 3

    @property
    def severity(self) -> str:
        if self.blocked:
            return "block"
        if self.score:
            return "warning"
        return "info"


@dataclass(frozen=True)
class FileRisk:
    path: str
    risk: PromptRisk


@dataclass(frozen=True)
class ScanSummary:
    files_scanned: int
    blocked: int
    warnings: int
    findings: tuple[FileRisk, ...]

    @property
    def has_blockers(self) -> bool:
        return self.blocked > 0


def classify_text(text: str, *, source: str = "external") -> PromptRisk:
    lowered = text.lower()
    findings: list[str] = []
    for marker in INJECTION_MARKERS:
        if marker in lowered:
            findings.append(f"injection marker: {marker}")
    if any(char in text for char in ZERO_WIDTH):
        findings.append("hidden unicode marker")
    for label, pattern in SECRET_PATTERNS:
        if pattern.search(text):
            findings.append(f"possible secret material: {label}")
    if "http://" in lowered or "https://" in lowered:
        findings.append("external link present")

    trust = "low" if source in {"external", "web", "pdf", "ocr", "generated"} else "medium"
    score = len(findings)
    if trust == "low" and findings:
        score += 1
    if trust == "low" and any(finding.startswith("injection marker:") for finding in findings):
        score += 1
    if any(finding.startswith("possible secret material:") for finding in findings):
        score += 2
    return PromptRisk(source=source, trust=trust, score=score, findings=tuple(findings))


def classify_file(path: Path, *, source: str = "external") -> PromptRisk:
    text = path.read_text(encoding="utf-8", errors="replace")
    return classify_text(text, source=source)


def scan_path(path: Path, *, source: str = "external") -> ScanSummary:
    paths = list(_iter_scan_files(path))
    findings: list[FileRisk] = []
    blocked = 0
    warnings = 0
    for item in paths:
        risk = classify_file(item, source=source)
        if risk.findings:
            findings.append(FileRisk(path=item.as_posix(), risk=risk))
        if risk.blocked:
            blocked += 1
        elif risk.score:
            warnings += 1
    return ScanSummary(files_scanned=len(paths), blocked=blocked, warnings=warnings, findings=tuple(findings))


def _iter_scan_files(path: Path) -> list[Path]:
    if path.is_file():
        return [path] if path.suffix.lower() in TEXT_SUFFIXES else []
    if not path.is_dir():
        raise FileNotFoundError(path)
    files: list[Path] = []
    for item in path.rglob("*"):
        if any(part in IGNORED_DIRS for part in item.parts):
            continue
        if item.is_file() and item.suffix.lower() in TEXT_SUFFIXES:
            files.append(item)
    return sorted(files)
