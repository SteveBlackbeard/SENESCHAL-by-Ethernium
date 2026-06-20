"""Pack repository context under an explicit token budget."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .prompt_firewall import IGNORED_DIRS, TEXT_SUFFIXES, classify_file
from .provider_profiles import get_profile
from .token_budget import budget_for_tokens, estimate_tokens


EXTRA_IGNORED_DIRS = {"coverage", ".mypy_cache", ".ruff_cache", ".tox", "htmlcov"}
HIGH_VALUE_NAMES = {"README.md", "pyproject.toml", "package.json", "TOOL_MANIFEST.json", "RULEBOOK.md", "FRUGALITY.md"}
LOW_VALUE_PARTS = {"dist", "build", "node_modules", ".git", ".venv", "__pycache__"}


@dataclass(frozen=True)
class PackedFile:
    path: str
    estimated_tokens: int
    score: int


@dataclass(frozen=True)
class ExcludedFile:
    path: str
    estimated_tokens: int
    reason: str


@dataclass(frozen=True)
class ContextPack:
    root: str
    model_id: str
    max_input_tokens: int
    estimated_total_tokens: int
    estimated_packed_tokens: int
    reduction_ratio: float
    included: tuple[PackedFile, ...]
    excluded: tuple[ExcludedFile, ...]

    def to_dict(self) -> dict[str, Any]:
        budget = budget_for_tokens(
            self.estimated_packed_tokens,
            profile=get_profile(self.model_id),
            reserve_output_tokens=max(0, get_profile(self.model_id).context_window - self.max_input_tokens),
        )
        return {
            "root": self.root,
            "model_id": self.model_id,
            "max_input_tokens": self.max_input_tokens,
            "estimated_total_tokens": self.estimated_total_tokens,
            "estimated_packed_tokens": self.estimated_packed_tokens,
            "reduction_ratio": self.reduction_ratio,
            "budget": budget.to_dict(),
            "included": [item.__dict__ for item in self.included],
            "excluded": [item.__dict__ for item in self.excluded],
        }


def pack_context(
    path: Path,
    *,
    model_id: str,
    max_tokens: int | None = None,
    reserve_output_tokens: int = 1024,
    source: str = "internal",
) -> ContextPack:
    root = path.resolve()
    profile = get_profile(model_id)
    max_input_tokens = max_tokens if max_tokens is not None else max(0, profile.context_window - reserve_output_tokens)
    candidates = _collect_candidates(root)
    estimated_total = sum(tokens for _, tokens, _ in candidates)

    included: list[PackedFile] = []
    excluded: list[ExcludedFile] = []
    used = 0
    for item, tokens, score in sorted(candidates, key=lambda row: (-row[2], row[1], row[0].as_posix())):
        relative = _relative(item, root)
        risk = classify_file(item, source=source)
        if risk.blocked:
            excluded.append(ExcludedFile(relative, tokens, "blocked-by-prompt-firewall"))
            continue
        if used + tokens > max_input_tokens:
            excluded.append(ExcludedFile(relative, tokens, "over-token-budget"))
            continue
        included.append(PackedFile(relative, tokens, score))
        used += tokens

    reduction_ratio = 1.0 - (used / estimated_total) if estimated_total else 0.0
    return ContextPack(
        root=root.as_posix(),
        model_id=model_id,
        max_input_tokens=max_input_tokens,
        estimated_total_tokens=estimated_total,
        estimated_packed_tokens=used,
        reduction_ratio=round(reduction_ratio, 4),
        included=tuple(included),
        excluded=tuple(excluded),
    )


def render_pack(pack: ContextPack, root: Path) -> str:
    sections = [
        "# ROBIN HOOD Context Pack",
        "",
        f"model_id: {pack.model_id}",
        f"estimated_packed_tokens: {pack.estimated_packed_tokens}",
        f"max_input_tokens: {pack.max_input_tokens}",
        "",
    ]
    for item in pack.included:
        file_path = root / item.path
        text = file_path.read_text(encoding="utf-8", errors="replace")
        sections.extend([f"## {item.path}", "", "```text", text.rstrip(), "```", ""])
    return "\n".join(sections).rstrip() + "\n"


def _collect_candidates(root: Path) -> list[tuple[Path, int, int]]:
    if root.is_file():
        files = [root] if root.suffix.lower() in TEXT_SUFFIXES else []
        base = root.parent
    elif root.is_dir():
        files = []
        base = root
        ignored = IGNORED_DIRS | EXTRA_IGNORED_DIRS
        for item in root.rglob("*"):
            if any(part in ignored or part.endswith(".egg-info") for part in item.parts):
                continue
            if item.is_file() and item.suffix.lower() in TEXT_SUFFIXES:
                files.append(item)
    else:
        raise FileNotFoundError(root)
    return [(item, estimate_tokens(item.read_text(encoding="utf-8", errors="replace")), _score_file(item, base)) for item in files]


def _score_file(path: Path, root: Path) -> int:
    relative = path.relative_to(root) if path != root else path.name
    parts = set(relative.parts if isinstance(relative, Path) else [str(relative)])
    score = 10
    if path.name in HIGH_VALUE_NAMES:
        score += 40
    if "tests" in parts:
        score += 15
    if "agentops" in parts or "src" in parts:
        score += 20
    if "integrations" in parts:
        score += 8
    if parts & LOW_VALUE_PARTS:
        score -= 40
    if path.name.lower().startswith(("readme", "roadmap", "pending")):
        score += 15
    return score


def _relative(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()
