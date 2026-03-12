"""
AlphaAlgo MSOS - Capital Allocation Governance

Capital allocation is the primary decision variable.

Allocate capital based on:
- Worst-case loss under hostile conditions
- Loss convexity
- Recovery half-life
- Failure correlation with other strategies

Strategies compete on capital efficiency under stress, not returns.

Author: AlphaAlgo MSOS
"""

import logging
import time
from collections import deque
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Deque, Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)


class SurvivalPriority(Enum):
    """Priority levels for survival"""
    CRITICAL = auto()      # Survival at all costs
    HIGH = auto()          # Strong survival focus
    MODERATE = auto()      # Balanced approach
    LOW = auto()           # Performance focus (dangerous)


class AllocationMode(Enum):
    """Capital allocation modes"""
    SURVIVAL = auto()      # Maximize survival probability
    DEFENSIVE = auto()     # Reduce exposure, protect capital
    BALANCED = auto()      # Normal operations
    RECOVERY = auto()      # Post-drawdown recovery mode


@dataclass
class LossConvexity:
    """Loss convexity metrics - how losses accelerate"""
    convexity_score: float = 0.0  # Positive = losses accelerate
    tail_ratio: float = 0.0  # Ratio of tail losses to normal losses
    loss_clustering: float = 0.0  # How clustered losses are
    worst_case_multiple: float = 1.0  # Worst case vs average loss
    
    def is_dangerous(self) -> bool:
        """Check if loss profile is dangerous"""
        return (
            self.convexity_score > 0.5 or
            self.tail_ratio > 3.0 or
            self.loss_clustering > 0.7
        )


@dataclass
class RecoveryHalfLife:
    """Recovery half-life metrics"""
    current_drawdown: float = 0.0
    estimated_half_life: float = float('inf')  # Days to recover half
    recovery_probability: float = 0.0  # Probability of full recovery
    historical_recoveries: List[float] = field(default_factory=list)
    
    def is_recovery_viable(self) -> bool:
        """Check if recovery is viable"""
        return (
            self.estimated_half_life < 60 and  # Less than 60 days
            self.recovery_probability > 0.5
        )


@dataclass
class FailureCorrelation:
    """Failure correlation between strategies"""
    correlation_matrix: Dict[str, Dict[str, float]] = field(default_factory=dict)
    max_correlation: float = 0.0
    average_correlation: float = 0.0
    clustered_strategies: List[List[str]] = field(default_factory=list)
    
    def is_diversified(self) -> bool:
        """Check if failures are diversified"""
        return self.max_correlation < 0.5 and self.average_correlation < 0.3


@dataclass
class SurvivalMetrics:
    """Core survival metrics"""
    survival_probability: float = 0.0  # Probability of surviving next period
    time_to_ruin: float = float('inf')  # Expected time to ruin
    fragility_index: float = 0.0  # How fragile the portfolio is
    regime_robustness: float = 0.0  # Robustness across regimes
    capital_efficiency: float = 0.0  # Return per unit of risk
    
    def is_survival_threatened(self) -> bool:
        """Check if survival is threatened"""
        return (
            self.survival_probability < 0.9 or
            self.time_to_ruin < 365 or
            self.fragility_index > 0.7
        )


@dataclass
class CapitalResult:
    """Result from capital governor"""
    strategy_id: str
    allocation: float  # 0-1, fraction of capital
    mode: AllocationMode
    survival: SurvivalMetrics
    loss_convexity: LossConvexity
    recovery: RecoveryHalfLife
    failure_correlation: FailureCorrelation
    reason: str
    constraints_applied: List[str]
    timestamp: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'strategy_id': self.strategy_id,
            'allocation': self.allocation,
            'mode': self.mode.name,
            'survival_probability': self.survival.survival_probability,
            'fragility_index': self.survival.fragility_index,
            'loss_convexity_dangerous': self.loss_convexity.is_dangerous(),
            'recovery_viable': self.recovery.is_recovery_viable(),
            'diversified': self.failure_correlation.is_diversified(),
            'reason': self.reason,
            'constraints_applied': self.constraints_applied,
            'timestamp': self.timestamp
        }


