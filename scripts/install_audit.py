#!/usr/bin/env python3
"""Installation & usage audit for Seneschal.

Builds the package, installs the wheel into a THROWAWAY virtual environment
(exactly what a user gets from PyPI — not the source tree), and exercises the
public CLI end to end. Catches the class of bugs unit tests miss because they
run from the repo: missing package data, broken entry points, and code that
assumes repo-relative paths.

    python scripts/install_audit.py            # build + audit
    python scripts/install_audit.py --no-build # reuse an existing dist/ wheel

Exit code 0 = the installed package is healthy and every headline command runs.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
import venv
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
FAILURES: list[str] = []


def run(cmd: list[str], **kw) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


def check(name: str, ok: bool, detail: str = "") -> None:
    mark = "PASS" if ok else "FAIL"
    print(f"  [{mark}] {name}" + (f" -> {detail}" if detail and not ok else ""))
    if not ok:
        FAILURES.append(name)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-build", action="store_true")
    args = parser.parse_args()

    if not args.no_build:
        print("== building package ==")
        build = run([sys.executable, "-m", "build"], cwd=REPO)
        check("build succeeds", build.returncode == 0, build.stderr[-400:])
        if build.returncode != 0:
            return 1

    wheels = sorted((REPO / "dist").glob("seneschal-*.whl"))
    check("wheel artifact exists", bool(wheels))
    if not wheels:
        return 1
    wheel = wheels[-1]

    with tempfile.TemporaryDirectory() as tmp:
        env_dir = Path(tmp) / "venv"
        print(f"== creating clean venv: {env_dir} ==")
        venv.create(env_dir, with_pip=True)
        bin_dir = env_dir / ("Scripts" if sys.platform == "win32" else "bin")
        py = bin_dir / ("python.exe" if sys.platform == "win32" else "python")

        print("== installing wheel[measure,security] ==")
        install = run([str(py), "-m", "pip", "install", "--quiet", f"{wheel}[measure,security]"])
        check("clean install succeeds", install.returncode == 0, install.stderr[-400:])
        if install.returncode != 0:
            return 1

        def cli(*a: str) -> subprocess.CompletedProcess:
            return run([str(py), "-m", "seneschal.cli", *a])

        # Entry-point health (the bug this audit was written to catch).
        health = run([str(py), "-m", "seneschal.health_guard", "--strict"])
        check("health --strict passes from installed package", health.returncode == 0,
              health.stdout.strip() + health.stderr.strip())

        # Bundled package data loads.
        models = cli("models")
        check("provider profiles load (models)", models.returncode == 0)

        keys = Path(tmp) / "k"
        grant = Path(tmp) / "g.json"
        check("keygen", run([str(py), "-m", "seneschal.cli", "keygen", "--keys", str(keys)]).returncode == 0)
        sign = cli("grant", "--sign", "--keys", str(keys), "--task-id", "A",
                   "--capability", "read", "--allowed-path", "src/", "--out", str(grant))
        check("grant --sign", sign.returncode == 0)
        verify = cli("grant", "--grant-file", str(grant), "--require-signed",
                     "--keys", str(keys), "--action", "read", "--path", "src/x.py")
        check("signed grant authorizes in-scope action", verify.returncode == 0)

        # Tampered grant must be rejected (security invariant, end to end).
        payload = json.loads(grant.read_text(encoding="utf-8"))
        payload["capabilities"] = ["read", "shell"]
        grant.write_text(json.dumps(payload), encoding="utf-8")
        tampered = cli("grant", "--grant-file", str(grant), "--require-signed",
                       "--keys", str(keys), "--action", "shell")
        check("tampered grant is rejected", tampered.returncode == 1)

        for label, a in [
            ("route --explore", ["route", "--objective", "fix typo", "--explore", "--seed", "1"]),
            ("select --objective", ["select", "--path", str(REPO), "--changed", "README.md",
                                     "--max-tokens", "4000", "--objective", "frugal routing"]),
            ("reuse --layout", ["reuse", "--system", "stable", "--user", "task", "--layout"]),
            ("scan", ["scan", "--path", str(REPO / "README.md"), "--source", "repo"]),
        ]:
            check(label, cli(*a).returncode == 0)

    print()
    if FAILURES:
        print(f"INSTALL AUDIT FAILED: {len(FAILURES)} check(s) -> {', '.join(FAILURES)}")
        return 1
    print("INSTALL AUDIT PASSED: package installs clean and every headline command runs.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
