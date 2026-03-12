"""
Market Microstructure Decisions (Concepts 61-70)
Order flow and market structure based approaches.
"""

import math
import random
from collections import deque
from typing import Dict, List

from .core_types import (
    DecisionConcept, DecisionContext, DecisionResult,
    DecisionCategory, DecisionAction, DecisionUrgency
)


class OrderFlowImbalanceDecision(DecisionConcept):
    """Concept 61: Order Flow Imbalance - Buy/sell pressure"""
    
    def __init__(self):
        super().__init__(61, "Order Flow Imbalance", DecisionCategory.MICROSTRUCTURE)
        
    def decide(self, context: DecisionContext) -> DecisionResult:
        # Infer order flow from price/volume
        price_move = context.trend
        volume_intensity = min(context.volume / 1000000, 2.0)
        
        # Imbalance: positive = buying pressure
        imbalance = price_move * volume_intensity
        
        if imbalance > 0.3:
            action = DecisionAction.BUY
            reason = f"Strong buying pressure ({imbalance:.2f})"
        elif imbalance > 0.1:
            action = DecisionAction.WEAK_BUY
            reason = f"Moderate buying ({imbalance:.2f})"
        elif imbalance > -0.1:
            action = DecisionAction.HOLD
            reason = "Balanced order flow"
        elif imbalance > -0.3:
            action = DecisionAction.WEAK_SELL
            reason = f"Moderate selling ({imbalance:.2f})"
        else:
            action = DecisionAction.SELL
            reason = f"Strong selling pressure ({imbalance:.2f})"
        
        return self._create_result(action, abs(imbalance), DecisionUrgency.HIGH, reason,
            {'imbalance': imbalance, 'volume_intensity': volume_intensity})


class SpreadAnalysisDecision(DecisionConcept):
    """Concept 62: Spread Analysis - Trade when spreads are tight"""
    
    def __init__(self):
        super().__init__(62, "Spread Analysis", DecisionCategory.MICROSTRUCTURE)
        
    def decide(self, context: DecisionContext) -> DecisionResult:
        # Estimate spread from volatility
        estimated_spread = context.volatility * 0.001  # Proxy
        
        signal = context.trend
        
        if estimated_spread > 0.002:  # Wide spread
            action = DecisionAction.HOLD
            reason = f"Wide spread ({estimated_spread:.4f}) - wait"
            conf = 0.3
        elif estimated_spread > 0.001:  # Normal spread
            action = self._signal_to_action(signal * 0.8)
            reason = f"Normal spread ({estimated_spread:.4f})"
            conf = abs(signal) * 0.8
        else:  # Tight spread
            action = self._signal_to_action(signal * 1.1)
            reason = f"Tight spread ({estimated_spread:.4f}) - good entry"
            conf = abs(signal)
        
        return self._create_result(action, conf, DecisionUrgency.NORMAL, reason, {'spread': estimated_spread})


class VolumeProfileDecision(DecisionConcept):
    """Concept 63: Volume Profile - Trade at high volume nodes"""
    
    def __init__(self):
        super().__init__(63, "Volume Profile", DecisionCategory.MICROSTRUCTURE)
        self.volume_at_price: Dict[float, float] = {}
        
    def decide(self, context: DecisionContext) -> DecisionResult:
        # Track volume at price levels
        price_level = round(context.price, 2)
        self.volume_at_price[price_level] = self.volume_at_price.get(price_level, 0) + context.volume
        
        # Find high volume node
        if self.volume_at_price:
            hvn = max(self.volume_at_price, key=self.volume_at_price.get)
            hvn_volume = self.volume_at_price[hvn]
            current_volume = self.volume_at_price.get(price_level, 0)
            
            at_hvn = abs(context.price - hvn) / context.price < 0.01
        else:
            at_hvn = False
            hvn = context.price
        
        signal = context.trend
        
        if at_hvn:
            # At high volume node - expect support/resistance
            if signal > 0:
                action = DecisionAction.BUY
                reason = "At HVN support"
            else:
                action = DecisionAction.SELL
                reason = "At HVN resistance"
            conf = 0.7
        else:
            action = self._signal_to_action(signal)
            reason = f"Away from HVN ({hvn:.2f})"
            conf = abs(signal) * 0.8
        
        return self._create_result(action, conf, DecisionUrgency.NORMAL, reason, {'hvn': hvn, 'at_hvn': at_hvn})


