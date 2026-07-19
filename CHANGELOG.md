# Changelog

All notable changes to Seneschal are documented here. This project follows
[Semantic Versioning](https://semver.org/).

## [0.2.1] - 2026-07-18

### Fixed
- **CI had been red since the rename, and the broken thing was the check
  itself.** The health step ran `python seneschal/health_guard.py`, which
  executes with no parent package, so the guard's relative import of
  `provider_profiles` raised and it declared a perfectly healthy tree broken.
  CI now invokes the console script — what a user actually runs — and the guard
  also stands on its own, because running a file directly is an obvious thing
  to try and should not produce a false alarm. A test now executes that entry
  point in a subprocess. Nothing covered it before, which is how a guard whose
  entire job is detecting breakage sat broken for months, announcing that
  something was wrong with itself.

### Added
- `scripts/publish.ps1`: builds, validates, uploads, and deletes `.pypirc` in a
  `finally` block, so a token never survives a failed run. Release steps written
  as prose get pasted into a shell whole, explanatory sentences and all; a file
  you run has no such failure mode.

### Note
- 0.2.0 was the first release published through Trusted Publishing. PyPI's
  attestation records that the wheel was built by this repository's
  `publish.yml`, so anyone can verify where the artifact came from without
  trusting the author — which is the claim this project makes about everything
  else it reports.

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
