"""Dry-run capacity broker for provider-neutral route decisions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from pathlib import Path

from .provider_state import ProviderState, provider_is_degraded, read_provider_states
from .provider_profiles import ProviderProfile, load_profiles
from .router import classify_task


QUALITY_WEIGHT = {
    "small-edit": {"small-edits", "fast", "cheap"},
    "repository-analysis": {"repository-context", "review", "long-context"},
    "release": {"release", "review", "tool-use"},
    "security-review": {"review", "tool-use", "private"},
    "long-context-synthesis": {"long-context", "synthesis", "analysis"},
    "creative-generation": {"drafting", "synthesis", "adapter-specific"},
}


@dataclass(frozen=True)
class BrokerDecision:
    objective: str
    task_class: str
    selected_provider: str
    selected_model: str
    selected_score: float
    estimated_input_tokens: int
    estimated_input_cost: float
    reasons: tuple[str, ...]
    rejected: tuple[dict[str, Any], ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "objective": self.objective,
            "task_class": self.task_class,
            "selected_provider": self.selected_provider,
            "selected_model": self.selected_model,
            "selected_score": self.selected_score,
            "estimated_input_tokens": self.estimated_input_tokens,
            "estimated_input_cost": self.estimated_input_cost,
            "reasons": list(self.reasons),
            "rejected": list(self.rejected),
        }


def broker_dry_run(
    objective: str,
    *,
    estimated_input_tokens: int,
    privacy: str = "local-first",
    max_cost: float | None = None,
    blocked_providers: set[str] | None = None,
    allowed_providers: set[str] | None = None,
    task_class: str | None = None,
    providers_path: Path | None = None,
    state_path: Path | None = None,
) -> BrokerDecision:
    selected_task = classify_task(objective, forced=task_class)
    blocked = blocked_providers or set()
    allowed = allowed_providers
    candidates = load_profiles(providers_path)
    provider_states = read_provider_states(state_path) if state_path else {}
    rejected: list[dict[str, Any]] = []
    scored: list[tuple[float, ProviderProfile, float, list[str]]] = []

    for profile in candidates:
        cost = round((estimated_input_tokens / 1_000_000) * profile.input_cost_per_million, 8)
        reject_reason = _reject_reason(
            profile,
            estimated_input_tokens=estimated_input_tokens,
            privacy=privacy,
            max_cost=max_cost,
            blocked_providers=blocked,
            allowed_providers=allowed,
            cost=cost,
            provider_states=provider_states,
        )
        if reject_reason:
            rejected.append({"model_id": profile.id, "provider": profile.provider, "reason": reject_reason})
            continue
        score, reasons = _score_profile(profile, selected_task, privacy=privacy, estimated_cost=cost)
        scored.append((score, profile, cost, reasons))

    if not scored:
        fallback = max(candidates, key=lambda item: item.context_window)
        return BrokerDecision(
            objective=objective,
            task_class=selected_task,
            selected_provider=fallback.provider,
            selected_model=fallback.id,
            selected_score=0.0,
            estimated_input_tokens=estimated_input_tokens,
            estimated_input_cost=round((estimated_input_tokens / 1_000_000) * fallback.input_cost_per_million, 8),
            reasons=("no candidate passed constraints; returned largest-context fallback",),
            rejected=tuple(rejected),
        )

    score, profile, cost, reasons = max(scored, key=lambda item: (item[0], -item[2], item[1].context_window))
    return BrokerDecision(
        objective=objective,
        task_class=selected_task,
        selected_provider=profile.provider,
        selected_model=profile.id,
        selected_score=round(score, 4),
        estimated_input_tokens=estimated_input_tokens,
        estimated_input_cost=cost,
        reasons=tuple(reasons),
        rejected=tuple(rejected),
    )


def _reject_reason(
    profile: ProviderProfile,
    *,
    estimated_input_tokens: int,
    privacy: str,
    max_cost: float | None,
    blocked_providers: set[str],
    allowed_providers: set[str] | None,
    cost: float,
    provider_states: dict[str, ProviderState],
) -> str | None:
    if not profile.enabled:
        return "provider-disabled"
    if provider_is_degraded(profile.id, provider_states) or provider_is_degraded(profile.provider, provider_states):
        return "provider-degraded"
    if profile.provider in blocked_providers or profile.id in blocked_providers:
        return "blocked-provider"
    if allowed_providers is not None and profile.provider not in allowed_providers and profile.id not in allowed_providers:
        return "not-in-allowed-providers"
    if privacy == "local-only" and profile.privacy != "local":
        return "privacy-requires-local"
    if estimated_input_tokens > profile.context_window:
        return "context-window-too-small"
    if max_cost is not None and cost > max_cost:
        return "over-max-cost"
    return None


def _score_profile(
    profile: ProviderProfile,
    task_class: str,
    *,
    privacy: str,
    estimated_cost: float,
) -> tuple[float, list[str]]:
    strengths = set(profile.strengths)
    wanted = QUALITY_WEIGHT.get(task_class, set())
    quality = len(strengths & wanted) * 20
    context = min(profile.context_window / 1000, 80)
    privacy_bonus = 25 if privacy in {"local-only", "local-first"} and profile.privacy == "local" else 0
    cloud_penalty = 10 if privacy == "local-first" and profile.privacy != "local" else 0
    cost_penalty = estimated_cost * 10
    score = quality + context + privacy_bonus - cloud_penalty - cost_penalty
    reasons = [
        f"quality_overlap={sorted(strengths & wanted)}",
        f"context_window={profile.context_window}",
        f"privacy={profile.privacy}",
        f"estimated_cost={estimated_cost}",
    ]
    return score, reasons
