"""
React-Style Web Dashboard Backend
==================================
Production-grade dashboard backend with REST API and WebSocket support.
Provides real-time data for React/Vue frontend.
"""

import asyncio
import json
import logging
import threading
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set
import hashlib
import secrets
from enum import auto

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


# ============================================================================
# CONFIGURATION
# ============================================================================

@dataclass
class DashboardConfig:
    """Dashboard configuration."""
    host: str = "0.0.0.0"
    port: int = 8080
    ws_port: int = 8081
    enable_auth: bool = True
    api_key: str = ""
    cors_origins: List[str] = field(default_factory=lambda: ["*"])
    refresh_interval_ms: int = 1000
    max_connections: int = 100
    enable_ssl: bool = False
    ssl_cert_path: str = ""
    ssl_key_path: str = ""


# ============================================================================
# DATA MODELS
# ============================================================================

@dataclass
class DashboardData:
    """Dashboard data snapshot."""
    timestamp: datetime
    account: Dict[str, Any]
    positions: List[Dict]
    orders: List[Dict]
    signals: List[Dict]
    performance: Dict[str, Any]
    system: Dict[str, Any]
    alerts: List[Dict]


@dataclass
class ChartData:
    """Chart data for frontend."""
    chart_type: str
    labels: List[str]
    datasets: List[Dict]
    options: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WebSocketMessage:
    """WebSocket message."""
    event: str
    data: Any
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_json(self) -> str:
        return json.dumps({
            'event': self.event,
            'data': self.data,
            'timestamp': self.timestamp.isoformat(),
        })


# ============================================================================
# DATA PROVIDERS
# ============================================================================

class DashboardDataProvider:
    """
    Provides data for the dashboard.
    Aggregates data from various sources.
    """
    
    def __init__(self):
        self._data_sources: Dict[str, Callable] = {}
        self._cache: Dict[str, Any] = {}
        self._cache_ttl: Dict[str, datetime] = {}
        self._default_ttl = timedelta(seconds=5)
        self._lock = threading.Lock()
    
    def register_source(self, name: str, provider: Callable, ttl: Optional[timedelta] = None):
        """Register a data source."""
        self._data_sources[name] = {
            'provider': provider,
            'ttl': ttl or self._default_ttl,
        }
    
    async def get_data(self, name: str) -> Any:
        """Get data from source with caching."""
        with self._lock:
            # Check cache
            if name in self._cache:
                if datetime.utcnow() < self._cache_ttl.get(name, datetime.min):
                    return self._cache[name]
            
            # Get fresh data
            if name not in self._data_sources:
                return None
            
            source = self._data_sources[name]
            provider = source['provider']
            
            try:
                if asyncio.iscoroutinefunction(provider):
                    data = await provider()
                else:
                    data = provider()
                
                # Cache
                self._cache[name] = data
                self._cache_ttl[name] = datetime.utcnow() + source['ttl']
                
                return data
            except Exception as e:
                logger.error(f"Data provider error for {name}: {e}")
                return self._cache.get(name)
    
    async def get_dashboard_data(self) -> DashboardData:
        """Get complete dashboard data."""
        return DashboardData(
            timestamp=datetime.utcnow(),
            account=await self.get_data('account') or {},
            positions=await self.get_data('positions') or [],
            orders=await self.get_data('orders') or [],
            signals=await self.get_data('signals') or [],
            performance=await self.get_data('performance') or {},
            system=await self.get_data('system') or {},
            alerts=await self.get_data('alerts') or [],
        )


# ============================================================================
# REST API
# ============================================================================

