"""JSONL ledger for measuring agent cost, retries, and outcomes."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path


@dataclass(frozen=True)
class LedgerEntry:
    task_id: str
    model: str
    tokens_estimated: int
    retries: int
    outcome: str
    reduced: str
    created_at: str


def new_entry(
    *,
    task_id: str,
    model: str,
    tokens_estimated: int,
    retries: int,
    outcome: str,
    reduced: str,
) -> LedgerEntry:
    if reduced not in {"cost", "risk", "drift"}:
        raise ValueError("reduced must be one of: cost, risk, drift")
    if tokens_estimated < 0 or retries < 0:
        raise ValueError("tokens_estimated and retries must be non-negative")
    return LedgerEntry(
        task_id=task_id,
        model=model,
        tokens_estimated=tokens_estimated,
        retries=retries,
        outcome=outcome,
        reduced=reduced,
        created_at=datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
    )


def append_entry(path: Path, entry: LedgerEntry) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(asdict(entry), sort_keys=True) + "\n")


def read_entries(path: Path) -> list[LedgerEntry]:
    if not path.exists():
        return []
    entries: list[LedgerEntry] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        data = json.loads(line)
        entries.append(LedgerEntry(**data))
    return entries


def summarize_entries(entries: list[LedgerEntry]) -> dict[str, int]:
    summary = {
        "entries": len(entries),
        "tokens_estimated": sum(entry.tokens_estimated for entry in entries),
        "retries": sum(entry.retries for entry in entries),
        "cost": 0,
        "risk": 0,
        "drift": 0,
    }
    for entry in entries:
        summary[entry.reduced] += 1
    return summary


def summarize_by_model(entries: list[LedgerEntry]) -> dict[str, dict[str, float]]:
    """Per-model track record from the ledger.

    This is what turns the ledger from a write-only log into feedback: the router
    can read these outcomes and down-rank models that have been failing or forcing
    retries, instead of recommending the same route every time regardless of how
    the last runs went."""
    stats: dict[str, dict[str, float]] = {}
    for entry in entries:
        row = stats.setdefault(
            entry.model, {"entries": 0, "failures": 0, "retries": 0, "failure_rate": 0.0}
        )
        row["entries"] += 1
        row["retries"] += entry.retries
        if entry.outcome == "fail":
            row["failures"] += 1
    for row in stats.values():
        total = row["entries"]
        row["failure_rate"] = round(row["failures"] / total, 4) if total else 0.0
    return stats
