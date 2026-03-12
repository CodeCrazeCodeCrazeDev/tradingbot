"""
Risk Budget Allocator - Portfolio risk budget management

Allocates risk budgets per symbol/strategy and enforces limits before position sizing.
"""

import logging
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from enum import Enum
from datetime import datetime

logger = logging.getLogger(__name__)


class AllocationMethod(Enum):
    """Risk allocation methods"""
    EQUAL_WEIGHT = 'equal_weight'
    VOLATILITY_PARITY = 'volatility_parity'
    RISK_PARITY = 'risk_parity'
    PERFORMANCE_BASED = 'performance_based'
    DYNAMIC = 'dynamic'


@dataclass
class RiskBudget:
    """Risk budget for a symbol/strategy"""
    identifier: str  # Symbol or strategy name
    allocated_risk_pct: float  # % of portfolio risk
    used_risk_pct: float = 0.0
    max_position_size: float = 0.0
    performance_score: float = 1.0
    volatility: float = 0.01
    last_updated: datetime = None
    
    def __post_init__(self):
        try:
            if self.last_updated is None:
                self.last_updated = datetime.now()
        except Exception as e:
            logger.error(f"Error in __post_init__: {e}")
            raise
    
    @property
    def available_risk_pct(self) -> float:
        """Get available risk percentage"""
        return max(0, self.allocated_risk_pct - self.used_risk_pct)
    
    @property
    def utilization_pct(self) -> float:
        """Get budget utilization percentage"""
        try:
            if self.allocated_risk_pct == 0:
                return 0
            return (self.used_risk_pct / self.allocated_risk_pct) * 100
        except Exception as e:
            logger.error(f"Error in utilization_pct: {e}")
            raise


