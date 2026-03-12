"""
Metacognitive Self-Awareness Layer
Self-confidence estimation, context recognition, and self-reflection
"""

import numpy as np
import pandas as pd
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import logging
from collections import deque, defaultdict
from typing import Set
import numpy
import pandas

logger = logging.getLogger(__name__)


class ConfidenceLevel(Enum):
    """Confidence levels"""
    VERY_LOW = 1
    LOW = 2
    MODERATE = 3
    HIGH = 4
    VERY_HIGH = 5


class ModelValidity(Enum):
    """Model validity in current context"""
    INVALID = "invalid"  # Outside training distribution
    LOW_VALIDITY = "low_validity"  # Edge of training distribution
    MODERATE_VALIDITY = "moderate_validity"  # Within training but uncertain
    HIGH_VALIDITY = "high_validity"  # Well within training distribution
    PERFECT_VALIDITY = "perfect_validity"  # Ideal conditions


@dataclass
class ConfidenceAssessment:
    """Comprehensive confidence assessment"""
    overall_confidence: float  # 0-10
    confidence_level: ConfidenceLevel
    model_agreement: float  # 0-1
    historical_accuracy: float  # 0-1
    data_quality: float  # 0-1
    regime_familiarity: float  # 0-1
    volatility_adjustment: float  # Multiplier
    components: Dict[str, float]
    reasoning: List[str]
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ContextRecognition:
    """Current context assessment"""
    regime_type: str
    within_training_distribution: bool
    validity: ModelValidity
    unprecedented_factors: List[str]
    similar_historical_periods: List[Dict[str, Any]]
    confidence_in_recognition: float
    warnings: List[str]


@dataclass
class SelfReflection:
    """Post-trade self-reflection"""
    trade_id: str
    outcome: str  # WIN, LOSS, BREAKEVEN
    expected_outcome: str
    prediction_accuracy: float
    lessons_learned: List[str]
    what_went_right: List[str]
    what_went_wrong: List[str]
    model_updates_needed: List[str]
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class KnowledgeGap:
    """Identified knowledge gap"""
    gap_type: str
    description: str
    severity: float  # 0-10
    impact_on_performance: str
    research_priority: int  # 1-10
    potential_solutions: List[str]


