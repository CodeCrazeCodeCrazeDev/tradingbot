"""
Layer 9: Explainability & Trust Interface
Provides natural language explanations and transparency.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class Explanation:
    """Structured explanation of a decision."""
    summary: str
    reasoning_chain: List[str]
    confidence_breakdown: Dict[str, float]
    key_factors: List[str]
    risks: List[str]
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class TrustScore:
    """Trust metrics for a decision."""
    overall_trust: float
    data_quality: float
    model_confidence: float
    historical_accuracy: float
    explanation_clarity: float


class ExplainabilityInterface:
    """
    Provides explanations for trading decisions.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.explanation_history: List[Explanation] = []
        logger.info("ExplainabilityInterface initialized")
    
    def explain_decision(self, decision: Dict[str, Any], 
                        context: Dict[str, Any]) -> Explanation:
        """Generate explanation for a trading decision."""
        # Build reasoning chain
        reasoning_chain = self._build_reasoning_chain(decision, context)
        
        # Identify key factors
        key_factors = self._identify_key_factors(decision, context)
        
        # Identify risks
        risks = self._identify_risks(decision, context)
        
        # Calculate confidence breakdown
        confidence_breakdown = self._calculate_confidence_breakdown(decision, context)
        
        # Generate summary
        summary = self._generate_summary(decision, key_factors, risks)
        
        explanation = Explanation(
            summary=summary,
            reasoning_chain=reasoning_chain,
            confidence_breakdown=confidence_breakdown,
            key_factors=key_factors,
            risks=risks
        )
        
        self.explanation_history.append(explanation)
        return explanation
    
    def _build_reasoning_chain(self, decision: Dict[str, Any], 
                               context: Dict[str, Any]) -> List[str]:
        """Build step-by-step reasoning chain."""
        chain = []
        
        # Market analysis step
        if 'market_state' in context:
            state = context['market_state']
            chain.append(f"1. Market Analysis: Detected {state.get('regime', 'unknown')} regime "
                        f"with {state.get('volatility', 0):.2%} volatility")
        
        # Signal analysis step
        if 'signals' in context:
            signals = context['signals']
            bullish = sum(1 for s in signals if s.get('direction') == 'long')
            bearish = sum(1 for s in signals if s.get('direction') == 'short')
            chain.append(f"2. Signal Analysis: {bullish} bullish signals, {bearish} bearish signals")
        
        # Risk assessment step
        if 'risk_score' in decision:
            chain.append(f"3. Risk Assessment: Risk score {decision['risk_score']:.2f}")
        
        # Decision step
        action = decision.get('action', 'hold')
        confidence = decision.get('confidence', 0.5)
        chain.append(f"4. Decision: {action.upper()} with {confidence:.1%} confidence")
        
        return chain
    
    def _identify_key_factors(self, decision: Dict[str, Any], 
                              context: Dict[str, Any]) -> List[str]:
        """Identify key factors influencing the decision."""
        factors = []
        
        if context.get('trend_strength', 0) > 0.5:
            factors.append(f"Strong trend detected (strength: {context['trend_strength']:.2f})")
        
        if context.get('volatility', 0) > 0.03:
            factors.append(f"High volatility environment ({context['volatility']:.2%})")
        
        if context.get('sentiment', 0) > 0.3:
            factors.append(f"Positive market sentiment ({context['sentiment']:.2f})")
        elif context.get('sentiment', 0) < -0.3:
            factors.append(f"Negative market sentiment ({context['sentiment']:.2f})")
        
        if decision.get('pattern_match'):
            factors.append(f"Pattern detected: {decision['pattern_match']}")
        
        if not factors:
            factors.append("No dominant factors identified")
        
        return factors
    
    def _identify_risks(self, decision: Dict[str, Any], 
                        context: Dict[str, Any]) -> List[str]:
        """Identify risks associated with the decision."""
        risks = []
        
        if context.get('volatility', 0) > 0.05:
            risks.append("High volatility may cause significant price swings")
        
        if decision.get('confidence', 1.0) < 0.5:
            risks.append("Low confidence in signal - consider smaller position")
        
        if context.get('liquidity', 1.0) < 0.3:
            risks.append("Low liquidity may impact execution")
        
        if context.get('correlation_risk', 0) > 0.7:
            risks.append("High correlation with existing positions")
        
        if not risks:
            risks.append("No significant risks identified")
        
        return risks
    
    def _calculate_confidence_breakdown(self, decision: Dict[str, Any], 
                                        context: Dict[str, Any]) -> Dict[str, float]:
        """Calculate confidence breakdown by component."""
        return {
            'technical_analysis': context.get('technical_confidence', 0.5),
            'sentiment_analysis': context.get('sentiment_confidence', 0.5),
            'risk_assessment': 1.0 - decision.get('risk_score', 0.5),
            'pattern_recognition': context.get('pattern_confidence', 0.5),
            'overall': decision.get('confidence', 0.5)
        }
    
    def _generate_summary(self, decision: Dict[str, Any], 
                         key_factors: List[str], 
                         risks: List[str]) -> str:
        """Generate natural language summary."""
        action = decision.get('action', 'hold')
        confidence = decision.get('confidence', 0.5)
        
        if action == 'buy':
            action_text = "LONG position"
        elif action == 'sell':
            action_text = "SHORT position"
        else:
            action_text = "HOLD (no action)"
        
        confidence_text = "high" if confidence > 0.7 else "moderate" if confidence > 0.4 else "low"
        
        summary = f"Recommendation: {action_text} with {confidence_text} confidence ({confidence:.1%}). "
        
        if key_factors:
            summary += f"Key factor: {key_factors[0]}. "
        
        if risks and risks[0] != "No significant risks identified":
            summary += f"Primary risk: {risks[0]}"
        
        return summary


