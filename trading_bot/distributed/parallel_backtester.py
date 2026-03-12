"""
Parallel Backtester
===================

Distributed backtesting across multiple workers.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any, Callable, Tuple
import pandas as pd
import numpy as np
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing as mp
import uuid
import time

logger = logging.getLogger(__name__)


class BacktestStatus(Enum):
    """Backtest job status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class BacktestConfig:
    """Backtest configuration"""
    symbol: str
    start_date: datetime
    end_date: datetime
    timeframe: str = "1h"
    initial_capital: float = 100000.0
    commission: float = 0.001
    slippage: float = 0.0001
    strategy_params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BacktestJob:
    """Backtest job definition"""
    job_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    config: BacktestConfig = None
    strategy_name: str = ""
    status: BacktestStatus = BacktestStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    worker_id: Optional[str] = None
    progress: float = 0.0


@dataclass
class TradeRecord:
    """Single trade record"""
    entry_time: datetime
    exit_time: datetime
    symbol: str
    direction: str  # 'long' or 'short'
    entry_price: float
    exit_price: float
    quantity: float
    pnl: float
    pnl_percent: float
    commission: float
    slippage: float


@dataclass
class BacktestResult:
    """Backtest result"""
    job_id: str
    status: BacktestStatus
    config: BacktestConfig
    
    # Performance metrics
    total_return: float = 0.0
    annual_return: float = 0.0
    sharpe_ratio: float = 0.0
    sortino_ratio: float = 0.0
    max_drawdown: float = 0.0
    calmar_ratio: float = 0.0
    win_rate: float = 0.0
    profit_factor: float = 0.0
    
    # Trade statistics
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    avg_win: float = 0.0
    avg_loss: float = 0.0
    largest_win: float = 0.0
    largest_loss: float = 0.0
    avg_trade_duration: float = 0.0
    
    # Equity curve
    equity_curve: List[float] = field(default_factory=list)
    drawdown_curve: List[float] = field(default_factory=list)
    
    # Trades
    trades: List[TradeRecord] = field(default_factory=list)
    
    # Execution info
    execution_time: float = 0.0
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'job_id': self.job_id,
            'status': self.status.value,
            'total_return': self.total_return,
            'annual_return': self.annual_return,
            'sharpe_ratio': self.sharpe_ratio,
            'sortino_ratio': self.sortino_ratio,
            'max_drawdown': self.max_drawdown,
            'calmar_ratio': self.calmar_ratio,
            'win_rate': self.win_rate,
            'profit_factor': self.profit_factor,
            'total_trades': self.total_trades,
            'execution_time': self.execution_time
        }


