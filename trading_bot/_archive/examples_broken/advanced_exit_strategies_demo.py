"""
Elite Trading Bot - Advanced Exit Strategies Demo

This script demonstrates the comprehensive exit strategies system including
adaptive exits, dynamic management, profit maximization, and signal generation.
"""

import os
import sys
from datetime import datetime as dt, timedelta
from typing import Dict, List, Optional, Any

import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import dash
from dash import dcc, html, Input, Output, dash_table
import dash_bootstrap_components as dbc

# Add parent directory to path to import trading_bot modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from trading_bot.exit_strategies import (
from typing import Set
from enum import auto
import datetime
import numpy
import pandas
    ExitSignalGenerator, ExitReason, ExitStrength
)

# Sample data generation functions
def generate_realistic_market_data(symbol, timeframes, num_candles=500):
    pass
    """Generate realistic market data with trends, reversals, and volatility."""
    data = {}
    
    # Use symbol as seed for reproducibility
    seed = sum(ord(c) for c in symbol)
    np.random.seed(seed)
    
    # Base price varies by symbol
    if symbol.startswith("BTC") or symbol.endswith("BTC"):
    pass
        base_price = 45000
    elif symbol.startswith("ETH") or symbol.endswith("ETH"):
    pass
        base_price = 2800
    elif "USD" in symbol:
    pass
        base_price = 1.08
    else:
    pass
        base_price = 150
    
    for timeframe in timeframes:
    pass
        # Generate dates
        end_date = dt.now()
        
        # Determine time delta based on timeframe
        if timeframe == "1m":
    pass
            delta = timedelta(minutes=1)
        elif timeframe == "5m":
    pass
            delta = timedelta(minutes=5)
        elif timeframe == "15m":
    pass
            delta = timedelta(minutes=15)
        elif timeframe == "30m":
    pass
            delta = timedelta(minutes=30)
        elif timeframe == "1h":
    pass
            delta = timedelta(hours=1)
        elif timeframe == "4h":
    pass
            delta = timedelta(hours=4)
        else:  # 1d
            delta = timedelta(days=1)
            
        dates = [end_date - delta * i for i in range(num_candles)]
        dates.reverse()
        
        # Generate realistic price movement with multiple phases
        close_prices = []
        current_price = base_price
        
        # Create different market phases
        phases = [
            {"type": "trend", "direction": 1, "strength": 0.3, "length": 100},    # Uptrend
            {"type": "consolidation", "direction": 0, "strength": 0.1, "length": 50},  # Sideways
            {"type": "trend", "direction": -1, "strength": 0.4, "length": 80},   # Downtrend
            {"type": "reversal", "direction": 1, "strength": 0.5, "length": 120}, # Strong reversal up
            {"type": "volatility", "direction": 0, "strength": 0.6, "length": 70}, # High volatility
            {"type": "trend", "direction": 1, "strength": 0.2, "length": 80},    # Gentle uptrend
        ]
        
        phase_idx = 0
        phase_progress = 0
        
        for i in range(num_candles):
    pass
            # Get current phase
            if phase_idx < len(phases):
    pass
                current_phase = phases[phase_idx]
            else:
    pass
                current_phase = {"type": "trend", "direction": 0.1, "strength": 0.1, "length": 50}
            
            # Calculate price change based on phase
            if current_phase["type"] == "trend":
    pass
                # Trending market
                trend_component = current_phase["direction"] * current_phase["strength"] * 0.01
                noise = np.random.randn() * 0.005
                price_change = trend_component + noise
                
            elif current_phase["type"] == "consolidation":
    pass
                # Sideways market with mean reversion
                mean_reversion = (base_price - current_price) * 0.001
                noise = np.random.randn() * 0.003
                price_change = mean_reversion + noise
                
            elif current_phase["type"] == "reversal":
    pass
                # Strong reversal
                reversal_component = current_phase["direction"] * current_phase["strength"] * 0.015
                momentum = min(phase_progress / current_phase["length"], 1.0)
                price_change = reversal_component * momentum + np.random.randn() * 0.008
                
            elif current_phase["type"] == "volatility":
    pass
                # High volatility period
                volatility_factor = current_phase["strength"] * 0.02
                price_change = np.random.randn() * volatility_factor
                
            else:
    pass
                price_change = np.random.randn() * 0.005
            
            # Apply price change
            current_price = current_price * (1 + price_change)
            close_prices.append(current_price)
            
            # Update phase progress
            phase_progress += 1
            if phase_progress >= current_phase["length"]:
    pass
                phase_idx += 1
                phase_progress = 0
        
        # Generate OHLCV data
        df = pd.DataFrame(index=dates)
        df['close'] = close_prices
        
        # Generate realistic OHLC based on close prices
        for i in range(len(df)):
    pass
            if i > 0:
    pass
                df.loc[df.index[i], 'open'] = df.loc[df.index[i-1], 'close'] * (1 + np.random.randn() * 0.001)
            else:
    pass
                df.loc[df.index[i], 'open'] = df.loc[df.index[i], 'close'] * (1 - 0.002)
                
            # Calculate realistic range
            close_price = df.loc[df.index[i], 'close']
            open_price = df.loc[df.index[i], 'open']
            
            # Range size based on volatility
            range_factor = 0.01 + abs(np.random.randn()) * 0.005
            range_size = close_price * range_factor
            
            # Determine high and low
            mid_price = (open_price + close_price) / 2
            df.loc[df.index[i], 'high'] = mid_price + range_size * (0.3 + 0.7 * np.random.rand())
            df.loc[df.index[i], 'low'] = mid_price - range_size * (0.3 + 0.7 * np.random.rand())
            
            # Ensure high >= max(open, close) and low <= min(open, close)
            df.loc[df.index[i], 'high'] = max(df.loc[df.index[i], 'high'], 
                                             open_price, close_price)
            df.loc[df.index[i], 'low'] = min(df.loc[df.index[i], 'low'], 
                                            open_price, close_price)
        
        # Generate volume with realistic patterns
        base_volume = 1000
        volumes = []
        
        for i in range(len(df)):
    pass
            # Volume tends to be higher on larger price moves
            price_change = abs(df.iloc[i]['close'] - df.iloc[i]['open']) / df.iloc[i]['open']
            volume_multiplier = 1 + price_change * 10
            
            # Add some randomness
            volume_multiplier *= (0.5 + np.random.rand())
            
            # Occasional volume spikes
            if np.random.rand() < 0.05:  # 5% chance of volume spike
                volume_multiplier *= (2 + 3 * np.random.rand())
            
            volume = int(base_volume * volume_multiplier)
            volumes.append(volume)
        
        df['volume'] = volumes
        
        # Add bid/ask volume for order flow analysis
        total_volume = df['volume'].values
        
        # Determine bid/ask split based on price action and trend
        price_changes = df['close'].pct_change().fillna(0)
        
        # Bias towards ask volume in uptrends, bid volume in downtrends
        ask_bias = 0.5 + price_changes * 2  # Base 50/50 split, adjusted by price change
        ask_bias = np.clip(ask_bias, 0.2, 0.8)  # Keep within reasonable bounds
        
        # Add some noise
        ask_bias += np.random.randn(len(ask_bias)) * 0.1
        ask_bias = np.clip(ask_bias, 0.1, 0.9)
        
        df['ask_volume'] = (total_volume * ask_bias).astype(int)
        df['bid_volume'] = total_volume - df['ask_volume']
        
        data[timeframe] = df
    
    return data

