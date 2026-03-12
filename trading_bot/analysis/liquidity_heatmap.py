import logging
logger = logging.getLogger(__name__)
"""
Liquidity Heatmap Visualization System

This module provides real-time liquidity heatmap visualization capabilities
for comprehensive market analysis and trading decision support.
"""

import time
from collections import defaultdict
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
import threading

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from loguru import logger

from .liquidity import LiquidityAnalyzer, LiquidityPool, OrderBlock, FairValueGap
from .realtime_liquidity import RealTimeLiquidityAnalyzer
from .order_block_tracker import OrderBlockTracker
from .market_structure import TimeFrame


class HeatmapType(Enum):
    """Types of liquidity heatmaps."""
    LIQUIDITY_POOLS = "liquidity_pools"
    ORDER_BLOCKS = "order_blocks"
    FAIR_VALUE_GAPS = "fvgs"
    COMBINED = "combined"
    VOLUME_PROFILE = "volume_profile"


@dataclass
class HeatmapConfig:
    """Configuration for heatmap visualization."""
    price_levels: int = 100
    time_window_hours: float = 24.0
    update_interval: float = 5.0
    color_scheme: str = "viridis"
    show_price_levels: bool = True
    show_volume: bool = True
    opacity: float = 0.7
    width: int = 1200
    height: int = 800


