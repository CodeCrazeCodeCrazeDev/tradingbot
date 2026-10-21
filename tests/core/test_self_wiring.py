"""Self-wiring supervisor tests — the organism rewires its advisory
electorate by measured evidence; the authority chain is invariant.

Transitions: ATTACHED -> DORMANT on sustained degenerate emits;
DORMANT -> SHADOW on scheduled re-probe; SHADOW -> ATTACHED on measured
graduation; SHADOW -> QUARANTINED on expired probation. Every transition
is an auditable RewireEvent.
"""
import pytest

from trading_bot.core.csc.self_wiring import (
    INVARIANT_IDS, NodeState, SelfWiringSupervisor)


def _sup(**kw):
    defaults = dict(rewire_interval=2, max_shadow=2, demote_after=3,
                    graduate_cycles=3, graduate_substantive=0.4,
                    fail_cycles=5, probe_interval=10)
    defaults.update(kw)
    return SelfWiringSupervisor(**defaults)


class _FakeService:
    def __init__(self, capability_id):
        self.capability_id = capability_id


# ------------------------------------------------------------- lifecycle


def test_degenerate_streak_demotes_to_dormant():
    sup = _sup()
    sup.register("svc_a", _FakeService("svc_a"))
    for _ in range(3):
        sup.observe("svc_a", "degenerate")
    events = sup.reevaluate(cycle=10)
    assert events[0].kind == "demote"
    assert sup.nodes["svc_a"].state == NodeState.DORMANT
    assert events[0].from_state == "attached"


def test_substantive_emits_keep_node_attached():
    sup = _sup()
    sup.register("svc_a", _FakeService("svc_a"))
    for _ in range(10):
        sup.observe("svc_a", "substantive")
    events = sup.reevaluate(cycle=10)
    assert events == []
    assert sup.nodes["svc_a"].state == NodeState.ATTACHED


def test_dormant_reprobes_as_shadow():
    sup = _sup()
    sup.register("svc_a", _FakeService("svc_a"))
    sup.observe("svc_a", "degenerate")
    sup.observe("svc_a", "degenerate")
    sup.observe("svc_a", "degenerate")
    sup.reevaluate(cycle=10)          # -> DORMANT at cycle 10
    events = sup.reevaluate(cycle=25)  # due = 10 + 10 + backoff(5) = 25
    assert any(e.kind == "probe" for e in events)
    assert sup.nodes["svc_a"].state == NodeState.SHADOW
    assert sup.nodes["svc_a"].shadow_cycles == 0


def test_shadow_graduates_on_substantive_share():
    sup = _sup()
    sup.register("svc_x", _FakeService("svc_x"), state=NodeState.SHADOW)
    for _ in range(3):
        sup.observe("svc_x", "substantive")
    events = sup.reevaluate(cycle=5)
    assert events[0].kind == "promote"
    assert sup.nodes["svc_x"].state == NodeState.ATTACHED


def test_shadow_probation_expiry_quarantines():
    sup = _sup()
    sup.register("svc_x", _FakeService("svc_x"), state=NodeState.SHADOW)
    for _ in range(5):
        sup.observe("svc_x", "degenerate")
    events = sup.reevaluate(cycle=5)
    assert events[0].kind == "quarantine"
    assert sup.nodes["svc_x"].state == NodeState.QUARANTINED


def test_shadow_ids_gate_tilt_electorate():
    sup = _sup()
    sup.register("new_svc", _FakeService("new_svc"),
                 state=NodeState.SHADOW)
    sup.register("old_svc", _FakeService("old_svc"))
    assert sup.shadow_ids() == {"new_svc"}


def test_discover_enters_shadow_bounded():
    sup = _sup(max_shadow=2)
    assert sup.discover("n1", _FakeService("n1")) is not None
    assert sup.discover("n2", _FakeService("n2")) is not None
    # Shadow cap reached — third discovery refused, not queued.
    assert sup.discover("n3", _FakeService("n3")) is None
    assert "n3" not in sup.nodes


def test_discovery_is_idempotent():
    sup = _sup()
    sup.discover("n1", _FakeService("n1"))
    assert sup.discover("n1", _FakeService("n1")) is None


# ------------------------------------------------------------- invariants


def test_authority_chain_is_invariant():
    for banned in ("csc", "risk_service", "shield", "governance_gate",
                   "execution_service", "verifier_swarm", "swarm_intelligence"):
        assert banned in INVARIANT_IDS


def test_invariant_registration_refused():
    sup = _sup()
    assert sup.register("risk_service", object()) is None
    assert "risk_service" not in sup.nodes
    assert sup.discover("immutable_shield", object()) is None


