# ROBIN HOOD Roadmap

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

- `ROBIN HOOD/health_guard.py`
- `ROBIN HOOD/context_packet.py`
- `ROBIN HOOD/frugality_ledger.py`
- `ROBIN HOOD/prompt_firewall.py`
- `ROBIN HOOD/capability_broker.py`
- `ROBIN HOOD/cli.py`
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

Status: planned.

Build:

- `provider_profiles.json`
- `provider_profiles.py`
- `token_budget.py`
- `context_packer.py`
- scorecard command
- routing recommendations
- CLI commands:
  - `ROBIN HOOD models`
  - `ROBIN HOOD budget`
  - `ROBIN HOOD pack`

Acceptance:

- compares model cost, latency, context, and reliability
- reports measured tokens where tokenizer support exists
- falls back to explicit estimates where tokenizer support does not exist
- packs context under a budget
- stores observations without proprietary prompts
- recommends local/cloud routing

## Phase 3.5: Editor And MCP Integration

Status: documentation scaffold complete, implementation planned.

Build:

- VS Code task template
- Cursor rule template
- MCP server contract
- optional MCP server implementation

Acceptance:

- integrations call ROBIN HOOD CLI or MCP
- ROBIN HOOD remains standalone
- no editor-specific integration becomes required
- MCP exposes health, scan, packet, capability, budget, pack, and route tools
- model invocation stays deferred until scan and budget controls are stable

## Phase 4: Standalone Repository

Build:

- `pyproject.toml`
- CI
- release notes
- installation docs

Acceptance:

- ROBIN HOOD is extracted from Continuity Legacy
- tests pass in its own repo
- no private Continuity file is required

## Deferred

Do not build until later:

- dashboard
- database
- blockchain anchoring
- autonomous multi-agent daemon
- provider-specific prompt emulation
- complex self-healing loops
