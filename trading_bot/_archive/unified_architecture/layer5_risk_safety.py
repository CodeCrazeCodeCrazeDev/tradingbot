"""
Layer 5: Risk & Safety
======================

The risk and safety layer that protects capital and ensures system stability.

Components:
- RiskManager: Position sizing, portfolio risk, drawdown control
- FailSafeSystem: Multi-layer fail-safes
- CircuitBreaker: Automatic trading halts
- EmergencyController: Emergency shutdown capabilities
- RiskSafetyLayer: Master coordinator

Integrates:
- trading_bot/risk/MASTER_risk_manager.py
- trading_bot/qwen_codemender/fail_safe.py
- trading_bot/risk/circuit_breaker.py
- trading_bot/safety/emergency_kill_switch.py
- trading_bot/risk/var_engine.py
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional, Tuple
from enum import Enum
import numpy as np

logger = logging.getLogger(__name__)


class RiskLevel(Enum):
    """Risk levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class FailSafeMode(Enum):
    """Fail-safe operating modes"""
    NORMAL = "normal"
    CAUTIOUS = "cautious"
    DEFENSIVE = "defensive"
    EMERGENCY = "emergency"
    SHUTDOWN = "shutdown"


class CircuitBreakerState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"      # Trading halted
    HALF_OPEN = "half_open"  # Testing recovery


@dataclass
class RiskMetrics:
    """Current risk metrics"""
    timestamp: datetime
    
    # Position risk
    total_exposure: float
    max_position_size: float
    position_count: int
    
    # Portfolio risk
    portfolio_var: float  # Value at Risk
    portfolio_cvar: float  # Conditional VaR
    correlation_risk: float
    
    # Drawdown
    current_drawdown: float
    max_drawdown: float
    drawdown_duration_days: int
    
    # Performance
    daily_pnl: float
    weekly_pnl: float
    win_rate: float
    
    # Risk level
    overall_risk_level: RiskLevel


@dataclass
class RiskLimits:
    """Risk limits configuration"""
    # Per-trade limits
    max_risk_per_trade_pct: float = 2.0
    max_position_size_pct: float = 10.0
    
    # Portfolio limits
    max_total_exposure_pct: float = 100.0
    max_correlated_exposure_pct: float = 30.0
    max_positions: int = 10
    
    # Drawdown limits
    max_daily_loss_pct: float = 5.0
    max_weekly_loss_pct: float = 10.0
    max_drawdown_pct: float = 20.0
    
    # VaR limits
    max_var_pct: float = 5.0
    var_confidence: float = 0.95


@dataclass
class RiskCheckResult:
    """Result of a risk check"""
    approved: bool
    risk_level: RiskLevel
    adjusted_size: float
    warnings: List[str] = field(default_factory=list)
    rejections: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)


