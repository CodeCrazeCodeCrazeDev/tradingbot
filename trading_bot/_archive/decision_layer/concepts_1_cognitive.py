"""
Cognitive Decision Patterns (Concepts 1-10)
Human-like reasoning approaches to trading decisions.
"""

import math
import random
import statistics
from collections import deque
from typing import Dict, List

from .core_types import (
    DecisionConcept, DecisionContext, DecisionResult,
    DecisionCategory, DecisionAction, DecisionUrgency
)


class DualProcessDecision(DecisionConcept):
    """Concept 1: Dual Process Theory - Fast intuitive + slow analytical thinking"""
    
    def __init__(self):
        super().__init__(1, "Dual Process Theory", DecisionCategory.COGNITIVE)
        
    def decide(self, context: DecisionContext) -> DecisionResult:
        system1 = context.trend * 0.4 + context.momentum * 0.4 + context.sentiment * 0.2
        vol_factor = 1.0 - min(context.volatility * 2, 0.5)
        system2 = system1 * vol_factor * (1 - context.drawdown * 2)
        uncertainty = context.volatility
        combined = system1 * (1 - uncertainty) + system2 * uncertainty
        
        return self._create_result(
            action=self._signal_to_action(combined),
            confidence=abs(combined) * (1 - uncertainty * 0.5),
            urgency=DecisionUrgency.NORMAL,
            reasoning=f"S1:{system1:.2f} S2:{system2:.2f}",
            factors={'system1': system1, 'system2': system2, 'uncertainty': uncertainty}
        )


class RecognitionPrimedDecision(DecisionConcept):
    """Concept 2: Recognition-Primed Decision - Pattern matching from experience"""
    
    def __init__(self):
        super().__init__(2, "Recognition-Primed", DecisionCategory.COGNITIVE)
        self.patterns: List[Dict] = []
        
    def decide(self, context: DecisionContext) -> DecisionResult:
        current = {'trend': round(context.trend, 1), 'momentum': round(context.momentum, 1), 'regime': context.regime}
        best_sim, best_match = 0.0, None
        
        for p in self.patterns[-50:]:
            sim = 0.4 * (1 - abs(current['trend'] - p['trend'])) + 0.3 * (1 - abs(current['momentum'] - p['momentum']))
            if current['regime'] == p.get('regime'): sim += 0.3
            if sim > best_sim: best_sim, best_match = sim, p
        
        self.patterns.append({**current, 'action': DecisionAction.HOLD})
        
        if best_match and best_sim > 0.7:
            return self._create_result(best_match.get('action', DecisionAction.HOLD), best_sim * 0.8, 
                DecisionUrgency.HIGH, f"Pattern match {best_sim:.0%}", {'similarity': best_sim})
        return self._create_result(DecisionAction.HOLD, 0.3, DecisionUrgency.LOW, "No pattern", {'similarity': best_sim})


class NaturalisticDecision(DecisionConcept):
    """Concept 3: Naturalistic Decision Making - Situational awareness"""
    
    def __init__(self):
        super().__init__(3, "Naturalistic Decision", DecisionCategory.COGNITIVE)
        
    def decide(self, context: DecisionContext) -> DecisionResult:
        score = 0.3 if (context.trend > 0 and context.momentum > 0) else (-0.3 if context.trend < 0 and context.momentum < 0 else 0)
        score *= 1.2 if context.volatility < 0.2 else (0.5 if context.volatility > 0.5 else 1.0)
        score *= (0.5 + context.win_rate)
        
        return self._create_result(self._signal_to_action(score), min(abs(score), 1.0), DecisionUrgency.NORMAL,
            f"Situation score: {score:.2f}", {'score': score, 'volatility': context.volatility})


class AnalogicalReasoningDecision(DecisionConcept):
    """Concept 4: Analogical Reasoning - Historical market analogies"""
    
    def __init__(self):
        super().__init__(4, "Analogical Reasoning", DecisionCategory.COGNITIVE)
        self.analogies = [
            {'name': '2008 Crisis', 'vol': 0.8, 'trend': -0.9, 'outcome': -0.7},
            {'name': 'COVID Crash', 'vol': 0.9, 'trend': -0.8, 'outcome': 0.5},
            {'name': 'Bull Run', 'vol': 0.4, 'trend': 0.8, 'outcome': 0.6},
        ]
        
    def decide(self, context: DecisionContext) -> DecisionResult:
        best = max(self.analogies, key=lambda a: 1 - abs(a['vol'] - context.volatility) * 0.5 - abs(a['trend'] - context.trend) * 0.5)
        sim = 1 - abs(best['vol'] - context.volatility) * 0.5 - abs(best['trend'] - context.trend) * 0.5
        action = DecisionAction.BUY if best['outcome'] > 0.2 else (DecisionAction.SELL if best['outcome'] < -0.2 else DecisionAction.HOLD)
        
        return self._create_result(action, sim * 0.7, DecisionUrgency.NORMAL, f"Like {best['name']}", {'analogy': best['name'], 'similarity': sim})


class CounterfactualDecision(DecisionConcept):
    """Concept 5: Counterfactual Thinking - What-if scenario analysis"""
    
    def __init__(self):
        super().__init__(5, "Counterfactual Thinking", DecisionCategory.COGNITIVE)
        
    def decide(self, context: DecisionContext) -> DecisionResult:
        base = context.trend * 0.5 + context.momentum * 0.3 + context.sentiment * 0.2
        scenarios = [-context.trend * 0.5, context.trend * (1 - context.volatility * 2), context.trend * (1 - abs(context.sentiment))]
        robust = all(s > 0 for s in scenarios) and base > 0 or all(s < 0 for s in scenarios) and base < 0
        
        if robust:
            action = DecisionAction.BUY if base > 0 else DecisionAction.SELL
            conf = min(scenarios) * 0.8 if base > 0 else abs(max(scenarios)) * 0.8
        else:
            action, conf = DecisionAction.HOLD, 0.4
            
        return self._create_result(action, abs(conf), DecisionUrgency.NORMAL, 
            "Robust" if robust else "Not robust", {'base': base, 'robust': robust})


