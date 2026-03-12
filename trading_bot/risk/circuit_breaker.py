"""
Elite Circuit Breaker System
Implements multiple layers of loss protection and automatic shutdown
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum
import json

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"      # Trading halted
    HALF_OPEN = "half_open"  # Testing recovery


class LossType(Enum):
    """Types of loss limits"""
    PER_TRADE = "per_trade"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    DRAWDOWN = "drawdown"


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker"""
    # Loss limits (as percentage of capital)
    max_loss_per_trade: float = 0.02  # 2%
    max_daily_loss: float = 0.05  # 5%
    max_weekly_loss: float = 0.10  # 10%
    max_monthly_loss: float = 0.15  # 15%
    max_drawdown: float = 0.20  # 20%
    
    # Position limits
    max_open_positions: int = 5
    max_correlated_positions: int = 3
    max_exposure_per_symbol: float = 0.10  # 10% of capital
    
    # Consecutive loss limits
    max_consecutive_losses: int = 5
    
    # Recovery settings
    recovery_wait_minutes: int = 60
    half_open_test_trades: int = 3
    
    # Emergency settings
    emergency_liquidation_drawdown: float = 0.25  # 25%


@dataclass
class TradingSession:
    """Track trading session metrics"""
    start_time: datetime
    initial_balance: float
    current_balance: float
    trades_today: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    consecutive_losses: int = 0
    daily_pnl: float = 0.0
    weekly_pnl: float = 0.0
    monthly_pnl: float = 0.0
    peak_balance: float = field(init=False)
    
    def __post_init__(self):
        try:
            self.peak_balance = self.initial_balance
        except Exception as e:
            logger.error(f"Error in __post_init__: {e}")
            raise


