# Using Seneschal in Cursor (and Claude Desktop)

Seneschal integrates with agent hosts through **MCP**, not through an editor
extension. In Cursor this is the supported way to give an agent real tools: the
model calls them directly, which is more useful than a button a human has to
remember to press.

Verified: a clean `pip install "seneschal[mcp]"` starts the server and completes
the MCP `initialize` handshake, exposing 19 tools.

## Install

```bash
pip install "seneschal[mcp]"
```

## Configure Cursor

Add this to your MCP configuration (`~/.cursor/mcp.json`, or Cursor Settings →
MCP → Add new server):

```json
{
  "mcpServers": {
    "seneschal": {
      "command": "seneschal-mcp"
    }
  }
}
```

If the executable is not on PATH, use the interpreter form:

```json
{
  "mcpServers": {
    "seneschal": {
      "command": "python",
      "args": ["-m", "seneschal.mcp_server"]
    }
  }
}
```

Restart Cursor. The tools appear under the `seneschal` server.

## Claude Desktop

Same shape, in `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "seneschal": {
      "command": "seneschal-mcp"
    }
  }
}
```

## What the agent gets

| Tool | Purpose |
| :--- | :--- |
| `scan_text` | Flag prompt-injection patterns and secret-like material before use |
| `budget` / `pack` | Estimate token budgets and pack repo context under a limit |
| `select` | Pick the most relevant files by BM25 relevance to the task |
| `route` / `plan_request` | Recommend the cheapest sufficient model path |
| `check_capability` | Enforce least-privilege capability grants |
| `reuse` / `savings` | Context snapshots and prompt-cache layout planning |
| `make_packet` | Build a scoped task packet for an agent |

## Cursor rules

`integrations/cursor/rules/seneschal.mdc` tells the agent *when* to reach for
these tools. Copy it into your project's `.cursor/rules/` directory. This matters
more than the tools existing: an agent that never calls them is the same as no
integration at all.

## Boundary

Seneschal decides **whether** to call a model and **what** context to send. It
does not sandbox what an agent does with a capability once granted. See
SECURITY.md.