class BacktestEngine:
    """Core backtesting engine"""
    
    def __init__(self, config: BacktestConfig):
        self.config = config
        self.capital = config.initial_capital
        self.position = 0.0
        self.position_price = 0.0
        self.equity = [config.initial_capital]
        self.trades: List[TradeRecord] = []
        
    def run(
        self,
        data: pd.DataFrame,
        strategy: Callable[[pd.DataFrame, int], Optional[str]]
    ) -> BacktestResult:
        """
        Run backtest.
        
        Args:
            data: OHLCV DataFrame
            strategy: Strategy function that returns 'buy', 'sell', or None
            
        Returns:
            BacktestResult
        """
        start_time = time.time()
        
        try:
            for i in range(len(data)):
                current_bar = data.iloc[i]
                signal = strategy(data, i)
                
                if signal == 'buy' and self.position <= 0:
                    self._open_long(current_bar)
                elif signal == 'sell' and self.position >= 0:
                    self._open_short(current_bar)
                elif signal == 'close':
                    self._close_position(current_bar)
                    
                # Update equity
                self._update_equity(current_bar)
                
            # Close any open position
            if self.position != 0:
                self._close_position(data.iloc[-1])
                
            return self._calculate_results(time.time() - start_time)
            
        except Exception as e:
            logger.error(f"Backtest error: {e}")
            return BacktestResult(
                job_id="",
                status=BacktestStatus.FAILED,
                config=self.config,
                error=str(e),
                execution_time=time.time() - start_time
            )
            
    def _open_long(self, bar: pd.Series):
        """Open long position"""
        if self.position < 0:
            self._close_position(bar)
            
        price = bar['close'] * (1 + self.config.slippage)
        quantity = self.capital * 0.95 / price  # Use 95% of capital
        commission = quantity * price * self.config.commission
        
        self.position = quantity
        self.position_price = price
        self.capital -= commission
        
    def _open_short(self, bar: pd.Series):
        """Open short position"""
        if self.position > 0:
            self._close_position(bar)
            
        price = bar['close'] * (1 - self.config.slippage)
        quantity = self.capital * 0.95 / price
        commission = quantity * price * self.config.commission
        
        self.position = -quantity
        self.position_price = price
        self.capital -= commission
        
    def _close_position(self, bar: pd.Series):
        """Close current position"""
        if self.position == 0:
            return
            
        if self.position > 0:
            exit_price = bar['close'] * (1 - self.config.slippage)
            pnl = (exit_price - self.position_price) * self.position
        else:
            exit_price = bar['close'] * (1 + self.config.slippage)
            pnl = (self.position_price - exit_price) * abs(self.position)
            
        commission = abs(self.position) * exit_price * self.config.commission
        net_pnl = pnl - commission
        
        trade = TradeRecord(
            entry_time=bar.name if hasattr(bar, 'name') else datetime.now(),
            exit_time=bar.name if hasattr(bar, 'name') else datetime.now(),
            symbol=self.config.symbol,
            direction='long' if self.position > 0 else 'short',
            entry_price=self.position_price,
            exit_price=exit_price,
            quantity=abs(self.position),
            pnl=net_pnl,
            pnl_percent=net_pnl / (self.position_price * abs(self.position)),
            commission=commission,
            slippage=abs(bar['close'] - exit_price)
        )
        self.trades.append(trade)
        
        self.capital += net_pnl
        self.position = 0
        self.position_price = 0
        
    def _update_equity(self, bar: pd.Series):
        """Update equity curve"""
        if self.position > 0:
            unrealized = (bar['close'] - self.position_price) * self.position
        elif self.position < 0:
            unrealized = (self.position_price - bar['close']) * abs(self.position)
        else:
            unrealized = 0
            
        self.equity.append(self.capital + unrealized)
        
    def _calculate_results(self, execution_time: float) -> BacktestResult:
        """Calculate backtest results"""
        equity = np.array(self.equity)
        returns = np.diff(equity) / equity[:-1]
        
        # Calculate metrics
        total_return = (equity[-1] - equity[0]) / equity[0]
        
        # Annualized return (assuming daily data)
        days = len(equity)
        annual_return = (1 + total_return) ** (252 / max(days, 1)) - 1
        
        # Sharpe ratio
        if len(returns) > 0 and np.std(returns) > 0:
            sharpe_ratio = np.sqrt(252) * np.mean(returns) / np.std(returns)
        else:
            sharpe_ratio = 0
            
        # Sortino ratio
        downside_returns = returns[returns < 0]
        if len(downside_returns) > 0 and np.std(downside_returns) > 0:
            sortino_ratio = np.sqrt(252) * np.mean(returns) / np.std(downside_returns)
        else:
            sortino_ratio = 0
            
        # Max drawdown
        peak = np.maximum.accumulate(equity)
        drawdown = (peak - equity) / peak
        max_drawdown = np.max(drawdown)
        
        # Calmar ratio
        calmar_ratio = annual_return / max_drawdown if max_drawdown > 0 else 0
        
        # Trade statistics
        winning_trades = [t for t in self.trades if t.pnl > 0]
        losing_trades = [t for t in self.trades if t.pnl <= 0]
        
        win_rate = len(winning_trades) / len(self.trades) if self.trades else 0
        
        avg_win = np.mean([t.pnl for t in winning_trades]) if winning_trades else 0
        avg_loss = np.mean([t.pnl for t in losing_trades]) if losing_trades else 0
        
        gross_profit = sum(t.pnl for t in winning_trades)
        gross_loss = abs(sum(t.pnl for t in losing_trades))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0
        
        return BacktestResult(
            job_id="",
            status=BacktestStatus.COMPLETED,
            config=self.config,
            total_return=total_return,
            annual_return=annual_return,
            sharpe_ratio=sharpe_ratio,
            sortino_ratio=sortino_ratio,
            max_drawdown=max_drawdown,
            calmar_ratio=calmar_ratio,
            win_rate=win_rate,
            profit_factor=profit_factor,
            total_trades=len(self.trades),
            winning_trades=len(winning_trades),
            losing_trades=len(losing_trades),
            avg_win=avg_win,
            avg_loss=avg_loss,
            largest_win=max((t.pnl for t in self.trades), default=0),
            largest_loss=min((t.pnl for t in self.trades), default=0),
            equity_curve=self.equity,
            drawdown_curve=drawdown.tolist(),
            trades=self.trades,
            execution_time=execution_time
        )


