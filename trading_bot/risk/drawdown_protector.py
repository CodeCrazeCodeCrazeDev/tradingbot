"""
DRAWDOWN PROTECTION MODULE - P0 CRITICAL FIX
============================================================

Implements maximum drawdown protection to prevent catastrophic losses.

Features:
- Real-time drawdown calculation
- Automatic trading halt when limit exceeded
- Daily loss limit enforcement
- Position size reduction on drawdown
- Emergency shutdown capability

Author: AI Assistant
Date: October 23, 2025
Version: 1.0.0
"""


from __future__ import annotations
import logging
logger = logging.getLogger(__name__)
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from typing import Any, Dict, List, Optional

import numpy as np
from loguru import logger
import numpy


class DrawdownStatus(Enum):
    """Drawdown status."""
    GREEN = auto()      # Safe (< 50% of limit)
    YELLOW = auto()     # Caution (50-80% of limit)
    RED = auto()        # Alert (80-100% of limit)
    CRITICAL = auto()   # Halt trading (>= 100% of limit)


@dataclass
class DrawdownMetrics:
    """Drawdown metrics."""
    current_balance: float
    peak_balance: float
    drawdown_amount: float
    drawdown_percent: float
    daily_loss: float
    daily_loss_percent: float
    status: DrawdownStatus
    timestamp: datetime = field(default_factory=datetime.now)


