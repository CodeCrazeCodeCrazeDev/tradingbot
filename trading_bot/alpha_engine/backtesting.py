"""
from typing import Callable, Dict, Optional, Set, Tuple
Advanced Backtesting Module
============================

Comprehensive backtesting with:
- Walk-forward optimization
- Monte Carlo simulation
- Stress testing
- Robustness analysis
"""

import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Optional, Tuple, Any, Callable, Generator
from collections import deque
import logging
from datetime import datetime, timedelta
from abc import ABC, abstractmethod
import random
import copy

logger = logging.getLogger(__name__)


class BacktestMode(Enum):
    """Backtesting modes"""
    SIMPLE = "simple"
    WALK_FORWARD = "walk_forward"
    MONTE_CARLO = "monte_carlo"
    STRESS_TEST = "stress_test"


@dataclass
class BacktestConfig:
    """Backtesting configuration"""
    start_date: datetime
    end_date: datetime
    initial_capital: float = 100000
    commission: float = 0.001  # 0.1%
    slippage: float = 0.0005  # 0.05%
    margin_requirement: float = 0.1
    max_position_size: float = 0.1  # 10% of capital
    
    # Walk-forward settings
    train_period_days: int = 252  # 1 year
    test_period_days: int = 63  # 3 months
    
    # Monte Carlo settings
    num_simulations: int = 1000
    
    # Stress test scenarios
    stress_scenarios: List[str] = field(default_factory=lambda: [
        'flash_crash', 'fed_surprise', 'liquidity_crisis', 'volatility_spike'
    ])


@dataclass
class BacktestResult:
    """Backtesting results"""
    config: BacktestConfig
    
    # Performance
    total_return: float
    annualized_return: float
    sharpe_ratio: float
    sortino_ratio: float
    max_drawdown: float
    calmar_ratio: float
    
    # Trade statistics
    total_trades: int
    win_rate: float
    profit_factor: float
    avg_trade_return: float
    
    # Risk metrics
    var_95: float
    var_99: float
    cvar_95: float
    
    # Equity curve
    equity_curve: pd.Series
    
    # Trade log
    trades: List[Dict[str, Any]]
    
    # Additional metrics
    metrics: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WalkForwardResult:
    """Walk-forward optimization results"""
    periods: List[Dict[str, Any]]
    overall_return: float
    overall_sharpe: float
    consistency_score: float  # % of periods profitable
    parameter_stability: float  # How stable are optimal parameters


@dataclass
class MonteCarloResult:
    """Monte Carlo simulation results"""
    num_simulations: int
    mean_return: float
    std_return: float
    percentile_5: float
    percentile_25: float
    percentile_50: float
    percentile_75: float
    percentile_95: float
    probability_profit: float
    probability_drawdown_20: float
    worst_case_return: float
    best_case_return: float


@dataclass
class StressTestResult:
    """Stress test results"""
    scenario: str
    return_impact: float
    max_drawdown: float
    recovery_days: int
    positions_liquidated: int
    margin_calls: int


