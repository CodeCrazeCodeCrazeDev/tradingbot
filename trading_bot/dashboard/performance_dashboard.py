"""
from pathlib import Path
from typing import List, Optional, Set, Tuple
Real-time Performance Dashboard with Anomaly Detection
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Union, Tuple
import logging
import asyncio
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import threading
import queue
import json
import os
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetric:
    """Performance metric data"""
    name: str
    value: float
    timestamp: datetime
    category: str
    is_anomaly: bool = False
    anomaly_score: float = 0.0
    expected_range: Tuple[float, float] = field(default_factory=lambda: (0.0, 0.0))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'name': self.name,
            'value': self.value,
            'timestamp': self.timestamp.isoformat(),
            'category': self.category,
            'is_anomaly': self.is_anomaly,
            'anomaly_score': self.anomaly_score,
            'expected_range': self.expected_range
        }


class AnomalyDetector:
    """
    Anomaly detection for performance metrics
    
    Features:
    - Statistical anomaly detection
    - Z-score based outlier detection
    - Moving average deviation detection
    - Seasonal decomposition
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Anomaly detection parameters
        self.z_score_threshold = self.config.get('z_score_threshold', 3.0)
        self.ma_window = self.config.get('ma_window', 20)
        self.ma_std_threshold = self.config.get('ma_std_threshold', 2.5)
        self.min_history_points = self.config.get('min_history_points', 10)
        
        # Metric history
        self.metric_history = {}
        
        logger.info("Anomaly Detector initialized")
    
    def detect_anomalies(self, metrics: List[PerformanceMetric]) -> List[PerformanceMetric]:
        """
        Detect anomalies in performance metrics
        
        Args:
            metrics: List of performance metrics
            
        Returns:
            List of metrics with anomaly flags set
        """
        result = []
        
        for metric in metrics:
            # Update history
            if metric.name not in self.metric_history:
                self.metric_history[metric.name] = []
            
            # Check for anomaly
            is_anomaly, anomaly_score, expected_range = self._check_anomaly(metric)
            
            # Create updated metric
            updated_metric = PerformanceMetric(
                name=metric.name,
                value=metric.value,
                timestamp=metric.timestamp,
                category=metric.category,
                is_anomaly=is_anomaly,
                anomaly_score=anomaly_score,
                expected_range=expected_range
            )
            
            # Add to result
            result.append(updated_metric)
            
            # Update history (after anomaly detection)
            self.metric_history[metric.name].append(metric.value)
            
            # Keep history at reasonable size
            if len(self.metric_history[metric.name]) > 1000:
                self.metric_history[metric.name] = self.metric_history[metric.name][-1000:]
        
        return result
    
    def _check_anomaly(self, metric: PerformanceMetric) -> Tuple[bool, float, Tuple[float, float]]:
        """Check if a metric is anomalous"""
        history = self.metric_history.get(metric.name, [])
        
        # Not enough history
        if len(history) < self.min_history_points:
            return False, 0.0, (0.0, 0.0)
        
        # Z-score method
        mean = np.mean(history)
        std = np.std(history)
        
        if std > 0:
            z_score = abs((metric.value - mean) / std)
            is_anomaly = z_score > self.z_score_threshold
            anomaly_score = z_score / self.z_score_threshold
        else:
            z_score = 0
            is_anomaly = False
            anomaly_score = 0
        
        # Moving average method (if enough history)
        if len(history) >= self.ma_window:
            ma = np.mean(history[-self.ma_window:])
            ma_std = np.std(history[-self.ma_window:])
            
            if ma_std > 0:
                ma_z_score = abs((metric.value - ma) / ma_std)
                ma_is_anomaly = ma_z_score > self.ma_std_threshold
                ma_anomaly_score = ma_z_score / self.ma_std_threshold
                
                # Combine methods
                is_anomaly = is_anomaly or ma_is_anomaly
                anomaly_score = max(anomaly_score, ma_anomaly_score)
        
        # Calculate expected range
        expected_range = (
            mean - self.z_score_threshold * std,
            mean + self.z_score_threshold * std
        )
        
        return is_anomaly, anomaly_score, expected_range


