"""
Tracks the quality, survival, and economic value of the scientific reasoning process.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)

@dataclass
class ScientificMetrics:
    # Hypothesis Quality
    avg_posterior: float = 0.0
    avg_novelty: float = 0.0
    avg_vfe: float = 0.0

    # Lifecycle Efficiency
    survival_rate: float = 0.0
    avg_steps_to_retirement: float = 0.0
    rejection_rate: float = 0.0

    # Economic & Scientific Value
    total_confirmed_hypotheses: int = 0
    total_institutionalized_knowledge: int = 0
    research_efficiency_ratio: float = 0.0 # Value / Cost

    # Calibration
    ece: float = 1.0 # Expected Calibration Error

    last_reset: datetime = field(default_factory=datetime.now)

    def update_from_registry(self, registry: Dict[str, Any]):
        """Update metrics based on the current state of the SRE registry."""
        total = len(registry)
        if total == 0:
            return

        confirmed = 0
        institutionalized = 0
        rejected = 0
        sum_posterior = 0.0
        sum_novelty = 0.0
        sum_vfe = 0.0

        for hyp in registry.values():
            sum_posterior += hyp.posterior
            sum_novelty += hyp.novelty_score
            sum_vfe += hyp.vfe

            if hyp.state.name == "CONFIRMED":
                confirmed += 1
            elif hyp.state.name == "INSTITUTIONALIZED":
                institutionalized += 1
            elif hyp.state.name == "REJECTED":
                rejected += 1

        self.avg_posterior = sum_posterior / total
        self.avg_novelty = sum_novelty / total
        self.avg_vfe = sum_vfe / total
        self.total_confirmed_hypotheses = confirmed
        self.total_institutionalized_knowledge = institutionalized
        self.rejection_rate = rejected / total
        self.survival_rate = (confirmed + institutionalized) / total if total > 0 else 0.0

        logger.info(f"Scientific Metrics Updated: Survival Rate {self.survival_rate:.2f}, Avg Posterior {self.avg_posterior:.2f}")

    def get_summary(self) -> Dict[str, Any]:
        return {
            "survival_rate": self.survival_rate,
            "rejection_rate": self.rejection_rate,
            "avg_posterior": self.avg_posterior,
            "total_knowledge_units": self.total_institutionalized_knowledge,
            "timestamp": datetime.now().isoformat()
        }
Scientific Performance Metrics - AlphaAlgo Audit 2026
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any
from datetime import datetime

@dataclass
class ScientificAuditMetrics:
    total_hypotheses: int = 0
    confirmed_count: int = 0
    rejected_count: int = 0
    institutionalized_count: int = 0

    # Quality metrics
    avg_posterior: float = 0.0
    avg_novelty: float = 0.0
    avg_validation_score: float = 0.0

    # Efficiency metrics
    avg_discovery_time: float = 0.0 # seconds from obs to final state

    # Self-improvement triggers
    bottlenecks_detected: List[str] = field(default_factory=list)

    def calculate_survival_rate(self) -> float:
        if self.total_hypotheses == 0: return 0.0
        return (self.confirmed_count + self.institutionalized_count) / self.total_hypotheses

    def detect_bottlenecks(self):
        if self.total_hypotheses > 10 and self.calculate_survival_rate() < 0.1:
            self.bottlenecks_detected.append("High Rejection Rate: Generation logic may be too noisy.")
        if self.avg_validation_score > 0.8 and self.confirmed_count < 2:
            self.bottlenecks_detected.append("Promotion Bottleneck: Validation is passing but hypotheses are not being confirmed.")
