from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "trading_bot" / "intelligence" / "reverse_engineering_engine.py"
SPEC = importlib.util.spec_from_file_location("reverse_engineering_engine_under_test", MODULE_PATH)
rie = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = rie
SPEC.loader.exec_module(rie)


def _profitable_rows(count=35):
    return [
        {"edge": 0.04, "cost": 0.01, "sharpe_delta": 0.2, "drawdown": 0.05}
        for _ in range(count)
    ]


def test_real_system_extracts_reusable_pattern_and_ghost_capability():
    engine = rie.CreatorIntelligenceEngine()

    report = engine.reverse_engineer(
        {
            "source_type": "ai_system",
            "title": "Claim gated paper trading system",
            "claims": ["Uses evidence validation before paper promotion"],
            "tools": ["claim graph", "cost model", "paper trading"],
            "workflow_steps": ["observe", "formalize claims", "verify", "paper log"],
            "data_flow": ["market data", "claim graph", "validation gate", "paper ledger"],
            "outputs": [{"decision": "PAPER_ONLY", "latency_guard": True}],
            "marketed_features": ["evidence validation"],
            "metrics": {"false_positive_reduction": 0.2},
            "market_tests": _profitable_rows(),
        }
    )

    assert rie.CapabilityClass.REAL_CAPABILITY in report.classifications
    assert rie.CapabilityClass.REUSABLE_COMPONENT in report.classifications
    assert report.useful_patterns
    assert "latency_guard" in report.ghost_capabilities


def test_fake_hype_and_honeypot_are_rejected():
    engine = rie.CreatorIntelligenceEngine()

    report = engine.reverse_engineer(
        {
            "source_type": "competitor",
            "title": "Secret infinite alpha",
            "claims": ["Copy exact proprietary leak for guaranteed 100% risk-free alpha"],
            "marketed_features": ["secret sauce no drawdown"],
            "tags": ["competitor"],
        }
    )

    assert rie.CapabilityClass.FAKE_HYPE in report.classifications
    assert rie.CapabilityClass.HONEYPOT_PATTERN in report.classifications
    assert rie.CapabilityClass.LOW_VALUE_IDEA in report.classifications
    assert not report.useful_patterns
    assert report.rejected_ideas


def test_scaling_cliff_detects_capital_inversion():
    engine = rie.CreatorIntelligenceEngine()

    report = engine.reverse_engineer(
        {
            "source_type": "paper",
            "title": "Capacity constrained microstructure edge",
            "claims": ["Order book imbalance edge survives costs at small size"],
            "tools": ["order book", "backtest", "cost model", "paper trading"],
            "workflow_steps": ["observe order book", "estimate cost", "paper trade"],
            "data_flow": ["order book", "feature store", "cost model"],
            "metrics": {"edge": 0.03},
            "capital_tests": [
                {"capital": 10_000, "edge": 0.04},
                {"capital": 100_000, "edge": 0.02},
                {"capital": 1_000_000, "edge": -0.01},
            ],
            "market_tests": _profitable_rows(),
        }
    )
    scale = engine.scale_what_works(report)

    assert report.scaling_cliffs
    assert report.scaling_cliffs[0].cliff_value == 1_000_000
    assert scale["recommended_max_before_cliff"] == 1_000_000


def test_profitability_test_requires_enough_data():
    engine = rie.CreatorIntelligenceEngine()

    result = engine.test_profitability("pattern-1", _profitable_rows(count=5))

    assert result.verdict == rie.ProfitabilityVerdict.NEEDS_MORE_DATA
    assert result.sample_size == 5


def test_creator_scan_aggregates_patterns_and_rejections():
    engine = rie.CreatorIntelligenceEngine()

    scan = engine.scan_creators(
        [
            {
                "source_type": "trader",
                "title": "Walk-forward cost-aware workflow",
                "claims": ["Walk forward validation with cost model"],
                "tools": ["walk forward", "cost model", "paper trading"],
                "workflow_steps": ["hypothesis", "walk forward", "paper validate"],
                "data_flow": ["bars", "features", "paper ledger"],
                "metrics": {"edge": 0.02},
                "market_tests": _profitable_rows(),
            },
            {
                "source_type": "book",
                "title": "Magic strategy",
                "claims": ["Always wins with no drawdown"],
            },
        ]
    )

    assert scan.scanned_artifacts == 2
    assert scan.useful_patterns
    assert scan.rejected_ideas
    assert scan.ranked_patterns


