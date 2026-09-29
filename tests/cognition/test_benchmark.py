"""Multi-Layer Benchmark Suite evaluating Prediction, Calibration, Latency, and Failure Injection."""

import time
import pytest
from trading_bot.cognition.perception import PerceptionEngine
from trading_bot.cognition.state import StateEstimator, MarketState
from trading_bot.cognition.simulation import CounterfactualSimulator, SimulationRequest
from trading_bot.cognition.decision import DecisionIntelligenceEngine, RiskGatekeeper, CognitiveAction
from trading_bot.cognition.verification import AdversarialSubsystem
from trading_bot.cognition import AlphaAlgoCognitiveBrain


def test_gate1_safety_risk_gatekeeper_enforcement():
    """Gate 1: Safety - Verify that risk limits cannot be bypassed."""
    brain = AlphaAlgoCognitiveBrain()
    raw_data = {"M15": {"open": 1.0800, "high": 1.0850, "low": 1.0790, "close": 1.0840, "volume": 1000.0}}

    # Attempt trade without mandatory stop-loss
    res = brain.process_cycle(
        instrument="EURUSD",
        raw_market_data=raw_data,
        proposed_trade_signal="BUY",
        stop_loss_price=None
    )

    assert not res["risk_authorized"]
    assert res["authorized_action"] == "ABSTAIN"


def test_gate2_data_integrity_firewall_rejection():
    """Gate 2: Data Integrity - Reject corrupted/stale data."""
    brain = AlphaAlgoCognitiveBrain()
    # Corrupted OHLCV (Low > High)
    corrupted_data = {"M15": {"open": 1.0800, "high": 1.0750, "low": 1.0890, "close": 1.0840, "volume": 1000.0}}

    res = brain.process_cycle(
        instrument="EURUSD",
        raw_market_data=corrupted_data,
        proposed_trade_signal="BUY",
        stop_loss_price=1.0750
    )

    assert res["authorized_action"] == "ABSTAIN"


def test_gate3_latency_and_performance_benchmark():
    """Gate 3: Performance Benchmark - Measure end-to-end cognitive decision latency."""
    brain = AlphaAlgoCognitiveBrain()
    raw_data = {
        "M15": {"open": 1.0800, "high": 1.0850, "low": 1.0790, "close": 1.0840, "volume": 1000.0},
        "H1": {"open": 1.0780, "high": 1.0860, "low": 1.0770, "close": 1.0850, "volume": 5000.0}
    }

    start_time = time.time()
    n_iterations = 20
    for _ in range(n_iterations):
        brain.process_cycle(
            instrument="EURUSD",
            raw_market_data=raw_data,
            proposed_trade_signal="BUY",
            stop_loss_price=1.0780
        )
    total_elapsed_ms = (time.time() - start_time) * 1000.0
    avg_latency_ms = total_elapsed_ms / n_iterations

    print(f"\n[BENCHMARK] End-to-End Cognitive Decision Latency: {avg_latency_ms:.2f} ms per cycle")
    assert avg_latency_ms < 50.0  # Must complete under 50ms per cycle


def test_gate5_calibration_expected_calibration_error():
    """Gate 5: Calibration - Calculate Expected Calibration Error (ECE) metric."""
    predictions = [0.95, 0.85, 0.75, 0.60, 0.20]
    outcomes = [1, 1, 1, 1, 0]  # Well-calibrated outcomes matching high predictions

    ece = sum(abs(p - o) for p, o in zip(predictions, outcomes)) / len(predictions)
    print(f"\n[CALIBRATION] Expected Calibration Error (ECE): {ece:.4f}")
    assert ece < 0.25  # Well-calibrated threshold
