"""
AlphaAlgo MSOS - Time-Based Risk Management

TIME-BASED RISK MANAGEMENT:
- Signal Half-Life Engine: Measure how long signals remain predictive
- Market Time: Use trade intensity, order book churn, volatility of volatility
- Institutional Calendar: Month-end, quarter-end, option expiry, futures roll
- Temporal Diversification: Stagger entries across time

Time itself is risk. Capital deployed too long becomes fragile.

Author: AlphaAlgo MSOS
"""

import logging
import time
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from typing import Any, Deque, Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)


class TimeRiskLevel(Enum):
    """Time-based risk levels"""
    LOW = auto()
    MODERATE = auto()
    HIGH = auto()
    EXTREME = auto()


class MarketTimeState(Enum):
    """Market time states (not clock time)"""
    SLOW = auto()          # Low activity
    NORMAL = auto()        # Normal activity
    FAST = auto()          # High activity
    COMPRESSED = auto()    # Time compression (high info density)
    EXPANDED = auto()      # Time expansion (low info density)


class InstitutionalPeriod(Enum):
    """Institutional calendar periods"""
    NORMAL = auto()
    MONTH_END = auto()
    QUARTER_END = auto()
    YEAR_END = auto()
    OPTIONS_EXPIRY = auto()
    FUTURES_ROLL = auto()
    REBALANCING = auto()
    EARNINGS_SEASON = auto()


@dataclass
class SignalHalfLife:
    """Signal half-life metrics"""
    signal_id: str
    estimated_half_life: float = float('inf')  # Periods
    decay_rate: float = 0.0
    current_age: float = 0.0  # Periods since signal generated
    remaining_life: float = float('inf')
    is_expired: bool = False
    predictive_power: float = 1.0
    
    def update_age(self, periods: float = 1.0):
        """Update signal age"""
        try:
            self.current_age += periods
        
            if self.estimated_half_life > 0:
                # Exponential decay
                self.predictive_power = 0.5 ** (self.current_age / self.estimated_half_life)
                self.remaining_life = max(0, self.estimated_half_life * 2 - self.current_age)
                self.is_expired = self.predictive_power < 0.25  # 25% threshold
        except Exception as e:
            logger.error(f"Error in update_age: {e}")
            raise


@dataclass
class MarketTime:
    """Market time metrics (not clock time)"""
    trade_intensity: float = 0.0  # Trades per unit time
    order_book_churn: float = 0.0  # Order book changes per unit time
    volatility_of_volatility: float = 0.0
    information_arrival_rate: float = 0.0
    time_compression_factor: float = 1.0  # >1 = compressed, <1 = expanded
    state: MarketTimeState = MarketTimeState.NORMAL
    
    def calculate_compression(self) -> float:
        """Calculate time compression factor"""
        # Higher intensity = more compressed time
        try:
            intensity_factor = min(3.0, self.trade_intensity / 100)  # Normalize to 100 trades
            churn_factor = min(2.0, self.order_book_churn / 50)
            vov_factor = min(2.0, self.volatility_of_volatility * 10)
        
            self.time_compression_factor = (
                intensity_factor * 0.4 +
                churn_factor * 0.3 +
                vov_factor * 0.3
            )
        
            return self.time_compression_factor
        except Exception as e:
            logger.error(f"Error in calculate_compression: {e}")
            raise


@dataclass
class TemporalDiversification:
    """Temporal diversification metrics"""
    entry_timestamps: List[float] = field(default_factory=list)
    time_concentration: float = 0.0  # 0 = diversified, 1 = concentrated
    average_holding_period: float = 0.0
    max_simultaneous_entries: int = 0
    is_diversified: bool = True
    
    def calculate_concentration(self) -> float:
        """Calculate temporal concentration"""
        try:
            if len(self.entry_timestamps) < 2:
                return 0.0
        
            # Calculate time gaps between entries
            sorted_times = sorted(self.entry_timestamps)
            gaps = [sorted_times[i+1] - sorted_times[i] for i in range(len(sorted_times)-1)]
        
            if not gaps:
                return 0.0
        
            # Concentration is inverse of gap variance
            mean_gap = np.mean(gaps)
            if mean_gap > 0:
                cv = np.std(gaps) / mean_gap  # Coefficient of variation
                self.time_concentration = max(0, 1 - cv)
        
            self.is_diversified = self.time_concentration < 0.5
            return self.time_concentration
        except Exception as e:
            logger.error(f"Error in calculate_concentration: {e}")
            raise


