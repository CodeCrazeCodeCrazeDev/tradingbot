"""
Interactive dashboard for AlphaAlgo 2.0
"""

import dash
from dash import dcc, html, callback, Input, Output, State
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import requests
import json
import os
from typing import Dict, List, Optional

# Initialize the Dash app
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.DARKLY],
    meta_tags=[
        {"name": "viewport", "content": "width=device-width, initial-scale=1"}
    ]
)

# Set app title
app.title = "AlphaAlgo 2.0 Dashboard"

# API settings
API_URL = os.getenv("API_URL", "http://localhost:8000")
API_TOKEN = os.getenv("API_TOKEN", "")

# Helper functions
def get_api_data(endpoint: str, params: Dict = None) -> Dict:
    """Get data from API."""
    headers = {}
    if API_TOKEN:
        headers["Authorization"] = f"Bearer {API_TOKEN}"
    
    try:
        response = requests.get(
            f"{API_URL}/{endpoint}",
            params=params,
            headers=headers
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"API error: {str(e)}")
        return {}

def create_performance_chart(performance_data: Dict):
    """Create performance chart."""
    if not performance_data or 'daily_returns' not in performance_data:
        return go.Figure()
    
    # Create DataFrame
    df = pd.DataFrame(performance_data['daily_returns'])
    df['date'] = pd.to_datetime(df['date'])
    df['cumulative_return'] = (1 + df['return']).cumprod() - 1
    
    # Create figure
    fig = go.Figure()
    
    # Add cumulative returns
    fig.add_trace(
        go.Scatter(
            x=df['date'],
            y=df['cumulative_return'],
            mode='lines',
            name='Cumulative Return',
            line=dict(color='#00cc96', width=2)
        )
    )
    
    # Add daily returns as bars
    fig.add_trace(
        go.Bar(
            x=df['date'],
            y=df['return'],
            name='Daily Return',
            marker_color=df['return'].apply(
                lambda x: '#00cc96' if x >= 0 else '#ef553b'
            ),
            opacity=0.7,
            yaxis='y2'
        )
    )
    
    # Update layout
    fig.update_layout(
        title='Performance',
        xaxis=dict(title='Date'),
        yaxis=dict(
            title='Cumulative Return',
            titlefont=dict(color='#00cc96'),
            tickfont=dict(color='#00cc96')
        ),
        yaxis2=dict(
            title='Daily Return',
            titlefont=dict(color='#ef553b'),
            tickfont=dict(color='#ef553b'),
            anchor='x',
            overlaying='y',
            side='right'
        ),
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=1.02,
            xanchor='right',
            x=1
        ),
        template='plotly_dark',
        height=400,
        margin=dict(l=50, r=50, t=50, b=50)
    )
    
    return fig

def create_trade_distribution_chart(trades_data: List):
    """Create trade distribution chart."""
    if not trades_data:
        return go.Figure()
    
    # Create DataFrame
    df = pd.DataFrame(trades_data)
    
    # Calculate PnL (placeholder)
    df['pnl'] = np.random.normal(100, 50, len(df))
    
    # Create figure
    fig = go.Figure()
    
    # Add histogram
    fig.add_trace(
        go.Histogram(
            x=df['pnl'],
            marker_color='#636efa',
            opacity=0.7,
            nbinsx=20
        )
    )
    
    # Update layout
    fig.update_layout(
        title='Trade P/L Distribution',
        xaxis=dict(title='P/L'),
        yaxis=dict(title='Frequency'),
        template='plotly_dark',
        height=300,
        margin=dict(l=50, r=50, t=50, b=50)
    )
    
    return fig

