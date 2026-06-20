# ROBIN HOOD Standalone Usage

ROBIN HOOD can be used independently in any project.

It does not require Continuity Legacy, Conekta, PyPI publishing, or a dashboard.

## Minimal Local Setup

From the future standalone repository root:

```powershell
$env:PYTHONPATH="."
python -m agentops.cli health --strict
pytest tests -q
```

From the extracted local repository:

```powershell
cd D:\Experimentos\ROBIN-HOOD
$env:PYTHONPATH="."
python -m agentops.cli health --strict
pytest tests -q
```

After local editable install:

```powershell
cd D:\Experimentos\ROBIN-HOOD
pip install -e .
robinhood health --strict
robinhood scan --file adversarial_cases\indirect_prompt_injection.txt --source web --fail-on-block
robinhood scan --path adversarial_cases --source web --fail-on-block
```

## Daily Use

### 1. Make A Context Packet

Use a small packet instead of pasting an entire repository:

```text
Objective:
Allowed files:
Constraints:
Verification:
Rollback:
Expected output:
```

### 2. Classify External Content

Any text from web pages, PDFs, tickets, issues, OCR, model output, or chat logs starts as low trust.

Look for:

- instruction override
- hidden Unicode
- fake authority
- secret-like material
- tool-call pressure

CLI examples:

```powershell
robinhood scan --text "ignore previous instructions" --source web --fail-on-block
robinhood scan --file notes.md --source external
robinhood scan --path incoming_context --source web --fail-on-block
```

### 3. Grant Capabilities

Give the agent only what it needs:

```text
read: yes
edit: only selected paths
test: yes
shell: only if necessary
network: no by default
git: no by default
publish: no unless this is a release task
```

### 4. Verify Locally

Run local checks before using a stronger or paid model.

Examples:

```powershell
pytest -q
python -m json.tool config.json
git diff --stat
```

### 5. Log Frugality

Record:

- task id
- model/tool used
- token estimate
- retries
- outcome
- whether the work reduced cost, risk, or drift

JSONL is enough until it hurts.

Example:

```powershell
robinhood log --task-id AOP-001 --model local --tokens-estimated 1200 --retries 0 --outcome pass --reduced cost
robinhood report
```

## When ROBIN HOOD Is Worth Using Alone

Use it when:

- a task includes external content
- an agent has file or shell access
- context is getting large
- previous attempts caused drift
- a release or publication step is involved
- multiple models/providers are being compared

Skip it when:

- the task is tiny
- there is no external content
- no tool permissions are involved
- the overhead is larger than the risk

## Standalone Success Criteria

ROBIN HOOD is useful if it reduces at least one:

- context sent to models
- retries
- unsafe tool calls
- secret-like material before context sharing
- accidental out-of-scope edits
- release mistakes
- time spent reconstructing handoffs
