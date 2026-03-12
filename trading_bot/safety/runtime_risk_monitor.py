"""
Runtime Risk Monitor - Comprehensive Real-Time Risk Monitoring
Integrates all safety systems for continuous protection
"""

import asyncio
import logging
import psutil
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from pathlib import Path
import json

try:
    from trading_bot.safety.emergency_kill_switch import EmergencyKillSwitch, EmergencyTrigger
    from trading_bot.risk.circuit_breaker import CircuitBreaker, CircuitBreakerConfig, CircuitState
except ImportError:
    EmergencyKillSwitch = None
    CircuitBreaker = None

logger = logging.getLogger(__name__)


@dataclass
class RiskMetrics:
    """Current risk metrics snapshot"""
    timestamp: datetime = field(default_factory=datetime.now)
    
    # Trading metrics
    current_equity: float = 0.0
    peak_equity: float = 0.0
    current_drawdown: float = 0.0
    daily_pnl: float = 0.0
    weekly_pnl: float = 0.0
    monthly_pnl: float = 0.0
    
    # Position metrics
    open_positions: int = 0
    total_exposure: float = 0.0
    largest_position_pct: float = 0.0
    
    # Performance metrics
    win_rate: float = 0.0
    profit_factor: float = 0.0
    consecutive_losses: int = 0
    
    # System health
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    disk_usage: float = 0.0
    broker_connected: bool = False
    
    # Risk status
    circuit_breaker_state: str = "CLOSED"
    emergency_triggered: bool = False
    trading_enabled: bool = True
    
    # AI status
    ai_active: bool = False
    ai_mode: str = "engineer"
    pending_approvals: int = 0
    active_ai_sessions: int = 0


@dataclass
class TradeFrequencyLimits:
    """Trade frequency limits configuration"""
    max_trades_per_minute: int = 5
    max_trades_per_hour: int = 50
    max_trades_per_day: int = 200
    min_seconds_between_trades: int = 60
    post_loss_cooldown_minutes: int = 5
    post_emergency_cooldown_minutes: int = 60


class TradeFrequencyLimiter:
    """Prevents runaway trading with frequency limits"""
    
    def __init__(self, limits: Optional[TradeFrequencyLimits] = None):
        self.limits = limits or TradeFrequencyLimits()
        self.trade_timestamps: List[datetime] = []
        self.last_trade_time: Optional[datetime] = None
        self.last_loss_time: Optional[datetime] = None
        self.last_emergency_time: Optional[datetime] = None
        
    def can_trade(self) -> tuple[bool, Optional[str]]:
        """Check if trading is allowed based on frequency limits"""
        now = datetime.now()
        
        # Remove old timestamps (older than 1 day)
        self.trade_timestamps = [
            ts for ts in self.trade_timestamps 
            if now - ts < timedelta(days=1)
        ]
        
        # Check minimum time between trades
        if self.last_trade_time:
            seconds_since_last = (now - self.last_trade_time).total_seconds()
            if seconds_since_last < self.limits.min_seconds_between_trades:
                return False, f"Min time between trades: {seconds_since_last:.0f}s < {self.limits.min_seconds_between_trades}s"
        
        # Check post-loss cooldown
        if self.last_loss_time:
            minutes_since_loss = (now - self.last_loss_time).total_seconds() / 60
            if minutes_since_loss < self.limits.post_loss_cooldown_minutes:
                return False, f"Post-loss cooldown: {minutes_since_loss:.1f}min < {self.limits.post_loss_cooldown_minutes}min"
        
        # Check post-emergency cooldown
        if self.last_emergency_time:
            minutes_since_emergency = (now - self.last_emergency_time).total_seconds() / 60
            if minutes_since_emergency < self.limits.post_emergency_cooldown_minutes:
                return False, f"Post-emergency cooldown: {minutes_since_emergency:.1f}min < {self.limits.post_emergency_cooldown_minutes}min"
        
        # Check per-minute limit
        minute_ago = now - timedelta(minutes=1)
        trades_last_minute = sum(1 for ts in self.trade_timestamps if ts > minute_ago)
        if trades_last_minute >= self.limits.max_trades_per_minute:
            logger.critical(f"🚨 RUNAWAY TRADING DETECTED: {trades_last_minute} trades in last minute!")
            return False, f"RUNAWAY TRADING: {trades_last_minute} trades/min exceeds limit {self.limits.max_trades_per_minute}"
        
        # Check per-hour limit
        hour_ago = now - timedelta(hours=1)
        trades_last_hour = sum(1 for ts in self.trade_timestamps if ts > hour_ago)
        if trades_last_hour >= self.limits.max_trades_per_hour:
            return False, f"Hourly limit: {trades_last_hour} trades exceeds {self.limits.max_trades_per_hour}"
        
        # Check daily limit
        trades_today = len(self.trade_timestamps)
        if trades_today >= self.limits.max_trades_per_day:
            return False, f"Daily limit: {trades_today} trades exceeds {self.limits.max_trades_per_day}"
        
        return True, None
    
    def record_trade(self, is_win: bool):
        """Record a trade"""
        now = datetime.now()
        self.trade_timestamps.append(now)
        self.last_trade_time = now
        
        if not is_win:
            self.last_loss_time = now
    
    def record_emergency(self):
        """Record emergency shutdown"""
        self.last_emergency_time = datetime.now()


