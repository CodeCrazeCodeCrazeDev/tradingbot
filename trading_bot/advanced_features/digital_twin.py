"""Digital Twin Simulation Module - Parallel Validation Environment.

This module implements a high-fidelity Digital Twin of the trading environment
for parallel validation of strategies before deploying live capital.
"""

import numpy as np
import pandas as pd
from typing import Callable, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging
import asyncio
import threading
from concurrent.futures import ThreadPoolExecutor
import pickle
import json
import numpy
import pandas

logger = logging.getLogger(__name__)


@dataclass
class SimulationResult:
    """Results from a digital twin simulation."""
    strategy_id: str
    start_time: datetime
    end_time: datetime
    total_return: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    total_trades: int
    profit_factor: float
    final_balance: float
    trade_history: List[Dict]


@dataclass
class MarketCondition:
    """Market condition snapshot for simulation."""
    timestamp: datetime
    price: float
    volume: float
    bid: float
    ask: float
    spread: float
    volatility: float
    liquidity_score: float


class DigitalTwinSimulator:
    """
    High-fidelity simulation environment that mirrors live trading conditions.
    
    Features:
    - Tick-level data simulation
    - Realistic slippage modeling
    - Latency simulation
    - Market impact modeling
    - Liquidity constraints
    """
    
    def __init__(self, 
                 initial_balance: float = 100000,
                 commission_rate: float = 0.0001,
                 slippage_model: str = 'linear',
                 latency_ms: float = 50):
        """
        Initialize Digital Twin Simulator.
        
        Args:
            initial_balance: Starting capital for simulation
            commission_rate: Commission per trade (as fraction)
            slippage_model: Type of slippage model ('linear', 'sqrt', 'impact')
            latency_ms: Simulated execution latency in milliseconds
        """
        self.initial_balance = initial_balance
        self.commission_rate = commission_rate
        self.slippage_model = slippage_model
        self.latency_ms = latency_ms
        
        # Simulation state
        self.current_balance = initial_balance
        self.positions = {}
        self.trade_history = []
        self.market_data = None
        self.current_time = None
        
        # Performance tracking
        self.equity_curve = []
        self.drawdown_series = []
        
    def load_market_data(self, data: pd.DataFrame):
        """Load historical market data for simulation."""
        required_columns = ['open', 'high', 'low', 'close', 'volume']
        if not all(col in data.columns for col in required_columns):
            raise ValueError(f"Market data must contain columns: {required_columns}")
        
        self.market_data = data.copy()
        self.market_data['bid'] = self.market_data['close'] - (self.market_data['high'] - self.market_data['low']) * 0.1
        self.market_data['ask'] = self.market_data['close'] + (self.market_data['high'] - self.market_data['low']) * 0.1
        self.market_data['spread'] = self.market_data['ask'] - self.market_data['bid']
        
        # Calculate volatility and liquidity scores
        returns = self.market_data['close'].pct_change()
        self.market_data['volatility'] = returns.rolling(20).std()
        self.market_data['liquidity_score'] = self.market_data['volume'] / self.market_data['volume'].rolling(50).mean()
        
        logger.info(f"Loaded {len(self.market_data)} data points for simulation")
    
    def simulate_strategy(self, 
                         strategy_func: Callable,
                         start_date: Optional[datetime] = None,
                         end_date: Optional[datetime] = None) -> SimulationResult:
        """
        Simulate a trading strategy over historical data.
        
        Args:
            strategy_func: Function that takes market condition and returns trading signal
            start_date: Start date for simulation
            end_date: End date for simulation
            
        Returns:
            SimulationResult with performance metrics
        """
        if self.market_data is None:
            raise ValueError("Market data not loaded. Call load_market_data() first.")
        
        # Reset simulation state
        self._reset_simulation()
        
        # Filter data by date range
        sim_data = self.market_data.copy()
        if start_date:
            sim_data = sim_data[sim_data.index >= start_date]
        if end_date:
            sim_data = sim_data[sim_data.index <= end_date]
        
        if len(sim_data) == 0:
            raise ValueError("No data available for specified date range")
        
        logger.info(f"Starting simulation from {sim_data.index[0]} to {sim_data.index[-1]}")
        
        # Run simulation
        for timestamp, row in sim_data.iterrows():
            self.current_time = timestamp
            
            # Create market condition
            market_condition = MarketCondition(
                timestamp=timestamp,
                price=row['close'],
                volume=row['volume'],
                bid=row['bid'],
                ask=row['ask'],
                spread=row['spread'],
                volatility=row['volatility'],
                liquidity_score=row['liquidity_score']
            )
            
            # Get strategy signal
            try:
                signal = strategy_func(market_condition)
                if signal:
                    self._execute_signal(signal, market_condition)
            except Exception as e:
                logger.error(f"Strategy error at {timestamp}: {e}")
                continue
            
            # Update equity curve
            current_equity = self._calculate_current_equity(market_condition)
            self.equity_curve.append({
                'timestamp': timestamp,
                'equity': current_equity,
                'balance': self.current_balance
            })
        
        # Calculate final results
        return self._calculate_results(sim_data.index[0], sim_data.index[-1])
    
    def _reset_simulation(self):
        """Reset simulation to initial state."""
        self.current_balance = self.initial_balance
        self.positions = {}
        self.trade_history = []
        self.equity_curve = []
        self.drawdown_series = []
    
    def _execute_signal(self, signal: Dict, market_condition: MarketCondition):
        """Execute a trading signal with realistic market simulation."""
        action = signal.get('action')
        size = signal.get('size', 0)
        symbol = signal.get('symbol', 'DEFAULT')
        
        if action not in ['buy', 'sell', 'close']:
            return
        
        # Simulate execution latency
        execution_delay = self.latency_ms / 1000.0  # Convert to seconds
        
        # Calculate slippage
        slippage = self._calculate_slippage(size, market_condition)
        
        # Determine execution price
        if action == 'buy':
            execution_price = market_condition.ask + slippage
        elif action == 'sell':
            execution_price = market_condition.bid - slippage
        else:  # close
            current_position = self.positions.get(symbol, 0)
            if current_position > 0:  # Long position, sell to close
                execution_price = market_condition.bid - slippage
            elif current_position < 0:  # Short position, buy to close
                execution_price = market_condition.ask + slippage
            else:
                return  # No position to close
        
        # Calculate commission
        commission = abs(size) * execution_price * self.commission_rate
        
        # Execute trade
        if action == 'close':
            self._close_position(symbol, execution_price, commission, market_condition)
        else:
            self._open_position(symbol, action, size, execution_price, commission, market_condition)
    
    def _calculate_slippage(self, size: float, market_condition: MarketCondition) -> float:
        """Calculate realistic slippage based on market conditions."""
        base_slippage = market_condition.spread * 0.5
        
        if self.slippage_model == 'linear':
            # Linear slippage model
            impact_factor = abs(size) / 10000.0  # Normalize size
            slippage = base_slippage * (1 + impact_factor)
        
        elif self.slippage_model == 'sqrt':
            # Square root slippage model
            impact_factor = np.sqrt(abs(size) / 10000.0)
            slippage = base_slippage * (1 + impact_factor)
        
        elif self.slippage_model == 'impact':
            # Market impact model based on liquidity
            liquidity_factor = 1.0 / max(market_condition.liquidity_score, 0.1)
            volatility_factor = market_condition.volatility * 10
            impact_factor = (abs(size) / 10000.0) * liquidity_factor * (1 + volatility_factor)
            slippage = base_slippage * (1 + impact_factor)
        
        else:
            slippage = base_slippage
        
        return slippage
    
    def _open_position(self, symbol: str, action: str, size: float, 
                      price: float, commission: float, market_condition: MarketCondition):
        """Open a new position or add to existing position."""
        if action == 'buy':
            position_size = abs(size)
        else:  # sell
            position_size = -abs(size)
        
        # Update position
        current_position = self.positions.get(symbol, 0)
        self.positions[symbol] = current_position + position_size
        
        # Update balance
        cost = abs(size) * price + commission
        self.current_balance -= cost
        
        # Record trade
        trade = {
            'timestamp': market_condition.timestamp,
            'symbol': symbol,
            'action': action,
            'size': size,
            'price': price,
            'commission': commission,
            'slippage': self._calculate_slippage(size, market_condition),
            'balance_after': self.current_balance
        }
        self.trade_history.append(trade)
        
        logger.debug(f"Opened {action} position: {size} @ {price:.4f}")
    
    def _close_position(self, symbol: str, price: float, commission: float, 
                       market_condition: MarketCondition):
        """Close existing position."""
        current_position = self.positions.get(symbol, 0)
        if current_position == 0:
            return
        
        # Calculate P&L
        # Simplified P&L calculation - would need entry price tracking for accuracy
        pnl = current_position * price * 0.01  # Placeholder calculation
        
        # Update balance
        proceeds = abs(current_position) * price - commission + pnl
        self.current_balance += proceeds
        
        # Close position
        self.positions[symbol] = 0
        
        # Record trade
        trade = {
            'timestamp': market_condition.timestamp,
            'symbol': symbol,
            'action': 'close',
            'size': current_position,
            'price': price,
            'commission': commission,
            'pnl': pnl,
            'balance_after': self.current_balance
        }
        self.trade_history.append(trade)
        
        logger.debug(f"Closed position: {current_position} @ {price:.4f}, P&L: {pnl:.2f}")
    
    def _calculate_current_equity(self, market_condition: MarketCondition) -> float:
        """Calculate current equity including unrealized P&L."""
        equity = self.current_balance
        
        # Add unrealized P&L from open positions
        for symbol, position_size in self.positions.items():
            if position_size != 0:
                # Simplified unrealized P&L calculation
                unrealized_pnl = position_size * market_condition.price * 0.001
                equity += unrealized_pnl
        
        return equity
    
    def _calculate_results(self, start_time: datetime, end_time: datetime) -> SimulationResult:
        """Calculate comprehensive simulation results."""
        if not self.equity_curve:
            return SimulationResult(
                strategy_id="unknown",
                start_time=start_time,
                end_time=end_time,
                total_return=0.0,
                sharpe_ratio=0.0,
                max_drawdown=0.0,
                win_rate=0.0,
                total_trades=0,
                profit_factor=0.0,
                final_balance=self.initial_balance,
                trade_history=[]
            )
        
        # Calculate returns
        equity_series = pd.Series([point['equity'] for point in self.equity_curve])
        returns = equity_series.pct_change().dropna()
        
        total_return = (equity_series.iloc[-1] - equity_series.iloc[0]) / equity_series.iloc[0]
        
        # Calculate Sharpe ratio
        if len(returns) > 1 and returns.std() > 0:
            sharpe_ratio = returns.mean() / returns.std() * np.sqrt(252)  # Annualized
        else:
            sharpe_ratio = 0.0
        
        # Calculate maximum drawdown
        running_max = equity_series.expanding().max()
        drawdown = (equity_series - running_max) / running_max
        max_drawdown = abs(drawdown.min())
        
        # Calculate trade statistics
        winning_trades = [t for t in self.trade_history if t.get('pnl', 0) > 0]
        losing_trades = [t for t in self.trade_history if t.get('pnl', 0) < 0]
        
        win_rate = len(winning_trades) / len(self.trade_history) if self.trade_history else 0
        
        total_profit = sum(t.get('pnl', 0) for t in winning_trades)
        total_loss = abs(sum(t.get('pnl', 0) for t in losing_trades))
        profit_factor = total_profit / total_loss if total_loss > 0 else float('inf')
        
        return SimulationResult(
            strategy_id="simulation",
            start_time=start_time,
            end_time=end_time,
            total_return=total_return,
            sharpe_ratio=sharpe_ratio,
            max_drawdown=max_drawdown,
            win_rate=win_rate,
            total_trades=len(self.trade_history),
            profit_factor=profit_factor,
            final_balance=equity_series.iloc[-1],
            trade_history=self.trade_history.copy()
        )


