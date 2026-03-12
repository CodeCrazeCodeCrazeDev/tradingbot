"""
Memory Layers Module
====================
Advanced memory systems for trading intelligence.

Memory Types:
- State Transition Memory
- Regime Shift Memory
- Seasonal Memory
- Volatility Cycle Memory
- Positioning Memory (COT, options gamma)
- Sentiment Memory

Author: AlphaAlgo Research Team
"""

import asyncio
import logging
import json
import pickle
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Tuple
from collections import deque
import threading
import sqlite3

import numpy as np
import pandas as pd

try:
    from scipy import stats
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False

logger = logging.getLogger(__name__)


class MemoryType(Enum):
    """Types of memory"""
    STATE_TRANSITION = auto()
    REGIME_SHIFT = auto()
    SEASONAL = auto()
    VOLATILITY_CYCLE = auto()
    POSITIONING = auto()
    SENTIMENT = auto()


@dataclass
class StateTransition:
    """State transition record"""
    from_state: str
    to_state: str
    timestamp: datetime
    
    # Transition metrics
    duration_in_state: float = 0.0  # seconds
    trigger: str = ""
    
    # Market context
    price_change: float = 0.0
    volume_change: float = 0.0
    volatility: float = 0.0


@dataclass
class RegimeShift:
    """Regime shift record"""
    from_regime: str
    to_regime: str
    timestamp: datetime
    
    # Shift characteristics
    shift_speed: str = "gradual"  # gradual, sudden
    confidence: float = 0.0
    
    # Indicators
    leading_indicators: List[str] = field(default_factory=list)
    price_at_shift: float = 0.0


@dataclass
class SeasonalPattern:
    """Seasonal pattern"""
    pattern_id: str
    pattern_type: str  # daily, weekly, monthly, yearly
    
    # Pattern data
    hour_of_day: Optional[int] = None
    day_of_week: Optional[int] = None
    day_of_month: Optional[int] = None
    month: Optional[int] = None
    
    # Statistics
    avg_return: float = 0.0
    win_rate: float = 0.0
    volatility: float = 0.0
    sample_count: int = 0


@dataclass
class VolatilityCycle:
    """Volatility cycle record"""
    cycle_id: str
    start_time: datetime
    
    # Cycle characteristics
    phase: str = "expansion"  # expansion, contraction
    duration_days: float = 0.0
    peak_volatility: float = 0.0
    trough_volatility: float = 0.0
    
    # Current position
    current_position: float = 0.0  # 0-1 in cycle


@dataclass
class PositioningData:
    """Positioning data (COT, gamma)"""
    timestamp: datetime
    
    # COT data
    commercial_long: float = 0.0
    commercial_short: float = 0.0
    commercial_net: float = 0.0
    
    non_commercial_long: float = 0.0
    non_commercial_short: float = 0.0
    non_commercial_net: float = 0.0
    
    # Options gamma
    total_gamma: float = 0.0
    gamma_flip_level: float = 0.0
    max_pain: float = 0.0
    
    # Derived signals
    positioning_signal: float = 0.0


@dataclass
class SentimentRecord:
    """Sentiment memory record"""
    timestamp: datetime
    
    # Sentiment scores
    news_sentiment: float = 0.0
    social_sentiment: float = 0.0
    analyst_sentiment: float = 0.0
    
    # Aggregate
    composite_sentiment: float = 0.0
    sentiment_momentum: float = 0.0
    
    # Extremes
    is_extreme: bool = False
    extreme_type: str = ""  # euphoria, panic