@dataclass
class InstitutionalCalendar:
    """Institutional calendar awareness"""
    current_period: InstitutionalPeriod = InstitutionalPeriod.NORMAL
    days_to_month_end: int = 0
    days_to_quarter_end: int = 0
    days_to_options_expiry: int = 0
    days_to_futures_roll: int = 0
    is_rebalancing_window: bool = False
    institutional_flow_estimate: float = 0.0
    risk_multiplier: float = 1.0
    
    def update(self, current_date: Optional[datetime] = None):
        """Update calendar metrics"""
        try:
            if current_date is None:
                current_date = datetime.now()
        
            # Days to month end
            next_month = current_date.replace(day=28) + timedelta(days=4)
            month_end = next_month - timedelta(days=next_month.day)
            self.days_to_month_end = (month_end - current_date).days
        
            # Days to quarter end
            quarter_month = ((current_date.month - 1) // 3 + 1) * 3
            quarter_end = current_date.replace(month=quarter_month, day=28) + timedelta(days=4)
            quarter_end = quarter_end - timedelta(days=quarter_end.day)
            self.days_to_quarter_end = (quarter_end - current_date).days
        
            # Determine current period
            if self.days_to_quarter_end <= 3:
                self.current_period = InstitutionalPeriod.QUARTER_END
                self.risk_multiplier = 0.5
            elif self.days_to_month_end <= 2:
                self.current_period = InstitutionalPeriod.MONTH_END
                self.risk_multiplier = 0.7
            elif self.days_to_options_expiry <= 1:
                self.current_period = InstitutionalPeriod.OPTIONS_EXPIRY
                self.risk_multiplier = 0.6
            elif self.days_to_futures_roll <= 2:
                self.current_period = InstitutionalPeriod.FUTURES_ROLL
                self.risk_multiplier = 0.7
            else:
                self.current_period = InstitutionalPeriod.NORMAL
                self.risk_multiplier = 1.0
        except Exception as e:
            logger.error(f"Error in update: {e}")
            raise


@dataclass
class TimeRiskResult:
    """Result from time risk analysis"""
    risk_level: TimeRiskLevel
    exposure_multiplier: float
    signal_half_lives: Dict[str, SignalHalfLife]
    market_time: MarketTime
    temporal_diversification: TemporalDiversification
    institutional_calendar: InstitutionalCalendar
    warnings: List[str]
    reason: str
    timestamp: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'risk_level': self.risk_level.name,
            'exposure_multiplier': self.exposure_multiplier,
            'market_time_state': self.market_time.state.name,
            'time_compression': self.market_time.time_compression_factor,
            'temporal_concentration': self.temporal_diversification.time_concentration,
            'institutional_period': self.institutional_calendar.current_period.name,
            'warnings': self.warnings,
            'reason': self.reason,
            'timestamp': self.timestamp
        }


