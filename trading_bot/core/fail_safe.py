"""
Fail-Safe System for Trading Bot
================================

Provides multiple layers of protection to prevent catastrophic losses:
1. Trading mode management (NO_TRADE, SIMULATION, PAPER, LIVE)
2. System health monitoring
3. Safety checks before any trade
4. Automatic degradation when issues detected
"""

import logging
import threading
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from typing import Dict, List, Optional, Callable, Any
from pathlib import Path
import json

logger = logging.getLogger(__name__)


class TradingMode(Enum):
    """Trading mode - determines what actions are allowed"""
    NO_TRADE = auto()      # No trading allowed - emergency mode
    SIMULATION = auto()    # Simulated trades only (no broker connection)
    PAPER = auto()         # Paper trading (broker connected, no real money)
    LIVE = auto()          # Live trading with real money


class SystemHealth(Enum):
    """System health levels"""
    CRITICAL = auto()      # System is in critical state - stop everything
    DEGRADED = auto()      # System has issues - reduce activity
    WARNING = auto()       # Minor issues detected - monitor closely
    HEALTHY = auto()       # System is operating normally
    OPTIMAL = auto()       # System is performing optimally


class SafetyCheck(Enum):
    """Types of safety checks"""
    BROKER_CONNECTION = "broker_connection"
    DATA_FRESHNESS = "data_freshness"
    RISK_LIMITS = "risk_limits"
    POSITION_LIMITS = "position_limits"
    DRAWDOWN_LIMIT = "drawdown_limit"
    DAILY_LOSS_LIMIT = "daily_loss_limit"
    SYSTEM_RESOURCES = "system_resources"
    MARKET_HOURS = "market_hours"
    VOLATILITY_CHECK = "volatility_check"
    CORRELATION_CHECK = "correlation_check"
    HEARTBEAT = "heartbeat"
    KILL_SWITCH = "kill_switch"


@dataclass
class SafetyCheckResult:
    """Result of a safety check"""
    check: SafetyCheck
    passed: bool
    message: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FailSafeState:
    """Current state of the fail-safe system"""
    trading_mode: TradingMode
    system_health: SystemHealth
    last_check: datetime
    failed_checks: List[SafetyCheck]
    warnings: List[str]
    can_trade: bool
    reason: str


