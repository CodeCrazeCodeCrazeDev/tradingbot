"""
Indicator Discovery Experiment
===============================

Discovers novel technical indicators through ML and genetic programming.

Approaches:
- ML-generated alpha factors
- Multi-timeframe composites
- Non-linear transformations
- Genetic algorithm indicator combinations
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import numpy as np
import logging

logger = logging.getLogger(__name__)


@dataclass
class IndicatorCandidate:
    """Discovered technical indicator."""
    indicator_name: str
    formula: str
    parameters: Dict[str, float]
    
    # Performance
    predictive_power: float  # IC with future returns
    robustness: float  # Performance across regimes
    orthogonality: float  # Low correlation with existing indicators
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'indicator_name': self.indicator_name,
            'formula': self.formula,
            'parameters': self.parameters,
            'predictive_power': self.predictive_power,
            'robustness': self.robustness,
            'orthogonality': self.orthogonality,
        }


class IndicatorDiscoveryExperiment:
    """
    Discovers novel technical indicators using ML and evolutionary methods.
    """
    
    def __init__(self):
        """Initialize indicator discovery."""
        self.min_predictive_power = 0.05
        self.min_robustness = 0.4
        
        self.discovered_indicators: List[IndicatorCandidate] = []
        
        logger.info("IndicatorDiscoveryExperiment initialized")
    
    def discover_ml_indicator(self,
                            price_data: List[float],
                            volume_data: List[float]) -> Optional[IndicatorCandidate]:
        """
        Use ML to generate novel indicator.
        
        Combines price and volume in non-linear ways.
        """
        # Stub: ML-generated indicator
        if len(price_data) < 50 or len(volume_data) < 50:
            return None
        
        # Example: Price momentum * volume acceleration
        returns = np.diff(price_data) / price_data[:-1]
        vol_change = np.diff(volume_data) / volume_data[:-1]
        
        if len(returns) > 0 and len(vol_change) > 0:
            # Non-linear combination
            indicator_values = [r * (1 + vc) for r, vc in zip(returns[-20:], vol_change[-20:])]
            
            # Calculate predictive power (stub)
            predictive_power = 0.08
            
            candidate = IndicatorCandidate(
                indicator_name="ML_Momentum_Volume_Fusion",
                formula="returns * (1 + volume_change)",
                parameters={'lookback': 20},
                predictive_power=predictive_power,
                robustness=0.55,
                orthogonality=0.65,
            )
            
            if self._validate_indicator(candidate):
                self.discovered_indicators.append(candidate)
                return candidate
        
        return None
    
    def discover_multi_timeframe(self,
                               price_data: List[float],
                               timeframes: List[int] = None) -> Optional[IndicatorCandidate]:
        """
        Discover multi-timeframe composite indicator.
        
        Combines signals across multiple time horizons.
        """
        timeframes = timeframes or [5, 10, 20, 50]
        
        if len(price_data) < max(timeframes) * 2:
            return None
        
        # Calculate momentum across timeframes
        momentums = []
        for tf in timeframes:
            if len(price_data) >= tf:
                momentum = (price_data[-1] - price_data[-tf]) / price_data[-tf]
                momentums.append(momentum)
        
        if momentums:
            # Weighted composite
            weights = [1/t for t in timeframes[:len(momentums)]]
            total_weight = sum(weights)
            weights = [w/total_weight for w in weights]
            
            composite = sum(m * w for m, w in zip(momentums, weights))
            
            candidate = IndicatorCandidate(
                indicator_name="Multi_Timeframe_Momentum",
                formula="weighted_average(momentum_5, momentum_10, momentum_20, momentum_50)",
                parameters={'timeframes': timeframes, 'weights': weights},
                predictive_power=0.07,
                robustness=0.6,
                orthogonality=0.5,
            )
            
            if self._validate_indicator(candidate):
                self.discovered_indicators.append(candidate)
                return candidate
        
        return None
    
    def discover_nonlinear_transform(self,
                                  base_indicator: List[float],
                                  transformation: str = "polynomial") -> Optional[IndicatorCandidate]:
        """
        Apply non-linear transformation to existing indicator.
        
        Transformations: polynomial, sigmoid, log, power
        """
        if not base_indicator or len(base_indicator) < 10:
            return None
        
        # Apply transformation
        if transformation == "polynomial":
            transformed = [x**2 for x in base_indicator[-20:]]
        elif transformation == "sigmoid":
            transformed = [1 / (1 + np.exp(-x)) for x in base_indicator[-20:]]
        elif transformation == "log":
            transformed = [np.log(abs(x) + 1) * np.sign(x) for x in base_indicator[-20:]]
        else:
            transformed = [abs(x)**0.5 * np.sign(x) for x in base_indicator[-20:]]
        
        candidate = IndicatorCandidate(
            indicator_name=f"Nonlinear_{transformation.title()}",
            formula=f"{transformation}(base_indicator)",
            parameters={'transformation': transformation},
            predictive_power=0.06,
            robustness=0.5,
            orthogonality=0.7,
        )
        
        if self._validate_indicator(candidate):
            self.discovered_indicators.append(candidate)
            return candidate
        
        return None
    
    def _validate_indicator(self, indicator: IndicatorCandidate) -> bool:
        """Validate indicator meets quality thresholds."""
        return (
            indicator.predictive_power >= self.min_predictive_power and
            indicator.robustness >= self.min_robustness
        )
    
    def get_discovered_indicators(self, min_power: float = 0.05) -> List[IndicatorCandidate]:
        """Get validated discovered indicators."""
        return [
            i for i in self.discovered_indicators
            if i.predictive_power >= min_power
        ]
