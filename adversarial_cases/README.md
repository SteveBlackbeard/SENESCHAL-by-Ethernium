# ROBIN HOOD Adversarial Cases

These are benign defensive test cases.

They exist to verify that ROBIN HOOD detects risky patterns without storing leaked prompts, real secrets, exploit chains, or provider-specific hidden instructions.

Rules:

- no real credentials
- no copied vendor prompts
- no operational exploit recipes
- no malware code
- no jailbreak packs

Each case should test one defensive idea:

- untrusted instruction override
- hidden Unicode
- fake secret marker
- suspicious tool request
- external-link pressure
