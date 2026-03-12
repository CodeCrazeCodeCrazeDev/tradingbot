"""
Elite Trading Bot - Simple Dashboard Demo

This script demonstrates the Elite Trading System's visualization capabilities
with a simple dashboard that works reliably.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import dash
import dash_bootstrap_components as dbc
from dash import html, dcc
from dash.dependencies import Input, Output, State
import logging
import asyncio
import sys
import traceback
import json
import os
from pathlib import Path
from typing import Optional
import numpy
import pandas
from typing import Set

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EliteSimpleDashboard:
    """Simple Elite Trading System Dashboard"""
    
    def __init__(self, config=None):
        """Initialize dashboard
        
        Args:
            config: Optional configuration dictionary
        """
        logger.info("Initializing Elite Simple Dashboard")
        
        # Set default configuration
        self.config = config or {
            'theme': 'dark',
            'refresh_interval': 5000,  # 5 seconds
            'default_symbol': 'EURUSD',
            'available_symbols': ['EURUSD', 'GBPUSD', 'USDJPY', 'BTCUSD'],
            'default_timeframe': '1H',
            'available_timeframes': ['5M', '15M', '1H', '4H', '1D'],
            'show_indicators': True,
            'show_volume': True,
            'output_dir': 'dashboard_output'
        }
        
        # Create output directory if needed
        os.makedirs(self.config['output_dir'], exist_ok=True)
        
        # Initialize Dash app
        self.app = dash.Dash(
            __name__,
            external_stylesheets=[dbc.themes.DARKLY]
        )
        
        # Setup layout
        self.app.layout = dbc.Container([
            # Header with title and controls
            dbc.Row([
                # Title
                dbc.Col([
                    html.H1(
                        "Elite Trading System Dashboard",
                        className="text-center text-primary mb-4"
                    )
                ], width=12)
            ]),
            
            # Controls row
            dbc.Row([
                # Symbol selector
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("Symbol"),
                        dbc.CardBody([
                            dcc.Dropdown(
                                id='symbol-selector',
                                options=[{'label': self._format_symbol(s), 'value': s} 
                                         for s in self.config['available_symbols']],
                                value=self.config['default_symbol'],
                                className="mb-2"
                            )
                        ])
                    ])
                ], width=3),
                
                # Timeframe selector
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("Timeframe"),
                        dbc.CardBody([
                            dcc.Dropdown(
                                id='timeframe-selector',
                                options=[{'label': tf, 'value': tf} 
                                         for tf in self.config['available_timeframes']],
                                value=self.config['default_timeframe'],
                                className="mb-2"
                            )
                        ])
                    ])
                ], width=3),
                
                # Indicator toggles
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("Display Options"),
                        dbc.CardBody([
                            dbc.Checklist(
                                options=[
                                    {"label": "Show Indicators", "value": "indicators"},
                                    {"label": "Show Volume", "value": "volume"},
                                    {"label": "Show Liquidity Zones", "value": "liquidity"}
                                ],
                                value=["indicators", "volume"] if self.config['show_indicators'] else ["volume"],
                                id="display-options",
                                switch=True,
                                inline=True
                            )
                        ])
                    ])
                ], width=6)
            ], className="mb-4"),
            
            # Main content row
            dbc.Row([
                # Market chart column
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader([
                            html.H4(id="chart-title", className="d-inline"),
                            dbc.ButtonGroup([
                                dbc.Button("Refresh", id="refresh-button", color="primary", size="sm", className="ms-2"),
                                dbc.Button("Export", id="export-button", color="secondary", size="sm")
                            ], className="float-end")
                        ]),
                        dbc.CardBody([
                            dcc.Loading(
                                id="loading-chart",
                                type="circle",
                                children=[dcc.Graph(id='market-chart')]
                            )
                        ])
                    ])
                ], width=8),
                
                # Analysis column
                dbc.Col([
                    # Trading signal card
                    dbc.Card([
                        dbc.CardHeader("Trading Signal"),
                        dbc.CardBody([
                            dcc.Loading(
                                id="loading-signal",
                                type="circle",
                                children=[html.Div(id='signal-display')]
                            )
                        ])
                    ], className="mb-3"),
                    
                    # Market info card
                    dbc.Card([
                        dbc.CardHeader("Market Analysis"),
                        dbc.CardBody([
                            dcc.Loading(
                                id="loading-market-info",
                                type="circle",
                                children=[html.Div(id='market-info')]
                            )
                        ])
                    ])
                ], width=4)
            ]),
            
            # Bottom row with additional analysis
            dbc.Row([
                # Technical indicators
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("Technical Indicators"),
                        dbc.CardBody([
                            dcc.Loading(
                                id="loading-indicators",
                                type="circle",
                                children=[html.Div(id='indicators-display')]
                            )
                        ])
                    ])
                ], width=6),
                
                # Quantum analysis
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("Quantum Analysis"),
                        dbc.CardBody([
                            dcc.Loading(
                                id="loading-quantum",
                                type="circle",
                                children=[html.Div(id='quantum-display')]
                            )
                        ])
                    ])
                ], width=6)
            ], className="mt-4"),
            
            # Status bar
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.Div(id='status-display', className="d-flex justify-content-between"),
                            dcc.Interval(
                                id='interval-component',
                                interval=self.config['refresh_interval'],
                                n_intervals=0
                            )
                        ], className="py-2")
                    ])
                ])
            ], className="mt-4"),
            
            # Symbol selector row (fixed)
            dbc.Row([
                dbc.Col([
                    dcc.Dropdown(
                        id='symbol-selector-fixed',
                        options=[
                            {'label': 'EUR/USD', 'value': 'EURUSD'},
                            {'label': 'GBP/USD', 'value': 'GBPUSD'},
                            {'label': 'BTC/USD', 'value': 'BTCUSD'}
                        ],
                        value='EURUSD',
                        className="mb-3"
                    )
                ], width=3)
            ]),
            
            # Market chart
            dbc.Row([
                dbc.Col([
                    dcc.Graph(id='market-chart'),
                    dcc.Interval(
                        id='market-update',
                        interval=5000  # 5 seconds
                    )
                ])
            ]),
            
            # Signal info
            dbc.Row([
                dbc.Col([
                    html.Div(id='signal-info', className="mt-3")
                ])
            ])
        ], fluid=True, className="p-4")
        
        # Setup callbacks
        self.setup_callbacks()
        
        logger.info("Elite Simple Dashboard initialized")
    
    def setup_callbacks(self):
        """Setup dashboard callbacks"""
        @self.app.callback(
            [Output('market-chart', 'figure'),
             Output('signal-info', 'children')],
            [Input('symbol-selector', 'value'),
             Input('market-update', 'n_intervals')]
        )
        def update_dashboard(symbol, n_intervals):
            """Update dashboard components"""
            try:
                # Generate sample market data
                market_data = self.generate_sample_data(symbol)
                
                # Create market chart
                market_chart = self.create_market_chart(market_data, symbol)
                
                # Create signal info card
                signal_info = self.create_signal_info(symbol, market_data)
                
                return market_chart, signal_info
                
            except Exception as e:
                logger.error(f"Error updating dashboard: {e}")
                traceback.print_exc()
                return go.Figure(), html.Div("Error loading data")
    
    def generate_sample_data(self, symbol):
        """Generate sample market data"""
        # Use symbol as seed for reproducibility
        seed = sum(ord(c) for c in symbol)
        np.random.seed(seed)
        
        # Generate data
        periods = 100
        dates = pd.date_range(end=datetime.now(), periods=periods, freq='1H')
        
        # Base price varies by symbol
        base_price = 100
        if symbol == 'EURUSD':
            base_price = 1.1
        elif symbol == 'GBPUSD':
            base_price = 1.3
        elif symbol == 'BTCUSD':
            base_price = 50000
        
        # Generate OHLCV data
        data = pd.DataFrame({
            'open': np.random.randn(periods).cumsum() + base_price,
            'high': np.random.randn(periods).cumsum() + base_price + 0.02 * base_price,
            'low': np.random.randn(periods).cumsum() + base_price - 0.02 * base_price,
            'close': np.random.randn(periods).cumsum() + base_price,
            'volume': np.random.randint(1000, 10000, periods)
        }, index=dates)
        
        # Ensure high is always highest and low is always lowest
        for i in range(len(data)):
            values = [data.iloc[i]['open'], data.iloc[i]['close']]
            data.iloc[i, data.columns.get_loc('high')] = max(values) + abs(np.random.randn()) * 0.01 * base_price
            data.iloc[i, data.columns.get_loc('low')] = min(values) - abs(np.random.randn()) * 0.01 * base_price
        
        return data
    
    def create_market_chart(self, market_data, symbol):
        """Create market chart"""
        # Create subplots for price and volume
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                           vertical_spacing=0.03,
                           row_heights=[0.7, 0.3])
        
        # Add price data
        fig.add_trace(
            go.Candlestick(
                x=market_data.index,
                open=market_data['open'],
                high=market_data['high'],
                low=market_data['low'],
                close=market_data['close'],
                name='Price'
            ),
            row=1, col=1
        )
        
        # Add volume
        colors = np.where(market_data['close'] >= market_data['open'],
                         'rgba(0, 255, 0, 0.5)',
                         'rgba(255, 0, 0, 0.5)')
        
        fig.add_trace(
            go.Bar(
                x=market_data.index,
                y=market_data['volume'],
                marker_color=colors,
                name='Volume'
            ),
            row=2, col=1
        )
        
        # Add moving averages
        ma20 = market_data['close'].rolling(window=20).mean()
        ma50 = market_data['close'].rolling(window=50).mean()
        
        fig.add_trace(
            go.Scatter(
                x=market_data.index,
                y=ma20,
                mode='lines',
                name='MA20',
                line=dict(color='rgba(255, 255, 0, 0.7)', width=1)
            ),
            row=1, col=1
        )
        
        fig.add_trace(
            go.Scatter(
                x=market_data.index,
                y=ma50,
                mode='lines',
                name='MA50',
                line=dict(color='rgba(0, 255, 255, 0.7)', width=1)
            ),
            row=1, col=1
        )
        
        # Add signals
        last_idx = market_data.index[-1]
        last_price = market_data['close'].iloc[-1]
        signal_type = "BUY" if ma20.iloc[-1] > ma50.iloc[-1] else "SELL"
        signal_color = "green" if signal_type == "BUY" else "red"
        
        fig.add_trace(
            go.Scatter(
                x=[last_idx],
                y=[last_price],
                mode='markers+text',
                marker=dict(
                    symbol='diamond',
                    size=15,
                    color=signal_color
                ),
                text=[signal_type],
                textposition="top center",
                name='Signal'
            ),
            row=1, col=1
        )
        
        # Update layout
        fig.update_layout(
            title=f"{symbol} Analysis",
            template='plotly_dark',
            xaxis_rangeslider_visible=False,
            height=600
        )
        
        return fig
    
    def create_signal_info(self, symbol, market_data):
        """Create signal info cards"""
        # Calculate simple metrics
        last_price = market_data['close'].iloc[-1]
        ma20 = market_data['close'].rolling(window=20).mean().iloc[-1]
        ma50 = market_data['close'].rolling(window=50).mean().iloc[-1]
        
        # Determine signal
        signal_type = "BUY" if ma20 > ma50 else "SELL"
        signal_strength = abs(ma20 - ma50) / last_price * 100
        
        # Create cards
        return dbc.Row([
            # Signal card
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H4("Trading Signal", className="text-center")),
                    dbc.CardBody([
                        html.P([html.Strong("Direction: "), html.Span(signal_type)]),
                        html.P([html.Strong("Strength: "), html.Span(f"{signal_strength:.2f}%")]),
                        html.P([html.Strong("Price: "), html.Span(f"{last_price:.5f}")]),
                        html.P([html.Strong("MA20: "), html.Span(f"{ma20:.5f}")]),
                        html.P([html.Strong("MA50: "), html.Span(f"{ma50:.5f}")])
                    ])
                ], className="mb-3")
            ], width=6),
            
            # Market info card
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H4("Market Info", className="text-center")),
                    dbc.CardBody([
                        html.P([html.Strong("Symbol: "), html.Span(symbol)]),
                        html.P([html.Strong("Timeframe: "), html.Span("1H")]),
                        html.P([html.Strong("Volatility: "), html.Span(f"{self.calculate_volatility(market_data):.2f}%")]),
                        html.P([html.Strong("24h Change: "), html.Span(f"{self.calculate_change(market_data):.2f}%")]),
                        html.P([html.Strong("Volume: "), html.Span(f"{market_data['volume'].iloc[-1]:,}")])
                    ])
                ], className="mb-3")
            ], width=6)
        ])
    
    def calculate_volatility(self, market_data):
        """Calculate volatility as ATR percentage"""
        high = market_data['high']
        low = market_data['low']
        close = market_data['close'].shift(1)
        
        tr1 = high - low
        tr2 = abs(high - close)
        tr3 = abs(low - close)
        
        tr = pd.DataFrame({'tr1': tr1, 'tr2': tr2, 'tr3': tr3}).max(axis=1)
        atr = tr.rolling(14).mean().iloc[-1]
        
        return atr / market_data['close'].iloc[-1] * 100
    
    def calculate_change(self, market_data):
        """Calculate 24h price change percentage"""
        if len(market_data) >= 24:
            return (market_data['close'].iloc[-1] / market_data['close'].iloc[-24] - 1) * 100
        else:
            return (market_data['close'].iloc[-1] / market_data['close'].iloc[0] - 1) * 100
    
    def run(self, port=8050, debug=False):
        """Run the dashboard"""
        logger.info(f"Starting Elite Simple Dashboard on port {port}")
        try:
            self.app.run_server(debug=debug, port=port, host='localhost')
        except Exception as e:
            logger.error(f"Error running dashboard: {e}")
            traceback.print_exc()

def main():
    """Main function"""
    print("Starting Elite Trading System Simple Dashboard...")
    dashboard = EliteSimpleDashboard()
    dashboard.run()

if __name__ == "__main__":
    main()