class FailSafe:
    """
    Fail-safe system that prevents trading when conditions are unsafe.
    
    Core principle: "I refuse to trade until conditions are safe"
    
    Features:
    - Multiple trading modes with automatic degradation
    - Comprehensive safety checks before each trade
    - System health monitoring
    - Automatic recovery when conditions improve
    - Immutable safety limits that cannot be bypassed
    """
    
    # IMMUTABLE LIMITS - Cannot be changed programmatically
    IMMUTABLE_MAX_RISK_PER_TRADE = 0.02      # 2% max risk per trade
    IMMUTABLE_MAX_DAILY_LOSS = 0.05          # 5% max daily loss
    IMMUTABLE_MAX_DRAWDOWN = 0.20            # 20% max drawdown
    IMMUTABLE_MAX_POSITION_SIZE = 0.10       # 10% max position size
    IMMUTABLE_MAX_LEVERAGE = 5.0             # 5x max leverage
    IMMUTABLE_MAX_CORRELATED_EXPOSURE = 0.30 # 30% max correlated exposure
    
    def __init__(
        self,
        initial_mode: TradingMode = TradingMode.PAPER,
        check_interval: float = 60.0,
        auto_degrade: bool = True,
        state_file: Optional[str] = None
    ):
        """
        Initialize fail-safe system.
        
        Args:
            initial_mode: Starting trading mode
            check_interval: Seconds between automatic checks
            auto_degrade: Automatically degrade mode on failures
            state_file: File to persist state
        """
        self._lock = threading.RLock()
        self._trading_mode = initial_mode
        self._system_health = SystemHealth.HEALTHY
        self._check_interval = check_interval
        self._auto_degrade = auto_degrade
        self._state_file = Path(state_file) if state_file else None
        
        # Check results
        self._check_results: Dict[SafetyCheck, SafetyCheckResult] = {}
        self._failed_checks: List[SafetyCheck] = []
        self._warnings: List[str] = []
        
        # Callbacks
        self._on_mode_change: Optional[Callable] = None
        self._on_health_change: Optional[Callable] = None
        self._on_trade_blocked: Optional[Callable] = None
        
        # Custom check functions
        self._custom_checks: Dict[str, Callable] = {}
        
        # Tracking
        self._last_check = datetime.utcnow()
        self._trade_blocked_count = 0
        self._mode_changes: List[Dict] = []
        
        # Load persisted state
        self._load_state()
        
        logger.info(f"FailSafe initialized: mode={initial_mode.name}, health={self._system_health.name}")
    
    @property
    def trading_mode(self) -> TradingMode:
        """Get current trading mode"""
        return self._trading_mode
    
    @property
    def system_health(self) -> SystemHealth:
        """Get current system health"""
        return self._system_health
    
    @property
    def can_trade(self) -> bool:
        """Check if trading is currently allowed"""
        with self._lock:
            if self._trading_mode == TradingMode.NO_TRADE:
                return False
            if self._system_health == SystemHealth.CRITICAL:
                return False
            if self._failed_checks:
                return False
            return True
    
    def set_mode(self, mode: TradingMode, reason: str = "Manual change") -> bool:
        """
        Set trading mode.
        
        Args:
            mode: New trading mode
            reason: Reason for change
            
        Returns:
            True if mode was changed
        """
        with self._lock:
            if mode == self._trading_mode:
                return False
            
            old_mode = self._trading_mode
            self._trading_mode = mode
            
            change = {
                "timestamp": datetime.utcnow().isoformat(),
                "from": old_mode.name,
                "to": mode.name,
                "reason": reason
            }
            self._mode_changes.append(change)
            
            logger.info(f"Trading mode changed: {old_mode.name} -> {mode.name} ({reason})")
            
            if self._on_mode_change:
                try:
                    self._on_mode_change(old_mode, mode, reason)
                except Exception as e:
                    logger.error(f"Mode change callback error: {e}")
            
            self._save_state()
            return True
    
    def set_health(self, health: SystemHealth, reason: str = ""):
        """Set system health level"""
        with self._lock:
            if health == self._system_health:
                return
            
            old_health = self._system_health
            self._system_health = health
            
            logger.info(f"System health changed: {old_health.name} -> {health.name} ({reason})")
            
            if self._on_health_change:
                try:
                    self._on_health_change(old_health, health, reason)
                except Exception as e:
                    logger.error(f"Health change callback error: {e}")
            
            # Auto-degrade trading mode if health is critical
            if self._auto_degrade and health == SystemHealth.CRITICAL:
                self.set_mode(TradingMode.NO_TRADE, "Critical system health")
            
            self._save_state()
    
    def run_safety_checks(
        self,
        broker_connected: bool = True,
        data_age_seconds: float = 0,
        current_drawdown: float = 0,
        daily_loss: float = 0,
        position_count: int = 0,
        max_positions: int = 10,
        market_open: bool = True,
        volatility_ratio: float = 1.0,
        kill_switch_active: bool = False
    ) -> List[SafetyCheckResult]:
        """
        Run all safety checks.
        
        Args:
            broker_connected: Is broker connection active
            data_age_seconds: Age of market data in seconds
            current_drawdown: Current drawdown as decimal
            daily_loss: Today's loss as decimal
            position_count: Number of open positions
            max_positions: Maximum allowed positions
            market_open: Is market currently open
            volatility_ratio: Current volatility vs normal
            kill_switch_active: Is kill switch activated
            
        Returns:
            List of SafetyCheckResult
        """
        results = []
        
        with self._lock:
            self._failed_checks = []
            self._warnings = []
            
            # Check 1: Broker Connection
            result = SafetyCheckResult(
                check=SafetyCheck.BROKER_CONNECTION,
                passed=broker_connected,
                message="Broker connected" if broker_connected else "Broker disconnected"
            )
            results.append(result)
            if not result.passed:
                self._failed_checks.append(SafetyCheck.BROKER_CONNECTION)
            
            # Check 2: Data Freshness
            data_fresh = data_age_seconds < 60
            result = SafetyCheckResult(
                check=SafetyCheck.DATA_FRESHNESS,
                passed=data_fresh,
                message=f"Data age: {data_age_seconds:.1f}s" if data_fresh else f"Stale data: {data_age_seconds:.1f}s"
            )
            results.append(result)
            if not result.passed:
                self._failed_checks.append(SafetyCheck.DATA_FRESHNESS)
            
            # Check 3: Drawdown Limit (IMMUTABLE)
            drawdown_ok = current_drawdown < self.IMMUTABLE_MAX_DRAWDOWN
            result = SafetyCheckResult(
                check=SafetyCheck.DRAWDOWN_LIMIT,
                passed=drawdown_ok,
                message=f"Drawdown: {current_drawdown:.1%}" if drawdown_ok else f"DRAWDOWN EXCEEDED: {current_drawdown:.1%}",
                details={"current": current_drawdown, "limit": self.IMMUTABLE_MAX_DRAWDOWN}
            )
            results.append(result)
            if not result.passed:
                self._failed_checks.append(SafetyCheck.DRAWDOWN_LIMIT)
            
            # Check 4: Daily Loss Limit (IMMUTABLE)
            daily_ok = daily_loss < self.IMMUTABLE_MAX_DAILY_LOSS
            result = SafetyCheckResult(
                check=SafetyCheck.DAILY_LOSS_LIMIT,
                passed=daily_ok,
                message=f"Daily loss: {daily_loss:.1%}" if daily_ok else f"DAILY LOSS EXCEEDED: {daily_loss:.1%}",
                details={"current": daily_loss, "limit": self.IMMUTABLE_MAX_DAILY_LOSS}
            )
            results.append(result)
            if not result.passed:
                self._failed_checks.append(SafetyCheck.DAILY_LOSS_LIMIT)
            
            # Check 5: Position Limits
            positions_ok = position_count < max_positions
            result = SafetyCheckResult(
                check=SafetyCheck.POSITION_LIMITS,
                passed=positions_ok,
                message=f"Positions: {position_count}/{max_positions}" if positions_ok else f"Position limit reached: {position_count}/{max_positions}"
            )
            results.append(result)
            if not result.passed:
                self._failed_checks.append(SafetyCheck.POSITION_LIMITS)
            
            # Check 6: Market Hours
            result = SafetyCheckResult(
                check=SafetyCheck.MARKET_HOURS,
                passed=market_open,
                message="Market open" if market_open else "Market closed"
            )
            results.append(result)
            if not result.passed:
                self._warnings.append("Market is closed")
            
            # Check 7: Volatility
            volatility_ok = volatility_ratio < 3.0
            result = SafetyCheckResult(
                check=SafetyCheck.VOLATILITY_CHECK,
                passed=volatility_ok,
                message=f"Volatility ratio: {volatility_ratio:.1f}x" if volatility_ok else f"EXTREME VOLATILITY: {volatility_ratio:.1f}x normal"
            )
            results.append(result)
            if not result.passed:
                self._warnings.append(f"High volatility: {volatility_ratio:.1f}x")
            
            # Check 8: Kill Switch
            result = SafetyCheckResult(
                check=SafetyCheck.KILL_SWITCH,
                passed=not kill_switch_active,
                message="Kill switch inactive" if not kill_switch_active else "KILL SWITCH ACTIVE"
            )
            results.append(result)
            if not result.passed:
                self._failed_checks.append(SafetyCheck.KILL_SWITCH)
            
            # Run custom checks
            for name, check_func in self._custom_checks.items():
                try:
                    passed, message = check_func()
                    result = SafetyCheckResult(
                        check=SafetyCheck.SYSTEM_RESOURCES,
                        passed=passed,
                        message=f"{name}: {message}"
                    )
                    results.append(result)
                    if not passed:
                        self._warnings.append(f"{name}: {message}")
                except Exception as e:
                    logger.error(f"Custom check '{name}' failed: {e}")
            
            # Store results
            for result in results:
                self._check_results[result.check] = result
            
            self._last_check = datetime.utcnow()
            
            # Update health based on results
            self._update_health()
            
            return results
    
    def _update_health(self):
        """Update system health based on check results"""
        if self._failed_checks:
            critical_checks = [
                SafetyCheck.KILL_SWITCH,
                SafetyCheck.DRAWDOWN_LIMIT,
                SafetyCheck.DAILY_LOSS_LIMIT
            ]
            
            if any(c in self._failed_checks for c in critical_checks):
                self.set_health(SystemHealth.CRITICAL, f"Critical check failed: {self._failed_checks}")
            else:
                self.set_health(SystemHealth.DEGRADED, f"Checks failed: {self._failed_checks}")
        elif self._warnings:
            self.set_health(SystemHealth.WARNING, f"Warnings: {len(self._warnings)}")
        else:
            self.set_health(SystemHealth.HEALTHY, "All checks passed")
    
    def validate_trade(
        self,
        symbol: str,
        direction: str,
        quantity: float,
        price: float,
        account_equity: float,
        current_positions: Dict[str, float] = None
    ) -> tuple:
        """
        Validate a trade against safety limits.
        
        Args:
            symbol: Trading symbol
            direction: BUY or SELL
            quantity: Trade quantity
            price: Trade price
            account_equity: Current account equity
            current_positions: Dict of symbol -> position value
            
        Returns:
            (allowed: bool, reason: str)
        """
        with self._lock:
            # Check if trading is allowed
            if not self.can_trade:
                reason = f"Trading not allowed: mode={self._trading_mode.name}, health={self._system_health.name}"
                self._block_trade(symbol, reason)
                return False, reason
            
            # Calculate trade value
            trade_value = quantity * price
            
            # Check position size limit (IMMUTABLE)
            position_pct = trade_value / account_equity if account_equity > 0 else 1.0
            if position_pct > self.IMMUTABLE_MAX_POSITION_SIZE:
                reason = f"Position size {position_pct:.1%} exceeds limit {self.IMMUTABLE_MAX_POSITION_SIZE:.1%}"
                self._block_trade(symbol, reason)
                return False, reason
            
            # Check risk per trade (IMMUTABLE)
            # Assuming 2% stop loss, risk = position_size * 0.02
            estimated_risk = position_pct * 0.02
            if estimated_risk > self.IMMUTABLE_MAX_RISK_PER_TRADE:
                reason = f"Estimated risk {estimated_risk:.1%} exceeds limit {self.IMMUTABLE_MAX_RISK_PER_TRADE:.1%}"
                self._block_trade(symbol, reason)
                return False, reason
            
            # Check correlated exposure
            if current_positions:
                # Simple correlation check - same symbol
                existing = current_positions.get(symbol, 0)
                total_exposure = (existing + trade_value) / account_equity if account_equity > 0 else 1.0
                if total_exposure > self.IMMUTABLE_MAX_CORRELATED_EXPOSURE:
                    reason = f"Correlated exposure {total_exposure:.1%} exceeds limit {self.IMMUTABLE_MAX_CORRELATED_EXPOSURE:.1%}"
                    self._block_trade(symbol, reason)
                    return False, reason
            
            return True, "Trade validated"
    
    def _block_trade(self, symbol: str, reason: str):
        """Record a blocked trade"""
        self._trade_blocked_count += 1
        logger.warning(f"Trade blocked for {symbol}: {reason}")
        
        if self._on_trade_blocked:
            try:
                self._on_trade_blocked(symbol, reason)
            except Exception as e:
                logger.error(f"Trade blocked callback error: {e}")
    
    def add_custom_check(self, name: str, check_func: Callable[[], tuple]):
        """
        Add a custom safety check.
        
        Args:
            name: Check name
            check_func: Function that returns (passed: bool, message: str)
        """
        self._custom_checks[name] = check_func
        logger.info(f"Added custom safety check: {name}")
    
    def get_state(self) -> FailSafeState:
        """Get current fail-safe state"""
        with self._lock:
            return FailSafeState(
                trading_mode=self._trading_mode,
                system_health=self._system_health,
                last_check=self._last_check,
                failed_checks=self._failed_checks.copy(),
                warnings=self._warnings.copy(),
                can_trade=self.can_trade,
                reason=self._get_reason()
            )
    
    def _get_reason(self) -> str:
        """Get reason for current state"""
        if self._trading_mode == TradingMode.NO_TRADE:
            return "Trading mode is NO_TRADE"
        if self._system_health == SystemHealth.CRITICAL:
            return "System health is CRITICAL"
        if self._failed_checks:
            return f"Failed checks: {[c.value for c in self._failed_checks]}"
        return "System operational"
    
    def _save_state(self):
        """Save state to file"""
        if not self._state_file:
            return
        try:
        
            state = {
                "trading_mode": self._trading_mode.name,
                "system_health": self._system_health.name,
                "last_check": self._last_check.isoformat(),
                "failed_checks": [c.value for c in self._failed_checks],
                "warnings": self._warnings,
                "mode_changes": self._mode_changes[-10:],
                "trade_blocked_count": self._trade_blocked_count
            }
            
            self._state_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self._state_file, 'w') as f:
                json.dump(state, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to save state: {e}")
    
    def _load_state(self):
        """Load state from file"""
        if not self._state_file or not self._state_file.exists():
            return
        try:
        
            with open(self._state_file, 'r') as f:
                state = json.load(f)
            
            # Only restore mode if it was NO_TRADE (safety)
            if state.get("trading_mode") == "NO_TRADE":
                self._trading_mode = TradingMode.NO_TRADE
                logger.warning("Restored NO_TRADE mode from saved state")
            
            self._trade_blocked_count = state.get("trade_blocked_count", 0)
            
        except Exception as e:
            logger.error(f"Failed to load state: {e}")
    
    def on_mode_change(self, callback: Callable):
        """Set callback for mode changes"""
        self._on_mode_change = callback
    
    def on_health_change(self, callback: Callable):
        """Set callback for health changes"""
        self._on_health_change = callback
    
    def on_trade_blocked(self, callback: Callable):
        """Set callback for blocked trades"""
        self._on_trade_blocked = callback


# Convenience functions
def create_fail_safe(mode: str = "paper", **kwargs) -> FailSafe:
    """Create a fail-safe instance with string mode"""
    mode_map = {
        "no_trade": TradingMode.NO_TRADE,
        "simulation": TradingMode.SIMULATION,
        "paper": TradingMode.PAPER,
        "live": TradingMode.LIVE
    }
    return FailSafe(initial_mode=mode_map.get(mode.lower(), TradingMode.PAPER), **kwargs)


# Global instance
_global_fail_safe: Optional[FailSafe] = None


def get_fail_safe() -> FailSafe:
    """Get global fail-safe instance"""
    global _global_fail_safe
    if _global_fail_safe is None:
        _global_fail_safe = FailSafe()
    return _global_fail_safe


def can_trade() -> bool:
    """Quick check if trading is allowed"""
    return get_fail_safe().can_trade
