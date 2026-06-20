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
```

The first implementation uses a conservative fallback estimate instead of pretending to know every provider tokenizer. Provider-specific tokenizers can be added later as optional adapters.
