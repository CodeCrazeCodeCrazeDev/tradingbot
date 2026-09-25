"""Tests preventing unmarked random experiment evidence."""

import pytest

from trading_bot.recursive_self_improvement.evaluation import EvaluationEngine
from trading_bot.recursive_self_improvement.experiment_manager import ExperimentManager


class Memory:
    def __init__(self):
        self.results = []

    def record_experiment(self, *args, **kwargs):
        pass

    def update_experiment_result(self, *args, **kwargs):
        self.results.append((args, kwargs))


@pytest.mark.asyncio
async def test_experiment_fails_closed_without_simulation_runner() -> None:
    manager = ExperimentManager(Memory(), EvaluationEngine())

    result = await manager.run_experiment("strategy", "test", {}, {})

    assert result["status"] == "error"
    assert "simulation_runner" in result["error"]


@pytest.mark.asyncio
async def test_synthetic_fallback_is_explicitly_non_promotable() -> None:
    manager = ExperimentManager(
        Memory(),
        EvaluationEngine(),
        config={"allow_synthetic_fallback": True},
    )

    result = await manager.run_experiment(
        "strategy", "test", {"x": 1}, {"baseline_metrics": {"sharpe_ratio": 1.0}}
    )

    assert result["status"] == "failed"
    assert result["evaluation"]["recommendation"] == "research_only_synthetic"
    assert result["evaluation"]["promotion_eligible"] is False


@pytest.mark.asyncio
async def test_injected_runner_provides_promotable_evidence() -> None:
    async def runner(domain, parameters):
        return {
            "sharpe_ratio": 2.0,
            "total_return": 0.2,
            "max_drawdown": 0.03,
            "win_rate": 0.7,
        }

    manager = ExperimentManager(Memory(), EvaluationEngine(), simulation_runner=runner)
    result = await manager.run_experiment(
        "strategy",
        "test",
        {"x": 1},
        {"baseline_metrics": {"sharpe_ratio": 1.0, "total_return": 0.1}},
    )

    assert result["status"] == "completed"
    assert result["evaluation"]["promotion_eligible"] is True
