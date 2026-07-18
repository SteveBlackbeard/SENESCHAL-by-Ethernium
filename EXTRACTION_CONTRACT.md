# Seneschal Extraction Contract

Seneschal is temporarily incubated inside Continuity Legacy, but it must remain removable.

## Removal Guarantee

This directory can be deleted:

```text
ROBIN-HOOD/
```

Deletion must not break:

- Continuity Legacy imports
- tests
- packaging
- PyPI release flow
- golden baseline verification
- Conekta extraction

## Dependency Rule

Continuity Legacy may mention Seneschal in documentation, but runtime code must not import it.

Seneschal may reference Continuity as inspiration, but must not depend on Continuity internals unless a future standalone adapter is explicitly designed.

## Future Repository Shape

Target standalone layout:

```text
Seneschal/
  __init__.py
  health_guard.py
  context_packet.py
  prompt_firewall.py
  frugality_ledger.py
  capability_broker.py
adversarial_cases/
templates/
tests/
README.md
RULEBOOK.md
FRUGALITY.md
THREAT_MODEL.md
pyproject.toml
```

## Standalone Guarantee

Seneschal must be useful without Continuity Legacy.

Standalone usage must support:

- local health checks
- context packet rendering
- prompt-risk classification
- capability checks
- JSONL frugality logs
- tests

No standalone command may require:

- `.continuity/`
- Continuity golden baseline
- Continuity PyPI package
- Continuity release workflows
- Conekta dashboard files

## Release Rule

Seneschal should not be released until it has:

- executable code
- tests
- a health gate
- a clean-room policy
- a clear CLI or library API
- no dependency on Continuity Legacy files

## Naming

Recommended package name:

```text
ethernium-Seneschal
```
