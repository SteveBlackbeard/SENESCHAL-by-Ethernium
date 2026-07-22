"""Preflight request planner for provider-neutral model calls."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .capacity_broker import broker_dry_run
from .provider_health import check_provider_health
from .provider_profiles import load_profiles


@dataclass(frozen=True)
class RequestPlan:
    objective: str
    task_class: str
    selected_provider: str
    selected_model: str
    fallback_models: tuple[str, ...]
    estimated_input_tokens: int
    estimated_output_tokens: int
    estimated_total_cost: float
    should_call: bool
    blockers: tuple[str, ...]
    warnings: tuple[str, ...]
    reasons: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "objective": self.objective,
            "task_class": self.task_class,
            "selected_provider": self.selected_provider,
            "selected_model": self.selected_model,
            "fallback_models": list(self.fallback_models),
            "estimated_input_tokens": self.estimated_input_tokens,
            "estimated_output_tokens": self.estimated_output_tokens,
            "estimated_total_cost": self.estimated_total_cost,
            "should_call": self.should_call,
            "blockers": list(self.blockers),
            "warnings": list(self.warnings),
            "reasons": list(self.reasons),
        }


def plan_request(
    objective: str,
    *,
    estimated_input_tokens: int,
    estimated_output_tokens: int = 1024,
    privacy: str = "local-first",
    max_cost: float | None = None,
    providers_path: Path | None = None,
    state_path: Path | None = None,
    task_class: str | None = None,
) -> RequestPlan:
    decision = broker_dry_run(
        objective,
        estimated_input_tokens=estimated_input_tokens,
        privacy=privacy,
        max_cost=max_cost,
        providers_path=providers_path,
        state_path=state_path,
        task_class=task_class,
    )
    profiles = load_profiles(providers_path)
    selected = next((profile for profile in profiles if profile.id == decision.selected_model), None)
    estimated_total_cost = 0.0
    if selected is not None:
        estimated_total_cost = round(
            ((estimated_input_tokens / 1_000_000) * selected.input_cost_per_million)
            + ((estimated_output_tokens / 1_000_000) * selected.output_cost_per_million),
            8,
        )

    health = check_provider_health(providers_path=providers_path)
    selected_health = _health_by_id(health).get(decision.selected_model)
    blockers: list[str] = []
    warnings: list[str] = []

    if selected_health and selected_health.get("enabled") and not selected_health.get("ready"):
        blockers.append("selected-provider-not-ready")
    if max_cost is not None and estimated_total_cost > max_cost:
        blockers.append("estimated-total-cost-over-max")
    if decision.selected_score <= 0:
        warnings.append("fallback-selected-after-constraints")
    if selected_health:
        warnings.extend(str(item) for item in selected_health.get("warnings", []))

    fallback_models = tuple(
        profile.id
        for profile in sorted(profiles, key=lambda item: item.context_window, reverse=True)
        if profile.id != decision.selected_model
        and profile.enabled
        and estimated_input_tokens <= profile.context_window
    )[:3]

    return RequestPlan(
        objective=objective,
        task_class=decision.task_class,
        selected_provider=decision.selected_provider,
        selected_model=decision.selected_model,
        fallback_models=fallback_models,
        estimated_input_tokens=estimated_input_tokens,
        estimated_output_tokens=estimated_output_tokens,
        estimated_total_cost=estimated_total_cost,
        should_call=not blockers,
        blockers=tuple(blockers),
        warnings=tuple(dict.fromkeys(warnings)),
        reasons=tuple(decision.reasons),
    )


def _health_by_id(health: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {str(item["id"]): item for item in health.get("profiles", [])}
