# Security Policy

ROBIN HOOD is a local-first control layer for AI-assisted work. This policy is
written to be honest about what it protects and what it does not.

## Supported versions

The latest `0.x` release on `main` receives security fixes. ROBIN HOOD is
pre-1.0: interfaces may change between minor versions.

## Reporting a vulnerability

Please report suspected vulnerabilities privately by opening a GitHub security
advisory on the repository, or by contacting the maintainer directly. Do not
open a public issue for an unfixed vulnerability. Expect an acknowledgement
within a few days; there is no bug-bounty program.

## What is in scope

- **Signed capability grants** (`agentops/signing.py`): forging a grant,
  escalating a signed grant after signing, bypassing expiry, or authorizing an
  action outside the granted capabilities/paths.
- **Prompt firewall / secret scanner** (`agentops/prompt_firewall.py`): missed
  injection markers or secret-like material in scanned inputs.
- **Capability broker** (`agentops/capability_broker.py`): path traversal or
  scope-escape in `check_action`.

## What is NOT protected (by design)

ROBIN HOOD is a preflight and control layer, not a sandbox. Honestly:

1. **It does not execute or contain model output.** It decides *whether* to call
   a model and *what* context to send; it does not sandbox what a model or an
   agent then does with a granted capability.
2. **Grant signing protects authorization, not the machine.** An attacker who
   already controls the process (or the private key in memory) can sign grants
   as the operator. Keep `grant.priv` out of version control; use
   `--expect-fingerprint` so a verifier pins the operator's key.
3. **Trust bootstrapping needs an out-of-band step.** A verifier must obtain the
   operator's key fingerprint through a channel an attacker cannot control.
   There is no certificate authority — a deliberate scope choice.
4. **Provider calls are the provider's trust boundary.** ROBIN HOOD scans and
   budgets, but does not certify a remote model's behavior.

## Cryptography

Ed25519 (via the optional `cryptography` extra) for grant signatures; SHA-256
for fingerprints. Signed documents carry a `sig_alg` tag for future algorithm
agility. No custom cryptographic primitives are implemented.