class LossConvexityCalculator:
    """Calculates loss convexity from return history"""
    
    def __init__(self, window_size: int = 252):
        try:
            self.window_size = window_size
            self._returns: Deque[float] = deque(maxlen=window_size)
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def update(self, return_value: float) -> LossConvexity:
        """Update with new return and calculate convexity"""
        try:
            self._returns.append(return_value)
        
            result = LossConvexity()
        
            if len(self._returns) < 30:
                return result
        
            returns = np.array(list(self._returns))
            losses = returns[returns < 0]
        
            if len(losses) < 10:
                return result
        
            # Calculate convexity (second derivative of loss distribution)
            sorted_losses = np.sort(losses)
            n = len(sorted_losses)
        
            # Compare tail losses to body losses
            tail_losses = sorted_losses[:int(n * 0.1)]  # Worst 10%
            body_losses = sorted_losses[int(n * 0.1):]
        
            if len(body_losses) > 0 and np.mean(body_losses) != 0:
                result.tail_ratio = abs(np.mean(tail_losses) / np.mean(body_losses))
        
            # Calculate loss clustering (autocorrelation of losses)
            loss_indicator = (returns < 0).astype(float)
            if len(loss_indicator) > 1:
                result.loss_clustering = np.corrcoef(
                    loss_indicator[:-1], loss_indicator[1:]
                )[0, 1]
                result.loss_clustering = max(0, result.loss_clustering)
        
            # Worst case multiple
            if np.mean(losses) != 0:
                result.worst_case_multiple = abs(np.min(losses) / np.mean(losses))
        
            # Overall convexity score
            result.convexity_score = (
                min(1.0, result.tail_ratio / 5) * 0.4 +
                result.loss_clustering * 0.3 +
                min(1.0, result.worst_case_multiple / 5) * 0.3
            )
        
            return result
        except Exception as e:
            logger.error(f"Error in update: {e}")
            raise


class RecoveryCalculator:
    """Calculates recovery metrics"""
    
    def __init__(self):
        try:
            self._equity_curve: Deque[float] = deque(maxlen=1000)
            self._peak: float = 0.0
            self._drawdown_starts: List[Tuple[float, float]] = []  # (start_time, peak)
            self._recoveries: List[float] = []  # Days to recover
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def update(self, equity: float) -> RecoveryHalfLife:
        """Update with new equity value"""
        try:
            self._equity_curve.append(equity)
        
            result = RecoveryHalfLife()
        
            # Update peak
            if equity > self._peak:
                self._peak = equity
                # Check if we recovered from a drawdown
                if self._drawdown_starts:
                    start_time, _ = self._drawdown_starts[-1]
                    recovery_days = (time.time() - start_time) / 86400
                    self._recoveries.append(recovery_days)
                    self._drawdown_starts.clear()
        
            # Calculate current drawdown
            if self._peak > 0:
                result.current_drawdown = (self._peak - equity) / self._peak
        
            # Track drawdown start
            if result.current_drawdown > 0.05 and not self._drawdown_starts:
                self._drawdown_starts.append((time.time(), self._peak))
        
            # Estimate half-life from historical recoveries
            if self._recoveries:
                result.historical_recoveries = self._recoveries.copy()
                avg_recovery = np.mean(self._recoveries)
                result.estimated_half_life = avg_recovery / 2
            
                # Recovery probability based on current drawdown
                similar_recoveries = [r for r in self._recoveries if r < avg_recovery * 2]
                result.recovery_probability = len(similar_recoveries) / len(self._recoveries)
            else:
                # Default estimates
                result.estimated_half_life = 30  # 30 days default
                result.recovery_probability = 0.7
        
            return result
        except Exception as e:
            logger.error(f"Error in update: {e}")
            raise


