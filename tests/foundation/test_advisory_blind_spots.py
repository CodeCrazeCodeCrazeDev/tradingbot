"""Regression tests for advisor-wiring blind spots.

Each test pins a failure mode that was verified in code before the fix:
authority vocabulary nested in lists bypassing the strip, the evidence
plane hiding skipped/disabled advisors, advisor-controlled timeouts and
weights, uncounted advisor exceptions, cross-symbol claim scoring, and
payload artifacts being miscounted as degenerate emits.
"""

import asyncio

import pytest


def _fresh_csc():
    from trading_bot.core.csc.controller import CognitiveSystemController

    CognitiveSystemController._instance = None
    return CognitiveSystemController()


def _done_csc(csc):
    from trading_bot.core.csc.controller import CognitiveSystemController

    CognitiveSystemController._instance = None


class _FakeWiring:
    def __init__(self):
        self.observed = []
        self.outcomes = []

    def observe(self, node_id, status, cycle=0):
        self.observed.append((node_id, status))

    def observe_outcome(self, node_id, hit):
        self.outcomes.append((node_id, hit))


def _stub_consult(csc, artifacts):
    async def fake(_obs):
        return list(artifacts)

    csc._consult_agent_population = fake


def test_strip_authority_recurses_into_lists():
    from trading_bot.cognition.advisory_adapter import (
        AdvisoryCognitiveBrain)

    out = AdvisoryCognitiveBrain._strip_authority({
        "note": "ok",
        "orders": [{"order": "BUY", "quantity": 0.1,
                    "symbol": "EURUSD"}],
        "nested": {"authorized_action": "BUY", "keep": 1},
    })
    assert out["orders"] == [{"symbol": "EURUSD"}]
    assert out["nested"] == {"keep": 1}
    assert out["note"] == "ok"


def test_evidence_plane_surfaces_assembly_disabled_verdicts():
    from trading_bot.ai_stack import AIStack

    class FakeCSC:
        def advisory_report(self):
            return {
                "attached": ["a"],
                "measured": {},
                "assembly": {"attached": ["a"], "skipped": ["b"],
                             "skipped_reasons": {"b": "boom"}},
                "disabled": ["c"],
                "contribution_verdicts": {"a": "measured_positive"},
                "signal_quality": {"advisor_degenerate": 3},
            }

    plane = AIStack(FakeCSC()).evidence_plane()
    assert plane["attached"] == ["a"]
    assert plane["assembly"]["skipped"] == ["b"]
    assert plane["assembly"]["skipped_reasons"] == {"b": "boom"}
    assert plane["disabled"] == ["c"]
    assert plane["contribution_verdicts"]["a"] == "measured_positive"
    assert plane["signal_quality"]["advisor_degenerate"] == 3


@pytest.mark.asyncio
async def test_advisor_timeout_coerced_and_ceiling_enforced():
    csc = _fresh_csc()
    try:
        # A garbage timeout_s used to raise TypeError inside gather and
        # count as a failure; now it coerces to the default budget.
        class NullTimeoutSvc:
            capability_id = "null_timeout"
            timeout_s = None

            async def analyze(self, ctx):
                return {"direction": "BUY"}

        csc.configure_cognition(NullTimeoutSvc())
        artifacts = await csc._consult_agent_population(
            {"symbol": "EURUSD"})
        assert any(a.get("agent") == "null_timeout" for a in artifacts)
        assert "null_timeout" not in csc._advisory_failures

        # A self-declared 1-hour timeout must be clamped to the ceiling —
        # shrink the ceiling so the test doesn't actually wait 10s.
        csc._ADVISORY_TIMEOUT_CEILING_S = 0.05

        class HoggingSvc:
            capability_id = "hogging"
            timeout_s = 3600

            async def analyze(self, ctx):
                await asyncio.sleep(0.5)
                return {"direction": "SELL"}

        csc.configure_cognition(HoggingSvc())
        await csc._consult_agent_population({"symbol": "EURUSD"})
        assert csc._advisory_failures["hogging"] == 1
        assert csc._funnel["advisor_exceptions"] >= 1
    finally:
        _done_csc(csc)


@pytest.mark.asyncio
async def test_advisor_exceptions_increment_funnel():
    csc = _fresh_csc()
    try:
        class BrokenSvc:
            capability_id = "broken"

            async def analyze(self, ctx):
                raise RuntimeError("dead")

        csc.configure_cognition(BrokenSvc())
        await csc._consult_agent_population({"symbol": "EURUSD"})
        assert csc._funnel["advisor_exceptions"] == 1
        assert csc._advisory_failures["broken"] == 1
    finally:
        _done_csc(csc)


