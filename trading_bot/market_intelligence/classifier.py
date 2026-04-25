"""
Market Intelligence Classifier
==============================

Takes raw anomalies from Layer 1 and classifies into 5 categories:
1. Liquidity Movement
2. Institutional Accumulation
3. Regulatory Change
4. Macro Regime Shifts
5. Technological Breakthroughs
"""

from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum, auto
from datetime import datetime
import logging

from ..signal_discovery.agents.base_agent import MarketAnomaly

logger = logging.getLogger(__name__)


class ClassificationCategory(Enum):
    """5 classification categories for market intelligence."""
    LIQUIDITY_MOVEMENT = "liquidity_movement"
    INSTITUTIONAL_ACCUMULATION = "institutional_accumulation"
    REGULATORY_CHANGE = "regulatory_change"
    MACRO_REGIME_SHIFTS = "macro_regime_shifts"
    TECHNOLOGICAL_BREAKTHROUGHS = "technological_breakthroughs"
    UNKNOWN = "unknown"


class DirectionalBias(Enum):
    """Directional bias from signal."""
    BULLISH = "bullish"
    BEARISH = "bearish"
    NEUTRAL = "neutral"


@dataclass
class ClassificationResult:
    """Result of classification."""
    category: ClassificationCategory
    confidence: float  # 0.0-1.0
    sub_category: str = ""  # More specific classification
    key_indicators: List[str] = field(default_factory=list)
    affected_assets: List[str] = field(default_factory=list)
    time_horizon: str = "short_term"  # immediate, short_term, medium_term, long_term


@dataclass
class ClassifiedSignal:
    """
    An anomaly that has been classified by the Market Intelligence Engine.
    
    This is the output of Layer 2, ready for fusion and routing to Layer 3.
    """
    # Original anomaly
    original_anomaly: MarketAnomaly
    
    # Classification
    classification: ClassificationResult
    
    # Market interpretation
    directional_bias: DirectionalBias
    conviction_score: float  # 0.0-1.0 combined confidence
    
    # Impact assessment
    expected_impact_magnitude: float  # 0.0-1.0
    expected_time_to_materialize: Optional[int] = None  # minutes
    
    # Cross-asset implications
    correlated_assets: List[str] = field(default_factory=list)
    hedging_assets: List[str] = field(default_factory=list)
    
    # Metadata
    classification_timestamp: datetime = field(default_factory=datetime.now)
    classifier_version: str = "1.0"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'original_anomaly': self.original_anomaly.to_dict(),
            'classification': {
                'category': self.classification.category.value,
                'confidence': self.classification.confidence,
                'sub_category': self.classification.sub_category,
                'key_indicators': self.classification.key_indicators,
                'affected_assets': self.classification.affected_assets,
                'time_horizon': self.classification.time_horizon,
            },
            'directional_bias': self.directional_bias.value,
            'conviction_score': self.conviction_score,
            'expected_impact_magnitude': self.expected_impact_magnitude,
            'expected_time_to_materialize': self.expected_time_to_materialize,
            'correlated_assets': self.correlated_assets,
            'hedging_assets': self.hedging_assets,
            'classification_timestamp': self.classification_timestamp.isoformat(),
            'classifier_version': self.classifier_version,
        }


