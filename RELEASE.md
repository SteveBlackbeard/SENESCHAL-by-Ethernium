# ROBIN HOOD Release Checklist

ROBIN HOOD is releasable when the package can be installed, tested, planned, and built without private files or remote model access.

## Local Gate

```powershell
python agentops\health_guard.py --strict
pytest -q
python -m build
python -m agentops.cli providers --providers providers.local.json.example
python -m agentops.cli provider-health --providers providers.local.json.example
python -m agentops.cli plan-request --config robinhood.config.json.example --objective "Analyze repo architecture" --estimated-input-tokens 8000
```

## Clean Install Gate

```powershell
python -m venv .venv-release
.\.venv-release\Scripts\python -m pip install --upgrade pip
.\.venv-release\Scripts\python -m pip install dist\robin_hood-*.whl
.\.venv-release\Scripts\robinhood health --strict
```

## Release Rules

- Keep `providers.local.json` private.
- Keep `robinhood.config.json` private.
- Do not publish real API keys, endpoints, quotas, or provider account names.
- Do not publish generated `.robinhood/` state.
- Every real adapter path must pass `plan-request` first.
- Every failed call should mark provider state.
- Quality gate failures are release-relevant failures.

## Current Product Surface

- CLI
- optional MCP server
- provider catalog
- project config
- Ollama adapter
- OpenAI-compatible adapter
- request planner
- quality gate
- circuit breaker
- context pack/select/cache
- prompt firewall
- frugality ledger
