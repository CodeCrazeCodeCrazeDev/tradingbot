"""
Monitoring and Analytics Module
================================

Real-time monitoring and performance analytics:
- Performance Dashboard
- Risk Monitor
- Alert System
- Trade Analytics
- System Health Monitoring
"""

import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple
from collections import deque
import logging
from datetime import datetime, timedelta
from abc import ABC, abstractmethod
import json
import asyncio
import numpy
import pandas

logger = logging.getLogger(__name__)


class AlertSeverity(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


class AlertType(Enum):
    """Types of alerts"""
    DAILY_LOSS = "daily_loss"
    POSITION_LOSS = "position_loss"
    EXECUTION_LATENCY = "execution_latency"
    API_FAILURE = "api_failure"
    VOLATILITY_SPIKE = "volatility_spike"
    MODEL_DEGRADATION = "model_degradation"
    RISK_LIMIT = "risk_limit"
    SYSTEM_HEALTH = "system_health"


@dataclass
class Alert:
    """Alert notification"""
    alert_id: str
    timestamp: datetime
    alert_type: AlertType
    severity: AlertSeverity
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    acknowledged: bool = False
    resolved: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'alert_id': self.alert_id,
            'timestamp': self.timestamp.isoformat(),
            'type': self.alert_type.value,
            'severity': self.severity.value,
            'message': self.message,
            'details': self.details,
            'acknowledged': self.acknowledged,
            'resolved': self.resolved,
        }


@dataclass
class PerformanceMetrics:
    """Trading performance metrics"""
    timestamp: datetime
    period: str  # 'daily', 'weekly', 'monthly', 'ytd'
    
    # P&L
    gross_pnl: float
    net_pnl: float
    transaction_costs: float
    slippage_costs: float
    
    # Returns
    total_return: float
    annualized_return: float
    
    # Risk metrics
    sharpe_ratio: float
    sortino_ratio: float
    max_drawdown: float
    current_drawdown: float
    var_95: float
    var_99: float
    
    # Trade statistics
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    avg_win: float
    avg_loss: float
    profit_factor: float
    expectancy: float
    
    # Execution quality
    avg_slippage_bps: float
    fill_rate: float


@dataclass
class SystemHealth:
    """System health status"""
    timestamp: datetime
    overall_status: str  # 'healthy', 'degraded', 'critical'
    
    # Component status
    data_feed_status: str
    execution_status: str
    risk_system_status: str
    model_status: str
    database_status: str
    
    # Performance metrics
    cpu_usage: float
    memory_usage: float
    latency_p50: float
    latency_p99: float
    error_rate: float
    
    # Uptime
    uptime_seconds: float
    last_restart: datetime


