# ROBIN HOOD by Ethernium

ROBIN HOOD by Ethernium is a local-first control layer for cheaper, safer AI-assisted work.

It helps decide what context to send, what to keep local, what to block, and whether a task deserves a stronger model. The goal is practical token economy: fewer whole-repo dumps, fewer retries, smaller prompts, safer tool scope, and clearer task packets.

## Product Objective

ROBIN HOOD's objective is to be the preflight and execution layer for AI work: reduce tokens, choose the cheapest sufficient provider, prefer local compute, block unsafe or wasteful calls, execute only when the plan is acceptable, and record enough evidence to improve the next run.

## What It Does

- estimates token budgets without locking into one provider
- packs repository context under an explicit model budget
- recommends the cheapest sufficient model path for a task
- snapshots context so unchanged files do not need to be resent
- estimates token-cost savings across repeated runs
- selects the most relevant neighboring context under a token budget
- dry-runs provider capacity routing without API keys or network calls
- scans untrusted text/files for prompt-injection and secret-like material
- creates scoped context packets for agents
- checks least-privilege capability grants
- records cost/retry/outcome data in a JSONL frugality ledger
- exposes terminal and optional MCP controls

## What It Is Not

ROBIN HOOD is not:

- a leaked-prompt archive
- a jailbreak toolkit
- a provider bypass tool
- a dashboard
- a database-backed agent platform
- a dependency of another project

The clean-room rule is simple: study economics and control patterns, then rebuild provider-neutral primitives. Do not copy proprietary prompts or hidden policies.

## Quick Start

```powershell
cd D:\Experimentos\ROBIN-HOOD
pip install -e .
robinhood health --strict
pytest -q
```

Inspect available model profiles:

```powershell
robinhood models
```

List provider profiles from a local catalog:

```powershell
copy providers.local.json.example providers.local.json
robinhood providers --providers providers.local.json
```

Check provider configuration without spending tokens:

```powershell
robinhood provider-health --providers providers.local.json
```

Record local provider state for circuit-breaker routing:

```powershell
robinhood provider-mark --provider ollama-local-code --status fail --reason timeout
robinhood provider-state
```

Estimate whether a file fits a model profile:

```powershell
robinhood budget --file README.md --model local-small
```

Pack a project into a smaller context budget:

```powershell
robinhood pack --path . --model local-long --max-tokens 12000
```

Render the included files as a text packet:

```powershell
robinhood pack --path . --model local-long --max-tokens 12000 --render
```

Recommend a route before spending stronger model budget:

```powershell
robinhood route --objective "Security review before release" --privacy cloud-allowed --max-escalation strong
```

Create a context cache and measure changed-only savings:

```powershell
robinhood snapshot --path .
```

Estimate how much of a prompt can be reused as stable/cacheable context:

```powershell
robinhood reuse --system "stable operating rules" --user "specific task"
```

Convert token savings into money:

```powershell
robinhood savings --full-tokens 28611 --optimized-tokens 6166 --input-cost-per-million 2 --runs 100
```

Or combine snapshot and ROI in one command:

```powershell
robinhood snapshot --path . --input-cost-per-million 2 --runs 100
```

Select changed files plus useful neighbors under a strict budget:

```powershell
robinhood select --path . --changed agentops/cli.py --max-tokens 4000
```

Dry-run provider capacity routing:

```powershell
robinhood broker-dry-run --objective "Security review before release" --estimated-input-tokens 12000 --privacy local-first
```

Use a local provider catalog:

```powershell
robinhood broker-dry-run --providers providers.local.json --objective "Analyze repo" --estimated-input-tokens 8000
```

Avoid locally degraded providers:

```powershell
robinhood broker-dry-run --providers providers.local.json --state .robinhood/provider-state.json --objective "Analyze repo" --estimated-input-tokens 8000
```

Plan the request before any API call:

```powershell
robinhood plan-request --providers providers.local.json --state .robinhood/provider-state.json --objective "Analyze repo" --estimated-input-tokens 8000 --estimated-output-tokens 1200
```

Run through the local Ollama adapter after planning:

```powershell
robinhood run --providers providers.local.json --objective "Summarize this repo" --path . --model llama3.1
```

## CLI

Current commands:

