"""
Survival Dashboard

This module implements a real-time dashboard for monitoring the Survival System.
"""

import os
import logging
import asyncio
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import numpy as np
try:
    from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends, Security
except ImportError:
    fastapi = None
from fastapi.security import APIKeyHeader
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
try:
    import uvicorn
except ImportError:
    uvicorn = None
from typing import Set
from enum import auto
import numpy
import pandas

# Dashboard models
class SystemStatus(BaseModel):
    running: bool
    paused: bool
    emergency_shutdown: bool
    error_count: int
    uptime: float
    last_error_time: Optional[str] = None

class ComponentStatus(BaseModel):
    status: str
    last_update: str
    details: Dict[str, Any] = {}

class PortfolioStatus(BaseModel):
    account_balance: float
    equity: float
    margin: float
    free_margin: float
    margin_level: float
    daily_pnl: float
    total_pnl: float
    drawdown: float
    positions: List[Dict[str, Any]] = []

class RiskMetrics(BaseModel):
    var_95: float
    var_99: float
    expected_shortfall: float
    sharpe_ratio: float
    sortino_ratio: float
    max_drawdown: float
    current_drawdown: float
    correlation_matrix: Dict[str, Dict[str, float]] = {}

class DashboardData(BaseModel):
    system: SystemStatus
    components: Dict[str, ComponentStatus] = {}
    portfolio: PortfolioStatus
    risk_metrics: RiskMetrics
    alerts: List[Dict[str, Any]] = []
    performance_metrics: Dict[str, Any] = {}