class MarketDepthDecision(DecisionConcept):
    """Concept 64: Market Depth - Assess order book depth"""
    
    def __init__(self):
        super().__init__(64, "Market Depth", DecisionCategory.MICROSTRUCTURE)
        
    def decide(self, context: DecisionContext) -> DecisionResult:
        # Estimate depth from volume
        depth_score = min(context.volume / 500000, 1.0)
        
        signal = context.trend
        
        if depth_score < 0.3:  # Thin market
            signal *= 0.5
            reason = f"Thin market (depth {depth_score:.2f})"
            urgency = DecisionUrgency.LOW
        elif depth_score > 0.7:  # Deep market
            signal *= 1.1
            reason = f"Deep market (depth {depth_score:.2f})"
            urgency = DecisionUrgency.NORMAL
        else:
            reason = f"Normal depth ({depth_score:.2f})"
            urgency = DecisionUrgency.NORMAL
        
        return self._create_result(self._signal_to_action(signal), abs(signal), urgency, reason, {'depth_score': depth_score})


class PriceImpactDecision(DecisionConcept):
    """Concept 65: Price Impact - Minimize market impact"""
    
    def __init__(self):
        super().__init__(65, "Price Impact", DecisionCategory.MICROSTRUCTURE)
        
    def decide(self, context: DecisionContext) -> DecisionResult:
        # Estimate price impact
        position_size = abs(context.current_position) * context.price
        daily_volume_value = context.volume * context.price
        
        if daily_volume_value > 0:
            impact_ratio = position_size / daily_volume_value
            estimated_impact = impact_ratio * context.volatility * 0.1
        else:
            impact_ratio = 1.0
            estimated_impact = 0.01
        
        signal = context.trend
        
        if estimated_impact > 0.005:  # High impact
            action = DecisionAction.HOLD
            reason = f"High impact ({estimated_impact:.2%}) - use TWAP"
            conf = 0.4
        else:
            action = self._signal_to_action(signal)
            reason = f"Low impact ({estimated_impact:.2%})"
            conf = abs(signal)
        
        return self._create_result(action, conf, DecisionUrgency.NORMAL, reason,
            {'impact_ratio': impact_ratio, 'estimated_impact': estimated_impact})


class TickDataDecision(DecisionConcept):
    """Concept 66: Tick Data Analysis - Micro price movements"""
    
    def __init__(self):
        super().__init__(66, "Tick Data", DecisionCategory.MICROSTRUCTURE)
        self.ticks: deque = deque(maxlen=100)
        
    def decide(self, context: DecisionContext) -> DecisionResult:
        self.ticks.append(context.price)
        
        if len(self.ticks) < 10:
            return self._create_result(DecisionAction.HOLD, 0.3, DecisionUrgency.LOW, "Building tick data", {})
        
        # Tick direction analysis
        up_ticks = sum(1 for i in range(1, len(self.ticks)) if self.ticks[i] > self.ticks[i-1])
        down_ticks = sum(1 for i in range(1, len(self.ticks)) if self.ticks[i] < self.ticks[i-1])
        total = up_ticks + down_ticks
        
        if total > 0:
            tick_ratio = (up_ticks - down_ticks) / total
        else:
            tick_ratio = 0
        
        if tick_ratio > 0.3:
            action = DecisionAction.BUY
            reason = f"Bullish tick flow ({tick_ratio:.2f})"
        elif tick_ratio < -0.3:
            action = DecisionAction.SELL
            reason = f"Bearish tick flow ({tick_ratio:.2f})"
        else:
            action = DecisionAction.HOLD
            reason = f"Neutral tick flow ({tick_ratio:.2f})"
        
        return self._create_result(action, abs(tick_ratio), DecisionUrgency.HIGH, reason,
            {'tick_ratio': tick_ratio, 'up_ticks': up_ticks, 'down_ticks': down_ticks})


class InstitutionalFlowDecision(DecisionConcept):
    """Concept 67: Institutional Flow - Follow smart money"""
    
    def __init__(self):
        super().__init__(67, "Institutional Flow", DecisionCategory.MICROSTRUCTURE)
        
    def decide(self, context: DecisionContext) -> DecisionResult:
        # Detect institutional activity from volume/price patterns
        # Large volume with small price move = accumulation/distribution
        
        volume_normalized = min(context.volume / 1000000, 2.0)
        price_move = abs(context.trend)
        
        if volume_normalized > 1.0 and price_move < 0.2:
            # High volume, low price move = institutional
            institutional = True
            # Direction from subtle price move
            inst_direction = 1 if context.trend > 0 else -1
        else:
            institutional = False
            inst_direction = 0
        
        signal = context.trend
        
        if institutional:
            signal = inst_direction * 0.5  # Follow institutions
            action = self._signal_to_action(signal)
            reason = f"Institutional {'accumulation' if inst_direction > 0 else 'distribution'}"
            conf = 0.7
        else:
            action = self._signal_to_action(signal)
            reason = "No institutional signal"
            conf = abs(signal) * 0.8
        
        return self._create_result(action, conf, DecisionUrgency.NORMAL, reason,
            {'institutional': institutional, 'inst_direction': inst_direction})


