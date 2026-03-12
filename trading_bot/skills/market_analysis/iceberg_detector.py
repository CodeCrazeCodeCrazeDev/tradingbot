"""
Skill #12: Iceberg Order Detector
=================================

Detects hidden liquidity and iceberg orders through
volume pattern analysis and order flow signatures.
"""

import numpy as np
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
from enum import Enum
from datetime import datetime
from collections import deque
import logging

logger = logging.getLogger(__name__)


class IcebergType(Enum):
    """Type of iceberg order."""
    STANDARD = "standard"  # Fixed clip size
    RANDOM = "random"  # Random clip sizes
    ADAPTIVE = "adaptive"  # Size adapts to market
    RESERVE = "reserve"  # Large reserve behind visible


class IcebergSide(Enum):
    """Side of iceberg order."""
    BID = "bid"
    ASK = "ask"
    UNKNOWN = "unknown"


@dataclass
class IcebergOrder:
    """Detected iceberg order."""
    timestamp: datetime
    price_level: float
    visible_size: float
    estimated_total: float
    clip_size: float
    clips_detected: int
    iceberg_type: IcebergType
    side: IcebergSide
    confidence: float
    is_active: bool


@dataclass
class IcebergAnalysisResult:
    """Complete iceberg detection result."""
    detected_icebergs: List[IcebergOrder]
    active_bid_icebergs: List[IcebergOrder]
    active_ask_icebergs: List[IcebergOrder]
    total_hidden_bid_volume: float
    total_hidden_ask_volume: float
    iceberg_imbalance: float  # Positive = more bid icebergs
    key_iceberg_levels: List[float]
    trading_signal: str
    confidence: float


