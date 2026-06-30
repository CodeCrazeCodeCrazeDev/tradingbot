import pytest
import asyncio
from trading_bot.core_agent_system.improvement.registry import ImprovementRegistry, ImprovementType, ImprovementStatus
from trading_bot.core_agent_system.improvement.evaluator import ImprovementEvaluator
from trading_bot.core_agent_system.improvement.orchestrator import ImprovementOrchestrator

@pytest.mark.asyncio
async def test_improvement_lifecycle():
    registry = ImprovementRegistry()
    evaluator = ImprovementEvaluator()
    orchestrator = ImprovementOrchestrator(registry, evaluator)

    # 1. Propose
    imp_id = await orchestrator.propose_trading_improvement(
        domain="alpha",
        source="TestAgent",
        logic="Improved SMA Crossover",
        parameters={"fast": 10, "slow": 30}
    )

    record = registry.get_record(imp_id)
    assert record is not None
    assert record.status == ImprovementStatus.CANDIDATE

    # 2. Run Cycle (Evaluate)
    await orchestrator.run_cycle({})

    # 3. Verify promotion (using mock success in orchestrator)
    updated_record = registry.get_record(imp_id)
    assert updated_record.status == ImprovementStatus.SHADOW
    assert "sharpe_ratio" in updated_record.evidence

if __name__ == "__main__":
    pytest.main([__file__])
