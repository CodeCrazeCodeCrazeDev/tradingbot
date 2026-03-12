"""
Layer 4: Neuro-Symbolic Reasoning
Combines neural pattern recognition with symbolic rule-based logic.
"""

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


@dataclass
class Pattern:
    """Detected pattern from neural layer."""
    name: str
    confidence: float
    features: Dict[str, float] = field(default_factory=dict)


@dataclass
class Rule:
    """Symbolic rule for reasoning."""
    name: str
    condition: str
    action: str
    priority: int = 1


@dataclass
class ReasoningResult:
    """Result of neuro-symbolic reasoning."""
    conclusion: str
    confidence: float
    explanation: str
    patterns_used: List[str] = field(default_factory=list)
    rules_applied: List[str] = field(default_factory=list)


class NeuralLayer:
    """
    Neural Layer - Pattern recognition using neural network concepts.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.patterns: List[Pattern] = []
        logger.info("NeuralLayer initialized")
    
    def extract_patterns(self, data: Dict[str, Any]) -> List[Pattern]:
        """Extract patterns from market data."""
        patterns = []
        
        # Trend pattern
        if 'prices' in data:
            prices = data['prices']
            if len(prices) >= 2:
                trend = (prices[-1] - prices[0]) / prices[0] if prices[0] != 0 else 0
                patterns.append(Pattern(
                    name='trend',
                    confidence=min(abs(trend) * 10, 1.0),
                    features={'direction': 1.0 if trend > 0 else -1.0, 'strength': abs(trend)}
                ))
        
        # Volatility pattern
        if 'volatility' in data:
            vol = data['volatility']
            patterns.append(Pattern(
                name='volatility',
                confidence=0.8,
                features={'level': vol, 'regime': 'high' if vol > 0.02 else 'low'}
            ))
        
        # Momentum pattern
        if 'momentum' in data:
            mom = data['momentum']
            patterns.append(Pattern(
                name='momentum',
                confidence=min(abs(mom), 1.0),
                features={'value': mom, 'direction': 'positive' if mom > 0 else 'negative'}
            ))
        
        self.patterns = patterns
        return patterns
    
    def get_pattern_embedding(self, patterns: List[Pattern]) -> Dict[str, float]:
        """Get combined embedding from patterns."""
        embedding = {}
        for pattern in patterns:
            for key, value in pattern.features.items():
                if isinstance(value, (int, float)):
                    embedding[f"{pattern.name}_{key}"] = value * pattern.confidence
        return embedding


class SymbolicLayer:
    """
    Symbolic Layer - Rule-based reasoning system.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.rules: List[Rule] = self._initialize_rules()
        logger.info("SymbolicLayer initialized with %d rules", len(self.rules))
    
    def _initialize_rules(self) -> List[Rule]:
        """Initialize default trading rules."""
        return [
            Rule("trend_follow", "trend.direction > 0 AND trend.strength > 0.5", "buy", priority=2),
            Rule("trend_follow_short", "trend.direction < 0 AND trend.strength > 0.5", "sell", priority=2),
            Rule("high_volatility_caution", "volatility.level > 0.03", "reduce_size", priority=3),
            Rule("momentum_confirm", "momentum.direction == trend.direction", "increase_confidence", priority=1),
            Rule("momentum_diverge", "momentum.direction != trend.direction", "caution", priority=2),
        ]
    
    def add_rule(self, rule: Rule):
        """Add a new rule to the system."""
        self.rules.append(rule)
    
    def evaluate_rules(self, patterns: List[Pattern]) -> List[Dict[str, Any]]:
        """Evaluate rules against detected patterns."""
        results = []
        pattern_dict = {p.name: p for p in patterns}
        
        for rule in sorted(self.rules, key=lambda r: r.priority, reverse=True):
            # Simple rule evaluation (in production, use proper expression parser)
            triggered = self._evaluate_condition(rule.condition, pattern_dict)
            if triggered:
                results.append({
                    'rule': rule.name,
                    'action': rule.action,
                    'priority': rule.priority
                })
        
        return results
    
    def _evaluate_condition(self, condition: str, patterns: Dict[str, Pattern]) -> bool:
        """Evaluate a rule condition against patterns."""
        try:
            # Simplified evaluation - in production use proper parser
            if 'trend.direction > 0' in condition:
                if 'trend' in patterns:
                    return patterns['trend'].features.get('direction', 0) > 0
            if 'trend.direction < 0' in condition:
                if 'trend' in patterns:
                    return patterns['trend'].features.get('direction', 0) < 0
            if 'volatility.level > 0.03' in condition:
                if 'volatility' in patterns:
                    return patterns['volatility'].features.get('level', 0) > 0.03
        except Exception as e:
            logger.warning(f"Rule evaluation error: {e}")
        return False


class ReasoningEngine:
    """
    Reasoning Engine - Combines neural and symbolic layers.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.neural = NeuralLayer(config)
        self.symbolic = SymbolicLayer(config)
        logger.info("ReasoningEngine initialized")
    
    def reason(self, data: Dict[str, Any]) -> ReasoningResult:
        """Perform neuro-symbolic reasoning on data."""
        # Extract patterns using neural layer
        patterns = self.neural.extract_patterns(data)
        
        # Apply symbolic rules
        rule_results = self.symbolic.evaluate_rules(patterns)
        
        # Combine results
        if not rule_results:
            return ReasoningResult(
                conclusion='hold',
                confidence=0.5,
                explanation='No rules triggered',
                patterns_used=[p.name for p in patterns],
                rules_applied=[]
            )
        
        # Get highest priority action
        top_result = rule_results[0]
        
        # Calculate confidence from pattern confidences
        avg_confidence = sum(p.confidence for p in patterns) / len(patterns) if patterns else 0.5
        
        return ReasoningResult(
            conclusion=top_result['action'],
            confidence=avg_confidence,
            explanation=f"Rule '{top_result['rule']}' triggered with action '{top_result['action']}'",
            patterns_used=[p.name for p in patterns],
            rules_applied=[r['rule'] for r in rule_results]
        )


class NeuroSymbolicSystem:
    """
    Complete Neuro-Symbolic System - Layer 4 of Cognitive Architecture.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.reasoning_engine = ReasoningEngine(config)
        logger.info("NeuroSymbolicSystem initialized")
    
    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process data through neuro-symbolic system."""
        result = self.reasoning_engine.reason(data)
        
        return {
            'conclusion': result.conclusion,
            'confidence': result.confidence,
            'explanation': result.explanation,
            'patterns': result.patterns_used,
            'rules': result.rules_applied
        }
    
    def explain(self, data: Dict[str, Any]) -> str:
        """Generate natural language explanation."""
        result = self.reasoning_engine.reason(data)
        
        explanation_parts = [
            f"Analysis conclusion: {result.conclusion}",
            f"Confidence level: {result.confidence:.1%}",
            f"Patterns detected: {', '.join(result.patterns_used) or 'none'}",
            f"Rules applied: {', '.join(result.rules_applied) or 'none'}",
            f"Reasoning: {result.explanation}"
        ]
        
        return "\n".join(explanation_parts)