class DrawdownProtector:
    """Protects account from catastrophic drawdown."""
    
    def __init__(self, max_drawdown_percent: float = 20.0,
                 max_daily_loss_percent: float = 2.0,
                 max_total_positions: int = 5):
        """
        Initialize drawdown protector.
        
        Args:
            max_drawdown_percent: Maximum allowed drawdown (default 20%)
            max_daily_loss_percent: Maximum daily loss (default 2%)
            max_total_positions: Maximum open positions (default 5)
        """
        try:
            self.max_drawdown_percent = max_drawdown_percent
            self.max_daily_loss_percent = max_daily_loss_percent
            self.max_total_positions = max_total_positions
        
            self.initial_balance = None
            self.peak_balance = None
            self.current_balance = None
            self.daily_start_balance = None
            self.daily_start_time = None
        
            self.drawdown_history: List[DrawdownMetrics] = []
            self.trading_halted = False
            self.halt_reason = None
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def initialize(self, initial_balance: float):
        """Initialize with account balance."""
        try:
            self.initial_balance = initial_balance
            self.peak_balance = initial_balance
            self.current_balance = initial_balance
            self.daily_start_balance = initial_balance
            self.daily_start_time = datetime.now()
        
            logger.info(f"Drawdown protector initialized with balance: ${initial_balance:,.2f}")
        except Exception as e:
            logger.error(f"Error in initialize: {e}")
            raise
    
    def update_balance(self, current_balance: float):
        """Update current balance and check limits."""
        try:
            self.current_balance = current_balance
        
            # Update peak if new high
            if current_balance > self.peak_balance:
                self.peak_balance = current_balance
                logger.info(f"New peak balance: ${self.peak_balance:,.2f}")
        
            # Check if new day
            if self._is_new_day():
                self._reset_daily_limits()
        
            # Calculate metrics
            metrics = self._calculate_metrics()
            self.drawdown_history.append(metrics)
        
            # Keep only last 1000 records
            if len(self.drawdown_history) > 1000:
                self.drawdown_history.pop(0)
        
            # Check limits
            self._check_limits(metrics)
        except Exception as e:
            logger.error(f"Error in update_balance: {e}")
            raise
    
    def _calculate_metrics(self) -> DrawdownMetrics:
        """Calculate current drawdown metrics."""
        # Overall drawdown
        try:
            drawdown_amount = self.peak_balance - self.current_balance
            drawdown_percent = (drawdown_amount / self.peak_balance * 100) if self.peak_balance > 0 else 0
        
            # Daily loss
            daily_loss = self.daily_start_balance - self.current_balance
            daily_loss_percent = (daily_loss / self.daily_start_balance * 100) if self.daily_start_balance > 0 else 0
        
            # Determine status
            status = self._get_status(drawdown_percent)
        
            return DrawdownMetrics(
                current_balance=self.current_balance,
                peak_balance=self.peak_balance,
                drawdown_amount=drawdown_amount,
                drawdown_percent=drawdown_percent,
                daily_loss=daily_loss,
                daily_loss_percent=daily_loss_percent,
                status=status
            )
        except Exception as e:
            logger.error(f"Error in _calculate_metrics: {e}")
            raise
    
    def _get_status(self, drawdown_percent: float) -> DrawdownStatus:
        """Determine drawdown status."""
        try:
            if drawdown_percent >= 100:
                return DrawdownStatus.CRITICAL
            elif drawdown_percent >= 80:
                return DrawdownStatus.RED
            elif drawdown_percent >= 50:
                return DrawdownStatus.YELLOW
            else:
                return DrawdownStatus.GREEN
        except Exception as e:
            logger.error(f"Error in _get_status: {e}")
            raise
    
    def _check_limits(self, metrics: DrawdownMetrics):
        """Check if limits exceeded."""
        # Check overall drawdown
        try:
            if metrics.drawdown_percent >= self.max_drawdown_percent:
                self.trading_halted = True
                self.halt_reason = f"Drawdown limit exceeded: {metrics.drawdown_percent:.2f}%"
                logger.critical(self.halt_reason)
        
            # Check daily loss
            if metrics.daily_loss_percent >= self.max_daily_loss_percent:
                self.trading_halted = True
                self.halt_reason = f"Daily loss limit exceeded: {metrics.daily_loss_percent:.2f}%"
                logger.critical(self.halt_reason)
        except Exception as e:
            logger.error(f"Error in _check_limits: {e}")
            raise
    
    def _is_new_day(self) -> bool:
        """Check if new trading day."""
        try:
            if self.daily_start_time is None:
                return False
        
            now = datetime.now()
            # Reset at 00:00 UTC
            if now.date() > self.daily_start_time.date():
                return True
        
            return False
        except Exception as e:
            logger.error(f"Error in _is_new_day: {e}")
            raise
    
    def _reset_daily_limits(self):
        """Reset daily loss limits."""
        try:
            self.daily_start_balance = self.current_balance
            self.daily_start_time = datetime.now()
            logger.info(f"Daily limits reset. Starting balance: ${self.daily_start_balance:,.2f}")
        except Exception as e:
            logger.error(f"Error in _reset_daily_limits: {e}")
            raise
    
    def should_stop_trading(self) -> bool:
        """Check if trading should be halted."""
        return self.trading_halted
    
    def get_drawdown_percent(self) -> float:
        """Get current drawdown percentage."""
        try:
            if self.peak_balance == 0:
                return 0
        
            drawdown = (self.peak_balance - self.current_balance) / self.peak_balance * 100
            return max(0, drawdown)
        except Exception as e:
            logger.error(f"Error in get_drawdown_percent: {e}")
            raise
    
    def get_daily_loss_percent(self) -> float:
        """Get current daily loss percentage."""
        try:
            if self.daily_start_balance == 0:
                return 0
        
            loss = (self.daily_start_balance - self.current_balance) / self.daily_start_balance * 100
            return max(0, loss)
        except Exception as e:
            logger.error(f"Error in get_daily_loss_percent: {e}")
            raise
    
    def get_status(self) -> DrawdownStatus:
        """Get current drawdown status."""
        try:
            drawdown_percent = self.get_drawdown_percent()
            return self._get_status(drawdown_percent)
        except Exception as e:
            logger.error(f"Error in get_status: {e}")
            raise
    
    def get_metrics(self) -> DrawdownMetrics:
        """Get current metrics."""
        return self._calculate_metrics()
    
    def get_status_string(self) -> str:
        """Get human-readable status string."""
        try:
            metrics = self.get_metrics()
        
            status_map = {
                DrawdownStatus.GREEN: "🟢 GREEN",
                DrawdownStatus.YELLOW: "🟡 YELLOW",
                DrawdownStatus.RED: "🔴 RED",
                DrawdownStatus.CRITICAL: "⛔ CRITICAL"
            }
        
            return f"""
    DRAWDOWN PROTECTION STATUS
    {'=' * 50}
    Status: {status_map[metrics.status]}
    Current Balance: ${metrics.current_balance:,.2f}
    Peak Balance: ${metrics.peak_balance:,.2f}
    Drawdown: {metrics.drawdown_percent:.2f}% (Max: {self.max_drawdown_percent}%)
    Daily Loss: {metrics.daily_loss_percent:.2f}% (Max: {self.max_daily_loss_percent}%)
    Trading Halted: {self.trading_halted}
    {f'Halt Reason: {self.halt_reason}' if self.halt_reason else ''}
    {'=' * 50}
    """
        except Exception as e:
            logger.error(f"Error in get_status_string: {e}")
            raise
    
    def get_position_size_multiplier(self) -> float:
        """
        Get position size multiplier based on drawdown.
        
        Returns:
            1.0 for GREEN
            0.75 for YELLOW
            0.5 for RED
            0.0 for CRITICAL
        """
        try:
            status = self.get_status()
        
            multipliers = {
                DrawdownStatus.GREEN: 1.0,
                DrawdownStatus.YELLOW: 0.75,
                DrawdownStatus.RED: 0.5,
                DrawdownStatus.CRITICAL: 0.0
            }
        
            return multipliers.get(status, 1.0)
        except Exception as e:
            logger.error(f"Error in get_position_size_multiplier: {e}")
            raise
    
    def get_history(self, lookback_hours: int = 24) -> List[DrawdownMetrics]:
        """Get drawdown history for last N hours."""
        try:
            if not self.drawdown_history:
                return []
        
            cutoff_time = datetime.now() - timedelta(hours=lookback_hours)
            return [m for m in self.drawdown_history if m.timestamp >= cutoff_time]
        except Exception as e:
            logger.error(f"Error in get_history: {e}")
            raise
    
    def get_worst_drawdown(self) -> float:
        """Get worst drawdown in history."""
        try:
            if not self.drawdown_history:
                return 0
        
            return max(m.drawdown_percent for m in self.drawdown_history)
        except Exception as e:
            logger.error(f"Error in get_worst_drawdown: {e}")
            raise
    
    def reset(self):
        """Reset all protections."""
        try:
            self.trading_halted = False
            self.halt_reason = None
            logger.info("Drawdown protector reset")
        except Exception as e:
            logger.error(f"Error in reset: {e}")
            raise
    
    def emergency_shutdown(self):
        """Emergency shutdown - halt all trading immediately."""
        try:
            self.trading_halted = True
            self.halt_reason = "EMERGENCY SHUTDOWN"
            logger.critical("EMERGENCY SHUTDOWN ACTIVATED")
        except Exception as e:
            logger.error(f"Error in emergency_shutdown: {e}")
            raise