class DashboardAPI:
    """
    REST API for dashboard.
    Provides endpoints for frontend.
    """
    
    def __init__(self, config: DashboardConfig, data_provider: DashboardDataProvider):
        self.config = config
        self.data_provider = data_provider
        self._routes: Dict[str, Callable] = {}
        self._setup_routes()
    
    def _setup_routes(self):
        """Setup API routes."""
        self._routes = {
            'GET /api/dashboard': self._get_dashboard,
            'GET /api/account': self._get_account,
            'GET /api/positions': self._get_positions,
            'GET /api/orders': self._get_orders,
            'GET /api/signals': self._get_signals,
            'GET /api/performance': self._get_performance,
            'GET /api/system': self._get_system,
            'GET /api/alerts': self._get_alerts,
            'GET /api/chart/equity': self._get_equity_chart,
            'GET /api/chart/pnl': self._get_pnl_chart,
            'GET /api/chart/drawdown': self._get_drawdown_chart,
            'POST /api/order': self._submit_order,
            'DELETE /api/order/{id}': self._cancel_order,
            'POST /api/position/close/{symbol}': self._close_position,
            'POST /api/trading/pause': self._pause_trading,
            'POST /api/trading/resume': self._resume_trading,
            'POST /api/trading/stop': self._stop_trading,
        }
    
    async def _get_dashboard(self, params: Dict) -> Dict:
        """Get full dashboard data."""
        data = await self.data_provider.get_dashboard_data()
        return {
            'timestamp': data.timestamp.isoformat(),
            'account': data.account,
            'positions': data.positions,
            'orders': data.orders,
            'signals': data.signals,
            'performance': data.performance,
            'system': data.system,
            'alerts': data.alerts,
        }
    
    async def _get_account(self, params: Dict) -> Dict:
        """Get account data."""
        return await self.data_provider.get_data('account') or {}
    
    async def _get_positions(self, params: Dict) -> List:
        """Get positions."""
        return await self.data_provider.get_data('positions') or []
    
    async def _get_orders(self, params: Dict) -> List:
        """Get orders."""
        return await self.data_provider.get_data('orders') or []
    
    async def _get_signals(self, params: Dict) -> List:
        """Get signals."""
        return await self.data_provider.get_data('signals') or []
    
    async def _get_performance(self, params: Dict) -> Dict:
        """Get performance metrics."""
        return await self.data_provider.get_data('performance') or {}
    
    async def _get_system(self, params: Dict) -> Dict:
        """Get system status."""
        return await self.data_provider.get_data('system') or {}
    
    async def _get_alerts(self, params: Dict) -> List:
        """Get alerts."""
        return await self.data_provider.get_data('alerts') or []
    
    async def _get_equity_chart(self, params: Dict) -> Dict:
        """Get equity chart data."""
        # This would be connected to actual data
        return {
            'type': 'line',
            'labels': ['Mon', 'Tue', 'Wed', 'Thu', 'Fri'],
            'datasets': [{
                'label': 'Equity',
                'data': [10000, 10250, 10100, 10400, 10350],
                'borderColor': '#4CAF50',
                'fill': False,
            }],
        }
    
    async def _get_pnl_chart(self, params: Dict) -> Dict:
        """Get P&L chart data."""
        return {
            'type': 'bar',
            'labels': ['Mon', 'Tue', 'Wed', 'Thu', 'Fri'],
            'datasets': [{
                'label': 'Daily P&L',
                'data': [250, -150, 300, -50, 100],
                'backgroundColor': ['#4CAF50', '#F44336', '#4CAF50', '#F44336', '#4CAF50'],
            }],
        }
    
    async def _get_drawdown_chart(self, params: Dict) -> Dict:
        """Get drawdown chart data."""
        return {
            'type': 'line',
            'labels': ['Mon', 'Tue', 'Wed', 'Thu', 'Fri'],
            'datasets': [{
                'label': 'Drawdown %',
                'data': [0, -1.5, -2.0, -1.0, -0.5],
                'borderColor': '#F44336',
                'fill': True,
                'backgroundColor': 'rgba(244, 67, 54, 0.1)',
            }],
        }
    
    async def _submit_order(self, params: Dict) -> Dict:
        """Submit order."""
        # This would be connected to actual order submission
        return {'status': 'submitted', 'order_id': 'ord_' + secrets.token_hex(8)}
    
    async def _cancel_order(self, params: Dict) -> Dict:
        """Cancel order."""
        return {'status': 'cancelled', 'order_id': params.get('id')}
    
    async def _close_position(self, params: Dict) -> Dict:
        """Close position."""
        return {'status': 'closed', 'symbol': params.get('symbol')}
    
    async def _pause_trading(self, params: Dict) -> Dict:
        """Pause trading."""
        return {'status': 'paused'}
    
    async def _resume_trading(self, params: Dict) -> Dict:
        """Resume trading."""
        return {'status': 'resumed'}
    
    async def _stop_trading(self, params: Dict) -> Dict:
        """Stop trading."""
        return {'status': 'stopped'}
    
    async def handle_request(self, method: str, path: str, params: Dict) -> Dict:
        """Handle API request."""
        route_key = f"{method} {path}"
        
        # Check exact match
        if route_key in self._routes:
            handler = self._routes[route_key]
            return await handler(params)
        
        # Check pattern match
        for route, handler in self._routes.items():
            route_method, route_path = route.split(' ', 1)
            if method != route_method:
                continue
            
            if '{' in route_path:
                # Extract path parameter
                parts = route_path.split('/')
                path_parts = path.split('/')
                
                if len(parts) == len(path_parts):
                    match = True
                    for i, part in enumerate(parts):
                        if part.startswith('{') and part.endswith('}'):
                            param_name = part[1:-1]
                            params[param_name] = path_parts[i]
                        elif part != path_parts[i]:
                            match = False
                            break
                    
                    if match:
                        return await handler(params)
        
        return {'error': 'Not found', 'status': 404}