```text
robinhood health
robinhood models
robinhood providers
robinhood provider-health
robinhood provider-state
robinhood provider-mark
robinhood budget
robinhood pack
robinhood route
robinhood snapshot
robinhood reuse
robinhood savings
robinhood select
robinhood broker-dry-run
robinhood plan-request
robinhood run
robinhood packet
robinhood scan
robinhood grant
robinhood log
robinhood report
```

Examples:

```powershell
robinhood scan --path adversarial_cases --source web --fail-on-block
robinhood route --objective "Fix typo in docs" --context "small task"
robinhood snapshot --path .
robinhood packet --objective "Fix release docs" --allowed-file README.md --verify "pytest -q"
robinhood grant --task-id RH-001 --capability read --capability edit --allowed-path ROBIN-HOOD/ --action edit --path ROBIN-HOOD/README.md
robinhood log --task-id RH-002 --model local-small --tokens-estimated 900 --outcome pass --reduced cost
robinhood report
```

## Frugality Core

ROBIN HOOD currently uses explicit provider profiles:

```text
local-small
local-long
openai-compatible-balanced
anthropic-compatible-long
generic-local-lora
```

The default tokenizer is an honest fallback estimate. That is deliberate: the tool should work before provider SDKs, API keys, local servers, or tokenizer packages are installed. Later adapters can add measured tokenizers without changing the command surface.

Private provider catalogs should live in `providers.local.json`. That file is ignored by Git. Use `providers.local.json.example` as a safe template and keep real endpoints, key names, quotas, and enabled providers local.

Experimental local models, including abliterated variants, can be represented as disabled provider profiles in `providers.local.json`. ROBIN HOOD treats them as local compute, not as privileged bypass tools. Keep them disabled until you explicitly need them, run `robinhood scan` on external prompts, run `robinhood plan-request` before use, and keep human review on outputs that affect code, security, legal, medical, finance, or public release decisions.

`robinhood provider-health` checks only local configuration. It verifies enabled/disabled state and required environment variables, but does not call remote APIs or run inference. This keeps readiness cheap, deterministic, and safe to run inside Cursor, VS Code, CI, or an MCP client before any model spend happens.

`robinhood provider-mark` and `robinhood provider-state` implement a small local circuit breaker. If a provider times out, hits quota, rate-limits, or should be disabled, ROBIN HOOD can remember that in `.robinhood/provider-state.json` and the broker can avoid that route before spending more tokens.

`robinhood plan-request` is the final preflight gate before a real adapter call. It combines broker routing, provider readiness, circuit-breaker state, fallback candidates, and estimated input/output cost. It still does not call APIs; it tells a caller whether the request should proceed.

`robinhood run` currently supports the Ollama/local adapter. It still plans first, then calls the selected local provider only if there are no blockers. Failed calls are written to provider state so later plans can avoid degraded routes.

## Integration

ROBIN HOOD can run from:

- terminal
- VS Code tasks
- Cursor rules
- MCP clients
- any workflow that can call a Python CLI

Integration scaffolds live in:

```text
integrations/vscode/tasks.json
integrations/cursor/rules/agentops.mdc
integrations/mcp/server_contract.json
```

Optional MCP server:

```powershell
pip install -e .[mcp]
robinhood-mcp
```

MCP tools expose local controls for health, prompt scanning, context packets, capability checks, model profiles, provider health, provider state, token budgets, context packing, context snapshots, prompt reuse estimates, and routing.
Routing is exposed as a recommendation only; ROBIN HOOD still does not invoke models.

## Compatibility With Continuity Legacy

ROBIN HOOD is compatible with Continuity Legacy, but does not require it.

The intended relationship is:

- Continuity Legacy governs repository integrity, baselines, release gates, and handoff discipline.
- ROBIN HOOD governs token economy, context packing, prompt-risk scanning, model selection, and agent operations.

They are designed to work beside each other. Neither should be embedded inside the other.

## Compatibility Note

The internal Python package is still named `agentops` for compatibility with the incubation prototype. The public product name is ROBIN HOOD.

Backward-compatible console aliases remain available:

```text
agentops
agentops-mcp
```

Prefer the public commands:

```text
robinhood
robinhood-mcp
```

## Status

```text
status: prototype
safe_to_extract: true
runtime_dependencies: none
optional_dependencies: mcp
```

ROBIN HOOD is useful today as a local frugality and safety tool. It is not yet a provider router or model invocation layer.