class PerformanceDashboard:
    """
    Real-time performance dashboard
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        # Trade history
        self.trades: deque = deque(maxlen=10000)
        
        # P&L history
        self.pnl_history: deque = deque(maxlen=10000)
        
        # Equity curve
        self.equity_curve: deque = deque(maxlen=10000)
        
        # Initial capital
        self.initial_capital = self.config.get('initial_capital', 100000)
        self.current_equity = self.initial_capital
        self.peak_equity = self.initial_capital
        
        # Daily tracking
        self.daily_pnl: Dict[str, float] = {}
        self.daily_trades: Dict[str, List[Dict]] = {}
    
    def record_trade(self, trade: Dict[str, Any]):
        """Record a completed trade"""
        self.trades.append(trade)
        
        # Update P&L
        pnl = trade.get('pnl', 0)
        self.pnl_history.append({
            'timestamp': trade.get('timestamp', datetime.now()),
            'pnl': pnl,
            'symbol': trade.get('symbol', ''),
        })
        
        # Update equity
        self.current_equity += pnl
        if self.current_equity > self.peak_equity:
            self.peak_equity = self.current_equity
        
        self.equity_curve.append({
            'timestamp': datetime.now(),
            'equity': self.current_equity,
        })
        
        # Daily tracking
        date_key = datetime.now().strftime('%Y-%m-%d')
        self.daily_pnl[date_key] = self.daily_pnl.get(date_key, 0) + pnl
        
        if date_key not in self.daily_trades:
            self.daily_trades[date_key] = []
        self.daily_trades[date_key].append(trade)
    
    def get_metrics(self, period: str = 'daily') -> PerformanceMetrics:
        """Get performance metrics for period"""
        # Filter trades by period
        now = datetime.now()
        if period == 'daily':
            cutoff = now - timedelta(days=1)
        elif period == 'weekly':
            cutoff = now - timedelta(weeks=1)
        elif period == 'monthly':
            cutoff = now - timedelta(days=30)
        elif period == 'ytd':
            cutoff = datetime(now.year, 1, 1)
        else:
            cutoff = datetime.min
        
        trades = [t for t in self.trades if t.get('timestamp', now) > cutoff]
        
        if not trades:
            return self._empty_metrics(period)
        
        # Calculate metrics
        pnls = [t.get('pnl', 0) for t in trades]
        gross_pnl = sum(pnls)
        
        costs = sum(t.get('costs', 0) for t in trades)
        slippage = sum(t.get('slippage', 0) for t in trades)
        net_pnl = gross_pnl - costs - slippage
        
        # Returns
        total_return = net_pnl / self.initial_capital
        days = max((now - cutoff).days, 1)
        annualized_return = total_return * (365 / days)
        
        # Win/loss
        wins = [p for p in pnls if p > 0]
        losses = [p for p in pnls if p < 0]
        
        win_rate = len(wins) / len(pnls) if pnls else 0
        avg_win = np.mean(wins) if wins else 0
        avg_loss = np.mean(losses) if losses else 0
        
        profit_factor = sum(wins) / abs(sum(losses)) if losses else float('inf')
        expectancy = win_rate * avg_win + (1 - win_rate) * avg_loss
        
        # Risk metrics
        returns = np.array(pnls) / self.initial_capital
        sharpe = np.mean(returns) / (np.std(returns) + 1e-10) * np.sqrt(252) if len(returns) > 1 else 0
        
        downside_returns = returns[returns < 0]
        sortino = np.mean(returns) / (np.std(downside_returns) + 1e-10) * np.sqrt(252) if len(downside_returns) > 0 else 0
        
        # Drawdown
        equity_values = [e['equity'] for e in self.equity_curve]
        if equity_values:
            running_max = np.maximum.accumulate(equity_values)
            drawdowns = (running_max - equity_values) / running_max
            max_drawdown = np.max(drawdowns) if len(drawdowns) > 0 else 0
            current_drawdown = drawdowns[-1] if len(drawdowns) > 0 else 0
        else:
            max_drawdown = 0
            current_drawdown = 0
        
        # VaR
        var_95 = np.percentile(returns, 5) * self.current_equity if len(returns) > 20 else 0
        var_99 = np.percentile(returns, 1) * self.current_equity if len(returns) > 20 else 0
        
        # Execution quality
        slippages = [t.get('slippage_bps', 0) for t in trades]
        avg_slippage = np.mean(slippages) if slippages else 0
        
        fill_rates = [t.get('fill_rate', 1) for t in trades]
        avg_fill_rate = np.mean(fill_rates) if fill_rates else 1
        
        return PerformanceMetrics(
            timestamp=now,
            period=period,
            gross_pnl=gross_pnl,
            net_pnl=net_pnl,
            transaction_costs=costs,
            slippage_costs=slippage,
            total_return=total_return,
            annualized_return=annualized_return,
            sharpe_ratio=sharpe,
            sortino_ratio=sortino,
            max_drawdown=max_drawdown,
            current_drawdown=current_drawdown,
            var_95=var_95,
            var_99=var_99,
            total_trades=len(trades),
            winning_trades=len(wins),
            losing_trades=len(losses),
            win_rate=win_rate,
            avg_win=avg_win,
            avg_loss=avg_loss,
            profit_factor=profit_factor,
            expectancy=expectancy,
            avg_slippage_bps=avg_slippage,
            fill_rate=avg_fill_rate,
        )
    
    def _empty_metrics(self, period: str) -> PerformanceMetrics:
        """Return empty metrics"""
        return PerformanceMetrics(
            timestamp=datetime.now(),
            period=period,
            gross_pnl=0, net_pnl=0, transaction_costs=0, slippage_costs=0,
            total_return=0, annualized_return=0,
            sharpe_ratio=0, sortino_ratio=0, max_drawdown=0, current_drawdown=0,
            var_95=0, var_99=0,
            total_trades=0, winning_trades=0, losing_trades=0,
            win_rate=0, avg_win=0, avg_loss=0, profit_factor=0, expectancy=0,
            avg_slippage_bps=0, fill_rate=0,
        )
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get data for dashboard display"""
        daily = self.get_metrics('daily')
        weekly = self.get_metrics('weekly')
        monthly = self.get_metrics('monthly')
        
        return {
            'current_equity': self.current_equity,
            'peak_equity': self.peak_equity,
            'current_drawdown': (self.peak_equity - self.current_equity) / self.peak_equity,
            'daily': daily.__dict__,
            'weekly': weekly.__dict__,
            'monthly': monthly.__dict__,
            'equity_curve': list(self.equity_curve)[-100:],
            'recent_trades': list(self.trades)[-20:],
        }


