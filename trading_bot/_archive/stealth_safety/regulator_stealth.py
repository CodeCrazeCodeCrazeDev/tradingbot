"""
Regulator & Broker Stealth System
=================================

Protects against:
1. Regulator suspicion from scaling too fast
2. Broker surveillance and account limitations
3. Pattern detection that flags algorithmic trading
4. Unusual activity that triggers reviews

PRINCIPLE: Be invisible. Trade like a sophisticated human, not a robot.
"""

import logging
import random
import threading
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta, time
from enum import Enum
from collections import deque
import hashlib

logger = logging.getLogger(__name__)


class VisibilityLevel(Enum):
    """How visible our trading is to observers"""
    INVISIBLE = "invisible"     # Looks like manual trading
    LOW = "low"                 # Minor algorithmic patterns
    MODERATE = "moderate"       # Noticeable but acceptable
    HIGH = "high"               # Clearly algorithmic
    FLAGGED = "flagged"         # Likely to trigger review


class BrokerRiskLevel(Enum):
    """Risk of broker taking action"""
    SAFE = "safe"
    CAUTION = "caution"
    WARNING = "warning"
    DANGER = "danger"
    CRITICAL = "critical"


@dataclass
class TradingPattern:
    """Record of trading patterns for analysis"""
    trades_per_hour: float
    avg_hold_time_minutes: float
    win_rate: float
    avg_trade_size: float
    time_between_trades_variance: float
    round_number_frequency: float  # How often we use round numbers
    market_order_ratio: float
    cancel_ratio: float