def _run_single_backtest(args: Tuple) -> BacktestResult:
    """Run single backtest (for multiprocessing)"""
    config, data_dict, strategy_code = args
    
    # Reconstruct DataFrame
    data = pd.DataFrame(data_dict)
    if 'timestamp' in data.columns:
        data.set_index('timestamp', inplace=True)
        
    # Create strategy function from code
    local_vars = {}
    exec(strategy_code, local_vars)
    strategy = local_vars.get('strategy')
    
    if not strategy:
        return BacktestResult(
            job_id="",
            status=BacktestStatus.FAILED,
            config=config,
            error="Strategy function not found"
        )
        
    engine = BacktestEngine(config)
    return engine.run(data, strategy)


class ParallelBacktester:
    """
    Parallel backtesting system.
    
    Features:
    - Multi-process execution
    - Parameter optimization
    - Walk-forward analysis
    - Monte Carlo simulation
    """
    
    def __init__(self, num_workers: int = None):
        self.num_workers = num_workers or mp.cpu_count()
        self._executor = None
        self._jobs: Dict[str, BacktestJob] = {}
        self._results: Dict[str, BacktestResult] = {}
        
    def start(self):
        """Start parallel backtester"""
        self._executor = ProcessPoolExecutor(max_workers=self.num_workers)
        logger.info(f"ParallelBacktester started with {self.num_workers} workers")
        
    def stop(self):
        """Stop parallel backtester"""
        if self._executor:
            self._executor.shutdown(wait=True)
            self._executor = None
            
    def run_single(
        self,
        config: BacktestConfig,
        data: pd.DataFrame,
        strategy: Callable
    ) -> BacktestResult:
        """Run single backtest"""
        engine = BacktestEngine(config)
        result = engine.run(data, strategy)
        return result
        
    async def run_multiple(
        self,
        configs: List[BacktestConfig],
        data: pd.DataFrame,
        strategy_code: str
    ) -> List[BacktestResult]:
        """
        Run multiple backtests in parallel.
        
        Args:
            configs: List of backtest configurations
            data: OHLCV DataFrame
            strategy_code: Strategy code as string
            
        Returns:
            List of BacktestResults
        """
        if not self._executor:
            self.start()
            
        # Prepare data for serialization
        data_dict = data.reset_index().to_dict('list')
        
        # Submit jobs
        futures = []
        for config in configs:
            args = (config, data_dict, strategy_code)
            future = self._executor.submit(_run_single_backtest, args)
            futures.append(future)
            
        # Collect results
        results = []
        for future in as_completed(futures):
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                logger.error(f"Backtest failed: {e}")
                results.append(BacktestResult(
                    job_id="",
                    status=BacktestStatus.FAILED,
                    config=configs[0],
                    error=str(e)
                ))
                
        return results
        
    async def optimize_parameters(
        self,
        base_config: BacktestConfig,
        data: pd.DataFrame,
        strategy_code: str,
        param_grid: Dict[str, List[Any]]
    ) -> Tuple[Dict[str, Any], BacktestResult]:
        """
        Optimize strategy parameters using grid search.
        
        Args:
            base_config: Base backtest configuration
            data: OHLCV DataFrame
            strategy_code: Strategy code with {param} placeholders
            param_grid: Parameter grid to search
            
        Returns:
            Tuple of (best_params, best_result)
        """
        import itertools
        
        # Generate all parameter combinations
        param_names = list(param_grid.keys())
        param_values = list(param_grid.values())
        combinations = list(itertools.product(*param_values))
        
        logger.info(f"Running {len(combinations)} parameter combinations")
        
        # Create configs for each combination
        configs = []
        param_sets = []
        
        for combo in combinations:
            params = dict(zip(param_names, combo))
            config = BacktestConfig(
                symbol=base_config.symbol,
                start_date=base_config.start_date,
                end_date=base_config.end_date,
                timeframe=base_config.timeframe,
                initial_capital=base_config.initial_capital,
                commission=base_config.commission,
                slippage=base_config.slippage,
                strategy_params=params
            )
            configs.append(config)
            param_sets.append(params)
            
        # Format strategy code with parameters
        formatted_codes = []
        for params in param_sets:
            code = strategy_code
            for name, value in params.items():
                code = code.replace(f"{{{name}}}", str(value))
            formatted_codes.append(code)
            
        # Run backtests
        results = await self.run_multiple(configs, data, formatted_codes[0])
        
        # Find best result
        best_idx = 0
        best_sharpe = float('-inf')
        
        for i, result in enumerate(results):
            if result.status == BacktestStatus.COMPLETED and result.sharpe_ratio > best_sharpe:
                best_sharpe = result.sharpe_ratio
                best_idx = i
                
        return param_sets[best_idx], results[best_idx]
        
    async def walk_forward_analysis(
        self,
        config: BacktestConfig,
        data: pd.DataFrame,
        strategy_code: str,
        in_sample_ratio: float = 0.7,
        num_folds: int = 5
    ) -> List[BacktestResult]:
        """
        Perform walk-forward analysis.
        
        Args:
            config: Backtest configuration
            data: OHLCV DataFrame
            strategy_code: Strategy code
            in_sample_ratio: Ratio of data for in-sample
            num_folds: Number of walk-forward folds
            
        Returns:
            List of out-of-sample results
        """
        results = []
        fold_size = len(data) // num_folds
        
        for i in range(num_folds - 1):
            # Split data
            start_idx = i * fold_size
            split_idx = start_idx + int(fold_size * in_sample_ratio)
            end_idx = (i + 1) * fold_size
            
            in_sample = data.iloc[start_idx:split_idx]
            out_sample = data.iloc[split_idx:end_idx]
            
            # Train on in-sample (could optimize parameters here)
            # Test on out-of-sample
            engine = BacktestEngine(config)
            
            # Create strategy function
            local_vars = {}
            exec(strategy_code, local_vars)
            strategy = local_vars.get('strategy')
            
            if strategy:
                result = engine.run(out_sample, strategy)
                result.job_id = f"fold_{i}"
                results.append(result)
                
        return results
        
    async def monte_carlo_simulation(
        self,
        trades: List[TradeRecord],
        num_simulations: int = 1000,
        initial_capital: float = 100000.0
    ) -> Dict[str, Any]:
        """
        Run Monte Carlo simulation on trade results.
        
        Args:
            trades: List of trade records
            num_simulations: Number of simulations
            initial_capital: Starting capital
            
        Returns:
            Simulation statistics
        """
        if not trades:
            return {}
            
        pnls = [t.pnl for t in trades]
        
        final_equities = []
        max_drawdowns = []
        
        for _ in range(num_simulations):
            # Shuffle trades
            shuffled = np.random.permutation(pnls)
            
            # Calculate equity curve
            equity = [initial_capital]
            for pnl in shuffled:
                equity.append(equity[-1] + pnl)
                
            equity = np.array(equity)
            final_equities.append(equity[-1])
            
            # Calculate max drawdown
            peak = np.maximum.accumulate(equity)
            drawdown = (peak - equity) / peak
            max_drawdowns.append(np.max(drawdown))
            
        return {
            'mean_final_equity': np.mean(final_equities),
            'std_final_equity': np.std(final_equities),
            'percentile_5': np.percentile(final_equities, 5),
            'percentile_25': np.percentile(final_equities, 25),
            'percentile_50': np.percentile(final_equities, 50),
            'percentile_75': np.percentile(final_equities, 75),
            'percentile_95': np.percentile(final_equities, 95),
            'mean_max_drawdown': np.mean(max_drawdowns),
            'worst_drawdown': np.max(max_drawdowns),
            'probability_profit': np.mean(np.array(final_equities) > initial_capital)
        }


