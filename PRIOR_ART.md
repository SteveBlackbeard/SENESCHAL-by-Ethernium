# Prior Art And Clean-Room Inspiration

ROBIN HOOD is not trying to clone existing tools. It borrows proven shapes and rebuilds a small local-first workflow for coding agents.

## Similar Projects

| Project | What It Does | What ROBIN HOOD Should Learn | What ROBIN HOOD Should Avoid |
| --- | --- | --- | --- |
| OWASP GenAI Top 10 | Risk taxonomy for LLM apps | map controls to named risks | becoming compliance theater |
| garak | LLM vulnerability scanner | probes + detectors + reports | broad offensive probe library in v1 |
| promptfoo | prompt/model/agent evals and red teaming | declarative tests, CI, local privacy | dashboard before metrics |
| PyRIT | repeatable GenAI risk identification | structured red-team workflows | dependency-heavy architecture early |
| NeMo Guardrails | programmable rails | model-independent controls | assuming rails solve all injection |
| AgentDojo | evaluates tool-use agents under prompt injection | task + tool + adversarial environment | large benchmark before local use |
| AgentWatcher | rule-based prompt-injection monitor with attribution | explainable rules and segment attribution | opaque “AI judge says no” decisions |

## ROBIN HOOD Differentiator

ROBIN HOOD should be narrower and more practical:

- local-first
- repo-aware
- frugal by default
- no provider lock-in
- no leaked prompt dependency
- designed to work beside Continuity Legacy
- focused on coding-agent operations, not generic chatbot safety

## Reverse Engineering Method

Use clean-room reverse engineering:

1. Observe public behavior and public incident patterns.
2. Extract control principles.
3. Name the invariant.
4. Rebuild as a small local primitive.
5. Measure whether it reduces cost, risk, or drift.

## Synergic Disciplines

Biotechnology:

- immune memory
- quarantine
- mutation testing
- phenotype/genotype separation

Neurotechnology:

- attention attribution
- cognitive load reduction
- signal/noise control

Symbolic programming:

- explicit contracts
- rule engines
- capability algebra

Systems programming:

- least privilege
- sandbox boundaries
- deterministic logs

Mathematics:

- entropy of context
- retry rate
- risk scoring
- cost functions

Security:

- threat modeling
- red-team/blue-team separation
- provenance
- secrets hygiene

ROBIN HOOD should combine these into small checks, not grand abstractions.
