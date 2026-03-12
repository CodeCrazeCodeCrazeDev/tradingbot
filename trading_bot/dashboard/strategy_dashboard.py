"""
Strategy Performance Dashboard
Real-time monitoring and analysis of advanced trading strategies
"""

import pandas as pd
import numpy as np
from typing import Any, Dict, List, Optional, Tuple, Union
import logging
from datetime import datetime, timedelta
try:
    import dash
except ImportError:
    dash = None

try:
    from dash import dcc, html
except ImportError:
    dash = None
from dash.dependencies import Input, Output
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import threading
import queue
import json
import os

from trading_bot.dashboard.performance_dashboard import PerformanceDashboard
from trading_bot.analysis.anomaly_detection import AdvancedAnomalyDetector
import numpy
import pandas

logger = logging.getLogger(__name__)


class StrategyDashboard(PerformanceDashboard):
    """
    Strategy-specific performance dashboard
    
    Features:
    - Strategy-level performance metrics
    - Signal analysis and monitoring
    - Strategy comparison
    - Alpha attribution
    - Risk metrics by strategy
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        
        # Strategy tracking
        self.strategies = {}
        self.strategy_metrics = {}
        self.strategy_signals = {}
        
        # Alpha attribution
        self.alpha_metrics = {}
        
        # Signal analysis
        self.signal_history = {}
        self.signal_performance = {}
        
        # Layout customization
        self._setup_strategy_layout()
        
        logger.info("Strategy Dashboard initialized")
    
    def _setup_strategy_layout(self):
        """Setup strategy-specific dashboard layout"""
        self.app.layout = html.Div([
            html.H1("Elite Trading Bot - Strategy Dashboard", style={'textAlign': 'center'}),
            
            # Strategy Selection
            html.Div([
                html.H3("Strategy Selection"),
                dcc.Dropdown(
                    id='strategy-dropdown',
                    options=[],
                    value=None,
                    placeholder="Select a strategy"
                )
            ], style={'margin': '20px'}),
            
            # Strategy Performance
            html.Div([
                html.Div([
                    html.H3("Strategy Performance"),
                    dcc.Graph(id='strategy-performance')
                ], className='six columns'),
                
                html.Div([
                    html.H3("Strategy Metrics"),
                    html.Div(id='strategy-metrics'),
                    html.H4("Signal Analysis"),
                    html.Div(id='signal-metrics')
                ], className='six columns')
            ], className='row'),
            
            # Alpha Attribution
            html.Div([
                html.Div([
                    html.H3("Alpha Attribution"),
                    dcc.Graph(id='alpha-attribution')
                ], className='six columns'),
                
                html.Div([
                    html.H3("Risk Analysis"),
                    dcc.Graph(id='risk-analysis')
                ], className='six columns')
            ], className='row'),
            
            # Signal Monitor
            html.Div([
                html.H3("Signal Monitor"),
                html.Div([
                    html.Div([
                        html.H4("Recent Signals"),
                        html.Div(id='signal-table')
                    ], className='six columns'),
                    
                    html.Div([
                        html.H4("Signal Performance"),
                        dcc.Graph(id='signal-performance')
                    ], className='six columns')
                ], className='row')
            ]),
            
            # Strategy Comparison
            html.Div([
                html.H3("Strategy Comparison"),
                dcc.Graph(id='strategy-comparison')
            ]),
            
            # Update interval
            dcc.Interval(
                id='interval-component',
                interval=5*1000  # 5 seconds
            )
        ])
        
        self._setup_strategy_callbacks()
    
    def _setup_strategy_callbacks(self):
        """Setup strategy-specific dashboard callbacks"""
        # Update strategy dropdown
        @self.app.callback(
            Output('strategy-dropdown', 'options'),
            Input('interval-component', 'n_intervals')
        )
        def update_strategy_dropdown(_):
            return [{'label': s, 'value': s} for s in self.strategies.keys()]
        
        # Update strategy performance chart
        @self.app.callback(
            Output('strategy-performance', 'figure'),
            [Input('strategy-dropdown', 'value'),
             Input('interval-component', 'n_intervals')]
        )
        def update_strategy_performance(strategy, _):
            if not strategy or strategy not in self.strategy_metrics:
                return go.Figure()
            
            metrics = self.strategy_metrics[strategy]
            
            # Create figure with secondary y-axis
            fig = make_subplots(specs=[[{"secondary_y": True}]])
            
            # Add equity curve
            fig.add_trace(
                go.Scatter(
                    x=metrics['timestamps'],
                    y=metrics['equity'],
                    name="Equity",
                    line=dict(color='blue')
                ),
                secondary_y=False
            )
            
            # Add drawdown
            fig.add_trace(
                go.Scatter(
                    x=metrics['timestamps'],
                    y=metrics['drawdown'],
                    name="Drawdown",
                    line=dict(color='red')
                ),
                secondary_y=True
            )
            
            fig.update_layout(
                title=f"{strategy} Performance",
                xaxis_title="Time",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            
            return fig
        
        # Update strategy metrics
        @self.app.callback(
            Output('strategy-metrics', 'children'),
            [Input('strategy-dropdown', 'value'),
             Input('interval-component', 'n_intervals')]
        )
        def update_strategy_metrics(strategy, _):
            if not strategy or strategy not in self.strategy_metrics:
                return html.P("No metrics available")
            
            metrics = self.strategy_metrics[strategy]
            
            return html.Div([
                html.Table([
                    html.Tr([html.Td("Total Return"), html.Td(f"{metrics['total_return']:.2%}")]),
                    html.Tr([html.Td("Sharpe Ratio"), html.Td(f"{metrics['sharpe_ratio']:.2f}")]),
                    html.Tr([html.Td("Win Rate"), html.Td(f"{metrics['win_rate']:.2%}")]),
                    html.Tr([html.Td("Profit Factor"), html.Td(f"{metrics['profit_factor']:.2f}")]),
                    html.Tr([html.Td("Max Drawdown"), html.Td(f"{metrics['max_drawdown']:.2%}")]),
                    html.Tr([html.Td("Recovery Factor"), html.Td(f"{metrics['recovery_factor']:.2f}")]),
                    html.Tr([html.Td("Avg Trade"), html.Td(f"{metrics['avg_trade']:.2f}")]),
                    html.Tr([html.Td("Alpha"), html.Td(f"{metrics['alpha']:.2%}")])
                ])
            ])
        
        # Update signal metrics
        @self.app.callback(
            Output('signal-metrics', 'children'),
            [Input('strategy-dropdown', 'value'),
             Input('interval-component', 'n_intervals')]
        )
        def update_signal_metrics(strategy, _):
            if not strategy or strategy not in self.signal_performance:
                return html.P("No signal metrics available")
            
            metrics = self.signal_performance[strategy]
            
            return html.Div([
                html.Table([
                    html.Tr([html.Td("Signal Accuracy"), html.Td(f"{metrics['accuracy']:.2%}")]),
                    html.Tr([html.Td("Signal Count"), html.Td(str(metrics['count']))]),
                    html.Tr([html.Td("Avg Confidence"), html.Td(f"{metrics['avg_confidence']:.2f}")]),
                    html.Tr([html.Td("Success Rate"), html.Td(f"{metrics['success_rate']:.2%}")])
                ])
            ])
        
        # Update alpha attribution chart
        @self.app.callback(
            Output('alpha-attribution', 'figure'),
            [Input('strategy-dropdown', 'value'),
             Input('interval-component', 'n_intervals')]
        )
        def update_alpha_attribution(strategy, _):
            if not strategy or strategy not in self.alpha_metrics:
                return go.Figure()
            
            metrics = self.alpha_metrics[strategy]
            
            fig = go.Figure(data=[
                go.Bar(
                    x=list(metrics.keys()),
                    y=list(metrics.values()),
                    marker_color=['blue', 'green', 'orange', 'red']
                )
            ])
            
            fig.update_layout(
                title="Alpha Attribution",
                xaxis_title="Source",
                yaxis_title="Contribution"
            )
            
            return fig
        
        # Update risk analysis chart
        @self.app.callback(
            Output('risk-analysis', 'figure'),
            [Input('strategy-dropdown', 'value'),
             Input('interval-component', 'n_intervals')]
        )
        def update_risk_analysis(strategy, _):
            if not strategy or strategy not in self.strategy_metrics:
                return go.Figure()
            
            metrics = self.strategy_metrics[strategy]
            
            # Create risk radar chart
            fig = go.Figure(data=go.Scatterpolar(
                r=[
                    metrics['sharpe_ratio'],
                    1 - metrics['max_drawdown'],
                    metrics['win_rate'],
                    metrics['profit_factor'] / 3,  # Normalize to 0-1
                    metrics['recovery_factor'] / 2  # Normalize to 0-1
                ],
                theta=['Sharpe Ratio', 'Drawdown Control', 'Win Rate', 
                       'Profit Factor', 'Recovery Factor'],
                fill='toself'
            ))
            
            fig.update_layout(
                polar=dict(
                    radialaxis=dict(
                        visible=True,
                        range=[0, 1]
                    )),
                showlegend=False
            )
            
            return fig
        
        # Update signal table
        @self.app.callback(
            Output('signal-table', 'children'),
            [Input('strategy-dropdown', 'value'),
             Input('interval-component', 'n_intervals')]
        )
        def update_signal_table(strategy, _):
            if not strategy or strategy not in self.signal_history:
                return html.P("No signals available")
            
            signals = self.signal_history[strategy][-10:]  # Last 10 signals
            
            return html.Table([
                html.Thead(html.Tr([
                    html.Th("Time"),
                    html.Th("Symbol"),
                    html.Th("Type"),
                    html.Th("Confidence")
                ])),
                html.Tbody([
                    html.Tr([
                        html.Td(s['timestamp'].strftime('%H:%M:%S')),
                        html.Td(s['symbol']),
                        html.Td(s['signal_type']),
                        html.Td(f"{s['confidence']:.2f}")
                    ]) for s in reversed(signals)
                ])
            ])
        
        # Update signal performance chart
        @self.app.callback(
            Output('signal-performance', 'figure'),
            [Input('strategy-dropdown', 'value'),
             Input('interval-component', 'n_intervals')]
        )
        def update_signal_performance(strategy, _):
            if not strategy or strategy not in self.signal_performance:
                return go.Figure()
            
            performance = self.signal_performance[strategy]
            
            # Create scatter plot of confidence vs. return
            fig = go.Figure(data=go.Scatter(
                x=performance['confidence'],
                y=performance['returns'],
                mode='markers',
                marker=dict(
                    size=8,
                    color=performance['returns'],
                    colorscale='RdYlGn',
                    showscale=True
                )
            ))
            
            fig.update_layout(
                title="Signal Confidence vs. Returns",
                xaxis_title="Signal Confidence",
                yaxis_title="Return"
            )
            
            return fig
        
        # Update strategy comparison chart
        @self.app.callback(
            Output('strategy-comparison', 'figure'),
            Input('interval-component', 'n_intervals')
        )
        def update_strategy_comparison(_):
            if not self.strategy_metrics:
                return go.Figure()
            
            # Prepare data for comparison
            strategies = list(self.strategy_metrics.keys())
            metrics = ['sharpe_ratio', 'win_rate', 'profit_factor', 'recovery_factor']
            
            fig = go.Figure()
            
            for metric in metrics:
                fig.add_trace(go.Bar(
                    name=metric.replace('_', ' ').title(),
                    x=strategies,
                    y=[self.strategy_metrics[s][metric] for s in strategies]
                ))
            
            fig.update_layout(
                barmode='group',
                title="Strategy Comparison",
                xaxis_title="Strategy",
                yaxis_title="Metric Value"
            )
            
            return fig
    
    def add_strategy(self, name: str, initial_metrics: Optional[Dict[str, Any]] = None):
        """
        Add a new strategy to track
        
        Args:
            name: Strategy name
            initial_metrics: Initial strategy metrics
        """
        self.strategies[name] = {
            'start_time': datetime.now(),
            'trades': [],
            'signals': []
        }
        
        if initial_metrics:
            self.strategy_metrics[name] = initial_metrics
        else:
            self.strategy_metrics[name] = {
                'timestamps': [],
                'equity': [],
                'drawdown': [],
                'total_return': 0.0,
                'sharpe_ratio': 0.0,
                'win_rate': 0.0,
                'profit_factor': 0.0,
                'max_drawdown': 0.0,
                'recovery_factor': 0.0,
                'avg_trade': 0.0,
                'alpha': 0.0
            }
        
        logger.info(f"Added strategy: {name}")
    
    def update_strategy(self, name: str, metrics: Dict[str, Any]):
        """
        Update strategy metrics
        
        Args:
            name: Strategy name
            metrics: Updated metrics
        """
        if name not in self.strategies:
            self.add_strategy(name)
        
        # Update metrics
        self.strategy_metrics[name].update(metrics)
        
        # Update timestamps
        self.strategy_metrics[name]['timestamps'].append(datetime.now())
        
        # Calculate alpha attribution
        self._calculate_alpha_attribution(name)
        
        logger.debug(f"Updated metrics for strategy: {name}")
    
    def add_signal(self, name: str, signal: Dict[str, Any]):
        """
        Add a new signal from a strategy
        
        Args:
            name: Strategy name
            signal: Signal information
        """
        if name not in self.strategies:
            self.add_strategy(name)
        
        if name not in self.signal_history:
            self.signal_history[name] = []
        
        self.signal_history[name].append(signal)
        
        # Update signal performance
        self._update_signal_performance(name)
        
        logger.debug(f"Added signal for strategy: {name}")
    
    def _calculate_alpha_attribution(self, name: str):
        """Calculate alpha attribution for a strategy"""
        if name not in self.strategy_metrics:
            return
        
        metrics = self.strategy_metrics[name]
        
        # Calculate attribution components
        market_return = 0.0  # This would come from market data
        strategy_return = metrics['total_return']
        alpha = strategy_return - market_return
        
        self.alpha_metrics[name] = {
            'Market': market_return,
            'Strategy Alpha': alpha,
            'Signal Quality': alpha * metrics['win_rate'],
            'Risk Management': alpha * (1 - metrics['max_drawdown'])
        }
    
    def _update_signal_performance(self, name: str):
        """Update signal performance metrics"""
        if name not in self.signal_history:
            return
        
        signals = self.signal_history[name]
        
        if not signals:
            return
        
        # Calculate signal performance metrics
        successful_signals = sum(1 for s in signals if s.get('success', False))
        total_signals = len(signals)
        
        self.signal_performance[name] = {
            'accuracy': successful_signals / total_signals if total_signals > 0 else 0,
            'count': total_signals,
            'avg_confidence': sum(s['confidence'] for s in signals) / total_signals if total_signals > 0 else 0,
            'success_rate': successful_signals / total_signals if total_signals > 0 else 0,
            'confidence': [s['confidence'] for s in signals],
            'returns': [s.get('return', 0) for s in signals]
        }


# Example usage
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Create dashboard
    dashboard = StrategyDashboard()
    
    # Add some example strategies
    dashboard.add_strategy("AlternativeData")
    dashboard.add_strategy("MultiTimeframeRL")
    dashboard.add_strategy("MarketRegime")
    
    # Start dashboard
    dashboard.start()
