import logging
logger = logging.getLogger(__name__)
"""Strategy Performance Tracker and Automatic Rotation System.

This module implements intelligent strategy selection and rotation based on
real-time performance metrics and market conditions.
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from loguru import logger
from .market_regime import MarketRegime
from typing import Set
import numpy
import pandas


class StrategyType(Enum):
    """Available trading strategy types."""
    TREND_FOLLOWING = "trend_following"
    MEAN_REVERSION = "mean_reversion"
    MOMENTUM = "momentum"
    BREAKOUT = "breakout"
    SCALPING = "scalping"
    SWING = "swing"
    ARBITRAGE = "arbitrage"
    SENTIMENT_BASED = "sentiment_based"
    CONSERVATIVE = "conservative"
    AGGRESSIVE = "aggressive"


@dataclass
class StrategyPerformance:
    """Performance metrics for a trading strategy."""
    strategy_type: StrategyType
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    total_pnl: float = 0.0
    max_drawdown: float = 0.0
    sharpe_ratio: float = 0.0
    win_rate: float = 0.0
    avg_win: float = 0.0
    avg_loss: float = 0.0
    profit_factor: float = 0.0
    last_updated: datetime = field(default_factory=datetime.now)
    regime_performance: Dict[MarketRegime, float] = field(default_factory=dict)
    recent_performance: List[float] = field(default_factory=list)
    confidence_score: float = 0.5
    active: bool = True


class StrategySelector:
    """Intelligent strategy selection and rotation system."""
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize the strategy selector.
        
        Args:
            config: Configuration dictionary
        """
        try:
            self.config = config or {}
            self.strategies = {}
            self.current_strategy = None
            self.strategy_history = []
        
            # Performance tracking settings
            self.min_trades_for_evaluation = self.config.get('min_trades_for_evaluation', 10)
            self.performance_window = self.config.get('performance_window', 50)
            self.rotation_threshold = self.config.get('rotation_threshold', 0.15)  # 15% performance difference
            self.confidence_threshold = self.config.get('confidence_threshold', 0.6)
        
            # Strategy weights for different regimes
            self.regime_strategy_weights = self._initialize_regime_weights()
        
            # Initialize strategies
            self._initialize_strategies()
        
            logger.info("StrategySelector initialized with adaptive rotation")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def _initialize_strategies(self):
        """Initialize available trading strategies."""
        try:
            strategy_types = [
                StrategyType.TREND_FOLLOWING,
                StrategyType.MEAN_REVERSION,
                StrategyType.MOMENTUM,
                StrategyType.BREAKOUT,
                StrategyType.SCALPING,
                StrategyType.SWING,
                StrategyType.SENTIMENT_BASED
            ]
        
            for strategy_type in strategy_types:
                self.strategies[strategy_type] = StrategyPerformance(strategy_type=strategy_type)
        
            # Set initial strategy
            self.current_strategy = StrategyType.TREND_FOLLOWING
            logger.info(f"Initialized {len(self.strategies)} strategies")
        except Exception as e:
            logger.error(f"Error in _initialize_strategies: {e}")
            raise
    
    def _initialize_regime_weights(self) -> Dict[MarketRegime, Dict[StrategyType, float]]:
        """Initialize strategy weights for different market regimes."""
        return {
            MarketRegime.TRENDING_BULL: {
                StrategyType.TREND_FOLLOWING: 0.4,
                StrategyType.MOMENTUM: 0.3,
                StrategyType.BREAKOUT: 0.2,
                StrategyType.SWING: 0.1,
                StrategyType.MEAN_REVERSION: 0.0,
                StrategyType.SCALPING: 0.0,
                StrategyType.SENTIMENT_BASED: 0.0
            },
            MarketRegime.TRENDING_BEAR: {
                StrategyType.TREND_FOLLOWING: 0.3,
                StrategyType.MOMENTUM: 0.2,
                StrategyType.MEAN_REVERSION: 0.2,
                StrategyType.SWING: 0.2,
                StrategyType.BREAKOUT: 0.1,
                StrategyType.SCALPING: 0.0,
                StrategyType.SENTIMENT_BASED: 0.0
            },
            MarketRegime.RANGING: {
                StrategyType.MEAN_REVERSION: 0.4,
                StrategyType.SCALPING: 0.3,
                StrategyType.SWING: 0.2,
                StrategyType.SENTIMENT_BASED: 0.1,
                StrategyType.TREND_FOLLOWING: 0.0,
                StrategyType.MOMENTUM: 0.0,
                StrategyType.BREAKOUT: 0.0
            },
            MarketRegime.HIGH_VOLATILITY: {
                StrategyType.BREAKOUT: 0.3,
                StrategyType.MOMENTUM: 0.3,
                StrategyType.SCALPING: 0.2,
                StrategyType.SWING: 0.2,
                StrategyType.TREND_FOLLOWING: 0.0,
                StrategyType.MEAN_REVERSION: 0.0,
                StrategyType.SENTIMENT_BASED: 0.0
            },
            MarketRegime.LOW_VOLATILITY: {
                StrategyType.MEAN_REVERSION: 0.3,
                StrategyType.SCALPING: 0.3,
                StrategyType.SWING: 0.2,
                StrategyType.SENTIMENT_BASED: 0.2,
                StrategyType.TREND_FOLLOWING: 0.0,
                StrategyType.MOMENTUM: 0.0,
                StrategyType.BREAKOUT: 0.0
            },
            MarketRegime.BREAKOUT: {
                StrategyType.BREAKOUT: 0.5,
                StrategyType.MOMENTUM: 0.3,
                StrategyType.TREND_FOLLOWING: 0.2,
                StrategyType.MEAN_REVERSION: 0.0,
                StrategyType.SCALPING: 0.0,
                StrategyType.SWING: 0.0,
                StrategyType.SENTIMENT_BASED: 0.0
            },
            MarketRegime.CRISIS: {
                StrategyType.MEAN_REVERSION: 0.4,
                StrategyType.SWING: 0.3,
                StrategyType.SENTIMENT_BASED: 0.3,
                StrategyType.TREND_FOLLOWING: 0.0,
                StrategyType.MOMENTUM: 0.0,
                StrategyType.BREAKOUT: 0.0,
                StrategyType.SCALPING: 0.0
            }
        }
    
    def update_strategy_performance(self, strategy_type: StrategyType, trade_result: Dict[str, Any]):
        """Update performance metrics for a specific strategy.
        
        Args:
            strategy_type: Type of strategy that generated the trade
            trade_result: Dictionary containing trade results
        """
        try:
            if strategy_type not in self.strategies:
                logger.warning(f"Unknown strategy type: {strategy_type}")
                return
        
            strategy = self.strategies[strategy_type]
            pnl = trade_result.get('pnl', 0.0)
        
            # Update basic metrics
            strategy.total_trades += 1
            strategy.total_pnl += pnl
        
            if pnl > 0:
                strategy.winning_trades += 1
            else:
                strategy.losing_trades += 1
        
            # Update recent performance
            strategy.recent_performance.append(pnl)
            if len(strategy.recent_performance) > self.performance_window:
                strategy.recent_performance.pop(0)
        
            # Calculate derived metrics
            self._calculate_strategy_metrics(strategy)
        
            # Update regime-specific performance
            regime = trade_result.get('regime')
            if regime and isinstance(regime, MarketRegime):
                if regime not in strategy.regime_performance:
                    strategy.regime_performance[regime] = 0.0
                strategy.regime_performance[regime] = (
                    strategy.regime_performance[regime] * 0.9 + pnl * 0.1
                )  # Exponential moving average
        
            strategy.last_updated = datetime.now()
        
            # Check if strategy rotation is needed
            self._evaluate_strategy_rotation()
        
            logger.debug(f"Updated performance for {strategy_type.value}: "
                        f"Total PnL: {strategy.total_pnl:.2f}, Win Rate: {strategy.win_rate:.2%}")
        except Exception as e:
            logger.error(f"Error in update_strategy_performance: {e}")
            raise
    
    def _calculate_strategy_metrics(self, strategy: StrategyPerformance):
        """Calculate derived performance metrics for a strategy."""
        try:
            if strategy.total_trades == 0:
                return
        
            # Win rate
            strategy.win_rate = strategy.winning_trades / strategy.total_trades
        
            # Average win/loss
            if strategy.winning_trades > 0:
                wins = [pnl for pnl in strategy.recent_performance if pnl > 0]
                strategy.avg_win = np.mean(wins) if wins else 0.0
        
            if strategy.losing_trades > 0:
                losses = [abs(pnl) for pnl in strategy.recent_performance if pnl < 0]
                strategy.avg_loss = np.mean(losses) if losses else 0.0
        
            # Profit factor
            total_wins = sum(pnl for pnl in strategy.recent_performance if pnl > 0)
            total_losses = abs(sum(pnl for pnl in strategy.recent_performance if pnl < 0))
            strategy.profit_factor = total_wins / total_losses if total_losses > 0 else float('inf')
        
            # Sharpe ratio (simplified)
            if len(strategy.recent_performance) > 1:
                returns = np.array(strategy.recent_performance)
                strategy.sharpe_ratio = np.mean(returns) / (np.std(returns) + 1e-6)
        
            # Max drawdown
            if strategy.recent_performance:
                cumulative = np.cumsum(strategy.recent_performance)
                running_max = np.maximum.accumulate(cumulative)
                drawdown = (cumulative - running_max) / (running_max + 1e-6)
                strategy.max_drawdown = abs(np.min(drawdown))
        
            # Confidence score based on multiple factors
            strategy.confidence_score = self._calculate_confidence_score(strategy)
        except Exception as e:
            logger.error(f"Error in _calculate_strategy_metrics: {e}")
            raise
    
    def _calculate_confidence_score(self, strategy: StrategyPerformance) -> float:
        """Calculate confidence score for a strategy."""
        try:
            if strategy.total_trades < self.min_trades_for_evaluation:
                return 0.3  # Low confidence with insufficient data
        
            # Factors contributing to confidence
            factors = []
        
            # Win rate factor
            win_rate_factor = min(1.0, strategy.win_rate * 2)  # 50% win rate = 1.0
            factors.append(win_rate_factor * 0.3)
        
            # Profit factor
            pf_factor = min(1.0, strategy.profit_factor / 2.0)  # PF of 2.0 = 1.0
            factors.append(pf_factor * 0.3)
        
            # Sharpe ratio factor
            sharpe_factor = min(1.0, max(0.0, strategy.sharpe_ratio / 2.0))  # Sharpe of 2.0 = 1.0
            factors.append(sharpe_factor * 0.2)
        
            # Consistency factor (low drawdown)
            consistency_factor = max(0.0, 1.0 - strategy.max_drawdown * 2)
            factors.append(consistency_factor * 0.2)
        
            return sum(factors)
        except Exception as e:
            logger.error(f"Error in _calculate_confidence_score: {e}")
            raise
    
    def select_best_strategy(self, regime: Optional[MarketRegime] = None) -> StrategyType:
        """Select the best strategy based on performance and market regime.
        
        Args:
            regime: Current market regime
            
        Returns:
            Best strategy type for current conditions
        """
        try:
            if not regime:
                # Select based on overall performance
                eligible_strategies = [
                    (strategy_type, perf) for strategy_type, perf in self.strategies.items()
                    if perf.active and perf.confidence_score >= self.confidence_threshold
                ]
            
                if not eligible_strategies:
                    # Fallback to best performing strategy regardless of confidence
                    eligible_strategies = [(st, perf) for st, perf in self.strategies.items() if perf.active]
            
                if eligible_strategies:
                    best_strategy = max(eligible_strategies, key=lambda x: x[1].total_pnl)
                    return best_strategy[0]
            
                return StrategyType.TREND_FOLLOWING  # Default fallback
        
            # Regime-based selection
            regime_weights = self.regime_strategy_weights.get(regime, {})
        
            # Calculate weighted scores
            strategy_scores = {}
            for strategy_type, weight in regime_weights.items():
                if weight == 0 or strategy_type not in self.strategies:
                    continue
            
                strategy = self.strategies[strategy_type]
                if not strategy.active:
                    continue
            
                # Combine regime weight with performance
                performance_score = strategy.confidence_score * strategy.total_pnl
                regime_performance = strategy.regime_performance.get(regime, 0.0)
            
                # Weighted score
                strategy_scores[strategy_type] = (
                    weight * 0.4 +  # Regime suitability
                    performance_score * 0.4 +  # Overall performance
                    regime_performance * 0.2  # Regime-specific performance
                )
        
            if strategy_scores:
                best_strategy = max(strategy_scores.items(), key=lambda x: x[1])
                logger.info(f"Selected strategy {best_strategy[0].value} for regime {regime.value} "
                           f"(score: {best_strategy[1]:.3f})")
                return best_strategy[0]
        
            # Fallback to highest weighted strategy for regime
            if regime_weights:
                return max(regime_weights.items(), key=lambda x: x[1])[0]
        
            return StrategyType.TREND_FOLLOWING
        except Exception as e:
            logger.error(f"Error in select_best_strategy: {e}")
            raise
    
    def _evaluate_strategy_rotation(self):
        """Evaluate if strategy rotation is needed."""
        try:
            if not self.current_strategy:
                return
        
            current_perf = self.strategies[self.current_strategy]
        
            # Don't rotate if current strategy has insufficient data
            if current_perf.total_trades < self.min_trades_for_evaluation:
                return
        
            # Find best alternative strategy
            alternatives = [
                (st, perf) for st, perf in self.strategies.items()
                if st != self.current_strategy and perf.active and 
                perf.total_trades >= self.min_trades_for_evaluation
            ]
        
            if not alternatives:
                return
        
            best_alternative = max(alternatives, key=lambda x: x[1].confidence_score)
            best_alt_type, best_alt_perf = best_alternative
        
            # Calculate performance difference
            current_score = current_perf.confidence_score
            alternative_score = best_alt_perf.confidence_score
        
            performance_diff = (alternative_score - current_score) / (current_score + 1e-6)
        
            # Rotate if alternative is significantly better
            if performance_diff > self.rotation_threshold:
                logger.info(f"Rotating strategy from {self.current_strategy.value} to {best_alt_type.value} "
                           f"(improvement: {performance_diff:.2%})")
            
                self.strategy_history.append({
                    'timestamp': datetime.now(),
                    'from_strategy': self.current_strategy,
                    'to_strategy': best_alt_type,
                    'reason': 'performance_improvement',
                    'improvement': performance_diff
                })
            
                self.current_strategy = best_alt_type
        except Exception as e:
            logger.error(f"Error in _evaluate_strategy_rotation: {e}")
            raise
    
    def force_strategy_rotation(self, new_strategy: StrategyType, reason: str = "manual"):
        """Force rotation to a specific strategy.
        
        Args:
            new_strategy: Strategy to rotate to
            reason: Reason for rotation
        """
        try:
            if new_strategy not in self.strategies:
                logger.error(f"Cannot rotate to unknown strategy: {new_strategy}")
                return
        
            old_strategy = self.current_strategy
            self.current_strategy = new_strategy
        
            self.strategy_history.append({
                'timestamp': datetime.now(),
                'from_strategy': old_strategy,
                'to_strategy': new_strategy,
                'reason': reason,
                'improvement': 0.0
            })
        
            logger.info(f"Forced strategy rotation from {old_strategy.value if old_strategy else 'None'} "
                       f"to {new_strategy.value} (reason: {reason})")
        except Exception as e:
            logger.error(f"Error in force_strategy_rotation: {e}")
            raise
    
    def disable_strategy(self, strategy_type: StrategyType, reason: str = "poor_performance"):
        """Disable a strategy from selection.
        
        Args:
            strategy_type: Strategy to disable
            reason: Reason for disabling
        """
        try:
            if strategy_type in self.strategies:
                self.strategies[strategy_type].active = False
                logger.warning(f"Disabled strategy {strategy_type.value} (reason: {reason})")
            
                # If current strategy is disabled, select new one
                if self.current_strategy == strategy_type:
                    self.current_strategy = self.select_best_strategy()
                    logger.info(f"Switched to {self.current_strategy.value} after disabling current strategy")
        except Exception as e:
            logger.error(f"Error in disable_strategy: {e}")
            raise
    
    def get_strategy_summary(self) -> Dict[str, Any]:
        """Get comprehensive strategy performance summary."""
        try:
            summary = {
                'current_strategy': self.current_strategy.value if self.current_strategy else None,
                'total_rotations': len(self.strategy_history),
                'strategies': {}
            }
        
            for strategy_type, perf in self.strategies.items():
                summary['strategies'][strategy_type.value] = {
                    'active': perf.active,
                    'total_trades': perf.total_trades,
                    'win_rate': perf.win_rate,
                    'total_pnl': perf.total_pnl,
                    'sharpe_ratio': perf.sharpe_ratio,
                    'max_drawdown': perf.max_drawdown,
                    'confidence_score': perf.confidence_score,
                    'last_updated': perf.last_updated.isoformat()
                }
        
            # Recent rotations
            summary['recent_rotations'] = self.strategy_history[-5:] if self.strategy_history else []
        
            return summary
        except Exception as e:
            logger.error(f"Error in get_strategy_summary: {e}")
            raise
