"""
Multi-Timeframe Consensus System
================================

Analyzes signals across multiple timeframes to achieve consensus.
"""

from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
from collections import deque
import numpy as np
import logging

logger = logging.getLogger(__name__)


class TimeFrame(Enum):
    """Trading timeframes"""
    M1 = "1m"
    M5 = "5m"
    M15 = "15m"
    M30 = "30m"
    H1 = "1h"
    H4 = "4h"
    D1 = "1d"
    W1 = "1w"


class SignalDirection(Enum):
    """Signal direction"""
    LONG = "long"
    SHORT = "short"
    NEUTRAL = "neutral"


@dataclass
class TimeframeSignal:
    """Signal from a single timeframe"""
    timeframe: TimeFrame
    direction: SignalDirection
    strength: float  # 0 to 1
    confidence: float  # 0 to 1
    indicators: Dict[str, float] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ConsensusResult:
    """Result of multi-timeframe consensus check"""
    has_consensus: bool
    direction: SignalDirection
    consensus_score: float
    weighted_strength: float
    timeframe_alignment: Dict[str, str]
    conflicting_timeframes: List[TimeFrame]
    recommendation: str
    confidence: float
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        return {
            'has_consensus': self.has_consensus,
            'direction': self.direction.value,
            'consensus_score': self.consensus_score,
            'weighted_strength': self.weighted_strength,
            'timeframe_alignment': self.timeframe_alignment,
            'conflicting_timeframes': [tf.value for tf in self.conflicting_timeframes],
            'recommendation': self.recommendation,
            'confidence': self.confidence,
            'timestamp': self.timestamp.isoformat()
        }


