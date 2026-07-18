"""Frugal cascade executor (FrugalGPT pattern).

`run` plans once and calls once. The cascade instead walks the candidate list
cheapest-sufficient-first: call → quality gate → escalate only on failure — and
records every hop in the frugality ledger as evidence. This is the published
pattern that showed ~90% cost reduction at equal quality; Seneschal already had
all the pieces (router, adapters, gate, ledger) — this is the loop that joins
them.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from .frugality_ledger import append_entry, new_entry
from .ollama_adapter import ModelResponse, call_ollama, resolve_ollama_settings
from .openai_compatible_adapter import call_openai_compatible, resolve_openai_compatible_settings
from .provider_profiles import load_profiles
from .provider_state import DEFAULT_PROVIDER_STATE, mark_provider_state
from .quality_gate import evaluate_response
from .router import _filter_profiles, _profile_score, classify_task
from .runner import _build_prompt
from .token_budget import count_tokens


@dataclass(frozen=True)
class CascadeHop:
    model_id: str
    provider: str
    called: bool
    ok: bool
    quality_score: int
    findings: tuple[str, ...]
    error: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "model_id": self.model_id,
            "provider": self.provider,
            "called": self.called,
            "ok": self.ok,
            "quality_score": self.quality_score,
            "findings": list(self.findings),
            "error": self.error,
        }


@dataclass(frozen=True)
class CascadeResult:
    ok: bool
    text: str
    selected_model: str
    task_class: str
    prompt_tokens: int
    hops: tuple[CascadeHop, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "text": self.text,
            "selected_model": self.selected_model,
            "task_class": self.task_class,
            "prompt_tokens": self.prompt_tokens,
            "escalations": max(0, sum(1 for h in self.hops if h.called) - 1),
            "hops": [hop.to_dict() for hop in self.hops],
        }


def run_cascade(
    objective: str,
    *,
    prompt: str = "",
    path: Path | None = None,
    privacy: str = "local-first",
    max_hops: int = 3,
    providers_path: Path | None = None,
    state_path: Path | None = None,
    ledger_path: Path | None = None,
    model_stats: dict[str, Any] | None = None,
    model_override: str | None = None,
    timeout: int = 120,
    transports: dict[str, Callable] | None = None,
) -> CascadeResult:
    packed = _build_prompt(objective=objective, prompt=prompt, path=path)
    task_class = classify_task(objective)
    profiles = [p for p in load_profiles(providers_path) if p.enabled]
    candidates = _filter_profiles(profiles, privacy=privacy, max_escalation="strong")
    ranked = sorted(
        candidates,
        key=lambda p: _profile_score(p, task_class, privacy, "strong", model_stats),
    )

    hops: list[CascadeHop] = []
    state_file = state_path or Path(DEFAULT_PROVIDER_STATE)
    for profile in ranked[: max(1, max_hops)]:
        transport = (transports or {}).get(profile.id)
        response = _call_profile(
            profile, packed, model_override=model_override, timeout=timeout, transport=transport
        )
        if not response.ok and response.error in {"missing-model", "missing-base-url", "missing-api-key", "unsupported-provider"}:
            # Not configured — skip without spending a ledger entry on it.
            hops.append(CascadeHop(profile.id, profile.provider, False, False, 0, (), response.error))
            continue

        quality = evaluate_response(objective, response.text if response.ok else "")
        passed = response.ok and quality.ok
        tokens, _used = count_tokens(packed, tokenizer=profile.tokenizer)
        hops.append(CascadeHop(
            profile.id, profile.provider, True, passed, quality.score,
            quality.findings, response.error,
        ))
        mark_provider_state(
            profile.id,
            status="ok" if passed else "fail",
            reason="cascade-pass" if passed else (response.error or ",".join(quality.findings)),
            path=state_file,
        )
        if ledger_path is not None:
            append_entry(ledger_path, new_entry(
                task_id=objective[:80] or "cascade",
                model=profile.id,
                tokens_estimated=tokens,
                retries=0,
                outcome="pass" if passed else "fail",
                reduced="cost",
            ))
        if passed:
            return CascadeResult(
                ok=True, text=response.text, selected_model=profile.id,
                task_class=task_class,
                prompt_tokens=count_tokens(packed)[0], hops=tuple(hops),
            )

    return CascadeResult(
        ok=False, text="", selected_model="",
        task_class=task_class, prompt_tokens=count_tokens(packed)[0], hops=tuple(hops),
    )


def _call_profile(profile, packed: str, *, model_override, timeout, transport) -> ModelResponse:
    if profile.provider == "ollama":
        base_url, model = resolve_ollama_settings(
            endpoint_env=profile.endpoint_env, model_env=profile.model_env, model_override=model_override
        )
        return call_ollama(packed, model=model, base_url=base_url, timeout=timeout, transport=transport)
    if profile.provider == "openai-compatible":
        base_url, api_key, model = resolve_openai_compatible_settings(
            endpoint_env=profile.endpoint_env, api_key_env=profile.api_key_env,
            model_env=profile.model_env, model_override=model_override,
        )
        return call_openai_compatible(
            packed, model=model, base_url=base_url, api_key=api_key, timeout=timeout, transport=transport
        )
    return ModelResponse(ok=False, provider=profile.provider, model=profile.id, text="", error="unsupported-provider")
