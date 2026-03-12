import logging
logger = logging.getLogger(__name__)
"""Trade Heatmap System.

This module implements advanced trade heatmap visualization capabilities
to identify liquidity pools, stop clusters, and imbalance zones.
"""

import numpy as np
import pandas as pd
from enum import Enum, auto
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple, Union
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from matplotlib.figure import Figure
import seaborn as sns
from loguru import logger
import numpy
import pandas


class HeatmapType(Enum):
    """Types of trade heatmaps."""
    LIQUIDITY = auto()
    STOP_CLUSTERS = auto()
    IMBALANCE = auto()
    ORDER_FLOW = auto()
    VOLUME_PROFILE = auto()
    MULTI_FACTOR = auto()


@dataclass
class HeatmapZone:
    """Zone identified in a heatmap."""
    price_start: float
    price_end: float
    intensity: float  # 0.0 to 1.0
    zone_type: str
    description: str
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
    
    @property
    def mid_price(self) -> float:
        """Get the middle price of the zone."""
        return (self.price_start + self.price_end) / 2


class TradeHeatmap:
    """Advanced trade heatmap system for visualizing market microstructure.
    
    Features:
    - Liquidity pool visualization
    - Stop-loss cluster detection
    - Order flow imbalance mapping
    - Volume profile integration
    - Multi-factor heatmaps
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize the trade heatmap system.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.price_resolution = self.config.get('price_resolution', 100)
        self.color_map = self.config.get('color_map', 'viridis')
        self.alpha = self.config.get('alpha', 0.7)
        self.heatmap_cache = {}
        logger.info("TradeHeatmap initialized")
    
    def generate_liquidity_heatmap(self, market_data: pd.DataFrame, 
                                 order_book_data: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """Generate a liquidity heatmap showing where liquidity pools exist.
        
        Args:
            market_data: DataFrame with OHLCV data
            order_book_data: Optional list of order book snapshots
            
        Returns:
            Dictionary with heatmap data and identified zones
        """
        logger.info("Generating liquidity heatmap")
        
        try:
            # Determine price range
            price_min = market_data['low'].min() * 0.995
            price_max = market_data['high'].max() * 1.005
            
            # Create price grid
            price_grid = np.linspace(price_min, price_max, self.price_resolution)
            liquidity_values = np.zeros(self.price_resolution)
            
            # Process market data for liquidity signals
            self._process_market_data_for_liquidity(market_data, price_grid, liquidity_values)
            
            # Process order book data if available
            if order_book_data:
                self._process_order_book_for_liquidity(order_book_data, price_grid, liquidity_values)
            
            # Normalize liquidity values
            max_liquidity = np.max(liquidity_values)
            if max_liquidity > 0:
                liquidity_values = liquidity_values / max_liquidity
            
            # Identify liquidity zones
            zones = self._identify_liquidity_zones(price_grid, liquidity_values)
            
            # Create heatmap figure
            fig = self._create_heatmap_figure(price_grid, liquidity_values, "Liquidity Heatmap")
            
            # Cache the result
            result = {
                'type': HeatmapType.LIQUIDITY,
                'price_grid': price_grid.tolist(),
                'values': liquidity_values.tolist(),
                'zones': zones,
                'figure': fig,
                'timestamp': datetime.now().isoformat()
            }
            
            self.heatmap_cache['liquidity'] = result
            return result
            
        except Exception as e:
            logger.error(f"Error generating liquidity heatmap: {e}")
            return {
                'type': HeatmapType.LIQUIDITY,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def generate_stop_cluster_heatmap(self, market_data: pd.DataFrame) -> Dict[str, Any]:
        """Generate a heatmap showing clusters of stop orders.
        
        Args:
            market_data: DataFrame with OHLCV data
            
        Returns:
            Dictionary with heatmap data and identified zones
        """
        logger.info("Generating stop cluster heatmap")
        
        try:
            # Determine price range
            price_min = market_data['low'].min() * 0.995
            price_max = market_data['high'].max() * 1.005
            
            # Create price grid
            price_grid = np.linspace(price_min, price_max, self.price_resolution)
            stop_values = np.zeros(self.price_resolution)
            
            # Process market data for stop clusters
            self._process_market_data_for_stops(market_data, price_grid, stop_values)
            
            # Normalize stop values
            max_stops = np.max(stop_values)
            if max_stops > 0:
                stop_values = stop_values / max_stops
            
            # Identify stop cluster zones
            zones = self._identify_stop_zones(price_grid, stop_values)
            
            # Create heatmap figure
            fig = self._create_heatmap_figure(price_grid, stop_values, "Stop Cluster Heatmap", cmap='hot')
            
            # Cache the result
            result = {
                'type': HeatmapType.STOP_CLUSTERS,
                'price_grid': price_grid.tolist(),
                'values': stop_values.tolist(),
                'zones': zones,
                'figure': fig,
                'timestamp': datetime.now().isoformat()
            }
            
            self.heatmap_cache['stop_clusters'] = result
            return result
            
        except Exception as e:
            logger.error(f"Error generating stop cluster heatmap: {e}")
            return {
                'type': HeatmapType.STOP_CLUSTERS,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def generate_imbalance_heatmap(self, market_data: pd.DataFrame) -> Dict[str, Any]:
        """Generate a heatmap showing order flow imbalances.
        
        Args:
            market_data: DataFrame with OHLCV data including buy/sell volume
            
        Returns:
            Dictionary with heatmap data and identified zones
        """
        logger.info("Generating imbalance heatmap")
        
        try:
            # Check if we have buy/sell volume data
            has_volume_data = all(col in market_data.columns for col in ['buy_volume', 'sell_volume'])
            
            if not has_volume_data:
                logger.warning("Buy/sell volume data not available, using synthetic data")
                # Create synthetic buy/sell volume
                market_data['buy_volume'] = market_data['volume'] * (0.5 + 0.5 * (market_data['close'] > market_data['open']).astype(float))
                market_data['sell_volume'] = market_data['volume'] - market_data['buy_volume']
            
            # Determine price range
            price_min = market_data['low'].min() * 0.995
            price_max = market_data['high'].max() * 1.005
            
            # Create price grid
            price_grid = np.linspace(price_min, price_max, self.price_resolution)
            imbalance_values = np.zeros(self.price_resolution)
            
            # Process market data for imbalances
            self._process_market_data_for_imbalance(market_data, price_grid, imbalance_values)
            
            # Normalize imbalance values to [-1, 1] range
            max_imbalance = np.max(np.abs(imbalance_values))
            if max_imbalance > 0:
                imbalance_values = imbalance_values / max_imbalance
            
            # Identify imbalance zones
            zones = self._identify_imbalance_zones(price_grid, imbalance_values)
            
            # Create heatmap figure
            fig = self._create_imbalance_heatmap_figure(price_grid, imbalance_values)
            
            # Cache the result
            result = {
                'type': HeatmapType.IMBALANCE,
                'price_grid': price_grid.tolist(),
                'values': imbalance_values.tolist(),
                'zones': zones,
                'figure': fig,
                'timestamp': datetime.now().isoformat()
            }
            
            self.heatmap_cache['imbalance'] = result
            return result
            
        except Exception as e:
            logger.error(f"Error generating imbalance heatmap: {e}")
            return {
                'type': HeatmapType.IMBALANCE,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def generate_multi_factor_heatmap(self, market_data: pd.DataFrame, 
                                    order_book_data: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """Generate a combined multi-factor heatmap.
        
        Args:
            market_data: DataFrame with OHLCV data
            order_book_data: Optional list of order book snapshots
            
        Returns:
            Dictionary with heatmap data and identified zones
        """
        logger.info("Generating multi-factor heatmap")
        
        try:
            # Generate individual heatmaps
            liquidity_heatmap = self.generate_liquidity_heatmap(market_data, order_book_data)
            stop_heatmap = self.generate_stop_cluster_heatmap(market_data)
            imbalance_heatmap = self.generate_imbalance_heatmap(market_data)
            
            # Check for errors
            if any('error' in hm for hm in [liquidity_heatmap, stop_heatmap, imbalance_heatmap]):
                logger.warning("One or more component heatmaps had errors")
            
            # Determine price range
            price_min = market_data['low'].min() * 0.995
            price_max = market_data['high'].max() * 1.005
            
            # Create price grid
            price_grid = np.linspace(price_min, price_max, self.price_resolution)
            multi_factor_values = np.zeros(self.price_resolution)
            
            # Combine heatmap values with weights
            if 'values' in liquidity_heatmap:
                liquidity_values = np.array(liquidity_heatmap['values'])
                multi_factor_values += liquidity_values * 0.4  # 40% weight
            
            if 'values' in stop_heatmap:
                stop_values = np.array(stop_heatmap['values'])
                multi_factor_values += stop_values * 0.3  # 30% weight
            
            if 'values' in imbalance_heatmap:
                imbalance_values = np.array(imbalance_heatmap['values'])
                # Convert from [-1, 1] to [0, 1] for combining
                imbalance_positive = (imbalance_values + 1) / 2
                multi_factor_values += imbalance_positive * 0.3  # 30% weight
            
            # Normalize combined values
            max_value = np.max(multi_factor_values)
            if max_value > 0:
                multi_factor_values = multi_factor_values / max_value
            
            # Identify combined zones
            zones = []
            if 'zones' in liquidity_heatmap:
                zones.extend(liquidity_heatmap['zones'])
            if 'zones' in stop_heatmap:
                zones.extend(stop_heatmap['zones'])
            if 'zones' in imbalance_heatmap:
                zones.extend(imbalance_heatmap['zones'])
            
            # Sort zones by intensity
            zones = sorted(zones, key=lambda z: z.intensity, reverse=True)
            
            # Create multi-factor heatmap figure
            fig = self._create_heatmap_figure(price_grid, multi_factor_values, "Multi-Factor Heatmap", cmap='plasma')
            
            # Cache the result
            result = {
                'type': HeatmapType.MULTI_FACTOR,
                'price_grid': price_grid.tolist(),
                'values': multi_factor_values.tolist(),
                'zones': zones,
                'component_heatmaps': {
                    'liquidity': liquidity_heatmap.get('type'),
                    'stop_clusters': stop_heatmap.get('type'),
                    'imbalance': imbalance_heatmap.get('type')
                },
                'figure': fig,
                'timestamp': datetime.now().isoformat()
            }
            
            self.heatmap_cache['multi_factor'] = result
            return result
            
        except Exception as e:
            logger.error(f"Error generating multi-factor heatmap: {e}")
            return {
                'type': HeatmapType.MULTI_FACTOR,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def _process_market_data_for_liquidity(self, data: pd.DataFrame, price_grid: np.ndarray, 
                                         liquidity_values: np.ndarray) -> None:
        """Process market data to extract liquidity signals."""
        # Find price levels with high volume
        for i, row in data.iterrows():
            # Price range for this candle
            low, high = row['low'], row['high']
            volume = row['volume']
            
            # Add volume to price grid
            for j, price in enumerate(price_grid):
                if low <= price <= high:
                    # Weight by proximity to open/close (liquidity often at these levels)
                    proximity_open = 1.0 - min(abs(price - row['open']) / (high - low) if high > low else 1.0, 1.0)
                    proximity_close = 1.0 - min(abs(price - row['close']) / (high - low) if high > low else 1.0, 1.0)
                    
                    # Higher weight for prices near open/close
                    weight = 0.5 + 0.5 * max(proximity_open, proximity_close)
                    
                    # Add weighted volume to liquidity
                    liquidity_values[j] += volume * weight
        
        # Apply smoothing
        liquidity_values = np.convolve(liquidity_values, np.ones(5)/5, mode='same')
    
    def _process_order_book_for_liquidity(self, order_book_data: List[Dict], price_grid: np.ndarray, 
                                        liquidity_values: np.ndarray) -> None:
        """Process order book data to extract liquidity signals."""
        if not order_book_data:
            return
        
        # Use the most recent order book snapshot
        latest_book = order_book_data[-1]
        
        # Process bids (buy orders)
        for price_str, volume in latest_book.get('bids', {}).items():
            try:
                price = float(price_str)
                # Find closest price in grid
                idx = np.abs(price_grid - price).argmin()
                liquidity_values[idx] += volume
            except (ValueError, TypeError):
                continue
        
        # Process asks (sell orders)
        for price_str, volume in latest_book.get('asks', {}).items():
            try:
                price = float(price_str)
                # Find closest price in grid
                idx = np.abs(price_grid - price).argmin()
                liquidity_values[idx] += volume
            except (ValueError, TypeError):
                continue
    
    def _process_market_data_for_stops(self, data: pd.DataFrame, price_grid: np.ndarray, 
                                     stop_values: np.ndarray) -> None:
        """Process market data to identify potential stop-loss clusters."""
        # Look for swing lows (potential stop areas for longs)
        for i in range(2, len(data) - 2):
            if data['low'].iloc[i] < data['low'].iloc[i-1] and data['low'].iloc[i] < data['low'].iloc[i-2] and \
               data['low'].iloc[i] < data['low'].iloc[i+1] and data['low'].iloc[i] < data['low'].iloc[i+2]:
                
                # This is a swing low, likely stop area below
                stop_price = data['low'].iloc[i] * 0.998  # Slightly below
                
                # Find closest price in grid
                idx = np.abs(price_grid - stop_price).argmin()
                
                # Add stop cluster with weight based on volume
                volume_weight = data['volume'].iloc[i] / data['volume'].mean()
                stop_values[idx] += volume_weight
                
                # Add some weight to nearby prices (stops are often clustered)
                for j in range(1, 6):
                    if idx - j >= 0:
                        stop_values[idx - j] += volume_weight * (1.0 - j * 0.15)
                    if idx + j < len(stop_values):
                        stop_values[idx + j] += volume_weight * (1.0 - j * 0.15)
        
        # Look for swing highs (potential stop areas for shorts)
        for i in range(2, len(data) - 2):
            if data['high'].iloc[i] > data['high'].iloc[i-1] and data['high'].iloc[i] > data['high'].iloc[i-2] and \
               data['high'].iloc[i] > data['high'].iloc[i+1] and data['high'].iloc[i] > data['high'].iloc[i+2]:
                
                # This is a swing high, likely stop area above
                stop_price = data['high'].iloc[i] * 1.002  # Slightly above
                
                # Find closest price in grid
                idx = np.abs(price_grid - stop_price).argmin()
                
                # Add stop cluster with weight based on volume
                volume_weight = data['volume'].iloc[i] / data['volume'].mean()
                stop_values[idx] += volume_weight
                
                # Add some weight to nearby prices (stops are often clustered)
                for j in range(1, 6):
                    if idx - j >= 0:
                        stop_values[idx - j] += volume_weight * (1.0 - j * 0.15)
                    if idx + j < len(stop_values):
                        stop_values[idx + j] += volume_weight * (1.0 - j * 0.15)
        
        # Add weight to round numbers (common stop placement)
        for i, price in enumerate(price_grid):
            # Check if price is a round number
            rounded_price = round(price, 2)
            if rounded_price == price:
                stop_values[i] += 0.5
            
            # Check for even more round numbers
            rounded_price = round(price, 1)
            if rounded_price == price:
                stop_values[i] += 1.0
            
            rounded_price = round(price, 0)
            if rounded_price == price:
                stop_values[i] += 2.0
        
        # Apply smoothing
        stop_values = np.convolve(stop_values, np.ones(3)/3, mode='same')
    
    def _process_market_data_for_imbalance(self, data: pd.DataFrame, price_grid: np.ndarray, 
                                         imbalance_values: np.ndarray) -> None:
        """Process market data to identify order flow imbalances."""
        # Calculate imbalance for each candle
        for i, row in data.iterrows():
            # Price range for this candle
            low, high = row['low'], row['high']
            buy_volume = row['buy_volume']
            sell_volume = row['sell_volume']
            
            # Calculate imbalance ratio (-1 to 1)
            total_volume = buy_volume + sell_volume
            if total_volume > 0:
                imbalance_ratio = (buy_volume - sell_volume) / total_volume
            else:
                imbalance_ratio = 0
            
            # Add imbalance to price grid
            for j, price in enumerate(price_grid):
                if low <= price <= high:
                    # Weight by volume
                    volume_weight = total_volume / data['volume'].mean()
                    
                    # Add weighted imbalance
                    imbalance_values[j] += imbalance_ratio * volume_weight
        
        # Look for fair value gaps (imbalance zones)
        for i in range(1, len(data)):
            # Check for bullish fair value gap
            if data['low'].iloc[i] > data['high'].iloc[i-1]:
                gap_bottom = data['high'].iloc[i-1]
                gap_top = data['low'].iloc[i]
                
                # Add strong bullish imbalance to the gap area
                for j, price in enumerate(price_grid):
                    if gap_bottom <= price <= gap_top:
                        imbalance_values[j] += 2.0  # Strong bullish signal
            
            # Check for bearish fair value gap
            if data['high'].iloc[i] < data['low'].iloc[i-1]:
                gap_bottom = data['high'].iloc[i]
                gap_top = data['low'].iloc[i-1]
                
                # Add strong bearish imbalance to the gap area
                for j, price in enumerate(price_grid):
                    if gap_bottom <= price <= gap_top:
                        imbalance_values[j] -= 2.0  # Strong bearish signal
        
        # Apply smoothing
        imbalance_values = np.convolve(imbalance_values, np.ones(3)/3, mode='same')
    
    def _identify_liquidity_zones(self, price_grid: np.ndarray, liquidity_values: np.ndarray) -> List[HeatmapZone]:
        """Identify significant liquidity zones from the heatmap."""
        zones = []
        threshold = 0.5  # Minimum intensity to consider
        
        # Find peaks in liquidity
        peaks = []
        for i in range(1, len(liquidity_values) - 1):
            if liquidity_values[i] > threshold and \
               liquidity_values[i] >= liquidity_values[i-1] and \
               liquidity_values[i] >= liquidity_values[i+1]:
                peaks.append(i)
        
        # Create zones around peaks
        for peak_idx in peaks:
            # Find zone boundaries
            left_idx = peak_idx
            while left_idx > 0 and liquidity_values[left_idx] > threshold * 0.5:
                left_idx -= 1
            
            right_idx = peak_idx
            while right_idx < len(liquidity_values) - 1 and liquidity_values[right_idx] > threshold * 0.5:
                right_idx += 1
            
            # Create zone
            zone = HeatmapZone(
                price_start=price_grid[left_idx],
                price_end=price_grid[right_idx],
                intensity=liquidity_values[peak_idx],
                zone_type="liquidity",
                description=f"Liquidity pool at {price_grid[peak_idx]:.5f}",
                metadata={
                    'peak_price': price_grid[peak_idx],
                    'width': price_grid[right_idx] - price_grid[left_idx]
                }
            )
            zones.append(zone)
        
        return zones
    
    def _identify_stop_zones(self, price_grid: np.ndarray, stop_values: np.ndarray) -> List[HeatmapZone]:
        """Identify significant stop-loss clusters from the heatmap."""
        zones = []
        threshold = 0.5  # Minimum intensity to consider
        
        # Find peaks in stop clusters
        peaks = []
        for i in range(1, len(stop_values) - 1):
            if stop_values[i] > threshold and \
               stop_values[i] >= stop_values[i-1] and \
               stop_values[i] >= stop_values[i+1]:
                peaks.append(i)
        
        # Create zones around peaks
        for peak_idx in peaks:
            # Find zone boundaries
            left_idx = peak_idx
            while left_idx > 0 and stop_values[left_idx] > threshold * 0.5:
                left_idx -= 1
            
            right_idx = peak_idx
            while right_idx < len(stop_values) - 1 and stop_values[right_idx] > threshold * 0.5:
                right_idx += 1
            
            # Create zone
            zone = HeatmapZone(
                price_start=price_grid[left_idx],
                price_end=price_grid[right_idx],
                intensity=stop_values[peak_idx],
                zone_type="stop_cluster",
                description=f"Stop cluster at {price_grid[peak_idx]:.5f}",
                metadata={
                    'peak_price': price_grid[peak_idx],
                    'width': price_grid[right_idx] - price_grid[left_idx]
                }
            )
            zones.append(zone)
        
        return zones
    
    def _identify_imbalance_zones(self, price_grid: np.ndarray, imbalance_values: np.ndarray) -> List[HeatmapZone]:
        """Identify significant imbalance zones from the heatmap."""
        zones = []
        threshold = 0.5  # Minimum absolute intensity to consider
        
        # Find peaks in imbalance (both positive and negative)
        peaks = []
        for i in range(1, len(imbalance_values) - 1):
            if abs(imbalance_values[i]) > threshold:
                if imbalance_values[i] > 0 and \
                   imbalance_values[i] >= imbalance_values[i-1] and \
                   imbalance_values[i] >= imbalance_values[i+1]:
                    peaks.append((i, "bullish"))
                elif imbalance_values[i] < 0 and \
                     imbalance_values[i] <= imbalance_values[i-1] and \
                     imbalance_values[i] <= imbalance_values[i+1]:
                    peaks.append((i, "bearish"))
        
        # Create zones around peaks
        for peak_idx, direction in peaks:
            # Find zone boundaries
            left_idx = peak_idx
            while left_idx > 0 and abs(imbalance_values[left_idx]) > threshold * 0.5:
                left_idx -= 1
            
            right_idx = peak_idx
            while right_idx < len(imbalance_values) - 1 and abs(imbalance_values[right_idx]) > threshold * 0.5:
                right_idx += 1
            
            # Create zone
            zone = HeatmapZone(
                price_start=price_grid[left_idx],
                price_end=price_grid[right_idx],
                intensity=abs(imbalance_values[peak_idx]),
                zone_type=f"imbalance_{direction}",
                description=f"{direction.capitalize()} imbalance at {price_grid[peak_idx]:.5f}",
                metadata={
                    'peak_price': price_grid[peak_idx],
                    'width': price_grid[right_idx] - price_grid[left_idx],
                    'direction': direction,
                    'imbalance_value': imbalance_values[peak_idx]
                }
            )
            zones.append(zone)
        
        return zones
    
    def _create_heatmap_figure(self, price_grid: np.ndarray, values: np.ndarray, 
                             title: str, cmap: str = None) -> Figure:
        """Create a matplotlib figure with the heatmap visualization."""
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Use specified colormap or default
        cmap = cmap or self.color_map
        
        # Create heatmap
        ax.fill_between(price_grid, 0, values, alpha=self.alpha, color='blue', 
                       label='Intensity')
        
        # Add grid and labels
        ax.grid(True, alpha=0.3)
        ax.set_xlabel('Price')
        ax.set_ylabel('Intensity')
        ax.set_title(title)
        
        # Add colorbar
        sm = plt.cm.ScalarMappable(cmap=cmap, norm=plt.Normalize(0, 1))
        sm.set_array([])
        fig.colorbar(sm, ax=ax, label='Intensity')
        
        fig.tight_layout()
        return fig
    
    def _create_imbalance_heatmap_figure(self, price_grid: np.ndarray, 
                                       imbalance_values: np.ndarray) -> Figure:
        """Create a matplotlib figure with the imbalance heatmap visualization."""
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Create positive and negative arrays
        positive_values = np.maximum(imbalance_values, 0)
        negative_values = np.minimum(imbalance_values, 0)
        
        # Plot positive (bullish) imbalance in green
        ax.fill_between(price_grid, 0, positive_values, alpha=self.alpha, color='green', 
                       label='Bullish Imbalance')
        
        # Plot negative (bearish) imbalance in red
        ax.fill_between(price_grid, 0, negative_values, alpha=self.alpha, color='red', 
                       label='Bearish Imbalance')
        
        # Add grid and labels
        ax.grid(True, alpha=0.3)
        ax.set_xlabel('Price')
        ax.set_ylabel('Imbalance')
        ax.set_title('Order Flow Imbalance Heatmap')
        ax.legend()
        
        fig.tight_layout()
        return fig