class AdvancedBacktester:
    """
    Advanced backtesting engine
    """
    
    def __init__(self, config: BacktestConfig = None):
        try:
            self.config = config or BacktestConfig(
                start_date=datetime.now() - timedelta(days=365),
                end_date=datetime.now()
            )
        
            # State
            self.equity = self.config.initial_capital
            self.peak_equity = self.equity
            self.positions: Dict[str, Dict[str, Any]] = {}
            self.trades: List[Dict[str, Any]] = []
            self.equity_curve: List[Tuple[datetime, float]] = []
        
            # Strategy to test
            self.strategy: Optional[Callable] = None
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def set_strategy(self, strategy: Callable):
        """Set strategy function to backtest"""
        try:
            self.strategy = strategy
        except Exception as e:
            logger.error(f"Error in set_strategy: {e}")
            raise
    
    def run(self, data: pd.DataFrame, mode: BacktestMode = BacktestMode.SIMPLE) -> BacktestResult:
        """
        Run backtest
        
        Args:
            data: OHLCV DataFrame with datetime index
            mode: Backtesting mode
            
        Returns:
            BacktestResult
        """
        try:
            if self.strategy is None:
                raise ValueError("Strategy not set. Call set_strategy() first.")
        
            # Reset state
            self._reset()
        
            # Filter data by date range
            data = data[(data.index >= self.config.start_date) & 
                       (data.index <= self.config.end_date)]
        
            if mode == BacktestMode.SIMPLE:
                return self._run_simple(data)
            elif mode == BacktestMode.WALK_FORWARD:
                return self._run_walk_forward(data)
            else:
                return self._run_simple(data)
        except Exception as e:
            logger.error(f"Error in run: {e}")
            raise
    
    def _reset(self):
        """Reset backtest state"""
        try:
            self.equity = self.config.initial_capital
            self.peak_equity = self.equity
            self.positions = {}
            self.trades = []
            self.equity_curve = []
        except Exception as e:
            logger.error(f"Error in _reset: {e}")
            raise
    
    def _run_simple(self, data: pd.DataFrame) -> BacktestResult:
        """Run simple backtest"""
        try:
            for timestamp, row in data.iterrows():
                # Update positions
                self._update_positions(row)
            
                # Generate signal
                signal = self.strategy(data.loc[:timestamp])
            
                # Execute signal
                if signal:
                    self._execute_signal(signal, row, timestamp)
            
                # Record equity
                self.equity_curve.append((timestamp, self.equity))
        
            # Close remaining positions
            if data.shape[0] > 0:
                last_row = data.iloc[-1]
                self._close_all_positions(last_row, data.index[-1])
        
            return self._calculate_results()
        except Exception as e:
            logger.error(f"Error in _run_simple: {e}")
            raise
    
    def _run_walk_forward(self, data: pd.DataFrame) -> BacktestResult:
        """Run walk-forward optimization"""
        try:
            results = []
        
            train_days = self.config.train_period_days
            test_days = self.config.test_period_days
        
            start_idx = 0
        
            while start_idx + train_days + test_days <= len(data):
                # Split data
                train_end = start_idx + train_days
                test_end = train_end + test_days
            
                train_data = data.iloc[start_idx:train_end]
                test_data = data.iloc[train_end:test_end]
            
                # Optimize on training data (simplified - just run strategy)
                self._reset()
                for timestamp, row in train_data.iterrows():
                    self._update_positions(row)
                    signal = self.strategy(train_data.loc[:timestamp])
                    if signal:
                        self._execute_signal(signal, row, timestamp)
            
                # Test on out-of-sample data
                self._reset()
                for timestamp, row in test_data.iterrows():
                    self._update_positions(row)
                    signal = self.strategy(test_data.loc[:timestamp])
                    if signal:
                        self._execute_signal(signal, row, timestamp)
                    self.equity_curve.append((timestamp, self.equity))
            
                # Record period result
                period_return = (self.equity - self.config.initial_capital) / self.config.initial_capital
                results.append({
                    'start': test_data.index[0],
                    'end': test_data.index[-1],
                    'return': period_return,
                    'trades': len(self.trades),
                })
            
                start_idx += test_days
        
            return self._calculate_results()
        except Exception as e:
            logger.error(f"Error in _run_walk_forward: {e}")
            raise
    
    def _update_positions(self, row: pd.Series):
        """Update position P&L"""
        try:
            for symbol, position in self.positions.items():
                if 'close' in row:
                    current_price = row['close']
                    entry_price = position['entry_price']
                    size = position['size']
                
                    if position['direction'] == 'long':
                        pnl = (current_price - entry_price) * size
                    else:
                        pnl = (entry_price - current_price) * size
                
                    position['unrealized_pnl'] = pnl
        except Exception as e:
            logger.error(f"Error in _update_positions: {e}")
            raise
    
    def _execute_signal(self, signal: Dict[str, Any], row: pd.Series, timestamp: datetime):
        """Execute trading signal"""
        try:
            symbol = signal.get('symbol', 'default')
            direction = signal.get('direction')
            size = signal.get('size', 0)
        
            if direction == 'neutral' or size == 0:
                return
        
            price = row.get('close', row.get('price', 0))
        
            # Apply slippage
            if direction == 'long':
                execution_price = price * (1 + self.config.slippage)
            else:
                execution_price = price * (1 - self.config.slippage)
        
            # Check if we have existing position
            if symbol in self.positions:
                existing = self.positions[symbol]
            
                # Close existing if opposite direction
                if existing['direction'] != direction:
                    self._close_position(symbol, price, timestamp)
        
            # Open new position
            if direction in ['long', 'short']:
                # Calculate position size
                max_size = self.equity * self.config.max_position_size / price
                actual_size = min(size, max_size)
            
                # Commission
                commission = actual_size * execution_price * self.config.commission
                self.equity -= commission
            
                self.positions[symbol] = {
                    'direction': direction,
                    'entry_price': execution_price,
                    'size': actual_size,
                    'entry_time': timestamp,
                    'unrealized_pnl': 0,
                }
        except Exception as e:
            logger.error(f"Error in _execute_signal: {e}")
            raise
    
    def _close_position(self, symbol: str, price: float, timestamp: datetime):
        """Close a position"""
        try:
            if symbol not in self.positions:
                return
        
            position = self.positions[symbol]
        
            # Apply slippage
            if position['direction'] == 'long':
                execution_price = price * (1 - self.config.slippage)
            else:
                execution_price = price * (1 + self.config.slippage)
        
            # Calculate P&L
            if position['direction'] == 'long':
                pnl = (execution_price - position['entry_price']) * position['size']
            else:
                pnl = (position['entry_price'] - execution_price) * position['size']
        
            # Commission
            commission = position['size'] * execution_price * self.config.commission
            pnl -= commission
        
            # Update equity
            self.equity += pnl
            if self.equity > self.peak_equity:
                self.peak_equity = self.equity
        
            # Record trade
            self.trades.append({
                'symbol': symbol,
                'direction': position['direction'],
                'entry_price': position['entry_price'],
                'exit_price': execution_price,
                'size': position['size'],
                'entry_time': position['entry_time'],
                'exit_time': timestamp,
                'pnl': pnl,
                'return': pnl / (position['entry_price'] * position['size']),
            })
        
            del self.positions[symbol]
        except Exception as e:
            logger.error(f"Error in _close_position: {e}")
            raise
    
    def _close_all_positions(self, row: pd.Series, timestamp: datetime):
        """Close all open positions"""
        try:
            price = row.get('close', row.get('price', 0))
            for symbol in list(self.positions.keys()):
                self._close_position(symbol, price, timestamp)
        except Exception as e:
            logger.error(f"Error in _close_all_positions: {e}")
            raise
    
    def _calculate_results(self) -> BacktestResult:
        """Calculate backtest results"""
        try:
            if not self.equity_curve:
                return self._empty_result()
        
            # Equity curve
            equity_series = pd.Series(
                [e[1] for e in self.equity_curve],
                index=[e[0] for e in self.equity_curve]
            )
        
            # Returns
            total_return = (self.equity - self.config.initial_capital) / self.config.initial_capital
        
            days = (self.equity_curve[-1][0] - self.equity_curve[0][0]).days
            annualized_return = (1 + total_return) ** (365 / max(days, 1)) - 1
        
            # Daily returns
            daily_returns = equity_series.pct_change().dropna()
        
            # Sharpe ratio
            if len(daily_returns) > 1:
                sharpe = np.mean(daily_returns) / (np.std(daily_returns) + 1e-10) * np.sqrt(252)
            else:
                sharpe = 0
        
            # Sortino ratio
            downside_returns = daily_returns[daily_returns < 0]
            if len(downside_returns) > 0:
                sortino = np.mean(daily_returns) / (np.std(downside_returns) + 1e-10) * np.sqrt(252)
            else:
                sortino = sharpe
        
            # Max drawdown
            running_max = equity_series.cummax()
            drawdown = (running_max - equity_series) / running_max
            max_drawdown = drawdown.max()
        
            # Calmar ratio
            calmar = annualized_return / max_drawdown if max_drawdown > 0 else 0
        
            # Trade statistics
            if self.trades:
                pnls = [t['pnl'] for t in self.trades]
                wins = [p for p in pnls if p > 0]
                losses = [p for p in pnls if p < 0]
            
                win_rate = len(wins) / len(pnls)
                profit_factor = sum(wins) / abs(sum(losses)) if losses else float('inf')
                avg_trade_return = np.mean([t['return'] for t in self.trades])
            else:
                win_rate = 0
                profit_factor = 0
                avg_trade_return = 0
        
            # VaR
            if len(daily_returns) > 20:
                var_95 = np.percentile(daily_returns, 5)
                var_99 = np.percentile(daily_returns, 1)
                cvar_95 = daily_returns[daily_returns <= var_95].mean()
            else:
                var_95 = var_99 = cvar_95 = 0
        
            return BacktestResult(
                config=self.config,
                total_return=total_return,
                annualized_return=annualized_return,
                sharpe_ratio=sharpe,
                sortino_ratio=sortino,
                max_drawdown=max_drawdown,
                calmar_ratio=calmar,
                total_trades=len(self.trades),
                win_rate=win_rate,
                profit_factor=profit_factor,
                avg_trade_return=avg_trade_return,
                var_95=var_95,
                var_99=var_99,
                cvar_95=cvar_95,
                equity_curve=equity_series,
                trades=self.trades,
            )
        except Exception as e:
            logger.error(f"Error in _calculate_results: {e}")
            raise
    
    def _empty_result(self) -> BacktestResult:
        """Return empty result"""
        return BacktestResult(
            config=self.config,
            total_return=0, annualized_return=0, sharpe_ratio=0, sortino_ratio=0,
            max_drawdown=0, calmar_ratio=0, total_trades=0, win_rate=0,
            profit_factor=0, avg_trade_return=0, var_95=0, var_99=0, cvar_95=0,
            equity_curve=pd.Series(), trades=[],
        )


