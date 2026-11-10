"""Evolution supervisor tests — the connectivity-gated self-mastery loop.

Every terminal decision becomes a remembered experience, outcomes join
by trade_id, the reflect/learn worker runs bounded on a daemon thread,
intel sweeps stay offline-gated, and CodeEvolver only ever *proposes* —
nothing self-applies. No capital authority anywhere in the loop.
"""
import json
from types import SimpleNamespace

import pytest

from trading_bot.core.csc import evolution_supervisor as evo_mod
from trading_bot.core.csc.evolution_supervisor import EvolutionSupervisor


def _decision(outcome="EXECUTED", action="BUY", trade_id="t1", **kw):
    d = dict(outcome=outcome, action=action, trade_id=trade_id,
             confidence=0.6, quantity=0.1,
             reasoning="unit test decision",
             dominant_rejection_reason=None)
    d.update(kw)
    return SimpleNamespace(**d)


def _obs(**kw):
    d = {"symbol": "EURUSD", "close": 1.10, "volume": 100.0,
         "volatility": 0.001, "spread": 0.0002, "regime": "trend",
         "trend": "up"}
    d.update(kw)
    return d


@pytest.fixture
def sup(tmp_path, monkeypatch):
    monkeypatch.delenv("TB_SELF_MASTERY", raising=False)
    s = EvolutionSupervisor(data_dir=str(tmp_path / "mastery"),
                            external=False)
    yield s
    s.stop()


def _join(sup, timeout=60.0):
    w = sup._worker
    assert w is not None
    w.join(timeout=timeout)
    assert not w.is_alive()


def test_constructor_is_side_effect_free(tmp_path, monkeypatch):
    monkeypatch.delenv("TB_SELF_MASTERY", raising=False)
    s = EvolutionSupervisor(data_dir=str(tmp_path / "m"),
                            external=False)
    assert s._worker is None and s._sentinel is None
    assert not (tmp_path / "m").exists()
    s.stop()


def test_ingest_executed_decision_records_experience(sup):
    exp_id = sup.ingest_decision(_obs(), _decision())
    assert exp_id
    assert sup.experiences_recorded == 1
    assert sup._open_experiences["t1"] == exp_id


def test_abstain_and_rejection_recorded_as_skipped(sup):
    a = sup.ingest_decision(_obs(), _decision(outcome="ABSTAIN",
                                              action="HOLD"))
    r = sup.ingest_decision(
        _obs(), _decision(outcome="TRADE_REJECTED",
                          dominant_rejection_reason="risk_veto"))
    assert a and r
    assert sup.experiences_recorded == 2


def test_outcome_attaches_to_open_experience(sup):
    sup.ingest_decision(_obs(), _decision(trade_id="t9"))
    ok = sup.ingest_outcome(
        "t9", {"action": "BUY", "regime": "trend",
               "entry_price": 1.10, "confidence": 0.6},
        was_correct=True, realized_return=0.004, exit_price=1.1044)
    assert ok is True
    assert sup.outcomes_recorded == 1
    assert "t9" not in sup._open_experiences


def test_outcome_without_prior_decision_rehydrates(sup):
    ok = sup.ingest_outcome(
        "old-trade", {"action": "SELL", "regime": "range",
                      "entry_price": 1.2, "confidence": 0.4},
        was_correct=False, realized_return=-0.003, exit_price=1.2036)
    assert ok is True
    assert sup.outcomes_recorded == 1


def test_settlement_attaches_and_dedupes(sup):
    sup.ingest_decision(_obs(), _decision(trade_id="d1"))
    settlement = {"settlement_id": "s1", "decision_id": "d1",
                  "gross_return": 0.005, "cost_return": 0.004,
                  "entry_price": 1.10, "exit_price": 1.105}
    assert sup.ingest_settlement(dict(settlement)) is True
    assert sup.ingest_settlement(dict(settlement)) is False
    assert sup.outcomes_recorded == 1


def test_offline_gates_intel_and_monitors(sup):
    res = sup.on_cycle(SimpleNamespace(), _obs())
    assert res["cycle"] == 1
    assert sup._sentinel is None
    assert sup.online() is None
    assert sup._intel_task is None
    assert sup.connectivity_status()["monitor"] == "unavailable"


def test_audit_outbox_drains(sup, monkeypatch):
    monkeypatch.setattr(evo_mod, "AUDIT_EVERY", 1)
    sup.on_cycle(SimpleNamespace(), _obs())
    audits = sup.drain_audits()
    assert audits and audits[0]["event_type"] == "EVOLUTION"
    assert sup.drain_audits() == []


def test_cadence_schedules_reflect_worker(sup, monkeypatch):
    monkeypatch.setattr(evo_mod, "REFLECT_EVERY", 2)
    sup.ingest_decision(_obs(), _decision())
    res = sup.on_cycle(SimpleNamespace(), _obs())
    res = sup.on_cycle(SimpleNamespace(), _obs())
    assert "reflect" in res["did"]
    _join(sup)
    assert sup.reflections_run == 1
    assert sup._last_learning["kind"] == "reflect"


