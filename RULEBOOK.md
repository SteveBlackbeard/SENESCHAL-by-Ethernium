# ROBIN HOOD Rulebook

ROBIN HOOD is a provider-neutral operations layer for AI agents. It exists to reduce cost, risk, and drift in assisted software work.

## Prime Rules

1. Keep ROBIN HOOD extractable.
2. Do not import ROBIN HOOD from Continuity Legacy runtime.
3. Do not package ROBIN HOOD into Continuity Legacy PyPI artifacts.
4. Do not store leaked prompts, hidden vendor instructions, or jailbreak collections.
5. Reverse engineer observable control patterns, not proprietary text.
6. Prefer local checks before paid model calls.
7. Prefer small context packets over whole-repo context.
8. Every module must reduce cost, risk, or drift.

## Clean-Room Reverse Engineering

Allowed:

- observe public behavior
- study public incident reports and papers
- compare provider outputs on your own benign tasks
- extract abstract control patterns
- rebuild provider-neutral primitives
- measure failures, retries, costs, and context sizes

Not allowed:

- copying leaked prompts
- storing proprietary hidden instructions
- building bypass or evasion packs
- impersonating vendor model behavior
- collecting exploit payloads for offensive use

## Operating Model

ROBIN HOOD should behave like an immune layer:

- classify inputs
- isolate untrusted context
- constrain capabilities
- measure resource use
- preserve audit logs
- escalate only when value justifies cost

## Minimum Useful Tool

The smallest real ROBIN HOOD implementation is:

- a context packet schema
- a prompt-risk classifier
- a capability checklist
- a JSONL frugality ledger
- a health guard
- a small adversarial test corpus

Anything beyond that must prove value through metrics.
