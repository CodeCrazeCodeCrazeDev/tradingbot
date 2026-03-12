"""
Game Theory Decisions (Concepts 31-40)
Strategic thinking approaches to trading decisions.
"""

import math
import random
from collections import deque
from typing import Dict, List

from .core_types import (
    DecisionConcept, DecisionContext, DecisionResult,
    DecisionCategory, DecisionAction, DecisionUrgency
)

import logging
logger = logging.getLogger(__name__)



class NashEquilibriumDecision(DecisionConcept):
    """Concept 31: Nash Equilibrium - Find stable strategy"""
    
    def __init__(self):
        try:
            super().__init__(31, "Nash Equilibrium", DecisionCategory.GAME_THEORY)
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    def decide(self, context: DecisionContext) -> DecisionResult:
        # Payoff matrix: [my_action][market_action] = payoff
        # Market can go up, down, or sideways
        try:
            payoffs = {
                'buy': {'up': 0.05, 'down': -0.03, 'side': -0.01},
                'sell': {'up': -0.03, 'down': 0.05, 'side': -0.01},
                'hold': {'up': 0, 'down': 0, 'side': 0}
            }
        
            # Estimate market probabilities
            p_up = 0.33 + context.trend * 0.2 + context.momentum * 0.1
            p_down = 0.33 - context.trend * 0.2 - context.momentum * 0.1
            p_side = 1 - p_up - p_down
        
            # Expected value for each action
            ev = {}
            for action in payoffs:
                ev[action] = payoffs[action]['up'] * p_up + payoffs[action]['down'] * p_down + payoffs[action]['side'] * p_side
        
            best = max(ev, key=ev.get)
            action = DecisionAction.BUY if best == 'buy' else (DecisionAction.SELL if best == 'sell' else DecisionAction.HOLD)
        
            return self._create_result(action, abs(ev[best]) * 10, DecisionUrgency.NORMAL,
                f"Nash EV: {ev}", {'ev_buy': ev['buy'], 'ev_sell': ev['sell'], 'ev_hold': ev['hold']})
        except Exception as e:
            logger.error(f"Error in decide: {e}")
            raise


class MinimaxDecision(DecisionConcept):
    """Concept 32: Minimax - Minimize maximum loss"""
    
    def __init__(self):
        try:
            super().__init__(32, "Minimax", DecisionCategory.GAME_THEORY)
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    def decide(self, context: DecisionContext) -> DecisionResult:
        # Worst case for each action
        try:
            worst_buy = -context.volatility * 0.1  # Max loss if buy
            worst_sell = -context.volatility * 0.1  # Max loss if sell
            worst_hold = -context.volatility * 0.02  # Opportunity cost
        
            # Adjust based on trend
            if context.trend > 0:
                worst_buy *= 0.7  # Less bad
                worst_sell *= 1.3  # Worse
            else:
                worst_buy *= 1.3
                worst_sell *= 0.7
        
            # Choose action with best worst-case
            worst_cases = {'buy': worst_buy, 'sell': worst_sell, 'hold': worst_hold}
            best = max(worst_cases, key=worst_cases.get)
        
            action = DecisionAction.BUY if best == 'buy' else (DecisionAction.SELL if best == 'sell' else DecisionAction.HOLD)
        
            return self._create_result(action, 0.6, DecisionUrgency.NORMAL,
                f"Minimax: best worst={worst_cases[best]:.4f}", worst_cases)
        except Exception as e:
            logger.error(f"Error in decide: {e}")
            raise


class StackelbergDecision(DecisionConcept):
    """Concept 33: Stackelberg Leadership - Lead or follow"""
    
    def __init__(self):
        try:
            super().__init__(33, "Stackelberg", DecisionCategory.GAME_THEORY)
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    def decide(self, context: DecisionContext) -> DecisionResult:
        # Are we leader (early) or follower (late)?
        # High volume = many followers, be leader
        # Low volume = few participants, be follower
        
        try:
            leader_score = context.volume / 1000000 if context.volume > 0 else 0.5
            leader_score = min(leader_score, 1.0)
        
            if leader_score > 0.6:  # Be leader - act on fundamentals
                signal = context.trend * 0.6 + context.sentiment * 0.4
                reason = "Leading - acting on fundamentals"
            else:  # Be follower - follow momentum
                signal = context.momentum * 0.7 + context.trend * 0.3
                reason = "Following - riding momentum"
        
            return self._create_result(self._signal_to_action(signal), abs(signal), DecisionUrgency.NORMAL,
                reason, {'leader_score': leader_score, 'signal': signal})
        except Exception as e:
            logger.error(f"Error in decide: {e}")
            raise


