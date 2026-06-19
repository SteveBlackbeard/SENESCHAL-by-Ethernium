# AgentOps Integrations

AgentOps integrations must be thin wrappers around the CLI and future MCP server.

The rule is simple: editors consume AgentOps; AgentOps does not become dependent on editors.

## Integration Architecture

```text
VS Code / Cursor / Antigravity / other agents
  -> AgentOps CLI or MCP server
  -> prompt firewall, token budget, capability broker, context packer
  -> optional model/provider adapter
```

This keeps the same controls available from terminal, IDE tasks, local agents, and CI.

## VS Code

Use VS Code tasks for the first integration layer.

Recommended commands:

- `agentops health --strict`
- `agentops scan --path . --source repo --fail-on-block`
- `agentops packet`
- future: `agentops pack --path . --max-tokens 32000`
- future: `agentops route --task code-review`

The template lives in:

```text
integrations/vscode/tasks.json
```

Copy it into a standalone repo as `.vscode/tasks.json` when AgentOps is extracted.

## Cursor

Use Cursor rules for the first integration layer.

The rule should tell the agent to:

- use AgentOps before ingesting external content
- create small context packets instead of pasting whole repos
- request only the capabilities needed
- prefer local/cheap models when the task permits it
- keep Continuity Legacy separate from AgentOps runtime

The template lives in:

```text
integrations/cursor/rules/agentops.mdc
```

## MCP

MCP is the preferred long-term integration because it gives editors and agents a stable tool surface.

Initial MCP tools should expose only local, low-risk operations:

- `agentops.health`
- `agentops.scan_text`
- `agentops.scan_path`
- `agentops.make_packet`
- `agentops.check_capability`
- future: `agentops.estimate_budget`
- future: `agentops.pack_context`
- future: `agentops.route_model`

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

- it runs through AgentOps CLI or MCP
- it keeps AgentOps standalone
- it avoids provider-specific hidden prompts
- it can be removed without breaking Continuity Legacy
- it reduces cost, risk, drift, or manual handoff time
