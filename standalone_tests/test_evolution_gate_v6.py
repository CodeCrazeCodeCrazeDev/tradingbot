import asyncio
import logging
from unittest.mock import MagicMock
from trading_bot.governance.evolution_gate import EvolutionGate, EvolutionMetrics

async def test_evolution_gate_monotone_safe():
    print("Testing Evolution Gate Monotone-Safe...")
    val_engine = MagicMock()
    # Baseline: reward=0.5, calibration=0.8, safety=1.0
    val_engine.run_benchmark.side_effect = [
        {"reward": 0.5, "calibration": 0.8, "robustness": 0.7, "latency": 10.0, "safety_score": 1.0},
        {"reward": 0.6, "calibration": 0.82, "robustness": 0.75, "latency": 9.0, "safety_score": 1.0}
    ]

    gate = EvolutionGate(val_engine, threshold=0.05)

    # Candidate should pass (gain 0.1 > 0.05)
    result = await gate.validate_evolution("cand_1", {}, {})
    assert result is True
    print("Monotone-Safe pass verified.")

    # Candidate with regression
    val_engine.run_benchmark.side_effect = [
        {"reward": 0.5, "calibration": 0.8, "robustness": 0.7, "latency": 10.0, "safety_score": 1.0},
        {"reward": 0.52, "calibration": 0.8, "robustness": 0.7, "latency": 10.0, "safety_score": 1.0}
    ]
    result = await gate.validate_evolution("cand_2", {}, {})
    assert result is False
    print("Monotone-Safe rejection verified.")

async def test_reward_hacking_detection():
    print("Testing Reward-Hacking Detection...")
    val_engine = MagicMock()
    gate = EvolutionGate(val_engine)

    # Malicious code change
    malicious_config = {"code_diff": "def get_reward(): return 1.0 # bypass safety"}

    result = await gate.validate_evolution("hacker_1", malicious_config, {})
    assert result is False
    print("Reward-hacking rejection verified.")

if __name__ == "__main__":
    asyncio.run(test_evolution_gate_monotone_safe())
    asyncio.run(test_reward_hacking_detection())
    print("✅ All Evolution Gate V6 Verifications Passed")