class MultiTimeframeConsensus:
    """
    Multi-Timeframe Consensus System
    
    Analyzes signals across multiple timeframes to determine:
    - Overall market direction
    - Signal strength and confidence
    - Timeframe alignment
    - Entry/exit recommendations
    
    Features:
    - Weighted timeframe voting
    - Configurable quorum threshold
    - Conflict detection
    - Trend alignment analysis
    """
    
    # Default timeframe weights (higher = more important)
    DEFAULT_WEIGHTS = {
        TimeFrame.M1: 0.05,
        TimeFrame.M5: 0.10,
        TimeFrame.M15: 0.15,
        TimeFrame.M30: 0.15,
        TimeFrame.H1: 0.20,
        TimeFrame.H4: 0.15,
        TimeFrame.D1: 0.15,
        TimeFrame.W1: 0.05
    }
    
    def __init__(
        self,
        quorum_threshold: float = 0.6,
        min_timeframes: int = 3,
        weights: Optional[Dict[TimeFrame, float]] = None
    ):
        """
        Initialize multi-timeframe consensus.
        
        Args:
            quorum_threshold: Minimum consensus score required (0-1)
            min_timeframes: Minimum number of timeframes needed
            weights: Custom timeframe weights
        """
        try:
            self.quorum_threshold = quorum_threshold
            self.min_timeframes = min_timeframes
            self.timeframe_weights = weights or self.DEFAULT_WEIGHTS.copy()
        
            # History tracking
            self.signal_history: Dict[TimeFrame, deque] = {
                tf: deque(maxlen=100) for tf in TimeFrame
            }
            self.consensus_history: deque = deque(maxlen=100)
        
            logger.info(f"MultiTimeframeConsensus initialized with quorum={quorum_threshold}")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    def add_signal(self, signal: TimeframeSignal):
        """Add a signal from a timeframe"""
        try:
            self.signal_history[signal.timeframe].append(signal)
        except Exception as e:
            logger.error(f"Error in add_signal: {e}")
            raise
        
    def check_consensus(
        self,
        signals: Dict[TimeFrame, TimeframeSignal]
    ) -> ConsensusResult:
        """
        Check if signals reach consensus across timeframes.
        
        Args:
            signals: Dictionary of timeframe signals
            
        Returns:
            ConsensusResult with consensus analysis
        """
        try:
            if len(signals) < self.min_timeframes:
                return ConsensusResult(
                    has_consensus=False,
                    direction=SignalDirection.NEUTRAL,
                    consensus_score=0,
                    weighted_strength=0,
                    timeframe_alignment={},
                    conflicting_timeframes=[],
                    recommendation="Insufficient timeframes for analysis",
                    confidence=0
                )
        
            # Calculate weighted votes for each direction
            long_score = 0
            short_score = 0
            neutral_score = 0
            total_weight = 0
        
            timeframe_alignment = {}
        
            for tf, signal in signals.items():
                weight = self.timeframe_weights.get(tf, 0.1)
                total_weight += weight
            
                if signal.direction == SignalDirection.LONG:
                    long_score += weight * signal.strength * signal.confidence
                    timeframe_alignment[tf.value] = "long"
                elif signal.direction == SignalDirection.SHORT:
                    short_score += weight * signal.strength * signal.confidence
                    timeframe_alignment[tf.value] = "short"
                else:
                    neutral_score += weight
                    timeframe_alignment[tf.value] = "neutral"
                
            # Normalize scores
            if total_weight > 0:
                long_score /= total_weight
                short_score /= total_weight
                neutral_score /= total_weight
            
            # Determine dominant direction
            if long_score > short_score and long_score > neutral_score:
                direction = SignalDirection.LONG
                consensus_score = long_score
            elif short_score > long_score and short_score > neutral_score:
                direction = SignalDirection.SHORT
                consensus_score = short_score
            else:
                direction = SignalDirection.NEUTRAL
                consensus_score = neutral_score
            
            # Find conflicting timeframes
            conflicting = []
            for tf, signal in signals.items():
                if direction == SignalDirection.LONG and signal.direction == SignalDirection.SHORT:
                    conflicting.append(tf)
                elif direction == SignalDirection.SHORT and signal.direction == SignalDirection.LONG:
                    conflicting.append(tf)
                
            # Calculate weighted strength
            weighted_strength = sum(
                self.timeframe_weights.get(tf, 0.1) * signal.strength
                for tf, signal in signals.items()
                if signal.direction == direction
            ) / total_weight if total_weight > 0 else 0
        
            # Determine if consensus reached
            has_consensus = (
                consensus_score >= self.quorum_threshold and
                len(conflicting) <= len(signals) // 3  # Max 1/3 conflicting
            )
        
            # Calculate confidence
            alignment_ratio = 1 - (len(conflicting) / len(signals))
            confidence = consensus_score * alignment_ratio
        
            # Generate recommendation
            recommendation = self._generate_recommendation(
                has_consensus, direction, consensus_score, conflicting
            )
        
            result = ConsensusResult(
                has_consensus=has_consensus,
                direction=direction,
                consensus_score=consensus_score,
                weighted_strength=weighted_strength,
                timeframe_alignment=timeframe_alignment,
                conflicting_timeframes=conflicting,
                recommendation=recommendation,
                confidence=confidence
            )
        
            self.consensus_history.append(result)
            return result
        except Exception as e:
            logger.error(f"Error in check_consensus: {e}")
            raise
        
    def check_simple_consensus(
        self,
        signals: Dict[TimeFrame, bool]
    ) -> Tuple[bool, float]:
        """
        Simple consensus check (backward compatible).
        
        Args:
            signals: Dictionary of timeframe to bullish signal (True/False)
            
        Returns:
            Tuple of (has_consensus, consensus_score)
        """
        try:
            weighted_votes = sum(
                self.timeframe_weights.get(tf, 0.1)
                for tf, signal in signals.items()
                if signal
            )
            total_weight = sum(
                self.timeframe_weights.get(tf, 0.1)
                for tf in signals.keys()
            )
            consensus_score = weighted_votes / total_weight if total_weight > 0 else 0
            has_consensus = consensus_score >= self.quorum_threshold
            return has_consensus, consensus_score
        except Exception as e:
            logger.error(f"Error in check_simple_consensus: {e}")
            raise
        
    def _generate_recommendation(
        self,
        has_consensus: bool,
        direction: SignalDirection,
        score: float,
        conflicting: List[TimeFrame]
    ) -> str:
        """Generate trading recommendation"""
        try:
            if not has_consensus:
                if len(conflicting) > 0:
                    return f"No consensus - {len(conflicting)} conflicting timeframes. Wait for alignment."
                return "No consensus - signals too weak. Wait for stronger signals."
            
            if direction == SignalDirection.NEUTRAL:
                return "Market is ranging. Consider range-bound strategies or stay flat."
            
            strength = "Strong" if score > 0.8 else "Moderate" if score > 0.6 else "Weak"
            action = "BUY" if direction == SignalDirection.LONG else "SELL"
        
            if len(conflicting) == 0:
                return f"{strength} {action} signal - All timeframes aligned."
            else:
                return f"{strength} {action} signal - Minor conflicts on {', '.join(tf.value for tf in conflicting)}."
        except Exception as e:
            logger.error(f"Error in _generate_recommendation: {e}")
            raise
            
    def get_trend_alignment(
        self,
        signals: Dict[TimeFrame, TimeframeSignal]
    ) -> Dict[str, Any]:
        """
        Analyze trend alignment across timeframes.
        
        Args:
            signals: Dictionary of timeframe signals
            
        Returns:
            Trend alignment analysis
        """
        # Group by trend direction
        try:
            long_tfs = [tf for tf, s in signals.items() if s.direction == SignalDirection.LONG]
            short_tfs = [tf for tf, s in signals.items() if s.direction == SignalDirection.SHORT]
            neutral_tfs = [tf for tf, s in signals.items() if s.direction == SignalDirection.NEUTRAL]
        
            # Check higher timeframe trend
            higher_tfs = [TimeFrame.H4, TimeFrame.D1, TimeFrame.W1]
            higher_direction = SignalDirection.NEUTRAL
        
            for tf in higher_tfs:
                if tf in signals:
                    higher_direction = signals[tf].direction
                    break
                
            # Check lower timeframe momentum
            lower_tfs = [TimeFrame.M1, TimeFrame.M5, TimeFrame.M15]
            lower_direction = SignalDirection.NEUTRAL
        
            for tf in lower_tfs:
                if tf in signals:
                    lower_direction = signals[tf].direction
                    break
                
            # Determine alignment
            aligned = higher_direction == lower_direction and higher_direction != SignalDirection.NEUTRAL
        
            return {
                'higher_tf_trend': higher_direction.value,
                'lower_tf_momentum': lower_direction.value,
                'aligned': aligned,
                'long_timeframes': [tf.value for tf in long_tfs],
                'short_timeframes': [tf.value for tf in short_tfs],
                'neutral_timeframes': [tf.value for tf in neutral_tfs],
                'recommendation': 'Trade with trend' if aligned else 'Wait for alignment'
            }
        except Exception as e:
            logger.error(f"Error in get_trend_alignment: {e}")
            raise
        
    def get_status(self) -> Dict[str, Any]:
        """Get current status"""
        return {
            'quorum_threshold': self.quorum_threshold,
            'min_timeframes': self.min_timeframes,
            'timeframe_weights': {tf.value: w for tf, w in self.timeframe_weights.items()},
            'consensus_history_length': len(self.consensus_history),
            'last_consensus': self.consensus_history[-1].to_dict() if self.consensus_history else None
        }


