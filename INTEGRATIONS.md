# ROBIN HOOD Integrations

ROBIN HOOD integrations must be thin wrappers around the CLI and future MCP server.

The rule is simple: editors consume ROBIN HOOD; ROBIN HOOD does not become dependent on editors.

## Integration Architecture

```text
VS Code / Cursor / Antigravity / other agents
  -> ROBIN HOOD CLI or MCP server
  -> prompt firewall, token budget, capability broker, context packer
  -> optional model/provider adapter
```

This keeps the same controls available from terminal, IDE tasks, local agents, and CI.

## VS Code

Use VS Code tasks for the first integration layer.

Recommended commands:

- `robinhood health --strict`
- `robinhood scan --path . --source repo --fail-on-block`
- `robinhood packet`
- future: `ROBIN HOOD pack --path . --max-tokens 32000`
- future: `ROBIN HOOD route --task code-review`

The template lives in:

```text
integrations/vscode/tasks.json
```

Copy it into a standalone repo as `.vscode/tasks.json` when ROBIN HOOD is extracted.

## Cursor

Use Cursor rules for the first integration layer.

The rule should tell the agent to:

- use ROBIN HOOD before ingesting external content
- create small context packets instead of pasting whole repos
- request only the capabilities needed
- prefer local/cheap models when the task permits it
- keep Continuity Legacy separate from ROBIN HOOD runtime

The template lives in:

```text
integrations/cursor/rules/agentops.mdc
```

## MCP

MCP is the preferred long-term integration because it gives editors and agents a stable tool surface.

Initial MCP tools should expose only local, low-risk operations:

- `robinhood.health`
- `robinhood.scan_text`
- `robinhood.scan_path`
- `robinhood.make_packet`
- `robinhood.check_capability`
- future: `robinhood.estimate_budget`
- future: `robinhood.pack_context`
- future: `robinhood.route_model`

The contract lives in:

```text
integrations/mcp/server_contract.json
```

Do not expose provider calls before prompt scanning, capability checks, and token budgets are stable.

## Antigravity

Do not add Antigravity-specific code until its stable extension points are confirmed.

For now, compatibility means:

- usable through CLI
- usable through MCP if Antigravity supports MCP or external local tools
- no assumption about hidden editor behavior

## Integration Acceptance

An integration is accepted only when:

- it runs through ROBIN HOOD CLI or MCP
- it keeps ROBIN HOOD standalone
- it avoids provider-specific hidden prompts
- it can be removed without breaking Continuity Legacy
- it reduces cost, risk, drift, or manual handoff time