class RiskManager:
    """
    Comprehensive risk management
    
    Integrates:
    - trading_bot/risk/MASTER_risk_manager.py
    - trading_bot/risk/var_engine.py
    - trading_bot/risk/position_sizer.py
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.limits = RiskLimits(**config.get('limits', {}))
        
        # Portfolio state
        self.equity = config.get('initial_equity', 100000)
        self.peak_equity = self.equity
        self.positions: Dict[str, Dict] = {}
        
        # Performance tracking
        self.daily_pnl = 0.0
        self.weekly_pnl = 0.0
        self.trade_results: List[float] = []
        
        try:
            # Import existing risk manager
            from trading_bot.risk.MASTER_risk_manager import MasterRiskManager
            self._risk_manager = MasterRiskManager(config)
            logger.info("Risk manager initialized with MasterRiskManager")
        except Exception as e:
            logger.warning(f"Using fallback risk manager: {e}")
            self._risk_manager = None
        # VaR engine
            from trading_bot.risk.var_engine import VaREngine
            self._var_engine = VaREngine(config.get('var', {}))
        except Exception:
            self._var_engine = None
    
    def check_trade(self, symbol: str, side: str, size: float,
                   entry_price: float, stop_loss: float) -> RiskCheckResult:
        """Check if a trade passes risk limits"""
        warnings = []
        rejections = []
        recommendations = []
        
        # Calculate risk
        risk_per_unit = abs(entry_price - stop_loss)
        total_risk = risk_per_unit * size
        risk_pct = (total_risk / self.equity) * 100
        
        # Check per-trade risk
        if risk_pct > self.limits.max_risk_per_trade_pct:
            rejections.append(f"Risk {risk_pct:.2f}% exceeds limit {self.limits.max_risk_per_trade_pct}%")
        elif risk_pct > self.limits.max_risk_per_trade_pct * 0.8:
            warnings.append(f"Risk {risk_pct:.2f}% approaching limit")
        
        # Check position size
        position_value = size * entry_price
        position_pct = (position_value / self.equity) * 100
        
        if position_pct > self.limits.max_position_size_pct:
            rejections.append(f"Position size {position_pct:.2f}% exceeds limit")
        
        # Check total exposure
        current_exposure = sum(p.get('value', 0) for p in self.positions.values())
        new_exposure = current_exposure + position_value
        exposure_pct = (new_exposure / self.equity) * 100
        
        if exposure_pct > self.limits.max_total_exposure_pct:
            rejections.append(f"Total exposure {exposure_pct:.2f}% would exceed limit")
        
        # Check position count
        if len(self.positions) >= self.limits.max_positions:
            rejections.append(f"Max positions ({self.limits.max_positions}) reached")
        
        # Check drawdown
        current_dd = self._calculate_drawdown()
        if current_dd > self.limits.max_drawdown_pct:
            rejections.append(f"Drawdown {current_dd:.2f}% exceeds limit")
        elif current_dd > self.limits.max_drawdown_pct * 0.7:
            warnings.append(f"Drawdown {current_dd:.2f}% elevated")
            recommendations.append("Consider reducing position size")
        
        # Check daily loss
        if self.daily_pnl < 0:
            daily_loss_pct = abs(self.daily_pnl / self.equity) * 100
            if daily_loss_pct > self.limits.max_daily_loss_pct:
                rejections.append(f"Daily loss {daily_loss_pct:.2f}% exceeds limit")
        
        # Determine result
        approved = len(rejections) == 0
        
        # Adjust size if needed
        adjusted_size = size
        if warnings and approved:
            # Reduce size by 20% if warnings present
            adjusted_size = size * 0.8
            recommendations.append(f"Size reduced from {size} to {adjusted_size}")
        
        # Determine risk level
        if rejections:
            risk_level = RiskLevel.CRITICAL
        elif len(warnings) > 2:
            risk_level = RiskLevel.HIGH
        elif warnings:
            risk_level = RiskLevel.MEDIUM
        else:
            risk_level = RiskLevel.LOW
        
        return RiskCheckResult(
            approved=approved,
            risk_level=risk_level,
            adjusted_size=adjusted_size,
            warnings=warnings,
            rejections=rejections,
            recommendations=recommendations
        )
    
    def calculate_position_size(self, symbol: str, entry_price: float,
                               stop_loss: float, risk_pct: Optional[float] = None) -> float:
        """Calculate optimal position size"""
        risk_pct = risk_pct or self.limits.max_risk_per_trade_pct
        
        # Risk per unit
        risk_per_unit = abs(entry_price - stop_loss)
        if risk_per_unit == 0:
            return 0
        
        # Max risk amount
        max_risk = self.equity * (risk_pct / 100)
        
        # Position size
        size = max_risk / risk_per_unit
        
        # Apply position size limit
        max_position_value = self.equity * (self.limits.max_position_size_pct / 100)
        max_size = max_position_value / entry_price
        
        return min(size, max_size)
    
    def update_position(self, symbol: str, size: float, entry_price: float,
                       current_price: float):
        """Update position tracking"""
        self.positions[symbol] = {
            'size': size,
            'entry_price': entry_price,
            'current_price': current_price,
            'value': size * current_price,
            'pnl': (current_price - entry_price) * size
        }
    
    def close_position(self, symbol: str, exit_price: float):
        """Close a position and record result"""
        if symbol not in self.positions:
            return
        
        position = self.positions[symbol]
        pnl = (exit_price - position['entry_price']) * position['size']
        
        # Update tracking
        self.daily_pnl += pnl
        self.weekly_pnl += pnl
        self.equity += pnl
        self.trade_results.append(pnl)
        
        # Update peak
        if self.equity > self.peak_equity:
            self.peak_equity = self.equity
        
        del self.positions[symbol]
    
    def _calculate_drawdown(self) -> float:
        """Calculate current drawdown percentage"""
        if self.peak_equity == 0:
            return 0
        return ((self.peak_equity - self.equity) / self.peak_equity) * 100
    
    def get_metrics(self) -> RiskMetrics:
        """Get current risk metrics"""
        # Calculate metrics
        total_exposure = sum(p.get('value', 0) for p in self.positions.values())
        max_position = max((p.get('value', 0) for p in self.positions.values()), default=0)
        
        # Win rate
        if self.trade_results:
            wins = sum(1 for r in self.trade_results if r > 0)
            win_rate = wins / len(self.trade_results)
        else:
            win_rate = 0.5
        
        # Determine risk level
        dd = self._calculate_drawdown()
        if dd > self.limits.max_drawdown_pct * 0.8:
            risk_level = RiskLevel.CRITICAL
        elif dd > self.limits.max_drawdown_pct * 0.5:
            risk_level = RiskLevel.HIGH
        elif dd > self.limits.max_drawdown_pct * 0.3:
            risk_level = RiskLevel.MEDIUM
        else:
            risk_level = RiskLevel.LOW
        
        return RiskMetrics(
            timestamp=datetime.now(),
            total_exposure=total_exposure,
            max_position_size=max_position,
            position_count=len(self.positions),
            portfolio_var=0.0,  # Would need VaR calculation
            portfolio_cvar=0.0,
            correlation_risk=0.0,
            current_drawdown=dd,
            max_drawdown=dd,  # Would need historical tracking
            drawdown_duration_days=0,
            daily_pnl=self.daily_pnl,
            weekly_pnl=self.weekly_pnl,
            win_rate=win_rate,
            overall_risk_level=risk_level
        )
    
    def reset_daily(self):
        """Reset daily metrics"""
        self.daily_pnl = 0.0
    
    def reset_weekly(self):
        """Reset weekly metrics"""
        self.weekly_pnl = 0.0


class FailSafeSystem:
    """
    Multi-layer fail-safe system
    
    Integrates trading_bot/qwen_codemender/fail_safe.py
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Current mode
        self.mode = FailSafeMode.NORMAL
        
        # Thresholds
        self.thresholds = {
            'cautious_drawdown': config.get('cautious_drawdown', 5.0),
            'defensive_drawdown': config.get('defensive_drawdown', 10.0),
            'emergency_drawdown': config.get('emergency_drawdown', 15.0),
            'shutdown_drawdown': config.get('shutdown_drawdown', 20.0),
            'max_consecutive_losses': config.get('max_consecutive_losses', 5),
            'max_daily_loss': config.get('max_daily_loss', 5.0)
        }
        
        # Position size multipliers by mode
        self.size_multipliers = {
            FailSafeMode.NORMAL: 1.0,
            FailSafeMode.CAUTIOUS: 0.75,
            FailSafeMode.DEFENSIVE: 0.5,
            FailSafeMode.EMERGENCY: 0.25,
            FailSafeMode.SHUTDOWN: 0.0
        }
        
        # Tracking
        self.consecutive_losses = 0
        self.mode_history: List[Tuple[datetime, FailSafeMode]] = []
        
        try:
            # Import existing fail-safe
            self._fail_safe = None  # Using built-in fail-safe
            logger.info("Fail-safe system initialized")
        except Exception as e:
            logger.warning(f"Using fallback fail-safe: {e}")
            self._fail_safe = None
    
    def check_and_update(self, metrics: RiskMetrics) -> FailSafeMode:
        """Check metrics and update fail-safe mode"""
        old_mode = self.mode
        
        # Check drawdown levels
        dd = metrics.current_drawdown
        
        if dd >= self.thresholds['shutdown_drawdown']:
            self.mode = FailSafeMode.SHUTDOWN
        elif dd >= self.thresholds['emergency_drawdown']:
            self.mode = FailSafeMode.EMERGENCY
        elif dd >= self.thresholds['defensive_drawdown']:
            self.mode = FailSafeMode.DEFENSIVE
        elif dd >= self.thresholds['cautious_drawdown']:
            self.mode = FailSafeMode.CAUTIOUS
        else:
            # Can recover to normal if conditions improve
            if self.mode != FailSafeMode.SHUTDOWN:
                self.mode = FailSafeMode.NORMAL
        
        # Check consecutive losses
        if self.consecutive_losses >= self.thresholds['max_consecutive_losses']:
            if self.mode.value < FailSafeMode.DEFENSIVE.value:
                self.mode = FailSafeMode.DEFENSIVE
        
        # Log mode change
        if self.mode != old_mode:
            self.mode_history.append((datetime.now(), self.mode))
            logger.warning(f"Fail-safe mode changed: {old_mode.value} -> {self.mode.value}")
        
        return self.mode
    
    def record_trade_result(self, is_win: bool):
        """Record trade result for consecutive loss tracking"""
        if is_win:
            self.consecutive_losses = 0
        else:
            self.consecutive_losses += 1
    
    def get_position_multiplier(self) -> float:
        """Get position size multiplier for current mode"""
        return self.size_multipliers.get(self.mode, 1.0)
    
    def can_trade(self) -> Tuple[bool, str]:
        """Check if trading is allowed"""
        if self.mode == FailSafeMode.SHUTDOWN:
            return False, "System in SHUTDOWN mode"
        if self.mode == FailSafeMode.EMERGENCY:
            return False, "System in EMERGENCY mode - new trades blocked"
        return True, "Trading allowed"
    
    def force_mode(self, mode: FailSafeMode, reason: str):
        """Force a specific mode"""
        old_mode = self.mode
        self.mode = mode
        self.mode_history.append((datetime.now(), mode))
        logger.warning(f"Fail-safe mode forced: {old_mode.value} -> {mode.value} - {reason}")


