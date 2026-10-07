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


def make_proposal(direction="buy", quantity=1.0, price=1.10):
    instrument = Instrument("EURUSD", InstrumentType.FX, "paper")
    signal = Signal(
        signal_id="signal-1",
        instrument=instrument,
        direction=direction,
        confidence=0.9,
        metadata={"quantity": quantity, "price": price},
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
async def test_risk_service_rejects_projected_exposure_breach() -> None:
    """Exposure after the proposed order — not just current — is the bound."""
    service = CanonicalRiskService()
    # qty 1.0 * price 1.10 * contract 1.0 = $1.10 -> 0.011% on $10k equity,
    # but current 4.5% + proposed marginal pushes projected over 5%.
    state = RiskState("account-1", 10000, 0.045, 0, 0.01, 0)
    ok = await service.evaluate(make_proposal(quantity=1.0), state)
    assert ok.approved is True

    breach = await service.evaluate(
        make_proposal(quantity=1000.0),  # > max_quantity anyway
        state,
    )
    assert breach.approved is False

    # Within quantity limit but projected notional blows past the cap:
    # 9 lots at mark 1.10 * contract 100000 = $990k -> +9900% exposure.
    # With a venue quantity increment the risk stage is the sizing
    # authority: the proposal is clamped to the largest permitted size —
    # and when that size floors below the venue grid, it rejects.
    instrument = Instrument(
        "EURUSD", InstrumentType.FX, "paper", contract_size=100000,
        quantity_increment=0.01)
    signal = Signal(
        signal_id="s", instrument=instrument, direction="buy",
        confidence=0.9,
        metadata={"quantity": 9.0, "price": 1.10, "quantity_min": 0.01})
    proposal = DecisionProposal(
        decision_id="d", signal=signal,
        portfolio=PortfolioSnapshot("account-1", 10000, 10000),
        risk_state=RiskState("account-1", 10000, 0.045, 0, 0.01, 0))
    result = await service.evaluate(proposal, proposal.risk_state)
    assert result.approved is False
    assert "projected_exposure_limit" in result.reason

    # Same breach on an account large enough for a valid clamp: sized to
    # the headroom, floored to the venue step.
    big = DecisionProposal(
        decision_id="d2", signal=signal,
        portfolio=PortfolioSnapshot("account-1", 1e9, 1e9),
        risk_state=RiskState("account-1", 1e9, 0.0, 0, 0.01, 0))
    clamped = await service.evaluate(big, big.risk_state)
    # headroom 5% * $1e9 / (1.10 * 100k) ~= 454 lots -> min(9, ~454) = 9
    assert clamped.approved is True
    assert clamped.approved_quantity == 9.0


@pytest.mark.asyncio
async def test_risk_service_unmeasurable_directional_mark_fails_closed() -> None:
    service = CanonicalRiskService()
    instrument = Instrument("EURUSD", InstrumentType.FX, "paper")
    signal = Signal(
        signal_id="s", instrument=instrument, direction="buy",
        confidence=0.9, metadata={"quantity": 0.5})   # no price/mark
    proposal = DecisionProposal(
        decision_id="d", signal=signal,
        portfolio=PortfolioSnapshot("account-1", 10000, 10000),
        risk_state=RiskState("account-1", 10000, 0.0, 0, 0.0, 0))
    result = await service.evaluate(proposal, proposal.risk_state)
    assert result.approved is False


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
        {"symbol": "EURUSD", "data_quality": "valid", "exposure": 0.01,
         "close": 1.10, "equity": 10000.0},
    )

    assert result.approved is True
    assert result.decision_id == "trade-1"


@pytest.mark.asyncio
async def test_risk_service_fails_closed_on_unverified_data_quality() -> None:
    """Only an explicit 'valid' marker is fresh: unknown/degraded quality and
    declared-stale flags cannot authorize risk."""
    service = CanonicalRiskService()
    action = {"trade_id": "trade-1", "symbol": "EURUSD", "action": "BUY",
              "quantity": 1.0, "confidence": 0.8}
    base_obs = {"symbol": "EURUSD", "exposure": 0.01, "close": 1.10,
                "equity": 10000.0}

    for quality in ("unknown", "degraded", "invalid", "stale", "garbage"):
        obs = {**base_obs, "data_quality": quality}
        result = await service.evaluate_action(action, obs)
        assert result.approved is False, f"quality={quality} must not approve"
        assert "data_fresh" in result.reason

    result = await service.evaluate_action(
        action, {**base_obs, "data_quality": "valid", "data_is_fresh": False})
    assert result.approved is False
    assert "data_fresh" in result.reason

    # Absent quality markers keep the legacy permissive path.
    result = await service.evaluate_action(action, dict(base_obs))
    assert result.approved is True


@pytest.mark.asyncio
async def test_risk_service_refreshes_portfolio_state() -> None:
    service = CanonicalRiskService()
    snapshot = PortfolioSnapshot("account-1", 10000, 9000, drawdown_fraction=0.03)

    state = await service.refresh(snapshot)

    assert state.account_id == "account-1"
    assert state.equity == 10000
    assert state.open_positions == 0
