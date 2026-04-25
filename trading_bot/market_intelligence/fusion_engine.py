"""
Intelligence Fusion Engine
==========================

Combines multiple classified signals into unified market intelligence.

Uses:
- Bayesian belief updating
- Confidence-weighted averaging
- Contradiction detection
- Temporal aggregation
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import numpy as np
import logging

from .classifier import ClassifiedSignal, ClassificationCategory, DirectionalBias

logger = logging.getLogger(__name__)


class FusionConfidence(Enum):
    """Confidence levels for fused intelligence."""
    HIGH = "high"      # >0.8
    MEDIUM = "medium"  # 0.5-0.8
    LOW = "low"        # <0.5


@dataclass
class UnifiedIntelligence:
    """
    Fused market intelligence combining multiple classified signals.
    
    This is the output of Layer 2, ready for Layer 3 (Strategy Discovery).
    """
    # Fusion metadata
    timestamp: datetime = field(default_factory=datetime.now)
    signals_fused: int = 0
    fusion_window_minutes: int = 5
    
    # Overall market view
    dominant_category: Optional[ClassificationCategory] = None
    overall_direction: DirectionalBias = DirectionalBias.NEUTRAL
    overall_confidence: float = 0.0
    
    # Category breakdown
    category_signals: Dict[ClassificationCategory, List[ClassifiedSignal]] = field(default_factory=dict)
    category_confidence: Dict[ClassificationCategory, float] = field(default_factory=dict)
    
    # Specific intelligence
    top_signals: List[ClassifiedSignal] = field(default_factory=list)
    contradicting_signals: List[Tuple[ClassifiedSignal, ClassifiedSignal]] = field(default_factory=list)
    
    # Actionable insights
    recommended_assets: List[str] = field(default_factory=list)
    recommended_direction: DirectionalBias = DirectionalBias.NEUTRAL
    recommended_position_size: float = 0.0  # 0.0-1.0 of max position
    
    # Risk flags
    high_confidence_contradictions: bool = False
    unusual_signal_clustering: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'timestamp': self.timestamp.isoformat(),
            'signals_fused': self.signals_fused,
            'fusion_window_minutes': self.fusion_window_minutes,
            'dominant_category': self.dominant_category.value if self.dominant_category else None,
            'overall_direction': self.overall_direction.value,
            'overall_confidence': self.overall_confidence,
            'category_confidence': {k.value: v for k, v in self.category_confidence.items()},
            'top_signals': [s.to_dict() for s in self.top_signals[:5]],
            'recommended_assets': self.recommended_assets,
            'recommended_direction': self.recommended_direction.value,
            'recommended_position_size': self.recommended_position_size,
            'risk_flags': {
                'high_confidence_contradictions': self.high_confidence_contradictions,
                'unusual_signal_clustering': self.unusual_signal_clustering,
            },
        }


class IntelligenceFusionEngine:
    """
    Fuses multiple classified signals into coherent market intelligence.
    
    Like Palantir's fusion capabilities, this engine combines disparate
    signals into a unified view of market conditions.
    """
    
    def __init__(self, fusion_window_minutes: int = 5):
        """
        Initialize fusion engine.
        
        Args:
            fusion_window_minutes: Time window for aggregating signals
        """
        self.fusion_window_minutes = fusion_window_minutes
        self._signal_buffer: List[ClassifiedSignal] = []
        self._max_buffer_size = 1000
        
        logger.info(f"IntelligenceFusionEngine initialized with {fusion_window_minutes}min window")
    
    def add_signal(self, signal: ClassifiedSignal):
        """
        Add a classified signal to the fusion buffer.
        
        Args:
            signal: Classified signal from Layer 2
        """
        self._signal_buffer.append(signal)
        
        # Trim buffer if too large
        if len(self._signal_buffer) > self._max_buffer_size:
            cutoff = datetime.now() - timedelta(minutes=self.fusion_window_minutes * 2)
            self._signal_buffer = [
                s for s in self._signal_buffer
                if s.classification_timestamp > cutoff
            ]
    
    def fuse_signals(self, signals: Optional[List[ClassifiedSignal]] = None) -> UnifiedIntelligence:
        """
        Fuse signals into unified market intelligence.
        
        Args:
            signals: List of signals to fuse (uses buffer if None)
            
        Returns:
            UnifiedIntelligence object
        """
        if signals is None:
            signals = self._get_recent_signals()
        
        if not signals:
            return UnifiedIntelligence(
                signals_fused=0,
                overall_direction=DirectionalBias.NEUTRAL,
                overall_confidence=0.0,
            )
        
        # Group by category
        category_signals = self._group_by_category(signals)
        
        # Calculate category confidence scores
        category_confidence = self._calculate_category_confidence(category_signals)
        
        # Determine dominant category
        dominant_category = self._determine_dominant_category(category_confidence)
        
        # Calculate overall direction
        overall_direction = self._calculate_overall_direction(signals)
        overall_confidence = self._calculate_overall_confidence(signals)
        
        # Find contradictions
        contradicting_signals = self._find_contradictions(signals)
        
        # Get top signals
        top_signals = self._get_top_signals(signals, n=10)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(signals, dominant_category, overall_direction)
        
        # Check risk flags
        high_confidence_contradictions = any(
            s1.conviction_score > 0.7 and s2.conviction_score > 0.7
            for s1, s2 in contradicting_signals
        )
        
        unusual_clustering = self._detect_unusual_clustering(signals)
        
        return UnifiedIntelligence(
            signals_fused=len(signals),
            fusion_window_minutes=self.fusion_window_minutes,
            dominant_category=dominant_category,
            overall_direction=overall_direction,
            overall_confidence=overall_confidence,
            category_signals=category_signals,
            category_confidence=category_confidence,
            top_signals=top_signals,
            contradicting_signals=contradicting_signals,
            recommended_assets=recommendations['assets'],
            recommended_direction=recommendations['direction'],
            recommended_position_size=recommendations['position_size'],
            high_confidence_contradictions=high_confidence_contradictions,
            unusual_signal_clustering=unusual_clustering,
        )
    
    def _get_recent_signals(self) -> List[ClassifiedSignal]:
        """Get signals from the fusion window."""
        cutoff = datetime.now() - timedelta(minutes=self.fusion_window_minutes)
        return [s for s in self._signal_buffer if s.classification_timestamp > cutoff]
    
    def _group_by_category(self, signals: List[ClassifiedSignal]) -> Dict[ClassificationCategory, List[ClassifiedSignal]]:
        """Group signals by classification category."""
        grouped = {}
        for signal in signals:
            category = signal.classification.category
            if category not in grouped:
                grouped[category] = []
            grouped[category].append(signal)
        return grouped
    
    def _calculate_category_confidence(self, 
                                     category_signals: Dict[ClassificationCategory, List[ClassifiedSignal]]
                                     ) -> Dict[ClassificationCategory, float]:
        """Calculate confidence score for each category."""
        confidence = {}
        for category, signals in category_signals.items():
            if not signals:
                continue
            
            # Weight by conviction and number of signals
            avg_conviction = np.mean([s.conviction_score for s in signals])
            signal_count_weight = min(1.0, len(signals) / 5)  # Saturate at 5 signals
            
            confidence[category] = avg_conviction * (0.7 + 0.3 * signal_count_weight)
        
        return confidence
    
    def _determine_dominant_category(self, 
                                    category_confidence: Dict[ClassificationCategory, float]
                                    ) -> Optional[ClassificationCategory]:
        """Determine the dominant category based on confidence."""
        if not category_confidence:
            return None
        
        return max(category_confidence.items(), key=lambda x: x[1])[0]
    
    def _calculate_overall_direction(self, signals: List[ClassifiedSignal]) -> DirectionalBias:
        """Calculate overall directional bias."""
        bullish_score = sum(s.conviction_score for s in signals if s.directional_bias == DirectionalBias.BULLISH)
        bearish_score = sum(s.conviction_score for s in signals if s.directional_bias == DirectionalBias.BEARISH)
        
        if bullish_score > bearish_score * 1.2:
            return DirectionalBias.BULLISH
        elif bearish_score > bullish_score * 1.2:
            return DirectionalBias.BEARISH
        return DirectionalBias.NEUTRAL
    
    def _calculate_overall_confidence(self, signals: List[ClassifiedSignal]) -> float:
        """Calculate overall confidence score."""
        if not signals:
            return 0.0
        
        # Average conviction weighted by impact
        total_weight = sum(s.expected_impact_magnitude for s in signals)
        if total_weight == 0:
            return np.mean([s.conviction_score for s in signals])
        
        weighted_confidence = sum(
            s.conviction_score * s.expected_impact_magnitude
            for s in signals
        ) / total_weight
        
        return min(1.0, weighted_confidence)
    
    def _find_contradictions(self, signals: List[ClassifiedSignal]) -> List[Tuple[ClassifiedSignal, ClassifiedSignal]]:
        """Find signals that contradict each other."""
        contradictions = []
        
        for i, s1 in enumerate(signals):
            for s2 in signals[i+1:]:
                # Same asset, opposite directions, both high confidence
                if (s1.classification.affected_assets and s2.classification.affected_assets and
                    any(asset in s2.classification.affected_assets for asset in s1.classification.affected_assets) and
                    s1.directional_bias != s2.directional_bias and
                    s1.directional_bias != DirectionalBias.NEUTRAL and
                    s2.directional_bias != DirectionalBias.NEUTRAL and
                    s1.conviction_score > 0.5 and s2.conviction_score > 0.5):
                    contradictions.append((s1, s2))
        
        return contradictions
    
    def _get_top_signals(self, signals: List[ClassifiedSignal], n: int = 10) -> List[ClassifiedSignal]:
        """Get top N signals by conviction."""
        sorted_signals = sorted(signals, key=lambda s: s.conviction_score, reverse=True)
        return sorted_signals[:n]
    
    def _generate_recommendations(self, signals: List[ClassifiedSignal],
                                 dominant_category: Optional[ClassificationCategory],
                                 overall_direction: DirectionalBias) -> Dict[str, Any]:
        """Generate trading recommendations."""
        # Collect affected assets
        all_assets = []
        for signal in signals:
            all_assets.extend(signal.classification.affected_assets)
        
        # Count asset mentions
        asset_counts = {}
        for asset in all_assets:
            asset_counts[asset] = asset_counts.get(asset, 0) + 1
        
        # Top assets
        top_assets = sorted(asset_counts.items(), key=lambda x: x[1], reverse=True)
        recommended_assets = [asset for asset, _ in top_assets[:5]]
        
        # Position size based on confidence and contradiction risk
        avg_confidence = np.mean([s.conviction_score for s in signals]) if signals else 0
        contradiction_penalty = 0.3 if any(s1.directional_bias != s2.directional_bias 
                                          for s1 in signals for s2 in signals) else 0
        
        position_size = max(0.0, min(1.0, avg_confidence - contradiction_penalty))
        
        return {
            'assets': recommended_assets,
            'direction': overall_direction,
            'position_size': position_size,
        }
    
    def _detect_unusual_clustering(self, signals: List[ClassifiedSignal]) -> bool:
        """Detect if signals are clustering unusually (potential manipulation or major event)."""
        if len(signals) < 10:
            return False
        
        # Check if many signals arrived in a short time window
        timestamps = [s.classification_timestamp for s in signals]
        time_span = max(timestamps) - min(timestamps)
        
        # If 10+ signals within 1 minute, flag as unusual
        if time_span < timedelta(minutes=1):
            return True
        
        return False
