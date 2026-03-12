"""
Temporal Decision Intelligence (Concepts 41-50)
Time-aware approaches to trading decisions.
"""

import math
import random
from datetime import datetime, timedelta
from collections import deque
from typing import Dict, List

from .core_types import (
    DecisionConcept, DecisionContext, DecisionResult,
    DecisionCategory, DecisionAction, DecisionUrgency
)


class TimeDecayDecision(DecisionConcept):
    """Concept 41: Time Decay - Signals lose value over time"""
    
    def __init__(self):
        super().__init__(41, "Time Decay", DecisionCategory.TEMPORAL)
        self.signal_age: Dict[str, datetime] = {}
        
    def decide(self, context: DecisionContext) -> DecisionResult:
        signal = context.trend * 0.5 + context.momentum * 0.5
        signal_key = f"{context.symbol}_{1 if signal > 0 else -1}"
        
        now = context.timestamp
        if signal_key in self.signal_age:
            age = (now - self.signal_age[signal_key]).total_seconds() / 3600  # Hours
            decay = math.exp(-age / 24)  # 24-hour half-life
        else:
            decay = 1.0
            self.signal_age[signal_key] = now
        
        decayed_signal = signal * decay
        
        if abs(decayed_signal) < 0.1:
            self.signal_age.pop(signal_key, None)  # Reset
        
        return self._create_result(self._signal_to_action(decayed_signal), abs(decayed_signal), DecisionUrgency.NORMAL,
            f"Decay factor: {decay:.2f}", {'original': signal, 'decayed': decayed_signal, 'decay': decay})


class MomentumPersistenceDecision(DecisionConcept):
    """Concept 42: Momentum Persistence - How long will momentum last"""
    
    def __init__(self):
        super().__init__(42, "Momentum Persistence", DecisionCategory.TEMPORAL)
        self.momentum_history: deque = deque(maxlen=20)
        
    def decide(self, context: DecisionContext) -> DecisionResult:
        self.momentum_history.append(context.momentum)
        
        if len(self.momentum_history) < 5:
            return self._create_result(DecisionAction.HOLD, 0.3, DecisionUrgency.LOW, "Building history", {})
        
        # Calculate momentum persistence
        same_sign = sum(1 for i in range(1, len(self.momentum_history)) 
                       if self.momentum_history[i] * self.momentum_history[i-1] > 0)
        persistence = same_sign / (len(self.momentum_history) - 1)
        
        if persistence > 0.7 and abs(context.momentum) > 0.2:
            action = DecisionAction.BUY if context.momentum > 0 else DecisionAction.SELL
            reason = f"High persistence ({persistence:.0%})"
            conf = persistence * abs(context.momentum)
        else:
            action = DecisionAction.HOLD
            reason = f"Low persistence ({persistence:.0%})"
            conf = 0.4
        
        return self._create_result(action, conf, DecisionUrgency.NORMAL, reason, {'persistence': persistence})


class SeasonalityDecision(DecisionConcept):
    """Concept 43: Seasonality - Time-of-day/week patterns"""
    
    def __init__(self):
        super().__init__(43, "Seasonality", DecisionCategory.TEMPORAL)
        
    def decide(self, context: DecisionContext) -> DecisionResult:
        hour = context.timestamp.hour
        weekday = context.timestamp.weekday()
        
        # Session effects
        if 8 <= hour <= 11:  # London open
            session_bias = 0.1
            session = "London open"
        elif 13 <= hour <= 16:  # US open
            session_bias = 0.05
            session = "US open"
        elif 21 <= hour or hour <= 2:  # Asian session
            session_bias = -0.05
            session = "Asian"
        else:
            session_bias = 0
            session = "Off-hours"
        
        # Day-of-week effects
        if weekday == 0:  # Monday
            day_bias = -0.05  # Monday blues
        elif weekday == 4:  # Friday
            day_bias = -0.03  # Weekend risk
        else:
            day_bias = 0.02
        
        total_bias = session_bias + day_bias
        signal = context.trend + total_bias
        
        return self._create_result(self._signal_to_action(signal), abs(signal), DecisionUrgency.NORMAL,
            f"{session}, day {weekday}", {'session_bias': session_bias, 'day_bias': day_bias})


class RegimeShiftDecision(DecisionConcept):
    """Concept 44: Regime Shift Detection - Identify market regime changes"""
    
    def __init__(self):
        super().__init__(44, "Regime Shift", DecisionCategory.TEMPORAL)
        self.regime_history: deque = deque(maxlen=30)
        
    def decide(self, context: DecisionContext) -> DecisionResult:
        current_regime = context.regime
        self.regime_history.append(current_regime)
        
        if len(self.regime_history) < 5:
            return self._create_result(DecisionAction.HOLD, 0.3, DecisionUrgency.LOW, "Building regime history", {})
        
        # Detect regime shift
        recent = list(self.regime_history)[-5:]
        regime_change = len(set(recent)) > 1
        
        if regime_change:
            # Be cautious during transitions
            action = DecisionAction.HOLD
            reason = "Regime transition detected"
            conf = 0.4
            urgency = DecisionUrgency.HIGH
        else:
            # Stable regime - trade normally
            signal = context.trend * 0.5 + context.momentum * 0.5
            action = self._signal_to_action(signal)
            reason = f"Stable regime: {current_regime}"
            conf = abs(signal)
            urgency = DecisionUrgency.NORMAL
        
        return self._create_result(action, conf, urgency, reason, {'regime': current_regime, 'shift': regime_change})