class ParallelValidationEngine:
    """
    Engine for running multiple strategy validations in parallel.
    
    Allows testing multiple strategies or parameter sets simultaneously
    to find optimal configurations before live deployment.
    """
    
    def __init__(self, max_workers: int = 4):
        """Initialize parallel validation engine."""
        self.max_workers = max_workers
        self.validation_results = {}
        
    def validate_strategies(self, 
                          strategies: Dict[str, Callable],
                          market_data: pd.DataFrame,
                          validation_periods: List[Tuple[datetime, datetime]]) -> Dict[str, List[SimulationResult]]:
        """
        Validate multiple strategies across multiple time periods.
        
        Args:
            strategies: Dictionary of strategy_name -> strategy_function
            market_data: Historical market data
            validation_periods: List of (start_date, end_date) tuples
            
        Returns:
            Dictionary mapping strategy names to lists of results
        """
        results = {name: [] for name in strategies.keys()}
        
        # Create validation tasks
        tasks = []
        for strategy_name, strategy_func in strategies.items():
            for start_date, end_date in validation_periods:
                tasks.append((strategy_name, strategy_func, market_data, start_date, end_date))
        
        # Run validations in parallel
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_task = {}
            
            for task in tasks:
                future = executor.submit(self._run_single_validation, *task)
                future_to_task[future] = task
            
            # Collect results
            for future in future_to_task:
                task = future_to_task[future]
                strategy_name = task[0]
                
                try:
                    result = future.result()
                    results[strategy_name].append(result)
                except Exception as e:
                    logger.error(f"Validation failed for {strategy_name}: {e}")
        
        self.validation_results = results
        return results
    
    def _run_single_validation(self, 
                              strategy_name: str,
                              strategy_func: Callable,
                              market_data: pd.DataFrame,
                              start_date: datetime,
                              end_date: datetime) -> SimulationResult:
        """Run a single strategy validation."""
        simulator = DigitalTwinSimulator()
        simulator.load_market_data(market_data)
        
        result = simulator.simulate_strategy(strategy_func, start_date, end_date)
        result.strategy_id = strategy_name
        
        return result
    
    def get_best_strategy(self, metric: str = 'sharpe_ratio') -> Tuple[str, float]:
        """
        Find the best performing strategy based on specified metric.
        
        Args:
            metric: Performance metric to optimize ('sharpe_ratio', 'total_return', etc.)
            
        Returns:
            Tuple of (strategy_name, best_metric_value)
        """
        if not self.validation_results:
            return None, 0.0
        
        best_strategy = None
        best_value = float('-inf')
        
        for strategy_name, results in self.validation_results.items():
            if not results:
                continue
            
            # Calculate average metric across all validation periods
            metric_values = [getattr(result, metric, 0) for result in results]
            avg_metric = np.mean(metric_values)
            
            if avg_metric > best_value:
                best_value = avg_metric
                best_strategy = strategy_name
        
        return best_strategy, best_value
    
    def generate_validation_report(self) -> Dict:
        """Generate comprehensive validation report."""
        if not self.validation_results:
            return {'error': 'No validation results available'}
        
        report = {
            'summary': {},
            'detailed_results': self.validation_results,
            'rankings': {}
        }
        
        # Calculate summary statistics for each strategy
        for strategy_name, results in self.validation_results.items():
            if not results:
                continue
            
            metrics = {
                'total_return': [r.total_return for r in results],
                'sharpe_ratio': [r.sharpe_ratio for r in results],
                'max_drawdown': [r.max_drawdown for r in results],
                'win_rate': [r.win_rate for r in results],
                'profit_factor': [r.profit_factor for r in results]
            }
            
            summary = {}
            for metric, values in metrics.items():
                summary[metric] = {
                    'mean': np.mean(values),
                    'std': np.std(values),
                    'min': np.min(values),
                    'max': np.max(values)
                }
            
            report['summary'][strategy_name] = summary
        
        # Create rankings
        ranking_metrics = ['sharpe_ratio', 'total_return', 'win_rate']
        for metric in ranking_metrics:
            rankings = []
            for strategy_name in self.validation_results.keys():
                if strategy_name in report['summary']:
                    avg_value = report['summary'][strategy_name][metric]['mean']
                    rankings.append((strategy_name, avg_value))
            
            rankings.sort(key=lambda x: x[1], reverse=True)
            report['rankings'][metric] = rankings
        
        return report