def create_risk_metrics_chart(analysis_data: Dict):
    """Create risk metrics chart."""
    if not analysis_data or 'risk_metrics' not in analysis_data:
        return go.Figure()
    
    # Extract risk metrics
    metrics = analysis_data['risk_metrics']
    
    # Create figure
    fig = go.Figure()
    
    # Add bar chart
    fig.add_trace(
        go.Bar(
            x=list(metrics.keys()),
            y=list(metrics.values()),
            marker_color=[
                '#00cc96' if v >= 0 else '#ef553b'
                for v in metrics.values()
            ]
        )
    )
    
    # Update layout
    fig.update_layout(
        title='Risk Metrics',
        xaxis=dict(title='Metric'),
        yaxis=dict(title='Value'),
        template='plotly_dark',
        height=300,
        margin=dict(l=50, r=50, t=50, b=50)
    )
    
    return fig

def create_system_status_chart(status_data: Dict):
    """Create system status chart."""
    if not status_data or 'components' not in status_data:
        return go.Figure()
    
    # Extract component status
    components = status_data['components']
    
    # Create figure
    fig = go.Figure()
    
    # Add indicator
    for i, (component, status) in enumerate(components.items()):
        fig.add_trace(
            go.Indicator(
                mode="gauge+number+delta",
                value=100 if status == 'healthy' else 50 if status == 'warning' else 0,
                domain=dict(
                    row=i // 3,
                    column=i % 3
                ),
                title=dict(text=component),
                gauge=dict(
                    axis=dict(range=[0, 100]),
                    bar=dict(color="#00cc96" if status == 'healthy' else
                                  "#ffa15a" if status == 'warning' else
                                  "#ef553b"),
                    bgcolor="white",
                    borderwidth=2,
                    bordercolor="gray",
                    steps=[
                        dict(range=[0, 30], color="#ef553b"),
                        dict(range=[30, 70], color="#ffa15a"),
                        dict(range=[70, 100], color="#00cc96")
                    ]
                )
            )
        )
    
    # Update layout
    fig.update_layout(
        grid=dict(rows=2, columns=3, pattern="independent"),
        template='plotly_dark',
        height=400,
        margin=dict(l=50, r=50, t=50, b=50)
    )
    
    return fig

# Define app layout
app.layout = dbc.Container(
    [
        # Header
        dbc.Row(
            [
                dbc.Col(
                    html.H1(
                        "AlphaAlgo 2.0 Dashboard",
                        className="text-center mb-4"
                    ),
                    width=12
                )
            ],
            className="mt-4"
        ),
        
        # System Status Card
        dbc.Row(
            [
                dbc.Col(
                    dbc.Card(
                        [
                            dbc.CardHeader("System Status"),
                            dbc.CardBody(
                                [
                                    dbc.Row(
                                        [
                                            dbc.Col(
                                                [
                                                    html.Div(id="system-status-text"),
                                                    html.Div(id="system-metrics")
                                                ],
                                                width=4
                                            ),
                                            dbc.Col(
                                                dcc.Graph(id="system-status-chart"),
                                                width=8
                                            )
                                        ]
                                    )
                                ]
                            )
                        ],
                        className="mb-4"
                    ),
                    width=12
                )
            ]
        ),
        
        # Performance and Analysis
        dbc.Row(
            [
                # Performance Chart
                dbc.Col(
                    dbc.Card(
                        [
                            dbc.CardHeader("Performance"),
                            dbc.CardBody(
                                dcc.Graph(id="performance-chart")
                            )
                        ],
                        className="mb-4"
                    ),
                    width=8
                ),
                
                # Performance Metrics
                dbc.Col(
                    dbc.Card(
                        [
                            dbc.CardHeader("Performance Metrics"),
                            dbc.CardBody(
                                html.Div(id="performance-metrics")
                            )
                        ],
                        className="mb-4"
                    ),
                    width=4
                )
            ]
        ),
        
        # Trade Analysis
        dbc.Row(
            [
                # Trade Distribution
                dbc.Col(
                    dbc.Card(
                        [
                            dbc.CardHeader("Trade Distribution"),
                            dbc.CardBody(
                                dcc.Graph(id="trade-distribution-chart")
                            )
                        ],
                        className="mb-4"
                    ),
                    width=6
                ),
                
                # Risk Metrics
                dbc.Col(
                    dbc.Card(
                        [
                            dbc.CardHeader("Risk Metrics"),
                            dbc.CardBody(
                                dcc.Graph(id="risk-metrics-chart")
                            )
                        ],
                        className="mb-4"
                    ),
                    width=6
                )
            ]
        ),
        
        # Recent Trades
        dbc.Row(
            [
                dbc.Col(
                    dbc.Card(
                        [
                            dbc.CardHeader("Recent Trades"),
                            dbc.CardBody(
                                html.Div(id="recent-trades-table")
                            )
                        ],
                        className="mb-4"
                    ),
                    width=12
                )
            ]
        ),
        
        # Symbol Analysis
        dbc.Row(
            [
                dbc.Col(
                    dbc.Card(
                        [
                            dbc.CardHeader("Symbol Analysis"),
                            dbc.CardBody(
                                [
                                    dbc.Row(
                                        [
                                            dbc.Col(
                                                dbc.Input(
                                                    id="symbol-input",
                                                    placeholder="Enter symbol (e.g., EURUSD)",
                                                    type="text",
                                                    value="EURUSD"
                                                ),
                                                width=8
                                            ),
                                            dbc.Col(
                                                dbc.Button(
                                                    "Analyze",
                                                    id="analyze-button",
                                                    color="primary"
                                                ),
                                                width=4
                                            )
                                        ],
                                        className="mb-3"
                                    ),
                                    html.Div(id="symbol-analysis")
                                ]
                            )
                        ],
                        className="mb-4"
                    ),
                    width=12
                )
            ]
        ),
        
        # Refresh interval
        dcc.Interval(
            id='interval-component',
            interval=30*1000,  # 30 seconds
            n_intervals=0
        )
    ],
    fluid=True,
    className="dbc"
)

