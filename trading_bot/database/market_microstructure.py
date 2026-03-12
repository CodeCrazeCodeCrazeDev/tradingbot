"""
Market Microstructure Analysis Module
Analyzes order flow and market microstructure for alpha generation
"""

import numpy as np
import pandas as pd
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime
import asyncio
from dataclasses import dataclass
import logging
from collections import deque
import numpy
import pandas

# Evolution: Added retry decorator
def retry(max_attempts=3, delay=1.0):
    """Retry decorator for resilient operations"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    if attempt < max_attempts - 1:
                        await asyncio.sleep(delay * (attempt + 1))
            raise last_error
        return wrapper
    return decorator



logger = logging.getLogger(__name__)

@dataclass
class OrderFlowMetrics:
    """Order flow analysis metrics"""
    buy_volume: float = 0.0
    sell_volume: float = 0.0
    buy_trades: int = 0
    sell_trades: int = 0
    avg_trade_size: float = 0.0
    large_trades: List[Dict] = None
    imbalance_ratio: float = 0.0
    pressure_score: float = 0.0

    def __post_init__(self):
        self.large_trades = []

class MarketMicrostructure:
    """
    Advanced market microstructure analysis
    Features:
    - Order flow analysis
    - Volume profile analysis
    - Trade size clustering
    - Liquidity analysis
    - Price impact modeling
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        
        # Thresholds
        self.large_trade_threshold = config.get('large_trade_threshold', 100000)
        self.vwap_window = config.get('vwap_window', 20)
        
        # Analysis buffers
        self.trade_buffer: Dict[str, deque] = {}
        self.volume_profile: Dict[str, Dict[float, float]] = {}
        self.order_flow_metrics: Dict[str, OrderFlowMetrics] = {}
        
        # Price impact model parameters
        self.impact_decay = config.get('impact_decay', 0.1)
        self.impact_coefficient = config.get('impact_coefficient', 0.1)
        
        logger.info("Market microstructure analyzer initialized")
    
    async def process_trade(self, symbol: str, trade: Dict[str, Any]):
        """Process a new trade and update metrics"""
        # Initialize buffers if needed
        if symbol not in self.trade_buffer:
            self.trade_buffer[symbol] = deque(maxlen=1000)
            self.order_flow_metrics[symbol] = OrderFlowMetrics()
        
        # Add to buffer
        self.trade_buffer[symbol].append(trade)
        
        # Update order flow metrics
        await self._update_order_flow_metrics(symbol, trade)
        
        # Update volume profile
        self._update_volume_profile(symbol, trade)
        
        # Analyze trade clusters
        clusters = self._analyze_trade_clusters(symbol)
        
        # Calculate price impact
        impact = self._calculate_price_impact(symbol, trade)
        
        return {
            'order_flow': self.order_flow_metrics[symbol],
            'clusters': clusters,
            'price_impact': impact
        }
    
    async def _update_order_flow_metrics(self, symbol: str, trade: Dict[str, Any]):
        """Update order flow metrics with new trade"""
        metrics = self.order_flow_metrics[symbol]
        
        # Update volumes
        if trade.get('side') == 'buy':
            metrics.buy_volume += trade.get('volume', 0)
            metrics.buy_trades += 1
        else:
            metrics.sell_volume += trade.get('volume', 0)
            metrics.sell_trades += 1
        
        # Update average trade size
        total_trades = metrics.buy_trades + metrics.sell_trades
        total_volume = metrics.buy_volume + metrics.sell_volume
        metrics.avg_trade_size = total_volume / total_trades if total_trades > 0 else 0
        
        # Track large trades
        if trade.get('volume', 0) > self.large_trade_threshold:
            metrics.large_trades.append({
                'timestamp': trade.get('timestamp', datetime.now()),
                'price': trade.get('price', 0),
                'volume': trade.get('volume', 0),
                'side': trade.get('side', 'unknown')
            })
        
        # Calculate imbalance ratio
        total_volume = metrics.buy_volume + metrics.sell_volume
        if total_volume > 0:
            metrics.imbalance_ratio = (metrics.buy_volume - metrics.sell_volume) / total_volume
        
        # Calculate buying/selling pressure
        metrics.pressure_score = self._calculate_pressure_score(symbol)
    
    def _update_volume_profile(self, symbol: str, trade: Dict[str, Any]):
        """Update volume profile"""
        if symbol not in self.volume_profile:
            self.volume_profile[symbol] = {}
        
        price = trade.get('price', 0)
        volume = trade.get('volume', 0)
        
        # Round price to appropriate precision
        price_level = round(price, 2)
        
        # Update volume at price level
        if price_level in self.volume_profile[symbol]:
            self.volume_profile[symbol][price_level] += volume
        else:
            self.volume_profile[symbol][price_level] = volume
    
    def _analyze_trade_clusters(self, symbol: str) -> List[Dict[str, Any]]:
        """Analyze trade clusters to identify potential institutional activity"""
        if symbol not in self.trade_buffer:
            return []
        
        trades = list(self.trade_buffer[symbol])
        if not trades:
            return []
        
        clusters = []
        current_cluster = {
            'start_time': trades[0].get('timestamp'),
            'volume': 0,
            'trades': 0,
            'avg_price': 0,
            'side': None
        }
        
        volume_sum = 0
        price_volume_sum = 0
        
        for trade in trades:
            # Check if trade belongs to current cluster
            if self._belongs_to_cluster(trade, current_cluster):
                current_cluster['volume'] += trade.get('volume', 0)
                current_cluster['trades'] += 1
                volume_sum += trade.get('volume', 0)
                price_volume_sum += trade.get('price', 0) * trade.get('volume', 0)
            else:
                # Finalize current cluster
                if current_cluster['volume'] > 0:
                    current_cluster['avg_price'] = price_volume_sum / volume_sum
                    clusters.append(current_cluster)
                
                # Start new cluster
                current_cluster = {
                    'start_time': trade.get('timestamp'),
                    'volume': trade.get('volume', 0),
                    'trades': 1,
                    'avg_price': trade.get('price', 0),
                    'side': trade.get('side')
                }
                volume_sum = trade.get('volume', 0)
                price_volume_sum = trade.get('price', 0) * trade.get('volume', 0)
        
        return clusters
    
    def _belongs_to_cluster(self, trade: Dict[str, Any], 
                          cluster: Dict[str, Any]) -> bool:
        """Check if trade belongs to current cluster"""
        if not cluster['start_time']:
            return True
        
        # Check time difference
        time_diff = (trade.get('timestamp', datetime.now()) - 
                    cluster['start_time']).total_seconds()
        
        # Check price difference
        price_diff = abs(trade.get('price', 0) - cluster['avg_price'])
        
        return (time_diff < 60 and  # 1 minute window
                price_diff < 0.001)  # 0.1 pip difference
    
    def _calculate_pressure_score(self, symbol: str) -> float:
        """Calculate buying/selling pressure score"""
        metrics = self.order_flow_metrics[symbol]
        
        # Base pressure on volume imbalance
        base_pressure = metrics.imbalance_ratio
        
        # Adjust for large trades
        large_trade_pressure = 0
        recent_large_trades = [
            t for t in metrics.large_trades
            if (datetime.now() - t['timestamp']).total_seconds() < 300  # 5 min window
        ]
        
        for trade in recent_large_trades:
            multiplier = 1 if trade['side'] == 'buy' else -1
            large_trade_pressure += (trade['volume'] / self.large_trade_threshold) * multiplier
        
        # Combine pressures
        total_pressure = (base_pressure * 0.7 + 
                         np.tanh(large_trade_pressure) * 0.3)  # Scale to [-1, 1]
        
        return total_pressure
    
    def _calculate_price_impact(self, symbol: str, trade: Dict[str, Any]) -> float:
        """Calculate price impact of trade"""
        metrics = self.order_flow_metrics[symbol]
        
        # Base impact
        volume_ratio = trade.get('volume', 0) / metrics.avg_trade_size
        base_impact = self.impact_coefficient * np.sign(metrics.imbalance_ratio) * volume_ratio
        
        # Decay factor based on recent trades
        recent_trades = len([
            t for t in self.trade_buffer[symbol]
            if (datetime.now() - t.get('timestamp', datetime.now())).total_seconds() < 60
        ])
        decay = np.exp(-self.impact_decay * recent_trades)
        
        return base_impact * decay
    
    def get_liquidity_analysis(self, symbol: str) -> Dict[str, Any]:
        """Get liquidity analysis for symbol"""
        if symbol not in self.volume_profile:
            return {}
        
        profile = self.volume_profile[symbol]
        metrics = self.order_flow_metrics[symbol]
        
        # Find liquidity zones
        sorted_prices = sorted(profile.keys())
        liquidity_zones = []
        
        for i in range(len(sorted_prices) - 1):
            current_vol = profile[sorted_prices[i]]
            next_vol = profile[sorted_prices[i + 1]]
            
            if current_vol > metrics.avg_trade_size * 2:  # Significant liquidity
                liquidity_zones.append({
                    'price': sorted_prices[i],
                    'volume': current_vol,
                    'type': 'support' if i < len(sorted_prices) / 2 else 'resistance'
                })
        
        return {
            'liquidity_zones': liquidity_zones,
            'avg_spread': np.mean([
                sorted_prices[i+1] - sorted_prices[i]
                for i in range(len(sorted_prices)-1)
            ]) if len(sorted_prices) > 1 else 0,
            'volume_concentration': self._calculate_volume_concentration(profile)
        }
    
    def _calculate_volume_concentration(self, 
                                     profile: Dict[float, float]) -> float:
        """Calculate volume concentration metric"""
        if not profile:
            return 0
        
        total_volume = sum(profile.values())
        if total_volume == 0:
            return 0
        
        # Calculate volume-weighted price standard deviation
        prices = np.array(list(profile.keys()))
        volumes = np.array(list(profile.values()))
        vwap = np.average(prices, weights=volumes)
        
        variance = np.average((prices - vwap) ** 2, weights=volumes)
        return np.sqrt(variance)
    
    def get_metrics(self, symbol: str) -> Dict[str, Any]:
        """Get all microstructure metrics for symbol"""
        if symbol not in self.order_flow_metrics:
            return {}
        
        metrics = self.order_flow_metrics[symbol]
        liquidity = self.get_liquidity_analysis(symbol)
        
        return {
            'order_flow': {
                'buy_volume': metrics.buy_volume,
                'sell_volume': metrics.sell_volume,
                'imbalance_ratio': metrics.imbalance_ratio,
                'pressure_score': metrics.pressure_score,
                'avg_trade_size': metrics.avg_trade_size,
                'large_trades_count': len(metrics.large_trades)
            },
            'liquidity_analysis': liquidity,
            'trading_patterns': {
                'cluster_count': len(self._analyze_trade_clusters(symbol)),
                'avg_cluster_size': np.mean([
                    c['volume'] for c in self._analyze_trade_clusters(symbol)
                ]) if self._analyze_trade_clusters(symbol) else 0
            }
        }
