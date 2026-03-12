"""
Order Flow Analysis System
Analyzes order flow patterns and institutional footprints
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import logging
from collections import deque
from scipy.stats import norm, skew, kurtosis
import numpy
import pandas

logger = logging.getLogger(__name__)

@dataclass
class OrderFlowSignal:
    """Order flow analysis signal"""
    signal_type: str
    strength: float
    confidence: float
    timestamp: datetime
    direction: str  # 'buy' or 'sell'
    volume: float
    price_impact: float
    supporting_data: Dict
    metadata: Dict

class OrderType:
    """Order types for analysis"""
    MARKET = "market"
    LIMIT = "limit"
    AGGRESSIVE = "aggressive"
    PASSIVE = "passive"
    HIDDEN = "hidden"
    ICEBERG = "iceberg"

class OrderFlowAnalyzer:
    """
    Advanced order flow analysis system
    """
    
    def __init__(self, config: Optional[Dict] = None):
        try:
            self.config = config or {}
        
            # Analysis parameters
            self.volume_threshold = self.config.get('volume_threshold', 100000)
            self.time_window = self.config.get('time_window', 300)  # 5 minutes
            self.aggressive_threshold = self.config.get('aggressive_threshold', 0.7)
        
            # Data buffers
            self.trade_buffer = deque(maxlen=10000)
            self.volume_profile = {}
            self.order_flow_imbalance = deque(maxlen=100)
        
            # Analysis state
            self.vwap_levels = {}
            self.volume_nodes = {}
            self.institutional_levels = {}
        
            logger.info("Order Flow Analyzer initialized")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def analyze_order_flow(self, trades: List[Dict], 
                          order_book: Optional[Dict] = None) -> List[OrderFlowSignal]:
        """
        Analyze order flow patterns
        """
        try:
            signals = []
        
            # Update buffers
            self._update_buffers(trades)
        
            # Analyze different components
            signals.extend(self._analyze_volume_patterns(trades))
            signals.extend(self._analyze_trade_flow(trades))
            signals.extend(self._analyze_aggressive_orders(trades))
            signals.extend(self._detect_institutional_activity(trades))
        
            if order_book:
                signals.extend(self._analyze_order_book_pressure(order_book))
        
            return signals
        except Exception as e:
            logger.error(f"Error in analyze_order_flow: {e}")
            raise
    
    def _update_buffers(self, trades: List[Dict]):
        """Update internal data buffers"""
        try:
            for trade in trades:
                self.trade_buffer.append(trade)
            
                # Update volume profile
                price = trade.get('price', 0)
                volume = trade.get('volume', 0)
                price_level = round(price, 2)
            
                if price_level not in self.volume_profile:
                    self.volume_profile[price_level] = 0
                self.volume_profile[price_level] += volume
            
                # Update order flow imbalance
                if trade.get('side') == 'buy':
                    imbalance = volume
                else:
                    imbalance = -volume
                self.order_flow_imbalance.append(imbalance)
        except Exception as e:
            logger.error(f"Error in _update_buffers: {e}")
            raise
    
    def _analyze_volume_patterns(self, trades: List[Dict]) -> List[OrderFlowSignal]:
        """
        Analyze volume patterns and clusters
        """
        try:
            signals = []
        
            if not trades:
                return signals
        
            # Calculate volume metrics
            volumes = [t.get('volume', 0) for t in trades]
            prices = [t.get('price', 0) for t in trades]
        
            avg_volume = np.mean(volumes)
            vol_std = np.std(volumes)
        
            # Detect large trades
            large_trades = [t for t in trades if t.get('volume', 0) > avg_volume + 2*vol_std]
        
            for trade in large_trades:
                price = trade.get('price', 0)
                volume = trade.get('volume', 0)
            
                signals.append(OrderFlowSignal(
                    signal_type="large_trade",
                    strength=min((volume - avg_volume) / (vol_std + 1), 1.0),
                    confidence=0.8,
                    timestamp=trade.get('timestamp', datetime.now()),
                    direction=trade.get('side', 'unknown'),
                    volume=volume,
                    price_impact=self._calculate_price_impact(trade, trades),
                    supporting_data={
                        'avg_volume': avg_volume,
                        'volume_std': vol_std,
                        'z_score': (volume - avg_volume) / (vol_std + 1)
                    },
                    metadata={'trade_id': trade.get('trade_id')}
                ))
        
            # Analyze volume clusters
            volume_clusters = self._identify_volume_clusters(trades)
        
            for cluster in volume_clusters:
                cluster_volume = sum(t.get('volume', 0) for t in cluster)
                cluster_direction = self._determine_cluster_direction(cluster)
            
                if cluster_volume > self.volume_threshold:
                    signals.append(OrderFlowSignal(
                        signal_type="volume_cluster",
                        strength=min(cluster_volume / self.volume_threshold, 1.0),
                        confidence=0.7,
                        timestamp=cluster[-1].get('timestamp', datetime.now()),
                        direction=cluster_direction,
                        volume=cluster_volume,
                        price_impact=self._calculate_cluster_impact(cluster),
                        supporting_data={
                            'cluster_size': len(cluster),
                            'avg_price': np.mean([t.get('price', 0) for t in cluster]),
                            'price_range': max([t.get('price', 0) for t in cluster]) - 
                                         min([t.get('price', 0) for t in cluster])
                        },
                        metadata={'cluster_id': datetime.now().timestamp()}
                    ))
        
            return signals
        except Exception as e:
            logger.error(f"Error in _analyze_volume_patterns: {e}")
            raise
    
    def _analyze_trade_flow(self, trades: List[Dict]) -> List[OrderFlowSignal]:
        """
        Analyze trade flow patterns
        """
        try:
            signals = []
        
            if len(trades) < 10:
                return signals
        
            # Calculate trade flow metrics
            buy_volume = sum(t.get('volume', 0) for t in trades if t.get('side') == 'buy')
            sell_volume = sum(t.get('volume', 0) for t in trades if t.get('side') == 'sell')
            total_volume = buy_volume + sell_volume
        
            if total_volume > 0:
                flow_ratio = (buy_volume - sell_volume) / total_volume
            
                # Strong directional flow
                if abs(flow_ratio) > 0.3:
                    signals.append(OrderFlowSignal(
                        signal_type="directional_flow",
                        strength=abs(flow_ratio),
                        confidence=0.7,
                        timestamp=trades[-1].get('timestamp', datetime.now()),
                        direction='buy' if flow_ratio > 0 else 'sell',
                        volume=total_volume,
                        price_impact=self._calculate_flow_impact(trades),
                        supporting_data={
                            'flow_ratio': flow_ratio,
                            'buy_volume': buy_volume,
                            'sell_volume': sell_volume
                        },
                        metadata={'window_size': len(trades)}
                    ))
        
            # Analyze trade sequence patterns
            if len(trades) >= 20:
                sequence_patterns = self._analyze_trade_sequence(trades[-20:])
                signals.extend(sequence_patterns)
        
            return signals
        except Exception as e:
            logger.error(f"Error in _analyze_trade_flow: {e}")
            raise
    
    def _analyze_aggressive_orders(self, trades: List[Dict]) -> List[OrderFlowSignal]:
        """
        Analyze aggressive order patterns
        """
        try:
            signals = []
        
            aggressive_trades = [t for t in trades if self._is_aggressive_trade(t)]
        
            if not aggressive_trades:
                return signals
        
            # Calculate aggressiveness metrics
            agg_volume = sum(t.get('volume', 0) for t in aggressive_trades)
            total_volume = sum(t.get('volume', 0) for t in trades)
        
            if total_volume > 0:
                agg_ratio = agg_volume / total_volume
            
                if agg_ratio > self.aggressive_threshold:
                    signals.append(OrderFlowSignal(
                        signal_type="aggressive_flow",
                        strength=agg_ratio,
                        confidence=0.8,
                        timestamp=trades[-1].get('timestamp', datetime.now()),
                        direction=self._determine_aggressive_direction(aggressive_trades),
                        volume=agg_volume,
                        price_impact=self._calculate_aggressive_impact(aggressive_trades),
                        supporting_data={
                            'aggressive_ratio': agg_ratio,
                            'aggressive_count': len(aggressive_trades),
                            'total_trades': len(trades)
                        },
                        metadata={'aggressive_threshold': self.aggressive_threshold}
                    ))
        
            return signals
        except Exception as e:
            logger.error(f"Error in _analyze_aggressive_orders: {e}")
            raise
    
    def _detect_institutional_activity(self, trades: List[Dict]) -> List[OrderFlowSignal]:
        """
        Detect potential institutional trading activity
        """
        try:
            signals = []
        
            # Identify potential iceberg orders
            iceberg_patterns = self._identify_iceberg_patterns(trades)
            signals.extend(iceberg_patterns)
        
            # Analyze trade size distribution
            size_distribution = self._analyze_size_distribution(trades)
            if size_distribution:
                signals.append(size_distribution)
        
            # Detect sophisticated execution patterns
            execution_patterns = self._detect_execution_patterns(trades)
            signals.extend(execution_patterns)
        
            return signals
        except Exception as e:
            logger.error(f"Error in _detect_institutional_activity: {e}")
            raise
    
    def _analyze_order_book_pressure(self, order_book: Dict) -> List[OrderFlowSignal]:
        """
        Analyze order book pressure and imbalance
        """
        try:
            signals = []
        
            if 'bids' not in order_book or 'asks' not in order_book:
                return signals
        
            bids = order_book['bids']
            asks = order_book['asks']
        
            # Calculate order book imbalance
            bid_volume = sum(bid[1] for bid in bids[:5])  # Top 5 levels
            ask_volume = sum(ask[1] for ask in asks[:5])
            total_volume = bid_volume + ask_volume
        
            if total_volume > 0:
                imbalance = (bid_volume - ask_volume) / total_volume
            
                if abs(imbalance) > 0.3:
                    signals.append(OrderFlowSignal(
                        signal_type="book_pressure",
                        strength=abs(imbalance),
                        confidence=0.7,
                        timestamp=datetime.now(),
                        direction='buy' if imbalance > 0 else 'sell',
                        volume=total_volume,
                        price_impact=self._estimate_price_impact(imbalance, total_volume),
                        supporting_data={
                            'imbalance': imbalance,
                            'bid_volume': bid_volume,
                            'ask_volume': ask_volume,
                            'spread': asks[0][0] - bids[0][0]
                        },
                        metadata={'levels_analyzed': 5}
                    ))
        
            return signals
        except Exception as e:
            logger.error(f"Error in _analyze_order_book_pressure: {e}")
            raise
    
    def _identify_volume_clusters(self, trades: List[Dict]) -> List[List[Dict]]:
        """
        Identify clusters of related trades
        """
        try:
            clusters = []
            current_cluster = []
        
            for i, trade in enumerate(trades):
                if not current_cluster:
                    current_cluster.append(trade)
                    continue
            
                # Check if trade belongs to current cluster
                if self._is_related_trade(trade, current_cluster[-1]):
                    current_cluster.append(trade)
                else:
                    if len(current_cluster) >= 3:  # Minimum cluster size
                        clusters.append(current_cluster)
                    current_cluster = [trade]
        
            # Add last cluster if significant
            if len(current_cluster) >= 3:
                clusters.append(current_cluster)
        
            return clusters
        except Exception as e:
            logger.error(f"Error in _identify_volume_clusters: {e}")
            raise
    
    def _is_related_trade(self, trade1: Dict, trade2: Dict) -> bool:
        """
        Check if trades are related (part of same cluster)
        """
        # Time proximity
        try:
            time1 = trade1.get('timestamp', datetime.now())
            time2 = trade2.get('timestamp', datetime.now())
            time_diff = abs((time1 - time2).total_seconds())
        
            if time_diff > 30:  # 30 seconds threshold
                return False
        
            # Price proximity
            price1 = trade1.get('price', 0)
            price2 = trade2.get('price', 0)
            price_diff = abs(price1 - price2) / price1 if price1 > 0 else float('inf')
        
            if price_diff > 0.001:  # 0.1% threshold
                return False
        
            # Size similarity
            size1 = trade1.get('volume', 0)
            size2 = trade2.get('volume', 0)
            size_ratio = min(size1, size2) / max(size1, size2) if max(size1, size2) > 0 else 0
        
            return size_ratio > 0.5
        except Exception as e:
            logger.error(f"Error in _is_related_trade: {e}")
            raise
    
    def _determine_cluster_direction(self, cluster: List[Dict]) -> str:
        """
        Determine dominant direction of a trade cluster
        """
        try:
            buy_volume = sum(t.get('volume', 0) for t in cluster if t.get('side') == 'buy')
            sell_volume = sum(t.get('volume', 0) for t in cluster if t.get('side') == 'sell')
        
            return 'buy' if buy_volume > sell_volume else 'sell'
        except Exception as e:
            logger.error(f"Error in _determine_cluster_direction: {e}")
            raise
    
    def _calculate_price_impact(self, trade: Dict, context: List[Dict]) -> float:
        """
        Calculate price impact of a trade
        """
        try:
            price = trade.get('price', 0)
            volume = trade.get('volume', 0)
        
            if not context or not price or not volume:
                return 0
        
            # Calculate price change from previous trades
            prev_prices = [t.get('price', price) for t in context if t.get('timestamp', datetime.now()) < 
                          trade.get('timestamp', datetime.now())]
        
            if not prev_prices:
                return 0
        
            avg_prev_price = np.mean(prev_prices[-5:])  # Last 5 trades
            return abs(price - avg_prev_price) / avg_prev_price
        except Exception as e:
            logger.error(f"Error in _calculate_price_impact: {e}")
            raise
    
    def _calculate_cluster_impact(self, cluster: List[Dict]) -> float:
        """
        Calculate price impact of a trade cluster
        """
        try:
            if not cluster:
                return 0
        
            start_price = cluster[0].get('price', 0)
            end_price = cluster[-1].get('price', 0)
        
            if start_price == 0:
                return 0
        
            return abs(end_price - start_price) / start_price
        except Exception as e:
            logger.error(f"Error in _calculate_cluster_impact: {e}")
            raise
    
    def _calculate_flow_impact(self, trades: List[Dict]) -> float:
        """
        Calculate price impact of trade flow
        """
        try:
            if not trades:
                return 0
        
            prices = [t.get('price', 0) for t in trades]
            volumes = [t.get('volume', 0) for t in trades]
        
            if not prices or not volumes:
                return 0
        
            vwap = np.average(prices, weights=volumes)
            last_price = prices[-1]
        
            return abs(last_price - vwap) / vwap
        except Exception as e:
            logger.error(f"Error in _calculate_flow_impact: {e}")
            raise
    
    def _is_aggressive_trade(self, trade: Dict) -> bool:
        """
        Determine if a trade is aggressive
        """
        # Aggressive if crosses spread or large size
        try:
            if trade.get('aggressor', False):
                return True
        
            if trade.get('volume', 0) > self.volume_threshold:
                return True
        
            # Check if price crosses previous quotes
            if len(self.trade_buffer) > 1:
                prev_trade = self.trade_buffer[-1]
                price_jump = abs(trade.get('price', 0) - prev_trade.get('price', 0))
            
                if price_jump > prev_trade.get('price', 0) * 0.001:  # 0.1% jump
                    return True
        
            return False
        except Exception as e:
            logger.error(f"Error in _is_aggressive_trade: {e}")
            raise
    
    def _determine_aggressive_direction(self, trades: List[Dict]) -> str:
        """
        Determine direction of aggressive trades
        """
        try:
            buy_volume = sum(t.get('volume', 0) for t in trades if t.get('side') == 'buy')
            sell_volume = sum(t.get('volume', 0) for t in trades if t.get('side') == 'sell')
        
            return 'buy' if buy_volume > sell_volume else 'sell'
        except Exception as e:
            logger.error(f"Error in _determine_aggressive_direction: {e}")
            raise
    
    def _calculate_aggressive_impact(self, trades: List[Dict]) -> float:
        """
        Calculate price impact of aggressive trades
        """
        try:
            if not trades:
                return 0
        
            # Use VWAP as reference
            vwap = np.average(
                [t.get('price', 0) for t in trades],
                weights=[t.get('volume', 0) for t in trades]
            )
        
            # Calculate average deviation from VWAP
            impacts = []
            for trade in trades:
                price = trade.get('price', 0)
                if price > 0:
                    impact = abs(price - vwap) / vwap
                    impacts.append(impact)
        
            return np.mean(impacts) if impacts else 0
        except Exception as e:
            logger.error(f"Error in _calculate_aggressive_impact: {e}")
            raise
    
    def _identify_iceberg_patterns(self, trades: List[Dict]) -> List[OrderFlowSignal]:
        """
        Identify potential iceberg order patterns
        """
        try:
            signals = []
        
            # Group trades by size
            size_groups = {}
            for trade in trades:
                size = trade.get('volume', 0)
                if size not in size_groups:
                    size_groups[size] = []
                size_groups[size].append(trade)
        
            # Look for repeated sizes
            for size, group in size_groups.items():
                if len(group) >= 3 and size > self.volume_threshold * 0.2:
                    signals.append(OrderFlowSignal(
                        signal_type="iceberg_pattern",
                        strength=min(len(group) / 10, 1.0),
                        confidence=0.6,
                        timestamp=group[-1].get('timestamp', datetime.now()),
                        direction=self._determine_aggressive_direction(group),
                        volume=size * len(group),
                        price_impact=self._calculate_aggressive_impact(group),
                        supporting_data={
                            'repeat_count': len(group),
                            'individual_size': size,
                            'time_span': (group[-1].get('timestamp', datetime.now()) - 
                                        group[0].get('timestamp', datetime.now())).total_seconds()
                        },
                        metadata={'pattern_type': 'iceberg'}
                    ))
        
            return signals
        except Exception as e:
            logger.error(f"Error in _identify_iceberg_patterns: {e}")
            raise
    
    def _analyze_size_distribution(self, trades: List[Dict]) -> Optional[OrderFlowSignal]:
        """
        Analyze trade size distribution for institutional patterns
        """
        try:
            if len(trades) < 20:
                return None
        
            sizes = [t.get('volume', 0) for t in trades]
        
            # Calculate distribution metrics
            size_skew = skew(sizes)
            size_kurt = kurtosis(sizes)
        
            # Look for heavy-tailed distribution (institutional characteristic)
            if size_kurt > 3 and abs(size_skew) > 1:
                return OrderFlowSignal(
                    signal_type="institutional_distribution",
                    strength=min(abs(size_kurt - 3) / 10, 1.0),
                    confidence=0.6,
                    timestamp=trades[-1].get('timestamp', datetime.now()),
                    direction='buy' if size_skew > 0 else 'sell',
                    volume=sum(sizes),
                    price_impact=self._calculate_flow_impact(trades),
                    supporting_data={
                        'skewness': size_skew,
                        'kurtosis': size_kurt,
                        'mean_size': np.mean(sizes),
                        'median_size': np.median(sizes)
                    },
                    metadata={'distribution_type': 'heavy_tailed'}
                )
        
            return None
        except Exception as e:
            logger.error(f"Error in _analyze_size_distribution: {e}")
            raise
    
    def _detect_execution_patterns(self, trades: List[Dict]) -> List[OrderFlowSignal]:
        """
        Detect sophisticated execution patterns
        """
        try:
            signals = []
        
            if len(trades) < 30:
                return signals
        
            # Time-weighted execution pattern
            twap_pattern = self._detect_twap_pattern(trades)
            if twap_pattern:
                signals.append(twap_pattern)
        
            # Volume-weighted execution pattern
            vwap_pattern = self._detect_vwap_pattern(trades)
            if vwap_pattern:
                signals.append(vwap_pattern)
        
            # Percentage of volume pattern
            pov_pattern = self._detect_pov_pattern(trades)
            if pov_pattern:
                signals.append(pov_pattern)
        
            return signals
        except Exception as e:
            logger.error(f"Error in _detect_execution_patterns: {e}")
            raise
    
    def _detect_twap_pattern(self, trades: List[Dict]) -> Optional[OrderFlowSignal]:
        """
        Detect Time-Weighted Average Price execution pattern
        """
        try:
            timestamps = [t.get('timestamp', datetime.now()) for t in trades]
            time_diffs = np.diff([t.timestamp() for t in timestamps])
        
            # Check for regular time intervals
            if len(time_diffs) > 0:
                regularity = np.std(time_diffs) / np.mean(time_diffs)
            
                if regularity < 0.3:  # High time regularity
                    return OrderFlowSignal(
                        signal_type="twap_pattern",
                        strength=1 - regularity,
                        confidence=0.7,
                        timestamp=timestamps[-1],
                        direction=self._determine_aggressive_direction(trades),
                        volume=sum(t.get('volume', 0) for t in trades),
                        price_impact=self._calculate_flow_impact(trades),
                        supporting_data={
                            'regularity': regularity,
                            'avg_interval': np.mean(time_diffs),
                            'trade_count': len(trades)
                        },
                        metadata={'pattern_type': 'twap'}
                    )
        
            return None
        except Exception as e:
            logger.error(f"Error in _detect_twap_pattern: {e}")
            raise
    
    def _detect_vwap_pattern(self, trades: List[Dict]) -> Optional[OrderFlowSignal]:
        """
        Detect Volume-Weighted Average Price execution pattern
        """
        try:
            volumes = [t.get('volume', 0) for t in trades]
            prices = [t.get('price', 0) for t in trades]
        
            if not volumes or not prices:
                return None
        
            # Calculate volume profile correlation
            volume_profile = np.array(volumes) / sum(volumes)
            historical_profile = self._get_historical_volume_profile()
        
            if len(historical_profile) == len(volume_profile):
                correlation = np.corrcoef(volume_profile, historical_profile)[0, 1]
            
                if correlation > 0.7:  # Strong correlation with typical volume profile
                    return OrderFlowSignal(
                        signal_type="vwap_pattern",
                        strength=correlation,
                        confidence=0.7,
                        timestamp=trades[-1].get('timestamp', datetime.now()),
                        direction=self._determine_aggressive_direction(trades),
                        volume=sum(volumes),
                        price_impact=self._calculate_flow_impact(trades),
                        supporting_data={
                            'correlation': correlation,
                            'volume_profile': volume_profile.tolist(),
                            'trade_count': len(trades)
                        },
                        metadata={'pattern_type': 'vwap'}
                    )
        
            return None
        except Exception as e:
            logger.error(f"Error in _detect_vwap_pattern: {e}")
            raise
    
    def _detect_pov_pattern(self, trades: List[Dict]) -> Optional[OrderFlowSignal]:
        """
        Detect Percentage of Volume execution pattern
        """
        try:
            if len(self.trade_buffer) < 100:
                return None
        
            # Calculate recent market volume
            market_volume = sum(t.get('volume', 0) for t in self.trade_buffer)
            pattern_volume = sum(t.get('volume', 0) for t in trades)
        
            if market_volume > 0:
                volume_ratio = pattern_volume / market_volume
            
                # Check if volume ratio is consistent
                if 0.1 <= volume_ratio <= 0.3:  # Typical PoV range
                    return OrderFlowSignal(
                        signal_type="pov_pattern",
                        strength=min(volume_ratio * 5, 1.0),
                        confidence=0.7,
                        timestamp=trades[-1].get('timestamp', datetime.now()),
                        direction=self._determine_aggressive_direction(trades),
                        volume=pattern_volume,
                        price_impact=self._calculate_flow_impact(trades),
                        supporting_data={
                            'volume_ratio': volume_ratio,
                            'market_volume': market_volume,
                            'pattern_volume': pattern_volume
                        },
                        metadata={'pattern_type': 'pov'}
                    )
        
            return None
        except Exception as e:
            logger.error(f"Error in _detect_pov_pattern: {e}")
            raise
    
    def _get_historical_volume_profile(self) -> np.ndarray:
        """
        Get historical volume profile for comparison
        """
        # Simple uniform distribution as fallback
        return np.ones(10) / 10  # Would be replaced with actual historical data
    
    def _estimate_price_impact(self, imbalance: float, volume: float) -> float:
        """
        Estimate potential price impact
        """
        # Simple square root model
        return abs(imbalance) * np.sqrt(volume / self.volume_threshold)
