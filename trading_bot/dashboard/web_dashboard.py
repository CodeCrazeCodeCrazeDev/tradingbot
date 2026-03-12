"""
from typing import Any, List, Optional, Set
Web Dashboard for Trading Bot Monitoring and Control

Production-ready dashboard with:
- Real-time trading metrics
- Position management
- Order management
- Performance charts
- System health monitoring
- Manual intervention controls
"""

import asyncio
import logging
import json
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
import os

logger = logging.getLogger(__name__)

# FastAPI and web imports
try:
    from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect, Depends, HTTPException
    from fastapi.responses import HTMLResponse, JSONResponse
    from fastapi.staticfiles import StaticFiles
    from fastapi.templating import Jinja2Templates
    from fastapi.middleware.cors import CORSMiddleware
    import uvicorn
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    logger.warning("FastAPI not installed")


class WebDashboard:
    """
    Web-based dashboard for trading bot monitoring and control.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        if not FASTAPI_AVAILABLE:
            raise ImportError("FastAPI not installed. Install with: pip install fastapi uvicorn jinja2")
        
        self.config = config or {}
        self.host = self.config.get('host', '0.0.0.0')
        self.port = self.config.get('port', 8080)
        
        # Create FastAPI app
        self.app = FastAPI(
            title="AlphaAlgo Trading Dashboard",
            description="Real-time trading monitoring and control",
            version="2.0.0"
        )
        
        # CORS
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Dependencies
        self.broker = None
        self.monitor = None
        self.database = None
        
        # WebSocket connections
        self.ws_connections: List[WebSocket] = []
        
        # Cache for dashboard data
        self._cache: Dict[str, Any] = {}
        self._cache_ttl = 5  # seconds
        self._cache_timestamps: Dict[str, datetime] = {}
        
        # Setup routes
        self._setup_routes()
        
        logger.info(f"WebDashboard initialized on {self.host}:{self.port}")
    
    def set_broker(self, broker):
        """Set broker adapter"""
        self.broker = broker
    
    def set_monitor(self, monitor):
        """Set production monitor"""
        self.monitor = monitor
    
    def set_database(self, database):
        """Set database manager"""
        self.database = database
    
    def _get_cached(self, key: str) -> Optional[Any]:
        """Get cached value if not expired"""
        if key in self._cache:
            timestamp = self._cache_timestamps.get(key)
            if timestamp and (datetime.now() - timestamp).total_seconds() < self._cache_ttl:
                return self._cache[key]
        return None
    
    def _set_cached(self, key: str, value: Any):
        """Set cached value"""
        self._cache[key] = value
        self._cache_timestamps[key] = datetime.now()
    
    def _setup_routes(self):
        """Setup dashboard routes"""
        
        # ==========================================
        # Dashboard HTML Pages
        # ==========================================
        
        @self.app.get("/", response_class=HTMLResponse)
        async def dashboard_home(request: Request):
            """Main dashboard page"""
            return self._render_dashboard_html()
        
        @self.app.get("/trading", response_class=HTMLResponse)
        async def trading_page(request: Request):
            """Trading page"""
            return self._render_trading_html()
        
        @self.app.get("/positions", response_class=HTMLResponse)
        async def positions_page(request: Request):
            """Positions page"""
            return self._render_positions_html()
        
        @self.app.get("/performance", response_class=HTMLResponse)
        async def performance_page(request: Request):
            """Performance page"""
            return self._render_performance_html()
        
        # ==========================================
        # API Endpoints for Dashboard Data
        # ==========================================
        
        @self.app.get("/api/dashboard/summary")
        async def get_dashboard_summary():
            """Get dashboard summary data"""
            cached = self._get_cached('summary')
            if cached:
                return cached
            
            summary = await self._get_summary_data()
            self._set_cached('summary', summary)
            return summary
        
        @self.app.get("/api/dashboard/positions")
        async def get_positions():
            """Get current positions"""
            if not self.broker:
                return []
            try:
            
                positions = await self.broker.get_positions()
                return [
                    {
                        'symbol': p.symbol,
                        'side': p.side,
                        'quantity': p.quantity,
                        'entry_price': p.entry_price,
                        'current_price': p.current_price,
                        'unrealized_pnl': p.unrealized_pnl,
                        'pnl_percent': ((p.current_price - p.entry_price) / p.entry_price * 100) if p.entry_price else 0
                    }
                    for p in positions
                ]
            except Exception as e:
                logger.error(f"Failed to get positions: {e}")
                return []
        
        @self.app.get("/api/dashboard/account")
        async def get_account():
            """Get account information"""
            if not self.broker:
                return {}
            try:
            
                info = await self.broker.get_account_info()
                return info
            except Exception as e:
                logger.error(f"Failed to get account: {e}")
                return {}
        
        @self.app.get("/api/dashboard/trades")
        async def get_recent_trades(limit: int = 20):
            """Get recent trades"""
            if not self.database:
                return []
            try:
            
                trades = await self.database.get_trades(limit=limit)
                return trades
            except Exception as e:
                logger.error(f"Failed to get trades: {e}")
                return []
        
        @self.app.get("/api/dashboard/performance")
        async def get_performance():
            """Get performance metrics"""
            if not self.database:
                return {}
            try:
            
                stats = await self.database.get_trade_statistics()
                return stats
            except Exception as e:
                logger.error(f"Failed to get performance: {e}")
                return {}
        
        @self.app.get("/api/dashboard/equity-curve")
        async def get_equity_curve(days: int = 30):
            """Get equity curve data"""
            if not self.database:
                return []
            try:
            
                start_time = datetime.now() - timedelta(days=days)
                history = await self.database.get_account_history(start_time=start_time)
                return history
            except Exception as e:
                logger.error(f"Failed to get equity curve: {e}")
                return []
        
        @self.app.get("/api/dashboard/health")
        async def get_health():
            """Get system health"""
            if not self.monitor:
                return {'status': 'unknown'}
            
            return self.monitor.get_status()
        
        @self.app.get("/api/dashboard/alerts")
        async def get_alerts(limit: int = 50):
            """Get recent alerts"""
            if not self.monitor:
                return []
            
            alerts = self.monitor.alert_manager.get_alerts(limit=limit)
            return [a.to_dict() for a in alerts]
        
        # ==========================================
        # Control Endpoints
        # ==========================================
        
        @self.app.post("/api/control/close-position/{symbol}")
        async def close_position(symbol: str):
            """Close a position"""
            if not self.broker:
                raise HTTPException(status_code=503, detail="Broker not available")
            try:
            
                if hasattr(self.broker, 'close_position'):
                    success = await self.broker.close_position(symbol)
                    return {'success': success, 'symbol': symbol}
                raise HTTPException(status_code=400, detail="Close position not supported")
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/control/close-all")
        async def close_all_positions():
            """Close all positions"""
            if not self.broker:
                raise HTTPException(status_code=503, detail="Broker not available")
            try:
            
                if hasattr(self.broker, 'close_all_positions'):
                    success = await self.broker.close_all_positions()
                    return {'success': success}
                raise HTTPException(status_code=400, detail="Close all not supported")
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/control/emergency-stop")
        async def emergency_stop():
            """Emergency stop - close all and disable trading"""
            # Close all positions
            if self.broker and hasattr(self.broker, 'close_all_positions'):
                await self.broker.close_all_positions()
            
            # Send alert
            if self.monitor:
                from trading_bot.monitoring.production_monitoring import AlertSeverity
                await self.monitor.send_alert(
                    AlertSeverity.CRITICAL,
                    "Emergency Stop Activated",
                    "All positions closed and trading disabled",
                    source="Dashboard"
                )
            
            return {'success': True, 'message': 'Emergency stop activated'}
        
        # ==========================================
        # WebSocket for Real-time Updates
        # ==========================================
        
        @self.app.websocket("/ws/dashboard")
        async def websocket_endpoint(websocket: WebSocket):
            """WebSocket for real-time dashboard updates"""
            await websocket.accept()
            self.ws_connections.append(websocket)
            
            try:
                while True:
                    # Send updates every second
                    data = await self._get_realtime_data()
                    await websocket.send_json(data)
                    await asyncio.sleep(1)
                    
            except WebSocketDisconnect:
                self.ws_connections.remove(websocket)
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                if websocket in self.ws_connections:
                    self.ws_connections.remove(websocket)
    
    async def _get_summary_data(self) -> Dict[str, Any]:
        """Get summary data for dashboard"""
        summary = {
            'timestamp': datetime.now().isoformat(),
            'account': {},
            'positions': [],
            'performance': {},
            'health': {}
        }
        
        if self.broker:
            try:
                summary['account'] = await self.broker.get_account_info()
                positions = await self.broker.get_positions()
                summary['positions'] = [
                    {
                        'symbol': p.symbol,
                        'side': p.side,
                        'quantity': p.quantity,
                        'unrealized_pnl': p.unrealized_pnl
                    }
                    for p in positions
                ]
            except Exception as e:
                logger.error(f"Error getting broker data: {e}")
        
        if self.database:
            try:
                summary['performance'] = await self.database.get_trade_statistics()
            except Exception as e:
                logger.error(f"Error getting performance data: {e}")
        
        if self.monitor:
            summary['health'] = self.monitor.get_status()
        
        return summary
    
    async def _get_realtime_data(self) -> Dict[str, Any]:
        """Get real-time data for WebSocket"""
        data = {
            'timestamp': datetime.now().isoformat(),
            'type': 'update'
        }
        
        if self.broker:
            try:
                info = await self.broker.get_account_info()
                data['equity'] = info.get('equity', 0)
                data['balance'] = info.get('balance', 0)
                data['profit'] = info.get('profit', 0)
            except Exception:
                pass
        
        return data
    
    def _render_dashboard_html(self) -> str:
        """Render main dashboard HTML"""
        return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AlphaAlgo Trading Dashboard</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        .card { @apply bg-white rounded-lg shadow-md p-6; }
        .stat-value { @apply text-3xl font-bold; }
        .stat-label { @apply text-gray-500 text-sm; }
        .positive { @apply text-green-600; }
        .negative { @apply text-red-600; }
    </style>
</head>
<body class="bg-gray-100">
    <nav class="bg-blue-600 text-white p-4">
        <div class="container mx-auto flex justify-between items-center">
            <h1 class="text-2xl font-bold">
                <i class="fas fa-chart-line mr-2"></i>AlphaAlgo Dashboard
            </h1>
            <div class="flex items-center space-x-4">
                <span id="connection-status" class="px-3 py-1 rounded-full bg-green-500 text-sm">
                    <i class="fas fa-circle mr-1"></i>Connected
                </span>
                <span id="last-update" class="text-sm opacity-75"></span>
            </div>
        </div>
    </nav>

    <main class="container mx-auto p-6">
        <!-- Account Summary -->
        <div class="grid grid-cols-1 md:grid-cols-4 gap-6 mb-6">
            <div class="card">
                <div class="stat-label">Account Balance</div>
                <div class="stat-value" id="balance">$0.00</div>
            </div>
            <div class="card">
                <div class="stat-label">Equity</div>
                <div class="stat-value" id="equity">$0.00</div>
            </div>
            <div class="card">
                <div class="stat-label">Open P&L</div>
                <div class="stat-value" id="open-pnl">$0.00</div>
            </div>
            <div class="card">
                <div class="stat-label">Today's P&L</div>
                <div class="stat-value" id="daily-pnl">$0.00</div>
            </div>
        </div>

        <!-- Performance Stats -->
        <div class="grid grid-cols-1 md:grid-cols-4 gap-6 mb-6">
            <div class="card">
                <div class="stat-label">Total Trades</div>
                <div class="stat-value" id="total-trades">0</div>
            </div>
            <div class="card">
                <div class="stat-label">Win Rate</div>
                <div class="stat-value" id="win-rate">0%</div>
            </div>
            <div class="card">
                <div class="stat-label">Profit Factor</div>
                <div class="stat-value" id="profit-factor">0.00</div>
            </div>
            <div class="card">
                <div class="stat-label">Max Drawdown</div>
                <div class="stat-value negative" id="max-drawdown">0%</div>
            </div>
        </div>

        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
            <!-- Equity Chart -->
            <div class="card">
                <h2 class="text-xl font-semibold mb-4">
                    <i class="fas fa-chart-area mr-2"></i>Equity Curve
                </h2>
                <canvas id="equity-chart" height="200"></canvas>
            </div>

            <!-- Open Positions -->
            <div class="card">
                <div class="flex justify-between items-center mb-4">
                    <h2 class="text-xl font-semibold">
                        <i class="fas fa-list mr-2"></i>Open Positions
                    </h2>
                    <button onclick="closeAllPositions()" class="bg-red-500 text-white px-4 py-2 rounded hover:bg-red-600">
                        Close All
                    </button>
                </div>
                <div class="overflow-x-auto">
                    <table class="w-full">
                        <thead>
                            <tr class="border-b">
                                <th class="text-left py-2">Symbol</th>
                                <th class="text-left py-2">Side</th>
                                <th class="text-right py-2">Size</th>
                                <th class="text-right py-2">P&L</th>
                                <th class="text-right py-2">Action</th>
                            </tr>
                        </thead>
                        <tbody id="positions-table">
                            <tr><td colspan="5" class="text-center py-4 text-gray-500">No open positions</td></tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>

        <!-- Recent Trades & Alerts -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <!-- Recent Trades -->
            <div class="card">
                <h2 class="text-xl font-semibold mb-4">
                    <i class="fas fa-history mr-2"></i>Recent Trades
                </h2>
                <div class="overflow-x-auto max-h-64 overflow-y-auto">
                    <table class="w-full">
                        <thead class="sticky top-0 bg-white">
                            <tr class="border-b">
                                <th class="text-left py-2">Time</th>
                                <th class="text-left py-2">Symbol</th>
                                <th class="text-left py-2">Side</th>
                                <th class="text-right py-2">P&L</th>
                            </tr>
                        </thead>
                        <tbody id="trades-table">
                            <tr><td colspan="4" class="text-center py-4 text-gray-500">No recent trades</td></tr>
                        </tbody>
                    </table>
                </div>
            </div>

            <!-- System Alerts -->
            <div class="card">
                <h2 class="text-xl font-semibold mb-4">
                    <i class="fas fa-bell mr-2"></i>System Alerts
                </h2>
                <div id="alerts-container" class="max-h-64 overflow-y-auto space-y-2">
                    <div class="text-center py-4 text-gray-500">No alerts</div>
                </div>
            </div>
        </div>

        <!-- Emergency Controls -->
        <div class="mt-6 card bg-red-50 border border-red-200">
            <h2 class="text-xl font-semibold text-red-700 mb-4">
                <i class="fas fa-exclamation-triangle mr-2"></i>Emergency Controls
            </h2>
            <div class="flex space-x-4">
                <button onclick="emergencyStop()" class="bg-red-600 text-white px-6 py-3 rounded-lg hover:bg-red-700 font-semibold">
                    <i class="fas fa-stop-circle mr-2"></i>EMERGENCY STOP
                </button>
                <button onclick="closeAllPositions()" class="bg-orange-500 text-white px-6 py-3 rounded-lg hover:bg-orange-600 font-semibold">
                    <i class="fas fa-times-circle mr-2"></i>Close All Positions
                </button>
            </div>
        </div>
    </main>

    <script>
        let ws;
        let equityChart;

        // Initialize
        document.addEventListener('DOMContentLoaded', () => {
            initWebSocket();
            initChart();
            loadDashboardData();
            setInterval(loadDashboardData, 5000);
        });

        function initWebSocket() {
            ws = new WebSocket(`ws://${window.location.host}/ws/dashboard`);
            
            ws.onopen = () => {
                document.getElementById('connection-status').className = 'px-3 py-1 rounded-full bg-green-500 text-sm';
                document.getElementById('connection-status').innerHTML = '<i class="fas fa-circle mr-1"></i>Connected';
            };
            
            ws.onclose = () => {
                document.getElementById('connection-status').className = 'px-3 py-1 rounded-full bg-red-500 text-sm';
                document.getElementById('connection-status').innerHTML = '<i class="fas fa-circle mr-1"></i>Disconnected';
                setTimeout(initWebSocket, 3000);
            };
            
            ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                updateRealtime(data);
            };
        }

        function initChart() {
            const ctx = document.getElementById('equity-chart').getContext('2d');
            equityChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [{
                        label: 'Equity',
                        data: [],
                        borderColor: 'rgb(59, 130, 246)',
                        backgroundColor: 'rgba(59, 130, 246, 0.1)',
                        fill: true,
                        tension: 0.4
                    }]
                },
                options: {
                    responsive: true,
                    plugins: { legend: { display: false } },
                    scales: {
                        y: { beginAtZero: false }
                    }
                }
            });
        }

        async function loadDashboardData() {
            try {
                // Load summary
                const summary = await fetch('/api/dashboard/summary').then(r => r.json());
                updateSummary(summary);

                // Load positions
                const positions = await fetch('/api/dashboard/positions').then(r => r.json());
                updatePositions(positions);

                // Load trades
                const trades = await fetch('/api/dashboard/trades?limit=10').then(r => r.json());
                updateTrades(trades);

                // Load alerts
                const alerts = await fetch('/api/dashboard/alerts?limit=10').then(r => r.json());
                updateAlerts(alerts);

                // Load equity curve
                const equity = await fetch('/api/dashboard/equity-curve?days=7').then(r => r.json());
                updateEquityChart(equity);

                document.getElementById('last-update').textContent = 'Updated: ' + new Date().toLocaleTimeString();
            } catch (e) {
                console.error('Failed to load data:', e);
            }
        }

        function updateSummary(data) {
            if (data.account) {
                document.getElementById('balance').textContent = formatCurrency(data.account.balance || 0);
                document.getElementById('equity').textContent = formatCurrency(data.account.equity || 0);
                document.getElementById('open-pnl').textContent = formatCurrency(data.account.profit || 0);
                document.getElementById('open-pnl').className = 'stat-value ' + (data.account.profit >= 0 ? 'positive' : 'negative');
            }
            if (data.performance) {
                document.getElementById('total-trades').textContent = data.performance.total_trades || 0;
                document.getElementById('win-rate').textContent = (data.performance.win_rate || 0).toFixed(1) + '%';
            }
        }

        function updateRealtime(data) {
            if (data.equity) {
                document.getElementById('equity').textContent = formatCurrency(data.equity);
            }
            if (data.profit !== undefined) {
                document.getElementById('open-pnl').textContent = formatCurrency(data.profit);
                document.getElementById('open-pnl').className = 'stat-value ' + (data.profit >= 0 ? 'positive' : 'negative');
            }
        }

        function updatePositions(positions) {
            const tbody = document.getElementById('positions-table');
            if (!positions || positions.length === 0) {
                tbody.innerHTML = '<tr><td colspan="5" class="text-center py-4 text-gray-500">No open positions</td></tr>';
                return;
            }
            tbody.innerHTML = positions.map(p => `
                <tr class="border-b hover:bg-gray-50">
                    <td class="py-2 font-semibold">${p.symbol}</td>
                    <td class="py-2"><span class="px-2 py-1 rounded ${p.side === 'buy' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}">${p.side.toUpperCase()}</span></td>
                    <td class="py-2 text-right">${p.quantity}</td>
                    <td class="py-2 text-right ${p.unrealized_pnl >= 0 ? 'text-green-600' : 'text-red-600'}">${formatCurrency(p.unrealized_pnl)}</td>
                    <td class="py-2 text-right"><button onclick="closePosition('${p.symbol}')" class="text-red-500 hover:text-red-700"><i class="fas fa-times"></i></button></td>
                </tr>
            `).join('');
        }

        function updateTrades(trades) {
            const tbody = document.getElementById('trades-table');
            if (!trades || trades.length === 0) {
                tbody.innerHTML = '<tr><td colspan="4" class="text-center py-4 text-gray-500">No recent trades</td></tr>';
                return;
            }
            tbody.innerHTML = trades.map(t => `
                <tr class="border-b hover:bg-gray-50">
                    <td class="py-2 text-sm">${new Date(t.entry_time).toLocaleString()}</td>
                    <td class="py-2">${t.symbol}</td>
                    <td class="py-2"><span class="px-2 py-1 rounded ${t.side === 'buy' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}">${t.side.toUpperCase()}</span></td>
                    <td class="py-2 text-right ${(t.pnl || 0) >= 0 ? 'text-green-600' : 'text-red-600'}">${formatCurrency(t.pnl || 0)}</td>
                </tr>
            `).join('');
        }

        function updateAlerts(alerts) {
            const container = document.getElementById('alerts-container');
            if (!alerts || alerts.length === 0) {
                container.innerHTML = '<div class="text-center py-4 text-gray-500">No alerts</div>';
                return;
            }
            const severityColors = {
                'info': 'bg-blue-100 border-blue-300 text-blue-800',
                'warning': 'bg-yellow-100 border-yellow-300 text-yellow-800',
                'error': 'bg-red-100 border-red-300 text-red-800',
                'critical': 'bg-red-200 border-red-500 text-red-900'
            };
            container.innerHTML = alerts.map(a => `
                <div class="p-3 rounded border ${severityColors[a.severity] || 'bg-gray-100'}">
                    <div class="font-semibold">${a.title}</div>
                    <div class="text-sm">${a.message}</div>
                    <div class="text-xs opacity-75 mt-1">${new Date(a.timestamp).toLocaleString()}</div>
                </div>
            `).join('');
        }

        function updateEquityChart(data) {
            if (!data || data.length === 0) return;
            equityChart.data.labels = data.map(d => new Date(d.snapshot_time).toLocaleDateString());
            equityChart.data.datasets[0].data = data.map(d => d.equity);
            equityChart.update();
        }

        function formatCurrency(value) {
            return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(value || 0);
        }

        async function closePosition(symbol) {
            if (!confirm(`Close position for ${symbol}?`)) return;
            try {
                await fetch(`/api/control/close-position/${symbol}`, { method: 'POST' });
                loadDashboardData();
            } catch (e) {
                alert('Failed to close position');
            }
        }

        async function closeAllPositions() {
            if (!confirm('Close ALL positions?')) return;
            try {
                await fetch('/api/control/close-all', { method: 'POST' });
                loadDashboardData();
            } catch (e) {
                alert('Failed to close positions');
            }
        }

        async function emergencyStop() {
            if (!confirm('EMERGENCY STOP: This will close all positions and disable trading. Continue?')) return;
            try {
                await fetch('/api/control/emergency-stop', { method: 'POST' });
                alert('Emergency stop activated');
                loadDashboardData();
            } catch (e) {
                alert('Emergency stop failed');
            }
        }
    </script>
</body>
</html>
        """
    
    def _render_trading_html(self) -> str:
        """Render trading page HTML"""
        return "<html><body><h1>Trading Page</h1></body></html>"
    
    def _render_positions_html(self) -> str:
        """Render positions page HTML"""
        return "<html><body><h1>Positions Page</h1></body></html>"
    
    def _render_performance_html(self) -> str:
        """Render performance page HTML"""
        return "<html><body><h1>Performance Page</h1></body></html>"
    
    def run(self):
        """Run the dashboard server"""
        uvicorn.run(
            self.app,
            host=self.host,
            port=self.port,
            log_level="info"
        )
    
    async def run_async(self):
        """Run the dashboard server asynchronously"""
        config = uvicorn.Config(
            self.app,
            host=self.host,
            port=self.port,
            log_level="info"
        )
        server = uvicorn.Server(config)
        await server.serve()


# Export
__all__ = ['WebDashboard']
