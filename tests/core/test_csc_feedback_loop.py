"""Outcome-feedback and subordinate-cognition wiring tests for the CSC.

Covers the closed learning loop that makes the one-brain architecture
self-measuring instead of self-asserting:

* ``configure_cognition`` registers an advisory service whose output enters
  the evidence channel with ``advisory_only`` provenance — never authority.
* ``configure_decision_sink`` persists every terminal decision as an
  AuditEvent so decisions can be joined to outcomes after restart.
* ``record_outcome`` matches a pending directional prediction against a
  realized move, updates the ReliabilityTracker, and adjusts epistemic
  uncertainty by measured error rather than mechanical decay.
"""

import pytest
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

from trading_bot.core.alphaalgo_core_engine import DecisionOutcome
from trading_bot.core.csc.controller import CognitiveSystemController
from trading_bot.core.hms.models import VerifierReport


class FakeSink:
    """Minimal durable sink matching the repository audit-event contract."""

    def __init__(self):
        self.events = []

    async def record_audit_event(self, event):
        self.events.append(event)
        return f"audit-{len(self.events)}"


class FakeAdvisory:
    capability_id = "fake_advisory"

    def __init__(self):
        self.calls = []

    async def analyze(self, context):
        self.calls.append(dict(context))
        return {"capability_id": self.capability_id,
                "evidence": {"regime": "ranging"}, "advisory_only": True}


@pytest.fixture
def csc(tmp_path):
    CognitiveSystemController._instance = None
    instance = CognitiveSystemController()
    yield instance
    CognitiveSystemController._instance = None


def _obs(**overrides):
    base = {
        "symbol": "EURUSD", "price": 1.0834, "volume": 1.4e6,
        "volatility": 0.001, "trend": "ranging", "rsi": 47.0,
    }
    base.update(overrides)
    return base


class TestAdvisoryCognitionWiring:

    def test_configure_cognition_requires_analyze(self, csc):
        with pytest.raises(TypeError):
            csc.configure_cognition(object())

    def test_configure_cognition_registers_service(self, csc):
        advisory = FakeAdvisory()
        csc.configure_cognition(advisory)
        assert advisory in csc._advisory_services

    @pytest.mark.asyncio
    async def test_advisory_artifact_enters_evidence_channel(self, csc):
        advisory = FakeAdvisory()
        csc.configure_cognition(advisory)

        artifacts = await csc._consult_agent_population(_obs())
        advisory_artifacts = [a for a in artifacts
                              if a.get("agent") == "fake_advisory"]
        assert advisory_artifacts, "advisory output must join the evidence channel"
        assert advisory_artifacts[0]["advisory_only"] is True
        assert advisory.calls, "advisory.analyze() was not consulted"

    @pytest.mark.asyncio
    async def test_advisory_failure_does_not_break_pipeline(self, csc):
        class BrokenAdvisory:
            capability_id = "broken_advisory"

            async def analyze(self, context):
                raise RuntimeError("advisory exploded")

        csc.configure_cognition(BrokenAdvisory())
        artifacts = await csc._consult_agent_population(_obs())
        assert isinstance(artifacts, list)  # pipeline survives


class TestDecisionPersistence:

    def test_configure_decision_sink_requires_record(self, csc):
        with pytest.raises(TypeError):
            csc.configure_decision_sink(object())

    @pytest.mark.asyncio
    async def test_terminal_decisions_are_persisted(self, csc, monkeypatch):
        sink = FakeSink()
        csc.configure_decision_sink(sink)

        # Drive an abstain through the real pipeline end.
        decision = await csc.process_market_observation(_obs())
        assert decision is not None
        assert sink.events, "terminal decision was not persisted durably"
        evt = sink.events[-1]
        assert evt.event_type == "DECISION"
        assert evt.correlation_id == decision.trade_id


