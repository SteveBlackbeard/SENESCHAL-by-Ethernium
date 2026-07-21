"""One command, one verdict: is it safe to send this to a model, and how.

An agent about to call a model on a path needs three questions answered
together, not in three separate invocations it has to stitch itself:

  1. Is the input safe?      (prompt injection / secret material)
  2. What should I send?     (relevant files under a token budget)
  3. Which model deserves it? (cheapest sufficient route)

`audit_path` answers all three and collapses them into a single machine-readable
verdict with a proceed / block decision. The pieces already existed as separate
commands; this is the aggregate the auditor noted was missing.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .prompt_firewall import scan_path
from .context_select import select_context
from .router import recommend_route


@dataclass(frozen=True)
class AuditVerdict:
    proceed: bool
    reason: str
    safety: dict[str, Any]
    context: dict[str, Any]
    route: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "proceed": self.proceed,
            "reason": self.reason,
            "safety": self.safety,
            "context": self.context,
            "route": self.route,
        }


def audit_path(
    path: Path,
    *,
    objective: str,
    max_tokens: int = 8000,
    source: str = "external",
    changed_paths: list[str] | None = None,
    reserve_output_tokens: int = 1024,
    providers_path: Path | None = None,
) -> AuditVerdict:
    """Compose scan + select + route into a single proceed/block verdict.

    proceed is False when the scan blocks. It is never True on unproven safety:
    a blocked scan short-circuits, because sending flagged input to a model is
    the failure this whole layer exists to prevent.
    """
    # 1. Safety first. If the input is blocked, nothing downstream matters.
    scan = scan_path(path, source=source)
    safety = {
        "files_scanned": scan.files_scanned,
        "blocked": scan.blocked,
        "warnings": scan.warnings,
        "findings": [
            {
                "path": f.path,
                "blocked": f.risk.blocked,
                "trust": f.risk.trust,
                "score": f.risk.score,
                "findings": list(f.risk.findings),
            }
            for f in scan.findings
        ],
    }
    if scan.has_blockers:
        return AuditVerdict(
            proceed=False,
            reason=f"blocked: {scan.blocked} file(s) failed the safety scan",
            safety=safety,
            context={},
            route={},
        )

    # 2. What to send, under budget.
    selection = select_context(
        path,
        changed_paths=changed_paths or [],
        max_tokens=max_tokens,
        source=source,
        objective=objective,
    )
    context = selection.to_dict()

    # 3. Which model deserves it, sized to the selected context.
    selected_text = "\n".join(item.path for item in selection.selected)
    route = recommend_route(
        objective,
        context=selected_text,
        reserve_output_tokens=reserve_output_tokens,
        providers_path=providers_path,
    ).to_dict()

    warn = f" ({scan.warnings} warning(s))" if scan.warnings else ""
    return AuditVerdict(
        proceed=True,
        reason=f"clear: {selection.estimated_selected_tokens} tokens selected, "
               f"route {route['selected_model']}{warn}",
        safety=safety,
        context=context,
        route=route,
    )