class ConfidenceEstimator:
    """Estimate confidence in predictions"""
    
    def __init__(self):
        try:
            self.prediction_history: deque = deque(maxlen=1000)
            self.accuracy_by_confidence: Dict[int, List[bool]] = defaultdict(list)
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    def estimate_confidence(self, prediction_context: Dict[str, Any]) -> ConfidenceAssessment:
        """Estimate confidence in current prediction"""
        
        try:
            components = {}
            reasoning = []
        
            # 1. Model Agreement
            model_agreement = prediction_context.get('model_agreement', 0.5)
            components['model_agreement'] = model_agreement
        
            if model_agreement > 0.8:
                reasoning.append(f"High model agreement ({model_agreement:.2%})")
            elif model_agreement < 0.5:
                reasoning.append(f"Low model agreement ({model_agreement:.2%}) - conflicting signals")
        
            # 2. Historical Accuracy
            historical_accuracy = self._calculate_historical_accuracy(prediction_context)
            components['historical_accuracy'] = historical_accuracy
        
            if historical_accuracy > 0.7:
                reasoning.append(f"Strong historical accuracy ({historical_accuracy:.2%})")
            elif historical_accuracy < 0.5:
                reasoning.append(f"Weak historical accuracy ({historical_accuracy:.2%})")
        
            # 3. Data Quality
            data_quality = prediction_context.get('data_quality', 0.8)
            components['data_quality'] = data_quality
        
            if data_quality < 0.7:
                reasoning.append(f"Data quality concerns ({data_quality:.2%})")
        
            # 4. Regime Familiarity
            regime_familiarity = prediction_context.get('regime_familiarity', 0.5)
            components['regime_familiarity'] = regime_familiarity
        
            if regime_familiarity < 0.5:
                reasoning.append(f"Unfamiliar regime ({regime_familiarity:.2%})")
        
            # 5. Volatility Adjustment
            volatility = prediction_context.get('volatility', 0.02)
            avg_volatility = prediction_context.get('avg_volatility', 0.02)
        
            if avg_volatility > 0:
                volatility_ratio = volatility / avg_volatility
                if volatility_ratio > 2.0:
                    volatility_adjustment = 0.5  # Reduce confidence in high vol
                    reasoning.append(f"High volatility ({volatility_ratio:.1f}x normal)")
                elif volatility_ratio < 0.5:
                    volatility_adjustment = 1.2  # Increase confidence in low vol
                    reasoning.append(f"Low volatility ({volatility_ratio:.1f}x normal)")
                else:
                    volatility_adjustment = 1.0
            else:
                volatility_adjustment = 1.0
        
            components['volatility_adjustment'] = volatility_adjustment
        
            # Calculate overall confidence
            base_confidence = (
                model_agreement * 0.3 +
                historical_accuracy * 0.3 +
                data_quality * 0.2 +
                regime_familiarity * 0.2
            )
        
            overall_confidence = base_confidence * volatility_adjustment * 10
            overall_confidence = max(0, min(10, overall_confidence))
        
            # Determine confidence level
            if overall_confidence >= 8:
                level = ConfidenceLevel.VERY_HIGH
            elif overall_confidence >= 6:
                level = ConfidenceLevel.HIGH
            elif overall_confidence >= 4:
                level = ConfidenceLevel.MODERATE
            elif overall_confidence >= 2:
                level = ConfidenceLevel.LOW
            else:
                level = ConfidenceLevel.VERY_LOW
        
            return ConfidenceAssessment(
                overall_confidence=overall_confidence,
                confidence_level=level,
                model_agreement=model_agreement,
                historical_accuracy=historical_accuracy,
                data_quality=data_quality,
                regime_familiarity=regime_familiarity,
                volatility_adjustment=volatility_adjustment,
                components=components,
                reasoning=reasoning
            )
        except Exception as e:
            logger.error(f"Error in estimate_confidence: {e}")
            raise
    
    def _calculate_historical_accuracy(self, context: Dict[str, Any]) -> float:
        """Calculate historical accuracy in similar contexts"""
        
        try:
            if not self.prediction_history:
                return 0.7  # Default moderate accuracy
        
            # Filter similar contexts
            similar = [p for p in self.prediction_history 
                      if self._is_similar_context(p['context'], context)]
        
            if not similar:
                return 0.6  # Lower confidence for novel contexts
        
            # Calculate accuracy
            correct = sum(1 for p in similar if p.get('correct', False))
            accuracy = correct / len(similar)
        
            return accuracy
        except Exception as e:
            logger.error(f"Error in _calculate_historical_accuracy: {e}")
            raise
    
    def _is_similar_context(self, ctx1: Dict, ctx2: Dict) -> bool:
        """Check if two contexts are similar"""
        
        # Simple similarity check
        try:
            regime1 = ctx1.get('regime', '')
            regime2 = ctx2.get('regime', '')
        
            return regime1 == regime2
        except Exception as e:
            logger.error(f"Error in _is_similar_context: {e}")
            raise
    
    def record_prediction(self, context: Dict[str, Any], 
                         confidence: float, correct: bool):
        """Record prediction outcome for calibration"""
        
        try:
            self.prediction_history.append({
                'context': context,
                'confidence': confidence,
                'correct': correct,
                'timestamp': datetime.now()
            })
        
            # Track accuracy by confidence bucket
            confidence_bucket = int(confidence)
            self.accuracy_by_confidence[confidence_bucket].append(correct)
        except Exception as e:
            logger.error(f"Error in record_prediction: {e}")
            raise
    
    def get_calibration_curve(self) -> Dict[int, float]:
        """Get calibration curve (confidence vs actual accuracy)"""
        
        try:
            calibration = {}
        
            for confidence_level, outcomes in self.accuracy_by_confidence.items():
                if outcomes:
                    accuracy = sum(outcomes) / len(outcomes)
                    calibration[confidence_level] = accuracy
        
            return calibration
        except Exception as e:
            logger.error(f"Error in get_calibration_curve: {e}")
            raise


