"""Thompson-sampling bandit over the frugality ledger.

The static reliability penalty was step one: it can only punish. A Beta-Bernoulli
bandit both *exploits* models with a good track record and *explores*
under-observed ones, converging on the cheapest reliable route as ledger
evidence accumulates. Pure stdlib — no numpy, no sklearn.

Each model is an arm. Its posterior is Beta(1 + passes, 1 + failures) built from
`summarize_by_model` stats; one sample per arm ranks the candidates. Arms with no
history sample from Beta(1, 1) (uniform) — maximum exploration pressure, which is
exactly right for an untried model.
"""

from __future__ import annotations

import random
from typing import Any


def posterior_params(stats: dict[str, Any] | None) -> tuple[float, float]:
    """Beta posterior (alpha, beta) for one arm from ledger stats."""
    if not stats or not stats.get("entries"):
        return (1.0, 1.0)
    entries = float(stats["entries"])
    failures = float(stats.get("failures", 0))
    passes = max(0.0, entries - failures)
    # Retries are soft evidence of friction: half-weight failures.
    retry_pressure = min(float(stats.get("retries", 0)) * 0.5, entries)
    return (1.0 + passes, 1.0 + failures + retry_pressure)


def thompson_scores(
    arm_ids: list[str],
    model_stats: dict[str, Any] | None,
    *,
    seed: int | None = None,
) -> dict[str, float]:
    """One posterior sample per arm. Deterministic under a fixed seed."""
    rng = random.Random(seed)
    samples: dict[str, float] = {}
    for arm in arm_ids:
        alpha, beta = posterior_params((model_stats or {}).get(arm))
        samples[arm] = rng.betavariate(alpha, beta)
    return samples


def expected_success(stats: dict[str, Any] | None) -> float:
    """Posterior mean — the deterministic companion to the sampled score."""
    alpha, beta = posterior_params(stats)
    return alpha / (alpha + beta)
