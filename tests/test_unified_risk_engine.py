import pytest
import asyncio
from trading_bot.core.risk.unified_risk_engine import UnifiedRiskEngine
from trading_bot.core.risk.interfaces import RiskResult

@pytest.mark.asyncio
async def test_unified_risk_engine_aggregation():
    engine = UnifiedRiskEngine()
    params = {
        "win_rate": 0.6,
        "win_loss_ratio": 2.0,
        "exposure": 10000,
        "confidence": 0.9, # Required by ModelRiskEvaluator
        "estimated_slippage": 0.001 # Required by ExecutionRiskEvaluator
    }
    context = {
        "model_uncertainty": 0.1,
        "market_volatility": 0.15,
        "portfolio_equity": 1000000,
        "market_novelty": 0.05,
        "model_calibration_error": 0.05,
        "slippage_tolerance": 0.01,
        "asset_correlation": 0.3,
        "sector_exposure": 0.1,
        "current_drawdown": 0.02,
        "average_daily_volume": 100000000
    }

    result = await engine.evaluate_risk(params, context)

    assert result.approved is True, f"Risk rejected: {result.violated_constraints}"
    assert result.recommended_position_size > 0
    assert "KellyEvaluator" in result.evidence
    assert "VaREvaluator" in result.evidence
    assert "ModelRiskEvaluator" in result.evidence

@pytest.mark.asyncio
async def test_risk_engine_rejection():
    engine = UnifiedRiskEngine()
    # High exposure to trigger VaR rejection
    params = {"win_rate": 0.6, "win_loss_ratio": 2.0, "exposure": 500000, "confidence": 0.9}
    context = {"model_uncertainty": 0.1, "market_volatility": 0.3, "portfolio_equity": 1000000, "market_novelty": 0.05}

    result = await engine.evaluate_risk(params, context)

    assert result.approved is False
    assert any("VaR" in c for c in result.violated_constraints)

@pytest.mark.asyncio
async def test_risk_engine_ood_rejection():
    engine = UnifiedRiskEngine()
    params = {"win_rate": 0.6, "win_loss_ratio": 2.0, "exposure": 10000, "confidence": 0.9}
    context = {"model_uncertainty": 0.1, "market_volatility": 0.1, "portfolio_equity": 1000000, "market_novelty": 0.9}

    result = await engine.evaluate_risk(params, context)

    assert result.approved is False
    assert "Market state is OOD" in result.violated_constraints
