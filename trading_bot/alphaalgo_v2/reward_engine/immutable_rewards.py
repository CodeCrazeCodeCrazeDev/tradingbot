"""
from typing import Any, List, Optional
AlphaAlgo V2 Immutable Reward Model

CRITICAL: This module contains the FROZEN reward function that defines
what "success" means for the trading system.

THE REWARD MODEL CANNOT BE MODIFIED BY:
- The evolution engine
- Any automated process
- Any AI component

Only human developers can modify this file, and any changes require
extensive review and testing.

Design Principles:
1. Immutability - The reward function is frozen
2. Transparency - Clear, understandable reward calculation
3. Safety First - Risk penalties are always applied
4. Long-term Focus - Rewards consistency over short-term gains
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Final
import math

from ..core.interfaces import IRewardModel
from ..core.types import TradeResult, Trade
from ..core.constants import (
    MAX_RISK_PER_TRADE,
    MAX_DAILY_LOSS,
    MAX_DRAWDOWN,
    MIN_SHARPE_RATIO,
    MIN_WIN_RATE,
    REWARD_WEIGHTS,
)

import logging
logger = logging.getLogger(__name__)



@dataclass(frozen=True)
class RewardComponents:
    """
    Breakdown of reward calculation components
    
    This is frozen to ensure immutability.
    """
    profit_component: float
    risk_adjusted_component: float
    consistency_component: float
    drawdown_penalty: float
    total_reward: float
    
    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary"""
        return {
            "profit_component": self.profit_component,
            "risk_adjusted_component": self.risk_adjusted_component,
            "consistency_component": self.consistency_component,
            "drawdown_penalty": self.drawdown_penalty,
            "total_reward": self.total_reward,
        }


