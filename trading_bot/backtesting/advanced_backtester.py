import logging
logger = logging.getLogger(__name__)
"""Advanced Backtesting/Forward Testing Framework

This module implements a comprehensive backtesting and forward testing system
with walk-forward analysis, Monte Carlo simulation, and performance attribution.
"""

import numpy as np
import pandas as pd
from typing import Any, Callable, Dict, List, Optional, Tuple, Union, Literal
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
import uuid
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from loguru import logger
import numpy
import pandas


class TestMode(Enum):
    """Testing modes."""
    BACKTEST = auto()
    FORWARD_TEST = auto()
    WALK_FORWARD = auto()
    MONTE_CARLO = auto()


class OrderType(Enum):
    """Order types for backtesting."""
    MARKET = auto()
    LIMIT = auto()
    STOP = auto()
    STOP_LIMIT = auto()


@dataclass
class BacktestOrder:
    """Order for backtesting."""
    id: str
    timestamp: datetime
    symbol: str
    side: str  # 'buy' or 'sell'
    order_type: OrderType
    quantity: float
    price: Optional[float] = None
    stop_price: Optional[float] = None
    filled_quantity: float = 0.0
    filled_price: Optional[float] = None
    status: str = 'pending'  # pending, filled, cancelled, rejected


@dataclass
class BacktestTrade:
    """Completed trade in backtest."""
    id: str
    symbol: str
    entry_time: datetime
    exit_time: datetime
    entry_price: float
    exit_price: float
    quantity: float
    side: str
    pnl: float
    pnl_pct: float
    duration: timedelta
    strategy: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BacktestResults:
    """Results of a backtest."""
    test_id: str
    start_date: datetime
    end_date: datetime
    initial_capital: float
    final_capital: float
    total_return: float
    total_return_pct: float
    sharpe_ratio: float
    sortino_ratio: float
    max_drawdown: float
    max_drawdown_pct: float
    win_rate: float
    profit_factor: float
    total_trades: int
    avg_trade_duration: timedelta
    trades: List[BacktestTrade]
    equity_curve: pd.DataFrame
    performance_metrics: Dict[str, float]
    risk_metrics: Dict[str, float]