class CircuitBreaker:
    """
    Circuit breaker for automatic trading halts
    
    Integrates trading_bot/risk/circuit_breaker.py
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # State
        self.state = CircuitBreakerState.CLOSED
        self.opened_at: Optional[datetime] = None
        self.open_reason: Optional[str] = None
        
        # Thresholds
        self.error_threshold = config.get('error_threshold', 5)
        self.error_window_seconds = config.get('error_window_seconds', 60)
        self.recovery_timeout_seconds = config.get('recovery_timeout_seconds', 300)
        
        # Error tracking
        self.errors: List[datetime] = []
        
        try:
            # Import existing circuit breaker
            from trading_bot.risk.circuit_breaker import CircuitBreaker as ExistingCB
            self._circuit_breaker = ExistingCB(config)
            logger.info("Circuit breaker initialized")
        except Exception as e:
            logger.warning(f"Using fallback circuit breaker: {e}")
            self._circuit_breaker = None
    
    def record_error(self, error: str):
        """Record an error"""
        now = datetime.now()
        self.errors.append(now)
        
        # Clean old errors
        cutoff = now - timedelta(seconds=self.error_window_seconds)
        self.errors = [e for e in self.errors if e > cutoff]
        
        # Check threshold
        if len(self.errors) >= self.error_threshold:
            self.trip(f"Error threshold exceeded: {error}")
    
    def trip(self, reason: str):
        """Trip the circuit breaker"""
        if self.state != CircuitBreakerState.OPEN:
            self.state = CircuitBreakerState.OPEN
            self.opened_at = datetime.now()
            self.open_reason = reason
            logger.error(f"Circuit breaker TRIPPED: {reason}")
    
    def check_recovery(self) -> bool:
        """Check if circuit breaker can recover"""
        if self.state != CircuitBreakerState.OPEN:
            return True
        
        if self.opened_at is None:
            return False
        
        elapsed = (datetime.now() - self.opened_at).total_seconds()
        
        if elapsed >= self.recovery_timeout_seconds:
            self.state = CircuitBreakerState.HALF_OPEN
            logger.info("Circuit breaker entering HALF_OPEN state")
            return True
        
        return False
    
    def record_success(self):
        """Record a successful operation"""
        if self.state == CircuitBreakerState.HALF_OPEN:
            self.state = CircuitBreakerState.CLOSED
            self.opened_at = None
            self.open_reason = None
            self.errors.clear()
            logger.info("Circuit breaker CLOSED - recovered")
    
    def is_open(self) -> bool:
        """Check if circuit breaker is open"""
        self.check_recovery()
        return self.state == CircuitBreakerState.OPEN
    
    def reset(self):
        """Manually reset the circuit breaker"""
        self.state = CircuitBreakerState.CLOSED
        self.opened_at = None
        self.open_reason = None
        self.errors.clear()
        logger.info("Circuit breaker manually reset")


class EmergencyController:
    """
    Emergency shutdown controller
    
    Integrates trading_bot/safety/emergency_kill_switch.py
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # State
        self.emergency_active = False
        self.shutdown_reason: Optional[str] = None
        self.shutdown_time: Optional[datetime] = None
        
        # Callbacks
        self.on_emergency: List[Callable] = []
        
        try:
            # Import existing kill switch
            from trading_bot.safety.emergency_kill_switch import EmergencyKillSwitch
            self._kill_switch = EmergencyKillSwitch(config)
            logger.info("Emergency controller initialized")
        except Exception as e:
            logger.warning(f"Using fallback emergency controller: {e}")
            self._kill_switch = None
    
    def trigger_emergency(self, reason: str):
        """Trigger emergency shutdown"""
        self.emergency_active = True
        self.shutdown_reason = reason
        self.shutdown_time = datetime.now()
        
        logger.critical(f"EMERGENCY SHUTDOWN TRIGGERED: {reason}")
        
        # Call callbacks
        for callback in self.on_emergency:
            try:
                callback(reason)
            except Exception as e:
                logger.error(f"Emergency callback error: {e}")
        
        # Use existing kill switch if available
        if self._kill_switch:
            self._kill_switch.activate(reason)
    
    def clear_emergency(self, authorization: str):
        """Clear emergency state (requires authorization)"""
        if authorization != self.config.get('emergency_clear_code', 'CLEAR_EMERGENCY'):
            logger.warning("Invalid emergency clear authorization")
            return False
        
        self.emergency_active = False
        self.shutdown_reason = None
        self.shutdown_time = None
        
        logger.info("Emergency state cleared")
        return True
    
    def is_emergency(self) -> bool:
        """Check if emergency is active"""
        return self.emergency_active
    
    def register_callback(self, callback: Callable):
        """Register emergency callback"""
        self.on_emergency.append(callback)


