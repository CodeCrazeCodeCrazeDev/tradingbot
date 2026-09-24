"""Tests for Wave-2 risk and governance policy adapters."""

import pytest

from trading_bot.foundation import (
    DecisionProposal,
    Instrument,
    InstrumentType,
    PortfolioSnapshot,
    RiskState,
    Signal,
)
from trading_bot.governance.policy_adapter import HumanApprovalPolicy
from trading_bot.risk.service import CanonicalRiskService, LegacyRiskPolicyAdapter


def proposal() -> DecisionProposal:
    instrument = Instrument("EURUSD", InstrumentType.FX, "paper")
    signal = Signal("signal-1", instrument, "buy", 0.9, metadata={"quantity": 1.0})
    state = RiskState("account-1", 10000, 0.01, 0.0, 0.01, 0)
    return DecisionProposal("decision-1", signal, PortfolioSnapshot("account-1", 10000, 10000), state)


@pytest.mark.asyncio
async def test_subordinate_risk_policy_can_veto_but_not_approve_alone() -> None:
    class Veto:
        async def evaluate(self, _proposal, _state):
            return {"approved": False, "reason": "legacy liquidity veto"}

    service = CanonicalRiskService()
    service.register_policy("legacy_liquidity", LegacyRiskPolicyAdapter("legacy_liquidity", Veto()))
    result = await service.evaluate(proposal(), proposal().risk_state)

    assert result.approved is False
    assert result.reason == "legacy liquidity veto"
    assert result.checks["policy_legacy_liquidity"] is False


@pytest.mark.asyncio
async def test_human_approval_policy_fails_closed_when_rejected() -> None:
    class Gate:
        def is_action_forbidden(self, _action):
            return False

        def is_approval_required(self, _action):
            return True

        async def request_approval(self, *args, **kwargs):
            return False

    result = await HumanApprovalPolicy(Gate()).authorize(
        "apply_evolution", {"genome_id": "g1"}, {"risk_assessment": "HIGH"}
    )

    assert result.approved is False
    assert "rejected" in result.reason.lower()


@pytest.mark.asyncio
@pytest.mark.asyncio
async def test_legacy_pre_trade_check_shape_becomes_veto_policy() -> None:
    from types import SimpleNamespace

    class LegacyChecks:
        def run_all_checks(self, order, portfolio):
            assert order["symbol"] == "EURUSD"
            assert portfolio["equity"] == 10000
            return [SimpleNamespace(result=SimpleNamespace(value="approved"), reason="")]

    result = await LegacyRiskPolicyAdapter("pre_trade", LegacyChecks()).evaluate(
        proposal(), proposal().risk_state
    )

    assert result["approved"] is True


@pytest.mark.asyncio
async def test_human_approval_policy_blocks_forbidden_actions() -> None:
    class Gate:
        def is_action_forbidden(self, _action):
            return True

        def is_approval_required(self, _action):
            return True

    result = await HumanApprovalPolicy(Gate()).authorize("disable_risk_limits", {}, {})

    assert result.approved is False
    assert "forbidden" in result.reason.lower()