class AdvancedBacktester:
    """Advanced backtesting and forward testing framework."""
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize the backtester.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self._init_default_config()
        
        # Backtesting state
        self.current_time: Optional[datetime] = None
        self.portfolio: Dict[str, float] = {}
        self.cash: float = 0.0
        self.equity_history: List[Tuple[datetime, float]] = []
        self.pending_orders: List[BacktestOrder] = []
        self.completed_trades: List[BacktestTrade] = []
        self.open_positions: Dict[str, Dict[str, Any]] = {}
        
        # Market data
        self.market_data: Dict[str, pd.DataFrame] = {}
        
        logger.info("AdvancedBacktester initialized")
    
    def _init_default_config(self):
        """Initialize default configuration."""
        defaults = {
            "initial_capital": 100000.0,
            "commission": 0.001,  # 0.1%
            "slippage": 0.0005,   # 0.05%
            "max_positions": 10,
            "position_size_limit": 0.2,  # 20% of portfolio
            "risk_free_rate": 0.02,  # 2% annual
            "benchmark_symbol": "SPY",
            "rebalance_frequency": "daily",
            "monte_carlo_runs": 1000,
            "walk_forward_periods": 12,
            "confidence_levels": [0.95, 0.99],
            "parallel_processing": True,
            "max_workers": 4
        }
        
        for key, value in defaults.items():
            if key not in self.config:
                self.config[key] = value
    
    def load_market_data(self, symbol: str, data: pd.DataFrame):
        """Load market data for backtesting.
        
        Args:
            symbol: Symbol identifier
            data: DataFrame with OHLCV data
        """
        # Ensure required columns exist
        required_columns = ['open', 'high', 'low', 'close', 'volume']
        if not all(col in data.columns for col in required_columns):
            raise ValueError(f"Data must contain columns: {required_columns}")
        
        # Ensure datetime index
        if not isinstance(data.index, pd.DatetimeIndex):
            data.index = pd.to_datetime(data.index)
        
        self.market_data[symbol] = data.sort_index()
        logger.info(f"Loaded {len(data)} bars for {symbol}")
    
    def run_backtest(self,
                    strategy_func: Callable,
                    start_date: datetime,
                    end_date: datetime,
                    symbols: List[str],
                    initial_capital: float = None) -> BacktestResults:
        """Run a backtest.
        
        Args:
            strategy_func: Strategy function to test
            start_date: Start date for backtest
            end_date: End date for backtest
            symbols: List of symbols to trade
            initial_capital: Initial capital (optional)
            
        Returns:
            Backtest results
        """
        test_id = str(uuid.uuid4())
        
        # Initialize backtest state
        self._initialize_backtest(initial_capital or self.config["initial_capital"])
        
        # Get date range
        date_range = self._get_date_range(start_date, end_date, symbols)
        
        logger.info(f"Starting backtest {test_id} from {start_date} to {end_date}")
        
        # Run backtest simulation
        for current_date in date_range:
            self.current_time = current_date
            
            # Update market data
            market_data = self._get_market_data_at_time(current_date, symbols)
            
            # Process pending orders
            self._process_pending_orders(market_data)
            
            # Update portfolio value
            portfolio_value = self._calculate_portfolio_value(market_data)
            self.equity_history.append((current_date, portfolio_value))
            
            # Run strategy
            try:
                signals = strategy_func(current_date, market_data, self._get_portfolio_state())
                self._process_strategy_signals(signals, market_data)
            except Exception as e:
                logger.error(f"Strategy error at {current_date}: {e}")
                continue
        
        # Generate results
        results = self._generate_backtest_results(test_id, start_date, end_date)
        
        logger.info(f"Backtest {test_id} completed. Total return: {results.total_return_pct:.2%}")
        return results
    
    def run_walk_forward_analysis(self,
                                 strategy_func: Callable,
                                 start_date: datetime,
                                 end_date: datetime,
                                 symbols: List[str],
                                 train_period_months: int = 12,
                                 test_period_months: int = 3) -> Dict[str, Any]:
        """Run walk-forward analysis.
        
        Args:
            strategy_func: Strategy function to test
            start_date: Start date for analysis
            end_date: End date for analysis
            symbols: List of symbols to trade
            train_period_months: Training period in months
            test_period_months: Testing period in months
            
        Returns:
            Walk-forward analysis results
        """
        logger.info("Starting walk-forward analysis")
        
        results = []
        current_start = start_date
        
        while current_start < end_date:
            # Define training and testing periods
            train_end = current_start + timedelta(days=train_period_months * 30)
            test_start = train_end
            test_end = test_start + timedelta(days=test_period_months * 30)
            
            if test_end > end_date:
                test_end = end_date
            
            if test_start >= end_date:
                break
            
            logger.info(f"Walk-forward period: train {current_start} to {train_end}, test {test_start} to {test_end}")
            
            # Run backtest for this period
            period_results = self.run_backtest(strategy_func, test_start, test_end, symbols)
            
            results.append({
                'train_start': current_start,
                'train_end': train_end,
                'test_start': test_start,
                'test_end': test_end,
                'results': period_results
            })
            
            # Move to next period
            current_start = test_end
        
        # Aggregate results
        return self._aggregate_walk_forward_results(results)
    
    def run_monte_carlo_simulation(self,
                                  strategy_func: Callable,
                                  start_date: datetime,
                                  end_date: datetime,
                                  symbols: List[str],
                                  num_runs: int = None) -> Dict[str, Any]:
        """Run Monte Carlo simulation.
        
        Args:
            strategy_func: Strategy function to test
            start_date: Start date for simulation
            end_date: End date for simulation
            symbols: List of symbols to trade
            num_runs: Number of simulation runs
            
        Returns:
            Monte Carlo simulation results
        """
        num_runs = num_runs or self.config["monte_carlo_runs"]
        logger.info(f"Starting Monte Carlo simulation with {num_runs} runs")
        
        # Prepare randomized market data scenarios
        scenarios = self._generate_market_scenarios(symbols, start_date, end_date, num_runs)
        
        # Run simulations
        if self.config["parallel_processing"]:
            results = self._run_parallel_simulations(strategy_func, scenarios, start_date, end_date, symbols)
        else:
            results = self._run_sequential_simulations(strategy_func, scenarios, start_date, end_date, symbols)
        
        # Analyze results
        return self._analyze_monte_carlo_results(results)
    
    def _initialize_backtest(self, initial_capital: float):
        """Initialize backtest state."""
        self.cash = initial_capital
        self.portfolio = {}
        self.equity_history = []
        self.pending_orders = []
        self.completed_trades = []
        self.open_positions = {}
    
    def _get_date_range(self, start_date: datetime, end_date: datetime, symbols: List[str]) -> pd.DatetimeIndex:
        """Get date range for backtesting."""
        # Find common date range across all symbols
        all_dates = set()
        
        for symbol in symbols:
            if symbol in self.market_data:
                symbol_dates = self.market_data[symbol].index
                symbol_dates = symbol_dates[(symbol_dates >= start_date) & (symbol_dates <= end_date)]
                all_dates.update(symbol_dates)
        
        if not all_dates:
            raise ValueError("No market data available for the specified date range")
        
        return pd.DatetimeIndex(sorted(all_dates))
    
    def _get_market_data_at_time(self, timestamp: datetime, symbols: List[str]) -> Dict[str, Dict[str, float]]:
        """Get market data at specific timestamp."""
        market_data = {}
        
        for symbol in symbols:
            if symbol in self.market_data:
                data = self.market_data[symbol]
                
                # Find closest timestamp (backward looking)
                available_times = data.index[data.index <= timestamp]
                if len(available_times) > 0:
                    closest_time = available_times[-1]
                    row = data.loc[closest_time]
                    
                    market_data[symbol] = {
                        'open': row['open'],
                        'high': row['high'],
                        'low': row['low'],
                        'close': row['close'],
                        'volume': row['volume'],
                        'timestamp': closest_time
                    }
        
        return market_data
    
    def _process_pending_orders(self, market_data: Dict[str, Dict[str, float]]):
        """Process pending orders."""
        filled_orders = []
        
        for order in self.pending_orders:
            if order.symbol in market_data:
                symbol_data = market_data[order.symbol]
                
                # Check if order can be filled
                if self._can_fill_order(order, symbol_data):
                    fill_price = self._calculate_fill_price(order, symbol_data)
                    self._fill_order(order, fill_price)
                    filled_orders.append(order)
        
        # Remove filled orders
        for order in filled_orders:
            self.pending_orders.remove(order)
    
    def _can_fill_order(self, order: BacktestOrder, market_data: Dict[str, float]) -> bool:
        """Check if order can be filled."""
        if order.order_type == OrderType.MARKET:
            return True
        elif order.order_type == OrderType.LIMIT:
            if order.side == 'buy':
                return market_data['low'] <= order.price
            else:
                return market_data['high'] >= order.price
        elif order.order_type == OrderType.STOP:
            if order.side == 'buy':
                return market_data['high'] >= order.stop_price
            else:
                return market_data['low'] <= order.stop_price
        
        return False
    
    def _calculate_fill_price(self, order: BacktestOrder, market_data: Dict[str, float]) -> float:
        """Calculate order fill price with variable spread and market impact."""
        # 1. Base price from market data
        base_price = market_data['open'] if order.order_type == OrderType.MARKET else (order.price if order.price else market_data['close'])

        # 2. Variable Spread modeling
        volatility = market_data.get('volatility', (market_data['high'] - market_data['low']) / market_data['close'])
        spread = self.config.get("base_spread", 0.0001) + (volatility * 0.1)

        # 3. Market Impact (Linear model based on quantity/volume)
        volume = market_data.get('volume', 1000000)
        market_impact = (order.quantity / volume) * self.config.get("impact_coefficient", 0.1)
        
        # 4. Realistic Slippage (linked to volatility)
        slippage = self.config["slippage"] + (volatility * np.random.uniform(0.05, 0.2))

        if order.side == 'buy':
            fill_price = base_price * (1 + spread/2 + market_impact + slippage)
        else:
            fill_price = base_price * (1 - spread/2 - market_impact - slippage)

        return fill_price
    
    def _fill_order(self, order: BacktestOrder, fill_price: float):
        """Fill an order."""
        # Calculate commission
        commission = order.quantity * fill_price * self.config["commission"]
        
        if order.side == 'buy':
            # Check if we have enough cash
            total_cost = order.quantity * fill_price + commission
            if self.cash >= total_cost:
                self.cash -= total_cost
                self.portfolio[order.symbol] = self.portfolio.get(order.symbol, 0) + order.quantity
                
                # Record as open position or add to existing
                if order.symbol not in self.open_positions:
                    self.open_positions[order.symbol] = {
                        'quantity': order.quantity,
                        'entry_price': fill_price,
                        'entry_time': order.timestamp,
                        'side': 'long'
                    }
                else:
                    # Average in
                    existing = self.open_positions[order.symbol]
                    total_quantity = existing['quantity'] + order.quantity
                    avg_price = ((existing['quantity'] * existing['entry_price']) + 
                               (order.quantity * fill_price)) / total_quantity
                    existing['quantity'] = total_quantity
                    existing['entry_price'] = avg_price
                
                order.status = 'filled'
                order.filled_quantity = order.quantity
                order.filled_price = fill_price
                
        else:  # sell
            if self.portfolio.get(order.symbol, 0) >= order.quantity:
                proceeds = order.quantity * fill_price - commission
                self.cash += proceeds
                self.portfolio[order.symbol] -= order.quantity
                
                # Close position and record trade
                if order.symbol in self.open_positions:
                    position = self.open_positions[order.symbol]
                    
                    # Calculate P&L
                    pnl = (fill_price - position['entry_price']) * order.quantity - commission
                    pnl_pct = pnl / (position['entry_price'] * order.quantity)
                    
                    # Create trade record
                    trade = BacktestTrade(
                        id=str(uuid.uuid4()),
                        symbol=order.symbol,
                        entry_time=position['entry_time'],
                        exit_time=order.timestamp,
                        entry_price=position['entry_price'],
                        exit_price=fill_price,
                        quantity=order.quantity,
                        side=position['side'],
                        pnl=pnl,
                        pnl_pct=pnl_pct,
                        duration=order.timestamp - position['entry_time'],
                        strategy="backtest"
                    )
                    
                    self.completed_trades.append(trade)
                    
                    # Update or remove position
                    if position['quantity'] > order.quantity:
                        position['quantity'] -= order.quantity
                    else:
                        del self.open_positions[order.symbol]
                
                order.status = 'filled'
                order.filled_quantity = order.quantity
                order.filled_price = fill_price
    
    def _calculate_portfolio_value(self, market_data: Dict[str, Dict[str, float]]) -> float:
        """Calculate current portfolio value."""
        total_value = self.cash
        
        for symbol, quantity in self.portfolio.items():
            if quantity > 0 and symbol in market_data:
                current_price = market_data[symbol]['close']
                total_value += quantity * current_price
        
        return total_value
    
    def _get_portfolio_state(self) -> Dict[str, Any]:
        """Get current portfolio state."""
        return {
            'cash': self.cash,
            'positions': self.portfolio.copy(),
            'open_positions': self.open_positions.copy(),
            'equity_history': self.equity_history.copy()
        }
    
    def _process_strategy_signals(self, signals: List[Dict[str, Any]], market_data: Dict[str, Dict[str, float]]):
        """Process signals from strategy."""
        for signal in signals:
            if signal['action'] in ['buy', 'sell']:
                order = BacktestOrder(
                    id=str(uuid.uuid4()),
                    timestamp=self.current_time,
                    symbol=signal['symbol'],
                    side=signal['action'],
                    order_type=OrderType.MARKET,
                    quantity=signal['quantity']
                )
                
                self.pending_orders.append(order)
    
    def _generate_backtest_results(self, test_id: str, start_date: datetime, end_date: datetime) -> BacktestResults:
        """Generate backtest results."""
        if not self.equity_history:
            raise ValueError("No equity history available")
        
        # Convert equity history to DataFrame
        equity_df = pd.DataFrame(self.equity_history, columns=['timestamp', 'equity'])
        equity_df.set_index('timestamp', inplace=True)
        
        initial_capital = self.config["initial_capital"]
        final_capital = equity_df['equity'].iloc[-1]
        
        # Calculate returns
        equity_df['returns'] = equity_df['equity'].pct_change().fillna(0)
        
        # Performance metrics
        total_return = final_capital - initial_capital
        total_return_pct = total_return / initial_capital
        
        # Risk metrics
        returns = equity_df['returns']
        sharpe_ratio = self._calculate_sharpe_ratio(returns)
        sortino_ratio = self._calculate_sortino_ratio(returns)
        max_drawdown, max_drawdown_pct = self._calculate_max_drawdown(equity_df['equity'])
        
        # Trade statistics
        if self.completed_trades:
            winning_trades = [t for t in self.completed_trades if t.pnl > 0]
            win_rate = len(winning_trades) / len(self.completed_trades)
            
            gross_profit = sum(t.pnl for t in winning_trades)
            gross_loss = abs(sum(t.pnl for t in self.completed_trades if t.pnl < 0))
            profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
            
            avg_duration = sum((t.duration for t in self.completed_trades), timedelta()) / len(self.completed_trades)
        else:
            win_rate = 0.0
            profit_factor = 0.0
            avg_duration = timedelta()
        
        return BacktestResults(
            test_id=test_id,
            start_date=start_date,
            end_date=end_date,
            initial_capital=initial_capital,
            final_capital=final_capital,
            total_return=total_return,
            total_return_pct=total_return_pct,
            sharpe_ratio=sharpe_ratio,
            sortino_ratio=sortino_ratio,
            max_drawdown=max_drawdown,
            max_drawdown_pct=max_drawdown_pct,
            win_rate=win_rate,
            profit_factor=profit_factor,
            total_trades=len(self.completed_trades),
            avg_trade_duration=avg_duration,
            trades=self.completed_trades.copy(),
            equity_curve=equity_df,
            performance_metrics={
                'volatility': returns.std() * np.sqrt(252),
                'skewness': returns.skew(),
                'kurtosis': returns.kurtosis()
            },
            risk_metrics={
                'var_95': returns.quantile(0.05),
                'cvar_95': returns[returns <= returns.quantile(0.05)].mean(),
                'calmar_ratio': total_return_pct / abs(max_drawdown_pct) if max_drawdown_pct != 0 else 0
            }
        )
    
    def _calculate_sharpe_ratio(self, returns: pd.Series) -> float:
        """Calculate Sharpe ratio."""
        if returns.std() == 0:
            return 0.0
        
        excess_returns = returns - self.config["risk_free_rate"] / 252
        return excess_returns.mean() / returns.std() * np.sqrt(252)
    
    def _calculate_sortino_ratio(self, returns: pd.Series) -> float:
        """Calculate Sortino ratio."""
        downside_returns = returns[returns < 0]
        if len(downside_returns) == 0 or downside_returns.std() == 0:
            return 0.0
        
        excess_returns = returns - self.config["risk_free_rate"] / 252
        return excess_returns.mean() / downside_returns.std() * np.sqrt(252)
    
    def _calculate_max_drawdown(self, equity: pd.Series) -> Tuple[float, float]:
        """Calculate maximum drawdown."""
        peak = equity.expanding().max()
        drawdown = equity - peak
        max_drawdown = drawdown.min()
        max_drawdown_pct = (drawdown / peak).min()
        
        return max_drawdown, max_drawdown_pct
    
    def _generate_market_scenarios(self, symbols: List[str], start_date: datetime, 
                                 end_date: datetime, num_scenarios: int) -> List[Dict[str, pd.DataFrame]]:
        """Generate market scenarios for Monte Carlo simulation."""
        scenarios = []
        
        for _ in range(num_scenarios):
            scenario = {}
            
            for symbol in symbols:
                if symbol in self.market_data:
                    original_data = self.market_data[symbol]
                    
                    # Bootstrap sampling with replacement
                    returns = original_data['close'].pct_change().dropna()
                    sampled_returns = np.random.choice(returns, size=len(returns), replace=True)
                    
                    # Reconstruct price series
                    initial_price = original_data['close'].iloc[0]
                    simulated_prices = [initial_price]
                    
                    for ret in sampled_returns:
                        simulated_prices.append(simulated_prices[-1] * (1 + ret))
                    
                    # Create simulated OHLCV data
                    simulated_data = original_data.copy()
                    simulated_data['close'] = simulated_prices[1:]
                    
                    # Adjust OHLC based on close prices
                    price_ratio = simulated_data['close'] / original_data['close']
                    simulated_data['open'] = original_data['open'] * price_ratio
                    simulated_data['high'] = original_data['high'] * price_ratio
                    simulated_data['low'] = original_data['low'] * price_ratio
                    
                    scenario[symbol] = simulated_data
            
            scenarios.append(scenario)
        
        return scenarios
    
    def _run_parallel_simulations(self, strategy_func: Callable, scenarios: List[Dict], 
                                start_date: datetime, end_date: datetime, symbols: List[str]) -> List[BacktestResults]:
        """Run simulations in parallel."""
        with ProcessPoolExecutor(max_workers=self.config["max_workers"]) as executor:
            futures = []
            
            for i, scenario in enumerate(scenarios):
                # Create a new backtester instance for each scenario
                future = executor.submit(self._run_single_simulation, strategy_func, scenario, 
                                       start_date, end_date, symbols, i)
                futures.append(future)
            
            results = [future.result() for future in futures]
        
        return results
    
    def _run_sequential_simulations(self, strategy_func: Callable, scenarios: List[Dict],
                                   start_date: datetime, end_date: datetime, symbols: List[str]) -> List[BacktestResults]:
        """Run simulations sequentially."""
        results = []
        
        for i, scenario in enumerate(scenarios):
            result = self._run_single_simulation(strategy_func, scenario, start_date, end_date, symbols, i)
            results.append(result)
        
        return results
    
    def _run_single_simulation(self, strategy_func: Callable, scenario: Dict[str, pd.DataFrame],
                             start_date: datetime, end_date: datetime, symbols: List[str], 
                             scenario_id: int) -> BacktestResults:
        """Run a single simulation scenario."""
        # Create new backtester instance
        backtester = AdvancedBacktester(self.config)
        
        # Load scenario data
        for symbol, data in scenario.items():
            backtester.load_market_data(symbol, data)
        
        # Run backtest
        return backtester.run_backtest(strategy_func, start_date, end_date, symbols)
    
    def _aggregate_walk_forward_results(self, results: List[Dict]) -> Dict[str, Any]:
        """Aggregate walk-forward analysis results."""
        if not results:
            return {}
        
        # Combine all results
        all_returns = []
        all_sharpe_ratios = []
        all_max_drawdowns = []
        
        for period in results:
            result = period['results']
            all_returns.append(result.total_return_pct)
            all_sharpe_ratios.append(result.sharpe_ratio)
            all_max_drawdowns.append(result.max_drawdown_pct)
        
        return {
            'total_periods': len(results),
            'average_return': np.mean(all_returns),
            'return_std': np.std(all_returns),
            'average_sharpe': np.mean(all_sharpe_ratios),
            'sharpe_std': np.std(all_sharpe_ratios),
            'average_max_drawdown': np.mean(all_max_drawdowns),
            'worst_drawdown': min(all_max_drawdowns),
            'consistency_score': len([r for r in all_returns if r > 0]) / len(all_returns),
            'period_results': results
        }
    
    def _analyze_monte_carlo_results(self, results: List[BacktestResults]) -> Dict[str, Any]:
        """Analyze Monte Carlo simulation results."""
        if not results:
            return {}
        
        returns = [r.total_return_pct for r in results]
        sharpe_ratios = [r.sharpe_ratio for r in results]
        max_drawdowns = [r.max_drawdown_pct for r in results]
        
        return {
            'num_simulations': len(results),
            'return_statistics': {
                'mean': np.mean(returns),
                'std': np.std(returns),
                'min': np.min(returns),
                'max': np.max(returns),
                'percentiles': {
                    '5%': np.percentile(returns, 5),
                    '25%': np.percentile(returns, 25),
                    '50%': np.percentile(returns, 50),
                    '75%': np.percentile(returns, 75),
                    '95%': np.percentile(returns, 95)
                }
            },
            'sharpe_statistics': {
                'mean': np.mean(sharpe_ratios),
                'std': np.std(sharpe_ratios),
                'min': np.min(sharpe_ratios),
                'max': np.max(sharpe_ratios)
            },
            'drawdown_statistics': {
                'mean': np.mean(max_drawdowns),
                'worst': np.min(max_drawdowns),
                'percentiles': {
                    '5%': np.percentile(max_drawdowns, 5),
                    '25%': np.percentile(max_drawdowns, 25),
                    '50%': np.percentile(max_drawdowns, 50),
                    '75%': np.percentile(max_drawdowns, 75),
                    '95%': np.percentile(max_drawdowns, 95)
                }
            },
            'probability_of_profit': len([r for r in returns if r > 0]) / len(returns),
            'value_at_risk': {
                '95%': np.percentile(returns, 5),
                '99%': np.percentile(returns, 1)
            }
        }