class CircuitBreaker:
    """
    Elite Circuit Breaker System
    
    Features:
    - Multiple loss limit layers
    - Automatic trading halt
    - Gradual recovery testing
    - Emergency liquidation
    - Position limits
    - Exposure management
    """
    
    def __init__(self, config: Optional[CircuitBreakerConfig] = None):
        try:
            self.config = config or CircuitBreakerConfig()
            self.state = CircuitState.CLOSED
            self.session: Optional[TradingSession] = None
            self.halt_reason: Optional[str] = None
            self.halt_time: Optional[datetime] = None
            self.test_trades_count = 0
        
            # Track daily/weekly/monthly resets
            self.last_daily_reset = datetime.now().date()
            self.last_weekly_reset = datetime.now().isocalendar()[1]
            self.last_monthly_reset = datetime.now().month
        
            logger.info("Circuit Breaker initialized")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def start_session(self, initial_balance: float):
        """Start a new trading session"""
        try:
            self.session = TradingSession(
                start_time=datetime.now(),
                initial_balance=initial_balance,
                current_balance=initial_balance
            )
            self.state = CircuitState.CLOSED
            logger.info(f"Trading session started with balance: ${initial_balance:,.2f}")
        except Exception as e:
            logger.error(f"Error in start_session: {e}")
            raise
    
    def can_trade(self) -> tuple[bool, Optional[str]]:
        """
        Check if trading is allowed
        
        Returns:
            (allowed, reason) tuple
        """
        try:
            if not self.session:
                return False, "No active trading session"
        
            # Check circuit state
            if self.state == CircuitState.OPEN:
                # Check if recovery period has passed
                if self.halt_time and datetime.now() - self.halt_time > timedelta(minutes=self.config.recovery_wait_minutes):
                    self._transition_to_half_open()
                else:
                    return False, f"Circuit OPEN: {self.halt_reason}"
        
            if self.state == CircuitState.HALF_OPEN:
                if self.test_trades_count >= self.config.half_open_test_trades:
                    return False, "Half-open test trades limit reached"
        
            # Reset counters if new period
            self._check_period_resets()
        
            # Check all limits
            checks = [
                self._check_daily_loss(),
                self._check_weekly_loss(),
                self._check_monthly_loss(),
                self._check_drawdown(),
                self._check_consecutive_losses(),
                self._check_position_limits()
            ]
        
            for passed, reason in checks:
                if not passed:
                    self._trip_circuit(reason)
                    return False, reason
        
            return True, None
        except Exception as e:
            logger.error(f"Error in can_trade: {e}")
            raise
    
    def record_trade(self, pnl: float, is_win: bool):
        """Record trade result and update metrics"""
        try:
            if not self.session:
                logger.error("No active session")
                return
        
            self.session.trades_today += 1
            self.session.current_balance += pnl
            self.session.daily_pnl += pnl
            self.session.weekly_pnl += pnl
            self.session.monthly_pnl += pnl
        
            # Update peak balance
            if self.session.current_balance > self.session.peak_balance:
                self.session.peak_balance = self.session.current_balance
        
            # Track wins/losses
            if is_win:
                self.session.winning_trades += 1
                self.session.consecutive_losses = 0
            else:
                self.session.losing_trades += 1
                self.session.consecutive_losses += 1
        
            # Check if in half-open state
            if self.state == CircuitState.HALF_OPEN:
                self.test_trades_count += 1
                if is_win:
                    # Successful test trade
                    if self.test_trades_count >= self.config.half_open_test_trades:
                        self._transition_to_closed()
        
            logger.info(f"Trade recorded: PNL=${pnl:,.2f}, Balance=${self.session.current_balance:,.2f}")
        except Exception as e:
            logger.error(f"Error in record_trade: {e}")
            raise
    
    def _check_daily_loss(self) -> tuple[bool, Optional[str]]:
        """Check daily loss limit"""
        try:
            if not self.session:
                return True, None
        
            daily_loss_pct = abs(self.session.daily_pnl) / self.session.initial_balance
            if self.session.daily_pnl < 0 and daily_loss_pct > self.config.max_daily_loss:
                return False, f"Daily loss limit exceeded: {daily_loss_pct:.2%}"
            return True, None
        except Exception as e:
            logger.error(f"Error in _check_daily_loss: {e}")
            raise
    
    def _check_weekly_loss(self) -> tuple[bool, Optional[str]]:
        """Check weekly loss limit"""
        try:
            if not self.session:
                return True, None
        
            weekly_loss_pct = abs(self.session.weekly_pnl) / self.session.initial_balance
            if self.session.weekly_pnl < 0 and weekly_loss_pct > self.config.max_weekly_loss:
                return False, f"Weekly loss limit exceeded: {weekly_loss_pct:.2%}"
            return True, None
        except Exception as e:
            logger.error(f"Error in _check_weekly_loss: {e}")
            raise
    
    def _check_monthly_loss(self) -> tuple[bool, Optional[str]]:
        """Check monthly loss limit"""
        try:
            if not self.session:
                return True, None
        
            monthly_loss_pct = abs(self.session.monthly_pnl) / self.session.initial_balance
            if self.session.monthly_pnl < 0 and monthly_loss_pct > self.config.max_monthly_loss:
                return False, f"Monthly loss limit exceeded: {monthly_loss_pct:.2%}"
            return True, None
        except Exception as e:
            logger.error(f"Error in _check_monthly_loss: {e}")
            raise
    
    def _check_drawdown(self) -> tuple[bool, Optional[str]]:
        """Check maximum drawdown"""
        try:
            if not self.session:
                return True, None
        
            drawdown = (self.session.peak_balance - self.session.current_balance) / self.session.peak_balance
        
            # Emergency liquidation
            if drawdown > self.config.emergency_liquidation_drawdown:
                logger.critical(f"EMERGENCY: Drawdown {drawdown:.2%} exceeds emergency threshold!")
                return False, f"EMERGENCY LIQUIDATION: Drawdown {drawdown:.2%}"
        
            if drawdown > self.config.max_drawdown:
                return False, f"Max drawdown exceeded: {drawdown:.2%}"
        
            return True, None
        except Exception as e:
            logger.error(f"Error in _check_drawdown: {e}")
            raise
    
    def _check_consecutive_losses(self) -> tuple[bool, Optional[str]]:
        """Check consecutive losses"""
        try:
            if not self.session:
                return True, None
        
            if self.session.consecutive_losses >= self.config.max_consecutive_losses:
                return False, f"Consecutive losses limit: {self.session.consecutive_losses}"
            return True, None
        except Exception as e:
            logger.error(f"Error in _check_consecutive_losses: {e}")
            raise
    
    def _check_position_limits(self) -> tuple[bool, Optional[str]]:
        """Check position limits (placeholder - integrate with position manager)"""
        # This would integrate with actual position manager
        return True, None
    
    def _check_period_resets(self):
        """Reset counters for new periods"""
        try:
            now = datetime.now()
        
            # Daily reset
            if now.date() > self.last_daily_reset:
                self.session.daily_pnl = 0.0
                self.session.trades_today = 0
                self.last_daily_reset = now.date()
                logger.info("Daily counters reset")
        
            # Weekly reset
            current_week = now.isocalendar()[1]
            if current_week != self.last_weekly_reset:
                self.session.weekly_pnl = 0.0
                self.last_weekly_reset = current_week
                logger.info("Weekly counters reset")
        
            # Monthly reset
            if now.month != self.last_monthly_reset:
                self.session.monthly_pnl = 0.0
                self.last_monthly_reset = now.month
                logger.info("Monthly counters reset")
        except Exception as e:
            logger.error(f"Error in _check_period_resets: {e}")
            raise
    
    def _trip_circuit(self, reason: str):
        """Trip the circuit breaker"""
        try:
            self.state = CircuitState.OPEN
            self.halt_reason = reason
            self.halt_time = datetime.now()
            logger.critical(f"🚨 CIRCUIT BREAKER TRIPPED: {reason}")
        
            # Send alerts (integrate with alert system)
            self._send_alert(f"Trading halted: {reason}")
        except Exception as e:
            logger.error(f"Error in _trip_circuit: {e}")
            raise
    
    def _transition_to_half_open(self):
        """Transition to half-open state for testing"""
        try:
            self.state = CircuitState.HALF_OPEN
            self.test_trades_count = 0
            logger.warning("Circuit breaker entering HALF-OPEN state for testing")
        except Exception as e:
            logger.error(f"Error in _transition_to_half_open: {e}")
            raise
    
    def _transition_to_closed(self):
        """Transition back to normal operation"""
        try:
            self.state = CircuitState.CLOSED
            self.halt_reason = None
            self.halt_time = None
            self.test_trades_count = 0
            logger.info("✅ Circuit breaker CLOSED - Normal trading resumed")
        except Exception as e:
            logger.error(f"Error in _transition_to_closed: {e}")
            raise
    
    def _send_alert(self, message: str):
        """Send alert (placeholder for integration with alert system)"""
        try:
            logger.critical(f"ALERT: {message}")
        except Exception as e:
            logger.error(f"Error in _send_alert: {e}")
            raise
        # Integrate with Telegram/Discord/Email alerts
    
    def get_status(self) -> Dict:
        """Get current circuit breaker status"""
        try:
            if not self.session:
                return {'status': 'NO_SESSION'}
        
            return {
                'state': self.state.value,
                'halt_reason': self.halt_reason,
                'balance': self.session.current_balance,
                'daily_pnl': self.session.daily_pnl,
                'weekly_pnl': self.session.weekly_pnl,
                'monthly_pnl': self.session.monthly_pnl,
                'trades_today': self.session.trades_today,
                'win_rate': self.session.winning_trades / max(self.session.trades_today, 1),
                'consecutive_losses': self.session.consecutive_losses,
                'drawdown': (self.session.peak_balance - self.session.current_balance) / self.session.peak_balance
            }
        except Exception as e:
            logger.error(f"Error in get_status: {e}")
            raise
    
    def force_reset(self):
        """Force reset circuit breaker (admin only)"""
        try:
            logger.warning("⚠️ Circuit breaker manually reset")
            self.state = CircuitState.CLOSED
            self.halt_reason = None
            self.halt_time = None
            if self.session:
                self.session.consecutive_losses = 0
        except Exception as e:
            logger.error(f"Error in force_reset: {e}")
            raise


# Export
__all__ = ['CircuitBreaker', 'CircuitBreakerConfig', 'CircuitState', 'LossType']