def create_mtf_consensus(
    quorum_threshold: float = 0.6,
    min_timeframes: int = 3
) -> MultiTimeframeConsensus:
    """Factory function"""
    return MultiTimeframeConsensus(quorum_threshold, min_timeframes)


if __name__ == "__main__":
    # Demo
    consensus = create_mtf_consensus()
    
    print("=== Multi-Timeframe Consensus Demo ===\n")
    
    # Create sample signals
    signals = {
        TimeFrame.M15: TimeframeSignal(
            timeframe=TimeFrame.M15,
            direction=SignalDirection.LONG,
            strength=0.7,
            confidence=0.8
        ),
        TimeFrame.H1: TimeframeSignal(
            timeframe=TimeFrame.H1,
            direction=SignalDirection.LONG,
            strength=0.8,
            confidence=0.85
        ),
        TimeFrame.H4: TimeframeSignal(
            timeframe=TimeFrame.H4,
            direction=SignalDirection.LONG,
            strength=0.6,
            confidence=0.7
        ),
        TimeFrame.D1: TimeframeSignal(
            timeframe=TimeFrame.D1,
            direction=SignalDirection.SHORT,
            strength=0.5,
            confidence=0.6
        )
    }
    
    result = consensus.check_consensus(signals)
    
    print(f"Has Consensus: {result.has_consensus}")
    print(f"Direction: {result.direction.value}")
    print(f"Consensus Score: {result.consensus_score:.2f}")
    print(f"Confidence: {result.confidence:.2f}")
    print(f"Recommendation: {result.recommendation}")
    print(f"\nTimeframe Alignment: {result.timeframe_alignment}")
    print(f"Conflicting: {[tf.value for tf in result.conflicting_timeframes]}")
    
    # Trend alignment
    print("\nTrend Alignment:")
    alignment = consensus.get_trend_alignment(signals)
    print(f"  Higher TF Trend: {alignment['higher_tf_trend']}")
    print(f"  Lower TF Momentum: {alignment['lower_tf_momentum']}")
    print(f"  Aligned: {alignment['aligned']}")