# ===========================================================================
# Institutional-Grade Backtesting Extensions (High Fidelity Costs & Limits)
# ===========================================================================

from trading_bot.strategy.strategy_engine import StrategyEngine, Signal

Direction = Literal["buy", "sell"]


@dataclass(slots=True)
class InstitutionalTrade:
    symbol: str
    direction: Direction
    entry_idx: int
    entry_time: float
    entry_price: float
    sl_price: float
    tp_price: float

    # Cost & Execution tracking fields
    spread_paid_pips: float = 0.0
    slippage_paid_pips: float = 0.0
    commission_paid_usd: float = 0.0

    exit_idx: int | None = None
    exit_price: float | None = None
    exit_reason: str | None = None  # "tp" | "sl" | "end" | "risk_breaker"

    def is_open(self) -> bool:
        return self.exit_idx is None

    def gross_pnl(self) -> float:
        if self.exit_price is None:
            return 0.0
        delta = self.exit_price - self.entry_price
        return delta if self.direction == "buy" else -delta

    def net_pnl_pips(self) -> float:
        """Calculates Net P&L in pips, deducting spread and slippage cost."""
        if self.exit_price is None:
            return 0.0
        gross_pips = self.gross_pnl() * 10000.0
        # Subtract costs
        net_pips = gross_pips - self.spread_paid_pips - self.slippage_paid_pips
        return net_pips

    def net_pnl_usd(self, lot_size_usd: float = 100000.0) -> float:
        """Translates Net P&L to USD based on lot size and commission drag."""
        pips = self.net_pnl_pips()
        # Pip value is typically $10 for 1 standard lot (100,000 units) on standard currency pairs
        pip_value_usd = (lot_size_usd * 0.0001)
        gross_net_usd = pips * pip_value_usd
        return gross_net_usd - self.commission_paid_usd


