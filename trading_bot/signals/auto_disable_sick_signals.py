"""
Signal Health Monitor
=====================

Automatically monitors and disables underperforming signals.
"""

from collections import defaultdict
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from collections import deque
import numpy as np
import logging

logger = logging.getLogger(__name__)


class SignalHealth(Enum):
    """Signal health status"""
    HEALTHY = "healthy"
    WARNING = "warning"
    SICK = "sick"
    DISABLED = "disabled"
    QUARANTINE = "quarantine"
    RECOVERING = "recovering"


@dataclass
class SignalMetrics:
    """Performance metrics for a signal"""
    signal_id: str
    wins: int = 0
    losses: int = 0
    total_pnl: float = 0
    avg_win: float = 0
    avg_loss: float = 0
    max_drawdown: float = 0
    consecutive_losses: int = 0
    max_consecutive_losses: int = 0
    last_trade_time: Optional[datetime] = None
    disabled: bool = False
    disabled_at: Optional[datetime] = None
    disabled_reason: str = ""
    health: SignalHealth = SignalHealth.HEALTHY
    
    @property
    def total_trades(self) -> int:
        return self.wins + self.losses
    
    @property
    def win_rate(self) -> float:
        return self.wins / self.total_trades if self.total_trades > 0 else 0
    
    @property
    def profit_factor(self) -> float:
        if self.avg_loss == 0:
            return 0
        gross_profit = self.wins * self.avg_win
        gross_loss = self.losses * abs(self.avg_loss)
        return gross_profit / gross_loss if gross_loss > 0 else 0
    
    @property
    def expectancy(self) -> float:
        return (self.win_rate * self.avg_win) - ((1 - self.win_rate) * abs(self.avg_loss))


@dataclass
class HealthAlert:
    """Alert for signal health issues"""
    signal_id: str
    alert_type: str
    severity: str
    message: str
    metrics: Dict[str, float]
    timestamp: datetime = field(default_factory=datetime.now)


