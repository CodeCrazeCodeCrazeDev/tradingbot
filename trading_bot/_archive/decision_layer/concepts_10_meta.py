"""
Meta-Decision Intelligence (Concepts 91-100)
Decisions about decisions - meta-level reasoning.
"""

import math
import random
import statistics
from collections import deque
from typing import Dict, List, Optional

from .core_types import (
    DecisionConcept, DecisionContext, DecisionResult,
    DecisionCategory, DecisionAction, DecisionUrgency
)


class DecisionConfidenceDecision(DecisionConcept):
    """Concept 91: Decision Confidence - Meta-assess confidence"""
    
    def __init__(self):
        super().__init__(91, "Decision Confidence", DecisionCategory.META)
        self.confidence_history: deque = deque(maxlen=30)
        
    def decide(self, context: DecisionContext) -> DecisionResult:
        # Base signal
        signal = context.trend * 0.4 + context.momentum * 0.4 + context.sentiment * 0.2
        base_conf = abs(signal)
        
        # Meta-confidence factors
        factors = []
        
        # Data quality
        data_quality = 1 - context.volatility * 0.5
        factors.append(('data_quality', data_quality))
        
        # Signal agreement
        agreement = 1 if (context.trend > 0) == (context.momentum > 0) == (context.sentiment > 0) else 0.5
        factors.append(('agreement', agreement))
        
        # Historical calibration
        if len(self.confidence_history) >= 10:
            avg_conf = sum(self.confidence_history) / len(self.confidence_history)
            calibration = min(context.win_rate / avg_conf, 1.5) if avg_conf > 0 else 1.0
        else:
            calibration = 1.0
        factors.append(('calibration', calibration))
        
        # Meta-confidence
        meta_conf = base_conf * sum(f[1] for f in factors) / len(factors)
        self.confidence_history.append(meta_conf)
        
        return self._create_result(self._signal_to_action(signal), meta_conf, DecisionUrgency.NORMAL,
            f"Meta-conf: {meta_conf:.2f}", {'base_conf': base_conf, 'factors': dict(factors)})


class DecisionTimingDecision(DecisionConcept):
    """Concept 92: Decision Timing - When to decide"""
    
    def __init__(self):
        super().__init__(92, "Decision Timing", DecisionCategory.META)
        self.last_decision_time = None
        
    def decide(self, context: DecisionContext) -> DecisionResult:
        signal = context.trend * 0.5 + context.momentum * 0.5
        
        # Should we decide now or wait?
        timing_factors = []
        
        # Market hours
        hour = context.timestamp.hour
        good_hours = 8 <= hour <= 16
        timing_factors.append(('market_hours', 1.0 if good_hours else 0.5))
        
        # Volatility timing
        vol_timing = 1.0 if context.volatility < 0.4 else 0.6
        timing_factors.append(('volatility', vol_timing))
        
        # Signal strength
        signal_strength = 1.0 if abs(signal) > 0.3 else 0.7
        timing_factors.append(('signal_strength', signal_strength))
        
        timing_score = sum(f[1] for f in timing_factors) / len(timing_factors)
        
        if timing_score < 0.7:
            action = DecisionAction.DEFER
            reason = f"Poor timing ({timing_score:.2f})"
        else:
            action = self._signal_to_action(signal)
            reason = f"Good timing ({timing_score:.2f})"
        
        return self._create_result(action, abs(signal) * timing_score, 
            DecisionUrgency.IMMEDIATE if timing_score > 0.9 else DecisionUrgency.NORMAL,
            reason, {'timing_score': timing_score, 'factors': dict(timing_factors)})


