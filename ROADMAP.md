# Seneschal Roadmap

## Phase 0: Incubation

Status: complete.

Deliverables:

- README
- governance seed
- rulebook
- frugality doctrine
- threat model
- extraction contract
- manifest

Acceptance:

- no leaked prompts
- no runtime dependency on Continuity Legacy
- clear value thesis: reduce cost, risk, and drift

## Phase 1: Minimal Executable Tool

Status: complete.

Build:

- `seneschal/health_guard.py`
- `seneschal/context_packet.py`
- `seneschal/frugality_ledger.py`
- `seneschal/prompt_firewall.py`
- `seneschal/capability_broker.py`
- `seneschal/cli.py`
- `tests/`

Acceptance:

- validates manifest and docs
- writes JSONL usage entries
- emits a context packet from a template
- scans text/files for basic prompt risk
- checks scoped capabilities
- runs locally without network

## Phase 2: Defensive Intelligence

Status: current.

Build:

- `adversarial_cases/`
- stronger prompt firewall detectors
- machine-readable mitigation reports

Acceptance:

- labels untrusted inputs
- detects common injection markers
- flags zero-width and suspicious Unicode
- checks tool permission scope
- runs tests against benign adversarial cases

## Phase 3: Provider-Neutral Scorecard

Status: partially implemented.

Build:

- `provider_profiles.json`
- `provider_profiles.py`
- `token_budget.py`
- `context_packer.py`
- scorecard command
- routing recommendations
- CLI commands:
  - `seneschal models`
  - `seneschal budget`
  - `seneschal pack`

Acceptance:

- compares model cost, latency, context, and reliability
- reports measured tokens where tokenizer support exists
- falls back to explicit estimates where tokenizer support does not exist
- packs context under a budget
- stores observations without proprietary prompts
- recommends local/cloud routing

Implemented now:

- provider profile registry
- fallback token budget estimator
- context packer under explicit token budget
- frugal route recommendations
- CLI and MCP surfaces for models, budget, pack, and route

Still planned:

- measured tokenizer plugins
- task classifier
- provider adapter dry-runs

## Phase 3.5: Editor And MCP Integration

Status: documentation scaffold complete, implementation planned.

Build:

- VS Code task template
- Cursor rule template
- MCP server contract
- optional MCP server implementation

Acceptance:

- integrations call Seneschal CLI or MCP
- Seneschal remains standalone
- no editor-specific integration becomes required
- MCP exposes health, scan, packet, capability, budget, pack, and route tools
- model invocation stays deferred until scan and budget controls are stable

## Phase 4: Standalone Release Hardening

Status: current.

Build:

- `pyproject.toml`
- local Ollama adapter
- `seneschal run`
- project config
- quality gate
- OpenAI-compatible adapter
- CI
- release notes
- installation docs

Acceptance:

- Seneschal stays independent from Continuity Legacy
- tests pass in its own repo
- no private Continuity file is required
- every real model call passes request planning first

## Deferred

Do not build until later:

- dashboard
- database
- blockchain anchoring
- autonomous multi-agent daemon
- provider-specific prompt emulation
- complex self-healing loops
