"""Wave-2 veto-only adapters over retained legacy risk analyzers.

Every adapter is a subordinate RiskPolicy: it may veto, never approve, size,
or execute. All tests exercise the fail-closed contract through
CanonicalRiskService where the authority boundary matters.
"""

import pytest

from trading_bot.foundation import (
    DecisionProposal,
    Instrument,
    InstrumentType,
    PortfolioSnapshot,
    RiskState,
    Signal,
)
from trading_bot.risk.policy_adapters import (
    SizingVetoPolicyAdapter,
    TradeAllowancePolicyAdapter,
    TradeAssessmentPolicyAdapter,
)
from trading_bot.risk.service import CanonicalRiskService


def proposal() -> DecisionProposal:
    instrument = Instrument("EURUSD", InstrumentType.FX, "paper")
    signal = Signal(
        "signal-1",
        instrument,
        "buy",
        0.9,
        metadata={"quantity": 1.0, "entry_price": 1.1, "stop_loss": 1.05},
    )
    state = RiskState("account-1", 10000, 0.01, 0.0, 0.01, 0)
    return DecisionProposal("decision-1", signal, PortfolioSnapshot("account-1", 10000, 10000), state)


@pytest.mark.asyncio
async def test_trade_assessment_adapter_vetoes_on_limit_alerts() -> None:
    from types import SimpleNamespace

    class Engine:
        def assess_trade_risk(self, **kwargs):
            return SimpleNamespace(risk_level="HIGH")

        def check_risk_limits(self, assessment):
            return [SimpleNamespace(message="max_position_size breached")]

    service = CanonicalRiskService()
    service.register_policy("legacy_engine", TradeAssessmentPolicyAdapter("legacy_engine", Engine()))
    result = await service.evaluate(proposal(), proposal().risk_state)

    assert result.approved is False
    assert "max_position_size breached" in result.reason
    assert result.checks["policy_legacy_engine"] is False


@pytest.mark.asyncio
async def test_trade_assessment_adapter_passes_clean_engine() -> None:
    from types import SimpleNamespace

    class Engine:
        def assess_trade_risk(self, **kwargs):
            assert kwargs["symbol"] == "EURUSD"
            return SimpleNamespace(risk_level="LOW")

        def check_risk_limits(self, assessment):
            return []

    result = await TradeAssessmentPolicyAdapter("engine", Engine()).evaluate(
        proposal(), proposal().risk_state
    )
    assert result["approved"] is True


@pytest.mark.asyncio
async def test_trade_assessment_adapter_fails_closed_on_error() -> None:
    class Broken:
        def assess_trade_risk(self, **kwargs):
            raise RuntimeError("model unavailable")

    result = await TradeAssessmentPolicyAdapter("broken", Broken()).evaluate(
        proposal(), proposal().risk_state
    )
    assert result["approved"] is False
    assert "assessment failed" in result["reason"]


@pytest.mark.asyncio
async def test_trade_allowance_adapter_vetoes_legacy_block() -> None:
    from types import SimpleNamespace

    class Controller:
        def check_trade_allowed(self, symbol, direction, size):
            return False, "Daily loss limit reached", SimpleNamespace(value="CLOSE_ALL")

    result = await TradeAllowancePolicyAdapter("ctl", Controller()).evaluate(
        proposal(), proposal().risk_state
    )
    assert result["approved"] is False
    assert "Daily loss" in result["reason"]
    assert result["legacy_action"] == "CLOSE_ALL"


@pytest.mark.asyncio
async def test_sizing_veto_adapter_never_approves_quantity() -> None:
    class Sizer:
        def calculate_position_size(self, symbol, direction, confidence):
            return 0.0  # sizer refuses -> veto

    result = await SizingVetoPolicyAdapter("sizer", Sizer()).evaluate(
        proposal(), proposal().risk_state
    )
    assert result["approved"] is False

    # A positive size is admissible evidence only — no quantity is produced.
    class BigSizer:
        def calculate_position_size(self, symbol, direction, confidence):
            return 5.0

    result = await SizingVetoPolicyAdapter("sizer", BigSizer()).evaluate(
        proposal(), proposal().risk_state
    )
    assert result["approved"] is True
    assert "approved_quantity" not in result


@pytest.mark.asyncio
async def test_subordinate_adapters_cannot_approve_alone() -> None:
    """Even a passing legacy policy cannot approve when canonical checks fail."""
    class Permissive:
        def check_trade_allowed(self, *args):
            return True, "ok", "ALLOW"

    service = CanonicalRiskService()
    service.register_policy("legacy", TradeAllowancePolicyAdapter("legacy", Permissive()))

    bad = proposal()
    bad_state = RiskState("account-1", 10000, 0.01, 0.0, 0.01, 0, emergency=True)
    result = await service.evaluate(bad, bad_state)

    assert result.approved is False
    assert result.checks["not_emergency"] is False