class StateTransitionMemory:
    """Memory for state transitions"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.transitions: deque = deque(maxlen=10000)
        self.transition_matrix: Dict[str, Dict[str, int]] = {}
        self.current_state: str = "unknown"
        self.state_entry_time: datetime = datetime.now()
        
    def record_transition(
        self,
        from_state: str,
        to_state: str,
        trigger: str = "",
        price_change: float = 0.0,
        volume_change: float = 0.0,
        volatility: float = 0.0
    ):
        """Record a state transition"""
        
        duration = (datetime.now() - self.state_entry_time).total_seconds()
        
        transition = StateTransition(
            from_state=from_state,
            to_state=to_state,
            timestamp=datetime.now(),
            duration_in_state=duration,
            trigger=trigger,
            price_change=price_change,
            volume_change=volume_change,
            volatility=volatility
        )
        
        self.transitions.append(transition)
        
        # Update transition matrix
        if from_state not in self.transition_matrix:
            self.transition_matrix[from_state] = {}
        if to_state not in self.transition_matrix[from_state]:
            self.transition_matrix[from_state][to_state] = 0
        self.transition_matrix[from_state][to_state] += 1
        
        # Update current state
        self.current_state = to_state
        self.state_entry_time = datetime.now()
    
    def get_transition_probability(self, from_state: str, to_state: str) -> float:
        """Get probability of transition"""
        
        if from_state not in self.transition_matrix:
            return 0.0
        
        total = sum(self.transition_matrix[from_state].values())
        if total == 0:
            return 0.0
        
        count = self.transition_matrix[from_state].get(to_state, 0)
        return count / total
    
    def predict_next_state(self, current_state: str) -> Tuple[str, float]:
        """Predict most likely next state"""
        
        if current_state not in self.transition_matrix:
            return "unknown", 0.0
        
        transitions = self.transition_matrix[current_state]
        if not transitions:
            return "unknown", 0.0
        
        most_likely = max(transitions.items(), key=lambda x: x[1])
        total = sum(transitions.values())
        
        return most_likely[0], most_likely[1] / total
    
    def get_avg_state_duration(self, state: str) -> float:
        """Get average duration in a state"""
        
        durations = [
            t.duration_in_state for t in self.transitions
            if t.from_state == state
        ]
        
        return np.mean(durations) if durations else 0.0


class RegimeShiftMemory:
    """Memory for regime shifts"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.shifts: deque = deque(maxlen=1000)
        self.current_regime: str = "unknown"
        self.regime_start: datetime = datetime.now()
        
    def record_shift(
        self,
        from_regime: str,
        to_regime: str,
        shift_speed: str = "gradual",
        confidence: float = 0.0,
        leading_indicators: List[str] = None,
        price: float = 0.0
    ):
        """Record a regime shift"""
        
        shift = RegimeShift(
            from_regime=from_regime,
            to_regime=to_regime,
            timestamp=datetime.now(),
            shift_speed=shift_speed,
            confidence=confidence,
            leading_indicators=leading_indicators or [],
            price_at_shift=price
        )
        
        self.shifts.append(shift)
        self.current_regime = to_regime
        self.regime_start = datetime.now()
    
    def get_regime_duration(self) -> float:
        """Get current regime duration in hours"""
        return (datetime.now() - self.regime_start).total_seconds() / 3600
    
    def get_common_leading_indicators(self, to_regime: str) -> List[Tuple[str, int]]:
        """Get common leading indicators for regime"""
        
        relevant_shifts = [s for s in self.shifts if s.to_regime == to_regime]
        
        indicator_counts = {}
        for shift in relevant_shifts:
            for indicator in shift.leading_indicators:
                indicator_counts[indicator] = indicator_counts.get(indicator, 0) + 1
        
        sorted_indicators = sorted(indicator_counts.items(), key=lambda x: x[1], reverse=True)
        return sorted_indicators[:5]
    
    def get_avg_regime_duration(self, regime: str) -> float:
        """Get average duration of a regime in hours"""
        
        durations = []
        prev_shift = None
        
        for shift in self.shifts:
            if prev_shift and prev_shift.to_regime == regime:
                duration = (shift.timestamp - prev_shift.timestamp).total_seconds() / 3600
                durations.append(duration)
            prev_shift = shift
        
        return np.mean(durations) if durations else 0.0


