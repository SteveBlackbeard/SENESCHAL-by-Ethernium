"""Provider-neutral frugal routing recommendations."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .provider_profiles import ProviderProfile, load_profiles
from .token_budget import budget_for_text


TASK_MARKERS: dict[str, tuple[str, ...]] = {
    "small-edit": ("fix typo", "small edit", "rename", "format", "readme", "docs"),
    "repository-analysis": ("analyze repo", "audit", "review codebase", "map project", "architecture"),
    "release": ("release", "pypi", "publish", "tag", "build", "twine", "ci"),
    "security-review": ("security", "secret", "prompt injection", "jailbreak", "vulnerability", "threat"),
    "long-context-synthesis": ("summarize", "synthesis", "whole repo", "large context", "many files"),
    "creative-generation": ("image", "video", "music", "creative", "lore", "art"),
}

TASK_WEIGHTS = {
    "small-edit": 1,
    "creative-generation": 2,
    "repository-analysis": 3,
    "long-context-synthesis": 3,
    "release": 4,
    "security-review": 5,
}


@dataclass(frozen=True)
class RouteRecommendation:
    task_class: str
    selected_model: str
    provider: str
    privacy: str
    estimated_input_tokens: int
    context_window: int
    fits: bool
    escalation_level: str
    reasons: tuple[str, ...]
    rejected: tuple[dict[str, Any], ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_class": self.task_class,
            "selected_model": self.selected_model,
            "provider": self.provider,
            "privacy": self.privacy,
            "estimated_input_tokens": self.estimated_input_tokens,
            "context_window": self.context_window,
            "fits": self.fits,
            "escalation_level": self.escalation_level,
            "reasons": list(self.reasons),
            "rejected": list(self.rejected),
        }


def classify_task(objective: str, *, forced: str | None = None) -> str:
    if forced:
        return forced
    lowered = objective.lower()
    scores = {
        task_class: sum(1 for marker in markers if marker in lowered)
        for task_class, markers in TASK_MARKERS.items()
    }
    best = max(scores.items(), key=lambda item: (item[1], TASK_WEIGHTS[item[0]]))
    return best[0] if best[1] else "small-edit"


def recommend_route(
    objective: str,
    *,
    context: str = "",
    task_class: str | None = None,
    privacy: str = "local-first",
    max_escalation: str = "balanced",
    reserve_output_tokens: int = 1024,
    model_stats: dict[str, Any] | None = None,
) -> RouteRecommendation:
    selected_task = classify_task(objective, forced=task_class)
    profiles = load_profiles()
    rejected: list[dict[str, Any]] = []
    reasons = [
        f"task_class={selected_task}",
        f"privacy={privacy}",
        f"max_escalation={max_escalation}",
    ]
    if model_stats:
        reasons.append("reliability-weighted from ledger history")
    candidates = _filter_profiles(profiles, privacy=privacy, max_escalation=max_escalation)
    ranked = sorted(
        candidates,
        key=lambda profile: _profile_score(profile, selected_task, privacy, max_escalation, model_stats),
    )
    text = f"{objective}\n\n{context}".strip()

    for profile in ranked:
        budget = budget_for_text(text, model_id=profile.id, reserve_output_tokens=reserve_output_tokens)
        if budget.fits and _profile_satisfies_task(profile, selected_task):
            reasons.append(f"selected {profile.id}: cheapest sufficient profile that fits context")
            return RouteRecommendation(
                task_class=selected_task,
                selected_model=profile.id,
                provider=profile.provider,
                privacy=profile.privacy,
                estimated_input_tokens=budget.estimated_input_tokens,
                context_window=profile.context_window,
                fits=True,
                escalation_level=_escalation_level(profile),
                reasons=tuple(reasons),
                rejected=tuple(rejected),
            )
        rejected.append(
            {
                "model_id": profile.id,
                "fits": budget.fits,
                "reason": "insufficient-context" if not budget.fits else "insufficient-task-strength",
            }
        )

    fallback = max(candidates or profiles, key=lambda profile: profile.context_window)
    budget = budget_for_text(text, model_id=fallback.id, reserve_output_tokens=reserve_output_tokens)
    reasons.append("no sufficient profile found; fallback is largest allowed context")
    return RouteRecommendation(
        task_class=selected_task,
        selected_model=fallback.id,
        provider=fallback.provider,
        privacy=fallback.privacy,
        estimated_input_tokens=budget.estimated_input_tokens,
        context_window=fallback.context_window,
        fits=budget.fits,
        escalation_level=_escalation_level(fallback),
        reasons=tuple(reasons),
        rejected=tuple(rejected),
    )


def _filter_profiles(
    profiles: list[ProviderProfile],
    *,
    privacy: str,
    max_escalation: str,
) -> list[ProviderProfile]:
    allowed = profiles
    if privacy == "local-only":
        allowed = [profile for profile in allowed if profile.privacy == "local"]
    if max_escalation == "local":
        allowed = [profile for profile in allowed if profile.privacy == "local"]
    if max_escalation == "balanced":
        allowed = [profile for profile in allowed if profile.id != "anthropic-compatible-long"]
    return allowed


def _reliability_penalty(profile: ProviderProfile, model_stats: dict[str, Any] | None) -> int:
    """Down-rank a model whose ledger history shows failures or heavy retries.

    Bounded on purpose: a poor track record penalizes a model, but a hard
    task-strength mismatch (penalty 20) still wins — being right for the task
    outranks being historically reliable at the wrong one."""
    if not model_stats:
        return 0
    stats = model_stats.get(profile.id)
    if not stats or not stats.get("entries"):
        return 0
    fail_rate = float(stats.get("failure_rate", 0.0))
    retry_rate = stats.get("retries", 0) / stats["entries"]
    return round(fail_rate * 10 + min(retry_rate, 1.0) * 2)


def _profile_score(
    profile: ProviderProfile,
    task_class: str,
    privacy: str,
    max_escalation: str,
    model_stats: dict[str, Any] | None = None,
) -> tuple[int, int, int]:
    local_penalty = 0 if profile.privacy == "local" else 10
    if privacy == "cloud-allowed":
        local_penalty = 0 if profile.privacy == "local" else 2
    if privacy == "cloud-allowed" and max_escalation == "strong" and task_class in {"release", "security-review"}:
        local_penalty = 8 if profile.privacy == "local" else 0
    strength_penalty = 0 if _profile_satisfies_task(profile, task_class) else 20
    reliability_penalty = _reliability_penalty(profile, model_stats)
    return (local_penalty + strength_penalty + reliability_penalty, profile.context_window, len(profile.strengths))


def _profile_satisfies_task(profile: ProviderProfile, task_class: str) -> bool:
    strengths = set(profile.strengths)
    if task_class == "small-edit":
        return True
    if task_class == "creative-generation":
        return profile.provider == "local" or "synthesis" in strengths or "drafting" in strengths
    if task_class == "repository-analysis":
        return "repository-context" in strengths or "review" in strengths or "long-context" in strengths
    if task_class == "long-context-synthesis":
        return "long-context" in strengths or profile.context_window >= 32768
    if task_class == "release":
        return "release" in strengths or "review" in strengths or profile.privacy == "local"
    if task_class == "security-review":
        return "review" in strengths or profile.privacy == "local"
    return True


def _escalation_level(profile: ProviderProfile) -> str:
    if profile.privacy == "local" and profile.context_window <= 8192:
        return "local-cheap"
    if profile.privacy == "local":
        return "local-extended"
    return "cloud-escalated"