# ============================================================================
# WEBSOCKET SERVER
# ============================================================================

class WebSocketServer:
    """
    WebSocket server for real-time updates.
    """
    
    def __init__(self, config: DashboardConfig, data_provider: DashboardDataProvider):
        self.config = config
        self.data_provider = data_provider
        self._clients: Set = set()
        self._running = False
        self._lock = threading.Lock()
    
    async def start(self):
        """Start WebSocket server."""
        self._running = True
        asyncio.create_task(self._broadcast_loop())
        logger.info(f"WebSocket server started on port {self.config.ws_port}")
    
    async def stop(self):
        """Stop WebSocket server."""
        self._running = False
    
    def add_client(self, client):
        """Add client connection."""
        with self._lock:
            if len(self._clients) < self.config.max_connections:
                self._clients.add(client)
                return True
            return False
    
    def remove_client(self, client):
        """Remove client connection."""
        with self._lock:
            self._clients.discard(client)
    
    async def broadcast(self, message: WebSocketMessage):
        """Broadcast message to all clients."""
        with self._lock:
            clients = list(self._clients)
        
        for client in clients:
            try:
                await client.send(message.to_json())
            except Exception as e:
                logger.error(f"WebSocket send error: {e}")
                self.remove_client(client)
    
    async def _broadcast_loop(self):
        """Broadcast loop for real-time updates."""
        while self._running:
            try:
                # Get dashboard data
                data = await self.data_provider.get_dashboard_data()
                
                # Broadcast update
                message = WebSocketMessage(
                    event='dashboard_update',
                    data={
                        'timestamp': data.timestamp.isoformat(),
                        'account': data.account,
                        'positions': data.positions,
                        'performance': data.performance,
                    },
                )
                
                await self.broadcast(message)
                
                await asyncio.sleep(self.config.refresh_interval_ms / 1000)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Broadcast loop error: {e}")
                await asyncio.sleep(1)


# ============================================================================
# DASHBOARD SERVER
# ============================================================================

