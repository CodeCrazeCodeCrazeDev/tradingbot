"""
Skill #46: Extreme Value Theory
===============================

Models tail risk using EVT for better VaR and ES estimates
during extreme market conditions.
"""

import numpy as np
from dataclasses import dataclass
from typing import Dict, Optional, List
import logging

logger = logging.getLogger(__name__)


@dataclass
class EVTResult:
    """Extreme Value Theory result."""
    tail_index: float
    scale_parameter: float
    var_evt: float
    es_evt: float
    exceedance_probability: float
    trading_signal: str


class ExtremeValueTheory:
    """Models tail risk using Extreme Value Theory."""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.threshold_percentile = self.config.get('threshold_percentile', 95)
        logger.info("ExtremeValueTheory initialized")
    
    def analyze(self, returns: np.ndarray, confidence: float = 0.99) -> EVTResult:
        """Analyze tail risk using EVT."""
        if len(returns) < 50:
            return self._create_empty_result()
        
        # Get threshold
        threshold = np.percentile(np.abs(returns), self.threshold_percentile)
        
        # Exceedances
        exceedances = np.abs(returns[np.abs(returns) > threshold]) - threshold
        
        if len(exceedances) < 10:
            return self._create_empty_result()
        
        # Fit GPD (simplified MLE)
        xi, beta = self._fit_gpd(exceedances)
        
        # Calculate VaR and ES
        n = len(returns)
        nu = len(exceedances)
        
        var_evt = threshold + (beta / xi) * ((n / nu * (1 - confidence)) ** (-xi) - 1)
        es_evt = var_evt / (1 - xi) + (beta - xi * threshold) / (1 - xi)
        
        # Exceedance probability
        exceed_prob = nu / n
        
        signal = self._generate_signal(var_evt, es_evt, xi)
        
        return EVTResult(
            tail_index=xi,
            scale_parameter=beta,
            var_evt=var_evt,
            es_evt=es_evt,
            exceedance_probability=exceed_prob,
            trading_signal=signal
        )
    
    def _fit_gpd(self, exceedances: np.ndarray) -> tuple:
        """Fit Generalized Pareto Distribution."""
        mean_exc = np.mean(exceedances)
        var_exc = np.var(exceedances)
        
        # Method of moments
        xi = 0.5 * (mean_exc ** 2 / var_exc - 1)
        beta = mean_exc * (1 + xi)
        
        return max(0.01, min(0.5, xi)), max(0.001, beta)
    
    def _generate_signal(self, var: float, es: float, xi: float) -> str:
        """Generate signal."""
        if xi > 0.3:
            return f"HIGH TAIL RISK: VaR {var:.2%}, ES {es:.2%}, heavy tails (ξ={xi:.2f})"
        return f"MODERATE TAIL: VaR {var:.2%}, ES {es:.2%}"
    
    def _create_empty_result(self) -> EVTResult:
        return EVTResult(0, 0, 0, 0, 0, "Insufficient data")
