"""
Risk Management Panel Component
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



class RiskPanel(BaseComponent):
    """
    Risk management panel component.
    
    Displays risk metrics, position sizing, and exposure analysis.
    """
    
    def __init__(self, config: ComponentConfig):
        """Initialize the risk panel."""
        super().__init__(config)
    
    def render(self) -> html.Div:
        """Render the risk panel."""
        # Create risk metrics cards
        risk_metrics = self._create_risk_metrics({})
        
        # Create exposure chart
        exposure_chart = dcc.Graph(
            id=f"{self.id}-exposure-chart",
            figure=self._create_empty_exposure_chart(),
            style={"height": "400px"}
        )
        
        # Create position sizing calculator
        position_calculator = self._create_position_calculator()
        
        # Create risk allocation table
        risk_allocation = html.Div(
            id=f"{self.id}-risk-allocation",
            children=self._create_risk_allocation_table([])
        )
        
        # Combine all elements
        return html.Div([
            dbc.Row([
                dbc.Col([
                    risk_metrics
                ], width=12)
            ], className="mb-4"),
            
            dbc.Row([
                dbc.Col([
                    exposure_chart
                ], width=12)
            ], className="mb-4"),
            
            dbc.Row([
                dbc.Col([
                    position_calculator
                ], width=6),
                
                dbc.Col([
                    html.H5("Risk Allocation"),
                    risk_allocation
                ], width=6)
            ])
        ], id=f"{self.id}-container")
    
    def _create_risk_metrics(self, data: Dict[str, Any]) -> html.Div:
        """Create risk metrics cards."""
        # Default data if none provided
        if not data:
            data = {
                "total_exposure": "N/A",
                "margin_used": "N/A",
                "free_margin": "N/A",
                "risk_level": "N/A",
                "max_drawdown": "N/A",
                "var_95": "N/A"
            }
        
        # Create metric cards
        return dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H5("Total Exposure", className="card-title"),
                        html.H3(data.get("total_exposure", "N/A"))
                    ])
                ])
            ], width=2),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H5("Margin Used", className="card-title"),
                        html.H3(data.get("margin_used", "N/A"))
                    ])
                ])
            ], width=2),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H5("Free Margin", className="card-title"),
                        html.H3(data.get("free_margin", "N/A"))
                    ])
                ])
            ], width=2),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H5("Risk Level", className="card-title"),
                        html.H3(data.get("risk_level", "N/A"))
                    ])
                ])
            ], width=2),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H5("Max Drawdown", className="card-title"),
                        html.H3(data.get("max_drawdown", "N/A"))
                    ])
                ])
            ], width=2),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H5("VaR (95%)", className="card-title"),
                        html.H3(data.get("var_95", "N/A"))
                    ])
                ])
            ], width=2),
        ])
    
    def _create_empty_exposure_chart(self) -> go.Figure:
        """Create an empty exposure chart."""
        fig = go.Figure()
        fig.update_layout(
            title="Portfolio Exposure",
            xaxis_title="Asset",
            yaxis_title="Exposure (%)",
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
            text="No exposure data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=16)
        )
        
        return fig
    
    def _create_position_calculator(self) -> html.Div:
        """Create position sizing calculator."""
        return html.Div([
            html.H5("Position Calculator"),
            
            dbc.Form([
                dbc.FormGroup([
                    dbc.Label("Account Size"),
                    dbc.Input(
                        id=f"{self.id}-account-size",
                        type="number",
                        placeholder="Enter account size"
                    )
                ]),
                
                dbc.FormGroup([
                    dbc.Label("Risk Per Trade (%)"),
                    dbc.Input(
                        id=f"{self.id}-risk-percent",
                        type="number",
                        placeholder="Enter risk percentage",
                        min=0.1,
                        max=10,
                        step=0.1,
                        value=1
                    )
                ]),
                
                dbc.FormGroup([
                    dbc.Label("Stop Loss (pips)"),
                    dbc.Input(
                        id=f"{self.id}-stop-loss",
                        type="number",
                        placeholder="Enter stop loss in pips"
                    )
                ]),
                
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
                        value="EURUSD"
                    )
                ]),
                
                dbc.Button(
                    "Calculate",
                    id=f"{self.id}-calculate-btn",
                    color="primary",
                    className="mt-3"
                )
            ]),
            
            html.Div(
                id=f"{self.id}-position-size-output",
                className="mt-3"
            )
        ])
    
    def _create_risk_allocation_table(self, allocations: List[Dict[str, Any]]) -> html.Table:
        """Create risk allocation table."""
        # Create default allocations if none provided
        if not allocations:
            allocations = []
        
        # Create table header
        header = html.Thead([
            html.Tr([
                html.Th("Asset"),
                html.Th("Position Size"),
                html.Th("Direction"),
                html.Th("Risk Amount"),
                html.Th("Risk %"),
                html.Th("Stop Loss"),
                html.Th("Take Profit"),
            ])
        ])
        
        # Create table rows
        rows = []
        for alloc in allocations:
            # Create row
            row = html.Tr([
                html.Td(alloc.get("asset", "")),
                html.Td(alloc.get("position_size", "")),
                html.Td(alloc.get("direction", "")),
                html.Td(alloc.get("risk_amount", "")),
                html.Td(alloc.get("risk_percent", "")),
                html.Td(alloc.get("stop_loss", "")),
                html.Td(alloc.get("take_profit", "")),
            ])
            rows.append(row)
        
        # If no allocations, add a placeholder row
        if not rows:
            rows = [html.Tr([html.Td("No risk allocations found", colSpan=7, className="text-center")])]
        
        # Create table body
        body = html.Tbody(rows)
        
        # Create table
        table = dbc.Table([header, body], bordered=True, hover=True, responsive=True, striped=True)
        
        return table
