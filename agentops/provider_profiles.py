"""Provider-neutral model profile registry."""

from __future__ import annotations

import json
from dataclasses import dataclass
from importlib import resources
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ProviderProfile:
    id: str
    provider: str
    context_window: int
    input_cost_per_million: float
    output_cost_per_million: float
    privacy: str
    latency: str
    strengths: tuple[str, ...]
    tokenizer: str = "estimate"

    @classmethod
    def from_mapping(cls, payload: dict[str, Any]) -> "ProviderProfile":
        return cls(
            id=str(payload["id"]),
            provider=str(payload["provider"]),
            context_window=int(payload["context_window"]),
            input_cost_per_million=float(payload.get("input_cost_per_million", 0.0)),
            output_cost_per_million=float(payload.get("output_cost_per_million", 0.0)),
            privacy=str(payload.get("privacy", "unknown")),
            latency=str(payload.get("latency", "unknown")),
            strengths=tuple(str(item) for item in payload.get("strengths", [])),
            tokenizer=str(payload.get("tokenizer", "estimate")),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "provider": self.provider,
            "context_window": self.context_window,
            "input_cost_per_million": self.input_cost_per_million,
            "output_cost_per_million": self.output_cost_per_million,
            "privacy": self.privacy,
            "latency": self.latency,
            "strengths": list(self.strengths),
            "tokenizer": self.tokenizer,
        }


def load_profiles(path: Path | None = None) -> list[ProviderProfile]:
    if path is None:
        raw = resources.files("agentops").joinpath("provider_profiles.json").read_text(encoding="utf-8")
    else:
        raw = path.read_text(encoding="utf-8")
    payload = json.loads(raw)
    return [ProviderProfile.from_mapping(item) for item in payload["profiles"]]


def get_profile(model_id: str, *, path: Path | None = None) -> ProviderProfile:
    for profile in load_profiles(path):
        if profile.id == model_id:
            return profile
    available = ", ".join(profile.id for profile in load_profiles(path))
    raise KeyError(f"unknown model profile: {model_id}. Available: {available}")
