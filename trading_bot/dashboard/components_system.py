"""
Elite Trading Bot - System Dashboard Components

This module provides the system monitoring components for the Elite Trading Bot dashboard.
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


class SystemPanel(BaseComponent):
    """
    System monitoring panel component.
    
    This component displays system metrics, performance statistics,
    and operational status information.
    """
    
    def __init__(self, config: ComponentConfig):
        """Initialize the system panel."""
        super().__init__(config)
    
    def render(self) -> html.Div:
        """Render the system panel."""
        # Create system status cards
        system_status = self._create_system_status({})
        
        # Create tabs for different system metrics
        tabs = dbc.Tabs([
            dbc.Tab(label="Performance", tab_id="performance-tab"),
            dbc.Tab(label="Resources", tab_id="resources-tab"),
            dbc.Tab(label="Logs", tab_id="logs-tab"),
            dbc.Tab(label="Connections", tab_id="connections-tab")
        ], id=f"{self.id}-tabs", active_tab="performance-tab")
        
        # Create tab content
        tab_content = html.Div(id=f"{self.id}-tab-content")
        
        # Create refresh button
        refresh_button = dbc.Button(
            "Refresh",
            id=f"{self.id}-refresh-button",
            color="primary",
            className="mb-3"
        )
        
        # Combine all elements
        return html.Div([
            dbc.Row([
                dbc.Col([
                    html.H5("System Status"),
                    system_status
                ], width=12)
            ], className="mb-4"),
            
            dbc.Row([
                dbc.Col([
                    refresh_button
                ], width=12)
            ]),
            
            dbc.Row([
                dbc.Col([
                    tabs,
                    html.Div(className="mt-4"),
                    tab_content
                ], width=12)
            ])
        ], id=f"{self.id}-container")
    
    def render_performance_tab(self, data: Dict[str, Any]) -> html.Div:
        """
        Render performance tab.
        
        Args:
            data: Performance data
            
        Returns:
            Tab content
        """
        # Default data if none provided
        if not data:
            data = {
                "execution_times": {
                    "market_analysis": [0.05, 0.06, 0.04, 0.07, 0.05],
                    "signal_generation": [0.12, 0.15, 0.11, 0.14, 0.13],
                    "risk_calculation": [0.03, 0.04, 0.03, 0.03, 0.04],
                    "order_execution": [0.08, 0.07, 0.09, 0.08, 0.08]
                },
                "bottlenecks": [
                    {"name": "signal_generation", "percentage": 35.2, "mean_time": 0.13},
                    {"name": "order_execution", "percentage": 22.1, "mean_time": 0.08},
                    {"name": "market_analysis", "percentage": 15.5, "mean_time": 0.05}
                ]
            }
        
        # Create execution time chart
        execution_chart = dcc.Graph(
            id=f"{self.id}-execution-chart",
            figure=self._create_execution_time_chart(data),
            style={"height": "400px"}
        )
        
        # Create bottlenecks chart
        bottlenecks_chart = dcc.Graph(
            id=f"{self.id}-bottlenecks-chart",
            figure=self._create_bottlenecks_chart(data),
            style={"height": "400px"}
        )
        
        # Combine all elements
        return html.Div([
            dbc.Row([
                dbc.Col([
                    html.H5("Execution Times"),
                    execution_chart
                ], width=12)
            ], className="mb-4"),
            
            dbc.Row([
                dbc.Col([
                    html.H5("Performance Bottlenecks"),
                    bottlenecks_chart
                ], width=12)
            ])
        ])
    
    def render_resources_tab(self, data: Dict[str, Any]) -> html.Div:
        """
        Render resources tab.
        
        Args:
            data: Resource usage data
            
        Returns:
            Tab content
        """
        # Default data if none provided
        if not data:
            data = {
                "cpu_usage": [25, 30, 28, 35, 40, 38, 32, 30, 28, 27],
                "memory_usage": [512, 520, 535, 550, 560, 570, 565, 550, 540, 530],
                "disk_io": [5, 8, 12, 15, 10, 7, 5, 6, 8, 10],
                "network_io": [20, 25, 30, 35, 40, 38, 32, 30, 28, 25]
            }
        
        # Create CPU usage chart
        cpu_chart = dcc.Graph(
            id=f"{self.id}-cpu-chart",
            figure=self._create_resource_chart(
                "CPU Usage", 
                data.get("cpu_usage", []), 
                "%",
                "blue"
            ),
            style={"height": "300px"}
        )
        
        # Create memory usage chart
        memory_chart = dcc.Graph(
            id=f"{self.id}-memory-chart",
            figure=self._create_resource_chart(
                "Memory Usage", 
                data.get("memory_usage", []), 
                "MB",
                "green"
            ),
            style={"height": "300px"}
        )
        
        # Create disk I/O chart
        disk_chart = dcc.Graph(
            id=f"{self.id}-disk-chart",
            figure=self._create_resource_chart(
                "Disk I/O", 
                data.get("disk_io", []), 
                "MB/s",
                "orange"
            ),
            style={"height": "300px"}
        )
        
        # Create network I/O chart
        network_chart = dcc.Graph(
            id=f"{self.id}-network-chart",
            figure=self._create_resource_chart(
                "Network I/O", 
                data.get("network_io", []), 
                "MB/s",
                "purple"
            ),
            style={"height": "300px"}
        )
        
        # Combine all elements
        return html.Div([
            dbc.Row([
                dbc.Col([
                    cpu_chart
                ], width=6),
                
                dbc.Col([
                    memory_chart
                ], width=6)
            ], className="mb-4"),
            
            dbc.Row([
                dbc.Col([
                    disk_chart
                ], width=6),
                
                dbc.Col([
                    network_chart
                ], width=6)
            ])
        ])
    
    def render_logs_tab(self, data: Dict[str, Any]) -> html.Div:
        """
        Render logs tab.
        
        Args:
            data: Log data
            
        Returns:
            Tab content
        """
        # Default data if none provided
        if not data:
            data = {
                "logs": [
                    {"level": "INFO", "timestamp": "2025-09-05 22:45:12", "message": "System started successfully"},
                    {"level": "INFO", "timestamp": "2025-09-05 22:45:15", "message": "Connected to market data feed"},
                    {"level": "INFO", "timestamp": "2025-09-05 22:45:18", "message": "Loaded trading strategy: ICT_Wyckoff_Fusion"},
                    {"level": "WARNING", "timestamp": "2025-09-05 22:45:20", "message": "Slow response from market data provider"},
                    {"level": "INFO", "timestamp": "2025-09-05 22:45:25", "message": "Analyzing EURUSD on timeframe H1"},
                    {"level": "INFO", "timestamp": "2025-09-05 22:45:30", "message": "Detected liquidity zone at 1.1050-1.1060"},
                    {"level": "ERROR", "timestamp": "2025-09-05 22:45:35", "message": "Failed to connect to secondary data source"},
                    {"level": "INFO", "timestamp": "2025-09-05 22:45:40", "message": "Generated buy signal for EURUSD at 1.1045"},
                    {"level": "INFO", "timestamp": "2025-09-05 22:45:45", "message": "Order placed: Buy 0.5 lots EURUSD at 1.1045"},
                    {"level": "INFO", "timestamp": "2025-09-05 22:45:50", "message": "Order executed: Buy 0.5 lots EURUSD at 1.1046"}
                ]
            }
        
        # Create log level filter
        log_filter = dbc.FormGroup([
            dbc.Label("Log Level"),
            dcc.Dropdown(
                id=f"{self.id}-log-level-filter",
                options=[
                    {"label": "All Levels", "value": "all"},
                    {"label": "INFO", "value": "info"},
                    {"label": "WARNING", "value": "warning"},
                    {"label": "ERROR", "value": "error"},
                    {"label": "DEBUG", "value": "debug"}
                ],
                value="all",
                clearable=False
            )
        ])
        
        # Create log search
        log_search = dbc.FormGroup([
            dbc.Label("Search"),
            dbc.Input(
                id=f"{self.id}-log-search",
                type="text",
                placeholder="Search logs..."
            )
        ])
        
        # Create log table
        log_table = self._create_log_table(data.get("logs", []))
        
        # Combine all elements
        return html.Div([
            dbc.Row([
                dbc.Col([
                    log_filter
                ], width=6),
                
                dbc.Col([
                    log_search
                ], width=6)
            ], className="mb-4"),
            
            dbc.Row([
                dbc.Col([
                    log_table
                ], width=12)
            ])
        ])
    
    def render_connections_tab(self, data: Dict[str, Any]) -> html.Div:
        """
        Render connections tab.
        
        Args:
            data: Connection data
            
        Returns:
            Tab content
        """
        # Default data if none provided
        if not data:
            data = {
                "connections": [
                    {"name": "Market Data Feed", "status": "connected", "latency": 45, "uptime": "12h 30m"},
                    {"name": "Broker API", "status": "connected", "latency": 120, "uptime": "12h 30m"},
                    {"name": "News Provider", "status": "connected", "latency": 250, "uptime": "12h 30m"},
                    {"name": "Secondary Data Source", "status": "disconnected", "latency": None, "uptime": "0h 0m"},
                    {"name": "Historical Data API", "status": "connected", "latency": 180, "uptime": "12h 30m"}
                ]
            }
        
        # Create connections table
        connections_table = self._create_connections_table(data.get("connections", []))
        
        # Create connection status chart
        status_chart = dcc.Graph(
            id=f"{self.id}-connection-status-chart",
            figure=self._create_connection_status_chart(data.get("connections", [])),
            style={"height": "300px"}
        )
        
        # Create latency chart
        latency_chart = dcc.Graph(
            id=f"{self.id}-latency-chart",
            figure=self._create_latency_chart(data.get("connections", [])),
            style={"height": "300px"}
        )
        
        # Combine all elements
        return html.Div([
            dbc.Row([
                dbc.Col([
                    html.H5("Connection Status"),
                    connections_table
                ], width=12)
            ], className="mb-4"),
            
            dbc.Row([
                dbc.Col([
                    status_chart
                ], width=6),
                
                dbc.Col([
                    latency_chart
                ], width=6)
            ])
        ])
    
    def _create_system_status(self, data: Dict[str, Any]) -> html.Div:
        """
        Create system status cards.
        
        Args:
            data: System status data
            
        Returns:
            Div with system status cards
        """
        # Default data if none provided
        if not data:
            data = {
                "status": "running",
                "uptime": "12h 30m",
                "cpu_usage": "32%",
                "memory_usage": "540 MB",
                "active_strategies": 3,
                "open_positions": 2,
                "pending_orders": 1,
                "last_signal": "5m ago",
                "data_feed_status": "connected",
                "broker_status": "connected"
            }
        
        # Determine status class
        status = data.get("status", "").lower()
        status_class = "text-warning"
        if status == "running":
            status_class = "text-success"
        elif status == "stopped" or status == "error":
            status_class = "text-danger"
        
        # Determine data feed status class
        data_feed_status = data.get("data_feed_status", "").lower()
        data_feed_class = "text-warning"
        if data_feed_status == "connected":
            data_feed_class = "text-success"
        elif data_feed_status == "disconnected" or data_feed_status == "error":
            data_feed_class = "text-danger"
        
        # Determine broker status class
        broker_status = data.get("broker_status", "").lower()
        broker_class = "text-warning"
        if broker_status == "connected":
            broker_class = "text-success"
        elif broker_status == "disconnected" or broker_status == "error":
            broker_class = "text-danger"
        
        # Create status cards
        return dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H5("System Status", className="card-title"),
                        html.H3(data.get("status", "N/A").title(), className=status_class)
                    ])
                ])
            ], width=2),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H5("Uptime", className="card-title"),
                        html.H3(data.get("uptime", "N/A"), className="text-info")
                    ])
                ])
            ], width=2),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H5("CPU Usage", className="card-title"),
                        html.H3(data.get("cpu_usage", "N/A"), className="text-primary")
                    ])
                ])
            ], width=2),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H5("Memory Usage", className="card-title"),
                        html.H3(data.get("memory_usage", "N/A"), className="text-primary")
                    ])
                ])
            ], width=2),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H5("Data Feed", className="card-title"),
                        html.H3(data.get("data_feed_status", "N/A").title(), className=data_feed_class)
                    ])
                ])
            ], width=2),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H5("Broker API", className="card-title"),
                        html.H3(data.get("broker_status", "N/A").title(), className=broker_class)
                    ])
                ])
            ], width=2)
        ])
    
    def _create_execution_time_chart(self, data: Dict[str, Any]) -> go.Figure:
        """
        Create execution time chart.
        
        Args:
            data: Execution time data
            
        Returns:
            Plotly figure
        """
        # Create figure
        fig = go.Figure()
        
        # Add execution time traces
        execution_times = data.get("execution_times", {})
        for component, times in execution_times.items():
            fig.add_trace(go.Box(
                y=times,
                name=component.replace("_", " ").title(),
                boxpoints="all",
                jitter=0.3,
                pointpos=-1.8
            ))
        
        # Update layout
        fig.update_layout(
            title="Component Execution Times",
            xaxis_title="Component",
            yaxis_title="Time (seconds)",
            template="plotly_dark",
            showlegend=False,
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
    
    def _create_bottlenecks_chart(self, data: Dict[str, Any]) -> go.Figure:
        """
        Create bottlenecks chart.
        
        Args:
            data: Bottlenecks data
            
        Returns:
            Plotly figure
        """
        # Extract bottleneck data
        bottlenecks = data.get("bottlenecks", [])
        names = [b.get("name", "").replace("_", " ").title() for b in bottlenecks]
        percentages = [b.get("percentage", 0) for b in bottlenecks]
        mean_times = [b.get("mean_time", 0) for b in bottlenecks]
        
        # Create figure
        fig = go.Figure()
        
        # Add percentage bars
        fig.add_trace(go.Bar(
            x=names,
            y=percentages,
            name="Percentage of Total Time",
            marker_color="blue",
            opacity=0.7
        ))
        
        # Create secondary y-axis for mean times
        fig.add_trace(go.Scatter(
            x=names,
            y=mean_times,
            name="Mean Execution Time (s)",
            mode="markers",
            marker=dict(
                color="red",
                size=12,
                symbol="circle"
            ),
            yaxis="y2"
        ))
        
        # Update layout
        fig.update_layout(
            title="Performance Bottlenecks",
            xaxis_title="Component",
            yaxis_title="Percentage of Total Time",
            template="plotly_dark",
            showlegend=True,
            xaxis=dict(
                showgrid=True,
                gridcolor="rgba(255, 255, 255, 0.1)",
            ),
            yaxis=dict(
                showgrid=True,
                gridcolor="rgba(255, 255, 255, 0.1)",
                title="Percentage of Total Time",
                side="left"
            ),
            yaxis2=dict(
                showgrid=False,
                title="Mean Execution Time (s)",
                side="right",
                overlaying="y"
            ),
            plot_bgcolor="rgba(0, 0, 0, 0)",
            paper_bgcolor="rgba(0, 0, 0, 0)",
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        return fig
    
    def _create_resource_chart(self, title: str, data: List[float], unit: str, color: str) -> go.Figure:
        """
        Create resource usage chart.
        
        Args:
            title: Chart title
            data: Resource usage data
            unit: Unit of measurement
            color: Line color
            
        Returns:
            Plotly figure
        """
        # Create figure
        fig = go.Figure()
        
        # Generate timestamps
        timestamps = [datetime.now() - timedelta(minutes=i) for i in range(len(data), 0, -1)]
        
        # Add resource usage line
        fig.add_trace(go.Scatter(
            x=timestamps,
            y=data,
            mode="lines+markers",
            name=title,
            line=dict(color=color, width=2)
        ))
        
        # Update layout
        fig.update_layout(
            title=title,
            xaxis_title="Time",
            yaxis_title=unit,
            template="plotly_dark",
            showlegend=False,
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
    
    def _create_log_table(self, logs: List[Dict[str, Any]]) -> html.Table:
        """
        Create log table.
        
        Args:
            logs: List of log entries
            
        Returns:
            HTML table
        """
        # Create table header
        header = html.Thead([
            html.Tr([
                html.Th("Timestamp"),
                html.Th("Level"),
                html.Th("Message")
            ])
        ])
        
        # Create table rows
        rows = []
        for log in logs:
            # Determine log level class
            level = log.get("level", "").lower()
            level_class = ""
            if level == "info":
                level_class = "text-info"
            elif level == "warning":
                level_class = "text-warning"
            elif level == "error":
                level_class = "text-danger"
            elif level == "debug":
                level_class = "text-secondary"
            
            # Create row
            row = html.Tr([
                html.Td(log.get("timestamp", "")),
                html.Td(log.get("level", ""), className=level_class),
                html.Td(log.get("message", ""))
            ])
            rows.append(row)
        
        # If no logs, add a placeholder row
        if not rows:
            rows = [html.Tr([html.Td("No logs available", colSpan=3, className="text-center")])]
        
        # Create table body
        body = html.Tbody(rows)
        
        # Create table
        table = dbc.Table([header, body], bordered=True, hover=True, responsive=True, striped=True)
        
        return table
    
    def _create_connections_table(self, connections: List[Dict[str, Any]]) -> html.Table:
        """
        Create connections table.
        
        Args:
            connections: List of connection data
            
        Returns:
            HTML table
        """
        # Create table header
        header = html.Thead([
            html.Tr([
                html.Th("Connection"),
                html.Th("Status"),
                html.Th("Latency (ms)"),
                html.Th("Uptime"),
                html.Th("Actions")
            ])
        ])
        
        # Create table rows
        rows = []
        for connection in connections:
            # Determine status class
            status = connection.get("status", "").lower()
            status_class = "text-warning"
            if status == "connected":
                status_class = "text-success"
            elif status == "disconnected" or status == "error":
                status_class = "text-danger"
            
            # Create row
            row = html.Tr([
                html.Td(connection.get("name", "")),
                html.Td(connection.get("status", "").title(), className=status_class),
                html.Td(connection.get("latency", "N/A")),
                html.Td(connection.get("uptime", "")),
                html.Td([
                    dbc.Button("Reconnect", color="primary", size="sm", className="mr-1"),
                    dbc.Button("Details", color="info", size="sm")
                ])
            ])
            rows.append(row)
        
        # If no connections, add a placeholder row
        if not rows:
            rows = [html.Tr([html.Td("No connections available", colSpan=5, className="text-center")])]
        
        # Create table body
        body = html.Tbody(rows)
        
        # Create table
        table = dbc.Table([header, body], bordered=True, hover=True, responsive=True, striped=True)
        
        return table
    
    def _create_connection_status_chart(self, connections: List[Dict[str, Any]]) -> go.Figure:
        """
        Create connection status chart.
        
        Args:
            connections: List of connection data
            
        Returns:
            Plotly figure
        """
        # Extract connection data
        names = [c.get("name", "") for c in connections]
        statuses = [1 if c.get("status", "").lower() == "connected" else 0 for c in connections]
        
        # Create figure
        fig = go.Figure()
        
        # Add status bars
        fig.add_trace(go.Bar(
            x=names,
            y=statuses,
            marker_color=["green" if s == 1 else "red" for s in statuses],
            opacity=0.7
        ))
        
        # Update layout
        fig.update_layout(
            title="Connection Status",
            xaxis_title="Connection",
            yaxis_title="Status",
            template="plotly_dark",
            showlegend=False,
            xaxis=dict(
                showgrid=True,
                gridcolor="rgba(255, 255, 255, 0.1)",
            ),
            yaxis=dict(
                showgrid=True,
                gridcolor="rgba(255, 255, 255, 0.1)",
                tickvals=[0, 1],
                ticktext=["Disconnected", "Connected"]
            ),
            plot_bgcolor="rgba(0, 0, 0, 0)",
            paper_bgcolor="rgba(0, 0, 0, 0)",
        )
        
        return fig
    
    def _create_latency_chart(self, connections: List[Dict[str, Any]]) -> go.Figure:
        """
        Create latency chart.
        
        Args:
            connections: List of connection data
            
        Returns:
            Plotly figure
        """
        # Extract connection data
        names = [c.get("name", "") for c in connections]
        latencies = [c.get("latency", 0) or 0 for c in connections]  # Replace None with 0
        
        # Create figure
        fig = go.Figure()
        
        # Add latency bars
        fig.add_trace(go.Bar(
            x=names,
            y=latencies,
            marker_color="blue",
            opacity=0.7
        ))
        
        # Update layout
        fig.update_layout(
            title="Connection Latency",
            xaxis_title="Connection",
            yaxis_title="Latency (ms)",
            template="plotly_dark",
            showlegend=False,
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
