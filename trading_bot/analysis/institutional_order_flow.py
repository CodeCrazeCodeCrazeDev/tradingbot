"""Institutional Order Flow Detection Module.

This module implements advanced institutional order flow detection capabilities
including footprint charts, volume profile analysis, and iceberg order recognition.
"""

import numpy as np
import pandas as pd
from enum import Enum, auto
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple, Union
from datetime import datetime
import logging
logger = logging.getLogger(__name__)
from loguru import logger
import numpy
import pandas


class OrderType(Enum):
    """Types of institutional orders."""
    ICEBERG = auto()
    BLOCK = auto()
    DARK_POOL = auto()
    STOP_HUNT = auto()
    LIQUIDITY_GRAB = auto()
    ACCUMULATION = auto()
    DISTRIBUTION = auto()
    SPOOFING = auto()


@dataclass
class OrderFlowSignal:
    """Signal from order flow analysis."""
    order_type: OrderType
    timestamp: datetime
    price_level: float
    volume: float
    confidence: float  # 0.0 to 1.0
    direction: str  # 'buy' or 'sell'
    timeframe: str
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class InstitutionalOrderFlowDetector:
    """Detects institutional order flow patterns in market data.
    
    Features:
    - Footprint chart analysis
    - Volume profile analysis
    - Iceberg order detection
    - Stop hunting patterns
    - Liquidity pool identification
    - Spoofing detection
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize the institutional order flow detector.
        
        Args:
            config: Configuration dictionary with detector parameters
        """
        self.config = config or {}
        self.min_block_volume = self.config.get('min_block_volume', 100)
        self.iceberg_threshold = self.config.get('iceberg_threshold', 0.7)
        self.volume_profile_bins = self.config.get('volume_profile_bins', 50)
        self.detection_history = []
        logger.info("InstitutionalOrderFlowDetector initialized")
    
    def detect_iceberg_orders(self, market_data: pd.DataFrame) -> List[OrderFlowSignal]:
        """Detect iceberg orders in market data.
        
        Iceberg orders are large orders that are broken into smaller visible parts,
        with the bulk of the order hidden from the order book.
        
        Args:
            market_data: DataFrame with market data including time, price, and volume
            
        Returns:
            List of OrderFlowSignal for detected iceberg orders
        """
        signals = []
        
        try:
            if len(market_data) < 10:
                logger.warning("Insufficient data for iceberg order detection")
                return signals
            
            # Calculate volume metrics
            market_data['volume_ma'] = market_data['volume'].rolling(10).mean()
            market_data['volume_std'] = market_data['volume'].rolling(10).std()
            market_data['volume_z'] = (market_data['volume'] - market_data['volume_ma']) / market_data['volume_std'].replace(0, 1)
            
            # Identify potential iceberg patterns
            # Look for repeated trades at same price level with similar volumes
            price_levels = market_data.groupby('price').agg({
                'volume': ['count', 'mean', 'std', 'sum']
            })
            price_levels.columns = ['count', 'mean_vol', 'std_vol', 'total_vol']
            
            # Filter for potential iceberg patterns
            iceberg_candidates = price_levels[
                (price_levels['count'] >= 3) &  # Multiple trades at same price
                (price_levels['std_vol'] / price_levels['mean_vol'] < 0.3) &  # Consistent volumes
                (price_levels['total_vol'] > self.min_block_volume)  # Significant total volume
            ]
            
            # Create signals for detected icebergs
            for price, row in iceberg_candidates.iterrows():
                # Determine direction (buy/sell) based on price movement
                price_data = market_data[market_data['price'] == price]
                if len(price_data) < 2:
                    continue
                    
                # Simple direction detection based on price movement after iceberg
                last_idx = price_data.index[-1]
                if last_idx + 1 < len(market_data):
                    direction = 'buy' if market_data.loc[last_idx + 1, 'price'] > price else 'sell'
                else:
                    direction = 'buy' if market_data['price'].iloc[-1] > market_data['price'].iloc[-2] else 'sell'
                
                # Calculate confidence based on pattern strength
                confidence = min(1.0, (row['count'] / 5) * (row['total_vol'] / self.min_block_volume) * self.iceberg_threshold)
                
                signal = OrderFlowSignal(
                    order_type=OrderType.ICEBERG,
                    timestamp=price_data.index[-1],
                    price_level=price,
                    volume=row['total_vol'],
                    confidence=confidence,
                    direction=direction,
                    timeframe=self.config.get('timeframe', '5m'),
                    metadata={
                        'trade_count': row['count'],
                        'mean_volume': row['mean_vol'],
                        'volume_consistency': row['std_vol'] / row['mean_vol']
                    }
                )
                
                signals.append(signal)
                logger.debug(f"Detected iceberg order at price {price}, volume {row['total_vol']}, confidence {confidence:.2f}")
            
            return signals
            
        except Exception as e:
            logger.error(f"Error in iceberg order detection: {e}")
            return []
    
    def analyze_volume_profile(self, market_data: pd.DataFrame) -> Dict[str, Any]:
        """Analyze volume profile to identify institutional interest areas.
        
        Args:
            market_data: DataFrame with market data including price and volume
            
        Returns:
            Dictionary with volume profile analysis
        """
        try:
            if len(market_data) < 50:
                logger.warning("Insufficient data for volume profile analysis")
                return {'status': 'insufficient_data'}
            
            # Calculate volume profile
            price_min = market_data['price'].min()
            price_max = market_data['price'].max()
            
            # Create price bins
            bins = np.linspace(price_min, price_max, self.volume_profile_bins + 1)
            labels = [(bins[i] + bins[i+1])/2 for i in range(len(bins)-1)]
            
            # Assign each price to a bin and sum volumes
            market_data['price_bin'] = pd.cut(market_data['price'], bins=bins, labels=labels)
            volume_profile = market_data.groupby('price_bin')['volume'].sum()
            
            # Identify high volume nodes (HVN) and low volume nodes (LVN)
            volume_threshold_high = volume_profile.quantile(0.8)
            volume_threshold_low = volume_profile.quantile(0.2)
            
            hvn = volume_profile[volume_profile >= volume_threshold_high]
            lvn = volume_profile[volume_profile <= volume_threshold_low]
            
            # Identify point of control (POC) - price with highest volume
            poc = volume_profile.idxmax()
            
            # Calculate value area (70% of volume)
            sorted_profile = volume_profile.sort_values(ascending=False)
            cumulative_volume = sorted_profile.cumsum() / sorted_profile.sum()
            value_area = sorted_profile[cumulative_volume <= 0.7].index.tolist()
            value_area_high = max(value_area)
            value_area_low = min(value_area)
            
            return {
                'poc': poc,
                'value_area_high': value_area_high,
                'value_area_low': value_area_low,
                'high_volume_nodes': hvn.to_dict(),
                'low_volume_nodes': lvn.to_dict(),
                'volume_profile': volume_profile.to_dict(),
                'status': 'success'
            }
            
        except Exception as e:
            logger.error(f"Error in volume profile analysis: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def detect_stop_hunts(self, market_data: pd.DataFrame) -> List[OrderFlowSignal]:
        """Detect stop hunting patterns in market data.
        
        Stop hunting is when large players push price to trigger stop losses,
        then reverse the price movement after stops are triggered.
        
        Args:
            market_data: DataFrame with OHLCV data
            
        Returns:
            List of OrderFlowSignal for detected stop hunts
        """
        signals = []
        
        try:
            if len(market_data) < 20:
                logger.warning("Insufficient data for stop hunt detection")
                return signals
            
            # Calculate price movements
            market_data['body_size'] = abs(market_data['close'] - market_data['open'])
            market_data['upper_wick'] = market_data['high'] - market_data[['open', 'close']].max(axis=1)
            market_data['lower_wick'] = market_data[['open', 'close']].min(axis=1) - market_data['low']
            
            # Calculate average volatility
            market_data['atr'] = (
                market_data['high'].rolling(14).max() - market_data['low'].rolling(14).min()
            ) / 14
            
            # Look for potential stop hunt patterns
            for i in range(5, len(market_data) - 1):
                # Skip if ATR is not available
                if pd.isna(market_data['atr'].iloc[i]):
                    continue
                
                # Bullish stop hunt (price drops sharply then reverses up)
                if (
                    # Sharp drop with long lower wick
                    market_data['lower_wick'].iloc[i] > market_data['body_size'].iloc[i] * 2 and
                    market_data['lower_wick'].iloc[i] > market_data['atr'].iloc[i] * 1.5 and
                    # Price was falling before
                    market_data['close'].iloc[i-1] < market_data['close'].iloc[i-3] and
                    # Price reverses up after
                    market_data['close'].iloc[i+1] > market_data['close'].iloc[i]
                ):
                    confidence = min(1.0, (
                        market_data['lower_wick'].iloc[i] / (market_data['atr'].iloc[i] * 2) * 
                        market_data['volume'].iloc[i] / market_data['volume'].iloc[i-5:i].mean()
                    ) * 0.8)
                    
                    signal = OrderFlowSignal(
                        order_type=OrderType.STOP_HUNT,
                        timestamp=market_data.index[i],
                        price_level=market_data['low'].iloc[i],
                        volume=market_data['volume'].iloc[i],
                        confidence=confidence,
                        direction='buy',
                        timeframe=self.config.get('timeframe', '5m'),
                        metadata={
                            'wick_size': market_data['lower_wick'].iloc[i],
                            'atr': market_data['atr'].iloc[i],
                            'volume_ratio': market_data['volume'].iloc[i] / market_data['volume'].iloc[i-5:i].mean()
                        }
                    )
                    
                    signals.append(signal)
                    logger.debug(f"Detected bullish stop hunt at {market_data.index[i]}, price {market_data['low'].iloc[i]}")
                
                # Bearish stop hunt (price spikes up sharply then reverses down)
                elif (
                    # Sharp spike with long upper wick
                    market_data['upper_wick'].iloc[i] > market_data['body_size'].iloc[i] * 2 and
                    market_data['upper_wick'].iloc[i] > market_data['atr'].iloc[i] * 1.5 and
                    # Price was rising before
                    market_data['close'].iloc[i-1] > market_data['close'].iloc[i-3] and
                    # Price reverses down after
                    market_data['close'].iloc[i+1] < market_data['close'].iloc[i]
                ):
                    confidence = min(1.0, (
                        market_data['upper_wick'].iloc[i] / (market_data['atr'].iloc[i] * 2) * 
                        market_data['volume'].iloc[i] / market_data['volume'].iloc[i-5:i].mean()
                    ) * 0.8)
                    
                    signal = OrderFlowSignal(
                        order_type=OrderType.STOP_HUNT,
                        timestamp=market_data.index[i],
                        price_level=market_data['high'].iloc[i],
                        volume=market_data['volume'].iloc[i],
                        confidence=confidence,
                        direction='sell',
                        timeframe=self.config.get('timeframe', '5m'),
                        metadata={
                            'wick_size': market_data['upper_wick'].iloc[i],
                            'atr': market_data['atr'].iloc[i],
                            'volume_ratio': market_data['volume'].iloc[i] / market_data['volume'].iloc[i-5:i].mean()
                        }
                    )
                    
                    signals.append(signal)
                    logger.debug(f"Detected bearish stop hunt at {market_data.index[i]}, price {market_data['high'].iloc[i]}")
            
            return signals
            
        except Exception as e:
            logger.error(f"Error in stop hunt detection: {e}")
            return []
    
    def detect_liquidity_pools(self, market_data: pd.DataFrame) -> Dict[str, Any]:
        """Detect liquidity pools in market data.
        
        Liquidity pools are price levels with significant pending orders,
        often at key technical levels like round numbers or support/resistance.
        
        Args:
            market_data: DataFrame with OHLCV data
            
        Returns:
            Dictionary with detected liquidity pools
        """
        try:
            if len(market_data) < 50:
                logger.warning("Insufficient data for liquidity pool detection")
                return {'status': 'insufficient_data'}
            
            # Identify swing highs and lows
            market_data['swing_high'] = (
                (market_data['high'] > market_data['high'].shift(1)) & 
                (market_data['high'] > market_data['high'].shift(2)) &
                (market_data['high'] > market_data['high'].shift(-1)) & 
                (market_data['high'] > market_data['high'].shift(-2))
            )
            
            market_data['swing_low'] = (
                (market_data['low'] < market_data['low'].shift(1)) & 
                (market_data['low'] < market_data['low'].shift(2)) &
                (market_data['low'] < market_data['low'].shift(-1)) & 
                (market_data['low'] < market_data['low'].shift(-2))
            )
            
            # Extract swing points
            swing_highs = market_data[market_data['swing_high']]['high'].tolist()
            swing_lows = market_data[market_data['swing_low']]['low'].tolist()
            
            # Find clusters of swing points (liquidity pools)
            def find_clusters(points, threshold=0.001):
                if not points:
                    return []
                
                # Sort points
                sorted_points = sorted(points)
                clusters = []
                current_cluster = [sorted_points[0]]
                
                for i in range(1, len(sorted_points)):
                    # If point is close to previous, add to current cluster
                    if sorted_points[i] - sorted_points[i-1] < threshold * sorted_points[i]:
                        current_cluster.append(sorted_points[i])
                    else:
                        # Start new cluster
                        if len(current_cluster) >= 2:  # Only keep clusters with multiple points
                            clusters.append(current_cluster)
                        current_cluster = [sorted_points[i]]
                
                # Add last cluster if it has multiple points
                if len(current_cluster) >= 2:
                    clusters.append(current_cluster)
                
                return clusters
            
            # Find clusters
            high_clusters = find_clusters(swing_highs)
            low_clusters = find_clusters(swing_lows)
            
            # Calculate average price for each cluster
            high_liquidity_pools = [sum(cluster) / len(cluster) for cluster in high_clusters]
            low_liquidity_pools = [sum(cluster) / len(cluster) for cluster in low_clusters]
            
            # Calculate strength based on cluster size and recency
            def calculate_strength(clusters, points):
                strengths = []
                for cluster in clusters:
                    # Strength based on number of points in cluster
                    size_factor = min(1.0, len(cluster) / 5)
                    
                    # Find most recent occurrence of cluster point
                    cluster_indices = [i for i, p in enumerate(points) if p in cluster]
                    if not cluster_indices:
                        strengths.append(size_factor * 0.5)
                        continue
                        
                    most_recent = max(cluster_indices)
                    recency_factor = 1.0 - (len(points) - most_recent) / len(points)
                    recency_factor = max(0.3, recency_factor)
                    
                    strengths.append(size_factor * recency_factor)
                
                return strengths
            
            high_strengths = calculate_strength(high_clusters, swing_highs)
            low_strengths = calculate_strength(low_clusters, swing_lows)
            
            return {
                'resistance_pools': [{'price': p, 'strength': s} for p, s in zip(high_liquidity_pools, high_strengths)],
                'support_pools': [{'price': p, 'strength': s} for p, s in zip(low_liquidity_pools, low_strengths)],
                'status': 'success'
            }
            
        except Exception as e:
            logger.error(f"Error in liquidity pool detection: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def create_footprint_chart(self, market_data: pd.DataFrame) -> Dict[str, Any]:
        """Create footprint chart data from market data.
        
        Footprint charts show buying and selling pressure within each candle,
        helping to identify institutional activity.
        
        Args:
            market_data: DataFrame with detailed tick data including price, volume, and direction
            
        Returns:
            Dictionary with footprint chart data
        """
        try:
            if len(market_data) < 100:
                logger.warning("Insufficient data for footprint chart creation")
                return {'status': 'insufficient_data'}
            
            # Ensure we have required columns
            required_cols = ['price', 'volume', 'direction']
            if not all(col in market_data.columns for col in required_cols):
                logger.error("Missing required columns for footprint chart")
                return {'status': 'missing_columns', 'required': required_cols}
            
            # Group data by price level
            price_levels = sorted(market_data['price'].unique())
            
            # Calculate delta (buy volume - sell volume) for each price level
            footprint_data = []
            
            for price in price_levels:
                price_data = market_data[market_data['price'] == price]
                buy_volume = price_data[price_data['direction'] == 'buy']['volume'].sum()
                sell_volume = price_data[price_data['direction'] == 'sell']['volume'].sum()
                total_volume = buy_volume + sell_volume
                delta = buy_volume - sell_volume
                delta_percent = (delta / total_volume) * 100 if total_volume > 0 else 0
                
                footprint_data.append({
                    'price': price,
                    'buy_volume': buy_volume,
                    'sell_volume': sell_volume,
                    'total_volume': total_volume,
                    'delta': delta,
                    'delta_percent': delta_percent
                })
            
            # Identify imbalance areas (high delta percent)
            imbalance_threshold = 70  # 70% imbalance
            buy_imbalances = [d for d in footprint_data if d['delta_percent'] > imbalance_threshold]
            sell_imbalances = [d for d in footprint_data if d['delta_percent'] < -imbalance_threshold]
            
            return {
                'footprint_data': footprint_data,
                'buy_imbalances': buy_imbalances,
                'sell_imbalances': sell_imbalances,
                'status': 'success'
            }
            
        except Exception as e:
            logger.error(f"Error in footprint chart creation: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def detect_spoofing(self, order_book_data: List[Dict]) -> List[OrderFlowSignal]:
        """Detect spoofing patterns in order book data.
        
        Spoofing is when traders place large orders they don't intend to execute,
        to manipulate the market, then quickly cancel them.
        
        Args:
            order_book_data: List of order book snapshots with timestamps
            
        Returns:
            List of OrderFlowSignal for detected spoofing
        """
        signals = []
        
        try:
            if len(order_book_data) < 10:
                logger.warning("Insufficient data for spoofing detection")
                return signals
            
            # Track large orders that appear and disappear quickly
            for i in range(1, len(order_book_data)):
                prev_snapshot = order_book_data[i-1]
                curr_snapshot = order_book_data[i]
                
                # Check for large bid orders that disappeared
                for price, volume in prev_snapshot.get('bids', {}).items():
                    # Skip if price doesn't exist in current snapshot
                    if price not in curr_snapshot.get('bids', {}):
                        continue
                        
                    # Check if large order disappeared or significantly reduced
                    prev_vol = volume
                    curr_vol = curr_snapshot['bids'][price]
                    
                    if (prev_vol > self.config.get('min_spoof_volume', 50) and
                        (curr_vol < prev_vol * 0.3) and  # Volume reduced by 70%+
                        (curr_snapshot['timestamp'] - prev_snapshot['timestamp']).total_seconds() < 60):  # Within 1 minute
                        
                        confidence = min(1.0, prev_vol / self.config.get('min_spoof_volume', 50) * 0.8)
                        
                        signal = OrderFlowSignal(
                            order_type=OrderType.SPOOFING,
                            timestamp=curr_snapshot['timestamp'],
                            price_level=float(price),
                            volume=prev_vol,
                            confidence=confidence,
                            direction='sell',  # Spoofing on bid side typically aims to push price down
                            timeframe='orderbook',
                            metadata={
                                'volume_change': curr_vol - prev_vol,
                                'volume_change_percent': (curr_vol - prev_vol) / prev_vol * 100,
                                'duration_seconds': (curr_snapshot['timestamp'] - prev_snapshot['timestamp']).total_seconds()
                            }
                        )
                        
                        signals.append(signal)
                        logger.debug(f"Detected potential bid spoofing at price {price}, volume {prev_vol}")
                
                # Check for large ask orders that disappeared
                for price, volume in prev_snapshot.get('asks', {}).items():
                    # Skip if price doesn't exist in current snapshot
                    if price not in curr_snapshot.get('asks', {}):
                        continue
                        
                    # Check if large order disappeared or significantly reduced
                    prev_vol = volume
                    curr_vol = curr_snapshot['asks'][price]
                    
                    if (prev_vol > self.config.get('min_spoof_volume', 50) and
                        (curr_vol < prev_vol * 0.3) and  # Volume reduced by 70%+
                        (curr_snapshot['timestamp'] - prev_snapshot['timestamp']).total_seconds() < 60):  # Within 1 minute
                        
                        confidence = min(1.0, prev_vol / self.config.get('min_spoof_volume', 50) * 0.8)
                        
                        signal = OrderFlowSignal(
                            order_type=OrderType.SPOOFING,
                            timestamp=curr_snapshot['timestamp'],
                            price_level=float(price),
                            volume=prev_vol,
                            confidence=confidence,
                            direction='buy',  # Spoofing on ask side typically aims to push price up
                            timeframe='orderbook',
                            metadata={
                                'volume_change': curr_vol - prev_vol,
                                'volume_change_percent': (curr_vol - prev_vol) / prev_vol * 100,
                                'duration_seconds': (curr_snapshot['timestamp'] - prev_snapshot['timestamp']).total_seconds()
                            }
                        )
                        
                        signals.append(signal)
                        logger.debug(f"Detected potential ask spoofing at price {price}, volume {prev_vol}")
            
            return signals
            
        except Exception as e:
            logger.error(f"Error in spoofing detection: {e}")
            return []