class PerformanceDashboard:
    """
    Real-time performance dashboard with anomaly detection
    
    Features:
    - Real-time performance monitoring
    - Anomaly detection and alerting
    - Interactive visualizations
    - Key performance indicators
    - Historical performance tracking
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Initialize components
        self.anomaly_detector = AnomalyDetector(self.config.get('anomaly_detector', {}))
        
        # Dashboard parameters
        self.update_interval = self.config.get('update_interval', 5)  # seconds
        self.history_length = self.config.get('history_length', 1000)  # data points
        self.port = self.config.get('port', 8050)
        self.debug = self.config.get('debug', False)
        
        # Performance data
        self.metrics = {}
        self.alerts = []
        self.trades = []
        
        # Data queue for thread-safe updates
        self.data_queue = queue.Queue()
        
        # Dashboard app
        self.app = dash.Dash(__name__, suppress_callback_exceptions=True)
        self._setup_layout()
        self._setup_callbacks()
        
        # Dashboard server thread
        self.server_thread = None
        self.running = False
        
        logger.info("Performance Dashboard initialized")
    
    def _setup_layout(self):
        """Setup dashboard layout"""
        self.app.layout = html.Div([
            html.H1("Elite Trading Bot - Performance Dashboard", style={'textAlign': 'center'}),
            
            html.Div([
                html.Div([
                    html.H3("Trading Performance"),
                    dcc.Graph(id='equity-chart'),
                    dcc.Interval(id='interval-component', interval=self.update_interval * 1000)
                ], className='six columns'),
                
                html.Div([
                    html.H3("Key Metrics"),
                    html.Div(id='kpi-indicators'),
                    html.H4("Recent Alerts"),
                    html.Div(id='alerts-table')
                ], className='six columns')
            ], className='row'),
            
            html.Div([
                html.Div([
                    html.H3("Trade History"),
                    html.Div(id='trade-table')
                ], className='six columns'),
                
                html.Div([
                    html.H3("Performance Metrics"),
                    dcc.Dropdown(
                        id='metric-dropdown',
                        options=[],
                        value=None,
                        placeholder="Select a metric"
                    ),
                    dcc.Graph(id='metric-chart')
                ], className='six columns')
            ], className='row')
        ])
    
    def _setup_callbacks(self):
        """Setup dashboard callbacks"""
        # Update equity chart
        @self.app.callback(
            Output('equity-chart', 'figure'),
            Input('interval-component', 'n_intervals')
        )
        def update_equity_chart(_):
            # Process any pending data updates
            self._process_queue()
            
            # Get equity curve data
            equity_data = self._get_metric_history('equity')
            drawdown_data = self._get_metric_history('drawdown')
            
            if not equity_data:
                # No data yet
                return go.Figure()
            
            # Create figure with secondary y-axis
            fig = make_subplots(specs=[[{"secondary_y": True}]])
            
            # Add equity curve
            fig.add_trace(
                go.Scatter(
                    x=[d['timestamp'] for d in equity_data],
                    y=[d['value'] for d in equity_data],
                    name="Equity",
                    line=dict(color='blue')
                ),
                secondary_y=False
            )
            
            # Add drawdown if available
            if drawdown_data:
                fig.add_trace(
                    go.Scatter(
                        x=[d['timestamp'] for d in drawdown_data],
                        y=[d['value'] * 100 for d in drawdown_data],  # Convert to percentage
                        name="Drawdown %",
                        line=dict(color='red')
                    ),
                    secondary_y=True
                )
            
            # Set titles
            fig.update_layout(
                title_text="Equity Curve and Drawdown",
                xaxis_title="Time",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            fig.update_yaxes(title_text="Equity", secondary_y=False)
            fig.update_yaxes(title_text="Drawdown %", secondary_y=True)
            
            return fig
        
        # Update KPI indicators
        @self.app.callback(
            Output('kpi-indicators', 'children'),
            Input('interval-component', 'n_intervals')
        )
        def update_kpi_indicators(_):
            # Get latest KPI values
            kpis = self._get_latest_kpis()
            
            # Create KPI cards
            kpi_cards = []
            for kpi in kpis:
                color = 'green' if kpi['value'] >= 0 else 'red'
                if kpi['name'] in ['drawdown', 'volatility']:
                    color = 'red' if kpi['value'] >= 0.1 else 'orange' if kpi['value'] >= 0.05 else 'green'
                
                card = html.Div([
                    html.H4(kpi['name'].title()),
                    html.P(f"{kpi['value']:.2f}", style={'color': color, 'fontSize': 24})
                ], style={'textAlign': 'center', 'border': '1px solid #ddd', 'padding': '10px', 'margin': '5px'})
                
                kpi_cards.append(card)
            
            return html.Div(kpi_cards, style={'display': 'flex', 'flexWrap': 'wrap'})
        
        # Update alerts table
        @self.app.callback(
            Output('alerts-table', 'children'),
            Input('interval-component', 'n_intervals')
        )
        def update_alerts_table(_):
            # Get recent alerts
            alerts = self.alerts[-10:]  # Last 10 alerts
            
            if not alerts:
                return html.P("No alerts")
            
            # Create table
            rows = []
            for alert in reversed(alerts):  # Most recent first
                row = html.Tr([
                    html.Td(alert['timestamp'].strftime('%H:%M:%S')),
                    html.Td(alert['metric']),
                    html.Td(f"{alert['value']:.2f}"),
                    html.Td(alert['message'])
                ])
                rows.append(row)
            
            table = html.Table([
                html.Thead(html.Tr([
                    html.Th("Time"), html.Th("Metric"), html.Th("Value"), html.Th("Message")
                ])),
                html.Tbody(rows)
            ], style={'width': '100%'})
            
            return table
        
        # Update trade table
        @self.app.callback(
            Output('trade-table', 'children'),
            Input('interval-component', 'n_intervals')
        )
        def update_trade_table(_):
            # Get recent trades
            trades = self.trades[-10:]  # Last 10 trades
            
            if not trades:
                return html.P("No trades")
            
            # Create table
            rows = []
            for trade in reversed(trades):  # Most recent first
                color = 'green' if trade['profit'] > 0 else 'red'
                row = html.Tr([
                    html.Td(trade['timestamp'].strftime('%H:%M:%S')),
                    html.Td(trade['symbol']),
                    html.Td(trade['direction']),
                    html.Td(f"{trade['profit']:.2f}", style={'color': color})
                ])
                rows.append(row)
            
            table = html.Table([
                html.Thead(html.Tr([
                    html.Th("Time"), html.Th("Symbol"), html.Th("Direction"), html.Th("Profit")
                ])),
                html.Tbody(rows)
            ], style={'width': '100%'})
            
            return table
        
        # Update metric dropdown options
        @self.app.callback(
            Output('metric-dropdown', 'options'),
            Input('interval-component', 'n_intervals')
        )
        def update_metric_dropdown(_):
            # Get available metrics
            metrics = list(self.metrics.keys())
            return [{'label': m.title(), 'value': m} for m in metrics]
        
        # Update metric chart
        @self.app.callback(
            Output('metric-chart', 'figure'),
            [Input('metric-dropdown', 'value'),
             Input('interval-component', 'n_intervals')]
        )
        def update_metric_chart(metric_name, _):
            if not metric_name or metric_name not in self.metrics:
                return go.Figure()
            
            # Get metric history
            metric_data = self._get_metric_history(metric_name)
            
            if not metric_data:
                return go.Figure()
            
            # Create figure
            fig = go.Figure()
            
            # Add metric line
            fig.add_trace(go.Scatter(
                x=[d['timestamp'] for d in metric_data],
                y=[d['value'] for d in metric_data],
                name=metric_name.title(),
                line=dict(color='blue')
            ))
            
            # Add anomaly points
            anomaly_timestamps = []
            anomaly_values = []
            
            for d in metric_data:
                if d.get('is_anomaly', False):
                    anomaly_timestamps.append(d['timestamp'])
                    anomaly_values.append(d['value'])
            
            if anomaly_timestamps:
                fig.add_trace(go.Scatter(
                    x=anomaly_timestamps,
                    y=anomaly_values,
                    mode='markers',
                    name='Anomalies',
                    marker=dict(color='red', size=10)
                ))
            
            # Set titles
            fig.update_layout(
                title_text=f"{metric_name.title()} Over Time",
                xaxis_title="Time",
                yaxis_title=metric_name.title()
            )
            
            return fig
    
    def start(self):
        """Start the dashboard server"""
        if self.running:
            logger.warning("Dashboard already running")
            return
        
        self.running = True
        
        # Start server in a separate thread
        self.server_thread = threading.Thread(target=self._run_server)
        self.server_thread.daemon = True
        self.server_thread.start()
        
        logger.info(f"Dashboard started on port {self.port}")
    
    def stop(self):
        """Stop the dashboard server"""
        self.running = False
        logger.info("Dashboard stopped")
    
    def _run_server(self):
        """Run the dashboard server"""
        self.app.run_server(debug=self.debug, port=self.port, use_reloader=False)
    
    def update_metric(self, name: str, value: float, category: str = 'general'):
        """
        Update a performance metric
        
        Args:
            name: Metric name
            value: Metric value
            category: Metric category
        """
        # Create metric object
        metric = PerformanceMetric(
            name=name,
            value=value,
            timestamp=datetime.now(),
            category=category
        )
        
        # Add to queue for thread-safe update
        self.data_queue.put(('metric', metric))
    
    def add_trade(self, trade: Dict[str, Any]):
        """
        Add a trade to the dashboard
        
        Args:
            trade: Trade information
        """
        # Ensure timestamp
        if 'timestamp' not in trade:
            trade['timestamp'] = datetime.now()
        
        # Add to queue for thread-safe update
        self.data_queue.put(('trade', trade))
    
    def _process_queue(self):
        """Process data queue"""
        while not self.data_queue.empty():
            try:
                data_type, data = self.data_queue.get_nowait()
                
                if data_type == 'metric':
                    self._process_metric(data)
                elif data_type == 'trade':
                    self._process_trade(data)
                
                self.data_queue.task_done()
            except queue.Empty:
                break
    
    def _process_metric(self, metric: PerformanceMetric):
        """Process a new metric"""
        # Initialize metric history if needed
        if metric.name not in self.metrics:
            self.metrics[metric.name] = []
        
        # Check for anomalies
        updated_metrics = self.anomaly_detector.detect_anomalies([metric])
        updated_metric = updated_metrics[0]
        
        # Add to history
        self.metrics[metric.name].append(updated_metric.to_dict())
        
        # Limit history length
        if len(self.metrics[metric.name]) > self.history_length:
            self.metrics[metric.name] = self.metrics[metric.name][-self.history_length:]
        
        # Check for alerts
        if updated_metric.is_anomaly:
            alert = {
                'timestamp': updated_metric.timestamp,
                'metric': updated_metric.name,
                'value': updated_metric.value,
                'message': f"Anomaly detected: {updated_metric.name} = {updated_metric.value:.2f}"
            }
            self.alerts.append(alert)
            
            # Limit alerts history
            if len(self.alerts) > 100:
                self.alerts = self.alerts[-100:]
            
            logger.warning(f"Anomaly detected: {updated_metric.name} = {updated_metric.value:.2f}")
    
    def _process_trade(self, trade: Dict[str, Any]):
        """Process a new trade"""
        # Add to trade history
        self.trades.append(trade)
        
        # Limit trade history
        if len(self.trades) > 1000:
            self.trades = self.trades[-1000:]
        
        # Update metrics based on trade
        self.update_metric('trade_count', len(self.trades), 'trading')
        
        # Calculate win rate
        wins = sum(1 for t in self.trades if t.get('profit', 0) > 0)
        win_rate = wins / len(self.trades) if self.trades else 0
        self.update_metric('win_rate', win_rate, 'trading')
        
        # Calculate profit factor
        gross_profit = sum(t.get('profit', 0) for t in self.trades if t.get('profit', 0) > 0)
        gross_loss = abs(sum(t.get('profit', 0) for t in self.trades if t.get('profit', 0) < 0))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
        self.update_metric('profit_factor', profit_factor, 'trading')
    
    def _get_metric_history(self, name: str) -> List[Dict[str, Any]]:
        """Get history for a specific metric"""
        return self.metrics.get(name, [])
    
    def _get_latest_kpis(self) -> List[Dict[str, Any]]:
        """Get latest values for key performance indicators"""
        kpis = []
        
        # Define key metrics
        key_metrics = ['equity', 'drawdown', 'win_rate', 'profit_factor', 'sharpe_ratio', 'volatility']
        
        for metric in key_metrics:
            history = self._get_metric_history(metric)
            if history:
                kpis.append({
                    'name': metric,
                    'value': history[-1]['value']
                })
        
        return kpis
    
    def save_metrics(self, file_path: str):
        """
        Save metrics to a file
        
        Args:
            file_path: Path to save metrics
        """
        data = {
            'metrics': self.metrics,
            'trades': [t for t in self.trades if isinstance(t.get('timestamp'), str) or 
                      isinstance(t.get('timestamp'), datetime)]
        }
        
        # Convert datetime objects to strings
        for metric_name, metric_data in data['metrics'].items():
            for item in metric_data:
                if isinstance(item.get('timestamp'), datetime):
                    item['timestamp'] = item['timestamp'].isoformat()
        
        for trade in data['trades']:
            pass
        try:
            if isinstance(trade.get('timestamp'), datetime):
                trade['timestamp'] = trade['timestamp'].isoformat()
        
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2)
            logger.info(f"Metrics saved to {file_path}")
        except Exception as e:
            logger.error(f"Error saving metrics: {e}")
    
    def load_metrics(self, file_path: str):
        """
        Load metrics from a file
        
        Args:
            file_path: Path to load metrics from
        """
        if not os.path.exists(file_path):
            logger.warning(f"Metrics file not found: {file_path}")
            return
        try:
        
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            # Convert string timestamps to datetime
            for metric_name, metric_data in data.get('metrics', {}).items():
                for item in metric_data:
                    if isinstance(item.get('timestamp'), str):
                        item['timestamp'] = datetime.fromisoformat(item['timestamp'])
            
            for trade in data.get('trades', []):
                if isinstance(trade.get('timestamp'), str):
                    trade['timestamp'] = datetime.fromisoformat(trade['timestamp'])
            
            self.metrics = data.get('metrics', {})
            self.trades = data.get('trades', [])
            
            logger.info(f"Metrics loaded from {file_path}")
        except Exception as e:
            logger.error(f"Error loading metrics: {e}")


# Example usage
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Create dashboard
    dashboard = PerformanceDashboard()
    
    # Start dashboard
    dashboard.start()
    
    # Simulate updating metrics
    import time
    import random
    
    # Initial equity
    equity = 10000.0
    
    try:
        for i in range(100):
            # Update equity
            change = random.normalvariate(0, 100)
            equity += change
            
            # Calculate drawdown
            max_equity = equity * 1.1  # Simulate max equity
            drawdown = (max_equity - equity) / max_equity
            
            # Update metrics
            dashboard.update_metric('equity', equity, 'trading')
            dashboard.update_metric('drawdown', drawdown, 'risk')
            dashboard.update_metric('win_rate', 0.55 + random.normalvariate(0, 0.02), 'trading')
            dashboard.update_metric('profit_factor', 1.5 + random.normalvariate(0, 0.1), 'trading')
            dashboard.update_metric('sharpe_ratio', 1.2 + random.normalvariate(0, 0.05), 'risk')
            dashboard.update_metric('volatility', 0.08 + random.normalvariate(0, 0.01), 'risk')
            
            # Simulate a trade every 5 iterations
            if i % 5 == 0:
                profit = random.normalvariate(50, 100)
                dashboard.add_trade({
                    'timestamp': datetime.now(),
                    'symbol': random.choice(['AAPL', 'MSFT', 'GOOGL', 'AMZN']),
                    'direction': random.choice(['BUY', 'SELL']),
                    'profit': profit,
                    'size': random.randint(1, 10) * 100
                })
            
            # Add anomaly occasionally
            if random.random() < 0.1:
                dashboard.update_metric('latency', random.uniform(100, 500), 'system')
            else:
                dashboard.update_metric('latency', random.uniform(10, 50), 'system')
            
            time.sleep(1)
    
    except KeyboardInterrupt:
        logger.info("Stopping dashboard...")
    
    finally:
        # Save metrics
        dashboard.save_metrics('dashboard_metrics.json')
        
        # Stop dashboard
        dashboard.stop()