class PrisonersDilemmaDecision(DecisionConcept):
    """Concept 34: Prisoner's Dilemma - Cooperate or defect"""
    
    def __init__(self):
        try:
            super().__init__(34, "Prisoners Dilemma", DecisionCategory.GAME_THEORY)
            self.market_history: deque = deque(maxlen=10)
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    def decide(self, context: DecisionContext) -> DecisionResult:
        # Market "cooperates" when trending, "defects" when choppy
        try:
            market_cooperates = context.volatility < 0.3 and abs(context.trend) > 0.2
            self.market_history.append(market_cooperates)
        
            # Tit-for-tat: cooperate if market cooperated last time
            if len(self.market_history) >= 2:
                last_coop = self.market_history[-2]
                if last_coop:  # Market cooperated - we cooperate (follow trend)
                    signal = context.trend
                    reason = "Cooperating - following trend"
                else:  # Market defected - we defect (reduce exposure)
                    signal = 0
                    reason = "Defecting - reducing exposure"
            else:
                signal = context.trend * 0.5  # Start cooperative
                reason = "Initial cooperation"
        
            return self._create_result(self._signal_to_action(signal), 0.6, DecisionUrgency.NORMAL,
                reason, {'market_cooperates': market_cooperates, 'signal': signal})
        except Exception as e:
            logger.error(f"Error in decide: {e}")
            raise


class ChickenGameDecision(DecisionConcept):
    """Concept 35: Chicken Game - Test of nerve"""
    
    def __init__(self):
        try:
            super().__init__(35, "Chicken Game", DecisionCategory.GAME_THEORY)
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    def decide(self, context: DecisionContext) -> DecisionResult:
        # In volatile markets, who blinks first?
        # High volatility = high stakes chicken game
        
        try:
            stakes = context.volatility
            our_nerve = context.win_rate  # Past success = more nerve
            market_nerve = abs(context.momentum)  # Strong momentum = market not blinking
        
            if stakes < 0.3:  # Low stakes - play normally
                signal = context.trend
                reason = "Low stakes - normal play"
            elif our_nerve > market_nerve:  # We have more nerve
                signal = context.trend * 1.2  # Press advantage
                reason = "We have nerve advantage"
            else:  # Market has more nerve
                signal = context.trend * 0.5  # Swerve (reduce)
                reason = "Swerving - market has nerve"
        
            return self._create_result(self._signal_to_action(signal), abs(signal) * (1 - stakes * 0.5), DecisionUrgency.NORMAL,
                reason, {'stakes': stakes, 'our_nerve': our_nerve, 'market_nerve': market_nerve})
        except Exception as e:
            logger.error(f"Error in decide: {e}")
            raise


class AuctionTheoryDecision(DecisionConcept):
    """Concept 36: Auction Theory - Bid strategically"""
    
    def __init__(self):
        try:
            super().__init__(36, "Auction Theory", DecisionCategory.GAME_THEORY)
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    def decide(self, context: DecisionContext) -> DecisionResult:
        # Market as continuous auction
        # Estimate true value vs current price
        
        # True value estimate based on fundamentals
        try:
            value_signal = context.trend * 0.4 + context.sentiment * 0.3 + context.momentum * 0.3
            estimated_value = context.price * (1 + value_signal * 0.05)
        
            # Winner's curse adjustment
            uncertainty = context.volatility
            adjusted_bid = estimated_value * (1 - uncertainty * 0.5)
        
            price_diff = (adjusted_bid - context.price) / context.price
        
            if price_diff > 0.02:  # Undervalued
                action = DecisionAction.BUY
                reason = f"Undervalued by {price_diff:.1%}"
            elif price_diff < -0.02:  # Overvalued
                action = DecisionAction.SELL
                reason = f"Overvalued by {abs(price_diff):.1%}"
            else:
                action = DecisionAction.HOLD
                reason = "Fair value"
        
            return self._create_result(action, min(abs(price_diff) * 20, 0.9), DecisionUrgency.NORMAL,
                reason, {'price_diff': price_diff, 'uncertainty': uncertainty})
        except Exception as e:
            logger.error(f"Error in decide: {e}")
            raise


class SignalingGameDecision(DecisionConcept):
    """Concept 37: Signaling Game - Read and send signals"""
    
    def __init__(self):
        try:
            super().__init__(37, "Signaling Game", DecisionCategory.GAME_THEORY)
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    def decide(self, context: DecisionContext) -> DecisionResult:
        # Interpret market signals
        try:
            signals = []
        
            # Volume signal
            if context.volume > 0:
                vol_signal = "strong" if context.volume > 1000000 else "weak"
                signals.append(('volume', vol_signal))
        
            # Price action signal
            if abs(context.trend) > 0.3:
                price_signal = "bullish" if context.trend > 0 else "bearish"
                signals.append(('price', price_signal))
        
            # Sentiment signal
            if abs(context.sentiment) > 0.3:
                sent_signal = "positive" if context.sentiment > 0 else "negative"
                signals.append(('sentiment', sent_signal))
        
            # Aggregate signals
            bullish = sum(1 for s in signals if s[1] in ['strong', 'bullish', 'positive'])
            bearish = sum(1 for s in signals if s[1] in ['weak', 'bearish', 'negative'])
        
            if bullish > bearish + 1:
                action, conf = DecisionAction.BUY, 0.7
            elif bearish > bullish + 1:
                action, conf = DecisionAction.SELL, 0.7
            else:
                action, conf = DecisionAction.HOLD, 0.5
        
            return self._create_result(action, conf, DecisionUrgency.NORMAL,
                f"Signals: {bullish} bull, {bearish} bear", {'bullish': bullish, 'bearish': bearish})
        except Exception as e:
            logger.error(f"Error in decide: {e}")
            raise


