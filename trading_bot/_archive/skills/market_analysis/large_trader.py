"""
Skill #11: Large Trader Activity Detector
=========================================

Identifies institutional footprints and large trader activity
through volume analysis and trade size distribution.
"""

import numpy as np
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
from enum import Enum
from datetime import datetime
from collections import deque
import logging

logger = logging.getLogger(__name__)


class TraderType(Enum):
    """Type of trader activity."""
    RETAIL = "retail"
    INSTITUTIONAL = "institutional"
    ALGORITHMIC = "algorithmic"
    MIXED = "mixed"


class ActivityPattern(Enum):
    """Pattern of large trader activity."""
    ACCUMULATION = "accumulation"
    DISTRIBUTION = "distribution"
    ICEBERG = "iceberg"
    SWEEP = "sweep"
    STEALTH = "stealth"
    AGGRESSIVE = "aggressive"
    PASSIVE = "passive"


@dataclass
class LargeOrder:
    """Detected large order."""
    timestamp: datetime
    price: float
    volume: float
    direction: str  # 'buy' or 'sell'
    size_percentile: float
    pattern: ActivityPattern
    is_hidden: bool


@dataclass
class TraderActivityResult:
    """Complete large trader analysis."""
    dominant_trader: TraderType
    activity_pattern: ActivityPattern
    large_orders: List[LargeOrder]
    institutional_volume_pct: float
    retail_volume_pct: float
    algo_volume_pct: float
    accumulation_score: float
    distribution_score: float
    smart_money_direction: Optional[str]
    block_trade_levels: List[float]
    trading_signal: str
    confidence: float


