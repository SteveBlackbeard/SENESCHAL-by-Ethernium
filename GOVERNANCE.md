# Seneschal Governance Seed

Seneschal is an incubated tool, not part of Continuity Legacy.

## Golden Rules

- Keep Seneschal extractable as a standalone repository.
- Do not import Seneschal from Continuity Legacy runtime code.
- Do not package Seneschal into Continuity Legacy PyPI artifacts.
- Use clean-room engineering only: patterns, economics, routing, and measurement are allowed; leaked prompts or proprietary hidden instructions are not.
- Prefer measurable credit/context reduction over narrative expansion.

## Health Gate

Seneschal is considered healthy when:

- `TOOL_MANIFEST.json` is valid JSON.
- `README.md` states the boundary from Continuity Legacy.
- `BLUEPRINT.md` describes the workflow without provider-specific hidden text.
- `RULEBOOK.md`, `FRUGALITY.md`, `THREAT_MODEL.md`, `EXTRACTION_CONTRACT.md`, and `ROADMAP.md` exist before executable code is added.
- `pyproject.toml` exposes the local `Seneschal` CLI when the prototype has executable code.
- No leaked prompt text, jailbreak collections, or vendor-imitation instructions are stored in this folder.
- Every new module states whether it reduces cost, risk, or drift.

## Extraction Contract

This directory must remain removable:

```text
ROBIN-HOOD/
```

Removing it must not break:

- Python package imports
- tests
- build
- golden baseline verification
- CONEKTA

## Maturity Levels

- `incubation`: docs and manifest only.
- `prototype`: local scripts exist and have tests.
- `tool`: installable package or executable exists.
- `product`: separate repo, CI, release notes, and user docs exist.

Current level:

```text
prototype
```

## Frugality Gate

Do not add a feature unless it has at least one measurable outcome:

- fewer tokens
- fewer retries
- fewer unsafe tool calls
- smaller context packets
- faster local verification
- clearer rollback

If the value cannot be measured, keep it as a note in `ROADMAP.md` instead of building it.
