"""Tests for the advanced frugality engine: Thompson bandit routing, the
FrugalGPT cascade, BM25 context relevance, and prompt-cache layout planning."""

from pathlib import Path

import json

import pytest

from agentops.bandit import expected_success, posterior_params, thompson_scores
from agentops.bm25 import BM25
from agentops.cascade import run_cascade
from agentops.context_cache import plan_cache_layout
from agentops.context_select import select_context
from agentops.frugality_ledger import new_entry, read_entries, summarize_by_model
from agentops.router import recommend_route


# ── Bandit ────────────────────────────────────────────────────────────────────

def test_posterior_params_reflect_track_record():
    assert posterior_params(None) == (1.0, 1.0)  # no history -> uniform
    good = posterior_params({"entries": 10, "failures": 0, "retries": 0})
    bad = posterior_params({"entries": 10, "failures": 10, "retries": 0})
    assert good == (11.0, 1.0)
    assert bad == (1.0, 11.0)
    assert expected_success({"entries": 10, "failures": 0, "retries": 0}) > 0.9
    assert expected_success({"entries": 10, "failures": 10, "retries": 0}) < 0.1


def test_thompson_scores_deterministic_under_seed():
    stats = {"a": {"entries": 5, "failures": 0, "retries": 0}}
    assert thompson_scores(["a", "b"], stats, seed=7) == thompson_scores(["a", "b"], stats, seed=7)


def test_route_explore_prefers_reliable_arm():
    # Perfect record for lora, perfect failure for local-small: with strongly
    # separated posteriors the sampled ranking must favor the reliable arm.
    stats = {
        "local-small": {"entries": 12, "failures": 12, "retries": 0, "failure_rate": 1.0},
        "generic-local-lora": {"entries": 12, "failures": 0, "retries": 0, "failure_rate": 0.0},
    }
    wins = 0
    for seed in range(20):
        route = recommend_route("fix typo in docs", privacy="local-first",
                                model_stats=stats, explore=True, seed=seed)
        if route.selected_model != "local-small":
            wins += 1
    assert wins >= 18, f"bandit ignored a perfect failure record ({wins}/20)"


def test_route_explore_reason_present():
    route = recommend_route("fix typo in docs", privacy="local-first",
                            model_stats={}, explore=True, seed=1)
    assert any("bandit" in r for r in route.reasons)


# ── Ledger failure semantics ─────────────────────────────────────────────────

def test_error_string_outcomes_count_as_failures():
    entries = [
        new_entry(task_id="a", model="m", tokens_estimated=1, retries=0, outcome="pass", reduced="cost"),
        new_entry(task_id="b", model="m", tokens_estimated=1, retries=0, outcome="quality-gate-failed", reduced="cost"),
        new_entry(task_id="c", model="m", tokens_estimated=1, retries=0, outcome="timeout", reduced="cost"),
    ]
    stats = summarize_by_model(entries)
    assert stats["m"]["failures"] == 2
    assert stats["m"]["failure_rate"] == round(2 / 3, 4)


# ── Cascade ───────────────────────────────────────────────────────────────────

def _write_providers(tmp_path: Path) -> Path:
    payload = {
        "version": "0.1.0",
        "profiles": [
            {
                "id": "cheap-a", "provider": "ollama", "context_window": 4096,
                "privacy": "local", "latency": "low", "strengths": ["cheap"],
                "model_env": "RH_TEST_MODEL_A",
            },
            {
                "id": "strong-b", "provider": "ollama", "context_window": 8192,
                "privacy": "local", "latency": "medium", "strengths": ["private"],
                "model_env": "RH_TEST_MODEL_B",
            },
        ],
    }
    path = tmp_path / "providers.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_cascade_escalates_on_quality_failure(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("RH_TEST_MODEL_A", "model-a")
    monkeypatch.setenv("RH_TEST_MODEL_B", "model-b")
    providers = _write_providers(tmp_path)
    ledger = tmp_path / "ledger.jsonl"
    state = tmp_path / "state.json"
    objective = "summarize the repository readme file"

    transports = {
        # Hop 1: empty answer -> quality gate fails -> escalate.
        "cheap-a": lambda endpoint, payload, timeout: {"response": ""},
        # Hop 2: grounded answer -> gate passes -> stop.
        "strong-b": lambda endpoint, payload, timeout: {
            "response": "The repository readme file explains the project purpose and usage instructions."
        },
    }
    result = run_cascade(
        objective,
        providers_path=providers,
        state_path=state,
        ledger_path=ledger,
        transports=transports,
    )
    assert result.ok
    assert result.selected_model == "strong-b"
    called = [h for h in result.hops if h.called]
    assert [h.model_id for h in called] == ["cheap-a", "strong-b"], "must try cheapest first, escalate once"
    assert not called[0].ok and called[1].ok
    outcomes = [e.outcome for e in read_entries(ledger)]
    assert outcomes == ["fail", "pass"], "every hop must leave ledger evidence"


