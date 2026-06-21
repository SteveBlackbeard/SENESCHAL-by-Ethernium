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
robinhood snapshot --path . --input-cost-per-million 2 --runs 100
robinhood reuse --system "stable operating rules" --user "task-specific request"
robinhood savings --full-tokens 28611 --optimized-tokens 6166 --input-cost-per-million 2 --runs 100
robinhood select --path . --changed agentops/cli.py --max-tokens 4000
robinhood broker-dry-run --objective "release review" --estimated-input-tokens 12000 --privacy local-first
robinhood broker-dry-run --providers providers.local.json --objective "release review" --estimated-input-tokens 12000
```

## Relevance Selection

Changed-only context is cheap, but it may be too thin.

`robinhood select` adds mathematical triage:

- changed files get first priority
- files in the same directory get extra weight
- same-stem files get extra weight
- simple Python import neighbors get extra weight
- selection is sorted by value-per-token density
- low-relevance files are filtered by a minimum score
- files over budget are excluded instead of silently bloating the prompt

This approximates a small knapsack optimizer: maximize useful context while staying under the token budget.

## Capacity Broker

The first broker layer is dry-run only.

It scores available provider profiles by:

- task class
- context window fit
- privacy mode
- estimated cost
- blocked/allowed providers
- quality overlap with the task

It does not call APIs, store secrets, or chase free tokens blindly. It recommends the cheapest sufficient capacity route before any expensive model invocation happens.

Provider catalogs:

- `providers.local.json.example` is safe to commit.
- `providers.local.json` is ignored by Git.
- real API keys must be referenced by environment variable names only.
- disabled providers stay visible for planning but cannot be selected.

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