class LargeTraderDetector:
    """
    Advanced Large Trader Detection System.
    
    Identifies institutional and algorithmic trading activity.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.large_trade_percentile = self.config.get('large_trade_percentile', 90)
        self.history_size = self.config.get('history_size', 500)
        self.trade_history: deque = deque(maxlen=self.history_size)
        self.volume_history: deque = deque(maxlen=self.history_size)
        
        logger.info("LargeTraderDetector initialized")
    
    def analyze(
        self,
        prices: np.ndarray,
        volumes: np.ndarray,
        timestamps: List[datetime],
        trade_counts: Optional[np.ndarray] = None
    ) -> TraderActivityResult:
        """
        Analyze for large trader activity.
        
        Args:
            prices: Array of prices
            volumes: Array of volumes
            timestamps: List of timestamps
            trade_counts: Optional array of trade counts per bar
            
        Returns:
            TraderActivityResult with analysis
        """
        if len(prices) < 10:
            return self._create_empty_result()
        
        # Estimate trade sizes if not provided
        if trade_counts is None:
            trade_counts = self._estimate_trade_counts(volumes)
        
        # Calculate average trade sizes
        avg_sizes = volumes / (trade_counts + 1e-10)
        
        # Detect large orders
        large_orders = self._detect_large_orders(
            prices, volumes, avg_sizes, timestamps
        )
        
        # Classify trader types
        institutional_pct, retail_pct, algo_pct = self._classify_volume(
            volumes, avg_sizes, trade_counts
        )
        
        # Determine dominant trader
        dominant = self._determine_dominant_trader(
            institutional_pct, retail_pct, algo_pct
        )
        
        # Identify activity pattern
        pattern = self._identify_pattern(large_orders, prices)
        
        # Calculate accumulation/distribution scores
        acc_score, dist_score = self._calculate_acc_dist_scores(
            large_orders, prices
        )
        
        # Determine smart money direction
        smart_money = self._determine_smart_money_direction(
            large_orders, acc_score, dist_score
        )
        
        # Find block trade levels
        block_levels = self._find_block_trade_levels(large_orders)
        
        # Generate signal
        signal = self._generate_signal(
            dominant, pattern, smart_money, acc_score, dist_score
        )
        
        # Calculate confidence
        confidence = self._calculate_confidence(
            large_orders, institutional_pct, pattern
        )
        
        return TraderActivityResult(
            dominant_trader=dominant,
            activity_pattern=pattern,
            large_orders=large_orders,
            institutional_volume_pct=institutional_pct,
            retail_volume_pct=retail_pct,
            algo_volume_pct=algo_pct,
            accumulation_score=acc_score,
            distribution_score=dist_score,
            smart_money_direction=smart_money,
            block_trade_levels=block_levels,
            trading_signal=signal,
            confidence=confidence
        )
    
    def _estimate_trade_counts(self, volumes: np.ndarray) -> np.ndarray:
        """Estimate number of trades from volume."""
        # Assume average trade size based on volume distribution
        avg_volume = np.mean(volumes)
        estimated_avg_trade = avg_volume / 100  # Rough estimate
        
        trade_counts = volumes / (estimated_avg_trade + 1e-10)
        return np.maximum(1, trade_counts)
    
    def _detect_large_orders(
        self,
        prices: np.ndarray,
        volumes: np.ndarray,
        avg_sizes: np.ndarray,
        timestamps: List[datetime]
    ) -> List[LargeOrder]:
        """Detect large orders in the data."""
        large_orders = []
        
        # Calculate threshold for large orders
        threshold = np.percentile(avg_sizes, self.large_trade_percentile)
        
        for i in range(len(prices)):
            if avg_sizes[i] > threshold:
                # Determine direction
                if i > 0:
                    direction = 'buy' if prices[i] > prices[i-1] else 'sell'
                else:
                    direction = 'buy'
                
                # Calculate percentile
                percentile = (np.sum(avg_sizes <= avg_sizes[i]) / len(avg_sizes)) * 100
                
                # Identify pattern
                pattern = self._classify_order_pattern(
                    i, prices, volumes, avg_sizes
                )
                
                # Check if hidden (iceberg)
                is_hidden = self._is_hidden_order(i, volumes, avg_sizes)
                
                large_orders.append(LargeOrder(
                    timestamp=timestamps[i],
                    price=prices[i],
                    volume=volumes[i],
                    direction=direction,
                    size_percentile=percentile,
                    pattern=pattern,
                    is_hidden=is_hidden
                ))
        
        return large_orders
    
    def _classify_order_pattern(
        self,
        idx: int,
        prices: np.ndarray,
        volumes: np.ndarray,
        avg_sizes: np.ndarray
    ) -> ActivityPattern:
        """Classify the pattern of a large order."""
        # Look at surrounding bars
        start = max(0, idx - 5)
        end = min(len(prices), idx + 6)
        
        window_prices = prices[start:end]
        window_volumes = volumes[start:end]
        window_sizes = avg_sizes[start:end]
        
        # Check for sweep (aggressive buying/selling through levels)
        price_range = np.max(window_prices) - np.min(window_prices)
        avg_price = np.mean(window_prices)
        
        if price_range / avg_price > 0.01:  # >1% move
            return ActivityPattern.SWEEP
        
        # Check for iceberg (consistent size over time)
        size_std = np.std(window_sizes)
        size_mean = np.mean(window_sizes)
        
        if size_std / (size_mean + 1e-10) < 0.2:
            return ActivityPattern.ICEBERG
        
        # Check for stealth (large orders with minimal impact)
        volume_impact = volumes[idx] / np.sum(window_volumes)
        price_impact = abs(prices[idx] - prices[start]) / prices[start] if start < idx else 0
        
        if volume_impact > 0.3 and price_impact < 0.002:
            return ActivityPattern.STEALTH
        
        # Check for aggressive
        if volume_impact > 0.4:
            return ActivityPattern.AGGRESSIVE
        
        return ActivityPattern.PASSIVE
    
    def _is_hidden_order(
        self,
        idx: int,
        volumes: np.ndarray,
        avg_sizes: np.ndarray
    ) -> bool:
        """Check if order appears to be hidden (iceberg)."""
        # Look for consistent volume over multiple bars
        start = max(0, idx - 3)
        end = min(len(volumes), idx + 4)
        
        window_volumes = volumes[start:end]
        
        # Hidden orders show consistent volume chunks
        if len(window_volumes) >= 3:
            cv = np.std(window_volumes) / (np.mean(window_volumes) + 1e-10)
            return cv < 0.3
        
        return False
    
    def _classify_volume(
        self,
        volumes: np.ndarray,
        avg_sizes: np.ndarray,
        trade_counts: np.ndarray
    ) -> Tuple[float, float, float]:
        """Classify volume by trader type."""
        # Size thresholds
        small_threshold = np.percentile(avg_sizes, 25)
        large_threshold = np.percentile(avg_sizes, 75)
        
        # Classify each bar
        retail_volume = 0
        institutional_volume = 0
        algo_volume = 0
        
        for i in range(len(volumes)):
            if avg_sizes[i] < small_threshold:
                retail_volume += volumes[i]
            elif avg_sizes[i] > large_threshold:
                institutional_volume += volumes[i]
            else:
                # Check for algo patterns (consistent timing/size)
                algo_volume += volumes[i] * 0.5
                institutional_volume += volumes[i] * 0.3
                retail_volume += volumes[i] * 0.2
        
        total = retail_volume + institutional_volume + algo_volume
        
        if total == 0:
            return 0.33, 0.33, 0.34
        
        return (
            institutional_volume / total,
            retail_volume / total,
            algo_volume / total
        )
    
    def _determine_dominant_trader(
        self,
        institutional: float,
        retail: float,
        algo: float
    ) -> TraderType:
        """Determine dominant trader type."""
        max_pct = max(institutional, retail, algo)
        
        if max_pct < 0.4:
            return TraderType.MIXED
        
        if institutional == max_pct:
            return TraderType.INSTITUTIONAL
        elif retail == max_pct:
            return TraderType.RETAIL
        else:
            return TraderType.ALGORITHMIC
    
    def _identify_pattern(
        self,
        large_orders: List[LargeOrder],
        prices: np.ndarray
    ) -> ActivityPattern:
        """Identify overall activity pattern."""
        if not large_orders:
            return ActivityPattern.PASSIVE
        
        # Count patterns
        pattern_counts = {}
        for order in large_orders:
            pattern_counts[order.pattern] = pattern_counts.get(order.pattern, 0) + 1
        
        # Return most common
        if pattern_counts:
            return max(pattern_counts, key=pattern_counts.get)
        
        return ActivityPattern.PASSIVE
    
    def _calculate_acc_dist_scores(
        self,
        large_orders: List[LargeOrder],
        prices: np.ndarray
    ) -> Tuple[float, float]:
        """Calculate accumulation and distribution scores."""
        if not large_orders:
            return 0.5, 0.5
        
        buy_volume = sum(o.volume for o in large_orders if o.direction == 'buy')
        sell_volume = sum(o.volume for o in large_orders if o.direction == 'sell')
        
        total = buy_volume + sell_volume
        
        if total == 0:
            return 0.5, 0.5
        
        acc_score = buy_volume / total
        dist_score = sell_volume / total
        
        return acc_score, dist_score
    
    def _determine_smart_money_direction(
        self,
        large_orders: List[LargeOrder],
        acc_score: float,
        dist_score: float
    ) -> Optional[str]:
        """Determine smart money direction."""
        if abs(acc_score - dist_score) < 0.2:
            return None
        
        if acc_score > dist_score:
            return "buying"
        else:
            return "selling"
    
    def _find_block_trade_levels(
        self,
        large_orders: List[LargeOrder]
    ) -> List[float]:
        """Find price levels with significant block trades."""
        if not large_orders:
            return []
        
        # Group by price level
        levels = {}
        for order in large_orders:
            # Round to nearest significant level
            level = round(order.price, 4)
            levels[level] = levels.get(level, 0) + order.volume
        
        # Sort by volume
        sorted_levels = sorted(levels.items(), key=lambda x: x[1], reverse=True)
        
        # Return top 5 levels
        return [level for level, _ in sorted_levels[:5]]
    
    def _generate_signal(
        self,
        dominant: TraderType,
        pattern: ActivityPattern,
        smart_money: Optional[str],
        acc_score: float,
        dist_score: float
    ) -> str:
        """Generate trading signal."""
        signals = []
        
        # Dominant trader signal
        if dominant == TraderType.INSTITUTIONAL:
            signals.append("INSTITUTIONAL: Large players active")
        elif dominant == TraderType.ALGORITHMIC:
            signals.append("ALGORITHMIC: Algo trading dominant")
        elif dominant == TraderType.RETAIL:
            signals.append("RETAIL: Small traders dominant")
        
        # Pattern signal
        if pattern == ActivityPattern.ACCUMULATION:
            signals.append("ACCUMULATION: Smart money buying")
        elif pattern == ActivityPattern.DISTRIBUTION:
            signals.append("DISTRIBUTION: Smart money selling")
        elif pattern == ActivityPattern.SWEEP:
            signals.append("SWEEP: Aggressive liquidity taking")
        elif pattern == ActivityPattern.ICEBERG:
            signals.append("ICEBERG: Hidden orders detected")
        
        # Smart money signal
        if smart_money == "buying":
            signals.append(f"SMART MONEY BUYING: Acc={acc_score:.0%}")
        elif smart_money == "selling":
            signals.append(f"SMART MONEY SELLING: Dist={dist_score:.0%}")
        
        return " | ".join(signals) if signals else "NEUTRAL: No clear institutional signal"
    
    def _calculate_confidence(
        self,
        large_orders: List[LargeOrder],
        institutional_pct: float,
        pattern: ActivityPattern
    ) -> float:
        """Calculate confidence in the analysis."""
        confidence = 0.5
        
        # More large orders = more confidence
        if len(large_orders) >= 10:
            confidence += 0.15
        elif len(large_orders) >= 5:
            confidence += 0.1
        
        # High institutional percentage = more confidence
        if institutional_pct > 0.5:
            confidence += 0.15
        elif institutional_pct > 0.3:
            confidence += 0.1
        
        # Clear pattern = more confidence
        if pattern in [ActivityPattern.ACCUMULATION, ActivityPattern.DISTRIBUTION]:
            confidence += 0.1
        
        return min(1.0, confidence)
    
    def _create_empty_result(self) -> TraderActivityResult:
        """Create empty result for insufficient data."""
        return TraderActivityResult(
            dominant_trader=TraderType.MIXED,
            activity_pattern=ActivityPattern.PASSIVE,
            large_orders=[],
            institutional_volume_pct=0.33,
            retail_volume_pct=0.33,
            algo_volume_pct=0.34,
            accumulation_score=0.5,
            distribution_score=0.5,
            smart_money_direction=None,
            block_trade_levels=[],
            trading_signal="Insufficient data",
            confidence=0
        )
