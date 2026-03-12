"""
System Panel Component
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
from typing import Any, Dict, List, Optional
from datetime import datetime

from .base_components import BaseComponent, ComponentConfig
from enum import auto
import numpy
import pandas

import logging
logger = logging.getLogger(__name__)



class SystemPanel(BaseComponent):
    """
    System monitoring panel component.
    
    Displays system health, resource usage, and infrastructure metrics.
    """
    
    def __init__(self, config: ComponentConfig):
        """Initialize the system panel."""
        super().__init__(config)
    
    def render(self) -> html.Div:
        """Render the system panel."""
        # Create system health cards
        health_metrics = self._create_health_metrics({})
        
        # Create resource usage chart
        resource_chart = dcc.Graph(
            id=f"{self.id}-resource-chart",
            figure=self._create_empty_resource_chart(),
            style={"height": "400px"}
        )
        
        # Create infrastructure metrics
        infra_metrics = html.Div(
            id=f"{self.id}-infra-metrics",
            children=self._create_infra_metrics({})
        )
        
        # Create log viewer
        log_viewer = html.Div(
            id=f"{self.id}-log-viewer",
            children=self._create_log_viewer([])
        )
        
        # Combine all elements
        return html.Div([
            dbc.Row([
                dbc.Col([
                    health_metrics
                ], width=12)
            ], className="mb-4"),
            
            dbc.Row([
                dbc.Col([
                    resource_chart
                ], width=12)
            ], className="mb-4"),
            
            dbc.Row([
                dbc.Col([
                    html.H5("Infrastructure Metrics"),
                    infra_metrics
                ], width=6),
                
                dbc.Col([
                    html.H5("System Logs"),
                    log_viewer
                ], width=6)
            ])
        ], id=f"{self.id}-container")
    
    def _create_health_metrics(self, data: Dict[str, Any]) -> html.Div:
        """Create system health metric cards."""
        # Default data if none provided
        if not data:
            data = {
                "system_status": "N/A",
                "uptime": "N/A",
                "cpu_usage": "N/A",
                "memory_usage": "N/A",
                "network_latency": "N/A",
                "error_rate": "N/A"
            }
        
        # Create metric cards
        return dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H5("System Status", className="card-title"),
                        html.H3(data.get("system_status", "N/A"))
                    ])
                ])
            ], width=2),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H5("Uptime", className="card-title"),
                        html.H3(data.get("uptime", "N/A"))
                    ])
                ])
            ], width=2),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H5("CPU Usage", className="card-title"),
                        html.H3(data.get("cpu_usage", "N/A"))
                    ])
                ])
            ], width=2),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H5("Memory Usage", className="card-title"),
                        html.H3(data.get("memory_usage", "N/A"))
                    ])
                ])
            ], width=2),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H5("Network Latency", className="card-title"),
                        html.H3(data.get("network_latency", "N/A"))
                    ])
                ])
            ], width=2),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H5("Error Rate", className="card-title"),
                        html.H3(data.get("error_rate", "N/A"))
                    ])
                ])
            ], width=2),
        ])
    
    def _create_empty_resource_chart(self) -> go.Figure:
        """Create an empty resource usage chart."""
        fig = go.Figure()
        fig.update_layout(
            title="Resource Usage Over Time",
            xaxis_title="Time",
            yaxis_title="Usage (%)",
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
            text="No resource usage data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=16)
        )
        
        return fig
    
    def _create_infra_metrics(self, data: Dict[str, Any]) -> html.Div:
        """Create infrastructure metrics section."""
        # Default data if none provided
        if not data:
            data = {
                "components": [],
                "connections": {},
                "performance": {}
            }
        
        # Create metrics sections
        sections = []
        
        # Component Status
        if data.get("components"):
            sections.append(html.Div([
                html.H6("Component Status"),
                dbc.ListGroup([
                    dbc.ListGroupItem([
                        html.Strong(f"{comp['name']}: "),
                        html.Span(comp['status'], 
                                className=f"text-{'success' if comp['status'] == 'healthy' else 'danger'}")
                    ]) for comp in data["components"]
                ])
            ], className="mb-3"))
        
        # Connection Status
        connections = data.get("connections", {})
        if connections:
            sections.append(html.Div([
                html.H6("Connection Status"),
                dbc.ListGroup([
                    dbc.ListGroupItem([
                        html.Strong(f"{name}: "),
                        html.Span(f"{status['latency']}ms - {status['status']}")
                    ]) for name, status in connections.items()
                ])
            ], className="mb-3"))
        
        # Performance Metrics
        performance = data.get("performance", {})
        if performance:
            sections.append(html.Div([
                html.H6("Performance Metrics"),
                dbc.ListGroup([
                    dbc.ListGroupItem([
                        html.Strong(f"{metric}: "),
                        html.Span(value)
                    ]) for metric, value in performance.items()
                ])
            ], className="mb-3"))
        
        return html.Div(sections)
    
    def _create_log_viewer(self, logs: List[Dict[str, Any]]) -> html.Div:
        """Create log viewer section."""
        # Create default logs if none provided
        if not logs:
            logs = []
        
        # Create table header
        header = html.Thead([
            html.Tr([
                html.Th("Time"),
                html.Th("Level"),
                html.Th("Component"),
                html.Th("Message")
            ])
        ])
        
        # Create table rows
        rows = []
        for log in logs:
            # Determine log level class
            level_class = {
                'ERROR': 'text-danger',
                'WARNING': 'text-warning',
                'INFO': 'text-info',
                'DEBUG': 'text-muted'
            }.get(log.get('level', '').upper(), '')
            
            # Create row
            row = html.Tr([
                html.Td(log.get('time', '')),
                html.Td(log.get('level', ''), className=level_class),
                html.Td(log.get('component', '')),
                html.Td(log.get('message', '')),
            ])
            rows.append(row)
        
        # If no logs, add a placeholder row
        if not rows:
            rows = [html.Tr([html.Td("No logs available", colSpan=4, className="text-center")])]
        
        # Create table body
        body = html.Tbody(rows)
        
        # Create table
        table = dbc.Table(
            [header, body], 
            bordered=True, 
            hover=True, 
            responsive=True, 
            striped=True,
            style={"height": "400px", "overflow": "auto"}
        )
        
        return table
