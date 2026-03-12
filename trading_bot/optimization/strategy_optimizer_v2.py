"""
Strategy Optimizer V2
Advanced strategy optimization using backtesting, parameter tuning, and walk-forward analysis.

Features:
- Grid search optimization
- Bayesian optimization
- Walk-forward validation
- Monte Carlo simulation
- Multi-objective optimization
"""

import asyncio
import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from itertools import product
import json
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
import warnings

logger = logging.getLogger(__name__)


class OptimizationMethod(Enum):
    """Optimization methods"""
    GRID_SEARCH = "grid_search"
    RANDOM_SEARCH = "random_search"
    BAYESIAN = "bayesian"
    GENETIC = "genetic"
    WALK_FORWARD = "walk_forward"


@dataclass
class ParameterSpace:
    """Parameter search space definition"""
    name: str
    param_type: str  # 'int', 'float', 'categorical'
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    step: Optional[float] = None
    values: Optional[List[Any]] = None  # For categorical
    
    def get_values(self, n_samples: int = 10) -> List[Any]:
        """Get parameter values for optimization"""
        if self.param_type == 'categorical':
            return self.values or []
        elif self.param_type == 'int':
            if self.step:
                return list(range(int(self.min_value), int(self.max_value) + 1, int(self.step)))
            return list(np.linspace(self.min_value, self.max_value, n_samples, dtype=int))
        else:  # float
            if self.step:
                return list(np.arange(self.min_value, self.max_value + self.step, self.step))
            return list(np.linspace(self.min_value, self.max_value, n_samples))


@dataclass
class OptimizationResult:
    """Optimization result"""
    best_params: Dict[str, Any]
    best_score: float
    all_results: List[Dict[str, Any]]
    optimization_time: float
    method: str
    validation_results: Optional[Dict] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'best_params': self.best_params,
            'best_score': self.best_score,
            'total_combinations': len(self.all_results),
            'optimization_time': self.optimization_time,
            'method': self.method,
            'validation': self.validation_results,
        }


@dataclass
class BacktestResult:
    """Backtest result for optimization"""
    params: Dict[str, Any]
    total_return: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    profit_factor: float
    total_trades: int
    
    @property
    def score(self) -> float:
        """Combined optimization score"""
        # Multi-objective score combining multiple metrics
        if self.total_trades < 10:
            return -999  # Penalize strategies with too few trades
        
        # Weighted combination
        score = (
            self.sharpe_ratio * 0.4 +
            self.total_return * 100 * 0.3 +
            (1 - abs(self.max_drawdown)) * 0.2 +
            self.win_rate * 0.1
        )
        
        return score


