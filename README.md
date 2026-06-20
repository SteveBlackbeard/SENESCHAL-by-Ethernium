# ROBIN HOOD

ROBIN HOOD is a local-first control layer for cheaper, safer AI-assisted work.

It helps decide what context to send, what to keep local, what to block, and whether a task deserves a stronger model. The goal is practical token economy: fewer whole-repo dumps, fewer retries, smaller prompts, safer tool scope, and clearer task packets.

## What It Does

- estimates token budgets without locking into one provider
- packs repository context under an explicit model budget
- recommends the cheapest sufficient model path for a task
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

## CLI

Current commands:

```text
robinhood health
robinhood models
robinhood budget
robinhood pack
robinhood route
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

MCP tools expose local controls for health, prompt scanning, context packets, capability checks, model profiles, token budgets, and context packing.
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
