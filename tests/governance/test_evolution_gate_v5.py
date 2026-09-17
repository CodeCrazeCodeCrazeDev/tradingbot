"""
UCA V5 Evolution Gate & Governance Tests
========================================

Validates the RSEA Monotone-Safe evolution gate, EKSFT compliance,
and deterministic replay requirements.
"""

import pytest
import asyncio
import numpy as np
from trading_bot.governance.evolution_gate import EvolutionGate, EvolutionMetrics

class MockValidationEngine:
    def __init__(self, reward_gain=0.05, regression=False):
        self.reward_gain = reward_gain
        self.regression = regression

    def run_benchmark(self, config, mode="stateless"):
        # Returns improved metrics for stateful if not regression
        base_reward = 0.1
        if mode == "stateful":
            reward = base_reward + self.reward_gain
            safety = 0.95 if self.regression else 1.0
            latency = 200 if self.regression else 50
        else:
            reward = base_reward
            safety = 1.0
            latency = 50

        return {
            "reward": reward,
            "safety_score": safety,
            "latency": latency,
            "ece": 0.05,
            "std_dev": 0.001
        }

@pytest.mark.asyncio
async def test_rsea_monotone_safe_promotion():
    """Validates that valid improvements are promoted."""
    engine = MockValidationEngine(reward_gain=0.10) # 10% gain (Significant)
    gate = EvolutionGate(engine)

    candidate = {"id": "C-001", "logic_shard": {"halt": False}}
    baseline = {"id": "B-001"}

    approved = await gate.validate_evolution("C-001", candidate, baseline)
    assert approved is True
    assert len(gate.evolution_history) == 1
    assert gate.evolution_history[0]["status"] == "PROMOTED"

@pytest.mark.asyncio
async def test_rsea_regression_rejection():
    """Validates that improvements with safety regressions are rejected."""
    engine = MockValidationEngine(reward_gain=0.10, regression=True)
    gate = EvolutionGate(engine)

    candidate = {"id": "C-002"}
    baseline = {"id": "B-001"}

    approved = await gate.validate_evolution("C-002", candidate, baseline)
    assert approved is False
    assert len(gate.evolution_history) == 0

@pytest.mark.asyncio
async def test_eksft_uncertainty_masking():
    """Validates that high-uncertainty concepts must be masked (EKSFT)."""
    engine = MockValidationEngine()
    gate = EvolutionGate(engine)

    # Concept with high entropy and NO mask -> Should Fail
    bad_candidate = {
        "id": "C-003",
        "training_metadata": {
            "eksft_trace": [{"id": "volatile_asset_x", "entropy": 0.9, "masked": False}]
        }
    }
    approved = await gate.validate_evolution("C-003", bad_candidate, {"id": "B-001"})
    assert approved is False

    # Concept with high entropy AND mask -> Should Pass
    good_candidate = {
        "id": "C-004",
        "training_metadata": {
            "eksft_trace": [{"id": "volatile_asset_x", "entropy": 0.9, "masked": True}]
        }
    }
    approved = await gate.validate_evolution("C-004", good_candidate, {"id": "B-001"})
    assert approved is True

@pytest.mark.asyncio
async def test_formal_invariant_halt_violation():
    """Validates that exposure cannot be increased while halted."""
    engine = MockValidationEngine()
    gate = EvolutionGate(engine)

    violating_candidate = {
        "id": "C-005",
        "logic_shard": {"halt": True, "increase_exposure": True}
    }
    approved = await gate.validate_evolution("C-005", violating_candidate, {"id": "B-001"})
    assert approved is False