class StrategyBacktester:
    """
    Fast backtester for strategy optimization.
    Optimized for speed during parameter search.
    """
    
    def __init__(self, data: pd.DataFrame, initial_capital: float = 100000.0):
        self.data = data
        self.initial_capital = initial_capital
        
        # Pre-calculate common values
        self.returns = data['close'].pct_change().fillna(0).values
        self.prices = data['close'].values
        self.highs = data['high'].values if 'high' in data.columns else self.prices
        self.lows = data['low'].values if 'low' in data.columns else self.prices
        self.volumes = data['volume'].values if 'volume' in data.columns else np.ones(len(data))
    
    def run(self, strategy_func: Callable, params: Dict[str, Any]) -> BacktestResult:
        """
        Run backtest with given parameters.
        
        Args:
            strategy_func: Strategy function that returns signals
            params: Strategy parameters
            
        Returns:
            BacktestResult
        """
        # Generate signals
        signals = strategy_func(self.data, **params)
        
        # Simulate trading
        capital = self.initial_capital
        position = 0
        entry_price = 0
        trades = []
        equity_curve = [capital]
        
        for i in range(1, len(self.prices)):
            signal = signals[i] if i < len(signals) else 0
            price = self.prices[i]
            
            # Execute trades
            if signal > 0 and position == 0:  # Buy
                position = capital * 0.95 / price  # Use 95% of capital
                entry_price = price
                capital = capital * 0.05  # Keep 5% cash
                
            elif signal < 0 and position > 0:  # Sell
                trade_return = (price - entry_price) / entry_price
                trade_pnl = position * (price - entry_price)
                capital += position * price
                trades.append({
                    'return': trade_return,
                    'pnl': trade_pnl,
                    'entry': entry_price,
                    'exit': price,
                })
                position = 0
            
            # Update equity
            equity = capital + position * price
            equity_curve.append(equity)
        
        # Close any open position
        if position > 0:
            trade_return = (self.prices[-1] - entry_price) / entry_price
            trade_pnl = position * (self.prices[-1] - entry_price)
            capital += position * self.prices[-1]
            trades.append({
                'return': trade_return,
                'pnl': trade_pnl,
                'entry': entry_price,
                'exit': self.prices[-1],
            })
        
        # Calculate metrics
        equity_curve = np.array(equity_curve)
        returns = np.diff(equity_curve) / equity_curve[:-1]
        
        total_return = (equity_curve[-1] - self.initial_capital) / self.initial_capital
        
        # Sharpe ratio (annualized)
        if len(returns) > 0 and np.std(returns) > 0:
            sharpe = np.mean(returns) / np.std(returns) * np.sqrt(252)
        else:
            sharpe = 0
        
        # Max drawdown
        peak = np.maximum.accumulate(equity_curve)
        drawdown = (peak - equity_curve) / peak
        max_dd = np.max(drawdown)
        
        # Win rate and profit factor
        if trades:
            winning = [t for t in trades if t['pnl'] > 0]
            losing = [t for t in trades if t['pnl'] <= 0]
            win_rate = len(winning) / len(trades)
            
            total_wins = sum(t['pnl'] for t in winning) if winning else 0
            total_losses = abs(sum(t['pnl'] for t in losing)) if losing else 1
            profit_factor = total_wins / total_losses if total_losses > 0 else total_wins
        else:
            win_rate = 0
            profit_factor = 0
        
        return BacktestResult(
            params=params,
            total_return=total_return,
            sharpe_ratio=sharpe,
            max_drawdown=max_dd,
            win_rate=win_rate,
            profit_factor=profit_factor,
            total_trades=len(trades),
        )