class ContextRecognizer:
    """Recognize and assess current market context"""
    
    def __init__(self):
        try:
            self.training_data_stats: Dict[str, Any] = {}
            self.historical_regimes: List[Dict[str, Any]] = []
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    def set_training_distribution(self, stats: Dict[str, Any]):
        """Set statistics of training data distribution"""
        try:
            self.training_data_stats = stats
        except Exception as e:
            logger.error(f"Error in set_training_distribution: {e}")
            raise
    
    def recognize_context(self, current_data: Dict[str, Any]) -> ContextRecognition:
        """Recognize current market context"""
        
        # Check if within training distribution
        try:
            within_training = self._check_training_distribution(current_data)
        
            # Determine validity
            validity = self._assess_validity(current_data, within_training)
        
            # Identify unprecedented factors
            unprecedented = self._identify_unprecedented_factors(current_data)
        
            # Find similar historical periods
            similar_periods = self._find_similar_periods(current_data)
        
            # Calculate confidence in recognition
            recognition_confidence = self._calculate_recognition_confidence(
                within_training, unprecedented, similar_periods
            )
        
            # Generate warnings
            warnings = self._generate_warnings(validity, unprecedented)
        
            return ContextRecognition(
                regime_type=current_data.get('regime', 'unknown'),
                within_training_distribution=within_training,
                validity=validity,
                unprecedented_factors=unprecedented,
                similar_historical_periods=similar_periods,
                confidence_in_recognition=recognition_confidence,
                warnings=warnings
            )
        except Exception as e:
            logger.error(f"Error in recognize_context: {e}")
            raise
    
    def _check_training_distribution(self, current_data: Dict[str, Any]) -> bool:
        """Check if current data is within training distribution"""
        
        try:
            if not self.training_data_stats:
                return True  # Assume valid if no stats available
        
            # Check key metrics
            for metric, value in current_data.items():
                if metric in self.training_data_stats:
                    stats = self.training_data_stats[metric]
                    min_val = stats.get('min', float('-inf'))
                    max_val = stats.get('max', float('inf'))
                
                    if not (min_val <= value <= max_val):
                        return False
        
            return True
        except Exception as e:
            logger.error(f"Error in _check_training_distribution: {e}")
            raise
    
    def _assess_validity(self, current_data: Dict[str, Any], 
                        within_training: bool) -> ModelValidity:
        """Assess model validity in current context"""
        
        try:
            if not within_training:
                return ModelValidity.INVALID
        
            # Check how far from center of distribution
            distance_from_center = 0.0
            count = 0
        
            for metric, value in current_data.items():
                if metric in self.training_data_stats:
                    stats = self.training_data_stats[metric]
                    mean = stats.get('mean', value)
                    std = stats.get('std', 1.0)
                
                    if std > 0:
                        z_score = abs((value - mean) / std)
                        distance_from_center += z_score
                        count += 1
        
            if count > 0:
                avg_distance = distance_from_center / count
            
                if avg_distance < 1.0:
                    return ModelValidity.PERFECT_VALIDITY
                elif avg_distance < 2.0:
                    return ModelValidity.HIGH_VALIDITY
                elif avg_distance < 3.0:
                    return ModelValidity.MODERATE_VALIDITY
                else:
                    return ModelValidity.LOW_VALIDITY
        
            return ModelValidity.MODERATE_VALIDITY
        except Exception as e:
            logger.error(f"Error in _assess_validity: {e}")
            raise
    
    def _identify_unprecedented_factors(self, current_data: Dict[str, Any]) -> List[str]:
        """Identify unprecedented factors"""
        
        try:
            unprecedented = []
        
            # Check for extreme values
            for metric, value in current_data.items():
                if metric in self.training_data_stats:
                    stats = self.training_data_stats[metric]
                    max_val = stats.get('max', float('inf'))
                    min_val = stats.get('min', float('-inf'))
                
                    if value > max_val:
                        unprecedented.append(f"{metric} at all-time high ({value:.2f} vs max {max_val:.2f})")
                    elif value < min_val:
                        unprecedented.append(f"{metric} at all-time low ({value:.2f} vs min {min_val:.2f})")
        
            return unprecedented
        except Exception as e:
            logger.error(f"Error in _identify_unprecedented_factors: {e}")
            raise
    
    def _find_similar_periods(self, current_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Find similar historical periods"""
        
        try:
            similar = []
        
            for period in self.historical_regimes:
                similarity = self._calculate_similarity(current_data, period)
            
                if similarity > 0.7:
                    similar.append({
                        'period': period.get('date', 'unknown'),
                        'similarity': similarity,
                        'outcome': period.get('outcome', 'unknown')
                    })
        
            return sorted(similar, key=lambda x: x['similarity'], reverse=True)[:5]
        except Exception as e:
            logger.error(f"Error in _find_similar_periods: {e}")
            raise
    
    def _calculate_similarity(self, data1: Dict, data2: Dict) -> float:
        """Calculate similarity between two data points"""
        
        try:
            common_keys = set(data1.keys()) & set(data2.keys())
        
            if not common_keys:
                return 0.0
        
            similarities = []
        
            for key in common_keys:
                v1, v2 = data1[key], data2[key]
            
                if isinstance(v1, (int, float)) and isinstance(v2, (int, float)):
                    # Numerical similarity
                    if v1 == 0 and v2 == 0:
                        sim = 1.0
                    elif v1 == 0 or v2 == 0:
                        sim = 0.0
                    else:
                        sim = 1 - min(abs(v1 - v2) / max(abs(v1), abs(v2)), 1.0)
                    similarities.append(sim)
        
            return np.mean(similarities) if similarities else 0.0
        except Exception as e:
            logger.error(f"Error in _calculate_similarity: {e}")
            raise
    
    def _calculate_recognition_confidence(self, within_training: bool,
                                         unprecedented: List[str],
                                         similar_periods: List[Dict]) -> float:
        """Calculate confidence in context recognition"""
        
        try:
            confidence = 0.5  # Base
        
            if within_training:
                confidence += 0.3
        
            if not unprecedented:
                confidence += 0.1
        
            if similar_periods:
                confidence += 0.1 * min(len(similar_periods) / 5, 1.0)
        
            return min(confidence, 1.0)
        except Exception as e:
            logger.error(f"Error in _calculate_recognition_confidence: {e}")
            raise
    
    def _generate_warnings(self, validity: ModelValidity, 
                          unprecedented: List[str]) -> List[str]:
        """Generate warnings about current context"""
        
        try:
            warnings = []
        
            if validity == ModelValidity.INVALID:
                warnings.append("CRITICAL: Current conditions outside training distribution")
                warnings.append("Model predictions UNRELIABLE")
            elif validity == ModelValidity.LOW_VALIDITY:
                warnings.append("WARNING: Low model validity in current conditions")
                warnings.append("Reduce position sizing recommended")
        
            if unprecedented:
                warnings.append(f"ALERT: {len(unprecedented)} unprecedented factors detected")
                for factor in unprecedented[:3]:
                    warnings.append(f"  • {factor}")
        
            return warnings
        except Exception as e:
            logger.error(f"Error in _generate_warnings: {e}")
            raise


class SelfReflectionEngine:
    """Post-trade reflection and learning"""
    
    def __init__(self):
        try:
            self.reflection_history: List[SelfReflection] = []
            self.lesson_database: Dict[str, List[str]] = defaultdict(list)
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    def reflect_on_trade(self, trade_data: Dict[str, Any]) -> SelfReflection:
        """Reflect on trade outcome"""
        
        # Determine outcome
        try:
            pnl = trade_data.get('pnl', 0)
            if pnl > 0:
                outcome = "WIN"
            elif pnl < 0:
                outcome = "LOSS"
            else:
                outcome = "BREAKEVEN"
        
            # Compare to expectation
            expected = trade_data.get('expected_outcome', 'WIN')
            prediction_accuracy = 1.0 if outcome == expected else 0.0
        
            # Analyze what went right/wrong
            what_went_right = self._analyze_success_factors(trade_data)
            what_went_wrong = self._analyze_failure_factors(trade_data)
        
            # Extract lessons
            lessons = self._extract_lessons(trade_data, outcome, expected)
        
            # Identify needed model updates
            model_updates = self._identify_model_updates(trade_data, outcome)
        
            reflection = SelfReflection(
                trade_id=trade_data.get('trade_id', 'unknown'),
                outcome=outcome,
                expected_outcome=expected,
                prediction_accuracy=prediction_accuracy,
                lessons_learned=lessons,
                what_went_right=what_went_right,
                what_went_wrong=what_went_wrong,
                model_updates_needed=model_updates
            )
        
            self.reflection_history.append(reflection)
        
            # Store lessons
            for lesson in lessons:
                self.lesson_database[outcome].append(lesson)
        
            return reflection
        except Exception as e:
            logger.error(f"Error in reflect_on_trade: {e}")
            raise
    
    def _analyze_success_factors(self, trade_data: Dict[str, Any]) -> List[str]:
        """Analyze what contributed to success"""
        
        try:
            factors = []
        
            if trade_data.get('confluence_score', 0) > 75:
                factors.append("High signal confluence across dimensions")
        
            if trade_data.get('regime_match', False):
                factors.append("Strategy matched market regime")
        
            if trade_data.get('execution_quality', 0) > 0.9:
                factors.append("Excellent execution with minimal slippage")
        
            return factors
        except Exception as e:
            logger.error(f"Error in _analyze_success_factors: {e}")
            raise
    
    def _analyze_failure_factors(self, trade_data: Dict[str, Any]) -> List[str]:
        """Analyze what led to failure"""
        
        try:
            factors = []
        
            if trade_data.get('stopped_out', False):
                factors.append("Stopped out - stop may have been too tight")
        
            if trade_data.get('regime_shift', False):
                factors.append("Market regime shifted during trade")
        
            if trade_data.get('news_event', False):
                factors.append("Unexpected news event impacted trade")
        
            return factors
        except Exception as e:
            logger.error(f"Error in _analyze_failure_factors: {e}")
            raise
    
    def _extract_lessons(self, trade_data: Dict[str, Any], 
                        outcome: str, expected: str) -> List[str]:
        """Extract lessons from trade"""
        
        try:
            lessons = []
        
            if outcome != expected:
                lessons.append(f"Prediction was incorrect - review {trade_data.get('strategy', 'unknown')} strategy")
        
            if trade_data.get('max_adverse_excursion', 0) > 0.02:
                lessons.append("Large adverse excursion - consider wider stops or better entry timing")
        
            if trade_data.get('time_in_trade', 0) > trade_data.get('expected_duration', float('inf')):
                lessons.append("Trade took longer than expected - review exit criteria")
        
            return lessons
        except Exception as e:
            logger.error(f"Error in _extract_lessons: {e}")
            raise
    
    def _identify_model_updates(self, trade_data: Dict[str, Any], 
                               outcome: str) -> List[str]:
        """Identify needed model updates"""
        
        try:
            updates = []
        
            if trade_data.get('model_confidence', 0) > 0.8 and outcome == "LOSS":
                updates.append("Recalibrate confidence estimation - overconfident")
        
            if trade_data.get('unexpected_correlation', False):
                updates.append("Update correlation matrix with new relationships")
        
            return updates
        except Exception as e:
            logger.error(f"Error in _identify_model_updates: {e}")
            raise
    
    def get_recurring_lessons(self, min_occurrences: int = 3) -> List[Tuple[str, int]]:
        """Get lessons that appear repeatedly"""
        
        try:
            all_lessons = []
            for lessons in self.lesson_database.values():
                all_lessons.extend(lessons)
        
            # Count occurrences
            lesson_counts = defaultdict(int)
            for lesson in all_lessons:
                lesson_counts[lesson] += 1
        
            # Filter by minimum occurrences
            recurring = [(lesson, count) for lesson, count in lesson_counts.items() 
                        if count >= min_occurrences]
        
            return sorted(recurring, key=lambda x: x[1], reverse=True)
        except Exception as e:
            logger.error(f"Error in get_recurring_lessons: {e}")
            raise


class MetacognitiveAwareness:
    """
    Complete metacognitive self-awareness system
    """
    
    def __init__(self):
        try:
            self.confidence_estimator = ConfidenceEstimator()
            self.context_recognizer = ContextRecognizer()
            self.reflection_engine = SelfReflectionEngine()
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    def assess_confidence(self, prediction_context: Dict[str, Any]) -> ConfidenceAssessment:
        """Assess confidence in current prediction"""
        return self.confidence_estimator.estimate_confidence(prediction_context)
    
    def recognize_context(self, current_data: Dict[str, Any]) -> ContextRecognition:
        """Recognize and assess current context"""
        return self.context_recognizer.recognize_context(current_data)
    
    def reflect_on_trade(self, trade_data: Dict[str, Any]) -> SelfReflection:
        """Reflect on completed trade"""
        return self.reflection_engine.reflect_on_trade(trade_data)
    
    def get_self_awareness_report(self) -> Dict[str, Any]:
        """Generate comprehensive self-awareness report"""
        
        # Calibration curve
        try:
            calibration = self.confidence_estimator.get_calibration_curve()
        
            # Recurring lessons
            recurring_lessons = self.reflection_engine.get_recurring_lessons()
        
            # Recent reflections
            recent_reflections = self.reflection_engine.reflection_history[-10:]
        
            return {
                'calibration_curve': calibration,
                'recurring_lessons': recurring_lessons,
                'recent_reflections': recent_reflections,
                'total_predictions': len(self.confidence_estimator.prediction_history),
                'total_reflections': len(self.reflection_engine.reflection_history)
            }
        except Exception as e:
            logger.error(f"Error in get_self_awareness_report: {e}")
            raise


# Example usage
if __name__ == "__main__":
    # Initialize system
    awareness = MetacognitiveAwareness()
    
    # Set training distribution
    awareness.context_recognizer.set_training_distribution({
        'volatility': {'min': 0.01, 'max': 0.05, 'mean': 0.02, 'std': 0.01},
        'volume': {'min': 1000, 'max': 10000, 'mean': 5000, 'std': 2000}
    })
    
    logger.info(f"\n{'='*80}")
    logger.info(f"METACOGNITIVE SELF-AWARENESS SYSTEM")
    logger.info(f"{'='*80}")
    
    # Assess confidence
    prediction_context = {
        'model_agreement': 0.85,
        'data_quality': 0.9,
        'regime_familiarity': 0.7,
        'volatility': 0.025,
        'avg_volatility': 0.02,
        'regime': 'trending'
    }
    
    confidence = awareness.assess_confidence(prediction_context)
    
    logger.info(f"\nCONFIDENCE ASSESSMENT:")
    logger.info(f"  Overall Confidence: {confidence.overall_confidence:.1f}/10")
    logger.info(f"  Level: {confidence.confidence_level.name}")
    logger.info(f"  Reasoning:")
    for reason in confidence.reasoning:
        logger.info(f"    • {reason}")
    
    # Recognize context
    current_data = {
        'volatility': 0.06,  # Outside training range!
        'volume': 5000,
        'regime': 'volatile'
    }
    
    context = awareness.recognize_context(current_data)
    
    logger.info(f"\nCONTEXT RECOGNITION:")
    logger.info(f"  Regime: {context.regime_type}")
    logger.info(f"  Within Training: {context.within_training_distribution}")
    logger.info(f"  Validity: {context.validity.value}")
    logger.info(f"  Recognition Confidence: {context.confidence_in_recognition:.2%}")
    
    if context.warnings:
        logger.info(f"  Warnings:")
        for warning in context.warnings:
            logger.info(f"    ⚠ {warning}")
    
    # Reflect on trade
    trade_data = {
        'trade_id': 'T001',
        'pnl': -100,
        'expected_outcome': 'WIN',
        'confluence_score': 65,
        'stopped_out': True,
        'regime_shift': True
    }
    
    reflection = awareness.reflect_on_trade(trade_data)
    
    logger.info(f"\nTRADE REFLECTION:")
    logger.info(f"  Outcome: {reflection.outcome}")
    logger.info(f"  Expected: {reflection.expected_outcome}")
    logger.info(f"  Accuracy: {reflection.prediction_accuracy:.0%}")
    
    if reflection.what_went_wrong:
        logger.info(f"  What Went Wrong:")
        for item in reflection.what_went_wrong:
            logger.info(f"    • {item}")
    
    if reflection.lessons_learned:
        logger.info(f"  Lessons Learned:")
        for lesson in reflection.lessons_learned:
            logger.info(f"    • {lesson}")
