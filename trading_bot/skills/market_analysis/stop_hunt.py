"""
Skill #14: Stop Hunt Predictor
==============================

Predicts liquidity grab zones where stop losses are likely
clustered and identifies potential stop hunt patterns.
"""

import numpy as np
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
from enum import Enum
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class StopHuntType(Enum):
    """Type of stop hunt."""
    LONG_SQUEEZE = "long_squeeze"  # Hunt stops below support
    SHORT_SQUEEZE = "short_squeeze"  # Hunt stops above resistance
    DOUBLE_HUNT = "double_hunt"  # Hunt both sides
    FAKE_BREAKOUT = "fake_breakout"  # False breakout to trigger stops


class LiquidityZone(Enum):
    """Type of liquidity zone."""
    STOP_LOSS_CLUSTER = "stop_loss_cluster"
    BREAKOUT_LEVEL = "breakout_level"
    ROUND_NUMBER = "round_number"
    SWING_POINT = "swing_point"
    GAP_FILL = "gap_fill"


@dataclass
class StopCluster:
    """Identified stop loss cluster."""
    price_level: float
    estimated_stops: float
    zone_type: LiquidityZone
    side: str  # 'long' or 'short'
    distance_from_current: float
    probability_of_hunt: float


@dataclass
class StopHuntEvent:
    """Detected or predicted stop hunt."""
    timestamp: datetime
    hunt_type: StopHuntType
    target_level: float
    triggered: bool
    reversal_probability: float
    expected_move_after: float


@dataclass
class StopHuntAnalysisResult:
    """Complete stop hunt analysis."""
    stop_clusters: List[StopCluster]
    recent_hunts: List[StopHuntEvent]
    nearest_long_stops: float
    nearest_short_stops: float
    hunt_in_progress: bool
    hunt_direction: Optional[str]
    safe_stop_levels: Dict[str, float]
    trading_signal: str
    confidence: float


