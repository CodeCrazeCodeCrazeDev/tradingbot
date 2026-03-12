"""
Risk-Aware Decisions (Concepts 51-60)
Risk-centric approaches to trading decisions.
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



class ValueAtRiskDecision(DecisionConcept):
    """Concept 51: Value at Risk - Don't exceed VaR limits"""
    
    def __init__(self):
        try:
            super().__init__(51, "Value at Risk", DecisionCategory.RISK_AWARE)
            self.max_var_pct = 0.02  # 2% daily VaR limit
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    def decide(self, context: DecisionContext) -> DecisionResult:
        # Calculate position VaR
        try:
            position_value = abs(context.current_position) * context.price
            daily_var = position_value * context.volatility * 2.33  # 99% VaR
            var_pct = daily_var / context.portfolio_value if context.portfolio_value > 0 else 0
        
            signal = context.trend * 0.5 + context.momentum * 0.5
        
            if var_pct > self.max_var_pct:
                action = DecisionAction.SELL if context.current_position > 0 else DecisionAction.BUY
                reason = f"VaR {var_pct:.1%} exceeds limit {self.max_var_pct:.1%}"
                urgency = DecisionUrgency.HIGH
            elif var_pct > self.max_var_pct * 0.8:
                action = DecisionAction.HOLD
                reason = f"VaR {var_pct:.1%} near limit"
                urgency = DecisionUrgency.NORMAL
            else:
                action = self._signal_to_action(signal)
                reason = f"VaR {var_pct:.1%} within limit"
                urgency = DecisionUrgency.NORMAL
        
            return self._create_result(action, 0.7, urgency, reason, {'var_pct': var_pct, 'limit': self.max_var_pct})
        except Exception as e:
            logger.error(f"Error in decide: {e}")
            raise


class DrawdownProtectionDecision(DecisionConcept):
    """Concept 52: Drawdown Protection - Scale down in drawdowns"""
    
    def __init__(self):
        try:
            super().__init__(52, "Drawdown Protection", DecisionCategory.RISK_AWARE)
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    def decide(self, context: DecisionContext) -> DecisionResult:
        try:
            dd = context.drawdown
        
            if dd > 0.15:  # Severe drawdown
                action = DecisionAction.ABSTAIN
                reason = f"Severe drawdown {dd:.1%} - no new trades"
                scale = 0
            elif dd > 0.10:  # Significant drawdown
                signal = context.trend * 0.3
                action = self._signal_to_action(signal)
                reason = f"Significant drawdown {dd:.1%} - reduced size"
                scale = 0.3
            elif dd > 0.05:  # Moderate drawdown
                signal = context.trend * 0.6
                action = self._signal_to_action(signal)
                reason = f"Moderate drawdown {dd:.1%}"
                scale = 0.6
            else:
                signal = context.trend
                action = self._signal_to_action(signal)
                reason = "Normal drawdown"
                scale = 1.0
        
            return self._create_result(action, abs(context.trend) * scale, DecisionUrgency.HIGH if dd > 0.1 else DecisionUrgency.NORMAL,
                reason, {'drawdown': dd, 'scale': scale})
        except Exception as e:
            logger.error(f"Error in decide: {e}")
            raise


class CorrelationRiskDecision(DecisionConcept):
    """Concept 53: Correlation Risk - Avoid correlated positions"""
    
    def __init__(self):
        try:
            super().__init__(53, "Correlation Risk", DecisionCategory.RISK_AWARE)
            self.positions: Dict[str, float] = {}
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    def decide(self, context: DecisionContext) -> DecisionResult:
        # Track position direction
        try:
            self.positions[context.symbol] = context.current_position
        
            # Count same-direction positions
            long_count = sum(1 for p in self.positions.values() if p > 0)
            short_count = sum(1 for p in self.positions.values() if p < 0)
        
            signal = context.trend
            proposed_direction = 1 if signal > 0 else -1
        
            # Check concentration
            if proposed_direction > 0 and long_count >= 3:
                action = DecisionAction.HOLD
                reason = f"Too many longs ({long_count})"
                conf = 0.4
            elif proposed_direction < 0 and short_count >= 3:
                action = DecisionAction.HOLD
                reason = f"Too many shorts ({short_count})"
                conf = 0.4
            else:
                action = self._signal_to_action(signal)
                reason = f"Correlation OK (L:{long_count} S:{short_count})"
                conf = abs(signal)
        
            return self._create_result(action, conf, DecisionUrgency.NORMAL, reason,
                {'long_count': long_count, 'short_count': short_count})
        except Exception as e:
            logger.error(f"Error in decide: {e}")
            raise


