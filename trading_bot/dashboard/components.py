"""
Elite Trading Bot - Dashboard Components

This module provides the component panels for the Elite Trading Bot dashboard,
including market analysis, performance tracking, risk management, and more.
"""

import logging
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta

try:
    import dash
except ImportError:
    dash = None

try:
    from dash import dcc, html, Input, Output, State
except ImportError:
    dash = None
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np

# Import components
from .risk_panel import RiskPanel
from .signal_panel import SignalPanel
from .analytics_panel import AnalyticsPanel
from .system_panel import SystemPanel

# Configure logging
logger = logging.getLogger(__name__)


from .base_components import ComponentType, ComponentConfig, BaseComponent
import numpy
import pandas

class MarketPanel(BaseComponent):
    """
    Market analysis panel component.
    
    This component displays market data, price charts, and technical indicators.
    """
    
    def __init__(self, config: ComponentConfig):
        """Initialize the market panel."""
        super().__init__(config)
    
    def render(self) -> html.Div:
        """Render the market panel."""
        # Create symbol selector
        symbol_selector = dbc.FormGroup([
            dbc.Label("Symbol"),
            dcc.Dropdown(
                id=f"{self.id}-symbol-selector",
                options=[
                    {"label": "EUR/USD", "value": "EURUSD"},
                    {"label": "GBP/USD", "value": "GBPUSD"},
                    {"label": "USD/JPY", "value": "USDJPY"},
                    {"label": "BTC/USD", "value": "BTCUSD"},
                ],
                value="EURUSD",
                clearable=False
            )
        ])
        
        # Create timeframe selector
        timeframe_selector = dbc.FormGroup([
            dbc.Label("Timeframe"),
            dcc.Dropdown(
                id=f"{self.id}-timeframe-selector",
                options=[
                    {"label": "1 Minute", "value": "1m"},
                    {"label": "5 Minutes", "value": "5m"},
                    {"label": "15 Minutes", "value": "15m"},
                    {"label": "1 Hour", "value": "1h"},
                    {"label": "4 Hours", "value": "4h"},
                    {"label": "Daily", "value": "1d"},
                ],
                value="1h",
                clearable=False
            )
        ])
        
        # Create indicator selector
        indicator_selector = dbc.FormGroup([
            dbc.Label("Indicators"),
            dcc.Dropdown(
                id=f"{self.id}-indicator-selector",
                options=[
                    {"label": "Moving Averages", "value": "ma"},
                    {"label": "Bollinger Bands", "value": "bb"},
                    {"label": "RSI", "value": "rsi"},
                    {"label": "MACD", "value": "macd"},
                    {"label": "Liquidity Zones", "value": "liquidity"},
                    {"label": "Order Blocks", "value": "order_blocks"},
                ],
                value=["ma", "liquidity"],
                multi=True
            )
        ])
        
        # Create price chart
        price_chart = dcc.Graph(
            id=f"{self.id}-price-chart",
            figure=self._create_empty_chart(),
            style={"height": "500px"}
        )
        
        # Create volume chart
        volume_chart = dcc.Graph(
            id=f"{self.id}-volume-chart",
            figure=self._create_empty_volume_chart(),
            style={"height": "200px"}
        )
        
        # Create market data table
        market_data_table = html.Div(
            id=f"{self.id}-market-data",
            children=self._create_market_data_table({})
        )
        
        # Combine all elements
        return html.Div([
            dbc.Row([
                dbc.Col(symbol_selector, width=4),
                dbc.Col(timeframe_selector, width=4),
                dbc.Col(indicator_selector, width=4),
            ], className="mb-4"),
            
            dbc.Row([
                dbc.Col([
                    price_chart
                ], width=12)
            ], className="mb-4"),
            
            dbc.Row([
                dbc.Col([
                    volume_chart
                ], width=12)
            ], className="mb-4"),
            
            dbc.Row([
                dbc.Col([
                    market_data_table
                ], width=12)
            ])
        ], id=f"{self.id}-container")
    
    def _create_empty_chart(self) -> go.Figure:
        """Create an empty price chart."""
        fig = go.Figure()
        fig.update_layout(
            title="Price Chart",
            xaxis_title="Time",
            yaxis_title="Price",
            template="plotly_dark",
            showlegend=True,
            xaxis=dict(
                showgrid=True,
                gridcolor="rgba(255, 255, 255, 0.1)",
            ),
            yaxis=dict(
                showgrid=True,
                gridcolor="rgba(255, 255, 255, 0.1)",
            ),
            plot_bgcolor="rgba(0, 0, 0, 0)",
            paper_bgcolor="rgba(0, 0, 0, 0)",
        )
        
        # Add annotation for empty chart
        fig.add_annotation(
            text="Select symbol and timeframe to load data",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=16)
        )
        
        return fig
    
    def _create_empty_volume_chart(self) -> go.Figure:
        """Create an empty volume chart."""
        fig = go.Figure()
        fig.update_layout(
            title="Volume",
            xaxis_title="Time",
            yaxis_title="Volume",
            template="plotly_dark",
            showlegend=True,
            xaxis=dict(
                showgrid=True,
                gridcolor="rgba(255, 255, 255, 0.1)",
            ),
            yaxis=dict(
                showgrid=True,
                gridcolor="rgba(255, 255, 255, 0.1)",
            ),
            plot_bgcolor="rgba(0, 0, 0, 0)",
            paper_bgcolor="rgba(0, 0, 0, 0)",
        )
        
        return fig
    
    def _create_market_data_table(self, data: Dict[str, Any]) -> html.Table:
        """
        Create a market data table.
        
        Args:
            data: Market data
            
        Returns:
            HTML table
        """
        # Default data if none provided
        if not data:
            data = {
                "open": "N/A",
                "high": "N/A",
                "low": "N/A",
                "close": "N/A",
                "volume": "N/A",
                "spread": "N/A",
                "daily_change": "N/A",
                "daily_range": "N/A",
                "atr": "N/A",
                "volatility": "N/A"
            }
        
        # Create table
        table = dbc.Table([
            html.Thead([
                html.Tr([
                    html.Th("Open"),
                    html.Th("High"),
                    html.Th("Low"),
                    html.Th("Close"),
                    html.Th("Volume"),
                    html.Th("Spread"),
                    html.Th("Daily Change"),
                    html.Th("Daily Range"),
                    html.Th("ATR"),
                    html.Th("Volatility"),
                ])
            ]),
            html.Tbody([
                html.Tr([
                    html.Td(data.get("open", "N/A")),
                    html.Td(data.get("high", "N/A")),
                    html.Td(data.get("low", "N/A")),
                    html.Td(data.get("close", "N/A")),
                    html.Td(data.get("volume", "N/A")),
                    html.Td(data.get("spread", "N/A")),
                    html.Td(data.get("daily_change", "N/A")),
                    html.Td(data.get("daily_range", "N/A")),
                    html.Td(data.get("atr", "N/A")),
                    html.Td(data.get("volatility", "N/A")),
                ])
            ])
        ], bordered=True, hover=True, responsive=True, striped=True)
        
        return table