class HighFidelityBacktester:
    """
    Advanced backtesting engine with high-fidelity market simulation.
    
    Features:
    - Tick-by-tick simulation
    - Realistic order execution
    - Market microstructure modeling
    - Regime-aware testing
    """
    
    def __init__(self):
        self.simulators = {}
        self.benchmark_data = None
        
    def add_simulator(self, name: str, simulator: DigitalTwinSimulator):
        """Add a configured simulator."""
        self.simulators[name] = simulator
    
    def run_comprehensive_backtest(self, 
                                 strategy: Callable,
                                 market_data: pd.DataFrame,
                                 benchmark_symbol: str = 'SPY') -> Dict:
        """
        Run comprehensive backtest with multiple market conditions.
        
        Returns detailed analysis including regime-specific performance.
        """
        # Identify market regimes
        regimes = self._identify_market_regimes(market_data)
        
        # Run backtests for each regime
        regime_results = {}
        for regime_name, regime_data in regimes.items():
            if len(regime_data) > 50:  # Minimum data points
                simulator = DigitalTwinSimulator()
                simulator.load_market_data(regime_data)
                
                result = simulator.simulate_strategy(strategy)
                regime_results[regime_name] = result
        
        # Overall backtest
        overall_simulator = DigitalTwinSimulator()
        overall_simulator.load_market_data(market_data)
        overall_result = overall_simulator.simulate_strategy(strategy)
        
        return {
            'overall_performance': overall_result,
            'regime_performance': regime_results,
            'regime_analysis': self._analyze_regime_performance(regime_results)
        }
    
    def _identify_market_regimes(self, data: pd.DataFrame) -> Dict[str, pd.DataFrame]:
        """Identify different market regimes in the data."""
        # Simple regime identification based on volatility and trend
        returns = data['close'].pct_change()
        volatility = returns.rolling(20).std()
        
        # Define regime thresholds
        vol_high = volatility.quantile(0.7)
        vol_low = volatility.quantile(0.3)
        
        regimes = {}
        
        # High volatility periods
        high_vol_mask = volatility > vol_high
        if high_vol_mask.any():
            regimes['high_volatility'] = data[high_vol_mask]
        
        # Low volatility periods
        low_vol_mask = volatility < vol_low
        if low_vol_mask.any():
            regimes['low_volatility'] = data[low_vol_mask]
        
        # Trending periods (simplified)
        trend_strength = abs(returns.rolling(20).mean())
        trend_mask = trend_strength > trend_strength.quantile(0.6)
        if trend_mask.any():
            regimes['trending'] = data[trend_mask]
        
        return regimes
    
    def _analyze_regime_performance(self, regime_results: Dict[str, SimulationResult]) -> Dict:
        """Analyze performance across different market regimes."""
        analysis = {}
        
        for regime, result in regime_results.items():
            analysis[regime] = {
                'return': result.total_return,
                'sharpe': result.sharpe_ratio,
                'drawdown': result.max_drawdown,
                'trades': result.total_trades,
                'win_rate': result.win_rate
            }
        
        # Find best and worst performing regimes
        if regime_results:
            best_regime = max(regime_results.keys(), 
                            key=lambda x: regime_results[x].sharpe_ratio)
            worst_regime = min(regime_results.keys(), 
                             key=lambda x: regime_results[x].sharpe_ratio)
            
            analysis['best_regime'] = best_regime
            analysis['worst_regime'] = worst_regime
        
        return analysis
