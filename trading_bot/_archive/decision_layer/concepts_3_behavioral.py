"""
Behavioral Finance Decisions (Concepts 21-30)
Psychology-based approaches to trading decisions.
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


class LossAversionDecision(DecisionConcept):
    """Concept 21: Loss Aversion - Weigh losses more heavily"""
    
    def __init__(self):
        super().__init__(21, "Loss Aversion", DecisionCategory.BEHAVIORAL)
        self.loss_mult = 2.5
        
    def decide(self, context: DecisionContext) -> DecisionResult:
        gain = max(0, context.trend * 0.03)
        loss = max(0, -context.trend * 0.03) + context.volatility * 0.02
        adjusted = gain - self.loss_mult * loss
        if context.drawdown > 0.05: adjusted *= (1 - context.drawdown)
        
        action = DecisionAction.BUY if adjusted > 0.02 else (DecisionAction.WEAK_BUY if adjusted > 0.005 else
            (DecisionAction.HOLD if adjusted > -0.005 else (DecisionAction.WEAK_SELL if adjusted > -0.02 else DecisionAction.SELL)))
        
        return self._create_result(action, min(abs(adjusted) * 20, 0.9), DecisionUrgency.NORMAL,
            f"Loss-adjusted: {adjusted:.4f}", {'gain': gain, 'loss': loss, 'adjusted': adjusted})


class AnchoringDecision(DecisionConcept):
    """Concept 22: Anchoring Awareness - Detect price anchoring"""
    
    def __init__(self):
        super().__init__(22, "Anchoring Awareness", DecisionCategory.BEHAVIORAL)
        self.prices: deque = deque(maxlen=20)
        
    def decide(self, context: DecisionContext) -> DecisionResult:
        self.prices.append(context.price)
        if len(self.prices) < 5:
            return self._create_result(DecisionAction.HOLD, 0.3, DecisionUrgency.LOW, "Need history", {'history': len(self.prices)})
        
        high, low, avg = max(self.prices), min(self.prices), statistics.mean(self.prices)
        dist_high = (context.price - high) / high
        dist_low = (context.price - low) / low
        
        if abs(dist_high) < 0.02:
            action, reason = DecisionAction.WEAK_SELL, "Near high anchor"
        elif abs(dist_low) < 0.02:
            action, reason = DecisionAction.WEAK_BUY, "Near low anchor"
        else:
            action = DecisionAction.BUY if context.trend > 0.2 else (DecisionAction.SELL if context.trend < -0.2 else DecisionAction.HOLD)
            reason = "No anchor effect"
            
        return self._create_result(action, 0.6, DecisionUrgency.NORMAL, reason, {'dist_high': dist_high, 'dist_low': dist_low})


class HerdingDecision(DecisionConcept):
    """Concept 23: Herding Behavior - Follow or fade the crowd"""
    
    def __init__(self):
        super().__init__(23, "Herding Behavior", DecisionCategory.BEHAVIORAL)
        
    def decide(self, context: DecisionContext) -> DecisionResult:
        herd_signal = context.sentiment * 0.6 + context.momentum * 0.4
        herd_strength = abs(herd_signal)
        
        if herd_strength > 0.7:  # Strong herd - consider fading
            action = DecisionAction.WEAK_SELL if herd_signal > 0 else DecisionAction.WEAK_BUY
            reason = "Fading extreme herd"
            conf = 0.5
        elif herd_strength > 0.3:  # Moderate herd - follow cautiously
            action = DecisionAction.WEAK_BUY if herd_signal > 0 else DecisionAction.WEAK_SELL
            reason = "Following moderate herd"
            conf = 0.6
        else:
            action = DecisionAction.HOLD
            reason = "No clear herd"
            conf = 0.4
            
        return self._create_result(action, conf, DecisionUrgency.NORMAL, reason, {'herd_signal': herd_signal, 'strength': herd_strength})


class OverconfidenceDecision(DecisionConcept):
    """Concept 24: Overconfidence Correction - Adjust for overconfidence bias"""
    
    def __init__(self):
        super().__init__(24, "Overconfidence Correction", DecisionCategory.BEHAVIORAL)
        self.predictions: deque = deque(maxlen=50)
        
    def decide(self, context: DecisionContext) -> DecisionResult:
        raw_signal = context.trend * 0.5 + context.momentum * 0.3 + context.sentiment * 0.2
        raw_conf = abs(raw_signal)
        
        # Calibration factor based on past accuracy
        if len(self.predictions) >= 10:
            accuracy = sum(1 for p in self.predictions if p['correct']) / len(self.predictions)
            calibration = accuracy / 0.7  # Assume 70% target
        else:
            calibration = 0.8  # Default conservative
        
        adjusted_conf = raw_conf * min(calibration, 1.0)
        self.predictions.append({'signal': raw_signal, 'conf': raw_conf, 'correct': random.random() < 0.5 + context.trend * 0.2})
        
        return self._create_result(self._signal_to_action(raw_signal), adjusted_conf, DecisionUrgency.NORMAL,
            f"Calibrated conf: {adjusted_conf:.2f}", {'raw_conf': raw_conf, 'calibration': calibration})


class DispositionEffectDecision(DecisionConcept):
    """Concept 25: Disposition Effect - Avoid selling winners too early"""
    
    def __init__(self):
        super().__init__(25, "Disposition Effect", DecisionCategory.BEHAVIORAL)
        
    def decide(self, context: DecisionContext) -> DecisionResult:
        # If in profit, tendency to sell too early
        # If in loss, tendency to hold too long
        position_pnl = context.current_position * context.trend * 0.1  # Simulated P&L
        
        if position_pnl > 0:  # In profit
            # Counter disposition: let winners run
            if context.trend > 0 and context.momentum > 0:
                action = DecisionAction.HOLD
                reason = "Let winner run"
            else:
                action = DecisionAction.WEAK_SELL
                reason = "Take profit on weakening"
        elif position_pnl < 0:  # In loss
            # Counter disposition: cut losses
            if context.trend < 0 and context.momentum < 0:
                action = DecisionAction.SELL
                reason = "Cut loss early"
            else:
                action = DecisionAction.HOLD
                reason = "Hold - trend improving"
        else:
            action = self._signal_to_action(context.trend)
            reason = "No position bias"
            
        return self._create_result(action, 0.6, DecisionUrgency.NORMAL, reason, {'position_pnl': position_pnl})


class MentalAccountingDecision(DecisionConcept):
    """Concept 26: Mental Accounting - Treat all money equally"""
    
    def __init__(self):
        super().__init__(26, "Mental Accounting", DecisionCategory.BEHAVIORAL)
        
    def decide(self, context: DecisionContext) -> DecisionResult:
        # Don't treat "house money" differently
        total_value = context.portfolio_value
        risk_per_trade = 0.02 * total_value  # 2% risk regardless of source
        
        # Signal based on fundamentals, not mental accounts
        signal = context.trend * 0.4 + context.momentum * 0.3 + (1 - context.volatility) * 0.3
        
        # Position size should be consistent
        position_pct = 0.1 if abs(signal) > 0.5 else (0.05 if abs(signal) > 0.2 else 0.02)
        
        action = self._signal_to_action(signal)
        return self._create_result(action, abs(signal), DecisionUrgency.NORMAL,
            f"Unified accounting: {position_pct:.0%} position", {'signal': signal, 'position_pct': position_pct})


class RegretAversionDecision(DecisionConcept):
    """Concept 27: Regret Aversion - Minimize potential regret"""
    
    def __init__(self):
        super().__init__(27, "Regret Aversion", DecisionCategory.BEHAVIORAL)
        
    def decide(self, context: DecisionContext) -> DecisionResult:
        # Regret of omission (not acting) vs commission (acting)
        signal = context.trend * 0.5 + context.momentum * 0.5
        
        # Strong signal = high regret of not acting
        regret_omission = abs(signal) * context.volatility * 2
        # Acting in uncertain market = high regret of commission
        regret_commission = context.volatility * (1 - abs(signal))
        
        if regret_omission > regret_commission + 0.1:
            action = DecisionAction.BUY if signal > 0 else DecisionAction.SELL
            reason = "Act to avoid omission regret"
        elif regret_commission > regret_omission + 0.1:
            action = DecisionAction.HOLD
            reason = "Hold to avoid commission regret"
        else:
            action = DecisionAction.WEAK_BUY if signal > 0.2 else (DecisionAction.WEAK_SELL if signal < -0.2 else DecisionAction.HOLD)
            reason = "Balanced regret"
            
        return self._create_result(action, 0.6, DecisionUrgency.NORMAL, reason,
            {'regret_omission': regret_omission, 'regret_commission': regret_commission})


class ConfirmationBiasDecision(DecisionConcept):
    """Concept 28: Confirmation Bias Correction - Seek disconfirming evidence"""
    
    def __init__(self):
        super().__init__(28, "Confirmation Bias", DecisionCategory.BEHAVIORAL)
        
    def decide(self, context: DecisionContext) -> DecisionResult:
        # Initial hypothesis based on trend
        hypothesis = "bullish" if context.trend > 0 else "bearish"
        
        # Actively seek disconfirming evidence
        disconfirming = []
        if hypothesis == "bullish":
            if context.sentiment < 0: disconfirming.append("negative sentiment")
            if context.volatility > 0.5: disconfirming.append("high volatility")
            if context.drawdown > 0.1: disconfirming.append("in drawdown")
        else:
            if context.sentiment > 0: disconfirming.append("positive sentiment")
            if context.momentum > 0: disconfirming.append("positive momentum")
        
        # Adjust confidence based on disconfirming evidence
        conf_penalty = len(disconfirming) * 0.15
        adjusted_conf = max(0.2, abs(context.trend) - conf_penalty)
        
        if len(disconfirming) >= 2:
            action = DecisionAction.HOLD
            reason = f"Disconfirming: {disconfirming}"
        else:
            action = DecisionAction.BUY if hypothesis == "bullish" else DecisionAction.SELL
            reason = f"Hypothesis confirmed despite {disconfirming}"
            
        return self._create_result(action, adjusted_conf, DecisionUrgency.NORMAL, reason,
            {'hypothesis': hypothesis, 'disconfirming': len(disconfirming)})


class AvailabilityHeuristicDecision(DecisionConcept):
    """Concept 29: Availability Heuristic - Don't overweight recent events"""
    
    def __init__(self):
        super().__init__(29, "Availability Heuristic", DecisionCategory.BEHAVIORAL)
        self.events: deque = deque(maxlen=30)
        
    def decide(self, context: DecisionContext) -> DecisionResult:
        # Record current "event"
        event = {'trend': context.trend, 'vol': context.volatility, 'time': context.timestamp}
        self.events.append(event)
        
        if len(self.events) < 10:
            return self._create_result(DecisionAction.HOLD, 0.3, DecisionUrgency.LOW, "Building history", {'events': len(self.events)})
        
        # Compare recent vs historical
        recent = list(self.events)[-5:]
        historical = list(self.events)[:-5]
        
        recent_avg_trend = statistics.mean(e['trend'] for e in recent)
        hist_avg_trend = statistics.mean(e['trend'] for e in historical)
        
        # If recent differs significantly from history, be cautious
        divergence = abs(recent_avg_trend - hist_avg_trend)
        
        if divergence > 0.3:
            # Recent events may be overweighted - use historical
            signal = hist_avg_trend * 0.6 + recent_avg_trend * 0.4
            reason = "Correcting for availability bias"
        else:
            signal = recent_avg_trend
            reason = "Recent consistent with history"
            
        return self._create_result(self._signal_to_action(signal), 0.6, DecisionUrgency.NORMAL, reason,
            {'recent_trend': recent_avg_trend, 'hist_trend': hist_avg_trend, 'divergence': divergence})


