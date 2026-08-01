# Seneschal Production Readiness

Seneschal 0.2.3 has production-shaped engineering gates while its package
classifier remains Alpha. The distinction is deliberate: the local planning,
security and context primitives are tested and packageable; wider real-provider
operations still require deployment-specific validation and external users.

## Verified product core

```text
seneschal health --strict
python -m pytest -q
python -m build
python -m twine check dist/*
```

The current suite covers context selection and packing, token budgets, prompt
firewall behavior, capability grants, Ed25519 signing, provider readiness and
circuit-breaker state, request planning, quality gates, MCP contracts and local
or OpenAI-compatible adapter orchestration. CI runs on Windows and Linux across
Python 3.10–3.13.

## Portability contract

- Core runtime dependencies remain zero; measurement, signing and MCP are
  explicit optional extras.
- Repository examples use relative paths or a fresh checkout, not a drive
  letter or user profile.
- Mutable provider configuration and state remain local and Git-ignored.
- Model credentials are supplied by environment variables named by provider
  profiles; no credential value belongs in source control.

## Product boundary

Seneschal is the consultative selection, budget, prompt-risk and provider-plan
layer. It does not own project truth, mutate another product without a scoped
grant, become Frugal's kernel, or provide CONEKTA's visual surface. Frugal may
consume its deterministic preflight contract through an adapter.

## Deployment obligations

- Exercise each enabled provider against its real endpoint and quota policy.
- Pin the optional dependency set used by the deployment.
- Keep human review for security, legal, medical, financial and public-release
  decisions.
- Treat reported savings as measured estimates for the named corpus/model, not
  universal guarantees.

No visual assets are part of this hardening wave.
