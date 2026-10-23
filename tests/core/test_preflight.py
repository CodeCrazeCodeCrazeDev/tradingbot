"""Preflight self-check tests — session-gate self-validation."""
import pytest


@pytest.fixture
def csc():
    from trading_bot.core.csc.controller import CognitiveSystemController
    CognitiveSystemController._instance = None
    instance = CognitiveSystemController()
    yield instance
    CognitiveSystemController._instance = None


@pytest.mark.asyncio
async def test_preflight_passes_on_healthy_csc(csc):
    report = await csc.preflight_self_check()
    names = {c["check"] for c in report["checks"]}
    assert "end_to_end_decision" in names
    assert "component:shield" in names
    # A healthy default CSC passes component presence; the probe may
    # abstain — that still counts as a valid decision.
    component_fails = [c["check"] for c in report["checks"]
                       if c["check"].startswith("component:")
                       and not c["passed"]]
    assert component_fails == []
    # Optional runtime-injected services are informational, never blocking.
    assert all(not c["check"].startswith("optional:") or c["passed"] or
               c["detail"] == "informational" for c in report["checks"])


@pytest.mark.asyncio
async def test_preflight_probe_never_dispatches_order(csc):
    """The probe runs the full pipeline but the TRADE_EXECUTION order is
    never dispatched — no venue-visible side effects."""
    dispatched = []

    class _Bus:
        async def propose_action(self, action):
            dispatched.append(getattr(action, "action_type", ""))

    class _NoOpAction:  # keep wait_for_decision paths quiet
        pass

    csc.decision_bus = _Bus()
    await csc.preflight_self_check()
    # TRADE_PROPOSAL may fire (bus reachability); TRADE_EXECUTION must not.
    assert "TRADE_EXECUTION" not in dispatched


@pytest.mark.asyncio
async def test_preflight_fails_closed_on_missing_component(csc):
    csc.decision_bus = None
    report = await csc.preflight_self_check()
    assert not report["all_passed"]
    assert "component:decision_bus" in report["blocking"]


@pytest.mark.asyncio
async def test_preflight_persists_audit(csc):
    events = []
    async def _sink(**kw):
        events.append(kw)
    csc._persist_audit_event = _sink
    await csc.preflight_self_check()
    assert any(e.get("event_type") == "PREFLIGHT" for e in events)
