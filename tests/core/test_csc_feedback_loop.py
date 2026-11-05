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
from trading_bot.core.csc.hypothesis import ReasoningBranch
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
        assert evt.event_type == "DECISION_TERMINAL"
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
        rewards = outcomes[0].details["rewards"]
        assert [r["domain"] for r in rewards] == ["trading", "prediction"]
        assert "missing_costs" in rewards[0]["blockers"]
        assert all(r["advisory_only"] and not r["promotion_eligible"] for r in rewards)
        # No pending prediction remains: a duplicate receipt earns nothing.
        repeated = await csc.record_outcome("t3", exit_price=0.99)
        assert repeated["status"] == "unmatched"
        assert len([e for e in sink.events if e.event_type == "DECISION_OUTCOME"]) == 1


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
        # Horizon counts own-symbol bars — each settle call is one bar,
        # not a seq jump (multi-symbol feeds advance seq Nx per bar).
        for _ in range(csc._position_max_hold):
            csc._observation_seq += 1
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
    async def test_close_dispatches_ledger_order_and_settles_at_fill(self, csc):
        """With an execution service wired, a horizon close must dispatch a
        real opposing order through the bus and settle at the actual fill
        price — the mark is not the exit."""
        from trading_bot.core.unified_event_bus import ActionStatus

        class FakeBus:
            def __init__(self):
                self.actions = []
            async def propose_action(self, action):
                self.actions.append(action)
                action.status = ActionStatus.EXECUTED

        class FakeAdapter:
            def __init__(self, qty, fill_price):
                from trading_bot.foundation.contracts import (
                    Fill, Instrument, InstrumentType, OrderSide,
                    OrderStatus, ExecutionReport)
                self._qty = qty
                self._fill_price = fill_price
                self._I, self._S, self._R = Instrument, OrderSide, ExecutionReport
            async def get_positions(self):
                inst = self._I("EURUSD", InstrumentType.SYNTHETIC, "paper")
                return [SimpleNamespace(instrument=inst, quantity=self._qty)]
            async def get_order(self, client_order_id):
                from trading_bot.foundation.contracts import (
                    Fill, Instrument, InstrumentType, OrderSide,
                    OrderStatus, ExecutionReport)
                inst = Instrument("EURUSD", InstrumentType.SYNTHETIC, "paper")
                fill = Fill(client_order_id=client_order_id,
                            venue_order_id="v", instrument=inst,
                            side=OrderSide.BUY, quantity=1.0,
                            price=self._fill_price)
                return ExecutionReport(client_order_id=client_order_id,
                                       status=OrderStatus.FILLED,
                                       fills=[fill])

        bus = FakeBus()
        csc.decision_bus = bus
        csc.execution_service = SimpleNamespace(
            adapter=FakeAdapter(qty=-2.0, fill_price=1.015))
        csc._observation_seq = 5
        await self._open(csc, action="SELL", price=1.0)
        for _ in range(csc._position_max_hold):
            csc._observation_seq += 1
            await csc._settle_pending_predictions(
                {"symbol": "EURUSD", "price": 1.01})
        # Close went through the bus as a position-close order
        assert any(a.payload.get("intent") == "position_close"
                   for a in bus.actions)
        # Position settled at the actual fill, not the mark
        settled = list(csc._settled_outcomes)
        assert settled[-1]["exit_price"] == 1.015
        assert settled[-1]["settled_at_fill"] is True
        # SELL entry at 1.0, filled exit at 1.015 -> realized = -0.015
        assert settled[-1]["realized_return"] == pytest.approx(-0.015)
        assert "EURUSD" not in csc._open_positions

    @pytest.mark.asyncio
    async def test_close_payload_carries_no_quantity(self, csc):
        """A position_close resolves size from the ledger at the bridge —
        sending quantity=0.0 trips the shield's quantity sanity veto and
        every close dies at consensus while the brain thinks it settled."""
        from trading_bot.core.unified_event_bus import ActionStatus

        captured = []

        class CaptureBus:
            async def propose_action(self, action):
                captured.append(action)
                action.status = ActionStatus.EXECUTED
                action._completed_event.set()

        csc.decision_bus = CaptureBus()
        csc.execution_service = SimpleNamespace(adapter=None)
        csc._observation_seq = 5
        await self._open(csc, action="BUY", price=1.0)
        await csc._close_position("EURUSD", 1.01, reason="stream_end")
        closes = [a for a in captured
                  if a.payload.get("intent") == "position_close"]
        assert closes, "close never dispatched to the bus"
        assert closes[0].payload.get("quantity") is None

    @pytest.mark.asyncio
    async def test_real_shield_approves_position_close(self, csc):
        """The real ImmutableShield must approve a close-intent payload —
        exit intents are already exempt from entry guards; only a bogus
        quantity was vetoing them."""
        from trading_bot.core.immutable_shield import (
            ImmutableShield, GovernanceDecision)

        shield = ImmutableShield()
        report = await shield.validate_action(
            "TRADE_EXECUTION",
            {"symbol": "EURUSD", "action": "CLOSE",
             "price": 1.01, "trade_id": "close-x",
             "intent": "position_close", "reason": "stream_end"},
            {"market": {}})
        assert report.decision == GovernanceDecision.APPROVED

    @pytest.mark.asyncio
    async def test_vetoed_close_keeps_position_open(self, csc):
        """A close order that fails must NOT mark the position settled —
        the ledger still holds exposure."""
        from trading_bot.core.unified_event_bus import ActionStatus

        class FakeBus:
            async def propose_action(self, action):
                action.status = ActionStatus.VETOED

        csc.decision_bus = FakeBus()
        csc.execution_service = SimpleNamespace(adapter=None)
        csc._observation_seq = 5
        await self._open(csc, action="BUY", price=1.0)
        csc._observation_seq = 5 + csc._position_max_hold
        await csc._settle_pending_predictions(
            {"symbol": "EURUSD", "price": 1.01})
        # Position stayed open — close was rejected, ledger exposure real
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
        # 0.002 EV > 10bps round-trip on default 5bps cost. The gate
        # compares CALIBRATED EV — seed realized evidence at par so
        # calibration stops shrinking the simulated value.
        for _ in range(csc._ev_min_samples):
            csc._ev_pairs.append((0.002, 0.002, "ranging"))
        csc._apply_net_of_cost_gate(
            proposal, branch, {"b1": {"expected_value": 0.002}},
            {"symbol": "EURUSD"})
        assert proposal["action"] == "BUY"

    def test_directional_beating_cost_downgrades_without_evidence(self, csc):
        # Cold prior: with no realized EV pairs the sim's raw edge is
        # deliberately not trusted — an uncalibrated 'beating-cost'
        # proposal still downgrades (except the deliberate trickle
        # probe every Nth call).
        proposal = {"action": "BUY", "symbol": "EURUSD"}
        branch = SimpleNamespace(branch_id="b1")
        csc._apply_net_of_cost_gate(
            proposal, branch, {"b1": {"expected_value": 0.002}},
            {"symbol": "EURUSD"})
        assert proposal["action"] == "HOLD"
        assert "insufficient net edge" in proposal["downgraded_reason"]

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


