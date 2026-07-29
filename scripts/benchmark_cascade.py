"""Measure the FrugalGPT cascade against a real local model stack.

Context selection savings are already measured with tiktoken (see
``benchmark_savings.py`` and the README table). The one figure the README used to
decline to publish was cascade behaviour, because it needs live model calls. This
script produces that figure honestly and reproducibly.

The honest metric with free local models is *first-tier sufficiency*: how often the
cheap tier clears the quality gate so the expensive tier is never called. Dollar
savings are not invented here — local calls cost nothing; what is measured is how
often the cascade avoids the bigger model, plus a proof that escalation recovers
when the cheap tier fails.

Usage (requires a running Ollama with two pulled models)::

    export SENESCHAL_OLLAMA_BASE_URL=http://localhost:11434
    export SEN_M_SMALL=<a small pulled model>
    export SEN_M_BIG=<a larger pulled model>
    python scripts/benchmark_cascade.py --providers examples/providers.2tier.json

The providers file must declare two enabled ollama profiles whose ``model_env``
point at SEN_M_SMALL (cheap, first) and SEN_M_BIG (strong, escalation target).
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time

DEFAULT_TASKS = [
    "What does a Merkle root prove? Answer in one clear sentence.",
    "Write a Python one-liner that reverses the string s.",
    "Define idempotency in one sentence.",
    "In one sentence, what is the purpose of an append-only log?",
    "Explain in 2-3 sentences why RFC 6962 prefixes leaf hashes with 0x00 and internal nodes with 0x01.",
    "Review this function and name the bug in one sentence: def add(a, b): return a - b",
    "Summarize in one sentence what a fail-closed default means for a security gate.",
]

QUALITY_PASS = 60  # the cascade's own quality gate threshold for "good enough"


def run_cascade(task: str, providers: str, ledger: str | None) -> dict:
    cmd = [
        sys.executable, "-m", "seneschal.cli", "cascade",
        "--objective", task, "--prompt", task,
        "--privacy", "local-only", "--providers", providers,
    ]
    if ledger:
        cmd += ["--ledger", ledger]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    return json.loads(proc.stdout)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--providers", required=True, help="Two-tier ollama providers file.")
    ap.add_argument("--ledger", default=None, help="Optional JSONL ledger path.")
    ap.add_argument("--json-out", default=None, help="Optional path to write the summary JSON.")
    args = ap.parse_args()

    rows = []
    t0 = time.time()
    for i, task in enumerate(DEFAULT_TASKS, 1):
        d = run_cascade(task, args.providers, args.ledger)
        hops = d.get("hops", [])
        tier1_ok = bool(
            hops
            and hops[0].get("ok")
            and hops[0].get("quality_score", 0) >= QUALITY_PASS
            and d.get("escalations", 0) == 0
        )
        rows.append({
            "task_class": d.get("task_class"),
            "selected": d.get("selected_model"),
            "escalations": d.get("escalations", 0),
            "hops": len(hops),
            "tier1_ok": tier1_ok,
            "final_ok": d.get("ok"),
        })
        r = rows[-1]
        print(f"  [{i}] {r['task_class']:<14} tier1_ok={str(r['tier1_ok']):<5} "
              f"esc={r['escalations']} hops={r['hops']} final_ok={r['final_ok']}")

    n = len(rows)
    tier1 = sum(1 for r in rows if r["tier1_ok"])
    esc = sum(r["escalations"] for r in rows)
    calls = sum(r["hops"] for r in rows)
    print("\n=== MEASURED (real local calls) ===")
    print(f"  tasks:                  {n}")
    print(f"  first-tier sufficiency: {tier1}/{n} = {round(100 * tier1 / n)}%")
    print(f"  escalations:            {esc}")
    print(f"  total model calls:      {calls} (naive always-strong would be {n})")
    print(f"  wall time:              {round(time.time() - t0)}s")

    summary = {
        "tasks": n,
        "first_tier_sufficiency_pct": round(100 * tier1 / n) if n else 0,
        "escalations": esc,
        "total_calls": calls,
        "rows": rows,
    }
    if args.json_out:
        with open(args.json_out, "w", encoding="utf-8") as fh:
            json.dump(summary, fh, indent=2)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
