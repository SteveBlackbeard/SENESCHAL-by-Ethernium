#!/usr/bin/env python3
"""Measure real context-token savings on a real repository.

Publishable numbers require measurement, not estimation. This compares what a
naive "dump the repo" prompt costs against what Seneschal actually selects under
a budget, counting tokens with a real tokenizer (tiktoken) when available and
saying so when it is not.

It measures ONLY what can be measured locally and honestly:
  * context reduction  (naive dump  vs  budgeted BM25 selection)
  * snapshot reuse     (second run  vs  first run, unchanged files)

It deliberately does NOT estimate cascade/routing savings: those depend on live
model calls and accumulated ledger evidence, so any number here would be a guess.

    python scripts/benchmark_savings.py --path . --objective "fix the token budget logic"
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from seneschal.context_cache import create_snapshot, diff_snapshot  # noqa: E402
from seneschal.context_packer import _collect_candidates, _relative  # noqa: E402
from seneschal.context_select import select_context  # noqa: E402
from seneschal.token_budget import count_tokens  # noqa: E402

TOKENIZER = "tiktoken:cl100k_base"


def measured(text: str) -> tuple[int, str]:
    return count_tokens(text, tokenizer=TOKENIZER)


def naive_dump(root: Path) -> tuple[int, int, str]:
    """What you pay if you paste every candidate file into the prompt."""
    total, files, used = 0, 0, "estimate"
    for item, _tokens, _score in _collect_candidates(root):
        try:
            text = item.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        n, used = measured(text)
        total += n
        files += 1
    return total, files, used


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", default=".")
    parser.add_argument("--objective", required=True)
    parser.add_argument("--changed", action="append", default=[])
    parser.add_argument("--max-tokens", type=int, default=8000)
    args = parser.parse_args()

    root = Path(args.path).resolve()
    print(f"repository : {root}")
    print(f"objective  : {args.objective}")
    print(f"budget     : {args.max_tokens} tokens\n")

    dump_tokens, dump_files, used = naive_dump(root)
    if used != TOKENIZER:
        print("WARNING: tiktoken not installed — numbers below are ESTIMATES.")
        print("         install with: pip install \"seneschal[measure]\"\n")

    selection = select_context(
        root,
        changed_paths=args.changed or [],
        max_tokens=args.max_tokens,
        min_score=0,
        objective=args.objective,
    )
    sel_text = ""
    for item in selection.selected:
        p = root / item.path
        try:
            sel_text += p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
    sel_tokens, _ = measured(sel_text)

    reduction = (1 - sel_tokens / dump_tokens) * 100 if dump_tokens else 0.0
    print("CONTEXT SELECTION")
    print(f"  naive dump      : {dump_tokens:>8,} tokens  ({dump_files} files)")
    print(f"  Seneschal select: {sel_tokens:>8,} tokens  ({len(selection.selected)} files)")
    print(f"  reduction       : {reduction:>7.1f}%")

    # Snapshot reuse: what a second run costs when nothing changed.
    snap = create_snapshot(root)
    diff = diff_snapshot(snap, create_snapshot(root))
    full = diff["full_context_tokens"]
    delta = diff["delta_context_tokens"]
    reuse = (1 - delta / full) * 100 if full else 0.0
    print("\nSNAPSHOT REUSE (second run, nothing changed)")
    print(f"  full context    : {full:>8,} tokens")
    print(f"  delta to resend : {delta:>8,} tokens")
    print(f"  avoided         : {reuse:>7.1f}%")

    print(f"\ntokenizer: {used}")
    print("Not measured here: cascade/routing savings — they need live model")
    print("calls and ledger history, so any figure would be a guess.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
