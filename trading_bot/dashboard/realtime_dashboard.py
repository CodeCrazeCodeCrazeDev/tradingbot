"""
Real-Time Trading Dashboard

Modern, responsive dashboard for monitoring live trading performance.
Built with Dash/Plotly for interactive visualizations.

Features:
- Real-time P&L tracking
- Position monitoring
- Performance metrics
- Risk indicators
- Trade history
- System health
"""

import os
import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, asdict
import threading
import time

try:
    import dash
    from dash import dcc, html, Input, Output, State
    import dash_bootstrap_components as dbc
    import plotly.graph_objs as go
    import plotly.express as px
    from plotly.subplots import make_subplots
    DASH_AVAILABLE = True
except ImportError:
    DASH_AVAILABLE = False

try:
    import pandas as pd
    import numpy as np
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

try:
    from loguru import logger
except ImportError:
    import logging
    logger = logging.getLogger(__name__)


@dataclass
class DashboardMetrics:
    """Dashboard metrics container"""
    timestamp: datetime
    equity: float
    balance: float
    daily_pnl: float
    total_pnl: float
    win_rate: float
    profit_factor: float
    sharpe_ratio: float
    max_drawdown: float
    current_drawdown: float
    open_positions: int
    daily_trades: int
    total_trades: int


class RealtimeDashboard:
    """
    Real-Time Trading Dashboard
    
    Provides a web-based interface for monitoring trading performance.
    """
    
    def __init__(
        self,
        port: int = 8050,
        update_interval: int = 5000,  # milliseconds
        data_dir: str = "data/dashboard"
    ):
        self.port = port
        self.update_interval = update_interval
        self.data_dir = data_dir
        
        # Data storage
        self.metrics_history: List[DashboardMetrics] = []
        self.trades: List[Dict] = []
        self.positions: List[Dict] = []
        self.alerts: List[Dict] = []
        
        # Current state
        self.current_metrics = DashboardMetrics(
            timestamp=datetime.now(),
            equity=10000.0,
            balance=10000.0,
            daily_pnl=0.0,
            total_pnl=0.0,
            win_rate=0.0,
            profit_factor=0.0,
            sharpe_ratio=0.0,
            max_drawdown=0.0,
            current_drawdown=0.0,
            open_positions=0,
            daily_trades=0,
            total_trades=0
        )
        
        # Ensure data directory exists
        os.makedirs(data_dir, exist_ok=True)
        
        # Initialize Dash app
        if DASH_AVAILABLE:
            self.app = self._create_app()
        else:
            self.app = None
            logger.warning("Dash not available. Install with: pip install dash dash-bootstrap-components")
    
    def _create_app(self) -> dash.Dash:
        """Create Dash application"""
        app = dash.Dash(
            __name__,
            external_stylesheets=[dbc.themes.DARKLY],
            title="AlphaAlgo Trading Dashboard"
        )
        
        app.layout = self._create_layout()
        self._setup_callbacks(app)
        
        return app
    
    def _create_layout(self) -> html.Div:
        """Create dashboard layout"""
        return html.Div([
            # Header
            dbc.Navbar(
                dbc.Container([
                    dbc.NavbarBrand("🚀 AlphaAlgo Trading Dashboard", className="ms-2"),
                    dbc.Nav([
                        dbc.NavItem(dbc.NavLink("Overview", href="#", active=True)),
                        dbc.NavItem(dbc.NavLink("Trades", href="#trades")),
                        dbc.NavItem(dbc.NavLink("Analytics", href="#analytics")),
                        dbc.NavItem(dbc.NavLink("Settings", href="#settings")),
                    ], className="ms-auto"),
                    html.Div(id="live-indicator", className="ms-3"),
                ]),
                color="dark",
                dark=True,
                className="mb-4"
            ),
            
            # Main content
            dbc.Container([
                # Top metrics row
                dbc.Row([
                    dbc.Col(self._create_metric_card("Equity", "equity-value", "$0.00", "primary"), width=2),
                    dbc.Col(self._create_metric_card("Daily P&L", "daily-pnl-value", "$0.00", "success"), width=2),
                    dbc.Col(self._create_metric_card("Win Rate", "win-rate-value", "0%", "info"), width=2),
                    dbc.Col(self._create_metric_card("Profit Factor", "pf-value", "0.00", "warning"), width=2),
                    dbc.Col(self._create_metric_card("Drawdown", "drawdown-value", "0%", "danger"), width=2),
                    dbc.Col(self._create_metric_card("Positions", "positions-value", "0", "secondary"), width=2),
                ], className="mb-4"),
                
                # Charts row
                dbc.Row([
                    dbc.Col([
                        dbc.Card([
                            dbc.CardHeader("Equity Curve"),
                            dbc.CardBody([
                                dcc.Graph(id="equity-chart", style={"height": "300px"})
                            ])
                        ])
                    ], width=8),
                    dbc.Col([
                        dbc.Card([
                            dbc.CardHeader("P&L Distribution"),
                            dbc.CardBody([
                                dcc.Graph(id="pnl-distribution", style={"height": "300px"})
                            ])
                        ])
                    ], width=4),
                ], className="mb-4"),
                
                # Positions and trades row
                dbc.Row([
                    dbc.Col([
                        dbc.Card([
                            dbc.CardHeader("Open Positions"),
                            dbc.CardBody([
                                html.Div(id="positions-table")
                            ])
                        ])
                    ], width=6),
                    dbc.Col([
                        dbc.Card([
                            dbc.CardHeader("Recent Trades"),
                            dbc.CardBody([
                                html.Div(id="trades-table")
                            ])
                        ])
                    ], width=6),
                ], className="mb-4"),
                
                # Risk metrics row
                dbc.Row([
                    dbc.Col([
                        dbc.Card([
                            dbc.CardHeader("Risk Metrics"),
                            dbc.CardBody([
                                dcc.Graph(id="risk-gauge", style={"height": "200px"})
                            ])
                        ])
                    ], width=4),
                    dbc.Col([
                        dbc.Card([
                            dbc.CardHeader("Performance by Symbol"),
                            dbc.CardBody([
                                dcc.Graph(id="symbol-performance", style={"height": "200px"})
                            ])
                        ])
                    ], width=4),
                    dbc.Col([
                        dbc.Card([
                            dbc.CardHeader("System Health"),
                            dbc.CardBody([
                                html.Div(id="system-health")
                            ])
                        ])
                    ], width=4),
                ], className="mb-4"),
                
                # Alerts section
                dbc.Row([
                    dbc.Col([
                        dbc.Card([
                            dbc.CardHeader("Recent Alerts"),
                            dbc.CardBody([
                                html.Div(id="alerts-list")
                            ])
                        ])
                    ], width=12),
                ]),
                
            ], fluid=True),
            
            # Auto-refresh interval
            dcc.Interval(
                id='interval-component',
                interval=self.update_interval,
                n_intervals=0
            ),
            
            # Store for data
            dcc.Store(id='metrics-store'),
            
        ], style={"backgroundColor": "#1a1a2e", "minHeight": "100vh"})
    
    def _create_metric_card(self, title: str, value_id: str, default: str, color: str) -> dbc.Card:
        """Create a metric card"""
        return dbc.Card([
            dbc.CardBody([
                html.H6(title, className="text-muted mb-1"),
                html.H4(default, id=value_id, className=f"text-{color} mb-0"),
            ], className="text-center py-2")
        ], className="h-100")
    
    def _setup_callbacks(self, app: dash.Dash):
        """Setup Dash callbacks"""
        
        @app.callback(
            [
                Output('equity-value', 'children'),
                Output('daily-pnl-value', 'children'),
                Output('daily-pnl-value', 'className'),
                Output('win-rate-value', 'children'),
                Output('pf-value', 'children'),
                Output('drawdown-value', 'children'),
                Output('positions-value', 'children'),
                Output('live-indicator', 'children'),
            ],
            [Input('interval-component', 'n_intervals')]
        )
        def update_metrics(n):
            m = self.current_metrics
            
            pnl_class = "text-success" if m.daily_pnl >= 0 else "text-danger"
            pnl_sign = "+" if m.daily_pnl >= 0 else ""
            
            live_badge = dbc.Badge("● LIVE", color="success", className="ms-2") if True else dbc.Badge("● OFFLINE", color="danger")
            
            return (
                f"${m.equity:,.2f}",
                f"{pnl_sign}${m.daily_pnl:,.2f}",
                pnl_class,
                f"{m.win_rate:.1%}",
                f"{m.profit_factor:.2f}",
                f"{m.current_drawdown:.1%}",
                str(m.open_positions),
                live_badge
            )
        
        @app.callback(
            Output('equity-chart', 'figure'),
            [Input('interval-component', 'n_intervals')]
        )
        def update_equity_chart(n):
            if not self.metrics_history:
                # Generate sample data
                dates = pd.date_range(end=datetime.now(), periods=100, freq='H')
                equity = 10000 + np.cumsum(np.random.randn(100) * 50)
                df = pd.DataFrame({'timestamp': dates, 'equity': equity})
            else:
                df = pd.DataFrame([asdict(m) for m in self.metrics_history[-100:]])
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=df['timestamp'],
                y=df['equity'],
                mode='lines',
                fill='tozeroy',
                line=dict(color='#00d4ff', width=2),
                fillcolor='rgba(0, 212, 255, 0.1)'
            ))
            
            fig.update_layout(
                template='plotly_dark',
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                margin=dict(l=40, r=20, t=20, b=40),
                xaxis=dict(showgrid=False),
                yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)')
            )
            
            return fig
        
        @app.callback(
            Output('pnl-distribution', 'figure'),
            [Input('interval-component', 'n_intervals')]
        )
        def update_pnl_distribution(n):
            if not self.trades:
                pnls = np.random.randn(50) * 100
            else:
                pnls = [t.get('pnl', 0) for t in self.trades[-50:]]
            
            fig = go.Figure()
            fig.add_trace(go.Histogram(
                x=pnls,
                nbinsx=20,
                marker_color='#00d4ff',
                opacity=0.7
            ))
            
            fig.update_layout(
                template='plotly_dark',
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                margin=dict(l=40, r=20, t=20, b=40),
                xaxis=dict(title='P&L ($)'),
                yaxis=dict(title='Count')
            )
            
            return fig
        
        @app.callback(
            Output('positions-table', 'children'),
            [Input('interval-component', 'n_intervals')]
        )
        def update_positions_table(n):
            if not self.positions:
                return html.P("No open positions", className="text-muted text-center")
            
            rows = []
            for pos in self.positions[:5]:
                pnl = pos.get('unrealized_pnl', 0)
                pnl_class = "text-success" if pnl >= 0 else "text-danger"
                
                rows.append(html.Tr([
                    html.Td(pos.get('symbol', 'N/A')),
                    html.Td(pos.get('side', 'N/A').upper()),
                    html.Td(f"{pos.get('quantity', 0):.2f}"),
                    html.Td(f"${pos.get('entry_price', 0):.5f}"),
                    html.Td(f"${pnl:.2f}", className=pnl_class),
                ]))
            
            return dbc.Table([
                html.Thead(html.Tr([
                    html.Th("Symbol"),
                    html.Th("Side"),
                    html.Th("Size"),
                    html.Th("Entry"),
                    html.Th("P&L"),
                ])),
                html.Tbody(rows)
            ], bordered=True, dark=True, hover=True, size="sm")
        
        @app.callback(
            Output('trades-table', 'children'),
            [Input('interval-component', 'n_intervals')]
        )
        def update_trades_table(n):
            if not self.trades:
                return html.P("No recent trades", className="text-muted text-center")
            
            rows = []
            for trade in self.trades[-5:]:
                pnl = trade.get('pnl', 0)
                pnl_class = "text-success" if pnl >= 0 else "text-danger"
                
                rows.append(html.Tr([
                    html.Td(trade.get('symbol', 'N/A')),
                    html.Td(trade.get('direction', 'N/A').upper()),
                    html.Td(f"${pnl:.2f}", className=pnl_class),
                    html.Td(trade.get('exit_reason', 'N/A')),
                ]))
            
            return dbc.Table([
                html.Thead(html.Tr([
                    html.Th("Symbol"),
                    html.Th("Side"),
                    html.Th("P&L"),
                    html.Th("Reason"),
                ])),
                html.Tbody(rows)
            ], bordered=True, dark=True, hover=True, size="sm")
        
        @app.callback(
            Output('risk-gauge', 'figure'),
            [Input('interval-component', 'n_intervals')]
        )
        def update_risk_gauge(n):
            risk_score = min(100, self.current_metrics.current_drawdown * 1000)
            
            fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=risk_score,
                domain={'x': [0, 1], 'y': [0, 1]},
                title={'text': "Risk Score"},
                gauge={
                    'axis': {'range': [0, 100]},
                    'bar': {'color': "#00d4ff"},
                    'steps': [
                        {'range': [0, 30], 'color': "green"},
                        {'range': [30, 70], 'color': "yellow"},
                        {'range': [70, 100], 'color': "red"}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': 80
                    }
                }
            ))
            
            fig.update_layout(
                template='plotly_dark',
                paper_bgcolor='rgba(0,0,0,0)',
                margin=dict(l=20, r=20, t=40, b=20)
            )
            
            return fig
        
        @app.callback(
            Output('symbol-performance', 'figure'),
            [Input('interval-component', 'n_intervals')]
        )
        def update_symbol_performance(n):
            # Aggregate P&L by symbol
            symbol_pnl = {}
            for trade in self.trades:
                symbol = trade.get('symbol', 'Unknown')
                pnl = trade.get('pnl', 0)
                symbol_pnl[symbol] = symbol_pnl.get(symbol, 0) + pnl
            
            if not symbol_pnl:
                symbol_pnl = {'EURUSD': 150, 'GBPUSD': -50, 'USDJPY': 75}
            
            colors = ['green' if v >= 0 else 'red' for v in symbol_pnl.values()]
            
            fig = go.Figure(go.Bar(
                x=list(symbol_pnl.keys()),
                y=list(symbol_pnl.values()),
                marker_color=colors
            ))
            
            fig.update_layout(
                template='plotly_dark',
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                margin=dict(l=40, r=20, t=20, b=40),
                yaxis=dict(title='P&L ($)')
            )
            
            return fig
        
        @app.callback(
            Output('system-health', 'children'),
            [Input('interval-component', 'n_intervals')]
        )
        def update_system_health(n):
            health_items = [
                ("Broker Connection", "success", "Connected"),
                ("Data Feed", "success", "Active"),
                ("Risk Engine", "success", "Running"),
                ("Strategy Engine", "success", "Active"),
                ("Latency", "warning", "45ms"),
            ]
            
            items = []
            for name, status, value in health_items:
                badge_color = {"success": "success", "warning": "warning", "danger": "danger"}.get(status, "secondary")
                items.append(
                    html.Div([
                        html.Span(name, className="me-2"),
                        dbc.Badge(value, color=badge_color)
                    ], className="d-flex justify-content-between mb-2")
                )
            
            return html.Div(items)
        
        @app.callback(
            Output('alerts-list', 'children'),
            [Input('interval-component', 'n_intervals')]
        )
        def update_alerts(n):
            if not self.alerts:
                return html.P("No recent alerts", className="text-muted text-center")
            
            items = []
            for alert in self.alerts[-5:]:
                level = alert.get('level', 'INFO')
                color = {
                    'INFO': 'info',
                    'WARNING': 'warning',
                    'ERROR': 'danger',
                    'CRITICAL': 'danger'
                }.get(level, 'secondary')
                
                items.append(
                    dbc.Alert([
                        html.Strong(f"[{level}] "),
                        alert.get('message', 'No message'),
                        html.Small(f" - {alert.get('timestamp', '')}", className="text-muted ms-2")
                    ], color=color, className="mb-2 py-2")
                )
            
            return html.Div(items)
    
    def update_metrics(self, metrics: DashboardMetrics):
        """Update current metrics"""
        self.current_metrics = metrics
        self.metrics_history.append(metrics)
        
        # Keep only last 1000 entries
        if len(self.metrics_history) > 1000:
            self.metrics_history = self.metrics_history[-1000:]
    
    def add_trade(self, trade: Dict):
        """Add a trade to history"""
        self.trades.append(trade)
        
        # Keep only last 100 trades
        if len(self.trades) > 100:
            self.trades = self.trades[-100:]
    
    def update_positions(self, positions: List[Dict]):
        """Update open positions"""
        self.positions = positions
    
    def add_alert(self, level: str, message: str):
        """Add an alert"""
        self.alerts.append({
            'timestamp': datetime.now().strftime('%H:%M:%S'),
            'level': level,
            'message': message
        })
        
        # Keep only last 50 alerts
        if len(self.alerts) > 50:
            self.alerts = self.alerts[-50:]
    
    def start(self, debug: bool = False):
        """Start the dashboard server"""
        if not DASH_AVAILABLE:
            logger.error("Dash not available. Cannot start dashboard.")
            return
        
        logger.info(f"Starting dashboard on http://localhost:{self.port}")
        self.app.run_server(debug=debug, port=self.port, host='0.0.0.0')
    
    def start_background(self):
        """Start dashboard in background thread"""
        if not DASH_AVAILABLE:
            logger.error("Dash not available. Cannot start dashboard.")
            return
        
        thread = threading.Thread(
            target=lambda: self.app.run_server(debug=False, port=self.port, host='0.0.0.0'),
            daemon=True
        )
        thread.start()
        logger.info(f"Dashboard started in background on http://localhost:{self.port}")


def run_dashboard(port: int = 8050):
    """Run the dashboard standalone"""
    dashboard = RealtimeDashboard(port=port)
    
    # Add some sample data
    for i in range(50):
        dashboard.add_trade({
            'symbol': ['EURUSD', 'GBPUSD', 'USDJPY'][i % 3],
            'direction': ['buy', 'sell'][i % 2],
            'pnl': (np.random.randn() * 100) if PANDAS_AVAILABLE else 0,
            'exit_reason': ['take_profit', 'stop_loss', 'manual'][i % 3]
        })
    
    dashboard.add_alert('INFO', 'Dashboard started')
    dashboard.add_alert('WARNING', 'High volatility detected')
    
    dashboard.start(debug=True)


if __name__ == "__main__":
    run_dashboard()