@pytest.mark.asyncio
async def test_calls_clamp_confidence_and_evidence_weight():
    csc = _fresh_csc()
    try:
        _stub_consult(csc, [
            {"agent": "a1", "direction": "BUY", "confidence": 9.9,
             "evidence_weight": "junk"},
            {"agent": "a2", "direction": "SELL",
             "confidence": "not-a-number", "evidence_weight": 1e9},
        ])
        await csc._stage_internalization(
            {"symbol": "EURUSD", "price": 1.1})
        calls = {c["capability_id"]: c
                 for c in csc._last_advisory_calls}
        assert calls["a1"]["confidence"] == 1.0
        assert calls["a1"]["evidence_weight"] == 1.0
        assert calls["a2"]["confidence"] is None
        assert calls["a2"]["evidence_weight"] == 1.0
    finally:
        _done_csc(csc)


@pytest.mark.asyncio
async def test_payload_artifacts_are_not_degenerate():
    csc = _fresh_csc()
    try:
        _stub_consult(csc, [
            {"agent": "research_engine", "source": "research:r1",
             "artifact": {"verdict": "x"}, "advisory_only": True},
            {"agent_id": "pca_macro", "type": "market_insight",
             "data": {"regime": "risk_off"}, "timestamp": "t"},
            {"agent": "empty_adv", "advisory_only": True},
        ])
        await csc._stage_internalization(
            {"symbol": "EURUSD", "price": 1.1})
        assert csc._funnel["advisor_substantive"] == 2
        assert csc._funnel["advisor_degenerate"] == 1
        assert "pca_macro" in csc._last_advisory_ids
        assert "research_engine" in csc._last_advisory_ids
    finally:
        _done_csc(csc)


@pytest.mark.asyncio
async def test_pending_claims_resolve_per_symbol():
    csc = _fresh_csc()
    wiring = _FakeWiring()
    csc._self_wiring = wiring
    try:
        _stub_consult(csc, [
            {"agent": "adv1", "direction": "BUY", "confidence": 0.6}])
        await csc._stage_internalization(
            {"symbol": "EURUSD", "price": 1.10})
        assert "adv1" in csc._advisor_dir_pending

        # A different instrument's bar must not score the EURUSD claim.
        _stub_consult(csc, [])
        await csc._stage_internalization(
            {"symbol": "GBPUSD", "price": 0.50})
        assert wiring.outcomes == []
        assert "adv1" in csc._advisor_dir_pending

        await csc._stage_internalization(
            {"symbol": "EURUSD", "price": 1.11})
        assert wiring.outcomes == [("adv1", True)]
        assert "adv1" not in csc._advisor_dir_pending
    finally:
        _done_csc(csc)


@pytest.mark.asyncio
async def test_abstain_opportunity_cost_is_per_symbol():
    csc = _fresh_csc()
    try:
        _stub_consult(csc, [])
        csc._last_obs_close = {"EURUSD": 1.10}
        csc._last_outcome_was_abstain = {"EURUSD": True}

        # GBPUSD's bar must not settle EURUSD's abstain bookkeeping.
        await csc._stage_internalization(
            {"symbol": "GBPUSD", "price": 0.50})
        assert csc._funnel["abstain_opp_cost_sum"] == 0
        assert csc._last_obs_close["EURUSD"] == 1.10
        assert csc._last_obs_close["GBPUSD"] == 0.50

        await csc._stage_internalization(
            {"symbol": "EURUSD", "price": 1.20})
        assert csc._funnel["abstain_opp_cost_sum"] > 0
    finally:
        _done_csc(csc)


@pytest.mark.asyncio
async def test_attach_report_records_skip_reasons():
    from trading_bot.core.csc.advisory import attach_advisory_modules

    csc = _fresh_csc()
    try:
        attach_advisory_modules(csc, factories=(
            ("attach_bad",
             lambda: (_ for _ in ()).throw(RuntimeError("nope"))),
        ), probe=False)
        report = csc.advisory_report()
        assert report["assembly"]["skipped"] == ["attach_bad"]
        assert report["assembly"]["skipped_reasons"] == {
            "attach_bad": "nope"}
    finally:
        _done_csc(csc)