class PerformancePanel(BaseComponent):
    """
    Trading performance panel component.
    
    This component displays trading performance metrics, equity curve, and statistics.
    """
    
    def __init__(self, config: ComponentConfig):
        """Initialize the performance panel."""
        super().__init__(config)
    
    def render(self) -> html.Div:
        """Render the performance panel."""
        # Create time period selector
        period_selector = dbc.FormGroup([
            dbc.Label("Time Period"),
            dcc.Dropdown(
                id=f"{self.id}-period-selector",
                options=[
                    {"label": "Today", "value": "today"},
                    {"label": "This Week", "value": "week"},
                    {"label": "This Month", "value": "month"},
                    {"label": "This Year", "value": "year"},
                    {"label": "All Time", "value": "all"},
                ],
                value="month",
                clearable=False
            )
        ])
        
        # Create equity curve chart
        equity_chart = dcc.Graph(
            id=f"{self.id}-equity-chart",
            figure=self._create_empty_equity_chart(),
            style={"height": "400px"}
        )
        
        # Create performance metrics cards
        metrics_cards = self._create_performance_metrics({})
        
        # Create trade history table
        trade_history = html.Div(
            id=f"{self.id}-trade-history",
            children=self._create_trade_history_table([])
        )
        
        # Combine all elements
        return html.Div([
            dbc.Row([
                dbc.Col(period_selector, width=4),
                dbc.Col(width=8)  # Empty column for alignment
            ], className="mb-4"),
            
            dbc.Row([
                dbc.Col([
                    equity_chart
                ], width=12)
            ], className="mb-4"),
            
            dbc.Row([
                dbc.Col([
                    metrics_cards
                ], width=12)
            ], className="mb-4"),
            
            dbc.Row([
                dbc.Col([
                    html.H5("Trade History"),
                    trade_history
                ], width=12)
            ])
        ], id=f"{self.id}-container")
    
    def _create_empty_equity_chart(self) -> go.Figure:
        """Create an empty equity curve chart."""
        fig = go.Figure()
        fig.update_layout(
            title="Equity Curve",
            xaxis_title="Time",
            yaxis_title="Equity",
            template="plotly_dark",
            showlegend=True,
            xaxis=dict(
                showgrid=True,
                gridcolor="rgba(255, 255, 255, 0.1)",
            ),
            yaxis=dict(
                showgrid=True,
                gridcolor="rgba(255, 255, 255, 0.1)",
            ),
            plot_bgcolor="rgba(0, 0, 0, 0)",
            paper_bgcolor="rgba(0, 0, 0, 0)",
        )
        
        # Add annotation for empty chart
        fig.add_annotation(
            text="Select time period to load data",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=16)
        )
        
        return fig
    
    def _create_performance_metrics(self, data: Dict[str, Any]) -> html.Div:
        """
        Create performance metrics cards.
        
        Args:
            data: Performance data
            
        Returns:
            Div with metric cards
        """
        # Default data if none provided
        if not data:
            data = {
                "total_profit": "N/A",
                "win_rate": "N/A",
                "profit_factor": "N/A",
                "max_drawdown": "N/A",
                "sharpe_ratio": "N/A",
                "total_trades": "N/A",
                "avg_trade": "N/A",
                "best_trade": "N/A",
                "worst_trade": "N/A",
                "avg_holding_time": "N/A"
            }
        
        # Create metric cards
        return dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H5("Total Profit", className="card-title"),
                        html.H3(data.get("total_profit", "N/A"), className="text-success")
                    ])
                ])
            ], width=2),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H5("Win Rate", className="card-title"),
                        html.H3(data.get("win_rate", "N/A"), className="text-info")
                    ])
                ])
            ], width=2),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H5("Profit Factor", className="card-title"),
                        html.H3(data.get("profit_factor", "N/A"), className="text-info")
                    ])
                ])
            ], width=2),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H5("Max Drawdown", className="card-title"),
                        html.H3(data.get("max_drawdown", "N/A"), className="text-danger")
                    ])
                ])
            ], width=2),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H5("Sharpe Ratio", className="card-title"),
                        html.H3(data.get("sharpe_ratio", "N/A"), className="text-info")
                    ])
                ])
            ], width=2),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H5("Total Trades", className="card-title"),
                        html.H3(data.get("total_trades", "N/A"), className="text-primary")
                    ])
                ])
            ], width=2),
        ])
    
    def _create_trade_history_table(self, trades: List[Dict[str, Any]]) -> html.Table:
        """
        Create a trade history table.
        
        Args:
            trades: List of trade data
            
        Returns:
            HTML table
        """
        # Create default trades if none provided
        if not trades:
            trades = []
        
        # Create table header
        header = html.Thead([
            html.Tr([
                html.Th("ID"),
                html.Th("Symbol"),
                html.Th("Type"),
                html.Th("Entry Time"),
                html.Th("Entry Price"),
                html.Th("Exit Time"),
                html.Th("Exit Price"),
                html.Th("Size"),
                html.Th("Profit/Loss"),
                html.Th("Status"),
            ])
        ])
        
        # Create table rows
        rows = []
        for trade in trades:
            # Determine profit/loss class
            pnl_class = ""
            if trade.get("profit_loss", 0) > 0:
                pnl_class = "text-success"
            elif trade.get("profit_loss", 0) < 0:
                pnl_class = "text-danger"
            
            # Create row
            row = html.Tr([
                html.Td(trade.get("id", "")),
                html.Td(trade.get("symbol", "")),
                html.Td(trade.get("type", "")),
                html.Td(trade.get("entry_time", "")),
                html.Td(trade.get("entry_price", "")),
                html.Td(trade.get("exit_time", "")),
                html.Td(trade.get("exit_price", "")),
                html.Td(trade.get("size", "")),
                html.Td(trade.get("profit_loss", ""), className=pnl_class),
                html.Td(trade.get("status", "")),
            ])
            rows.append(row)
        
        # If no trades, add a placeholder row
        if not rows:
            rows = [html.Tr([html.Td("No trades found", colSpan=10, className="text-center")])]
        
        # Create table body
        body = html.Tbody(rows)
        
        # Create table
        table = dbc.Table([header, body], bordered=True, hover=True, responsive=True, striped=True)
        
        return table