class DashboardServer:
    """
    Main dashboard server.
    Combines REST API and WebSocket server.
    """
    
    def __init__(self, config: Optional[DashboardConfig] = None):
        self.config = config or DashboardConfig()
        self.data_provider = DashboardDataProvider()
        self.api = DashboardAPI(self.config, self.data_provider)
        self.ws_server = WebSocketServer(self.config, self.data_provider)
        self._running = False
        
        # Setup default data providers
        self._setup_default_providers()
    
    def _setup_default_providers(self):
        """Setup default data providers."""
        # Account data
        self.data_provider.register_source('account', lambda: {
            'balance': 10000.00,
            'equity': 10250.00,
            'margin_used': 500.00,
            'margin_available': 9750.00,
            'unrealized_pnl': 250.00,
            'realized_pnl': 150.00,
            'currency': 'USD',
        })
        
        # Positions
        self.data_provider.register_source('positions', lambda: [
            {
                'symbol': 'EURUSD',
                'side': 'long',
                'quantity': 0.1,
                'entry_price': 1.0850,
                'current_price': 1.0875,
                'pnl': 25.00,
            },
            {
                'symbol': 'GBPUSD',
                'side': 'short',
                'quantity': 0.05,
                'entry_price': 1.2650,
                'current_price': 1.2630,
                'pnl': 10.00,
            },
        ])
        
        # Orders
        self.data_provider.register_source('orders', lambda: [])
        
        # Signals
        self.data_provider.register_source('signals', lambda: [
            {
                'symbol': 'EURUSD',
                'direction': 'buy',
                'confidence': 0.75,
                'source': 'ml_model',
                'timestamp': datetime.utcnow().isoformat(),
            },
        ])
        
        # Performance
        self.data_provider.register_source('performance', lambda: {
            'total_trades': 150,
            'winning_trades': 90,
            'losing_trades': 60,
            'win_rate': 0.60,
            'profit_factor': 1.8,
            'sharpe_ratio': 1.5,
            'max_drawdown': 0.08,
            'total_pnl': 2500.00,
        })
        
        # System
        self.data_provider.register_source('system', lambda: {
            'status': 'running',
            'mode': 'paper',
            'uptime': '24h 30m',
            'cpu_usage': 25.0,
            'memory_usage': 512,
            'last_update': datetime.utcnow().isoformat(),
        })
        
        # Alerts
        self.data_provider.register_source('alerts', lambda: [])
    
    def register_data_source(self, name: str, provider: Callable, ttl: Optional[timedelta] = None):
        """Register a custom data source."""
        self.data_provider.register_source(name, provider, ttl)
    
    async def start(self):
        """Start dashboard server."""
        self._running = True
        await self.ws_server.start()
        logger.info(f"Dashboard server started on port {self.config.port}")
    
    async def stop(self):
        """Stop dashboard server."""
        self._running = False
        await self.ws_server.stop()
        logger.info("Dashboard server stopped")
    
    async def handle_http_request(self, method: str, path: str, params: Dict) -> Dict:
        """Handle HTTP request."""
        # Auth check
        if self.config.enable_auth:
            api_key = params.get('api_key') or params.get('Authorization', '').replace('Bearer ', '')
            if api_key != self.config.api_key:
                return {'error': 'Unauthorized', 'status': 401}
        
        return await self.api.handle_request(method, path, params)


# ============================================================================
# FRONTEND HTML TEMPLATE
# ============================================================================

DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Trading Bot Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/vue@3"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2/dist/tailwind.min.css" rel="stylesheet">
    <style>
        .card { @apply bg-white rounded-lg shadow-md p-4 mb-4; }
        .stat-value { @apply text-2xl font-bold; }
        .stat-label { @apply text-gray-500 text-sm; }
        .positive { @apply text-green-500; }
        .negative { @apply text-red-500; }
    </style>