def create_parallel_backtester(num_workers: int = None) -> ParallelBacktester:
    """Factory function to create ParallelBacktester"""
    backtester = ParallelBacktester(num_workers)
    backtester.start()
    return backtester


# Example strategy
EXAMPLE_STRATEGY = '''
def strategy(data, i):
    """Simple moving average crossover strategy"""
    if i < 50:
        return None
        
    short_ma = data['close'].iloc[i-20:i].mean()
    long_ma = data['close'].iloc[i-50:i].mean()
    
    prev_short = data['close'].iloc[i-21:i-1].mean()
    prev_long = data['close'].iloc[i-51:i-1].mean()
    
    # Crossover signals
    if prev_short <= prev_long and short_ma > long_ma:
        return 'buy'
    elif prev_short >= prev_long and short_ma < long_ma:
        return 'sell'
        
    return None
'''


if __name__ == "__main__":
    async def main():
        print("=== Parallel Backtester Demo ===\n")
        
        # Generate sample data
        np.random.seed(42)
        dates = pd.date_range('2023-01-01', '2024-01-01', freq='1h')
        prices = 100 * np.cumprod(1 + np.random.randn(len(dates)) * 0.001)
        
        data = pd.DataFrame({
            'open': prices * (1 + np.random.randn(len(dates)) * 0.001),
            'high': prices * (1 + np.abs(np.random.randn(len(dates))) * 0.002),
            'low': prices * (1 - np.abs(np.random.randn(len(dates))) * 0.002),
            'close': prices,
            'volume': np.random.randint(1000, 10000, len(dates))
        }, index=dates)
        
        config = BacktestConfig(
            symbol='TEST',
            start_date=dates[0],
            end_date=dates[-1],
            timeframe='1h',
            initial_capital=100000
        )
        
        backtester = create_parallel_backtester(num_workers=4)
        
        try:
            # Single backtest
            print("1. Single backtest:")
            local_vars = {}
            exec(EXAMPLE_STRATEGY, local_vars)
            strategy = local_vars['strategy']
            
            result = backtester.run_single(config, data, strategy)
            print(f"   Total Return: {result.total_return:.2%}")
            print(f"   Sharpe Ratio: {result.sharpe_ratio:.2f}")
            print(f"   Max Drawdown: {result.max_drawdown:.2%}")
            print(f"   Total Trades: {result.total_trades}")
            
            # Monte Carlo
            if result.trades:
                print("\n2. Monte Carlo Simulation:")
                mc_results = await backtester.monte_carlo_simulation(
                    result.trades,
                    num_simulations=1000
                )
                print(f"   Mean Final Equity: ${mc_results['mean_final_equity']:,.2f}")
                print(f"   5th Percentile: ${mc_results['percentile_5']:,.2f}")
                print(f"   95th Percentile: ${mc_results['percentile_95']:,.2f}")
                print(f"   Probability of Profit: {mc_results['probability_profit']:.1%}")
                
        finally:
            backtester.stop()
            
    asyncio.run(main())
