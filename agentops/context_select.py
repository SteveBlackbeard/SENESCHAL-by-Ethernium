"""Select the most useful neighboring context under a token budget."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .context_packer import _collect_candidates, _relative, _score_file
from .prompt_firewall import classify_file


@dataclass(frozen=True)
class SelectedContextFile:
    path: str
    estimated_tokens: int
    score: int
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "estimated_tokens": self.estimated_tokens,
            "score": self.score,
            "reason": self.reason,
        }


@dataclass(frozen=True)
class ContextSelection:
    root: str
    max_tokens: int
    estimated_selected_tokens: int
    changed_paths: tuple[str, ...]
    selected: tuple[SelectedContextFile, ...]
    excluded: tuple[SelectedContextFile, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "root": self.root,
            "max_tokens": self.max_tokens,
            "estimated_selected_tokens": self.estimated_selected_tokens,
            "changed_paths": list(self.changed_paths),
            "selected": [item.to_dict() for item in self.selected],
            "excluded": [item.to_dict() for item in self.excluded],
        }


def select_context(
    root: Path,
    *,
    changed_paths: list[str],
    max_tokens: int,
    source: str = "internal",
    min_score: int = 30,
    objective: str = "",
) -> ContextSelection:
    resolved_root = root.resolve()
    changed = {_normalize(path) for path in changed_paths}
    candidates = _collect_candidates(resolved_root)

    # BM25 relevance to the task objective: real IR evidence on top of the
    # structural heuristics (same-dir / same-stem / import-neighbor).
    bm25_scores: dict[str, float] = {}
    if objective:
        from .bm25 import BM25

        corpus = {
            _relative(item, resolved_root): _safe_text(item)
            for item, _tokens, _base in candidates
        }
        raw = BM25(corpus).scores(objective)
        top = max(raw.values(), default=0.0)
        if top > 0:
            bm25_scores = {doc: value / top for doc, value in raw.items()}

    scored: list[SelectedContextFile] = []
    excluded: list[SelectedContextFile] = []

    for item, tokens, base_score in candidates:
        relative = _relative(item, resolved_root)
        risk = classify_file(item, source=source)
        score, reason = _context_score(item, resolved_root, changed, base_score)
        relevance = bm25_scores.get(relative, 0.0)
        if relevance > 0:
            score += int(50 * relevance)
            if relevance >= 0.3:
                reason = f"{reason}+bm25-match"
        record = SelectedContextFile(relative, tokens, score, reason)
        if source != "internal" and risk.blocked:
            excluded.append(SelectedContextFile(relative, tokens, score, "blocked-by-prompt-firewall"))
            continue
        scored.append(record)

    selected: list[SelectedContextFile] = []
    used = 0
    mandatory = [item for item in scored if _normalize(item.path) in changed]
    optional = [item for item in scored if _normalize(item.path) not in changed]

    for item in sorted(mandatory, key=lambda row: (row.estimated_tokens, row.path)):
        if used + item.estimated_tokens > max_tokens:
            excluded.append(SelectedContextFile(item.path, item.estimated_tokens, item.score, "changed-file-over-token-budget"))
            continue
        selected.append(item)
        used += item.estimated_tokens

    for item in sorted(optional, key=lambda row: (-_density(row), -row.score, row.estimated_tokens, row.path)):
        if item.score < min_score:
            excluded.append(SelectedContextFile(item.path, item.estimated_tokens, item.score, "low-relevance"))
            continue
        if used + item.estimated_tokens > max_tokens:
            excluded.append(SelectedContextFile(item.path, item.estimated_tokens, item.score, "over-token-budget"))
            continue
        selected.append(item)
        used += item.estimated_tokens

    return ContextSelection(
        root=resolved_root.as_posix(),
        max_tokens=max_tokens,
        estimated_selected_tokens=used,
        changed_paths=tuple(sorted(changed)),
        selected=tuple(selected),
        excluded=tuple(excluded),
    )


def _context_score(path: Path, root: Path, changed: set[str], base_score: int) -> tuple[int, str]:
    relative = _normalize(_relative(path, root))
    if relative in changed:
        return base_score + 120, "changed-file"
    same_dir = any(Path(relative).parent == Path(item).parent for item in changed)
    same_stem = any(Path(relative).stem == Path(item).stem for item in changed)
    imported = _is_import_neighbor(path, root, changed)

    score = base_score
    reasons: list[str] = []
    if same_dir:
        score += 35
        reasons.append("same-directory")
    if same_stem:
        score += 25
        reasons.append("same-stem")
    if imported:
        score += 45
        reasons.append("import-neighbor")
    if not reasons:
        reasons.append("base-relevance")
    return score, "+".join(reasons)


def _is_import_neighbor(path: Path, root: Path, changed: set[str]) -> bool:
    if path.suffix.lower() != ".py":
        return False
    module_name = path.relative_to(root).with_suffix("").as_posix().replace("/", ".")
    short_name = path.stem
    for changed_path in changed:
        candidate = root / changed_path
        if not candidate.exists() or candidate.suffix.lower() != ".py":
            continue
        text = candidate.read_text(encoding="utf-8", errors="replace")
        if f"import {module_name}" in text or f"from {module_name}" in text:
            return True
        if f"import {short_name}" in text or f"from . import {short_name}" in text or f"from .{short_name}" in text:
            return True
    return False


def _safe_text(path: Path, limit: int = 200_000) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")[:limit]
    except OSError:
        return ""


def _density(item: SelectedContextFile) -> float:
    return item.score / max(1, item.estimated_tokens)


def _normalize(path: str) -> str:
    return path.replace("\\", "/").strip().lstrip("./")
