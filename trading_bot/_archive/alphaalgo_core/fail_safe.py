"""
AlphaAlgo Fail-Safe System

NO TRADE MODE - Refuses to trade when conditions are unsafe:
- Data is missing
- Architecture unstable
- Risk broken
- Market abnormal
- Spread too wide
- Volatility extreme
- Connection unstable

"I refuse to trade until conditions are safe."
"""

import asyncio
import logging
import threading
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


class TradingMode(Enum):
    """Trading modes"""
    NO_TRADE = "no_trade"           # Refuse all trades
    SIMULATION = "simulation"        # Paper trading only
    PAPER = "paper"                  # Paper trading with real data
    LIVE_CAUTIOUS = "live_cautious"  # Live with reduced size
    LIVE = "live"                    # Full live trading


class SystemHealth(Enum):
    """System health levels"""
    CRITICAL = "critical"    # System failure - NO TRADE
    UNHEALTHY = "unhealthy"  # Major issues - NO TRADE
    DEGRADED = "degraded"    # Some issues - CAUTIOUS
    HEALTHY = "healthy"      # All good - NORMAL
    OPTIMAL = "optimal"      # Everything perfect


class SafetyCheck(Enum):
    """Safety checks that must pass"""
    DATA_AVAILABLE = "data_available"
    DATA_FRESH = "data_fresh"
    ARCHITECTURE_STABLE = "architecture_stable"
    RISK_ENGINE_OK = "risk_engine_ok"
    BROKER_CONNECTED = "broker_connected"
    SPREAD_ACCEPTABLE = "spread_acceptable"
    VOLATILITY_NORMAL = "volatility_normal"
    CONNECTION_STABLE = "connection_stable"
    MARKET_OPEN = "market_open"
    NO_HIGH_IMPACT_NEWS = "no_high_impact_news"
    POSITION_LIMITS_OK = "position_limits_ok"
    DRAWDOWN_ACCEPTABLE = "drawdown_acceptable"


@dataclass
class SafetyCheckResult:
    """Result of a safety check"""
    check: SafetyCheck
    passed: bool
    message: str
    value: Optional[Any] = None
    threshold: Optional[Any] = None
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class SystemStatus:
    """Current system status"""
    health: SystemHealth
    trading_mode: TradingMode
    checks: List[SafetyCheckResult]
    issues: List[str]
    timestamp: datetime = field(default_factory=datetime.now)
    
    @property
    def can_trade(self) -> bool:
        """
        can_trade function.

    Auto-documented by QwenCodeMender.
        """
        return self.trading_mode not in [TradingMode.NO_TRADE]
    
    @property
    def can_trade_live(self) -> bool:
        return self.trading_mode in [TradingMode.LIVE, TradingMode.LIVE_CAUTIOUS]


