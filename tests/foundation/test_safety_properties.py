"""Canonical fail-closed safety properties.

Locks the first-principles audit's core invariants:

- no verdicts / low consensus / high-confidence veto -> evidence gate REJECTS
- missing portfolio state -> risk service REJECTS
- any single limit breach -> risk service REJECTS
- kill switch / oversized quantity / excessive drawdown -> shield BLOCKS
- live execution is opt-in only; it fails loudly, never degrades to paper
- approving paths still approve (rejections are not vacuous)
"""

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from trading_bot.core.verification.interface import VerifierVerdict
from trading_bot.core.verification.swarm import EvidenceGraphGate
from trading_bot.core.execution_bridge import (
    BrokerExecutionBridge,
    PaperExecutionBridge,
    make_execution_bridge,
)
from trading_bot.core.immutable_shield import (
    GovernanceDecision,
    ImmutableShield,
)
from trading_bot.foundation.contracts import (
    DecisionProposal,
    Instrument,
    InstrumentType,
    PortfolioSnapshot,
    RiskState,
    Signal,
)
from trading_bot.risk.service import CanonicalRiskService


# ---------------------------------------------------------------------------
# Evidence gate — verification is a hard prerequisite
# ---------------------------------------------------------------------------

def _verdict(valid=True, confidence=0.9, critique="ok"):
    return VerifierVerdict(
        agent_name="test-agent",
        is_valid=valid,
        confidence=confidence,
        critique=critique,
    )


def _populated_graph(nodes=5, edges=3):
    return SimpleNamespace(
        nodes={f"n{i}": {"node_id": f"n{i}"} for i in range(nodes)},
        edges=[{"source_id": "a", "target_id": "b"} for _ in range(edges)],
    )


def test_empty_verdicts_rejected():
    assert EvidenceGraphGate.verify_evidence_first(None, []) is False
    assert "verdicts" in EvidenceGraphGate.last_rejection_reason.lower()


def test_low_consensus_rejected():
    verdicts = [_verdict(valid=True)] * 3 + [_verdict(valid=False)] * 2
    assert EvidenceGraphGate.verify_evidence_first(None, verdicts) is False


def test_exactly_80pct_passes_consensus_but_veto_still_fires():
    verdicts = [_verdict(valid=True)] * 4 + [_verdict(valid=False, confidence=0.9)]
    assert EvidenceGraphGate.verify_evidence_first(None, verdicts) is False
    assert "veto" in EvidenceGraphGate.last_rejection_reason.lower()


def test_mock_critique_does_not_crash_gate():
    verdicts = [_verdict(valid=True)] * 2 + [
        VerifierVerdict(agent_name="m", is_valid=False, confidence=0.9,
                        critique=MagicMock())
    ]
    assert EvidenceGraphGate.verify_evidence_first(None, verdicts) is False


def test_non_numeric_confidence_does_not_crash_gate():
    verdicts = [_verdict(valid=True)] * 4 + [
        VerifierVerdict(agent_name="x", is_valid=False, confidence="high",
                        critique="bad")
    ]
    # consensus fails first (1/5 invalid) — the point is no TypeError
    assert EvidenceGraphGate.verify_evidence_first(None, verdicts) is False


def test_sufficient_evidence_approves():
    snapshot = SimpleNamespace(evidence_graph_snapshot=_populated_graph())
    verdicts = [_verdict(valid=True)] * 5
    assert EvidenceGraphGate.verify_evidence_first(snapshot, verdicts) is True


def test_thin_evidence_graph_rejected():
    snapshot = SimpleNamespace(evidence_graph_snapshot=_populated_graph(nodes=4, edges=2))
    verdicts = [_verdict(valid=True)] * 5
    assert EvidenceGraphGate.verify_evidence_first(snapshot, verdicts) is False


# ---------------------------------------------------------------------------
# Canonical risk service — every limit is a hard check
# ---------------------------------------------------------------------------

def _healthy_state(**overrides):
    base = dict(
        account_id="acct",
        equity=100_000.0,
        portfolio_exposure=0.01,
        daily_pnl=0.0,
        drawdown_fraction=0.0,
        open_positions=0,
        data_is_fresh=True,
        trading_enabled=True,
        emergency=False,
    )
    base.update(overrides)
    return RiskState(**base)


def _proposal(quantity=1.0, direction="buy"):
    inst = Instrument("EURUSD", InstrumentType.FX, "paper")
    signal = Signal(
        signal_id="sig-1", instrument=inst, direction=direction,
        confidence=0.8, metadata={"quantity": quantity},
    )
    portfolio = PortfolioSnapshot(account_id="acct", equity=100_000.0, cash=99_000.0)
    return DecisionProposal(
        decision_id="d-1", signal=signal, portfolio=portfolio,
        risk_state=_healthy_state(),
    )


@pytest.mark.asyncio
async def test_risk_approves_clean_state():
    svc = CanonicalRiskService()
    decision = await svc.evaluate(_proposal(), _healthy_state())
    assert decision.approved is True
    assert decision.approved_quantity == 1.0


@pytest.mark.asyncio
@pytest.mark.parametrize("field,bad_value", [
    ("drawdown_fraction", 0.30),          # > 0.25 default cap
    ("daily_pnl", -10_000.0),             # beyond 5% daily loss
    ("portfolio_exposure", 0.20),         # > 0.05 cap
    ("open_positions", 11),               # > 10 cap
    ("trading_enabled", False),
    ("data_is_fresh", False),
    ("emergency", True),
])
async def test_risk_each_limit_rejects(field, bad_value):
    svc = CanonicalRiskService()
    decision = await svc.evaluate(_proposal(), _healthy_state(**{field: bad_value}))
    assert decision.approved is False
    assert decision.approved_quantity == 0.0


