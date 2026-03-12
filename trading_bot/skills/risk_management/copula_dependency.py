"""
Skill #47: Copula-Based Dependency
==================================

Models non-linear dependencies between assets using copulas.
"""

import numpy as np
from dataclasses import dataclass
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


@dataclass
class CopulaResult:
    """Copula dependency result."""
    copula_type: str
    tail_dependence_lower: float
    tail_dependence_upper: float
    kendall_tau: float
    joint_var: float
    trading_signal: str


class CopulaBasedDependency:
    """Models dependencies using copulas."""
    
    def __init__(self, config: Optional[Dict] = None):
        try:
            self.config = config or {}
            logger.info("CopulaBasedDependency initialized")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def analyze(self, returns1: np.ndarray, returns2: np.ndarray) -> CopulaResult:
        """Analyze dependency using copulas."""
        try:
            if len(returns1) < 30 or len(returns2) < 30:
                return self._create_empty_result()
        
            # Kendall's tau
            tau = self._kendall_tau(returns1, returns2)
        
            # Estimate tail dependence
            lower_tail = self._estimate_tail_dependence(returns1, returns2, lower=True)
            upper_tail = self._estimate_tail_dependence(returns1, returns2, lower=False)
        
            # Select copula type
            if lower_tail > 0.3:
                copula_type = "clayton"
            elif upper_tail > 0.3:
                copula_type = "gumbel"
            else:
                copula_type = "gaussian"
        
            # Joint VaR
            joint_var = self._calculate_joint_var(returns1, returns2, tau)
        
            signal = self._generate_signal(copula_type, lower_tail, upper_tail)
        
            return CopulaResult(
                copula_type=copula_type,
                tail_dependence_lower=lower_tail,
                tail_dependence_upper=upper_tail,
                kendall_tau=tau,
                joint_var=joint_var,
                trading_signal=signal
            )
        except Exception as e:
            logger.error(f"Error in analyze: {e}")
            raise
    
    def _kendall_tau(self, x: np.ndarray, y: np.ndarray) -> float:
        """Calculate Kendall's tau."""
        try:
            n = len(x)
            concordant = discordant = 0
            for i in range(n):
                for j in range(i + 1, n):
                    if (x[i] - x[j]) * (y[i] - y[j]) > 0:
                        concordant += 1
                    elif (x[i] - x[j]) * (y[i] - y[j]) < 0:
                        discordant += 1
            return (concordant - discordant) / (n * (n - 1) / 2)
        except Exception as e:
            logger.error(f"Error in _kendall_tau: {e}")
            raise
    
    def _estimate_tail_dependence(self, x: np.ndarray, y: np.ndarray, lower: bool) -> float:
        """Estimate tail dependence coefficient."""
        try:
            q = 0.1 if lower else 0.9
            threshold_x = np.percentile(x, q * 100 if lower else (1 - q) * 100)
            threshold_y = np.percentile(y, q * 100 if lower else (1 - q) * 100)
        
            if lower:
                joint = np.sum((x < threshold_x) & (y < threshold_y))
                marginal = np.sum(x < threshold_x)
            else:
                joint = np.sum((x > threshold_x) & (y > threshold_y))
                marginal = np.sum(x > threshold_x)
        
            return joint / (marginal + 1e-10)
        except Exception as e:
            logger.error(f"Error in _estimate_tail_dependence: {e}")
            raise
    
    def _calculate_joint_var(self, x: np.ndarray, y: np.ndarray, tau: float) -> float:
        """Calculate joint VaR."""
        try:
            combined = x + y
            return np.percentile(combined, 5)
        except Exception as e:
            logger.error(f"Error in _calculate_joint_var: {e}")
            raise
    
    def _generate_signal(self, copula: str, lower: float, upper: float) -> str:
        """Generate signal."""
        try:
            if lower > 0.3:
                return f"HIGH CRASH DEPENDENCE: {copula} copula, lower tail {lower:.0%}"
            elif upper > 0.3:
                return f"HIGH BOOM DEPENDENCE: {copula} copula, upper tail {upper:.0%}"
            return f"MODERATE DEPENDENCE: {copula} copula"
        except Exception as e:
            logger.error(f"Error in _generate_signal: {e}")
            raise
    
    def _create_empty_result(self) -> CopulaResult:
        return CopulaResult("unknown", 0, 0, 0, 0, "Insufficient data")