class DecisionReversalDecision(DecisionConcept):
    """Concept 93: Decision Reversal - When to change mind"""
    
    def __init__(self):
        super().__init__(93, "Decision Reversal", DecisionCategory.META)
        self.last_decision: Optional[DecisionAction] = None
        self.decision_age = 0
        
    def decide(self, context: DecisionContext) -> DecisionResult:
        signal = context.trend * 0.5 + context.momentum * 0.5
        new_action = self._signal_to_action(signal)
        
        # Should we reverse?
        if self.last_decision is not None:
            self.decision_age += 1
            
            # Reversal cost increases with age
            reversal_cost = min(self.decision_age * 0.05, 0.3)
            
            # Signal must overcome reversal cost
            if new_action != self.last_decision:
                if abs(signal) > reversal_cost + 0.2:
                    action = new_action
                    reason = f"Reversal justified (signal {abs(signal):.2f} > cost {reversal_cost:.2f})"
                    self.last_decision = action
                    self.decision_age = 0
                else:
                    action = self.last_decision
                    reason = f"Maintaining (signal {abs(signal):.2f} < cost {reversal_cost:.2f})"
            else:
                action = new_action
                reason = "Confirming direction"
        else:
            action = new_action
            self.last_decision = action
            self.decision_age = 0
            reason = "Initial decision"
        
        return self._create_result(action, abs(signal), DecisionUrgency.NORMAL, reason,
            {'decision_age': self.decision_age, 'last': str(self.last_decision)})


class DecisionDelegationDecision(DecisionConcept):
    """Concept 94: Decision Delegation - Which system should decide"""
    
    def __init__(self):
        super().__init__(94, "Decision Delegation", DecisionCategory.META)
        
    def decide(self, context: DecisionContext) -> DecisionResult:
        # Determine best system for current conditions
        
        if context.volatility > 0.5:
            delegate_to = "risk_system"
            signal = -context.volatility  # Conservative
            reason = "Delegating to risk system (high vol)"
        elif abs(context.trend) > 0.4:
            delegate_to = "trend_system"
            signal = context.trend
            reason = "Delegating to trend system"
        elif abs(context.momentum) > 0.4:
            delegate_to = "momentum_system"
            signal = context.momentum
            reason = "Delegating to momentum system"
        else:
            delegate_to = "default_system"
            signal = context.trend * 0.5 + context.sentiment * 0.5
            reason = "Using default system"
        
        return self._create_result(self._signal_to_action(signal), abs(signal), DecisionUrgency.NORMAL, reason,
            {'delegate_to': delegate_to, 'signal': signal})


class DecisionAuditDecision(DecisionConcept):
    """Concept 95: Decision Audit - Review past decisions"""
    
    def __init__(self):
        super().__init__(95, "Decision Audit", DecisionCategory.META)
        self.decision_log: deque = deque(maxlen=50)
        
    def decide(self, context: DecisionContext) -> DecisionResult:
        signal = context.trend * 0.5 + context.momentum * 0.5
        
        # Audit past decisions
        if len(self.decision_log) >= 10:
            recent = list(self.decision_log)[-10:]
            
            # Check for patterns
            buy_count = sum(1 for d in recent if d['action'] in ['buy', 'strong_buy'])
            sell_count = sum(1 for d in recent if d['action'] in ['sell', 'strong_sell'])
            
            # Detect bias
            if buy_count > 7:
                bias = "bullish_bias"
                signal *= 0.7  # Reduce bullish signals
            elif sell_count > 7:
                bias = "bearish_bias"
                signal *= 0.7  # Reduce bearish signals
            else:
                bias = "balanced"
        else:
            bias = "insufficient_data"
        
        action = self._signal_to_action(signal)
        
        # Log decision
        self.decision_log.append({'action': action.value, 'signal': signal, 'context_trend': context.trend})
        
        return self._create_result(action, abs(signal), DecisionUrgency.NORMAL,
            f"Audit: {bias}", {'bias': bias, 'log_size': len(self.decision_log)})


