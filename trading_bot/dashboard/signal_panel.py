"""
Signal Panel Component
"""

try:
    import dash
except ImportError:
    dash = None

try:
    from dash import dcc, html
except ImportError:
    dash = None
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from typing import Any, Dict, List, Optional
from datetime import datetime

from .base_components import BaseComponent, ComponentConfig
import numpy
import pandas

import logging
logger = logging.getLogger(__name__)



class SignalPanel(BaseComponent):
    """
    Trading signal panel component.
    
    Displays trading signals, predictions, and strategy insights.
    """
    
    def __init__(self, config: ComponentConfig):
        """Initialize the signal panel."""
        super().__init__(config)
    
    def render(self) -> html.Div:
        """Render the signal panel."""
        # Create signal summary cards
        signal_summary = self._create_signal_summary({})
        
        # Create signal chart
        signal_chart = dcc.Graph(
            id=f"{self.id}-signal-chart",
            figure=self._create_empty_signal_chart(),
            style={"height": "400px"}
        )
        
        # Create signal table
        signal_table = html.Div(
            id=f"{self.id}-signal-table",
            children=self._create_signal_table([])
        )
        
        # Create strategy insights
        strategy_insights = html.Div(
            id=f"{self.id}-strategy-insights",
            children=self._create_strategy_insights({})
        )
        
        # Combine all elements
        return html.Div([
            dbc.Row([
                dbc.Col([
                    signal_summary
                ], width=12)
            ], className="mb-4"),
            
            dbc.Row([
                dbc.Col([
                    signal_chart
                ], width=12)
            ], className="mb-4"),
            
            dbc.Row([
                dbc.Col([
                    html.H5("Active Signals"),
                    signal_table
                ], width=6),
                
                dbc.Col([
                    html.H5("Strategy Insights"),
                    strategy_insights
                ], width=6)
            ])
        ], id=f"{self.id}-container")
    
    def _create_signal_summary(self, data: Dict[str, Any]) -> html.Div:
        """Create signal summary cards."""
        # Default data if none provided
        if not data:
            data = {
                "total_signals": "N/A",
                "active_signals": "N/A",
                "signal_accuracy": "N/A",
                "avg_confidence": "N/A",
                "profitable_signals": "N/A",
                "signal_win_rate": "N/A"
            }
        
        # Create metric cards
        return dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H5("Total Signals", className="card-title"),
                        html.H3(data.get("total_signals", "N/A"))
                    ])
                ])
            ], width=2),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H5("Active Signals", className="card-title"),
                        html.H3(data.get("active_signals", "N/A"))
                    ])
                ])
            ], width=2),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H5("Signal Accuracy", className="card-title"),
                        html.H3(data.get("signal_accuracy", "N/A"))
                    ])
                ])
            ], width=2),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H5("Avg Confidence", className="card-title"),
                        html.H3(data.get("avg_confidence", "N/A"))
                    ])
                ])
            ], width=2),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H5("Profitable Signals", className="card-title"),
                        html.H3(data.get("profitable_signals", "N/A"))
                    ])
                ])
            ], width=2),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H5("Signal Win Rate", className="card-title"),
                        html.H3(data.get("signal_win_rate", "N/A"))
                    ])
                ])
            ], width=2),
        ])
    
    def _create_empty_signal_chart(self) -> go.Figure:
        """Create an empty signal chart."""
        fig = go.Figure()
        fig.update_layout(
            title="Signal Distribution",
            xaxis_title="Signal Type",
            yaxis_title="Count",
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
            text="No signal data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=16)
        )
        
        return fig
    
    def _create_signal_table(self, signals: List[Dict[str, Any]]) -> html.Table:
        """Create signal table."""
        # Create default signals if none provided
        if not signals:
            signals = []
        
        # Create table header
        header = html.Thead([
            html.Tr([
                html.Th("Time"),
                html.Th("Symbol"),
                html.Th("Signal"),
                html.Th("Direction"),
                html.Th("Confidence"),
                html.Th("Strategy"),
                html.Th("Status"),
            ])
        ])
        
        # Create table rows
        rows = []
        for signal in signals:
            # Determine signal class
            signal_class = ""
            if signal.get("direction", "").lower() == "buy":
                signal_class = "text-success"
            elif signal.get("direction", "").lower() == "sell":
                signal_class = "text-danger"
            
            # Create row
            row = html.Tr([
                html.Td(signal.get("time", "")),
                html.Td(signal.get("symbol", "")),
                html.Td(signal.get("signal", "")),
                html.Td(signal.get("direction", ""), className=signal_class),
                html.Td(f"{signal.get('confidence', 0):.2%}"),
                html.Td(signal.get("strategy", "")),
                html.Td(signal.get("status", "")),
            ])
            rows.append(row)
        
        # If no signals, add a placeholder row
        if not rows:
            rows = [html.Tr([html.Td("No active signals", colSpan=7, className="text-center")])]
        
        # Create table body
        body = html.Tbody(rows)
        
        # Create table
        table = dbc.Table([header, body], bordered=True, hover=True, responsive=True, striped=True)
        
        return table
    
    def _create_strategy_insights(self, data: Dict[str, Any]) -> html.Div:
        """Create strategy insights."""
        # Default data if none provided
        if not data:
            data = {
                "top_strategies": [],
                "market_regime": "N/A",
                "sentiment": "N/A",
                "volatility": "N/A",
                "recommendations": []
            }
        
        # Create insights
        insights = []
        
        # Add top strategies
        if data.get("top_strategies"):
            insights.append(html.Div([
                html.H6("Top Performing Strategies"),
                html.Ul([
                    html.Li(f"{strategy}: {performance:.2%}")
                    for strategy, performance in data["top_strategies"]
                ])
            ], className="mb-3"))
        
        # Add market conditions
        insights.append(html.Div([
            html.H6("Market Conditions"),
            dbc.ListGroup([
                dbc.ListGroupItem([
                    html.Strong("Market Regime: "),
                    html.Span(data.get("market_regime", "N/A"))
                ]),
                dbc.ListGroupItem([
                    html.Strong("Sentiment: "),
                    html.Span(data.get("sentiment", "N/A"))
                ]),
                dbc.ListGroupItem([
                    html.Strong("Volatility: "),
                    html.Span(data.get("volatility", "N/A"))
                ])
            ])
        ], className="mb-3"))
        
        # Add recommendations
        if data.get("recommendations"):
            insights.append(html.Div([
                html.H6("Strategy Recommendations"),
                html.Ul([
                    html.Li(rec) for rec in data["recommendations"]
                ])
            ], className="mb-3"))
        
        return html.Div(insights)