class MarketMakerDecision(DecisionConcept):
    """Concept 68: Market Maker Behavior - Anticipate MM actions"""
    
    def __init__(self):
        super().__init__(68, "Market Maker", DecisionCategory.MICROSTRUCTURE)
        
    def decide(self, context: DecisionContext) -> DecisionResult:
        # MMs profit from spread and inventory management
        # They fade extremes and provide liquidity
        
        # Extreme move = MM will fade
        extreme_move = abs(context.momentum) > 0.5
        
        if extreme_move:
            # Fade with MMs
            signal = -context.momentum * 0.5
            reason = "Fading with MMs"
        else:
            # Normal - follow trend
            signal = context.trend
            reason = "Normal MM activity"
        
        return self._create_result(self._signal_to_action(signal), abs(signal), DecisionUrgency.NORMAL, reason,
            {'extreme_move': extreme_move, 'momentum': context.momentum})


class LiquidityHuntDecision(DecisionConcept):
    """Concept 69: Liquidity Hunt - Avoid stop hunts"""
    
    def __init__(self):
        super().__init__(69, "Liquidity Hunt", DecisionCategory.MICROSTRUCTURE)
        self.recent_highs: deque = deque(maxlen=20)
        self.recent_lows: deque = deque(maxlen=20)
        
    def decide(self, context: DecisionContext) -> DecisionResult:
        self.recent_highs.append(context.price * (1 + context.volatility * 0.5))
        self.recent_lows.append(context.price * (1 - context.volatility * 0.5))
        
        if len(self.recent_highs) < 5:
            return self._create_result(DecisionAction.HOLD, 0.3, DecisionUrgency.LOW, "Building levels", {})
        
        # Detect potential stop hunt
        recent_high = max(self.recent_highs)
        recent_low = min(self.recent_lows)
        
        near_high = context.price > recent_high * 0.99
        near_low = context.price < recent_low * 1.01
        
        signal = context.trend
        
        if near_high and context.momentum > 0.3:
            # Potential stop hunt above
            action = DecisionAction.WEAK_SELL
            reason = "Potential stop hunt above"
            conf = 0.6
        elif near_low and context.momentum < -0.3:
            # Potential stop hunt below
            action = DecisionAction.WEAK_BUY
            reason = "Potential stop hunt below"
            conf = 0.6
        else:
            action = self._signal_to_action(signal)
            reason = "No stop hunt detected"
            conf = abs(signal)
        
        return self._create_result(action, conf, DecisionUrgency.HIGH if (near_high or near_low) else DecisionUrgency.NORMAL,
            reason, {'near_high': near_high, 'near_low': near_low})


class ExecutionQualityDecision(DecisionConcept):
    """Concept 70: Execution Quality - Optimize entry/exit"""
    
    def __init__(self):
        super().__init__(70, "Execution Quality", DecisionCategory.MICROSTRUCTURE)
        
    def decide(self, context: DecisionContext) -> DecisionResult:
        # Score execution conditions
        spread_score = 1 - min(context.volatility * 2, 1)  # Lower vol = tighter spread
        depth_score = min(context.volume / 500000, 1)
        timing_score = 0.8 if 8 <= context.timestamp.hour <= 16 else 0.5  # Market hours
        
        execution_quality = (spread_score + depth_score + timing_score) / 3
        
        signal = context.trend
        
        if execution_quality > 0.7:
            action = self._signal_to_action(signal)
            reason = f"Good execution ({execution_quality:.2f})"
            urgency = DecisionUrgency.IMMEDIATE
        elif execution_quality > 0.4:
            action = self._signal_to_action(signal * 0.8)
            reason = f"Fair execution ({execution_quality:.2f})"
            urgency = DecisionUrgency.NORMAL
        else:
            action = DecisionAction.DEFER
            reason = f"Poor execution ({execution_quality:.2f}) - defer"
            urgency = DecisionUrgency.LOW
        
        return self._create_result(action, abs(signal) * execution_quality, urgency, reason,
            {'execution_quality': execution_quality, 'spread_score': spread_score, 'depth_score': depth_score})


MICROSTRUCTURE_CONCEPTS = [
    OrderFlowImbalanceDecision,
    SpreadAnalysisDecision,
    VolumeProfileDecision,
    MarketDepthDecision,
    PriceImpactDecision,
    TickDataDecision,
    InstitutionalFlowDecision,
    MarketMakerDecision,
    LiquidityHuntDecision,
    ExecutionQualityDecision,
]