class SignalHalfLifeTracker:
    """Tracks signal half-lives"""
    
    def __init__(self, window_size: int = 100):
        try:
            self.window_size = window_size
            self._signals: Dict[str, SignalHalfLife] = {}
            self._signal_performance: Dict[str, Deque[Tuple[float, float]]] = {}  # (age, accuracy)
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def register_signal(self, signal_id: str, initial_half_life: float = 20.0):
        """Register a new signal"""
        try:
            self._signals[signal_id] = SignalHalfLife(
                signal_id=signal_id,
                estimated_half_life=initial_half_life
            )
            self._signal_performance[signal_id] = deque(maxlen=self.window_size)
        except Exception as e:
            logger.error(f"Error in register_signal: {e}")
            raise
    
    def update(
        self,
        signal_id: str,
        age: float,
        was_correct: bool
    ) -> SignalHalfLife:
        """Update signal with new performance data"""
        try:
            if signal_id not in self._signals:
                self.register_signal(signal_id)
        
            signal = self._signals[signal_id]
            signal.update_age(1.0)
        
            # Track performance
            accuracy = 1.0 if was_correct else 0.0
            self._signal_performance[signal_id].append((age, accuracy))
        
            # Estimate half-life from performance decay
            if len(self._signal_performance[signal_id]) >= 20:
                self._estimate_half_life(signal_id)
        
            return signal
        except Exception as e:
            logger.error(f"Error in update: {e}")
            raise
    
    def _estimate_half_life(self, signal_id: str):
        """Estimate half-life from performance data"""
        try:
            data = list(self._signal_performance[signal_id])
            ages = np.array([d[0] for d in data])
            accuracies = np.array([d[1] for d in data])
        
            if len(ages) < 20:
                return
        
            # Bin by age and calculate accuracy per bin
            bins = np.linspace(ages.min(), ages.max(), 10)
            bin_indices = np.digitize(ages, bins)
        
            bin_accuracies = []
            bin_ages = []
            for i in range(1, len(bins)):
                mask = bin_indices == i
                if np.sum(mask) > 0:
                    bin_accuracies.append(np.mean(accuracies[mask]))
                    bin_ages.append(np.mean(ages[mask]))
        
            if len(bin_accuracies) >= 3:
                # Fit exponential decay
                initial_accuracy = bin_accuracies[0]
                if initial_accuracy > 0.5:
                    # Find where accuracy drops to half
                    for i, acc in enumerate(bin_accuracies):
                        if acc < initial_accuracy * 0.5:
                            self._signals[signal_id].estimated_half_life = bin_ages[i]
                            break
        except Exception as e:
            logger.error(f"Error in _estimate_half_life: {e}")
            raise
    
    def get_signal(self, signal_id: str) -> Optional[SignalHalfLife]:
        """Get signal half-life info"""
        return self._signals.get(signal_id)
    
    def get_expired_signals(self) -> List[str]:
        """Get list of expired signals"""
        return [s.signal_id for s in self._signals.values() if s.is_expired]


class MarketTimeTracker:
    """Tracks market time (not clock time)"""
    
    def __init__(self, window_size: int = 100):
        try:
            self.window_size = window_size
            self._trade_counts: Deque[int] = deque(maxlen=window_size)
            self._order_book_changes: Deque[int] = deque(maxlen=window_size)
            self._volatilities: Deque[float] = deque(maxlen=window_size)
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def update(
        self,
        trade_count: int,
        order_book_changes: int,
        volatility: float
    ) -> MarketTime:
        """Update with new market activity data"""
        try:
            self._trade_counts.append(trade_count)
            self._order_book_changes.append(order_book_changes)
            self._volatilities.append(volatility)
        
            result = MarketTime()
        
            if len(self._trade_counts) >= 10:
                result.trade_intensity = np.mean(list(self._trade_counts)[-10:])
                result.order_book_churn = np.mean(list(self._order_book_changes)[-10:])
            
                vols = np.array(list(self._volatilities))
                result.volatility_of_volatility = np.std(vols) if len(vols) > 1 else 0.0
            
                # Calculate compression
                result.calculate_compression()
            
                # Determine state
                if result.time_compression_factor > 2.0:
                    result.state = MarketTimeState.COMPRESSED
                elif result.time_compression_factor > 1.5:
                    result.state = MarketTimeState.FAST
                elif result.time_compression_factor < 0.5:
                    result.state = MarketTimeState.EXPANDED
                elif result.time_compression_factor < 0.8:
                    result.state = MarketTimeState.SLOW
                else:
                    result.state = MarketTimeState.NORMAL
        
            return result
        except Exception as e:
            logger.error(f"Error in update: {e}")
            raise


