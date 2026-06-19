# ROBIN HOOD

ROBIN HOOD is intentionally separate from Continuity Legacy.

It started as the AgentOps incubation layer and is now its own tool/repository.

ROBIN HOOD can be used in two modes:

- **Standalone**: as an independent local-first tool for any AI-assisted project.
- **With Continuity Legacy**: as an optional operations layer beside Continuity governance.

## What This Tool Is

ROBIN HOOD is a provider-neutral operating layer for reducing AI agent cost, context waste, retries, and coordination drift.

It focuses on:

- model routing
- local/cloud task splitting
- task packet templates
- context compaction
- credit usage tracking
- batch workflows
- clean-room reverse engineering of agent control patterns

## What This Tool Is Not

It is not:

- part of the Continuity Legacy runtime
- part of the PyPI package
- part of Continuity governance
- a copy of leaked prompts
- a provider bypass tool
- a storage place for proprietary hidden instructions

## Extraction Rule

This folder should be removable without breaking Continuity:

```text
AGENTOPS_TOOL/
```

## Clean-Room Rule

Reverse engineer the economics and control system, not proprietary text.

Allowed:

- study public behavior
- identify reusable control patterns
- rebuild them as local, provider-neutral primitives
- measure cost, retries, and context size

Not allowed:

- copying leaked prompts
- using hidden vendor policies as source material
- impersonating another provider's model behavior
- adding jailbreak collections

## Current Status

```text
status: prototype
relationship_to_continuity: none
safe_to_extract: true
```

## Governance

The local governance seed is in `GOVERNANCE.md`.

AgentOps should adopt Continuity-style discipline only where it adds leverage:

- clear boundary
- explicit health gate
- clean-room policy
- extraction contract
- measurable value

It should not inherit the full Continuity Legacy baseline system until it becomes a real standalone tool with executable code.

## Frugal Build Path

AgentOps should grow only through modules that reduce one of three things:

- cost
- risk
- drift

The first standalone version should be small:

- `RULEBOOK.md`: operating rules and clean-room limits
- `FRUGALITY.md`: token, retry, model, and context economy
- `THREAT_MODEL.md`: defensive model for prompt injection, tool hijack, memory poisoning, and secret leakage
- `EXTRACTION_CONTRACT.md`: guarantee that this folder can become its own repository
- `ROADMAP.md`: phased path from incubation to product
- `PENDING.md`: unfinished work before standalone release
- `INTEGRATIONS.md`: VS Code, Cursor, MCP, and future editor integration boundary

Executable code now starts with the local-first prototype:

```text
agentops/health_guard.py
agentops/context_packet.py
agentops/prompt_firewall.py
agentops/frugality_ledger.py
tests/
```

## Design Principle

AgentOps is a small immune system for AI-agent work: observe, classify, constrain, measure, and improve.

It should not become a lore archive or a leaked-prompt archive.

## Standalone Use

AgentOps does not require Continuity Legacy.

Minimal standalone loop:

```powershell
$env:PYTHONPATH="."
python agentops\health_guard.py --strict
pytest tests -q
```

Operational loop:

1. Create a context packet.
2. Classify external content with the prompt firewall.
3. Grant only the capabilities needed for the task.
4. Execute locally.
5. Log cost, retries, and outcome in the frugality ledger.
6. Review whether the task reduced cost, risk, or drift.

## CLI Prototype

Current commands:

```text
agentops health
agentops packet
agentops scan
agentops grant
agentops log
agentops report
```

Install locally:

```powershell
cd AGENTOPS_TOOL
pip install -e .
agentops health --strict
agentops scan --path adversarial_cases --source web --fail-on-block
```

## Integration Scaffolds

AgentOps now includes thin integration templates:

```text
integrations/vscode/tasks.json
integrations/cursor/rules/agentops.mdc
integrations/mcp/server_contract.json
```

These are contracts and starter templates, not editor dependencies.

Optional MCP server:

```powershell
cd AGENTOPS_TOOL
pip install -e .[mcp]
agentops-mcp
```

The MCP server exposes local controls only: health, scan text, scan path, context packet generation, and capability checks.
