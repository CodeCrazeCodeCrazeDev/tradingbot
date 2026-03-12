"""
Skill #49: Greeks Calculator
============================

Calculates option Greeks (Delta, Gamma, Theta, Vega, Rho) for risk management.
"""

import numpy as np
from dataclasses import dataclass
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


@dataclass
class GreeksResult:
    """Option Greeks result."""
    delta: float
    gamma: float
    theta: float
    vega: float
    rho: float
    trading_signal: str


class GreeksCalculator:
    """Calculates option Greeks using Black-Scholes."""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        logger.info("GreeksCalculator initialized")
    
    def calculate(
        self,
        spot: float,
        strike: float,
        time_to_expiry: float,
        volatility: float,
        risk_free_rate: float = 0.05,
        is_call: bool = True
    ) -> GreeksResult:
        """Calculate option Greeks."""
        if time_to_expiry <= 0 or volatility <= 0:
            return self._create_empty_result()
        
        d1 = (np.log(spot / strike) + (risk_free_rate + 0.5 * volatility**2) * time_to_expiry) / (volatility * np.sqrt(time_to_expiry))
        d2 = d1 - volatility * np.sqrt(time_to_expiry)
        
        # Delta
        if is_call:
            delta = self._norm_cdf(d1)
        else:
            delta = self._norm_cdf(d1) - 1
        
        # Gamma
        gamma = self._norm_pdf(d1) / (spot * volatility * np.sqrt(time_to_expiry))
        
        # Theta
        theta_term1 = -spot * self._norm_pdf(d1) * volatility / (2 * np.sqrt(time_to_expiry))
        if is_call:
            theta = theta_term1 - risk_free_rate * strike * np.exp(-risk_free_rate * time_to_expiry) * self._norm_cdf(d2)
        else:
            theta = theta_term1 + risk_free_rate * strike * np.exp(-risk_free_rate * time_to_expiry) * self._norm_cdf(-d2)
        theta = theta / 365  # Daily theta
        
        # Vega
        vega = spot * self._norm_pdf(d1) * np.sqrt(time_to_expiry) / 100
        
        # Rho
        if is_call:
            rho = strike * time_to_expiry * np.exp(-risk_free_rate * time_to_expiry) * self._norm_cdf(d2) / 100
        else:
            rho = -strike * time_to_expiry * np.exp(-risk_free_rate * time_to_expiry) * self._norm_cdf(-d2) / 100
        
        signal = self._generate_signal(delta, gamma, theta, vega)
        
        return GreeksResult(delta=delta, gamma=gamma, theta=theta, vega=vega, rho=rho, trading_signal=signal)
    
    def _norm_cdf(self, x: float) -> float:
        """Standard normal CDF."""
        return 0.5 * (1 + np.erf(x / np.sqrt(2)))
    
    def _norm_pdf(self, x: float) -> float:
        """Standard normal PDF."""
        return np.exp(-0.5 * x**2) / np.sqrt(2 * np.pi)
    
    def _generate_signal(self, delta: float, gamma: float, theta: float, vega: float) -> str:
        """Generate signal."""
        return f"GREEKS: Δ={delta:.3f}, Γ={gamma:.4f}, Θ={theta:.4f}, V={vega:.4f}"
    
    def _create_empty_result(self) -> GreeksResult:
        return GreeksResult(0, 0, 0, 0, 0, "Invalid parameters")
