"""
Institutional Scientific Metrics (UCA V5)
========================================

Tracks the quality, survival, and economic value of the scientific reasoning process,
providing feedback for the self-improvement loop.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Any, Optional
import logging
import numpy as np

logger = logging.getLogger(__name__)

@dataclass
class ScientificMetrics:
    # Hypothesis Quality
    avg_posterior: float = 0.0
    avg_novelty: float = 0.0
    avg_vfe: float = 0.0
    avg_validation_score: float = 0.0

    # Lifecycle Efficiency
    survival_rate: float = 0.0
    rejection_rate: float = 0.0
    avg_steps_to_retirement: float = 0.0

    # Counts
    total_hypotheses: int = 0
    confirmed_count: int = 0
    rejected_count: int = 0
    institutionalized_count: int = 0
    inconclusive_count: int = 0

    # Economic & Scientific Value
    research_efficiency_ratio: float = 0.0 # Value / Cost
    ece: float = 1.0 # Expected Calibration Error

    # Latency Tracking (First-class observability)
    csc_stage_latency: Dict[str, float] = field(default_factory=dict)
    router_dispatch_latency: float = 0.0
    hms_latency: float = 0.0
    swarm_latency: float = 0.0
    gate_latency: float = 0.0
    end_to_end_latency: float = 0.0
    queue_depth: int = 0
    memory_growth_bytes: float = 0.0
    retry_counts: int = 0
    failure_counts: int = 0

    # Self-Improvement
    bottlenecks_detected: List[str] = field(default_factory=list)
    last_update: datetime = field(default_factory=datetime.now)

    @property
    def total_institutionalized_knowledge(self) -> int:
        return self.institutionalized_count

    def update_from_registry(self, registry: Dict[str, Any]):
        """Update metrics based on the current state of the SRE registry."""
        total = len(registry)
        self.total_hypotheses = total
        if total == 0:
            return

        counts = {
            "CONFIRMED": 0,
            "INSTITUTIONALIZED": 0,
            "REJECTED": 0,
            "INCONCLUSIVE": 0
        }

        sum_posterior = 0.0
        sum_novelty = 0.0
        sum_vfe = 0.0
        sum_val = 0.0

        for hyp in registry.values():
            sum_posterior += getattr(hyp, 'posterior', 0.5)
            sum_novelty += getattr(hyp, 'novelty_score', 0.0)
            sum_vfe += getattr(hyp, 'vfe', 0.0)
            sum_val += getattr(hyp, 'validation_score', 0.0)

            # Check both attribute and string representations safely
            state_name = ""
            if hasattr(hyp, 'state'):
                if hasattr(hyp.state, 'name'):
                    state_name = hyp.state.name
                else:
                    state_name = str(hyp.state)

            if state_name in counts:
                counts[state_name] += 1

        self.confirmed_count = counts["CONFIRMED"]
        self.institutionalized_count = counts["INSTITUTIONALIZED"]
        self.rejected_count = counts["REJECTED"]
        self.inconclusive_count = counts["INCONCLUSIVE"]

        self.avg_posterior = sum_posterior / total
        self.avg_novelty = sum_novelty / total
        self.avg_vfe = sum_vfe / total
        self.avg_validation_score = sum_val / total

        self.rejection_rate = self.rejected_count / total
        self.survival_rate = (self.confirmed_count + self.institutionalized_count) / total
        self._detect_bottlenecks()

    def _detect_bottlenecks(self):
        """Identifies systemic weaknesses in the hypothesis ecosystem."""
        self.bottlenecks_detected = []

        if self.total_hypotheses > 20:
            if self.survival_rate < 0.05:
                self.bottlenecks_detected.append("GENERATION_NOISE: Too many low-quality hypotheses generated.")

            if self.rejection_rate > 0.8:
                self.bottlenecks_detected.append("FILTERING_STRICTNESS: Evidence collection might be too hostile or priors too low.")

            if self.avg_validation_score > 0.7 and self.confirmed_count + self.institutionalized_count < 2:
                self.bottlenecks_detected.append("PROMOTION_FRICTION: Hypotheses pass validation but fail to reach confirmation.")

    @property
    def total_institutionalized_knowledge(self) -> int:
        return self.institutionalized_count

    @property
    def total_institutionalized_knowledge(self) -> int:
        return self.institutionalized_count

        # Run bottleneck detection
        self.detect_bottlenecks()

    def detect_bottlenecks(self):
        """Identifies systemic weaknesses in the hypothesis ecosystem."""
        self.bottlenecks_detected = []

        if self.total_hypotheses > 20:
            if self.survival_rate < 0.05:
                self.bottlenecks_detected.append("GENERATION_NOISE")

            if self.rejection_rate > 0.8:
                self.bottlenecks_detected.append("FILTERING_STRICTNESS")

            if self.avg_validation_score > 0.7 and self.confirmed_count < 2:
                self.bottlenecks_detected.append("PROMOTION_FRICTION")

        # Detect bottlenecks on update
        self.detect_bottlenecks()

    def detect_bottlenecks(self):
        """Identifies systemic weaknesses in the hypothesis ecosystem."""
        self.bottlenecks_detected = []

        if self.total_hypotheses > 20:
            if self.survival_rate < 0.05:
                self.bottlenecks_detected.append("GENERATION_NOISE")

            if self.rejection_rate > 0.8:
                self.bottlenecks_detected.append("FILTERING_STRICTNESS")

            if self.avg_validation_score > 0.7 and self.confirmed_count < 2:
                self.bottlenecks_detected.append("PROMOTION_FRICTION")

        self.detect_bottlenecks()

        # Drive first-class bottleneck analysis
        self.detect_bottlenecks()

    def get_summary(self) -> Dict[str, Any]:
        return {
            "survival_rate": self.survival_rate,
            "rejection_rate": self.rejection_rate,
            "avg_posterior": self.avg_posterior,
            "total_knowledge_units": self.institutionalized_count,
            "timestamp": datetime.now().isoformat()
        }


class BottleneckDetector:
    """Specialized component for identifying systemic constraints and friction points."""
    @staticmethod
    def analyze(metrics: Any) -> List[str]:
        bottlenecks = []
        if metrics.total_hypotheses > 20:
            if metrics.survival_rate < 0.05:
                bottlenecks.append("GENERATION_NOISE")

            if metrics.rejection_rate > 0.8:
                bottlenecks.append("FILTERING_STRICTNESS")

            if metrics.avg_validation_score > 0.7 and metrics.confirmed_count < 2:
                bottlenecks.append("PROMOTION_FRICTION")
        return bottlenecks


@dataclass
class ScientificAuditMetrics:
    total_hypotheses: int = 0
    confirmed_count: int = 0
    rejected_count: int = 0
    institutionalized_count: int = 0
    survival_rate: float = 0.0
    rejection_rate: float = 0.0
    avg_posterior: float = 0.0
    avg_validation_score: float = 0.0
    bottlenecks_detected: List[str] = field(default_factory=list)
    last_update: datetime = field(default_factory=datetime.now)

    def detect_bottlenecks(self):
        """Identifies systemic weaknesses in the hypothesis ecosystem."""
        self.bottlenecks_detected = []

        if self.total_hypotheses > 20:
            if self.survival_rate < 0.05:
                self.bottlenecks_detected.append("GENERATION_NOISE")

            if self.rejection_rate > 0.8:
                self.bottlenecks_detected.append("FILTERING_STRICTNESS")

            if self.avg_validation_score > 0.7 and self.confirmed_count < 2:
                self.bottlenecks_detected.append("PROMOTION_FRICTION")

    def get_summary(self) -> Dict[str, Any]:
        return {
            "total_hypotheses": self.total_hypotheses,
            "survival_rate": self.survival_rate,
            "rejection_rate": self.rejection_rate,
            "avg_posterior": self.avg_posterior,
            "knowledge_units": self.institutionalized_count,
            "bottlenecks": self.bottlenecks_detected,
            "timestamp": self.last_update.isoformat()
        }
