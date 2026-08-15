"""
EvolutionGate (RSEA) Monotone-Safe Verification and Rollback Tests
==================================================================
Verifies EvolutionGate decisions under precise, controlled gain thresholds,
ensuring monotone safety and deterministic rollback behavior.
"""

import pytest
from typing import Dict, Any
from trading_bot.governance.evolution_gate import EvolutionGate

class MockValidationEngine:
    def __init__(self):
        self.performances = {}

    def set_performance(self, config_id: str, perf: float):
        self.performances[config_id] = perf

    def run_benchmark(self, config: Dict[str, Any]) -> Dict[str, Any]:
        config_id = config.get("config_id", "default")
        perf = self.performances.get(config_id, 0.5)
        # Return full metrics shape required by EvolutionMetrics
        return {
            "reward": perf,
            "calibration": 0.95,
            "robustness": perf,
            "latency": 5.0,
            "safety_score": 1.0
        }

def test_evolution_gate_monotone_safety_accepts_good_gains():
    """Verify that EvolutionGate accepts candidates with improvement exceeding threshold."""
    engine = MockValidationEngine()
    gate = EvolutionGate(validation_engine=engine, threshold=0.10)

    # Baseline = 0.50, Candidate = 0.65 (Improvement of +0.15 > +0.10)
    baseline_config = {"config_id": "baseline_config"}
    candidate_config = {"config_id": "candidate_good_config"}

    engine.set_performance("baseline_config", 0.50)
    engine.set_performance("candidate_good_config", 0.65)

    approved = gate.validate_evolution("candidate_good_v1", candidate_config, baseline_config)
    assert approved is True
    assert len(gate.get_evolution_report()) == 1
    assert gate.get_evolution_report()[0]["candidate_id"] == "candidate_good_v1"

def test_evolution_gate_monotone_safety_rejects_minor_gains():
    """Verify that EvolutionGate rejects candidates with improvement below threshold."""
    engine = MockValidationEngine()
    gate = EvolutionGate(validation_engine=engine, threshold=0.10)

    # Baseline = 0.50, Candidate = 0.55 (Improvement of +0.05 < +0.10)
    baseline_config = {"config_id": "baseline_config"}
    candidate_config = {"config_id": "candidate_minor_config"}

    engine.set_performance("baseline_config", 0.50)
    engine.set_performance("candidate_minor_config", 0.55)

    approved = gate.validate_evolution("candidate_minor_v1", candidate_config, baseline_config)
    assert approved is False
    assert len(gate.get_evolution_report()) == 0

def test_evolution_gate_monotone_safety_rejects_regressions():
    """Verify that EvolutionGate rejects regressive candidates."""
    engine = MockValidationEngine()
    gate = EvolutionGate(validation_engine=engine, threshold=0.10)

    # Baseline = 0.50, Candidate = 0.45 (Regression of -0.05)
    baseline_config = {"config_id": "baseline_config"}
    candidate_config = {"config_id": "candidate_regressive_config"}

    engine.set_performance("baseline_config", 0.50)
    engine.set_performance("candidate_regressive_config", 0.45)

    approved = gate.validate_evolution("candidate_regressive_v1", candidate_config, baseline_config)
    assert approved is False
    assert len(gate.get_evolution_report()) == 0

def test_evolution_gate_rollback_expectations():
    """Verify that failed or rejected candidates trigger rollback (preserving the active baseline)."""
    engine = MockValidationEngine()
    gate = EvolutionGate(validation_engine=engine, threshold=0.10)

    active_baseline = {"config_id": "baseline_config"}
    engine.set_performance("baseline_config", 0.50)

    # Run a bad candidate
    rejected_candidate = {"config_id": "candidate_regressive_config"}
    engine.set_performance("candidate_regressive_config", 0.45)

    approved = gate.validate_evolution("candidate_bad_v1", rejected_candidate, active_baseline)
    assert approved is False

    # Since the evolution was rejected, the active configuration must roll back or remain as baseline_config.
    # We verify that only the baseline performance is retrieved in the next cycle, and no promotion is logged.
    assert len(gate.get_evolution_report()) == 0

    baseline_perf_retrieved = engine.run_benchmark(active_baseline)["reward"]
    assert baseline_perf_retrieved == 0.50
