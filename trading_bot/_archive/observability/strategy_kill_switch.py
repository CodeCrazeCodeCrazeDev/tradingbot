"""
Strategy Kill Switch Registry
==============================

Centralized registry for strategy enable/disable control.
Provides immediate ability to kill underperforming or dangerous strategies.

Features:
- Centralized kill switch management
- Automatic kill based on performance thresholds
- Manual override capability
- Kill reason tracking and audit
- Gradual re-enablement with probation
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from typing import Dict, List, Optional, Any, Callable, Set, Tuple
from collections import deque
import threading
import logging
import hashlib

logger = logging.getLogger(__name__)


class KillReason(Enum):
    """Reasons for killing a strategy."""
    MANUAL = auto()               # Manual kill by operator
    DRAWDOWN_LIMIT = auto()       # Exceeded drawdown threshold
    LOSS_LIMIT = auto()           # Exceeded loss limit
    WIN_RATE_DECAY = auto()       # Win rate dropped below threshold
    CORRELATION_BREAKDOWN = auto()  # Correlation assumptions violated
    REGIME_MISMATCH = auto()      # Strategy not suited for current regime
    EXECUTION_ISSUES = auto()     # Execution quality problems
    DATA_QUALITY = auto()         # Data quality issues
    RISK_LIMIT = auto()           # Risk limits exceeded
    CIRCUIT_BREAKER = auto()      # Circuit breaker triggered
    SCHEDULED = auto()            # Scheduled maintenance
    EMERGENCY = auto()            # Emergency shutdown
    PERFORMANCE_DECAY = auto()    # General performance decay
    SYSTEM_ERROR = auto()         # System error detected


class StrategyStatus(Enum):
    """Strategy operational status."""
    ACTIVE = auto()           # Fully operational
    KILLED = auto()           # Killed - no trading
    PROBATION = auto()        # Re-enabled with restrictions
    PAUSED = auto()           # Temporarily paused
    WARMING_UP = auto()       # Warming up after restart
    DEGRADED = auto()         # Operating with reduced capacity


@dataclass
class KillSwitch:
    """Kill switch state for a strategy."""
    strategy_id: str
    status: StrategyStatus
    kill_reason: Optional[KillReason] = None
    killed_at: Optional[datetime] = None
    killed_by: str = "system"
    kill_message: str = ""
    
    # Re-enablement
    can_reenable: bool = True
    reenable_after: Optional[datetime] = None
    probation_until: Optional[datetime] = None
    probation_restrictions: Dict[str, Any] = field(default_factory=dict)
    
    # Metrics at kill time
    metrics_at_kill: Dict[str, float] = field(default_factory=dict)
    
    # History
    kill_count: int = 0
    last_active: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "strategy_id": self.strategy_id,
            "status": self.status.name,
            "kill_reason": self.kill_reason.name if self.kill_reason else None,
            "killed_at": self.killed_at.isoformat() if self.killed_at else None,
            "killed_by": self.killed_by,
            "kill_message": self.kill_message,
            "can_reenable": self.can_reenable,
            "reenable_after": self.reenable_after.isoformat() if self.reenable_after else None,
            "probation_until": self.probation_until.isoformat() if self.probation_until else None,
            "kill_count": self.kill_count,
        }


@dataclass
class StrategyHealth:
    """Health metrics for a strategy."""
    strategy_id: str
    is_healthy: bool
    health_score: float  # 0-100
    win_rate: float
    profit_factor: float
    sharpe_ratio: float
    max_drawdown: float
    current_drawdown: float
    daily_pnl: float
    weekly_pnl: float
    trade_count: int
    last_trade: Optional[datetime] = None
    warnings: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "strategy_id": self.strategy_id,
            "is_healthy": self.is_healthy,
            "health_score": self.health_score,
            "win_rate": self.win_rate,
            "profit_factor": self.profit_factor,
            "sharpe_ratio": self.sharpe_ratio,
            "max_drawdown": self.max_drawdown,
            "current_drawdown": self.current_drawdown,
            "daily_pnl": self.daily_pnl,
            "weekly_pnl": self.weekly_pnl,
            "trade_count": self.trade_count,
            "warnings": self.warnings,
        }


@dataclass
class KillSwitchConfig:
    """Configuration for kill switch registry."""
    # Auto-kill thresholds
    max_drawdown_pct: float = 0.10          # 10% max drawdown
    max_daily_loss_pct: float = 0.03        # 3% max daily loss
    min_win_rate: float = 0.35              # 35% minimum win rate
    min_profit_factor: float = 0.8          # Minimum profit factor
    min_sharpe_ratio: float = -1.0          # Minimum Sharpe ratio
    
    # Probation settings
    probation_duration_hours: int = 24
    probation_position_limit_pct: float = 0.5  # 50% of normal
    probation_trade_limit_pct: float = 0.5     # 50% of normal
    
    # Re-enablement
    min_cooldown_minutes: int = 30
    max_kills_before_permanent: int = 5
    
    # Monitoring
    health_check_interval_seconds: int = 60
    min_trades_for_evaluation: int = 10


class AutoKillMonitor:
    """Monitors strategies for auto-kill conditions."""
    
    def __init__(self, config: KillSwitchConfig):
        self.config = config
    
    def check_health(self, health: StrategyHealth) -> Optional[KillReason]:
        """Check if strategy should be auto-killed."""
        # Check drawdown
        if health.current_drawdown > self.config.max_drawdown_pct:
            return KillReason.DRAWDOWN_LIMIT
        
        # Check daily loss
        if health.daily_pnl < -self.config.max_daily_loss_pct:
            return KillReason.LOSS_LIMIT
        
        # Only check performance metrics if enough trades
        if health.trade_count >= self.config.min_trades_for_evaluation:
            # Check win rate
            if health.win_rate < self.config.min_win_rate:
                return KillReason.WIN_RATE_DECAY
            
            # Check profit factor
            if health.profit_factor < self.config.min_profit_factor:
                return KillReason.PERFORMANCE_DECAY
            
            # Check Sharpe ratio
            if health.sharpe_ratio < self.config.min_sharpe_ratio:
                return KillReason.PERFORMANCE_DECAY
        
        return None
    
    def get_warnings(self, health: StrategyHealth) -> List[str]:
        """Get warnings for a strategy approaching kill thresholds."""
        warnings = []
        
        # Drawdown warning at 70% of limit
        if health.current_drawdown > self.config.max_drawdown_pct * 0.7:
            warnings.append(f"Drawdown at {health.current_drawdown:.1%} (limit: {self.config.max_drawdown_pct:.1%})")
        
        # Daily loss warning at 70% of limit
        if health.daily_pnl < -self.config.max_daily_loss_pct * 0.7:
            warnings.append(f"Daily loss at {health.daily_pnl:.1%} (limit: {-self.config.max_daily_loss_pct:.1%})")
        
        # Win rate warning
        if health.trade_count >= self.config.min_trades_for_evaluation:
            if health.win_rate < self.config.min_win_rate * 1.2:
                warnings.append(f"Win rate at {health.win_rate:.1%} (min: {self.config.min_win_rate:.1%})")
        
        return warnings


class StrategyKillSwitchRegistry:
    """
    Centralized registry for strategy kill switches.
    
    Provides immediate ability to kill, pause, or restrict strategies.
    """
    
    def __init__(self, config: Optional[KillSwitchConfig] = None):
        self.config = config or KillSwitchConfig()
        
        # Kill switches
        self._switches: Dict[str, KillSwitch] = {}
        self._health: Dict[str, StrategyHealth] = {}
        
        # Auto-kill monitor
        self._auto_monitor = AutoKillMonitor(self.config)
        
        # Event handlers
        self._kill_handlers: List[Callable[[str, KillReason], None]] = []
        self._reenable_handlers: List[Callable[[str], None]] = []
        
        # History
        self._kill_history: deque = deque(maxlen=10000)
        
        # Thread safety
        self._lock = threading.Lock()
        
        # Global kill switch
        self._global_kill = False
        self._global_kill_reason: Optional[str] = None
        
        logger.info("StrategyKillSwitchRegistry initialized")
    
    def register_strategy(self, strategy_id: str) -> None:
        """Register a strategy with the kill switch registry."""
        with self._lock:
            if strategy_id not in self._switches:
                self._switches[strategy_id] = KillSwitch(
                    strategy_id=strategy_id,
                    status=StrategyStatus.ACTIVE,
                    last_active=datetime.utcnow(),
                )
                logger.info(f"Strategy registered: {strategy_id}")
    
    def unregister_strategy(self, strategy_id: str) -> bool:
        """Unregister a strategy."""
        with self._lock:
            if strategy_id in self._switches:
                del self._switches[strategy_id]
                if strategy_id in self._health:
                    del self._health[strategy_id]
                return True
        return False
    
    def kill(
        self,
        strategy_id: str,
        reason: KillReason,
        message: str = "",
        killed_by: str = "system",
        can_reenable: bool = True,
        cooldown_minutes: Optional[int] = None,
    ) -> bool:
        """
        Kill a strategy immediately.
        
        Args:
            strategy_id: Strategy to kill
            reason: Reason for killing
            message: Additional message
            killed_by: Who/what triggered the kill
            can_reenable: Whether strategy can be re-enabled
            cooldown_minutes: Minimum time before re-enablement
        
        Returns:
            True if killed successfully
        """
        with self._lock:
            if strategy_id not in self._switches:
                self.register_strategy(strategy_id)
            
            switch = self._switches[strategy_id]
            
            # Check if already killed
            if switch.status == StrategyStatus.KILLED:
                return False
            
            # Record last active time
            switch.last_active = datetime.utcnow()
            
            # Kill the strategy
            switch.status = StrategyStatus.KILLED
            switch.kill_reason = reason
            switch.killed_at = datetime.utcnow()
            switch.killed_by = killed_by
            switch.kill_message = message
            switch.can_reenable = can_reenable
            switch.kill_count += 1
            
            # Set cooldown
            cooldown = cooldown_minutes or self.config.min_cooldown_minutes
            switch.reenable_after = datetime.utcnow() + timedelta(minutes=cooldown)
            
            # Store metrics at kill time
            if strategy_id in self._health:
                switch.metrics_at_kill = {
                    "health_score": self._health[strategy_id].health_score,
                    "win_rate": self._health[strategy_id].win_rate,
                    "drawdown": self._health[strategy_id].current_drawdown,
                    "daily_pnl": self._health[strategy_id].daily_pnl,
                }
            
            # Check for permanent kill
            if switch.kill_count >= self.config.max_kills_before_permanent:
                switch.can_reenable = False
                logger.warning(f"Strategy {strategy_id} permanently killed after {switch.kill_count} kills")
            
            # Record history
            self._kill_history.append({
                "strategy_id": strategy_id,
                "reason": reason.name,
                "message": message,
                "killed_by": killed_by,
                "timestamp": datetime.utcnow().isoformat(),
                "kill_count": switch.kill_count,
            })
        
        # Trigger handlers
        for handler in self._kill_handlers:
            try:
                handler(strategy_id, reason)
            except Exception as e:
                logger.error(f"Kill handler error: {e}")
        
        logger.warning(f"Strategy KILLED: {strategy_id} - {reason.name}: {message}")
        return True
    
    def reenable(
        self,
        strategy_id: str,
        reenabled_by: str = "system",
        with_probation: bool = True,
    ) -> Tuple[bool, str]:
        """
        Re-enable a killed strategy.
        
        Args:
            strategy_id: Strategy to re-enable
            reenabled_by: Who/what is re-enabling
            with_probation: Whether to apply probation restrictions
        
        Returns:
            Tuple of (success, message)
        """
        with self._lock:
            if strategy_id not in self._switches:
                return False, "Strategy not found"
            
            switch = self._switches[strategy_id]
            
            # Check if can be re-enabled
            if not switch.can_reenable:
                return False, "Strategy cannot be re-enabled (permanent kill)"
            
            if switch.status == StrategyStatus.ACTIVE:
                return False, "Strategy is already active"
            
            # Check cooldown
            if switch.reenable_after and datetime.utcnow() < switch.reenable_after:
                remaining = (switch.reenable_after - datetime.utcnow()).total_seconds() / 60
                return False, f"Cooldown active: {remaining:.1f} minutes remaining"
            
            # Re-enable with or without probation
            if with_probation:
                switch.status = StrategyStatus.PROBATION
                switch.probation_until = datetime.utcnow() + timedelta(hours=self.config.probation_duration_hours)
                switch.probation_restrictions = {
                    "position_limit_pct": self.config.probation_position_limit_pct,
                    "trade_limit_pct": self.config.probation_trade_limit_pct,
                }
                message = f"Re-enabled with probation until {switch.probation_until.isoformat()}"
            else:
                switch.status = StrategyStatus.ACTIVE
                switch.probation_until = None
                switch.probation_restrictions = {}
                message = "Re-enabled without probation"
            
            switch.kill_reason = None
            switch.killed_at = None
            switch.killed_by = ""
            switch.kill_message = ""
        
        # Trigger handlers
        for handler in self._reenable_handlers:
            try:
                handler(strategy_id)
            except Exception as e:
                logger.error(f"Reenable handler error: {e}")
        
        logger.info(f"Strategy RE-ENABLED: {strategy_id} by {reenabled_by} - {message}")
        return True, message
    
    def pause(self, strategy_id: str, duration_minutes: int = 60, reason: str = "") -> bool:
        """Temporarily pause a strategy."""
        with self._lock:
            if strategy_id not in self._switches:
                return False
            
            switch = self._switches[strategy_id]
            switch.status = StrategyStatus.PAUSED
            switch.reenable_after = datetime.utcnow() + timedelta(minutes=duration_minutes)
            switch.kill_message = reason or f"Paused for {duration_minutes} minutes"
        
        logger.info(f"Strategy PAUSED: {strategy_id} for {duration_minutes} minutes")
        return True
    
    def resume(self, strategy_id: str) -> bool:
        """Resume a paused strategy."""
        with self._lock:
            if strategy_id not in self._switches:
                return False
            
            switch = self._switches[strategy_id]
            if switch.status != StrategyStatus.PAUSED:
                return False
            
            switch.status = StrategyStatus.ACTIVE
            switch.reenable_after = None
            switch.kill_message = ""
        
        logger.info(f"Strategy RESUMED: {strategy_id}")
        return True
    
    def global_kill(self, reason: str, killed_by: str = "system") -> int:
        """Kill all strategies globally."""
        self._global_kill = True
        self._global_kill_reason = reason
        
        killed_count = 0
        with self._lock:
            for strategy_id in self._switches:
                if self._switches[strategy_id].status == StrategyStatus.ACTIVE:
                    self.kill(strategy_id, KillReason.EMERGENCY, reason, killed_by)
                    killed_count += 1
        
        logger.critical(f"GLOBAL KILL: {killed_count} strategies killed - {reason}")
        return killed_count
    
    def global_reenable(self, reenabled_by: str = "system") -> int:
        """Re-enable all strategies globally."""
        self._global_kill = False
        self._global_kill_reason = None
        
        reenabled_count = 0
        with self._lock:
            for strategy_id in self._switches:
                if self._switches[strategy_id].status == StrategyStatus.KILLED:
                    success, _ = self.reenable(strategy_id, reenabled_by)
                    if success:
                        reenabled_count += 1
        
        logger.info(f"GLOBAL REENABLE: {reenabled_count} strategies re-enabled")
        return reenabled_count
    
    def update_health(self, strategy_id: str, health: StrategyHealth) -> Optional[KillReason]:
        """
        Update strategy health and check for auto-kill.
        
        Returns KillReason if auto-killed, None otherwise.
        """
        with self._lock:
            self._health[strategy_id] = health
            
            # Check if strategy should be auto-killed
            if strategy_id in self._switches:
                switch = self._switches[strategy_id]
                if switch.status == StrategyStatus.ACTIVE:
                    kill_reason = self._auto_monitor.check_health(health)
                    if kill_reason:
                        # Auto-kill
                        self.kill(
                            strategy_id,
                            kill_reason,
                            f"Auto-killed: {kill_reason.name}",
                            "auto_monitor",
                        )
                        return kill_reason
                    
                    # Update warnings
                    health.warnings = self._auto_monitor.get_warnings(health)
            
            # Check probation expiry
            if strategy_id in self._switches:
                switch = self._switches[strategy_id]
                if switch.status == StrategyStatus.PROBATION:
                    if switch.probation_until and datetime.utcnow() > switch.probation_until:
                        switch.status = StrategyStatus.ACTIVE
                        switch.probation_until = None
                        switch.probation_restrictions = {}
                        logger.info(f"Strategy {strategy_id} probation ended")
        
        return None
    
    def is_allowed(self, strategy_id: str) -> Tuple[bool, str]:
        """
        Check if a strategy is allowed to trade.
        
        Returns:
            Tuple of (allowed, reason)
        """
        # Check global kill
        if self._global_kill:
            return False, f"Global kill active: {self._global_kill_reason}"
        
        with self._lock:
            if strategy_id not in self._switches:
                return True, "Strategy not registered (allowed by default)"
            
            switch = self._switches[strategy_id]
            
            if switch.status == StrategyStatus.KILLED:
                return False, f"Strategy killed: {switch.kill_reason.name if switch.kill_reason else 'Unknown'}"
            
            if switch.status == StrategyStatus.PAUSED:
                return False, f"Strategy paused: {switch.kill_message}"
            
            if switch.status == StrategyStatus.PROBATION:
                return True, "Strategy on probation (restricted)"
            
            if switch.status == StrategyStatus.WARMING_UP:
                return False, "Strategy warming up"
            
            return True, "Strategy active"
    
    def get_restrictions(self, strategy_id: str) -> Dict[str, Any]:
        """Get any restrictions for a strategy."""
        with self._lock:
            if strategy_id not in self._switches:
                return {}
            
            switch = self._switches[strategy_id]
            if switch.status == StrategyStatus.PROBATION:
                return switch.probation_restrictions
            
            return {}
    
    def get_status(self, strategy_id: str) -> Optional[KillSwitch]:
        """Get kill switch status for a strategy."""
        with self._lock:
            return self._switches.get(strategy_id)
    
    def get_health(self, strategy_id: str) -> Optional[StrategyHealth]:
        """Get health metrics for a strategy."""
        with self._lock:
            return self._health.get(strategy_id)
    
    def get_all_statuses(self) -> List[KillSwitch]:
        """Get status of all strategies."""
        with self._lock:
            return list(self._switches.values())
    
    def get_killed_strategies(self) -> List[KillSwitch]:
        """Get all killed strategies."""
        with self._lock:
            return [s for s in self._switches.values() if s.status == StrategyStatus.KILLED]
    
    def get_active_strategies(self) -> List[str]:
        """Get list of active strategy IDs."""
        with self._lock:
            return [
                s.strategy_id for s in self._switches.values()
                if s.status in (StrategyStatus.ACTIVE, StrategyStatus.PROBATION)
            ]
    
    def register_kill_handler(self, handler: Callable[[str, KillReason], None]) -> None:
        """Register a handler to be called when a strategy is killed."""
        self._kill_handlers.append(handler)
    
    def register_reenable_handler(self, handler: Callable[[str], None]) -> None:
        """Register a handler to be called when a strategy is re-enabled."""
        self._reenable_handlers.append(handler)
    
    def get_kill_history(self, strategy_id: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Get kill history."""
        history = list(self._kill_history)
        if strategy_id:
            history = [h for h in history if h["strategy_id"] == strategy_id]
        return history[-limit:]
    
    def get_summary(self) -> Dict[str, Any]:
        """Get registry summary."""
        with self._lock:
            statuses = list(self._switches.values())
            
            return {
                "total_strategies": len(statuses),
                "active": len([s for s in statuses if s.status == StrategyStatus.ACTIVE]),
                "killed": len([s for s in statuses if s.status == StrategyStatus.KILLED]),
                "paused": len([s for s in statuses if s.status == StrategyStatus.PAUSED]),
                "probation": len([s for s in statuses if s.status == StrategyStatus.PROBATION]),
                "global_kill_active": self._global_kill,
                "global_kill_reason": self._global_kill_reason,
                "kill_reasons": self._get_kill_reason_counts(),
                "recent_kills": self.get_kill_history(limit=5),
            }
    
    def _get_kill_reason_counts(self) -> Dict[str, int]:
        """Get counts of kills by reason."""
        counts: Dict[str, int] = {}
        for entry in self._kill_history:
            reason = entry["reason"]
            counts[reason] = counts.get(reason, 0) + 1
        return counts
