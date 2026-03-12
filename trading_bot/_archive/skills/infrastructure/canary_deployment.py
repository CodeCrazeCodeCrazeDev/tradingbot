"""
Skill #90: Canary Deployment System
===================================

Gradually rolls out new strategies with automatic rollback.
"""

from dataclasses import dataclass
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


@dataclass
class CanaryResult:
    """Canary deployment result."""
    canary_percentage: float
    canary_performance: float
    baseline_performance: float
    should_promote: bool
    trading_signal: str


class CanaryDeploymentSystem:
    """Canary deployment for strategies."""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.canary_percentage = 0.0
        self.canary_strategy = None
        self.baseline_strategy = None
        logger.info("CanaryDeploymentSystem initialized")
    
    def start_canary(self, canary: str, baseline: str, initial_pct: float = 0.05):
        """Start canary deployment."""
        self.canary_strategy = canary
        self.baseline_strategy = baseline
        self.canary_percentage = initial_pct
    
    def evaluate(self, canary_perf: float, baseline_perf: float) -> CanaryResult:
        """Evaluate canary performance."""
        should_promote = canary_perf > baseline_perf * 0.95  # Within 5%
        
        if should_promote and self.canary_percentage < 1.0:
            self.canary_percentage = min(1.0, self.canary_percentage * 2)
        elif not should_promote:
            self.canary_percentage = 0  # Rollback
        
        return CanaryResult(
            canary_percentage=self.canary_percentage, canary_performance=canary_perf,
            baseline_performance=baseline_perf, should_promote=should_promote,
            trading_signal=f"CANARY: {self.canary_percentage:.0%} traffic, {'promoting' if should_promote else 'rolling back'}"
        )
