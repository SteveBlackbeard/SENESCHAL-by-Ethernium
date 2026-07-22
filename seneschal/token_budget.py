"""Token budget estimates without provider lock-in."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .provider_profiles import ProviderProfile, get_profile


@dataclass(frozen=True)
class TokenBudget:
    model_id: str
    provider: str
    tokenizer: str
    context_window: int
    reserve_output_tokens: int
    available_input_tokens: int
    estimated_input_tokens: int
    fits: bool
    usage_ratio: float
    estimated_input_cost: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "model_id": self.model_id,
            "provider": self.provider,
            "tokenizer": self.tokenizer,
            "context_window": self.context_window,
            "reserve_output_tokens": self.reserve_output_tokens,
            "available_input_tokens": self.available_input_tokens,
            "estimated_input_tokens": self.estimated_input_tokens,
            "fits": self.fits,
            "usage_ratio": self.usage_ratio,
            "estimated_input_cost": self.estimated_input_cost,
        }


def estimate_tokens(text: str) -> int:
    """Conservative tokenizer-free estimate for mixed prose and code."""
    if not text:
        return 0
    non_space = sum(1 for char in text if not char.isspace())
    lines = text.count("\n") + 1
    return max(1, (non_space + 3) // 4 + lines)


def count_tokens(text: str, *, tokenizer: str = "estimate") -> tuple[int, str]:
    """Return ``(token_count, tokenizer_used)``.

    When a profile declares a real tokenizer (e.g. ``"tiktoken:cl100k_base"``)
    and the package is installed, the count is measured and ``tokenizer_used``
    reflects that. Otherwise it falls back to the heuristic estimate, so the tool
    still runs with zero extra dependencies. This is what turns "we *estimate*
    your savings" into "we *measured* them" wherever a measured tokenizer exists.
    """
    if not text:
        return 0, "estimate"
    if tokenizer.startswith("tiktoken"):
        encoding_name = tokenizer.split(":", 1)[1] if ":" in tokenizer else "cl100k_base"
        try:
            import tiktoken

            encoder = tiktoken.get_encoding(encoding_name)
            return len(encoder.encode(text)), f"tiktoken:{encoding_name}"
        except Exception:
            pass  # package/encoding unavailable -> honest fallback below
    return estimate_tokens(text), "estimate"


def budget_for_text(text: str, *, model_id: str, reserve_output_tokens: int = 1024) -> TokenBudget:
    profile = get_profile(model_id)
    tokens, tokenizer_used = count_tokens(text, tokenizer=profile.tokenizer)
    return budget_for_tokens(
        tokens,
        profile=profile,
        reserve_output_tokens=reserve_output_tokens,
        tokenizer_used=tokenizer_used,
    )


def budget_for_file(path: Path, *, model_id: str, reserve_output_tokens: int = 1024) -> TokenBudget:
    text = path.read_text(encoding="utf-8", errors="replace")
    return budget_for_text(text, model_id=model_id, reserve_output_tokens=reserve_output_tokens)


def budget_for_tokens(
    estimated_input_tokens: int,
    *,
    profile: ProviderProfile,
    reserve_output_tokens: int = 1024,
    tokenizer_used: str | None = None,
) -> TokenBudget:
    available_input_tokens = max(0, profile.context_window - reserve_output_tokens)
    usage_ratio = estimated_input_tokens / available_input_tokens if available_input_tokens else 1.0
    estimated_input_cost = (estimated_input_tokens / 1_000_000) * profile.input_cost_per_million
    return TokenBudget(
        model_id=profile.id,
        provider=profile.provider,
        tokenizer=tokenizer_used or profile.tokenizer,
        context_window=profile.context_window,
        reserve_output_tokens=reserve_output_tokens,
        available_input_tokens=available_input_tokens,
        estimated_input_tokens=estimated_input_tokens,
        fits=estimated_input_tokens <= available_input_tokens,
        usage_ratio=round(usage_ratio, 4),
        estimated_input_cost=round(estimated_input_cost, 8),
    )
