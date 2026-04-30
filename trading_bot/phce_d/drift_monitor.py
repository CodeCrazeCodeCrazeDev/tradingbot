"""
PHCE-D Module 13: Drift and Degradation Monitor with Post-Promotion Regime Tracker

P1 #13 + #14: Track drift across features, regimes, verifier outputs, and edge.
Post-promotion: compare regime fingerprint at approval time vs current conditions.

Runs asynchronously. Outputs:
- HOLD_PROMOTION
- DEMOTE_TO_RESEARCH
- SUSPEND_HYPOTHESIS

This is necessary once strategies survive paper trading.
"""

from __future__ import annotations

import logging
import math
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Any, Deque, Dict, List, Optional, Tuple

from .core_types import (
    DecisionOutput,
    DriftAction,
    Hypothesis,
    HypothesisStatus,
    VerificationReport,
)

logger = logging.getLogger(__name__)


@dataclass
class DriftMeasurement:
    """A single drift measurement."""
    timestamp: float
    metric_name: str
    reference_value: float  # Value at approval/baseline time
    current_value: float
    drift_pct: float  # (current - reference) / |reference| * 100
    threshold_pct: float
    exceeded: bool


@dataclass
class RegimeFingerprint:
    """Regime conditions at the time of hypothesis approval."""
    hypothesis_id: str
    timestamp: float
    volatility_state: str
    liquidity_state: str
    trend_persistence: float
    correlation_clustering: str
    spread_conditions: str
    # Numerical vector for similarity comparison
    vector: Dict[str, float] = field(default_factory=dict)


@dataclass
class DriftAssessment:
    """Result of a drift assessment for a hypothesis."""
    hypothesis_id: str
    overall_drift_score: float  # 0-1, higher = more drift
    drift_measurements: List[DriftMeasurement]
    regime_similarity: float  # 0-1, 1 = identical to approval regime
    recommended_action: DriftAction
    details: str