class SeasonalMemory:
    """Memory for seasonal patterns"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.patterns: Dict[str, SeasonalPattern] = {}
        self.return_history: deque = deque(maxlen=50000)
        
    def add_return(self, timestamp: datetime, return_: float, volatility: float = 0.0):
        """Add return observation"""
        
        self.return_history.append({
            'timestamp': timestamp,
            'return': return_,
            'volatility': volatility,
            'hour': timestamp.hour,
            'day_of_week': timestamp.weekday(),
            'day_of_month': timestamp.day,
            'month': timestamp.month
        })
    
    def calculate_patterns(self):
        """Calculate seasonal patterns"""
        
        if len(self.return_history) < 100:
            return
        
        data = list(self.return_history)
        
        # Hourly patterns
        for hour in range(24):
            hour_data = [d for d in data if d['hour'] == hour]
            if len(hour_data) >= 10:
                returns = [d['return'] for d in hour_data]
                self.patterns[f'hour_{hour}'] = SeasonalPattern(
                    pattern_id=f'hour_{hour}',
                    pattern_type='daily',
                    hour_of_day=hour,
                    avg_return=np.mean(returns),
                    win_rate=sum(1 for r in returns if r > 0) / len(returns),
                    volatility=np.std(returns),
                    sample_count=len(hour_data)
                )
        
        # Day of week patterns
        for dow in range(7):
            dow_data = [d for d in data if d['day_of_week'] == dow]
            if len(dow_data) >= 10:
                returns = [d['return'] for d in dow_data]
                self.patterns[f'dow_{dow}'] = SeasonalPattern(
                    pattern_id=f'dow_{dow}',
                    pattern_type='weekly',
                    day_of_week=dow,
                    avg_return=np.mean(returns),
                    win_rate=sum(1 for r in returns if r > 0) / len(returns),
                    volatility=np.std(returns),
                    sample_count=len(dow_data)
                )
        
        # Monthly patterns
        for month in range(1, 13):
            month_data = [d for d in data if d['month'] == month]
            if len(month_data) >= 5:
                returns = [d['return'] for d in month_data]
                self.patterns[f'month_{month}'] = SeasonalPattern(
                    pattern_id=f'month_{month}',
                    pattern_type='yearly',
                    month=month,
                    avg_return=np.mean(returns),
                    win_rate=sum(1 for r in returns if r > 0) / len(returns),
                    volatility=np.std(returns),
                    sample_count=len(month_data)
                )
    
    def get_current_seasonality(self, timestamp: datetime = None) -> Dict[str, float]:
        """Get current seasonal factors"""
        
        timestamp = timestamp or datetime.now()
        
        factors = {}
        
        hour_pattern = self.patterns.get(f'hour_{timestamp.hour}')
        if hour_pattern:
            factors['hourly_bias'] = hour_pattern.avg_return
            factors['hourly_win_rate'] = hour_pattern.win_rate
        
        dow_pattern = self.patterns.get(f'dow_{timestamp.weekday()}')
        if dow_pattern:
            factors['daily_bias'] = dow_pattern.avg_return
            factors['daily_win_rate'] = dow_pattern.win_rate
        
        month_pattern = self.patterns.get(f'month_{timestamp.month}')
        if month_pattern:
            factors['monthly_bias'] = month_pattern.avg_return
            factors['monthly_win_rate'] = month_pattern.win_rate
        
        return factors


class VolatilityCycleMemory:
    """Memory for volatility cycles"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.cycles: List[VolatilityCycle] = []
        self.volatility_history: deque = deque(maxlen=10000)
        self.current_cycle: Optional[VolatilityCycle] = None
        
    def add_volatility(self, volatility: float, timestamp: datetime = None):
        """Add volatility observation"""
        
        timestamp = timestamp or datetime.now()
        
        self.volatility_history.append({
            'timestamp': timestamp,
            'volatility': volatility
        })
        
        # Detect cycle phase
        self._update_cycle(volatility, timestamp)
    
    def _update_cycle(self, volatility: float, timestamp: datetime):
        """Update current cycle"""
        
        if len(self.volatility_history) < 50:
            return
        
        recent_vols = [v['volatility'] for v in list(self.volatility_history)[-50:]]
        
        # Detect phase
        avg_vol = np.mean(recent_vols)
        trend = np.polyfit(range(len(recent_vols)), recent_vols, 1)[0]
        
        if trend > 0:
            phase = "expansion"
        else:
            phase = "contraction"
        
        # Check for cycle change
        if self.current_cycle is None or self.current_cycle.phase != phase:
            # New cycle
            if self.current_cycle:
                self.cycles.append(self.current_cycle)
            
            self.current_cycle = VolatilityCycle(
                cycle_id=f"cycle_{len(self.cycles)}",
                start_time=timestamp,
                phase=phase,
                peak_volatility=max(recent_vols),
                trough_volatility=min(recent_vols)
            )
        else:
            # Update current cycle
            self.current_cycle.duration_days = (timestamp - self.current_cycle.start_time).days
            self.current_cycle.peak_volatility = max(self.current_cycle.peak_volatility, volatility)
            self.current_cycle.trough_volatility = min(self.current_cycle.trough_volatility, volatility)
            
            # Calculate position in cycle
            vol_range = self.current_cycle.peak_volatility - self.current_cycle.trough_volatility
            if vol_range > 0:
                self.current_cycle.current_position = (volatility - self.current_cycle.trough_volatility) / vol_range
    
    def get_cycle_position(self) -> Tuple[str, float]:
        """Get current cycle phase and position"""
        
        if self.current_cycle:
            return self.current_cycle.phase, self.current_cycle.current_position
        return "unknown", 0.5
    
    def get_avg_cycle_duration(self, phase: str) -> float:
        """Get average cycle duration for phase"""
        
        durations = [c.duration_days for c in self.cycles if c.phase == phase]
        return np.mean(durations) if durations else 0.0