class RuntimeRiskMonitor:
    """
    Comprehensive Runtime Risk Monitor
    
    Integrates:
    - Emergency Kill Switch
    - Circuit Breaker
    - Trade Frequency Limiter
    - System Health Monitor
    - Real-time risk metrics
    """
    
    def __init__(
        self,
        kill_switch: Optional[EmergencyKillSwitch] = None,
        circuit_breaker: Optional[CircuitBreaker] = None,
        frequency_limiter: Optional[TradeFrequencyLimiter] = None
    ):
        # Initialize safety systems
        self.kill_switch = kill_switch or (EmergencyKillSwitch() if EmergencyKillSwitch else None)
        self.circuit_breaker = circuit_breaker or (CircuitBreaker() if CircuitBreaker else None)
        self.frequency_limiter = frequency_limiter or TradeFrequencyLimiter()
        
        # State
        self.monitoring_active = False
        self.trading_enabled = True
        self.current_metrics = RiskMetrics()
        
        # Monitoring intervals
        self.monitor_interval = 1.0  # Check every 1 second
        self.metrics_update_interval = 5.0  # Update metrics every 5 seconds
        
        # Alert thresholds
        self.cpu_alert_threshold = 90.0
        self.memory_alert_threshold = 90.0
        self.disk_alert_threshold = 95.0
        
        # Logs
        self.log_dir = Path("logs/risk_monitor")
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info("Runtime Risk Monitor initialized")
    
    async def start_monitoring(self):
        """Start risk monitoring loop"""
        self.monitoring_active = True
        logger.info("🛡️ Runtime Risk Monitor STARTED")
        
        # Start monitoring tasks
        tasks = [
            asyncio.create_task(self._monitor_loop()),
            asyncio.create_task(self._metrics_update_loop()),
            asyncio.create_task(self._system_health_loop())
        ]
        
        await asyncio.gather(*tasks)
    
    def stop_monitoring(self):
        """Stop risk monitoring"""
        self.monitoring_active = False
        logger.info("Runtime Risk Monitor STOPPED")
    
    async def _monitor_loop(self):
        """Main monitoring loop - checks safety systems"""
        while self.monitoring_active:
            try:
                # Check kill switch
                if self.kill_switch:
                    triggers = self.kill_switch.check_triggers(
                        current_equity=self.current_metrics.current_equity,
                        last_trade_pnl=None  # Would get from trade history
                    )
                    
                    triggered = [t for t in triggers if t.triggered]
                    if triggered:
                        await self._handle_emergency_triggers(triggered)
                
                # Check circuit breaker
                if self.circuit_breaker:
                    can_trade, reason = self.circuit_breaker.can_trade()
                    if not can_trade:
                        logger.warning(f"Circuit breaker prevents trading: {reason}")
                        self.trading_enabled = False
                
                await asyncio.sleep(self.monitor_interval)
                
            except Exception as e:
                logger.error(f"Error in monitor loop: {e}")
                await asyncio.sleep(self.monitor_interval)
    
    async def _metrics_update_loop(self):
        """Update risk metrics periodically"""
        while self.monitoring_active:
            try:
                self.current_metrics = await self._collect_metrics()
                await self._save_metrics()
                await asyncio.sleep(self.metrics_update_interval)
            except Exception as e:
                logger.error(f"Error updating metrics: {e}")
                await asyncio.sleep(self.metrics_update_interval)
    
    async def _system_health_loop(self):
        """Monitor system health (CPU, memory, disk)"""
        while self.monitoring_active:
            try:
                cpu = psutil.cpu_percent(interval=1)
                memory = psutil.virtual_memory().percent
                disk = psutil.disk_usage('/').percent
                
                # Check thresholds
                if cpu > self.cpu_alert_threshold:
                    logger.critical(f"🚨 HIGH CPU USAGE: {cpu:.1f}%")
                
                if memory > self.memory_alert_threshold:
                    logger.critical(f"🚨 HIGH MEMORY USAGE: {memory:.1f}%")
                
                if disk > self.disk_alert_threshold:
                    logger.critical(f"🚨 HIGH DISK USAGE: {disk:.1f}%")
                
                await asyncio.sleep(10)  # Check every 10 seconds
                
            except Exception as e:
                logger.error(f"Error in system health loop: {e}")
                await asyncio.sleep(10)
    
    async def _collect_metrics(self) -> RiskMetrics:
        """Collect current risk metrics"""
        metrics = RiskMetrics()
        
        # System health
        metrics.cpu_usage = psutil.cpu_percent()
        metrics.memory_usage = psutil.virtual_memory().percent
        metrics.disk_usage = psutil.disk_usage('/').percent
        
        # Circuit breaker state
        if self.circuit_breaker:
            status = self.circuit_breaker.get_status()
            if isinstance(status, dict):
                metrics.circuit_breaker_state = status.get('state', 'UNKNOWN')
                metrics.current_equity = status.get('balance', 0.0)
                metrics.daily_pnl = status.get('daily_pnl', 0.0)
                metrics.weekly_pnl = status.get('weekly_pnl', 0.0)
                metrics.monthly_pnl = status.get('monthly_pnl', 0.0)
                metrics.current_drawdown = status.get('drawdown', 0.0)
                metrics.consecutive_losses = status.get('consecutive_losses', 0)
                metrics.win_rate = status.get('win_rate', 0.0)
        
        # Kill switch state
        if self.kill_switch:
            metrics.emergency_triggered = self.kill_switch.is_triggered()
        
        metrics.trading_enabled = self.trading_enabled
        
        return metrics
    
    async def _save_metrics(self):
        """Save metrics to file"""
        try:
            metrics_file = self.log_dir / f"metrics_{datetime.now().strftime('%Y%m%d')}.jsonl"
            
            with open(metrics_file, 'a') as f:
                metrics_dict = {
                    'timestamp': self.current_metrics.timestamp.isoformat(),
                    'current_equity': self.current_metrics.current_equity,
                    'current_drawdown': self.current_metrics.current_drawdown,
                    'daily_pnl': self.current_metrics.daily_pnl,
                    'circuit_breaker_state': self.current_metrics.circuit_breaker_state,
                    'emergency_triggered': self.current_metrics.emergency_triggered,
                    'trading_enabled': self.current_metrics.trading_enabled,
                    'cpu_usage': self.current_metrics.cpu_usage,
                    'memory_usage': self.current_metrics.memory_usage
                }
                f.write(json.dumps(metrics_dict) + '\n')
        except Exception as e:
            logger.error(f"Failed to save metrics: {e}")
    
    async def _handle_emergency_triggers(self, triggers: List[EmergencyTrigger]):
        """Handle emergency triggers"""
        logger.critical("=" * 80)
        logger.critical("🚨 EMERGENCY TRIGGERS DETECTED 🚨")
        logger.critical("=" * 80)
        
        for trigger in triggers:
            logger.critical(f"⚠️  {trigger.name}: {trigger.message}")
        
        # Execute emergency shutdown
        if self.kill_switch:
            self.kill_switch.execute_emergency_stop(triggers)
        
        # Stop trading
        self.trading_enabled = False
        
        # Record emergency
        self.frequency_limiter.record_emergency()
        
        logger.critical("=" * 80)
    
    def can_trade(self) -> tuple[bool, Optional[str]]:
        """
        Check if trading is allowed
        
        Returns:
            (allowed, reason) tuple
        """
        # Check if monitoring is active
        if not self.monitoring_active:
            return False, "Risk monitoring not active"
        
        # Check emergency state
        if self.kill_switch and self.kill_switch.is_triggered():
            return False, "Emergency kill switch triggered"
        
        # Check circuit breaker
        if self.circuit_breaker:
            can_trade, reason = self.circuit_breaker.can_trade()
            if not can_trade:
                return False, f"Circuit breaker: {reason}"
        
        # Check frequency limits
        can_trade, reason = self.frequency_limiter.can_trade()
        if not can_trade:
            return False, f"Frequency limit: {reason}"
        
        # Check trading enabled flag
        if not self.trading_enabled:
            return False, "Trading manually disabled"
        
        return True, None
    
    def record_trade(self, pnl: float, is_win: bool):
        """Record a trade result"""
        # Update frequency limiter
        self.frequency_limiter.record_trade(is_win)
        
        # Update circuit breaker
        if self.circuit_breaker:
            self.circuit_breaker.record_trade(pnl, is_win)
    
    def get_status(self) -> Dict[str, Any]:
        """Get current risk monitor status"""
        return {
            'monitoring_active': self.monitoring_active,
            'trading_enabled': self.trading_enabled,
            'metrics': {
                'current_equity': self.current_metrics.current_equity,
                'current_drawdown': self.current_metrics.current_drawdown,
                'daily_pnl': self.current_metrics.daily_pnl,
                'weekly_pnl': self.current_metrics.weekly_pnl,
                'monthly_pnl': self.current_metrics.monthly_pnl,
                'consecutive_losses': self.current_metrics.consecutive_losses,
                'win_rate': self.current_metrics.win_rate,
                'circuit_breaker_state': self.current_metrics.circuit_breaker_state,
                'emergency_triggered': self.current_metrics.emergency_triggered,
                'cpu_usage': self.current_metrics.cpu_usage,
                'memory_usage': self.current_metrics.memory_usage,
                'disk_usage': self.current_metrics.disk_usage
            },
            'frequency_limits': {
                'trades_last_minute': len([
                    ts for ts in self.frequency_limiter.trade_timestamps 
                    if datetime.now() - ts < timedelta(minutes=1)
                ]),
                'trades_last_hour': len([
                    ts for ts in self.frequency_limiter.trade_timestamps 
                    if datetime.now() - ts < timedelta(hours=1)
                ]),
                'trades_today': len(self.frequency_limiter.trade_timestamps)
            }
        }
    
    async def emergency_shutdown(self, reason: str):
        """Execute emergency shutdown"""
        logger.critical(f"🚨 EMERGENCY SHUTDOWN INITIATED: {reason}")
        
        # Stop trading
        self.trading_enabled = False
        
        # Trigger kill switch
        if self.kill_switch:
            triggers = [EmergencyTrigger(
                name="Manual Emergency",
                threshold=1.0,
                current_value=1.0,
                triggered=True,
                message=reason
            )]
            self.kill_switch.execute_emergency_stop(triggers)
        
        # Record emergency
        self.frequency_limiter.record_emergency()
        
        logger.critical("✅ Emergency shutdown complete")


# Export
__all__ = [
    'RuntimeRiskMonitor',
    'RiskMetrics',
    'TradeFrequencyLimiter',
    'TradeFrequencyLimits'
]
