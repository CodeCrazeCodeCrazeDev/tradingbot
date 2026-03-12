"""
Multi-Agent Decision Systems (Concepts 81-90)
Ensemble and multi-agent approaches to trading decisions.
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


class VotingEnsembleDecision(DecisionConcept):
    """Concept 81: Voting Ensemble - Democratic decision making"""
    
    def __init__(self):
        super().__init__(81, "Voting Ensemble", DecisionCategory.MULTI_AGENT)
        
    def decide(self, context: DecisionContext) -> DecisionResult:
        # Multiple "voters"
        votes = []
        
        # Trend voter
        if context.trend > 0.2: votes.append('buy')
        elif context.trend < -0.2: votes.append('sell')
        else: votes.append('hold')
        
        # Momentum voter
        if context.momentum > 0.2: votes.append('buy')
        elif context.momentum < -0.2: votes.append('sell')
        else: votes.append('hold')
        
        # Sentiment voter
        if context.sentiment > 0.2: votes.append('buy')
        elif context.sentiment < -0.2: votes.append('sell')
        else: votes.append('hold')
        
        # Volatility voter (contrarian in high vol)
        if context.volatility > 0.4: votes.append('hold')
        else: votes.append(votes[0] if votes else 'hold')
        
        # Risk voter
        if context.drawdown > 0.1: votes.append('hold')
        else: votes.append(votes[0] if votes else 'hold')
        
        # Count votes
        buy_votes = votes.count('buy')
        sell_votes = votes.count('sell')
        hold_votes = votes.count('hold')
        
        if buy_votes > sell_votes and buy_votes > hold_votes:
            action = DecisionAction.BUY
            consensus = buy_votes / len(votes)
        elif sell_votes > buy_votes and sell_votes > hold_votes:
            action = DecisionAction.SELL
            consensus = sell_votes / len(votes)
        else:
            action = DecisionAction.HOLD
            consensus = hold_votes / len(votes)
        
        return self._create_result(action, consensus, DecisionUrgency.NORMAL,
            f"Votes: B{buy_votes} S{sell_votes} H{hold_votes}", {'buy': buy_votes, 'sell': sell_votes, 'hold': hold_votes})


class WeightedExpertsDecision(DecisionConcept):
    """Concept 82: Weighted Experts - Expert opinions with weights"""
    
    def __init__(self):
        super().__init__(82, "Weighted Experts", DecisionCategory.MULTI_AGENT)
        self.expert_weights = {'technical': 0.3, 'fundamental': 0.25, 'sentiment': 0.25, 'risk': 0.2}
        self.expert_accuracy: Dict[str, deque] = {k: deque(maxlen=20) for k in self.expert_weights}
        
    def decide(self, context: DecisionContext) -> DecisionResult:
        # Expert opinions
        opinions = {
            'technical': context.trend * 0.6 + context.momentum * 0.4,
            'fundamental': context.trend * 0.8,
            'sentiment': context.sentiment,
            'risk': (1 - context.volatility - context.drawdown) * context.trend
        }
        
        # Weighted combination
        signal = sum(self.expert_weights[e] * opinions[e] for e in opinions)
        
        # Update weights based on accuracy
        for expert, opinion in opinions.items():
            correct = (opinion > 0 and context.trend > 0) or (opinion < 0 and context.trend < 0)
            self.expert_accuracy[expert].append(1 if correct else 0)
            
            if len(self.expert_accuracy[expert]) >= 5:
                acc = sum(self.expert_accuracy[expert]) / len(self.expert_accuracy[expert])
                self.expert_weights[expert] = max(0.1, acc)
        
        # Normalize
        total = sum(self.expert_weights.values())
        self.expert_weights = {k: v / total for k, v in self.expert_weights.items()}
        
        return self._create_result(self._signal_to_action(signal), abs(signal), DecisionUrgency.NORMAL,
            f"Expert signal: {signal:.3f}", {'opinions': opinions, 'weights': self.expert_weights})


class DebateDecision(DecisionConcept):
    """Concept 83: Agent Debate - Bulls vs Bears debate"""
    
    def __init__(self):
        super().__init__(83, "Agent Debate", DecisionCategory.MULTI_AGENT)
        
    def decide(self, context: DecisionContext) -> DecisionResult:
        # Bull arguments
        bull_args = []
        if context.trend > 0: bull_args.append(('trend', context.trend))
        if context.momentum > 0: bull_args.append(('momentum', context.momentum))
        if context.sentiment > 0: bull_args.append(('sentiment', context.sentiment))
        
        # Bear arguments
        bear_args = []
        if context.trend < 0: bear_args.append(('trend', abs(context.trend)))
        if context.momentum < 0: bear_args.append(('momentum', abs(context.momentum)))
        if context.sentiment < 0: bear_args.append(('sentiment', abs(context.sentiment)))
        if context.volatility > 0.3: bear_args.append(('volatility', context.volatility))
        if context.drawdown > 0.05: bear_args.append(('drawdown', context.drawdown))
        
        # Score arguments
        bull_score = sum(arg[1] for arg in bull_args)
        bear_score = sum(arg[1] for arg in bear_args)
        
        if bull_score > bear_score * 1.2:
            action = DecisionAction.BUY
            winner = "Bulls"
        elif bear_score > bull_score * 1.2:
            action = DecisionAction.SELL
            winner = "Bears"
        else:
            action = DecisionAction.HOLD
            winner = "Tie"
        
        return self._create_result(action, abs(bull_score - bear_score), DecisionUrgency.NORMAL,
            f"{winner} win debate", {'bull_score': bull_score, 'bear_score': bear_score})


class ConsensusDecision(DecisionConcept):
    """Concept 84: Consensus Building - Require agreement"""
    
    def __init__(self):
        super().__init__(84, "Consensus Building", DecisionCategory.MULTI_AGENT)
        self.consensus_threshold = 0.7
        
    def decide(self, context: DecisionContext) -> DecisionResult:
        # Agent signals
        agents = {
            'trend_agent': context.trend,
            'momentum_agent': context.momentum,
            'sentiment_agent': context.sentiment,
            'risk_agent': -context.volatility + (1 - context.drawdown)
        }
        
        # Check for consensus
        bullish = sum(1 for s in agents.values() if s > 0.1)
        bearish = sum(1 for s in agents.values() if s < -0.1)
        
        consensus_ratio = max(bullish, bearish) / len(agents)
        
        if consensus_ratio >= self.consensus_threshold:
            if bullish > bearish:
                action = DecisionAction.BUY
                reason = f"Bullish consensus ({consensus_ratio:.0%})"
            else:
                action = DecisionAction.SELL
                reason = f"Bearish consensus ({consensus_ratio:.0%})"
            conf = consensus_ratio
        else:
            action = DecisionAction.HOLD
            reason = f"No consensus ({consensus_ratio:.0%})"
            conf = 0.4
        
        return self._create_result(action, conf, DecisionUrgency.NORMAL, reason,
            {'bullish': bullish, 'bearish': bearish, 'consensus': consensus_ratio})


class HierarchicalDecision(DecisionConcept):
    """Concept 85: Hierarchical Agents - Layered decision making"""
    
    def __init__(self):
        super().__init__(85, "Hierarchical Agents", DecisionCategory.MULTI_AGENT)
        
    def decide(self, context: DecisionContext) -> DecisionResult:
        # Level 1: Risk gate
        if context.drawdown > 0.15 or context.volatility > 0.6:
            return self._create_result(DecisionAction.ABSTAIN, 0.9, DecisionUrgency.HIGH,
                "L1 Risk gate: blocked", {'level': 1, 'reason': 'risk'})
        
        # Level 2: Regime filter
        if context.regime in ['crisis', 'extreme']:
            return self._create_result(DecisionAction.HOLD, 0.7, DecisionUrgency.HIGH,
                "L2 Regime filter: hold", {'level': 2, 'regime': context.regime})
        
        # Level 3: Signal generation
        signal = context.trend * 0.5 + context.momentum * 0.3 + context.sentiment * 0.2
        
        # Level 4: Position sizing
        size_factor = 1.0 - context.volatility
        adjusted_signal = signal * size_factor
        
        return self._create_result(self._signal_to_action(adjusted_signal), abs(adjusted_signal), DecisionUrgency.NORMAL,
            f"L4 Signal: {adjusted_signal:.3f}", {'level': 4, 'signal': signal, 'size_factor': size_factor})


class SwarmIntelligenceDecision(DecisionConcept):
    """Concept 86: Swarm Intelligence - Emergent collective behavior"""
    
    def __init__(self):
        super().__init__(86, "Swarm Intelligence", DecisionCategory.MULTI_AGENT)
        self.swarm_size = 20
        
    def decide(self, context: DecisionContext) -> DecisionResult:
        # Simulate swarm of simple agents
        positions = []
        
        for _ in range(self.swarm_size):
            # Each agent has slight randomness
            noise = random.gauss(0, 0.1)
            agent_signal = context.trend + context.momentum * 0.5 + noise
            positions.append(1 if agent_signal > 0 else -1)
        
        # Emergent behavior
        swarm_direction = sum(positions) / self.swarm_size
        
        if swarm_direction > 0.5:
            action = DecisionAction.BUY
        elif swarm_direction < -0.5:
            action = DecisionAction.SELL
        else:
            action = DecisionAction.HOLD
        
        return self._create_result(action, abs(swarm_direction), DecisionUrgency.NORMAL,
            f"Swarm: {swarm_direction:.2f}", {'swarm_direction': swarm_direction})


class AdversarialDecision(DecisionConcept):
    """Concept 87: Adversarial Agents - Challenge own decisions"""
    
    def __init__(self):
        super().__init__(87, "Adversarial Agents", DecisionCategory.MULTI_AGENT)
        
    def decide(self, context: DecisionContext) -> DecisionResult:
        # Primary agent
        primary_signal = context.trend * 0.5 + context.momentum * 0.5
        
        # Adversarial agent tries to find flaws
        adversarial_concerns = []
        
        if primary_signal > 0:
            # Challenge bullish view
            if context.volatility > 0.3: adversarial_concerns.append("high volatility")
            if context.sentiment < 0: adversarial_concerns.append("negative sentiment")
            if context.drawdown > 0.05: adversarial_concerns.append("in drawdown")
        else:
            # Challenge bearish view
            if context.momentum > 0: adversarial_concerns.append("positive momentum")
            if context.sentiment > 0: adversarial_concerns.append("positive sentiment")
        
        # Adjust based on adversarial feedback
        concern_penalty = len(adversarial_concerns) * 0.15
        adjusted_signal = primary_signal * (1 - concern_penalty)
        
        if len(adversarial_concerns) >= 2:
            action = DecisionAction.HOLD
            reason = f"Adversarial blocked: {adversarial_concerns}"
        else:
            action = self._signal_to_action(adjusted_signal)
            reason = f"Passed adversarial ({len(adversarial_concerns)} concerns)"
        
        return self._create_result(action, abs(adjusted_signal), DecisionUrgency.NORMAL, reason,
            {'primary': primary_signal, 'concerns': len(adversarial_concerns)})


class SpecialistCommitteeDecision(DecisionConcept):
    """Concept 88: Specialist Committee - Domain experts"""
    
    def __init__(self):
        super().__init__(88, "Specialist Committee", DecisionCategory.MULTI_AGENT)
        
    def decide(self, context: DecisionContext) -> DecisionResult:
        # Specialists with domain expertise
        specialists = {
            'trend_specialist': {'signal': context.trend, 'confidence': 0.8 if abs(context.trend) > 0.3 else 0.5},
            'vol_specialist': {'signal': -context.volatility * 2 + 1, 'confidence': 0.7},
            'sentiment_specialist': {'signal': context.sentiment, 'confidence': 0.6},
            'risk_specialist': {'signal': 1 - context.drawdown * 5, 'confidence': 0.9 if context.drawdown > 0.05 else 0.5}
        }
        
        # Weight by confidence
        total_conf = sum(s['confidence'] for s in specialists.values())
        weighted_signal = sum(s['signal'] * s['confidence'] for s in specialists.values()) / total_conf
        
        # Find most confident specialist
        most_confident = max(specialists, key=lambda k: specialists[k]['confidence'])
        
        return self._create_result(self._signal_to_action(weighted_signal), abs(weighted_signal), DecisionUrgency.NORMAL,
            f"Lead: {most_confident}", {'weighted_signal': weighted_signal, 'lead_specialist': most_confident})


class MarketMakingAgentDecision(DecisionConcept):
    """Concept 89: Market Making Agent - Provide liquidity"""
    
    def __init__(self):
        super().__init__(89, "Market Making Agent", DecisionCategory.MULTI_AGENT)
        self.inventory = 0.0
        
    def decide(self, context: DecisionContext) -> DecisionResult:
        # MM wants to stay neutral
        inventory_skew = self.inventory / 100  # Normalized
        
        # Fade inventory
        if inventory_skew > 0.2:
            action = DecisionAction.SELL
            reason = "Reducing long inventory"
        elif inventory_skew < -0.2:
            action = DecisionAction.BUY
            reason = "Reducing short inventory"
        else:
            # Normal MM behavior - fade extremes
            if context.momentum > 0.4:
                action = DecisionAction.WEAK_SELL
                reason = "Fading momentum"
            elif context.momentum < -0.4:
                action = DecisionAction.WEAK_BUY
                reason = "Fading momentum"
            else:
                action = DecisionAction.HOLD
                reason = "Neutral inventory"
        
        # Update inventory (simulated)
        if action in [DecisionAction.BUY, DecisionAction.WEAK_BUY]:
            self.inventory += 10
        elif action in [DecisionAction.SELL, DecisionAction.WEAK_SELL]:
            self.inventory -= 10
        
        return self._create_result(action, 0.6, DecisionUrgency.NORMAL, reason,
            {'inventory': self.inventory, 'skew': inventory_skew})


class ArbitrageAgentDecision(DecisionConcept):
    """Concept 90: Arbitrage Agent - Exploit mispricings"""
    
    def __init__(self):
        super().__init__(90, "Arbitrage Agent", DecisionCategory.MULTI_AGENT)
        self.fair_value_history: deque = deque(maxlen=20)
        
    def decide(self, context: DecisionContext) -> DecisionResult:
        # Estimate fair value
        fair_value = context.price * (1 + context.trend * 0.01)
        self.fair_value_history.append(fair_value)
        
        if len(self.fair_value_history) < 5:
            return self._create_result(DecisionAction.HOLD, 0.3, DecisionUrgency.LOW, "Building fair value", {})
        
        avg_fair_value = statistics.mean(self.fair_value_history)
        mispricing = (context.price - avg_fair_value) / avg_fair_value
        
        if mispricing > 0.02:  # Overpriced
            action = DecisionAction.SELL
            reason = f"Overpriced by {mispricing:.1%}"
            conf = min(abs(mispricing) * 20, 0.9)
        elif mispricing < -0.02:  # Underpriced
            action = DecisionAction.BUY
            reason = f"Underpriced by {abs(mispricing):.1%}"
            conf = min(abs(mispricing) * 20, 0.9)
        else:
            action = DecisionAction.HOLD
            reason = "Fair value"
            conf = 0.5
        
        return self._create_result(action, conf, DecisionUrgency.HIGH if abs(mispricing) > 0.03 else DecisionUrgency.NORMAL,
            reason, {'mispricing': mispricing, 'fair_value': avg_fair_value})


MULTIAGENT_CONCEPTS = [
    VotingEnsembleDecision,
    WeightedExpertsDecision,
    DebateDecision,
    ConsensusDecision,
    HierarchicalDecision,
    SwarmIntelligenceDecision,
    AdversarialDecision,
    SpecialistCommitteeDecision,
    MarketMakingAgentDecision,
    ArbitrageAgentDecision,
]