class MetacognitiveDecision(DecisionConcept):
    """Concept 6: Metacognitive Monitoring - Bias detection"""
    
    def __init__(self):
        super().__init__(6, "Metacognitive", DecisionCategory.COGNITIVE)
        self.recent: deque = deque(maxlen=20)
        
    def decide(self, context: DecisionContext) -> DecisionResult:
        signal = context.trend * 0.4 + context.momentum * 0.4 + context.sentiment * 0.2
        adj = 1.0
        biases = []
        
        if len(self.recent) >= 5:
            buys = sum(1 for d in self.recent if 'buy' in d.action.value)
            if buys > 4 or buys < 1: biases.append('recency'); adj *= 0.8
        if abs(signal) > 0.8: biases.append('overconfidence'); adj *= 0.9
        
        result = self._create_result(self._signal_to_action(signal * adj), abs(signal) * adj, DecisionUrgency.NORMAL,
            f"Biases: {biases}" if biases else "No biases", {'adjustment': adj, 'biases': len(biases)})
        self.recent.append(result)
        return result


class HeuristicDecision(DecisionConcept):
    """Concept 7: Heuristic-Based Decision - Simple rules of thumb"""
    
    def __init__(self):
        super().__init__(7, "Heuristic", DecisionCategory.COGNITIVE)
        
    def decide(self, context: DecisionContext) -> DecisionResult:
        signals = []
        signals.append(1 if context.trend > 0.3 else (-1 if context.trend < -0.3 else 0))
        signals.append(1 if context.momentum > 0.2 and context.trend > 0 else (-1 if context.momentum < -0.2 and context.trend < 0 else 0))
        signals.append(0 if context.volatility > 0.5 else signals[0])
        signals.append(-0.5 if context.drawdown > 0.1 else 0)
        
        total = sum(signals) / len(signals)
        return self._create_result(self._signal_to_action(total), abs(total), DecisionUrgency.HIGH,
            f"Heuristic: {total:.2f}", {'total': total})


class IntuitionDecision(DecisionConcept):
    """Concept 8: Intuition-Based Decision - Expert gut feeling"""
    
    def __init__(self):
        super().__init__(8, "Intuition", DecisionCategory.COGNITIVE)
        
    def decide(self, context: DecisionContext) -> DecisionResult:
        alignment = context.trend * context.momentum
        score = 0.3 * (1 if context.trend > 0 else -1) if alignment > 0.2 else 0
        if context.volatility > 0.3 and abs(context.sentiment) < 0.2: score *= 0.5
        score *= (0.5 + context.win_rate * 0.5)
        
        return self._create_result(self._signal_to_action(score), min(abs(score) + 0.2, 0.9), DecisionUrgency.HIGH,
            f"Intuition: {score:.2f}", {'alignment': alignment, 'score': score})


class SatisficingDecision(DecisionConcept):
    """Concept 9: Satisficing - First acceptable option"""
    
    def __init__(self):
        super().__init__(9, "Satisficing", DecisionCategory.COGNITIVE)
        
    def decide(self, context: DecisionContext) -> DecisionResult:
        if context.trend > 0.2 and context.momentum > 0:
            return self._create_result(DecisionAction.BUY, context.trend * 0.8, DecisionUrgency.NORMAL, "Buy satisfies", {'threshold': 0.2})
        if context.trend < -0.2 and context.momentum < 0:
            return self._create_result(DecisionAction.SELL, abs(context.trend) * 0.8, DecisionUrgency.NORMAL, "Sell satisfies", {'threshold': 0.2})
        return self._create_result(DecisionAction.HOLD, 0.5, DecisionUrgency.LOW, "Hold default", {'threshold': 0.2})


class ElaborationLikelihoodDecision(DecisionConcept):
    """Concept 10: Elaboration Likelihood - Central vs peripheral processing"""
    
    def __init__(self):
        super().__init__(10, "Elaboration Likelihood", DecisionCategory.COGNITIVE)
        
    def decide(self, context: DecisionContext) -> DecisionResult:
        el = (1.0 - context.volatility) * context.win_rate
        if el > 0.5:
            signal = context.trend * 0.3 + context.momentum * 0.25 + context.sentiment * 0.15 + (1 - context.volatility) * 0.15 + (1 - context.drawdown) * 0.15
            route = "central"
        else:
            signal = context.trend * 0.7 + context.sentiment * 0.3
            route = "peripheral"
            
        return self._create_result(self._signal_to_action(signal), abs(signal) * (0.9 if route == "central" else 0.7),
            DecisionUrgency.NORMAL if route == "central" else DecisionUrgency.HIGH, f"{route} route", {'el': el, 'route': route})


# Export all concepts
COGNITIVE_CONCEPTS = [
    DualProcessDecision,
    RecognitionPrimedDecision,
    NaturalisticDecision,
    AnalogicalReasoningDecision,
    CounterfactualDecision,
    MetacognitiveDecision,
    HeuristicDecision,
    IntuitionDecision,
    SatisficingDecision,
    ElaborationLikelihoodDecision,
]
