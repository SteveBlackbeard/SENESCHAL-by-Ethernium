# ROBIN HOOD Optimization Model

ROBIN HOOD minimizes spend by treating model power as an escalation resource, not the default path.

## Core Loop

```text
classify -> scan risk -> estimate tokens -> pack context -> route -> execute elsewhere -> log outcome
```

ROBIN HOOD does not need to invoke models to save money. The first savings come from avoiding bad context, bad routing, bad retries, and unsafe scope.

## Disciplinary Model

Systems engineering:

- define inputs, outputs, constraints and gates before execution
- prefer deterministic local controls before probabilistic model calls
- keep CLI, MCP and editor integrations on the same core modules

Neural systems:

- use a reflex ladder: cheap local response first, stronger response only when signal intensity rises
- reduce cognitive load by sending compact, relevant context instead of raw memory dumps
- preserve attention for high-uncertainty decisions

Symbolic programming:

- encode task classes, privacy modes and escalation levels as explicit symbols
- make decisions inspectable as JSON
- avoid hidden policy magic

Biology and immune systems:

- scan untrusted input before ingestion
- isolate suspicious material
- escalate only when a threat crosses a threshold

Cybersecurity:

- block prompt-injection markers
- flag secret-like material
- apply least-privilege capability checks
- keep provider secrets out of config files

Reverse engineering:

- study public behavior and cost patterns
- rebuild control primitives cleanly
- do not copy leaked prompts or hidden instructions

Low-code and automation:

- keep commands small enough for VS Code tasks, Cursor rules, CI, MCP and shell scripts
- use JSON output so other tools can compose around ROBIN HOOD

Advanced programming:

- keep core modules dependency-free
- add provider/tokenizer adapters later as optional plugins
- make every expensive feature prove measurable value first

## Spend-Minimum Policy

1. Do not send whole repositories when a context pack fits.
2. Do not use cloud models when local profiles satisfy the task and privacy requirements.
3. Do not use long-context models for small edits.
4. Do not retry blindly; log retries and inspect failure class.
5. Do not invoke a provider until prompt-risk and budget controls pass.
6. Do not add a database before JSONL becomes limiting.
7. Do not add dashboards before CLI/MCP value is proven.

## Quality Preservation

Frugal does not mean weak.

ROBIN HOOD escalates when:

- the task is security-sensitive
- the task is release-critical
- the context does not fit local profiles
- the objective requires long-context synthesis
- the user explicitly allows stronger/cloud escalation

The ideal result is not the cheapest possible answer. The ideal result is the cheapest path that still preserves correctness, safety and reviewability.