class SignalHealthMonitor:
    """
    Signal Health Monitor
    
    Monitors signal performance and automatically disables underperforming signals.
    
    Features:
    - Win rate monitoring
    - Consecutive loss tracking
    - Drawdown monitoring
    - Automatic quarantine and recovery
    - Performance alerts
    - Gradual re-enablement
    """
    
    def __init__(
        self,
        min_trades: int = 10,
        min_win_rate: float = 0.4,
        max_consecutive_losses: int = 5,
        max_drawdown: float = 0.2,
        quarantine_hours: int = 24,
        recovery_trades: int = 5
    ):
        """
        Initialize signal health monitor.
        
        Args:
            min_trades: Minimum trades before evaluation
            min_win_rate: Minimum acceptable win rate
            max_consecutive_losses: Max consecutive losses before disable
            max_drawdown: Max drawdown before disable
            quarantine_hours: Hours in quarantine before recovery attempt
            recovery_trades: Trades needed to recover from quarantine
        """
        self.min_trades = min_trades
        self.min_win_rate = min_win_rate
        self.max_consecutive_losses = max_consecutive_losses
        self.max_drawdown = max_drawdown
        self.quarantine_hours = quarantine_hours
        self.recovery_trades = recovery_trades
        
        # Signal tracking
        self.signal_metrics: Dict[str, SignalMetrics] = {}
        self.trade_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        self.alerts: deque = deque(maxlen=100)
        
        # Callbacks
        self._alert_callbacks: List[Callable] = []
        
        logger.info("SignalHealthMonitor initialized")
        
    def _get_or_create_metrics(self, signal_id: str) -> SignalMetrics:
        """Get or create metrics for a signal"""
        if signal_id not in self.signal_metrics:
            self.signal_metrics[signal_id] = SignalMetrics(signal_id=signal_id)
        return self.signal_metrics[signal_id]
        
    def record_outcome(
        self,
        signal_id: str,
        won: bool,
        pnl: float = 0,
        metadata: Optional[Dict] = None
    ):
        """
        Record signal outcome and update health status.
        
        Args:
            signal_id: Signal identifier
            won: Whether the trade won
            pnl: Profit/loss amount
            metadata: Additional trade metadata
        """
        metrics = self._get_or_create_metrics(signal_id)
        
        # Update basic stats
        if won:
            metrics.wins += 1
            metrics.consecutive_losses = 0
            if pnl > 0:
                # Update average win
                metrics.avg_win = (
                    (metrics.avg_win * (metrics.wins - 1) + pnl) / metrics.wins
                )
        else:
            metrics.losses += 1
            metrics.consecutive_losses += 1
            metrics.max_consecutive_losses = max(
                metrics.max_consecutive_losses,
                metrics.consecutive_losses
            )
            if pnl < 0:
                # Update average loss
                metrics.avg_loss = (
                    (metrics.avg_loss * (metrics.losses - 1) + abs(pnl)) / metrics.losses
                )
                
        metrics.total_pnl += pnl
        metrics.last_trade_time = datetime.now()
        
        # Record trade
        self.trade_history[signal_id].append({
            'won': won,
            'pnl': pnl,
            'timestamp': datetime.now(),
            'metadata': metadata or {}
        })
        
        # Update drawdown
        self._update_drawdown(signal_id)
        
        # Evaluate health
        self._evaluate_health(signal_id)
        
    def _update_drawdown(self, signal_id: str):
        """Update drawdown for signal"""
        trades = list(self.trade_history[signal_id])
        if not trades:
            return
            
        # Calculate equity curve
        equity = [0]
        for trade in trades:
            equity.append(equity[-1] + trade['pnl'])
            
        equity = np.array(equity)
        peak = np.maximum.accumulate(equity)
        drawdown = (peak - equity) / np.maximum(peak, 1)
        
        metrics = self.signal_metrics[signal_id]
        metrics.max_drawdown = float(np.max(drawdown))
        
    def _evaluate_health(self, signal_id: str):
        """Evaluate signal health and take action"""
        metrics = self.signal_metrics[signal_id]
        
        # Skip if already disabled
        if metrics.disabled and metrics.health != SignalHealth.QUARANTINE:
            return
            
        # Check for recovery from quarantine
        if metrics.health == SignalHealth.QUARANTINE:
            self._check_recovery(signal_id)
            return
            
        # Need minimum trades for evaluation
        if metrics.total_trades < self.min_trades:
            return
            
        reasons = []
        
        # Check win rate
        if metrics.win_rate < self.min_win_rate:
            reasons.append(f"Win rate {metrics.win_rate:.1%} below {self.min_win_rate:.1%}")
            
        # Check consecutive losses
        if metrics.consecutive_losses >= self.max_consecutive_losses:
            reasons.append(f"Consecutive losses: {metrics.consecutive_losses}")
            
        # Check drawdown
        if metrics.max_drawdown > self.max_drawdown:
            reasons.append(f"Drawdown {metrics.max_drawdown:.1%} exceeds {self.max_drawdown:.1%}")
            
        # Determine health status
        if len(reasons) >= 2:
            self._disable_signal(signal_id, "Multiple health issues: " + "; ".join(reasons))
        elif len(reasons) == 1:
            if metrics.health != SignalHealth.WARNING:
                metrics.health = SignalHealth.WARNING
                self._create_alert(signal_id, "warning", reasons[0])
        else:
            # Check for recovery from warning
            if metrics.health == SignalHealth.WARNING:
                metrics.health = SignalHealth.RECOVERING
            elif metrics.health == SignalHealth.RECOVERING:
                metrics.health = SignalHealth.HEALTHY
                
    def _disable_signal(self, signal_id: str, reason: str):
        """Disable a signal"""
        metrics = self.signal_metrics[signal_id]
        metrics.disabled = True
        metrics.disabled_at = datetime.now()
        metrics.disabled_reason = reason
        metrics.health = SignalHealth.QUARANTINE
        
        self._create_alert(signal_id, "disabled", reason)
        logger.warning(f"Signal {signal_id} disabled: {reason}")
        
    def _check_recovery(self, signal_id: str):
        """Check if signal can recover from quarantine"""
        metrics = self.signal_metrics[signal_id]
        
        if not metrics.disabled_at:
            return
            
        # Check quarantine period
        quarantine_end = metrics.disabled_at + timedelta(hours=self.quarantine_hours)
        if datetime.now() < quarantine_end:
            return
            
        # Check recent performance
        recent_trades = [
            t for t in self.trade_history[signal_id]
            if t['timestamp'] > metrics.disabled_at
        ]
        
        if len(recent_trades) >= self.recovery_trades:
            recent_wins = sum(1 for t in recent_trades if t['won'])
            recent_win_rate = recent_wins / len(recent_trades)
            
            if recent_win_rate >= self.min_win_rate:
                self._enable_signal(signal_id)
                
    def _enable_signal(self, signal_id: str):
        """Re-enable a signal"""
        metrics = self.signal_metrics[signal_id]
        metrics.disabled = False
        metrics.health = SignalHealth.RECOVERING
        metrics.consecutive_losses = 0
        
        self._create_alert(signal_id, "recovered", "Signal recovered from quarantine")
        logger.info(f"Signal {signal_id} recovered and re-enabled")
        
    def _create_alert(self, signal_id: str, alert_type: str, message: str):
        """Create health alert"""
        metrics = self.signal_metrics[signal_id]
        
        alert = HealthAlert(
            signal_id=signal_id,
            alert_type=alert_type,
            severity="high" if alert_type == "disabled" else "medium",
            message=message,
            metrics={
                'win_rate': metrics.win_rate,
                'total_trades': metrics.total_trades,
                'consecutive_losses': metrics.consecutive_losses,
                'max_drawdown': metrics.max_drawdown,
                'profit_factor': metrics.profit_factor
            }
        )
        
        self.alerts.append(alert)
        
        # Notify callbacks
        for callback in self._alert_callbacks:
            try:
                callback(alert)
            except Exception as e:
                logger.error(f"Alert callback error: {e}")
                
    def is_signal_healthy(self, signal_id: str) -> bool:
        """Check if signal is healthy and enabled"""
        if signal_id not in self.signal_metrics:
            return True  # New signals are healthy by default
        return not self.signal_metrics[signal_id].disabled
        
    def get_signal_health(self, signal_id: str) -> SignalHealth:
        """Get signal health status"""
        if signal_id not in self.signal_metrics:
            return SignalHealth.HEALTHY
        return self.signal_metrics[signal_id].health
        
    def get_signal_metrics(self, signal_id: str) -> Optional[SignalMetrics]:
        """Get metrics for a signal"""
        return self.signal_metrics.get(signal_id)
        
    def get_all_metrics(self) -> Dict[str, SignalMetrics]:
        """Get all signal metrics"""
        return self.signal_metrics.copy()
        
    def get_disabled_signals(self) -> List[str]:
        """Get list of disabled signals"""
        return [
            signal_id for signal_id, metrics in self.signal_metrics.items()
            if metrics.disabled
        ]
        
    def get_healthy_signals(self) -> List[str]:
        """Get list of healthy signals"""
        return [
            signal_id for signal_id, metrics in self.signal_metrics.items()
            if not metrics.disabled and metrics.health in [SignalHealth.HEALTHY, SignalHealth.RECOVERING]
        ]
        
    def force_enable(self, signal_id: str):
        """Force enable a signal (admin override)"""
        if signal_id in self.signal_metrics:
            self._enable_signal(signal_id)
            logger.info(f"Signal {signal_id} force-enabled by admin")
            
    def force_disable(self, signal_id: str, reason: str = "Admin disabled"):
        """Force disable a signal (admin override)"""
        self._disable_signal(signal_id, reason)
        
    def add_alert_callback(self, callback: Callable):
        """Add callback for health alerts"""
        self._alert_callbacks.append(callback)
        
    def get_recent_alerts(self, limit: int = 10) -> List[HealthAlert]:
        """Get recent alerts"""
        return list(self.alerts)[-limit:]
        
    def get_status(self) -> Dict[str, Any]:
        """Get monitor status"""
        total = len(self.signal_metrics)
        disabled = len(self.get_disabled_signals())
        healthy = len(self.get_healthy_signals())
        
        return {
            'total_signals': total,
            'healthy_signals': healthy,
            'disabled_signals': disabled,
            'warning_signals': total - healthy - disabled,
            'recent_alerts': len(self.alerts),
            'config': {
                'min_trades': self.min_trades,
                'min_win_rate': self.min_win_rate,
                'max_consecutive_losses': self.max_consecutive_losses,
                'max_drawdown': self.max_drawdown
            }
        }