class TailRiskDecision(DecisionConcept):
    """Concept 54: Tail Risk - Protect against black swans"""
    
    def __init__(self):
        try:
            super().__init__(54, "Tail Risk", DecisionCategory.RISK_AWARE)
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    def decide(self, context: DecisionContext) -> DecisionResult:
        # Estimate tail risk
        try:
            tail_risk = context.volatility * 3  # 3-sigma events
        
            # Kurtosis proxy (high vol = fat tails)
            fat_tails = context.volatility > 0.4
        
            signal = context.trend * 0.5 + context.momentum * 0.5
        
            if fat_tails:
                # Reduce exposure significantly
                signal *= 0.3
                reason = "Fat tails detected - reducing"
                urgency = DecisionUrgency.HIGH
            elif tail_risk > 0.1:
                signal *= 0.6
                reason = f"Elevated tail risk ({tail_risk:.1%})"
                urgency = DecisionUrgency.NORMAL
            else:
                reason = "Normal tail risk"
                urgency = DecisionUrgency.NORMAL
        
            return self._create_result(self._signal_to_action(signal), abs(signal), urgency, reason,
                {'tail_risk': tail_risk, 'fat_tails': fat_tails})
        except Exception as e:
            logger.error(f"Error in decide: {e}")
            raise


class LiquidityRiskDecision(DecisionConcept):
    """Concept 55: Liquidity Risk - Ensure exit capability"""
    
    def __init__(self):
        try:
            super().__init__(55, "Liquidity Risk", DecisionCategory.RISK_AWARE)
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    def decide(self, context: DecisionContext) -> DecisionResult:
        # Liquidity proxy from volume
        try:
            avg_daily_volume = context.volume
            position_size = abs(context.current_position) * context.price
        
            # Days to liquidate
            days_to_exit = position_size / avg_daily_volume if avg_daily_volume > 0 else float('inf')
        
            signal = context.trend
        
            if days_to_exit > 5:
                action = DecisionAction.ABSTAIN
                reason = f"Illiquid - {days_to_exit:.1f} days to exit"
                conf = 0.3
            elif days_to_exit > 1:
                signal *= 0.5
                action = self._signal_to_action(signal)
                reason = f"Low liquidity - {days_to_exit:.1f} days"
                conf = abs(signal)
            else:
                action = self._signal_to_action(signal)
                reason = "Good liquidity"
                conf = abs(signal)
        
            return self._create_result(action, conf, DecisionUrgency.NORMAL, reason, {'days_to_exit': days_to_exit})
        except Exception as e:
            logger.error(f"Error in decide: {e}")
            raise


class RiskParityDecision(DecisionConcept):
    """Concept 56: Risk Parity - Equal risk contribution"""
    
    def __init__(self):
        try:
            super().__init__(56, "Risk Parity", DecisionCategory.RISK_AWARE)
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    def decide(self, context: DecisionContext) -> DecisionResult:
        # Target equal risk contribution
        try:
            target_risk = 0.01  # 1% risk per position
        
            # Current risk contribution
            position_risk = abs(context.current_position) * context.price * context.volatility / context.portfolio_value
        
            signal = context.trend
        
            if position_risk > target_risk * 1.5:
                # Reduce to target
                action = DecisionAction.WEAK_SELL if context.current_position > 0 else DecisionAction.WEAK_BUY
                reason = f"Risk {position_risk:.2%} > target {target_risk:.2%}"
            elif position_risk < target_risk * 0.5 and abs(signal) > 0.2:
                # Can increase
                action = self._signal_to_action(signal * 1.2)
                reason = f"Risk {position_risk:.2%} < target - can increase"
            else:
                action = self._signal_to_action(signal)
                reason = f"Risk {position_risk:.2%} near target"
        
            return self._create_result(action, 0.6, DecisionUrgency.NORMAL, reason,
                {'position_risk': position_risk, 'target_risk': target_risk})
        except Exception as e:
            logger.error(f"Error in decide: {e}")
            raise


class StopLossDecision(DecisionConcept):
    """Concept 57: Dynamic Stop Loss - Adaptive stop levels"""
    
    def __init__(self):
        try:
            super().__init__(57, "Dynamic Stop Loss", DecisionCategory.RISK_AWARE)
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    def decide(self, context: DecisionContext) -> DecisionResult:
        # ATR-based stop
        try:
            atr_multiplier = 2.0
            stop_distance = context.volatility * atr_multiplier * context.price
        
            # Tighter stops in high vol
            if context.volatility > 0.4:
                stop_distance *= 0.7
                reason = "Tight stop (high vol)"
            elif context.volatility < 0.2:
                stop_distance *= 1.3
                reason = "Wide stop (low vol)"
            else:
                reason = "Normal stop"
        
            stop_pct = stop_distance / context.price
        
            signal = context.trend
            action = self._signal_to_action(signal)
        
            return self._create_result(action, abs(signal), DecisionUrgency.NORMAL, reason,
                {'stop_pct': stop_pct, 'stop_distance': stop_distance})
        except Exception as e:
            logger.error(f"Error in decide: {e}")
            raise


