"""Command-line interface for ROBIN HOOD."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .capability_broker import CapabilityGrant, check_action
from .capacity_broker import broker_dry_run
from .context_packer import pack_context, render_pack
from .context_cache import DEFAULT_CACHE, create_snapshot, diff_snapshot, estimate_prompt_reuse, read_snapshot, write_snapshot
from .context_packet import ContextPacket
from .context_select import select_context
from .frugality_ledger import append_entry, new_entry, read_entries, summarize_entries
from .health_guard import main as health_main
from .prompt_firewall import classify_file, classify_text, scan_path
from .provider_health import check_provider_health
from .provider_profiles import load_profiles
from .provider_state import DEFAULT_PROVIDER_STATE, mark_provider_state, read_provider_states
from .router import recommend_route
from .savings import estimate_savings
from .token_budget import budget_for_file, budget_for_text


def cmd_health(args: argparse.Namespace) -> int:
    return health_main(["--strict"] if args.strict else [])


def cmd_packet(args: argparse.Namespace) -> int:
    packet = ContextPacket(
        objective=args.objective,
        allowed_files=args.allowed_file or [],
        constraints=args.constraint or [],
        verification=args.verify or [],
        rollback=args.rollback,
        expected_output=args.expected_output,
    )
    print(packet.render())
    return 0


def cmd_scan(args: argparse.Namespace) -> int:
    if args.path is not None:
        summary = scan_path(Path(args.path), source=args.source)
        payload = {
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
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 1 if args.fail_on_block and summary.has_blockers else 0
    if args.text is not None:
        risk = classify_text(args.text, source=args.source)
    elif args.file is not None:
        risk = classify_file(Path(args.file), source=args.source)
    else:
        print("ERROR: scan requires --text or --file", file=sys.stderr)
        return 2
    payload = {
        "source": risk.source,
        "trust": risk.trust,
        "score": risk.score,
        "severity": risk.severity,
        "blocked": risk.blocked,
        "findings": list(risk.findings),
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 1 if args.fail_on_block and risk.blocked else 0


def cmd_grant(args: argparse.Namespace) -> int:
    grant = CapabilityGrant(
        task_id=args.task_id,
        capabilities=set(args.capability),
        allowed_paths=tuple(args.allowed_path or []),
        denied_paths=tuple(args.denied_path or []),
    )
    decision = check_action(grant, capability=args.action, path=args.path)
    print(json.dumps({"allowed": decision.allowed, "reason": decision.reason}, indent=2, sort_keys=True))
    return 0 if decision.allowed else 1


def cmd_log(args: argparse.Namespace) -> int:
    entry = new_entry(
        task_id=args.task_id,
        model=args.model,
        tokens_estimated=args.tokens_estimated,
        retries=args.retries,
        outcome=args.outcome,
        reduced=args.reduced,
    )
    append_entry(Path(args.ledger), entry)
    print(json.dumps({"logged": True, "task_id": entry.task_id, "ledger": args.ledger}, indent=2, sort_keys=True))
    return 0


def cmd_report(args: argparse.Namespace) -> int:
    entries = read_entries(Path(args.ledger))
    print(json.dumps(summarize_entries(entries), indent=2, sort_keys=True))
    return 0


def cmd_models(args: argparse.Namespace) -> int:
    profiles = [profile.to_dict() for profile in load_profiles(Path(args.profiles) if args.profiles else None)]
    print(json.dumps({"profiles": profiles}, indent=2, sort_keys=True))
    return 0


def cmd_providers(args: argparse.Namespace) -> int:
    profiles = [profile.to_dict() for profile in load_profiles(Path(args.providers) if args.providers else None)]
    print(json.dumps({"profiles": profiles}, indent=2, sort_keys=True))
    return 0


def cmd_provider_health(args: argparse.Namespace) -> int:
    payload = check_provider_health(providers_path=Path(args.providers) if args.providers else None)
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload["ok"] else 1


def cmd_provider_state(args: argparse.Namespace) -> int:
    states = read_provider_states(Path(args.state))
    print(json.dumps({"providers": [state.to_dict() for state in states.values()]}, indent=2, sort_keys=True))
    return 0


def cmd_provider_mark(args: argparse.Namespace) -> int:
    state = mark_provider_state(args.provider, status=args.status, reason=args.reason or "", path=Path(args.state))
    print(json.dumps({"provider": state.to_dict(), "state": args.state}, indent=2, sort_keys=True))
    return 0


def cmd_budget(args: argparse.Namespace) -> int:
    if args.text is not None:
        budget = budget_for_text(args.text, model_id=args.model, reserve_output_tokens=args.reserve_output)
    elif args.file is not None:
        budget = budget_for_file(Path(args.file), model_id=args.model, reserve_output_tokens=args.reserve_output)
    else:
        print("ERROR: budget requires --text or --file", file=sys.stderr)
        return 2
    print(json.dumps(budget.to_dict(), indent=2, sort_keys=True))
    return 0 if budget.fits else 1


def cmd_pack(args: argparse.Namespace) -> int:
    root = Path(args.path)
    pack = pack_context(
        root,
        model_id=args.model,
        max_tokens=args.max_tokens,
        reserve_output_tokens=args.reserve_output,
        source=args.source,
    )
    if args.render:
        print(render_pack(pack, root.resolve()))
    else:
        print(json.dumps(pack.to_dict(), indent=2, sort_keys=True))
    return 0 if pack.estimated_packed_tokens <= pack.max_input_tokens else 1


def cmd_route(args: argparse.Namespace) -> int:
    context = ""
    if args.context is not None:
        context = args.context
    elif args.context_file is not None:
        context = Path(args.context_file).read_text(encoding="utf-8", errors="replace")
    recommendation = recommend_route(
        args.objective,
        context=context,
        task_class=args.task_class,
        privacy=args.privacy,
        max_escalation=args.max_escalation,
        reserve_output_tokens=args.reserve_output,
    )
    print(json.dumps(recommendation.to_dict(), indent=2, sort_keys=True))
    return 0 if recommendation.fits else 1


def cmd_snapshot(args: argparse.Namespace) -> int:
    cache_path = Path(args.cache)
    current = create_snapshot(Path(args.path))
    payload = {"snapshot": current.to_dict()}
    if cache_path.exists() and not args.no_diff:
        diff = diff_snapshot(read_snapshot(cache_path), current)
        payload["diff"] = diff
        if args.input_cost_per_million is not None:
            payload["savings"] = estimate_savings(
                full_context_tokens=diff["full_context_tokens"],
                optimized_context_tokens=diff["delta_context_tokens"],
                input_cost_per_million=args.input_cost_per_million,
                runs=args.runs,
            ).to_dict()
    write_snapshot(current, cache_path)
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


def cmd_reuse(args: argparse.Namespace) -> int:
    system_prompt = args.system or ""
    user_prompt = args.user or ""
    if args.system_file:
        system_prompt = Path(args.system_file).read_text(encoding="utf-8", errors="replace")
    if args.user_file:
        user_prompt = Path(args.user_file).read_text(encoding="utf-8", errors="replace")
    print(json.dumps(estimate_prompt_reuse(system_prompt, user_prompt), indent=2, sort_keys=True))
    return 0


def cmd_savings(args: argparse.Namespace) -> int:
    estimate = estimate_savings(
        full_context_tokens=args.full_tokens,
        optimized_context_tokens=args.optimized_tokens,
        input_cost_per_million=args.input_cost_per_million,
        runs=args.runs,
    )
    print(json.dumps(estimate.to_dict(), indent=2, sort_keys=True))
    return 0


def cmd_select(args: argparse.Namespace) -> int:
    selection = select_context(
        Path(args.path),
        changed_paths=args.changed,
        max_tokens=args.max_tokens,
        source=args.source,
        min_score=args.min_score,
    )
    print(json.dumps(selection.to_dict(), indent=2, sort_keys=True))
    return 0


def cmd_broker_dry_run(args: argparse.Namespace) -> int:
    decision = broker_dry_run(
        args.objective,
        estimated_input_tokens=args.estimated_input_tokens,
        privacy=args.privacy,
        max_cost=args.max_cost,
        blocked_providers=set(args.blocked_provider or []),
        allowed_providers=set(args.allowed_provider) if args.allowed_provider else None,
        task_class=args.task_class,
        providers_path=Path(args.providers) if args.providers else None,
        state_path=Path(args.state) if args.state else None,
    )
    print(json.dumps(decision.to_dict(), indent=2, sort_keys=True))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="robinhood", description="Frugal operations for AI-agent work.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    health = subparsers.add_parser("health", help="Run ROBIN HOOD health checks.")
    health.add_argument("--strict", action="store_true", help="Treat warnings as errors.")
    health.set_defaults(func=cmd_health)

    packet = subparsers.add_parser("packet", help="Render a scoped context packet.")
    packet.add_argument("--objective", required=True)
    packet.add_argument("--allowed-file", action="append")
    packet.add_argument("--constraint", action="append")
    packet.add_argument("--verify", action="append")
    packet.add_argument("--rollback", default="Revert the scoped change and rerun verification.")
    packet.add_argument("--expected-output", default="A concise implementation or review result.")
    packet.set_defaults(func=cmd_packet)

    scan = subparsers.add_parser("scan", help="Classify prompt-risk in text or a file.")
    scan.add_argument("--text")
    scan.add_argument("--file")
    scan.add_argument("--path", help="Scan a file or directory recursively.")
    scan.add_argument("--source", default="external")
    scan.add_argument("--fail-on-block", action="store_true")
    scan.set_defaults(func=cmd_scan)

    grant = subparsers.add_parser("grant", help="Check a least-privilege capability grant.")
    grant.add_argument("--task-id", required=True)
    grant.add_argument("--capability", action="append", required=True)
    grant.add_argument("--allowed-path", action="append")
    grant.add_argument("--denied-path", action="append")
    grant.add_argument("--action", required=True)
    grant.add_argument("--path")
    grant.set_defaults(func=cmd_grant)

    log = subparsers.add_parser("log", help="Append a JSONL frugality ledger entry.")
    log.add_argument("--ledger", default="agentops-usage.jsonl")
    log.add_argument("--task-id", required=True)
    log.add_argument("--model", required=True)
    log.add_argument("--tokens-estimated", type=int, required=True)
    log.add_argument("--retries", type=int, default=0)
    log.add_argument("--outcome", required=True)
    log.add_argument("--reduced", choices=["cost", "risk", "drift"], required=True)
    log.set_defaults(func=cmd_log)

    report = subparsers.add_parser("report", help="Summarize a JSONL frugality ledger.")
    report.add_argument("--ledger", default="agentops-usage.jsonl")
    report.set_defaults(func=cmd_report)

    models = subparsers.add_parser("models", help="List model/provider profiles.")
    models.add_argument("--profiles", help="Optional custom provider_profiles.json path.")
    models.set_defaults(func=cmd_models)

    providers = subparsers.add_parser("providers", help="List provider profiles from the active catalog.")
    providers.add_argument("--providers", help="Optional providers.local.json path.")
    providers.set_defaults(func=cmd_providers)

    provider_health = subparsers.add_parser("provider-health", help="Check provider configuration without API calls.")
    provider_health.add_argument("--providers", help="Optional providers.local.json path.")
    provider_health.set_defaults(func=cmd_provider_health)

    provider_state = subparsers.add_parser("provider-state", help="Show local provider circuit-breaker state.")
    provider_state.add_argument("--state", default=DEFAULT_PROVIDER_STATE)
    provider_state.set_defaults(func=cmd_provider_state)

    provider_mark = subparsers.add_parser("provider-mark", help="Record a provider state event.")
    provider_mark.add_argument("--provider", required=True)
    provider_mark.add_argument("--status", required=True, choices=["ok", "fail", "rate_limited", "quota_exhausted", "disabled"])
    provider_mark.add_argument("--reason")
    provider_mark.add_argument("--state", default=DEFAULT_PROVIDER_STATE)
    provider_mark.set_defaults(func=cmd_provider_mark)

    budget = subparsers.add_parser("budget", help="Estimate whether text or a file fits a model budget.")
    budget.add_argument("--model", default="local-small")
    budget.add_argument("--reserve-output", type=int, default=1024)
    budget.add_argument("--text")
    budget.add_argument("--file")
    budget.set_defaults(func=cmd_budget)

    pack = subparsers.add_parser("pack", help="Pack a file or directory under a token budget.")
    pack.add_argument("--path", required=True)
    pack.add_argument("--model", default="local-long")
    pack.add_argument("--max-tokens", type=int)
    pack.add_argument("--reserve-output", type=int, default=1024)
    pack.add_argument("--source", default="internal")
    pack.add_argument("--render", action="store_true", help="Render included files as a text packet.")
    pack.set_defaults(func=cmd_pack)

    route = subparsers.add_parser("route", help="Recommend the cheapest sufficient model path.")
    route.add_argument("--objective", required=True)
    route.add_argument("--context")
    route.add_argument("--context-file")
    route.add_argument("--task-class")
    route.add_argument("--privacy", choices=["local-only", "local-first", "cloud-allowed"], default="local-first")
    route.add_argument("--max-escalation", choices=["local", "balanced", "strong"], default="balanced")
    route.add_argument("--reserve-output", type=int, default=1024)
    route.set_defaults(func=cmd_route)

    snapshot = subparsers.add_parser("snapshot", help="Create a context snapshot and estimate changed-only savings.")
    snapshot.add_argument("--path", default=".")
    snapshot.add_argument("--cache", default=DEFAULT_CACHE)
    snapshot.add_argument("--no-diff", action="store_true")
    snapshot.add_argument("--input-cost-per-million", type=float)
    snapshot.add_argument("--runs", type=int, default=1)
    snapshot.set_defaults(func=cmd_snapshot)

    reuse = subparsers.add_parser("reuse", help="Estimate reusable prompt/cacheable token share.")
    reuse.add_argument("--system")
    reuse.add_argument("--user")
    reuse.add_argument("--system-file")
    reuse.add_argument("--user-file")
    reuse.set_defaults(func=cmd_reuse)

    savings = subparsers.add_parser("savings", help="Estimate token and cost savings across repeated runs.")
    savings.add_argument("--full-tokens", type=int, required=True)
    savings.add_argument("--optimized-tokens", type=int, required=True)
    savings.add_argument("--input-cost-per-million", type=float, required=True)
    savings.add_argument("--runs", type=int, default=1)
    savings.set_defaults(func=cmd_savings)

    select = subparsers.add_parser("select", help="Select relevant neighboring context under a token budget.")
    select.add_argument("--path", default=".")
    select.add_argument("--changed", action="append", required=True)
    select.add_argument("--max-tokens", type=int, required=True)
    select.add_argument("--source", default="internal")
    select.add_argument("--min-score", type=int, default=30)
    select.set_defaults(func=cmd_select)

    broker = subparsers.add_parser("broker-dry-run", help="Dry-run provider capacity routing without API calls.")
    broker.add_argument("--objective", required=True)
    broker.add_argument("--estimated-input-tokens", type=int, required=True)
    broker.add_argument("--privacy", choices=["local-only", "local-first", "cloud-allowed"], default="local-first")
    broker.add_argument("--max-cost", type=float)
    broker.add_argument("--allowed-provider", action="append")
    broker.add_argument("--blocked-provider", action="append")
    broker.add_argument("--task-class")
    broker.add_argument("--providers", help="Optional providers.local.json path.")
    broker.add_argument("--state", help="Optional provider-state.json path for circuit-breaker routing.")
    broker.set_defaults(func=cmd_broker_dry_run)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
