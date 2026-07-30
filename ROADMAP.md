# Seneschal Roadmap

Status lines below describe **the code, not the intent**. Phases 0 through 4 are
built and covered by the test suite; a phase is only marked complete when its
acceptance criteria are exercised by tests that run in CI.

Verify it yourself rather than trusting this file:

```bash
python -m pytest -q          # 90 tests
seneschal health --strict    # works from an installed wheel, not just a checkout
```

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

Status: complete.

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

Completed since this phase was written:

- measured tokenizer plugins — `token_budget.count_tokens` uses tiktoken when a
  profile declares one (`"tiktoken:cl100k_base"`) and reports `tokenizer_used`
  so a measured count is never confused with an estimate
- task classifier — `router.classify_task`
- provider adapter dry-runs — `capacity_broker.broker_dry_run`, exposed on the
  CLI and as an MCP tool

## Phase 3.5: Editor And MCP Integration

Status: complete. The MCP server is implemented (`seneschal/mcp_server.py`,
19 tools) and runs under Cursor and Claude Desktop; see
`integrations/mcp/cursor-setup.md`.

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

Status: complete, shipped as 0.2.0. Every item below exists in the package:
`quality_gate.py`, `ollama_adapter.py`, `openai_compatible_adapter.py`,
`seneschal run`, `config.py`, CI on Linux and Windows across Python 3.10-3.13,
`CHANGELOG.md`, and `GETTING_STARTED.md`.

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

## Known Gaps

Built, but without published measurements:

- **Cascade and bandit savings.** Both are implemented and tested against fake
  transports, so the logic is verified. What is *not* published is a savings
  figure, because an honest one needs real provider calls accumulated in a
  ledger over time. Context selection is measured instead — see the table in
  `README.md` and `scripts/benchmark_savings.py`. A cascade number will be
  published when it can be reproduced, not before.

## Deferred

Do not build until later:

- dashboard
- database
- blockchain anchoring
- autonomous multi-agent daemon
- provider-specific prompt emulation
- complex self-healing loops