class MeanReversionTimingDecision(DecisionConcept):
    """Concept 45: Mean Reversion Timing - When to expect reversion"""
    
    def __init__(self):
        super().__init__(45, "Mean Reversion Timing", DecisionCategory.TEMPORAL)
        self.deviation_history: deque = deque(maxlen=50)
        
    def decide(self, context: DecisionContext) -> DecisionResult:
        deviation = context.trend  # Deviation from mean
        self.deviation_history.append(deviation)
        
        if len(self.deviation_history) < 10:
            return self._create_result(DecisionAction.HOLD, 0.3, DecisionUrgency.LOW, "Building history", {})
        
        # Calculate average reversion time
        sign_changes = sum(1 for i in range(1, len(self.deviation_history))
                         if self.deviation_history[i] * self.deviation_history[i-1] < 0)
        avg_duration = len(self.deviation_history) / (sign_changes + 1)
        
        # Current streak
        current_sign = 1 if deviation > 0 else -1
        streak = 0
        for d in reversed(self.deviation_history):
            if (d > 0) == (current_sign > 0):
                streak += 1
            else:
                break
        
        # If streak > avg_duration, expect reversion
        if streak > avg_duration * 1.5 and abs(deviation) > 0.2:
            action = DecisionAction.SELL if deviation > 0 else DecisionAction.BUY
            reason = f"Reversion expected (streak {streak} > avg {avg_duration:.1f})"
            conf = 0.7
        else:
            action = self._signal_to_action(deviation)
            reason = f"Trend continues (streak {streak})"
            conf = 0.5
        
        return self._create_result(action, conf, DecisionUrgency.NORMAL, reason,
            {'streak': streak, 'avg_duration': avg_duration})


class VolatilityClusteringDecision(DecisionConcept):
    """Concept 46: Volatility Clustering - Vol begets vol"""
    
    def __init__(self):
        super().__init__(46, "Volatility Clustering", DecisionCategory.TEMPORAL)
        self.vol_history: deque = deque(maxlen=20)
        
    def decide(self, context: DecisionContext) -> DecisionResult:
        self.vol_history.append(context.volatility)
        
        if len(self.vol_history) < 5:
            return self._create_result(DecisionAction.HOLD, 0.3, DecisionUrgency.LOW, "Building vol history", {})
        
        recent_vol = sum(self.vol_history) / len(self.vol_history)
        vol_trend = context.volatility - recent_vol
        
        if vol_trend > 0.1:  # Vol increasing
            # Reduce exposure
            signal = context.trend * 0.3
            reason = "Vol clustering up - reducing"
            urgency = DecisionUrgency.HIGH
        elif vol_trend < -0.1:  # Vol decreasing
            # Can increase exposure
            signal = context.trend * 1.2
            reason = "Vol clustering down - increasing"
            urgency = DecisionUrgency.NORMAL
        else:
            signal = context.trend
            reason = "Stable vol"
            urgency = DecisionUrgency.NORMAL
        
        return self._create_result(self._signal_to_action(signal), abs(signal), urgency, reason,
            {'vol_trend': vol_trend, 'recent_vol': recent_vol})


class EventWindowDecision(DecisionConcept):
    """Concept 47: Event Window - Pre/post event behavior"""
    
    def __init__(self):
        super().__init__(47, "Event Window", DecisionCategory.TEMPORAL)
        
    def decide(self, context: DecisionContext) -> DecisionResult:
        # Check for event proximity (simulated)
        hour = context.timestamp.hour
        
        # Major events typically at specific times
        pre_event = hour in [7, 8, 12, 13]  # Before London/US opens
        post_event = hour in [9, 10, 14, 15]  # After opens
        
        if pre_event:
            # Reduce exposure before events
            signal = context.trend * 0.5
            reason = "Pre-event caution"
            urgency = DecisionUrgency.HIGH
        elif post_event:
            # React to event outcome
            signal = context.momentum * 0.8 + context.trend * 0.2
            reason = "Post-event momentum"
            urgency = DecisionUrgency.IMMEDIATE
        else:
            signal = context.trend
            reason = "Normal window"
            urgency = DecisionUrgency.NORMAL
        
        return self._create_result(self._signal_to_action(signal), abs(signal), urgency, reason,
            {'pre_event': pre_event, 'post_event': post_event})


