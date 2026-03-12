"""
Elite System Visualization Module

This module provides visualization tools for the Elite Trading System,
including interactive charts, dashboards, and visual analysis tools.
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union
import logging
from pathlib import Path
import json
import mplfinance as mpf
import seaborn as sns
from dataclasses import dataclass
from enum import Enum

from .elite_system import EliteSignal, SignalDirection, SignalStrength
from .market_structure_oracle import MarketPhase, SwingPoint
from .liquidity_warfare import LiquidityZone
from .config import VisualizationConfig
from typing import Set
import numpy
import pandas

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ChartType(Enum):
    """Chart Types"""
    CANDLESTICK = "candlestick"
    LINE = "line"
    OHLC = "ohlc"
    RENKO = "renko"
    POINT_AND_FIGURE = "point_and_figure"

class Theme(Enum):
    """Chart Themes"""
    DARK = "dark"
    LIGHT = "light"
    TRADING = "trading"
    MINIMAL = "minimal"

@dataclass
class ChartOverlay:
    """Chart Overlay Configuration"""
    name: str
    data: pd.Series
    color: str
    width: int = 1
    opacity: float = 1.0
    type: str = "line"  # line, scatter, bar

class EliteVisualizer:
    """Elite System Visualization Tools"""
    
    def __init__(self, config: Optional[VisualizationConfig] = None):
        """Initialize visualizer with configuration"""
        self.config = config or VisualizationConfig()
        
        # Create charts directory if needed
        if self.config.auto_save_charts:
            Path(self.config.charts_directory).mkdir(parents=True, exist_ok=True)
        
        # Set theme
        self.set_theme(Theme(self.config.default_theme))
    
    def set_theme(self, theme: Theme):
        """Set chart theme"""
        if theme == Theme.DARK:
            self.colors = {
                'background': '#1e1e1e',
                'text': '#ffffff',
                'grid': '#333333',
                'bullish': '#26a69a',
                'bearish': '#ef5350',
                'neutral': '#9e9e9e',
                'volume': '#2196f3',
                'signal': '#ffd700',
                'liquidity': '#7b1fa2',
                'order_block': '#ff9800',
                'fvg': '#4caf50'
            }
        elif theme == Theme.LIGHT:
            self.colors = {
                'background': '#ffffff',
                'text': '#000000',
                'grid': '#e0e0e0',
                'bullish': '#4caf50',
                'bearish': '#f44336',
                'neutral': '#9e9e9e',
                'volume': '#2196f3',
                'signal': '#ffc107',
                'liquidity': '#9c27b0',
                'order_block': '#ff9800',
                'fvg': '#009688'
            }
        elif theme == Theme.TRADING:
            self.colors = {
                'background': '#131722',
                'text': '#d1d4dc',
                'grid': '#363c4e',
                'bullish': '#089981',
                'bearish': '#f23645',
                'neutral': '#787b86',
                'volume': '#2962ff',
                'signal': '#f0b90b',
                'liquidity': '#7b1fa2',
                'order_block': '#e65100',
                'fvg': '#00c853'
            }
        else:  # MINIMAL
            self.colors = {
                'background': '#ffffff',
                'text': '#000000',
                'grid': '#f5f5f5',
                'bullish': '#000000',
                'bearish': '#666666',
                'neutral': '#999999',
                'volume': '#cccccc',
                'signal': '#333333',
                'liquidity': '#666666',
                'order_block': '#999999',
                'fvg': '#333333'
            }
    
    def create_market_chart(self, market_data: pd.DataFrame, 
                          signals: Optional[List[EliteSignal]] = None,
                          liquidity_zones: Optional[List[LiquidityZone]] = None,
                          chart_type: Optional[ChartType] = None,
                          overlays: Optional[List[ChartOverlay]] = None,
                          title: Optional[str] = None) -> go.Figure:
        """
        Create interactive market chart with signals and analysis overlays
        
        Args:
            market_data: OHLCV DataFrame
            signals: Optional list of trading signals
            liquidity_zones: Optional list of liquidity zones
            chart_type: Chart type (default from config)
            overlays: Optional technical indicators to overlay
            title: Optional chart title
        
        Returns:
            Plotly figure object
        """
        # Create subplots for price and volume
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                           vertical_spacing=0.03,
                           row_heights=[0.7, 0.3])
        
        # Set chart type
        chart_type = chart_type or ChartType(self.config.chart_type)
        
        # Add price data
        if chart_type == ChartType.CANDLESTICK:
            fig.add_trace(
                go.Candlestick(
                    x=market_data.index,
                    open=market_data['open'],
                    high=market_data['high'],
                    low=market_data['low'],
                    close=market_data['close'],
                    increasing_line_color=self.colors['bullish'],
                    decreasing_line_color=self.colors['bearish'],
                    name='Price'
                ),
                row=1, col=1
            )
        elif chart_type == ChartType.OHLC:
            fig.add_trace(
                go.Ohlc(
                    x=market_data.index,
                    open=market_data['open'],
                    high=market_data['high'],
                    low=market_data['low'],
                    close=market_data['close'],
                    increasing_line_color=self.colors['bullish'],
                    decreasing_line_color=self.colors['bearish'],
                    name='Price'
                ),
                row=1, col=1
            )
        else:  # LINE
            fig.add_trace(
                go.Scatter(
                    x=market_data.index,
                    y=market_data['close'],
                    mode='lines',
                    name='Price',
                    line=dict(color=self.colors['neutral'])
                ),
                row=1, col=1
            )
        
        # Add volume
        colors = np.where(market_data['close'] >= market_data['open'],
                         self.colors['bullish'],
                         self.colors['bearish'])
        
        fig.add_trace(
            go.Bar(
                x=market_data.index,
                y=market_data['volume'],
                marker_color=colors,
                name='Volume'
            ),
            row=2, col=1
        )
        
        # Add signals if provided
        if signals and self.config.show_signals:
            for signal in signals:
                marker_symbol = '▲' if signal.direction == SignalDirection.BULLISH else '▼'
                marker_color = (self.colors['bullish'] if signal.direction == SignalDirection.BULLISH
                              else self.colors['bearish'])
                
                fig.add_trace(
                    go.Scatter(
                        x=[signal.timestamp],
                        y=[market_data.loc[signal.timestamp, 'close']],
                        mode='markers+text',
                        marker=dict(
                            symbol=marker_symbol,
                            size=12,
                            color=marker_color
                        ),
                        text=[f"{signal.strength:.2f}"],
                        textposition="top center",
                        name=f'Signal ({signal.direction.value})'
                    ),
                    row=1, col=1
                )
        
        # Add liquidity zones if provided
        if liquidity_zones and self.config.show_liquidity_zones:
            for zone in liquidity_zones:
                fig.add_shape(
                    type="rect",
                    x0=zone.start_time,
                    x1=zone.end_time,
                    y0=zone.price_low,
                    y1=zone.price_high,
                    fillcolor=self.colors['liquidity'],
                    opacity=0.3,
                    layer="below",
                    line_width=0,
                )
        
        # Add technical indicator overlays
        if overlays:
            for overlay in overlays:
                fig.add_trace(
                    go.Scatter(
                        x=market_data.index,
                        y=overlay.data,
                        mode='lines',
                        name=overlay.name,
                        line=dict(
                            color=overlay.color,
                            width=overlay.width
                        ),
                        opacity=overlay.opacity
                    ),
                    row=1, col=1
                )
        
        # Update layout
        fig.update_layout(
            title=title or "Market Analysis",
            template='plotly_dark' if self.config.default_theme == 'dark' else 'plotly_white',
            xaxis_rangeslider_visible=False,
            plot_bgcolor=self.colors['background'],
            paper_bgcolor=self.colors['background'],
            font=dict(color=self.colors['text']),
            showlegend=True,
            height=800
        )
        
        # Update axes
        fig.update_xaxes(
            gridcolor=self.colors['grid'],
            row=1, col=1
        )
        fig.update_xaxes(
            gridcolor=self.colors['grid'],
            row=2, col=1
        )
        fig.update_yaxes(
            gridcolor=self.colors['grid'],
            row=1, col=1
        )
        fig.update_yaxes(
            gridcolor=self.colors['grid'],
            row=2, col=1
        )
        
        return fig
    
    def create_signal_dashboard(self, signal: EliteSignal) -> go.Figure:
        """
        Create comprehensive signal analysis dashboard
        
        Args:
            signal: Elite trading signal to visualize
        
        Returns:
            Plotly figure object with multiple subplots
        """
        # Create subplot grid
        fig = make_subplots(
            rows=3, cols=2,
            subplot_titles=(
                'Signal Strength Analysis',
                'Component Contributions',
                'Risk Assessment',
                'Position Sizing',
                'Psychology Assessment',
                'Signal Timeline'
            ),
            vertical_spacing=0.1,
            horizontal_spacing=0.1
        )
        
        # 1. Signal Strength Analysis (Gauge)
        fig.add_trace(
            go.Indicator(
                mode="gauge+number",
                value=signal.strength * 100,
                title={'text': f"Signal Strength ({signal.direction.value})"},
                gauge={
                    'axis': {'range': [0, 100]},
                    'bar': {'color': self.colors['signal']},
                    'steps': [
                        {'range': [0, 20], 'color': "lightgray"},
                        {'range': [20, 40], 'color': "gray"},
                        {'range': [40, 60], 'color': "lightblue"},
                        {'range': [60, 80], 'color': "blue"},
                        {'range': [80, 100], 'color': "darkblue"}
                    ]
                }
            ),
            row=1, col=1
        )
        
        # 2. Component Contributions (Bar Chart)
        components = {
            'Price Action': signal.price_action_signal.get('strength', 0),
            'Market Structure': signal.market_structure_signal.get('strength', 0),
            'Liquidity': signal.liquidity_signal.get('strength', 0),
            'Order Flow': signal.order_flow_signal.get('strength', 0),
            'Institutional': signal.institutional_signal.get('strength', 0),
            'AI/ML': signal.ai_ml_signal.get('strength', 0)
        }
        
        fig.add_trace(
            go.Bar(
                x=list(components.keys()),
                y=list(components.values()),
                marker_color=self.colors['signal']
            ),
            row=1, col=2
        )
        
        # 3. Risk Assessment (Radar Chart)
        risk_metrics = signal.risk_assessment
        if risk_metrics and 'error' not in risk_metrics:
            fig.add_trace(
                go.Scatterpolar(
                    r=[
                        risk_metrics.get('portfolio_var', 0) * 100,
                        risk_metrics.get('portfolio_cvar', 0) * 100,
                        risk_metrics.get('correlation_risk', 0) * 100,
                        risk_metrics.get('black_swan_probability', 0) * 100,
                        risk_metrics.get('portfolio_var', 0) * 100  # Close the polygon
                    ],
                    theta=['VaR', 'CVaR', 'Correlation', 'Black Swan', 'VaR'],
                    fill='toself',
                    name='Risk Profile'
                ),
                row=2, col=1
            )
        
        # 4. Position Sizing (Pie Chart)
        position_data = signal.position_sizing
        if position_data and 'error' not in position_data:
            fig.add_trace(
                go.Pie(
                    labels=['Position Size', 'Available'],
                    values=[
                        position_data.get('recommended_size', 0),
                        1 - position_data.get('recommended_size', 0)
                    ],
                    marker_colors=[self.colors['signal'], self.colors['neutral']]
                ),
                row=2, col=2
            )
        
        # 5. Psychology Assessment (Gauge + Text)
        psychology = signal.psychology_assessment
        if psychology and 'error' not in psychology:
            fig.add_trace(
                go.Indicator(
                    mode="gauge+number",
                    value=psychology.get('emotional_stability', 0) * 100,
                    title={'text': "Emotional Stability"},
                    gauge={'axis': {'range': [0, 100]}}
                ),
                row=3, col=1
            )
        
        # 6. Signal Timeline
        fig.add_trace(
            go.Scatter(
                x=[signal.timestamp],
                y=[signal.strength],
                mode='markers+text',
                marker=dict(
                    symbol='diamond',
                    size=15,
                    color=self.colors['signal']
                ),
                text=[signal.action.value],
                textposition="top center"
            ),
            row=3, col=2
        )
        
        # Update layout
        fig.update_layout(
            title=f"Signal Analysis Dashboard - {signal.symbol} ({signal.timeframe})",
            template='plotly_dark' if self.config.default_theme == 'dark' else 'plotly_white',
            plot_bgcolor=self.colors['background'],
            paper_bgcolor=self.colors['background'],
            font=dict(color=self.colors['text']),
            showlegend=False,
            height=1000
        )
        
        return fig
    
    def create_performance_dashboard(self, signals: List[EliteSignal],
                                  trades: List[Dict[str, Any]]) -> go.Figure:
        """
        Create performance analysis dashboard
        
        Args:
            signals: List of historical signals
            trades: List of executed trades with performance metrics
        
        Returns:
            Plotly figure object with performance analysis
        """
        # Create subplot grid
        fig = make_subplots(
            rows=3, cols=2,
            subplot_titles=(
                'Cumulative Returns',
                'Win Rate Analysis',
                'Signal Quality Distribution',
                'Risk-Reward Distribution',
                'Psychology Metrics',
                'Trading Activity'
            ),
            vertical_spacing=0.1,
            horizontal_spacing=0.1
        )
        
        # 1. Cumulative Returns
        if trades:
            returns = pd.Series([t['pnl_percent'] for t in trades]).cumsum()
            fig.add_trace(
                go.Scatter(
                    x=list(range(len(returns))),
                    y=returns,
                    mode='lines',
                    name='Cumulative Returns',
                    line=dict(color=self.colors['signal'])
                ),
                row=1, col=1
            )
        
        # 2. Win Rate Analysis
        if trades:
            wins = sum(1 for t in trades if t['pnl_percent'] > 0)
            losses = sum(1 for t in trades if t['pnl_percent'] < 0)
            fig.add_trace(
                go.Pie(
                    labels=['Wins', 'Losses'],
                    values=[wins, losses],
                    marker_colors=[self.colors['bullish'], self.colors['bearish']]
                ),
                row=1, col=2
            )
        
        # 3. Signal Quality Distribution
        if signals:
            strengths = [s.strength for s in signals]
            fig.add_trace(
                go.Histogram(
                    x=strengths,
                    nbinsx=20,
                    marker_color=self.colors['signal']
                ),
                row=2, col=1
            )
        
        # 4. Risk-Reward Distribution
        if signals:
            risk_rewards = [s.risk_reward_ratio for s in signals if s.risk_reward_ratio]
            fig.add_trace(
                go.Box(
                    y=risk_rewards,
                    marker_color=self.colors['signal']
                ),
                row=2, col=2
            )
        
        # 5. Psychology Metrics
        if signals:
            psychology_metrics = []
            for s in signals:
                if s.psychology_assessment and 'error' not in s.psychology_assessment:
                    psychology_metrics.append({
                        'emotional_stability': s.psychology_assessment.get('emotional_stability', 0),
                        'discipline_score': s.psychology_assessment.get('discipline_score', 0)
                    })
            
            if psychology_metrics:
                metrics_df = pd.DataFrame(psychology_metrics)
                fig.add_trace(
                    go.Scatter(
                        x=list(range(len(metrics_df))),
                        y=metrics_df['emotional_stability'],
                        mode='lines',
                        name='Emotional Stability',
                        line=dict(color=self.colors['bullish'])
                    ),
                    row=3, col=1
                )
                fig.add_trace(
                    go.Scatter(
                        x=list(range(len(metrics_df))),
                        y=metrics_df['discipline_score'],
                        mode='lines',
                        name='Discipline Score',
                        line=dict(color=self.colors['bearish'])
                    ),
                    row=3, col=1
                )
        
        # 6. Trading Activity
        if trades:
            activity = pd.Series([t['timestamp'] for t in trades]).value_counts().sort_index()
            fig.add_trace(
                go.Bar(
                    x=activity.index,
                    y=activity.values,
                    marker_color=self.colors['signal']
                ),
                row=3, col=2
            )
        
        # Update layout
        fig.update_layout(
            title="Trading Performance Dashboard",
            template='plotly_dark' if self.config.default_theme == 'dark' else 'plotly_white',
            plot_bgcolor=self.colors['background'],
            paper_bgcolor=self.colors['background'],
            font=dict(color=self.colors['text']),
            showlegend=True,
            height=1200
        )
        
        return fig
    
    def save_chart(self, fig: go.Figure, filename: str):
        """Save chart to file"""
        if self.config.auto_save_charts:
            try:
                filepath = Path(self.config.charts_directory) / filename
                fig.write_html(str(filepath))
                logger.info(f"Chart saved to {filepath}")
                return True
            except Exception as e:
                logger.error(f"Error saving chart: {e}")
                return False
        return False
    
    def show_chart(self, fig: go.Figure):
        """Display chart in browser"""
        fig.show()
    
    @staticmethod
    def create_overlay(name: str, data: pd.Series, color: str,
                      width: int = 1, opacity: float = 1.0,
                      type: str = "line") -> ChartOverlay:
        """Create a chart overlay"""
        return ChartOverlay(
            name=name,
            data=data,
            color=color,
            width=width,
            opacity=opacity,
            type=type
        )

# Example usage
if __name__ == "__main__":
    # Create sample data
    dates = pd.date_range(start='2024-01-01', end='2024-02-01', freq='1H')
    np.random.seed(42)
    
    market_data = pd.DataFrame({
        'open': np.random.randn(len(dates)).cumsum() + 100,
        'high': np.random.randn(len(dates)).cumsum() + 102,
        'low': np.random.randn(len(dates)).cumsum() + 98,
        'close': np.random.randn(len(dates)).cumsum() + 100,
        'volume': np.random.randint(1000, 10000, len(dates))
    }, index=dates)
    
    # Create visualizer
    config = VisualizationConfig(default_theme="dark")
    visualizer = EliteVisualizer(config)
    
    # Create and show chart
    chart = visualizer.create_market_chart(
        market_data=market_data,
        title="Example Market Chart"
    )
    
    visualizer.show_chart(chart)
