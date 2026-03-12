"""
Analytics Panel Component
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
import plotly.express as px
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
from datetime import datetime

from .base_components import BaseComponent, ComponentConfig
import numpy
import pandas

import logging
logger = logging.getLogger(__name__)



class AnalyticsPanel(BaseComponent):
    """
    Advanced analytics panel component.
    
    Displays advanced market analysis, ML insights, and quantum predictions.
    """
    
    def __init__(self, config: ComponentConfig):
        """Initialize the analytics panel."""
        super().__init__(config)
    
    def render(self) -> html.Div:
        """Render the analytics panel."""
        # Create ML insights cards
        ml_insights = self._create_ml_insights({})
        
        # Create quantum predictions chart
        quantum_chart = dcc.Graph(
            id=f"{self.id}-quantum-chart",
            figure=self._create_empty_quantum_chart(),
            style={"height": "400px"}
        )
        
        # Create market analysis
        market_analysis = html.Div(
            id=f"{self.id}-market-analysis",
            children=self._create_market_analysis({})
        )
        
        # Create feature importance chart
        feature_chart = dcc.Graph(
            id=f"{self.id}-feature-chart",
            figure=self._create_empty_feature_chart(),
            style={"height": "400px"}
        )
        
        # Combine all elements
        return html.Div([
            dbc.Row([
                dbc.Col([
                    ml_insights
                ], width=12)
            ], className="mb-4"),
            
            dbc.Row([
                dbc.Col([
                    quantum_chart
                ], width=6),
                
                dbc.Col([
                    feature_chart
                ], width=6)
            ], className="mb-4"),
            
            dbc.Row([
                dbc.Col([
                    html.H5("Market Analysis"),
                    market_analysis
                ], width=12)
            ])
        ], id=f"{self.id}-container")
    
    def _create_ml_insights(self, data: Dict[str, Any]) -> html.Div:
        """Create ML insights cards."""
        # Default data if none provided
        if not data:
            data = {
                "model_accuracy": "N/A",
                "prediction_confidence": "N/A",
                "quantum_advantage": "N/A",
                "feature_importance": "N/A",
                "regime_prediction": "N/A",
                "anomaly_score": "N/A"
            }
        
        # Create metric cards
        return dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H5("Model Accuracy", className="card-title"),
                        html.H3(data.get("model_accuracy", "N/A"))
                    ])
                ])
            ], width=2),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H5("Prediction Confidence", className="card-title"),
                        html.H3(data.get("prediction_confidence", "N/A"))
                    ])
                ])
            ], width=2),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H5("Quantum Advantage", className="card-title"),
                        html.H3(data.get("quantum_advantage", "N/A"))
                    ])
                ])
            ], width=2),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H5("Feature Importance", className="card-title"),
                        html.H3(data.get("feature_importance", "N/A"))
                    ])
                ])
            ], width=2),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H5("Regime Prediction", className="card-title"),
                        html.H3(data.get("regime_prediction", "N/A"))
                    ])
                ])
            ], width=2),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H5("Anomaly Score", className="card-title"),
                        html.H3(data.get("anomaly_score", "N/A"))
                    ])
                ])
            ], width=2),
        ])
    
    def _create_empty_quantum_chart(self) -> go.Figure:
        """Create an empty quantum predictions chart."""
        fig = go.Figure()
        fig.update_layout(
            title="Quantum Portfolio Optimization",
            xaxis_title="Asset",
            yaxis_title="Allocation (%)",
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
            text="No quantum optimization data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=16)
        )
        
        return fig
    
    def _create_empty_feature_chart(self) -> go.Figure:
        """Create an empty feature importance chart."""
        fig = go.Figure()
        fig.update_layout(
            title="Feature Importance",
            xaxis_title="Feature",
            yaxis_title="Importance Score",
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
            text="No feature importance data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=16)
        )
        
        return fig
    
    def _create_market_analysis(self, data: Dict[str, Any]) -> html.Div:
        """Create market analysis section."""
        # Default data if none provided
        if not data:
            data = {
                "market_insights": [],
                "correlation_matrix": None,
                "regime_analysis": {},
                "anomalies": []
            }
        
        # Create analysis sections
        sections = []
        
        # Market Insights
        if data.get("market_insights"):
            sections.append(html.Div([
                html.H6("Market Insights"),
                html.Ul([
                    html.Li(insight) for insight in data["market_insights"]
                ])
            ], className="mb-3"))
        
        # Regime Analysis
        regime_data = data.get("regime_analysis", {})
        if regime_data:
            sections.append(html.Div([
                html.H6("Market Regime Analysis"),
                dbc.ListGroup([
                    dbc.ListGroupItem([
                        html.Strong("Current Regime: "),
                        html.Span(regime_data.get("current_regime", "N/A"))
                    ]),
                    dbc.ListGroupItem([
                        html.Strong("Regime Probability: "),
                        html.Span(f"{regime_data.get('regime_probability', 0):.2%}")
                    ]),
                    dbc.ListGroupItem([
                        html.Strong("Regime Duration: "),
                        html.Span(regime_data.get("regime_duration", "N/A"))
                    ])
                ])
            ], className="mb-3"))
        
        # Anomalies
        if data.get("anomalies"):
            sections.append(html.Div([
                html.H6("Detected Anomalies"),
                html.Ul([
                    html.Li([
                        html.Strong(f"{anomaly['type']}: "),
                        html.Span(anomaly['description'])
                    ]) for anomaly in data["anomalies"]
                ])
            ], className="mb-3"))
        
        # Create correlation matrix if available
        if data.get("correlation_matrix") is not None:
            correlation_chart = dcc.Graph(
                figure=px.imshow(
                    data["correlation_matrix"],
                    title="Asset Correlation Matrix",
                    color_continuous_scale="RdBu",
                    template="plotly_dark"
                ),
                style={"height": "400px"}
            )
            sections.append(correlation_chart)
        
        return html.Div(sections)
