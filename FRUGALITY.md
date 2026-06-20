# ROBIN HOOD Frugality Doctrine

Frugality is not cheapness. It is disciplined allocation of model power, context, time, and human attention.

## Core Question

Every ROBIN HOOD feature must answer:

```text
Does this reduce cost, risk, or drift?
```

If the answer is unclear, do not build it yet.

## Cost Surfaces

Track:

- prompt tokens
- completion tokens
- files included
- retries
- model used
- wall time
- human review time
- failed tool calls
- rollback cost

## Default Storage

Use JSONL first:

```json
{"task_id":"AOP-001","model":"local","tokens_estimated":1200,"retries":0,"outcome":"pass"}
```

Do not add a database until JSONL becomes painful.

## Routing Policy

Use local or cheaper tools for:

- file discovery
- diff inspection
- lint interpretation
- documentation drafts
- checklist generation
- duplicate detection
- static validation

Use stronger/cloud tools for:

- security-sensitive review
- release readiness
- complex architecture decisions
- ambiguous bug triage
- high-risk edits

## Context Diet

Before sending context to a model, remove:

- generated files
- virtual environments
- build outputs
- logs without errors
- old release artifacts
- repeated docs
- unrelated translations

Preferred packet:

```text
Objective:
Why now:
Allowed files:
Known constraints:
Relevant diff:
Verification:
Rollback:
Expected output:
```

## Stop Conditions

Stop or compact when:

- the task has more than two failed attempts
- context exceeds the useful scope
- the model requests unrelated files
- tool calls start repeating
- output quality drops while token use rises

## Metrics

Minimum metrics for prototype:

- average retries per task
- estimated tokens per completed task
- percent of tasks solved locally
- number of blocked unsafe inputs
- number of avoided whole-repo context loads

## Executable Controls

ROBIN HOOD now includes a small token core:

```powershell
robinhood models
robinhood budget --file README.md --model local-small
robinhood pack --path . --model local-long --max-tokens 12000
robinhood route --objective "Security review before release" --privacy cloud-allowed
robinhood snapshot --path .
robinhood reuse --system "stable operating rules" --user "task-specific request"
robinhood savings --full-tokens 28611 --optimized-tokens 6166 --input-cost-per-million 2 --runs 100
```

The first implementation uses a conservative fallback estimate instead of pretending to know every provider tokenizer. Provider-specific tokenizers can be added later as optional adapters.

## Escalation Ladder

The router follows a cheap-first ladder:

1. Local small model for simple edits, summaries and low-risk drafting.
2. Local long-context model for repository analysis and larger context.
3. Cloud-compatible balanced model only when risk, release quality or tool reasoning justifies it.
4. Long-context cloud profile only when context size or synthesis demands it and escalation is explicitly allowed.

This mirrors a defensive biological pattern: cheap reflex first, stronger immune response only when the signal crosses a threshold.

## Context Memory

Most teams waste tokens by resending unchanged files.

`robinhood snapshot` creates a local hash/token cache under `.robinhood/`. The next run reports added, changed, deleted and unchanged files, plus an estimated changed-only token cost.

This is useful for:

- Cursor sessions
- VS Code tasks
- terminal workflows
- API clients that want to send only changed context
- CI checks that need a compact task packet