class RegulatorAvoidance:
    """
    Avoids triggering regulatory scrutiny.
    
    REGULATORS GET INTERESTED WHEN:
    1. Scaling too fast (sudden large volumes)
    2. Unusual patterns (perfect timing, no losses)
    3. Market manipulation signals
    4. Suspicious order flow
    5. Abnormal profitability
    
    OUR RESPONSE:
    - Gradual scaling over months
    - Introduce realistic imperfections
    - Vary timing and patterns
    - Stay below reporting thresholds
    - Maintain human-like behavior
    """
    
    # Thresholds that trigger regulatory interest
    DAILY_VOLUME_THRESHOLD = 100000      # USD - stay below
    MONTHLY_GROWTH_MAX = 0.20            # 20% max monthly growth
    WIN_RATE_CEILING = 0.70              # Don't look too good
    PERFECT_TIMING_THRESHOLD = 0.80      # Don't be too perfect
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Tracking
        self.daily_volume = 0.0
        self.monthly_volumes: deque = deque(maxlen=12)
        self.trade_history: deque = deque(maxlen=1000)
        
        # Current state
        self.visibility_level = VisibilityLevel.INVISIBLE
        self.scaling_allowed = True
        self.current_growth_rate = 0.0
        
        # Randomization seeds
        self._randomize_parameters()
        
        logger.info("RegulatorAvoidance initialized - STEALTH MODE ACTIVE")
    
    def _randomize_parameters(self):
        """Randomize parameters to avoid pattern detection"""
        self.timing_jitter = random.uniform(0.1, 0.3)
        self.size_jitter = random.uniform(0.05, 0.15)
        self.round_number_avoidance = random.uniform(0.7, 0.9)
    
    def check_trade_visibility(
        self,
        trade_size: float,
        is_market_order: bool,
        time_since_last_trade: float
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Check if a trade would increase visibility.
        
        Returns:
            Tuple of (is_safe, reason, adjustments)
        """
        adjustments = {}
        
        # Check daily volume
        if self.daily_volume + trade_size > self.DAILY_VOLUME_THRESHOLD:
            return False, "Would exceed daily volume threshold", {}
        
        # Check if trade is too fast (algorithmic signal)
        if time_since_last_trade < 5:  # Less than 5 seconds
            adjustments['delay_seconds'] = random.uniform(5, 30)
        
        # Avoid round numbers (algorithmic signal)
        if self._is_round_number(trade_size):
            adjusted_size = self._add_noise_to_size(trade_size)
            adjustments['adjusted_size'] = adjusted_size
        
        # Prefer limit orders (less algorithmic looking)
        if is_market_order and random.random() < 0.3:
            adjustments['use_limit_order'] = True
        
        return True, "Trade acceptable", adjustments
    
    def _is_round_number(self, value: float) -> bool:
        """Check if value is suspiciously round"""
        # Check for multiples of 100, 1000, etc.
        if value >= 1000 and value % 1000 == 0:
            return True
        if value >= 100 and value % 100 == 0:
            return True
        if value >= 10 and value % 10 == 0:
            return True
        return False
    
    def _add_noise_to_size(self, size: float) -> float:
        """Add noise to avoid round numbers"""
        noise = size * random.uniform(-self.size_jitter, self.size_jitter)
        return size + noise
    
    def check_scaling_speed(self, current_monthly_volume: float) -> Tuple[bool, str]:
        """
        Check if we're scaling too fast.
        
        REGULATORS NOTICE:
        - Sudden volume increases
        - Exponential growth patterns
        - Unusual consistency
        """
        if not self.monthly_volumes:
            self.monthly_volumes.append(current_monthly_volume)
            return True, "First month - baseline established"
        
        last_month = self.monthly_volumes[-1]
        if last_month > 0:
            growth_rate = (current_monthly_volume - last_month) / last_month
            self.current_growth_rate = growth_rate
            
            if growth_rate > self.MONTHLY_GROWTH_MAX:
                self.scaling_allowed = False
                return False, f"Growth rate {growth_rate*100:.1f}% exceeds {self.MONTHLY_GROWTH_MAX*100:.0f}% limit"
        
        self.monthly_volumes.append(current_monthly_volume)
        return True, "Scaling within acceptable limits"
    
    def get_recommended_daily_limit(self) -> float:
        """Get recommended daily volume limit"""
        # Start conservative, grow slowly
        base_limit = self.DAILY_VOLUME_THRESHOLD * 0.5
        
        # Adjust based on history
        if len(self.monthly_volumes) > 3:
            # Can increase slightly after establishing pattern
            base_limit *= 1.1
        
        return base_limit
    
    def introduce_imperfection(self, win_rate: float) -> Dict[str, Any]:
        """
        Introduce realistic imperfections to avoid looking too good.
        
        A 90% win rate is suspicious. 55-65% is normal.
        """
        recommendations = {}
        
        if win_rate > self.WIN_RATE_CEILING:
            recommendations['reduce_trade_frequency'] = True
            recommendations['reason'] = f"Win rate {win_rate*100:.0f}% too high - looks suspicious"
            recommendations['target_win_rate'] = 0.60
        
        return recommendations
    
    def get_visibility_status(self) -> Dict[str, Any]:
        """Get current visibility status"""
        return {
            'visibility_level': self.visibility_level.value,
            'daily_volume': self.daily_volume,
            'daily_limit': self.get_recommended_daily_limit(),
            'scaling_allowed': self.scaling_allowed,
            'current_growth_rate': self.current_growth_rate
        }


class BrokerFriendlyFlow:
    """
    Maintains broker-friendly trading patterns.
    
    BROKERS MAY LIMIT OR CLOSE YOUR ACCOUNT IF:
    1. Too many orders per second
    2. High cancel/fill ratio
    3. Unusual order patterns
    4. Suspected manipulation
    5. Excessive API usage
    
    OUR RESPONSE:
    - Rate limit ourselves below broker limits
    - Maintain healthy cancel ratio
    - Vary order types and timing
    - Stay within normal parameters
    - Be a "good" client
    """
    
    # Broker-friendly limits (conservative)
    MAX_ORDERS_PER_MINUTE = 10
    MAX_ORDERS_PER_HOUR = 100
    MAX_CANCEL_RATIO = 0.30
    MIN_HOLD_TIME_SECONDS = 60
    MAX_API_CALLS_PER_MINUTE = 30
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Tracking
        self.orders_this_minute: deque = deque(maxlen=100)
        self.orders_this_hour: deque = deque(maxlen=1000)
        self.cancels_today = 0
        self.fills_today = 0
        self.api_calls_this_minute: deque = deque(maxlen=100)
        
        # State
        self.broker_risk_level = BrokerRiskLevel.SAFE
        self.is_throttled = False
        
        logger.info("BrokerFriendlyFlow initialized")
    
    def can_place_order(self) -> Tuple[bool, str, int]:
        """
        Check if we can place an order without triggering broker limits.
        
        Returns:
            Tuple of (can_place, reason, wait_seconds)
        """
        now = datetime.now()
        
        # Clean old entries
        minute_ago = now - timedelta(minutes=1)
        hour_ago = now - timedelta(hours=1)
        
        recent_minute = [o for o in self.orders_this_minute if o > minute_ago]
        recent_hour = [o for o in self.orders_this_hour if o > hour_ago]
        
        # Check minute limit
        if len(recent_minute) >= self.MAX_ORDERS_PER_MINUTE:
            wait = 60 - (now - min(recent_minute)).seconds
            return False, "Minute order limit reached", max(1, wait)
        
        # Check hour limit
        if len(recent_hour) >= self.MAX_ORDERS_PER_HOUR:
            wait = 3600 - (now - min(recent_hour)).seconds
            return False, "Hour order limit reached", max(1, wait)
        
        return True, "Order allowed", 0
    
    def record_order(self, was_cancelled: bool = False, was_filled: bool = False):
        """Record an order for tracking"""
        now = datetime.now()
        self.orders_this_minute.append(now)
        self.orders_this_hour.append(now)
        
        if was_cancelled:
            self.cancels_today += 1
        if was_filled:
            self.fills_today += 1
        
        self._update_risk_level()
    
    def record_api_call(self):
        """Record an API call"""
        self.api_calls_this_minute.append(datetime.now())
    
    def can_make_api_call(self) -> Tuple[bool, int]:
        """Check if we can make an API call"""
        now = datetime.now()
        minute_ago = now - timedelta(minutes=1)
        
        recent = [c for c in self.api_calls_this_minute if c > minute_ago]
        
        if len(recent) >= self.MAX_API_CALLS_PER_MINUTE:
            wait = 60 - (now - min(recent)).seconds
            return False, max(1, wait)
        
        return True, 0
    
    def _update_risk_level(self):
        """Update broker risk level"""
        # Calculate cancel ratio
        total_orders = self.cancels_today + self.fills_today
        if total_orders > 0:
            cancel_ratio = self.cancels_today / total_orders
            
            if cancel_ratio > 0.5:
                self.broker_risk_level = BrokerRiskLevel.CRITICAL
            elif cancel_ratio > 0.4:
                self.broker_risk_level = BrokerRiskLevel.DANGER
            elif cancel_ratio > self.MAX_CANCEL_RATIO:
                self.broker_risk_level = BrokerRiskLevel.WARNING
            elif cancel_ratio > 0.2:
                self.broker_risk_level = BrokerRiskLevel.CAUTION
            else:
                self.broker_risk_level = BrokerRiskLevel.SAFE
    
    def get_cancel_ratio(self) -> float:
        """Get current cancel ratio"""
        total = self.cancels_today + self.fills_today
        if total == 0:
            return 0.0
        return self.cancels_today / total
    
    def should_reduce_activity(self) -> Tuple[bool, str]:
        """Check if we should reduce trading activity"""
        if self.broker_risk_level in [BrokerRiskLevel.DANGER, BrokerRiskLevel.CRITICAL]:
            return True, f"Broker risk level: {self.broker_risk_level.value}"
        
        if self.get_cancel_ratio() > self.MAX_CANCEL_RATIO:
            return True, f"Cancel ratio {self.get_cancel_ratio()*100:.0f}% too high"
        
        return False, "Activity levels acceptable"
    
    def reset_daily_counters(self):
        """Reset daily counters"""
        self.cancels_today = 0
        self.fills_today = 0
    
    def get_status(self) -> Dict[str, Any]:
        """Get broker-friendly status"""
        return {
            'risk_level': self.broker_risk_level.value,
            'cancel_ratio': self.get_cancel_ratio(),
            'orders_this_hour': len(self.orders_this_hour),
            'is_throttled': self.is_throttled
        }


class ScalingSpeedLimiter:
    """
    Limits how fast the system can scale.
    
    FAST SCALING TRIGGERS:
    1. Regulatory review
    2. Broker scrutiny
    3. Market impact
    4. Operational risk
    
    OUR APPROACH:
    - Maximum 20% monthly growth
    - Minimum 3 months before doubling
    - Gradual position size increases
    - Volume smoothing
    """
    
    # Scaling limits
    MAX_MONTHLY_GROWTH = 0.20           # 20%
    MAX_WEEKLY_GROWTH = 0.05            # 5%
    MIN_MONTHS_TO_DOUBLE = 3
    POSITION_SIZE_INCREMENT = 0.10      # 10% max increase per week
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Tracking
        self.weekly_volumes: deque = deque(maxlen=52)
        self.monthly_volumes: deque = deque(maxlen=12)
        self.position_size_history: deque = deque(maxlen=100)
        
        # Current limits
        self.current_max_position = config.get('initial_max_position', 1000)
        self.current_max_daily_volume = config.get('initial_daily_volume', 10000)
        
        # State
        self.scaling_paused = False
        self.pause_reason = None
        
        logger.info("ScalingSpeedLimiter initialized")
    
    def can_increase_position_size(self, proposed_increase: float) -> Tuple[bool, float]:
        """
        Check if position size can be increased.
        
        Returns:
            Tuple of (can_increase, max_allowed_increase)
        """
        max_increase = self.current_max_position * self.POSITION_SIZE_INCREMENT
        
        if proposed_increase > max_increase:
            return False, max_increase
        
        return True, proposed_increase
    
    def can_increase_volume(self, proposed_volume: float) -> Tuple[bool, float]:
        """
        Check if daily volume can be increased.
        
        Returns:
            Tuple of (can_increase, max_allowed_volume)
        """
        if not self.weekly_volumes:
            return True, proposed_volume
        
        last_week_avg = sum(self.weekly_volumes) / len(self.weekly_volumes)
        max_volume = last_week_avg * (1 + self.MAX_WEEKLY_GROWTH)
        
        if proposed_volume > max_volume:
            return False, max_volume
        
        return True, proposed_volume
    
    def record_volume(self, daily_volume: float):
        """Record daily volume"""
        # Add to weekly (simplified - just track daily)
        self.weekly_volumes.append(daily_volume)
    
    def get_scaling_schedule(self, target_volume: float) -> List[Dict]:
        """
        Get a safe scaling schedule to reach target volume.
        
        Returns list of weekly volume targets.
        """
        if not self.weekly_volumes:
            current = self.current_max_daily_volume
        else:
            current = sum(self.weekly_volumes) / len(self.weekly_volumes)
        
        schedule = []
        week = 0
        
        while current < target_volume:
            week += 1
            current = min(current * (1 + self.MAX_WEEKLY_GROWTH), target_volume)
            schedule.append({
                'week': week,
                'target_volume': current,
                'growth_rate': self.MAX_WEEKLY_GROWTH
            })
            
            if week > 52:  # Max 1 year schedule
                break
        
        return schedule
    
    def pause_scaling(self, reason: str):
        """Pause all scaling"""
        self.scaling_paused = True
        self.pause_reason = reason
        logger.warning(f"Scaling PAUSED: {reason}")
    
    def resume_scaling(self):
        """Resume scaling"""
        self.scaling_paused = False
        self.pause_reason = None
        logger.info("Scaling resumed")
    
    def get_status(self) -> Dict[str, Any]:
        """Get scaling status"""
        return {
            'scaling_paused': self.scaling_paused,
            'pause_reason': self.pause_reason,
            'current_max_position': self.current_max_position,
            'current_max_daily_volume': self.current_max_daily_volume,
            'weeks_of_data': len(self.weekly_volumes)
        }


class LowVisibilityMode:
    """
    Adaptive low-visibility trading mode.
    
    MAKES TRADING LOOK HUMAN:
    1. Variable timing (not precise intervals)
    2. Imperfect execution (occasional slippage)
    3. Mixed order types
    4. Natural patterns
    5. Session-aware activity
    
    AVOIDS:
    1. Millisecond precision
    2. Perfect fills
    3. Mechanical patterns
    4. 24/7 activity
    5. Inhuman consistency
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Humanization parameters
        self.min_delay_seconds = 3
        self.max_delay_seconds = 30
        self.activity_variance = 0.3
        
        # Session awareness
        self.active_sessions = config.get('active_sessions', [
            {'start': time(8, 0), 'end': time(17, 0), 'timezone': 'US/Eastern'},
            {'start': time(3, 0), 'end': time(12, 0), 'timezone': 'Europe/London'},
        ])
        
        # State
        self.is_low_visibility = True
        self.current_activity_level = 0.5
        
        logger.info("LowVisibilityMode initialized - STEALTH ACTIVE")
    
    def get_humanized_delay(self) -> float:
        """Get a human-like delay between actions"""
        # Base delay with variance
        base = random.uniform(self.min_delay_seconds, self.max_delay_seconds)
        
        # Add occasional longer pauses (like a human thinking)
        if random.random() < 0.1:
            base += random.uniform(30, 120)
        
        # Add micro-variance
        base += random.gauss(0, 1)
        
        return max(1, base)
    
    def get_humanized_size(self, intended_size: float) -> float:
        """Get a human-like order size (not perfectly round)"""
        # Add noise
        noise = intended_size * random.uniform(-0.05, 0.05)
        size = intended_size + noise
        
        # Avoid round numbers
        if size % 100 < 10:
            size += random.uniform(10, 50)
        
        return round(size, 2)
    
    def should_use_limit_order(self) -> bool:
        """Decide if we should use limit order (more human-like)"""
        # Humans use more limit orders
        return random.random() < 0.7
    
    def get_order_type_mix(self) -> Dict[str, float]:
        """Get recommended order type mix"""
        return {
            'limit': 0.60,
            'market': 0.25,
            'stop_limit': 0.10,
            'trailing_stop': 0.05
        }
    
    def is_good_time_to_trade(self) -> Tuple[bool, str]:
        """Check if current time looks natural for trading"""
        now = datetime.now()
        hour = now.hour
        
        # Avoid suspicious hours
        if hour < 6 or hour > 22:
            return False, "Outside normal trading hours"
        
        # Reduce activity during lunch
        if 12 <= hour <= 13:
            if random.random() < 0.5:
                return False, "Lunch hour - reduced activity"
        
        return True, "Good time to trade"
    
    def add_execution_imperfection(self) -> Dict[str, Any]:
        """Add realistic execution imperfections"""
        imperfections = {}
        
        # Occasional slight delay
        if random.random() < 0.2:
            imperfections['delay_ms'] = random.randint(100, 500)
        
        # Occasional partial fill
        if random.random() < 0.1:
            imperfections['partial_fill_pct'] = random.uniform(0.7, 0.95)
        
        # Occasional price improvement (or slippage)
        if random.random() < 0.3:
            imperfections['price_adjustment_bps'] = random.gauss(0, 2)
        
        return imperfections
    
    def get_activity_pattern(self) -> Dict[str, float]:
        """Get human-like activity pattern by hour"""
        # Typical human trading pattern
        return {
            '06': 0.2, '07': 0.4, '08': 0.7, '09': 0.9,
            '10': 1.0, '11': 0.9, '12': 0.5, '13': 0.6,
            '14': 0.8, '15': 0.9, '16': 0.7, '17': 0.4,
            '18': 0.2, '19': 0.1, '20': 0.1, '21': 0.05
        }
    
    def get_status(self) -> Dict[str, Any]:
        """Get low visibility status"""
        return {
            'is_low_visibility': self.is_low_visibility,
            'current_activity_level': self.current_activity_level,
            'recommended_delay': self.get_humanized_delay()
        }