def _explore_branch(branch_id, action, quantity=1.0, confidence=0.8,
                    probability=0.5, uncertainty=0.1):
    return ReasoningBranch(
        branch_id=branch_id,
        name=branch_id,
        confidence=confidence,
        probability=probability,
        uncertainty=uncertainty,
        execution_plan={
            "action": action,
            "symbol": "EURUSD",
            "quantity": quantity,
        })


class TestExploreProbe:
    """Bounded exploration (TB_CSC_EXPLORE_BUDGET) must promote a
    directional probe only when the electorate's winner is nondirectional,
    cap its size, bypass ONLY the net-cost gate, and spend budget solely
    at approval — risk, shield, governance, and consensus still gate it."""

    @staticmethod
    def _synthesize(csc, winner, sim_results, branches, trade_id="t-x"):
        return csc._stage_synthesis(
            winner, sim_results, trade_id, _obs(), branches=branches)

    def test_budget_off_keeps_hold_winner(self, csc):
        csc._explore_budget = 0
        hold = _explore_branch("branch_hold", "HOLD")
        bull = _explore_branch("branch_bull", "BUY")
        proposal = self._synthesize(
            csc, hold,
            {"branch_hold": {}, "branch_bull": {"expected_value": 0.01}},
            [hold, bull])
        assert proposal["action"] == "HOLD"
        assert proposal["quantity"] == 0.0
        assert csc._funnel.get("explore_probes", 0) == 0

    def test_probe_promotes_directional_and_caps_size(self, csc):
        csc._explore_budget = 2
        hold = _explore_branch("branch_hold", "HOLD")
        bull = _explore_branch(
            "branch_bull", "BUY", confidence=0.9, probability=0.6)
        bear = _explore_branch(
            "branch_bear", "SELL", confidence=0.5, probability=0.3)
        proposal = self._synthesize(
            csc, hold,
            {"branch_hold": {},
             "branch_bull": {"expected_value": 0.005},
             "branch_bear": {"expected_value": 0.004}},
            [hold, bull, bear])
        assert proposal["action"] == "BUY"
        assert proposal["exploratory"] is True
        assert proposal["quantity"] == pytest.approx(csc._explore_factor)
        # Audit join: the folded ledger entry is the verified winner's;
        # the proposal records which branch was actually promoted.
        assert proposal["verified_winner_id"] == "branch_hold"
        assert proposal["promoted_branch_id"] == "branch_bull"
        assert csc._funnel["explore_probes"] == 1
        # Budget is spent at approval, not at proposal time — a gated
        # probe must not consume allowance it never used.
        assert csc._explore_budget == 2

    def test_probe_prefers_nonnegative_sim_ev(self, csc):
        csc._explore_budget = 2
        hold = _explore_branch("branch_hold", "HOLD")
        # Higher score but negative sim EV -> the lower-scored
        # non-negative-EV candidate wins promotion.
        bear = _explore_branch(
            "branch_bear", "SELL", confidence=0.95, probability=0.9)
        bull = _explore_branch(
            "branch_bull", "BUY", confidence=0.5, probability=0.4)
        proposal = self._synthesize(
            csc, hold,
            {"branch_hold": {},
             "branch_bear": {"expected_value": -0.5},
             "branch_bull": {"expected_value": 0.0}},
            [hold, bear, bull])
        assert proposal["action"] == "BUY"
        assert proposal["exploratory"] is True

    def test_no_directional_candidate_keeps_hold(self, csc):
        csc._explore_budget = 2
        hold = _explore_branch("branch_hold", "HOLD")
        rng = _explore_branch("branch_range", "WAIT")
        proposal = self._synthesize(
            csc, hold, {"branch_hold": {}, "branch_range": {}},
            [hold, rng])
        assert proposal["action"] == "HOLD"
        assert csc._funnel.get("explore_probes", 0) == 0

    def test_directional_winner_not_retagged_exploratory(self, csc):
        csc._explore_budget = 2
        # Moderate measured confidence so sizing survives the epistemic-
        # uncertainty shrink — otherwise the (pre-existing) qty<=0 trap
        # escape marks even a directional winner exploratory.
        csc.state.epistemic_uncertainty = 0.5
        # Seed realized EV pairs at par so the net-cost gate's calibration
        # passes a genuine directional proposal through unchanged.
        for _ in range(csc._ev_min_samples):
            csc._ev_pairs.append((0.005, 0.005, "ranging"))
        bull = _explore_branch("branch_bull", "BUY")
        proposal = self._synthesize(
            csc, bull, {"branch_bull": {"expected_value": 0.005}},
            [bull])
        assert proposal["action"] == "BUY"
        assert proposal["exploratory"] is False
        assert 0.0 < proposal["quantity"] <= 1.0
        # The promotion path only fires for a nondirectional winner.
        assert csc._funnel.get("explore_probes", 0) == 0

    def test_exploratory_bypasses_net_cost_gate_only(self, csc):
        proposal = {"action": "BUY", "symbol": "EURUSD",
                    "exploratory": True}
        branch = SimpleNamespace(branch_id="b1")
        csc._apply_net_of_cost_gate(
            proposal, branch, {"b1": {"expected_value": -1.0}}, _obs())
        assert proposal["action"] == "BUY"  # not downgraded to HOLD
        assert proposal["net_cost_bypass"] == "exploration"
        assert csc._funnel["net_cost_explore_bypass"] == 1

    @pytest.mark.asyncio
    async def test_risk_gate_still_rejects_probe(self, csc):
        class DenyRisk:
            async def evaluate_action(self, proposal, obs):
                return SimpleNamespace(
                    approved=False, reason="exposure limit hit")

        csc.risk_engine = DenyRisk()
        proposal = {"action": "BUY", "symbol": "EURUSD", "quantity": 0.1,
                    "exploratory": True, "trade_id": "t-risk"}
        terminal, _ = await csc._stage_risk_check(
            proposal, _obs(), "t-risk")
        assert terminal is not None
        assert terminal.decision.outcome == DecisionOutcome.TRADE_REJECTED
        assert "Risk" in terminal.decision.dominant_rejection_reason

    @pytest.mark.asyncio
    async def test_shield_gate_still_rejects_probe(self, csc):
        class VetoShield:
            async def validate_action(self, kind, proposal, context):
                return SimpleNamespace(
                    decision="VETOED", reason="shield veto")

        csc.shield = VetoShield()
        proposal = {"action": "BUY", "symbol": "EURUSD", "quantity": 0.1,
                    "exploratory": True, "trade_id": "t-shield"}
        terminal = await csc._stage_shield(proposal, _obs())
        assert terminal is not None
        assert terminal.decision.outcome == DecisionOutcome.TRADE_REJECTED
        assert "Shield" in terminal.decision.dominant_rejection_reason

    @pytest.mark.asyncio
    async def test_governance_gate_still_rejects_probe(self, csc):
        class DenyGate:
            async def authorize(self, action, payload, context):
                return SimpleNamespace(
                    approved=False, reason="operator denied")

        csc._governance_gate_resolved = True
        csc.governance_gate = DenyGate()
        proposal = {"action": "BUY", "symbol": "EURUSD", "quantity": 0.1,
                    "exploratory": True, "trade_id": "t-gov"}
        terminal = await csc._stage_governance(
            proposal, _obs(), None, "t-gov")
        assert terminal is not None
        assert terminal.decision.outcome == DecisionOutcome.TRADE_REJECTED
        assert "Governance" in terminal.decision.dominant_rejection_reason

    @pytest.mark.asyncio
    async def test_approved_probe_spends_budget_and_opens_position(
            self, csc):
        from trading_bot.core.unified_event_bus import ActionStatus

        class ApproveBus:
            async def propose_action(self, action):
                action.status = ActionStatus.EXECUTED
                action._completed_event.set()

        csc.decision_bus = ApproveBus()
        csc._explore_budget = 1
        hold = _explore_branch("branch_hold", "HOLD")
        bull = _explore_branch("branch_bull", "BUY")
        proposal = self._synthesize(
            csc, hold,
            {"branch_hold": {}, "branch_bull": {"expected_value": 0.005}},
            [hold, bull], trade_id="t-spend")
        ledger = csc._create_ledger_entry(
            bull, {"expected_value": 0.005})
        decision = await csc._stage_execute_and_persist(
            ledger, proposal, "t-spend", _obs())
        assert decision.outcome == DecisionOutcome.TRADE_APPROVED
        assert csc._explore_budget == 0
        assert csc._funnel["exploratory_trades"] == 1
        # A real pending prediction opened — the outcome feedback loop
        # now has measurable fill to settle against.
        assert "t-spend" in csc._pending_predictions

    @pytest.mark.asyncio
    async def test_vetoed_probe_keeps_budget_and_no_position(self, csc):
        from trading_bot.core.unified_event_bus import ActionStatus

        class VetoBus:
            async def propose_action(self, action):
                action.status = ActionStatus.VETOED
                action._completed_event.set()

        csc.decision_bus = VetoBus()
        csc._explore_budget = 1
        hold = _explore_branch("branch_hold", "HOLD")
        bull = _explore_branch("branch_bull", "BUY")
        proposal = self._synthesize(
            csc, hold,
            {"branch_hold": {}, "branch_bull": {"expected_value": 0.005}},
            [hold, bull], trade_id="t-veto")
        ledger = csc._create_ledger_entry(
            bull, {"expected_value": 0.005})
        decision = await csc._stage_execute_and_persist(
            ledger, proposal, "t-veto", _obs())
        assert decision.outcome == DecisionOutcome.TRADE_REJECTED
        assert csc._explore_budget == 1  # vetoed probe spends nothing
        assert csc._funnel.get("exploratory_trades", 0) == 0
        assert "t-veto" not in csc._pending_predictions
        assert "EURUSD" not in csc._open_positions

    @pytest.mark.asyncio
    async def test_pipeline_probe_count_never_exceeds_budget(self, csc):
        """End-to-end: drive the real pipeline past warmup with budget=2.
        Whatever path each cycle takes, approved exploratory trades are
        bounded by the budget and each approval opens exactly one
        measurable position/prediction."""
        from trading_bot.core.unified_event_bus import ActionStatus

        class ApproveBus:
            async def propose_action(self, action):
                action.status = ActionStatus.EXECUTED
                action._completed_event.set()

        csc.decision_bus = ApproveBus()
        csc._explore_budget = 2
        price = 1.08
        for i in range(18):
            price *= 1.0004 if i % 4 else 0.9996
            await csc.process_market_observation(
                _obs(price=round(price, 5), volatility=0.001,
                     trend="bull" if i % 4 else "ranging"))
        approved = csc._funnel.get("exploratory_trades", 0)
        assert approved <= 2, "approved probes exceeded the explore budget"
        # Budget bookkeeping is exact: each approved probe spent exactly
        # one unit; gated/vetoed probes spent nothing.
        assert csc._explore_budget == 2 - approved
        # Promotion precedes approval — a probe can't trade unpromoted.
        assert csc._funnel.get("explore_probes", 0) >= approved
        # Approved probes fed the outcome loop: same-direction probes
        # share one position/outcome by design, so at least one
        # measurable artifact must exist whenever any probe was approved.
        n_artifacts = (len(csc._pending_predictions)
                       + len(csc._settled_outcomes)
                       + len(csc._open_positions))
        assert (approved == 0) or n_artifacts >= 1
