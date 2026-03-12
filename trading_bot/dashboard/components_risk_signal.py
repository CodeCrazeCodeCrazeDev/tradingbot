"""
Elite Trading Bot - Risk and Signal Dashboard Components

This module provides the risk management and signal panel components
for the Elite Trading Bot dashboard.
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

from .components import BaseComponent, ComponentConfig, ComponentType
import numpy
import pandas

# Configure logging
logger = logging.getLogger(__name__)


class RiskPanel(BaseComponent):
    """
    Risk management panel component.
    
    This component displays risk metrics, position sizing, and risk controls.
    """
    
    def __init__(self, config: ComponentConfig):
        """Initialize the risk panel."""
        super().__init__(config)
    
    def render(self) -> html.Div:
        """Render the risk panel."""
        # Create risk overview cards
        risk_overview = self._create_risk_overview({})
        
        # Create position sizing calculator
        position_sizing = self._create_position_sizing_calculator()
        
        # Create risk allocation chart
        risk_allocation_chart = dcc.Graph(
            id=f"{self.id}-risk-allocation-chart",
            figure=self._create_risk_allocation_chart({}),
            style={"height": "400px"}
        )
        
        # Create VaR chart
        var_chart = dcc.Graph(
            id=f"{self.id}-var-chart",
            figure=self._create_var_chart({}),
            style={"height": "300px"}
        )
        
        # Create black swan protection status
        black_swan_status = self._create_black_swan_status({})
        
        # Combine all elements
        return html.Div([
            dbc.Row([
                dbc.Col([
                    html.H5("Risk Overview"),
                    risk_overview
                ], width=12)
            ], className="mb-4"),
            
            dbc.Row([
                dbc.Col([
                    html.H5("Position Sizing Calculator"),
                    position_sizing
                ], width=6),
                
                dbc.Col([
                    html.H5("Risk Allocation"),
                    risk_allocation_chart
                ], width=6)
            ], className="mb-4"),
            
            dbc.Row([
                dbc.Col([
                    html.H5("Value at Risk (VaR)"),
                    var_chart
                ], width=6),
                
                dbc.Col([
                    html.H5("Black Swan Protection"),
                    black_swan_status
                ], width=6)
            ])
        ], id=f"{self.id}-container")
    
    def _create_risk_overview(self, data: Dict[str, Any]) -> html.Div:
        """
        Create risk overview cards.
        
        Args:
            data: Risk data
            
        Returns:
            Div with risk metric cards
        """
        # Default data if none provided
        if not data:
            data = {
                "account_balance": "N/A",
                "margin_used": "N/A",
                "free_margin": "N/A",
                "margin_level": "N/A",
                "daily_drawdown": "N/A",
                "risk_exposure": "N/A",
                "risk_per_trade": "N/A",
                "portfolio_heat": "N/A",
                "risk_reward_ratio": "N/A",
                "risk_level": "N/A"
            }
        
        # Determine risk level class
        risk_level_class = "text-info"
        risk_level = data.get("risk_level", "").lower()
        if risk_level == "low":
            risk_level_class = "text-success"
        elif risk_level == "medium":
            risk_level_class = "text-warning"
        elif risk_level == "high":
            risk_level_class = "text-danger"
        
        # Create metric cards
        return dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H5("Account Balance", className="card-title"),
                        html.H3(data.get("account_balance", "N/A"), className="text-primary")
                    ])
                ])
            ], width=2),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H5("Margin Used", className="card-title"),
                        html.H3(data.get("margin_used", "N/A"), className="text-warning")
                    ])
                ])
            ], width=2),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H5("Free Margin", className="card-title"),
                        html.H3(data.get("free_margin", "N/A"), className="text-success")
                    ])
                ])
            ], width=2),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H5("Daily Drawdown", className="card-title"),
                        html.H3(data.get("daily_drawdown", "N/A"), className="text-danger")
                    ])
                ])
            ], width=2),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H5("Portfolio Heat", className="card-title"),
                        html.H3(data.get("portfolio_heat", "N/A"), className="text-warning")
                    ])
                ])
            ], width=2),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H5("Risk Level", className="card-title"),
                        html.H3(data.get("risk_level", "N/A"), className=risk_level_class)
                    ])
                ])
            ], width=2),
        ])
    
    def _create_position_sizing_calculator(self) -> html.Div:
        """
        Create position sizing calculator.
        
        Returns:
            Position sizing calculator component
        """
        return dbc.Card([
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        dbc.FormGroup([
                            dbc.Label("Account Balance"),
                            dbc.InputGroup([
                                dbc.Input(
                                    id=f"{self.id}-account-balance",
                                    type="number",
                                    value=10000,
                                    min=0
                                ),
                                dbc.InputGroupAddon("$", addon_type="append")
                            ])
                        ])
                    ], width=6),
                    
                    dbc.Col([
                        dbc.FormGroup([
                            dbc.Label("Risk Per Trade (%)"),
                            dbc.InputGroup([
                                dbc.Input(
                                    id=f"{self.id}-risk-percent",
                                    type="number",
                                    value=1,
                                    min=0,
                                    max=100,
                                    step=0.1
                                ),
                                dbc.InputGroupAddon("%", addon_type="append")
                            ])
                        ])
                    ], width=6)
                ]),
                
                dbc.Row([
                    dbc.Col([
                        dbc.FormGroup([
                            dbc.Label("Entry Price"),
                            dbc.Input(
                                id=f"{self.id}-entry-price",
                                type="number",
                                value=1.1000,
                                step=0.0001,
                                min=0
                            )
                        ])
                    ], width=4),
                    
                    dbc.Col([
                        dbc.FormGroup([
                            dbc.Label("Stop Loss Price"),
                            dbc.Input(
                                id=f"{self.id}-stop-loss-price",
                                type="number",
                                value=1.0950,
                                step=0.0001,
                                min=0
                            )
                        ])
                    ], width=4),
                    
                    dbc.Col([
                        dbc.FormGroup([
                            dbc.Label("Position Sizing Method"),
                            dcc.Dropdown(
                                id=f"{self.id}-position-sizing-method",
                                options=[
                                    {"label": "Fixed Risk", "value": "fixed_risk"},
                                    {"label": "Fixed Fractional", "value": "fixed_fractional"},
                                    {"label": "Kelly Criterion", "value": "kelly"},
                                    {"label": "Optimal F", "value": "optimal_f"},
                                    {"label": "Volatility-Based", "value": "volatility"}
                                ],
                                value="fixed_risk",
                                clearable=False
                            )
                        ])
                    ], width=4)
                ]),
                
                dbc.Row([
                    dbc.Col([
                        dbc.Button(
                            "Calculate Position Size",
                            id=f"{self.id}-calculate-button",
                            color="primary",
                            block=True
                        )
                    ], width=12)
                ], className="mb-3"),
                
                dbc.Row([
                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                html.H5("Position Size", className="card-title"),
                                html.H3("0.5 lots", id=f"{self.id}-position-size-result", className="text-primary")
                            ])
                        ])
                    ], width=4),
                    
                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                html.H5("Risk Amount", className="card-title"),
                                html.H3("$100.00", id=f"{self.id}-risk-amount-result", className="text-danger")
                            ])
                        ])
                    ], width=4),
                    
                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                html.H5("Risk/Reward Ratio", className="card-title"),
                                html.H3("1:2", id=f"{self.id}-risk-reward-result", className="text-info")
                            ])
                        ])
                    ], width=4)
                ])
            ])
        ])
    
    def _create_risk_allocation_chart(self, data: Dict[str, Any]) -> go.Figure:
        """
        Create risk allocation chart.
        
        Args:
            data: Risk allocation data
            
        Returns:
            Plotly figure
        """
        # Default data if none provided
        if not data:
            data = {
                "categories": ["EURUSD", "GBPUSD", "USDJPY", "BTCUSD", "XAUUSD"],
                "values": [30, 25, 20, 15, 10]
            }
        
        # Create pie chart
        fig = go.Figure(data=[go.Pie(
            labels=data.get("categories", []),
            values=data.get("values", []),
            hole=0.4,
            textinfo="label+percent",
            insidetextorientation="radial"
        )])
        
        # Update layout
        fig.update_layout(
            title="Portfolio Risk Allocation",
            template="plotly_dark",
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.2,
                xanchor="center",
                x=0.5
            ),
            plot_bgcolor="rgba(0, 0, 0, 0)",
            paper_bgcolor="rgba(0, 0, 0, 0)",
        )
        
        return fig
    
    def _create_var_chart(self, data: Dict[str, Any]) -> go.Figure:
        """
        Create Value at Risk (VaR) chart.
        
        Args:
            data: VaR data
            
        Returns:
            Plotly figure
        """
        # Default data if none provided
        if not data:
            data = {
                "dates": [str(datetime.now().date() - timedelta(days=i)) for i in range(30, 0, -1)],
                "var_95": [round(100 + i * 2 + np.random.normal(0, 10), 2) for i in range(30)],
                "var_99": [round(150 + i * 2 + np.random.normal(0, 15), 2) for i in range(30)],
                "actual_loss": [round(50 + i * 1.5 + np.random.normal(0, 30), 2) for i in range(30)]
            }
        
        # Create figure
        fig = go.Figure()
        
        # Add VaR lines
        fig.add_trace(go.Scatter(
            x=data.get("dates", []),
            y=data.get("var_95", []),
            mode="lines",
            name="95% VaR",
            line=dict(color="orange", width=2)
        ))
        
        fig.add_trace(go.Scatter(
            x=data.get("dates", []),
            y=data.get("var_99", []),
            mode="lines",
            name="99% VaR",
            line=dict(color="red", width=2)
        ))
        
        # Add actual loss as bar chart
        fig.add_trace(go.Bar(
            x=data.get("dates", []),
            y=data.get("actual_loss", []),
            name="Actual Loss",
            marker_color="rgba(0, 123, 255, 0.7)"
        ))
        
        # Update layout
        fig.update_layout(
            title="Value at Risk (VaR) vs. Actual Loss",
            xaxis_title="Date",
            yaxis_title="Amount ($)",
            template="plotly_dark",
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            plot_bgcolor="rgba(0, 0, 0, 0)",
            paper_bgcolor="rgba(0, 0, 0, 0)",
        )
        
        return fig
    
    def _create_black_swan_status(self, data: Dict[str, Any]) -> html.Div:
        """
        Create black swan protection status component.
        
        Args:
            data: Black swan protection data
            
        Returns:
            Black swan protection status component
        """
        # Default data if none provided
        if not data:
            data = {
                "protection_level": "Medium",
                "tail_risk_score": 0.35,
                "volatility_regime": "Normal",
                "correlation_status": "Stable",
                "gap_risk": "Low",
                "hedging_status": "Active",
                "alerts": [
                    {"level": "info", "message": "Volatility slightly elevated in EURUSD"},
                    {"level": "warning", "message": "Correlation breakdown detected in commodity pairs"}
                ]
            }
        
        # Determine protection level class
        protection_level = data.get("protection_level", "").lower()
        protection_class = "text-info"
        if protection_level == "high":
            protection_class = "text-success"
        elif protection_level == "medium":
            protection_class = "text-warning"
        elif protection_level == "low":
            protection_class = "text-danger"
        
        # Create status indicators
        status_indicators = dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H5("Protection Level", className="card-title"),
                        html.H3(data.get("protection_level", "N/A"), className=protection_class)
                    ])
                ])
            ], width=6),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H5("Tail Risk Score", className="card-title"),
                        html.H3(data.get("tail_risk_score", "N/A"), className="text-info")
                    ])
                ])
            ], width=6)
        ], className="mb-3")
        
        # Create status table
        status_table = dbc.Table([
            html.Thead([
                html.Tr([
                    html.Th("Metric"),
                    html.Th("Status")
                ])
            ]),
            html.Tbody([
                html.Tr([
                    html.Td("Volatility Regime"),
                    html.Td(data.get("volatility_regime", "N/A"))
                ]),
                html.Tr([
                    html.Td("Correlation Status"),
                    html.Td(data.get("correlation_status", "N/A"))
                ]),
                html.Tr([
                    html.Td("Gap Risk"),
                    html.Td(data.get("gap_risk", "N/A"))
                ]),
                html.Tr([
                    html.Td("Hedging Status"),
                    html.Td(data.get("hedging_status", "N/A"))
                ])
            ])
        ], bordered=True, hover=True, responsive=True, striped=True, className="mb-3")
        
        # Create alerts
        alerts = []
        for alert in data.get("alerts", []):
            level = alert.get("level", "info").lower()
            color = "info"
            if level == "warning":
                color = "warning"
            elif level == "danger":
                color = "danger"
            
            alerts.append(
                dbc.Alert(
                    alert.get("message", ""),
                    color=color,
                    className="mb-2"
                )
            )
        
        # If no alerts, add a placeholder
        if not alerts:
            alerts = [dbc.Alert("No active alerts", color="success")]
        
        # Combine all elements
        return html.Div([
            status_indicators,
            status_table,
            html.H6("Active Alerts"),
            html.Div(alerts)
        ])


class SignalPanel(BaseComponent):
    """
    Trading signals panel component.
    
    This component displays trading signals, entry/exit points, and signal analysis.
    """
    
    def __init__(self, config: ComponentConfig):
        """Initialize the signal panel."""
        super().__init__(config)
    
    def render(self) -> html.Div:
        """Render the signal panel."""
        # Create symbol and timeframe selectors
        selectors = dbc.Row([
            dbc.Col([
                dbc.FormGroup([
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
            ], width=4),
            
            dbc.Col([
                dbc.FormGroup([
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
            ], width=4),
            
            dbc.Col([
                dbc.FormGroup([
                    dbc.Label("Signal Type"),
                    dcc.Dropdown(
                        id=f"{self.id}-signal-type-selector",
                        options=[
                            {"label": "All Signals", "value": "all"},
                            {"label": "Entry Signals", "value": "entry"},
                            {"label": "Exit Signals", "value": "exit"},
                            {"label": "Strong Signals Only", "value": "strong"},
                        ],
                        value="all",
                        clearable=False
                    )
                ])
            ], width=4)
        ], className="mb-4")
        
        # Create signal chart
        signal_chart = dcc.Graph(
            id=f"{self.id}-signal-chart",
            figure=self._create_empty_signal_chart(),
            style={"height": "500px"}
        )
        
        # Create active signals table
        active_signals = html.Div(
            id=f"{self.id}-active-signals",
            children=self._create_active_signals_table([])
        )
        
        # Create signal history table
        signal_history = html.Div(
            id=f"{self.id}-signal-history",
            children=self._create_signal_history_table([])
        )
        
        # Combine all elements
        return html.Div([
            selectors,
            
            dbc.Row([
                dbc.Col([
                    signal_chart
                ], width=12)
            ], className="mb-4"),
            
            dbc.Row([
                dbc.Col([
                    html.H5("Active Signals"),
                    active_signals
                ], width=12)
            ], className="mb-4"),
            
            dbc.Row([
                dbc.Col([
                    html.H5("Signal History"),
                    signal_history
                ], width=12)
            ])
        ], id=f"{self.id}-container")
    
    def _create_empty_signal_chart(self) -> go.Figure:
        """Create an empty signal chart."""
        fig = go.Figure()
        fig.update_layout(
            title="Trading Signals",
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
            text="Select symbol and timeframe to load signals",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=16)
        )
        
        return fig
    
    def _create_active_signals_table(self, signals: List[Dict[str, Any]]) -> html.Table:
        """
        Create active signals table.
        
        Args:
            signals: List of active signal data
            
        Returns:
            HTML table
        """
        # Create table header
        header = html.Thead([
            html.Tr([
                html.Th("Symbol"),
                html.Th("Type"),
                html.Th("Direction"),
                html.Th("Timeframe"),
                html.Th("Price"),
                html.Th("Time"),
                html.Th("Strength"),
                html.Th("Source"),
                html.Th("Actions")
            ])
        ])
        
        # Create table rows
        rows = []
        for signal in signals:
            # Determine signal direction class
            direction_class = ""
            if signal.get("direction", "").lower() == "buy":
                direction_class = "text-success"
            elif signal.get("direction", "").lower() == "sell":
                direction_class = "text-danger"
            
            # Determine signal strength class
            strength_class = "text-info"
            strength = signal.get("strength", "").lower()
            if strength == "strong":
                strength_class = "text-success"
            elif strength == "moderate":
                strength_class = "text-warning"
            elif strength == "weak":
                strength_class = "text-danger"
            
            # Create row
            row = html.Tr([
                html.Td(signal.get("symbol", "")),
                html.Td(signal.get("type", "")),
                html.Td(signal.get("direction", ""), className=direction_class),
                html.Td(signal.get("timeframe", "")),
                html.Td(signal.get("price", "")),
                html.Td(signal.get("time", "")),
                html.Td(signal.get("strength", ""), className=strength_class),
                html.Td(signal.get("source", "")),
                html.Td([
                    dbc.Button("View", color="primary", size="sm", className="mr-1"),
                    dbc.Button("Trade", color="success", size="sm")
                ])
            ])
            rows.append(row)
        
        # If no signals, add a placeholder row
        if not rows:
            rows = [html.Tr([html.Td("No active signals", colSpan=9, className="text-center")])]
        
        # Create table body
        body = html.Tbody(rows)
        
        # Create table
        table = dbc.Table([header, body], bordered=True, hover=True, responsive=True, striped=True)
        
        return table
    
    def _create_signal_history_table(self, signals: List[Dict[str, Any]]) -> html.Table:
        """
        Create signal history table.
        
        Args:
            signals: List of historical signal data
            
        Returns:
            HTML table
        """
        # Create table header
        header = html.Thead([
            html.Tr([
                html.Th("Symbol"),
                html.Th("Type"),
                html.Th("Direction"),
                html.Th("Timeframe"),
                html.Th("Price"),
                html.Th("Time"),
                html.Th("Result"),
                html.Th("Profit/Loss"),
                html.Th("Actions")
            ])
        ])
        
        # Create table rows
        rows = []
        for signal in signals:
            # Determine signal direction class
            direction_class = ""
            if signal.get("direction", "").lower() == "buy":
                direction_class = "text-success"
            elif signal.get("direction", "").lower() == "sell":
                direction_class = "text-danger"
            
            # Determine result class
            result_class = ""
            result = signal.get("result", "").lower()
            if result == "win":
                result_class = "text-success"
            elif result == "loss":
                result_class = "text-danger"
            
            # Determine profit/loss class
            pnl_class = ""
            pnl = signal.get("profit_loss", 0)
            if pnl > 0:
                pnl_class = "text-success"
            elif pnl < 0:
                pnl_class = "text-danger"
            
            # Create row
            row = html.Tr([
                html.Td(signal.get("symbol", "")),
                html.Td(signal.get("type", "")),
                html.Td(signal.get("direction", ""), className=direction_class),
                html.Td(signal.get("timeframe", "")),
                html.Td(signal.get("price", "")),
                html.Td(signal.get("time", "")),
                html.Td(signal.get("result", ""), className=result_class),
                html.Td(signal.get("profit_loss", ""), className=pnl_class),
                html.Td([
                    dbc.Button("View", color="primary", size="sm", className="mr-1"),
                    dbc.Button("Details", color="info", size="sm")
                ])
            ])
            rows.append(row)
        
        # If no signals, add a placeholder row
        if not rows:
            rows = [html.Tr([html.Td("No signal history", colSpan=9, className="text-center")])]
        
        # Create table body
        body = html.Tbody(rows)
        
        # Create table
        table = dbc.Table([header, body], bordered=True, hover=True, responsive=True, striped=True)
        
        return table