class TemporalDiversificationTracker:
    """Tracks temporal diversification of entries"""
    
    def __init__(self, max_entries: int = 100):
        try:
            self.max_entries = max_entries
            self._entries: Deque[float] = deque(maxlen=max_entries)
            self._holding_periods: Deque[float] = deque(maxlen=max_entries)
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def record_entry(self, timestamp: Optional[float] = None):
        """Record a new entry"""
        try:
            self._entries.append(timestamp or time.time())
        except Exception as e:
            logger.error(f"Error in record_entry: {e}")
            raise
    
    def record_exit(self, entry_time: float, exit_time: Optional[float] = None):
        """Record an exit and calculate holding period"""
        try:
            exit_time = exit_time or time.time()
            holding_period = exit_time - entry_time
            self._holding_periods.append(holding_period)
        except Exception as e:
            logger.error(f"Error in record_exit: {e}")
            raise
    
    def get_diversification(self) -> TemporalDiversification:
        """Get temporal diversification metrics"""
        try:
            result = TemporalDiversification()
            result.entry_timestamps = list(self._entries)
        
            if self._holding_periods:
                result.average_holding_period = np.mean(list(self._holding_periods))
        
            # Count simultaneous entries (within 1 hour)
            if len(self._entries) >= 2:
                sorted_entries = sorted(self._entries)
                max_simultaneous = 1
                current_count = 1
            
                for i in range(1, len(sorted_entries)):
                    if sorted_entries[i] - sorted_entries[i-1] < 3600:  # 1 hour
                        current_count += 1
                        max_simultaneous = max(max_simultaneous, current_count)
                    else:
                        current_count = 1
            
                result.max_simultaneous_entries = max_simultaneous
        
            result.calculate_concentration()
            return result
        except Exception as e:
            logger.error(f"Error in get_diversification: {e}")
            raise


