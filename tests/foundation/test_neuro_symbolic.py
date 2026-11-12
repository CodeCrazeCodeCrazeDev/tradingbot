"""Neuro-symbolic reasoner: policy gates enforced as data, specialist
routing, sealed ledger chain, vulnerability disclosure hold, sandbox
routing for untrusted input. Advisory-only — tests assert REFUSALS."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from trading_bot.core.csc.neuro_symbolic import (  # noqa: E402
    ActionClass, Fact, Ledger, NeuroSymbolicReasoner, POLICY)


def _r(tmp_path):
    return NeuroSymbolicReasoner(
        ctx={}, ledger=Ledger(tmp_path / "nsr.jsonl"))


def test_policy_matrix():
    assert POLICY[ActionClass.LIVE_EXECUTION] == "refused"
    assert POLICY[ActionClass.RISKY_CHANGE] == "requires_signed_approval"
    assert POLICY[ActionClass.TRADING_RESEARCH] == "allow"


def test_live_execution_refused_by_construction(tmp_path):
    d = _r(tmp_path).route({
        "id": "h1", "action_class": "live_execution",
        "sends_orders": True})
    assert d.gate == "refused" and d.verdict == "refused"


def test_risky_change_needs_signed_approval(tmp_path):
    r = _r(tmp_path)
    d = r.route({"id": "h2", "action_class": "risky_change",
                 "action": "promote"})
    assert d.verdict == "pending_approval"
    d2 = r.route({"id": "h3", "action_class": "risky_change",
                  "action": "promote"}, operator_approved=True)
    assert d2.verdict == "approved_to_execute"


def test_untrusted_routes_sandbox_only(tmp_path):
    d = _r(tmp_path).route({
        "id": "h4", "action_class": "code_hardening",
        "untrusted": True})
    assert d.gate == "sandbox_only" and d.verdict == "sandbox_only"


def test_vulnerability_sealed(tmp_path):
    d = _r(tmp_path).route({
        "id": "h5", "action_class": "defensive_security",
        "vulnerability": True})
    assert d.sealed is True


def test_benchmark_channel_never_confirms(tmp_path):
    r = _r(tmp_path)
    assert r.verify({"channel": "benchmark"}, []) == "needs_regression"


def test_ledger_hash_chain(tmp_path):
    led = Ledger(tmp_path / "nsr.jsonl")
    led.append({"type": "a", "x": 1})
    led.append({"type": "b", "x": 2})
    assert led.verify_chain() is True
    # tamper detection: rewrite a row
    lines = (tmp_path / "nsr.jsonl").read_text().splitlines()
    lines[0] = lines[0].replace('"x": 1', '"x": 9')
    (tmp_path / "nsr.jsonl").write_text("\n".join(lines) + "\n")
    assert led.verify_chain() is False


def test_propose_templates_from_facts(tmp_path):
    r = _r(tmp_path)
    hyps = r.propose([Fact("edge_verdict", "rate_diff", "no_edge",
                           "edge_gate"),
                      Fact("spread", "XAUUSD", 15.0, "dsc")])
    kinds = {h["id"] for h in hyps}
    assert "h_rate_diff_invert" in kinds
    assert "h_XAUUSD_spread" in kinds
    for h in hyps:
        assert h["action_class"] == "trading_research"
        assert h["channel"] == "regression"


def test_analyze_end_to_end(tmp_path):
    rep = _r(tmp_path).analyze(
        [Fact("edge_verdict", "mom", "no_edge", "edge_gate")])
    assert rep["advisory_only"] is True
    assert rep["decisions"][0]["route"] == "allowed"
