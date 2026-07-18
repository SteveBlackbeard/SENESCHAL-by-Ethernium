"""Minimal least-privilege capability checks for agent operations."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import PurePosixPath


KNOWN_CAPABILITIES = {
    "read",
    "edit",
    "test",
    "shell",
    "network",
    "git",
    "publish",
}


@dataclass(frozen=True)
class CapabilityGrant:
    task_id: str
    capabilities: set[str]
    allowed_paths: tuple[str, ...] = field(default_factory=tuple)
    denied_paths: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        unknown = self.capabilities - KNOWN_CAPABILITIES
        if unknown:
            raise ValueError(f"unknown capabilities: {', '.join(sorted(unknown))}")


@dataclass(frozen=True)
class CapabilityDecision:
    allowed: bool
    reason: str


def check_action(grant: CapabilityGrant, *, capability: str, path: str | None = None) -> CapabilityDecision:
    if capability not in KNOWN_CAPABILITIES:
        return CapabilityDecision(False, f"unknown capability: {capability}")
    if capability not in grant.capabilities:
        return CapabilityDecision(False, f"capability not granted: {capability}")
    if path is None:
        return CapabilityDecision(True, "capability granted")

    if _is_unsafe_path(path):
        return CapabilityDecision(False, "path traversal or absolute paths are not allowed")

    normalized = _normalize(path)
    for denied in grant.denied_paths:
        if _is_inside(normalized, _normalize(denied)):
            return CapabilityDecision(False, f"path is denied: {denied}")

    if not grant.allowed_paths:
        return CapabilityDecision(False, "path-scoped action requires allowed_paths")
    if any(_is_inside(normalized, _normalize(allowed)) for allowed in grant.allowed_paths):
        return CapabilityDecision(True, "capability and path granted")
    return CapabilityDecision(False, f"path is outside allowed scope: {path}")


def _normalize(path: str) -> str:
    return PurePosixPath(path.replace("\\", "/")).as_posix().strip("/")


def _is_unsafe_path(path: str) -> bool:
    normalized = path.replace("\\", "/")
    pure = PurePosixPath(normalized)
    if pure.is_absolute() or ":" in normalized:
        return True
    return ".." in pure.parts


def _is_inside(path: str, root: str) -> bool:
    return path == root or path.startswith(root.rstrip("/") + "/")
