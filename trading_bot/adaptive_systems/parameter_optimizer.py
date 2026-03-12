import logging
logger = logging.getLogger(__name__)
"""Self-Optimizing Parameter System.

This module implements automatic parameter optimization that continuously
adjusts trading parameters based on performance feedback and market conditions.
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, field
from loguru import logger
from scipy.optimize import minimize
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import Matern
from .market_regime import MarketRegime
from typing import Set
import numpy
import pandas


@dataclass
class ParameterBounds:
    """Parameter bounds for optimization."""
    min_value: float
    max_value: float
    step_size: Optional[float] = None
    parameter_type: str = "continuous"  # continuous, discrete, categorical


@dataclass
class OptimizationResult:
    """Result of parameter optimization."""
    parameters: Dict[str, Any]
    performance_score: float
    confidence: float
    iterations: int
    improvement: float
    timestamp: datetime = field(default_factory=datetime.now)


class ParameterOptimizer:
    """Self-optimizing parameter system using Bayesian optimization."""
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize the parameter optimizer.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.optimization_history = []
        self.current_parameters = {}
        self.parameter_bounds = {}
        self.performance_history = []
        
        # Optimization settings
        self.min_samples = self.config.get('min_samples', 20)
        self.optimization_frequency = self.config.get('optimization_frequency', 100)  # trades
        self.improvement_threshold = self.config.get('improvement_threshold', 0.05)
        
        # Gaussian Process for Bayesian optimization
        kernel = Matern(length_scale=1.0, nu=2.5)
        self.gp_model = GaussianProcessRegressor(kernel=kernel, alpha=1e-6, normalize_y=True)
        
        # Initialize default parameters
        self._initialize_default_parameters()
        
        logger.info("ParameterOptimizer initialized")
    
    def _initialize_default_parameters(self):
        """Initialize default trading parameters and their bounds."""
        # Risk management parameters
        self.parameter_bounds.update({
            'risk_per_trade': ParameterBounds(0.005, 0.05, 0.005),  # 0.5% to 5%
            'stop_loss_atr': ParameterBounds(1.0, 4.0, 0.1),
            'take_profit_rr': ParameterBounds(1.0, 4.0, 0.1),
            'trailing_stop_atr': ParameterBounds(1.5, 3.5, 0.1),
            'max_positions': ParameterBounds(1, 10, 1, "discrete"),
        })
        
        # Technical indicator parameters
        self.parameter_bounds.update({
            'rsi_period': ParameterBounds(10, 30, 1, "discrete"),
            'rsi_oversold': ParameterBounds(20, 35, 1, "discrete"),
            'rsi_overbought': ParameterBounds(65, 80, 1, "discrete"),
            'ma_fast': ParameterBounds(5, 20, 1, "discrete"),
            'ma_slow': ParameterBounds(20, 100, 5, "discrete"),
            'bb_period': ParameterBounds(15, 30, 1, "discrete"),
            'bb_std': ParameterBounds(1.5, 2.5, 0.1),
        })
        
        # Entry/Exit parameters
        self.parameter_bounds.update({
            'entry_confidence': ParameterBounds(0.6, 0.9, 0.05),
            'exit_confidence': ParameterBounds(0.5, 0.8, 0.05),
            'sentiment_weight': ParameterBounds(0.1, 0.5, 0.05),
        })
        
        # Set default values (middle of ranges)
        self.current_parameters = {
            name: (bounds.min_value + bounds.max_value) / 2
            for name, bounds in self.parameter_bounds.items()
        }
        
        # Adjust discrete parameters
        for name, bounds in self.parameter_bounds.items():
            if bounds.parameter_type == "discrete":
                self.current_parameters[name] = int(self.current_parameters[name])
    
    def update_performance(self, trade_result: Dict[str, Any]):
        """Update performance history with new trade result.
        
        Args:
            trade_result: Dictionary containing trade performance data
        """
        # Add current parameters to trade result
        trade_result['parameters'] = self.current_parameters.copy()
        trade_result['timestamp'] = datetime.now()
        
        self.performance_history.append(trade_result)
        
        # Trigger optimization if enough samples
        if len(self.performance_history) >= self.min_samples:
            if len(self.performance_history) % self.optimization_frequency == 0:
                self._trigger_optimization()
        
        logger.debug(f"Performance updated: {len(self.performance_history)} samples")
    
    def _trigger_optimization(self):
        """Trigger parameter optimization process."""
        logger.info("Triggering parameter optimization")
        
        try:
            # Prepare data for optimization
            X, y = self._prepare_optimization_data()
            
            if len(X) < self.min_samples:
                logger.warning(f"Insufficient data for optimization: {len(X)} < {self.min_samples}")
                return
            
            # Perform Bayesian optimization
            result = self._bayesian_optimize(X, y)
            
            if result and result.improvement > self.improvement_threshold:
                logger.info(f"Parameter optimization successful: {result.improvement:.2%} improvement")
                self.current_parameters.update(result.parameters)
                self.optimization_history.append(result)
            else:
                logger.info("No significant improvement found in optimization")
                
        except Exception as e:
            logger.error(f"Error during parameter optimization: {e}")
    
    def _prepare_optimization_data(self) -> Tuple[np.ndarray, np.ndarray]:
        """Prepare data for optimization."""
        recent_trades = self.performance_history[-200:]  # Last 200 trades
        
        X = []  # Parameter vectors
        y = []  # Performance scores
        
        for trade in recent_trades:
            if 'parameters' not in trade or 'pnl' not in trade:
                continue
            
            # Create parameter vector
            param_vector = []
            for param_name in sorted(self.parameter_bounds.keys()):
                value = trade['parameters'].get(param_name, self.current_parameters[param_name])
                # Normalize to [0, 1]
                bounds = self.parameter_bounds[param_name]
                normalized = (value - bounds.min_value) / (bounds.max_value - bounds.min_value)
                param_vector.append(normalized)
            
            X.append(param_vector)
            
            # Calculate performance score
            pnl = trade['pnl']
            duration = trade.get('duration_minutes', 60)
            drawdown = trade.get('max_drawdown', 0)
            
            # Composite score: profit per minute adjusted for drawdown
            score = (pnl / duration) * (1 - abs(drawdown))
            y.append(score)
        
        return np.array(X), np.array(y)
    
    def _bayesian_optimize(self, X: np.ndarray, y: np.ndarray) -> Optional[OptimizationResult]:
        """Perform Bayesian optimization using Gaussian Process."""
        # Fit Gaussian Process
        self.gp_model.fit(X, y)
        
        # Define acquisition function (Expected Improvement)
        def acquisition_function(x):
            """Expected Improvement acquisition function."""
            x = x.reshape(1, -1)
            mu, sigma = self.gp_model.predict(x, return_std=True)
            
            # Expected Improvement
            best_y = np.max(y)
            z = (mu - best_y) / (sigma + 1e-9)
            ei = (mu - best_y) * self._normal_cdf(z) + sigma * self._normal_pdf(z)
            return -ei[0]  # Minimize negative EI
        
        # Optimize acquisition function
        best_params = None
        best_score = float('inf')
            
        # Multiple random starts
        for _ in range(10):
            x0 = np.random.random(len(self.parameter_bounds))
            
            result = minimize(
                acquisition_function,
                x0,
                bounds=[(0, 1)] * len(self.parameter_bounds),
                method='L-BFGS-B'
            )
            
            if result.success and result.fun < best_score:
                best_score = result.fun
                best_params = result.x
        
        if best_params is None:
            return None
        
        # Convert normalized parameters back to original scale
        optimized_params = {}
        for i, param_name in enumerate(sorted(self.parameter_bounds.keys())):
            bounds = self.parameter_bounds[param_name]
            value = bounds.min_value + best_params[i] * (bounds.max_value - bounds.min_value)
            
            if bounds.parameter_type == "discrete":
                value = int(round(value))
            
            optimized_params[param_name] = value
        
        # Estimate performance improvement
        current_vector = self._params_to_vector(self.current_parameters)
        optimized_vector = best_params.reshape(1, -1)
        
        current_pred, _ = self.gp_model.predict(current_vector.reshape(1, -1), return_std=True)
        optimized_pred, confidence = self.gp_model.predict(optimized_vector, return_std=True)
        
        improvement = (optimized_pred[0] - current_pred[0]) / abs(current_pred[0]) if current_pred[0] != 0 else 0
        
        return OptimizationResult(
            parameters=optimized_params,
            performance_score=optimized_pred[0],
            confidence=1.0 / (confidence[0] + 1e-6),
            iterations=len(self.optimization_history) + 1,
            improvement=improvement
        )
    
    def _params_to_vector(self, params: Dict[str, Any]) -> np.ndarray:
        """Convert parameter dictionary to normalized vector."""
        vector = []
        for param_name in sorted(self.parameter_bounds.keys()):
            value = params.get(param_name, self.current_parameters[param_name])
            bounds = self.parameter_bounds[param_name]
            normalized = (value - bounds.min_value) / (bounds.max_value - bounds.min_value)
            vector.append(normalized)
        return np.array(vector)
    
    def _normal_cdf(self, x):
        """Standard normal cumulative distribution function."""
        return 0.5 * (1 + np.sign(x) * np.sqrt(1 - np.exp(-2 * x**2 / np.pi)))
    
    def _normal_pdf(self, x):
        """Standard normal probability density function."""
        return np.exp(-0.5 * x**2) / np.sqrt(2 * np.pi)
    
    def get_regime_specific_parameters(self, regime: MarketRegime) -> Dict[str, Any]:
        """Get parameters optimized for specific market regime.
        
        Args:
            regime: Market regime
            
        Returns:
            Dictionary of optimized parameters for the regime
        """
        # Filter optimization history by regime
        regime_optimizations = [
            opt for opt in self.optimization_history
            if hasattr(opt, 'regime') and opt.regime == regime
        ]
        
        if regime_optimizations:
            # Use most recent successful optimization for this regime
            best_opt = max(regime_optimizations, key=lambda x: x.performance_score)
            return best_opt.parameters
        
        # Apply regime-specific adjustments to current parameters
        adjusted_params = self.current_parameters.copy()
        
        regime_adjustments = {
            MarketRegime.TRENDING_BULL: {
                'risk_per_trade': 1.2,
                'take_profit_rr': 1.3,
                'trailing_stop_atr': 0.9
            },
            MarketRegime.TRENDING_BEAR: {
                'risk_per_trade': 0.8,
                'stop_loss_atr': 1.1,
                'take_profit_rr': 0.9
            },
            MarketRegime.HIGH_VOLATILITY: {
                'risk_per_trade': 0.6,
                'stop_loss_atr': 1.5,
                'bb_std': 1.2
            },
            MarketRegime.LOW_VOLATILITY: {
                'risk_per_trade': 1.1,
                'stop_loss_atr': 0.8,
                'bb_std': 0.9
            },
            MarketRegime.RANGING: {
                'take_profit_rr': 0.8,
                'rsi_oversold': 1.1,
                'rsi_overbought': 0.9
            }
        }
        
        adjustments = regime_adjustments.get(regime, {})
        for param, multiplier in adjustments.items():
            if param in adjusted_params:
                bounds = self.parameter_bounds[param]
                new_value = adjusted_params[param] * multiplier
                adjusted_params[param] = max(bounds.min_value, min(bounds.max_value, new_value))
                
                if bounds.parameter_type == "discrete":
                    adjusted_params[param] = int(round(adjusted_params[param]))
        
        return adjusted_params
    
    def get_optimization_summary(self) -> Dict[str, Any]:
        """Get summary of optimization performance."""
        if not self.optimization_history:
            return {'status': 'no_optimizations', 'current_parameters': self.current_parameters}
        
        recent_opts = self.optimization_history[-10:]
        avg_improvement = np.mean([opt.improvement for opt in recent_opts])
        
        return {
            'status': 'active',
            'total_optimizations': len(self.optimization_history),
            'average_improvement': avg_improvement,
            'last_optimization': self.optimization_history[-1].timestamp,
            'current_parameters': self.current_parameters,
            'performance_samples': len(self.performance_history)
        }