class TestOutcomeFeedback:

    @pytest.mark.asyncio
    async def test_unmatched_outcome_is_honest(self, csc):
        result = await csc.record_outcome("nonexistent-trade")
        assert result["status"] == "unmatched"

    @pytest.mark.asyncio
    async def test_correct_prediction_updates_reliability(self, csc):
        csc._pending_predictions["t1"] = {
            "action": "BUY", "symbol": "EURUSD",
            "entry_price": 1.0, "confidence": 0.7, "regime": "bull",
        }
        result = await csc.record_outcome("t1", exit_price=1.01)
        assert result["status"] == "recorded"
        assert result["was_correct"] is True
        assert "csc" in csc.reliability_tracker.metrics
        assert csc.reliability_tracker.metrics["csc"]["bull"].total_predictions == 1

    @pytest.mark.asyncio
    async def test_wrong_prediction_raises_uncertainty(self, csc):
        csc.state.epistemic_uncertainty = 0.5
        csc._pending_predictions["t2"] = {
            "action": "BUY", "symbol": "EURUSD",
            "entry_price": 1.0, "confidence": 0.9, "regime": "bull",
        }
        result = await csc.record_outcome("t2", exit_price=0.98)
        assert result["was_correct"] is False
        # High-confidence miss increases uncertainty; bounded, not mechanical.
        assert csc.state.epistemic_uncertainty > 0.5

    @pytest.mark.asyncio
    async def test_outcome_persists_audit_event(self, csc):
        sink = FakeSink()
        csc.configure_decision_sink(sink)
        csc._pending_predictions["t3"] = {
            "action": "SELL", "symbol": "EURUSD",
            "entry_price": 1.0, "confidence": 0.6, "regime": "bear",
        }
        await csc.record_outcome("t3", exit_price=0.99)
        outcomes = [e for e in sink.events if e.event_type == "DECISION_OUTCOME"]
        assert outcomes and outcomes[0].correlation_id == "t3"
        assert outcomes[0].details["realized_return"] > 0  # SELL gains on drop


class TestLiveOutcomeSettlement:
    """Position-lifetime accounting: an approved directional decision opens
    a position; an opposing decision or the holding horizon closes it; the
    realized entry->exit return is the measured outcome."""

    async def _open(self, csc, action="BUY", symbol="EURUSD", price=1.0,
                    confidence=0.6, regime="bull", trade_id="t-live"):
        await csc._register_directional(
            trade_id, action, symbol, price, confidence, regime)

    @pytest.mark.asyncio
    async def test_position_closes_at_holding_horizon(self, csc):
        csc._observation_seq = 5
        await self._open(csc)
        csc._observation_seq = 5 + csc._position_max_hold
        await csc._settle_pending_predictions(
            {"symbol": "EURUSD", "price": 1.01})
        assert "t-live" not in csc._pending_predictions
        assert "EURUSD" not in csc._open_positions
        m = csc.reliability_tracker.metrics["csc"]["bull"]
        assert m.total_predictions == 1
        assert m.precision > 0  # BUY + price rose -> correct

    @pytest.mark.asyncio
    async def test_position_survives_before_horizon(self, csc):
        csc._observation_seq = 5
        await self._open(csc, trade_id="t-early")
        csc._observation_seq = 6
        await csc._settle_pending_predictions(
            {"symbol": "EURUSD", "price": 1.01})
        assert "t-early" in csc._pending_predictions
        assert "EURUSD" in csc._open_positions

    @pytest.mark.asyncio
    async def test_foreign_symbol_observation_does_not_settle(self, csc):
        csc._observation_seq = 5
        await self._open(csc, action="SELL", symbol="GBPUSD", price=1.3,
                         regime="bear", trade_id="t-gbp")
        csc._observation_seq = 5 + csc._position_max_hold
        await csc._settle_pending_predictions(
            {"symbol": "EURUSD", "price": 1.01})
        assert "t-gbp" in csc._pending_predictions
        assert "GBPUSD" in csc._open_positions

    @pytest.mark.asyncio
    async def test_opposing_decision_reverses_position(self, csc):
        csc._observation_seq = 5
        await self._open(csc, action="BUY", price=1.0, trade_id="t-long")
        # Opposing signal closes the long at the new bar's price.
        await csc._register_directional(
            "t-short", "SELL", "EURUSD", 1.02, 0.7, "bear")
        assert "t-long" not in csc._pending_predictions
        pos = csc._open_positions["EURUSD"]
        assert pos["direction"] == "SELL"
        assert pos["entry_price"] == 1.02
        m = csc.reliability_tracker.metrics["csc"]["bull"]
        assert m.total_predictions == 1
        assert m.precision > 0  # long gained on the move up

    @pytest.mark.asyncio
    async def test_same_direction_extends_position(self, csc):
        csc._observation_seq = 5
        await self._open(csc, trade_id="t-a")
        await csc._register_directional(
            "t-b", "BUY", "EURUSD", 1.01, 0.7, "bull")
        pos = csc._open_positions["EURUSD"]
        assert pos["trade_ids"] == ["t-a", "t-b"]

    @pytest.mark.asyncio
    async def test_close_all_positions_flushes_at_stream_end(self, csc):
        await self._open(csc, trade_id="t-flush")
        realized = await csc.close_all_positions({"EURUSD": 0.98})
        assert realized["EURUSD"] == pytest.approx(-0.02)
        assert not csc._open_positions
        assert "t-flush" not in csc._pending_predictions

    @pytest.mark.asyncio
    async def test_pipeline_advances_observation_sequence(self, csc):
        before = csc._observation_seq
        await csc.process_market_observation(_obs())
        assert csc._observation_seq == before + 1