def test_probe_backoff_grows_on_quarantine():
    sup = _sup()
    sup.register("svc_q", _FakeService("svc_q"), state=NodeState.SHADOW)
    for _ in range(5):
        sup.observe("svc_q", "degenerate")
    sup.reevaluate(cycle=5)
    assert sup.nodes["svc_q"].probe_backoff > 0


# ------------------------------------------------------------- persistence


def test_wiring_state_persists_and_restores(tmp_path):
    path = tmp_path / "self_wiring.json"
    sup = _sup()
    sup.set_persistence(str(path))
    sup.register("svc_a", _FakeService("svc_a"))
    sup.observe("svc_a", "degenerate")
    sup.observe("svc_a", "degenerate")
    sup.observe("svc_a", "degenerate")
    sup.reevaluate(cycle=10)
    sup._persist()

    restored = SelfWiringSupervisor.load(str(path))
    assert restored.nodes["svc_a"].state == NodeState.DORMANT
    assert restored.nodes["svc_a"].rewires == 1
    assert len(restored.events) == 1


def test_report_is_transparent():
    sup = _sup()
    sup.register("svc_a", _FakeService("svc_a"))
    sup.observe("svc_a", "substantive")
    report = sup.report()
    assert report["by_state"]["attached"] == 1
    assert report["nodes"]["svc_a"]["substantive"] == 1


# ------------------------------------------------- controller integration


@pytest.fixture
def csc(tmp_path):
    from trading_bot.core.csc.controller import CognitiveSystemController
    CognitiveSystemController._instance = None
    instance = CognitiveSystemController()
    yield instance
    CognitiveSystemController._instance = None


def test_csc_constructs_with_supervisor(csc):
    assert isinstance(csc._self_wiring, SelfWiringSupervisor)


def test_configure_cognition_registers_attached(csc):
    svc = _FakeService("test_advisor")
    svc.analyze = lambda ctx: {"evidence": {}}
    csc.configure_cognition(svc)
    node = csc._self_wiring.nodes.get("test_advisor")
    assert node is not None and node.state == NodeState.ATTACHED
    assert node.service is svc


@pytest.mark.asyncio
async def test_rewire_demote_detaches_service(csc):
    svc = _FakeService("degenerate_advisor")
    svc.analyze = lambda ctx: {"evidence": {}}
    csc.configure_cognition(svc)
    node = csc._self_wiring.nodes["degenerate_advisor"]
    node.degenerate_streak = csc._self_wiring.demote_after
    csc._observation_seq = csc._self_wiring.rewire_interval  # due
    await csc._maybe_rewire_electorate()
    assert node.state == NodeState.DORMANT
    assert all(getattr(s, "capability_id", None) != "degenerate_advisor"
               for s in csc._advisory_services)


@pytest.mark.asyncio
async def test_rewire_probe_reattaches_service(csc):
    svc = _FakeService("dormant_advisor")
    svc.analyze = lambda ctx: {"evidence": {}}
    csc.configure_cognition(svc)
    node = csc._self_wiring.nodes["dormant_advisor"]
    # Force dormant state, then let the rewire cycle probe it back.
    node.state = NodeState.DORMANT
    node.last_rewired_cycle = 0
    csc._advisory_services = [
        s for s in csc._advisory_services if s is not svc]
    # Due at probe_interval(40) + last_rewired(0); seq must also be a
    # multiple of rewire_interval(10) for the hook to evaluate.
    csc._observation_seq = 40
    await csc._maybe_rewire_electorate()
    assert node.state == NodeState.SHADOW
    assert svc in csc._advisory_services


@pytest.mark.asyncio
async def test_rewire_events_persist_audit(csc):
    class _Sink:
        def __init__(self):
            self.events = []

        async def record_audit_event(self, e):
            self.events.append(e)
            return "ok"

    sink = _Sink()
    csc.configure_decision_sink(sink)
    svc = _FakeService("bad_advisor")
    svc.analyze = lambda ctx: {"evidence": {}}
    csc.configure_cognition(svc)
    node = csc._self_wiring.nodes["bad_advisor"]
    node.degenerate_streak = csc._self_wiring.demote_after
    csc._observation_seq = csc._self_wiring.rewire_interval
    await csc._maybe_rewire_electorate()
    wired = [e for e in sink.events if e.event_type == "SELF_WIRE"]
    assert wired and wired[0].correlation_id == "bad_advisor"
    assert wired[0].outcome == "attached->dormant"


def test_self_model_report_shape(csc):
    report = csc.self_model_report()
    assert "nodes" in report and "by_state" in report
