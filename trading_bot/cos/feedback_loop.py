"""
Reality Calibration Loop — Compare, Correct, Evolve
=====================================================

The "closing" of the COS loop. This is what makes the system recurrent
and recursive — every prediction is checked against reality, every gap
produces a correction, and every correction makes the next prediction
better.

The loop:
    1. OBSERVE:   Collect actual outcomes from execution
    2. COMPARE:   Match predictions (from DecisionTrace) against reality
    3. CORRECT:   Generate CalibrationDeltas — adjustments to simulation model
    4. UPDATE:    Apply corrections to Cognition Store and Simulation Engine
    5. EVOLVE:    Extract meta-cognitive insights (the loop learning about itself)

This is the controlled, validated, reality-calibrated simulation loop
that ensures the COS becomes smarter over time in a STRUCTURED way —
not by accumulating raw data, but by closing the gap between
imagination and reality.

Integration with existing systems:
    - trading_bot.feedback.analyzer.FeedbackAnalyzer → trade performance data
    - trading_bot.world_model.experience_replay       → experience storage
"""

from __future__ import annotations

import logging
import time
from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

import numpy as np

from .types import (
    CalibrationDelta,
    COSConfig,
    DecisionTrace,
    IdeaStatus,
    KnowledgeCategory,
    KnowledgeNode,
    RealityCheck,
    SimulationFidelity,
)

logger = logging.getLogger(__name__)


