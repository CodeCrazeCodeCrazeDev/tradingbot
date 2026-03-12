"""
AlphaAlgo Self-Optimizer - Automatic Parameter Optimization

This module handles automatic optimization of trading parameters.
All optimization is bounded by the IMMUTABLE reward model constraints.

Version: 1.0.0
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional
from enum import Enum
import logging
import random
import math

from .reward_model import get_reward_model, MAX_RISK_PER_TRADE, MAX_DRAWDOWN

logger = logging.getLogger(__name__)


class OptimizationTarget(Enum):
    """What to optimize"""
    SIGNAL_WEIGHTS = "signal_weights"
    RISK_PARAMETERS = "risk_parameters"
    EXECUTION_PARAMETERS = "execution_parameters"
    REGIME_ADJUSTMENTS = "regime_adjustments"
    ENTRY_TIMING = "entry_timing"
    EXIT_TIMING = "exit_timing"
    POSITION_SIZING = "position_sizing"


@dataclass
class OptimizationResult:
    """Result of an optimization cycle"""
    success: bool
    target: OptimizationTarget
    
    # Before/after
    original_params: Dict[str, Any]
    optimized_params: Dict[str, Any]
    
    # Performance
    original_score: float
    optimized_score: float
    improvement: float
    
    # Metadata
    iterations: int
    method: str
    timestamp: datetime = field(default_factory=datetime.now)
    
    @property
    def is_improvement(self) -> bool:
        return self.improvement > 0


class SelfOptimizer:
    """
    Self-optimization system for trading parameters.
    
    Key principles:
    1. All optimizations are bounded by the IMMUTABLE reward model
    2. No optimization can increase risk beyond limits
    3. All changes require validation before deployment
    4. Optimization is guided by the reward function
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.reward_model = get_reward_model()
        
        # Optimization bounds (derived from reward model)
        self._bounds = {
            'risk_per_trade': (0.005, MAX_RISK_PER_TRADE),  # 0.5% to 2%
            'position_size': (0.01, 0.10),  # 1% to 10%
            'stop_loss_mult': (0.5, 2.0),
            'take_profit_mult': (1.0, 5.0),
            'signal_weight': (0.1, 0.5),
            'confidence_threshold': (0.5, 0.95),
            'urgency_threshold': (0.3, 0.9),
        }
        
        # Optimization history
        self._history: List[OptimizationResult] = []
        
        logger.info("SelfOptimizer initialized")
    
    def optimize(
        self,
        target: OptimizationTarget,
        current_params: Dict[str, Any],
        evaluation_fn: Callable[[Dict[str, Any]], float],
        max_iterations: int = 100
    ) -> OptimizationResult:
        """
        Optimize parameters for a specific target.
        
        Args:
            target: What to optimize
            current_params: Current parameter values
            evaluation_fn: Function to evaluate parameter quality (returns score)
            max_iterations: Maximum optimization iterations
        
        Returns:
            OptimizationResult with original and optimized parameters
        """
        logger.info(f"Starting optimization for {target.value}")
        
        # Evaluate original
        original_score = evaluation_fn(current_params)
        
        # Choose optimization method
        if target == OptimizationTarget.SIGNAL_WEIGHTS:
            optimized_params, iterations = self._optimize_signal_weights(
                current_params, evaluation_fn, max_iterations
            )
        elif target == OptimizationTarget.RISK_PARAMETERS:
            optimized_params, iterations = self._optimize_risk_params(
                current_params, evaluation_fn, max_iterations
            )
        elif target == OptimizationTarget.EXECUTION_PARAMETERS:
            optimized_params, iterations = self._optimize_execution_params(
                current_params, evaluation_fn, max_iterations
            )
        elif target == OptimizationTarget.POSITION_SIZING:
            optimized_params, iterations = self._optimize_position_sizing(
                current_params, evaluation_fn, max_iterations
            )
        else:
            optimized_params, iterations = self._generic_optimize(
                current_params, evaluation_fn, max_iterations
            )
        
        # Evaluate optimized
        optimized_score = evaluation_fn(optimized_params)
        
        # Validate against reward model constraints
        if not self._validate_params(optimized_params):
            logger.warning("Optimized params violate constraints, reverting")
            optimized_params = current_params
            optimized_score = original_score
        
        result = OptimizationResult(
            success=optimized_score > original_score,
            target=target,
            original_params=current_params,
            optimized_params=optimized_params,
            original_score=original_score,
            optimized_score=optimized_score,
            improvement=optimized_score - original_score,
            iterations=iterations,
            method=self._get_method_name(target),
        )
        
        self._history.append(result)
        logger.info(f"Optimization complete: improvement={result.improvement:.4f}")
        
        return result
    
    def _optimize_signal_weights(
        self,
        params: Dict[str, Any],
        eval_fn: Callable,
        max_iter: int
    ) -> tuple:
        """Optimize signal weights using grid search"""
        best_params = params.copy()
        best_score = eval_fn(params)
        
        weights = params.get('signal_weights', {})
        weight_keys = list(weights.keys())
        
        iterations = 0
        for _ in range(max_iter):
            iterations += 1
            
            # Generate candidate weights (must sum to 1)
            new_weights = {}
            remaining = 1.0
            for i, key in enumerate(weight_keys[:-1]):
                max_w = min(remaining - 0.1 * (len(weight_keys) - i - 1), 0.5)
                new_weights[key] = random.uniform(0.1, max_w)
                remaining -= new_weights[key]
            new_weights[weight_keys[-1]] = remaining
            
            # Evaluate
            test_params = params.copy()
            test_params['signal_weights'] = new_weights
            score = eval_fn(test_params)
            
            if score > best_score:
                best_score = score
                best_params = test_params.copy()
        
        return best_params, iterations
    
    def _optimize_risk_params(
        self,
        params: Dict[str, Any],
        eval_fn: Callable,
        max_iter: int
    ) -> tuple:
        """Optimize risk parameters using bounded search"""
        best_params = params.copy()
        best_score = eval_fn(params)
        
        risk_params = params.get('risk', {})
        
        iterations = 0
        for _ in range(max_iter):
            iterations += 1
            
            # Generate candidate risk params (bounded by reward model)
            new_risk = {
                'base_risk_percent': random.uniform(
                    self._bounds['risk_per_trade'][0],
                    self._bounds['risk_per_trade'][1]
                ),
                'confidence_multiplier': random.uniform(1.0, 2.0),
                'drawdown_reduction_factor': random.uniform(0.3, 0.7),
            }
            
            # Evaluate
            test_params = params.copy()
            test_params['risk'] = new_risk
            score = eval_fn(test_params)
            
            if score > best_score:
                best_score = score
                best_params = test_params.copy()
        
        return best_params, iterations
    
    def _optimize_execution_params(
        self,
        params: Dict[str, Any],
        eval_fn: Callable,
        max_iter: int
    ) -> tuple:
        """Optimize execution parameters"""
        best_params = params.copy()
        best_score = eval_fn(params)
        
        iterations = 0
        for _ in range(max_iter):
            iterations += 1
            
            new_exec = {
                'max_slippage_bps': random.uniform(2, 10),
                'urgency_threshold': random.uniform(
                    self._bounds['urgency_threshold'][0],
                    self._bounds['urgency_threshold'][1]
                ),
                'split_order_threshold': random.randint(5000, 50000),
            }
            
            test_params = params.copy()
            test_params['execution'] = new_exec
            score = eval_fn(test_params)
            
            if score > best_score:
                best_score = score
                best_params = test_params.copy()
        
        return best_params, iterations
    
    def _optimize_position_sizing(
        self,
        params: Dict[str, Any],
        eval_fn: Callable,
        max_iter: int
    ) -> tuple:
        """Optimize position sizing parameters"""
        best_params = params.copy()
        best_score = eval_fn(params)
        
        iterations = 0
        for _ in range(max_iter):
            iterations += 1
            
            new_sizing = {
                'base_size_percent': random.uniform(0.01, 0.05),
                'max_size_percent': random.uniform(0.05, 0.10),
                'confidence_scaling': random.uniform(0.5, 1.5),
                'volatility_adjustment': random.uniform(0.5, 1.5),
            }
            
            test_params = params.copy()
            test_params['position_sizing'] = new_sizing
            score = eval_fn(test_params)
            
            if score > best_score:
                best_score = score
                best_params = test_params.copy()
        
        return best_params, iterations
    
    def _generic_optimize(
        self,
        params: Dict[str, Any],
        eval_fn: Callable,
        max_iter: int
    ) -> tuple:
        """Generic optimization using simulated annealing"""
        best_params = params.copy()
        current_params = params.copy()
        best_score = eval_fn(params)
        current_score = best_score
        
        temperature = 1.0
        cooling_rate = 0.95
        
        iterations = 0
        for _ in range(max_iter):
            iterations += 1
            
            # Generate neighbor
            new_params = self._perturb_params(current_params)
            new_score = eval_fn(new_params)
            
            # Accept or reject
            delta = new_score - current_score
            if delta > 0 or random.random() < math.exp(delta / temperature):
                current_params = new_params
                current_score = new_score
                
                if current_score > best_score:
                    best_score = current_score
                    best_params = current_params.copy()
            
            temperature *= cooling_rate
        
        return best_params, iterations
    
    def _perturb_params(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Slightly perturb parameters"""
        new_params = {}
        for key, value in params.items():
            if isinstance(value, dict):
                new_params[key] = self._perturb_params(value)
            elif isinstance(value, float):
                # Perturb by up to 10%
                perturbation = value * random.uniform(-0.1, 0.1)
                new_params[key] = value + perturbation
            elif isinstance(value, int):
                perturbation = int(value * random.uniform(-0.1, 0.1))
                new_params[key] = value + perturbation
            else:
                new_params[key] = value
        return new_params
    
    def _validate_params(self, params: Dict[str, Any]) -> bool:
        """Validate parameters against reward model constraints"""
        # Check risk bounds
        risk = params.get('risk', {})
        if risk.get('base_risk_percent', 0) > MAX_RISK_PER_TRADE:
            return False
        
        # Check position sizing bounds
        sizing = params.get('position_sizing', {})
        if sizing.get('max_size_percent', 0) > 0.10:  # 10% max
            return False
        
        # Check signal weights sum to ~1
        weights = params.get('signal_weights', {})
        if weights:
            total = sum(weights.values())
            if abs(total - 1.0) > 0.01:
                return False
        
        return True
    
    def _get_method_name(self, target: OptimizationTarget) -> str:
        """Get optimization method name for target"""
        methods = {
            OptimizationTarget.SIGNAL_WEIGHTS: "grid_search",
            OptimizationTarget.RISK_PARAMETERS: "bounded_random",
            OptimizationTarget.EXECUTION_PARAMETERS: "random_search",
            OptimizationTarget.POSITION_SIZING: "random_search",
        }
        return methods.get(target, "simulated_annealing")
    
    def get_optimization_history(self) -> List[OptimizationResult]:
        """Get optimization history"""
        return self._history.copy()
    
    def get_best_params(self, target: OptimizationTarget) -> Optional[Dict[str, Any]]:
        """Get best parameters found for a target"""
        relevant = [r for r in self._history if r.target == target and r.is_improvement]
        if not relevant:
            return None
        
        best = max(relevant, key=lambda r: r.optimized_score)
        return best.optimized_params