# Callbacks
@app.callback(
    [
        Output("system-status-text", "children"),
        Output("system-metrics", "children"),
        Output("system-status-chart", "figure")
    ],
    [Input("interval-component", "n_intervals")]
)
def update_system_status(n):
    """Update system status."""
    status_data = get_api_data("system/status")
    
    if not status_data:
        return "No data available", "", go.Figure()
    
    # Create status text
    status_text = html.Div(
        [
            html.H4(
                f"Status: {status_data.get('status', 'unknown').upper()}",
                style={
                    "color": "#00cc96" if status_data.get('status') == 'running' else "#ef553b"
                }
            ),
            html.P(f"Uptime: {status_data.get('uptime', 'unknown')}"),
            html.P(f"Last Update: {status_data.get('timestamp', 'unknown')}")
        ]
    )
    
    # Create metrics
    metrics = html.Div(
        [
            html.P(f"CPU: {status_data.get('cpu_usage', 0):.1f}%"),
            html.P(f"Memory: {status_data.get('memory_usage', 0):.1f} MB"),
            html.P(f"Connections: {status_data.get('active_connections', 0)}"),
            html.P(f"Error Rate: {status_data.get('error_rate', 0):.2%}")
        ]
    )
    
    # Create chart
    chart = create_system_status_chart(status_data)
    
    return status_text, metrics, chart

@app.callback(
    [
        Output("performance-chart", "figure"),
        Output("performance-metrics", "children")
    ],
    [Input("interval-component", "n_intervals")]
)
def update_performance(n):
    """Update performance charts and metrics."""
    performance_data = get_api_data("performance")
    
    if not performance_data:
        return go.Figure(), "No data available"
    
    # Create chart
    chart = create_performance_chart(performance_data)
    
    # Create metrics
    metrics = html.Div(
        [
            html.H4("Trading Performance"),
            html.P(f"Total Trades: {performance_data.get('total_trades', 0)}"),
            html.P(f"Win Rate: {performance_data.get('win_rate', 0):.1%}"),
            html.P(f"Total P/L: ${performance_data.get('total_pnl', 0):,.2f}"),
            html.Hr(),
            html.H4("Risk Metrics"),
            html.P(f"Sharpe Ratio: {performance_data.get('sharpe_ratio', 0):.2f}"),
            html.P(f"Max Drawdown: {performance_data.get('max_drawdown', 0):.1%}"),
            html.P(f"CVaR (5%): {performance_data.get('cvar_5%', 0):.2%}")
        ]
    )
    
    return chart, metrics