class DriftMonitor:
    """
    Module 13: Drift and Degradation Monitor

    Tracks:
    - Feature distribution drift
    - Regime drift
    - Verifier-output drift
    - Paper/live edge decay
    - Realized vs expected edge

    Outputs:
    - HOLD_PROMOTION: Don't promote yet, but don't suspend
    - DEMOTE_TO_RESEARCH: Downgrade from paper-trade to research
    - SUSPEND_HYPOTHESIS: Suspend the hypothesis entirely

    Also includes post-promotion regime tracker (P1 #14):
    Compare the regime fingerprint at approval time against current conditions.
    """

    def __init__(
        self,
        feature_drift_threshold_pct: float = 30.0,
        regime_similarity_threshold: float = 0.7,
        edge_decay_threshold_pct: float = 50.0,
        verifier_drift_threshold_pct: float = 20.0,
        min_observations_for_drift: int = 20,
    ):
        self.feature_drift_threshold = feature_drift_threshold_pct
        self.regime_similarity_threshold = regime_similarity_threshold
        self.edge_decay_threshold = edge_decay_threshold_pct
        self.verifier_drift_threshold = verifier_drift_threshold_pct
        self.min_observations = min_observations_for_drift

        # Baseline measurements per hypothesis
        self._baselines: Dict[str, Dict[str, float]] = {}
        # Regime fingerprints at approval time
        self._approval_fingerprints: Dict[str, RegimeFingerprint] = {}
        # Rolling drift measurements
        self._drift_history: Dict[str, Deque[DriftMeasurement]] = {}
        # Edge tracking
        self._edge_history: Dict[str, Deque[Tuple[float, float]]] = {}  # (timestamp, edge_bps)

        # Statistics
        self.total_assessments = 0
        self.actions_taken: Dict[str, int] = {}

    def record_baseline(
        self,
        hypothesis_id: str,
        feature_values: Dict[str, float],
        regime: Dict[str, Any],
        expected_edge_bps: float,
    ) -> None:
        """
        Record baseline measurements at the time of hypothesis approval.
        """
        self._baselines[hypothesis_id] = dict(feature_values)
        self._baselines[hypothesis_id]["expected_edge_bps"] = expected_edge_bps

        # Record regime fingerprint
        fingerprint = RegimeFingerprint(
            hypothesis_id=hypothesis_id,
            timestamp=time.time(),
            volatility_state=regime.get("volatility_state", "normal"),
            liquidity_state=regime.get("liquidity_state", "normal"),
            trend_persistence=regime.get("trend_persistence", 0.5),
            correlation_clustering=regime.get("correlation_clustering", "dispersed"),
            spread_conditions=regime.get("spread_impact_conditions", "normal"),
            vector={
                "volatility": regime.get("volatility_numeric", 0.33),
                "liquidity": regime.get("liquidity_numeric", 0.33),
                "trend_persistence": regime.get("trend_persistence", 0.5),
                "correlation": regime.get("correlation_numeric", 0.0),
                "spread": regime.get("spread_numeric", 0.33),
            },
        )
        self._approval_fingerprints[hypothesis_id] = fingerprint

        # Initialize edge tracking
        self._edge_history[hypothesis_id] = deque(maxlen=200)
        self._edge_history[hypothesis_id].append((time.time(), expected_edge_bps))

        logger.info(f"Drift baseline recorded for hypothesis {hypothesis_id}")

    def record_edge_observation(
        self,
        hypothesis_id: str,
        realized_edge_bps: float,
        timestamp: Optional[float] = None,
    ) -> None:
        """Record a realized edge observation for decay tracking."""
        if hypothesis_id not in self._edge_history:
            self._edge_history[hypothesis_id] = deque(maxlen=200)
        self._edge_history[hypothesis_id].append(
            (timestamp or time.time(), realized_edge_bps)
        )

    def assess(
        self,
        hypothesis_id: str,
        current_features: Dict[str, float],
        current_regime: Dict[str, Any],
        current_verifier_pass_rate: float = 1.0,
    ) -> DriftAssessment:
        """
        Assess drift for a hypothesis.

        Compares current state against baseline measurements taken at approval time.

        Args:
            hypothesis_id: The hypothesis to assess
            current_features: Current feature values
            current_regime: Current regime state
            current_verifier_pass_rate: Current verifier pass rate (0-1)

        Returns:
            DriftAssessment with recommended action
        """
        start = time.monotonic()
        self.total_assessments += 1

        baseline = self._baselines.get(hypothesis_id)
        if baseline is None:
            return DriftAssessment(
                hypothesis_id=hypothesis_id,
                overall_drift_score=0.0,
                drift_measurements=[],
                regime_similarity=1.0,
                recommended_action=DriftAction.HOLD_PROMOTION,
                details="No baseline recorded — cannot assess drift",
            )

        measurements: List[DriftMeasurement] = []

        # Step 1: Feature distribution drift
        for feature_name, current_val in current_features.items():
            ref_val = baseline.get(feature_name)
            if ref_val is None or ref_val == 0:
                continue
            drift_pct = abs(current_val - ref_val) / abs(ref_val) * 100
            exceeded = drift_pct > self.feature_drift_threshold
            measurements.append(DriftMeasurement(
                timestamp=time.time(),
                metric_name=f"feature_{feature_name}",
                reference_value=ref_val,
                current_value=current_val,
                drift_pct=drift_pct,
                threshold_pct=self.feature_drift_threshold,
                exceeded=exceeded,
            ))

        # Step 2: Edge decay
        expected_edge = baseline.get("expected_edge_bps", 0)
        if expected_edge > 0 and hypothesis_id in self._edge_history:
            recent_edges = list(self._edge_history[hypothesis_id])
            if len(recent_edges) >= self.min_observations_for_drift:
                avg_recent_edge = sum(e for _, e in recent_edges[-20:]) / min(20, len(recent_edges))
                edge_decay_pct = abs(expected_edge - avg_recent_edge) / expected_edge * 100
                measurements.append(DriftMeasurement(
                    timestamp=time.time(),
                    metric_name="edge_decay",
                    reference_value=expected_edge,
                    current_value=avg_recent_edge,
                    drift_pct=edge_decay_pct,
                    threshold_pct=self.edge_decay_threshold,
                    exceeded=edge_decay_pct > self.edge_decay_threshold,
                ))

        # Step 3: Verifier drift
        baseline_pass_rate = 1.0  # At approval, all verifiers passed
        verifier_drift_pct = abs(current_verifier_pass_rate - baseline_pass_rate) / baseline_pass_rate * 100
        measurements.append(DriftMeasurement(
            timestamp=time.time(),
            metric_name="verifier_pass_rate",
            reference_value=baseline_pass_rate,
            current_value=current_verifier_pass_rate,
            drift_pct=verifier_drift_pct,
            threshold_pct=self.verifier_drift_threshold,
            exceeded=verifier_drift_pct > self.verifier_drift_threshold,
        ))

        # Step 4: Regime similarity (post-promotion regime tracker)
        regime_similarity = self._compute_regime_similarity(hypothesis_id, current_regime)

        # Compute overall drift score
        exceeded_count = sum(1 for m in measurements if m.exceeded)
        total_count = len(measurements)
        overall_drift = exceeded_count / max(1, total_count)

        # Add regime dissimilarity to drift score
        regime_dissimilarity = 1.0 - regime_similarity
        overall_drift = (overall_drift + regime_dissimilarity) / 2.0

        # Determine recommended action
        if overall_drift > 0.6:
            action = DriftAction.SUSPEND_HYPOTHESIS
        elif overall_drift > 0.3:
            action = DriftAction.DEMOTE_TO_RESEARCH
        else:
            action = DriftAction.HOLD_PROMOTION

        # Record
        action_key = action.value
        self.actions_taken[action_key] = self.actions_taken.get(action_key, 0) + 1

        if hypothesis_id not in self._drift_history:
            self._drift_history[hypothesis_id] = deque(maxlen=100)
        for m in measurements:
            self._drift_history[hypothesis_id].append(m)

        details = (
            f"drift_score={overall_drift:.2f} "
            f"regime_sim={regime_similarity:.2f} "
            f"exceeded={exceeded_count}/{total_count} "
            f"action={action.value}"
        )

        if action != DriftAction.HOLD_PROMOTION:
            logger.warning(f"DRIFT DETECTED for {hypothesis_id}: {details}")

        return DriftAssessment(
            hypothesis_id=hypothesis_id,
            overall_drift_score=overall_drift,
            drift_measurements=measurements,
            regime_similarity=regime_similarity,
            recommended_action=action,
            details=details,
        )

    def _compute_regime_similarity(
        self,
        hypothesis_id: str,
        current_regime: Dict[str, Any],
    ) -> float:
        """
        Compute cosine similarity between approval regime and current regime.
        Returns 0-1, where 1 = identical regimes.
        """
        fingerprint = self._approval_fingerprints.get(hypothesis_id)
        if fingerprint is None:
            return 1.0  # No fingerprint → assume similar

        # Build current regime vector
        current_vector = {
            "volatility": current_regime.get("volatility_numeric", 0.33),
            "liquidity": current_regime.get("liquidity_numeric", 0.33),
            "trend_persistence": current_regime.get("trend_persistence", 0.5),
            "correlation": current_regime.get("correlation_numeric", 0.0),
            "spread": current_regime.get("spread_numeric", 0.33),
        }

        # Cosine similarity
        ref_vector = fingerprint.vector
        keys = set(ref_vector.keys()) | set(current_vector.keys())

        dot = sum(ref_vector.get(k, 0) * current_vector.get(k, 0) for k in keys)
        ref_norm = math.sqrt(sum(v ** 2 for v in ref_vector.values()))
        cur_norm = math.sqrt(sum(v ** 2 for v in current_vector.values()))

        if ref_norm == 0 or cur_norm == 0:
            return 0.0

        similarity = dot / (ref_norm * cur_norm)
        return max(0.0, min(1.0, similarity))

    def get_stats(self) -> Dict[str, Any]:
        """Return drift monitor statistics."""
        return {
            "total_assessments": self.total_assessments,
            "actions_taken": self.actions_taken,
            "hypotheses_with_baselines": len(self._baselines),
            "hypotheses_with_fingerprints": len(self._approval_fingerprints),
        }
