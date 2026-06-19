"""Health guard for the incubated AgentOps tool."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REQUIRED_DOCS = [
    "README.md",
    "BLUEPRINT.md",
    "GOVERNANCE.md",
    "RULEBOOK.md",
    "FRUGALITY.md",
    "THREAT_MODEL.md",
    "EXTRACTION_CONTRACT.md",
    "ROADMAP.md",
    "PENDING.md",
    "INTEGRATIONS.md",
    "TOOL_MANIFEST.json",
    "pyproject.toml",
    "integrations/vscode/tasks.json",
    "integrations/cursor/rules/agentops.mdc",
    "integrations/mcp/server_contract.json",
]
FORBIDDEN_MARKERS = [
    "begin leaked prompt",
    "end leaked prompt",
    "verbatim system prompt",
    "jailbreak payload:",
    "ignore safety policy",
]


@dataclass(frozen=True)
class Finding:
    severity: str
    message: str


def check_required_docs() -> list[Finding]:
    findings: list[Finding] = []
    for rel_path in REQUIRED_DOCS:
        path = ROOT / rel_path
        if not path.is_file():
            findings.append(Finding("error", f"missing required document: {rel_path}"))
    return findings


def check_manifest() -> list[Finding]:
    path = ROOT / "TOOL_MANIFEST.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        return [Finding("error", f"invalid manifest: {exc}")]
    if data.get("extractable") is not True:
        return [Finding("error", "manifest must declare extractable=true")]
    if data.get("relationship_to_continuity") != "none":
        return [Finding("error", "AgentOps must remain independent from Continuity runtime")]
    return []


def check_forbidden_text() -> list[Finding]:
    findings: list[Finding] = []
    for path in ROOT.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in {".md", ".json", ".py", ".txt"}:
            continue
        if path == Path(__file__).resolve():
            continue
        text = path.read_text(encoding="utf-8", errors="replace").lower()
        for marker in FORBIDDEN_MARKERS:
            if marker in text:
                findings.append(Finding("warning", f"review wording in {path.relative_to(ROOT)}: {marker}"))
    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="AgentOps incubation health guard.")
    parser.add_argument("--strict", action="store_true", help="Treat warnings as errors.")
    args = parser.parse_args(argv)

    findings = check_required_docs() + check_manifest() + check_forbidden_text()
    for finding in findings:
        print(f"{finding.severity.upper()}: {finding.message}")

    if not findings:
        print("agentops-health: ok")
        return 0
    if any(f.severity == "error" for f in findings):
        return 1
    if args.strict and any(f.severity == "warning" for f in findings):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
