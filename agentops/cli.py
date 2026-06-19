"""Command-line interface for the AgentOps prototype."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .capability_broker import CapabilityGrant, check_action
from .context_packet import ContextPacket
from .frugality_ledger import append_entry, new_entry, read_entries, summarize_entries
from .health_guard import main as health_main
from .prompt_firewall import classify_file, classify_text, scan_path


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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="agentops", description="Frugal operations for AI-agent work.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    health = subparsers.add_parser("health", help="Run AgentOps health checks.")
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
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