class WalkForwardOptimizer:
    """
    Walk-forward optimization
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        try:
            self.config = config or {}
            self.train_ratio = self.config.get('train_ratio', 0.8)
            self.num_folds = self.config.get('num_folds', 5)
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def optimize(self, data: pd.DataFrame, strategy_factory: Callable,
                param_grid: Dict[str, List[Any]]) -> WalkForwardResult:
        """
        Run walk-forward optimization
        
        Args:
            data: OHLCV DataFrame
            strategy_factory: Function that creates strategy given parameters
            param_grid: Parameter grid to search
            
        Returns:
            WalkForwardResult
        """
        try:
            fold_size = len(data) // self.num_folds
            results = []
            optimal_params_history = []
        
            for fold in range(self.num_folds - 1):
                # Split data
                train_start = fold * fold_size
                train_end = train_start + int(fold_size * self.train_ratio)
                test_end = (fold + 1) * fold_size
            
                train_data = data.iloc[train_start:train_end]
                test_data = data.iloc[train_end:test_end]
            
                # Find optimal parameters on training data
                best_params, best_sharpe = self._grid_search(train_data, strategy_factory, param_grid)
                optimal_params_history.append(best_params)
            
                # Test on out-of-sample data
                strategy = strategy_factory(**best_params)
                backtester = AdvancedBacktester(BacktestConfig(
                    start_date=test_data.index[0],
                    end_date=test_data.index[-1],
                ))
                backtester.set_strategy(strategy)
                result = backtester.run(test_data)
            
                results.append({
                    'fold': fold,
                    'train_sharpe': best_sharpe,
                    'test_sharpe': result.sharpe_ratio,
                    'test_return': result.total_return,
                    'optimal_params': best_params,
                })
        
            # Calculate overall metrics
            overall_return = np.mean([r['test_return'] for r in results])
            overall_sharpe = np.mean([r['test_sharpe'] for r in results])
            consistency = sum(1 for r in results if r['test_return'] > 0) / len(results)
        
            # Parameter stability
            param_stability = self._calculate_param_stability(optimal_params_history)
        
            return WalkForwardResult(
                periods=results,
                overall_return=overall_return,
                overall_sharpe=overall_sharpe,
                consistency_score=consistency,
                parameter_stability=param_stability,
            )
        except Exception as e:
            logger.error(f"Error in optimize: {e}")
            raise
    
    def _grid_search(self, data: pd.DataFrame, strategy_factory: Callable,
                    param_grid: Dict[str, List[Any]]) -> Tuple[Dict[str, Any], float]:
        """Simple grid search for optimal parameters"""
        try:
            best_params = {}
            best_sharpe = -np.inf
        
            # Generate all parameter combinations
            param_names = list(param_grid.keys())
            param_values = list(param_grid.values())
        
            from itertools import product
            for values in product(*param_values):
                params = dict(zip(param_names, values))
            
                # Create strategy and backtest
                strategy = strategy_factory(**params)
                backtester = AdvancedBacktester(BacktestConfig(
                    start_date=data.index[0],
                    end_date=data.index[-1],
                ))
                backtester.set_strategy(strategy)
                result = backtester.run(data)
            
                if result.sharpe_ratio > best_sharpe:
                    best_sharpe = result.sharpe_ratio
                    best_params = params
        
            return best_params, best_sharpe
        except Exception as e:
            logger.error(f"Error in _grid_search: {e}")
            raise
    
    def _calculate_param_stability(self, params_history: List[Dict[str, Any]]) -> float:
        """Calculate parameter stability across folds"""
        try:
            if len(params_history) < 2:
                return 1.0
        
            # For each parameter, calculate coefficient of variation
            param_names = params_history[0].keys()
            cvs = []
        
            for param in param_names:
                values = [p[param] for p in params_history if isinstance(p[param], (int, float))]
                if values:
                    cv = np.std(values) / (np.mean(values) + 1e-10)
                    cvs.append(cv)
        
            # Stability = 1 - average CV
            return max(0, 1 - np.mean(cvs)) if cvs else 1.0
        except Exception as e:
            logger.error(f"Error in _calculate_param_stability: {e}")
            raise


class MonteCarloSimulator:
    """
    Monte Carlo simulation for robustness testing
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        try:
            self.config = config or {}
            self.num_simulations = self.config.get('num_simulations', 1000)
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def simulate(self, trades: List[Dict[str, Any]], 
                initial_capital: float = 100000) -> MonteCarloResult:
        """
        Run Monte Carlo simulation on trade results
        
        Args:
            trades: List of historical trades
            initial_capital: Starting capital
            
        Returns:
            MonteCarloResult
        """
        try:
            if not trades:
                return self._empty_result()
        
            # Extract returns
            returns = [t.get('return', 0) for t in trades]
        
            # Run simulations
            final_returns = []
            max_drawdowns = []
        
            for _ in range(self.num_simulations):
                # Shuffle trades
                shuffled = random.sample(returns, len(returns))
            
                # Calculate equity curve
                equity = initial_capital
                peak = equity
                max_dd = 0
            
                for ret in shuffled:
                    equity *= (1 + ret)
                    if equity > peak:
                        peak = equity
                    dd = (peak - equity) / peak
                    max_dd = max(max_dd, dd)
            
                final_return = (equity - initial_capital) / initial_capital
                final_returns.append(final_return)
                max_drawdowns.append(max_dd)
        
            return MonteCarloResult(
                num_simulations=self.num_simulations,
                mean_return=np.mean(final_returns),
                std_return=np.std(final_returns),
                percentile_5=np.percentile(final_returns, 5),
                percentile_25=np.percentile(final_returns, 25),
                percentile_50=np.percentile(final_returns, 50),
                percentile_75=np.percentile(final_returns, 75),
                percentile_95=np.percentile(final_returns, 95),
                probability_profit=sum(1 for r in final_returns if r > 0) / len(final_returns),
                probability_drawdown_20=sum(1 for d in max_drawdowns if d > 0.2) / len(max_drawdowns),
                worst_case_return=min(final_returns),
                best_case_return=max(final_returns),
            )
        except Exception as e:
            logger.error(f"Error in simulate: {e}")
            raise
    
    def _empty_result(self) -> MonteCarloResult:
        """Return empty result"""
        return MonteCarloResult(
            num_simulations=0, mean_return=0, std_return=0,
            percentile_5=0, percentile_25=0, percentile_50=0,
            percentile_75=0, percentile_95=0,
            probability_profit=0, probability_drawdown_20=0,
            worst_case_return=0, best_case_return=0,
        )


