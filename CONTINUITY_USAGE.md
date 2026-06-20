# Using Continuity Legacy With ROBIN HOOD

Continuity Legacy and ROBIN HOOD solve different parts of the same workflow.

Continuity Legacy protects project state:

- governed baseline
- live handoff
- health guard
- package/release integrity
- cryptographic identity and continuity memory

ROBIN HOOD protects agent operations:

- context minimization
- prompt-risk triage
- least-privilege capability scope
- frugality ledger
- provider-neutral task packets

## Recommended Workflow

1. Run Continuity checks before a high-risk task:

```powershell
python scripts\golden_baseline.py verify
python scripts\health_guard.py --strict
```

2. Build an ROBIN HOOD context packet:

```text
Objective:
Allowed files:
Constraints:
Verification:
Rollback:
Expected output:
```

3. Classify external content before putting it in a model context:

```text
source: web/pdf/ticket/generated
trust: low
risk findings: prompt injection, hidden unicode, secret material, links
```

4. Grant only the needed capabilities:

```text
read: yes
edit: specific paths only
test: yes
shell: only if needed
network: no by default
publish: no unless release task
```

5. Execute the task.

6. Record cost/risk/drift in the frugality ledger.

7. Run Continuity checks again:

```powershell
python scripts\golden_baseline.py verify
python scripts\health_guard.py --strict
pytest -q
```

## Practical Example

Task: update a README from an external issue.

Use ROBIN HOOD to:

- mark the issue text as untrusted external content
- scan for prompt-injection phrases
- build a minimal context packet with only README and relevant docs
- grant `read`, `edit`, and `test`, but not `publish`
- log retries and token estimate

Use Continuity to:

- verify the repo baseline before and after
- ensure protected files were not changed accidentally
- preserve the handoff state

## Boundary

ROBIN HOOD must not become a dependency of Continuity Legacy runtime.

Continuity can call ROBIN HOOD in future CI as an optional external gate, but Legacy must remain usable without ROBIN HOOD installed.