class LiquidityHeatmapVisualizer:
    """
    Advanced liquidity heatmap visualization system.
    
    Provides real-time visual analysis of liquidity zones including:
    - Liquidity pool density maps
    - Order block strength visualization
    - Fair value gap analysis
    - Combined multi-layer heatmaps
    """
    
    def __init__(self, config: HeatmapConfig = None):
        """Initialize the heatmap visualizer."""
        self.config = config or HeatmapConfig()
        
        # Data storage
        self.liquidity_data: Dict[str, Dict[TimeFrame, Dict]] = defaultdict(
            lambda: defaultdict(dict)
        )
        self.price_history: Dict[str, List[Tuple[float, float]]] = defaultdict(list)
        
        # Visualization components
        self.figures: Dict[str, go.Figure] = {}
        self.update_lock = threading.RLock()
        
        # Performance tracking
        self.render_times = []
        self.update_count = 0
    
    def update_liquidity_data(self, symbol: str, timeframe: TimeFrame, 
                            liquidity_data: Dict[str, Any]):
        """Update liquidity data for visualization."""
        with self.update_lock:
            self.liquidity_data[symbol][timeframe] = {
                'timestamp': time.time(),
                'buy_pools': liquidity_data.get('buy_pools', []),
                'sell_pools': liquidity_data.get('sell_pools', []),
                'order_blocks': liquidity_data.get('order_blocks', []),
                'fvgs': liquidity_data.get('fvgs', []),
                'volume_profile': liquidity_data.get('volume_profile', None)
            }
            self.update_count += 1
    
    def create_liquidity_pools_heatmap(self, symbol: str, timeframe: TimeFrame) -> go.Figure:
        """Create heatmap for liquidity pools."""
        start_time = time.time()
        
        data = self.liquidity_data[symbol][timeframe]
        if not data:
            return self._create_empty_figure(f"{symbol} {timeframe.name} - No Data")
        
        # Extract pool data
        buy_pools = data.get('buy_pools', [])
        sell_pools = data.get('sell_pools', [])
        
        # Create price grid
        all_prices = []
        for pool in buy_pools + sell_pools:
            if isinstance(pool, dict):
                all_prices.append(pool.get('price', 0))
            else:
                all_prices.append(pool.price)
        
        if not all_prices:
            return self._create_empty_figure(f"{symbol} {timeframe.name} - No Pools")
        
        price_min = min(all_prices) * 0.999
        price_max = max(all_prices) * 1.001
        price_levels = np.linspace(price_min, price_max, self.config.price_levels)
        
        # Create heatmap data
        buy_intensity = np.zeros(len(price_levels))
        sell_intensity = np.zeros(len(price_levels))
        
        # Map buy pools to intensity
        for pool in buy_pools:
            price = pool.get('price', 0) if isinstance(pool, dict) else pool.price
            strength = pool.get('strength', 1.0) if isinstance(pool, dict) else pool.strength
            
            # Find nearest price level
            idx = np.argmin(np.abs(price_levels - price))
            buy_intensity[idx] += strength
        
        # Map sell pools to intensity
        for pool in sell_pools:
            price = pool.get('price', 0) if isinstance(pool, dict) else pool.price
            strength = pool.get('strength', 1.0) if isinstance(pool, dict) else pool.strength
            
            idx = np.argmin(np.abs(price_levels - price))
            sell_intensity[idx] += strength
        
        # Create figure
        fig = go.Figure()
        
        # Add buy pools heatmap
        fig.add_trace(go.Scatter(
            x=buy_intensity,
            y=price_levels,
            mode='lines',
            fill='tonextx',
            name='Buy Liquidity',
            line=dict(color='green', width=0),
            fillcolor='rgba(0, 255, 0, 0.3)'
        ))
        
        # Add sell pools heatmap
        fig.add_trace(go.Scatter(
            x=-sell_intensity,
            y=price_levels,
            mode='lines',
            fill='tonextx',
            name='Sell Liquidity',
            line=dict(color='red', width=0),
            fillcolor='rgba(255, 0, 0, 0.3)'
        ))
        
        # Update layout
        fig.update_layout(
            title=f"{symbol} {timeframe.name} - Liquidity Pools Heatmap",
            xaxis_title="Liquidity Intensity",
            yaxis_title="Price Level",
            width=self.config.width,
            height=self.config.height,
            showlegend=True
        )
        
        self.render_times.append(time.time() - start_time)
        return fig
    
    def create_order_blocks_heatmap(self, symbol: str, timeframe: TimeFrame) -> go.Figure:
        """Create heatmap for order blocks."""
        start_time = time.time()
        
        data = self.liquidity_data[symbol][timeframe]
        if not data:
            return self._create_empty_figure(f"{symbol} {timeframe.name} - No Data")
        
        order_blocks = data.get('order_blocks', [])
        if not order_blocks:
            return self._create_empty_figure(f"{symbol} {timeframe.name} - No Order Blocks")
        
        # Create figure
        fig = go.Figure()
        
        # Add order blocks as rectangles
        for i, ob in enumerate(order_blocks):
            if isinstance(ob, dict):
                high = ob.get('high', 0)
                low = ob.get('low', 0)
                strength = ob.get('strength', 1.0)
                ob_type = ob.get('type', 'bullish')
            else:
                high = ob.high
                low = ob.low
                strength = ob.strength
                ob_type = ob.type.value
            
            color = 'green' if ob_type == 'bullish' else 'red'
            opacity = min(0.8, strength / 2.0)
            
            fig.add_shape(
                type="rect",
                x0=0, x1=1,
                y0=low, y1=high,
                fillcolor=color,
                opacity=opacity,
                line=dict(color=color, width=2)
            )
        
        # Update layout
        fig.update_layout(
            title=f"{symbol} {timeframe.name} - Order Blocks Heatmap",
            xaxis_title="Time",
            yaxis_title="Price Level",
            width=self.config.width,
            height=self.config.height
        )
        
        self.render_times.append(time.time() - start_time)
        return fig
    
    def create_combined_heatmap(self, symbol: str, timeframe: TimeFrame) -> go.Figure:
        """Create combined heatmap with all liquidity elements."""
        start_time = time.time()
        
        data = self.liquidity_data[symbol][timeframe]
        if not data:
            return self._create_empty_figure(f"{symbol} {timeframe.name} - No Data")
        
        # Create subplots
        fig = make_subplots(
            rows=3, cols=1,
            subplot_titles=['Liquidity Pools', 'Order Blocks', 'Fair Value Gaps'],
            vertical_spacing=0.1,
            shared_xaxes=True
        )
        
        # Add liquidity pools
        buy_pools = data.get('buy_pools', [])
        sell_pools = data.get('sell_pools', [])
        
        for pool in buy_pools:
            price = pool.get('price', 0) if isinstance(pool, dict) else pool.price
            strength = pool.get('strength', 1.0) if isinstance(pool, dict) else pool.strength
            
            fig.add_trace(go.Scatter(
                x=[0, strength], y=[price, price],
                mode='lines+markers',
                name='Buy Pool',
                line=dict(color='green', width=3),
                showlegend=False
            ), row=1, col=1)
        
        for pool in sell_pools:
            price = pool.get('price', 0) if isinstance(pool, dict) else pool.price
            strength = pool.get('strength', 1.0) if isinstance(pool, dict) else pool.strength
            
            fig.add_trace(go.Scatter(
                x=[0, strength], y=[price, price],
                mode='lines+markers',
                name='Sell Pool',
                line=dict(color='red', width=3),
                showlegend=False
            ), row=1, col=1)
        
        # Add order blocks
        order_blocks = data.get('order_blocks', [])
        for ob in order_blocks:
            if isinstance(ob, dict):
                high = ob.get('high', 0)
                low = ob.get('low', 0)
                strength = ob.get('strength', 1.0)
                ob_type = ob.get('type', 'bullish')
            else:
                high = ob.high
                low = ob.low
                strength = ob.strength
                ob_type = ob.type.value
            
            color = 'green' if ob_type == 'bullish' else 'red'
            
            fig.add_trace(go.Scatter(
                x=[0, strength, strength, 0, 0],
                y=[low, low, high, high, low],
                fill='toself',
                fillcolor=color,
                opacity=0.3,
                line=dict(color=color),
                name=f'{ob_type.title()} OB',
                showlegend=False
            ), row=2, col=1)
        
        # Add FVGs
        fvgs = data.get('fvgs', [])
        for fvg in fvgs:
            if isinstance(fvg, dict):
                high = fvg.get('high', 0)
                low = fvg.get('low', 0)
                fvg_type = fvg.get('type', 'bullish')
            else:
                high = fvg.high
                low = fvg.low
                fvg_type = fvg.type.value
            
            color = 'blue' if fvg_type == 'bullish' else 'orange'
            
            fig.add_trace(go.Scatter(
                x=[0, 1, 1, 0, 0],
                y=[low, low, high, high, low],
                fill='toself',
                fillcolor=color,
                opacity=0.2,
                line=dict(color=color),
                name=f'{fvg_type.title()} FVG',
                showlegend=False
            ), row=3, col=1)
        
        # Update layout
        fig.update_layout(
            title=f"{symbol} {timeframe.name} - Combined Liquidity Analysis",
            width=self.config.width,
            height=self.config.height * 1.5,
            showlegend=True
        )
        
        self.render_times.append(time.time() - start_time)
        return fig
    
    def create_volume_profile_heatmap(self, symbol: str, timeframe: TimeFrame) -> go.Figure:
        """Create volume profile heatmap."""
        start_time = time.time()
        
        data = self.liquidity_data[symbol][timeframe]
        if not data:
            return self._create_empty_figure(f"{symbol} {timeframe.name} - No Data")
        
        volume_profile = data.get('volume_profile')
        if not volume_profile:
            return self._create_empty_figure(f"{symbol} {timeframe.name} - No Volume Profile")
        
        # Extract volume profile data
        if isinstance(volume_profile, dict):
            price_levels = np.array(volume_profile.get('price_levels', []))
            volumes = np.array(volume_profile.get('volumes', []))
            poc = volume_profile.get('poc', 0)
            va_high = volume_profile.get('value_area_high', 0)
            va_low = volume_profile.get('value_area_low', 0)
        else:
            price_levels = volume_profile.price_levels
            volumes = volume_profile.volumes
            poc = volume_profile.poc
            va_high = volume_profile.value_area_high
            va_low = volume_profile.value_area_low
        
        # Create figure
        fig = go.Figure()
        
        # Add volume profile
        fig.add_trace(go.Scatter(
            x=volumes,
            y=price_levels,
            mode='lines',
            fill='tonextx',
            name='Volume Profile',
            line=dict(color='blue', width=2),
            fillcolor='rgba(0, 0, 255, 0.3)'
        ))
        
        # Add POC line
        fig.add_hline(
            y=poc,
            line_dash="dash",
            line_color="red",
            annotation_text="POC"
        )
        
        # Add value area
        fig.add_hrect(
            y0=va_low, y1=va_high,
            fillcolor="yellow",
            opacity=0.2,
            annotation_text="Value Area"
        )
        
        # Update layout
        fig.update_layout(
            title=f"{symbol} {timeframe.name} - Volume Profile Heatmap",
            xaxis_title="Volume",
            yaxis_title="Price Level",
            width=self.config.width,
            height=self.config.height
        )
        
        self.render_times.append(time.time() - start_time)
        return fig
    
    def _create_empty_figure(self, title: str) -> go.Figure:
        """Create an empty figure with a title."""
        fig = go.Figure()
        fig.update_layout(
            title=title,
            width=self.config.width,
            height=self.config.height,
            annotations=[
                dict(
                    text="No data available",
                    xref="paper", yref="paper",
                    x=0.5, y=0.5,
                    xanchor='center', yanchor='middle',
                    showarrow=False,
                    font=dict(size=20, color="gray")
                )
            ]
        )
        return fig
    
    def save_heatmap(self, fig: go.Figure, filename: str, format: str = 'html'):
        """Save heatmap to file."""
        try:
            if format.lower() == 'html':
                fig.write_html(filename)
            elif format.lower() == 'png':
                fig.write_image(filename)
            elif format.lower() == 'pdf':
                fig.write_image(filename)
            else:
                raise ValueError(f"Unsupported format: {format}")
            
            logger.info(f"Heatmap saved to {filename}")
            
        except Exception as e:
            logger.error(f"Error saving heatmap: {e}")
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get visualization performance statistics."""
        avg_render_time = np.mean(self.render_times) if self.render_times else 0.0
        
        return {
            'total_updates': self.update_count,
            'total_renders': len(self.render_times),
            'avg_render_time': avg_render_time,
            'max_render_time': max(self.render_times) if self.render_times else 0.0,
            'min_render_time': min(self.render_times) if self.render_times else 0.0
        }


class RealTimeHeatmapDashboard:
    """Real-time dashboard for liquidity heatmap visualization."""
    
    def __init__(self, analyzer: RealTimeLiquidityAnalyzer, 
                 visualizer: LiquidityHeatmapVisualizer):
        """Initialize the dashboard."""
        self.analyzer = analyzer
        self.visualizer = visualizer
        self.running = False
        self.update_thread: Optional[threading.Thread] = None
    
    def start_dashboard(self, symbols: List[str], timeframes: List[TimeFrame]):
        """Start the real-time dashboard."""
        self.symbols = symbols
        self.timeframes = timeframes
        self.running = True
        
        # Start update thread
        self.update_thread = threading.Thread(target=self._update_loop, daemon=True)
        self.update_thread.start()
        
        logger.info("Real-time heatmap dashboard started")
    
    def stop_dashboard(self):
        """Stop the dashboard."""
        self.running = False
        
        if self.update_thread and self.update_thread.is_alive():
            self.update_thread.join(timeout=5.0)
        
        logger.info("Real-time heatmap dashboard stopped")
    
    def _update_loop(self):
        """Main update loop for the dashboard."""
        while self.running:
            try:
                for symbol in self.symbols:
                    for timeframe in self.timeframes:
                        # Get liquidity data from analyzer
                        liquidity_data = self.analyzer.get_active_liquidity(symbol, timeframe)
                        
                        # Update visualizer
                        self.visualizer.update_liquidity_data(symbol, timeframe, liquidity_data)
                
                time.sleep(self.visualizer.config.update_interval)
                
            except Exception as e:
                logger.error(f"Error in dashboard update loop: {e}")
                time.sleep(1.0)


# Factory functions
def create_heatmap_visualizer(color_scheme: str = "viridis") -> LiquidityHeatmapVisualizer:
    """Create a heatmap visualizer with specified color scheme."""
    config = HeatmapConfig(
        color_scheme=color_scheme,
        update_interval=5.0,
        width=1200,
        height=800
    )
    
    return LiquidityHeatmapVisualizer(config)


def create_realtime_dashboard(symbols: List[str], timeframes: List[TimeFrame]) -> RealTimeHeatmapDashboard:
    """Create a complete real-time heatmap dashboard."""
    from .realtime_liquidity import create_default_streaming_analyzer
    
    # Create components
    analyzer = create_default_streaming_analyzer(symbols, timeframes)
    visualizer = create_heatmap_visualizer()
    
    # Create dashboard
    dashboard = RealTimeHeatmapDashboard(analyzer, visualizer)
    dashboard.start_dashboard(symbols, timeframes)
    
    return dashboard


if __name__ == "__main__":
    # Example usage
    
    # Create visualizer
    visualizer = create_heatmap_visualizer()
    
    # Sample data
    sample_data = {
        'buy_pools': [
            {'price': 1.1050, 'strength': 1.5},
            {'price': 1.1060, 'strength': 1.2}
        ],
        'sell_pools': [
            {'price': 1.1040, 'strength': 1.3},
            {'price': 1.1030, 'strength': 1.8}
        ],
        'order_blocks': [
            {'high': 1.1055, 'low': 1.1050, 'strength': 1.4, 'type': 'bullish'}
        ]
    }
    
    # Update data
    visualizer.update_liquidity_data('EURUSD', TimeFrame.M15, sample_data)
    
    # Create heatmaps
    pools_fig = visualizer.create_liquidity_pools_heatmap('EURUSD', TimeFrame.M15)
    combined_fig = visualizer.create_combined_heatmap('EURUSD', TimeFrame.M15)
    
    # Save heatmaps
    visualizer.save_heatmap(pools_fig, 'liquidity_pools_heatmap.html')
    visualizer.save_heatmap(combined_fig, 'combined_heatmap.html')
    
    # Get performance stats
    stats = visualizer.get_performance_stats()
    logger.info(f"Visualization performance: {stats}")
