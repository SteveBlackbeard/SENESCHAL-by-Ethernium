# AgentOps MCP Integration

This folder defines the future MCP surface for AgentOps.

The current codebase includes an optional local MCP server:

```powershell
cd AGENTOPS_TOOL
pip install -e .[mcp]
agentops-mcp
```

MCP should expose local controls first:

- health checks
- prompt and path scanning
- context packet generation
- capability checks
- token budgeting
- context packing
- routing recommendations

Provider calls should stay deferred until the defensive controls are stable.

## Proposed Tools

| Tool | Purpose | Risk |
| --- | --- | --- |
| `agentops.health` | Run local health checks | Low |
| `agentops.scan_text` | Classify untrusted text | Low |
| `agentops.scan_path` | Scan files or directories | Medium |
| `agentops.make_packet` | Build a context packet | Low |
| `agentops.check_capability` | Validate requested capability and path | Low |
| `agentops.estimate_budget` | Estimate token budget | Low, planned |
| `agentops.pack_context` | Build compact context under budget | Medium, planned |
| `agentops.route_model` | Recommend model/provider path | Medium, planned |

## Constraints

- No provider secrets in MCP config.
- No network calls in the first MCP version.
- No direct model invocation until scanning and budgeting are stable.
- All MCP tools should call the same Python modules used by the CLI.
