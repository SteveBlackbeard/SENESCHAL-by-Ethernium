"""Cost and token savings estimates."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class SavingsEstimate:
    full_context_tokens: int
    optimized_context_tokens: int
    saved_tokens_per_run: int
    saved_ratio: float
    runs: int
    input_cost_per_million: float
    full_cost: float
    optimized_cost: float
    estimated_saved_cost: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "full_context_tokens": self.full_context_tokens,
            "optimized_context_tokens": self.optimized_context_tokens,
            "saved_tokens_per_run": self.saved_tokens_per_run,
            "saved_ratio": self.saved_ratio,
            "runs": self.runs,
            "input_cost_per_million": self.input_cost_per_million,
            "full_cost": self.full_cost,
            "optimized_cost": self.optimized_cost,
            "estimated_saved_cost": self.estimated_saved_cost,
        }


def estimate_savings(
    *,
    full_context_tokens: int,
    optimized_context_tokens: int,
    input_cost_per_million: float,
    runs: int = 1,
) -> SavingsEstimate:
    saved_tokens_per_run = max(0, full_context_tokens - optimized_context_tokens)
    full_tokens_total = full_context_tokens * runs
    optimized_tokens_total = optimized_context_tokens * runs
    full_cost = (full_tokens_total / 1_000_000) * input_cost_per_million
    optimized_cost = (optimized_tokens_total / 1_000_000) * input_cost_per_million
    saved_ratio = saved_tokens_per_run / full_context_tokens if full_context_tokens else 0.0
    return SavingsEstimate(
        full_context_tokens=full_context_tokens,
        optimized_context_tokens=optimized_context_tokens,
        saved_tokens_per_run=saved_tokens_per_run,
        saved_ratio=round(saved_ratio, 4),
        runs=runs,
        input_cost_per_million=input_cost_per_million,
        full_cost=round(full_cost, 8),
        optimized_cost=round(optimized_cost, 8),
        estimated_saved_cost=round(full_cost - optimized_cost, 8),
    )
