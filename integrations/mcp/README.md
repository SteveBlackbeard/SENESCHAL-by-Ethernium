# ROBIN HOOD MCP Integration

This folder defines the future MCP surface for ROBIN HOOD.

The current codebase includes an optional local MCP server:

```powershell
cd D:\Experimentos\ROBIN-HOOD
pip install -e .[mcp]
robinhood-mcp
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
| `robinhood.health` | Run local health checks | Low |
| `robinhood.scan_text` | Classify untrusted text | Low |
| `robinhood.scan_path` | Scan files or directories | Medium |
| `robinhood.make_packet` | Build a context packet | Low |
| `robinhood.check_capability` | Validate requested capability and path | Low |
| `robinhood.estimate_budget` | Estimate token budget | Low, planned |
| `robinhood.pack_context` | Build compact context under budget | Medium, planned |
| `robinhood.route_model` | Recommend model/provider path | Medium, planned |

## Constraints

- No provider secrets in MCP config.
- No network calls in the first MCP version.
- No direct model invocation until scanning and budgeting are stable.
- All MCP tools should call the same Python modules used by the CLI.