@dataclass(slots=True)
class InstitutionalBacktestResult:
    trades: List[InstitutionalTrade] = field(default_factory=list)
    total_commission_paid: float = 0.0
    total_slippage_paid_pips: float = 0.0
    sharpe_ratio: float = 0.0
    max_drawdown_pct: float = 0.0
    total_return_pct: float = 0.0
    passed_objectives: bool = True
    objectives_report: Dict[str, Any] = field(default_factory=dict)

    @property
    def n_trades(self) -> int:
        return len(self.trades)

    @property
    def win_rate(self) -> float:
        if not self.trades:
            return 0.0
        wins = sum(1 for t in self.trades if t.exit_reason == "tp")
        return (wins / len(self.trades)) * 100.0


class InstitutionalBacktester:
    """
    Simulates high-fidelity backtests with transaction costs, slippage, and spread modeling.
    """

    def __init__(
        self,
        bars: pd.DataFrame,
        strategy: StrategyEngine,
        config: Dict[str, Any] = None,
        lookback: int = 100,
    ) -> None:
        self.bars = bars.reset_index(drop=True)
        self.strategy = strategy
        self.lookback = lookback
        self.open_trades: List[InstitutionalTrade] = []
        self.result = InstitutionalBacktestResult()

        # Load Institutional Config defaults if not provided
        self.config = config or {
            "execution_cost": {
                "commission_per_million_usd": 15.0,
                "fixed_commission_per_trade": 2.0,
                "default_spread_pips": 0.8,
                "default_slippage_pips": 0.4
            },
            "risk_limits": {
                "max_positions": 5,
                "max_spread_pips_limit": 2.5
            },
            "objectives": {
                "target_sharpe": 2.5,
                "max_drawdown_pct": 10.0
            }
        }

    def run(self) -> InstitutionalBacktestResult:
        logger.info(f"Starting Institutional Backtest - {len(self.bars)} bars.")

        # Initial stats tracking
        equity_curve = [100000.0]  # Start with $100,000 standard capital

        for i in range(self.lookback, len(self.bars)):
            window = self.bars.iloc[i - self.lookback : i + 1]
            signals = self.strategy.analyse(window)

            # Filter signals on the current bar
            current_idx = window.index[-1]
            if current_idx == i:
                for sig in signals:
                    # Enforce Hard Risk Limits before opening trade
                    if len(self.open_trades) >= self.config["risk_limits"]["max_positions"]:
                        logger.warning("Risk Limit: Max positions exceeded. Trade rejected.")
                        continue

                    spread = self.config["execution_cost"]["default_spread_pips"]
                    if spread > self.config["risk_limits"]["max_spread_pips_limit"]:
                        logger.warning("Risk Limit: Spread circuit breaker triggered. Trade rejected.")
                        continue

                    self._open_trade_with_costs(sig, i)

            self._update_open_trades(i)

            # Record current equity
            current_equity = 100000.0 + sum(t.net_pnl_usd() for t in self.result.trades) + sum(self._calculate_floating_pnl_usd(t, i) for t in self.open_trades)
            equity_curve.append(current_equity)

        # Force-close remaining positions
        last_idx = len(self.bars) - 1
        last_close = float(self.bars.iloc[last_idx].close)
        for t in list(self.open_trades):
            t.exit_idx = last_idx
            t.exit_price = last_close
            t.exit_reason = "end"
            self.result.trades.append(t)
        self.open_trades.clear()

        # Compute Institutional Performance Metrics
        self._calculate_performance_metrics(equity_curve)
        return self.result

    def _open_trade_with_costs(self, sig: Signal, idx: int) -> None:
        bar = self.bars.iloc[idx]
        price = float(bar.close)

        # Apply cost parameters
        spread = self.config["execution_cost"]["default_spread_pips"]
        # Slippage varies slightly based on market volatility/randomness
        slippage = self.config["execution_cost"]["default_slippage_pips"] + np.random.uniform(0, 0.2)
        fixed_comm = self.config["execution_cost"]["fixed_commission_per_trade"]

        # Calculate entry price adjusted for cost (slippage and half spread paid on entry)
        cost_drag_pips = (spread / 2.0) + slippage
        cost_drag_price_delta = cost_drag_pips * 0.0001

        if sig.direction == "buy":
            entry_price = price + cost_drag_price_delta
            sl_price = entry_price - sig.stop_loss_pips * 0.0001
            tp_price = entry_price + sig.stop_loss_pips * sig.take_profit_rr * 0.0001
        else:
            entry_price = price - cost_drag_price_delta
            sl_price = entry_price + sig.stop_loss_pips * 0.0001
            tp_price = entry_price - sig.stop_loss_pips * sig.take_profit_rr * 0.0001

        trade = InstitutionalTrade(
            symbol=sig.symbol,
            direction=sig.direction,
            entry_idx=idx,
            entry_time=float(bar.time) if "time" in bar else float(idx),
            entry_price=entry_price,
            sl_price=sl_price,
            tp_price=tp_price,
            spread_paid_pips=spread,
            slippage_paid_pips=slippage,
            commission_paid_usd=fixed_comm
        )
        self.open_trades.append(trade)

    def _update_open_trades(self, idx: int) -> None:
        bar = self.bars.iloc[idx]
        for trade in list(self.open_trades):
            if trade.direction == "buy":
                # Check for SL hit
                if bar.low <= trade.sl_price:
                    trade.exit_idx = idx
                    trade.exit_price = trade.sl_price
                    trade.exit_reason = "sl"
                # Check for TP hit
                elif bar.high >= trade.tp_price:
                    trade.exit_idx = idx
                    trade.exit_price = trade.tp_price
                    trade.exit_reason = "tp"
            else:  # sell
                # Check for SL hit
                if bar.high >= trade.sl_price:
                    trade.exit_idx = idx
                    trade.exit_price = trade.sl_price
                    trade.exit_reason = "sl"
                # Check for TP hit
                elif bar.low <= trade.tp_price:
                    trade.exit_idx = idx
                    trade.exit_price = trade.tp_price
                    trade.exit_reason = "tp"

            if not trade.is_open():
                self.open_trades.remove(trade)
                self.result.trades.append(trade)

    def _calculate_floating_pnl_usd(self, trade: InstitutionalTrade, idx: int) -> float:
        bar = self.bars.iloc[idx]
        curr_price = float(bar.close)
        gross_delta = curr_price - trade.entry_price
        pips = (gross_delta if trade.direction == "buy" else -gross_delta) * 10000.0
        # Subtract floating cost drag (remaining half spread + slippage)
        net_pips = pips - (trade.spread_paid_pips / 2.0) - trade.slippage_paid_pips
        return (net_pips * 10.0) - trade.commission_paid_usd

    def _calculate_performance_metrics(self, equity_curve: List[float]) -> None:
        eq = np.array(equity_curve)
        returns = np.diff(eq) / eq[:-1]

        # Cumulative return
        self.result.total_return_pct = ((eq[-1] - eq[0]) / eq[0]) * 100.0

        # Sharpe Ratio (annualized assuming standard bars/daily intervals or high turnover)
        if len(returns) > 1 and np.std(returns) > 0:
            avg_ret = np.mean(returns)
            std_ret = np.std(returns)
            # Standard Sharpe (non-annualized daily representation first, then scale by standard 252 days)
            self.result.sharpe_ratio = float((avg_ret / std_ret) * np.sqrt(252))
        else:
            self.result.sharpe_ratio = 0.0

        # Max Peak-to-Trough Drawdown
        cum_max = np.maximum.accumulate(eq)
        drawdowns = (cum_max - eq) / cum_max * 100.0
        self.result.max_drawdown_pct = float(np.max(drawdowns))

        # Commission and Slippage aggregates
        self.result.total_commission_paid = sum(t.commission_paid_usd for t in self.result.trades)
        self.result.total_slippage_paid_pips = sum(t.slippage_paid_pips for t in self.result.trades)

        # Validate Objectives
        target_sharpe = self.config["objectives"]["target_sharpe"]
        max_dd_allowed = self.config["objectives"]["max_drawdown_pct"]

        passed_sharpe = self.result.sharpe_ratio >= target_sharpe
        passed_drawdown = self.result.max_drawdown_pct <= max_dd_allowed

        self.result.passed_objectives = passed_sharpe and passed_drawdown
        self.result.objectives_report = {
            "sharpe_ratio": {"value": self.result.sharpe_ratio, "target": target_sharpe, "status": "PASS" if passed_sharpe else "FAIL"},
            "max_drawdown": {"value": self.result.max_drawdown_pct, "target": max_dd_allowed, "status": "PASS" if passed_drawdown else "FAIL"},
            "commission_paid_usd": self.result.total_commission_paid,
            "slippage_paid_pips": self.result.total_slippage_paid_pips
        }
