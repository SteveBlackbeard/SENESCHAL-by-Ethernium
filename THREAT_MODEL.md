# Seneschal Threat Model

Seneschal is defensive infrastructure for AI-agent workflows.

## Assets

Protect:

- source code
- secrets and API keys
- release credentials
- private notes
- governance rules
- memory and handoff files
- tool permissions
- human trust

## Trust Zones

| Zone | Examples | Default Trust |
| --- | --- | --- |
| System | local rulebook, explicit developer policy | high |
| User | current task request | high but scoped |
| Repository | tracked source code | medium |
| External content | web pages, pasted prompts, PDFs, tickets | low |
| Generated content | model outputs, summaries, drafts | low until verified |
| Tools | shell, git, network, package upload | privileged |

## Main Risks

### Prompt Injection

External text attempts to override instructions.

Controls:

- mark external content as data
- strip hidden instructions from authority
- detect instruction override phrases
- preserve source labels

### Indirect Prompt Injection

A document, webpage, dependency note, image, or issue comment contains instructions for the agent.

Controls:

- treat retrieved content as untrusted
- require explicit user intent for tool actions
- separate facts from commands

### Memory Poisoning

Bad content enters long-term memory or handoff and later influences work.

Controls:

- sign or hash trusted handoffs
- label memory provenance
- quarantine unverified summaries

### Tool Hijack

The model is tricked into running commands, publishing packages, changing remotes, or exposing secrets.

Controls:

- capability broker
- explicit allowed files
- dry-run first for destructive operations
- release actions require checklist

### Secret Leakage

Secrets appear in logs, diffs, prompts, generated files, or release artifacts.

Controls:

- secret scanner
- redact logs
- never include credentials in context packets
- block accidental uploads

### Reasoning Interruption

Adversarial inputs cause empty answers, broken reasoning, or premature final responses.

Controls:

- timeout and retry classification
- require final answer completeness checks
- verify outputs with local tests

### Multimodal Injection

Images, PDFs, OCR, or generated screenshots hide instructions.

Controls:

- OCR text is untrusted
- visual content cannot issue commands
- extracted text keeps source labels

## Defensive Reverse Engineering

Study known incidents only to extract defensive classes:

- leaked prompt risk shows prompts are not security boundaries
- tool misuse shows permissions need external control
- memory attacks show provenance matters
- reasoning attacks show outputs need validation
- deepfake/content failures show policy must be enforced outside generation

Seneschal must convert incidents into tests, not into exploit recipes.
