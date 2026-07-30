# Seneschal Mitigation Matrix

This matrix turns known GenAI/agent risks into local, frugal controls.

## Risk To Control Map

| Risk | Seneschal Control | Continuity Control | Status |
| --- | --- | --- | --- |
| Prompt injection | `prompt_firewall.py`, adversarial cases | health guard after edits | prototype |
| Indirect prompt injection | source labels, trust zones, context packet | handoff provenance | documented |
| Sensitive information disclosure | secret markers, recursive scan, capability broker | release gates | prototype |
| Supply chain/tool abuse | capability broker, no network by default | package checks | prototype |
| Data/memory poisoning | provenance labels, immune memory roadmap | golden baseline, live handoff | partial |
| Improper output handling | verification field in packet | pytest/build/twine gates | prototype |
| Excessive agency | least privilege capability grants | governed paths | prototype |
| System prompt leakage | clean-room policy, no prompt vault | no leaked prompts in repo | documented |
| Vector/RAG weakness | external content marked untrusted | canonical docs | planned |
| Misinformation | local verification, source labels | release docs | partial |
| Unbounded consumption | frugality ledger, stop conditions | autophagy report | prototype |

## Design Lessons From Existing Tools

### OWASP GenAI Top 10

Seneschal should map every feature to a concrete risk class. The most important classes for local agent work are prompt injection, sensitive data leakage, supply chain, excessive agency, system prompt leakage, and unbounded consumption.

### garak

Useful pattern: probes, targets, detectors, reports.

Seneschal adaptation:

- probes become benign adversarial cases
- target is the local agent workflow
- detectors are explicit, inspectable rules
- reports stay JSON/Markdown first

### promptfoo

Useful pattern: declarative tests, local/private evaluation, CI integration, model comparison.

Seneschal adaptation:

- keep provider-neutral scorecards
- compare cost and failure rate, not personality
- use simple config before dashboard

### PyRIT

Useful pattern: security professionals need repeatable risk identification, not ad hoc prompt games.

Seneschal adaptation:

- keep clean-room tests
- store results as JSONL
- separate test generation from operational decisions

### NeMo Guardrails

Useful pattern: programmable runtime rails independent of the base model.

Seneschal adaptation:

- use explicit capability checks
- avoid trusting system prompts as the only control

### AgentDojo / AgentWatcher

Useful pattern: agent security depends on tool-use context and attribution, not just input strings.

Seneschal adaptation:

- future version should attribute risky actions to context segments
- long context must be reduced before classification

## Frugal Principle

Do not implement a full red-team suite yet.

Implement the smallest useful loop:

```text
packet -> scan path/text/file -> grant capabilities -> execute -> verify -> log -> learn
```

If that loop reduces retries, unsafe scope, or token volume, then build the next layer.