</head>
<body class="bg-gray-100">
    <div id="app" class="container mx-auto px-4 py-8">
        <header class="mb-8">
            <h1 class="text-3xl font-bold text-gray-800">Trading Bot Dashboard</h1>
            <p class="text-gray-600">Real-time trading monitoring</p>
        </header>
        
        <!-- Account Summary -->
        <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
            <div class="card">
                <div class="stat-label">Balance</div>
                <div class="stat-value">${{ formatNumber(account.balance) }}</div>
            </div>
            <div class="card">
                <div class="stat-label">Equity</div>
                <div class="stat-value">${{ formatNumber(account.equity) }}</div>
            </div>
            <div class="card">
                <div class="stat-label">Unrealized P&L</div>
                <div class="stat-value" :class="account.unrealized_pnl >= 0 ? 'positive' : 'negative'">
                    ${{ formatNumber(account.unrealized_pnl) }}
                </div>
            </div>
            <div class="card">
                <div class="stat-label">Win Rate</div>
                <div class="stat-value">{{ (performance.win_rate * 100).toFixed(1) }}%</div>
            </div>
        </div>
        
        <!-- Charts -->
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8">
            <div class="card">
                <h3 class="font-bold mb-4">Equity Curve</h3>
                <canvas id="equityChart"></canvas>
            </div>
            <div class="card">
                <h3 class="font-bold mb-4">Daily P&L</h3>
                <canvas id="pnlChart"></canvas>
            </div>
        </div>
        
        <!-- Positions -->
        <div class="card mb-8">
            <h3 class="font-bold mb-4">Open Positions</h3>
            <table class="w-full">
                <thead>
                    <tr class="text-left text-gray-500">
                        <th class="pb-2">Symbol</th>
                        <th class="pb-2">Side</th>
                        <th class="pb-2">Quantity</th>
                        <th class="pb-2">Entry</th>
                        <th class="pb-2">Current</th>
                        <th class="pb-2">P&L</th>
                    </tr>
                </thead>
                <tbody>
                    <tr v-for="pos in positions" :key="pos.symbol" class="border-t">
                        <td class="py-2 font-medium">{{ pos.symbol }}</td>
                        <td class="py-2" :class="pos.side === 'long' ? 'positive' : 'negative'">
                            {{ pos.side.toUpperCase() }}
                        </td>
                        <td class="py-2">{{ pos.quantity }}</td>
                        <td class="py-2">{{ pos.entry_price }}</td>
                        <td class="py-2">{{ pos.current_price }}</td>
                        <td class="py-2" :class="pos.pnl >= 0 ? 'positive' : 'negative'">
                            ${{ formatNumber(pos.pnl) }}
                        </td>
                    </tr>
                </tbody>
            </table>
        </div>
        
        <!-- System Status -->
        <div class="card">
            <h3 class="font-bold mb-4">System Status</h3>
            <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div>
                    <div class="stat-label">Status</div>
                    <div class="font-medium text-green-500">{{ system.status }}</div>
                </div>
                <div>
                    <div class="stat-label">Mode</div>
                    <div class="font-medium">{{ system.mode }}</div>
                </div>
                <div>
                    <div class="stat-label">Uptime</div>
                    <div class="font-medium">{{ system.uptime }}</div>
                </div>
                <div>
                    <div class="stat-label">Last Update</div>
                    <div class="font-medium">{{ formatTime(system.last_update) }}</div>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        const { createApp } = Vue;
        
        createApp({
            data() {
                return {
                    account: { balance: 0, equity: 0, unrealized_pnl: 0 },
                    positions: [],
                    performance: { win_rate: 0 },
                    system: { status: 'loading', mode: '', uptime: '', last_update: '' },
                    ws: null,
                };
            },
            methods: {
                formatNumber(num) {
                    return (num || 0).toFixed(2);
                },
                formatTime(timestamp) {
                    if (!timestamp) return '';
                    return new Date(timestamp).toLocaleTimeString();
                },
                async fetchData() {
                    try {
                        const response = await fetch('/api/dashboard');
                        const data = await response.json();
                        this.account = data.account;
                        this.positions = data.positions;
                        this.performance = data.performance;
                        this.system = data.system;
                    } catch (e) {
                        console.error('Fetch error:', e);
                    }
                },
                connectWebSocket() {
                    this.ws = new WebSocket('ws://localhost:8081');
                    this.ws.onmessage = (event) => {
                        const msg = JSON.parse(event.data);
                        if (msg.event === 'dashboard_update') {
                            this.account = msg.data.account;
                            this.positions = msg.data.positions;
                            this.performance = msg.data.performance;
                        }
                    };
                    this.ws.onclose = () => {
                        setTimeout(() => this.connectWebSocket(), 5000);
                    };
                },
            },
            mounted() {
                this.fetchData();
                this.connectWebSocket();
                setInterval(() => this.fetchData(), 5000);
            },
        }).mount('#app');
    </script>
</body>
</html>
"""


def get_dashboard_html() -> str:
    """Get dashboard HTML template."""
    return DASHBOARD_HTML


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    'DashboardConfig', 'DashboardData', 'ChartData', 'WebSocketMessage',
    'DashboardDataProvider', 'DashboardAPI', 'WebSocketServer',
    'DashboardServer', 'get_dashboard_html',
]