class PositioningMemory:
    """Memory for positioning data (COT, gamma)"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.positioning_history: deque = deque(maxlen=1000)
        self.current_positioning: Optional[PositioningData] = None
        
    def update_cot(
        self,
        commercial_long: float,
        commercial_short: float,
        non_commercial_long: float,
        non_commercial_short: float
    ):
        """Update COT data"""
        
        if self.current_positioning is None:
            self.current_positioning = PositioningData(timestamp=datetime.now())
        
        self.current_positioning.commercial_long = commercial_long
        self.current_positioning.commercial_short = commercial_short
        self.current_positioning.commercial_net = commercial_long - commercial_short
        
        self.current_positioning.non_commercial_long = non_commercial_long
        self.current_positioning.non_commercial_short = non_commercial_short
        self.current_positioning.non_commercial_net = non_commercial_long - non_commercial_short
        
        self._calculate_signal()
        self._save_snapshot()
    
    def update_gamma(
        self,
        total_gamma: float,
        gamma_flip_level: float,
        max_pain: float
    ):
        """Update options gamma data"""
        
        if self.current_positioning is None:
            self.current_positioning = PositioningData(timestamp=datetime.now())
        
        self.current_positioning.total_gamma = total_gamma
        self.current_positioning.gamma_flip_level = gamma_flip_level
        self.current_positioning.max_pain = max_pain
        
        self._calculate_signal()
        self._save_snapshot()
    
    def _calculate_signal(self):
        """Calculate positioning signal"""
        
        if self.current_positioning is None:
            return
        
        # COT signal (commercials are usually right)
        cot_signal = 0
        if len(self.positioning_history) > 10:
            commercial_nets = [p.commercial_net for p in self.positioning_history]
            percentile = stats.percentileofscore(commercial_nets, self.current_positioning.commercial_net) / 100 if SCIPY_AVAILABLE else 0.5
            cot_signal = (percentile - 0.5) * 2  # -1 to 1
        
        # Gamma signal
        gamma_signal = np.sign(self.current_positioning.total_gamma) * 0.5
        
        # Combined
        self.current_positioning.positioning_signal = 0.6 * cot_signal + 0.4 * gamma_signal
    
    def _save_snapshot(self):
        """Save current positioning snapshot"""
        
        if self.current_positioning:
            self.positioning_history.append(PositioningData(
                timestamp=datetime.now(),
                commercial_long=self.current_positioning.commercial_long,
                commercial_short=self.current_positioning.commercial_short,
                commercial_net=self.current_positioning.commercial_net,
                non_commercial_long=self.current_positioning.non_commercial_long,
                non_commercial_short=self.current_positioning.non_commercial_short,
                non_commercial_net=self.current_positioning.non_commercial_net,
                total_gamma=self.current_positioning.total_gamma,
                gamma_flip_level=self.current_positioning.gamma_flip_level,
                max_pain=self.current_positioning.max_pain,
                positioning_signal=self.current_positioning.positioning_signal
            ))
    
    def get_positioning_signal(self) -> float:
        """Get current positioning signal"""
        
        if self.current_positioning:
            return self.current_positioning.positioning_signal
        return 0.0


class SentimentMemory:
    """Memory for sentiment data"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.sentiment_history: deque = deque(maxlen=5000)
        self.current_sentiment: Optional[SentimentRecord] = None
        
    def update_sentiment(
        self,
        news_sentiment: float = 0.0,
        social_sentiment: float = 0.0,
        analyst_sentiment: float = 0.0
    ):
        """Update sentiment data"""
        
        # Calculate composite
        composite = 0.4 * news_sentiment + 0.35 * social_sentiment + 0.25 * analyst_sentiment
        
        # Calculate momentum
        if len(self.sentiment_history) > 0:
            prev_composite = self.sentiment_history[-1].composite_sentiment
            momentum = composite - prev_composite
        else:
            momentum = 0
        
        # Detect extremes
        is_extreme = False
        extreme_type = ""
        
        if len(self.sentiment_history) > 50:
            composites = [s.composite_sentiment for s in self.sentiment_history]
            percentile = stats.percentileofscore(composites, composite) / 100 if SCIPY_AVAILABLE else 0.5
            
            if percentile > 0.95:
                is_extreme = True
                extreme_type = "euphoria"
            elif percentile < 0.05:
                is_extreme = True
                extreme_type = "panic"
        
        self.current_sentiment = SentimentRecord(
            timestamp=datetime.now(),
            news_sentiment=news_sentiment,
            social_sentiment=social_sentiment,
            analyst_sentiment=analyst_sentiment,
            composite_sentiment=composite,
            sentiment_momentum=momentum,
            is_extreme=is_extreme,
            extreme_type=extreme_type
        )
        
        self.sentiment_history.append(self.current_sentiment)
    
    def get_sentiment_signal(self) -> Tuple[float, bool, str]:
        """Get sentiment signal and extreme status"""
        
        if self.current_sentiment:
            return (
                self.current_sentiment.composite_sentiment,
                self.current_sentiment.is_extreme,
                self.current_sentiment.extreme_type
            )
        return 0.0, False, ""
    
    def get_contrarian_signal(self) -> float:
        """Get contrarian signal (fade extremes)"""
        
        if self.current_sentiment and self.current_sentiment.is_extreme:
            # Fade the extreme
            return -self.current_sentiment.composite_sentiment * 0.5
        return 0.0