# Create sample trades with different scenarios
def create_sample_trades():
    pass
    """Create sample trades for demonstration."""
    current_time = dt.now()
    
    trades = [
        {
            "id": "trade_001",
            "symbol": "BTCUSD",
            "entry_price": 44500.0,
            "direction": "long",
            "stop_loss": 43500.0,
            "take_profit": 47500.0,
            "entry_time": current_time - timedelta(hours=6),
            "position_size": 1.0,
            "scenario": "trending_up"
        },
        {
            "id": "trade_002", 
            "symbol": "ETHUSD",
            "entry_price": 2750.0,
            "direction": "short",
            "stop_loss": 2850.0,
            "take_profit": 2550.0,
            "entry_time": current_time - timedelta(hours=12),
            "position_size": 2.0,
            "scenario": "reversal_down"
        },
        {
            "id": "trade_003",
            "symbol": "EURUSD", 
            "entry_price": 1.0820,
            "direction": "long",
            "stop_loss": 1.0770,
            "take_profit": 1.0920,
            "entry_time": current_time - timedelta(hours=18),
            "position_size": 0.5,
            "scenario": "consolidation"
        }
    ]
    
    return trades

# Main application class
class AdvancedExitStrategiesDemo:
    pass
    """Demo application for advanced exit strategies."""
    
    def __init__(self):
    pass
        """Initialize the demo application."""
        # Configuration
        self.config = {
            "symbols": ["BTCUSD", "ETHUSD", "EURUSD"],
            "timeframes": ["5m", "15m", "1h", "4h"],
            "update_interval_ms": 3000,  # 3 seconds
        }
        
        # Initialize exit strategies system
        self.exit_signal_generator = ExitSignalGenerator({
            "enable_adaptive_exits": True,
            "enable_dynamic_management": True,
            "enable_profit_maximization": True,
            "enable_multi_timeframe_analysis": True,
            "min_signal_strength": ExitStrength.WEAK,
            "min_confirmations": 1
        })
        
        # Initialize data and trades
        self.market_data = {}
        self.sample_trades = create_sample_trades()
        self.current_prices = {}
        self.exit_signals = {}
        
        # Generate market data
        self._generate_market_data()
        
        # Register sample trades
        self._register_sample_trades()
        
        # Initialize Dash app
        self.app = dash.Dash(
            __name__,
            external_stylesheets=[dbc.themes.DARKLY],
            update_title=None
        )
        self.app.title = "Elite Trading Bot - Advanced Exit Strategies Demo"
        
        # Set up layout and callbacks
        self._setup_layout()
        self._setup_callbacks()
    
    def _generate_market_data(self):
    pass
        """Generate market data for all symbols."""
        for symbol in self.config["symbols"]:
    pass
            self.market_data[symbol] = generate_realistic_market_data(
                symbol, 
                self.config["timeframes"]
            )
            
            # Set current price (latest close)
            primary_tf = "1h"
            if primary_tf in self.market_data[symbol]:
    pass
                self.current_prices[symbol] = self.market_data[symbol][primary_tf]['close'].iloc[-1]
    
    def _register_sample_trades(self):
    pass
        """Register sample trades with the exit signal generator."""
        for trade in self.sample_trades:
    pass
            symbol = trade["symbol"]
            
            if symbol in self.market_data:
    pass
                self.exit_signal_generator.register_trade(
                    trade_id=trade["id"],
                    symbol=symbol,
                    entry_price=trade["entry_price"],
                    direction=trade["direction"],
                    stop_loss=trade["stop_loss"],
                    take_profit=trade["take_profit"],
                    entry_time=trade["entry_time"],
                    position_size=trade["position_size"],
                    market_data=self.market_data[symbol]
                )
                
                # Initialize exit signals list
                self.exit_signals[trade["id"]] = []
    
    def _setup_layout(self):
    pass
        """Set up the Dash app layout."""
        self.app.layout = dbc.Container([
            dbc.Row([
                dbc.Col([
                    html.H1("Elite Trading Bot - Advanced Exit Strategies Demo", 
                           className="text-center mb-4"),
                    html.P("Comprehensive demonstration of adaptive exits, dynamic management, and profit maximization.",
                          className="text-center text-muted mb-4")
                ], width=12)
            ]),
            
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader(html.H4("Active Trades")),
                        dbc.CardBody([
                            html.Div(id="trades-overview")
                        ])
                    ])
                ], width=4),
                
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader(html.H4("Exit Signals")),
                        dbc.CardBody([
                            html.Div(id="exit-signals-overview")
                        ])
                    ])
                ], width=4),
                
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader(html.H4("Strategy Performance")),
                        dbc.CardBody([
                            html.Div(id="strategy-performance")
                        ])
                    ])
                ], width=4)
            ], className="mb-4"),
            
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader([
                            html.H4("Trade Details", className="d-inline"),
                            dbc.Select(
                                id="trade-selector",
                                options=[{"label": f"{t['id']} ({t['symbol']})", "value": t['id']} 
                                        for t in self.sample_trades],
                                value=self.sample_trades[0]["id"] if self.sample_trades else None,
                                className="d-inline ms-3",
                                style={"width": "200px", "display": "inline-block"}
                            )
                        ]),
                        dbc.CardBody([
                            dcc.Graph(id="trade-chart", style={"height": "500px"})
                        ])
                    ])
                ], width=8),
                
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader(html.H4("Trade Management")),
                        dbc.CardBody([
                            html.Div(id="trade-management-details")
                        ])
                    ])
                ], width=4)
            ], className="mb-4"),
            
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader(html.H4("Exit Signals History")),
                        dbc.CardBody([
                            html.Div(id="signals-history-table")
                        ])
                    ])
                ], width=12)
            ]),
            
            # New row for multi-symbol portfolio visualization
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader(html.H4("Multi-Symbol Portfolio Overview")),
                        dbc.CardBody([
                            dcc.Graph(id="portfolio-chart", style={"height": "400px"})
                        ])
                    ])
                ], width=12)
            ], className="mb-4"),
            
            # New row for error handling simulation
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader(html.H4("Error Handling Simulation")),
                        dbc.CardBody([
                            html.Div(id="error-handling-status"),
                            dbc.Button("Simulate Error", id="simulate-error-btn", color="danger", className="mt-2")
                        ])
                    ])
                ], width=12)
            ], className="mb-4"),
            
            # Dashboard link
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.A("Open Trading Dashboard", href="http://localhost:8000", target="_blank", className="btn btn-primary")
                        ])
                    ])
                ], width=12)
            ]),
            
            # Auto-update component
            dcc.Interval(
                id="interval-component",
                interval=self.config["update_interval_ms"],
                n_intervals=0
            )
        ], fluid=True, className="px-4")
    
    def _setup_callbacks(self):
    pass
        """Set up Dash app callbacks."""
        @self.app.callback(
            [
                Output("trades-overview", "children"),
                Output("exit-signals-overview", "children"),
                Output("strategy-performance", "children"),
                Output("trade-chart", "figure"),
                Output("trade-management-details", "children"),
                Output("signals-history-table", "children"),
                Output("portfolio-chart", "figure"),
                Output("error-handling-status", "children")
            ],
            [
                Input("interval-component", "n_intervals"),
                Input("trade-selector", "value"),
                Input("simulate-error-btn", "n_clicks")
            ]
        )
        def update_charts(_n_intervals, selected_trade_id, error_clicks):
    pass
            # Simulate market updates
            self._simulate_market_updates()
            
            # Generate new exit signals
            self._update_exit_signals()
            
            # Create trades overview
            trades_overview = self._create_trades_overview()
            
            # Create exit signals overview
            signals_overview = self._create_signals_overview()
            
            # Create strategy performance
            performance = self._create_performance_overview()
            
            # Create trade chart
            chart = self._create_trade_chart(selected_trade_id)
            
            # Create trade management details
            management_details = self._create_management_details(selected_trade_id)
            
            # Create signals history table
            signals_table = self._create_signals_table(selected_trade_id)
            
            # Create portfolio overview chart
            portfolio_chart = self._create_portfolio_chart()
            
            # Handle error simulation
            error_status = self._handle_error_simulation(error_clicks)
            
            return (trades_overview, signals_overview, performance, 
                   chart, management_details, signals_table,
                   portfolio_chart, error_status)
    
    def _simulate_market_updates(self):
    pass
        """Simulate real-time market price updates."""
        for symbol in self.config["symbols"]:
    pass
            if symbol in self.current_prices:
    pass
                # Add small random price movement
                change_pct = np.random.randn() * 0.002  # 0.2% random walk
                self.current_prices[symbol] *= (1 + change_pct)
                
                # Update the latest candle in market data
                primary_tf = "1h"
                if primary_tf in self.market_data[symbol]:
    pass
                    df = self.market_data[symbol][primary_tf]
                    df.iloc[-1, df.columns.get_loc('close')] = self.current_prices[symbol]
    
    def _update_exit_signals(self):
    pass
        """Update exit signals for all trades."""
        current_time = dt.now()
        
        for trade in self.sample_trades:
    pass
            trade_id = trade["id"]
            symbol = trade["symbol"]
            
            if symbol in self.current_prices and symbol in self.market_data:
    pass
                # Generate exit signals
                new_signals = self.exit_signal_generator.generate_exit_signals(
                    trade_id=trade_id,
                    current_price=self.current_prices[symbol],
                    current_time=current_time,
                    market_data=self.market_data[symbol]
                )
                
                # Add to signals history
                if trade_id not in self.exit_signals:
    pass
                    self.exit_signals[trade_id] = []
                
                self.exit_signals[trade_id].extend(new_signals)
                
                # Keep only recent signals (last 20)
                self.exit_signals[trade_id] = self.exit_signals[trade_id][-20:]
    
    def _create_trades_overview(self):
    pass
        """Create trades overview component."""
        cards = []
        
        for trade in self.sample_trades:
    pass
            symbol = trade["symbol"]
            current_price = self.current_prices.get(symbol, trade["entry_price"])
            
            # Calculate P&L
            if trade["direction"] == "long":
    pass
                pnl_pct = ((current_price - trade["entry_price"]) / trade["entry_price"]) * 100
            else:
    pass
                pnl_pct = ((trade["entry_price"] - current_price) / trade["entry_price"]) * 100
            
            pnl_color = "success" if pnl_pct >= 0 else "danger"
            
            card = dbc.Card([
                dbc.CardBody([
                    html.H6(f"{trade['id']}", className="card-title"),
                    html.P([
                        html.Strong(f"{symbol} "),
                        html.Span(f"({trade['direction'].upper()})", 
                                 className=f"text-{'success' if trade['direction'] == 'long' else 'warning'}")
                    ], className="mb-1"),
                    html.P([
                        html.Strong("Entry: "),
                        html.Span(f"{trade['entry_price']:.4f}")
                    ], className="mb-1"),
                    html.P([
                        html.Strong("Current: "),
                        html.Span(f"{current_price:.4f}")
                    ], className="mb-1"),
                    html.P([
                        html.Strong("P&L: "),
                        html.Span(f"{pnl_pct:+.2f}%", className=f"text-{pnl_color}")
                    ], className="mb-0")
                ])
            ], className="mb-2")
            
            cards.append(card)
        
        return cards
    
    def _create_signals_overview(self):
    pass
        """Create exit signals overview component."""
        total_signals = sum(len(signals) for signals in self.exit_signals.values())
        recent_signals = []
        
        # Get most recent signals across all trades
        for _, signals in self.exit_signals.items():
    pass
            recent_signals.extend(signals[-3:])  # Last 3 signals per trade
        
        # Sort by timestamp (most recent first)
        recent_signals.sort(key=lambda x: x.timestamp, reverse=True)
        recent_signals = recent_signals[:5]  # Top 5 most recent
        
        signal_items = []
        
        for signal in recent_signals:
    pass
            signal_color = "success" if signal.exit_reason in [
                ExitReason.TAKE_PROFIT_HIT, ExitReason.TARGET_REACHED
            ] else "warning"
            
            item = html.Div([
                html.P([
                    html.Strong(f"{signal.position_id}: "),
                    html.Span(signal.exit_reason.value.replace("_", " ").title(),
                             className=f"text-{signal_color}")
                ], className="mb-1"),
                html.Small(f"{signal.timestamp.strftime('%H:%M:%S')}", 
                          className="text-muted")
            ], className="mb-2")
            
            signal_items.append(item)
        
        if not signal_items:
    pass
            signal_items = [html.P("No recent signals", className="text-muted")]
        
        return [
            html.P([
                html.Strong("Total Signals: "),
                html.Span(str(total_signals))
            ], className="mb-3"),
            html.H6("Recent Signals:", className="mb-2"),
            *signal_items
        ]
    
    def _create_performance_overview(self):
    pass
        """Create strategy performance overview."""
        # Calculate performance metrics
        total_trades = len(self.sample_trades)
        total_signals = sum(len(signals) for signals in self.exit_signals.values())
        
        # Count signal types
        signal_types = {}
        for signals in self.exit_signals.values():
    pass
            for signal in signals:
    pass
                signal_type = signal.exit_type.value
                signal_types[signal_type] = signal_types.get(signal_type, 0) + 1
        
        performance_items = [
            html.P([
                html.Strong("Active Trades: "),
                html.Span(str(total_trades))
            ]),
            html.P([
                html.Strong("Total Signals: "),
                html.Span(str(total_signals))
            ]),
            html.Hr(),
            html.H6("Signal Types:", className="mb-2")
        ]
        
        for signal_type, count in signal_types.items():
    pass
            performance_items.append(
                html.P([
                    html.Span(signal_type.replace("_", " ").title() + ": "),
                    html.Strong(str(count))
                ], className="mb-1")
            )
        
        return performance_items
    
    def _create_trade_chart(self, trade_id):
    pass
        """Create trade chart with exit levels and signals."""
        if not trade_id:
    pass
            return go.Figure()
        
        # Find the trade
        trade = next((t for t in self.sample_trades if t["id"] == trade_id), None)
        if not trade:
    pass
            return go.Figure()
        
        symbol = trade["symbol"]
        if symbol not in self.market_data:
    pass
            return go.Figure()
        
        # Get 1h data for chart
        df = self.market_data[symbol]["1h"].copy()
        
        # Create figure
        fig = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.05,
            row_heights=[0.7, 0.3],
            subplot_titles=(f"{symbol} - {trade_id}", "Volume")
        )
        
        # Add candlestick chart
        fig.add_trace(
            go.Candlestick(
                x=df.index,
                open=df['open'],
                high=df['high'],
                low=df['low'],
                close=df['close'],
                name="Price"
            ),
            row=1, col=1
        )
        
        # Add volume
        colors = ['green' if row['close'] >= row['open'] else 'red' for _, row in df.iterrows()]
        fig.add_trace(
            go.Bar(
                x=df.index,
                y=df['volume'],
                name="Volume",
                marker_color=colors
            ),
            row=2, col=1
        )
        
        # Add entry point
        fig.add_trace(
            go.Scatter(
                x=[trade["entry_time"]],
                y=[trade["entry_price"]],
                mode="markers",
                marker=dict(
                    symbol="star",
                    size=15,
                    color="blue",
                    line=dict(width=2, color="white")
                ),
                name="Entry",
                hovertext=f"Entry: {trade['entry_price']:.4f}"
            ),
            row=1, col=1
        )
        
        # Add stop loss and take profit lines
        fig.add_hline(
            y=trade["stop_loss"],
            line_dash="dash",
            line_color="red",
            annotation_text="Stop Loss",
            row=1, col=1
        )
        
        fig.add_hline(
            y=trade["take_profit"],
            line_dash="dash", 
            line_color="green",
            annotation_text="Take Profit",
            row=1, col=1
        )
        
        # Add exit signals
        if trade_id in self.exit_signals:
    pass
            for signal in self.exit_signals[trade_id]:
    pass
                marker_color = "red" if "stop" in signal.exit_reason.value else "orange"
                
                fig.add_trace(
                    go.Scatter(
                        x=[signal.timestamp],
                        y=[signal.price],
                        mode="markers",
                        marker=dict(
                            symbol="x",
                            size=12,
                            color=marker_color,
                            line=dict(width=2, color="white")
                        ),
                        name=signal.exit_reason.value.replace("_", " ").title(),
                        hovertext=f"{signal.exit_reason.value}<br>Price: {signal.price:.4f}<br>Size: {signal.size_percentage:.1f}%"
                    ),
                    row=1, col=1
                )
        
        # Update layout
        fig.update_layout(
            title=f"{symbol} - {trade_id}",
            xaxis_title="Time",
            yaxis_title="Price",
            template="plotly_dark",
            height=500,
            showlegend=True
        )
        
        return fig
    
    def _create_management_details(self, trade_id):
    pass
        """Create trade management details."""
        if not trade_id:
    pass
            return html.P("Select a trade to view details")
        
        # Get trade summary from exit signal generator
        trade_summary = self.exit_signal_generator.get_trade_summary(trade_id)
        
        if not trade_summary:
    pass
            return html.P("Trade details not available")
        
        details = [
            html.H6("Strategy Status:", className="mb-2")
        ]
        
        # Show status for each strategy
        if isinstance(trade_summary, dict) and "strategies" in trade_summary:
    pass
            for strategy_name, strategy_info in trade_summary["strategies"].items():
    pass
                strategy_title = strategy_name.replace("_", " ").title()
                
                details.append(
                    dbc.Card([
                        dbc.CardHeader(html.H6(strategy_title, className="mb-0")),
                        dbc.CardBody([
                            self._format_strategy_info(strategy_info, strategy_name)
                        ])
                    ], className="mb-2")
                )
        
        # Add signal summary
        details.append(
            html.Div([
                html.Hr(),
                html.P([
                    html.Strong("Total Signals: "),
                    html.Span(str(trade_summary.get("total_signals", 0) if isinstance(trade_summary, dict) else 0))
                ])
            ])
        )
        
        return details
    
    def _format_strategy_info(self, info, strategy_name):
    pass
        """Format strategy information for display."""
        if strategy_name == "adaptive_exits":
    pass
            return [
                html.P([html.Strong("Remaining Size: "), html.Span(f"{info.get('remaining_size', 0):.2f}")]),
                html.P([html.Strong("Partial Exits: "), html.Span(str(len(info.get('partial_exits', []))))]),
                html.P([html.Strong("Breakeven Active: "), html.Span(str(info.get('breakeven_activated', False)))])
            ]
        elif strategy_name == "dynamic_management":
    pass
            return [
                html.P([html.Strong("Health: "), html.Span(info.get('health', 'Unknown').title())]),
                html.P([html.Strong("Performance: "), html.Span(f"{info.get('current_performance_pct', 0):.2f}%")]),
                html.P([html.Strong("Total Exits: "), html.Span(str(info.get('total_exits', 0)))])
            ]
        elif strategy_name == "profit_maximization":
    pass
            return [
                html.P([html.Strong("Highest Profit: "), html.Span(f"{info.get('highest_profit_pct', 0):.2f}%")]),
                html.P([html.Strong("Trailing Active: "), html.Span(str(info.get('trailing_profit_active', False)))]),
                html.P([html.Strong("Momentum Riding: "), html.Span(str(info.get('momentum_riding_active', False)))])
            ]
        else:
    pass
            return [html.P("Strategy information available")]
    
    def _create_signals_table(self, trade_id):
    pass
        """Create signals history table."""
        if not trade_id or trade_id not in self.exit_signals:
    pass
            return html.P("No signals available")
        
        signals = self.exit_signals[trade_id]
        
        if not signals:
    pass
            return html.P("No signals generated yet")
        
        # Prepare data for table
        table_data = []
        for signal in signals[-10:]:  # Last 10 signals
            table_data.append({
                "Time": signal.timestamp.strftime("%H:%M:%S"),
                "Type": signal.exit_type.value.replace("_", " ").title(),
                "Reason": signal.exit_reason.value.replace("_", " ").title(),
                "Price": f"{signal.price:.4f}",
                "Size %": f"{signal.size_percentage:.1f}%",
                "Confidence": f"{signal.confidence:.2f}"
            })
        
        return dash_table.DataTable(
            data=table_data,
            columns=[{"name": col, "id": col} for col in table_data[0].keys()] if table_data else [],
            style_cell={'textAlign': 'left', 'backgroundColor': '#2b3e50', 'color': 'white'},
            style_header={'backgroundColor': '#34495e', 'fontWeight': 'bold'},
            style_data_conditional=[
                {
                    'if': {'filter_query': '{Reason} contains "profit"'},
                    'backgroundColor': '#27ae60',
                    'color': 'white',
                },
                {
                    'if': {'filter_query': '{Reason} contains "stop"'},
                    'backgroundColor': '#e74c3c',
                    'color': 'white',
                }
            ]
        )
    
    def _create_portfolio_chart(self):
    pass
        """Create multi-symbol portfolio overview chart."""
        # Calculate performance for each symbol
        performance_data = {}
        for symbol in self.config["symbols"]:
    pass
            if symbol in self.market_data and symbol in self.current_prices:
    pass
                # Get initial price (first candle in 1h timeframe)
                initial_price = self.market_data[symbol]["1h"]["close"].iloc[0]
                current_price = self.current_prices[symbol]
                
                # Calculate performance
                performance_pct = ((current_price - initial_price) / initial_price) * 100
                performance_data[symbol] = {
                    "symbol": symbol,
                    "initial_price": initial_price,
                    "current_price": current_price,
                    "performance_pct": performance_pct
                }
        
        # Create figure
        fig = go.Figure()
        
        # Add performance bars
        symbols = list(performance_data.keys())
        performance_values = [performance_data[s]["performance_pct"] for s in symbols]
        colors = ["green" if p >= 0 else "red" for p in performance_values]
        
        fig.add_trace(go.Bar(
            x=symbols,
            y=performance_values,
            marker_color=colors,
            text=[f"{p:.2f}%" for p in performance_values],
            textposition="auto"
        ))
        
        # Add correlation heatmap as a second subplot
        if len(symbols) > 1:
    pass
            # Calculate correlation matrix
            price_data = {}
            for symbol in symbols:
    pass
                price_data[symbol] = self.market_data[symbol]["1h"]["close"]
            
            df = pd.DataFrame(price_data)
            corr_matrix = df.corr().values
            
            # Create annotation text
            annotations = []
            for i, symbol1 in enumerate(symbols):
    pass
                for j, symbol2 in enumerate(symbols):
    pass
                    if i != j:  # Skip diagonal
                        annotations.append({
                            "x": j,
                            "y": i,
                            "text": f"{corr_matrix[i, j]:.2f}",
                            "showarrow": False,
                            "font": {"color": "white"}
                        })
            
            # Update layout to include correlation heatmap
            fig.update_layout(
                title="Multi-Symbol Portfolio Performance & Correlation",
                xaxis_title="Symbol",
                yaxis_title="Performance (%)",
                template="plotly_dark",
                height=400,
                annotations=annotations
            )
        else:
    pass
            fig.update_layout(
                title="Symbol Performance",
                xaxis_title="Symbol",
                yaxis_title="Performance (%)",
                template="plotly_dark",
                height=400
            )
        
        return fig
    
    def _handle_error_simulation(self, error_clicks):
    pass
        """Handle error simulation button clicks."""
        # Initialize error state if not exists
        if not hasattr(self, "_error_state"):
    pass
            self._error_state = {
                "last_clicks": 0,
                "error_active": False,
                "error_time": None,
                "recovery_stage": 0,
                "recovery_steps": [
                    "Circuit Breaker Activated",
                    "Health Monitor Alert",
                    "Recovery Manager Engaged",
                    "Attempting Component Restart",
                    "Switching to Fallback Strategy",
                    "System Recovered"
                ]
            }
        
        # Check if button was clicked
        if error_clicks and error_clicks > self._error_state["last_clicks"]:
    pass
            self._error_state["last_clicks"] = error_clicks
            self._error_state["error_active"] = True
            self._error_state["error_time"] = dt.now()
            self._error_state["recovery_stage"] = 0
        
        # If error is active, progress through recovery stages
        if self._error_state["error_active"]:
    pass
            elapsed = (dt.now() - self._error_state["error_time"]).total_seconds()
            
            # Progress through recovery stages (one stage every 3 seconds)
            stage = min(int(elapsed / 3), len(self._error_state["recovery_steps"]) - 1)
            self._error_state["recovery_stage"] = stage
            
            # Check if recovery is complete
            if stage == len(self._error_state["recovery_steps"]) - 1:
    pass
                # Reset after 3 more seconds
                if elapsed > (len(self._error_state["recovery_steps"]) * 3):
    pass
                    self._error_state["error_active"] = False
            
            # Create status message
            status_message = self._error_state["recovery_steps"][stage]
            status_color = "danger" if stage < len(self._error_state["recovery_steps"]) - 1 else "success"
            
            return dbc.Alert(
                status_message,
                color=status_color,
                className="mb-0"
            )
        else:
    pass
            return dbc.Alert(
                "System Healthy - No Errors Detected",
                color="success",
                className="mb-0"
            )
    
    def run(self, debug=False, port=8051):
    pass
        """Run the Dash app."""
        self.app.run_server(debug=debug, port=port)


# Main entry point
if __name__ == "__main__":
    pass
    demo = AdvancedExitStrategiesDemo()
    print("Starting Advanced Exit Strategies Demo...")
    print("Open your browser to http://localhost:8051")
    demo.run(debug=True)