class RiskMonitor:
    """
    Real-time risk monitoring
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        # Risk limits
        self.max_daily_loss = self.config.get('max_daily_loss', 0.03)
        self.max_position_loss = self.config.get('max_position_loss', 0.01)
        self.max_drawdown = self.config.get('max_drawdown', 0.15)
        self.max_var = self.config.get('max_var', 0.05)
        
        # Current state
        self.daily_pnl = 0
        self.current_equity = self.config.get('initial_capital', 100000)
        self.peak_equity = self.current_equity
        
        # Position tracking
        self.positions: Dict[str, Dict[str, Any]] = {}
        
        # Risk history
        self.risk_history: deque = deque(maxlen=1000)
        
        # Callbacks
        self.on_limit_breach: Optional[Callable[[str, float], None]] = None
    
    def update_position(self, symbol: str, position: Dict[str, Any]):
        """Update position for risk monitoring"""
        self.positions[symbol] = position
    
    def update_pnl(self, pnl: float):
        """Update daily P&L"""
        self.daily_pnl += pnl
        self.current_equity += pnl
        
        if self.current_equity > self.peak_equity:
            self.peak_equity = self.current_equity
    
    def check_limits(self) -> List[Dict[str, Any]]:
        """Check all risk limits"""
        breaches = []
        
        # Daily loss limit
        daily_loss_pct = -self.daily_pnl / self.current_equity if self.current_equity > 0 else 0
        if daily_loss_pct > self.max_daily_loss:
            breaches.append({
                'type': 'daily_loss',
                'limit': self.max_daily_loss,
                'current': daily_loss_pct,
                'severity': 'critical',
            })
        
        # Drawdown limit
        drawdown = (self.peak_equity - self.current_equity) / self.peak_equity if self.peak_equity > 0 else 0
        if drawdown > self.max_drawdown:
            breaches.append({
                'type': 'max_drawdown',
                'limit': self.max_drawdown,
                'current': drawdown,
                'severity': 'critical',
            })
        elif drawdown > self.max_drawdown * 0.8:
            breaches.append({
                'type': 'drawdown_warning',
                'limit': self.max_drawdown,
                'current': drawdown,
                'severity': 'warning',
            })
        
        # Position-level limits
        for symbol, position in self.positions.items():
            position_pnl = position.get('unrealized_pnl', 0)
            position_loss_pct = -position_pnl / self.current_equity if self.current_equity > 0 else 0
            
            if position_loss_pct > self.max_position_loss:
                breaches.append({
                    'type': 'position_loss',
                    'symbol': symbol,
                    'limit': self.max_position_loss,
                    'current': position_loss_pct,
                    'severity': 'warning',
                })
        
        # Record
        self.risk_history.append({
            'timestamp': datetime.now(),
            'daily_pnl': self.daily_pnl,
            'drawdown': drawdown,
            'breaches': breaches,
        })
        
        # Trigger callbacks
        if breaches and self.on_limit_breach:
            for breach in breaches:
                self.on_limit_breach(breach['type'], breach['current'])
        
        return breaches
    
    def get_risk_status(self) -> Dict[str, Any]:
        """Get current risk status"""
        drawdown = (self.peak_equity - self.current_equity) / self.peak_equity if self.peak_equity > 0 else 0
        daily_loss_pct = -self.daily_pnl / self.current_equity if self.current_equity > 0 else 0
        
        # Determine overall status
        if daily_loss_pct > self.max_daily_loss or drawdown > self.max_drawdown:
            status = 'critical'
        elif daily_loss_pct > self.max_daily_loss * 0.8 or drawdown > self.max_drawdown * 0.8:
            status = 'warning'
        else:
            status = 'normal'
        
        return {
            'status': status,
            'daily_pnl': self.daily_pnl,
            'daily_loss_pct': daily_loss_pct,
            'daily_loss_limit': self.max_daily_loss,
            'current_drawdown': drawdown,
            'max_drawdown_limit': self.max_drawdown,
            'current_equity': self.current_equity,
            'peak_equity': self.peak_equity,
            'position_count': len(self.positions),
        }
    
    def reset_daily(self):
        """Reset daily tracking"""
        self.daily_pnl = 0


class AlertSystem:
    """
    Alert management system
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        # Alert history
        self.alerts: deque = deque(maxlen=1000)
        self.active_alerts: Dict[str, Alert] = {}
        
        # Alert thresholds
        self.thresholds = {
            AlertType.DAILY_LOSS: self.config.get('daily_loss_threshold', 0.03),
            AlertType.POSITION_LOSS: self.config.get('position_loss_threshold', 0.01),
            AlertType.EXECUTION_LATENCY: self.config.get('latency_threshold', 100),  # ms
            AlertType.VOLATILITY_SPIKE: self.config.get('volatility_threshold', 3),  # std devs
            AlertType.MODEL_DEGRADATION: self.config.get('model_degradation_threshold', 0.55),
        }
        
        # Notification callbacks
        self.notification_handlers: List[Callable[[Alert], None]] = []
        
        # Alert counter for IDs
        self._alert_counter = 0
    
    def create_alert(self, alert_type: AlertType, severity: AlertSeverity,
                    message: str, details: Dict[str, Any] = None) -> Alert:
        """Create and dispatch alert"""
        self._alert_counter += 1
        alert_id = f"ALERT_{self._alert_counter:06d}"
        
        alert = Alert(
            alert_id=alert_id,
            timestamp=datetime.now(),
            alert_type=alert_type,
            severity=severity,
            message=message,
            details=details or {},
        )
        
        self.alerts.append(alert)
        self.active_alerts[alert_id] = alert
        
        # Dispatch to handlers
        for handler in self.notification_handlers:
            try:
                handler(alert)
            except Exception as e:
                logger.error(f"Alert handler failed: {e}")
        
        logger.warning(f"Alert created: [{severity.value}] {message}")
        
        return alert
    
    def check_condition(self, alert_type: AlertType, value: float,
                       details: Dict[str, Any] = None) -> Optional[Alert]:
        """Check if condition triggers alert"""
        threshold = self.thresholds.get(alert_type)
        
        if threshold is None:
            return None
        
        if value > threshold:
            # Determine severity
            if value > threshold * 1.5:
                severity = AlertSeverity.CRITICAL
            elif value > threshold * 1.2:
                severity = AlertSeverity.WARNING
            else:
                severity = AlertSeverity.INFO
            
            message = f"{alert_type.value}: {value:.4f} exceeds threshold {threshold:.4f}"
            
            return self.create_alert(alert_type, severity, message, details)
        
        return None
    
    def acknowledge_alert(self, alert_id: str) -> bool:
        """Acknowledge an alert"""
        if alert_id in self.active_alerts:
            self.active_alerts[alert_id].acknowledged = True
            return True
        return False
    
    def resolve_alert(self, alert_id: str) -> bool:
        """Resolve an alert"""
        if alert_id in self.active_alerts:
            self.active_alerts[alert_id].resolved = True
            del self.active_alerts[alert_id]
            return True
        return False
    
    def get_active_alerts(self, severity: AlertSeverity = None) -> List[Alert]:
        """Get active alerts, optionally filtered by severity"""
        alerts = list(self.active_alerts.values())
        
        if severity:
            alerts = [a for a in alerts if a.severity == severity]
        
        return sorted(alerts, key=lambda a: a.timestamp, reverse=True)
    
    def add_notification_handler(self, handler: Callable[[Alert], None]):
        """Add notification handler"""
        self.notification_handlers.append(handler)