class StressTestEngine:
    """
    Stress testing engine
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        try:
            self.config = config or {}
        
            # Stress scenarios
            self.scenarios = {
                'flash_crash': {
                    'description': '10% drop in minutes',
                    'price_shock': -0.10,
                    'volatility_multiplier': 5.0,
                    'liquidity_reduction': 0.8,
                },
                'fed_surprise': {
                    'description': 'Unexpected rate hike',
                    'price_shock': -0.05,
                    'volatility_multiplier': 3.0,
                    'liquidity_reduction': 0.3,
                },
                'liquidity_crisis': {
                    'description': 'Market liquidity evaporates',
                    'price_shock': -0.03,
                    'volatility_multiplier': 2.0,
                    'liquidity_reduction': 0.9,
                },
                'volatility_spike': {
                    'description': 'VIX spikes 100%',
                    'price_shock': -0.02,
                    'volatility_multiplier': 4.0,
                    'liquidity_reduction': 0.5,
                },
                'overnight_gap': {
                    'description': 'Large overnight gap',
                    'price_shock': -0.08,
                    'volatility_multiplier': 2.0,
                    'liquidity_reduction': 0.4,
                },
            }
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def run_stress_test(self, portfolio: Dict[str, Dict[str, Any]],
                       scenario_name: str) -> StressTestResult:
        """
        Run stress test on portfolio
        
        Args:
            portfolio: Dictionary of positions
            scenario_name: Name of stress scenario
            
        Returns:
            StressTestResult
        """
        try:
            if scenario_name not in self.scenarios:
                raise ValueError(f"Unknown scenario: {scenario_name}")
        
            scenario = self.scenarios[scenario_name]
        
            # Calculate impact
            total_value = sum(p.get('value', 0) for p in portfolio.values())
        
            # Price shock impact
            price_impact = total_value * scenario['price_shock']
        
            # Additional volatility impact
            vol_impact = total_value * 0.01 * scenario['volatility_multiplier']
        
            total_impact = price_impact - vol_impact
            return_impact = total_impact / total_value if total_value > 0 else 0
        
            # Max drawdown during stress
            max_drawdown = abs(return_impact) * 1.5  # Assume 50% worse during stress
        
            # Recovery estimate (simplified)
            recovery_days = int(abs(return_impact) * 100 * 5)  # 5 days per 1% loss
        
            # Positions that would be liquidated
            liquidated = sum(1 for p in portfolio.values() 
                            if p.get('value', 0) * (1 + scenario['price_shock']) < p.get('margin', 0))
        
            # Margin calls
            margin_calls = sum(1 for p in portfolio.values()
                             if p.get('value', 0) * (1 + scenario['price_shock']) < p.get('margin', 0) * 1.5)
        
            return StressTestResult(
                scenario=scenario_name,
                return_impact=return_impact,
                max_drawdown=max_drawdown,
                recovery_days=recovery_days,
                positions_liquidated=liquidated,
                margin_calls=margin_calls,
            )
        except Exception as e:
            logger.error(f"Error in run_stress_test: {e}")
            raise
    
    def run_all_scenarios(self, portfolio: Dict[str, Dict[str, Any]]) -> List[StressTestResult]:
        """Run all stress scenarios"""
        try:
            results = []
            for scenario_name in self.scenarios.keys():
                result = self.run_stress_test(portfolio, scenario_name)
                results.append(result)
            return results
        except Exception as e:
            logger.error(f"Error in run_all_scenarios: {e}")
            raise
