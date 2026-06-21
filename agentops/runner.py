"""High-level local run pipeline for ROBIN HOOD."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .context_packer import pack_context, render_pack
from .frugality_ledger import append_entry, new_entry
from .ollama_adapter import ModelResponse, call_ollama, resolve_ollama_settings
from .openai_compatible_adapter import call_openai_compatible, resolve_openai_compatible_settings
from .provider_profiles import get_profile
from .provider_state import DEFAULT_PROVIDER_STATE, mark_provider_state
from .quality_gate import QualityReport, evaluate_response
from .request_planner import RequestPlan, plan_request
from .token_budget import estimate_tokens


@dataclass(frozen=True)
class RunResult:
    plan: RequestPlan
    response: ModelResponse
    quality: QualityReport
    prompt_tokens: int
    ledger_path: str | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "plan": self.plan.to_dict(),
            "response": self.response.to_dict(),
            "quality": self.quality.to_dict(),
            "prompt_tokens": self.prompt_tokens,
            "ledger_path": self.ledger_path,
        }


def run_request(
    *,
    objective: str,
    prompt: str = "",
    path: Path | None = None,
    providers_path: Path | None = None,
    state_path: Path | None = None,
    privacy: str = "local-first",
    max_cost: float | None = None,
    estimated_output_tokens: int = 1024,
    model_override: str | None = None,
    ledger_path: Path | None = None,
    timeout: int = 120,
) -> RunResult:
    packed_prompt = _build_prompt(objective=objective, prompt=prompt, path=path)
    prompt_tokens = estimate_tokens(packed_prompt)
    plan = plan_request(
        objective,
        estimated_input_tokens=prompt_tokens,
        estimated_output_tokens=estimated_output_tokens,
        privacy=privacy,
        max_cost=max_cost,
        providers_path=providers_path,
        state_path=state_path,
    )
    if not plan.should_call:
        response = ModelResponse(
            ok=False,
            provider=plan.selected_provider,
            model=plan.selected_model,
            text="",
            error="blocked-by-request-plan",
        )
        quality = evaluate_response(objective, response.text)
        return RunResult(plan=plan, response=response, quality=quality, prompt_tokens=prompt_tokens, ledger_path=str(ledger_path) if ledger_path else None)

    profile = get_profile(plan.selected_model, path=providers_path)
    if profile.provider != "ollama":
        if profile.provider == "openai-compatible":
            base_url, api_key, model = resolve_openai_compatible_settings(
                endpoint_env=profile.endpoint_env,
                api_key_env=profile.api_key_env,
                model_env=profile.model_env,
                model_override=model_override,
            )
            response = call_openai_compatible(packed_prompt, model=model, base_url=base_url, api_key=api_key, timeout=timeout)
        else:
            response = ModelResponse(ok=False, provider=profile.provider, model=profile.id, text="", error="unsupported-provider")
    else:
        base_url, model = resolve_ollama_settings(
            endpoint_env=profile.endpoint_env,
            model_env=profile.model_env,
            model_override=model_override,
        )
        response = call_ollama(packed_prompt, model=model, base_url=base_url, timeout=timeout)

    quality = evaluate_response(objective, response.text) if response.ok else evaluate_response(objective, "")
    state_file = state_path or Path(DEFAULT_PROVIDER_STATE)
    if response.ok and quality.ok:
        mark_provider_state(profile.id, status="ok", reason="run-success", path=state_file)
    else:
        mark_provider_state(profile.id, status="fail", reason=response.error or ",".join(quality.findings), path=state_file)

    if ledger_path is not None:
        append_entry(
            ledger_path,
            new_entry(
                task_id=objective[:80] or "robinhood-run",
                model=plan.selected_model,
                tokens_estimated=prompt_tokens,
                retries=0,
                outcome="ok" if response.ok and quality.ok else (response.error or "quality-gate-failed"),
                reduced="cost",
            ),
        )
    return RunResult(plan=plan, response=response, quality=quality, prompt_tokens=prompt_tokens, ledger_path=str(ledger_path) if ledger_path else None)


def _build_prompt(*, objective: str, prompt: str, path: Path | None) -> str:
    sections = ["# Objective", objective.strip(), ""]
    if prompt:
        sections.extend(["# Prompt", prompt.strip(), ""])
    if path is not None:
        pack = pack_context(path, model_id="local-long", max_tokens=12000, source="internal")
        sections.extend(["# Context", render_pack(pack, path.resolve() if path.is_dir() else path.parent.resolve())])
    return "\n".join(sections).strip() + "\n"
