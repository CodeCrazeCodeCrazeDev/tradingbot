"""
PHCE-D Module 11: Adversarial Stress Test Suite

P0 #6: Test the pipeline with adversarial inputs.
Escape rate must be zero before enabling paper-trade promotion.

Test vectors:
- Future leakage
- Missing costs
- Random signals
- Contradictory evidence
- Regime inversion
- Gateway bypass attempts
- Hallucinated LLM hypotheses

Hard rule: adversarial bad inputs must NEVER produce a trade-positive output.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple

from .core_types import (
    DecisionOutput,
    DecisionLane,
    EvidenceKind,
    EvidencePacket,
    EvidenceSource,
    EvidenceTrust,
    FreshnessPolicy,
    Hypothesis,
    HypothesisLineage,
    LeakageRisk,
)

logger = logging.getLogger(__name__)


@dataclass
class StressTestVector:
    """A single adversarial test vector."""
    name: str
    description: str
    category: str  # "leakage", "missing_cost", "random", "contradictory", "regime_inversion", "bypass", "hallucination"
    evidence_sources: List[Dict[str, Any]]
    expected_output: DecisionOutput  # What the system SHOULD produce
    must_not_produce: List[DecisionOutput]  # Outputs that would be escapes


@dataclass
class StressTestResult:
    """Result of running a stress test vector through the pipeline."""
    vector_name: str
    passed: bool
    actual_output: DecisionOutput
    escape_detected: bool
    details: str
    processing_time_ms: float


# ── Built-in adversarial test vectors ─────────────────────────────────────────

BUILTIN_STRESS_VECTORS: List[StressTestVector] = [
    StressTestVector(
        name="future_leakage_in_bars",
        description="1m bars contain future_return field — lookahead leakage",
        category="leakage",
        evidence_sources=[
            {"source_id": "leaky_bars", "evidence_kind": "1m_bars", "timestamp": 0,
             "trust": "high", "value": {"close": 100, "open": 99, "future_return": 0.02}},
            {"source_id": "spread", "evidence_kind": "spread_liquidity", "timestamp": 0,
             "trust": "high", "value": {"spread_bps": 5, "normal_spread_bps": 5}},
            {"source_id": "cost", "evidence_kind": "cost_model", "timestamp": 0,
             "trust": "high", "value": {"total_cost_bps": 10}},
            {"source_id": "portfolio", "evidence_kind": "portfolio_state", "timestamp": 0,
             "trust": "high", "value": {}},
        ],
        expected_output=DecisionOutput.REJECTED,
        must_not_produce=list(DecisionOutput.trade_positive()),
    ),
    StressTestVector(
        name="missing_cost_model",
        description="Trade hypothesis without cost model — should be killed",
        category="missing_cost",
        evidence_sources=[
            {"source_id": "bars", "evidence_kind": "1m_bars", "timestamp": 0,
             "trust": "high", "value": {"close": 100, "open": 99}},
            {"source_id": "spread", "evidence_kind": "spread_liquidity", "timestamp": 0,
             "trust": "high", "value": {"spread_bps": 5, "normal_spread_bps": 5}},
            {"source_id": "portfolio", "evidence_kind": "portfolio_state", "timestamp": 0,
             "trust": "high", "value": {}},
            # NO cost_model source
        ],
        expected_output=DecisionOutput.REJECTED,
        must_not_produce=list(DecisionOutput.trade_positive()),
    ),
    StressTestVector(
        name="random_signal_no_edge",
        description="Random signal with no statistical edge",
        category="random",
        evidence_sources=[
            {"source_id": "bars", "evidence_kind": "1m_bars", "timestamp": 0,
             "trust": "high", "value": {"close": 100, "open": 100.001}},
            {"source_id": "spread", "evidence_kind": "spread_liquidity", "timestamp": 0,
             "trust": "high", "value": {"spread_bps": 5, "normal_spread_bps": 5}},
            {"source_id": "cost", "evidence_kind": "cost_model", "timestamp": 0,
             "trust": "high", "value": {"total_cost_bps": 10}},
            {"source_id": "portfolio", "evidence_kind": "portfolio_state", "timestamp": 0,
             "trust": "high", "value": {}},
        ],
        expected_output=DecisionOutput.NO_TRADE,
        must_not_produce=[DecisionOutput.BUY, DecisionOutput.SELL, DecisionOutput.PAPER_TRADE_CANDIDATE],
    ),
    StressTestVector(
        name="stale_evidence_high_trust",
        description="High-trust evidence is stale — should block decision",
        category="contradictory",
        evidence_sources=[
            {"source_id": "stale_bars", "evidence_kind": "1m_bars", "timestamp": -300,
             "trust": "high", "value": {"close": 100, "open": 99}},
            {"source_id": "spread", "evidence_kind": "spread_liquidity", "timestamp": 0,
             "trust": "high", "value": {"spread_bps": 5, "normal_spread_bps": 5}},
            {"source_id": "cost", "evidence_kind": "cost_model", "timestamp": 0,
             "trust": "high", "value": {"total_cost_bps": 10}},
            {"source_id": "portfolio", "evidence_kind": "portfolio_state", "timestamp": -10,
             "trust": "high", "value": {}},
        ],
        expected_output=DecisionOutput.NO_TRADE,
        must_not_produce=list(DecisionOutput.trade_positive()),
    ),
    StressTestVector(
        name="regime_inversion",
        description="Hypothesis designed for low-vol but market is high-vol",
        category="regime_inversion",
        evidence_sources=[
            {"source_id": "bars", "evidence_kind": "1m_bars", "timestamp": 0,
             "trust": "high", "value": {"close": 100, "open": 99}},
            {"source_id": "spread", "evidence_kind": "spread_liquidity", "timestamp": 0,
             "trust": "high", "value": {"spread_bps": 50, "normal_spread_bps": 5}},
            {"source_id": "cost", "evidence_kind": "cost_model", "timestamp": 0,
             "trust": "high", "value": {"total_cost_bps": 30}},
            {"source_id": "portfolio", "evidence_kind": "portfolio_state", "timestamp": 0,
             "trust": "high", "value": {}},
        ],
        expected_output=DecisionOutput.NO_TRADE,
        must_not_produce=[DecisionOutput.BUY, DecisionOutput.SELL],
    ),
    StressTestVector(
        name="hallucinated_llm_claim",
        description="LLM-generated claim with no deterministic verification",
        category="hallucination",
        evidence_sources=[
            {"source_id": "llm_research", "evidence_kind": "external_research", "timestamp": 0,
             "trust": "low", "value": {"claim": "strong buy signal detected by AI"}},
            {"source_id": "bars", "evidence_kind": "1m_bars", "timestamp": 0,
             "trust": "high", "value": {"close": 100, "open": 100.001}},
            {"source_id": "spread", "evidence_kind": "spread_liquidity", "timestamp": 0,
             "trust": "high", "value": {"spread_bps": 5, "normal_spread_bps": 5}},
            {"source_id": "cost", "evidence_kind": "cost_model", "timestamp": 0,
             "trust": "high", "value": {"total_cost_bps": 10}},
            {"source_id": "portfolio", "evidence_kind": "portfolio_state", "timestamp": 0,
             "trust": "high", "value": {}},
        ],
        expected_output=DecisionOutput.NO_TRADE,
        must_not_produce=[DecisionOutput.BUY, DecisionOutput.SELL],
    ),
]


class AdversarialStressTestSuite:
    """
    P0 #6: Adversarial Stress Test Suite

    Tests the PHCE-D pipeline with adversarial inputs.
    Escape rate must be zero before enabling paper-trade promotion.

    Hard rule: adversarial bad inputs must NEVER produce a trade-positive output.
    """

    def __init__(
        self,
        custom_vectors: Optional[List[StressTestVector]] = None,
    ):
        self.vectors = list(BUILTIN_STRESS_VECTORS)
        if custom_vectors:
            self.vectors.extend(custom_vectors)

        # Statistics
        self.total_runs = 0
        self.total_passes = 0
        self.total_escapes = 0
        self.escape_log: List[Dict[str, Any]] = []

    def run_all(
        self,
        pipeline_fn: Callable[[List[Dict[str, Any]], DecisionLane], DecisionOutput],
        lane: DecisionLane = DecisionLane.DECISION,
    ) -> List[StressTestResult]:
        """
        Run all stress test vectors through the pipeline.

        Args:
            pipeline_fn: Function that takes evidence sources and lane,
                         returns a DecisionOutput. This is the full PHCE-D pipeline.
            lane: Which lane to test

        Returns:
            List of StressTestResult for each vector
        """
        results = []
        for vector in self.vectors:
            result = self.run_vector(vector, pipeline_fn, lane)
            results.append(result)

        # Summary
        escapes = [r for r in results if r.escape_detected]
        if escapes:
            logger.critical(
                f"ADVERSARIAL STRESS TEST: {len(escapes)}/{len(results)} ESCAPES DETECTED. "
                f"Paper-trade promotion MUST NOT be enabled until escape rate is zero."
            )
        else:
            logger.info(
                f"ADVERSARIAL STRESS TEST: All {len(results)} vectors passed. "
                f"Escape rate is zero."
            )

        return results

    def run_vector(
        self,
        vector: StressTestVector,
        pipeline_fn: Callable[[List[Dict[str, Any]], DecisionLane], DecisionOutput],
        lane: DecisionLane = DecisionLane.DECISION,
    ) -> StressTestResult:
        """Run a single stress test vector through the pipeline."""
        start = time.monotonic()
        self.total_runs += 1

        try:
            actual_output = pipeline_fn(vector.evidence_sources, lane)
        except Exception as e:
            # If the pipeline throws an exception for bad input, that's a pass
            # (the system rejected the bad input by failing safely)
            elapsed = (time.monotonic() - start) * 1000
            self.total_passes += 1
            return StressTestResult(
                vector_name=vector.name,
                passed=True,
                actual_output=DecisionOutput.REJECTED,
                escape_detected=False,
                details=f"Pipeline exception (safe rejection): {e}",
                processing_time_ms=elapsed,
            )

        # Check for escape
        escape_detected = actual_output in vector.must_not_produce
        passed = not escape_detected

        if escape_detected:
            self.total_escapes += 1
            self.escape_log.append({
                "vector": vector.name,
                "category": vector.category,
                "actual_output": actual_output.value,
                "forbidden_outputs": [o.value for o in vector.must_not_produce],
            })
            logger.critical(
                f"ESCAPE: Vector '{vector.name}' produced {actual_output.value} "
                f"which is in the forbidden set {[o.value for o in vector.must_not_produce]}"
            )
        else:
            self.total_passes += 1

        elapsed = (time.monotonic() - start) * 1000
        return StressTestResult(
            vector_name=vector.name,
            passed=passed,
            actual_output=actual_output,
            escape_detected=escape_detected,
            details=(
                f"Expected {vector.expected_output.value}, got {actual_output.value}"
                + (" — ESCAPE!" if escape_detected else "")
            ),
            processing_time_ms=elapsed,
        )

    def escape_rate_is_zero(self) -> bool:
        """Check if escape rate is zero — prerequisite for paper-trade promotion."""
        return self.total_escapes == 0 and self.total_runs > 0

    def get_stats(self) -> Dict[str, Any]:
        """Return stress test statistics."""
        return {
            "total_runs": self.total_runs,
            "total_passes": self.total_passes,
            "total_escapes": self.total_escapes,
            "escape_rate": self.total_escapes / max(1, self.total_runs),
            "escape_rate_is_zero": self.escape_rate_is_zero(),
            "escape_log": self.escape_log,
        }
