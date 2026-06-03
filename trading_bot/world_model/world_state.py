"""
Institutional-Grade Market World State Governance Structure
==========================================================

Defines the standardized WorldState structure required for hierarchical
governance and intelligence-core compliance.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any
from datetime import datetime


class VolatilityRegime(Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    EXTREME = "extreme"


class LiquidityCondition(Enum):
    DEEP = "deep"
    NORMAL = "normal"
    THIN = "thin"
    ILLIQUID = "illiquid"


class SystemMode(Enum):
    EXPLORE = "explore"
    EXPLOIT = "exploit"
    NORMAL = "normal"
    REDUCED_RISK = "reduced_risk"
    DEFENSIVE = "defensive"
    OBSERVE_ONLY = "observe_only"
    HALT = "halt"


@dataclass(frozen=True)
class MarketWorldState:
    """
    Standardized WorldState structure for governance.
    This object is the mandatory output of the World Model before any prediction.
    """
    timestamp: float = field(default_factory=lambda: datetime.utcnow().timestamp())
    symbol: str = "EURUSD"

    # Core Regime Classification
    volatility_regime: VolatilityRegime = VolatilityRegime.NORMAL
    liquidity_condition: LiquidityCondition = LiquidityCondition.NORMAL

    # Stability and Pressure Metrics
    trend_stability: float = 0.5  # 0.0 (chaotic) to 1.0 (stable)
    participation_pressure: float = 0.0  # -1.0 (sell) to 1.0 (buy)
    systemic_risk_level: float = 0.1  # 0.0 (safe) to 1.0 (crisis)

    # Uncertainty and Entropy
    regime_entropy: float = 0.0  # Uncertainty in regime classification
    state_confidence: float = 1.0  # 0.0 to 1.0, overall confidence in this state

    # Uncertainty Decomposition
    epistemic_uncertainty: float = 0.0  # Model ignorance (knowledge gap)
    aleatoric_uncertainty: float = 0.0  # Market randomness (noise)

    # Institutional-Grade Metrics
    tail_risk_probability: float = 0.01  # Estimated prob of >3-sigma move
    correlation_regime: float = 0.0  # Average cross-asset correlation (0 to 1)
    sentiment_drift: float = 0.0  # Rate of change in market sentiment
    causal_attribution: Dict[str, float] = field(default_factory=dict)  # Key drivers

    # Governance Integration
    ignorance_score: float = 0.0  # Unified 0.0 to 1.0 ignorance score
    recommended_mode: SystemMode = SystemMode.NORMAL

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "symbol": self.symbol,
            "volatility_regime": self.volatility_regime.value,
            "liquidity_condition": self.liquidity_condition.value,
            "trend_stability": self.trend_stability,
            "participation_pressure": self.participation_pressure,
            "systemic_risk_level": self.systemic_risk_level,
            "regime_entropy": self.regime_entropy,
            "state_confidence": self.state_confidence,
            "epistemic_uncertainty": self.epistemic_uncertainty,
            "aleatoric_uncertainty": self.aleatoric_uncertainty,
            "ignorance_score": self.ignorance_score,
            "recommended_mode": self.recommended_mode.value
        }