class DecisionExplanationDecision(DecisionConcept):
    """Concept 96: Decision Explanation - Generate reasoning"""
    
    def __init__(self):
        super().__init__(96, "Decision Explanation", DecisionCategory.META)
        
    def decide(self, context: DecisionContext) -> DecisionResult:
        # Build explanation
        reasons = []
        
        if context.trend > 0.2:
            reasons.append(f"Bullish trend ({context.trend:.2f})")
        elif context.trend < -0.2:
            reasons.append(f"Bearish trend ({context.trend:.2f})")
        
        if context.momentum > 0.2:
            reasons.append(f"Positive momentum ({context.momentum:.2f})")
        elif context.momentum < -0.2:
            reasons.append(f"Negative momentum ({context.momentum:.2f})")
        
        if context.volatility > 0.4:
            reasons.append(f"High volatility caution ({context.volatility:.2f})")
        
        if context.drawdown > 0.1:
            reasons.append(f"Drawdown protection ({context.drawdown:.1%})")
        
        # Generate signal
        signal = context.trend * 0.4 + context.momentum * 0.4 + context.sentiment * 0.2
        action = self._signal_to_action(signal)
        
        explanation = " | ".join(reasons) if reasons else "No strong signals"
        
        return self._create_result(action, abs(signal), DecisionUrgency.NORMAL, explanation,
            {'reasons_count': len(reasons), 'signal': signal})


class DecisionUncertaintyDecision(DecisionConcept):
    """Concept 97: Decision Uncertainty - Quantify unknowns"""
    
    def __init__(self):
        super().__init__(97, "Decision Uncertainty", DecisionCategory.META)
        
    def decide(self, context: DecisionContext) -> DecisionResult:
        # Quantify uncertainty sources
        uncertainties = {}
        
        # Market uncertainty
        uncertainties['market'] = context.volatility
        
        # Signal uncertainty
        signal_disagreement = abs(context.trend - context.momentum)
        uncertainties['signal'] = signal_disagreement
        
        # Model uncertainty (proxy)
        uncertainties['model'] = 0.2 + context.volatility * 0.3
        
        # Total uncertainty
        total_uncertainty = sum(uncertainties.values()) / len(uncertainties)
        
        signal = context.trend * 0.5 + context.momentum * 0.5
        
        # Adjust for uncertainty
        if total_uncertainty > 0.5:
            action = DecisionAction.HOLD
            reason = f"High uncertainty ({total_uncertainty:.2f})"
            conf = 0.3
        else:
            action = self._signal_to_action(signal)
            reason = f"Acceptable uncertainty ({total_uncertainty:.2f})"
            conf = abs(signal) * (1 - total_uncertainty)
        
        return self._create_result(action, conf, DecisionUrgency.NORMAL, reason,
            {'total_uncertainty': total_uncertainty, 'sources': uncertainties})


class DecisionRobustnessDecision(DecisionConcept):
    """Concept 98: Decision Robustness - Test decision stability"""
    
    def __init__(self):
        super().__init__(98, "Decision Robustness", DecisionCategory.META)
        
    def decide(self, context: DecisionContext) -> DecisionResult:
        # Test decision under perturbations
        base_signal = context.trend * 0.5 + context.momentum * 0.5
        base_action = self._signal_to_action(base_signal)
        
        # Perturb inputs
        perturbations = []
        for _ in range(10):
            perturbed_trend = context.trend + random.gauss(0, 0.1)
            perturbed_momentum = context.momentum + random.gauss(0, 0.1)
            perturbed_signal = perturbed_trend * 0.5 + perturbed_momentum * 0.5
            perturbed_action = self._signal_to_action(perturbed_signal)
            perturbations.append(perturbed_action == base_action)
        
        robustness = sum(perturbations) / len(perturbations)
        
        if robustness < 0.7:
            action = DecisionAction.HOLD
            reason = f"Low robustness ({robustness:.0%})"
        else:
            action = base_action
            reason = f"Robust decision ({robustness:.0%})"
        
        return self._create_result(action, abs(base_signal) * robustness, DecisionUrgency.NORMAL, reason,
            {'robustness': robustness, 'base_signal': base_signal})