class EvolutionaryGameDecision(DecisionConcept):
    """Concept 38: Evolutionary Game Theory - Adapt strategy mix"""
    
    def __init__(self):
        try:
            super().__init__(38, "Evolutionary Game", DecisionCategory.GAME_THEORY)
            self.strategy_fitness = {'trend': 1.0, 'mean_rev': 1.0, 'momentum': 1.0}
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    def decide(self, context: DecisionContext) -> DecisionResult:
        # Each strategy's signal
        try:
            trend_signal = context.trend
            mean_rev_signal = -context.trend * 0.5  # Fade extremes
            momentum_signal = context.momentum
        
            # Weighted by fitness
            total_fitness = sum(self.strategy_fitness.values())
            weights = {k: v / total_fitness for k, v in self.strategy_fitness.items()}
        
            combined = (trend_signal * weights['trend'] + 
                       mean_rev_signal * weights['mean_rev'] + 
                       momentum_signal * weights['momentum'])
        
            # Update fitness based on market conditions
            if abs(context.trend) > 0.3:
                self.strategy_fitness['trend'] *= 1.05
                self.strategy_fitness['mean_rev'] *= 0.95
            else:
                self.strategy_fitness['trend'] *= 0.95
                self.strategy_fitness['mean_rev'] *= 1.05
        
            # Normalize
            max_fit = max(self.strategy_fitness.values())
            self.strategy_fitness = {k: v / max_fit for k, v in self.strategy_fitness.items()}
        
            return self._create_result(self._signal_to_action(combined), abs(combined), DecisionUrgency.NORMAL,
                f"Evolved weights: {weights}", {'combined': combined, 'weights': weights})
        except Exception as e:
            logger.error(f"Error in decide: {e}")
            raise


class MechanismDesignDecision(DecisionConcept):
    """Concept 39: Mechanism Design - Design optimal response"""
    
    def __init__(self):
        try:
            super().__init__(39, "Mechanism Design", DecisionCategory.GAME_THEORY)
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    def decide(self, context: DecisionContext) -> DecisionResult:
        # Design mechanism that incentivizes truth-telling from market
        # Market "tells truth" when price reflects fundamentals
        
        # Measure market efficiency
        try:
            efficiency = 1 - abs(context.trend - context.momentum) * 0.5
            efficiency = max(0, min(1, efficiency))
        
            if efficiency > 0.7:  # Efficient market - follow price
                signal = context.trend
                reason = "Efficient market - following price"
            else:  # Inefficient - look for mispricings
                signal = context.sentiment * 0.5 + context.momentum * 0.5
                reason = "Inefficient - seeking alpha"
        
            return self._create_result(self._signal_to_action(signal), abs(signal) * efficiency, DecisionUrgency.NORMAL,
                reason, {'efficiency': efficiency, 'signal': signal})
        except Exception as e:
            logger.error(f"Error in decide: {e}")
            raise


class CoalitionGameDecision(DecisionConcept):
    """Concept 40: Coalition Game - Align with winning side"""
    
    def __init__(self):
        try:
            super().__init__(40, "Coalition Game", DecisionCategory.GAME_THEORY)
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    def decide(self, context: DecisionContext) -> DecisionResult:
        # Identify coalitions: bulls vs bears
        try:
            bull_strength = max(0, context.trend) + max(0, context.momentum) + max(0, context.sentiment)
            bear_strength = abs(min(0, context.trend)) + abs(min(0, context.momentum)) + abs(min(0, context.sentiment))
        
            total = bull_strength + bear_strength + 0.01
            bull_share = bull_strength / total
            bear_share = bear_strength / total
        
            # Join stronger coalition
            if bull_share > 0.6:
                action = DecisionAction.BUY
                reason = f"Joining bull coalition ({bull_share:.0%})"
            elif bear_share > 0.6:
                action = DecisionAction.SELL
                reason = f"Joining bear coalition ({bear_share:.0%})"
            else:
                action = DecisionAction.HOLD
                reason = "No dominant coalition"
        
            return self._create_result(action, max(bull_share, bear_share), DecisionUrgency.NORMAL,
                reason, {'bull_share': bull_share, 'bear_share': bear_share})
        except Exception as e:
            logger.error(f"Error in decide: {e}")
            raise


GAME_THEORY_CONCEPTS = [
    NashEquilibriumDecision,
    MinimaxDecision,
    StackelbergDecision,
    PrisonersDilemmaDecision,
    ChickenGameDecision,
    AuctionTheoryDecision,
    SignalingGameDecision,
    EvolutionaryGameDecision,
    MechanismDesignDecision,
    CoalitionGameDecision,
]
