"""Project-level Seneschal configuration."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


DEFAULT_CONFIG = "seneschal.config.json"


@dataclass(frozen=True)
class RobinHoodConfig:
    providers: str | None = None
    state: str | None = None
    privacy: str | None = None
    max_cost: float | None = None
    model: str | None = None
    ledger: str | None = None
    estimated_output_tokens: int | None = None

    @classmethod
    def from_mapping(cls, payload: dict[str, Any]) -> "RobinHoodConfig":
        return cls(
            providers=_optional_str(payload.get("providers")),
            state=_optional_str(payload.get("state")),
            privacy=_optional_str(payload.get("privacy")),
            max_cost=float(payload["max_cost"]) if payload.get("max_cost") is not None else None,
            model=_optional_str(payload.get("model")),
            ledger=_optional_str(payload.get("ledger")),
            estimated_output_tokens=int(payload["estimated_output_tokens"]) if payload.get("estimated_output_tokens") is not None else None,
        )


def load_config(path: Path | None) -> RobinHoodConfig:
    if path is None:
        default = Path(DEFAULT_CONFIG)
        if not default.exists():
            return RobinHoodConfig()
        path = default
    if not path.exists():
        return RobinHoodConfig()
    return RobinHoodConfig.from_mapping(json.loads(path.read_text(encoding="utf-8")))


def _optional_str(value: object) -> str | None:
    if value is None:
        return None
    text = str(value)
    return text if text else None
