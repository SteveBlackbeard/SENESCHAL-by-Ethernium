# Seneschal MCP Integration

This folder defines the MCP surface for Seneschal local controls.

The current codebase includes an optional local MCP server:

```powershell
cd D:\Experimentos\ROBIN-HOOD
pip install -e .[mcp]
seneschal-mcp
```

MCP should expose local controls first:

- health checks
- prompt and path scanning
- context packet generation
- capability checks
- model profile listing
- token budgeting
- context packing
- routing recommendations
- context snapshots
- prompt reuse estimates
- relevance selection
- capacity broker dry-runs

Provider calls should stay deferred until the defensive controls are stable.

## Proposed Tools

| Tool | Purpose | Risk |
| --- | --- | --- |
| `seneschal.health` | Run local health checks | Low |
| `seneschal.scan_text` | Classify untrusted text | Low |
| `seneschal.scan_path` | Scan files or directories | Medium |
| `seneschal.make_packet` | Build a context packet | Low |
| `seneschal.check_capability` | Validate requested capability and path | Low |
| `seneschal.models` | List model profiles | Low |
| `seneschal.budget` | Estimate token budget | Low |
| `seneschal.pack` | Build compact context under budget | Medium |
| `seneschal.route` | Recommend model/provider path | Medium |
| `seneschal.snapshot` | Snapshot context and estimate changed-only savings | Low |
| `seneschal.reuse` | Estimate reusable/cacheable prompt share | Low |
| `seneschal.savings` | Estimate token/cost savings | Low |
| `seneschal.select` | Select useful neighboring context under budget | Medium |
| `seneschal.broker_dry_run` | Dry-run provider capacity routing | Medium |

## Constraints

- No provider secrets in MCP config.
- No network calls in the first MCP version.
- No direct model invocation until provider adapters are explicitly enabled.
- All MCP tools should call the same Python modules used by the CLI.