class MarketIntelligenceClassifier:
    """
    Classifies raw anomalies into 5 market intelligence categories.
    
    Uses rule-based and ML-based classification to determine:
    - What type of market signal this is
    - Directional bias (bullish/bearish/neutral)
    - Expected impact magnitude
    - Time horizon
    """
    
    def __init__(self):
        """Initialize classifier with category-specific classifiers."""
        self.category_classifiers = {
            ClassificationCategory.LIQUIDITY_MOVEMENT: self._classify_liquidity,
            ClassificationCategory.INSTITUTIONAL_ACCUMULATION: self._classify_institutional,
            ClassificationCategory.REGULATORY_CHANGE: self._classify_regulatory,
            ClassificationCategory.MACRO_REGIME_SHIFTS: self._classify_macro,
            ClassificationCategory.TECHNOLOGICAL_BREAKTHROUGHS: self._classify_tech,
        }
        
        logger.info("MarketIntelligenceClassifier initialized")
    
    def classify_signal(self, anomaly: MarketAnomaly) -> List[ClassifiedSignal]:
        """
        Classify a raw anomaly into market intelligence categories.
        
        Can return multiple classifications if anomaly fits multiple categories.
        
        Args:
            anomaly: Raw anomaly from Layer 1
            
        Returns:
            List of classified signals (can be empty if unclassifiable)
        """
        classified_signals = []
        
        # Try classification for each category
        for category, classifier in self.category_classifiers.items():
            try:
                classification = classifier(anomaly)
                if classification and classification.confidence > 0.3:
                    # Calculate directional bias
                    bias = self._calculate_directional_bias(anomaly, classification)
                    
                    # Calculate conviction score
                    conviction = self._calculate_conviction(anomaly, classification)
                    
                    classified = ClassifiedSignal(
                        original_anomaly=anomaly,
                        classification=classification,
                        directional_bias=bias,
                        conviction_score=conviction,
                        expected_impact_magnitude=self._estimate_impact(anomaly, classification),
                    )
                    
                    classified_signals.append(classified)
            except Exception as e:
                logger.error(f"Classification error for {category.value}: {e}")
        
        # If no classifications, mark as unknown
        if not classified_signals:
            unknown_classification = ClassificationResult(
                category=ClassificationCategory.UNKNOWN,
                confidence=0.5,
                sub_category="unclassified",
                affected_assets=[anomaly.primary_asset] if anomaly.primary_asset else [],
            )
            classified_signals.append(ClassifiedSignal(
                original_anomaly=anomaly,
                classification=unknown_classification,
                directional_bias=DirectionalBias.NEUTRAL,
                conviction_score=0.3,
                expected_impact_magnitude=0.1,
            ))
        
        return classified_signals
    
    def _classify_liquidity(self, anomaly: MarketAnomaly) -> Optional[ClassificationResult]:
        """Classify liquidity movement signals."""
        # Check if anomaly relates to liquidity
        liquidity_indicators = ['volume', 'spread', 'depth', 'flow', 'dark_pool', 'block']
        
        desc_lower = anomaly.description.lower()
        has_liquidity_signal = any(ind in desc_lower for ind in liquidity_indicators)
        
        if not has_liquidity_signal and anomaly.anomaly_type.value not in ['volume_anomaly', 'liquidity_anomaly']:
            return None
        
        # Determine liquidity direction
        is_inflow = any(word in desc_lower for word in ['inflow', 'increase', 'accumulation', 'buying'])
        is_outflow = any(word in desc_lower for word in ['outflow', 'decrease', 'distribution', 'selling'])
        
        sub_category = "liquidity_inflow" if is_inflow else "liquidity_outflow" if is_outflow else "liquidity_shift"
        
        return ClassificationResult(
            category=ClassificationCategory.LIQUIDITY_MOVEMENT,
            confidence=anomaly.confidence * (1.2 if has_liquidity_signal else 0.8),
            sub_category=sub_category,
            key_indicators=[anomaly.anomaly_type.value],
            affected_assets=[anomaly.primary_asset] if anomaly.primary_asset else [],
            time_horizon="immediate" if anomaly.anomaly_type.value == 'volume_anomaly' else "short_term",
        )
    
    def _classify_institutional(self, anomaly: MarketAnomaly) -> Optional[ClassificationResult]:
        """Classify institutional accumulation signals."""
        institutional_indicators = ['institutional', 'whale', '13f', 'otc', 'block_trade', 'smart_money']
        
        desc_lower = anomaly.description.lower()
        source_str = anomaly.data_source.value if anomaly.data_source else ""
        
        is_institutional = any(ind in desc_lower or ind in source_str for ind in institutional_indicators)
        
        if not is_institutional:
            return None
        
        sub_category = "accumulation" if "buy" in desc_lower or "inflow" in desc_lower else "distribution"
        
        return ClassificationResult(
            category=ClassificationCategory.INSTITUTIONAL_ACCUMULATION,
            confidence=anomaly.confidence,
            sub_category=sub_category,
            key_indicators=['large_block_trade', 'dark_pool_activity'],
            affected_assets=[anomaly.primary_asset] if anomaly.primary_asset else [],
            time_horizon="medium_term",
        )
    
    def _classify_regulatory(self, anomaly: MarketAnomaly) -> Optional[ClassificationResult]:
        """Classify regulatory change signals."""
        regulatory_indicators = ['regulation', 'policy', 'sec', 'fed', 'legislation', 'compliance', 'hearing']
        
        desc_lower = anomaly.description.lower()
        source_str = anomaly.data_source.value if anomaly.data_source else ""
        
        is_regulatory = any(ind in desc_lower or ind in source_str for ind in regulatory_indicators)
        
        if not is_regulatory:
            return None
        
        # Determine impact direction
        is_positive = any(word in desc_lower for word in ['approve', 'favorable', 'ease', 'deregulation'])
        is_negative = any(word in desc_lower for word in ['ban', 'restrict', 'crackdown', 'investigation'])
        
        sub_category = "positive_regulation" if is_positive else "negative_regulation" if is_negative else "regulatory_change"
        
        return ClassificationResult(
            category=ClassificationCategory.REGULATORY_CHANGE,
            confidence=anomaly.confidence * 1.1,  # Higher confidence for regulatory
            sub_category=sub_category,
            key_indicators=['policy_shift', 'regulatory_announcement'],
            affected_assets=[anomaly.primary_asset] if anomaly.primary_asset else ['sector_etfs'],
            time_horizon="long_term",
        )
    
    def _classify_macro(self, anomaly: MarketAnomaly) -> Optional[ClassificationResult]:
        """Classify macro regime shift signals."""
        macro_indicators = ['inflation', 'recession', 'yield_curve', 'fed', 'ecb', 'employment', 'gdp', 'cpi']
        
        desc_lower = anomaly.description.lower()
        source_str = anomaly.data_source.value if anomaly.data_source else ""
        
        is_macro = any(ind in desc_lower or ind in source_str for ind in macro_indicators)
        
        if not is_macro and anomaly.anomaly_type.value != 'regime_change':
            return None
        
        sub_category = "monetary_policy" if "fed" in source_str else "economic_indicator" if "bls" in source_str or "bea" in source_str else "macro_shift"
        
        return ClassificationResult(
            category=ClassificationCategory.MACRO_REGIME_SHIFTS,
            confidence=anomaly.confidence,
            sub_category=sub_category,
            key_indicators=['regime_change', 'macro_indicator'],
            affected_assets=['macro_etfs', 'bonds', 'currencies'],
            time_horizon="long_term",
        )
    
    def _classify_tech(self, anomaly: MarketAnomaly) -> Optional[ClassificationResult]:
        """Classify technological breakthrough signals."""
        tech_indicators = ['patent', 'github', 'protocol', 'defi', 'ai', 'breakthrough', 'product_launch']
        
        desc_lower = anomaly.description.lower()
        source_str = anomaly.data_source.value if anomaly.data_source else ""
        
        is_tech = any(ind in desc_lower or ind in source_str for ind in tech_indicators)
        
        if not is_tech:
            return None
        
        sub_category = "protocol_upgrade" if "protocol" in source_str else "patent_filing" if "patent" in desc_lower else "tech_breakthrough"
        
        return ClassificationResult(
            category=ClassificationCategory.TECHNOLOGICAL_BREAKTHROUGHS,
            confidence=anomaly.confidence * 0.9,
            sub_category=sub_category,
            key_indicators=['innovation', 'disruption'],
            affected_assets=[anomaly.primary_asset] if anomaly.primary_asset else ['tech_stocks'],
            time_horizon="medium_term",
        )
    
    def _calculate_directional_bias(self, anomaly: MarketAnomaly, 
                                   classification: ClassificationResult) -> DirectionalBias:
        """Calculate directional bias from anomaly and classification."""
        desc_lower = anomaly.description.lower()
        
        # Positive indicators
        positive_words = ['bullish', 'accumulation', 'inflow', 'breakthrough', 'approval', 'launch', 'positive']
        # Negative indicators
        negative_words = ['bearish', 'distribution', 'outflow', 'ban', 'restriction', 'crisis', 'negative', 'crash']
        
        positive_score = sum(1 for word in positive_words if word in desc_lower)
        negative_score = sum(1 for word in negative_words if word in desc_lower)
        
        if classification.category == ClassificationCategory.LIQUIDITY_MOVEMENT:
            if 'inflow' in classification.sub_category:
                positive_score += 1
            elif 'outflow' in classification.sub_category:
                negative_score += 1
        
        if positive_score > negative_score:
            return DirectionalBias.BULLISH
        elif negative_score > positive_score:
            return DirectionalBias.BEARISH
        return DirectionalBias.NEUTRAL
    
    def _calculate_conviction(self, anomaly: MarketAnomaly, 
                            classification: ClassificationResult) -> float:
        """Calculate overall conviction score."""
        base_confidence = anomaly.confidence
        classification_confidence = classification.confidence
        
        # Weight by anomaly severity
        severity_weight = anomaly.severity / 10
        
        conviction = (base_confidence + classification_confidence + severity_weight) / 3
        return min(1.0, conviction)
    
    def _estimate_impact(self, anomaly: MarketAnomaly, 
                        classification: ClassificationResult) -> float:
        """Estimate expected impact magnitude."""
        # Base impact from confidence
        base_impact = anomaly.confidence
        
        # Adjust by category
        category_multipliers = {
            ClassificationCategory.LIQUIDITY_MOVEMENT: 0.7,
            ClassificationCategory.INSTITUTIONAL_ACCUMULATION: 0.8,
            ClassificationCategory.REGULATORY_CHANGE: 0.9,
            ClassificationCategory.MACRO_REGIME_SHIFTS: 1.0,
            ClassificationCategory.TECHNOLOGICAL_BREAKTHROUGHS: 0.75,
        }
        
        multiplier = category_multipliers.get(classification.category, 0.5)
        return min(1.0, base_impact * multiplier)
