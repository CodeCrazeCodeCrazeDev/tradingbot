"""Focused checks for the canonical-runtime recovery plan."""

from argparse import Namespace

import pytest


class _Service:
    capability_id = "test_advisory"

    async def analyze(self, context):
        return {"direction": "BUY", "confidence": 0.5}


@pytest.mark.asyncio
async def test_cognitive_registration_is_idempotent_and_reports_assembly():
    from trading_bot.core.csc.advisory import attach_advisory_modules
    from trading_bot.core.csc.controller import CognitiveSystemController

    CognitiveSystemController._instance = None
    csc = CognitiveSystemController()
    try:
        first = _Service()
        second = _Service()
        csc.configure_cognition(first)
        csc.configure_cognition(second)
        # CSC self-registers built-in services (e.g. SRE advisory) at
        # init — idempotence means exactly one entry per capability_id.
        same_cap = [s for s in csc._advisory_services
                    if getattr(s, "capability_id", None)
                    == "test_advisory"]
        assert same_cap == [second]

        attach_advisory_modules(csc, factories=(
            ("attach_ok", lambda: _Service()),
            ("attach_bad", lambda: (_ for _ in ()).throw(RuntimeError("bad"))),
        ), probe=False)
        report = csc.advisory_report()
        assert report["assembly"]["attached"] == ["attach_ok"]
        assert report["assembly"]["skipped"] == ["attach_bad"]
    finally:
        CognitiveSystemController._instance = None


@pytest.mark.asyncio
async def test_every_terminal_decision_gets_durable_audit_row():
    from trading_bot.core.alphaalgo_core_engine import (
        CoreDecision, DecisionOutcome)
    from trading_bot.core.csc.controller import CognitiveSystemController

    class Sink:
        def __init__(self):
            self.events = []

        async def record_audit_event(self, event):
            self.events.append(event)
            return "audit-id"

    CognitiveSystemController._instance = None
    csc = CognitiveSystemController()
    sink = Sink()
    csc.configure_decision_sink(sink)

    async def rejected(_observation):
        return CoreDecision(
            outcome=DecisionOutcome.TRADE_REJECTED,
            trade_id="trade-test",
            dominant_rejection_reason="test rejection")

    csc._process_observation_pipeline = rejected
    try:
        decision = await csc.process_market_observation({"symbol": "EURUSD"})
        assert decision.outcome is DecisionOutcome.TRADE_REJECTED
        assert len(sink.events) == 1
        event = sink.events[0]
        assert event.event_type == "DECISION_TERMINAL"
        assert event.outcome == "TRADE_REJECTED"
        assert event.correlation_id == "trade-test"
        assert event.details["dominant_rejection_reason"] == "test rejection"
    finally:
        CognitiveSystemController._instance = None


def test_runtime_canonical_assembly_config(monkeypatch, tmp_path):
    from trading_bot.core.csc import assembly
    from trading_bot.foundation.runtime import ModularMonolithRuntime

    calls = []

    def fake_build(csc, **kwargs):
        calls.append((csc, kwargs))
        return csc

    class FakeCSC:
        def configure_decision_sink(self, sink):
            self.sink = sink

    class FakeBot:
        csc = FakeCSC()
        trading_repository = None
        hms = None
        config = {
            "trading_state_path": str(tmp_path / "trading_state.db"),
            "enable_cognitive_advisory": True,
            "cognitive_assembly": {
                "enabled": True,
                "research_interval": 25,
                "discover_advisors": True,
            },
        }

    monkeypatch.setattr(assembly, "build_cognitive_system", fake_build)
    runtime = ModularMonolithRuntime({})
    runtime.bot = FakeBot()
    runtime._wire_csc_persistence()

    assert calls == [(FakeBot.csc, {
        "research_interval": 25,
        "advisory_brain": True,
        "discover_advisors": True,
    })]


