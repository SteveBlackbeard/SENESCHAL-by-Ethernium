"""Context snapshot and diff cache for token reuse."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .context_packer import _collect_candidates
from .token_budget import estimate_tokens


DEFAULT_CACHE = ".robinhood/context-cache.json"


@dataclass(frozen=True)
class FileSnapshot:
    path: str
    sha256: str
    estimated_tokens: int

    def to_dict(self) -> dict[str, Any]:
        return {"path": self.path, "sha256": self.sha256, "estimated_tokens": self.estimated_tokens}


@dataclass(frozen=True)
class ContextSnapshot:
    root: str
    created_at: str
    files: tuple[FileSnapshot, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "root": self.root,
            "created_at": self.created_at,
            "files": [item.to_dict() for item in self.files],
        }


def create_snapshot(path: Path) -> ContextSnapshot:
    root = path.resolve()
    base = root.parent if root.is_file() else root
    files: list[FileSnapshot] = []
    for item, tokens, _score in _collect_candidates(root):
        text = item.read_text(encoding="utf-8", errors="replace")
        relative = item.relative_to(base).as_posix()
        files.append(
            FileSnapshot(
                path=relative,
                sha256=hashlib.sha256(text.encode("utf-8")).hexdigest(),
                estimated_tokens=tokens,
            )
        )
    return ContextSnapshot(
        root=root.as_posix(),
        created_at=datetime.now(timezone.utc).isoformat(),
        files=tuple(sorted(files, key=lambda item: item.path)),
    )


def write_snapshot(snapshot: ContextSnapshot, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(snapshot.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def read_snapshot(path: Path) -> ContextSnapshot:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return ContextSnapshot(
        root=str(payload["root"]),
        created_at=str(payload["created_at"]),
        files=tuple(
            FileSnapshot(
                path=str(item["path"]),
                sha256=str(item["sha256"]),
                estimated_tokens=int(item["estimated_tokens"]),
            )
            for item in payload["files"]
        ),
    )


def diff_snapshot(previous: ContextSnapshot, current: ContextSnapshot) -> dict[str, Any]:
    old = {item.path: item for item in previous.files}
    new = {item.path: item for item in current.files}
    added = [new[path] for path in sorted(new.keys() - old.keys())]
    deleted = [old[path] for path in sorted(old.keys() - new.keys())]
    changed = [new[path] for path in sorted(new.keys() & old.keys()) if new[path].sha256 != old[path].sha256]
    unchanged = [new[path] for path in sorted(new.keys() & old.keys()) if new[path].sha256 == old[path].sha256]
    full_tokens = sum(item.estimated_tokens for item in current.files)
    delta_tokens = sum(item.estimated_tokens for item in added + changed)
    saved_tokens = max(0, full_tokens - delta_tokens)
    saved_ratio = saved_tokens / full_tokens if full_tokens else 0.0
    return {
        "previous_created_at": previous.created_at,
        "current_created_at": current.created_at,
        "files_total": len(current.files),
        "added": [item.to_dict() for item in added],
        "changed": [item.to_dict() for item in changed],
        "deleted": [item.to_dict() for item in deleted],
        "unchanged_count": len(unchanged),
        "full_context_tokens": full_tokens,
        "delta_context_tokens": delta_tokens,
        "estimated_saved_tokens": saved_tokens,
        "estimated_saved_ratio": round(saved_ratio, 4),
    }


def estimate_prompt_reuse(system_prompt: str, user_prompt: str) -> dict[str, Any]:
    system_tokens = estimate_tokens(system_prompt)
    user_tokens = estimate_tokens(user_prompt)
    total = system_tokens + user_tokens
    return {
        "system_prompt_tokens": system_tokens,
        "user_prompt_tokens": user_tokens,
        "total_tokens": total,
        "cacheable_tokens": system_tokens,
        "cacheable_ratio": round(system_tokens / total, 4) if total else 0.0,
    }


def plan_cache_layout(
    system_prompt: str,
    user_prompt: str,
    stable_blocks: list[str] | None = None,
    *,
    input_cost_per_million: float = 0.0,
    runs: int = 1,
    cache_discount: float = 0.9,
) -> dict[str, Any]:
    """Provider prompt-caching layout optimizer.

    Providers (Anthropic/OpenAI) discount ~90% of a cached prompt PREFIX — but
    only the prefix: one variable byte early in the prompt invalidates everything
    after it. The optimal layout is therefore [system + stable blocks, largest
    first] then the variable user segment last. Returns the ordered layout, the
    cacheable prefix size, and the money left on the table by a naive layout.
    """
    blocks = stable_blocks or []
    ordered_stable = sorted(blocks, key=lambda b: -estimate_tokens(b))
    stable_segments = [s for s in [system_prompt, *ordered_stable] if s and s.strip()]
    prefix_tokens = sum(estimate_tokens(s) for s in stable_segments)
    user_tokens = estimate_tokens(user_prompt)
    total = prefix_tokens + user_tokens

    # Savings model: from run 2 onward the stable prefix costs (1-discount) of
    # its normal price. A naive layout that interleaves variable content caches 0.
    cached_runs = max(0, runs - 1)
    tokens_discounted = prefix_tokens * cached_runs
    cost_saved = (tokens_discounted / 1_000_000) * input_cost_per_million * cache_discount

    return {
        "layout": (
            [{"segment": "system+stable", "order": i, "tokens": estimate_tokens(s)} for i, s in enumerate(stable_segments)]
            + [{"segment": "variable-user", "order": len(stable_segments), "tokens": user_tokens}]
        ),
        "cacheable_prefix_tokens": prefix_tokens,
        "total_tokens": total,
        "cacheable_ratio": round(prefix_tokens / total, 4) if total else 0.0,
        "runs": runs,
        "tokens_discounted_across_runs": tokens_discounted,
        "estimated_cost_saved": round(cost_saved, 6),
        "advice": "place stable segments first; one variable byte early in the prompt invalidates the provider cache for everything after it",
    }
