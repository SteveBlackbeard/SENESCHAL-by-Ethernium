# Changelog

All notable changes to Seneschal are documented here. This project follows
[Semantic Versioning](https://semver.org/).

## [0.2.0] - 2026-07-16

### Added — frugal engine
- **`cascade`**: FrugalGPT-style executor. Calls the cheapest sufficient model,
  applies the quality gate, and escalates only on failure — every hop is recorded
  in the frugality ledger as evidence. Unconfigured profiles are skipped without
  polluting the ledger.
- **`route --explore`**: Thompson-sampling bandit over Beta posteriors built from
  ledger outcomes — exploits reliable models and keeps exploring under-observed
  ones. Reproducible with `--seed` (`seneschal/bandit.py`, pure stdlib).
- **`select --objective`**: Okapi BM25 lexical relevance to the task objective,
  blended with the structural heuristics (`seneschal/bm25.py`, zero dependencies).
- **`reuse --layout`**: provider prompt-caching layout planner — orders the stable
  prefix first, reports the cacheable ratio and the savings a naive layout wastes.

### Added — security
- **Ed25519-signed capability grants** (`seneschal/signing.py`, `keygen`,
  `grant --sign` / `--grant-file` / `--require-signed`). The broker fails closed
  on unsigned grants (when required), untrusted keys, any modification after
  signing (capability escalation), and expiry. The public key and `sig_alg` are
  bound into the signed payload. `cryptography` ships as the optional `security`
  extra; the zero-dependency core is intact.

### Fixed
- Ledger failure semantics: any outcome not in `{pass, ok}` now counts as a
  failure for routing (the runner/cascade record error strings as outcomes).

### CI
- Matrix expanded to Ubuntu + Windows × Python 3.10–3.13.
- Installs the `measure` and `security` extras so the measured tokenizer and
  signing paths are exercised; tokenizer/crypto tests `importorskip` cleanly
  without the extras.

## [0.1.0]

- Initial local-first control layer: health guard, context packet, frugality
  ledger, prompt firewall, capability broker, provider/model profiles,
  tokenizer-free budget estimator, context packer, frugal router, local Ollama
  and OpenAI-compatible adapters, quality gate, and optional MCP server.