def test_mt5_replay_uses_non_executing_analysis_runtime():
    from scripts import mt5_demo_runner

    args = Namespace(
        replay=3, symbol="EURUSD", timeframe="M15", terminal_path=None,
        auto_approve=True, state_dir="var/test_mt5", strategy_id=None,
        initial_equity=10000.0, research_interval=0,
        current_session=False)
    config = mt5_demo_runner._runtime_config(args)

    assert config["execution_mode"] == "analysis"
    assert config["account_id"] == "mt5_replay"
    # Replay keeps trading_enabled on so approvals produce paper fills
    # (analysis mode -> paper boundary, no venue adapter) — the
    # non-execution guarantee lives in execution_mode, not this flag.
    assert config["trading_enabled"] is True
    assert config["cognitive_assembly"]["enabled"] is True


@pytest.mark.asyncio
async def test_mt5_warmup_seeds_features_without_decision_cycles():
    from scripts import mt5_demo_runner

    class CSC:
        def __init__(self):
            self.seeded = []

        def seed_observation_history(self, symbol, closes):
            self.seeded.append((symbol, closes))

    class Bot:
        def __init__(self):
            self.csc = CSC()
            self._price_window = []

    runtime = Namespace(bot=Bot())
    bars = [{"close": 1.10}, {"close": 1.11}, {"close": 1.12}]

    assert await mt5_demo_runner._seed_warmup(
        runtime, "EURUSD", bars) == 3
    assert runtime.bot.csc.seeded == [("EURUSD", [1.10, 1.11, 1.12])]
    assert runtime.bot._price_window == [1.10, 1.11, 1.12]


def test_mt5_snapshot_reports_advisors_and_replay_boundary():
    from scripts import mt5_demo_runner

    class CSC:
        def advisory_report(self):
            return {"attached": ["a"], "measured": {}}

    class Bot:
        csc = CSC()
        execution_mode = "analysis"
        execution_service = Namespace(adapter=None)

    class Console:
        bot = Bot()

        def control_state(self):
            return {"trading_allowed": True}

    runtime = Namespace(bot=Bot(), ai_stack=None)
    args = Namespace(replay=2, symbol="EURUSD")
    snapshot = mt5_demo_runner._snapshot(
        2, Console(), args, runtime, adapter=None)

    assert snapshot["mode"] == "mt5_replay"
    assert snapshot["execution_mode"] == "analysis"
    assert snapshot["advisors"]["attached"] == ["a"]


@pytest.mark.asyncio
async def test_funnel_report_counts_terminal_outcomes():
    from trading_bot.core.alphaalgo_core_engine import (
        CoreDecision, DecisionOutcome)
    from trading_bot.core.csc.controller import CognitiveSystemController

    CognitiveSystemController._instance = None
    csc = CognitiveSystemController()
    try:
        report = csc.funnel_report()
        assert "observations" in report
        assert "verification_terminal" in report
        assert "directional_proposals" in report

        async def rejected(_observation):
            return CoreDecision(
                outcome=DecisionOutcome.TRADE_REJECTED,
                trade_id="funnel-test",
                dominant_rejection_reason="test veto")

        csc._process_observation_pipeline = rejected
        await csc.process_market_observation({"symbol": "EURUSD"})
        report = csc.funnel_report()
        assert report["terminal_TRADE_REJECTED"] == 1
    finally:
        CognitiveSystemController._instance = None


@pytest.mark.asyncio
async def test_discoloop_projection_does_not_use_process_randomized_hash(
        monkeypatch):
    import builtins
    import numpy as np

    from trading_bot.core.csc.controller import CognitiveSystemController

    # Record rather than raise: a raising patch is still installed when
    # pytest builds the failure report (pathlib hashes internally) and
    # crashes the run with INTERNALERROR; also patch only around the
    # call under test — CSC construction legitimately hashes.
    real_hash = builtins.hash
    hash_calls = []

    def spy_hash(value):
        hash_calls.append(value)
        return real_hash(value)

    CognitiveSystemController._instance = None
    csc = CognitiveSystemController()
    monkeypatch.setattr(builtins, "hash", spy_hash)
    try:
        await csc._run_discoloop_reasoning({
            "symbol": "EURUSD", "price": 1.1, "volume": 1000.0,
            "volatility": 0.01, "sentiment": 0.0})
        assert np.asarray(csc.continuous_state["latent"]).shape == (512,)
        assert not hash_calls, (
            f"process-randomized hash used on {hash_calls!r}")
    finally:
        CognitiveSystemController._instance = None
