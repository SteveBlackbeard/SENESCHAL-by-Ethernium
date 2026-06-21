"""Local provider state for cheap circuit-breaker decisions."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_PROVIDER_STATE = ".robinhood/provider-state.json"
DEGRADED_STATUSES = {"fail", "rate_limited", "quota_exhausted", "disabled"}


@dataclass(frozen=True)
class ProviderState:
    id: str
    status: str
    reason: str
    failures: int
    updated_at: str

    @property
    def degraded(self) -> bool:
        return self.status in DEGRADED_STATUSES

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "status": self.status,
            "reason": self.reason,
            "failures": self.failures,
            "updated_at": self.updated_at,
            "degraded": self.degraded,
        }


def read_provider_states(path: Path | str = DEFAULT_PROVIDER_STATE) -> dict[str, ProviderState]:
    state_path = Path(path)
    if not state_path.exists():
        return {}
    payload = json.loads(state_path.read_text(encoding="utf-8"))
    return {
        str(item["id"]): ProviderState(
            id=str(item["id"]),
            status=str(item.get("status", "unknown")),
            reason=str(item.get("reason", "")),
            failures=int(item.get("failures", 0)),
            updated_at=str(item.get("updated_at", "")),
        )
        for item in payload.get("providers", [])
    }


def write_provider_states(
    states: dict[str, ProviderState],
    path: Path | str = DEFAULT_PROVIDER_STATE,
) -> None:
    state_path = Path(path)
    state_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"version": "0.1.0", "providers": [state.to_dict() for state in sorted(states.values(), key=lambda item: item.id)]}
    state_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def mark_provider_state(
    provider_id: str,
    *,
    status: str,
    reason: str = "",
    path: Path | str = DEFAULT_PROVIDER_STATE,
) -> ProviderState:
    states = read_provider_states(path)
    previous = states.get(provider_id)
    failures = 0 if status == "ok" else ((previous.failures if previous else 0) + 1)
    state = ProviderState(
        id=provider_id,
        status=status,
        reason=reason,
        failures=failures,
        updated_at=datetime.now(timezone.utc).isoformat(),
    )
    states[provider_id] = state
    write_provider_states(states, path)
    return state


def provider_is_degraded(provider_id: str, states: dict[str, ProviderState]) -> bool:
    state = states.get(provider_id)
    return bool(state and state.degraded)