class TrendMaturityDecision(DecisionConcept):
    """Concept 48: Trend Maturity - Young vs old trends"""
    
    def __init__(self):
        super().__init__(48, "Trend Maturity", DecisionCategory.TEMPORAL)
        self.trend_start: Dict[str, datetime] = {}
        self.last_trend_sign: Dict[str, int] = {}
        
    def decide(self, context: DecisionContext) -> DecisionResult:
        trend_sign = 1 if context.trend > 0.1 else (-1 if context.trend < -0.1 else 0)
        key = context.symbol
        
        # Track trend age
        if key not in self.last_trend_sign or self.last_trend_sign[key] != trend_sign:
            self.trend_start[key] = context.timestamp
            self.last_trend_sign[key] = trend_sign
        
        if trend_sign == 0:
            return self._create_result(DecisionAction.HOLD, 0.4, DecisionUrgency.NORMAL, "No clear trend", {})
        
        age_hours = (context.timestamp - self.trend_start[key]).total_seconds() / 3600
        
        if age_hours < 2:  # Young trend
            signal = context.trend * 1.3  # Follow aggressively
            reason = f"Young trend ({age_hours:.1f}h)"
        elif age_hours < 24:  # Mature trend
            signal = context.trend  # Normal following
            reason = f"Mature trend ({age_hours:.1f}h)"
        else:  # Old trend
            signal = context.trend * 0.5  # Cautious
            reason = f"Old trend ({age_hours:.1f}h) - caution"
        
        return self._create_result(self._signal_to_action(signal), abs(signal), DecisionUrgency.NORMAL, reason,
            {'trend_age_hours': age_hours})


class CyclePhaseDecision(DecisionConcept):
    """Concept 49: Cycle Phase - Market cycle positioning"""
    
    def __init__(self):
        super().__init__(49, "Cycle Phase", DecisionCategory.TEMPORAL)
        self.price_history: deque = deque(maxlen=100)
        
    def decide(self, context: DecisionContext) -> DecisionResult:
        self.price_history.append(context.price)
        
        if len(self.price_history) < 20:
            return self._create_result(DecisionAction.HOLD, 0.3, DecisionUrgency.LOW, "Building cycle data", {})
        
        prices = list(self.price_history)
        avg = sum(prices) / len(prices)
        
        # Simple cycle detection
        above_avg = context.price > avg
        recent_above = sum(1 for p in prices[-10:] if p > avg) / 10
        
        if recent_above > 0.8:  # Late cycle bull
            phase = "late_bull"
            signal = context.trend * 0.5  # Cautious
        elif recent_above < 0.2:  # Late cycle bear
            phase = "late_bear"
            signal = context.trend * 0.5  # Cautious
        elif recent_above > 0.5 and above_avg:  # Early bull
            phase = "early_bull"
            signal = context.trend * 1.2  # Aggressive
        elif recent_above < 0.5 and not above_avg:  # Early bear
            phase = "early_bear"
            signal = context.trend * 1.2
        else:
            phase = "transition"
            signal = context.trend * 0.7
        
        return self._create_result(self._signal_to_action(signal), abs(signal), DecisionUrgency.NORMAL,
            f"Cycle phase: {phase}", {'phase': phase, 'recent_above': recent_above})


class HoldingPeriodDecision(DecisionConcept):
    """Concept 50: Optimal Holding Period - Time-based exit"""
    
    def __init__(self):
        super().__init__(50, "Holding Period", DecisionCategory.TEMPORAL)
        self.entry_times: Dict[str, datetime] = {}
        
    def decide(self, context: DecisionContext) -> DecisionResult:
        key = context.symbol
        
        # Optimal holding period based on volatility
        optimal_hours = 24 / (1 + context.volatility * 5)  # Higher vol = shorter hold
        
        if context.current_position != 0:
            if key not in self.entry_times:
                self.entry_times[key] = context.timestamp
            
            held_hours = (context.timestamp - self.entry_times[key]).total_seconds() / 3600
            
            if held_hours > optimal_hours * 1.5:
                action = DecisionAction.SELL if context.current_position > 0 else DecisionAction.BUY
                reason = f"Exceeded optimal hold ({held_hours:.1f}h > {optimal_hours:.1f}h)"
            elif held_hours > optimal_hours:
                action = DecisionAction.WEAK_SELL if context.current_position > 0 else DecisionAction.WEAK_BUY
                reason = f"Approaching hold limit"
            else:
                action = DecisionAction.HOLD
                reason = f"Within optimal hold ({held_hours:.1f}h / {optimal_hours:.1f}h)"
        else:
            self.entry_times.pop(key, None)
            signal = context.trend
            action = self._signal_to_action(signal)
            reason = f"No position, optimal hold: {optimal_hours:.1f}h"
        
        return self._create_result(action, 0.6, DecisionUrgency.NORMAL, reason,
            {'optimal_hours': optimal_hours})


TEMPORAL_CONCEPTS = [
    TimeDecayDecision,
    MomentumPersistenceDecision,
    SeasonalityDecision,
    RegimeShiftDecision,
    MeanReversionTimingDecision,
    VolatilityClusteringDecision,
    EventWindowDecision,
    TrendMaturityDecision,
    CyclePhaseDecision,
    HoldingPeriodDecision,
]
