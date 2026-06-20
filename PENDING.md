# ROBIN HOOD Pending Work

This file tracks what remains before ROBIN HOOD becomes a finished standalone tool.

## Mission

ROBIN HOOD exists to reduce wasted tokens, retries, unsafe tool use, and context drift across AI-assisted work.

The target is not a generic agent framework. The target is a small local-first control layer that can work with cloud LLM APIs, local LLM servers, LoRA-backed model variants, IDE agents, and repository governance tools without becoming locked to any provider.

## Current Reality

Implemented:

- local health guard
- context packet renderer
- frugality JSONL ledger
- prompt firewall
- recursive prompt and secret-like material scanner
- capability broker
- model/provider profile registry
- tokenizer-free budget estimator
- context packer with ignored-directory filtering
- CLI commands for health, models, budget, pack, packet, scan, grant, log, and report
- optional MCP server with local control tools
- clean-room governance and extraction docs

Not implemented yet:

- API adapters
- routing recommendations based on task class
- VS Code integration package
- Cursor integration package
- standalone repository CI
- measured tokenizer integrations for specific providers
- provider invocation layer

## Phase 2.5: Token Core

Goal: turn frugality from an estimate into a measurable control.

Build:

- `agentops/provider_profiles.py`
- `agentops/provider_profiles.json`
- `agentops/token_budget.py`
- `agentops/context_packer.py`
- CLI commands:
  - `robinhood models`
  - `robinhood budget`
  - `robinhood pack`

Acceptance:

- reports estimated or measured tokens per selected model
- supports a safe fallback when no tokenizer is installed
- excludes ignored directories by default
- ranks files by relevance and risk
- emits a compact context packet under a token budget
- reports before/after token reduction

Status: implemented with fallback token estimates. Provider-specific measured tokenizers remain deferred.

## Phase 3: Provider-Neutral Router

Goal: recommend the cheapest sufficient model path for a task.

Build:

- task classifier:
  - small edit
  - repository analysis
  - release operation
  - security-sensitive review
  - long-context synthesis
- model capability matrix:
  - context window
  - local/cloud
  - tool calling
  - code strength
  - privacy class
  - approximate latency
  - approximate cost
- routing command:
  - `ROBIN HOOD route --task release --privacy local-first`

Acceptance:

- recommends local models for cheap/private work
- recommends stronger models only when needed
- explains the routing decision
- never requires provider secrets in config files

## Phase 4: API Adapter Layer

Goal: connect to model providers without coupling ROBIN HOOD to one vendor.

Planned adapters:

- OpenAI-compatible HTTP APIs
- Ollama
- llama.cpp server
- LM Studio
- vLLM
- Anthropic-compatible adapter
- generic local HTTP adapter

LoRA handling:

- treat LoRA as a model variant or adapter profile, not as a provider by itself
- store base model, adapter id, expected strengths, context window, and local endpoint
- avoid assuming LoRA can be called unless it is served by a compatible runtime

Acceptance:

- adapters implement one small protocol
- provider credentials come from environment variables or local secret stores
- dry-run mode shows the request plan without sending data
- all adapters can be disabled

## Phase 5: Editor And Agent Integrations

Goal: make ROBIN HOOD usable from coding environments without becoming editor-specific.

Build:

- VS Code task templates
- Cursor rules
- MCP server contract
- optional MCP server implementation
- Antigravity notes once its stable extension points are confirmed

Acceptance:

- editor integrations call the same CLI
- ROBIN HOOD remains usable from terminal
- no editor config becomes required for the package
- no integration bypasses prompt scanning or capability checks

## Phase 6: Standalone Release Hardening

Goal: make ROBIN HOOD releasable as its own package and repository without depending on Continuity Legacy.

Build:

- CI
- release notes
- package metadata
- minimal examples

Acceptance:

- `pip install -e .` works in the extracted repo
- tests pass without Continuity Legacy files
- docs explain standalone and Continuity-adjacent use
- no private Continuity file is required

## Frugality Gate

Every new feature must reduce at least one:

- prompt tokens
- completion tokens
- retries
- unsafe scope
- manual reconstruction time
- model cost
- release risk

If it does not reduce one of these, it remains deferred.
