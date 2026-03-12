"""
Skill #57: Correlation Regime Detector
======================================

Detects changes in correlation regimes for portfolio risk.
"""

import numpy as np
from dataclasses import dataclass
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


@dataclass
class CorrelationRegimeResult:
    """Correlation regime result."""
    current_regime: str
    avg_correlation: float
    correlation_change: float
    regime_stability: float
    trading_signal: str


class CorrelationRegimeDetector:
    """Detects correlation regime changes."""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        logger.info("CorrelationRegimeDetector initialized")
    
    def detect(self, returns_matrix: np.ndarray) -> CorrelationRegimeResult:
        """Detect correlation regime."""
        if returns_matrix.shape[0] < 30 or returns_matrix.shape[1] < 2:
            return self._create_empty_result()
        
        # Recent vs historical correlation
        recent_corr = np.corrcoef(returns_matrix[-20:].T)
        historical_corr = np.corrcoef(returns_matrix[:-20].T)
        
        avg_recent = np.mean(recent_corr[np.triu_indices_from(recent_corr, k=1)])
        avg_historical = np.mean(historical_corr[np.triu_indices_from(historical_corr, k=1)])
        
        change = avg_recent - avg_historical
        
        # Regime classification
        if avg_recent > 0.7:
            regime = "high_correlation"
        elif avg_recent > 0.3:
            regime = "moderate_correlation"
        else:
            regime = "low_correlation"
        
        stability = 1 - abs(change)
        signal = self._generate_signal(regime, avg_recent, change)
        
        return CorrelationRegimeResult(
            current_regime=regime, avg_correlation=avg_recent,
            correlation_change=change, regime_stability=stability,
            trading_signal=signal
        )
    
    def _generate_signal(self, regime: str, corr: float, change: float) -> str:
        if regime == "high_correlation":
            return f"HIGH CORR REGIME: {corr:.2f}, diversification reduced"
        return f"{regime.upper()}: Avg corr {corr:.2f}, change {change:+.2f}"
    
    def _create_empty_result(self) -> CorrelationRegimeResult:
        return CorrelationRegimeResult("unknown", 0, 0, 0, "Insufficient data")