def test_learn_worker_journals_and_never_applies(sup, monkeypatch):
    from trading_bot.self_mastery.code_evolver import CodeEvolver
    applied = []
    monkeypatch.setattr(CodeEvolver, "apply_modification",
                        lambda self, *a, **k: applied.append(1))
    for i in range(6):
        sup.ingest_decision(
            _obs(), _decision(trade_id=f"t{i}",
                              outcome="EXECUTED" if i % 2 else "ABSTAIN"))
    assert sup._start_worker("learn") is True
    _join(sup)
    assert sup.learning_cycles_run == 1
    rep = sup._last_learning
    assert rep["kind"] == "learn"
    assert "pending_proposals" in rep
    # Proposals are journaled for operator/RSI review — never applied.
    assert applied == []
    journal = sup.data_dir / "evolution_journal.jsonl"
    assert journal.exists()
    lines = [json.loads(l) for l in journal.read_text().splitlines()]
    assert lines[-1]["kind"] == "learn"


def test_one_worker_at_a_time(sup):
    class _Alive:
        def is_alive(self):
            return True
    sup._worker = _Alive()
    assert sup._start_worker("learn") is False


def test_mastery_disabled_env(sup, monkeypatch):
    monkeypatch.setenv("TB_SELF_MASTERY", "0")
    assert sup.ingest_decision(_obs(), _decision()) is None
    assert sup._start_worker("learn") is False
    assert sup.experiences_recorded == 0


def test_ingest_survives_garbage_decision(sup):
    assert sup.ingest_decision(_obs(), object()) is None
    # A failure must not kill the loop — counters stay consistent.
    assert sup.experiences_recorded == 0


def test_report_shape(sup):
    rep = sup.report()
    for key in ("cycles", "external_enabled", "experiences_recorded",
                "outcomes_recorded", "connectivity", "mastery",
                "cadence", "last_security", "last_intel"):
        assert key in rep
    assert rep["external_enabled"] is False
    assert rep["mastery"]["status"] == "not_started"


def test_intel_topics_bounded_and_rotating(sup):
    topics = sup._intel_topics(SimpleNamespace(_self_question=lambda: None))
    assert 1 <= len(topics) <= evo_mod.MAX_INTEL_PER_SWEEP


# -- frontier observation feed ----------------------------------------------

def test_observe_frontier_buffers_and_persists(sup, tmp_path):
    oid = sup.observe_frontier(
        "deepseek", "eval_result",
        summary="DeepSeek V4 posts 92 on MMLU",
        observed_behavior="benchmark eval result page",
        source_uri="https://example.com/ds")
    assert oid
    assert len(sup._frontier_obs["deepseek"]) == 1
    journal = sup.data_dir / "frontier_observations.jsonl"
    assert journal.exists()
    # A fresh supervisor reloads the buffered evidence.
    s2 = EvolutionSupervisor(data_dir=str(tmp_path / "mastery"),
                             external=False)
    s2._load_frontier_journal()
    assert len(s2._frontier_obs["deepseek"]) == 1
    s2.stop()


def test_harvest_frontier_obs_from_intel_entry(sup):
    entry = {
        "web": {"status": "ok", "results": [
            {"title": "Claude benchmark eval results",
             "snippet": "scores on agentic coding", "url": "https://x/a"}]},
        "page": {"url": "https://x/a", "excerpt": "claude eval numbers"}}
    made = sup._harvest_frontier_obs("ai benchmarks", entry)
    assert made == 1
    obs = sup._frontier_obs["claude"][-1]
    assert obs["observation_type"] == "eval_result"
    assert obs["source_uri"] == "https://x/a"


def test_frontier_obs_type_classification():
    f = EvolutionSupervisor._frontier_obs_type
    assert f("new mmlu benchmark results") == "eval_result"
    assert f("major incident and jailbreak report") == "failure_report"
    assert f("api tool use patterns") == "api_behavior"
    assert f("model release announcement") == "model_release"
    assert f("arxiv preprint") == "paper"


class _FakeCsc:
    def __init__(self, fn):
        self.distill_frontier = fn


def test_frontier_distill_fires_at_min_obs(sup, monkeypatch):
    import weakref
    monkeypatch.setattr(evo_mod, "FRONTIER_MIN_OBS", 3)
    calls = []
    def _distill(m, o, t, r):
        calls.append((m, len(o)))
        return {"model": m, "patterns": 1, "artifacts": 0,
                "rejected": []}
    fake = _FakeCsc(_distill)
    sup._csc_ref = weakref.ref(fake)
    for i in range(3):
        sup.observe_frontier("qwen", "paper", f"paper {i}")
    sup._maybe_distill_frontier()
    assert calls == [("qwen", 3)]
    # Same learn window -> no re-run.
    sup._maybe_distill_frontier()
    assert len(calls) == 1


def test_frontier_distill_below_min_skips(sup, monkeypatch):
    import weakref
    monkeypatch.setattr(evo_mod, "FRONTIER_MIN_OBS", 5)
    fake = _FakeCsc(lambda *a: {"ok": True})
    sup._csc_ref = weakref.ref(fake)
    sup.observe_frontier("llama", "paper", "one obs only")
    sup._maybe_distill_frontier()
    assert sup.frontier_runs == 0