@pytest.mark.asyncio
async def test_risk_rejects_zero_and_negative_quantity():
    svc = CanonicalRiskService()
    for q in (0.0, -1.0):
        decision = await svc.evaluate(_proposal(quantity=q), _healthy_state())
        assert decision.approved is False


@pytest.mark.asyncio
async def test_risk_rejects_hold_direction():
    svc = CanonicalRiskService()
    decision = await svc.evaluate(_proposal(direction="hold"), _healthy_state())
    assert decision.approved is False


@pytest.mark.asyncio
async def test_risk_fails_closed_when_state_provider_broken():
    def broken_provider(obs):
        raise RuntimeError("db down")

    svc = CanonicalRiskService(state_provider=broken_provider)
    decision = await svc.evaluate_action(
        {"trade_id": "t1", "quantity": 1.0}, {}
    )
    assert decision.approved is False
    assert decision.approved_quantity == 0.0
    assert "unavailable" in decision.reason.lower()


@pytest.mark.asyncio
async def test_risk_fails_closed_when_policy_raises():
    class ExplodingPolicy:
        def evaluate(self, proposal, state):
            raise RuntimeError("policy blew up")

    svc = CanonicalRiskService(policies={"exploding": ExplodingPolicy()})
    decision = await svc.evaluate(_proposal(), _healthy_state())
    assert decision.approved is False
    assert "failed closed" in decision.reason


# ---------------------------------------------------------------------------
# Immutable shield — last gate cannot be bypassed
# ---------------------------------------------------------------------------

@pytest.fixture
def fresh_shield():
    ImmutableShield._instance = None
    yield
    ImmutableShield._instance = None


@pytest.mark.asyncio
async def test_shield_kill_switch(fresh_shield):
    shield = ImmutableShield({"trading_enabled": False})
    report = await shield.validate_action("trade", {"quantity": 1.0}, {})
    assert report.decision == GovernanceDecision.BLOCKED


@pytest.mark.asyncio
async def test_shield_approves_clean_action(fresh_shield):
    shield = ImmutableShield({})
    report = await shield.validate_action(
        "trade", {"quantity": 1.0, "confidence": 0.8}, {}
    )
    assert report.decision == GovernanceDecision.APPROVED


@pytest.mark.asyncio
async def test_shield_blocks_oversized_quantity(fresh_shield):
    shield = ImmutableShield({"max_quantity": 5.0})
    report = await shield.validate_action("trade", {"quantity": 50.0}, {})
    assert report.decision == GovernanceDecision.BLOCKED


@pytest.mark.asyncio
async def test_shield_blocks_excessive_drawdown(fresh_shield):
    shield = ImmutableShield({"max_drawdown": 0.15})
    report = await shield.validate_action(
        "trade", {"quantity": 1.0, "confidence": 0.8},
        {"portfolio": {"drawdown": 0.20}},
    )
    assert report.decision == GovernanceDecision.BLOCKED


@pytest.mark.asyncio
async def test_shield_blocks_stale_market_data(fresh_shield):
    shield = ImmutableShield({})
    report = await shield.validate_action(
        "trade", {"quantity": 1.0, "confidence": 0.8},
        {"market": {"data_is_fresh": False}},
    )
    assert report.decision == GovernanceDecision.BLOCKED


@pytest.mark.asyncio
async def test_shield_blocks_non_whitelisted_action(fresh_shield):
    shield = ImmutableShield({"allowed_actions": ["read"]})
    report = await shield.validate_action("trade", {"quantity": 1.0}, {})
    assert report.decision == GovernanceDecision.REJECTED


@pytest.mark.asyncio
async def test_shield_extreme_volatility_only_exits(fresh_shield):
    shield = ImmutableShield({})
    ctx = {"market": {"regime": "EXTREME_VOLATILITY"}}
    entry = await shield.validate_action(
        "trade", {"quantity": 1.0, "confidence": 0.8, "action": "enter"}, ctx
    )
    assert entry.decision == GovernanceDecision.BLOCKED
    exit_ = await shield.validate_action(
        "trade", {"quantity": 1.0, "confidence": 0.8, "action": "exit"}, ctx
    )
    assert exit_.decision == GovernanceDecision.APPROVED


def test_evolution_gate_requires_strict_gain(fresh_shield):
    shield = ImmutableShield({})
    assert shield.check_evolution_gate(1.00, 1.01) is False   # below 2% gain
    assert shield.check_evolution_gate(1.00, 1.03) is True    # above 2% gain


# ---------------------------------------------------------------------------
# Execution boundary — paper by default, live is loud-or-nothing
# ---------------------------------------------------------------------------

def test_execution_defaults_to_paper(tmp_path):
    bridge = make_execution_bridge(persist_path=str(tmp_path / "fills.jsonl"))
    assert isinstance(bridge, PaperExecutionBridge)


def test_execution_unknown_mode_raises(tmp_path):
    with pytest.raises(ValueError):
        make_execution_bridge("live", persist_path=str(tmp_path / "f.jsonl"))


def test_execution_broker_mode_requires_broker(tmp_path):
    with pytest.raises(ValueError):
        make_execution_bridge("broker", broker=None)


def test_execution_broker_mode_requires_place_order(tmp_path):
    with pytest.raises(ValueError):
        BrokerExecutionBridge(broker=object())