class RiskBudgetAllocator:
    """Manages portfolio risk budgets across symbols/strategies"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        try:
            self.config = config or {}
        
            # Total portfolio risk budget
            self.total_risk_budget = self.config.get('total_risk_budget', 0.10)  # 10% of portfolio
        
            # Allocation method
            self.allocation_method = AllocationMethod(
                self.config.get('allocation_method', 'risk_parity')
            )
        
            # Risk budgets by identifier
            self.budgets: Dict[str, RiskBudget] = {}
        
            # Rebalance settings
            self.rebalance_interval = self.config.get('rebalance_interval', 3600)  # 1 hour
            self.last_rebalance = datetime.now()
        
            # Performance tracking
            self.performance_window = self.config.get('performance_window', 30)  # days
        
            logger.info(f"Risk budget allocator initialized: method={self.allocation_method.value}")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def allocate_budgets(self, identifiers: List[str], 
                        volatilities: Optional[Dict[str, float]] = None,
                        performances: Optional[Dict[str, float]] = None) -> Dict[str, RiskBudget]:
        """
        Allocate risk budgets to identifiers
        
        Args:
            identifiers: List of symbols or strategy names
            volatilities: Optional volatility estimates per identifier
            performances: Optional performance scores per identifier
            
        Returns:
            Dictionary of risk budgets
        """
        try:
            if not identifiers:
                logger.warning("No identifiers provided for allocation")
                return {}
        
            volatilities = volatilities or {}
            performances = performances or {}
        
            # Calculate allocations based on method
            if self.allocation_method == AllocationMethod.EQUAL_WEIGHT:
                allocations = self._equal_weight_allocation(identifiers)
            elif self.allocation_method == AllocationMethod.VOLATILITY_PARITY:
                allocations = self._volatility_parity_allocation(identifiers, volatilities)
            elif self.allocation_method == AllocationMethod.RISK_PARITY:
                allocations = self._risk_parity_allocation(identifiers, volatilities)
            elif self.allocation_method == AllocationMethod.PERFORMANCE_BASED:
                allocations = self._performance_based_allocation(identifiers, performances)
            else:  # DYNAMIC
                allocations = self._dynamic_allocation(identifiers, volatilities, performances)
        
            # Create or update budgets
            for identifier, allocation in allocations.items():
                if identifier in self.budgets:
                    # Update existing budget
                    self.budgets[identifier].allocated_risk_pct = allocation
                    self.budgets[identifier].volatility = volatilities.get(identifier, 0.01)
                    self.budgets[identifier].performance_score = performances.get(identifier, 1.0)
                    self.budgets[identifier].last_updated = datetime.now()
                else:
                    # Create new budget
                    self.budgets[identifier] = RiskBudget(
                        identifier=identifier,
                        allocated_risk_pct=allocation,
                        volatility=volatilities.get(identifier, 0.01),
                        performance_score=performances.get(identifier, 1.0)
                    )
        
            self.last_rebalance = datetime.now()
            logger.info(f"Allocated budgets to {len(identifiers)} identifiers")
        
            return self.budgets
        except Exception as e:
            logger.error(f"Error in allocate_budgets: {e}")
            raise
    
    def _equal_weight_allocation(self, identifiers: List[str]) -> Dict[str, float]:
        """Equal weight allocation"""
        try:
            allocation = self.total_risk_budget / len(identifiers)
            return {id: allocation for id in identifiers}
        except Exception as e:
            logger.error(f"Error in _equal_weight_allocation: {e}")
            raise
    
    def _volatility_parity_allocation(self, identifiers: List[str], 
                                     volatilities: Dict[str, float]) -> Dict[str, float]:
        """Inverse volatility weighting"""
        # Use inverse volatility
        try:
            inv_vols = {}
            for id in identifiers:
                vol = volatilities.get(id, 0.01)
                inv_vols[id] = 1.0 / max(vol, 0.001)  # Avoid division by zero
        
            # Normalize to total budget
            total_inv_vol = sum(inv_vols.values())
            return {
                id: (inv_vol / total_inv_vol) * self.total_risk_budget
                for id, inv_vol in inv_vols.items()
            }
        except Exception as e:
            logger.error(f"Error in _volatility_parity_allocation: {e}")
            raise
    
    def _risk_parity_allocation(self, identifiers: List[str],
                               volatilities: Dict[str, float]) -> Dict[str, float]:
        """Risk parity allocation (equal risk contribution)"""
        # Simplified risk parity: inverse volatility with normalization
        return self._volatility_parity_allocation(identifiers, volatilities)
    
    def _performance_based_allocation(self, identifiers: List[str],
                                     performances: Dict[str, float]) -> Dict[str, float]:
        """Allocate based on performance scores"""
        # Use performance scores (higher = more allocation)
        try:
            perf_scores = {id: max(performances.get(id, 1.0), 0.1) for id in identifiers}
        
            total_perf = sum(perf_scores.values())
            return {
                id: (score / total_perf) * self.total_risk_budget
                for id, score in perf_scores.items()
            }
        except Exception as e:
            logger.error(f"Error in _performance_based_allocation: {e}")
            raise
    
    def _dynamic_allocation(self, identifiers: List[str],
                           volatilities: Dict[str, float],
                           performances: Dict[str, float]) -> Dict[str, float]:
        """Dynamic allocation combining volatility and performance"""
        # Combine inverse volatility and performance
        try:
            scores = {}
            for id in identifiers:
                vol = volatilities.get(id, 0.01)
                perf = performances.get(id, 1.0)
            
                # Score = performance / volatility (risk-adjusted return proxy)
                scores[id] = max(perf, 0.1) / max(vol, 0.001)
        
            total_score = sum(scores.values())
            return {
                id: (score / total_score) * self.total_risk_budget
                for id, score in scores.items()
            }
        except Exception as e:
            logger.error(f"Error in _dynamic_allocation: {e}")
            raise
    
    def check_budget(self, identifier: str, requested_risk: float) -> Dict[str, Any]:
        """
        Check if requested risk is within budget
        
        Args:
            identifier: Symbol or strategy name
            requested_risk: Requested risk amount (% of portfolio)
            
        Returns:
            Check result with approval status
        """
        try:
            if identifier not in self.budgets:
                return {
                    'approved': False,
                    'reason': f'No budget allocated for {identifier}',
                    'available_risk': 0,
                    'requested_risk': requested_risk
                }
        
            budget = self.budgets[identifier]
            available = budget.available_risk_pct
        
            if requested_risk <= available:
                return {
                    'approved': True,
                    'available_risk': available,
                    'requested_risk': requested_risk,
                    'utilization': budget.utilization_pct
                }
            else:
                return {
                    'approved': False,
                    'reason': f'Insufficient budget: requested {requested_risk:.4f}%, available {available:.4f}%',
                    'available_risk': available,
                    'requested_risk': requested_risk,
                    'utilization': budget.utilization_pct
                }
        except Exception as e:
            logger.error(f"Error in check_budget: {e}")
            raise
    
    def allocate_risk(self, identifier: str, risk_amount: float) -> bool:
        """
        Allocate risk from budget
        
        Args:
            identifier: Symbol or strategy name
            risk_amount: Risk amount to allocate
            
        Returns:
            True if allocated successfully
        """
        try:
            check = self.check_budget(identifier, risk_amount)
        
            if check['approved']:
                self.budgets[identifier].used_risk_pct += risk_amount
                logger.info(
                    f"Allocated {risk_amount:.4f}% risk to {identifier}, "
                    f"utilization: {self.budgets[identifier].utilization_pct:.1f}%"
                )
                return True
            else:
                logger.warning(f"Risk allocation rejected for {identifier}: {check['reason']}")
                return False
        except Exception as e:
            logger.error(f"Error in allocate_risk: {e}")
            raise
    
    def release_risk(self, identifier: str, risk_amount: float):
        """Release risk back to budget"""
        try:
            if identifier in self.budgets:
                self.budgets[identifier].used_risk_pct = max(
                    0, self.budgets[identifier].used_risk_pct - risk_amount
                )
                logger.info(f"Released {risk_amount:.4f}% risk from {identifier}")
        except Exception as e:
            logger.error(f"Error in release_risk: {e}")
            raise
    
    def get_budget(self, identifier: str) -> Optional[RiskBudget]:
        """Get budget for identifier"""
        return self.budgets.get(identifier)
    
    def get_all_budgets(self) -> Dict[str, RiskBudget]:
        """Get all budgets"""
        return self.budgets.copy()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get allocator statistics"""
        try:
            total_allocated = sum(b.allocated_risk_pct for b in self.budgets.values())
            total_used = sum(b.used_risk_pct for b in self.budgets.values())
        
            return {
                'total_risk_budget': self.total_risk_budget,
                'total_allocated': total_allocated,
                'total_used': total_used,
                'utilization_pct': (total_used / self.total_risk_budget * 100) if self.total_risk_budget > 0 else 0,
                'num_budgets': len(self.budgets),
                'allocation_method': self.allocation_method.value,
                'last_rebalance': self.last_rebalance.isoformat(),
                'budgets': {
                    id: {
                        'allocated': b.allocated_risk_pct,
                        'used': b.used_risk_pct,
                        'available': b.available_risk_pct,
                        'utilization': b.utilization_pct
                    }
                    for id, b in self.budgets.items()
                }
            }
        except Exception as e:
            logger.error(f"Error in get_stats: {e}")
            raise