def test_claim_extractor_formalizes_marketing_without_treating_it_as_fact():
    engine = rie.CreatorIntelligenceEngine()

    claims = engine.extract_claims(
        {
            "source_type": "competitor",
            "title": "Smart money reversal dashboard",
            "claims": ["Our AI detects institutional liquidity and predicts smart money reversals."],
            "outputs": [{"signal": "LONG", "zone": "accumulation"}],
        }
    )

    assert claims[0].claim_type == "market_structure_detection"
    assert claims[0].evidence_present is False
    assert claims[0].risk_of_hype == "high"
    assert "transaction-cost-adjusted profitability" in claims[0].required_validation
    assert claims[0].inference_notes


def test_hype_detector_rejects_unvalidated_high_accuracy_claims():
    engine = rie.CreatorIntelligenceEngine()

    report = engine.reverse_engineer(
        {
            "source_type": "ai_system",
            "title": "Ninety percent reversal AI",
            "claims": ["Predicts reversals with 90% accuracy and huge profit."],
            "marketed_features": ["institutional AI"],
            "screenshots": ["after_move_signal.png"],
        }
    )

    assert report.hype_report.verdict == "reject"
    assert "no transaction costs" in report.hype_report.red_flags
    assert "no sample size" in report.hype_report.red_flags
    assert report.promotion_decision.decision == rie.ReverseEngineeringDecision.REJECT


def test_reusable_pattern_generates_sandbox_experiment_not_production_change():
    engine = rie.CreatorIntelligenceEngine()

    report = engine.reverse_engineer(
        {
            "source_type": "paper",
            "title": "Absorption zone breakout model",
            "claims": ["Volume compression plus breakout confirmation improves entry quality."],
            "tools": ["backtest", "cost model", "slippage model", "walk forward"],
            "workflow_steps": ["detect compression", "confirm breakout", "compare baseline"],
            "data_flow": ["OHLCV", "volume features", "walk-forward validator"],
            "metrics": {"sample_size": 200, "max_drawdown": 0.08, "benchmark_delta": 0.12},
            "market_tests": _profitable_rows(),
            "tags": ["EURUSD", "H1"],
        }
    )

    assert report.useful_patterns
    assert report.sandbox_experiments
    assert report.sandbox_experiments[0].live_trading_allowed is False
    assert report.sandbox_experiments[0].target_directory == "sandbox/generated_experiments"
    assert report.promotion_decision.live_code_modification_allowed is False


def test_research_boundary_blocks_live_code_targets():
    engine = rie.CreatorIntelligenceEngine()

    try:
        engine.enforce_research_boundary("trading_bot/execution/router.py")
    except PermissionError as exc:
        assert "research-only" in str(exc)
    else:
        raise AssertionError("protected live execution path should be blocked")


def test_anti_repeat_memory_blocks_known_failed_ideas():
    engine = rie.CreatorIntelligenceEngine()
    engine.remember_research_outcome(
        rie.ResearchMemoryRecord(
            pattern="RSI divergence reversal system",
            status="rejected",
            tested_on=["EURUSD", "GBPUSD", "XAUUSD"],
            reason="Weak after transaction costs and unstable across regimes.",
            do_not_retry_until="new evidence or new filter introduced",
            related_patterns=["momentum divergence", "hidden divergence", "oscillator exhaustion"],
        )
    )

    report = engine.reverse_engineer(
        {
            "source_type": "trader",
            "title": "RSI divergence reversal system",
            "claims": ["RSI divergence predicts reversals."],
            "tools": ["rsi", "backtest", "cost model", "slippage model"],
            "workflow_steps": ["detect divergence", "enter reversal"],
            "data_flow": ["OHLCV", "indicator stack"],
            "metrics": {"sample_size": 100, "max_drawdown": 0.1},
            "market_tests": _profitable_rows(),
        }
    )

    assert report.promotion_decision.decision == rie.ReverseEngineeringDecision.REJECT
    assert "failed research memory" in report.promotion_decision.reason


def test_capability_graph_links_claim_evidence_validation_and_alphaalgo_module():
    engine = rie.CreatorIntelligenceEngine()

    report = engine.reverse_engineer(
        {
            "source_type": "paper",
            "title": "Regime embedding paper",
            "claims": ["Market regime embeddings improve portfolio allocation."],
            "tools": ["vector database", "walk forward", "cost model", "slippage model"],
            "workflow_steps": ["embed regimes", "allocate", "validate"],
            "data_flow": ["macro data", "embedding", "portfolio allocator"],
            "metrics": {"sample_size": 80, "benchmark_delta": 0.05},
            "market_tests": _profitable_rows(),
        }
    )

    node_types = {node.node_type for node in report.capability_graph.nodes}
    predicates = {edge.predicate for edge in report.capability_graph.edges}

    assert {"Claim", "Evidence", "Mechanism", "ValidationTest", "AlphaAlgoModule"}.issubset(node_types)
    assert "requires_validation" in predicates
    assert "feeds_research_module" in predicates