class PositionSizingDecision(DecisionConcept):
    """Concept 58: Optimal Position Sizing - Size based on edge"""
    
    def __init__(self):
        try:
            super().__init__(58, "Position Sizing", DecisionCategory.RISK_AWARE)
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    def decide(self, context: DecisionContext) -> DecisionResult:
        # Kelly-inspired sizing
        try:
            win_rate = context.win_rate
            avg_win = 0.02  # Assumed
            avg_loss = 0.01
        
            if avg_loss > 0:
                kelly = (win_rate * avg_win - (1 - win_rate) * avg_loss) / avg_loss
            else:
                kelly = 0
        
            # Half-Kelly for safety
            position_pct = max(0, min(kelly / 2, 0.1))  # Cap at 10%
        
            signal = context.trend
        
            if position_pct < 0.01:
                action = DecisionAction.ABSTAIN
                reason = "No edge - no position"
            else:
                action = self._signal_to_action(signal)
                reason = f"Position size: {position_pct:.1%}"
        
            return self._create_result(action, abs(signal) * position_pct * 10, DecisionUrgency.NORMAL, reason,
                {'kelly': kelly, 'position_pct': position_pct})
        except Exception as e:
            logger.error(f"Error in decide: {e}")
            raise


class RiskBudgetDecision(DecisionConcept):
    """Concept 59: Risk Budget - Allocate risk budget"""
    
    def __init__(self):
        try:
            super().__init__(59, "Risk Budget", DecisionCategory.RISK_AWARE)
            self.daily_risk_used = 0.0
            self.daily_risk_budget = 0.05  # 5% daily
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    def decide(self, context: DecisionContext) -> DecisionResult:
        # Reset daily (simplified)
        try:
            if context.timestamp.hour == 0:
                self.daily_risk_used = 0.0
        
            trade_risk = context.volatility * 0.02  # Risk of this trade
            remaining_budget = self.daily_risk_budget - self.daily_risk_used
        
            signal = context.trend
        
            if remaining_budget <= 0:
                action = DecisionAction.ABSTAIN
                reason = "Daily risk budget exhausted"
                conf = 0.3
            elif trade_risk > remaining_budget:
                # Reduce size to fit budget
                scale = remaining_budget / trade_risk
                signal *= scale
                action = self._signal_to_action(signal)
                reason = f"Scaled to fit budget ({scale:.0%})"
                conf = abs(signal)
            else:
                action = self._signal_to_action(signal)
                reason = f"Budget OK ({remaining_budget:.1%} remaining)"
                conf = abs(signal)
                self.daily_risk_used += trade_risk
        
            return self._create_result(action, conf, DecisionUrgency.NORMAL, reason,
                {'remaining_budget': remaining_budget, 'trade_risk': trade_risk})
        except Exception as e:
            logger.error(f"Error in decide: {e}")
            raise


class ConvexityDecision(DecisionConcept):
    """Concept 60: Convexity - Prefer asymmetric payoffs"""
    
    def __init__(self):
        try:
            super().__init__(60, "Convexity", DecisionCategory.RISK_AWARE)
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    def decide(self, context: DecisionContext) -> DecisionResult:
        # Look for convex opportunities (limited downside, unlimited upside)
        
        # Convexity score: high when potential gain >> potential loss
        try:
            potential_gain = max(0, context.trend) * context.volatility * 2
            potential_loss = max(0, -context.trend) * context.volatility + context.volatility * 0.5
        
            if potential_loss > 0:
                convexity = potential_gain / potential_loss
            else:
                convexity = potential_gain * 10
        
            if convexity > 2:  # Good convexity
                signal = context.trend * 1.3
                reason = f"High convexity ({convexity:.1f}x)"
            elif convexity > 1:
                signal = context.trend
                reason = f"Moderate convexity ({convexity:.1f}x)"
            else:
                signal = context.trend * 0.5
                reason = f"Poor convexity ({convexity:.1f}x)"
        
            return self._create_result(self._signal_to_action(signal), abs(signal), DecisionUrgency.NORMAL, reason,
                {'convexity': convexity, 'potential_gain': potential_gain, 'potential_loss': potential_loss})
        except Exception as e:
            logger.error(f"Error in decide: {e}")
            raise


RISK_CONCEPTS = [
    ValueAtRiskDecision,
    DrawdownProtectionDecision,
    CorrelationRiskDecision,
    TailRiskDecision,
    LiquidityRiskDecision,
    RiskParityDecision,
    StopLossDecision,
    PositionSizingDecision,
    RiskBudgetDecision,
    ConvexityDecision,
]
