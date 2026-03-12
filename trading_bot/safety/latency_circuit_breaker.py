"""
Latency Circuit Breaker

Monitors connection latency and adjusts trading mode to prevent losses during
connectivity issues.
"""

import time
import logging
from collections import deque
from dataclasses import dataclass
from enum import Enum
from typing import Deque, Optional

logger = logging.getLogger(__name__)


class TradingMode(Enum):
    """Trading mode based on system health."""
    NORMAL = "normal"
    CONSERVATIVE = "conservative"
    PAUSED = "paused"


@dataclass
class LatencyCheck:
    """Record of a latency check."""
    timestamp: float
    latency_ms: float
    passed: bool


class LatencyCircuitBreaker:
    """
    Circuit breaker that monitors latency and adjusts trading mode.
    
    Modes:
    - NORMAL: Latency OK, trade normally
    - CONSERVATIVE: High latency detected, reduce position sizes
    - PAUSED: Critical latency, pause new entries
    """
    
    def __init__(
        self,
        latency_threshold_ms: float = 500,
        consecutive_failures: int = 3,
        check_window_size: int = 10
    ):
        """
        Initialize latency circuit breaker.
        
        Args:
            latency_threshold_ms: Latency threshold in milliseconds
            consecutive_failures: Number of consecutive failures to trigger pause
            check_window_size: Size of rolling window for latency checks
        """
        try:
            self.latency_threshold = latency_threshold_ms
            self.consecutive_failures = consecutive_failures
            self.recent_checks: Deque[LatencyCheck] = deque(maxlen=check_window_size)
            self.current_mode = TradingMode.NORMAL
        
            logger.info(f"Latency Circuit Breaker initialized:")
            logger.info(f"  Threshold: {latency_threshold_ms}ms")
            logger.info(f"  Consecutive failures to pause: {consecutive_failures}")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def check_latency(self, latency_ms: float) -> TradingMode:
        """
        Check latency and adjust trading mode.
        
        Args:
            latency_ms: Current latency in milliseconds
        
        Returns:
            Current trading mode
        """
        try:
            check = LatencyCheck(
                timestamp=time.time(),
                latency_ms=latency_ms,
                passed=latency_ms < self.latency_threshold
            )
            self.recent_checks.append(check)
        
            # Count consecutive failures
            consecutive = 0
            for check in reversed(self.recent_checks):
                if not check.passed:
                    consecutive += 1
                else:
                    break
        
            # Determine mode
            previous_mode = self.current_mode
        
            if consecutive >= self.consecutive_failures:
                self.current_mode = TradingMode.PAUSED
            elif consecutive >= 2:
                self.current_mode = TradingMode.CONSERVATIVE
            else:
                self.current_mode = TradingMode.NORMAL
        
            # Log mode changes
            if self.current_mode != previous_mode:
                logger.warning(
                    f"Trading mode changed: {previous_mode.value} → {self.current_mode.value} "
                    f"(latency: {latency_ms:.0f}ms, consecutive failures: {consecutive})"
                )
        
            # Log high latency
            if latency_ms > self.latency_threshold:
                logger.warning(
                    f"High latency detected: {latency_ms:.0f}ms "
                    f"(threshold: {self.latency_threshold:.0f}ms)"
                )
        
            return self.current_mode
        except Exception as e:
            logger.error(f"Error in check_latency: {e}")
            raise
    
    def should_allow_new_entries(self) -> bool:
        """Check if new entries are allowed."""
        return self.current_mode != TradingMode.PAUSED
    
    def get_position_size_multiplier(self) -> float:
        """
        Get position size adjustment based on mode.
        
        Returns:
            Multiplier for position size (0.0 to 1.0)
        """
        try:
            if self.current_mode == TradingMode.PAUSED:
                return 0.0
            elif self.current_mode == TradingMode.CONSERVATIVE:
                return 0.5  # Reduce size by 50%
            return 1.0
        except Exception as e:
            logger.error(f"Error in get_position_size_multiplier: {e}")
            raise
    
    def get_average_latency(self) -> Optional[float]:
        """Get average latency from recent checks."""
        try:
            if not self.recent_checks:
                return None
            return sum(c.latency_ms for c in self.recent_checks) / len(self.recent_checks)
        except Exception as e:
            logger.error(f"Error in get_average_latency: {e}")
            raise
    
    def get_status(self) -> dict:
        """Get current status."""
        try:
            avg_latency = self.get_average_latency()
            return {
                'mode': self.current_mode.value,
                'average_latency_ms': avg_latency,
                'recent_checks': len(self.recent_checks),
                'allow_new_entries': self.should_allow_new_entries(),
                'position_size_multiplier': self.get_position_size_multiplier(),
            }
        except Exception as e:
            logger.error(f"Error in get_status: {e}")
            raise
    
    def is_open(self) -> bool:
        """Check if circuit breaker is open (trading paused)."""
        return self.current_mode == TradingMode.PAUSED
    
    def is_closed(self) -> bool:
        """Check if circuit breaker is closed (trading allowed)."""
        return self.current_mode == TradingMode.NORMAL