class IcebergOrderDetector:
    """
    Advanced Iceberg Order Detection System.
    
    Identifies hidden liquidity through pattern recognition.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        try:
            self.config = config or {}
            self.min_clips = self.config.get('min_clips', 3)
            self.clip_variance_threshold = self.config.get('clip_variance_threshold', 0.3)
            self.history_size = self.config.get('history_size', 100)
            self.detection_history: deque = deque(maxlen=self.history_size)
        
            logger.info("IcebergOrderDetector initialized")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def analyze(
        self,
        prices: np.ndarray,
        volumes: np.ndarray,
        timestamps: List[datetime],
        bid_volumes: Optional[np.ndarray] = None,
        ask_volumes: Optional[np.ndarray] = None
    ) -> IcebergAnalysisResult:
        """
        Analyze for iceberg orders.
        
        Args:
            prices: Array of prices
            volumes: Array of volumes
            timestamps: List of timestamps
            bid_volumes: Optional bid volumes
            ask_volumes: Optional ask volumes
            
        Returns:
            IcebergAnalysisResult with detected icebergs
        """
        try:
            if len(prices) < 10:
                return self._create_empty_result()
        
            # Estimate bid/ask if not provided
            if bid_volumes is None or ask_volumes is None:
                bid_volumes, ask_volumes = self._estimate_bid_ask(prices, volumes)
        
            # Detect icebergs at each price level
            icebergs = self._detect_icebergs(
                prices, volumes, bid_volumes, ask_volumes, timestamps
            )
        
            # Separate active bid and ask icebergs
            active_bids = [i for i in icebergs if i.is_active and i.side == IcebergSide.BID]
            active_asks = [i for i in icebergs if i.is_active and i.side == IcebergSide.ASK]
        
            # Calculate hidden volumes
            hidden_bid = sum(i.estimated_total - i.visible_size for i in active_bids)
            hidden_ask = sum(i.estimated_total - i.visible_size for i in active_asks)
        
            # Calculate imbalance
            total_hidden = hidden_bid + hidden_ask
            imbalance = (hidden_bid - hidden_ask) / (total_hidden + 1e-10)
        
            # Find key levels
            key_levels = self._find_key_iceberg_levels(icebergs)
        
            # Generate signal
            signal = self._generate_signal(
                active_bids, active_asks, imbalance, key_levels
            )
        
            # Calculate confidence
            confidence = self._calculate_confidence(icebergs, imbalance)
        
            return IcebergAnalysisResult(
                detected_icebergs=icebergs,
                active_bid_icebergs=active_bids,
                active_ask_icebergs=active_asks,
                total_hidden_bid_volume=hidden_bid,
                total_hidden_ask_volume=hidden_ask,
                iceberg_imbalance=imbalance,
                key_iceberg_levels=key_levels,
                trading_signal=signal,
                confidence=confidence
            )
        except Exception as e:
            logger.error(f"Error in analyze: {e}")
            raise
    
    def _estimate_bid_ask(
        self,
        prices: np.ndarray,
        volumes: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Estimate bid/ask volume from price movement."""
        try:
            bid_volumes = np.zeros(len(volumes))
            ask_volumes = np.zeros(len(volumes))
        
            for i in range(1, len(volumes)):
                if prices[i] > prices[i-1]:
                    # Price up = more buying
                    bid_volumes[i] = volumes[i] * 0.7
                    ask_volumes[i] = volumes[i] * 0.3
                elif prices[i] < prices[i-1]:
                    # Price down = more selling
                    bid_volumes[i] = volumes[i] * 0.3
                    ask_volumes[i] = volumes[i] * 0.7
                else:
                    bid_volumes[i] = volumes[i] * 0.5
                    ask_volumes[i] = volumes[i] * 0.5
        
            return bid_volumes, ask_volumes
        except Exception as e:
            logger.error(f"Error in _estimate_bid_ask: {e}")
            raise
    
    def _detect_icebergs(
        self,
        prices: np.ndarray,
        volumes: np.ndarray,
        bid_volumes: np.ndarray,
        ask_volumes: np.ndarray,
        timestamps: List[datetime]
    ) -> List[IcebergOrder]:
        """Detect iceberg orders in the data."""
        try:
            icebergs = []
        
            # Group by price level
            price_levels = self._group_by_price_level(prices, volumes, bid_volumes, ask_volumes, timestamps)
        
            for level, data in price_levels.items():
                # Check for iceberg pattern at this level
                iceberg = self._check_iceberg_pattern(level, data)
                if iceberg:
                    icebergs.append(iceberg)
        
            # Also check for time-based icebergs (same size over time)
            time_icebergs = self._detect_time_based_icebergs(
                prices, volumes, bid_volumes, ask_volumes, timestamps
            )
            icebergs.extend(time_icebergs)
        
            return icebergs
        except Exception as e:
            logger.error(f"Error in _detect_icebergs: {e}")
            raise
    
    def _group_by_price_level(
        self,
        prices: np.ndarray,
        volumes: np.ndarray,
        bid_volumes: np.ndarray,
        ask_volumes: np.ndarray,
        timestamps: List[datetime]
    ) -> Dict[float, List[Dict]]:
        """Group data by price level."""
        try:
            levels = {}
        
            # Round prices to create levels
            tick_size = self._get_tick_size(np.min(prices))
        
            for i in range(len(prices)):
                level = round(prices[i] / tick_size) * tick_size
            
                if level not in levels:
                    levels[level] = []
            
                levels[level].append({
                    'timestamp': timestamps[i],
                    'volume': volumes[i],
                    'bid_volume': bid_volumes[i],
                    'ask_volume': ask_volumes[i],
                    'index': i
                })
        
            return levels
        except Exception as e:
            logger.error(f"Error in _group_by_price_level: {e}")
            raise
    
    def _get_tick_size(self, price: float) -> float:
        """Get appropriate tick size."""
        try:
            if price < 1:
                return 0.0001
            elif price < 10:
                return 0.001
            elif price < 100:
                return 0.01
            else:
                return 0.1
        except Exception as e:
            logger.error(f"Error in _get_tick_size: {e}")
            raise
    
    def _check_iceberg_pattern(
        self,
        level: float,
        data: List[Dict]
    ) -> Optional[IcebergOrder]:
        """Check for iceberg pattern at a price level."""
        try:
            if len(data) < self.min_clips:
                return None
        
            volumes = [d['volume'] for d in data]
            bid_volumes = [d['bid_volume'] for d in data]
            ask_volumes = [d['ask_volume'] for d in data]
        
            # Check for consistent clip sizes (iceberg signature)
            mean_vol = np.mean(volumes)
            std_vol = np.std(volumes)
            cv = std_vol / (mean_vol + 1e-10)
        
            # Low coefficient of variation suggests iceberg
            if cv < self.clip_variance_threshold:
                # Determine side
                total_bid = sum(bid_volumes)
                total_ask = sum(ask_volumes)
            
                if total_bid > total_ask * 1.5:
                    side = IcebergSide.BID
                elif total_ask > total_bid * 1.5:
                    side = IcebergSide.ASK
                else:
                    side = IcebergSide.UNKNOWN
            
                # Estimate total size
                clips_detected = len(data)
                clip_size = mean_vol
                visible_size = sum(volumes)
            
                # Estimate remaining (assume we've seen ~30-50% of total)
                estimated_total = visible_size / 0.4
            
                # Determine iceberg type
                if cv < 0.1:
                    iceberg_type = IcebergType.STANDARD
                elif cv < 0.2:
                    iceberg_type = IcebergType.RANDOM
                else:
                    iceberg_type = IcebergType.ADAPTIVE
            
                # Calculate confidence
                confidence = min(1.0, 0.5 + (1 - cv) * 0.3 + clips_detected * 0.02)
            
                return IcebergOrder(
                    timestamp=data[-1]['timestamp'],
                    price_level=level,
                    visible_size=visible_size,
                    estimated_total=estimated_total,
                    clip_size=clip_size,
                    clips_detected=clips_detected,
                    iceberg_type=iceberg_type,
                    side=side,
                    confidence=confidence,
                    is_active=True
                )
        
            return None
        except Exception as e:
            logger.error(f"Error in _check_iceberg_pattern: {e}")
            raise
    
    def _detect_time_based_icebergs(
        self,
        prices: np.ndarray,
        volumes: np.ndarray,
        bid_volumes: np.ndarray,
        ask_volumes: np.ndarray,
        timestamps: List[datetime]
    ) -> List[IcebergOrder]:
        """Detect icebergs based on time patterns."""
        try:
            icebergs = []
        
            # Look for consistent volume patterns over time
            window_size = 5
        
            for i in range(window_size, len(volumes)):
                window = volumes[i-window_size:i]
            
                mean_vol = np.mean(window)
                std_vol = np.std(window)
                cv = std_vol / (mean_vol + 1e-10)
            
                # Check for consistent pattern
                if cv < 0.2 and mean_vol > np.mean(volumes) * 1.5:
                    # High consistent volume = potential iceberg
                
                    # Determine side from price movement
                    price_change = prices[i] - prices[i-window_size]
                    if price_change > 0:
                        side = IcebergSide.BID
                    elif price_change < 0:
                        side = IcebergSide.ASK
                    else:
                        side = IcebergSide.UNKNOWN
                
                    visible = sum(window)
                    estimated = visible / 0.35
                
                    icebergs.append(IcebergOrder(
                        timestamp=timestamps[i],
                        price_level=prices[i],
                        visible_size=visible,
                        estimated_total=estimated,
                        clip_size=mean_vol,
                        clips_detected=window_size,
                        iceberg_type=IcebergType.STANDARD,
                        side=side,
                        confidence=0.6,
                        is_active=True
                    ))
        
            return icebergs
        except Exception as e:
            logger.error(f"Error in _detect_time_based_icebergs: {e}")
            raise
    
    def _find_key_iceberg_levels(
        self,
        icebergs: List[IcebergOrder]
    ) -> List[float]:
        """Find key price levels with significant icebergs."""
        try:
            if not icebergs:
                return []
        
            # Sort by estimated total size
            sorted_icebergs = sorted(
                icebergs,
                key=lambda x: x.estimated_total,
                reverse=True
            )
        
            # Return top 5 levels
            return [i.price_level for i in sorted_icebergs[:5]]
        except Exception as e:
            logger.error(f"Error in _find_key_iceberg_levels: {e}")
            raise
    
    def _generate_signal(
        self,
        bid_icebergs: List[IcebergOrder],
        ask_icebergs: List[IcebergOrder],
        imbalance: float,
        key_levels: List[float]
    ) -> str:
        """Generate trading signal."""
        try:
            signals = []
        
            # Iceberg count signal
            if bid_icebergs:
                total_bid = sum(i.estimated_total for i in bid_icebergs)
                signals.append(f"BID ICEBERGS: {len(bid_icebergs)} detected (~{total_bid:.0f} hidden)")
        
            if ask_icebergs:
                total_ask = sum(i.estimated_total for i in ask_icebergs)
                signals.append(f"ASK ICEBERGS: {len(ask_icebergs)} detected (~{total_ask:.0f} hidden)")
        
            # Imbalance signal
            if imbalance > 0.3:
                signals.append("BULLISH: More hidden bid liquidity")
            elif imbalance < -0.3:
                signals.append("BEARISH: More hidden ask liquidity")
        
            # Key levels
            if key_levels:
                signals.append(f"KEY LEVELS: {', '.join(f'{l:.4f}' for l in key_levels[:3])}")
        
            return " | ".join(signals) if signals else "No significant icebergs detected"
        except Exception as e:
            logger.error(f"Error in _generate_signal: {e}")
            raise
    
    def _calculate_confidence(
        self,
        icebergs: List[IcebergOrder],
        imbalance: float
    ) -> float:
        """Calculate confidence in the analysis."""
        try:
            if not icebergs:
                return 0.3
        
            # Average confidence of detected icebergs
            avg_conf = np.mean([i.confidence for i in icebergs])
        
            # Adjust for imbalance clarity
            imbalance_factor = abs(imbalance) * 0.2
        
            return min(1.0, avg_conf + imbalance_factor)
        except Exception as e:
            logger.error(f"Error in _calculate_confidence: {e}")
            raise
    
    def _create_empty_result(self) -> IcebergAnalysisResult:
        """Create empty result for insufficient data."""
        return IcebergAnalysisResult(
            detected_icebergs=[],
            active_bid_icebergs=[],
            active_ask_icebergs=[],
            total_hidden_bid_volume=0,
            total_hidden_ask_volume=0,
            iceberg_imbalance=0,
            key_iceberg_levels=[],
            trading_signal="Insufficient data",
            confidence=0
        )