class NaturalLanguageGenerator:
    """
    Generates natural language explanations.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.templates = self._load_templates()
        logger.info("NaturalLanguageGenerator initialized")
    
    def _load_templates(self) -> Dict[str, str]:
        """Load explanation templates."""
        return {
            'bullish': "The analysis suggests a bullish outlook. {reasons}",
            'bearish': "The analysis suggests a bearish outlook. {reasons}",
            'neutral': "The analysis is neutral with no clear directional bias. {reasons}",
            'high_confidence': "This signal has high confidence ({confidence:.1%}) based on {factors}.",
            'low_confidence': "This signal has lower confidence ({confidence:.1%}). Consider {caution}.",
            'risk_warning': "Risk Alert: {risk_description}. Consider {mitigation}."
        }
    
    def generate(self, template_key: str, **kwargs) -> str:
        """Generate text from template."""
        template = self.templates.get(template_key, "{}")
        try:
            return template.format(**kwargs)
        except KeyError:
            return template
    
    def explain_signal(self, signal: Dict[str, Any]) -> str:
        """Generate explanation for a trading signal."""
        direction = signal.get('direction', 'neutral')
        confidence = signal.get('confidence', 0.5)
        reasons = signal.get('reasons', ['market conditions'])
        
        # Select template based on direction
        if direction == 'long':
            base = self.generate('bullish', reasons=', '.join(reasons))
        elif direction == 'short':
            base = self.generate('bearish', reasons=', '.join(reasons))
        else:
            base = self.generate('neutral', reasons=', '.join(reasons))
        
        # Add confidence context
        if confidence > 0.7:
            confidence_text = self.generate('high_confidence', 
                                           confidence=confidence, 
                                           factors='multiple confirming indicators')
        else:
            confidence_text = self.generate('low_confidence', 
                                           confidence=confidence, 
                                           caution='smaller position size')
        
        return f"{base} {confidence_text}"
    
    def explain_risk(self, risk: Dict[str, Any]) -> str:
        """Generate risk explanation."""
        return self.generate('risk_warning',
                           risk_description=risk.get('description', 'Unknown risk'),
                           mitigation=risk.get('mitigation', 'reducing position size'))


class TrustMetrics:
    """
    Calculates and tracks trust metrics.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.accuracy_history: List[bool] = []
        self.prediction_history: List[Dict[str, Any]] = []
        logger.info("TrustMetrics initialized")
    
    def calculate_trust(self, decision: Dict[str, Any], 
                       context: Dict[str, Any]) -> TrustScore:
        """Calculate trust score for a decision."""
        # Data quality score
        data_quality = self._assess_data_quality(context)
        
        # Model confidence
        model_confidence = decision.get('confidence', 0.5)
        
        # Historical accuracy
        historical_accuracy = self._calculate_historical_accuracy()
        
        # Explanation clarity
        explanation_clarity = self._assess_explanation_clarity(decision)
        
        # Overall trust (weighted average)
        overall = (
            0.25 * data_quality +
            0.30 * model_confidence +
            0.30 * historical_accuracy +
            0.15 * explanation_clarity
        )
        
        return TrustScore(
            overall_trust=overall,
            data_quality=data_quality,
            model_confidence=model_confidence,
            historical_accuracy=historical_accuracy,
            explanation_clarity=explanation_clarity
        )
    
    def _assess_data_quality(self, context: Dict[str, Any]) -> float:
        """Assess quality of input data."""
        quality = 1.0
        
        # Check for missing data
        if not context.get('prices'):
            quality -= 0.3
        if not context.get('volume'):
            quality -= 0.1
        
        # Check for stale data
        if context.get('data_age_minutes', 0) > 5:
            quality -= 0.2
        
        return max(0.0, quality)
    
    def _calculate_historical_accuracy(self) -> float:
        """Calculate historical prediction accuracy."""
        if not self.accuracy_history:
            return 0.5  # Default when no history
        
        recent = self.accuracy_history[-100:]  # Last 100 predictions
        return sum(recent) / len(recent)
    
    def _assess_explanation_clarity(self, decision: Dict[str, Any]) -> float:
        """Assess clarity of explanation."""
        clarity = 0.5
        
        if decision.get('reasoning'):
            clarity += 0.2
        if decision.get('key_factors'):
            clarity += 0.15
        if decision.get('risks'):
            clarity += 0.15
        
        return min(1.0, clarity)
    
    def record_outcome(self, prediction: Dict[str, Any], actual_outcome: bool):
        """Record prediction outcome for accuracy tracking."""
        self.accuracy_history.append(actual_outcome)
        self.prediction_history.append({
            'prediction': prediction,
            'correct': actual_outcome,
            'timestamp': datetime.now()
        })
        
        # Keep history bounded
        if len(self.accuracy_history) > 1000:
            self.accuracy_history = self.accuracy_history[-1000:]
        if len(self.prediction_history) > 1000:
            self.prediction_history = self.prediction_history[-1000:]
    
    def get_trust_trend(self) -> str:
        """Get trend in trust metrics."""
        if len(self.accuracy_history) < 20:
            return 'insufficient_data'
        
        recent = self.accuracy_history[-20:]
        older = self.accuracy_history[-40:-20] if len(self.accuracy_history) >= 40 else self.accuracy_history[:20]
        
        recent_acc = sum(recent) / len(recent)
        older_acc = sum(older) / len(older)
        
        if recent_acc > older_acc + 0.05:
            return 'improving'
        elif recent_acc < older_acc - 0.05:
            return 'declining'
        return 'stable'
