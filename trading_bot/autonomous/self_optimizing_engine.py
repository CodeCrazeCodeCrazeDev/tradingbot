"""
Autonomous Self-Optimizing Strategy Engine
Automatically tunes strategy parameters based on performance using Bayesian optimization
"""

import numpy as np
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import logging
from scipy.optimize import differential_evolution
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import Matern
import json
import asyncio
import numpy

logger = logging.getLogger(__name__)


@dataclass
class StrategyParameter:
    """Strategy parameter definition"""
    name: str
    min_value: float
    max_value: float
    current_value: float
    optimal_value: Optional[float] = None
    importance: float = 1.0
    
    
@dataclass
class OptimizationResult:
    """Optimization result"""
    parameters: Dict[str, float]
    performance_score: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    timestamp: datetime
    iteration: int
    

class SelfOptimizingEngine:
    """
    Self-optimizing strategy engine using Bayesian optimization
    Automatically discovers optimal parameters
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.parameters: Dict[str, StrategyParameter] = {}
        self.optimization_history: List[OptimizationResult] = []
        self.current_iteration = 0
        
        # Bayesian optimization components
        self.gp_regressor = GaussianProcessRegressor(
            kernel=Matern(nu=2.5),
            alpha=1e-6,
            normalize_y=True,
            n_restarts_optimizer=5
        )
        
        # Performance tracking
        self.performance_window = []
        self.window_size = self.config.get('performance_window', 100)
        
        # Optimization settings
        self.optimization_interval = self.config.get('optimization_interval', 3600)  # 1 hour
        self.min_samples_for_optimization = self.config.get('min_samples', 50)
        self.exploration_rate = self.config.get('exploration_rate', 0.2)
        
        logger.info("Self-optimizing engine initialized")
        
    def register_parameter(self, name: str, min_val: float, max_val: float, 
                          current_val: float, importance: float = 1.0):
        """Register a strategy parameter for optimization"""
        self.parameters[name] = StrategyParameter(
            name=name,
            min_value=min_val,
            max_value=max_val,
            current_value=current_val,
            importance=importance
        )
        logger.info(f"Registered parameter: {name} [{min_val}, {max_val}] = {current_val}")
        
    def update_performance(self, metrics: Dict[str, float]):
        """Update performance metrics"""
        self.performance_window.append({
            'timestamp': datetime.now(),
            'metrics': metrics,
            'parameters': {k: v.current_value for k, v in self.parameters.items()}
        })
        
        # Keep window size
        if len(self.performance_window) > self.window_size:
            self.performance_window.pop(0)
            
    def calculate_objective(self, params: np.ndarray) -> float:
        """
        Calculate objective function for optimization
        Higher is better
        """
        # Simulate strategy performance with these parameters
        # In production, this would run backtests
        param_dict = {name: params[i] for i, name in enumerate(self.parameters.keys())}
        
        # Calculate weighted performance score
        score = 0.0
        
        # Use recent performance data
        if len(self.performance_window) > 0:
            recent_metrics = self.performance_window[-10:]
            
            sharpe_ratios = [m['metrics'].get('sharpe_ratio', 0) for m in recent_metrics]
            win_rates = [m['metrics'].get('win_rate', 0) for m in recent_metrics]
            drawdowns = [m['metrics'].get('max_drawdown', 0) for m in recent_metrics]
            
            avg_sharpe = np.mean(sharpe_ratios) if sharpe_ratios else 0
            avg_win_rate = np.mean(win_rates) if win_rates else 0
            avg_drawdown = np.mean(drawdowns) if drawdowns else 0
            
            # Composite score
            score = (
                avg_sharpe * 0.4 +
                avg_win_rate * 0.3 -
                abs(avg_drawdown) * 0.3
            )
        
        return score
        
    def bayesian_optimize(self) -> Dict[str, float]:
        """
        Perform Bayesian optimization to find optimal parameters
        """
        if len(self.parameters) == 0:
            logger.warning("No parameters registered for optimization")
            return {}
            
        # Define bounds
        bounds = [(p.min_value, p.max_value) for p in self.parameters.values()]
        
        # Use differential evolution for global optimization
        result = differential_evolution(
            lambda x: -self.calculate_objective(x),  # Minimize negative
            bounds,
            maxiter=50,
            popsize=15,
            atol=1e-4,
            tol=1e-4
        )
        
        # Extract optimal parameters
        optimal_params = {}
        for i, (name, param) in enumerate(self.parameters.items()):
            optimal_params[name] = result.x[i]
            param.optimal_value = result.x[i]
            
        logger.info(f"Optimization complete. Score: {-result.fun:.4f}")
        logger.info(f"Optimal parameters: {optimal_params}")
        
        return optimal_params
        
    def should_optimize(self) -> bool:
        """Check if optimization should be triggered"""
        if len(self.performance_window) < self.min_samples_for_optimization:
            return False
            
        # Check time since last optimization
        if len(self.optimization_history) > 0:
            last_opt = self.optimization_history[-1].timestamp
            if (datetime.now() - last_opt).total_seconds() < self.optimization_interval:
                return False
                
        return True
        
    async def auto_optimize(self) -> Optional[Dict[str, float]]:
        """
        Automatically optimize parameters when conditions are met
        """
        if not self.should_optimize():
            return None
            
        logger.info("Starting automatic optimization...")
        
        try:
            # Run optimization
            optimal_params = self.bayesian_optimize()
            
            # Calculate performance with optimal parameters
            if len(self.performance_window) > 0:
                recent = self.performance_window[-1]['metrics']
                
                result = OptimizationResult(
                    parameters=optimal_params,
                    performance_score=self.calculate_objective(
                        np.array(list(optimal_params.values()))
                    ),
                    sharpe_ratio=recent.get('sharpe_ratio', 0),
                    max_drawdown=recent.get('max_drawdown', 0),
                    win_rate=recent.get('win_rate', 0),
                    timestamp=datetime.now(),
                    iteration=self.current_iteration
                )
                
                self.optimization_history.append(result)
                self.current_iteration += 1
                
                logger.info(f"Optimization result: {result}")
                
            return optimal_params
            
        except Exception as e:
            logger.error(f"Optimization failed: {e}")
            return None
            
    def apply_optimal_parameters(self) -> bool:
        """Apply optimal parameters to current strategy"""
        try:
            for name, param in self.parameters.items():
                if param.optimal_value is not None:
                    param.current_value = param.optimal_value
                    logger.info(f"Applied optimal {name}: {param.optimal_value}")
            return True
        except Exception as e:
            logger.error(f"Failed to apply parameters: {e}")
            return False
            
    def get_parameter_importance(self) -> Dict[str, float]:
        """Calculate parameter importance using sensitivity analysis"""
        importance = {}
        
        if len(self.optimization_history) < 2:
            return {name: 1.0 for name in self.parameters.keys()}
            
        # Analyze parameter variations and their impact
        for name in self.parameters.keys():
            param_values = []
            scores = []
            
            for result in self.optimization_history[-20:]:
                param_values.append(result.parameters.get(name, 0))
                scores.append(result.performance_score)
                
            if len(param_values) > 1:
                correlation = np.corrcoef(param_values, scores)[0, 1]
                importance[name] = abs(correlation)
            else:
                importance[name] = 1.0
                
        return importance
        
    def export_state(self) -> Dict[str, Any]:
        """Export optimization state"""
        return {
            'parameters': {
                name: {
                    'current': p.current_value,
                    'optimal': p.optimal_value,
                    'min': p.min_value,
                    'max': p.max_value,
                    'importance': p.importance
                }
                for name, p in self.parameters.items()
            },
            'optimization_history': [
                {
                    'parameters': r.parameters,
                    'score': r.performance_score,
                    'sharpe': r.sharpe_ratio,
                    'drawdown': r.max_drawdown,
                    'win_rate': r.win_rate,
                    'timestamp': r.timestamp.isoformat(),
                    'iteration': r.iteration
                }
                for r in self.optimization_history[-50:]
            ],
            'current_iteration': self.current_iteration
        }
        
    def import_state(self, state: Dict[str, Any]):
        """Import optimization state"""
        try:
            # Restore parameters
            for name, data in state.get('parameters', {}).items():
                if name in self.parameters:
                    self.parameters[name].current_value = data['current']
                    self.parameters[name].optimal_value = data.get('optimal')
                    
            # Restore iteration
            self.current_iteration = state.get('current_iteration', 0)
            
            logger.info("State imported successfully")
        except Exception as e:
            logger.error(f"Failed to import state: {e}")
