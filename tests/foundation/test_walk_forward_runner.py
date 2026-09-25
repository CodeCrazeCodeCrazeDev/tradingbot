"""Tests for replay-backed experiment evaluation."""

from types import SimpleNamespace

import pytest

from trading_bot.evaluation.runner import WalkForwardSimulationRunner


@pytest.mark.asyncio
async def test_walk_forward_runner_emits_oos_provenance() -> None:
    class FakeEvaluator:
        def run(self, symbol):
            return {
                "train": SimpleNamespace(total_return=0.1),
                "test": SimpleNamespace(
                    total_return=0.2,
                    max_drawdown=0.03,
                    win_rate=0.65,
                    ece_raw=0.2,
                    ece_calibrated=0.1,
                ),
            }

    runner = WalkForwardSimulationRunner(symbol="EURUSD", evaluator_factory=FakeEvaluator)
    result = await runner("strategy", {})

    assert result["evidence_source"] == "chronological_walk_forward"
    assert result["promotion_eligible"] is True
    assert result["oos_score"] == 0.2
    assert result["provenance"]["test_split"] == "chronological_oos"
