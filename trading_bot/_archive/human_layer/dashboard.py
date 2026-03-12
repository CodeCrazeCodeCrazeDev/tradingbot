"""
AlphaAlgo Human Dashboard - Monitoring Interface

This module provides a simple dashboard interface for human monitoring.

Version: 1.0.0
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from enum import Enum
import logging
import asyncio

# Evolution: Added retry decorator
def retry(max_attempts=3, delay=1.0):
    """Retry decorator for resilient operations"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    if attempt < max_attempts - 1:
                        await asyncio.sleep(delay * (attempt + 1))
            raise last_error
        return wrapper
    return decorator



logger = logging.getLogger(__name__)


class AlertLevel(Enum):
    """Dashboard alert levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class DashboardPanel(Enum):
    """Dashboard panels"""
    OVERVIEW = "overview"
    POSITIONS = "positions"
    ORDERS = "orders"
    SIGNALS = "signals"
    RISK = "risk"
    PERFORMANCE = "performance"
    EVOLUTION = "evolution"
    APPROVALS = "approvals"
    ALERTS = "alerts"
    SYSTEM = "system"


@dataclass
class DashboardData:
    """Data for dashboard display"""
    timestamp: datetime
    
    # Overview
    trading_mode: str = "paper"
    is_trading: bool = False
    account_balance: float = 0.0
    daily_pnl: float = 0.0
    daily_pnl_percent: float = 0.0
    
    # Positions
    open_positions: int = 0
    total_exposure: float = 0.0
    unrealized_pnl: float = 0.0
    
    # Orders
    pending_orders: int = 0
    filled_today: int = 0
    
    # Risk
    current_drawdown: float = 0.0
    risk_level: str = "low"
    daily_loss_used: float = 0.0
    
    # Performance
    win_rate: float = 0.0
    profit_factor: float = 0.0
    sharpe_ratio: float = 0.0
    
    # System
    system_status: str = "running"
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    
    # Alerts
    pending_alerts: int = 0
    pending_approvals: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'timestamp': self.timestamp.isoformat(),
            'overview': {
                'trading_mode': self.trading_mode,
                'is_trading': self.is_trading,
                'account_balance': self.account_balance,
                'daily_pnl': self.daily_pnl,
                'daily_pnl_percent': self.daily_pnl_percent,
            },
            'positions': {
                'open_positions': self.open_positions,
                'total_exposure': self.total_exposure,
                'unrealized_pnl': self.unrealized_pnl,
            },
            'orders': {
                'pending_orders': self.pending_orders,
                'filled_today': self.filled_today,
            },
            'risk': {
                'current_drawdown': self.current_drawdown,
                'risk_level': self.risk_level,
                'daily_loss_used': self.daily_loss_used,
            },
            'performance': {
                'win_rate': self.win_rate,
                'profit_factor': self.profit_factor,
                'sharpe_ratio': self.sharpe_ratio,
            },
            'system': {
                'system_status': self.system_status,
                'cpu_usage': self.cpu_usage,
                'memory_usage': self.memory_usage,
            },
            'alerts': {
                'pending_alerts': self.pending_alerts,
                'pending_approvals': self.pending_approvals,
            },
        }


class HumanDashboard:
    """
    Human monitoring dashboard.
    
    Provides a simple interface for humans to monitor the trading bot.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Data providers
        self._data_providers: Dict[str, callable] = {}
        
        # Current data
        self._current_data = DashboardData(timestamp=datetime.now())
        
        # Update callbacks
        self._update_callbacks: List[callable] = []
        
        logger.info("HumanDashboard initialized")
    
    def register_data_provider(self, name: str, provider: callable) -> None:
        """Register a data provider"""
        self._data_providers[name] = provider
    
    def add_update_callback(self, callback: callable) -> None:
        """Add callback for data updates"""
        self._update_callbacks.append(callback)
    
    async def update(self) -> DashboardData:
        """Update dashboard data from providers"""
        data = DashboardData(timestamp=datetime.now())
        
        for name, provider in self._data_providers.items():
            try:
                result = await provider() if callable(provider) else provider
                
                # Map provider results to data fields
                if name == 'account':
                    data.account_balance = result.get('balance', 0)
                    data.daily_pnl = result.get('daily_pnl', 0)
                    data.daily_pnl_percent = result.get('daily_pnl_percent', 0)
                
                elif name == 'positions':
                    data.open_positions = result.get('count', 0)
                    data.total_exposure = result.get('exposure', 0)
                    data.unrealized_pnl = result.get('unrealized_pnl', 0)
                
                elif name == 'orders':
                    data.pending_orders = result.get('pending', 0)
                    data.filled_today = result.get('filled_today', 0)
                
                elif name == 'risk':
                    data.current_drawdown = result.get('drawdown', 0)
                    data.risk_level = result.get('level', 'low')
                    data.daily_loss_used = result.get('daily_loss_used', 0)
                
                elif name == 'performance':
                    data.win_rate = result.get('win_rate', 0)
                    data.profit_factor = result.get('profit_factor', 0)
                    data.sharpe_ratio = result.get('sharpe_ratio', 0)
                
                elif name == 'system':
                    data.system_status = result.get('status', 'unknown')
                    data.cpu_usage = result.get('cpu', 0)
                    data.memory_usage = result.get('memory', 0)
                
                elif name == 'alerts':
                    data.pending_alerts = result.get('pending_alerts', 0)
                    data.pending_approvals = result.get('pending_approvals', 0)
                
                elif name == 'trading':
                    data.trading_mode = result.get('mode', 'paper')
                    data.is_trading = result.get('is_trading', False)
                    
            except Exception as e:
                logger.error(f"Data provider {name} failed: {e}")
        
        self._current_data = data
        
        # Notify callbacks
        for callback in self._update_callbacks:
            try:
                callback(data)
            except Exception as e:
                logger.error(f"Update callback failed: {e}")
        
        return data
    
    def get_data(self) -> Dict[str, Any]:
        """Get current dashboard data"""
        return self._current_data.to_dict()
    
    def get_panel_data(self, panel: DashboardPanel) -> Dict[str, Any]:
        """Get data for a specific panel"""
        data = self._current_data.to_dict()
        
        panel_map = {
            DashboardPanel.OVERVIEW: 'overview',
            DashboardPanel.POSITIONS: 'positions',
            DashboardPanel.ORDERS: 'orders',
            DashboardPanel.RISK: 'risk',
            DashboardPanel.PERFORMANCE: 'performance',
            DashboardPanel.SYSTEM: 'system',
            DashboardPanel.ALERTS: 'alerts',
        }
        
        key = panel_map.get(panel)
        if key and key in data:
            return data[key]
        
        return {}
    
    def render_text(self) -> str:
        """Render dashboard as text"""
        data = self._current_data
        
        lines = [
            "=" * 60,
            "ALPHAALGO TRADING BOT - DASHBOARD",
            "=" * 60,
            f"Time: {data.timestamp.strftime('%Y-%m-%d %H:%M:%S')}",
            f"Mode: {data.trading_mode.upper()} | Trading: {'YES' if data.is_trading else 'NO'}",
            "",
            "--- ACCOUNT ---",
            f"Balance: ${data.account_balance:,.2f}",
            f"Daily P&L: ${data.daily_pnl:,.2f} ({data.daily_pnl_percent:+.2%})",
            "",
            "--- POSITIONS ---",
            f"Open: {data.open_positions} | Exposure: ${data.total_exposure:,.2f}",
            f"Unrealized P&L: ${data.unrealized_pnl:,.2f}",
            "",
            "--- RISK ---",
            f"Drawdown: {data.current_drawdown:.2%} | Level: {data.risk_level.upper()}",
            f"Daily Loss Used: {data.daily_loss_used:.2%}",
            "",
            "--- PERFORMANCE ---",
            f"Win Rate: {data.win_rate:.1%} | Profit Factor: {data.profit_factor:.2f}",
            f"Sharpe Ratio: {data.sharpe_ratio:.2f}",
            "",
            "--- SYSTEM ---",
            f"Status: {data.system_status.upper()}",
            f"CPU: {data.cpu_usage:.1%} | Memory: {data.memory_usage:.1%}",
            "",
            "--- ALERTS ---",
            f"Pending Alerts: {data.pending_alerts} | Pending Approvals: {data.pending_approvals}",
            "=" * 60,
        ]
        
        return "\n".join(lines)


# =============================================================================
# SINGLETON
# =============================================================================

_dashboard_instance: Optional[HumanDashboard] = None


def get_dashboard(config: Optional[Dict[str, Any]] = None) -> HumanDashboard:
    """Get the singleton dashboard"""
    global _dashboard_instance
    if _dashboard_instance is None:
        _dashboard_instance = HumanDashboard(config)
    return _dashboard_instance