class StatusQuoBiasDecision(DecisionConcept):
    """Concept 30: Status Quo Bias - Overcome inertia when appropriate"""
    
    def __init__(self):
        super().__init__(30, "Status Quo Bias", DecisionCategory.BEHAVIORAL)
        self.last_action = DecisionAction.HOLD
        
    def decide(self, context: DecisionContext) -> DecisionResult:
        signal = context.trend * 0.4 + context.momentum * 0.4 + context.sentiment * 0.2
        suggested = self._signal_to_action(signal)
        
        # Calculate switching cost (psychological)
        switching_cost = 0.1 if self.last_action != suggested else 0
        
        # Only switch if benefit exceeds cost
        benefit = abs(signal)
        
        if benefit > switching_cost + 0.2:
            action = suggested
            reason = f"Benefit ({benefit:.2f}) > switching cost"
            self.last_action = action
        else:
            action = self.last_action
            reason = f"Maintaining status quo (benefit {benefit:.2f} < threshold)"
            
        return self._create_result(action, benefit, DecisionUrgency.NORMAL, reason,
            {'signal': signal, 'switching_cost': switching_cost, 'benefit': benefit})


BEHAVIORAL_CONCEPTS = [
    LossAversionDecision,
    AnchoringDecision,
    HerdingDecision,
    OverconfidenceDecision,
    DispositionEffectDecision,
    MentalAccountingDecision,
    RegretAversionDecision,
    ConfirmationBiasDecision,
    AvailabilityHeuristicDecision,
    StatusQuoBiasDecision,
]
