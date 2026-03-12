"""
Live Dashboard - Real-time monitoring with FastAPI and WebSockets

Provides live dashboard tiles for risk, orders, latency, throughput with component drilldown.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import json

logger = logging.getLogger(__name__)


class LiveDashboard:
    """Real-time dashboard with WebSocket updates"""
    
    def __init__(self, survival_core, config: Optional[Dict[str, Any]] = None):
        self.survival_core = survival_core
        self.config = config or {}
        
        # FastAPI app
        self.app = FastAPI(title="Elite Trading Bot Dashboard")
        
        # Active WebSocket connections
        self.active_connections: List[WebSocket] = []
        
        # Metrics tracking
        self.metrics_history = []
        self.max_history = 1000
        
        # Setup routes
        self._setup_routes()
        
        logger.info("Live dashboard initialized")
    
    def _setup_routes(self):
        """Setup FastAPI routes"""
        
        @self.app.get("/", response_class=HTMLResponse)
        async def dashboard_home():
            return self._get_dashboard_html()
        
        @self.app.get("/api/status")
        async def get_status():
            return self.survival_core.get_system_status()
        
        @self.app.get("/api/metrics")
        async def get_metrics():
            return self._get_current_metrics()
        
        @self.app.get("/api/positions")
        async def get_positions():
            positions = self.survival_core.execution.get_active_positions()
            return [
                {
                    'symbol': p.symbol,
                    'quantity': p.quantity,
                    'entry_price': p.entry_price,
                    'current_price': p.current_price,
                    'unrealized_pnl': p.unrealized_pnl,
                    'realized_pnl': p.realized_pnl
                }
                for p in positions
            ]
        
        @self.app.get("/api/orders")
        async def get_orders():
            orders = self.survival_core.execution.get_orders()
            return [
                {
                    'id': o.id,
                    'symbol': o.symbol,
                    'side': o.side,
                    'quantity': o.quantity,
                    'status': o.status.value,
                    'created_at': o.created_at.isoformat()
                }
                for o in orders[-50:]  # Last 50 orders
            ]
        
        
        @self.app.get("/health/live")
        async def liveness():
            """Kubernetes liveness probe"""
            return {"status": "alive", "timestamp": datetime.now().isoformat()}
        
        @self.app.get("/health/ready")
        async def readiness():
            """Kubernetes readiness probe"""
            from fastapi.responses import JSONResponse
            
            checks = {
                'survival_core': self.survival_core.running if hasattr(self.survival_core, 'running') else False,
                'database': hasattr(self.survival_core, 'time_series_db'),
                'execution': hasattr(self.survival_core, 'execution')
            }
            
            ready = all(checks.values())
            status_code = 200 if ready else 503
            
            return JSONResponse(
                content={"status": "ready" if ready else "not_ready", "checks": checks},
                status_code=status_code
            )

        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            await self._handle_websocket(websocket)
    
    async def _handle_websocket(self, websocket: WebSocket):
        """Handle WebSocket connection"""
        await websocket.accept()
        self.active_connections.append(websocket)
        
        try:
            while True:
                # Send updates every second
                await asyncio.sleep(1)
                metrics = self._get_current_metrics()
                await websocket.send_json(metrics)
        except WebSocketDisconnect:
            self.active_connections.remove(websocket)
    
    def _get_current_metrics(self) -> Dict[str, Any]:
        """Get current system metrics"""
        status = self.survival_core.get_system_status()
        
        # Calculate throughput
        positions = self.survival_core.execution.get_active_positions()
        orders = self.survival_core.execution.get_orders()
        
        metrics = {
            'timestamp': datetime.now().isoformat(),
            'system': {
                'running': status['system']['running'],
                'paused': status['system']['paused'],
                'error_count': status['system']['error_count']
            },
            'risk': {
                'positions_count': len(positions),
                'total_exposure': sum(abs(p.quantity * p.current_price) for p in positions),
                'total_pnl': sum(p.unrealized_pnl for p in positions),
                'risk_limits': status.get('risk_limits', {})
            },
            'orders': {
                'total': len(orders),
                'pending': len([o for o in orders if o.status.value == 'pending']),
                'filled': len([o for o in orders if o.status.value == 'filled']),
                'rejected': len([o for o in orders if o.status.value == 'rejected'])
            },
            'performance': {
                'uptime_seconds': (datetime.now() - status['system'].get('start_time', datetime.now())).total_seconds() if 'start_time' in status['system'] else 0,
                'data_quality': status.get('data_quality', {})
            }
        }
        
        # Store in history
        self.metrics_history.append(metrics)
        if len(self.metrics_history) > self.max_history:
            self.metrics_history = self.metrics_history[-self.max_history:]
        
        return metrics
    
    def _get_dashboard_html(self) -> str:
        """Get dashboard HTML"""
        return """