class SurvivalDashboard:
    """Real-time dashboard for monitoring the Survival System"""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the dashboard"""
        self.logger = logging.getLogger(self.__class__.__name__)
        self.config = config
        self.dashboard_config = config.get('dashboard', {})
        
        # Initialize FastAPI
        self.app = FastAPI(
            title="Elite Trading Bot - Survival System Dashboard",
            description="Real-time monitoring dashboard for the Survival System",
            version="1.0.0"
        )
        
        # Set up API key security
        self.api_key_header = APIKeyHeader(name="X-API-Key")
        self.api_keys = self.dashboard_config.get('api_keys', ["default_key"])
        
        # Initialize data storage
        self.system_status = {}
        self.component_status = {}
        self.portfolio_status = {}
        self.risk_metrics = {}
        self.alerts = []
        self.performance_metrics = {}
        
        # Initialize WebSocket connections
        self.active_connections: List[WebSocket] = []
        
        # Set up routes
        self._setup_routes()
        
        # Set up static files
        dashboard_path = Path(self.dashboard_config.get('static_files_path', 'dashboard/static'))
        if dashboard_path.exists():
            self.app.mount("/static", StaticFiles(directory=str(dashboard_path)), name="static")
    
    def _setup_routes(self):
        """Set up API routes"""
        
        @self.app.get("/", response_class=HTMLResponse)
        async def get_dashboard():
            """Serve the dashboard HTML"""
            try:
                dashboard_path = Path(self.dashboard_config.get('index_path', 'dashboard/static/index.html'))
                if dashboard_path.exists():
                    with open(dashboard_path, 'r') as f:
                        return f.read()
                else:
                    return """
                    <!DOCTYPE html>
                    <html>
                    <head>
                        <title>Elite Trading Bot - Survival System Dashboard</title>
                        <meta charset="UTF-8">
                        <meta name="viewport" content="width=device-width, initial-scale=1.0">
                        <script src="https://cdn.tailwindcss.com"></script>
                        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
                    </head>
                    <body class="bg-gray-100">
                        <div class="container mx-auto px-4 py-8">
                            <h1 class="text-3xl font-bold mb-8">Elite Trading Bot - Survival System Dashboard</h1>
                            
                            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                                <!-- System Status -->
                                <div class="bg-white p-6 rounded-lg shadow-md">
                                    <h2 class="text-xl font-semibold mb-4">System Status</h2>
                                    <div id="system-status">Loading...</div>
                                </div>
                                
                                <!-- Portfolio Status -->
                                <div class="bg-white p-6 rounded-lg shadow-md">
                                    <h2 class="text-xl font-semibold mb-4">Portfolio</h2>
                                    <div id="portfolio-status">Loading...</div>
                                </div>
                                
                                <!-- Risk Metrics -->
                                <div class="bg-white p-6 rounded-lg shadow-md">
                                    <h2 class="text-xl font-semibold mb-4">Risk Metrics</h2>
                                    <div id="risk-metrics">Loading...</div>
                                </div>
                                
                                <!-- Component Status -->
                                <div class="bg-white p-6 rounded-lg shadow-md col-span-1 md:col-span-2">
                                    <h2 class="text-xl font-semibold mb-4">Components</h2>
                                    <div id="component-status">Loading...</div>
                                </div>
                                
                                <!-- Alerts -->
                                <div class="bg-white p-6 rounded-lg shadow-md">
                                    <h2 class="text-xl font-semibold mb-4">Alerts</h2>
                                    <div id="alerts">Loading...</div>
                                </div>
                                
                                <!-- Performance Chart -->
                                <div class="bg-white p-6 rounded-lg shadow-md col-span-1 md:col-span-2">
                                    <h2 class="text-xl font-semibold mb-4">Performance</h2>
                                    <canvas id="performance-chart"></canvas>
                                </div>
                            </div>
                        </div>
                        
                        <script>
                            // WebSocket connection
                            const socket = new WebSocket(`ws://${window.location.host}/ws`);
                            
                            socket.onmessage = function(event) {
                                const data = JSON.parse(event.data);
                                updateDashboard(data);
                            };
                            
                            socket.onclose = function(event) {
                                console.log('Connection closed');
                                setTimeout(() => {
                                    window.location.reload();
                                }, 5000);
                            };
                            
                            function updateDashboard(data) {
                                // Update system status
                                document.getElementById('system-status').innerHTML = renderSystemStatus(data.system);
                                
                                // Update portfolio status
                                document.getElementById('portfolio-status').innerHTML = renderPortfolioStatus(data.portfolio);
                                
                                // Update risk metrics
                                document.getElementById('risk-metrics').innerHTML = renderRiskMetrics(data.risk_metrics);
                                
                                // Update component status
                                document.getElementById('component-status').innerHTML = renderComponentStatus(data.components);
                                
                                // Update alerts
                                document.getElementById('alerts').innerHTML = renderAlerts(data.alerts);
                                
                                // Update performance chart
                                updatePerformanceChart(data.performance_metrics);
                            }
                            
                            function renderSystemStatus(system) {
                                const statusClass = system.running ? 'text-green-500' : 'text-red-500';
                                const statusText = system.running ? 'Running' : 'Stopped';
                                
                                return `
                                    <div class="grid grid-cols-2 gap-2">
                                        <div class="font-semibold">Status:</div>
                                        <div class="${statusClass}">${statusText}</div>
                                        
                                        <div class="font-semibold">Paused:</div>
                                        <div>${system.paused ? 'Yes' : 'No'}</div>
                                        
                                        <div class="font-semibold">Emergency:</div>
                                        <div>${system.emergency_shutdown ? 'Yes' : 'No'}</div>
                                        
                                        <div class="font-semibold">Errors:</div>
                                        <div>${system.error_count}</div>
                                        
                                        <div class="font-semibold">Uptime:</div>
                                        <div>${formatUptime(system.uptime)}</div>
                                    </div>
                                `;
                            }
                            
                            function renderPortfolioStatus(portfolio) {
                                return `
                                    <div class="grid grid-cols-2 gap-2">
                                        <div class="font-semibold">Balance:</div>
                                        <div>$${portfolio.account_balance.toFixed(2)}</div>
                                        
                                        <div class="font-semibold">Equity:</div>
                                        <div>$${portfolio.equity.toFixed(2)}</div>
                                        
                                        <div class="font-semibold">Daily P&L:</div>
                                        <div class="${portfolio.daily_pnl >= 0 ? 'text-green-500' : 'text-red-500'}">
                                            $${portfolio.daily_pnl.toFixed(2)}
                                        </div>
                                        
                                        <div class="font-semibold">Total P&L:</div>
                                        <div class="${portfolio.total_pnl >= 0 ? 'text-green-500' : 'text-red-500'}">
                                            $${portfolio.total_pnl.toFixed(2)}
                                        </div>
                                        
                                        <div class="font-semibold">Drawdown:</div>
                                        <div>${(portfolio.drawdown * 100).toFixed(2)}%</div>
                                        
                                        <div class="font-semibold">Positions:</div>
                                        <div>${portfolio.positions.length}</div>
                                    </div>
                                `;
                            }
                            
                            function renderRiskMetrics(metrics) {
                                return `
                                    <div class="grid grid-cols-2 gap-2">
                                        <div class="font-semibold">VaR (95%):</div>
                                        <div>${(metrics.var_95 * 100).toFixed(2)}%</div>
                                        
                                        <div class="font-semibold">VaR (99%):</div>
                                        <div>${(metrics.var_99 * 100).toFixed(2)}%</div>
                                        
                                        <div class="font-semibold">Expected Shortfall:</div>
                                        <div>${(metrics.expected_shortfall * 100).toFixed(2)}%</div>
                                        
                                        <div class="font-semibold">Sharpe Ratio:</div>
                                        <div>${metrics.sharpe_ratio.toFixed(2)}</div>
                                        
                                        <div class="font-semibold">Sortino Ratio:</div>
                                        <div>${metrics.sortino_ratio.toFixed(2)}</div>
                                        
                                        <div class="font-semibold">Max Drawdown:</div>
                                        <div>${(metrics.max_drawdown * 100).toFixed(2)}%</div>
                                    </div>
                                `;
                            }
                            
                            function renderComponentStatus(components) {
                                let html = '<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">';
                                
                                for (const [name, component] of Object.entries(components)) {
                                    const statusClass = getStatusClass(component.status);
                                    
                                    html += `
                                        <div class="border rounded p-3">
                                            <div class="font-semibold">${name}</div>
                                            <div class="${statusClass}">${component.status}</div>
                                            <div class="text-xs text-gray-500">${component.last_update}</div>
                                        </div>
                                    `;
                                }
                                
                                html += '</div>';
                                return html;
                            }
                            
                            function renderAlerts(alerts) {
                                if (alerts.length === 0) {
                                    return '<div class="text-gray-500">No alerts</div>';
                                }
                                
                                let html = '<div class="space-y-2 max-h-60 overflow-y-auto">';
                                
                                for (const alert of alerts.slice(0, 10)) {
                                    const levelClass = getLevelClass(alert.level);
                                    
                                    html += `
                                        <div class="border-l-4 ${levelClass} pl-2 py-1">
                                            <div class="font-semibold">${alert.title}</div>
                                            <div>${alert.message}</div>
                                            <div class="text-xs text-gray-500">${alert.timestamp}</div>
                                        </div>
                                    `;
                                }
                                
                                html += '</div>';
                                return html;
                            }
                            
                            let performanceChart = null;
                            
                            function updatePerformanceChart(metrics) {
                                if (!metrics.equity_curve) return;
                                
                                const ctx = document.getElementById('performance-chart').getContext('2d');
                                
                                if (performanceChart) {
                                    performanceChart.data.labels = metrics.equity_curve.labels;
                                    performanceChart.data.datasets[0].data = metrics.equity_curve.equity;
                                    performanceChart.data.datasets[1].data = metrics.equity_curve.drawdown;
                                    performanceChart.update();
                                } else {
                                    performanceChart = new Chart(ctx, {
                                        type: 'line',
                                        data: {
                                            labels: metrics.equity_curve.labels,
                                            datasets: [
                                                {
                                                    label: 'Equity',
                                                    data: metrics.equity_curve.equity,
                                                    borderColor: 'rgb(59, 130, 246)',
                                                    backgroundColor: 'rgba(59, 130, 246, 0.1)',
                                                    fill: true,
                                                    tension: 0.1
                                                },
                                                {
                                                    label: 'Drawdown',
                                                    data: metrics.equity_curve.drawdown,
                                                    borderColor: 'rgb(239, 68, 68)',
                                                    backgroundColor: 'rgba(239, 68, 68, 0.1)',
                                                    fill: true,
                                                    tension: 0.1,
                                                    yAxisID: 'y1'
                                                }
                                            ]
                                        },
                                        options: {
                                            responsive: true,
                                            scales: {
                                                y: {
                                                    beginAtZero: false,
                                                    title: {
                                                        display: true,
                                                        text: 'Equity'
                                                    }
                                                },
                                                y1: {
                                                    beginAtZero: true,
                                                    position: 'right',
                                                    grid: {
                                                        drawOnChartArea: false
                                                    },
                                                    title: {
                                                        display: true,
                                                        text: 'Drawdown %'
                                                    },
                                                    ticks: {
                                                        callback: function(value) {
                                                            return value + '%';
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                    });
                                }
                            }
                            
                            function formatUptime(seconds) {
                                const days = Math.floor(seconds / 86400);
                                const hours = Math.floor((seconds % 86400) / 3600);
                                const minutes = Math.floor((seconds % 3600) / 60);
                                const secs = Math.floor(seconds % 60);
                                
                                if (days > 0) {
                                    return `${days}d ${hours}h ${minutes}m`;
                                } else if (hours > 0) {
                                    return `${hours}h ${minutes}m ${secs}s`;
                                } else if (minutes > 0) {
                                    return `${minutes}m ${secs}s`;
                                } else {
                                    return `${secs}s`;
                                }
                            }
                            
                            function getStatusClass(status) {
                                switch (status.toLowerCase()) {
                                    case 'ok':
                                        return 'text-green-500';
                                    case 'warning':
                                        return 'text-yellow-500';
                                    case 'error':
                                        return 'text-red-500';
                                    default:
                                        return 'text-gray-500';
                                }
                            }
                            
                            function getLevelClass(level) {
                                switch (level.toLowerCase()) {
                                    case 'info':
                                        return 'border-blue-500';
                                    case 'warning':
                                        return 'border-yellow-500';
                                    case 'error':
                                        return 'border-red-500';
                                    case 'critical':
                                        return 'border-purple-500';
                                    default:
                                        return 'border-gray-500';
                                }
                            }
                        </script>
                    </body>
                    </html>
                    """
            except Exception as e:
                self.logger.exception(f"Error serving dashboard HTML: {e}")
                return HTMLResponse(content="<h1>Error loading dashboard</h1><p>" + str(e) + "</p>")
        
        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            await websocket.accept()
            self.active_connections.append(websocket)
            try:
                # Send initial data
                await self.send_dashboard_data(websocket)
                
                # Keep connection alive
                while True:
                    await websocket.receive_text()
                    
            except WebSocketDisconnect:
                self.active_connections.remove(websocket)
            except Exception as e:
                self.logger.exception(f"WebSocket error: {e}")
                if websocket in self.active_connections:
                    self.active_connections.remove(websocket)
        
        async def verify_api_key(api_key: str = Security(self.api_key_header)):
            if api_key not in self.api_keys:
                raise HTTPException(
                    status_code=403,
                    detail="Invalid API Key"
                )
            return api_key
        
        @self.app.get("/api/status", response_model=DashboardData)
        async def get_status(api_key: str = Depends(verify_api_key)):
            """Get current system status"""
            return self.get_dashboard_data()
        
        @self.app.post("/api/emergency/stop")
        async def emergency_stop(api_key: str = Depends(verify_api_key)):
            """Trigger emergency stop"""
            # This will be handled by the survival core
            return {"status": "emergency_stop_triggered"}
        
        @self.app.post("/api/trading/pause")
        async def pause_trading(api_key: str = Depends(verify_api_key)):
            """Pause trading"""
            # This will be handled by the survival core
            return {"status": "trading_paused"}
        
        @self.app.post("/api/trading/resume")
        async def resume_trading(api_key: str = Depends(verify_api_key)):
            """Resume trading"""
            # This will be handled by the survival core
            return {"status": "trading_resumed"}
    
    async def start(self, host: str = "0.0.0.0", port: int = 8000):
        """Start the dashboard server"""
        config = uvicorn.Config(
            app=self.app,
            host=host,
            port=port,
            log_level="info"
        )
        server = uvicorn.Server(config)
        await server.serve()
    
    async def update_system_status(self, status: Dict[str, Any]):
        """Update system status"""
        self.system_status = status
        await self.broadcast_dashboard_data()
    
    async def update_component_status(self, component: str, status: str, details: Dict[str, Any]):
        """Update component status"""
        self.component_status[component] = {
            "status": status,
            "last_update": datetime.now().isoformat(),
            "details": details
        }
        await self.broadcast_dashboard_data()
    
    async def update_portfolio_status(self, status: Dict[str, Any]):
        """Update portfolio status"""
        self.portfolio_status = status
        await self.broadcast_dashboard_data()
    
    async def update_risk_metrics(self, metrics: Dict[str, Any]):
        """Update risk metrics"""
        self.risk_metrics = metrics
        await self.broadcast_dashboard_data()
    
    async def add_alert(self, title: str, message: str, level: str = "info"):
        """Add an alert to the dashboard"""
        self.alerts.append({
            "title": title,
            "message": message,
            "level": level,
            "timestamp": datetime.now().isoformat()
        })
        
        # Keep only the latest 100 alerts
        if len(self.alerts) > 100:
            self.alerts = self.alerts[-100:]
        
        await self.broadcast_dashboard_data()
    
    async def update_performance_metrics(self, metrics: Dict[str, Any]):
        """Update performance metrics"""
        self.performance_metrics = metrics
        await self.broadcast_dashboard_data()
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get current dashboard data"""
        return {
            "system": self.system_status,
            "components": self.component_status,
            "portfolio": self.portfolio_status,
            "risk_metrics": self.risk_metrics,
            "alerts": self.alerts,
            "performance_metrics": self.performance_metrics
        }
    
    async def send_dashboard_data(self, websocket: WebSocket):
        """Send dashboard data to a specific WebSocket connection"""
        try:
            await websocket.send_json(self.get_dashboard_data())
        except Exception as e:
            self.logger.exception(f"Error sending dashboard data: {e}")
    
    async def broadcast_dashboard_data(self):
        """Broadcast dashboard data to all connected clients"""
        if not self.active_connections:
            return
        
        data = self.get_dashboard_data()
        for connection in self.active_connections:
            try:
                await connection.send_json(data)
            except Exception as e:
                self.logger.exception(f"Error broadcasting dashboard data: {e}")
                # Remove failed connection
                if connection in self.active_connections:
                    self.active_connections.remove(connection)
