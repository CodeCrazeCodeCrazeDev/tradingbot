"""
Skill #10: Speed of Tape Analyzer
=================================

Analyzes trade velocity and acceleration to detect
institutional activity and momentum shifts.
"""

import numpy as np
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
from enum import Enum
from datetime import datetime, timedelta
from collections import deque
import logging

logger = logging.getLogger(__name__)


class TapeSpeed(Enum):
    """Speed of tape classification."""
    VERY_SLOW = "very_slow"
    SLOW = "slow"
    NORMAL = "normal"
    FAST = "fast"
    VERY_FAST = "very_fast"
    EXTREME = "extreme"


class TapeCondition(Enum):
    """Current tape condition."""
    QUIET = "quiet"
    ACTIVE = "active"
    AGGRESSIVE = "aggressive"
    CLIMACTIC = "climactic"
    EXHAUSTION = "exhaustion"


@dataclass
class TapeReading:
    """Single tape reading."""
    timestamp: datetime
    trades_per_second: float
    volume_per_second: float
    avg_trade_size: float
    price_velocity: float
    tape_speed: TapeSpeed


@dataclass
class TapeAnalysisResult:
    """Complete tape analysis result."""
    current_speed: TapeSpeed
    current_condition: TapeCondition
    trades_per_second: float
    volume_per_second: float
    avg_trade_size: float
    price_velocity: float
    price_acceleration: float
    speed_percentile: float
    is_accelerating: bool
    is_climactic: bool
    institutional_activity: float
    tape_history: List[TapeReading]
    trading_signal: str
    confidence: float


