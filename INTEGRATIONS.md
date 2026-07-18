# Seneschal Integrations

Seneschal integrations must be thin wrappers around the CLI and future MCP server.

The rule is simple: editors consume Seneschal; Seneschal does not become dependent on editors.

## Integration Architecture

```text
VS Code / Cursor / Antigravity / other agents
  -> Seneschal CLI or MCP server
  -> prompt firewall, token budget, capability broker, context packer
  -> optional model/provider adapter
```

This keeps the same controls available from terminal, IDE tasks, local agents, and CI.

## VS Code

Use VS Code tasks for the first integration layer.

Recommended commands:

- `seneschal health --strict`
- `seneschal scan --path . --source repo --fail-on-block`
- `seneschal plan-request --config seneschal.config.json --objective "Review change" --estimated-input-tokens 8000`
- `seneschal run --config seneschal.config.json --objective "Review change" --path .`
- `seneschal packet`
- `seneschal pack --path . --max-tokens 32000`
- `seneschal route --objective "Review change"`

The template lives in:

```text
integrations/vscode/tasks.json
```

Copy it into a standalone repo as `.vscode/tasks.json` when Seneschal is extracted.

## Cursor

Use Cursor rules for the first integration layer.

The rule should tell the agent to:

- use Seneschal before ingesting external content
- create small context packets instead of pasting whole repos
- request only the capabilities needed
- prefer local/cheap models when the task permits it
- keep Continuity Legacy separate from Seneschal runtime

The template lives in:

```text
integrations/cursor/rules/seneschal.mdc
```

## MCP

MCP is the preferred long-term integration because it gives editors and agents a stable tool surface.

Initial MCP tools should expose only local, low-risk operations:

- `seneschal.health`
- `seneschal.scan_text`
- `seneschal.scan_path`
- `seneschal.make_packet`
- `seneschal.check_capability`
- `seneschal.budget`
- `seneschal.pack`
- `seneschal.route`
- `seneschal.plan_request`
- `seneschal.run`

The contract lives in:

```text
integrations/mcp/server_contract.json
```

Provider calls must stay behind planning, provider health, circuit-breaker state, and quality gates.

## Antigravity

Do not add Antigravity-specific code until its stable extension points are confirmed.

For now, compatibility means:

- usable through CLI
- usable through MCP if Antigravity supports MCP or external local tools
- no assumption about hidden editor behavior

## Integration Acceptance

An integration is accepted only when:

- it runs through Seneschal CLI or MCP
- it keeps Seneschal standalone
- it avoids provider-specific hidden prompts
- it can be removed without breaking Continuity Legacy
- it reduces cost, risk, drift, or manual handoff time
