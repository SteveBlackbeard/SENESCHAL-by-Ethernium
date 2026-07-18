"""Minimal Ollama adapter with no third-party dependencies."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Callable


DEFAULT_OLLAMA_BASE_URL = "http://localhost:11434"


@dataclass(frozen=True)
class ModelResponse:
    ok: bool
    provider: str
    model: str
    text: str
    error: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "provider": self.provider,
            "model": self.model,
            "text": self.text,
            "error": self.error,
        }


Transport = Callable[[str, bytes, int], dict[str, Any]]


def call_ollama(
    prompt: str,
    *,
    model: str,
    base_url: str | None = None,
    timeout: int = 120,
    transport: Transport | None = None,
) -> ModelResponse:
    if not model:
        return ModelResponse(ok=False, provider="ollama", model="", text="", error="missing-model")
    endpoint = (base_url or DEFAULT_OLLAMA_BASE_URL).rstrip("/") + "/api/generate"
    payload = json.dumps({"model": model, "prompt": prompt, "stream": False}).encode("utf-8")
    try:
        data = transport(endpoint, payload, timeout) if transport else _post_json(endpoint, payload, timeout)
    except urllib.error.URLError as exc:
        return ModelResponse(ok=False, provider="ollama", model=model, text="", error=f"network-error: {exc.reason}")
    except TimeoutError:
        return ModelResponse(ok=False, provider="ollama", model=model, text="", error="timeout")
    except json.JSONDecodeError as exc:
        return ModelResponse(ok=False, provider="ollama", model=model, text="", error=f"invalid-json: {exc}")

    if "error" in data:
        return ModelResponse(ok=False, provider="ollama", model=model, text="", error=str(data["error"]))
    return ModelResponse(ok=True, provider="ollama", model=model, text=str(data.get("response", "")))


def resolve_ollama_settings(
    *,
    endpoint_env: str | None,
    model_env: str | None,
    model_override: str | None = None,
) -> tuple[str, str]:
    base_url = os.environ.get(endpoint_env or "", DEFAULT_OLLAMA_BASE_URL)
    model = model_override or os.environ.get(model_env or "", "")
    return base_url, model


def _post_json(endpoint: str, payload: bytes, timeout: int) -> dict[str, Any]:
    request = urllib.request.Request(
        endpoint,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))
