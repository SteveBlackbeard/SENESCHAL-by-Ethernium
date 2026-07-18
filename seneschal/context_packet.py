"""Context packet primitives for frugal agent handoffs."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ContextPacket:
    objective: str
    allowed_files: list[str] = field(default_factory=list)
    constraints: list[str] = field(default_factory=list)
    verification: list[str] = field(default_factory=list)
    rollback: str = "Revert the scoped change and rerun verification."
    expected_output: str = "A concise implementation or review result."

    def render(self) -> str:
        return "\n".join(
            [
                "Objective:",
                self.objective.strip(),
                "",
                "Allowed files:",
                _render_list(self.allowed_files),
                "",
                "Constraints:",
                _render_list(self.constraints),
                "",
                "Verification:",
                _render_list(self.verification),
                "",
                "Rollback:",
                self.rollback.strip(),
                "",
                "Expected output:",
                self.expected_output.strip(),
                "",
            ]
        )


def _render_list(items: list[str]) -> str:
    if not items:
        return "- none declared"
    return "\n".join(f"- {item.strip()}" for item in items if item.strip())