@app.callback(
    Output("trade-distribution-chart", "figure"),
    [Input("interval-component", "n_intervals")]
)
def update_trade_distribution(n):
    """Update trade distribution chart."""
    trades_data = get_api_data("trades", {"limit": 100})
    
    if not trades_data:
        return go.Figure()
    
    return create_trade_distribution_chart(trades_data)

@app.callback(
    Output("risk-metrics-chart", "figure"),
    [Input("interval-component", "n_intervals")]
)
def update_risk_metrics(n):
    """Update risk metrics chart."""
    analysis_data = get_api_data("analysis/EURUSD")
    
    if not analysis_data:
        return go.Figure()
    
    return create_risk_metrics_chart(analysis_data)

@app.callback(
    Output("recent-trades-table", "children"),
    [Input("interval-component", "n_intervals")]
)
def update_recent_trades(n):
    """Update recent trades table."""
    trades_data = get_api_data("trades", {"limit": 10})
    
    if not trades_data:
        return "No trades available"
    
    # Create table
    table = dbc.Table(
        [
            html.Thead(
                html.Tr(
                    [
                        html.Th("ID"),
                        html.Th("Symbol"),
                        html.Th("Side"),
                        html.Th("Quantity"),
                        html.Th("Price"),
                        html.Th("Status"),
                        html.Th("Timestamp")
                    ]
                )
            ),
            html.Tbody(
                [
                    html.Tr(
                        [
                            html.Td(trade["trade_id"]),
                            html.Td(trade["symbol"]),
                            html.Td(
                                trade["side"],
                                style={
                                    "color": "#00cc96" if trade["side"] == "BUY" else "#ef553b"
                                }
                            ),
                            html.Td(f"{trade['quantity']:.2f}"),
                            html.Td(f"${trade['price']:.2f}"),
                            html.Td(trade["status"]),
                            html.Td(trade["timestamp"])
                        ]
                    )
                    for trade in trades_data
                ]
            )
        ],
        bordered=True,
        hover=True,
        responsive=True,
        striped=True
    )
    
    return table

@app.callback(
    Output("symbol-analysis", "children"),
    [Input("analyze-button", "n_clicks")],
    [State("symbol-input", "value")]
)
def update_symbol_analysis(n_clicks, symbol):
    """Update symbol analysis."""
    if not n_clicks or not symbol:
        return "Enter a symbol and click Analyze"
    
    analysis_data = get_api_data(f"analysis/{symbol}")
    
    if not analysis_data:
        return f"No analysis available for {symbol}"
    
    # Create analysis card
    analysis = html.Div(
        [
            html.H4(
                f"Signal: {analysis_data.get('signal', 'unknown')}",
                style={
                    "color": "#00cc96" if analysis_data.get('signal') == 'BUY' else
                             "#ef553b" if analysis_data.get('signal') == 'SELL' else
                             "#ffa15a"
                }
            ),
            html.P(f"Confidence: {analysis_data.get('confidence', 0):.1%}"),
            html.Hr(),
            html.H5("Technical Indicators"),
            html.Div(
                [
                    html.P(f"{indicator}: {value}")
                    for indicator, value in analysis_data.get('technical_indicators', {}).items()
                ]
            ),
            html.Hr(),
            html.H5("Risk Metrics"),
            html.Div(
                [
                    html.P(f"{metric}: {value:.4f}")
                    for metric, value in analysis_data.get('risk_metrics', {}).items()
                ]
            )
        ]
    )
    
    return analysis

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True, host='0.0.0.0', port=8050)
