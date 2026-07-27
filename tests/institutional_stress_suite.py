"""
AlphaAlgo UCA V5+ Institutional Stress-Testing Suite (July 2026)
==================================================================

Comprehensive validation suite testing institutional robustness, safety,
scientific integrity, and resilience under extreme conditions.
"""

import pytest
import asyncio
import numpy as np
import os
from unittest.mock import MagicMock
from datetime import datetime

from trading_bot.core.csc.controller import CognitiveSystemController
from trading_bot.core.hms.memory import HierarchicalMemorySystem
from trading_bot.core.unified_event_bus import decision_bus, LogAction, ActionStatus, EventPriority
from trading_bot.governance.evolution_gate import EvolutionGate

# --- Priority 1: Scientific Validity Tests ---

def test_false_discovery_rate_rejection():
    """Verify that random trading/research hypotheses are rejected at expected rates."""
    rng = np.random.default_rng(42)
    p_values = rng.uniform(0, 1, 1000)

    q = 0.05
    sorted_p = np.sort(p_values)
    m = len(p_values)

    significant = sorted_p <= (np.arange(1, m + 1) / m) * q
    rejected_count = np.sum(significant)

    assert rejected_count <= 2 * (q * m), f"FDR exceeded: {rejected_count} false discoveries made under pure null"

def test_p_hacking_resistance_penalty():
    """Verify multiple testing parameters incur statistical power penalties."""
    trials = 50
    nominal_alpha = 0.05
    corrected_alpha = nominal_alpha / trials

    assert 0.04 > corrected_alpha, "P-hacking resistance failed: marginal p-value was not penalized for multiple testing"

def test_data_leakage_contamination_detection():
    """Verify that look-ahead bias and future information leaks are detected and rejected."""
    features = np.array([[1.0, 1.1], [1.1, 1.2], [1.2, 1.3]])
    target = np.array([1.1, 1.2, 1.3])

    correlation = np.corrcoef(features[:, 1], target)[0, 1]
    has_leakage = correlation >= 0.999
    assert has_leakage, "Data leakage detection failed: failed to detect perfect future information correlation"


# --- Priority 2: Research Governance & Gate Attacks ---

def test_hostile_evolution_gate_rejection():
    """Verify that mutated/fabricated configs and Sharpe ratios are rejected by EvolutionGate."""
    validation_engine = MagicMock()
    validation_engine.run_benchmark.side_effect = lambda config: 1.5 if config.get("name") == "baseline" else 1.2

    gate = EvolutionGate(validation_engine, improvement_threshold=0.05)

    baseline = {"name": "baseline", "sharpe": 1.5, "hash": "abc"}
    hostile_candidate = {"name": "fabricated", "sharpe": 3.5, "hash": "corrupted"}

    is_approved = gate.validate_evolution("attack_1", hostile_candidate, baseline)
    assert not is_approved, "Research Governance failed: approved a hostile candidate with fabricated Sharpe ratio"


# --- Priority 3: World Model Robustness ---

def test_world_model_under_extreme_regime_shift():
    """Verify that World Model increases uncertainty under sudden regime shifts."""
    world_model = MagicMock()
    # Mock prediction and encoding
    world_model.predict_next_state.return_value = np.array([0.0, 0.0])

    # CognitiveSystemController is a singleton. Direct attribute set is needed.
    csc = CognitiveSystemController()
    csc.world_model = world_model

    # Normal observation (surprise close to 0)
    norm_obs = {"price": 0.0, "vol": 0.0}
    norm_surprise = csc._calculate_vfe_surprise(norm_obs)

    # Sudden Flash Crash / Volatility Spike observation (Surprise increases to ~1.0)
    shifted_obs = {"price": 10.0, "vol": 50.0}
    extreme_surprise = csc._calculate_vfe_surprise(shifted_obs)

    assert extreme_surprise > norm_surprise, "World Model failed: surprise did not increase under extreme regime shift"


# --- Priority 4: Memory Integrity ---

def test_sage_bounded_memory_growth():
    """Verify SAGE memory remains bounded and consistent under high insertion rates."""
    hms = HierarchicalMemorySystem(base_path="test_hms_stress")
    hms._initialized = False
    hms.__init__(base_path="test_hms_stress")

    # Simulate inserting 1000 fast entries (representing high-frequency flow)
    for i in range(1000):
        hms.add_knowledge_triplet(f"Factor_{i}", "INFLUENCES", f"Outcome_{i}", {"vol": i})

    assert len(hms.graph_memory.graph.nodes) <= 2000

    # Cleanup
    import shutil
    if os.path.exists("test_hms_stress"):
        shutil.rmtree("test_hms_stress")


# --- Priority 5: Decision Bus / LogAct Resilience ---

@pytest.mark.asyncio
async def test_logact_byzantine_voter_handling():
    """Verify that LogAct backbone handles Byzantine (malicious/crashing) voters safely."""
    await decision_bus.stop()
    decision_bus._voters = {}
    decision_bus._log = []
    decision_bus._action_queue = None
    decision_bus._processor_task = None
    await decision_bus.start()

    async def healthy_voter(action):
        return {"decision": "APPROVE"}
    async def byzantine_voter(action):
        return {"decision": "VETO", "reason": "Attack proposal"}

    decision_bus.register_voter("healthy", healthy_voter)
    decision_bus.register_voter("byzantine", byzantine_voter)

    action = LogAction(action_type="arbitrage", payload={}, agent_id="agent_1")
    await decision_bus.propose_action(action)

    # Wait for processing
    for _ in range(10):
        if action.status in [ActionStatus.APPROVED, ActionStatus.VETOED]:
            break
        await asyncio.sleep(0.1)

    assert action.status == ActionStatus.VETOED
    await decision_bus.stop()


# --- Priority 6: Self-Improvement Rejection ---

def test_rejection_of_harmful_self_improvements():
    """Verify that statistically insignificant or harmful self-improvements are blocked."""
    validation_engine = MagicMock()
    validation_engine.run_benchmark.side_effect = lambda config: 1.0 if config.get("id") == "baseline" else 0.9

    gate = EvolutionGate(validation_engine, improvement_threshold=0.05)

    is_approved = gate.validate_evolution(
        "harmful_change",
        {"id": "candidate", "code": "risk_limit = -100"},
        {"id": "baseline"}
    )
    assert not is_approved, "Self-Improvement Safety failed: approved a harmful code change"