class FailureCorrelationCalculator:
    """Calculates failure correlation between strategies"""
    
    def __init__(self, window_size: int = 100):
        try:
            self.window_size = window_size
            self._strategy_returns: Dict[str, Deque[float]] = {}
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def update(self, strategy_returns: Dict[str, float]) -> FailureCorrelation:
        """Update with new strategy returns"""
        try:
            result = FailureCorrelation()
        
            # Store returns
            for strategy_id, ret in strategy_returns.items():
                if strategy_id not in self._strategy_returns:
                    self._strategy_returns[strategy_id] = deque(maxlen=self.window_size)
                self._strategy_returns[strategy_id].append(ret)
        
            strategies = list(self._strategy_returns.keys())
            if len(strategies) < 2:
                return result
        
            # Check if we have enough data
            min_len = min(len(self._strategy_returns[s]) for s in strategies)
            if min_len < 20:
                return result
        
            # Build return matrix
            return_matrix = np.array([
                list(self._strategy_returns[s])[-min_len:]
                for s in strategies
            ])
        
            # Calculate correlation matrix
            corr_matrix = np.corrcoef(return_matrix)
        
            # Store in result
            for i, s1 in enumerate(strategies):
                result.correlation_matrix[s1] = {}
                for j, s2 in enumerate(strategies):
                    result.correlation_matrix[s1][s2] = corr_matrix[i, j]
        
            # Calculate metrics
            off_diag = corr_matrix[np.triu_indices_from(corr_matrix, k=1)]
            result.max_correlation = np.max(off_diag) if len(off_diag) > 0 else 0.0
            result.average_correlation = np.mean(off_diag) if len(off_diag) > 0 else 0.0
        
            # Find clustered strategies (correlation > 0.7)
            clusters = []
            for i, s1 in enumerate(strategies):
                cluster = [s1]
                for j, s2 in enumerate(strategies):
                    if i != j and corr_matrix[i, j] > 0.7:
                        cluster.append(s2)
                if len(cluster) > 1:
                    clusters.append(cluster)
            result.clustered_strategies = clusters
        
            return result
        except Exception as e:
            logger.error(f"Error in update: {e}")
            raise


class SurvivalCalculator:
    """Calculates survival metrics"""
    
    def __init__(self):
        try:
            self._returns: Deque[float] = deque(maxlen=1000)
            self._drawdowns: Deque[float] = deque(maxlen=1000)
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def update(
        self,
        return_value: float,
        drawdown: float,
        loss_convexity: LossConvexity,
        failure_correlation: FailureCorrelation
    ) -> SurvivalMetrics:
        """Calculate survival metrics"""
        try:
            self._returns.append(return_value)
            self._drawdowns.append(drawdown)
        
            result = SurvivalMetrics()
        
            if len(self._returns) < 30:
                result.survival_probability = 0.5
                return result
        
            returns = np.array(list(self._returns))
            drawdowns = np.array(list(self._drawdowns))
        
            # Survival probability (simplified)
            # Based on: current drawdown, loss convexity, correlation
            base_survival = 0.99  # 99% daily survival
        
            # Adjust for drawdown
            dd_penalty = min(0.1, drawdown * 0.5)
        
            # Adjust for loss convexity
            convexity_penalty = loss_convexity.convexity_score * 0.05
        
            # Adjust for correlation
            corr_penalty = failure_correlation.average_correlation * 0.03
        
            result.survival_probability = max(0.5, base_survival - dd_penalty - convexity_penalty - corr_penalty)
        
            # Time to ruin (simplified Monte Carlo)
            if np.std(returns) > 0:
                sharpe = np.mean(returns) / np.std(returns) * np.sqrt(252)
                if sharpe < 0:
                    result.time_to_ruin = max(30, 365 / abs(sharpe))
                else:
                    result.time_to_ruin = float('inf')
        
            # Fragility index
            result.fragility_index = (
                loss_convexity.convexity_score * 0.4 +
                (1 - result.survival_probability) * 10 * 0.3 +
                failure_correlation.average_correlation * 0.3
            )
        
            # Regime robustness (simplified)
            # Higher if returns are consistent across different volatility regimes
            vol_regimes = np.percentile(np.abs(returns), [25, 50, 75])
            regime_returns = []
            for i, threshold in enumerate(vol_regimes):
                mask = np.abs(returns) <= threshold
                if np.sum(mask) > 5:
                    regime_returns.append(np.mean(returns[mask]))
        
            if len(regime_returns) >= 2:
                result.regime_robustness = 1 - np.std(regime_returns) / (np.mean(np.abs(regime_returns)) + 1e-10)
                result.regime_robustness = max(0, min(1, result.regime_robustness))
        
            # Capital efficiency
            if np.std(returns) > 0:
                result.capital_efficiency = np.mean(returns) / np.std(returns)
        
            return result
        except Exception as e:
            logger.error(f"Error in update: {e}")
            raise