class SpeedOfTapeAnalyzer:
    """
    Advanced Speed of Tape Analysis System.
    
    Monitors trade velocity to detect institutional activity.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.history_size = self.config.get('history_size', 100)
        self.climactic_threshold = self.config.get('climactic_threshold', 3.0)
        self.tape_history: deque = deque(maxlen=self.history_size)
        self.baseline_tps: Optional[float] = None
        self.baseline_vps: Optional[float] = None
        
        logger.info("SpeedOfTapeAnalyzer initialized")
    
    def update(
        self,
        timestamp: datetime,
        price: float,
        volume: float,
        num_trades: int,
        duration_seconds: float = 1.0
    ) -> TapeAnalysisResult:
        """
        Update with new tape data.
        
        Args:
            timestamp: Current timestamp
            price: Current price
            volume: Volume in period
            num_trades: Number of trades in period
            duration_seconds: Duration of the period
            
        Returns:
            TapeAnalysisResult with analysis
        """
        # Calculate metrics
        tps = num_trades / duration_seconds if duration_seconds > 0 else 0
        vps = volume / duration_seconds if duration_seconds > 0 else 0
        avg_size = volume / num_trades if num_trades > 0 else 0
        
        # Calculate price velocity
        if self.tape_history:
            last = self.tape_history[-1]
            time_diff = (timestamp - last.timestamp).total_seconds()
            if time_diff > 0:
                # Get last price from history (stored in a custom way)
                price_velocity = 0  # Will be calculated properly
            else:
                price_velocity = 0
        else:
            price_velocity = 0
        
        # Determine tape speed
        tape_speed = self._classify_speed(tps, vps)
        
        # Create reading
        reading = TapeReading(
            timestamp=timestamp,
            trades_per_second=tps,
            volume_per_second=vps,
            avg_trade_size=avg_size,
            price_velocity=price_velocity,
            tape_speed=tape_speed
        )
        
        self.tape_history.append(reading)
        
        # Update baseline
        self._update_baseline()
        
        return self.analyze(price)
    
    def analyze(self, current_price: float = 0) -> TapeAnalysisResult:
        """Perform complete tape analysis."""
        if len(self.tape_history) < 5:
            return self._create_empty_result()
        
        current = self.tape_history[-1]
        
        # Current metrics
        current_speed = current.tape_speed
        tps = current.trades_per_second
        vps = current.volume_per_second
        avg_size = current.avg_trade_size
        
        # Calculate price velocity and acceleration
        price_velocity = self._calculate_price_velocity(current_price)
        price_acceleration = self._calculate_price_acceleration()
        
        # Determine condition
        condition = self._determine_condition(tps, vps, price_velocity)
        
        # Calculate speed percentile
        percentile = self._calculate_speed_percentile(tps)
        
        # Check for acceleration
        is_accelerating = self._is_accelerating()
        
        # Check for climactic activity
        is_climactic = self._is_climactic(tps, vps)
        
        # Estimate institutional activity
        institutional = self._estimate_institutional_activity(avg_size, vps)
        
        # Generate signal
        signal = self._generate_signal(
            condition, is_accelerating, is_climactic, institutional
        )
        
        # Calculate confidence
        confidence = self._calculate_confidence(
            condition, percentile, is_climactic
        )
        
        return TapeAnalysisResult(
            current_speed=current_speed,
            current_condition=condition,
            trades_per_second=tps,
            volume_per_second=vps,
            avg_trade_size=avg_size,
            price_velocity=price_velocity,
            price_acceleration=price_acceleration,
            speed_percentile=percentile,
            is_accelerating=is_accelerating,
            is_climactic=is_climactic,
            institutional_activity=institutional,
            tape_history=list(self.tape_history)[-20:],
            trading_signal=signal,
            confidence=confidence
        )
    
    def _classify_speed(self, tps: float, vps: float) -> TapeSpeed:
        """Classify tape speed."""
        if self.baseline_tps is None:
            return TapeSpeed.NORMAL
        
        ratio = tps / (self.baseline_tps + 1e-10)
        
        if ratio < 0.3:
            return TapeSpeed.VERY_SLOW
        elif ratio < 0.7:
            return TapeSpeed.SLOW
        elif ratio < 1.5:
            return TapeSpeed.NORMAL
        elif ratio < 2.5:
            return TapeSpeed.FAST
        elif ratio < 4.0:
            return TapeSpeed.VERY_FAST
        else:
            return TapeSpeed.EXTREME
    
    def _update_baseline(self):
        """Update baseline metrics."""
        if len(self.tape_history) < 20:
            return
        
        recent = list(self.tape_history)[-50:]
        
        # Use median for robustness
        tps_values = [r.trades_per_second for r in recent]
        vps_values = [r.volume_per_second for r in recent]
        
        self.baseline_tps = np.median(tps_values)
        self.baseline_vps = np.median(vps_values)
    
    def _calculate_price_velocity(self, current_price: float) -> float:
        """Calculate price velocity (price change per second)."""
        if len(self.tape_history) < 2 or current_price == 0:
            return 0.0
        
        # Use recent readings
        recent = list(self.tape_history)[-5:]
        
        if len(recent) < 2:
            return 0.0
        
        time_diff = (recent[-1].timestamp - recent[0].timestamp).total_seconds()
        
        if time_diff <= 0:
            return 0.0
        
        # Estimate price change from volume and trade direction
        # This is a simplified estimate
        total_volume = sum(r.volume_per_second for r in recent)
        avg_size = np.mean([r.avg_trade_size for r in recent])
        
        # Velocity proxy based on volume intensity
        velocity = total_volume / (time_diff * 1000 + 1e-10)
        
        return velocity
    
    def _calculate_price_acceleration(self) -> float:
        """Calculate price acceleration."""
        if len(self.tape_history) < 10:
            return 0.0
        
        recent = list(self.tape_history)[-10:]
        
        # Calculate velocity at two points
        mid = len(recent) // 2
        
        early_vps = np.mean([r.volume_per_second for r in recent[:mid]])
        late_vps = np.mean([r.volume_per_second for r in recent[mid:]])
        
        if early_vps == 0:
            return 0.0
        
        return (late_vps - early_vps) / early_vps
    
    def _determine_condition(
        self,
        tps: float,
        vps: float,
        price_velocity: float
    ) -> TapeCondition:
        """Determine current tape condition."""
        if self.baseline_tps is None:
            return TapeCondition.ACTIVE
        
        tps_ratio = tps / (self.baseline_tps + 1e-10)
        vps_ratio = vps / (self.baseline_vps + 1e-10)
        
        # Climactic: extreme volume and speed
        if tps_ratio > 3.0 and vps_ratio > 3.0:
            return TapeCondition.CLIMACTIC
        
        # Exhaustion: high speed but declining
        if tps_ratio > 2.0 and self._is_declining():
            return TapeCondition.EXHAUSTION
        
        # Aggressive: high speed
        if tps_ratio > 2.0:
            return TapeCondition.AGGRESSIVE
        
        # Quiet: low activity
        if tps_ratio < 0.5:
            return TapeCondition.QUIET
        
        return TapeCondition.ACTIVE
    
    def _is_declining(self) -> bool:
        """Check if tape speed is declining."""
        if len(self.tape_history) < 5:
            return False
        
        recent = list(self.tape_history)[-5:]
        tps_values = [r.trades_per_second for r in recent]
        
        # Check if declining
        return tps_values[-1] < tps_values[0] * 0.8
    
    def _calculate_speed_percentile(self, tps: float) -> float:
        """Calculate current speed as percentile of history."""
        if len(self.tape_history) < 10:
            return 50.0
        
        all_tps = [r.trades_per_second for r in self.tape_history]
        
        below = sum(1 for t in all_tps if t < tps)
        percentile = (below / len(all_tps)) * 100
        
        return percentile
    
    def _is_accelerating(self) -> bool:
        """Check if tape is accelerating."""
        if len(self.tape_history) < 5:
            return False
        
        recent = list(self.tape_history)[-5:]
        tps_values = [r.trades_per_second for r in recent]
        
        # Check for increasing trend
        increases = sum(1 for i in range(1, len(tps_values)) if tps_values[i] > tps_values[i-1])
        
        return increases >= 3
    
    def _is_climactic(self, tps: float, vps: float) -> bool:
        """Check for climactic activity."""
        if self.baseline_tps is None or self.baseline_vps is None:
            return False
        
        tps_ratio = tps / (self.baseline_tps + 1e-10)
        vps_ratio = vps / (self.baseline_vps + 1e-10)
        
        return tps_ratio > self.climactic_threshold and vps_ratio > self.climactic_threshold
    
    def _estimate_institutional_activity(
        self,
        avg_size: float,
        vps: float
    ) -> float:
        """Estimate institutional activity level (0-1)."""
        if len(self.tape_history) < 10:
            return 0.5
        
        # Get baseline average size
        all_sizes = [r.avg_trade_size for r in self.tape_history]
        baseline_size = np.median(all_sizes)
        
        if baseline_size == 0:
            return 0.5
        
        # Large trades indicate institutional activity
        size_ratio = avg_size / baseline_size
        
        # High volume also indicates institutional
        if self.baseline_vps:
            volume_ratio = vps / (self.baseline_vps + 1e-10)
        else:
            volume_ratio = 1.0
        
        # Combine factors
        institutional = min(1.0, (size_ratio * 0.6 + volume_ratio * 0.4) / 2)
        
        return institutional
    
    def _generate_signal(
        self,
        condition: TapeCondition,
        is_accelerating: bool,
        is_climactic: bool,
        institutional: float
    ) -> str:
        """Generate trading signal."""
        signals = []
        
        # Condition-based signals
        if condition == TapeCondition.CLIMACTIC:
            signals.append("CLIMACTIC: Extreme activity - potential reversal")
        elif condition == TapeCondition.EXHAUSTION:
            signals.append("EXHAUSTION: Momentum fading - prepare for reversal")
        elif condition == TapeCondition.AGGRESSIVE:
            signals.append("AGGRESSIVE: Strong momentum - follow the flow")
        elif condition == TapeCondition.QUIET:
            signals.append("QUIET: Low activity - wait for breakout")
        
        # Acceleration signal
        if is_accelerating:
            signals.append("ACCELERATING: Momentum building")
        
        # Institutional signal
        if institutional > 0.7:
            signals.append("INSTITUTIONAL: Large players active")
        elif institutional < 0.3:
            signals.append("RETAIL: Small trades dominating")
        
        return " | ".join(signals) if signals else "NORMAL: Average tape activity"
    
    def _calculate_confidence(
        self,
        condition: TapeCondition,
        percentile: float,
        is_climactic: bool
    ) -> float:
        """Calculate confidence in the analysis."""
        confidence = 0.5
        
        # Clear condition adds confidence
        if condition in [TapeCondition.CLIMACTIC, TapeCondition.EXHAUSTION]:
            confidence += 0.2
        elif condition == TapeCondition.AGGRESSIVE:
            confidence += 0.15
        
        # Extreme percentile adds confidence
        if percentile > 90 or percentile < 10:
            confidence += 0.15
        
        # Climactic adds confidence
        if is_climactic:
            confidence += 0.1
        
        # More history adds confidence
        if len(self.tape_history) >= 50:
            confidence += 0.1
        
        return min(1.0, confidence)
    
    def _create_empty_result(self) -> TapeAnalysisResult:
        """Create empty result for insufficient data."""
        return TapeAnalysisResult(
            current_speed=TapeSpeed.NORMAL,
            current_condition=TapeCondition.ACTIVE,
            trades_per_second=0,
            volume_per_second=0,
            avg_trade_size=0,
            price_velocity=0,
            price_acceleration=0,
            speed_percentile=50,
            is_accelerating=False,
            is_climactic=False,
            institutional_activity=0.5,
            tape_history=[],
            trading_signal="Insufficient data",
            confidence=0
        )
    
    def reset(self):
        """Reset the analyzer."""
        self.tape_history.clear()
        self.baseline_tps = None
        self.baseline_vps = None
