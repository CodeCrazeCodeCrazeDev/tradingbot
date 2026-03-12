"""
Dashboard Visualization Module
"""

from enum import Enum
from typing import Dict, List, Any, Optional
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
import numpy
import pandas

import logging
logger = logging.getLogger(__name__)



class ChartType(Enum):
    """Types of charts available."""
    LINE = "line"
    CANDLESTICK = "candlestick"
    BAR = "bar"
    SCATTER = "scatter"
    HEATMAP = "heatmap"
    PIE = "pie"
    HISTOGRAM = "histogram"
    BOX = "box"
    VIOLIN = "violin"
    AREA = "area"
    WATERFALL = "waterfall"
    RADAR = "radar"
    TREEMAP = "treemap"
    SUNBURST = "sunburst"
    SANKEY = "sankey"


class ChartTheme(Enum):
    """Chart themes."""
    DARK = "plotly_dark"
    LIGHT = "plotly_white"
    MINIMAL = "simple_white"
    MODERN = "plotly"
    PRESENTATION = "presentation"


class ChartFactory:
    """Factory for creating various types of charts."""
    
    def __init__(self, theme: ChartTheme = ChartTheme.DARK):
        """Initialize chart factory."""
        try:
            self.theme = theme
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def create_chart(self, chart_type: ChartType, data: Dict[str, Any], 
                    title: str = "", x_title: str = "", y_title: str = "") -> go.Figure:
        """Create a chart based on type."""
        try:
            if chart_type == ChartType.LINE:
                return self._create_line_chart(data, title, x_title, y_title)
            elif chart_type == ChartType.CANDLESTICK:
                return self._create_candlestick_chart(data, title, x_title, y_title)
            elif chart_type == ChartType.BAR:
                return self._create_bar_chart(data, title, x_title, y_title)
            elif chart_type == ChartType.SCATTER:
                return self._create_scatter_chart(data, title, x_title, y_title)
            elif chart_type == ChartType.HEATMAP:
                return self._create_heatmap_chart(data, title, x_title, y_title)
            else:
                raise ValueError(f"Chart type {chart_type} not supported")
        except Exception as e:
            logger.error(f"Error in create_chart: {e}")
            raise
    
    def _create_line_chart(self, data: Dict[str, Any], title: str, 
                          x_title: str, y_title: str) -> go.Figure:
        """Create a line chart."""
        try:
            fig = go.Figure()
        
            # Add traces
            for name, series in data.items():
                fig.add_trace(go.Scatter(
                    x=series.get('x'),
                    y=series.get('y'),
                    name=name,
                    mode='lines'
                ))
        
            # Update layout
            self._update_layout(fig, title, x_title, y_title)
        
            return fig
        except Exception as e:
            logger.error(f"Error in _create_line_chart: {e}")
            raise
    
    def _create_candlestick_chart(self, data: Dict[str, Any], title: str, 
                                 x_title: str, y_title: str) -> go.Figure:
        """Create a candlestick chart."""
        try:
            fig = go.Figure()
        
            # Add candlestick
            fig.add_trace(go.Candlestick(
                x=data.get('time'),
                open=data.get('open'),
                high=data.get('high'),
                low=data.get('low'),
                close=data.get('close'),
                name="OHLC"
            ))
        
            # Update layout
            self._update_layout(fig, title, x_title, y_title)
        
            return fig
        except Exception as e:
            logger.error(f"Error in _create_candlestick_chart: {e}")
            raise
    
    def _create_bar_chart(self, data: Dict[str, Any], title: str, 
                         x_title: str, y_title: str) -> go.Figure:
        """Create a bar chart."""
        try:
            fig = go.Figure()
        
            # Add bars
            for name, series in data.items():
                fig.add_trace(go.Bar(
                    x=series.get('x'),
                    y=series.get('y'),
                    name=name
                ))
        
            # Update layout
            self._update_layout(fig, title, x_title, y_title)
        
            return fig
        except Exception as e:
            logger.error(f"Error in _create_bar_chart: {e}")
            raise
    
    def _create_scatter_chart(self, data: Dict[str, Any], title: str, 
                            x_title: str, y_title: str) -> go.Figure:
        """Create a scatter chart."""
        try:
            fig = go.Figure()
        
            # Add scatter plots
            for name, series in data.items():
                fig.add_trace(go.Scatter(
                    x=series.get('x'),
                    y=series.get('y'),
                    name=name,
                    mode='markers'
                ))
        
            # Update layout
            self._update_layout(fig, title, x_title, y_title)
        
            return fig
        except Exception as e:
            logger.error(f"Error in _create_scatter_chart: {e}")
            raise
    
    def _create_heatmap_chart(self, data: Dict[str, Any], title: str, 
                             x_title: str, y_title: str) -> go.Figure:
        """Create a heatmap chart."""
        try:
            fig = go.Figure()
        
            # Add heatmap
            fig.add_trace(go.Heatmap(
                z=data.get('values'),
                x=data.get('x_labels'),
                y=data.get('y_labels'),
                colorscale='RdBu'
            ))
        
            # Update layout
            self._update_layout(fig, title, x_title, y_title)
        
            return fig
        except Exception as e:
            logger.error(f"Error in _create_heatmap_chart: {e}")
            raise
    
    def _update_layout(self, fig: go.Figure, title: str, x_title: str, y_title: str):
        """Update chart layout with common settings."""
        try:
            fig.update_layout(
                title=title,
                xaxis_title=x_title,
                yaxis_title=y_title,
                template=self.theme.value,
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
        except Exception as e:
            logger.error(f"Error in _update_layout: {e}")
            raise