class DecisionEvolutionDecision(DecisionConcept):
    """Concept 99: Decision Evolution - Evolve decision rules"""
    
    def __init__(self):
        super().__init__(99, "Decision Evolution", DecisionCategory.META)
        self.generation = 1
        self.rules = {'trend_weight': 0.4, 'momentum_weight': 0.4, 'sentiment_weight': 0.2}
        self.fitness_history: deque = deque(maxlen=20)
        
    def decide(self, context: DecisionContext) -> DecisionResult:
        # Apply current rules
        signal = (self.rules['trend_weight'] * context.trend +
                 self.rules['momentum_weight'] * context.momentum +
                 self.rules['sentiment_weight'] * context.sentiment)
        
        # Track fitness
        fitness = signal * context.trend  # Reward alignment
        self.fitness_history.append(fitness)
        
        # Evolve rules periodically
        if len(self.fitness_history) >= 10:
            avg_fitness = sum(self.fitness_history) / len(self.fitness_history)
            
            if avg_fitness < 0:  # Poor performance
                # Mutate rules
                self.rules['trend_weight'] += random.gauss(0, 0.05)
                self.rules['momentum_weight'] += random.gauss(0, 0.05)
                
                # Normalize
                total = sum(self.rules.values())
                self.rules = {k: max(0.1, v / total) for k, v in self.rules.items()}
                
                self.generation += 1
                self.fitness_history.clear()
        
        return self._create_result(self._signal_to_action(signal), abs(signal), DecisionUrgency.NORMAL,
            f"Gen {self.generation}", {'generation': self.generation, 'rules': self.rules})


class MetaDecisionOrchestratorDecision(DecisionConcept):
    """Concept 100: Meta-Decision Orchestrator - Coordinate all meta-decisions"""
    
    def __init__(self):
        super().__init__(100, "Meta Orchestrator", DecisionCategory.META)
        self.meta_weights = {
            'confidence': 0.2,
            'timing': 0.15,
            'uncertainty': 0.2,
            'robustness': 0.2,
            'explanation': 0.1,
            'evolution': 0.15
        }
        
    def decide(self, context: DecisionContext) -> DecisionResult:
        # Orchestrate meta-level considerations
        
        # Confidence assessment
        signal = context.trend * 0.4 + context.momentum * 0.4 + context.sentiment * 0.2
        base_conf = abs(signal)
        
        # Timing assessment
        timing = 1.0 if 8 <= context.timestamp.hour <= 16 else 0.7
        
        # Uncertainty assessment
        uncertainty = context.volatility
        
        # Robustness (simplified)
        robustness = 1.0 if abs(context.trend - context.momentum) < 0.2 else 0.7
        
        # Meta-score
        meta_score = (
            self.meta_weights['confidence'] * base_conf +
            self.meta_weights['timing'] * timing +
            self.meta_weights['uncertainty'] * (1 - uncertainty) +
            self.meta_weights['robustness'] * robustness
        )
        
        # Final decision
        if meta_score > 0.6:
            action = self._signal_to_action(signal)
            reason = f"Meta-approved ({meta_score:.2f})"
        elif meta_score > 0.4:
            action = self._signal_to_action(signal * 0.5)
            reason = f"Meta-cautious ({meta_score:.2f})"
        else:
            action = DecisionAction.HOLD
            reason = f"Meta-blocked ({meta_score:.2f})"
        
        return self._create_result(action, meta_score, DecisionUrgency.NORMAL, reason,
            {'meta_score': meta_score, 'timing': timing, 'robustness': robustness})


META_CONCEPTS = [
    DecisionConfidenceDecision,
    DecisionTimingDecision,
    DecisionReversalDecision,
    DecisionDelegationDecision,
    DecisionAuditDecision,
    DecisionExplanationDecision,
    DecisionUncertaintyDecision,
    DecisionRobustnessDecision,
    DecisionEvolutionDecision,
    MetaDecisionOrchestratorDecision,
]