class FailSafeSystem:
    """
    Fail-Safe Trading System
    
    Continuously monitors system health and enforces NO TRADE mode
    when conditions are unsafe.
    
    "I refuse to trade until conditions are safe."
    """
    
    # Thresholds
    MAX_SPREAD_PIPS = 5.0
    MAX_VOLATILITY_MULTIPLIER = 3.0  # 3x normal volatility
    MAX_DRAWDOWN_PCT = 20.0
    DATA_STALENESS_SECONDS = 60
    
    def __init__(self):
        self._current_status: Optional[SystemStatus] = None
        self._check_results: Dict[SafetyCheck, SafetyCheckResult] = {}
        self._override_active = False
        self._override_expires: Optional[datetime] = None
        self._lock = threading.Lock()
        
        # Callbacks for checks
        self._check_callbacks: Dict[SafetyCheck, Callable] = {}
        
        # Initialize with NO_TRADE
        self._current_mode = TradingMode.NO_TRADE
        
        logger.info("[FailSafe] Initialized in NO_TRADE mode")
    
    def register_check(self, check: SafetyCheck, callback: Callable[[], SafetyCheckResult]):
        """Register a callback for a safety check"""
        self._check_callbacks[check] = callback
    
    async def run_all_checks(self) -> SystemStatus:
        """Run all safety checks and determine trading mode"""
        results = []
        issues = []
        
        # Run each registered check
        for check, callback in self._check_callbacks.items():
            try:
                result = callback()
                results.append(result)
                self._check_results[check] = result
                
                if not result.passed:
                    issues.append(f"{check.value}: {result.message}")
            except Exception as e:
                result = SafetyCheckResult(
                    check=check,
                    passed=False,
                    message=f"Check failed with error: {e}",
                )
                results.append(result)
                issues.append(f"{check.value}: Error - {e}")
        
        # Run default checks for unregistered
        for check in SafetyCheck:
            if check not in self._check_callbacks:
                result = self._default_check(check)
                results.append(result)
                if not result.passed:
                    issues.append(f"{check.value}: {result.message}")
        
        # Determine health and mode
        health = self._determine_health(results)
        mode = self._determine_mode(health, results)
        
        # Check for override
        if self._override_active:
            if self._override_expires and datetime.now() > self._override_expires:
                self._override_active = False
                logger.info("[FailSafe] Override expired")
            else:
                # Override allows trading but logs warning
                logger.warning("[FailSafe] Override active - trading allowed despite issues")
        
        status = SystemStatus(
            health=health,
            trading_mode=mode,
            checks=results,
            issues=issues,
        )
        
        with self._lock:
            self._current_status = status
        
        self._log_status(status)
        return status
    
    def _default_check(self, check: SafetyCheck) -> SafetyCheckResult:
        """Default check implementation"""
        # Default to failed for critical checks
        critical_checks = {
            SafetyCheck.DATA_AVAILABLE,
            SafetyCheck.RISK_ENGINE_OK,
            SafetyCheck.BROKER_CONNECTED,
        }
        
        if check in critical_checks:
            return SafetyCheckResult(
                check=check,
                passed=False,
                message="Check not configured",
            )
        
        # Default to passed for non-critical
        return SafetyCheckResult(
            check=check,
            passed=True,
            message="Default pass (not configured)",
        )
    
    def _determine_health(self, results: List[SafetyCheckResult]) -> SystemHealth:
        """Determine system health from check results"""
        failed = [r for r in results if not r.passed]
        
        if len(failed) == 0:
            return SystemHealth.OPTIMAL
        
        # Critical checks
        critical_checks = {
            SafetyCheck.DATA_AVAILABLE,
            SafetyCheck.RISK_ENGINE_OK,
            SafetyCheck.ARCHITECTURE_STABLE,
        }
        
        critical_failed = [r for r in failed if r.check in critical_checks]
        
        if len(critical_failed) > 0:
            return SystemHealth.CRITICAL
        
        if len(failed) >= 3:
            return SystemHealth.UNHEALTHY
        
        if len(failed) >= 1:
            return SystemHealth.DEGRADED
        
        return SystemHealth.HEALTHY
    
    def _determine_mode(
        self,
        health: SystemHealth,
        results: List[SafetyCheckResult]
    ) -> TradingMode:
        """Determine trading mode from health"""
        # Override check
        if self._override_active:
            return TradingMode.LIVE_CAUTIOUS
        
        if health == SystemHealth.CRITICAL:
            return TradingMode.NO_TRADE
        
        if health == SystemHealth.UNHEALTHY:
            return TradingMode.NO_TRADE
        
        if health == SystemHealth.DEGRADED:
            return TradingMode.LIVE_CAUTIOUS
        
        # Check broker connection for live
        broker_check = next(
            (r for r in results if r.check == SafetyCheck.BROKER_CONNECTED),
            None
        )
        
        if broker_check and broker_check.passed:
            return TradingMode.LIVE
        
        return TradingMode.PAPER
    
    def _log_status(self, status: SystemStatus):
        """Log status changes"""
        if status.health in [SystemHealth.CRITICAL, SystemHealth.UNHEALTHY]:
            logger.warning(
                f"[FailSafe] {status.health.value.upper()} - "
                f"Mode: {status.trading_mode.value} - "
                f"Issues: {len(status.issues)}"
            )
            for issue in status.issues:
                logger.warning(f"[FailSafe] Issue: {issue}")
        else:
            logger.info(
                f"[FailSafe] {status.health.value} - "
                f"Mode: {status.trading_mode.value}"
            )
    
    def can_trade(self) -> Tuple[bool, str]:
        """Check if trading is allowed"""
        with self._lock:
            if not self._current_status:
                return (False, "System not initialized - run checks first")
            
            if not self._current_status.can_trade:
                issues = "; ".join(self._current_status.issues[:3])
                return (False, f"NO TRADE MODE: {issues}")
            
            return (True, f"Trading allowed in {self._current_status.trading_mode.value} mode")
    
    def can_trade_live(self) -> Tuple[bool, str]:
        """Check if live trading is allowed"""
        with self._lock:
            if not self._current_status:
                return (False, "System not initialized")
            
            if not self._current_status.can_trade_live:
                return (False, f"Live trading not allowed - mode: {self._current_status.trading_mode.value}")
            
            return (True, "Live trading allowed")
    
    def get_status(self) -> Optional[SystemStatus]:
        """Get current system status"""
        with self._lock:
            return self._current_status
    
    def get_issues(self) -> List[str]:
        """Get current issues"""
        with self._lock:
            if self._current_status:
                return self._current_status.issues.copy()
            return ["System not initialized"]
    
    def request_override(
        self,
        reason: str,
        duration_minutes: int = 60,
        approved_by: str = "human"
    ) -> bool:
        """
        Request override of safety checks.
        
        This should only be used by humans in exceptional circumstances.
        """
        logger.warning(
            f"[FailSafe] Override requested by {approved_by}: {reason} "
            f"(duration: {duration_minutes} min)"
        )
        
        with self._lock:
            self._override_active = True
            self._override_expires = datetime.now() + timedelta(minutes=duration_minutes)
        
        return True
    
    def cancel_override(self):
        """Cancel active override"""
        with self._lock:
            self._override_active = False
            self._override_expires = None
        logger.info("[FailSafe] Override cancelled")
    
    def emergency_stop(self, reason: str):
        """Emergency stop - force NO_TRADE mode"""
        logger.critical(f"[FailSafe] EMERGENCY STOP: {reason}")
        
        with self._lock:
            self._override_active = False
            self._current_status = SystemStatus(
                health=SystemHealth.CRITICAL,
                trading_mode=TradingMode.NO_TRADE,
                checks=[],
                issues=[f"EMERGENCY STOP: {reason}"],
            )
    
    # Pre-built check implementations
    @staticmethod
    def check_spread(current_spread: float, max_spread: float = 5.0) -> SafetyCheckResult:
        """Check if spread is acceptable"""
        passed = current_spread <= max_spread
        return SafetyCheckResult(
            check=SafetyCheck.SPREAD_ACCEPTABLE,
            passed=passed,
            message=f"Spread {current_spread:.1f} pips" + 
                    ("" if passed else f" exceeds max {max_spread}"),
            value=current_spread,
            threshold=max_spread,
        )
    
    @staticmethod
    def check_volatility(
        current_vol: float,
        normal_vol: float,
        max_multiplier: float = 3.0
    ) -> SafetyCheckResult:
        """Check if volatility is acceptable"""
        multiplier = current_vol / normal_vol if normal_vol > 0 else 999
        passed = multiplier <= max_multiplier
        return SafetyCheckResult(
            check=SafetyCheck.VOLATILITY_NORMAL,
            passed=passed,
            message=f"Volatility {multiplier:.1f}x normal" +
                    ("" if passed else " - EXTREME"),
            value=multiplier,
            threshold=max_multiplier,
        )
    
    @staticmethod
    def check_drawdown(
        current_drawdown: float,
        max_drawdown: float = 20.0
    ) -> SafetyCheckResult:
        """Check if drawdown is acceptable"""
        passed = current_drawdown <= max_drawdown
        return SafetyCheckResult(
            check=SafetyCheck.DRAWDOWN_ACCEPTABLE,
            passed=passed,
            message=f"Drawdown {current_drawdown:.1f}%" +
                    ("" if passed else f" exceeds max {max_drawdown}%"),
            value=current_drawdown,
            threshold=max_drawdown,
        )
    
    @staticmethod
    def check_data_freshness(
        last_data_time: Optional[datetime],
        max_age_seconds: int = 60
    ) -> SafetyCheckResult:
        """Check if data is fresh"""
        if not last_data_time:
            return SafetyCheckResult(
                check=SafetyCheck.DATA_FRESH,
                passed=False,
                message="No data received",
            )
        
        age = (datetime.now() - last_data_time).total_seconds()
        passed = age <= max_age_seconds
        return SafetyCheckResult(
            check=SafetyCheck.DATA_FRESH,
            passed=passed,
            message=f"Data age {age:.0f}s" +
                    ("" if passed else f" - STALE (max {max_age_seconds}s)"),
            value=age,
            threshold=max_age_seconds,
        )


# Convenience function
def create_fail_safe() -> FailSafeSystem:
    """Create and return a FailSafeSystem"""
    return FailSafeSystem()
