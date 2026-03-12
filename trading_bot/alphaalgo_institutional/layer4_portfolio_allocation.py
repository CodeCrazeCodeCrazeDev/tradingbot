"""
AlphaAlgo Institutional - Layer 4: Strategic Portfolio Allocation
=================================================================

The Strategic Portfolio Allocation Layer is responsible for:
- Capital allocation across strategies and assets
- Portfolio construction with risk constraints
- Dynamic rebalancing based on regime and performance
- Correlation management
- Capacity constraints

This layer operates as the PORTFOLIO & CAPITAL COMMITTEE.

Key principles:
- Capital allocation > signal quality
- Portfolio behavior matters more than individual strategies
- Diversification across uncorrelated return streams
- Dynamic allocation based on regime
- Strict position limits and concentration controls
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
import numpy as np
from collections import defaultdict
import uuid

from .core_types import (
    CapitalAllocation, MarketRegime, CommitteeType, CommitteeVote,
    CommitteeDecision, RiskLevel, SystemConstants, ModelStatus
)

logger = logging.getLogger(__name__)


# =============================================================================
# ALLOCATION TYPES
# =============================================================================

class AllocationMethod(Enum):
    """Portfolio allocation methods."""
    EQUAL_WEIGHT = "equal_weight"
    RISK_PARITY = "risk_parity"
    MEAN_VARIANCE = "mean_variance"
    MINIMUM_VARIANCE = "minimum_variance"
    MAXIMUM_DIVERSIFICATION = "maximum_diversification"
    HIERARCHICAL_RISK_PARITY = "hierarchical_risk_parity"
    KELLY_CRITERION = "kelly_criterion"
    REGIME_ADAPTIVE = "regime_adaptive"


class RebalanceReason(Enum):
    """Reasons for portfolio rebalancing."""
    SCHEDULED = "scheduled"
    DRIFT_THRESHOLD = "drift_threshold"
    REGIME_CHANGE = "regime_change"
    RISK_BREACH = "risk_breach"
    PERFORMANCE_TRIGGER = "performance_trigger"
    CORRELATION_CHANGE = "correlation_change"
    CAPACITY_CONSTRAINT = "capacity_constraint"
    MANUAL = "manual"


@dataclass
class StrategyAllocation:
    """Allocation to a single strategy."""
    strategy_id: str
    target_weight: float
    current_weight: float
    min_weight: float
    max_weight: float
    risk_contribution: float
    expected_return: float
    expected_volatility: float
    correlation_to_portfolio: float
    capacity_used: float
    capacity_limit: float


@dataclass
class PortfolioState:
    """Current portfolio state."""
    total_capital: float
    allocated_capital: float
    cash_reserve: float
    strategy_allocations: Dict[str, StrategyAllocation]
    total_risk: float
    expected_return: float
    diversification_ratio: float
    concentration_score: float
    regime: MarketRegime
    last_rebalance: datetime
    rebalance_count: int


@dataclass
class RebalanceProposal:
    """Proposed portfolio rebalance."""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    timestamp: datetime = field(default_factory=datetime.utcnow)
    reason: RebalanceReason = RebalanceReason.SCHEDULED
    current_allocations: Dict[str, float] = field(default_factory=dict)
    proposed_allocations: Dict[str, float] = field(default_factory=dict)
    expected_turnover: float = 0.0
    expected_cost: float = 0.0
    risk_impact: float = 0.0
    approved: bool = False
    executed: bool = False


# =============================================================================
# ALLOCATION ENGINES
# =============================================================================

class RiskParityAllocator:
    """Risk parity allocation engine."""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.target_volatility = self.config.get('target_volatility', 0.10)
        self.max_leverage = self.config.get('max_leverage', 1.5)
    
    def allocate(
        self,
        expected_returns: np.ndarray,
        covariance_matrix: np.ndarray,
        constraints: Dict[str, Any] = None
    ) -> np.ndarray:
        """
        Compute risk parity weights.
        
        Args:
            expected_returns: Expected returns vector
            covariance_matrix: Covariance matrix
            constraints: Optional constraints
            
        Returns:
            Weight vector
        """
        n_assets = len(expected_returns)
        
        # Initial equal risk contribution
        volatilities = np.sqrt(np.diag(covariance_matrix))
        inv_vol = 1.0 / np.maximum(volatilities, 1e-8)
        weights = inv_vol / np.sum(inv_vol)
        
        # Iterative risk parity (simplified)
        for _ in range(100):
            portfolio_vol = np.sqrt(weights @ covariance_matrix @ weights)
            marginal_risk = covariance_matrix @ weights / portfolio_vol
            risk_contrib = weights * marginal_risk
            target_risk = portfolio_vol / n_assets
            
            # Adjust weights
            adjustment = target_risk / np.maximum(risk_contrib, 1e-8)
            weights = weights * adjustment
            weights = weights / np.sum(weights)
        
        # Apply constraints
        if constraints:
            min_weight = constraints.get('min_weight', 0.0)
            max_weight = constraints.get('max_weight', 1.0)
            weights = np.clip(weights, min_weight, max_weight)
            weights = weights / np.sum(weights)
        
        return weights


class MeanVarianceAllocator:
    """Mean-variance optimization allocator."""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.risk_aversion = self.config.get('risk_aversion', 2.0)
    
    def allocate(
        self,
        expected_returns: np.ndarray,
        covariance_matrix: np.ndarray,
        constraints: Dict[str, Any] = None
    ) -> np.ndarray:
        """
        Compute mean-variance optimal weights.
        
        Args:
            expected_returns: Expected returns vector
            covariance_matrix: Covariance matrix
            constraints: Optional constraints
            
        Returns:
            Weight vector
        """
        n_assets = len(expected_returns)
        
        # Analytical solution for unconstrained case
        try:
            inv_cov = np.linalg.inv(covariance_matrix + np.eye(n_assets) * 1e-6)
            weights = inv_cov @ expected_returns / self.risk_aversion
        except np.linalg.LinAlgError:
            # Fallback to equal weight
            weights = np.ones(n_assets) / n_assets
        
        # Normalize and apply constraints
        if constraints:
            min_weight = constraints.get('min_weight', 0.0)
            max_weight = constraints.get('max_weight', 1.0)
            weights = np.clip(weights, min_weight, max_weight)
        
        # Ensure weights sum to 1
        if np.sum(weights) > 0:
            weights = weights / np.sum(weights)
        else:
            weights = np.ones(n_assets) / n_assets
        
        return weights


class MinimumVarianceAllocator:
    """Minimum variance portfolio allocator."""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
    
    def allocate(
        self,
        expected_returns: np.ndarray,
        covariance_matrix: np.ndarray,
        constraints: Dict[str, Any] = None
    ) -> np.ndarray:
        """
        Compute minimum variance weights.
        
        Args:
            expected_returns: Expected returns vector (not used)
            covariance_matrix: Covariance matrix
            constraints: Optional constraints
            
        Returns:
            Weight vector
        """
        n_assets = len(expected_returns)
        
        try:
            inv_cov = np.linalg.inv(covariance_matrix + np.eye(n_assets) * 1e-6)
            ones = np.ones(n_assets)
            weights = inv_cov @ ones / (ones @ inv_cov @ ones)
        except np.linalg.LinAlgError:
            weights = np.ones(n_assets) / n_assets
        
        # Apply constraints
        if constraints:
            min_weight = constraints.get('min_weight', 0.0)
            max_weight = constraints.get('max_weight', 1.0)
            weights = np.clip(weights, min_weight, max_weight)
            weights = weights / np.sum(weights)
        
        return weights


class KellyCriterionAllocator:
    """Kelly criterion allocator with fractional Kelly."""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.kelly_fraction = self.config.get('kelly_fraction', 0.25)  # Quarter Kelly
        self.max_position = self.config.get('max_position', 0.20)
    
    def allocate(
        self,
        expected_returns: np.ndarray,
        covariance_matrix: np.ndarray,
        constraints: Dict[str, Any] = None
    ) -> np.ndarray:
        """
        Compute Kelly criterion weights.
        
        Args:
            expected_returns: Expected returns vector
            covariance_matrix: Covariance matrix
            constraints: Optional constraints
            
        Returns:
            Weight vector
        """
        n_assets = len(expected_returns)
        
        try:
            inv_cov = np.linalg.inv(covariance_matrix + np.eye(n_assets) * 1e-6)
            full_kelly = inv_cov @ expected_returns
            weights = full_kelly * self.kelly_fraction
        except np.linalg.LinAlgError:
            weights = np.ones(n_assets) / n_assets
        
        # Apply position limits
        weights = np.clip(weights, -self.max_position, self.max_position)
        
        # Normalize if all positive
        if np.all(weights >= 0) and np.sum(weights) > 0:
            weights = weights / np.sum(weights)
        
        return weights


class RegimeAdaptiveAllocator:
    """Regime-adaptive allocation engine."""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        # Regime-specific allocators
        self.allocators = {
            MarketRegime.CALM: RiskParityAllocator(),
            MarketRegime.NORMAL: MeanVarianceAllocator(),
            MarketRegime.VOLATILE: MinimumVarianceAllocator(),
            MarketRegime.CRISIS: MinimumVarianceAllocator(),
            MarketRegime.TRENDING: MeanVarianceAllocator(),
            MarketRegime.MEAN_REVERTING: RiskParityAllocator(),
            MarketRegime.TRANSITION: MinimumVarianceAllocator()
        }
        
        # Regime-specific risk scaling
        self.risk_scaling = {
            MarketRegime.CALM: 1.2,
            MarketRegime.NORMAL: 1.0,
            MarketRegime.VOLATILE: 0.6,
            MarketRegime.CRISIS: 0.3,
            MarketRegime.TRENDING: 0.9,
            MarketRegime.MEAN_REVERTING: 1.0,
            MarketRegime.TRANSITION: 0.5
        }
    
    def allocate(
        self,
        expected_returns: np.ndarray,
        covariance_matrix: np.ndarray,
        regime: MarketRegime,
        constraints: Dict[str, Any] = None
    ) -> np.ndarray:
        """
        Compute regime-adaptive weights.
        
        Args:
            expected_returns: Expected returns vector
            covariance_matrix: Covariance matrix
            regime: Current market regime
            constraints: Optional constraints
            
        Returns:
            Weight vector
        """
        allocator = self.allocators.get(regime, self.allocators[MarketRegime.NORMAL])
        weights = allocator.allocate(expected_returns, covariance_matrix, constraints)
        
        # Apply regime-specific risk scaling
        risk_scale = self.risk_scaling.get(regime, 1.0)
        weights = weights * risk_scale
        
        # Ensure weights sum to at most 1 (allow cash)
        total_weight = np.sum(np.abs(weights))
        if total_weight > 1.0:
            weights = weights / total_weight
        
        return weights


# =============================================================================
# CORRELATION MANAGER
# =============================================================================

class CorrelationManager:
    """Manages correlation analysis and constraints."""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.max_correlation = self.config.get('max_correlation', 0.7)
        self.correlation_window = self.config.get('correlation_window', 60)
        
        # Historical correlations
        self.correlation_history: List[Tuple[datetime, np.ndarray]] = []
    
    def compute_correlation_matrix(self, returns: np.ndarray) -> np.ndarray:
        """Compute correlation matrix from returns."""
        if returns.shape[0] < 2:
            n = returns.shape[1] if len(returns.shape) > 1 else 1
            return np.eye(n)
        
        return np.corrcoef(returns.T)
    
    def check_correlation_constraints(
        self,
        weights: np.ndarray,
        correlation_matrix: np.ndarray
    ) -> Tuple[bool, List[str]]:
        """
        Check if portfolio satisfies correlation constraints.
        
        Returns:
            Tuple of (passes, list of violations)
        """
        violations = []
        n = len(weights)
        
        for i in range(n):
            for j in range(i + 1, n):
                if weights[i] > 0.01 and weights[j] > 0.01:
                    corr = correlation_matrix[i, j]
                    if abs(corr) > self.max_correlation:
                        violations.append(
                            f"High correlation ({corr:.2f}) between assets {i} and {j}"
                        )
        
        return len(violations) == 0, violations
    
    def compute_diversification_ratio(
        self,
        weights: np.ndarray,
        volatilities: np.ndarray,
        covariance_matrix: np.ndarray
    ) -> float:
        """Compute portfolio diversification ratio."""
        weighted_vol = np.sum(weights * volatilities)
        portfolio_vol = np.sqrt(weights @ covariance_matrix @ weights)
        
        if portfolio_vol > 0:
            return weighted_vol / portfolio_vol
        return 1.0
    
    def detect_correlation_regime_change(
        self,
        current_correlation: np.ndarray,
        threshold: float = 0.3
    ) -> bool:
        """Detect significant change in correlation structure."""
        if not self.correlation_history:
            return False
        
        _, last_correlation = self.correlation_history[-1]
        
        # Compute Frobenius norm of difference
        diff = current_correlation - last_correlation
        change = np.sqrt(np.sum(diff ** 2))
        
        return change > threshold


# =============================================================================
# CAPACITY MANAGER
# =============================================================================

class CapacityManager:
    """Manages strategy capacity constraints."""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        # Capacity limits by strategy type
        self.capacity_limits: Dict[str, float] = {}
        self.current_usage: Dict[str, float] = {}
    
    def set_capacity_limit(self, strategy_id: str, limit: float):
        """Set capacity limit for a strategy."""
        self.capacity_limits[strategy_id] = limit
    
    def update_usage(self, strategy_id: str, usage: float):
        """Update capacity usage for a strategy."""
        self.current_usage[strategy_id] = usage
    
    def get_available_capacity(self, strategy_id: str) -> float:
        """Get available capacity for a strategy."""
        limit = self.capacity_limits.get(strategy_id, float('inf'))
        usage = self.current_usage.get(strategy_id, 0.0)
        return max(0.0, limit - usage)
    
    def check_capacity_constraints(
        self,
        allocations: Dict[str, float],
        total_capital: float
    ) -> Tuple[bool, Dict[str, float]]:
        """
        Check if allocations satisfy capacity constraints.
        
        Returns:
            Tuple of (passes, adjusted allocations)
        """
        adjusted = {}
        passes = True
        
        for strategy_id, weight in allocations.items():
            requested_capital = weight * total_capital
            available = self.get_available_capacity(strategy_id)
            
            if requested_capital > available:
                adjusted[strategy_id] = available / total_capital
                passes = False
            else:
                adjusted[strategy_id] = weight
        
        return passes, adjusted


# =============================================================================
# PORTFOLIO & CAPITAL COMMITTEE
# =============================================================================

class PortfolioCapitalCommittee:
    """
    Internal committee responsible for portfolio allocation.
    
    Responsibilities:
    - Capital allocation across strategies
    - Portfolio construction
    - Rebalancing decisions
    - Correlation management
    - Capacity constraints
    
    Key principles:
    - Capital allocation > signal quality
    - Portfolio behavior > individual strategies
    - Diversification is mandatory
    - Regime-aware allocation
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.committee_type = CommitteeType.PORTFOLIO_CAPITAL
        
        # Initialize allocators
        self.allocators = {
            AllocationMethod.EQUAL_WEIGHT: lambda: np.ones(1),  # Placeholder
            AllocationMethod.RISK_PARITY: RiskParityAllocator(self.config),
            AllocationMethod.MEAN_VARIANCE: MeanVarianceAllocator(self.config),
            AllocationMethod.MINIMUM_VARIANCE: MinimumVarianceAllocator(self.config),
            AllocationMethod.KELLY_CRITERION: KellyCriterionAllocator(self.config),
            AllocationMethod.REGIME_ADAPTIVE: RegimeAdaptiveAllocator(self.config)
        }
        
        # Initialize managers
        self.correlation_manager = CorrelationManager(self.config)
        self.capacity_manager = CapacityManager(self.config)
        
        # Portfolio state
        self.portfolio_state: Optional[PortfolioState] = None
        self.rebalance_history: List[RebalanceProposal] = []
        
        # Allocation constraints
        self.min_cash_reserve = self.config.get('min_cash_reserve', 0.10)
        self.max_single_strategy = self.config.get('max_single_strategy', 0.25)
        self.max_correlated_exposure = self.config.get('max_correlated_exposure', 0.40)
        self.rebalance_threshold = self.config.get('rebalance_threshold', 0.05)
        
        logger.info("PortfolioCapitalCommittee initialized")
    
    def initialize_portfolio(
        self,
        total_capital: float,
        strategy_ids: List[str]
    ) -> PortfolioState:
        """
        Initialize portfolio state.
        
        Args:
            total_capital: Total capital to allocate
            strategy_ids: List of strategy IDs
            
        Returns:
            Initial PortfolioState
        """
        n_strategies = len(strategy_ids)
        initial_weight = (1.0 - self.min_cash_reserve) / max(1, n_strategies)
        
        allocations = {}
        for strategy_id in strategy_ids:
            allocations[strategy_id] = StrategyAllocation(
                strategy_id=strategy_id,
                target_weight=initial_weight,
                current_weight=initial_weight,
                min_weight=0.0,
                max_weight=self.max_single_strategy,
                risk_contribution=initial_weight,
                expected_return=0.0,
                expected_volatility=0.0,
                correlation_to_portfolio=0.0,
                capacity_used=0.0,
                capacity_limit=float('inf')
            )
        
        self.portfolio_state = PortfolioState(
            total_capital=total_capital,
            allocated_capital=total_capital * (1.0 - self.min_cash_reserve),
            cash_reserve=total_capital * self.min_cash_reserve,
            strategy_allocations=allocations,
            total_risk=0.0,
            expected_return=0.0,
            diversification_ratio=1.0,
            concentration_score=1.0 / max(1, n_strategies),
            regime=MarketRegime.NORMAL,
            last_rebalance=datetime.utcnow(),
            rebalance_count=0
        )
        
        return self.portfolio_state
    
    def compute_optimal_allocation(
        self,
        expected_returns: Dict[str, float],
        covariance_matrix: np.ndarray,
        strategy_ids: List[str],
        method: AllocationMethod = AllocationMethod.REGIME_ADAPTIVE,
        regime: MarketRegime = MarketRegime.NORMAL
    ) -> Dict[str, float]:
        """
        Compute optimal allocation weights.
        
        Args:
            expected_returns: Expected returns by strategy
            covariance_matrix: Covariance matrix
            strategy_ids: Strategy IDs in order
            method: Allocation method
            regime: Current market regime
            
        Returns:
            Dict of strategy_id -> weight
        """
        # Convert to arrays
        returns_array = np.array([expected_returns.get(s, 0.0) for s in strategy_ids])
        
        # Get allocator
        if method == AllocationMethod.REGIME_ADAPTIVE:
            allocator = self.allocators[method]
            weights = allocator.allocate(
                returns_array, covariance_matrix, regime,
                {'min_weight': 0.0, 'max_weight': self.max_single_strategy}
            )
        elif method == AllocationMethod.EQUAL_WEIGHT:
            n = len(strategy_ids)
            weights = np.ones(n) / n
        else:
            allocator = self.allocators.get(method, self.allocators[AllocationMethod.RISK_PARITY])
            weights = allocator.allocate(
                returns_array, covariance_matrix,
                {'min_weight': 0.0, 'max_weight': self.max_single_strategy}
            )
        
        # Apply cash reserve
        weights = weights * (1.0 - self.min_cash_reserve)
        
        # Convert to dict
        allocation = {s: w for s, w in zip(strategy_ids, weights)}
        
        return allocation
    
    def propose_rebalance(
        self,
        reason: RebalanceReason,
        new_allocations: Dict[str, float],
        transaction_costs: Dict[str, float] = None
    ) -> RebalanceProposal:
        """
        Create a rebalance proposal.
        
        Args:
            reason: Reason for rebalancing
            new_allocations: Proposed new allocations
            transaction_costs: Estimated transaction costs
            
        Returns:
            RebalanceProposal
        """
        if self.portfolio_state is None:
            raise ValueError("Portfolio not initialized")
        
        current_allocations = {
            s: a.current_weight
            for s, a in self.portfolio_state.strategy_allocations.items()
        }
        
        # Compute turnover
        turnover = sum(
            abs(new_allocations.get(s, 0) - current_allocations.get(s, 0))
            for s in set(new_allocations.keys()) | set(current_allocations.keys())
        ) / 2
        
        # Estimate costs
        costs = transaction_costs or {}
        total_cost = sum(
            costs.get(s, 0.001) * abs(new_allocations.get(s, 0) - current_allocations.get(s, 0))
            for s in new_allocations.keys()
        ) * self.portfolio_state.total_capital
        
        proposal = RebalanceProposal(
            reason=reason,
            current_allocations=current_allocations,
            proposed_allocations=new_allocations,
            expected_turnover=turnover,
            expected_cost=total_cost
        )
        
        self.rebalance_history.append(proposal)
        return proposal
    
    def execute_rebalance(self, proposal: RebalanceProposal) -> bool:
        """
        Execute a rebalance proposal.
        
        Args:
            proposal: Approved rebalance proposal
            
        Returns:
            True if successful
        """
        if not proposal.approved:
            logger.warning("Cannot execute unapproved rebalance proposal")
            return False
        
        if self.portfolio_state is None:
            return False
        
        # Update allocations
        for strategy_id, weight in proposal.proposed_allocations.items():
            if strategy_id in self.portfolio_state.strategy_allocations:
                self.portfolio_state.strategy_allocations[strategy_id].target_weight = weight
                self.portfolio_state.strategy_allocations[strategy_id].current_weight = weight
        
        self.portfolio_state.last_rebalance = datetime.utcnow()
        self.portfolio_state.rebalance_count += 1
        proposal.executed = True
        
        logger.info(f"Executed rebalance proposal {proposal.id}")
        return True
    
    def check_rebalance_needed(self) -> Tuple[bool, RebalanceReason]:
        """
        Check if rebalancing is needed.
        
        Returns:
            Tuple of (needs_rebalance, reason)
        """
        if self.portfolio_state is None:
            return False, RebalanceReason.SCHEDULED
        
        # Check drift
        max_drift = 0.0
        for allocation in self.portfolio_state.strategy_allocations.values():
            drift = abs(allocation.current_weight - allocation.target_weight)
            max_drift = max(max_drift, drift)
        
        if max_drift > self.rebalance_threshold:
            return True, RebalanceReason.DRIFT_THRESHOLD
        
        return False, RebalanceReason.SCHEDULED
    
    def vote(self, proposal: RebalanceProposal) -> CommitteeVote:
        """
        Vote on a rebalance proposal.
        
        Returns:
            CommitteeVote with allocation assessment
        """
        # Evaluate proposal
        issues = []
        
        # Check concentration
        max_weight = max(proposal.proposed_allocations.values()) if proposal.proposed_allocations else 0
        if max_weight > self.max_single_strategy:
            issues.append(f"Max weight {max_weight:.2%} exceeds limit {self.max_single_strategy:.2%}")
        
        # Check turnover
        if proposal.expected_turnover > 0.5:
            issues.append(f"High turnover: {proposal.expected_turnover:.2%}")
        
        # Check cost
        if self.portfolio_state and proposal.expected_cost > self.portfolio_state.total_capital * 0.01:
            issues.append(f"High transaction cost: ${proposal.expected_cost:.2f}")
        
        # Make decision
        if not issues:
            decision = CommitteeDecision.APPROVE
            confidence = 0.9
            rationale = "Rebalance proposal meets all criteria"
        elif len(issues) == 1:
            decision = CommitteeDecision.CONDITIONAL
            confidence = 0.6
            rationale = f"Conditional approval: {issues[0]}"
        else:
            decision = CommitteeDecision.REJECT
            confidence = 0.8
            rationale = f"Rejected due to: {', '.join(issues)}"
        
        return CommitteeVote(
            committee=self.committee_type,
            decision=decision,
            confidence=confidence,
            rationale=rationale,
            conditions=issues if decision == CommitteeDecision.CONDITIONAL else []
        )
    
    def get_portfolio_metrics(self) -> Dict[str, Any]:
        """Get current portfolio metrics."""
        if self.portfolio_state is None:
            return {}
        
        return {
            'total_capital': self.portfolio_state.total_capital,
            'allocated_capital': self.portfolio_state.allocated_capital,
            'cash_reserve': self.portfolio_state.cash_reserve,
            'n_strategies': len(self.portfolio_state.strategy_allocations),
            'total_risk': self.portfolio_state.total_risk,
            'expected_return': self.portfolio_state.expected_return,
            'diversification_ratio': self.portfolio_state.diversification_ratio,
            'concentration_score': self.portfolio_state.concentration_score,
            'regime': self.portfolio_state.regime.value,
            'last_rebalance': self.portfolio_state.last_rebalance.isoformat(),
            'rebalance_count': self.portfolio_state.rebalance_count
        }


