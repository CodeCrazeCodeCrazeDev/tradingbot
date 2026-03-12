"""
Strategic Intelligence
======================

Meta-strategy selection and portfolio optimization system.
Makes high-level strategic decisions about trading approach.

Features:
- Meta-strategy selection based on market conditions
- Multi-strategy portfolio optimization
- Risk-reward optimization
- Capital allocation across strategies
- Strategy performance tracking
- Dynamic strategy weighting
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import logging

logger = logging.getLogger(__name__)

try:
    from scipy.optimize import minimize
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False
    logger.debug("scipy not available for portfolio optimization")


class StrategyType(Enum):
    """Available strategy types"""
    TREND_FOLLOWING = "trend_following"
    MEAN_REVERSION = "mean_reversion"
    BREAKOUT = "breakout"
    MOMENTUM = "momentum"
    SCALPING = "scalping"
    SWING = "swing"
    POSITION = "position"
    ARBITRAGE = "arbitrage"
    MARKET_MAKING = "market_making"


class MarketCondition(Enum):
    """Market condition types"""
    TRENDING = "trending"
    RANGING = "ranging"
    VOLATILE = "volatile"
    CALM = "calm"
    UNCERTAIN = "uncertain"


@dataclass
class StrategyAllocation:
    """Capital allocation for a strategy"""
    strategy_type: StrategyType
    allocation_percentage: float
    expected_return: float
    expected_risk: float
    sharpe_ratio: float
    max_drawdown: float
    confidence: float
    reason: str


@dataclass
class StrategicDecision:
    """High-level strategic decision"""
    decision_type: str
    primary_strategy: StrategyType
    backup_strategies: List[StrategyType]
    allocations: List[StrategyAllocation]
    market_condition: MarketCondition
    confidence: float
    reasoning: List[str]
    expected_performance: Dict[str, float]
    decided_at: datetime


@dataclass
class StrategyPerformanceMetrics:
    """Performance metrics for a strategy"""
    strategy_type: StrategyType
    total_trades: int = 0
    win_rate: float = 0.0
    profit_factor: float = 0.0
    sharpe_ratio: float = 0.0
    sortino_ratio: float = 0.0
    max_drawdown: float = 0.0
    avg_return: float = 0.0
    volatility: float = 0.0
    calmar_ratio: float = 0.0
    last_updated: datetime = field(default_factory=datetime.now)


class StrategicIntelligence:
    """
    High-level strategic decision making system.
    
    Decides:
    - Which strategies to use
    - How to allocate capital
    - When to switch strategies
    - Risk-reward optimization
    - Portfolio composition
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Strategic settings
        self.total_capital = self.config.get('total_capital', 10000.0)
        self.max_strategies = self.config.get('max_strategies', 3)
        self.rebalance_threshold = self.config.get('rebalance_threshold', 0.1)
        
        # Performance tracking
        self.strategy_metrics: Dict[StrategyType, StrategyPerformanceMetrics] = {}
        self.decision_history: List[StrategicDecision] = []
        self.current_allocations: List[StrategyAllocation] = []
        
        # Initialize default metrics
        self._init_strategy_metrics()
        
        logger.info("Strategic Intelligence initialized")
    
    def _init_strategy_metrics(self):
        """Initialize metrics for all strategy types"""
        for strategy_type in StrategyType:
            self.strategy_metrics[strategy_type] = StrategyPerformanceMetrics(
                strategy_type=strategy_type
            )
    
    async def select_optimal_strategy(
        self,
        market_state: Dict[str, Any],
        available_strategies: Optional[List[StrategyType]] = None
    ) -> StrategicDecision:
        """
        Select optimal strategy mix for current market conditions.
        
        Args:
            market_state: Current market conditions
            available_strategies: List of available strategies (default: all)
        
        Returns:
            Strategic decision with allocations
        """
        try:
            if available_strategies is None:
                available_strategies = list(StrategyType)
            
            # Classify market condition
            market_condition = self._classify_market_condition(market_state)
            
            # Score each strategy for current conditions
            strategy_scores = self._score_strategies(
                market_state=market_state,
                market_condition=market_condition,
                available_strategies=available_strategies
            )
            
            # Select top strategies
            top_strategies = sorted(
                strategy_scores.items(),
                key=lambda x: x[1]['score'],
                reverse=True
            )[:self.max_strategies]
            
            # Optimize allocations
            allocations = await self._optimize_allocations(
                strategies=top_strategies,
                market_state=market_state
            )
            
            # Create strategic decision
            decision = StrategicDecision(
                decision_type='strategy_selection',
                primary_strategy=top_strategies[0][0],
                backup_strategies=[s[0] for s in top_strategies[1:]],
                allocations=allocations,
                market_condition=market_condition,
                confidence=top_strategies[0][1]['score'],
                reasoning=self._generate_reasoning(
                    market_condition=market_condition,
                    selected_strategies=top_strategies,
                    market_state=market_state
                ),
                expected_performance=self._calculate_expected_performance(allocations),
                decided_at=datetime.now()
            )
            
            self.decision_history.append(decision)
            self.current_allocations = allocations
            
            # Keep only recent history
            if len(self.decision_history) > 500:
                self.decision_history = self.decision_history[-500:]
            
            logger.info(f"Selected strategy: {decision.primary_strategy.value} "
                       f"(confidence: {decision.confidence:.2f})")
            
            return decision
            
        except Exception as e:
            logger.error(f"Error selecting optimal strategy: {e}")
            return self._get_default_decision(market_state)
    
    def _classify_market_condition(self, market_state: Dict[str, Any]) -> MarketCondition:
        """Classify current market condition"""
        try:
            volatility = market_state.get('volatility', 0.01)
            trend_strength = market_state.get('trend_strength', 0.0)
            
            # High volatility
            if volatility > 0.02:
                return MarketCondition.VOLATILE
            
            # Low volatility
            if volatility < 0.005:
                return MarketCondition.CALM
            
            # Strong trend
            if trend_strength > 0.6:
                return MarketCondition.TRENDING
            
            # Weak trend
            if trend_strength < 0.3:
                return MarketCondition.RANGING
            
            return MarketCondition.UNCERTAIN
            
        except Exception:
            return MarketCondition.UNCERTAIN
    
    def _score_strategies(
        self,
        market_state: Dict[str, Any],
        market_condition: MarketCondition,
        available_strategies: List[StrategyType]
    ) -> Dict[StrategyType, Dict[str, float]]:
        """Score each strategy for current market conditions"""
        
        scores = {}
        
        for strategy in available_strategies:
            # Base score from historical performance
            metrics = self.strategy_metrics.get(strategy)
            base_score = 0.5
            
            if metrics and metrics.total_trades > 10:
                base_score = (
                    metrics.win_rate * 0.3 +
                    min(metrics.sharpe_ratio / 2.0, 0.5) * 0.3 +
                    (1.0 - metrics.max_drawdown) * 0.2 +
                    min(metrics.profit_factor / 2.0, 0.5) * 0.2
                )
            
            # Adjust for market conditions
            condition_multiplier = self._get_condition_multiplier(
                strategy=strategy,
                condition=market_condition,
                market_state=market_state
            )
            
            final_score = base_score * condition_multiplier
            
            scores[strategy] = {
                'score': final_score,
                'base_score': base_score,
                'condition_multiplier': condition_multiplier
            }
        
        return scores
    
    def _get_condition_multiplier(
        self,
        strategy: StrategyType,
        condition: MarketCondition,
        market_state: Dict[str, Any]
    ) -> float:
        """Get multiplier based on strategy fit for market condition"""
        
        # Strategy-condition compatibility matrix
        compatibility = {
            StrategyType.TREND_FOLLOWING: {
                MarketCondition.TRENDING: 1.5,
                MarketCondition.RANGING: 0.5,
                MarketCondition.VOLATILE: 0.8,
                MarketCondition.CALM: 1.0,
                MarketCondition.UNCERTAIN: 0.7
            },
            StrategyType.MEAN_REVERSION: {
                MarketCondition.TRENDING: 0.6,
                MarketCondition.RANGING: 1.5,
                MarketCondition.VOLATILE: 0.7,
                MarketCondition.CALM: 1.3,
                MarketCondition.UNCERTAIN: 1.0
            },
            StrategyType.BREAKOUT: {
                MarketCondition.TRENDING: 1.2,
                MarketCondition.RANGING: 1.3,
                MarketCondition.VOLATILE: 1.4,
                MarketCondition.CALM: 0.6,
                MarketCondition.UNCERTAIN: 0.9
            },
            StrategyType.MOMENTUM: {
                MarketCondition.TRENDING: 1.4,
                MarketCondition.RANGING: 0.7,
                MarketCondition.VOLATILE: 1.1,
                MarketCondition.CALM: 0.8,
                MarketCondition.UNCERTAIN: 0.8
            },
            StrategyType.SCALPING: {
                MarketCondition.TRENDING: 0.9,
                MarketCondition.RANGING: 1.2,
                MarketCondition.VOLATILE: 1.3,
                MarketCondition.CALM: 0.7,
                MarketCondition.UNCERTAIN: 1.0
            },
            StrategyType.SWING: {
                MarketCondition.TRENDING: 1.3,
                MarketCondition.RANGING: 0.9,
                MarketCondition.VOLATILE: 0.8,
                MarketCondition.CALM: 1.1,
                MarketCondition.UNCERTAIN: 1.0
            },
            StrategyType.POSITION: {
                MarketCondition.TRENDING: 1.4,
                MarketCondition.RANGING: 0.6,
                MarketCondition.VOLATILE: 0.7,
                MarketCondition.CALM: 1.2,
                MarketCondition.UNCERTAIN: 0.8
            },
            StrategyType.ARBITRAGE: {
                MarketCondition.TRENDING: 0.8,
                MarketCondition.RANGING: 1.1,
                MarketCondition.VOLATILE: 1.4,
                MarketCondition.CALM: 1.0,
                MarketCondition.UNCERTAIN: 1.0
            },
            StrategyType.MARKET_MAKING: {
                MarketCondition.TRENDING: 0.7,
                MarketCondition.RANGING: 1.4,
                MarketCondition.VOLATILE: 0.6,
                MarketCondition.CALM: 1.3,
                MarketCondition.UNCERTAIN: 1.0
            }
        }
        
        return compatibility.get(strategy, {}).get(condition, 1.0)
    
    async def _optimize_allocations(
        self,
        strategies: List[Tuple[StrategyType, Dict[str, float]]],
        market_state: Dict[str, Any]
    ) -> List[StrategyAllocation]:
        """Optimize capital allocation across strategies"""
        
        try:
            if not strategies:
                return []
            
            if SCIPY_AVAILABLE and len(strategies) > 1:
                # Use optimization
                allocations = self._optimize_with_scipy(strategies, market_state)
            else:
                # Simple allocation based on scores
                allocations = self._simple_allocation(strategies, market_state)
            
            return allocations
            
        except Exception as e:
            logger.error(f"Error optimizing allocations: {e}")
            return self._simple_allocation(strategies, market_state)
    
    def _optimize_with_scipy(
        self,
        strategies: List[Tuple[StrategyType, Dict[str, float]]],
        market_state: Dict[str, Any]
    ) -> List[StrategyAllocation]:
        """Optimize allocations using scipy"""
        
        n = len(strategies)
        
        # Expected returns and risks
        returns = []
        risks = []
        
        for strategy, score_data in strategies:
            metrics = self.strategy_metrics.get(strategy)
            
            if metrics and metrics.total_trades > 0:
                returns.append(metrics.avg_return)
                risks.append(metrics.volatility)
            else:
                returns.append(score_data['score'] * 0.01)
                risks.append(0.01)
        
        returns = np.array(returns)
        risks = np.array(risks)
        
        # Objective: maximize Sharpe ratio
        def objective(weights):
            portfolio_return = np.sum(weights * returns)
            portfolio_risk = np.sqrt(np.sum((weights * risks) ** 2))
            
            if portfolio_risk == 0:
                return 0
            
            sharpe = portfolio_return / portfolio_risk
            return -sharpe  # Minimize negative Sharpe
        
        # Constraints
        constraints = [
            {'type': 'eq', 'fun': lambda w: np.sum(w) - 1.0}  # Sum to 1
        ]
        
        # Bounds (0 to 1 for each weight)
        bounds = [(0.0, 1.0) for _ in range(n)]
        
        # Initial guess (equal weights)
        x0 = np.array([1.0 / n] * n)
        
        # Optimize
        result = minimize(
            objective,
            x0,
            method='SLSQP',
            bounds=bounds,
            constraints=constraints
        )
        
        if result.success:
            weights = result.x
        else:
            # Fall back to score-based weights
            scores = np.array([s[1]['score'] for s in strategies])
            weights = scores / np.sum(scores)
        
        # Create allocations
        allocations = []
        for i, (strategy, score_data) in enumerate(strategies):
            metrics = self.strategy_metrics.get(strategy)
            
            allocations.append(StrategyAllocation(
                strategy_type=strategy,
                allocation_percentage=float(weights[i] * 100),
                expected_return=float(returns[i]),
                expected_risk=float(risks[i]),
                sharpe_ratio=metrics.sharpe_ratio if metrics else 0.0,
                max_drawdown=metrics.max_drawdown if metrics else 0.0,
                confidence=score_data['score'],
                reason=f"Optimized allocation based on risk-return profile"
            ))
        
        return allocations
    
    def _simple_allocation(
        self,
        strategies: List[Tuple[StrategyType, Dict[str, float]]],
        market_state: Dict[str, Any]
    ) -> List[StrategyAllocation]:
        """Simple score-based allocation"""
        
        total_score = sum(s[1]['score'] for s in strategies)
        
        allocations = []
        for strategy, score_data in strategies:
            metrics = self.strategy_metrics.get(strategy)
            
            allocation_pct = (score_data['score'] / total_score) * 100
            
            allocations.append(StrategyAllocation(
                strategy_type=strategy,
                allocation_percentage=allocation_pct,
                expected_return=metrics.avg_return if metrics else 0.01,
                expected_risk=metrics.volatility if metrics else 0.01,
                sharpe_ratio=metrics.sharpe_ratio if metrics else 0.0,
                max_drawdown=metrics.max_drawdown if metrics else 0.0,
                confidence=score_data['score'],
                reason=f"Score-based allocation ({score_data['score']:.2f})"
            ))
        
        return allocations
    
    def _generate_reasoning(
        self,
        market_condition: MarketCondition,
        selected_strategies: List[Tuple[StrategyType, Dict[str, float]]],
        market_state: Dict[str, Any]
    ) -> List[str]:
        """Generate human-readable reasoning for decision"""
        
        reasoning = []
        
        # Market condition reasoning
        reasoning.append(f"Market condition: {market_condition.value}")
        
        volatility = market_state.get('volatility', 0.0)
        if volatility > 0.02:
            reasoning.append("High volatility detected - favoring adaptive strategies")
        elif volatility < 0.005:
            reasoning.append("Low volatility - suitable for range-bound strategies")
        
        trend_strength = market_state.get('trend_strength', 0.0)
        if trend_strength > 0.6:
            reasoning.append("Strong trend detected - trend-following strategies preferred")
        elif trend_strength < 0.3:
            reasoning.append("Weak trend - mean reversion strategies suitable")
        
        # Strategy selection reasoning
        primary = selected_strategies[0]
        reasoning.append(
            f"Primary strategy: {primary[0].value} "
            f"(score: {primary[1]['score']:.2f})"
        )
        
        if len(selected_strategies) > 1:
            backups = [s[0].value for s in selected_strategies[1:]]
            reasoning.append(f"Backup strategies: {', '.join(backups)}")
        
        return reasoning
    
    def _calculate_expected_performance(
        self,
        allocations: List[StrategyAllocation]
    ) -> Dict[str, float]:
        """Calculate expected portfolio performance"""
        
        if not allocations:
            return {
                'expected_return': 0.0,
                'expected_risk': 0.0,
                'expected_sharpe': 0.0
            }
        
        # Weighted average
        total_return = sum(
            a.expected_return * (a.allocation_percentage / 100)
            for a in allocations
        )
        
        total_risk = np.sqrt(sum(
            (a.expected_risk * (a.allocation_percentage / 100)) ** 2
            for a in allocations
        ))
        
        sharpe = total_return / total_risk if total_risk > 0 else 0.0
        
        return {
            'expected_return': float(total_return),
            'expected_risk': float(total_risk),
            'expected_sharpe': float(sharpe)
        }
    
    def _get_default_decision(self, market_state: Dict[str, Any]) -> StrategicDecision:
        """Get default decision in case of error"""
        
        default_allocation = StrategyAllocation(
            strategy_type=StrategyType.TREND_FOLLOWING,
            allocation_percentage=100.0,
            expected_return=0.01,
            expected_risk=0.01,
            sharpe_ratio=1.0,
            max_drawdown=0.1,
            confidence=0.5,
            reason="Default allocation"
        )
        
        return StrategicDecision(
            decision_type='default',
            primary_strategy=StrategyType.TREND_FOLLOWING,
            backup_strategies=[],
            allocations=[default_allocation],
            market_condition=MarketCondition.UNCERTAIN,
            confidence=0.5,
            reasoning=["Default decision due to error"],
            expected_performance={'expected_return': 0.01, 'expected_risk': 0.01, 'expected_sharpe': 1.0},
            decided_at=datetime.now()
        )
    
    async def update_strategy_performance(
        self,
        strategy_type: StrategyType,
        trade_result: Dict[str, Any]
    ):
        """Update performance metrics for a strategy"""
        
        try:
            if strategy_type not in self.strategy_metrics:
                self.strategy_metrics[strategy_type] = StrategyPerformanceMetrics(
                    strategy_type=strategy_type
                )
            
            metrics = self.strategy_metrics[strategy_type]
            
            profit = trade_result.get('profit', 0.0)
            
            metrics.total_trades += 1
            
            # Update win rate
            if profit > 0:
                wins = metrics.win_rate * (metrics.total_trades - 1) + 1
                metrics.win_rate = wins / metrics.total_trades
            else:
                wins = metrics.win_rate * (metrics.total_trades - 1)
                metrics.win_rate = wins / metrics.total_trades
            
            # Update average return
            metrics.avg_return = (
                metrics.avg_return * (metrics.total_trades - 1) + profit
            ) / metrics.total_trades
            
            metrics.last_updated = datetime.now()
            
            logger.debug(f"Updated performance for {strategy_type.value}")
            
        except Exception as e:
            logger.error(f"Error updating strategy performance: {e}")
    
    async def should_rebalance(self) -> bool:
        """Check if portfolio should be rebalanced"""
        
        try:
            if not self.decision_history:
                return True
            
            last_decision = self.decision_history[-1]
            time_since_decision = datetime.now() - last_decision.decided_at
            
            # Rebalance if it's been more than 4 hours
            if time_since_decision > timedelta(hours=4):
                return True
            
            # Rebalance if primary strategy performance degraded
            primary_metrics = self.strategy_metrics.get(last_decision.primary_strategy)
            
            if primary_metrics and primary_metrics.total_trades > 20:
                if primary_metrics.win_rate < 0.4:
                    logger.info("Rebalancing due to poor primary strategy performance")
                    return True
            
            return False
            
        except Exception:
            return False
    
    def get_strategic_statistics(self) -> Dict[str, Any]:
        """Get strategic intelligence statistics"""
        
        return {
            'total_decisions': len(self.decision_history),
            'current_allocations': [
                {
                    'strategy': a.strategy_type.value,
                    'allocation': a.allocation_percentage,
                    'confidence': a.confidence
                }
                for a in self.current_allocations
            ],
            'strategy_performance': {
                strategy.value: {
                    'total_trades': metrics.total_trades,
                    'win_rate': metrics.win_rate,
                    'sharpe_ratio': metrics.sharpe_ratio,
                    'avg_return': metrics.avg_return
                }
                for strategy, metrics in self.strategy_metrics.items()
                if metrics.total_trades > 0
            },
            'recent_decisions': [
                {
                    'timestamp': d.decided_at.isoformat(),
                    'primary_strategy': d.primary_strategy.value,
                    'market_condition': d.market_condition.value,
                    'confidence': d.confidence
                }
                for d in self.decision_history[-5:]
            ]
        }