class MemoryLayerSystem:
    """
    Complete Memory Layer System.
    
    Memory Types:
    - State Transition Memory
    - Regime Shift Memory
    - Seasonal Memory
    - Volatility Cycle Memory
    - Positioning Memory
    - Sentiment Memory
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Memory layers
        self.state_memory = StateTransitionMemory(config)
        self.regime_memory = RegimeShiftMemory(config)
        self.seasonal_memory = SeasonalMemory(config)
        self.volatility_memory = VolatilityCycleMemory(config)
        self.positioning_memory = PositioningMemory(config)
        self.sentiment_memory = SentimentMemory(config)
        
        logger.info("MemoryLayerSystem initialized")
    
    def get_combined_memory_signal(self) -> Dict[str, Any]:
        """Get combined signal from all memory layers"""
        
        signals = {}
        
        # State transition
        next_state, prob = self.state_memory.predict_next_state(self.state_memory.current_state)
        signals['state_prediction'] = {'next_state': next_state, 'probability': prob}
        
        # Regime
        signals['regime'] = {
            'current': self.regime_memory.current_regime,
            'duration_hours': self.regime_memory.get_regime_duration()
        }
        
        # Seasonality
        signals['seasonality'] = self.seasonal_memory.get_current_seasonality()
        
        # Volatility cycle
        phase, position = self.volatility_memory.get_cycle_position()
        signals['volatility_cycle'] = {'phase': phase, 'position': position}
        
        # Positioning
        signals['positioning'] = self.positioning_memory.get_positioning_signal()
        
        # Sentiment
        sentiment, is_extreme, extreme_type = self.sentiment_memory.get_sentiment_signal()
        signals['sentiment'] = {
            'value': sentiment,
            'is_extreme': is_extreme,
            'extreme_type': extreme_type,
            'contrarian': self.sentiment_memory.get_contrarian_signal()
        }
        
        return signals
    
    def get_memory_context(self) -> str:
        """Get human-readable memory context"""
        
        signals = self.get_combined_memory_signal()
        
        parts = []
        
        parts.append(f"State: {self.state_memory.current_state} -> {signals['state_prediction']['next_state']} ({signals['state_prediction']['probability']:.0%})")
        parts.append(f"Regime: {signals['regime']['current']} ({signals['regime']['duration_hours']:.1f}h)")
        parts.append(f"Vol Cycle: {signals['volatility_cycle']['phase']} ({signals['volatility_cycle']['position']:.0%})")
        parts.append(f"Positioning: {signals['positioning']:.2f}")
        parts.append(f"Sentiment: {signals['sentiment']['value']:.2f}" + 
                    (f" [{signals['sentiment']['extreme_type']}]" if signals['sentiment']['is_extreme'] else ""))
        
        return " | ".join(parts)


# Factory function
def create_memory_system(config: Optional[Dict] = None) -> MemoryLayerSystem:
    """Create and return a MemoryLayerSystem instance"""
    return MemoryLayerSystem(config)