# =============================================================================
# PORTFOLIO ALLOCATION LAYER
# =============================================================================

class PortfolioAllocationLayer:
    """
    Layer 4: Strategic Portfolio Allocation Layer
    
    Responsible for:
    - Capital allocation across strategies
    - Portfolio construction
    - Rebalancing decisions
    - Correlation management
    - Capacity constraints
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.committee = PortfolioCapitalCommittee(self.config)
        
        # Layer state
        self.allocation_method = AllocationMethod(
            self.config.get('allocation_method', AllocationMethod.REGIME_ADAPTIVE.value)
        )
        self.current_regime = MarketRegime.NORMAL
        
        logger.info("PortfolioAllocationLayer initialized")
    
    def initialize(self, total_capital: float, strategy_ids: List[str]) -> PortfolioState:
        """Initialize portfolio."""
        return self.committee.initialize_portfolio(total_capital, strategy_ids)
    
    def update_regime(self, regime: MarketRegime):
        """Update current market regime."""
        self.current_regime = regime
        if self.committee.portfolio_state:
            self.committee.portfolio_state.regime = regime
    
    def compute_allocation(
        self,
        expected_returns: Dict[str, float],
        covariance_matrix: np.ndarray,
        strategy_ids: List[str]
    ) -> Dict[str, float]:
        """Compute optimal allocation."""
        return self.committee.compute_optimal_allocation(
            expected_returns,
            covariance_matrix,
            strategy_ids,
            self.allocation_method,
            self.current_regime
        )
    
    def propose_rebalance(
        self,
        reason: RebalanceReason,
        new_allocations: Dict[str, float]
    ) -> RebalanceProposal:
        """Propose a rebalance."""
        return self.committee.propose_rebalance(reason, new_allocations)
    
    def approve_rebalance(self, proposal: RebalanceProposal) -> CommitteeVote:
        """Vote on rebalance proposal."""
        vote = self.committee.vote(proposal)
        if vote.decision == CommitteeDecision.APPROVE:
            proposal.approved = True
        return vote
    
    def execute_rebalance(self, proposal: RebalanceProposal) -> bool:
        """Execute approved rebalance."""
        return self.committee.execute_rebalance(proposal)
    
    def check_rebalance_needed(self) -> Tuple[bool, RebalanceReason]:
        """Check if rebalancing is needed."""
        return self.committee.check_rebalance_needed()
    
    def get_portfolio_state(self) -> Optional[PortfolioState]:
        """Get current portfolio state."""
        return self.committee.portfolio_state
    
    def get_layer_state(self) -> Dict[str, Any]:
        """Get current layer state."""
        return {
            'allocation_method': self.allocation_method.value,
            'current_regime': self.current_regime.value,
            'portfolio_metrics': self.committee.get_portfolio_metrics(),
            'rebalance_history_count': len(self.committee.rebalance_history)
        }
