"""
Cross-Validator - Multi-Source Validation System

Validates trading decisions by cross-referencing multiple independent sources
to detect hallucinations and ensure decision integrity.

VALIDATION SOURCES:
1. Technical Analysis (multiple indicators)
2. Sentiment Analysis (multiple sources)
3. Fundamental Data (if available)
4. Historical Patterns (backtested accuracy)
5. Expert Systems (multiple strategies)
6. External APIs (when available)

Author: AlphaAlgo Team
Date: 2026-01-28
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from collections import defaultdict
import statistics

logger = logging.getLogger(__name__)


class SourceType(Enum):
    """Types of validation sources"""
    TECHNICAL = "technical"
    SENTIMENT = "sentiment"
    FUNDAMENTAL = "fundamental"
    HISTORICAL = "historical"
    EXPERT = "expert"
    EXTERNAL = "external"
    ML_MODEL = "ml_model"
    RULE_BASED = "rule_based"


class AgreementLevel(Enum):
    """Level of agreement between sources"""
    UNANIMOUS = "unanimous"       # 100% agree
    STRONG = "strong"             # 80%+ agree
    MODERATE = "moderate"         # 60%+ agree
    WEAK = "weak"                 # 40%+ agree
    CONFLICTING = "conflicting"   # <40% agree
    INSUFFICIENT = "insufficient" # Not enough sources


@dataclass
class SourceOpinion:
    """Opinion from a single source"""
    source_name: str
    source_type: SourceType
    direction: str  # BUY, SELL, HOLD
    confidence: float
    reasoning: str
    data_points: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    weight: float = 1.0  # Source weight for voting


@dataclass
class SourceAgreement:
    """Agreement analysis between sources"""
    total_sources: int
    agreeing_sources: int
    disagreeing_sources: int
    neutral_sources: int
    agreement_ratio: float
    agreement_level: AgreementLevel
    majority_direction: str
    majority_confidence: float
    dissenting_opinions: List[SourceOpinion]
    weighted_agreement: float


@dataclass
class CrossValidationResult:
    """Result of cross-validation"""
    decision_id: str
    original_direction: str
    original_confidence: float
    source_agreement: SourceAgreement
    validated: bool
    adjusted_confidence: float
    adjusted_direction: Optional[str]
    warnings: List[str]
    recommendations: List[str]
    source_breakdown: Dict[str, List[SourceOpinion]]
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'decision_id': self.decision_id,
            'original_direction': self.original_direction,
            'original_confidence': self.original_confidence,
            'agreement_level': self.source_agreement.agreement_level.value,
            'agreement_ratio': self.source_agreement.agreement_ratio,
            'validated': self.validated,
            'adjusted_confidence': self.adjusted_confidence,
            'adjusted_direction': self.adjusted_direction,
            'warnings': self.warnings,
            'total_sources': self.source_agreement.total_sources,
            'timestamp': self.timestamp.isoformat()
        }


class CrossValidator:
    """
    Cross-validates trading decisions against multiple independent sources.
    
    The validator collects opinions from various sources and determines
    if there is sufficient agreement to validate the decision.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Validation thresholds
        self.min_sources = self.config.get('min_sources', 3)
        self.min_agreement_ratio = self.config.get('min_agreement_ratio', 0.6)
        self.strong_agreement_ratio = self.config.get('strong_agreement_ratio', 0.8)
        
        # Source weights (higher = more trusted)
        self.source_weights = self.config.get('source_weights', {
            SourceType.TECHNICAL: 1.0,
            SourceType.SENTIMENT: 0.7,
            SourceType.FUNDAMENTAL: 0.9,
            SourceType.HISTORICAL: 0.8,
            SourceType.EXPERT: 0.85,
            SourceType.EXTERNAL: 0.6,
            SourceType.ML_MODEL: 0.75,
            SourceType.RULE_BASED: 0.7,
        })
        
        # Registered sources
        self.sources: Dict[str, Dict[str, Any]] = {}
        
        # Validation history
        self.validation_history: List[CrossValidationResult] = []
        
        logger.info("CrossValidator initialized")
    
    def register_source(
        self,
        name: str,
        source_type: SourceType,
        weight: Optional[float] = None,
        callback: Optional[callable] = None
    ):
        """Register a validation source"""
        self.sources[name] = {
            'type': source_type,
            'weight': weight or self.source_weights.get(source_type, 1.0),
            'callback': callback,
            'accuracy_history': [],
        }
        logger.info(f"Registered source: {name} (type={source_type.value})")
    
    async def validate(
        self,
        decision: Dict[str, Any],
        source_opinions: Optional[List[SourceOpinion]] = None,
        market_data: Optional[Dict[str, Any]] = None
    ) -> CrossValidationResult:
        """
        Validate a decision against multiple sources.
        
        Args:
            decision: The decision to validate
            source_opinions: Pre-collected opinions (optional)
            market_data: Current market data for generating opinions
            
        Returns:
            CrossValidationResult with validation details
        """
        decision_id = decision.get('id', str(hash(str(decision)))[:8])
        original_direction = decision.get('direction', 'UNKNOWN').upper()
        original_confidence = decision.get('confidence', 0.5)
        
        # Collect opinions
        opinions = source_opinions or []
        
        # Generate opinions from registered sources if callbacks available
        if market_data:
            for name, source_info in self.sources.items():
                if source_info.get('callback'):
                    try:
                        opinion = await source_info['callback'](decision, market_data)
                        if opinion:
                            opinions.append(opinion)
                    except Exception as e:
                        logger.warning(f"Source {name} failed: {e}")
        
        # Generate synthetic opinions from decision data if not enough
        if len(opinions) < self.min_sources:
            synthetic = self._generate_synthetic_opinions(decision, market_data)
            opinions.extend(synthetic)
        
        # Analyze agreement
        agreement = self._analyze_agreement(opinions, original_direction)
        
        # Determine validation result
        validated, adjusted_confidence, adjusted_direction = self._determine_validation(
            original_direction, original_confidence, agreement
        )
        
        # Generate warnings and recommendations
        warnings = self._generate_warnings(agreement, original_direction)
        recommendations = self._generate_recommendations(agreement, validated)
        
        # Group opinions by source type
        source_breakdown = defaultdict(list)
        for op in opinions:
            source_breakdown[op.source_type.value].append(op)
        
        result = CrossValidationResult(
            decision_id=decision_id,
            original_direction=original_direction,
            original_confidence=original_confidence,
            source_agreement=agreement,
            validated=validated,
            adjusted_confidence=adjusted_confidence,
            adjusted_direction=adjusted_direction,
            warnings=warnings,
            recommendations=recommendations,
            source_breakdown=dict(source_breakdown)
        )
        
        self.validation_history.append(result)
        
        logger.info(
            f"Cross-validation for {decision_id}: "
            f"validated={validated}, agreement={agreement.agreement_level.value}"
        )
        
        return result
    
    def _analyze_agreement(
        self,
        opinions: List[SourceOpinion],
        target_direction: str
    ) -> SourceAgreement:
        """Analyze agreement between source opinions"""
        
        if not opinions:
            return SourceAgreement(
                total_sources=0,
                agreeing_sources=0,
                disagreeing_sources=0,
                neutral_sources=0,
                agreement_ratio=0.0,
                agreement_level=AgreementLevel.INSUFFICIENT,
                majority_direction='UNKNOWN',
                majority_confidence=0.0,
                dissenting_opinions=[],
                weighted_agreement=0.0
            )
        
        # Count by direction
        direction_counts = defaultdict(list)
        for op in opinions:
            direction_counts[op.direction.upper()].append(op)
        
        # Find majority
        majority_direction = max(direction_counts.keys(), key=lambda d: len(direction_counts[d]))
        majority_opinions = direction_counts[majority_direction]
        
        # Calculate agreement with target direction
        agreeing = [op for op in opinions if op.direction.upper() == target_direction.upper()]
        disagreeing = [op for op in opinions if op.direction.upper() != target_direction.upper() and op.direction.upper() != 'HOLD']
        neutral = [op for op in opinions if op.direction.upper() == 'HOLD']
        
        total = len(opinions)
        agreement_ratio = len(agreeing) / total if total > 0 else 0
        
        # Calculate weighted agreement
        total_weight = sum(op.weight for op in opinions)
        agreeing_weight = sum(op.weight for op in agreeing)
        weighted_agreement = agreeing_weight / total_weight if total_weight > 0 else 0
        
        # Determine agreement level
        if agreement_ratio >= 1.0:
            level = AgreementLevel.UNANIMOUS
        elif agreement_ratio >= 0.8:
            level = AgreementLevel.STRONG
        elif agreement_ratio >= 0.6:
            level = AgreementLevel.MODERATE
        elif agreement_ratio >= 0.4:
            level = AgreementLevel.WEAK
        elif total < self.min_sources:
            level = AgreementLevel.INSUFFICIENT
        else:
            level = AgreementLevel.CONFLICTING
        
        # Calculate majority confidence
        majority_confidence = statistics.mean([op.confidence for op in majority_opinions]) if majority_opinions else 0
        
        return SourceAgreement(
            total_sources=total,
            agreeing_sources=len(agreeing),
            disagreeing_sources=len(disagreeing),
            neutral_sources=len(neutral),
            agreement_ratio=agreement_ratio,
            agreement_level=level,
            majority_direction=majority_direction,
            majority_confidence=majority_confidence,
            dissenting_opinions=disagreeing,
            weighted_agreement=weighted_agreement
        )
    
    def _determine_validation(
        self,
        original_direction: str,
        original_confidence: float,
        agreement: SourceAgreement
    ) -> Tuple[bool, float, Optional[str]]:
        """Determine if decision is validated and adjust confidence"""
        
        adjusted_direction = None
        
        # Check if validated
        if agreement.agreement_level == AgreementLevel.INSUFFICIENT:
            # Not enough sources - reduce confidence but don't reject
            validated = True
            adjusted_confidence = original_confidence * 0.7
        
        elif agreement.agreement_level == AgreementLevel.CONFLICTING:
            # Sources disagree - reject or switch direction
            if agreement.majority_direction != original_direction:
                validated = False
                adjusted_confidence = original_confidence * 0.3
                adjusted_direction = agreement.majority_direction
            else:
                validated = True
                adjusted_confidence = original_confidence * 0.5
        
        elif agreement.agreement_level == AgreementLevel.WEAK:
            # Weak agreement - reduce confidence
            validated = True
            adjusted_confidence = original_confidence * 0.7
        
        elif agreement.agreement_level == AgreementLevel.MODERATE:
            # Moderate agreement - slight reduction
            validated = True
            adjusted_confidence = original_confidence * 0.9
        
        elif agreement.agreement_level == AgreementLevel.STRONG:
            # Strong agreement - boost confidence
            validated = True
            adjusted_confidence = min(original_confidence * 1.1, 0.95)
        
        else:  # UNANIMOUS
            # Unanimous agreement - max boost
            validated = True
            adjusted_confidence = min(original_confidence * 1.2, 0.98)
        
        return validated, adjusted_confidence, adjusted_direction
    
    def _generate_warnings(
        self,
        agreement: SourceAgreement,
        original_direction: str
    ) -> List[str]:
        """Generate warnings based on agreement analysis"""
        warnings = []
        
        if agreement.agreement_level == AgreementLevel.INSUFFICIENT:
            warnings.append(f"Only {agreement.total_sources} sources available (minimum: {self.min_sources})")
        
        if agreement.agreement_level == AgreementLevel.CONFLICTING:
            warnings.append(f"Sources are conflicting: {agreement.agreeing_sources} agree, {agreement.disagreeing_sources} disagree")
        
        if agreement.majority_direction != original_direction and agreement.majority_direction != 'HOLD':
            warnings.append(f"Majority of sources suggest {agreement.majority_direction}, not {original_direction}")
        
        if agreement.dissenting_opinions:
            high_confidence_dissent = [op for op in agreement.dissenting_opinions if op.confidence > 0.7]
            if high_confidence_dissent:
                warnings.append(f"{len(high_confidence_dissent)} high-confidence sources disagree")
        
        if agreement.weighted_agreement < agreement.agreement_ratio:
            warnings.append("Weighted agreement is lower than simple agreement (trusted sources disagree)")
        
        return warnings
    
    def _generate_recommendations(
        self,
        agreement: SourceAgreement,
        validated: bool
    ) -> List[str]:
        """Generate recommendations based on validation result"""
        recommendations = []
        
        if not validated:
            recommendations.append("Consider reversing position direction")
            recommendations.append("Reduce position size significantly")
        
        if agreement.agreement_level in [AgreementLevel.WEAK, AgreementLevel.CONFLICTING]:
            recommendations.append("Wait for clearer signals before entering")
            recommendations.append("Use tighter stop-loss if entering")
        
        if agreement.agreement_level == AgreementLevel.INSUFFICIENT:
            recommendations.append("Gather more data sources before deciding")
        
        if agreement.agreement_level in [AgreementLevel.STRONG, AgreementLevel.UNANIMOUS]:
            recommendations.append("High conviction trade - consider larger position")
        
        return recommendations
    
    def _generate_synthetic_opinions(
        self,
        decision: Dict[str, Any],
        market_data: Optional[Dict[str, Any]]
    ) -> List[SourceOpinion]:
        """Generate synthetic opinions from decision data"""
        opinions = []
        
        # Technical indicators opinion
        if decision.get('rsi'):
            rsi = decision['rsi']
            if rsi < 30:
                direction = 'BUY'
                confidence = (30 - rsi) / 30
            elif rsi > 70:
                direction = 'SELL'
                confidence = (rsi - 70) / 30
            else:
                direction = 'HOLD'
                confidence = 0.3
            
            opinions.append(SourceOpinion(
                source_name='RSI_Indicator',
                source_type=SourceType.TECHNICAL,
                direction=direction,
                confidence=min(confidence, 0.9),
                reasoning=f"RSI at {rsi}",
                weight=0.8
            ))
        
        # Trend opinion
        if decision.get('trend'):
            trend = decision['trend'].upper()
            if trend in ['UP', 'BULLISH']:
                direction = 'BUY'
            elif trend in ['DOWN', 'BEARISH']:
                direction = 'SELL'
            else:
                direction = 'HOLD'
            
            opinions.append(SourceOpinion(
                source_name='Trend_Analysis',
                source_type=SourceType.TECHNICAL,
                direction=direction,
                confidence=0.7,
                reasoning=f"Trend is {trend}",
                weight=0.9
            ))
        
        # Volume opinion
        if decision.get('volume_ratio'):
            vol_ratio = decision['volume_ratio']
            if vol_ratio > 2.0:
                # High volume confirms direction
                direction = decision.get('direction', 'HOLD')
                confidence = min(vol_ratio / 5.0, 0.9)
            else:
                direction = 'HOLD'
                confidence = 0.4
            
            opinions.append(SourceOpinion(
                source_name='Volume_Analysis',
                source_type=SourceType.TECHNICAL,
                direction=direction,
                confidence=confidence,
                reasoning=f"Volume ratio: {vol_ratio:.2f}x",
                weight=0.7
            ))
        
        # Pattern opinion
        if decision.get('pattern'):
            pattern = decision['pattern']
            bullish_patterns = ['double_bottom', 'inverse_head_shoulders', 'bullish_engulfing', 'morning_star']
            bearish_patterns = ['double_top', 'head_shoulders', 'bearish_engulfing', 'evening_star']
            
            if any(p in pattern.lower() for p in bullish_patterns):
                direction = 'BUY'
            elif any(p in pattern.lower() for p in bearish_patterns):
                direction = 'SELL'
            else:
                direction = 'HOLD'
            
            opinions.append(SourceOpinion(
                source_name='Pattern_Recognition',
                source_type=SourceType.TECHNICAL,
                direction=direction,
                confidence=0.75,
                reasoning=f"Pattern: {pattern}",
                weight=0.85
            ))
        
        # Sentiment opinion (if available)
        if decision.get('sentiment'):
            sentiment = decision['sentiment']
            if isinstance(sentiment, (int, float)):
                if sentiment > 0.3:
                    direction = 'BUY'
                elif sentiment < -0.3:
                    direction = 'SELL'
                else:
                    direction = 'HOLD'
                confidence = abs(sentiment)
            else:
                direction = 'HOLD'
                confidence = 0.3
            
            opinions.append(SourceOpinion(
                source_name='Sentiment_Analysis',
                source_type=SourceType.SENTIMENT,
                direction=direction,
                confidence=confidence,
                reasoning=f"Sentiment: {sentiment}",
                weight=0.7
            ))
        
        return opinions
    
    def get_validation_stats(self) -> Dict[str, Any]:
        """Get validation statistics"""
        if not self.validation_history:
            return {'status': 'no_history'}
        
        validated_count = sum(1 for v in self.validation_history if v.validated)
        
        agreement_levels = defaultdict(int)
        for v in self.validation_history:
            agreement_levels[v.source_agreement.agreement_level.value] += 1
        
        return {
            'total_validations': len(self.validation_history),
            'validated_count': validated_count,
            'validation_rate': validated_count / len(self.validation_history),
            'agreement_distribution': dict(agreement_levels),
            'avg_agreement_ratio': statistics.mean(
                v.source_agreement.agreement_ratio for v in self.validation_history
            ),
            'avg_adjusted_confidence': statistics.mean(
                v.adjusted_confidence for v in self.validation_history
            ),
        }


def create_cross_validator(config: Optional[Dict[str, Any]] = None) -> CrossValidator:
    """Create a new cross-validator instance"""
    return CrossValidator(config)


__all__ = [
    'CrossValidator',
    'CrossValidationResult',
    'SourceAgreement',
    'SourceOpinion',
    'SourceType',
    'AgreementLevel',
    'create_cross_validator',
]
