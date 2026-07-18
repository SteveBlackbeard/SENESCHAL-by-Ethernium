"""OpenAI-compatible chat completions adapter."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any, Callable

from .ollama_adapter import ModelResponse


Transport = Callable[[str, bytes, dict[str, str], int], dict[str, Any]]


def call_openai_compatible(
    prompt: str,
    *,
    model: str,
    base_url: str,
    api_key: str,
    timeout: int = 120,
    transport: Transport | None = None,
) -> ModelResponse:
    if not model:
        return ModelResponse(ok=False, provider="openai-compatible", model="", text="", error="missing-model")
    if not base_url:
        return ModelResponse(ok=False, provider="openai-compatible", model=model, text="", error="missing-base-url")
    if not api_key:
        return ModelResponse(ok=False, provider="openai-compatible", model=model, text="", error="missing-api-key")

    endpoint = base_url.rstrip("/") + "/v1/chat/completions"
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}
    payload = json.dumps(
        {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
        }
    ).encode("utf-8")
    try:
        data = transport(endpoint, payload, headers, timeout) if transport else _post_json(endpoint, payload, headers, timeout)
    except urllib.error.URLError as exc:
        return ModelResponse(ok=False, provider="openai-compatible", model=model, text="", error=f"network-error: {exc.reason}")
    except TimeoutError:
        return ModelResponse(ok=False, provider="openai-compatible", model=model, text="", error="timeout")
    except json.JSONDecodeError as exc:
        return ModelResponse(ok=False, provider="openai-compatible", model=model, text="", error=f"invalid-json: {exc}")

    if "error" in data:
        return ModelResponse(ok=False, provider="openai-compatible", model=model, text="", error=str(data["error"]))
    choices = data.get("choices", [])
    text = ""
    if choices:
        text = str(choices[0].get("message", {}).get("content", ""))
    return ModelResponse(ok=True, provider="openai-compatible", model=model, text=text)


def resolve_openai_compatible_settings(
    *,
    endpoint_env: str | None,
    api_key_env: str | None,
    model_env: str | None,
    model_override: str | None = None,
) -> tuple[str, str, str]:
    base_url = os.environ.get(endpoint_env or "", "")
    api_key = os.environ.get(api_key_env or "", "")
    model = model_override or os.environ.get(model_env or "", "")
    return base_url, api_key, model


def _post_json(endpoint: str, payload: bytes, headers: dict[str, str], timeout: int) -> dict[str, Any]:
    request = urllib.request.Request(endpoint, data=payload, headers=headers, method="POST")
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))