class StrategyOptimizer:
    """
    Advanced strategy optimizer with multiple optimization methods.
    """
    
    def __init__(self, data: pd.DataFrame, initial_capital: float = 100000.0):
        self.data = data
        self.initial_capital = initial_capital
        self.backtester = StrategyBacktester(data, initial_capital)
        self.results_history: List[OptimizationResult] = []
        
        logger.info(f"StrategyOptimizer initialized with {len(data)} data points")
    
    def optimize(self, 
                strategy_func: Callable,
                param_space: List[ParameterSpace],
                method: OptimizationMethod = OptimizationMethod.GRID_SEARCH,
                n_iterations: int = 100,
                n_jobs: int = 1) -> OptimizationResult:
        """
        Optimize strategy parameters.
        
        Args:
            strategy_func: Strategy function
            param_space: Parameter search space
            method: Optimization method
            n_iterations: Number of iterations (for random/bayesian)
            n_jobs: Number of parallel jobs
            
        Returns:
            OptimizationResult
        """
        start_time = datetime.now()
        
        if method == OptimizationMethod.GRID_SEARCH:
            result = self._grid_search(strategy_func, param_space, n_jobs)
        elif method == OptimizationMethod.RANDOM_SEARCH:
            result = self._random_search(strategy_func, param_space, n_iterations, n_jobs)
        elif method == OptimizationMethod.BAYESIAN:
            result = self._bayesian_optimization(strategy_func, param_space, n_iterations)
        elif method == OptimizationMethod.WALK_FORWARD:
            result = self._walk_forward_optimization(strategy_func, param_space)
        else:
            raise ValueError(f"Unknown optimization method: {method}")
        
        result.optimization_time = (datetime.now() - start_time).total_seconds()
        result.method = method.value
        
        self.results_history.append(result)
        
        logger.info(f"Optimization complete: best_score={result.best_score:.4f}, "
                   f"time={result.optimization_time:.2f}s")
        
        return result
    
    def _grid_search(self, strategy_func: Callable, 
                    param_space: List[ParameterSpace],
                    n_jobs: int = 1) -> OptimizationResult:
        """Grid search optimization"""
        # Generate all parameter combinations
        param_names = [p.name for p in param_space]
        param_values = [p.get_values() for p in param_space]
        combinations = list(product(*param_values))
        
        logger.info(f"Grid search: {len(combinations)} combinations")
        
        all_results = []
        best_result = None
        best_score = float('-inf')
        
        for combo in combinations:
            params = dict(zip(param_names, combo))
            
            try:
                result = self.backtester.run(strategy_func, params)
                all_results.append({
                    'params': params,
                    'score': result.score,
                    'metrics': {
                        'return': result.total_return,
                        'sharpe': result.sharpe_ratio,
                        'max_dd': result.max_drawdown,
                        'win_rate': result.win_rate,
                        'trades': result.total_trades,
                    }
                })
                
                if result.score > best_score:
                    best_score = result.score
                    best_result = result
                    
            except Exception as e:
                logger.warning(f"Error with params {params}: {e}")
        
        return OptimizationResult(
            best_params=best_result.params if best_result else {},
            best_score=best_score,
            all_results=all_results,
            optimization_time=0,
            method='grid_search',
        )
    
    def _random_search(self, strategy_func: Callable,
                      param_space: List[ParameterSpace],
                      n_iterations: int,
                      n_jobs: int = 1) -> OptimizationResult:
        """Random search optimization"""
        all_results = []
        best_result = None
        best_score = float('-inf')
        
        for i in range(n_iterations):
            # Sample random parameters
            params = {}
            for p in param_space:
                pass
            try:
                values = p.get_values(n_samples=100)
                params[p.name] = np.random.choice(values)
            
                result = self.backtester.run(strategy_func, params)
                all_results.append({
                    'params': params,
                    'score': result.score,
                    'iteration': i,
                })
                
                if result.score > best_score:
                    best_score = result.score
                    best_result = result
                    
            except Exception as e:
                logger.warning(f"Error at iteration {i}: {e}")
        
        return OptimizationResult(
            best_params=best_result.params if best_result else {},
            best_score=best_score,
            all_results=all_results,
            optimization_time=0,
            method='random_search',
        )
    
    def _bayesian_optimization(self, strategy_func: Callable,
                              param_space: List[ParameterSpace],
                              n_iterations: int) -> OptimizationResult:
        """Bayesian optimization using Gaussian Process"""
        try:
            from sklearn.gaussian_process import GaussianProcessRegressor
            from sklearn.gaussian_process.kernels import Matern
        except ImportError:
            logger.warning("sklearn not available, falling back to random search")
            return self._random_search(strategy_func, param_space, n_iterations, 1)
        
        # Initialize with random samples
        n_initial = min(10, n_iterations // 3)
        
        X_samples = []
        y_samples = []
        all_results = []
        
        # Initial random sampling
        for _ in range(n_initial):
            params = {}
            x = []
            for p in param_space:
                pass
            try:
                if p.param_type == 'categorical':
                    idx = np.random.randint(len(p.values))
                    params[p.name] = p.values[idx]
                    x.append(idx)
                else:
                    val = np.random.uniform(p.min_value, p.max_value)
                    if p.param_type == 'int':
                        val = int(val)
                    params[p.name] = val
                    x.append(val)
            
                result = self.backtester.run(strategy_func, params)
                X_samples.append(x)
                y_samples.append(result.score)
                all_results.append({'params': params, 'score': result.score})
            except Exception as e:
                logger.warning(f"Initial sample error: {e}")
        
        # Bayesian optimization loop
        gp = GaussianProcessRegressor(kernel=Matern(nu=2.5), n_restarts_optimizer=5)
        
        best_score = max(y_samples) if y_samples else float('-inf')
        best_idx = y_samples.index(best_score) if y_samples else 0
        
        for i in range(n_iterations - n_initial):
            if len(X_samples) < 2:
                continue
                
            # Fit GP
            X = np.array(X_samples)
            y = np.array(y_samples)
            
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                gp.fit(X, y)
            
            # Find next point using Expected Improvement
            best_x = self._expected_improvement_search(gp, param_space, best_score)
            
            # Convert to params
            params = {}
            for j, p in enumerate(param_space):
                pass
            try:
                if p.param_type == 'categorical':
                    params[p.name] = p.values[int(best_x[j]) % len(p.values)]
                elif p.param_type == 'int':
                    params[p.name] = int(best_x[j])
                else:
                    params[p.name] = best_x[j]
            
                result = self.backtester.run(strategy_func, params)
                X_samples.append(best_x)
                y_samples.append(result.score)
                all_results.append({'params': params, 'score': result.score})
                
                if result.score > best_score:
                    best_score = result.score
                    best_idx = len(y_samples) - 1
                    
            except Exception as e:
                logger.warning(f"Bayesian iteration {i} error: {e}")
        
        best_params = all_results[best_idx]['params'] if all_results else {}
        
        return OptimizationResult(
            best_params=best_params,
            best_score=best_score,
            all_results=all_results,
            optimization_time=0,
            method='bayesian',
        )
    
    def _expected_improvement_search(self, gp, param_space: List[ParameterSpace], 
                                    best_score: float, n_samples: int = 1000) -> List[float]:
        """Find point with highest expected improvement"""
        from scipy.stats import norm
        
        best_ei = float('-inf')
        best_x = None
        
        for _ in range(n_samples):
            x = []
            for p in param_space:
                if p.param_type == 'categorical':
                    x.append(np.random.randint(len(p.values)))
                else:
                    x.append(np.random.uniform(p.min_value, p.max_value))
            
            x = np.array(x).reshape(1, -1)
            
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                mu, sigma = gp.predict(x, return_std=True)
            
            if sigma > 0:
                z = (mu - best_score) / sigma
                ei = (mu - best_score) * norm.cdf(z) + sigma * norm.pdf(z)
            else:
                ei = 0
            
            if ei > best_ei:
                best_ei = ei
                best_x = x[0].tolist()
        
        return best_x or [0] * len(param_space)
    
    def _walk_forward_optimization(self, strategy_func: Callable,
                                  param_space: List[ParameterSpace],
                                  n_windows: int = 5,
                                  train_ratio: float = 0.7) -> OptimizationResult:
        """Walk-forward optimization with out-of-sample validation"""
        n_samples = len(self.data)
        window_size = n_samples // n_windows
        
        all_results = []
        oos_results = []
        
        for i in range(n_windows):
            # Define train/test split
            start_idx = i * window_size
            end_idx = min((i + 2) * window_size, n_samples)
            
            train_end = start_idx + int((end_idx - start_idx) * train_ratio)
            
            train_data = self.data.iloc[start_idx:train_end]
            test_data = self.data.iloc[train_end:end_idx]
            
            if len(train_data) < 50 or len(test_data) < 20:
                continue
            
            # Optimize on training data
            train_backtester = StrategyBacktester(train_data, self.initial_capital)
            
            # Simple grid search for walk-forward
            param_names = [p.name for p in param_space]
            param_values = [p.get_values(n_samples=5) for p in param_space]  # Fewer samples
            combinations = list(product(*param_values))
            
            best_train_score = float('-inf')
            best_params = {}
            
            for combo in combinations[:100]:  # Limit combinations
                params = dict(zip(param_names, combo))
                try:
                    result = train_backtester.run(strategy_func, params)
                    if result.score > best_train_score:
                        best_train_score = result.score
                        best_params = params
                except Exception:
                    continue
            
            # Test on out-of-sample data
            if best_params:
                test_backtester = StrategyBacktester(test_data, self.initial_capital)
                try:
                    oos_result = test_backtester.run(strategy_func, best_params)
                    oos_results.append({
                        'window': i,
                        'params': best_params,
                        'train_score': best_train_score,
                        'oos_score': oos_result.score,
                        'oos_return': oos_result.total_return,
                        'oos_sharpe': oos_result.sharpe_ratio,
                    })
                    all_results.append({
                        'params': best_params,
                        'score': oos_result.score,
                    })
                except Exception as e:
                    logger.warning(f"OOS test error in window {i}: {e}")
        
        # Find best overall parameters
        if oos_results:
            best_oos = max(oos_results, key=lambda x: x['oos_score'])
            avg_oos_score = np.mean([r['oos_score'] for r in oos_results])
        else:
            best_oos = {'params': {}, 'oos_score': 0}
            avg_oos_score = 0
        
        return OptimizationResult(
            best_params=best_oos['params'],
            best_score=best_oos['oos_score'],
            all_results=all_results,
            optimization_time=0,
            method='walk_forward',
            validation_results={
                'n_windows': n_windows,
                'avg_oos_score': avg_oos_score,
                'window_results': oos_results,
            }
        )
    
    def monte_carlo_validation(self, strategy_func: Callable, 
                              params: Dict[str, Any],
                              n_simulations: int = 1000) -> Dict[str, Any]:
        """
        Monte Carlo validation of strategy parameters.
        
        Args:
            strategy_func: Strategy function
            params: Strategy parameters
            n_simulations: Number of simulations
            
        Returns:
            Monte Carlo results
        """
        results = []
        
        for i in range(n_simulations):
            # Shuffle returns to create synthetic data
            shuffled_returns = np.random.permutation(self.backtester.returns)
            
            # Reconstruct prices
            synthetic_prices = self.backtester.prices[0] * np.cumprod(1 + shuffled_returns)
            
            # Create synthetic data
            synthetic_data = self.data.copy()
            synthetic_data['close'] = synthetic_prices
            
            # Run backtest
            synthetic_backtester = StrategyBacktester(synthetic_data, self.initial_capital)
            try:
                result = synthetic_backtester.run(strategy_func, params)
                results.append({
                    'return': result.total_return,
                    'sharpe': result.sharpe_ratio,
                    'max_dd': result.max_drawdown,
                })
            except Exception:
                continue
        
        if not results:
            return {}
        
        returns = [r['return'] for r in results]
        sharpes = [r['sharpe'] for r in results]
        drawdowns = [r['max_dd'] for r in results]
        
        return {
            'n_simulations': len(results),
            'return_mean': np.mean(returns),
            'return_std': np.std(returns),
            'return_5th': np.percentile(returns, 5),
            'return_95th': np.percentile(returns, 95),
            'sharpe_mean': np.mean(sharpes),
            'sharpe_std': np.std(sharpes),
            'max_dd_mean': np.mean(drawdowns),
            'max_dd_worst': np.max(drawdowns),
            'prob_positive': np.mean([r > 0 for r in returns]),
        }
    
    def export_results(self, filepath: str):
        """Export optimization results to file"""
        results = {
            'timestamp': datetime.now().isoformat(),
            'data_points': len(self.data),
            'optimizations': [r.to_dict() for r in self.results_history],
        }
        
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        logger.info(f"Results exported to {filepath}")


# Example strategies for optimization
def sma_crossover_strategy(data: pd.DataFrame, fast_period: int = 10, 
                          slow_period: int = 20) -> np.ndarray:
    """Simple SMA crossover strategy"""
    fast_sma = data['close'].rolling(fast_period).mean()
    slow_sma = data['close'].rolling(slow_period).mean()
    
    signals = np.zeros(len(data))
    signals[fast_sma > slow_sma] = 1
    signals[fast_sma < slow_sma] = -1
    
    # Generate trade signals on crossover
    signal_diff = np.diff(signals, prepend=0)
    trade_signals = np.zeros(len(data))
    trade_signals[signal_diff > 0] = 1  # Buy
    trade_signals[signal_diff < 0] = -1  # Sell
    
    return trade_signals


def rsi_strategy(data: pd.DataFrame, period: int = 14, 
                oversold: int = 30, overbought: int = 70) -> np.ndarray:
    """RSI mean reversion strategy"""
    delta = data['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(period).mean()
    
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    
    signals = np.zeros(len(data))
    signals[rsi < oversold] = 1  # Buy when oversold
    signals[rsi > overbought] = -1  # Sell when overbought
    
    return signals


def momentum_strategy(data: pd.DataFrame, lookback: int = 20, 
                     threshold: float = 0.02) -> np.ndarray:
    """Momentum strategy"""
    returns = data['close'].pct_change(lookback)
    
    signals = np.zeros(len(data))
    signals[returns > threshold] = 1  # Buy on positive momentum
    signals[returns < -threshold] = -1  # Sell on negative momentum
    
    return signals


async def run_optimization_demo():
    """Run optimization demo"""
    print("\n" + "=" * 60)
    logger.info("STRATEGY OPTIMIZER DEMO")
    print("=" * 60)
    
    # Generate sample data
    np.random.seed(42)
    n_days = 500
    dates = pd.date_range('2023-01-01', periods=n_days, freq='D')
    
    # Generate realistic price data
    returns = np.random.randn(n_days) * 0.015 + 0.0003
    prices = 100 * np.exp(np.cumsum(returns))
    
    data = pd.DataFrame({
        'open': prices * (1 + np.random.randn(n_days) * 0.002),
        'high': prices * (1 + abs(np.random.randn(n_days) * 0.015)),
        'low': prices * (1 - abs(np.random.randn(n_days) * 0.015)),
        'close': prices,
        'volume': np.random.randint(100000, 1000000, n_days)
    }, index=dates)
    
    # Create optimizer
    optimizer = StrategyOptimizer(data, initial_capital=100000)
    
    # Define parameter space for SMA crossover
    param_space = [
        ParameterSpace('fast_period', 'int', 5, 20, 5),
        ParameterSpace('slow_period', 'int', 20, 50, 10),
    ]
    
    # Run grid search
    logger.info("\n[1] Running Grid Search Optimization...")
    result = optimizer.optimize(
        sma_crossover_strategy,
        param_space,
        method=OptimizationMethod.GRID_SEARCH
    )
    
    logger.info(f"\nGrid Search Results:")
    logger.info(f"  Best Parameters: {result.best_params}")
    logger.info(f"  Best Score: {result.best_score:.4f}")
    logger.info(f"  Combinations Tested: {len(result.all_results)}")
    logger.info(f"  Time: {result.optimization_time:.2f}s")
    
    # Run walk-forward optimization
    logger.info("\n[2] Running Walk-Forward Optimization...")
    wf_result = optimizer.optimize(
        sma_crossover_strategy,
        param_space,
        method=OptimizationMethod.WALK_FORWARD
    )
    
    logger.info(f"\nWalk-Forward Results:")
    logger.info(f"  Best Parameters: {wf_result.best_params}")
    logger.info(f"  Best OOS Score: {wf_result.best_score:.4f}")
    if wf_result.validation_results:
        logger.info(f"  Avg OOS Score: {wf_result.validation_results['avg_oos_score']:.4f}")
    
    # Monte Carlo validation
    logger.info("\n[3] Running Monte Carlo Validation...")
    mc_results = optimizer.monte_carlo_validation(
        sma_crossover_strategy,
        result.best_params,
        n_simulations=500
    )
    
    logger.info(f"\nMonte Carlo Results:")
    logger.info(f"  Return Mean: {mc_results['return_mean']:.2%}")
    logger.info(f"  Return Std: {mc_results['return_std']:.2%}")
    logger.info(f"  5th Percentile: {mc_results['return_5th']:.2%}")
    logger.info(f"  95th Percentile: {mc_results['return_95th']:.2%}")
    logger.info(f"  Prob Positive: {mc_results['prob_positive']:.2%}")
    
    # Export results
    optimizer.export_results('results/optimization_results.json')
    
    print("\n" + "=" * 60)
    logger.info("OPTIMIZATION COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(run_optimization_demo())