class TestNetOfCostGate:

    def test_directional_below_cost_downgrades_to_hold(self, csc):
        proposal = {"action": "BUY", "symbol": "EURUSD"}
        branch = SimpleNamespace(branch_id="b1")
        csc._apply_net_of_cost_gate(
            proposal, branch, {"b1": {"expected_value": 0.0002}},
            {"symbol": "EURUSD"})
        assert proposal["action"] == "HOLD"
        assert "insufficient net edge" in proposal["downgraded_reason"]

    def test_directional_beating_cost_survives(self, csc):
        proposal = {"action": "BUY", "symbol": "EURUSD"}
        branch = SimpleNamespace(branch_id="b1")
        # 0.002 EV > 10bps round-trip on default 5bps cost.
        csc._apply_net_of_cost_gate(
            proposal, branch, {"b1": {"expected_value": 0.002}},
            {"symbol": "EURUSD"})
        assert proposal["action"] == "BUY"

    def test_missing_sim_evidence_downgrades(self, csc):
        proposal = {"action": "SELL", "symbol": "EURUSD"}
        branch = SimpleNamespace(branch_id="b1")
        csc._apply_net_of_cost_gate(
            proposal, branch, {"b1": {}}, {"symbol": "EURUSD"})
        assert proposal["action"] == "HOLD"

    def test_non_directional_untouched(self, csc):
        proposal = {"action": "HOLD"}
        branch = SimpleNamespace(branch_id="b1")
        csc._apply_net_of_cost_gate(
            proposal, branch, {"b1": {"expected_value": -1.0}}, {})
        assert proposal["action"] == "HOLD"
        assert "downgraded_reason" not in proposal


class TestOperatorReadSurface:

    @pytest.mark.asyncio
    async def test_decision_journal_projection(self, csc):
        from trading_bot.interfaces.read_models import ModularMonolithReadModel
        runtime = SimpleNamespace(bot=SimpleNamespace(
            csc=csc, trading_repository=None, execution_mode="paper",
            config={}), running=True)
        rm = ModularMonolithReadModel(runtime)
        journal = rm.decision_journal()
        assert journal["available"] is True
        assert "pending_predictions" in journal
        assert "reliability" in journal

    @pytest.mark.asyncio
    async def test_journal_unavailable_without_brain(self):
        from trading_bot.interfaces.read_models import ModularMonolithReadModel
        runtime = SimpleNamespace(bot=SimpleNamespace(csc=None))
        rm = ModularMonolithReadModel(runtime)
        assert rm.decision_journal() == {"available": False}

    @pytest.mark.asyncio
    async def test_explain_decision_joins_audit_and_pending(self, csc):
        from trading_bot.interfaces.read_models import ModularMonolithReadModel

        class _Repo:
            async def list_audit_events(self, correlation_id=None, **kw):
                if correlation_id == "t-x":
                    return [{"event_type": "DECISION", "outcome": "ABSTAIN",
                             "correlation_id": correlation_id}]
                return []

        csc._pending_predictions["t-x"] = {
            "action": "BUY", "entry_price": 1.0, "confidence": 0.6,
            "regime": "bull", "settle_after": 99}
        runtime = SimpleNamespace(bot=SimpleNamespace(
            csc=csc, trading_repository=_Repo()))
        rm = ModularMonolithReadModel(runtime)
        expl = await rm.explain_decision("t-x")
        assert expl["audit_trail"][0]["outcome"] == "ABSTAIN"
        assert expl["pending_prediction"]["action"] == "BUY"

        none = await rm.explain_decision("no-such-trade")
        assert none["status"] == "no_record"
