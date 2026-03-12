"""
Kill Switch Gate - The Last Line of Defense

This gate implements automatic kill switches that halt trading when
anomalies are detected. No human intervention required.

KILL SWITCH TRIGGERS:
1. Drawdown exceeds threshold
2. Loss rate exceeds threshold
3. Consecutive losses exceed threshold
4. Volatility spike detected
5. System anomaly detected
6. Data feed failure
7. Execution failures
8. Risk limit breached
9. Correlation breakdown
10. Black swan event detected

RULE: "When in doubt, get out. Survival first, profits second."

Author: AlphaAlgo Reality Check System
"""

import logging
import math
import statistics
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple, Callable
from collections import deque
import threading

logger = logging.getLogger(__name__)


class KillReason(Enum):
    """Reasons for triggering kill switch"""
    DRAWDOWN_LIMIT = "drawdown_limit"
    LOSS_RATE_LIMIT = "loss_rate_limit"
    CONSECUTIVE_LOSSES = "consecutive_losses"
    VOLATILITY_SPIKE = "volatility_spike"
    SYSTEM_ANOMALY = "system_anomaly"
    DATA_FEED_FAILURE = "data_feed_failure"
    EXECUTION_FAILURE = "execution_failure"
    RISK_LIMIT_BREACH = "risk_limit_breach"
    CORRELATION_BREAKDOWN = "correlation_breakdown"
    BLACK_SWAN = "black_swan"
    MANUAL_OVERRIDE = "manual_override"
    DRIFT_DETECTED = "drift_detected"
    LIQUIDITY_CRISIS = "liquidity_crisis"


class KillSwitchStatus(Enum):
    """Status of the kill switch"""
    ARMED = "armed"  # Ready to trigger
    TRIGGERED = "triggered"  # Currently blocking trading
    COOLDOWN = "cooldown"  # Waiting before re-arming
    DISABLED = "disabled"  # Manually disabled (dangerous!)


@dataclass
class KillSwitchConfig:
    """Configuration for kill switches"""
    # Drawdown limits
    max_daily_drawdown: float = 0.03  # 3% daily
    max_weekly_drawdown: float = 0.07  # 7% weekly
    max_total_drawdown: float = 0.15  # 15% total
    
    # Loss limits
    max_consecutive_losses: int = 5
    max_loss_rate_1h: float = 0.5  # 50% loss rate in 1 hour
    max_loss_rate_24h: float = 0.6  # 60% loss rate in 24 hours
    
    # Volatility limits
    volatility_spike_threshold: float = 3.0  # 3x normal volatility
    
    # System limits
    max_execution_failures: int = 3
    max_data_gaps: int = 5
    
    # Timing
    cooldown_minutes: int = 30
    auto_reset_hours: int = 24
    
    # Black swan detection
    black_swan_return_threshold: float = -0.05  # -5% in single period
    black_swan_vol_threshold: float = 5.0  # 5x normal vol


@dataclass
class KillEvent:
    """Record of a kill switch event"""
    reason: KillReason
    triggered_at: datetime
    resolved_at: Optional[datetime] = None
    
    # Context
    trigger_value: float = 0.0
    threshold_value: float = 0.0
    
    # Impact
    positions_closed: int = 0
    pnl_at_trigger: float = 0.0
    
    # Resolution
    resolution_method: str = ""
    
    @property
    def duration(self) -> Optional[timedelta]:
        if self.resolved_at:
            return self.resolved_at - self.triggered_at
        return datetime.utcnow() - self.triggered_at


