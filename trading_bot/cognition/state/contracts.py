"""Probabilistic Market State representation and contracts."""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
import time


@dataclass
class MarketState:
    """Probabilistic explicit state representation of the market."""
    timestamp: float
    instrument: str
    primary_timeframe: str

    # Probabilistic Regime Distribution (sums to 1.0)
    regime_distribution: Dict[str, float] = field(
        default_factory=lambda: {"trending": 0.33, "ranging": 0.33, "transitional": 0.34}
    )

    # Metrics and Structural Factors
    trend_direction: str = "NEUTRAL"  # BULLISH, BEARISH, NEUTRAL
    trend_strength: float = 0.0      # 0.0 to 1.0
    volatility_state: str = "NORMAL"  # LOW, NORMAL, HIGH, EXTREME
    volatility_percentile: float = 0.50
    liquidity_state: str = "NORMAL"   # ILLIQUID, NORMAL, DEEP
    liquidity_score: float = 0.50
    momentum_score: float = 0.0       # -1.0 to 1.0

    # Multi-Timeframe Structure Mapping
    timescale_structure: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    # Risk & Context
    event_risk_level: str = "LOW"     # LOW, MEDIUM, HIGH
    uncertainty: float = 0.20         # Overall epistemic uncertainty [0.0, 1.0]
    data_quality_score: float = 1.0

    metadata: Dict[str, Any] = field(default_factory=dict)

    def get_dominant_regime(self) -> str:
        """Returns the regime with highest probability."""
        if not self.regime_distribution:
            return "transitional"
        return max(self.regime_distribution, key=self.regime_distribution.get)