def create_health_monitor(
    min_trades: int = 10,
    min_win_rate: float = 0.4
) -> SignalHealthMonitor:
    """Factory function"""
    return SignalHealthMonitor(min_trades=min_trades, min_win_rate=min_win_rate)


if __name__ == "__main__":
    # Demo
    monitor = create_health_monitor(min_trades=5, min_win_rate=0.4)
    
    print("=== Signal Health Monitor Demo ===\n")
    
    # Simulate trades for a healthy signal
    for i in range(10):
        monitor.record_outcome("signal_A", won=i % 2 == 0, pnl=100 if i % 2 == 0 else -50)
        
    # Simulate trades for a sick signal
    for i in range(10):
        monitor.record_outcome("signal_B", won=i > 7, pnl=100 if i > 7 else -80)
        
    print("Signal A:")
    metrics_a = monitor.get_signal_metrics("signal_A")
    print(f"  Health: {metrics_a.health.value}")
    print(f"  Win Rate: {metrics_a.win_rate:.1%}")
    print(f"  Enabled: {not metrics_a.disabled}")
    
    print("\nSignal B:")
    metrics_b = monitor.get_signal_metrics("signal_B")
    print(f"  Health: {metrics_b.health.value}")
    print(f"  Win Rate: {metrics_b.win_rate:.1%}")
    print(f"  Enabled: {not metrics_b.disabled}")
    if metrics_b.disabled:
        print(f"  Reason: {metrics_b.disabled_reason}")
        
    print(f"\nStatus: {monitor.get_status()}")