class TimeRiskManager:
    """
    Main Time Risk Manager
    
    RULES:
    1. Time itself is risk
    2. Signals decay - track half-lives
    3. Market time ≠ clock time
    4. Institutional calendar affects risk
    5. Temporal diversification is essential
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        try:
            self.config = config or {}
            self.logger = logging.getLogger("msos.time_risk")
        
            # Components
            self._signal_tracker = SignalHalfLifeTracker()
            self._market_time_tracker = MarketTimeTracker()
            self._diversification_tracker = TemporalDiversificationTracker()
            self._calendar = InstitutionalCalendar()
        
            self.logger.info("Time Risk Manager initialized")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def update(
        self,
        market_data: Dict[str, Any]
    ) -> TimeRiskResult:
        """
        Update time risk analysis with new data.
        """
        try:
            warnings = []
        
            # Update market time
            market_time = self._market_time_tracker.update(
                trade_count=market_data.get('trade_count', 0),
                order_book_changes=market_data.get('order_book_changes', 0),
                volatility=market_data.get('volatility', 0.02)
            )
        
            # Update calendar
            self._calendar.update()
        
            # Get diversification
            diversification = self._diversification_tracker.get_diversification()
        
            # Check for warnings
            if market_time.state == MarketTimeState.COMPRESSED:
                warnings.append("Market time compressed - high information density")
        
            if self._calendar.current_period != InstitutionalPeriod.NORMAL:
                warnings.append(f"Institutional period: {self._calendar.current_period.name}")
        
            if not diversification.is_diversified:
                warnings.append(f"Temporal concentration: {diversification.time_concentration:.2f}")
        
            # Check expired signals
            expired = self._signal_tracker.get_expired_signals()
            if expired:
                warnings.append(f"Expired signals: {expired}")
        
            # Calculate overall risk level
            risk_score = self._calculate_risk_score(
                market_time, diversification, self._calendar
            )
        
            if risk_score >= 0.8:
                risk_level = TimeRiskLevel.EXTREME
                exposure_multiplier = 0.2
            elif risk_score >= 0.6:
                risk_level = TimeRiskLevel.HIGH
                exposure_multiplier = 0.5
            elif risk_score >= 0.4:
                risk_level = TimeRiskLevel.MODERATE
                exposure_multiplier = 0.7
            else:
                risk_level = TimeRiskLevel.LOW
                exposure_multiplier = 1.0
        
            # Apply calendar multiplier
            exposure_multiplier *= self._calendar.risk_multiplier
        
            reason = self._generate_reason(risk_level, warnings)
        
            return TimeRiskResult(
                risk_level=risk_level,
                exposure_multiplier=exposure_multiplier,
                signal_half_lives={s: self._signal_tracker.get_signal(s) 
                                 for s in self._signal_tracker._signals},
                market_time=market_time,
                temporal_diversification=diversification,
                institutional_calendar=self._calendar,
                warnings=warnings,
                reason=reason
            )
        except Exception as e:
            logger.error(f"Error in update: {e}")
            raise
    
    def _calculate_risk_score(
        self,
        market_time: MarketTime,
        diversification: TemporalDiversification,
        calendar: InstitutionalCalendar
    ) -> float:
        """Calculate overall time risk score"""
        # Market time risk
        try:
            if market_time.state == MarketTimeState.COMPRESSED:
                time_risk = 0.8
            elif market_time.state == MarketTimeState.FAST:
                time_risk = 0.6
            elif market_time.state == MarketTimeState.SLOW:
                time_risk = 0.3
            else:
                time_risk = 0.4
        
            # Diversification risk
            diversification_risk = diversification.time_concentration
        
            # Calendar risk
            calendar_risk = 1 - calendar.risk_multiplier
        
            return (
                time_risk * 0.4 +
                diversification_risk * 0.3 +
                calendar_risk * 0.3
            )
        except Exception as e:
            logger.error(f"Error in _calculate_risk_score: {e}")
            raise
    
    def _generate_reason(
        self,
        risk_level: TimeRiskLevel,
        warnings: List[str]
    ) -> str:
        """Generate explanation"""
        try:
            if risk_level == TimeRiskLevel.EXTREME:
                return f"EXTREME time risk: {'; '.join(warnings)}"
            elif risk_level == TimeRiskLevel.HIGH:
                return f"High time risk: {'; '.join(warnings)}"
            elif risk_level == TimeRiskLevel.MODERATE:
                return f"Moderate time risk: {'; '.join(warnings) if warnings else 'Normal conditions'}"
            else:
                return "Low time risk"
        except Exception as e:
            logger.error(f"Error in _generate_reason: {e}")
            raise
    
    def register_signal(self, signal_id: str, half_life: float = 20.0):
        """Register a signal for half-life tracking"""
        try:
            self._signal_tracker.register_signal(signal_id, half_life)
        except Exception as e:
            logger.error(f"Error in register_signal: {e}")
            raise
    
    def update_signal(self, signal_id: str, age: float, was_correct: bool):
        """Update signal performance"""
        try:
            self._signal_tracker.update(signal_id, age, was_correct)
        except Exception as e:
            logger.error(f"Error in update_signal: {e}")
            raise
    
    def record_entry(self, timestamp: Optional[float] = None):
        """Record a trade entry"""
        try:
            self._diversification_tracker.record_entry(timestamp)
        except Exception as e:
            logger.error(f"Error in record_entry: {e}")
            raise
    
    def record_exit(self, entry_time: float, exit_time: Optional[float] = None):
        """Record a trade exit"""
        try:
            self._diversification_tracker.record_exit(entry_time, exit_time)
        except Exception as e:
            logger.error(f"Error in record_exit: {e}")
            raise
    
    def get_signal_half_life(self, signal_id: str) -> Optional[float]:
        """Get estimated half-life for a signal"""
        try:
            signal = self._signal_tracker.get_signal(signal_id)
            return signal.estimated_half_life if signal else None
        except Exception as e:
            logger.error(f"Error in get_signal_half_life: {e}")
            raise
    
    def is_signal_expired(self, signal_id: str) -> bool:
        """Check if a signal is expired"""
        try:
            signal = self._signal_tracker.get_signal(signal_id)
            return signal.is_expired if signal else True
        except Exception as e:
            logger.error(f"Error in is_signal_expired: {e}")
            raise
