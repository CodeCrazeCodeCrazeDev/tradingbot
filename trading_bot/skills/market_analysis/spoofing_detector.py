"""
Skill #13: Spoofing Pattern Detector
====================================

Identifies market manipulation attempts including spoofing,
layering, and quote stuffing patterns.
"""

import numpy as np
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
from enum import Enum
from datetime import datetime
from collections import deque
import logging

logger = logging.getLogger(__name__)


class ManipulationType(Enum):
    """Type of market manipulation."""
    SPOOFING = "spoofing"  # Large orders placed and cancelled
    LAYERING = "layering"  # Multiple orders at different levels
    QUOTE_STUFFING = "quote_stuffing"  # Rapid order placement/cancellation
    MOMENTUM_IGNITION = "momentum_ignition"  # Trigger stops/momentum
    WASH_TRADING = "wash_trading"  # Trading with self
    PAINTING_TAPE = "painting_tape"  # Creating false impression


class ManipulationSeverity(Enum):
    """Severity of detected manipulation."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ManipulationEvent:
    """Detected manipulation event."""
    timestamp: datetime
    manipulation_type: ManipulationType
    severity: ManipulationSeverity
    price_level: float
    estimated_size: float
    duration_seconds: float
    confidence: float
    description: str


@dataclass
class SpoofingAnalysisResult:
    """Complete spoofing detection result."""
    manipulation_events: List[ManipulationEvent]
    active_spoofing: bool
    spoofing_side: Optional[str]  # 'bid' or 'ask'
    manipulation_score: float  # 0-1
    affected_price_levels: List[float]
    recommended_action: str
    trading_signal: str
    confidence: float


class SpoofingPatternDetector:
    """
    Advanced Spoofing and Manipulation Detection System.
    
    Identifies various forms of market manipulation.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        try:
            self.config = config or {}
            self.cancel_ratio_threshold = self.config.get('cancel_ratio_threshold', 0.8)
            self.quote_velocity_threshold = self.config.get('quote_velocity_threshold', 100)
            self.history_size = self.config.get('history_size', 200)
            self.event_history: deque = deque(maxlen=self.history_size)
        
            logger.info("SpoofingPatternDetector initialized")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def analyze(
        self,
        prices: np.ndarray,
        volumes: np.ndarray,
        timestamps: List[datetime],
        bid_sizes: Optional[np.ndarray] = None,
        ask_sizes: Optional[np.ndarray] = None,
        order_counts: Optional[np.ndarray] = None,
        cancel_counts: Optional[np.ndarray] = None
    ) -> SpoofingAnalysisResult:
        """
        Analyze for spoofing and manipulation.
        
        Args:
            prices: Array of prices
            volumes: Array of volumes
            timestamps: List of timestamps
            bid_sizes: Optional bid sizes at best bid
            ask_sizes: Optional ask sizes at best ask
            order_counts: Optional order counts per period
            cancel_counts: Optional cancellation counts
            
        Returns:
            SpoofingAnalysisResult with detected manipulation
        """
        try:
            if len(prices) < 10:
                return self._create_empty_result()
        
            events = []
        
            # Detect spoofing patterns
            spoofing_events = self._detect_spoofing(
                prices, volumes, timestamps, bid_sizes, ask_sizes
            )
            events.extend(spoofing_events)
        
            # Detect layering
            layering_events = self._detect_layering(
                prices, volumes, timestamps, bid_sizes, ask_sizes
            )
            events.extend(layering_events)
        
            # Detect quote stuffing
            if order_counts is not None:
                stuffing_events = self._detect_quote_stuffing(
                    timestamps, order_counts, cancel_counts
                )
                events.extend(stuffing_events)
        
            # Detect momentum ignition
            ignition_events = self._detect_momentum_ignition(
                prices, volumes, timestamps
            )
            events.extend(ignition_events)
        
            # Detect wash trading
            wash_events = self._detect_wash_trading(
                prices, volumes, timestamps
            )
            events.extend(wash_events)
        
            # Determine if active spoofing
            active_spoofing = any(
                e.manipulation_type == ManipulationType.SPOOFING and
                e.severity in [ManipulationSeverity.HIGH, ManipulationSeverity.CRITICAL]
                for e in events
            )
        
            # Determine spoofing side
            spoofing_side = self._determine_spoofing_side(events)
        
            # Calculate manipulation score
            manipulation_score = self._calculate_manipulation_score(events)
        
            # Get affected levels
            affected_levels = list(set(e.price_level for e in events))
        
            # Generate recommendation
            recommendation = self._generate_recommendation(
                events, active_spoofing, manipulation_score
            )
        
            # Generate signal
            signal = self._generate_signal(
                events, active_spoofing, spoofing_side, manipulation_score
            )
        
            # Calculate confidence
            confidence = self._calculate_confidence(events)
        
            # Store events
            self.event_history.extend(events)
        
            return SpoofingAnalysisResult(
                manipulation_events=events,
                active_spoofing=active_spoofing,
                spoofing_side=spoofing_side,
                manipulation_score=manipulation_score,
                affected_price_levels=affected_levels[:10],
                recommended_action=recommendation,
                trading_signal=signal,
                confidence=confidence
            )
        except Exception as e:
            logger.error(f"Error in analyze: {e}")
            raise
    
    def _detect_spoofing(
        self,
        prices: np.ndarray,
        volumes: np.ndarray,
        timestamps: List[datetime],
        bid_sizes: Optional[np.ndarray],
        ask_sizes: Optional[np.ndarray]
    ) -> List[ManipulationEvent]:
        """Detect spoofing patterns."""
        try:
            events = []
        
            if bid_sizes is None or ask_sizes is None:
                # Estimate from volume patterns
                bid_sizes, ask_sizes = self._estimate_book_sizes(prices, volumes)
        
            # Look for large size imbalances that don't result in trades
            for i in range(5, len(prices)):
                window_prices = prices[i-5:i]
                window_bids = bid_sizes[i-5:i]
                window_asks = ask_sizes[i-5:i]
            
                # Check for large bid that doesn't move price up
                max_bid = np.max(window_bids)
                avg_bid = np.mean(window_bids)
                price_change = prices[i] - prices[i-5]
            
                if max_bid > avg_bid * 3 and price_change <= 0:
                    # Large bid but price didn't go up = potential spoof
                    severity = self._classify_severity(max_bid / avg_bid)
                
                    events.append(ManipulationEvent(
                        timestamp=timestamps[i],
                        manipulation_type=ManipulationType.SPOOFING,
                        severity=severity,
                        price_level=prices[i],
                        estimated_size=max_bid,
                        duration_seconds=5.0,
                        confidence=0.6,
                        description=f"Large bid ({max_bid:.0f}) without price increase"
                    ))
            
                # Check for large ask that doesn't move price down
                max_ask = np.max(window_asks)
                avg_ask = np.mean(window_asks)
            
                if max_ask > avg_ask * 3 and price_change >= 0:
                    severity = self._classify_severity(max_ask / avg_ask)
                
                    events.append(ManipulationEvent(
                        timestamp=timestamps[i],
                        manipulation_type=ManipulationType.SPOOFING,
                        severity=severity,
                        price_level=prices[i],
                        estimated_size=max_ask,
                        duration_seconds=5.0,
                        confidence=0.6,
                        description=f"Large ask ({max_ask:.0f}) without price decrease"
                    ))
        
            return events
        except Exception as e:
            logger.error(f"Error in _detect_spoofing: {e}")
            raise
    
    def _detect_layering(
        self,
        prices: np.ndarray,
        volumes: np.ndarray,
        timestamps: List[datetime],
        bid_sizes: Optional[np.ndarray],
        ask_sizes: Optional[np.ndarray]
    ) -> List[ManipulationEvent]:
        """Detect layering patterns (multiple orders at different levels)."""
        try:
            events = []
        
            # Layering shows as consistent volume at multiple price levels
            # Look for unusual volume distribution
        
            for i in range(10, len(prices)):
                window = volumes[i-10:i]
            
                # Check for unusually consistent volume (layering signature)
                cv = np.std(window) / (np.mean(window) + 1e-10)
            
                if cv < 0.2 and np.mean(window) > np.mean(volumes) * 1.5:
                    # Consistent high volume = potential layering
                    events.append(ManipulationEvent(
                        timestamp=timestamps[i],
                        manipulation_type=ManipulationType.LAYERING,
                        severity=ManipulationSeverity.MEDIUM,
                        price_level=prices[i],
                        estimated_size=np.sum(window),
                        duration_seconds=10.0,
                        confidence=0.5,
                        description="Consistent volume pattern suggesting layering"
                    ))
        
            return events
        except Exception as e:
            logger.error(f"Error in _detect_layering: {e}")
            raise
    
    def _detect_quote_stuffing(
        self,
        timestamps: List[datetime],
        order_counts: np.ndarray,
        cancel_counts: Optional[np.ndarray]
    ) -> List[ManipulationEvent]:
        """Detect quote stuffing (rapid order/cancel)."""
        try:
            events = []
        
            if cancel_counts is None:
                return events
        
            for i in range(len(order_counts)):
                # High order rate with high cancel rate = quote stuffing
                if order_counts[i] > self.quote_velocity_threshold:
                    cancel_ratio = cancel_counts[i] / (order_counts[i] + 1e-10)
                
                    if cancel_ratio > self.cancel_ratio_threshold:
                        severity = ManipulationSeverity.HIGH if cancel_ratio > 0.9 else ManipulationSeverity.MEDIUM
                    
                        events.append(ManipulationEvent(
                            timestamp=timestamps[i],
                            manipulation_type=ManipulationType.QUOTE_STUFFING,
                            severity=severity,
                            price_level=0,  # Not price-specific
                            estimated_size=order_counts[i],
                            duration_seconds=1.0,
                            confidence=0.7,
                            description=f"High order rate ({order_counts[i]}) with {cancel_ratio:.0%} cancels"
                        ))
        
            return events
        except Exception as e:
            logger.error(f"Error in _detect_quote_stuffing: {e}")
            raise
    
    def _detect_momentum_ignition(
        self,
        prices: np.ndarray,
        volumes: np.ndarray,
        timestamps: List[datetime]
    ) -> List[ManipulationEvent]:
        """Detect momentum ignition attempts."""
        try:
            events = []
        
            for i in range(10, len(prices)):
                # Look for sharp price move followed by reversal
                window_prices = prices[i-10:i+1]
            
                # Calculate move
                max_price = np.max(window_prices)
                min_price = np.min(window_prices)
                current = prices[i]
            
                # Check for spike and reversal
                if max_price > min_price * 1.01:  # >1% range
                    # Did price spike then reverse?
                    max_idx = np.argmax(window_prices)
                    min_idx = np.argmin(window_prices)
                
                    # Spike up then down
                    if max_idx < len(window_prices) - 2 and current < max_price * 0.995:
                        # Check if high volume at spike
                        spike_volume = volumes[i - 10 + max_idx]
                        avg_volume = np.mean(volumes[i-10:i])
                    
                        if spike_volume > avg_volume * 2:
                            events.append(ManipulationEvent(
                                timestamp=timestamps[i],
                                manipulation_type=ManipulationType.MOMENTUM_IGNITION,
                                severity=ManipulationSeverity.MEDIUM,
                                price_level=max_price,
                                estimated_size=spike_volume,
                                duration_seconds=10.0,
                                confidence=0.5,
                                description="Price spike with high volume followed by reversal"
                            ))
        
            return events
        except Exception as e:
            logger.error(f"Error in _detect_momentum_ignition: {e}")
            raise
    
    def _detect_wash_trading(
        self,
        prices: np.ndarray,
        volumes: np.ndarray,
        timestamps: List[datetime]
    ) -> List[ManipulationEvent]:
        """Detect potential wash trading."""
        try:
            events = []
        
            # Wash trading shows as volume without price impact
            for i in range(5, len(prices)):
                window_volumes = volumes[i-5:i]
                window_prices = prices[i-5:i]
            
                # High volume but no price movement
                total_volume = np.sum(window_volumes)
                price_range = np.max(window_prices) - np.min(window_prices)
                avg_price = np.mean(window_prices)
            
                # Volume/price impact ratio
                expected_impact = total_volume / (np.mean(volumes) * 5) * 0.001  # Expected % move
                actual_impact = price_range / avg_price
            
                if total_volume > np.mean(volumes) * 10 and actual_impact < expected_impact * 0.2:
                    events.append(ManipulationEvent(
                        timestamp=timestamps[i],
                        manipulation_type=ManipulationType.WASH_TRADING,
                        severity=ManipulationSeverity.MEDIUM,
                        price_level=prices[i],
                        estimated_size=total_volume,
                        duration_seconds=5.0,
                        confidence=0.4,
                        description="High volume with minimal price impact"
                    ))
        
            return events
        except Exception as e:
            logger.error(f"Error in _detect_wash_trading: {e}")
            raise
    
    def _estimate_book_sizes(
        self,
        prices: np.ndarray,
        volumes: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Estimate bid/ask sizes from price/volume."""
        try:
            bid_sizes = np.zeros(len(volumes))
            ask_sizes = np.zeros(len(volumes))
        
            for i in range(1, len(volumes)):
                if prices[i] > prices[i-1]:
                    # Price up = bid was larger
                    bid_sizes[i] = volumes[i] * 0.7
                    ask_sizes[i] = volumes[i] * 0.3
                else:
                    bid_sizes[i] = volumes[i] * 0.3
                    ask_sizes[i] = volumes[i] * 0.7
        
            return bid_sizes, ask_sizes
        except Exception as e:
            logger.error(f"Error in _estimate_book_sizes: {e}")
            raise
    
    def _classify_severity(self, ratio: float) -> ManipulationSeverity:
        """Classify severity based on ratio."""
        try:
            if ratio > 10:
                return ManipulationSeverity.CRITICAL
            elif ratio > 5:
                return ManipulationSeverity.HIGH
            elif ratio > 3:
                return ManipulationSeverity.MEDIUM
            else:
                return ManipulationSeverity.LOW
        except Exception as e:
            logger.error(f"Error in _classify_severity: {e}")
            raise
    
    def _determine_spoofing_side(
        self,
        events: List[ManipulationEvent]
    ) -> Optional[str]:
        """Determine which side is being spoofed."""
        try:
            spoofing_events = [
                e for e in events
                if e.manipulation_type == ManipulationType.SPOOFING
            ]
        
            if not spoofing_events:
                return None
        
            # Check descriptions for bid/ask
            bid_count = sum(1 for e in spoofing_events if 'bid' in e.description.lower())
            ask_count = sum(1 for e in spoofing_events if 'ask' in e.description.lower())
        
            if bid_count > ask_count:
                return 'bid'
            elif ask_count > bid_count:
                return 'ask'
        
            return None
        except Exception as e:
            logger.error(f"Error in _determine_spoofing_side: {e}")
            raise
    
    def _calculate_manipulation_score(
        self,
        events: List[ManipulationEvent]
    ) -> float:
        """Calculate overall manipulation score."""
        try:
            if not events:
                return 0.0
        
            # Weight by severity
            severity_weights = {
                ManipulationSeverity.LOW: 0.25,
                ManipulationSeverity.MEDIUM: 0.5,
                ManipulationSeverity.HIGH: 0.75,
                ManipulationSeverity.CRITICAL: 1.0
            }
        
            total_weight = sum(
                severity_weights[e.severity] * e.confidence
                for e in events
            )
        
            # Normalize
            max_possible = len(events) * 1.0
            score = total_weight / (max_possible + 1e-10)
        
            return min(1.0, score)
        except Exception as e:
            logger.error(f"Error in _calculate_manipulation_score: {e}")
            raise
    
    def _generate_recommendation(
        self,
        events: List[ManipulationEvent],
        active_spoofing: bool,
        score: float
    ) -> str:
        """Generate recommended action."""
        try:
            if score > 0.7:
                return "AVOID TRADING: High manipulation detected. Wait for clean market."
            elif score > 0.4:
                return "CAUTION: Moderate manipulation. Reduce size, use limit orders."
            elif active_spoofing:
                return "ALERT: Active spoofing detected. Be aware of false liquidity."
            else:
                return "NORMAL: No significant manipulation detected."
        except Exception as e:
            logger.error(f"Error in _generate_recommendation: {e}")
            raise
    
    def _generate_signal(
        self,
        events: List[ManipulationEvent],
        active_spoofing: bool,
        spoofing_side: Optional[str],
        score: float
    ) -> str:
        """Generate trading signal."""
        try:
            signals = []
        
            if active_spoofing:
                signals.append(f"ACTIVE SPOOFING on {spoofing_side or 'unknown'} side")
        
            # Count by type
            type_counts = {}
            for e in events:
                type_counts[e.manipulation_type] = type_counts.get(e.manipulation_type, 0) + 1
        
            for mtype, count in type_counts.items():
                signals.append(f"{mtype.value.upper()}: {count} events")
        
            signals.append(f"MANIPULATION SCORE: {score:.0%}")
        
            return " | ".join(signals) if signals else "No manipulation detected"
        except Exception as e:
            logger.error(f"Error in _generate_signal: {e}")
            raise
    
    def _calculate_confidence(
        self,
        events: List[ManipulationEvent]
    ) -> float:
        """Calculate confidence in the analysis."""
        try:
            if not events:
                return 0.5
        
            return np.mean([e.confidence for e in events])
        except Exception as e:
            logger.error(f"Error in _calculate_confidence: {e}")
            raise
    
    def _create_empty_result(self) -> SpoofingAnalysisResult:
        """Create empty result for insufficient data."""
        return SpoofingAnalysisResult(
            manipulation_events=[],
            active_spoofing=False,
            spoofing_side=None,
            manipulation_score=0,
            affected_price_levels=[],
            recommended_action="Insufficient data",
            trading_signal="Insufficient data",
            confidence=0
        )