class RiskSafetyLayer:
    """
    Master coordinator for Layer 5: Risk & Safety
    
    Orchestrates all risk and safety components
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Initialize components
        self.risk_manager = RiskManager(config.get('risk', {}))
        self.fail_safe = FailSafeSystem(config.get('fail_safe', {}))
        self.circuit_breaker = CircuitBreaker(config.get('circuit_breaker', {}))
        self.emergency = EmergencyController(config.get('emergency', {}))
        
        # Register emergency callback
        self.emergency.register_callback(self._on_emergency)
        
        logger.info("Risk & Safety Layer initialized")
    
    def _on_emergency(self, reason: str):
        """Handle emergency"""
        self.fail_safe.force_mode(FailSafeMode.SHUTDOWN, reason)
        self.circuit_breaker.trip(reason)
    
    def pre_trade_check(self, symbol: str, side: str, size: float,
                       entry_price: float, stop_loss: float) -> RiskCheckResult:
        """
        Comprehensive pre-trade risk check
        
        Checks:
        1. Emergency status
        2. Circuit breaker
        3. Fail-safe mode
        4. Risk limits
        """
        # Check emergency
        if self.emergency.is_emergency():
            return RiskCheckResult(
                approved=False,
                risk_level=RiskLevel.CRITICAL,
                adjusted_size=0,
                rejections=["Emergency shutdown active"]
            )
        
        # Check circuit breaker
        if self.circuit_breaker.is_open():
            return RiskCheckResult(
                approved=False,
                risk_level=RiskLevel.CRITICAL,
                adjusted_size=0,
                rejections=[f"Circuit breaker open: {self.circuit_breaker.open_reason}"]
            )
        
        # Check fail-safe
        can_trade, reason = self.fail_safe.can_trade()
        if not can_trade:
            return RiskCheckResult(
                approved=False,
                risk_level=RiskLevel.CRITICAL,
                adjusted_size=0,
                rejections=[reason]
            )
        
        # Run risk check
        result = self.risk_manager.check_trade(symbol, side, size, entry_price, stop_loss)
        
        # Apply fail-safe multiplier
        if result.approved:
            multiplier = self.fail_safe.get_position_multiplier()
            result.adjusted_size *= multiplier
            if multiplier < 1.0:
                result.warnings.append(f"Size reduced by fail-safe ({self.fail_safe.mode.value})")
        
        return result
    
    def record_trade_result(self, symbol: str, is_win: bool, pnl: float,
                           exit_price: float):
        """Record trade result and update all systems"""
        # Update risk manager
        self.risk_manager.close_position(symbol, exit_price)
        
        # Update fail-safe
        self.fail_safe.record_trade_result(is_win)
        
        # Update fail-safe mode based on new metrics
        metrics = self.risk_manager.get_metrics()
        self.fail_safe.check_and_update(metrics)
        
        # Record success for circuit breaker
        if is_win:
            self.circuit_breaker.record_success()
    
    def record_error(self, error: str):
        """Record an error"""
        self.circuit_breaker.record_error(error)
    
    def get_status(self) -> Dict[str, Any]:
        """Get risk & safety status"""
        metrics = self.risk_manager.get_metrics()
        
        return {
            'risk_metrics': {
                'drawdown': metrics.current_drawdown,
                'daily_pnl': metrics.daily_pnl,
                'positions': metrics.position_count,
                'risk_level': metrics.overall_risk_level.value
            },
            'fail_safe': {
                'mode': self.fail_safe.mode.value,
                'position_multiplier': self.fail_safe.get_position_multiplier(),
                'consecutive_losses': self.fail_safe.consecutive_losses
            },
            'circuit_breaker': {
                'state': self.circuit_breaker.state.value,
                'open_reason': self.circuit_breaker.open_reason
            },
            'emergency': {
                'active': self.emergency.is_emergency(),
                'reason': self.emergency.shutdown_reason
            }
        }
    
    def trigger_emergency(self, reason: str):
        """Trigger emergency shutdown"""
        self.emergency.trigger_emergency(reason)
