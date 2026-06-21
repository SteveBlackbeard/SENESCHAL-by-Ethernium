"""Optional MCP server for ROBIN HOOD local controls."""

from __future__ import annotations

import argparse
import contextlib
import sys
from pathlib import Path
from typing import Any

from .capability_broker import CapabilityGrant, check_action
from .capacity_broker import broker_dry_run
from .context_cache import create_snapshot, diff_snapshot, estimate_prompt_reuse, read_snapshot, write_snapshot
from .context_packer import pack_context
from .context_select import select_context
from .context_packet import ContextPacket
from .health_guard import check_forbidden_text, check_manifest, check_required_docs
from .prompt_firewall import classify_text, scan_path
from .provider_health import check_provider_health
from .provider_profiles import load_profiles
from .provider_state import mark_provider_state, read_provider_states
from .request_planner import plan_request
from .router import recommend_route
from .savings import estimate_savings
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


def provider_health_tool(*, providers_path: str | None = None) -> dict[str, Any]:
    return check_provider_health(providers_path=Path(providers_path) if providers_path else None)


def provider_state_tool(*, state_path: str = ".robinhood/provider-state.json") -> dict[str, Any]:
    states = read_provider_states(Path(state_path))
    return {"providers": [state.to_dict() for state in states.values()]}


def provider_mark_tool(
    provider: str,
    *,
    status: str,
    reason: str = "",
    state_path: str = ".robinhood/provider-state.json",
) -> dict[str, Any]:
    state = mark_provider_state(provider, status=status, reason=reason, path=Path(state_path))
    return {"provider": state.to_dict(), "state_path": state_path}


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


def snapshot_tool(
    path: str,
    *,
    cache: str = ".robinhood/context-cache.json",
    no_diff: bool = False,
    input_cost_per_million: float | None = None,
    runs: int = 1,
) -> dict[str, Any]:
    cache_path = Path(cache)
    current = create_snapshot(Path(path))
    payload: dict[str, Any] = {"snapshot": current.to_dict()}
    if cache_path.exists() and not no_diff:
        diff = diff_snapshot(read_snapshot(cache_path), current)
        payload["diff"] = diff
        if input_cost_per_million is not None:
            payload["savings"] = estimate_savings(
                full_context_tokens=diff["full_context_tokens"],
                optimized_context_tokens=diff["delta_context_tokens"],
                input_cost_per_million=input_cost_per_million,
                runs=runs,
            ).to_dict()
    write_snapshot(current, cache_path)
    return payload


def reuse_tool(*, system_prompt: str = "", user_prompt: str = "") -> dict[str, Any]:
    return estimate_prompt_reuse(system_prompt, user_prompt)


def savings_tool(
    *,
    full_context_tokens: int,
    optimized_context_tokens: int,
    input_cost_per_million: float,
    runs: int = 1,
) -> dict[str, Any]:
    return estimate_savings(
        full_context_tokens=full_context_tokens,
        optimized_context_tokens=optimized_context_tokens,
        input_cost_per_million=input_cost_per_million,
        runs=runs,
    ).to_dict()


def select_tool(
    path: str,
    *,
    changed_paths: list[str],
    max_tokens: int,
    source: str = "internal",
    min_score: int = 30,
) -> dict[str, Any]:
    return select_context(
        Path(path),
        changed_paths=changed_paths,
        max_tokens=max_tokens,
        source=source,
        min_score=min_score,
    ).to_dict()


def broker_dry_run_tool(
    objective: str,
    *,
    estimated_input_tokens: int,
    privacy: str = "local-first",
    max_cost: float | None = None,
    blocked_providers: list[str] | None = None,
    allowed_providers: list[str] | None = None,
    task_class: str | None = None,
    providers_path: str | None = None,
    state_path: str | None = None,
) -> dict[str, Any]:
    return broker_dry_run(
        objective,
        estimated_input_tokens=estimated_input_tokens,
        privacy=privacy,
        max_cost=max_cost,
        blocked_providers=set(blocked_providers or []),
        allowed_providers=set(allowed_providers) if allowed_providers else None,
        task_class=task_class,
        providers_path=Path(providers_path) if providers_path else None,
        state_path=Path(state_path) if state_path else None,
    ).to_dict()


def plan_request_tool(
    objective: str,
    *,
    estimated_input_tokens: int,
    estimated_output_tokens: int = 1024,
    privacy: str = "local-first",
    max_cost: float | None = None,
    task_class: str | None = None,
    providers_path: str | None = None,
    state_path: str | None = None,
) -> dict[str, Any]:
    return plan_request(
        objective,
        estimated_input_tokens=estimated_input_tokens,
        estimated_output_tokens=estimated_output_tokens,
        privacy=privacy,
        max_cost=max_cost,
        task_class=task_class,
        providers_path=Path(providers_path) if providers_path else None,
        state_path=Path(state_path) if state_path else None,
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
    server.tool(name="robinhood.provider_health")(provider_health_tool)
    server.tool(name="robinhood.provider_state")(provider_state_tool)
    server.tool(name="robinhood.provider_mark")(provider_mark_tool)
    server.tool(name="robinhood.budget")(budget_tool)
    server.tool(name="robinhood.pack")(pack_tool)
    server.tool(name="robinhood.route")(route_tool)
    server.tool(name="robinhood.snapshot")(snapshot_tool)
    server.tool(name="robinhood.reuse")(reuse_tool)
    server.tool(name="robinhood.savings")(savings_tool)
    server.tool(name="robinhood.select")(select_tool)
    server.tool(name="robinhood.broker_dry_run")(broker_dry_run_tool)
    server.tool(name="robinhood.plan_request")(plan_request_tool)

    # Backward-compatible aliases from the agent-ops incubation phase.
    server.tool(name="agentops.health")(health_tool)
    server.tool(name="agentops.scan_text")(scan_text_tool)
    server.tool(name="agentops.scan_path")(scan_path_tool)
    server.tool(name="agentops.make_packet")(make_packet_tool)
    server.tool(name="agentops.check_capability")(check_capability_tool)
    server.tool(name="agentops.models")(models_tool)
    server.tool(name="agentops.provider_health")(provider_health_tool)
    server.tool(name="agentops.provider_state")(provider_state_tool)
    server.tool(name="agentops.provider_mark")(provider_mark_tool)
    server.tool(name="agentops.budget")(budget_tool)
    server.tool(name="agentops.pack")(pack_tool)
    server.tool(name="agentops.route")(route_tool)
    server.tool(name="agentops.snapshot")(snapshot_tool)
    server.tool(name="agentops.reuse")(reuse_tool)
    server.tool(name="agentops.savings")(savings_tool)
    server.tool(name="agentops.select")(select_tool)
    server.tool(name="agentops.broker_dry_run")(broker_dry_run_tool)
    server.tool(name="agentops.plan_request")(plan_request_tool)
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