<!DOCTYPE html>
<html>
<head>
    <title>Elite Trading Bot Dashboard</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #0a0e27; color: #fff; }
        .header { background: #1a1f3a; padding: 20px; border-bottom: 2px solid #2a3f5f; }
        .header h1 { font-size: 24px; }
        .status { display: inline-block; margin-left: 20px; padding: 5px 15px; border-radius: 20px; font-size: 14px; }
        .status.running { background: #10b981; }
        .status.paused { background: #f59e0b; }
        .status.stopped { background: #ef4444; }
        .container { padding: 20px; }
        .tiles { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin-bottom: 20px; }
        .tile { background: #1a1f3a; border-radius: 10px; padding: 20px; border: 1px solid #2a3f5f; }
        .tile h2 { font-size: 18px; margin-bottom: 15px; color: #60a5fa; }
        .metric { display: flex; justify-content: space-between; margin: 10px 0; padding: 10px; background: #0f1629; border-radius: 5px; }
        .metric-label { color: #9ca3af; }
        .metric-value { font-weight: bold; font-size: 18px; }
        .metric-value.positive { color: #10b981; }
        .metric-value.negative { color: #ef4444; }
        .chart { height: 200px; background: #0f1629; border-radius: 5px; margin-top: 10px; }
        table { width: 100%; border-collapse: collapse; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #2a3f5f; }
        th { background: #0f1629; color: #60a5fa; }
        .position-row { background: #1a1f3a; }
        .position-row:hover { background: #2a3f5f; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🚀 Elite Trading Bot Dashboard</h1>
        <span class="status running" id="status">● RUNNING</span>
    </div>
    
    <div class="container">
        <div class="tiles">
            <div class="tile">
                <h2>📊 System Status</h2>
                <div class="metric">
                    <span class="metric-label">Running</span>
                    <span class="metric-value" id="running">Yes</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Errors</span>
                    <span class="metric-value" id="errors">0</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Uptime</span>
                    <span class="metric-value" id="uptime">0s</span>
                </div>
            </div>
            
            <div class="tile">
                <h2>💰 Risk Metrics</h2>
                <div class="metric">
                    <span class="metric-label">Positions</span>
                    <span class="metric-value" id="positions">0</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Total Exposure</span>
                    <span class="metric-value" id="exposure">$0</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Unrealized P&L</span>
                    <span class="metric-value" id="pnl">$0</span>
                </div>
            </div>
            
            <div class="tile">
                <h2>📈 Orders</h2>
                <div class="metric">
                    <span class="metric-label">Total</span>
                    <span class="metric-value" id="orders-total">0</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Pending</span>
                    <span class="metric-value" id="orders-pending">0</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Filled</span>
                    <span class="metric-value positive" id="orders-filled">0</span>
                </div>
            </div>
            
            <div class="tile">
                <h2>⚡ Performance</h2>
                <div class="metric">
                    <span class="metric-label">Data Latency</span>
                    <span class="metric-value" id="latency">0ms</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Throughput</span>
                    <span class="metric-value" id="throughput">0/s</span>
                </div>
                <div class="metric">
                    <span class="metric-label">CPU Usage</span>
                    <span class="metric-value" id="cpu">0%</span>
                </div>
            </div>
        </div>
        
        <div class="tile">
            <h2>📋 Open Positions</h2>
            <table id="positions-table">
                <thead>
                    <tr>
                        <th>Symbol</th>
                        <th>Quantity</th>
                        <th>Entry</th>
                        <th>Current</th>
                        <th>P&L</th>
                    </tr>
                </thead>
                <tbody id="positions-body">
                    <tr><td colspan="5" style="text-align:center;">No positions</td></tr>
                </tbody>
            </table>
        </div>
    </div>
    
    <script>
        const ws = new WebSocket('ws://' + window.location.host + '/ws');
        
        ws.onmessage = function(event) {
            const data = JSON.parse(event.data);
            updateDashboard(data);
        };
        
        function updateDashboard(data) {
            // System status
            document.getElementById('running').textContent = data.system.running ? 'Yes' : 'No';
            document.getElementById('errors').textContent = data.system.error_count;
            document.getElementById('uptime').textContent = Math.floor(data.performance.uptime_seconds) + 's';
            
            // Risk metrics
            document.getElementById('positions').textContent = data.risk.positions_count;
            document.getElementById('exposure').textContent = '$' + data.risk.total_exposure.toFixed(2);
            
            const pnlElement = document.getElementById('pnl');
            pnlElement.textContent = '$' + data.risk.total_pnl.toFixed(2);
            pnlElement.className = 'metric-value ' + (data.risk.total_pnl >= 0 ? 'positive' : 'negative');
            
            // Orders
            document.getElementById('orders-total').textContent = data.orders.total;
            document.getElementById('orders-pending').textContent = data.orders.pending;
            document.getElementById('orders-filled').textContent = data.orders.filled;
            
            // Status indicator
            const statusEl = document.getElementById('status');
            if (data.system.paused) {
                statusEl.textContent = '⏸ PAUSED';
                statusEl.className = 'status paused';
            } else if (data.system.running) {
                statusEl.textContent = '● RUNNING';
                statusEl.className = 'status running';
            } else {
                statusEl.textContent = '■ STOPPED';
                statusEl.className = 'status stopped';
            }
        }
        
        // Fetch positions periodically
        async function updatePositions() {
            const response = await fetch('/api/positions');
            const positions = await response.json();
            
            const tbody = document.getElementById('positions-body');
            if (positions.length === 0) {
                tbody.innerHTML = '<tr><td colspan="5" style="text-align:center;">No positions</td></tr>';
            } else {
                tbody.innerHTML = positions.map(p => `
                    <tr class="position-row">
                        <td>${p.symbol}</td>
                        <td>${p.quantity.toFixed(2)}</td>
                        <td>${p.entry_price.toFixed(5)}</td>
                        <td>${p.current_price.toFixed(5)}</td>
                        <td class="${p.unrealized_pnl >= 0 ? 'positive' : 'negative'}">
                            $${p.unrealized_pnl.toFixed(2)}
                        </td>
                    </tr>
                `).join('');
            }
        }
        
        setInterval(updatePositions, 2000);
        updatePositions();
    </script>
</body>
</html>
        """
    
    async def start(self, host: str = "0.0.0.0", port: int = 8000):
        """Start dashboard server"""
        import uvicorn
        config = uvicorn.Config(self.app, host=host, port=port, log_level="info")
        server = uvicorn.Server(config)
        await server.serve()
