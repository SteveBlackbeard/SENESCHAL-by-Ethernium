"""Optional MCP server for ROBIN HOOD local controls."""

from __future__ import annotations

import argparse
import contextlib
import sys
from pathlib import Path
from typing import Any

from .capability_broker import CapabilityGrant, check_action
from .context_packer import pack_context
from .context_packet import ContextPacket
from .health_guard import check_forbidden_text, check_manifest, check_required_docs
from .prompt_firewall import classify_text, scan_path
from .provider_profiles import load_profiles
from .router import recommend_route
from .token_budget import budget_for_file, budget_for_text


def health_tool(*, strict: bool = False) -> dict[str, Any]:
    findings = check_required_docs() + check_manifest() + check_forbidden_text()
    payload = {
        "ok": not findings or (not strict and all(finding.severity != "error" for finding in findings)),
        "strict": strict,
        "findings": [
            {"severity": finding.severity, "message": finding.message}
            for finding in findings
        ],
    }
    return payload


def scan_text_tool(text: str, *, source: str = "external") -> dict[str, Any]:
    risk = classify_text(text, source=source)
    return {
        "source": risk.source,
        "trust": risk.trust,
        "score": risk.score,
        "severity": risk.severity,
        "blocked": risk.blocked,
        "findings": list(risk.findings),
    }


def scan_path_tool(path: str, *, source: str = "external") -> dict[str, Any]:
    summary = scan_path(Path(path), source=source)
    return {
        "files_scanned": summary.files_scanned,
        "blocked": summary.blocked,
        "warnings": summary.warnings,
        "findings": [
            {
                "path": finding.path,
                "severity": finding.risk.severity,
                "score": finding.risk.score,
                "blocked": finding.risk.blocked,
                "findings": list(finding.risk.findings),
            }
            for finding in summary.findings
        ],
    }


def make_packet_tool(
    objective: str,
    *,
    allowed_files: list[str] | None = None,
    constraints: list[str] | None = None,
    verification: list[str] | None = None,
    rollback: str = "Revert the scoped change and rerun verification.",
    expected_output: str = "A concise implementation or review result.",
) -> str:
    return ContextPacket(
        objective=objective,
        allowed_files=allowed_files or [],
        constraints=constraints or [],
        verification=verification or [],
        rollback=rollback,
        expected_output=expected_output,
    ).render()


def check_capability_tool(
    task_id: str,
    capabilities: list[str],
    action: str,
    *,
    path: str | None = None,
    allowed_paths: list[str] | None = None,
    denied_paths: list[str] | None = None,
) -> dict[str, Any]:
    grant = CapabilityGrant(
        task_id=task_id,
        capabilities=set(capabilities),
        allowed_paths=tuple(allowed_paths or []),
        denied_paths=tuple(denied_paths or []),
    )
    decision = check_action(grant, capability=action, path=path)
    return {"allowed": decision.allowed, "reason": decision.reason}


def models_tool() -> dict[str, Any]:
    return {"profiles": [profile.to_dict() for profile in load_profiles()]}


def budget_tool(
    *,
    model_id: str = "local-small",
    text: str | None = None,
    file: str | None = None,
    reserve_output_tokens: int = 1024,
) -> dict[str, Any]:
    if text is not None:
        return budget_for_text(text, model_id=model_id, reserve_output_tokens=reserve_output_tokens).to_dict()
    if file is not None:
        return budget_for_file(Path(file), model_id=model_id, reserve_output_tokens=reserve_output_tokens).to_dict()
    raise ValueError("budget_tool requires text or file")


def pack_tool(
    path: str,
    *,
    model_id: str = "local-long",
    max_tokens: int | None = None,
    reserve_output_tokens: int = 1024,
    source: str = "internal",
) -> dict[str, Any]:
    return pack_context(
        Path(path),
        model_id=model_id,
        max_tokens=max_tokens,
        reserve_output_tokens=reserve_output_tokens,
        source=source,
    ).to_dict()


def route_tool(
    objective: str,
    *,
    context: str = "",
    task_class: str | None = None,
    privacy: str = "local-first",
    max_escalation: str = "balanced",
    reserve_output_tokens: int = 1024,
) -> dict[str, Any]:
    return recommend_route(
        objective,
        context=context,
        task_class=task_class,
        privacy=privacy,
        max_escalation=max_escalation,
        reserve_output_tokens=reserve_output_tokens,
    ).to_dict()


def build_mcp_server() -> Any:
    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError as exc:  # pragma: no cover - depends on optional package
        raise RuntimeError("Install the optional MCP extra first: pip install -e .[mcp]") from exc

    server = FastMCP("robin-hood")

    server.tool(name="robinhood.health")(health_tool)
    server.tool(name="robinhood.scan_text")(scan_text_tool)
    server.tool(name="robinhood.scan_path")(scan_path_tool)
    server.tool(name="robinhood.make_packet")(make_packet_tool)
    server.tool(name="robinhood.check_capability")(check_capability_tool)
    server.tool(name="robinhood.models")(models_tool)
    server.tool(name="robinhood.budget")(budget_tool)
    server.tool(name="robinhood.pack")(pack_tool)
    server.tool(name="robinhood.route")(route_tool)

    # Backward-compatible aliases from the agent-ops incubation phase.
    server.tool(name="agentops.health")(health_tool)
    server.tool(name="agentops.scan_text")(scan_text_tool)
    server.tool(name="agentops.scan_path")(scan_path_tool)
    server.tool(name="agentops.make_packet")(make_packet_tool)
    server.tool(name="agentops.check_capability")(check_capability_tool)
    server.tool(name="agentops.models")(models_tool)
    server.tool(name="agentops.budget")(budget_tool)
    server.tool(name="agentops.pack")(pack_tool)
    server.tool(name="agentops.route")(route_tool)
    return server


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the optional ROBIN HOOD MCP server.")
    parser.add_argument("--stdio", action="store_true", help="Run over stdio. This is the default MCP transport.")
    parser.parse_args(argv)

    try:
        server = build_mcp_server()
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    with contextlib.redirect_stdout(sys.stderr):
        print("robinhood-mcp: starting stdio server")
    server.run()
    return 0


if __name__ == "__main__":
    sys.exit(main())
