"""Autonomy manager tests — the organism's operations layer.

Every cycle the manager emits one auditable activity portfolio:
self-question (measured weakness first), research cycle, capability
review, RSI gaps, rewire — gated by health and the shared background
slot. Plus a capability-expansion ledger accounting for every agent
the organism has grown. No capital authority anywhere.
"""
import pytest
from types import SimpleNamespace

from trading_bot.core.csc.autonomy import (
    ACTIVITY_PRIORITY, AutonomyManager)


def _csc_stub(health_score=None, task_done=True, engineered=None,
              wiring_nodes=None, proposals=None):
    """Minimal CSC-shaped stub for the manager's read surface."""
    class _Task:
        def done(self):
            return task_done
    csc = SimpleNamespace()
    csc._observation_seq = 10
    csc._last_self_health = (
        {"score": health_score} if health_score is not None else None)
    csc._research_cycle_task = None if task_done else _Task()
    csc._engineered_models = engineered or {}
    csc._self_wiring = wiring_nodes or SimpleNamespace(nodes={})
    csc.research_engine = SimpleNamespace(
        capability_proposals=lambda: proposals or [])
    csc._self_question = lambda: None
    return csc


def test_tick_decides_all_activities():
    am = AutonomyManager()
    csc = _csc_stub()
    tick = am.tick(csc)
    assert set(d.activity for d in tick.decisions) == set(ACTIVITY_PRIORITY)
    assert tick.cycle == 10


def test_degraded_health_suspends_exploration():
    am = AutonomyManager()
    csc = _csc_stub(health_score=20)
    csc._self_question = lambda: ("why?", [])
    tick = am.tick(csc)
    by_name = {d.activity: d for d in tick.decisions}
    assert not by_name["self_question"].allowed
    assert "health degraded" in by_name["self_question"].reason
    assert not by_name["research_cycle"].allowed
    # Safety-relevant activities stay on even when degraded.
    assert by_name["rewire"].allowed
    assert by_name["capability_review"].allowed


def test_weakness_outranks_research():
    am = AutonomyManager()
    csc = _csc_stub()
    csc._self_question = lambda: ("why did the model degrade?", [])
    tick = am.tick(csc)
    by_name = {d.activity: d for d in tick.decisions}
    assert by_name["self_question"].allowed
    assert "measured weakness" in by_name["self_question"].reason


def test_busy_slot_defers_background_activities():
    am = AutonomyManager()
    csc = _csc_stub(task_done=False)
    tick = am.tick(csc)
    by_name = {d.activity: d for d in tick.decisions}
    assert not by_name["research_cycle"].allowed
    assert "busy" in by_name["research_cycle"].reason


def test_capability_ledger_counts_pipeline():
    am = AutonomyManager()
    c1 = SimpleNamespace(status="ATTACHED")
    c2 = SimpleNamespace(status="ROLLED_BACK")
    sup = SimpleNamespace(nodes={
        "a": SimpleNamespace(state=SimpleNamespace(value="attached")),
        "b": SimpleNamespace(state=SimpleNamespace(value="shadow")),
    })
    csc = _csc_stub(engineered={"c1": c1, "c2": c2},
                    wiring_nodes=sup, proposals=[1, 2])
    ledger = am.capability_ledger(csc)
    assert ledger["candidate_attached"] == 1
    assert ledger["candidate_rolled_back"] == 1
    assert ledger["node_attached"] == 1
    assert ledger["node_shadow"] == 1
    assert ledger["capability_proposals"] == 2


def test_audit_cadence():
    am = AutonomyManager()
    csc = _csc_stub()
    for _ in range(24):
        am.tick(csc)
    assert not am.should_audit()
    am.tick(csc)
    assert am.should_audit()


def test_report_shape():
    am = AutonomyManager()
    am.tick(_csc_stub())
    report = am.report()
    assert report["ticks"] == 1
    assert report["last_tick"]["cycle"] == 10


# ------------------------------------------------- controller integration


@pytest.fixture
def csc(tmp_path):
    from trading_bot.core.csc.controller import CognitiveSystemController
    CognitiveSystemController._instance = None
    instance = CognitiveSystemController()
    yield instance
    CognitiveSystemController._instance = None


def test_csc_constructs_with_autonomy(csc):
    assert isinstance(csc._autonomy, AutonomyManager)


def test_autonomy_tick_records_pipeline(csc):
    tick = csc._autonomy.tick(csc)
    assert tick.cycle == csc._observation_seq
    assert isinstance(tick.capability_pipeline, dict)
    # Every decision carries an explicit reason — auditable, not silent.
    assert all(d.reason for d in tick.decisions)


def test_autonomy_report_surface(csc):
    report = csc.autonomy_report()
    assert "ticks" in report and "activity_counts" in report


def test_capability_review_surfaces_proposals(csc):
    class _Engine:
        def capability_proposals(self):
            return [SimpleNamespace(
                proposal_id="p1", summary="validated momentum claim",
                confidence_profile=SimpleNamespace(level="HIGH"))]
    csc.research_engine = _Engine()
    csc._capability_review()
    assert len(csc._research_artifacts) == 1
    art = csc._research_artifacts[0]
    assert art["agent"] == "capability_proposal"
    assert art["advisory_only"] is True
    # Idempotent — the same proposal doesn't re-enter the channel.
    csc._capability_review()
    assert len(csc._research_artifacts) == 1