class StopHuntPredictor:
    """
    Advanced Stop Hunt Prediction System.
    
    Identifies likely stop loss clusters and predicts stop hunts.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        try:
            self.config = config or {}
            self.lookback = self.config.get('lookback', 50)
            self.round_number_significance = self.config.get('round_number_significance', 0.001)
            self.hunt_history: List[StopHuntEvent] = []
        
            logger.info("StopHuntPredictor initialized")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def analyze(
        self,
        highs: np.ndarray,
        lows: np.ndarray,
        closes: np.ndarray,
        volumes: np.ndarray,
        timestamps: List[datetime]
    ) -> StopHuntAnalysisResult:
        """
        Analyze for stop hunt patterns.
        
        Args:
            highs: Array of high prices
            lows: Array of low prices
            closes: Array of close prices
            volumes: Array of volumes
            timestamps: List of timestamps
            
        Returns:
            StopHuntAnalysisResult with analysis
        """
        try:
            if len(closes) < 20:
                return self._create_empty_result()
        
            current_price = closes[-1]
        
            # Find stop loss clusters
            stop_clusters = self._find_stop_clusters(
                highs, lows, closes, current_price
            )
        
            # Detect recent stop hunts
            recent_hunts = self._detect_recent_hunts(
                highs, lows, closes, volumes, timestamps
            )
        
            # Find nearest stops
            nearest_long = self._find_nearest_stops(stop_clusters, 'long', current_price)
            nearest_short = self._find_nearest_stops(stop_clusters, 'short', current_price)
        
            # Check if hunt in progress
            hunt_in_progress, hunt_direction = self._check_hunt_in_progress(
                highs, lows, closes, stop_clusters
            )
        
            # Calculate safe stop levels
            safe_stops = self._calculate_safe_stops(
                stop_clusters, current_price, highs, lows
            )
        
            # Generate signal
            signal = self._generate_signal(
                stop_clusters, hunt_in_progress, hunt_direction, nearest_long, nearest_short
            )
        
            # Calculate confidence
            confidence = self._calculate_confidence(stop_clusters, recent_hunts)
        
            return StopHuntAnalysisResult(
                stop_clusters=stop_clusters,
                recent_hunts=recent_hunts,
                nearest_long_stops=nearest_long,
                nearest_short_stops=nearest_short,
                hunt_in_progress=hunt_in_progress,
                hunt_direction=hunt_direction,
                safe_stop_levels=safe_stops,
                trading_signal=signal,
                confidence=confidence
            )
        except Exception as e:
            logger.error(f"Error in analyze: {e}")
            raise
    
    def _find_stop_clusters(
        self,
        highs: np.ndarray,
        lows: np.ndarray,
        closes: np.ndarray,
        current_price: float
    ) -> List[StopCluster]:
        """Find likely stop loss cluster levels."""
        try:
            clusters = []
        
            # Find swing lows (long stop clusters below)
            swing_lows = self._find_swing_points(lows, is_high=False)
            for idx in swing_lows:
                level = lows[idx]
                distance = (current_price - level) / current_price
            
                if 0 < distance < 0.05:  # Within 5% below
                    clusters.append(StopCluster(
                        price_level=level,
                        estimated_stops=self._estimate_stop_volume(level, closes),
                        zone_type=LiquidityZone.SWING_POINT,
                        side='long',
                        distance_from_current=distance,
                        probability_of_hunt=self._calculate_hunt_probability(level, closes, 'long')
                    ))
        
            # Find swing highs (short stop clusters above)
            swing_highs = self._find_swing_points(highs, is_high=True)
            for idx in swing_highs:
                level = highs[idx]
                distance = (level - current_price) / current_price
            
                if 0 < distance < 0.05:  # Within 5% above
                    clusters.append(StopCluster(
                        price_level=level,
                        estimated_stops=self._estimate_stop_volume(level, closes),
                        zone_type=LiquidityZone.SWING_POINT,
                        side='short',
                        distance_from_current=distance,
                        probability_of_hunt=self._calculate_hunt_probability(level, closes, 'short')
                    ))
        
            # Find round numbers
            round_levels = self._find_round_numbers(current_price)
            for level in round_levels:
                distance = abs(level - current_price) / current_price
            
                if distance < 0.03:  # Within 3%
                    side = 'long' if level < current_price else 'short'
                    clusters.append(StopCluster(
                        price_level=level,
                        estimated_stops=self._estimate_stop_volume(level, closes) * 1.5,
                        zone_type=LiquidityZone.ROUND_NUMBER,
                        side=side,
                        distance_from_current=distance,
                        probability_of_hunt=0.6  # Round numbers are common targets
                    ))
        
            # Sort by probability
            clusters.sort(key=lambda x: x.probability_of_hunt, reverse=True)
        
            return clusters[:10]  # Top 10 clusters
        except Exception as e:
            logger.error(f"Error in _find_stop_clusters: {e}")
            raise
    
    def _find_swing_points(
        self,
        data: np.ndarray,
        is_high: bool,
        lookback: int = 5
    ) -> List[int]:
        """Find swing high or low indices."""
        try:
            swings = []
        
            for i in range(lookback, len(data) - lookback):
                if is_high:
                    is_swing = all(data[i] >= data[i-j] for j in range(1, lookback+1))
                    is_swing = is_swing and all(data[i] >= data[i+j] for j in range(1, lookback+1))
                else:
                    is_swing = all(data[i] <= data[i-j] for j in range(1, lookback+1))
                    is_swing = is_swing and all(data[i] <= data[i+j] for j in range(1, lookback+1))
            
                if is_swing:
                    swings.append(i)
        
            return swings
        except Exception as e:
            logger.error(f"Error in _find_swing_points: {e}")
            raise
    
    def _find_round_numbers(self, current_price: float) -> List[float]:
        """Find significant round numbers near current price."""
        try:
            rounds = []
        
            # Determine significance based on price
            if current_price < 1:
                increments = [0.01, 0.05, 0.1]
            elif current_price < 10:
                increments = [0.1, 0.5, 1.0]
            elif current_price < 100:
                increments = [1, 5, 10]
            elif current_price < 1000:
                increments = [10, 50, 100]
            else:
                increments = [100, 500, 1000]
        
            for inc in increments:
                # Find nearest round numbers
                lower = np.floor(current_price / inc) * inc
                upper = np.ceil(current_price / inc) * inc
            
                if lower not in rounds:
                    rounds.append(lower)
                if upper not in rounds:
                    rounds.append(upper)
        
            return rounds
        except Exception as e:
            logger.error(f"Error in _find_round_numbers: {e}")
            raise
    
    def _estimate_stop_volume(self, level: float, closes: np.ndarray) -> float:
        """Estimate volume of stops at a level."""
        # Count how many times price approached this level
        try:
            approaches = 0
            for i in range(1, len(closes)):
                if abs(closes[i] - level) / level < 0.002:
                    approaches += 1
        
            # More approaches = more stops accumulated
            base_volume = 1000
            return base_volume * (1 + approaches * 0.5)
        except Exception as e:
            logger.error(f"Error in _estimate_stop_volume: {e}")
            raise
    
    def _calculate_hunt_probability(
        self,
        level: float,
        closes: np.ndarray,
        side: str
    ) -> float:
        """Calculate probability of stop hunt at level."""
        try:
            probability = 0.3  # Base probability
        
            # Recent price action near level increases probability
            recent = closes[-20:]
            touches = sum(1 for c in recent if abs(c - level) / level < 0.005)
            probability += touches * 0.05
        
            # Multiple swing points at similar level increases probability
            # (more stops accumulated)
        
            # Time since last visit increases probability
            # (stops have had time to accumulate)
        
            return min(0.9, probability)
        except Exception as e:
            logger.error(f"Error in _calculate_hunt_probability: {e}")
            raise
    
    def _detect_recent_hunts(
        self,
        highs: np.ndarray,
        lows: np.ndarray,
        closes: np.ndarray,
        volumes: np.ndarray,
        timestamps: List[datetime]
    ) -> List[StopHuntEvent]:
        """Detect recent stop hunt events."""
        try:
            hunts = []
        
            for i in range(10, len(closes)):
                # Look for spike and reversal pattern
                window_highs = highs[i-10:i+1]
                window_lows = lows[i-10:i+1]
                window_closes = closes[i-10:i+1]
            
                # Long squeeze: spike down then reversal up
                min_idx = np.argmin(window_lows)
                if min_idx > 0 and min_idx < len(window_closes) - 2:
                    spike_low = window_lows[min_idx]
                    close_after = window_closes[-1]
                
                    # Did price spike down then recover?
                    if close_after > spike_low * 1.01:  # >1% recovery
                        hunts.append(StopHuntEvent(
                            timestamp=timestamps[i - 10 + min_idx],
                            hunt_type=StopHuntType.LONG_SQUEEZE,
                            target_level=spike_low,
                            triggered=True,
                            reversal_probability=0.7,
                            expected_move_after=(close_after - spike_low) / spike_low
                        ))
            
                # Short squeeze: spike up then reversal down
                max_idx = np.argmax(window_highs)
                if max_idx > 0 and max_idx < len(window_closes) - 2:
                    spike_high = window_highs[max_idx]
                    close_after = window_closes[-1]
                
                    if close_after < spike_high * 0.99:  # >1% reversal
                        hunts.append(StopHuntEvent(
                            timestamp=timestamps[i - 10 + max_idx],
                            hunt_type=StopHuntType.SHORT_SQUEEZE,
                            target_level=spike_high,
                            triggered=True,
                            reversal_probability=0.7,
                            expected_move_after=(spike_high - close_after) / spike_high
                        ))
        
            return hunts[-5:]  # Return last 5 hunts
        except Exception as e:
            logger.error(f"Error in _detect_recent_hunts: {e}")
            raise
    
    def _find_nearest_stops(
        self,
        clusters: List[StopCluster],
        side: str,
        current_price: float
    ) -> float:
        """Find nearest stop cluster for a side."""
        try:
            side_clusters = [c for c in clusters if c.side == side]
        
            if not side_clusters:
                if side == 'long':
                    return current_price * 0.98  # Default 2% below
                else:
                    return current_price * 1.02  # Default 2% above
        
            # Return closest
            return min(side_clusters, key=lambda x: x.distance_from_current).price_level
        except Exception as e:
            logger.error(f"Error in _find_nearest_stops: {e}")
            raise
    
    def _check_hunt_in_progress(
        self,
        highs: np.ndarray,
        lows: np.ndarray,
        closes: np.ndarray,
        clusters: List[StopCluster]
    ) -> Tuple[bool, Optional[str]]:
        """Check if a stop hunt is currently in progress."""
        try:
            if len(closes) < 5:
                return False, None
        
            recent_high = np.max(highs[-5:])
            recent_low = np.min(lows[-5:])
            current = closes[-1]
        
            # Check if price spiked to a cluster level
            for cluster in clusters:
                level = cluster.price_level
            
                if cluster.side == 'long':
                    # Did price spike down to long stop cluster?
                    if recent_low <= level * 1.002 and current > level * 1.005:
                        return True, 'long_squeeze'
                else:
                    # Did price spike up to short stop cluster?
                    if recent_high >= level * 0.998 and current < level * 0.995:
                        return True, 'short_squeeze'
        
            return False, None
        except Exception as e:
            logger.error(f"Error in _check_hunt_in_progress: {e}")
            raise
    
    def _calculate_safe_stops(
        self,
        clusters: List[StopCluster],
        current_price: float,
        highs: np.ndarray,
        lows: np.ndarray
    ) -> Dict[str, float]:
        """Calculate safe stop loss levels avoiding clusters."""
        try:
            safe_stops = {}
        
            # For longs: place stop below the cluster zone
            long_clusters = [c for c in clusters if c.side == 'long']
            if long_clusters:
                lowest_cluster = min(c.price_level for c in long_clusters)
                safe_stops['long'] = lowest_cluster * 0.995  # 0.5% below cluster
            else:
                safe_stops['long'] = current_price * 0.97  # Default 3% below
        
            # For shorts: place stop above the cluster zone
            short_clusters = [c for c in clusters if c.side == 'short']
            if short_clusters:
                highest_cluster = max(c.price_level for c in short_clusters)
                safe_stops['short'] = highest_cluster * 1.005  # 0.5% above cluster
            else:
                safe_stops['short'] = current_price * 1.03  # Default 3% above
        
            return safe_stops
        except Exception as e:
            logger.error(f"Error in _calculate_safe_stops: {e}")
            raise
    
    def _generate_signal(
        self,
        clusters: List[StopCluster],
        hunt_in_progress: bool,
        hunt_direction: Optional[str],
        nearest_long: float,
        nearest_short: float
    ) -> str:
        """Generate trading signal."""
        try:
            signals = []
        
            if hunt_in_progress:
                signals.append(f"HUNT IN PROGRESS: {hunt_direction} - wait for reversal")
        
            # High probability clusters
            high_prob = [c for c in clusters if c.probability_of_hunt > 0.6]
            if high_prob:
                for c in high_prob[:2]:
                    signals.append(
                        f"HIGH RISK {c.side.upper()} STOPS at {c.price_level:.4f} "
                        f"({c.probability_of_hunt:.0%} hunt probability)"
                    )
        
            signals.append(f"NEAREST LONG STOPS: {nearest_long:.4f}")
            signals.append(f"NEAREST SHORT STOPS: {nearest_short:.4f}")
        
            return " | ".join(signals)
        except Exception as e:
            logger.error(f"Error in _generate_signal: {e}")
            raise
    
    def _calculate_confidence(
        self,
        clusters: List[StopCluster],
        recent_hunts: List[StopHuntEvent]
    ) -> float:
        """Calculate confidence in the analysis."""
        try:
            confidence = 0.5
        
            # More clusters identified = more confidence
            if len(clusters) >= 5:
                confidence += 0.15
            elif len(clusters) >= 3:
                confidence += 0.1
        
            # Recent hunts validate the analysis
            if recent_hunts:
                confidence += 0.15
        
            # High probability clusters add confidence
            high_prob = [c for c in clusters if c.probability_of_hunt > 0.6]
            confidence += len(high_prob) * 0.05
        
            return min(1.0, confidence)
        except Exception as e:
            logger.error(f"Error in _calculate_confidence: {e}")
            raise
    
    def _create_empty_result(self) -> StopHuntAnalysisResult:
        """Create empty result for insufficient data."""
        return StopHuntAnalysisResult(
            stop_clusters=[],
            recent_hunts=[],
            nearest_long_stops=0,
            nearest_short_stops=0,
            hunt_in_progress=False,
            hunt_direction=None,
            safe_stop_levels={},
            trading_signal="Insufficient data",
            confidence=0
        )
