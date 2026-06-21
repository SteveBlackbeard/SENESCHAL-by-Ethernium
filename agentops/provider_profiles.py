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
    enabled: bool = True
    endpoint_env: str | None = None
    api_key_env: str | None = None
    model_env: str | None = None
    quota_policy: str | None = None
    notes: str | None = None

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
            enabled=bool(payload.get("enabled", True)),
            endpoint_env=str(payload["endpoint_env"]) if payload.get("endpoint_env") else None,
            api_key_env=str(payload["api_key_env"]) if payload.get("api_key_env") else None,
            model_env=str(payload["model_env"]) if payload.get("model_env") else None,
            quota_policy=str(payload["quota_policy"]) if payload.get("quota_policy") else None,
            notes=str(payload["notes"]) if payload.get("notes") else None,
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
            "enabled": self.enabled,
            "endpoint_env": self.endpoint_env,
            "api_key_env": self.api_key_env,
            "model_env": self.model_env,
            "quota_policy": self.quota_policy,
            "notes": self.notes,
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
