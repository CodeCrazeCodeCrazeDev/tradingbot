from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "trading_bot" / "core" / "phce_d_engine.py"
SPEC = importlib.util.spec_from_file_location("phce_d_engine_under_test", MODULE_PATH)
phce_d = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = phce_d
SPEC.loader.exec_module(phce_d)


def _base_evidence(**overrides):
    evidence = {
        "symbol": "AAPL",
        "as_of": 1_000.0,
        "market_timestamp": 1_000.0,
        "price": 100.0,
        "signal_strength": 0.72,
        "expected_edge_bps": 18.0,
        "spread_bps": 2.0,
        "slippage_bps": 2.0,
        "fee_bps": 0.5,
        "market_impact_bps": 1.0,
        "volatility": 0.12,
        "liquidity_score": 0.85,
        "sample_size": 80,
        "horizon_seconds": 300,
        "source_id": "unit-test",
        "trusted": True,
        "lineage_hash": "known-lineage",
        "portfolio_state": {"drawdown": 0.02},
        "feature_timestamps": {"signal": 999.0},
        "metadata": {"broker_venue_health": "healthy"},
    }
    evidence.update(overrides)
    return evidence


def _engine():
    return phce_d.ParallelHypothesisCorrectionEngine(clock=lambda: 1_000.0)


def test_positive_signal_becomes_paper_trade_candidate_only():
    engine = _engine()

    decision = engine.evaluate(_base_evidence())

    assert decision.policy_output == phce_d.PHCEDOutput.BUY
    assert decision.final_output == phce_d.PHCEDOutput.PAPER_TRADE_CANDIDATE
    assert decision.capital_allowed is False
    assert decision.gateway_result.approved is True
    assert decision.paper_trade_intent is not None
    assert len(engine.paper_logger.intents) == 1


def test_cost_stress_failure_abstains_without_paper_log():
    engine = _engine()

    decision = engine.evaluate(_base_evidence(expected_edge_bps=5.0, slippage_bps=5.0))

    assert decision.final_output == phce_d.PHCEDOutput.NO_TRADE
    assert "COST_STRESS_FAILED" in decision.reason_codes or "VERIFIER_FAILED" in decision.reason_codes
    assert decision.paper_trade_intent is None
    assert engine.paper_logger.intents == []


def test_temporal_leakage_rejects_evidence():
    engine = _engine()

    decision = engine.evaluate(_base_evidence(feature_timestamps={"future_feature": 1_001.0}))

    assert decision.final_output == phce_d.PHCEDOutput.REJECTED
    assert "EVIDENCE_REJECTED" in decision.reason_codes
    assert "lookahead" in decision.rationale


def test_vendor_disagreement_routes_to_no_trade():
    engine = _engine()

    decision = engine.evaluate(_base_evidence(vendor_signals={"vendor_a": 0.8, "vendor_b": -0.7}))

    assert decision.final_output == phce_d.PHCEDOutput.NO_TRADE
    assert decision.contradiction.contradiction_type == phce_d.ContradictionType.MEASUREMENT_CONFLICT
    assert "CONTRADICTION_TOO_SEVERE" in decision.reason_codes


def test_validation_gateway_blocks_market_hostility():
    engine = _engine()

    decision = engine.evaluate(_base_evidence(metadata={"market_hostility_score": 0.95, "broker_venue_health": "healthy"}))

    assert decision.policy_output == phce_d.PHCEDOutput.BUY
    assert decision.final_output == phce_d.PHCEDOutput.REJECTED
    assert decision.gateway_result.approved is False
    assert "VALIDATION_GATEWAY_REJECTED" in decision.reason_codes
    assert engine.paper_logger.intents == []