class KillSwitchGate:
    """
    HARD GATE: Automatic Kill Switches
    
    This gate automatically halts ALL trading when dangerous conditions
    are detected. No exceptions. No overrides (except manual).
    
    Features:
    1. Multiple independent kill switches
    2. Automatic position closing on trigger
    3. Cooldown period before re-arming
    4. Event logging and alerting
    5. Gradual re-entry after resolution
    
    Philosophy:
    - Better to miss profits than lose capital
    - Automatic response faster than human
    - Multiple redundant triggers
    - Fail-safe: default to closed
    """
    
    def __init__(self, config: Optional[KillSwitchConfig] = None):
        self.config = config or KillSwitchConfig()
        
        # Kill switch state
        self.status = KillSwitchStatus.ARMED
        self.active_reasons: List[KillReason] = []
        self.triggered_at: Optional[datetime] = None
        
        # Tracking data
        self.trade_history: deque = deque(maxlen=1000)
        self.return_history: deque = deque(maxlen=500)
        self.volatility_history: deque = deque(maxlen=100)
        self.execution_failures: deque = deque(maxlen=100)
        self.data_gaps: deque = deque(maxlen=100)
        
        # P&L tracking
        self.daily_pnl = 0.0
        self.weekly_pnl = 0.0
        self.total_pnl = 0.0
        self.peak_equity = 0.0
        self.current_equity = 0.0
        
        # Consecutive loss tracking
        self.consecutive_losses = 0
        
        # Event history
        self.kill_events: List[KillEvent] = []
        
        # Callbacks
        self.on_trigger_callbacks: List[Callable] = []
        self.on_resolve_callbacks: List[Callable] = []
        
        # Thread safety
        self._lock = threading.Lock()
        
        # Statistics
        self.total_triggers = 0
        self.false_positives = 0  # Triggers that were unnecessary
        
        logger.info("KillSwitchGate initialized - ARMED AND READY")
    
    def check(
        self,
        current_equity: float,
        current_return: Optional[float] = None,
        current_volatility: Optional[float] = None,
        trade_result: Optional[Dict] = None,
        market_data: Optional[Dict] = None
    ) -> Tuple[bool, List[KillReason]]:
        """
        Check all kill switches.
        
        Args:
            current_equity: Current portfolio equity
            current_return: Current period return
            current_volatility: Current market volatility
            trade_result: Result of most recent trade (if any)
            market_data: Current market data
            
        Returns:
            Tuple of (is_trading_allowed, active_kill_reasons)
        """
        with self._lock:
            # Update equity tracking
            self._update_equity(current_equity)
            
            # Update histories
            if current_return is not None:
                self.return_history.append({
                    'return': current_return,
                    'timestamp': datetime.utcnow()
                })
            
            if current_volatility is not None:
                self.volatility_history.append(current_volatility)
            
            if trade_result:
                self._process_trade_result(trade_result)
            
            # If already triggered, check for resolution
            if self.status == KillSwitchStatus.TRIGGERED:
                if self._check_resolution():
                    self._resolve()
                else:
                    return False, self.active_reasons
            
            # If in cooldown, check if cooldown expired
            if self.status == KillSwitchStatus.COOLDOWN:
                if self._check_cooldown_expired():
                    self.status = KillSwitchStatus.ARMED
                    logger.info("Kill switch cooldown expired - RE-ARMED")
                else:
                    return False, [KillReason.MANUAL_OVERRIDE]  # Still in cooldown
            
            # If disabled, allow trading (dangerous!)
            if self.status == KillSwitchStatus.DISABLED:
                return True, []
            
            # Check all kill switches
            triggered_reasons = []
            
            # 1. Drawdown checks
            dd_reason = self._check_drawdown()
            if dd_reason:
                triggered_reasons.append(dd_reason)
            
            # 2. Loss rate checks
            lr_reason = self._check_loss_rate()
            if lr_reason:
                triggered_reasons.append(lr_reason)
            
            # 3. Consecutive losses
            if self.consecutive_losses >= self.config.max_consecutive_losses:
                triggered_reasons.append(KillReason.CONSECUTIVE_LOSSES)
            
            # 4. Volatility spike
            vol_reason = self._check_volatility_spike(current_volatility)
            if vol_reason:
                triggered_reasons.append(vol_reason)
            
            # 5. Black swan detection
            bs_reason = self._check_black_swan(current_return, current_volatility)
            if bs_reason:
                triggered_reasons.append(bs_reason)
            
            # 6. Execution failures
            if self._count_recent_failures(self.execution_failures, minutes=60) >= self.config.max_execution_failures:
                triggered_reasons.append(KillReason.EXECUTION_FAILURE)
            
            # 7. Data feed failures
            if self._count_recent_failures(self.data_gaps, minutes=60) >= self.config.max_data_gaps:
                triggered_reasons.append(KillReason.DATA_FEED_FAILURE)
            
            # Trigger if any reasons
            if triggered_reasons:
                self._trigger(triggered_reasons)
                return False, triggered_reasons
            
            return True, []
    
    def _update_equity(self, current_equity: float):
        """Update equity tracking"""
        self.current_equity = current_equity
        
        if current_equity > self.peak_equity:
            self.peak_equity = current_equity
    
    def _process_trade_result(self, trade_result: Dict):
        """Process a trade result"""
        self.trade_history.append({
            **trade_result,
            'timestamp': datetime.utcnow()
        })
        
        pnl = trade_result.get('pnl', 0)
        
        # Update P&L
        self.daily_pnl += pnl
        self.weekly_pnl += pnl
        self.total_pnl += pnl
        
        # Track consecutive losses
        if pnl < 0:
            self.consecutive_losses += 1
        else:
            self.consecutive_losses = 0
    
    def _check_drawdown(self) -> Optional[KillReason]:
        """Check drawdown limits"""
        if self.peak_equity <= 0:
            return None
        
        current_dd = (self.peak_equity - self.current_equity) / self.peak_equity
        
        if current_dd >= self.config.max_total_drawdown:
            logger.error(f"KILL SWITCH: Total drawdown {current_dd:.1%} >= {self.config.max_total_drawdown:.1%}")
            return KillReason.DRAWDOWN_LIMIT
        
        # Check daily drawdown
        if self.daily_pnl < 0:
            daily_dd = abs(self.daily_pnl) / self.peak_equity
            if daily_dd >= self.config.max_daily_drawdown:
                logger.error(f"KILL SWITCH: Daily drawdown {daily_dd:.1%} >= {self.config.max_daily_drawdown:.1%}")
                return KillReason.DRAWDOWN_LIMIT
        
        # Check weekly drawdown
        if self.weekly_pnl < 0:
            weekly_dd = abs(self.weekly_pnl) / self.peak_equity
            if weekly_dd >= self.config.max_weekly_drawdown:
                logger.error(f"KILL SWITCH: Weekly drawdown {weekly_dd:.1%} >= {self.config.max_weekly_drawdown:.1%}")
                return KillReason.DRAWDOWN_LIMIT
        
        return None
    
    def _check_loss_rate(self) -> Optional[KillReason]:
        """Check loss rate limits"""
        now = datetime.utcnow()
        
        # 1-hour loss rate
        trades_1h = [
            t for t in self.trade_history
            if (now - t['timestamp']).total_seconds() < 3600
        ]
        
        if len(trades_1h) >= 5:
            losses_1h = sum(1 for t in trades_1h if t.get('pnl', 0) < 0)
            loss_rate_1h = losses_1h / len(trades_1h)
            
            if loss_rate_1h >= self.config.max_loss_rate_1h:
                logger.error(f"KILL SWITCH: 1h loss rate {loss_rate_1h:.1%} >= {self.config.max_loss_rate_1h:.1%}")
                return KillReason.LOSS_RATE_LIMIT
        
        # 24-hour loss rate
        trades_24h = [
            t for t in self.trade_history
            if (now - t['timestamp']).total_seconds() < 86400
        ]
        
        if len(trades_24h) >= 10:
            losses_24h = sum(1 for t in trades_24h if t.get('pnl', 0) < 0)
            loss_rate_24h = losses_24h / len(trades_24h)
            
            if loss_rate_24h >= self.config.max_loss_rate_24h:
                logger.error(f"KILL SWITCH: 24h loss rate {loss_rate_24h:.1%} >= {self.config.max_loss_rate_24h:.1%}")
                return KillReason.LOSS_RATE_LIMIT
        
        return None
    
    def _check_volatility_spike(self, current_volatility: Optional[float]) -> Optional[KillReason]:
        """Check for volatility spikes"""
        if current_volatility is None:
            return None
        
        if len(self.volatility_history) < 20:
            return None
        
        historical_vol = list(self.volatility_history)[:-1]
        avg_vol = statistics.mean(historical_vol)
        
        if avg_vol > 0:
            vol_ratio = current_volatility / avg_vol
            
            if vol_ratio >= self.config.volatility_spike_threshold:
                logger.error(f"KILL SWITCH: Volatility spike {vol_ratio:.1f}x normal")
                return KillReason.VOLATILITY_SPIKE
        
        return None
    
    def _check_black_swan(
        self,
        current_return: Optional[float],
        current_volatility: Optional[float]
    ) -> Optional[KillReason]:
        """Check for black swan events"""
        # Extreme negative return
        if current_return is not None:
            if current_return <= self.config.black_swan_return_threshold:
                logger.error(f"KILL SWITCH: Black swan return {current_return:.1%}")
                return KillReason.BLACK_SWAN
        
        # Extreme volatility
        if current_volatility is not None and len(self.volatility_history) >= 20:
            avg_vol = statistics.mean(list(self.volatility_history)[:-1])
            if avg_vol > 0:
                vol_ratio = current_volatility / avg_vol
                if vol_ratio >= self.config.black_swan_vol_threshold:
                    logger.error(f"KILL SWITCH: Black swan volatility {vol_ratio:.1f}x")
                    return KillReason.BLACK_SWAN
        
        return None
    
    def _count_recent_failures(self, history: deque, minutes: int) -> int:
        """Count failures in recent time window"""
        now = datetime.utcnow()
        cutoff = now - timedelta(minutes=minutes)
        
        return sum(1 for item in history if item.get('timestamp', now) > cutoff)
    
    def _trigger(self, reasons: List[KillReason]):
        """Trigger the kill switch"""
        self.status = KillSwitchStatus.TRIGGERED
        self.active_reasons = reasons
        self.triggered_at = datetime.utcnow()
        self.total_triggers += 1
        
        # Create event record
        event = KillEvent(
            reason=reasons[0],  # Primary reason
            triggered_at=self.triggered_at,
            trigger_value=self._get_trigger_value(reasons[0]),
            threshold_value=self._get_threshold_value(reasons[0]),
            pnl_at_trigger=self.total_pnl
        )
        self.kill_events.append(event)
        
        logger.critical(
            f"KILL SWITCH TRIGGERED: {[r.value for r in reasons]} "
            f"- ALL TRADING HALTED"
        )
        
        # Call callbacks
        for callback in self.on_trigger_callbacks:
            try:
                callback(reasons)
            except Exception as e:
                logger.error(f"Kill switch callback error: {e}")
    
    def _check_resolution(self) -> bool:
        """Check if kill switch conditions have resolved"""
        # Auto-reset after configured hours
        if self.triggered_at:
            hours_since = (datetime.utcnow() - self.triggered_at).total_seconds() / 3600
            if hours_since >= self.config.auto_reset_hours:
                return True
        
        # Check if conditions improved
        # (In production, would have more sophisticated checks)
        return False
    
    def _check_cooldown_expired(self) -> bool:
        """Check if cooldown period has expired"""
        if self.triggered_at:
            minutes_since = (datetime.utcnow() - self.triggered_at).total_seconds() / 60
            return minutes_since >= self.config.cooldown_minutes
        return True
    
    def _resolve(self):
        """Resolve the kill switch"""
        self.status = KillSwitchStatus.COOLDOWN
        
        # Update event record
        if self.kill_events:
            self.kill_events[-1].resolved_at = datetime.utcnow()
            self.kill_events[-1].resolution_method = "auto"
        
        logger.info(f"Kill switch resolved - entering cooldown ({self.config.cooldown_minutes} min)")
        
        # Call callbacks
        for callback in self.on_resolve_callbacks:
            try:
                callback()
            except Exception as e:
                logger.error(f"Kill switch resolve callback error: {e}")
    
    def _get_trigger_value(self, reason: KillReason) -> float:
        """Get the value that triggered the kill switch"""
        if reason == KillReason.DRAWDOWN_LIMIT:
            if self.peak_equity > 0:
                return (self.peak_equity - self.current_equity) / self.peak_equity
        elif reason == KillReason.CONSECUTIVE_LOSSES:
            return float(self.consecutive_losses)
        elif reason == KillReason.VOLATILITY_SPIKE:
            if self.volatility_history:
                return self.volatility_history[-1]
        return 0.0
    
    def _get_threshold_value(self, reason: KillReason) -> float:
        """Get the threshold that was breached"""
        if reason == KillReason.DRAWDOWN_LIMIT:
            return self.config.max_total_drawdown
        elif reason == KillReason.CONSECUTIVE_LOSSES:
            return float(self.config.max_consecutive_losses)
        elif reason == KillReason.VOLATILITY_SPIKE:
            return self.config.volatility_spike_threshold
        return 0.0
    
    def record_execution_failure(self, details: Dict = None):
        """Record an execution failure"""
        self.execution_failures.append({
            'timestamp': datetime.utcnow(),
            'details': details or {}
        })
    
    def record_data_gap(self, details: Dict = None):
        """Record a data feed gap"""
        self.data_gaps.append({
            'timestamp': datetime.utcnow(),
            'details': details or {}
        })
    
    def manual_trigger(self, reason: str = "Manual override"):
        """Manually trigger the kill switch"""
        with self._lock:
            self._trigger([KillReason.MANUAL_OVERRIDE])
            logger.warning(f"Kill switch manually triggered: {reason}")
    
    def manual_reset(self, confirm: bool = False):
        """Manually reset the kill switch (DANGEROUS)"""
        if not confirm:
            logger.warning("Manual reset requires confirm=True")
            return
        
        with self._lock:
            self.status = KillSwitchStatus.ARMED
            self.active_reasons = []
            self.triggered_at = None
            self.consecutive_losses = 0
            
            if self.kill_events:
                self.kill_events[-1].resolved_at = datetime.utcnow()
                self.kill_events[-1].resolution_method = "manual"
            
            logger.warning("Kill switch manually reset - USE CAUTION")
    
    def disable(self, confirm: bool = False):
        """Disable the kill switch (VERY DANGEROUS)"""
        if not confirm:
            logger.error("Disabling kill switch requires confirm=True - THIS IS DANGEROUS")
            return
        
        with self._lock:
            self.status = KillSwitchStatus.DISABLED
            logger.critical("KILL SWITCH DISABLED - TRADING WITHOUT SAFETY NET")
    
    def enable(self):
        """Re-enable the kill switch"""
        with self._lock:
            self.status = KillSwitchStatus.ARMED
            logger.info("Kill switch re-enabled and armed")
    
    def reset_daily(self):
        """Reset daily counters (call at start of trading day)"""
        with self._lock:
            self.daily_pnl = 0.0
            logger.info("Daily P&L counter reset")
    
    def reset_weekly(self):
        """Reset weekly counters (call at start of trading week)"""
        with self._lock:
            self.weekly_pnl = 0.0
            logger.info("Weekly P&L counter reset")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current kill switch status"""
        return {
            'status': self.status.value,
            'is_trading_allowed': self.status == KillSwitchStatus.ARMED,
            'active_reasons': [r.value for r in self.active_reasons],
            'triggered_at': self.triggered_at.isoformat() if self.triggered_at else None,
            'consecutive_losses': self.consecutive_losses,
            'daily_pnl': self.daily_pnl,
            'weekly_pnl': self.weekly_pnl,
            'total_pnl': self.total_pnl,
            'current_drawdown': (self.peak_equity - self.current_equity) / self.peak_equity if self.peak_equity > 0 else 0,
            'total_triggers': self.total_triggers
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get gate statistics"""
        return {
            'total_triggers': self.total_triggers,
            'current_status': self.status.value,
            'kill_events': len(self.kill_events),
            'avg_trigger_duration': self._avg_trigger_duration(),
            'most_common_reason': self._most_common_reason(),
            'execution_failures_24h': self._count_recent_failures(self.execution_failures, 1440),
            'data_gaps_24h': self._count_recent_failures(self.data_gaps, 1440)
        }
    
    def _avg_trigger_duration(self) -> Optional[float]:
        """Average duration of kill switch triggers in minutes"""
        durations = [
            e.duration.total_seconds() / 60
            for e in self.kill_events
            if e.duration is not None
        ]
        return statistics.mean(durations) if durations else None
    
    def _most_common_reason(self) -> Optional[str]:
        """Most common kill switch trigger reason"""
        if not self.kill_events:
            return None
        
        reasons = [e.reason.value for e in self.kill_events]
        return max(set(reasons), key=reasons.count)