def test_cascade_stops_at_first_pass(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("RH_TEST_MODEL_A", "model-a")
    monkeypatch.setenv("RH_TEST_MODEL_B", "model-b")
    providers = _write_providers(tmp_path)
    calls = {"b": 0}

    def transport_b(endpoint, payload, timeout):
        calls["b"] += 1
        return {"response": "unused"}

    transports = {
        "cheap-a": lambda endpoint, payload, timeout: {
            "response": "The repository readme file explains the project purpose and usage instructions."
        },
        "strong-b": transport_b,
    }
    result = run_cascade(
        "summarize the repository readme file",
        providers_path=providers,
        state_path=tmp_path / "state.json",
        transports=transports,
    )
    assert result.ok and result.selected_model == "cheap-a"
    assert calls["b"] == 0, "no escalation when the cheap model passes the gate"


def test_cascade_skips_unconfigured_profiles(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("RH_TEST_MODEL_A", raising=False)
    monkeypatch.setenv("RH_TEST_MODEL_B", "model-b")
    providers = _write_providers(tmp_path)
    ledger = tmp_path / "ledger.jsonl"
    transports = {
        "strong-b": lambda endpoint, payload, timeout: {
            "response": "The repository readme file explains the project purpose and usage instructions."
        },
    }
    result = run_cascade(
        "summarize the repository readme file",
        providers_path=providers,
        state_path=tmp_path / "state.json",
        ledger_path=ledger,
        transports=transports,
    )
    assert result.ok and result.selected_model == "strong-b"
    skipped = [h for h in result.hops if not h.called]
    assert skipped and skipped[0].error == "missing-model"
    assert len(read_entries(ledger)) == 1, "skipped hops must not pollute the ledger"


# ── BM25 context relevance ───────────────────────────────────────────────────

def test_bm25_ranks_relevant_document_first():
    corpus = {
        "auth.py": "def login(user, password): verify credentials token session",
        "billing.py": "def invoice(amount): tax subtotal currency payment",
        "readme.md": "project overview installation quickstart",
    }
    scores = BM25(corpus).scores("fix the login credentials verification")
    assert scores["auth.py"] > scores["billing.py"]
    assert scores["auth.py"] > scores["readme.md"]


def test_select_context_objective_boosts_relevant_file(tmp_path: Path):
    (tmp_path / "auth.py").write_text(
        "def login(user, password):\n    # verify credentials and issue token\n    return token\n",
        encoding="utf-8",
    )
    (tmp_path / "billing.py").write_text(
        "def invoice(amount):\n    return amount * 1.16\n", encoding="utf-8"
    )
    (tmp_path / "changed.py").write_text("print('x')\n", encoding="utf-8")

    with_objective = select_context(
        tmp_path, changed_paths=["changed.py"], max_tokens=4000,
        min_score=0, objective="fix the login credentials token verification",
    )
    by_path = {item.path: item for item in with_objective.selected}
    assert "auth.py" in by_path
    assert "bm25-match" in by_path["auth.py"].reason
    baseline = select_context(tmp_path, changed_paths=["changed.py"], max_tokens=4000, min_score=0)
    baseline_auth = {i.path: i for i in baseline.selected}["auth.py"]
    assert by_path["auth.py"].score > baseline_auth.score


# ── Health guard (runtime vs repo modes) ─────────────────────────────────────

def test_health_runtime_passes_without_repo_docs(monkeypatch: pytest.MonkeyPatch):
    # Simulate an installed package (no repo checkout): runtime health must pass
    # and the governance doc checks must be skipped — the bug the install audit
    # caught was health failing on missing README/BLUEPRINT from site-packages.
    import agentops.health_guard as hg

    monkeypatch.setattr(hg, "is_repo_checkout", lambda: False)
    assert hg.check_runtime() == []
    assert hg.main(["--strict"]) == 0


def test_health_runtime_detects_broken_profiles(monkeypatch: pytest.MonkeyPatch):
    import agentops.health_guard as hg
    from agentops import provider_profiles

    monkeypatch.setattr(provider_profiles, "load_profiles", lambda *a, **k: [])
    findings = hg.check_runtime()
    assert any("provider profiles" in f.message for f in findings)


# ── Signed capability grants ─────────────────────────────────────────────────

def _require_crypto():
    pytest.importorskip("cryptography")


def test_signed_grant_roundtrip(tmp_path: Path):
    _require_crypto()
    from agentops.signing import generate_keys, load_keys, sign_grant, verify_grant

    generate_keys(tmp_path)
    priv, pub = load_keys(tmp_path)
    grant = {"task_id": "RH-1", "capabilities": ["read"], "allowed_paths": ["src/"], "denied_paths": []}
    sign_grant(grant, priv, pub)
    ok, reason = verify_grant(grant, pub)
    assert ok, reason


def test_capability_escalation_is_rejected(tmp_path: Path):
    _require_crypto()
    from agentops.signing import generate_keys, load_keys, sign_grant, verify_grant

    generate_keys(tmp_path)
    priv, pub = load_keys(tmp_path)
    grant = {"task_id": "RH-1", "capabilities": ["read"], "allowed_paths": ["src/"], "denied_paths": []}
    sign_grant(grant, priv, pub)
    grant["capabilities"] = ["read", "shell", "publish"]  # agent forges more power
    ok, reason = verify_grant(grant, pub)
    assert not ok
    assert "modified after signing" in reason


def test_foreign_key_resign_is_rejected(tmp_path: Path):
    _require_crypto()
    from agentops.signing import generate_keys, load_keys, sign_grant, verify_grant

    generate_keys(tmp_path / "operator")
    _op_priv, op_pub = load_keys(tmp_path / "operator")
    generate_keys(tmp_path / "attacker")
    att_priv, att_pub = load_keys(tmp_path / "attacker")
    grant = {"task_id": "RH-1", "capabilities": ["shell"], "allowed_paths": ["/"], "denied_paths": []}
    sign_grant(grant, att_priv, att_pub)  # attacker signs with THEIR key
    ok, reason = verify_grant(grant, op_pub)
    assert not ok
    assert "untrusted key" in reason


def test_grant_fingerprint_pin(tmp_path: Path):
    _require_crypto()
    from agentops.signing import generate_keys, key_fingerprint, load_keys, sign_grant, verify_grant_fingerprint

    generate_keys(tmp_path)
    priv, pub = load_keys(tmp_path)
    fp = key_fingerprint(pub)
    grant = {"task_id": "RH-1", "capabilities": ["read"], "allowed_paths": ["src/"], "denied_paths": []}
    sign_grant(grant, priv, pub)
    ok, _ = verify_grant_fingerprint(grant, fp)
    assert ok
    bad, reason = verify_grant_fingerprint(grant, "SHA256:not-the-key")
    assert not bad and "fingerprint" in reason


def test_cli_grant_fingerprint_and_task_binding(tmp_path: Path, capsys: pytest.CaptureFixture):
    _require_crypto()
    from agentops.cli import main as cli_main
    from agentops.signing import key_fingerprint, load_keys

    keys = str(tmp_path / "keys")
    grant_file = str(tmp_path / "grant.json")
    assert cli_main(["keygen", "--keys", keys]) == 0
    capsys.readouterr()
    cli_main(["grant", "--sign", "--keys", keys, "--task-id", "TASK-A",
              "--capability", "read", "--allowed-path", "src/", "--out", grant_file])
    capsys.readouterr()
    fp = key_fingerprint(load_keys(keys)[1])

    # Third party with only the fingerprint (no --keys dir) authorizes in-scope.
    assert cli_main(["grant", "--grant-file", grant_file, "--expect-fingerprint", fp,
                     "--keys", str(tmp_path / "nonexistent"),
                     "--action", "read", "--path", "src/main.py"]) == 0
    capsys.readouterr()
    # Wrong fingerprint -> rejected.
    assert cli_main(["grant", "--grant-file", grant_file, "--expect-fingerprint", "SHA256:wrong",
                     "--action", "read", "--path", "src/main.py"]) == 1
    assert "fingerprint" in capsys.readouterr().out
    # Replay for a different task -> rejected even though signature is valid.
    assert cli_main(["grant", "--grant-file", grant_file, "--require-signed", "--keys", keys,
                     "--task-id", "TASK-B", "--action", "read", "--path", "src/main.py"]) == 1
    assert "bound to task" in capsys.readouterr().out


def test_expired_grant_is_rejected(tmp_path: Path):
    _require_crypto()
    from agentops.signing import generate_keys, load_keys, sign_grant, verify_grant

    generate_keys(tmp_path)
    priv, pub = load_keys(tmp_path)
    grant = {"task_id": "RH-1", "capabilities": ["read"], "allowed_paths": ["src/"],
             "denied_paths": [], "expires": "2020-01-01T00:00:00+00:00"}
    sign_grant(grant, priv, pub)
    ok, reason = verify_grant(grant, pub)
    assert not ok
    assert "expired" in reason


def test_cli_sign_and_check_signed_grant(tmp_path: Path, capsys: pytest.CaptureFixture):
    _require_crypto()
    from agentops.cli import main as cli_main

    keys = str(tmp_path / "keys")
    grant_file = str(tmp_path / "grant.json")
    assert cli_main(["keygen", "--keys", keys]) == 0
    capsys.readouterr()
    assert cli_main([
        "grant", "--sign", "--keys", keys, "--task-id", "RH-9",
        "--capability", "read", "--allowed-path", "src/", "--out", grant_file,
    ]) == 0
    capsys.readouterr()
    # Signed grant verifies and authorizes an in-scope action.
    assert cli_main([
        "grant", "--grant-file", grant_file, "--require-signed", "--keys", keys,
        "--action", "read", "--path", "src/main.py",
    ]) == 0
    capsys.readouterr()
    # Tampered grant (escalated capabilities) is rejected fail-closed.
    payload = json.loads(Path(grant_file).read_text(encoding="utf-8"))
    payload["capabilities"] = ["read", "shell"]
    Path(grant_file).write_text(json.dumps(payload), encoding="utf-8")
    assert cli_main([
        "grant", "--grant-file", grant_file, "--require-signed", "--keys", keys,
        "--action", "shell",
    ]) == 1
    out = capsys.readouterr().out
    assert "rejected" in out


def test_cli_unsigned_grant_with_require_signed_fails(tmp_path: Path, capsys: pytest.CaptureFixture):
    from agentops.cli import main as cli_main

    assert cli_main([
        "grant", "--task-id", "RH-1", "--capability", "read",
        "--allowed-path", "src/", "--action", "read", "--path", "src/x.py",
        "--require-signed",
    ]) == 1
    assert "unsigned" in capsys.readouterr().out


# ── Prompt-cache layout ──────────────────────────────────────────────────────

def test_cache_layout_orders_stable_first_and_prices_savings():
    plan = plan_cache_layout(
        "You are a frugal assistant." * 20,
        "What changed today?",
        ["STABLE RULESET " * 50],
        input_cost_per_million=2.0,
        runs=101,
    )
    assert plan["layout"][-1]["segment"] == "variable-user"
    assert all(seg["segment"] == "system+stable" for seg in plan["layout"][:-1])
    assert plan["cacheable_ratio"] > 0.9
    expected = (plan["cacheable_prefix_tokens"] * 100 / 1_000_000) * 2.0 * 0.9
    assert plan["estimated_cost_saved"] == round(expected, 6)
