"""
Probabilistic Decision Models (Concepts 11-20)
Statistical and probability-based approaches to trading decisions.
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

import logging
logger = logging.getLogger(__name__)



class BayesianDecision(DecisionConcept):
    """Concept 11: Bayesian Decision Theory - Update beliefs with evidence"""
    
    def __init__(self):
        try:
            super().__init__(11, "Bayesian Decision", DecisionCategory.PROBABILISTIC)
            self.prior = 0.5
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    def decide(self, context: DecisionContext) -> DecisionResult:
        try:
            l_bull = (0.8 if context.trend > 0 else 0.3) * (0.7 if context.momentum > 0 else 0.4)
            l_bear = (0.3 if context.trend > 0 else 0.8) * (0.4 if context.momentum > 0 else 0.7)
            evidence = l_bull * self.prior + l_bear * (1 - self.prior)
            posterior = (l_bull * self.prior) / evidence if evidence > 0 else 0.5
            self.prior = posterior * 0.7 + 0.5 * 0.3
        
            action = DecisionAction.STRONG_BUY if posterior > 0.7 else (DecisionAction.BUY if posterior > 0.6 else 
                (DecisionAction.WEAK_BUY if posterior > 0.55 else (DecisionAction.HOLD if posterior > 0.45 else
                (DecisionAction.WEAK_SELL if posterior > 0.4 else (DecisionAction.SELL if posterior > 0.3 else DecisionAction.STRONG_SELL)))))
        
            return self._create_result(action, abs(posterior - 0.5) * 2, DecisionUrgency.NORMAL,
                f"P(bull)={posterior:.1%}", {'posterior': posterior, 'prior': self.prior})
        except Exception as e:
            logger.error(f"Error in decide: {e}")
            raise


class ExpectedUtilityDecision(DecisionConcept):
    """Concept 12: Expected Utility Theory - Maximize risk-adjusted utility"""
    
    def __init__(self):
        try:
            super().__init__(12, "Expected Utility", DecisionCategory.PROBABILISTIC)
            self.risk_aversion = 0.5
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    def decide(self, context: DecisionContext) -> DecisionResult:
        try:
            def utility(x): return math.log(1 + x) if x > -1 else -10
        
            outcomes_buy = [(0.6 if context.trend > 0 else 0.3, 0.05), (0.3, 0.01), (0.1 if context.trend > 0 else 0.4, -0.03)]
            outcomes_sell = [(0.3 if context.trend > 0 else 0.5, 0.04), (0.4, -0.01), (0.3 if context.trend > 0 else 0.2, -0.04)]
        
            eu_buy = sum(p * utility(r) for p, r in outcomes_buy)
            eu_sell = sum(p * utility(r) for p, r in outcomes_sell)
        
            if eu_buy > eu_sell and eu_buy > 0:
                action, best = DecisionAction.BUY, eu_buy
            elif eu_sell > eu_buy and eu_sell > 0:
                action, best = DecisionAction.SELL, eu_sell
            else:
                action, best = DecisionAction.HOLD, 0
            
            return self._create_result(action, min(abs(best) * 10, 0.9), DecisionUrgency.NORMAL,
                f"EU: buy={eu_buy:.3f} sell={eu_sell:.3f}", {'eu_buy': eu_buy, 'eu_sell': eu_sell})
        except Exception as e:
            logger.error(f"Error in decide: {e}")
            raise


class ProspectTheoryDecision(DecisionConcept):
    """Concept 13: Prospect Theory - Loss aversion and probability weighting"""
    
    def __init__(self):
        try:
            super().__init__(13, "Prospect Theory", DecisionCategory.PROBABILISTIC)
            self.loss_aversion = 2.25
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    def decide(self, context: DecisionContext) -> DecisionResult:
        try:
            def value(x): return x ** 0.88 if x >= 0 else -self.loss_aversion * ((-x) ** 0.88)
            def weight(p): return (p ** 0.65) / ((p ** 0.65 + (1 - p) ** 0.65) ** (1 / 0.65))
        
            p_buy = 0.5 + context.trend * 0.3
            prospect_buy = weight(p_buy) * value(context.volatility * 2) + weight(1 - p_buy) * value(-context.volatility * 1.5)
            prospect_sell = weight(1 - p_buy) * value(context.volatility * 1.8) + weight(p_buy) * value(-context.volatility * 1.8)
        
            if prospect_buy > prospect_sell and prospect_buy > 0:
                action = DecisionAction.BUY
            elif prospect_sell > prospect_buy and prospect_sell > 0:
                action = DecisionAction.SELL
            else:
                action = DecisionAction.HOLD
            
            return self._create_result(action, min(abs(max(prospect_buy, prospect_sell)) / 2, 0.9), DecisionUrgency.NORMAL,
                f"Prospect: buy={prospect_buy:.3f}", {'prospect_buy': prospect_buy, 'prospect_sell': prospect_sell})
        except Exception as e:
            logger.error(f"Error in decide: {e}")
            raise


class MonteCarloDecision(DecisionConcept):
    """Concept 14: Monte Carlo Simulation - Simulate many outcomes"""
    
    def __init__(self):
        try:
            super().__init__(14, "Monte Carlo", DecisionCategory.PROBABILISTIC)
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    def decide(self, context: DecisionContext) -> DecisionResult:
        try:
            buy_outcomes = [sum(context.trend * 0.01 + context.volatility * 0.02 * random.gauss(0, 1) for _ in range(10)) for _ in range(500)]
            sell_outcomes = [-o for o in buy_outcomes]
        
            buy_mean, buy_std = statistics.mean(buy_outcomes), statistics.stdev(buy_outcomes)
            sell_mean, sell_std = statistics.mean(sell_outcomes), statistics.stdev(sell_outcomes)
            buy_sharpe = buy_mean / buy_std if buy_std > 0 else 0
            sell_sharpe = sell_mean / sell_std if sell_std > 0 else 0
        
            if buy_sharpe > 0.5:
                action, conf = DecisionAction.BUY, min(buy_sharpe / 2, 0.9)
            elif sell_sharpe > 0.5:
                action, conf = DecisionAction.SELL, min(sell_sharpe / 2, 0.9)
            else:
                action, conf = DecisionAction.HOLD, 0.5
            
            return self._create_result(action, conf, DecisionUrgency.NORMAL,
                f"MC Sharpe: buy={buy_sharpe:.2f}", {'buy_sharpe': buy_sharpe, 'sell_sharpe': sell_sharpe})
        except Exception as e:
            logger.error(f"Error in decide: {e}")
            raise


class MaximumEntropyDecision(DecisionConcept):
    """Concept 15: Maximum Entropy - Decide under maximum uncertainty"""
    
    def __init__(self):
        try:
            super().__init__(15, "Maximum Entropy", DecisionCategory.PROBABILISTIC)
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    def decide(self, context: DecisionContext) -> DecisionResult:
        try:
            values = [abs(context.trend), abs(context.momentum), abs(context.sentiment)]
            total = sum(values) + 1e-10
            probs = [v / total for v in values]
            entropy = -sum(p * math.log(p + 1e-10) for p in probs)
            norm_entropy = entropy / math.log(3)
        
            if norm_entropy > 0.8:
                action, conf = DecisionAction.HOLD, 0.3
            else:
                dominant = context.trend if abs(context.trend) >= abs(context.momentum) and abs(context.trend) >= abs(context.sentiment) else context.momentum
                action = DecisionAction.BUY if dominant > 0.3 else (DecisionAction.SELL if dominant < -0.3 else DecisionAction.HOLD)
                conf = (1 - norm_entropy) * abs(dominant)
            
            return self._create_result(action, conf, DecisionUrgency.NORMAL,
                f"Entropy: {norm_entropy:.2f}", {'entropy': norm_entropy})
        except Exception as e:
            logger.error(f"Error in decide: {e}")
            raise


class InformationTheoreticDecision(DecisionConcept):
    """Concept 16: Information-Theoretic - Mutual information based"""
    
    def __init__(self):
        try:
            super().__init__(16, "Information Theoretic", DecisionCategory.PROBABILISTIC)
            self.history: deque = deque(maxlen=50)
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    def decide(self, context: DecisionContext) -> DecisionResult:
        try:
            current = (1 if context.trend > 0 else 0, 1 if context.momentum > 0 else 0)
            self.history.append(current)
        
            if len(self.history) < 10:
                return self._create_result(DecisionAction.HOLD, 0.3, DecisionUrgency.LOW, "Insufficient data", {'history': len(self.history)})
        
            agreements = sum(1 for h in self.history if h[0] == current[0]) / len(self.history)
            info_gain = 1 - agreements
            signal = current[0] * 2 - 1 + (current[1] * 2 - 1) * 0.5
        
            if info_gain > 0.7:
                action, conf = DecisionAction.HOLD, 0.4
            else:
                action = DecisionAction.BUY if signal > 0.5 else (DecisionAction.SELL if signal < -0.5 else DecisionAction.HOLD)
                conf = (1 - info_gain) * 0.8
            
            return self._create_result(action, conf, DecisionUrgency.NORMAL,
                f"Info gain: {info_gain:.2f}", {'info_gain': info_gain, 'signal': signal})
        except Exception as e:
            logger.error(f"Error in decide: {e}")
            raise


class StochasticDominanceDecision(DecisionConcept):
    """Concept 17: Stochastic Dominance - Compare outcome distributions"""
    
    def __init__(self):
        try:
            super().__init__(17, "Stochastic Dominance", DecisionCategory.PROBABILISTIC)
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    def decide(self, context: DecisionContext) -> DecisionResult:
        try:
            buy = sorted([context.trend * 0.05 + context.volatility * random.gauss(0, 1) * 0.02 for _ in range(100)])
            sell = sorted([-context.trend * 0.05 + context.volatility * random.gauss(0, 1) * 0.02 for _ in range(100)])
        
            buy_dom = all(b >= s for b, s in zip(buy, sell))
            sell_dom = all(s >= b for b, s in zip(buy, sell))
            buy_mean, sell_mean = statistics.mean(buy), statistics.mean(sell)
        
            if buy_dom:
                action, conf = DecisionAction.STRONG_BUY, 0.9
            elif sell_dom:
                action, conf = DecisionAction.STRONG_SELL, 0.9
            elif buy_mean > sell_mean + 0.01:
                action, conf = DecisionAction.BUY, 0.6
            elif sell_mean > buy_mean + 0.01:
                action, conf = DecisionAction.SELL, 0.6
            else:
                action, conf = DecisionAction.HOLD, 0.5
            
            return self._create_result(action, conf, DecisionUrgency.NORMAL,
                f"Buy mean: {buy_mean:.4f}", {'buy_mean': buy_mean, 'sell_mean': sell_mean})
        except Exception as e:
            logger.error(f"Error in decide: {e}")
            raise


class ConfidenceIntervalDecision(DecisionConcept):
    """Concept 18: Confidence Interval - Statistical CI based decisions"""
    
    def __init__(self):
        try:
            super().__init__(18, "Confidence Interval", DecisionCategory.PROBABILISTIC)
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    def decide(self, context: DecisionContext) -> DecisionResult:
        try:
            expected = context.trend * 0.02 + context.momentum * 0.01
            std_err = context.volatility * 0.03
            ci_lower = expected - 1.96 * std_err
            ci_upper = expected + 1.96 * std_err
        
            if ci_lower > 0.005:
                action, conf = DecisionAction.BUY, 0.8
            elif ci_upper < -0.005:
                action, conf = DecisionAction.SELL, 0.8
            elif ci_lower > 0:
                action, conf = DecisionAction.WEAK_BUY, 0.6
            elif ci_upper < 0:
                action, conf = DecisionAction.WEAK_SELL, 0.6
            else:
                action, conf = DecisionAction.HOLD, 0.4
            
            return self._create_result(action, conf, DecisionUrgency.NORMAL,
                f"95% CI: [{ci_lower:.4f}, {ci_upper:.4f}]", {'ci_lower': ci_lower, 'ci_upper': ci_upper})
        except Exception as e:
            logger.error(f"Error in decide: {e}")
            raise


class MarkovDecision(DecisionConcept):
    """Concept 19: Markov Decision Process - State transition based"""
    
    def __init__(self):
        try:
            super().__init__(19, "Markov Decision", DecisionCategory.PROBABILISTIC)
            self.transitions = {'bull': {'bull': 2, 'neutral': 1, 'bear': 1}, 'neutral': {'bull': 1, 'neutral': 2, 'bear': 1}, 'bear': {'bull': 1, 'neutral': 1, 'bear': 2}}
            self.last = 'neutral'
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    def decide(self, context: DecisionContext) -> DecisionResult:
        try:
            current = 'bull' if context.trend > 0.2 else ('bear' if context.trend < -0.2 else 'neutral')
            self.transitions[self.last][current] += 1
        
            total = sum(self.transitions[current].values())
            probs = {s: c / total for s, c in self.transitions[current].items()}
            expected = probs['bull'] - probs['bear']
            self.last = current
        
            action = DecisionAction.BUY if expected > 0.3 else (DecisionAction.WEAK_BUY if expected > 0.1 else
                (DecisionAction.HOLD if expected > -0.1 else (DecisionAction.WEAK_SELL if expected > -0.3 else DecisionAction.SELL)))
        
            return self._create_result(action, abs(expected), DecisionUrgency.NORMAL,
                f"E[next]={expected:.2f}", {'current': current, 'expected': expected})
        except Exception as e:
            logger.error(f"Error in decide: {e}")
            raise


class KellyDecision(DecisionConcept):
    """Concept 20: Kelly Criterion - Optimal position sizing"""
    
    def __init__(self):
        try:
            super().__init__(20, "Kelly Criterion", DecisionCategory.PROBABILISTIC)
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    def decide(self, context: DecisionContext) -> DecisionResult:
        try:
            win_prob = max(0.1, min(0.9, 0.5 + context.trend * 0.2 + context.momentum * 0.1))
            payoff = 1.5 - context.volatility
            kelly = (win_prob * payoff - (1 - win_prob)) / payoff
            half_kelly = kelly / 2
        
            if half_kelly > 0.2:
                action, conf = DecisionAction.STRONG_BUY, min(half_kelly * 2, 0.9)
            elif half_kelly > 0.1:
                action, conf = DecisionAction.BUY, half_kelly * 3
            elif half_kelly > 0.02:
                action, conf = DecisionAction.WEAK_BUY, half_kelly * 5
            elif half_kelly > -0.02:
                action, conf = DecisionAction.HOLD, 0.5
            elif half_kelly > -0.1:
                action, conf = DecisionAction.WEAK_SELL, abs(half_kelly) * 5
            else:
                action, conf = DecisionAction.SELL, min(abs(half_kelly) * 3, 0.9)
            
            return self._create_result(action, conf, DecisionUrgency.NORMAL,
                f"Kelly: {kelly:.1%}", {'kelly': kelly, 'half_kelly': half_kelly, 'win_prob': win_prob})
        except Exception as e:
            logger.error(f"Error in decide: {e}")
            raise


PROBABILISTIC_CONCEPTS = [
    BayesianDecision,
    ExpectedUtilityDecision,
    ProspectTheoryDecision,
    MonteCarloDecision,
    MaximumEntropyDecision,
    InformationTheoreticDecision,
    StochasticDominanceDecision,
    ConfidenceIntervalDecision,
    MarkovDecision,
    KellyDecision,
]
