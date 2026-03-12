"""
Layer 2: Adaptive Integration Core
Dynamic mode selection based on market conditions.
"""

from enum import Enum
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class IntegrationMode(Enum):
    """Integration modes for different market conditions."""
    FULL_TIER = "full_tier"
    FAST_TRACK = "fast_track"
    EMERGENCY = "emergency"
    TREND_FOCUSED = "trend_focused"
    MEAN_REVERSION = "mean_reversion"
    ADAPTIVE = "adaptive"


@dataclass
class MetaAgent:
    """Meta-agent for coordinating integration decisions."""
    name: str
    mode: IntegrationMode
    confidence: float = 0.5
    active: bool = True
    
    def evaluate(self, market_state: Dict[str, Any]) -> float:
        """Evaluate market state and return confidence score."""
        return self.confidence


class AdaptiveIntegrationCore:
    """
    Adaptive Integration Core - Layer 2 of Cognitive Architecture.
    
    Dynamically selects integration mode based on market conditions
    and coordinates between different processing tiers.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.current_mode = IntegrationMode.ADAPTIVE
        self.meta_agents: List[MetaAgent] = []
        self._initialize_agents()
        logger.info("AdaptiveIntegrationCore initialized")
    
    def _initialize_agents(self):
        """Initialize meta-agents for each mode."""
        for mode in IntegrationMode:
            self.meta_agents.append(MetaAgent(
                name=f"{mode.value}_agent",
                mode=mode,
                confidence=0.5
            ))
    
    def select_mode(self, market_state: Dict[str, Any]) -> IntegrationMode:
        """Select optimal integration mode based on market state."""
        volatility = market_state.get('volatility', 0.5)
        trend_strength = market_state.get('trend_strength', 0.5)
        urgency = market_state.get('urgency', 0.5)
        
        # Emergency mode for high urgency
        if urgency > 0.8:
            self.current_mode = IntegrationMode.EMERGENCY
        # Fast track for high volatility
        elif volatility > 0.7:
            self.current_mode = IntegrationMode.FAST_TRACK
        # Trend focused for strong trends
        elif trend_strength > 0.7:
            self.current_mode = IntegrationMode.TREND_FOCUSED
        # Mean reversion for ranging markets
        elif trend_strength < 0.3:
            self.current_mode = IntegrationMode.MEAN_REVERSION
        # Full tier for normal conditions
        else:
            self.current_mode = IntegrationMode.FULL_TIER
        
        logger.debug(f"Selected integration mode: {self.current_mode.value}")
        return self.current_mode
    
    def integrate(self, signals: List[Dict[str, Any]], market_state: Dict[str, Any]) -> Dict[str, Any]:
        """Integrate signals based on current mode."""
        mode = self.select_mode(market_state)
        
        result = {
            'mode': mode.value,
            'signals': signals,
            'integrated_signal': None,
            'confidence': 0.0
        }
        
        if not signals:
            return result
        
        # Simple weighted average integration
        total_weight = 0.0
        weighted_direction = 0.0
        
        for signal in signals:
            weight = signal.get('confidence', 0.5)
            direction = 1.0 if signal.get('direction') == 'long' else -1.0
            weighted_direction += direction * weight
            total_weight += weight
        
        if total_weight > 0:
            avg_direction = weighted_direction / total_weight
            result['integrated_signal'] = {
                'direction': 'long' if avg_direction > 0 else 'short',
                'strength': abs(avg_direction)
            }
            result['confidence'] = min(total_weight / len(signals), 1.0)
        
        return result
    
    def get_status(self) -> Dict[str, Any]:
        """Get current status of the integration core."""
        return {
            'current_mode': self.current_mode.value,
            'active_agents': len([a for a in self.meta_agents if a.active]),
            'total_agents': len(self.meta_agents)
        }
