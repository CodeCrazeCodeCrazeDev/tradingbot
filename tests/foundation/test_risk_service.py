"""Tests for the canonical portfolio-risk service."""

import pytest

from trading_bot.foundation import (
    DecisionProposal,
    Instrument,
    InstrumentType,
    PortfolioSnapshot,
    RiskState,
    Signal,
)
from trading_bot.risk.service import CanonicalRiskService


def make_proposal(direction="buy", quantity=1.0):
    instrument = Instrument("EURUSD", InstrumentType.FX, "paper")
    signal = Signal(
        signal_id="signal-1",
        instrument=instrument,
        direction=direction,
        confidence=0.9,
        metadata={"quantity": quantity},
    )
    return DecisionProposal(
        decision_id="decision-1",
        signal=signal,
        portfolio=PortfolioSnapshot("account-1", 10000, 10000),
        risk_state=RiskState("account-1", 10000, 0.01, 0, 0.01, 0),
    )


@pytest.mark.asyncio
async def test_risk_service_approves_within_limits() -> None:
    service = CanonicalRiskService()
    result = await service.evaluate(make_proposal(), RiskState("account-1", 10000, 0.01, 0, 0.01, 0))

    assert result.approved is True
    assert result.approved_quantity == 1.0
    assert all(result.checks.values())


@pytest.mark.asyncio
async def test_risk_service_rejects_stale_or_overexposed_state() -> None:
    service = CanonicalRiskService()
    state = RiskState(
        "account-1", 10000, 0.08, 0, 0.01, 0, data_is_fresh=False
    )
    result = await service.evaluate(make_proposal(), state)

    assert result.approved is False
    assert "data_fresh" in result.reason
    assert "exposure_limit" in result.reason


@pytest.mark.asyncio
async def test_risk_service_adapts_current_csc_action_payload() -> None:
    service = CanonicalRiskService()

    result = await service.evaluate_action(
        {"trade_id": "trade-1", "symbol": "EURUSD", "action": "BUY", "quantity": 1.0, "confidence": 0.8},
        {"symbol": "EURUSD", "data_quality": "valid", "exposure": 0.01},
    )

    assert result.approved is True
    assert result.decision_id == "trade-1"


@pytest.mark.asyncio
async def test_risk_service_refreshes_portfolio_state() -> None:
    service = CanonicalRiskService()
    snapshot = PortfolioSnapshot("account-1", 10000, 9000, drawdown_fraction=0.03)

    state = await service.refresh(snapshot)

    assert state.account_id == "account-1"
    assert state.equity == 10000
    assert state.open_positions == 0