class TradeAnalytics:
    """
    Trade analytics and attribution
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        # Trade history
        self.trades: deque = deque(maxlen=10000)
        
        # Attribution tracking
        self.signal_attribution: Dict[str, List[float]] = {}
        self.strategy_attribution: Dict[str, List[float]] = {}
    
    def record_trade(self, trade: Dict[str, Any]):
        """Record trade for analytics"""
        self.trades.append(trade)
        
        # Signal attribution
        signal_source = trade.get('signal_source', 'unknown')
        if signal_source not in self.signal_attribution:
            self.signal_attribution[signal_source] = []
        self.signal_attribution[signal_source].append(trade.get('pnl', 0))
        
        # Strategy attribution
        strategy = trade.get('strategy', 'unknown')
        if strategy not in self.strategy_attribution:
            self.strategy_attribution[strategy] = []
        self.strategy_attribution[strategy].append(trade.get('pnl', 0))
    
    def get_signal_attribution(self) -> Dict[str, Dict[str, float]]:
        """Get P&L attribution by signal source"""
        attribution = {}
        
        for source, pnls in self.signal_attribution.items():
            if pnls:
                attribution[source] = {
                    'total_pnl': sum(pnls),
                    'trade_count': len(pnls),
                    'avg_pnl': np.mean(pnls),
                    'win_rate': sum(1 for p in pnls if p > 0) / len(pnls),
                    'sharpe': np.mean(pnls) / (np.std(pnls) + 1e-10) * np.sqrt(252),
                }
        
        return attribution
    
    def get_strategy_attribution(self) -> Dict[str, Dict[str, float]]:
        """Get P&L attribution by strategy"""
        attribution = {}
        
        for strategy, pnls in self.strategy_attribution.items():
            if pnls:
                attribution[strategy] = {
                    'total_pnl': sum(pnls),
                    'trade_count': len(pnls),
                    'avg_pnl': np.mean(pnls),
                    'win_rate': sum(1 for p in pnls if p > 0) / len(pnls),
                    'sharpe': np.mean(pnls) / (np.std(pnls) + 1e-10) * np.sqrt(252),
                }
        
        return attribution
    
    def get_time_analysis(self) -> Dict[str, Any]:
        """Analyze performance by time of day/week"""
        if not self.trades:
            return {}
        
        # By hour
        hourly_pnl = {}
        for trade in self.trades:
            hour = trade.get('timestamp', datetime.now()).hour
            if hour not in hourly_pnl:
                hourly_pnl[hour] = []
            hourly_pnl[hour].append(trade.get('pnl', 0))
        
        hourly_stats = {
            hour: {
                'avg_pnl': np.mean(pnls),
                'trade_count': len(pnls),
                'win_rate': sum(1 for p in pnls if p > 0) / len(pnls),
            }
            for hour, pnls in hourly_pnl.items()
        }
        
        # By day of week
        daily_pnl = {}
        for trade in self.trades:
            day = trade.get('timestamp', datetime.now()).strftime('%A')
            if day not in daily_pnl:
                daily_pnl[day] = []
            daily_pnl[day].append(trade.get('pnl', 0))
        
        daily_stats = {
            day: {
                'avg_pnl': np.mean(pnls),
                'trade_count': len(pnls),
                'win_rate': sum(1 for p in pnls if p > 0) / len(pnls),
            }
            for day, pnls in daily_pnl.items()
        }
        
        return {
            'hourly': hourly_stats,
            'daily': daily_stats,
        }
    
    def get_trade_statistics(self) -> Dict[str, Any]:
        """Get comprehensive trade statistics"""
        if not self.trades:
            return {}
        
        trades = list(self.trades)
        pnls = [t.get('pnl', 0) for t in trades]
        
        wins = [p for p in pnls if p > 0]
        losses = [p for p in pnls if p < 0]
        
        # Hold times
        hold_times = []
        for trade in trades:
            entry_time = trade.get('entry_time')
            exit_time = trade.get('exit_time')
            if entry_time and exit_time:
                hold_times.append((exit_time - entry_time).total_seconds() / 60)
        
        return {
            'total_trades': len(trades),
            'winning_trades': len(wins),
            'losing_trades': len(losses),
            'win_rate': len(wins) / len(pnls) if pnls else 0,
            'avg_win': np.mean(wins) if wins else 0,
            'avg_loss': np.mean(losses) if losses else 0,
            'largest_win': max(wins) if wins else 0,
            'largest_loss': min(losses) if losses else 0,
            'profit_factor': sum(wins) / abs(sum(losses)) if losses else float('inf'),
            'avg_hold_time_minutes': np.mean(hold_times) if hold_times else 0,
            'median_hold_time_minutes': np.median(hold_times) if hold_times else 0,
        }