class ImmutableRewardModel(IRewardModel):
    """
    THE REWARD MODEL THAT NEVER CHANGES
    
    This class defines what "success" means for the trading bot.
    Once set, this CANNOT be modified by the evolution layer.
    
    Reward Calculation:
    - Profit Factor: 40% weight
    - Sharpe Ratio: 30% weight
    - Win Rate: 20% weight
    - Drawdown Penalty: 10% weight (subtracted)
    
    Constraints (IMMUTABLE):
    - Max Risk Per Trade: 2%
    - Max Daily Loss: 5%
    - Max Drawdown: 20%
    - Min Sharpe Ratio: 1.5
    - Min Win Rate: 45%
    """
    
    # IMMUTABLE WEIGHTS (Cannot be changed)
    PROFIT_WEIGHT: Final[float] = 0.40
    SHARPE_WEIGHT: Final[float] = 0.30
    WINRATE_WEIGHT: Final[float] = 0.20
    DRAWDOWN_WEIGHT: Final[float] = 0.10
    
    # IMMUTABLE CONSTRAINTS (Cannot be changed)
    MAX_RISK_PER_TRADE: Final[float] = MAX_RISK_PER_TRADE
    MAX_DAILY_LOSS: Final[float] = MAX_DAILY_LOSS
    MAX_DRAWDOWN: Final[float] = MAX_DRAWDOWN
    MIN_SHARPE_RATIO: Final[float] = MIN_SHARPE_RATIO
    MIN_WIN_RATE: Final[float] = MIN_WIN_RATE
    
    def __init__(self):
        """Initialize the immutable reward model"""
        # Verify weights sum to 1.0
        try:
            total_weight = (
                self.PROFIT_WEIGHT +
                self.SHARPE_WEIGHT +
                self.WINRATE_WEIGHT +
                self.DRAWDOWN_WEIGHT
            )
            assert abs(total_weight - 1.0) < 0.001, "Weights must sum to 1.0"
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def calculate_reward(self, trade_result: TradeResult) -> float:
        """
        Calculate reward for a single trade
        
        THIS FUNCTION IS IMMUTABLE AND CANNOT BE MODIFIED BY EVOLUTION
        
        Args:
            trade_result: Result of completed trade
            
        Returns:
            Reward score (higher is better, range: -1.0 to 2.0)
        """
        try:
            components = self._calculate_components(trade_result)
            return components.total_reward
        except Exception as e:
            logger.error(f"Error in calculate_reward: {e}")
            raise
    
    def calculate_reward_with_breakdown(
        self,
        trade_result: TradeResult
    ) -> RewardComponents:
        """
        Calculate reward with full breakdown
        
        Args:
            trade_result: Result of completed trade
            
        Returns:
            RewardComponents with detailed breakdown
        """
        return self._calculate_components(trade_result)
    
    def _calculate_components(self, trade_result: TradeResult) -> RewardComponents:
        """
        Calculate all reward components
        
        THIS LOGIC IS FROZEN AND CANNOT BE MODIFIED
        """
        # Profit component (40% weight)
        # Normalize profit factor to 0-1 range (assuming max PF of 3.0)
        try:
            profit_factor = min(trade_result.profit_factor, 3.0) / 3.0
            profit_component = profit_factor * self.PROFIT_WEIGHT
        
            # Risk-adjusted component (30% weight)
            # Normalize Sharpe ratio to 0-1 range (assuming max Sharpe of 3.0)
            sharpe = min(max(trade_result.sharpe_ratio, 0.0), 3.0) / 3.0
            risk_adjusted_component = sharpe * self.SHARPE_WEIGHT
        
            # Consistency component (20% weight)
            # Win rate is already 0-1
            win_rate = min(max(trade_result.win_rate, 0.0), 1.0)
            consistency_component = win_rate * self.WINRATE_WEIGHT
        
            # Drawdown penalty (10% weight, subtracted)
            # Higher drawdown = higher penalty
            drawdown = min(trade_result.max_drawdown, 1.0)
            drawdown_penalty = drawdown * self.DRAWDOWN_WEIGHT
        
            # Total reward
            total_reward = (
                profit_component +
                risk_adjusted_component +
                consistency_component -
                drawdown_penalty
            )
        
            return RewardComponents(
                profit_component=profit_component,
                risk_adjusted_component=risk_adjusted_component,
                consistency_component=consistency_component,
                drawdown_penalty=drawdown_penalty,
                total_reward=total_reward,
            )
        except Exception as e:
            logger.error(f"Error in _calculate_components: {e}")
            raise
    
    def calculate_portfolio_reward(
        self,
        trades: List[TradeResult],
        period_days: int = 30
    ) -> float:
        """
        Calculate portfolio-level reward over a period
        
        THIS FUNCTION IS IMMUTABLE AND CANNOT BE MODIFIED BY EVOLUTION
        
        Args:
            trades: List of trade results
            period_days: Evaluation period in days
            
        Returns:
            Portfolio reward score
        """
        try:
            if not trades:
                return 0.0
        
            # Calculate aggregate metrics
            total_profit = sum(t.trade.profit for t in trades)
            total_trades = len(trades)
            winning_trades = sum(1 for t in trades if t.trade.is_winner)
        
            # Win rate
            win_rate = winning_trades / total_trades if total_trades > 0 else 0.0
        
            # Profit factor
            gross_profit = sum(t.trade.profit for t in trades if t.trade.profit > 0)
            gross_loss = abs(sum(t.trade.profit for t in trades if t.trade.profit < 0))
            profit_factor = gross_profit / gross_loss if gross_loss > 0 else 2.0
        
            # Average Sharpe ratio
            avg_sharpe = sum(t.sharpe_ratio for t in trades) / total_trades
        
            # Maximum drawdown
            max_dd = max(t.max_drawdown for t in trades)
        
            # Create aggregate trade result
            aggregate = TradeResult(
                trade=trades[-1].trade if trades else None,
                profit_factor=profit_factor,
                sharpe_ratio=avg_sharpe,
                win_rate=win_rate,
                max_drawdown=max_dd,
                risk_reward_ratio=sum(t.risk_reward_ratio for t in trades) / total_trades,
            )
        
            # Calculate base reward
            base_reward = self.calculate_reward(aggregate)
        
            # Apply time-based scaling (longer periods get slight bonus for consistency)
            time_factor = min(period_days / 30, 2.0)  # Max 2x for 60+ days
        
            return base_reward * (1.0 + (time_factor - 1.0) * 0.1)
        except Exception as e:
            logger.error(f"Error in calculate_portfolio_reward: {e}")
            raise
    
    def get_constraints(self) -> Dict[str, float]:
        """
        Get immutable constraints
        
        Returns:
            Dict of constraint name to value
        """
        return {
            "max_risk_per_trade": self.MAX_RISK_PER_TRADE,
            "max_daily_loss": self.MAX_DAILY_LOSS,
            "max_drawdown": self.MAX_DRAWDOWN,
            "min_sharpe_ratio": self.MIN_SHARPE_RATIO,
            "min_win_rate": self.MIN_WIN_RATE,
        }
    
    def check_constraints(self, metrics: Dict[str, float]) -> Dict[str, bool]:
        """
        Check if metrics violate constraints
        
        Args:
            metrics: Current performance metrics
            
        Returns:
            Dict of constraint name to violation status (True = violated)
        """
        try:
            violations = {}
        
            # Check risk per trade
            if "risk_per_trade" in metrics:
                violations["max_risk_per_trade"] = (
                    metrics["risk_per_trade"] > self.MAX_RISK_PER_TRADE
                )
        
            # Check daily loss
            if "daily_loss" in metrics:
                violations["max_daily_loss"] = (
                    metrics["daily_loss"] > self.MAX_DAILY_LOSS
                )
        
            # Check drawdown
            if "drawdown" in metrics:
                violations["max_drawdown"] = (
                    metrics["drawdown"] > self.MAX_DRAWDOWN
                )
        
            # Check Sharpe ratio (violation if below minimum)
            if "sharpe_ratio" in metrics:
                violations["min_sharpe_ratio"] = (
                    metrics["sharpe_ratio"] < self.MIN_SHARPE_RATIO
                )
        
            # Check win rate (violation if below minimum)
            if "win_rate" in metrics:
                violations["min_win_rate"] = (
                    metrics["win_rate"] < self.MIN_WIN_RATE
                )
        
            return violations
        except Exception as e:
            logger.error(f"Error in check_constraints: {e}")
            raise
    
    def is_acceptable_performance(self, metrics: Dict[str, float]) -> bool:
        """
        Check if overall performance is acceptable
        
        Args:
            metrics: Current performance metrics
            
        Returns:
            True if performance meets minimum standards
        """
        try:
            violations = self.check_constraints(metrics)
        
            # Critical violations that must not occur
            critical_violations = [
                "max_risk_per_trade",
                "max_daily_loss",
                "max_drawdown",
            ]
        
            for violation in critical_violations:
                if violations.get(violation, False):
                    return False
        
            return True
        except Exception as e:
            logger.error(f"Error in is_acceptable_performance: {e}")
            raise
    
    def get_improvement_suggestions(
        self,
        metrics: Dict[str, float]
    ) -> List[str]:
        """
        Get suggestions for improving performance
        
        Args:
            metrics: Current performance metrics
            
        Returns:
            List of improvement suggestions
        """
        try:
            suggestions = []
            violations = self.check_constraints(metrics)
        
            if violations.get("max_risk_per_trade", False):
                suggestions.append(
                    f"Reduce risk per trade from {metrics.get('risk_per_trade', 0):.1%} "
                    f"to below {self.MAX_RISK_PER_TRADE:.1%}"
                )
        
            if violations.get("max_daily_loss", False):
                suggestions.append(
                    f"Reduce daily loss from {metrics.get('daily_loss', 0):.1%} "
                    f"to below {self.MAX_DAILY_LOSS:.1%}"
                )
        
            if violations.get("max_drawdown", False):
                suggestions.append(
                    f"Reduce drawdown from {metrics.get('drawdown', 0):.1%} "
                    f"to below {self.MAX_DRAWDOWN:.1%}"
                )
        
            if violations.get("min_sharpe_ratio", False):
                suggestions.append(
                    f"Improve Sharpe ratio from {metrics.get('sharpe_ratio', 0):.2f} "
                    f"to above {self.MIN_SHARPE_RATIO:.2f}"
                )
        
            if violations.get("min_win_rate", False):
                suggestions.append(
                    f"Improve win rate from {metrics.get('win_rate', 0):.1%} "
                    f"to above {self.MIN_WIN_RATE:.1%}"
                )
        
            return suggestions
        except Exception as e:
            logger.error(f"Error in get_improvement_suggestions: {e}")
            raise


# Singleton instance
_reward_model: Optional[ImmutableRewardModel] = None


def get_reward_model() -> ImmutableRewardModel:
    """Get the singleton reward model instance"""
    try:
        global _reward_model
        if _reward_model is None:
            _reward_model = ImmutableRewardModel()
        return _reward_model
    except Exception as e:
        logger.error(f"Error in get_reward_model: {e}")
        raise
