"""
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
