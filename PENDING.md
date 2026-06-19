# AgentOps Pending Work

This file tracks what remains before AgentOps becomes a finished standalone tool.

## Mission

AgentOps exists to reduce wasted tokens, retries, unsafe tool use, and context drift across AI-assisted work.

The target is not a generic agent framework. The target is a small local-first control layer that can work with cloud LLM APIs, local LLM servers, LoRA-backed model variants, IDE agents, and repository governance tools without becoming locked to any provider.

## Current Reality

Implemented:

- local health guard
- context packet renderer
- frugality JSONL ledger
- prompt firewall
- recursive prompt and secret-like material scanner
- capability broker
- CLI commands for health, packet, scan, grant, log, and report
- clean-room governance and extraction docs

Not implemented yet:

- measured token accounting per model
- tokenizer-aware context packing
- model/provider profile registry
- API adapters
- routing recommendations based on task class
- VS Code integration package
- Cursor integration package
- MCP server
- standalone repository CI

## Phase 2.5: Token Core

Goal: turn frugality from an estimate into a measurable control.

Build:

- `agentops/provider_profiles.py`
- `agentops/provider_profiles.json`
- `agentops/token_budget.py`
- `agentops/context_packer.py`
- CLI commands:
  - `agentops models`
  - `agentops budget`
  - `agentops pack`

Acceptance:

- reports estimated or measured tokens per selected model
- supports a safe fallback when no tokenizer is installed
- excludes ignored directories by default
- ranks files by relevance and risk
- emits a compact context packet under a token budget
- reports before/after token reduction

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
  - `agentops route --task release --privacy local-first`

Acceptance:

- recommends local models for cheap/private work
- recommends stronger models only when needed
- explains the routing decision
- never requires provider secrets in config files

## Phase 4: API Adapter Layer

Goal: connect to model providers without coupling AgentOps to one vendor.

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

Goal: make AgentOps usable from coding environments without becoming editor-specific.

Build:

- VS Code task templates
- Cursor rules
- MCP server contract
- optional MCP server implementation
- Antigravity notes once its stable extension points are confirmed

Acceptance:

- editor integrations call the same CLI
- AgentOps remains usable from terminal
- no editor config becomes required for the package
- no integration bypasses prompt scanning or capability checks

## Phase 6: Standalone Release

Goal: extract AgentOps cleanly from Continuity Legacy.

Build:

- own repository
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