class RealityCalibrationLoop:
    """
    Closes the COS loop by comparing predictions to reality and
    generating corrections.

    This is the engine that makes the COS "smarter over time":
      - Every RealityCheck measures the prediction-reality gap
      - Every CalibrationDelta corrects the simulation model
      - Every meta-cognitive insight improves the loop itself

    The loop is:
        CLOSED:    Every execution result feeds back as calibration input
        RECURRENT: Calibration state persists across cycles
        RECURSIVE: Meta-cognitive corrections improve the correction process
    """

    def __init__(self, config: COSConfig, cognition_store=None, simulation_engine=None, decision_support=None):
        self.config = config
        self.cognition_store = cognition_store
        self.simulation_engine = simulation_engine
        self.decision_support = decision_support

        # Pending traces awaiting reality checks: trace_id → DecisionTrace
        self._pending_traces: Dict[str, DecisionTrace] = {}

        # Completed reality checks: check_id → RealityCheck
        self._reality_checks: Dict[str, RealityCheck] = {}

        # Calibration deltas: delta_id → CalibrationDelta
        self._calibration_deltas: Dict[str, CalibrationDelta] = {}

        # Rolling prediction quality: regime → list of quality scores
        self._prediction_quality_history: Dict[str, List[float]] = defaultdict(list)

        # Global calibration score (rolling average)
        self._global_calibration_score: float = 0.0
        self._calibration_sample_count: int = 0

        # External feedback analyzer reference
        self._feedback_analyzer = None

        # Stats
        self._checks_performed = 0
        self._deltas_generated = 0
        self._deltas_applied = 0

        logger.info(
            f"RealityCalibrationLoop initialized | "
            f"interval={config.reality_check_interval_seconds}s | "
            f"learning_rate={config.calibration_learning_rate}"
        )

    # ── Public API ────────────────────────────────────────────────────────

    def register_decision(self, trace: DecisionTrace):
        """
        Register a decision trace for later reality checking.

        Called by DecisionSupportSystem when a decision is made.
        The trace will be checked against reality once outcomes are available.
        """
        self._pending_traces[trace.trace_id] = trace
        logger.debug(f"Registered trace {trace.trace_id} for reality checking")

    def check_reality(
        self,
        trace_id: str,
        actual_pnl: float,
        actual_risk: float,
        actual_regime: str = "",
    ) -> Optional[RealityCheck]:
        """
        Compare a decision's predicted outcome against actual outcome.

        This is the core "compare" step of the loop.
        """
        trace = self._pending_traces.get(trace_id)
        if trace is None:
            logger.warning(f"Trace {trace_id} not found for reality check")
            return None

        # Build reality check
        check = RealityCheck(
            trace_id=trace_id,
            predicted_pnl=trace.expected_pnl,
            predicted_risk=trace.expected_risk,
            predicted_regime="",  # filled from simulation context if available
            actual_pnl=actual_pnl,
            actual_risk=actual_risk,
            actual_regime=actual_regime,
            pnl_gap=trace.expected_pnl - actual_pnl,
            risk_gap=trace.expected_risk - actual_risk,
            regime_match=True,  # simplified
            was_profitable=actual_pnl > 0,
            was_expected_profitable=trace.expected_pnl > 0,
            node_ids=trace.knowledge_node_ids,
            simulation_ids=trace.simulation_ids,
        )

        # Compute prediction quality
        check.prediction_quality = self._compute_prediction_quality(check)

        # Store
        self._reality_checks[check.check_id] = check
        self._pending_traces.pop(trace_id, None)

        # Update rolling quality
        regime = actual_regime or "default"
        self._prediction_quality_history[regime].append(check.prediction_quality)
        self._update_global_calibration(check.prediction_quality)

        # Resolve the decision in DecisionSupport
        if self.decision_support is not None:
            self.decision_support.resolve_decision(trace_id, actual_pnl, actual_risk)

        # Validate knowledge nodes that were used
        self._validate_knowledge_nodes(check)

        # Update simulation calibration
        self._update_simulation_calibration(check, regime)

        self._checks_performed += 1

        logger.info(
            f"Reality check | trace={trace_id} | "
            f"predicted_pnl={check.predicted_pnl:.4f} | actual_pnl={actual_pnl:.4f} | "
            f"gap={check.pnl_gap:.4f} | quality={check.prediction_quality:.2f}"
        )

        return check

    def generate_calibration_delta(self, check: RealityCheck) -> CalibrationDelta:
        """
        Generate a correction from a reality check.

        This is the "correct" step of the loop — translating a
        prediction-reality gap into actionable adjustments.
        """
        # Classify the error
        error_type = self._classify_error(check)
        error_magnitude = abs(check.pnl_gap) + abs(check.risk_gap)

        # Build corrections
        corrections = self._build_corrections(check, error_type)

        # Identify which knowledge nodes need updating
        node_ids_to_update = check.node_ids[:]

        # Compute simulation parameter adjustments
        sim_param_deltas = self._compute_sim_param_deltas(check)

        # Meta-cognitive correction (should the COS itself change?)
        meta_correction = None
        if self.config.enable_meta_cognition:
            meta_correction = self._meta_cognitive_correction(check)

        delta = CalibrationDelta(
            check_id=check.check_id,
            error_type=error_type,
            error_magnitude=error_magnitude,
            corrections=corrections,
            node_ids_to_update=node_ids_to_update,
            simulation_param_deltas=sim_param_deltas,
            meta_cognitive_correction=meta_correction,
        )

        self._calibration_deltas[delta.delta_id] = delta
        self._deltas_generated += 1

        logger.info(
            f"Calibration delta | error_type={error_type} | "
            f"magnitude={error_magnitude:.4f} | "
            f"corrections={len(corrections)} | "
            f"sim_deltas={len(sim_param_deltas)}"
        )

        return delta

    def apply_calibration_delta(self, delta: CalibrationDelta) -> bool:
        """
        Apply a calibration delta to the system.

        This is where the loop actually "closes" — corrections are applied
        to the simulation model and knowledge base, making the next
        prediction better.
        """
        # 1. Update knowledge nodes
        if self.cognition_store is not None:
            for nid in delta.node_ids_to_update:
                # The validation score was already updated in check_reality
                # Here we update structured data based on corrections
                node = self.cognition_store._nodes.get(nid)
                if node is not None:
                    for key, value in delta.corrections.items():
                        if key in node.structured_data:
                            # Adjust the value toward reality
                            old_val = node.structured_data[key]
                            if isinstance(old_val, (int, float)) and isinstance(value, (int, float)):
                                lr = self.config.calibration_learning_rate
                                node.structured_data[key] = old_val + lr * (value - old_val)
                    node.updated_at = datetime.utcnow()

        # 2. Update simulation parameters
        if self.simulation_engine is not None:
            # The simulation engine's calibration is updated via
            # update_calibration() which was called in check_reality
            # Additional param deltas can be applied to config
            for param, delta_val in delta.simulation_param_deltas.items():
                logger.debug(f"Sim param delta: {param} += {delta_val:.4f}")

        # 3. Apply meta-cognitive corrections
        if delta.meta_cognitive_correction and self.config.enable_meta_cognition:
            self._apply_meta_correction(delta.meta_cognitive_correction)

        delta.applied = True
        delta.applied_at = datetime.utcnow()
        self._deltas_applied += 1

        logger.info(f"Applied calibration delta {delta.delta_id}")
        return True

    def run_calibration_cycle(self) -> List[CalibrationDelta]:
        """
        Run a full calibration cycle over all pending reality checks.

        Returns the list of generated calibration deltas.
        """
        deltas = []

        # Process any new reality checks
        for check_id, check in list(self._reality_checks.items()):
            if check.prediction_quality < 0.8:  # only correct if prediction was off
                delta = self.generate_calibration_delta(check)
                self.apply_calibration_delta(delta)
                deltas.append(delta)

        # Extract meta-cognitive insights from accumulated calibration data
        if self.config.enable_meta_cognition and len(deltas) > 0:
            self._extract_meta_insights(deltas)

        return deltas

    # ── Batch Reality Checking ─────────────────────────────────────────────

    def check_reality_batch(
        self,
        outcomes: List[Dict[str, Any]],
    ) -> List[RealityCheck]:
        """
        Check multiple decisions against reality at once.

        Args:
            outcomes: List of dicts with keys: trace_id, actual_pnl, actual_risk, actual_regime
        """
        checks = []
        for outcome in outcomes:
            check = self.check_reality(
                trace_id=outcome["trace_id"],
                actual_pnl=outcome.get("actual_pnl", 0.0),
                actual_risk=outcome.get("actual_risk", 0.0),
                actual_regime=outcome.get("actual_regime", ""),
            )
            if check is not None:
                checks.append(check)
        return checks

    # ── External Integration ──────────────────────────────────────────────

    def connect_feedback_analyzer(self, analyzer):
        """Connect to the existing FeedbackAnalyzer."""
        self._feedback_analyzer = analyzer
        logger.info("Connected FeedbackAnalyzer")

    def ingest_trade_performance(self, performances: List[Dict[str, Any]]):
        """
        Ingest trade performance data from the execution layer.

        Automatically matches trades to pending decision traces and
        runs reality checks.
        """
        for perf in performances:
            # Try to find a matching pending trace
            strategy = perf.get("strategy", "")
            symbol = perf.get("symbol", "")
            pnl = perf.get("pnl", 0.0)
            regime = perf.get("market_regime", "")

            # Match by closest timestamp or strategy
            matched_trace_id = self._find_matching_trace(strategy, symbol)

            if matched_trace_id:
                self.check_reality(
                    trace_id=matched_trace_id,
                    actual_pnl=pnl,
                    actual_risk=abs(pnl) * 0.5,  # approximate risk from PnL
                    actual_regime=regime,
                )

    # ── Internal ──────────────────────────────────────────────────────────

    def _compute_prediction_quality(self, check: RealityCheck) -> float:
        """
        Score how well the prediction matched reality.

        1.0 = perfect prediction
        0.0 = completely wrong
        """
        # Direction accuracy
        direction_correct = check.was_profitable == check.was_expected_profitable
        direction_score = 1.0 if direction_correct else 0.0

        # Magnitude accuracy (normalized)
        if abs(check.predicted_pnl) + abs(check.actual_pnl) > 1e-8:
            magnitude_error = abs(check.pnl_gap) / (abs(check.predicted_pnl) + abs(check.actual_pnl))
            magnitude_score = max(0, 1.0 - magnitude_error)
        else:
            magnitude_score = 1.0  # both near zero = accurate

        # Risk accuracy
        risk_error = abs(check.risk_gap) / max(abs(check.predicted_risk), 1e-6)
        risk_score = max(0, 1.0 - min(1.0, risk_error))

        # Composite (direction is most important)
        quality = 0.5 * direction_score + 0.3 * magnitude_score + 0.2 * risk_score
        return float(quality)

    def _classify_error(self, check: RealityCheck) -> str:
        """Classify the type of prediction error."""
        if not (check.was_profitable == check.was_expected_profitable):
            return "direction_mismatch"

        if abs(check.pnl_gap) > abs(check.predicted_pnl) * 0.5:
            if check.pnl_gap > 0:
                return "pnl_underestimate"
            else:
                return "pnl_overestimate"

        if abs(check.risk_gap) > abs(check.predicted_risk) * 0.5:
            if check.risk_gap > 0:
                return "risk_underestimate"
            else:
                return "risk_overestimate"

        if not check.regime_match:
            return "regime_mismatch"

        return "minor_deviation"

    def _build_corrections(self, check: RealityCheck, error_type: str) -> Dict[str, Any]:
        """Build specific corrections based on the error type."""
        corrections = {}

        if error_type == "direction_mismatch":
            corrections["direction_bias"] = -np.sign(check.pnl_gap)
            corrections["confidence_discount"] = 0.1  # reduce confidence for similar scenarios

        elif error_type == "pnl_overestimate":
            corrections["pnl_adjustment"] = -abs(check.pnl_gap) * self.config.calibration_learning_rate
            corrections["optimism_bias"] = -0.05

        elif error_type == "pnl_underestimate":
            corrections["pnl_adjustment"] = abs(check.pnl_gap) * self.config.calibration_learning_rate
            corrections["pessimism_bias"] = -0.05

        elif error_type == "risk_underestimate":
            corrections["risk_multiplier"] = 1.0 + self.config.calibration_learning_rate
            corrections["risk_floor"] = abs(check.actual_risk) * 0.8

        elif error_type == "risk_overestimate":
            corrections["risk_multiplier"] = 1.0 - self.config.calibration_learning_rate * 0.5

        elif error_type == "regime_mismatch":
            corrections["regime_detection_sensitivity"] = 0.1

        return corrections

    def _compute_sim_param_deltas(self, check: RealityCheck) -> Dict[str, float]:
        """Compute adjustments to simulation parameters."""
        deltas = {}
        lr = self.config.calibration_learning_rate

        # Volatility adjustment
        if abs(check.risk_gap) > 0.01:
            deltas["base_volatility"] = np.sign(check.risk_gap) * abs(check.risk_gap) * lr

        # Drift adjustment
        if abs(check.pnl_gap) > 0.01:
            deltas["drift_correction"] = -check.pnl_gap * lr

        return deltas

    def _validate_knowledge_nodes(self, check: RealityCheck):
        """Update validation scores of knowledge nodes based on reality check."""
        if self.cognition_store is None:
            return

        # Nodes that contributed to a correct prediction get positive validation
        # Nodes that contributed to a wrong prediction get negative validation
        validation_score = check.prediction_quality * 2 - 1  # map [0,1] → [-1,1]

        for nid in check.node_ids:
            self.cognition_store.validate(nid, validation_score)

    def _update_simulation_calibration(self, check: RealityCheck, regime: str):
        """Update the simulation engine's calibration tracking."""
        if self.simulation_engine is None:
            return

        self.simulation_engine.update_calibration(
            regime=regime,
            predicted_pnl=check.predicted_pnl,
            actual_pnl=check.actual_pnl,
        )

    def _update_global_calibration(self, quality: float):
        """Update the rolling global calibration score."""
        n = self._calibration_sample_count
        self._global_calibration_score = (
            self._global_calibration_score * n + quality
        ) / (n + 1)
        self._calibration_sample_count += 1

    def _meta_cognitive_correction(self, check: RealityCheck) -> Optional[Dict[str, Any]]:
        """
        Generate a meta-cognitive correction — the loop learning about itself.

        Examples:
          - "We consistently overestimate in volatile regimes → reduce confidence in volatile"
          - "Direction predictions are accurate but magnitude is off → focus on magnitude calibration"
        """
        regime = check.actual_regime or "default"
        history = self._prediction_quality_history.get(regime, [])

        if len(history) < 5:
            return None

        recent_quality = np.mean(history[-5:])
        overall_quality = self._global_calibration_score

        correction = {}

        # Is this regime systematically harder?
        if recent_quality < overall_quality - 0.15:
            correction["confidence_discount_regime"] = {
                "regime": regime,
                "discount": 0.2,
                "reason": f"Systematically lower prediction quality ({recent_quality:.2f}) "
                          f"vs overall ({overall_quality:.2f})",
            }

        # Is direction accuracy good but magnitude poor?
        direction_correct = check.was_profitable == check.was_expected_profitable
        magnitude_off = abs(check.pnl_gap) > abs(check.predicted_pnl) * 0.3

        if direction_correct and magnitude_off:
            correction["focus_area"] = {
                "area": "magnitude_calibration",
                "reason": "Direction predictions accurate but magnitude consistently off",
            }

        return correction if correction else None

    def _apply_meta_correction(self, correction: Dict[str, Any]):
        """Apply a meta-cognitive correction to the COS itself."""
        if "confidence_discount_regime" in correction:
            disc = correction["confidence_discount_regime"]
            # Store as meta-cognitive knowledge
            if self.cognition_store is not None:
                node = KnowledgeNode(
                    category=KnowledgeCategory.META_COGNITIVE,
                    title=f"Confidence discount: {disc['regime']}",
                    content=disc["reason"],
                    structured_data=disc,
                    source="meta_cognitive_correction",
                )
                self.cognition_store.ingest(node)

        if "focus_area" in correction:
            focus = correction["focus_area"]
            if self.cognition_store is not None:
                node = KnowledgeNode(
                    category=KnowledgeCategory.META_COGNITIVE,
                    title=f"Calibration focus: {focus['area']}",
                    content=focus["reason"],
                    structured_data=focus,
                    source="meta_cognitive_correction",
                )
                self.cognition_store.ingest(node)

    def _extract_meta_insights(self, deltas: List[CalibrationDelta]):
        """
        Extract high-level insights from accumulated calibration data.

        This is the "recursive" part — the loop generates knowledge
        about its own operation, which feeds back into future cycles.
        """
        if self.cognition_store is None:
            return

        # Analyze error patterns
        error_types = [d.error_type for d in deltas]
        error_counts = defaultdict(int)
        for et in error_types:
            error_counts[et] += 1

        if len(deltas) >= 3:
            dominant_error = max(error_counts, key=error_counts.get)
            node = KnowledgeNode(
                category=KnowledgeCategory.META_COGNITIVE,
                title=f"Dominant error pattern: {dominant_error}",
                content=f"Over {len(deltas)} recent calibrations, the dominant error type "
                        f"is '{dominant_error}' ({error_counts[dominant_error]}/{len(deltas)}). "
                        f"This suggests the simulation model needs adjustment in this area.",
                structured_data={
                    "dominant_error": dominant_error,
                    "error_distribution": dict(error_counts),
                    "sample_size": len(deltas),
                    "global_calibration": self._global_calibration_score,
                },
                source="meta_cognitive_insight",
            )
            self.cognition_store.ingest(node)

    def _find_matching_trace(self, strategy: str, symbol: str) -> Optional[str]:
        """Find a pending trace that matches a trade outcome."""
        # Simple matching: find the oldest pending trace
        # In production, this would match by strategy, symbol, and timestamp
        for trace_id, trace in self._pending_traces.items():
            return trace_id  # return first available
        return None

    # ── Stats ─────────────────────────────────────────────────────────────

    def stats(self) -> Dict[str, Any]:
        """Return feedback loop statistics."""
        regime_quality = {
            r: float(np.mean(scores[-10:])) if scores else 0.0
            for r, scores in self._prediction_quality_history.items()
        }

        return {
            "pending_traces": len(self._pending_traces),
            "reality_checks_performed": self._checks_performed,
            "calibration_deltas_generated": self._deltas_generated,
            "calibration_deltas_applied": self._deltas_applied,
            "global_calibration_score": self._global_calibration_score,
            "calibration_sample_count": self._calibration_sample_count,
            "regime_prediction_quality": regime_quality,
            "feedback_analyzer_connected": self._feedback_analyzer is not None,
        }
