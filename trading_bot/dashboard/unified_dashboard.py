"""
Unified Dashboard for Multi-Exchange Trading
Provides a comprehensive dashboard for monitoring multiple exchanges
"""

try:
    import dash
except ImportError:
    dash = None

try:
    from dash import dcc, html, callback, Input, Output, State
except ImportError:
    dash = None
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import threading
import time
import logging
import asyncio
from typing import Dict, List, Any, Optional

# Import connectors
from trading_bot.connectors.binance_connector import BinanceConnector
from trading_bot.connectors.mt5_connector import MT5Connector
from typing import Set
from enum import auto
import numpy
import pandas

logger = logging.getLogger(__name__)


class UnifiedDashboard:
    """
    Unified Dashboard for Multi-Exchange Trading
    
    Features:
    - Real-time price monitoring across exchanges
    - Portfolio performance tracking
    - Trade history visualization
    - Strategy performance metrics
    - Market analysis indicators
    """
    
    def __init__(self, config: Dict = None):
        """Initialize the unified dashboard"""
        self.config = config or {}
        
        # Dashboard settings
        self.port = self.config.get('port', 8050)
        self.theme = self.config.get('theme', 'darkly')
        self.title = self.config.get('title', 'Elite Trading Bot - Unified Dashboard')
        self.refresh_interval = self.config.get('refresh_interval', 5000)  # ms
        
        # Data storage
        self.prices = {}
        self.trades = []
        self.signals = []
        self.metrics = {}
        self.portfolio = {}
        self.exchange_data = {}
        
        # Exchange connectors
        self.connectors = {}
        self.initialize_connectors()
        
        # Initialize Dash app
        self.app = dash.Dash(
            __name__,
            external_stylesheets=[dbc.themes.DARKLY if self.theme == 'dark' else dbc.themes.BOOTSTRAP],
            suppress_callback_exceptions=True
        )
        
        # Set up layout
        self.setup_layout()
        
        # Set up callbacks
        self.setup_callbacks()
        
        # Background update thread
        self.update_thread = None
        self.running = False
        
        logger.info("Unified Dashboard initialized")
    
    def initialize_connectors(self):
        """Initialize exchange connectors"""
        # Initialize Binance connector if configured
        binance_config = self.config.get('binance_config')
        if binance_config:
            try:
                self.connectors['binance'] = BinanceConnector(binance_config)
                logger.info("Binance connector initialized")
            except Exception as e:
                logger.error(f"Error initializing Binance connector: {e}")
        
        # Initialize MT5 connector if configured
        mt5_config = self.config.get('mt5_config')
        if mt5_config:
            try:
                self.connectors['mt5'] = MT5Connector(mt5_config)
                logger.info("MT5 connector initialized")
            except Exception as e:
                logger.error(f"Error initializing MT5 connector: {e}")
    
    def setup_layout(self):
        """Set up dashboard layout"""
        self.app.layout = dbc.Container([
            # Header
            dbc.Row([
                dbc.Col([
                    html.H1(self.title),
                    html.P("Real-time trading dashboard for multiple exchanges", className="lead")
                ], width=8),
                dbc.Col([
                    html.Div(id="clock", className="h4 text-right"),
                    html.Div(id="status-indicators", className="text-right")
                ], width=4)
            ], className="mb-4 mt-2"),
            
            # Tabs
            dbc.Tabs([
                # Overview Tab
                dbc.Tab([
                    dbc.Row([
                        # Portfolio Summary
                        dbc.Col([
                            dbc.Card([
                                dbc.CardHeader("Portfolio Summary"),
                                dbc.CardBody([
                                    html.Div(id="portfolio-summary")
                                ])
                            ])
                        ], width=4),
                        
                        # Performance Metrics
                        dbc.Col([
                            dbc.Card([
                                dbc.CardHeader("Performance Metrics"),
                                dbc.CardBody([
                                    html.Div(id="performance-metrics")
                                ])
                            ])
                        ], width=8)
                    ], className="mb-4"),
                    
                    dbc.Row([
                        # Price Chart
                        dbc.Col([
                            dbc.Card([
                                dbc.CardHeader([
                                    dbc.Row([
                                        dbc.Col(html.H5("Price Chart"), width=6),
                                        dbc.Col([
                                            dbc.Select(
                                                id="symbol-selector",
                                                options=[],
                                                value=None
                                            )
                                        ], width=3),
                                        dbc.Col([
                                            dbc.Select(
                                                id="timeframe-selector",
                                                options=[
                                                    {"label": "1 Minute", "value": "1m"},
                                                    {"label": "5 Minutes", "value": "5m"},
                                                    {"label": "15 Minutes", "value": "15m"},
                                                    {"label": "1 Hour", "value": "1h"},
                                                    {"label": "4 Hours", "value": "4h"},
                                                    {"label": "1 Day", "value": "1d"}
                                                ],
                                                value="15m"
                                            )
                                        ], width=3)
                                    ])
                                ]),
                                dbc.CardBody([
                                    dcc.Graph(id="price-chart", style={"height": "400px"})
                                ])
                            ])
                        ], width=8),
                        
                        # Recent Signals
                        dbc.Col([
                            dbc.Card([
                                dbc.CardHeader("Recent Signals"),
                                dbc.CardBody([
                                    html.Div(id="recent-signals", style={"height": "400px", "overflow": "auto"})
                                ])
                            ])
                        ], width=4)
                    ], className="mb-4"),
                    
                    dbc.Row([
                        # Recent Trades
                        dbc.Col([
                            dbc.Card([
                                dbc.CardHeader("Recent Trades"),
                                dbc.CardBody([
                                    html.Div(id="recent-trades", style={"height": "300px", "overflow": "auto"})
                                ])
                            ])
                        ], width=12)
                    ])
                ], label="Overview"),
                
                # Exchange-specific Tabs
                dbc.Tab([
                    dbc.Row([
                        dbc.Col([
                            dbc.Card([
                                dbc.CardHeader("MT5 Account Information"),
                                dbc.CardBody([
                                    html.Div(id="mt5-account-info")
                                ])
                            ])
                        ], width=4),
                        
                        dbc.Col([
                            dbc.Card([
                                dbc.CardHeader("MT5 Positions"),
                                dbc.CardBody([
                                    html.Div(id="mt5-positions")
                                ])
                            ])
                        ], width=8)
                    ], className="mb-4"),
                    
                    dbc.Row([
                        dbc.Col([
                            dbc.Card([
                                dbc.CardHeader("MT5 Order Book"),
                                dbc.CardBody([
                                    dcc.Graph(id="mt5-order-book", style={"height": "400px"})
                                ])
                            ])
                        ], width=6),
                        
                        dbc.Col([
                            dbc.Card([
                                dbc.CardHeader("MT5 Trade History"),
                                dbc.CardBody([
                                    html.Div(id="mt5-trade-history", style={"height": "400px", "overflow": "auto"})
                                ])
                            ])
                        ], width=6)
                    ])
                ], label="MT5"),
                
                dbc.Tab([
                    dbc.Row([
                        dbc.Col([
                            dbc.Card([
                                dbc.CardHeader("Binance Account Information"),
                                dbc.CardBody([
                                    html.Div(id="binance-account-info")
                                ])
                            ])
                        ], width=4),
                        
                        dbc.Col([
                            dbc.Card([
                                dbc.CardHeader("Binance Positions"),
                                dbc.CardBody([
                                    html.Div(id="binance-positions")
                                ])
                            ])
                        ], width=8)
                    ], className="mb-4"),
                    
                    dbc.Row([
                        dbc.Col([
                            dbc.Card([
                                dbc.CardHeader("Binance Order Book"),
                                dbc.CardBody([
                                    dcc.Graph(id="binance-order-book", style={"height": "400px"})
                                ])
                            ])
                        ], width=6),
                        
                        dbc.Col([
                            dbc.Card([
                                dbc.CardHeader("Binance Trade History"),
                                dbc.CardBody([
                                    html.Div(id="binance-trade-history", style={"height": "400px", "overflow": "auto"})
                                ])
                            ])
                        ], width=6)
                    ])
                ], label="Binance"),
                
                # Analysis Tab
                dbc.Tab([
                    dbc.Row([
                        dbc.Col([
                            dbc.Card([
                                dbc.CardHeader("Technical Indicators"),
                                dbc.CardBody([
                                    dcc.Graph(id="technical-indicators", style={"height": "400px"})
                                ])
                            ])
                        ], width=6),
                        
                        dbc.Col([
                            dbc.Card([
                                dbc.CardHeader("Market Sentiment"),
                                dbc.CardBody([
                                    dcc.Graph(id="market-sentiment", style={"height": "400px"})
                                ])
                            ])
                        ], width=6)
                    ], className="mb-4"),
                    
                    dbc.Row([
                        dbc.Col([
                            dbc.Card([
                                dbc.CardHeader("Strategy Performance"),
                                dbc.CardBody([
                                    dcc.Graph(id="strategy-performance", style={"height": "400px"})
                                ])
                            ])
                        ], width=12)
                    ])
                ], label="Analysis"),
                
                # Settings Tab
                dbc.Tab([
                    dbc.Row([
                        dbc.Col([
                            dbc.Card([
                                dbc.CardHeader("Dashboard Settings"),
                                dbc.CardBody([
                                    dbc.Form([
                                        dbc.FormGroup([
                                            dbc.Label("Refresh Interval (seconds)"),
                                            dbc.Input(id="refresh-interval", type="number", value=self.refresh_interval/1000)
                                        ]),
                                        dbc.FormGroup([
                                            dbc.Label("Theme"),
                                            dbc.Select(
                                                id="theme-selector",
                                                options=[
                                                    {"label": "Light", "value": "light"},
                                                    {"label": "Dark", "value": "dark"}
                                                ],
                                                value=self.theme
                                            )
                                        ]),
                                        dbc.Button("Apply", id="apply-settings", color="primary")
                                    ])
                                ])
                            ])
                        ], width=6),
                        
                        dbc.Col([
                            dbc.Card([
                                dbc.CardHeader("Exchange Settings"),
                                dbc.CardBody([
                                    html.Div(id="exchange-settings")
                                ])
                            ])
                        ], width=6)
                    ])
                ], label="Settings")
            ]),
            
            # Hidden components for storing data
            dcc.Store(id="prices-store"),
            dcc.Store(id="trades-store"),
            dcc.Store(id="signals-store"),
            dcc.Store(id="metrics-store"),
            
            # Interval for updates
            dcc.Interval(id="update-interval", interval=self.refresh_interval)
        ], fluid=True)
    
    def setup_callbacks(self):
        """Set up dashboard callbacks"""
        # Clock update callback
        @self.app.callback(
            Output("clock", "children"),
            Input("update-interval", "n_intervals")
        )
        def update_clock(_):
            return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Symbol selector options callback
        @self.app.callback(
            Output("symbol-selector", "options"),
            Input("update-interval", "n_intervals")
        )
        def update_symbol_options(_):
            symbols = []
            for exchange, data in self.exchange_data.items():
                for symbol in data.get('symbols', []):
                    symbols.append({"label": f"{symbol} ({exchange.upper()})", "value": f"{exchange}:{symbol}"})
            return symbols
        
        # Price chart callback
        @self.app.callback(
            Output("price-chart", "figure"),
            [Input("symbol-selector", "value"),
             Input("timeframe-selector", "value"),
             Input("prices-store", "data")]
        )
        def update_price_chart(symbol, timeframe, prices_data):
            if not symbol or not prices_data:
                return go.Figure().update_layout(title="Select a symbol")
            
            exchange, symbol_name = symbol.split(":")
            key = f"{exchange}:{symbol_name}:{timeframe}"
            
            if key not in prices_data:
                return go.Figure().update_layout(title=f"No data for {symbol_name} ({timeframe})")
            
            df = pd.DataFrame(prices_data[key])
            
            # Create candlestick chart
            fig = go.Figure(data=[go.Candlestick(
                x=df['timestamp'],
                open=df['open'],
                high=df['high'],
                low=df['low'],
                close=df['close'],
                name=symbol_name
            )])
            
            # Add trades if available
            trades_df = self._get_trades_for_symbol(symbol)
            if not trades_df.empty:
                buy_trades = trades_df[trades_df['side'] == 'buy']
                sell_trades = trades_df[trades_df['side'] == 'sell']
                
                fig.add_trace(go.Scatter(
                    x=buy_trades['timestamp'],
                    y=buy_trades['price'],
                    mode='markers',
                    marker=dict(symbol='triangle-up', size=10, color='green'),
                    name='Buy'
                ))
                
                fig.add_trace(go.Scatter(
                    x=sell_trades['timestamp'],
                    y=sell_trades['price'],
                    mode='markers',
                    marker=dict(symbol='triangle-down', size=10, color='red'),
                    name='Sell'
                ))
            
            # Update layout
            fig.update_layout(
                title=f"{symbol_name} ({timeframe})",
                xaxis_title="Time",
                yaxis_title="Price",
                template="plotly_dark" if self.theme == 'dark' else "plotly_white",
                height=400
            )
            
            return fig
        
        # Recent trades callback
        @self.app.callback(
            Output("recent-trades", "children"),
            Input("trades-store", "data")
        )
        def update_recent_trades(trades_data):
            if not trades_data:
                return html.P("No trades yet")
            
            trades = trades_data[-20:]  # Show last 20 trades
            
            return html.Table([
                html.Thead(
                    html.Tr([
                        html.Th("Time"),
                        html.Th("Symbol"),
                        html.Th("Exchange"),
                        html.Th("Side"),
                        html.Th("Price"),
                        html.Th("Size"),
                        html.Th("Value")
                    ])
                ),
                html.Tbody([
                    html.Tr([
                        html.Td(trade['timestamp']),
                        html.Td(trade['symbol']),
                        html.Td(trade['exchange'].upper()),
                        html.Td(html.Span(trade['side'].upper(), 
                                         style={'color': 'green' if trade['side'] == 'buy' else 'red'})),
                        html.Td(f"{trade['price']:.5f}"),
                        html.Td(f"{trade['size']:.5f}"),
                        html.Td(f"{trade['price'] * trade['size']:.2f}")
                    ]) for trade in trades
                ])
            ], className="table table-striped table-hover")
        
        # Recent signals callback
        @self.app.callback(
            Output("recent-signals", "children"),
            Input("signals-store", "data")
        )
        def update_recent_signals(signals_data):
            if not signals_data:
                return html.P("No signals yet")
            
            signals = signals_data[-10:]  # Show last 10 signals
            
            return html.Table([
                html.Thead(
                    html.Tr([
                        html.Th("Time"),
                        html.Th("Symbol"),
                        html.Th("Signal"),
                        html.Th("Confidence"),
                        html.Th("Strategy")
                    ])
                ),
                html.Tbody([
                    html.Tr([
                        html.Td(signal['timestamp']),
                        html.Td(signal['symbol']),
                        html.Td(html.Span(signal['signal'].upper(), 
                                         style={'color': self._get_signal_color(signal['signal'])})),
                        html.Td(f"{signal['confidence']:.2f}"),
                        html.Td(signal['strategy'])
                    ]) for signal in signals
                ])
            ], className="table table-striped table-hover")
        
        # Portfolio summary callback
        @self.app.callback(
            Output("portfolio-summary", "children"),
            Input("metrics-store", "data")
        )
        def update_portfolio_summary(metrics_data):
            if not metrics_data or 'portfolio' not in metrics_data:
                return html.P("No portfolio data")
            
            portfolio = metrics_data['portfolio']
            
            return [
                html.H3(f"${portfolio.get('total_value', 0):.2f}"),
                html.P(f"Daily Change: {portfolio.get('daily_change', 0):.2f}%", 
                      style={'color': 'green' if portfolio.get('daily_change', 0) >= 0 else 'red'}),
                html.Hr(),
                html.Table([
                    html.Thead(
                        html.Tr([
                            html.Th("Asset"),
                            html.Th("Value"),
                            html.Th("Allocation")
                        ])
                    ),
                    html.Tbody([
                        html.Tr([
                            html.Td(asset),
                            html.Td(f"${value:.2f}"),
                            html.Td(f"{value / portfolio.get('total_value', 1) * 100:.1f}%")
                        ]) for asset, value in portfolio.get('assets', {}).items()
                    ])
                ], className="table table-sm")
            ]
        
        # Performance metrics callback
        @self.app.callback(
            Output("performance-metrics", "children"),
            Input("metrics-store", "data")
        )
        def update_performance_metrics(metrics_data):
            if not metrics_data or 'performance' not in metrics_data:
                return html.P("No performance data")
            
            performance = metrics_data['performance']
            
            return dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H5("Win Rate"),
                            html.H3(f"{performance.get('win_rate', 0):.1f}%")
                        ])
                    ], className="text-center")
                ]),
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H5("Profit Factor"),
                            html.H3(f"{performance.get('profit_factor', 0):.2f}")
                        ])
                    ], className="text-center")
                ]),
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H5("Sharpe Ratio"),
                            html.H3(f"{performance.get('sharpe_ratio', 0):.2f}")
                        ])
                    ], className="text-center")
                ]),
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H5("Max Drawdown"),
                            html.H3(f"{performance.get('max_drawdown', 0):.2f}%")
                        ])
                    ], className="text-center")
                ])
            ])
    
    def start(self, debug=False):
        """Start the dashboard"""
        if self.running:
            logger.warning("Dashboard already running")
            return
        
        self.running = True
        
        # Start update thread
        self.update_thread = threading.Thread(target=self._update_loop)
        self.update_thread.daemon = True
        self.update_thread.start()
        
        # Start Dash app
        logger.info(f"Starting dashboard on port {self.port}")
        self.app.run_server(debug=debug, port=self.port)
    
    def stop(self):
        """Stop the dashboard"""
        self.running = False
        
        if self.update_thread:
            self.update_thread.join(timeout=5)
            self.update_thread = None
        
        logger.info("Dashboard stopped")
    
    def _update_loop(self):
        """Background update loop"""
        while self.running:
            try:
                # Update data
                self._update_exchange_data()
                self._update_prices()
                self._update_trades()
                self._update_signals()
                self._update_metrics()
                
                # Update stores
                self._update_stores()
                
            except Exception as e:
                logger.error(f"Error in update loop: {e}")
            
            time.sleep(self.refresh_interval / 1000)
    
    def _update_exchange_data(self):
        """Update exchange data"""
        for exchange, connector in self.connectors.items():
            try:
                # Get account info
                account_info = asyncio.run(connector.get_balance())
                
                # Get positions
                positions = asyncio.run(connector.get_positions())
                
                # Get symbols
                symbols = [pos['symbol'] for pos in positions]
                
                # Store data
                self.exchange_data[exchange] = {
                    'account_info': account_info,
                    'positions': positions,
                    'symbols': symbols
                }
                
            except Exception as e:
                logger.error(f"Error updating {exchange} data: {e}")
    
    def _update_prices(self):
        """Update price data"""
        for exchange, data in self.exchange_data.items():
            connector = self.connectors.get(exchange)
            if not connector:
                continue
            
            for symbol in data.get('symbols', []):
                try:
                    # Get ticker
                    ticker = asyncio.run(connector.get_ticker(symbol))
                    
                    # Store price
                    key = f"{exchange}:{symbol}"
                    if key not in self.prices:
                        self.prices[key] = []
                    
                    self.prices[key].append({
                        'timestamp': datetime.now(),
                        'price': ticker.last,
                        'bid': ticker.bid,
                        'ask': ticker.ask,
                        'volume': ticker.volume_24h
                    })
                    
                    # Limit history
                    if len(self.prices[key]) > 1000:
                        self.prices[key] = self.prices[key][-1000:]
                    
                except Exception as e:
                    logger.error(f"Error updating price for {symbol} on {exchange}: {e}")
    
    def _update_trades(self):
        """Update trade data"""
        # In a real implementation, this would get trades from a database or API
        pass
    
    def _update_signals(self):
        """Update signal data"""
        # In a real implementation, this would get signals from strategies
        pass
    
    def _update_metrics(self):
        """Update metrics data"""
        # In a real implementation, this would calculate performance metrics
        pass
    
    def _update_stores(self):
        """Update data stores for callbacks"""
        # This would update the dcc.Store components
        pass
    
    def _get_trades_for_symbol(self, symbol_key):
        """Get trades for a specific symbol"""
        if not self.trades:
            return pd.DataFrame()
        
        exchange, symbol = symbol_key.split(":")
        
        # Filter trades
        filtered_trades = [
            trade for trade in self.trades
            if trade['exchange'] == exchange and trade['symbol'] == symbol
        ]
        
        return pd.DataFrame(filtered_trades)
    
    def _get_signal_color(self, signal):
        """Get color for signal"""
        if signal.lower() == 'buy':
            return 'green'
        elif signal.lower() == 'sell':
            return 'red'
        else:
            return 'orange'
    
    def add_trade(self, trade):
        """Add a trade to the dashboard"""
        self.trades.append(trade)
        
        # Limit history
        if len(self.trades) > 1000:
            self.trades = self.trades[-1000:]
    
    def add_signal(self, signal):
        """Add a signal to the dashboard"""
        self.signals.append(signal)
        
        # Limit history
        if len(self.signals) > 1000:
            self.signals = self.signals[-1000:]
    
    def update_metric(self, name, value):
        """Update a metric"""
        self.metrics[name] = value


# Example usage
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Create dashboard
    dashboard = UnifiedDashboard({
        'port': 8050,
        'theme': 'dark',
        'refresh_interval': 5000
    })
    
    # Start dashboard
    dashboard.start(debug=True)