class CapitalGovernor:
    """
    Main Capital Governor
    
    RULES:
    1. Capital allocation is the PRIMARY decision variable
    2. Allocate based on worst-case loss, not expected return
    3. Strategies compete on capital efficiency under STRESS
    4. Survival probability is the primary KPI
    """
    
    # Constraints
    MAX_SINGLE_STRATEGY_ALLOCATION = 0.20  # 20% max per strategy
    MAX_CORRELATED_ALLOCATION = 0.30  # 30% max for correlated strategies
    MIN_SURVIVAL_PROBABILITY = 0.95  # 95% minimum survival
    MAX_FRAGILITY = 0.5  # Maximum fragility index
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        try:
            self.config = config or {}
            self.logger = logging.getLogger("msos.capital")
        
            # Calculators
            self._loss_convexity = LossConvexityCalculator()
            self._recovery = RecoveryCalculator()
            self._failure_correlation = FailureCorrelationCalculator()
            self._survival = SurvivalCalculator()
        
            # State
            self._mode = AllocationMode.BALANCED
            self._strategy_allocations: Dict[str, float] = {}
            self._total_equity: float = 0.0
        
            self.logger.info("Capital Governor initialized")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def update(
        self,
        equity: float,
        strategy_returns: Dict[str, float]
    ):
        """Update governor with new data"""
        try:
            self._total_equity = equity
        
            # Update calculators
            total_return = sum(strategy_returns.values()) if strategy_returns else 0.0
            self._loss_convexity.update(total_return)
            self._recovery.update(equity)
            self._failure_correlation.update(strategy_returns)
        except Exception as e:
            logger.error(f"Error in update: {e}")
            raise
    
    def allocate(
        self,
        strategy_id: str,
        strategy_metrics: Dict[str, Any]
    ) -> CapitalResult:
        """
        Determine capital allocation for a strategy.
        
        Allocation is based on survival metrics, NOT expected return.
        """
        try:
            constraints_applied = []
        
            # Get current metrics
            loss_convexity = self._loss_convexity.update(
                strategy_metrics.get('return', 0.0)
            )
            recovery = self._recovery.update(self._total_equity)
            failure_correlation = self._failure_correlation.update(
                {strategy_id: strategy_metrics.get('return', 0.0)}
            )
            survival = self._survival.update(
                strategy_metrics.get('return', 0.0),
                recovery.current_drawdown,
                loss_convexity,
                failure_correlation
            )
        
            # Determine allocation mode
            if survival.is_survival_threatened():
                self._mode = AllocationMode.SURVIVAL
            elif recovery.current_drawdown > 0.10:
                self._mode = AllocationMode.RECOVERY
            elif loss_convexity.is_dangerous():
                self._mode = AllocationMode.DEFENSIVE
            else:
                self._mode = AllocationMode.BALANCED
        
            # Base allocation
            base_allocation = self._calculate_base_allocation(
                strategy_metrics, survival, loss_convexity
            )
        
            # Apply constraints
            allocation = base_allocation
        
            # Constraint 1: Max single strategy
            if allocation > self.MAX_SINGLE_STRATEGY_ALLOCATION:
                allocation = self.MAX_SINGLE_STRATEGY_ALLOCATION
                constraints_applied.append("MAX_SINGLE_STRATEGY")
        
            # Constraint 2: Survival probability
            if survival.survival_probability < self.MIN_SURVIVAL_PROBABILITY:
                reduction = (self.MIN_SURVIVAL_PROBABILITY - survival.survival_probability) * 10
                allocation *= max(0.1, 1 - reduction)
                constraints_applied.append("SURVIVAL_PROBABILITY")
        
            # Constraint 3: Fragility
            if survival.fragility_index > self.MAX_FRAGILITY:
                reduction = (survival.fragility_index - self.MAX_FRAGILITY) * 2
                allocation *= max(0.1, 1 - reduction)
                constraints_applied.append("FRAGILITY")
        
            # Constraint 4: Loss convexity
            if loss_convexity.is_dangerous():
                allocation *= 0.5
                constraints_applied.append("LOSS_CONVEXITY")
        
            # Constraint 5: Recovery mode
            if self._mode == AllocationMode.RECOVERY:
                allocation *= 0.7
                constraints_applied.append("RECOVERY_MODE")
        
            # Constraint 6: Survival mode
            if self._mode == AllocationMode.SURVIVAL:
                allocation *= 0.3
                constraints_applied.append("SURVIVAL_MODE")
        
            # Constraint 7: Correlated strategies
            if not failure_correlation.is_diversified():
                allocation *= 0.8
                constraints_applied.append("CORRELATION")
        
            # Store allocation
            self._strategy_allocations[strategy_id] = allocation
        
            # Generate reason
            reason = self._generate_reason(
                allocation, self._mode, constraints_applied, survival
            )
        
            return CapitalResult(
                strategy_id=strategy_id,
                allocation=allocation,
                mode=self._mode,
                survival=survival,
                loss_convexity=loss_convexity,
                recovery=recovery,
                failure_correlation=failure_correlation,
                reason=reason,
                constraints_applied=constraints_applied
            )
        except Exception as e:
            logger.error(f"Error in allocate: {e}")
            raise
    
    def _calculate_base_allocation(
        self,
        strategy_metrics: Dict[str, Any],
        survival: SurvivalMetrics,
        loss_convexity: LossConvexity
    ) -> float:
        """Calculate base allocation before constraints"""
        # Start with survival-based allocation
        try:
            survival_factor = survival.survival_probability ** 10  # Exponential penalty
        
            # Adjust for regime robustness
            robustness_factor = survival.regime_robustness
        
            # Adjust for capital efficiency
            efficiency_factor = min(1.0, max(0.1, survival.capital_efficiency + 0.5))
        
            # Combine factors
            base = survival_factor * robustness_factor * efficiency_factor
        
            # Scale to reasonable range
            return min(0.20, max(0.01, base * 0.20))
        except Exception as e:
            logger.error(f"Error in _calculate_base_allocation: {e}")
            raise
    
    def _generate_reason(
        self,
        allocation: float,
        mode: AllocationMode,
        constraints: List[str],
        survival: SurvivalMetrics
    ) -> str:
        """Generate explanation for allocation"""
        try:
            if allocation < 0.05:
                return f"Minimal allocation ({allocation:.1%}): Survival threatened. Mode: {mode.name}"
            elif allocation < 0.10:
                return f"Reduced allocation ({allocation:.1%}): Constraints: {constraints}. Mode: {mode.name}"
            else:
                return f"Normal allocation ({allocation:.1%}): Survival prob: {survival.survival_probability:.1%}. Mode: {mode.name}"
        except Exception as e:
            logger.error(f"Error in _generate_reason: {e}")
            raise
    
    def get_total_allocation(self) -> float:
        """Get total allocation across all strategies"""
        return sum(self._strategy_allocations.values())
    
    def get_mode(self) -> AllocationMode:
        """Get current allocation mode"""
        return self._mode
    
    def force_survival_mode(self, reason: str):
        """Force system into survival mode"""
        try:
            self._mode = AllocationMode.SURVIVAL
            self.logger.critical(f"SURVIVAL MODE ACTIVATED: {reason}")
        except Exception as e:
            logger.error(f"Error in force_survival_mode: {e}")
            raise
