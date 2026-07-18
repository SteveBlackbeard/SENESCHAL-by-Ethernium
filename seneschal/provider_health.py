"""Configuration-only provider readiness checks."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

from .provider_profiles import ProviderProfile, load_profiles


@dataclass(frozen=True)
class ProviderHealth:
    id: str
    provider: str
    enabled: bool
    ready: bool
    status: str
    missing_env: tuple[str, ...]
    configured_env: tuple[str, ...]
    warnings: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "id": self.id,
            "provider": self.provider,
            "enabled": self.enabled,
            "ready": self.ready,
            "status": self.status,
            "missing_env": list(self.missing_env),
            "configured_env": list(self.configured_env),
            "warnings": list(self.warnings),
        }


def check_provider_health(
    *,
    providers_path: Path | None = None,
    environ: Mapping[str, str] | None = None,
) -> dict[str, object]:
    env = environ if environ is not None else os.environ
    checks = [_check_profile(profile, env) for profile in load_profiles(providers_path)]
    return {
        "ok": all(check.ready or not check.enabled for check in checks),
        "profiles": [check.to_dict() for check in checks],
    }


def _check_profile(profile: ProviderProfile, env: Mapping[str, str]) -> ProviderHealth:
    env_names = tuple(
        name
        for name in (profile.endpoint_env, profile.api_key_env, profile.model_env)
        if name
    )
    configured = tuple(name for name in env_names if env.get(name))
    missing = tuple(name for name in env_names if not env.get(name))
    warnings: list[str] = []

    if not profile.enabled:
        return ProviderHealth(
            id=profile.id,
            provider=profile.provider,
            enabled=False,
            ready=False,
            status="disabled",
            missing_env=missing,
            configured_env=configured,
            warnings=tuple(warnings),
        )

    required = _required_env(profile)
    missing_required = tuple(name for name in required if not env.get(name))
    if missing_required:
        status = "missing-required-env"
        ready = False
    else:
        status = "ready"
        ready = True

    optional_missing = tuple(name for name in missing if name not in missing_required)
    if optional_missing:
        warnings.append("optional-env-not-set")

    return ProviderHealth(
        id=profile.id,
        provider=profile.provider,
        enabled=True,
        ready=ready,
        status=status,
        missing_env=missing,
        configured_env=configured,
        warnings=tuple(warnings),
    )


def _required_env(profile: ProviderProfile) -> tuple[str, ...]:
    required: list[str] = []
    if profile.api_key_env:
        required.append(profile.api_key_env)
    if profile.provider not in {"local", "ollama", "local-lora"} and profile.endpoint_env:
        required.append(profile.endpoint_env)
    return tuple(required)
