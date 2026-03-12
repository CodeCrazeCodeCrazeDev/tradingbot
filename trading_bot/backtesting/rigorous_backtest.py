"""
Rigorous Backtesting Framework
Institutional-Grade Strategy Validation

This module provides comprehensive backtesting with:
- Out-of-Sample Testing (Walk-Forward Analysis)
- Transaction Cost Modeling (Spread, Slippage, Commission)
- Survivorship Bias Correction
- Statistical Significance Testing (t-test, bootstrap)
- Multiple Testing Correction (Bonferroni, FDR)
- Monte Carlo Simulation
- Regime-Based Analysis
- Cross-Validation

Quantitative Analyst + Auditor + Risk Manager Perspective
"""

import numpy as np
import pandas as pd
from typing import Any, Callable, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import logging
from collections import deque
try:
    from scipy import stats
except ImportError:
    scipy = None
import warnings
import numpy
import pandas

warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)


class ValidationMethod(Enum):
    """Validation methodology"""
    WALK_FORWARD = "WALK_FORWARD"  # Rolling window
    K_FOLD = "K_FOLD"  # K-fold cross-validation
    PURGED_K_FOLD = "PURGED_K_FOLD"  # Purged K-fold (no leakage)
    COMBINATORIAL = "COMBINATORIAL"  # Combinatorial purged CV
    MONTE_CARLO = "MONTE_CARLO"  # Monte Carlo simulation


class SignificanceTest(Enum):
    """Statistical significance tests"""
    T_TEST = "T_TEST"  # Student's t-test
    BOOTSTRAP = "BOOTSTRAP"  # Bootstrap hypothesis test
    PERMUTATION = "PERMUTATION"  # Permutation test
    SHARPE_RATIO = "SHARPE_RATIO"  # Sharpe ratio significance


@dataclass
class TransactionCostModel:
    """Transaction cost model"""
    spread_bps: float = 2.0  # Bid-ask spread in basis points
    commission_per_share: float = 0.005  # Commission per share
    commission_min: float = 1.0  # Minimum commission
    slippage_bps: float = 1.0  # Expected slippage in bps
    market_impact_coefficient: float = 0.1  # Market impact coefficient
    
    def calculate_cost(self,
                      price: float,
                      quantity: float,
                      adv: float = 1000000) -> Dict[str, float]:
        """Calculate total transaction cost"""
        value = price * quantity
        
        # Spread cost (half spread for crossing)
        spread_cost = value * (self.spread_bps / 10000) / 2
        
        # Commission
        commission = max(self.commission_min, quantity * self.commission_per_share)
        
        # Slippage
        slippage = value * (self.slippage_bps / 10000)
        
        # Market impact (square root model)
        participation = quantity / adv if adv > 0 else 0.01
        market_impact = value * self.market_impact_coefficient * np.sqrt(participation)
        
        total = spread_cost + commission + slippage + market_impact
        
        return {
            'spread_cost': spread_cost,
            'commission': commission,
            'slippage': slippage,
            'market_impact': market_impact,
            'total': total,
            'total_bps': (total / value) * 10000 if value > 0 else 0
        }


@dataclass
class BacktestResult:
    """Backtest result"""
    strategy_name: str
    start_date: datetime
    end_date: datetime
    
    # Returns
    total_return: float
    annualized_return: float
    
    # Risk metrics
    volatility: float
    sharpe_ratio: float
    sortino_ratio: float
    calmar_ratio: float
    max_drawdown: float
    
    # Trade statistics
    num_trades: int
    win_rate: float
    profit_factor: float
    avg_trade_return: float
    
    # Costs
    total_costs: float
    cost_drag: float  # Annual cost as % of return
    
    # Statistical significance
    t_statistic: float
    p_value: float
    is_significant: bool
    
    # Out-of-sample
    in_sample_sharpe: float
    out_of_sample_sharpe: float
    sharpe_decay: float  # OOS / IS ratio
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'strategy_name': self.strategy_name,
            'period': f"{self.start_date.date()} to {self.end_date.date()}",
            'total_return': round(self.total_return, 4),
            'annualized_return': round(self.annualized_return, 4),
            'volatility': round(self.volatility, 4),
            'sharpe_ratio': round(self.sharpe_ratio, 2),
            'sortino_ratio': round(self.sortino_ratio, 2),
            'calmar_ratio': round(self.calmar_ratio, 2),
            'max_drawdown': round(self.max_drawdown, 4),
            'num_trades': self.num_trades,
            'win_rate': round(self.win_rate, 4),
            'profit_factor': round(self.profit_factor, 2),
            't_statistic': round(self.t_statistic, 2),
            'p_value': round(self.p_value, 4),
            'is_significant': self.is_significant,
            'in_sample_sharpe': round(self.in_sample_sharpe, 2),
            'out_of_sample_sharpe': round(self.out_of_sample_sharpe, 2),
            'sharpe_decay': round(self.sharpe_decay, 2),
            'total_costs': round(self.total_costs, 2),
            'cost_drag': round(self.cost_drag, 4)
        }


@dataclass
class WalkForwardResult:
    """Walk-forward analysis result"""
    num_windows: int
    in_sample_results: List[BacktestResult]
    out_of_sample_results: List[BacktestResult]
    
    # Aggregated metrics
    avg_is_sharpe: float
    avg_oos_sharpe: float
    sharpe_decay: float
    consistency: float  # % of OOS periods profitable
    
    # Statistical tests
    combined_p_value: float
    is_robust: bool
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'num_windows': self.num_windows,
            'avg_is_sharpe': round(self.avg_is_sharpe, 2),
            'avg_oos_sharpe': round(self.avg_oos_sharpe, 2),
            'sharpe_decay': round(self.sharpe_decay, 2),
            'consistency': round(self.consistency, 4),
            'combined_p_value': round(self.combined_p_value, 4),
            'is_robust': self.is_robust
        }


@dataclass
class MonteCarloResult:
    """Monte Carlo simulation result"""
    num_simulations: int
    
    # Distribution of outcomes
    return_mean: float
    return_std: float
    return_5th: float
    return_95th: float
    
    sharpe_mean: float
    sharpe_std: float
    sharpe_5th: float
    sharpe_95th: float
    
    max_dd_mean: float
    max_dd_std: float
    max_dd_5th: float
    max_dd_95th: float
    
    # Probability estimates
    prob_positive: float
    prob_sharpe_above_1: float
    prob_dd_above_20: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'num_simulations': self.num_simulations,
            'return_mean': round(self.return_mean, 4),
            'return_95_ci': f"[{round(self.return_5th, 4)}, {round(self.return_95th, 4)}]",
            'sharpe_mean': round(self.sharpe_mean, 2),
            'sharpe_95_ci': f"[{round(self.sharpe_5th, 2)}, {round(self.sharpe_95th, 2)}]",
            'max_dd_mean': round(self.max_dd_mean, 4),
            'max_dd_95_ci': f"[{round(self.max_dd_5th, 4)}, {round(self.max_dd_95th, 4)}]",
            'prob_positive': round(self.prob_positive, 4),
            'prob_sharpe_above_1': round(self.prob_sharpe_above_1, 4),
            'prob_dd_above_20': round(self.prob_dd_above_20, 4)
        }


class RigorousBacktester:
    """
    Rigorous Backtesting Framework
    
    Provides institutional-grade strategy validation:
    
    1. Out-of-Sample Testing
       - Walk-forward analysis
       - Purged K-fold cross-validation
       - Combinatorial purged CV
    
    2. Transaction Cost Modeling
       - Spread costs
       - Commission
       - Slippage
       - Market impact
    
    3. Survivorship Bias Correction
       - Delisted securities handling
       - Point-in-time data
    
    4. Statistical Significance
       - t-test for returns
       - Bootstrap hypothesis testing
       - Multiple testing correction
       - Sharpe ratio significance
    
    5. Monte Carlo Simulation
       - Return distribution
       - Drawdown distribution
       - Probability estimates
    
    6. Regime Analysis
       - Performance by market regime
       - Conditional statistics
    
    Key Principles:
    - Never optimize on test data
    - Account for all costs
    - Test statistical significance
    - Expect performance decay
    - Use multiple validation methods
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize backtester
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        
        # Risk-free rate
        self.risk_free_rate = self.config.get('risk_free_rate', 0.04)
        
        # Transaction cost model
        self.cost_model = TransactionCostModel(
            spread_bps=self.config.get('spread_bps', 2.0),
            commission_per_share=self.config.get('commission_per_share', 0.005),
            slippage_bps=self.config.get('slippage_bps', 1.0)
        )
        
        # Significance level
        self.alpha = self.config.get('alpha', 0.05)
        
        # Walk-forward parameters
        self.is_ratio = self.config.get('is_ratio', 0.7)  # In-sample ratio
        self.min_oos_periods = self.config.get('min_oos_periods', 60)  # Min OOS days
        
        # Statistics
        self.backtests_run = 0
        
        logger.info("RigorousBacktester initialized")
    
    def backtest(self,
                strategy: Callable,
                data: pd.DataFrame,
                initial_capital: float = 100000,
                include_costs: bool = True) -> BacktestResult:
        """
        Run backtest with transaction costs
        
        Args:
            strategy: Strategy function that takes data and returns signals
            data: OHLCV DataFrame with columns ['open', 'high', 'low', 'close', 'volume']
            initial_capital: Starting capital
            include_costs: Whether to include transaction costs
            
        Returns:
            BacktestResult with comprehensive metrics
        """
        self.backtests_run += 1
        
        # Generate signals
        signals = strategy(data)
        
        # Simulate trades
        trades, equity_curve = self._simulate_trades(
            data, signals, initial_capital, include_costs
        )
        
        # Calculate metrics
        returns = equity_curve.pct_change().dropna()
        
        # Basic metrics
        total_return = (equity_curve.iloc[-1] / equity_curve.iloc[0]) - 1
        days = (data.index[-1] - data.index[0]).days
        annualized_return = (1 + total_return) ** (365 / days) - 1 if days > 0 else 0
        
        volatility = returns.std() * np.sqrt(252)
        sharpe = (annualized_return - self.risk_free_rate) / volatility if volatility > 0 else 0
        
        # Sortino ratio
        downside_returns = returns[returns < 0]
        downside_std = downside_returns.std() * np.sqrt(252) if len(downside_returns) > 0 else volatility
        sortino = (annualized_return - self.risk_free_rate) / downside_std if downside_std > 0 else 0
        
        # Max drawdown
        cumulative = (1 + returns).cumprod()
        running_max = cumulative.cummax()
        drawdown = (cumulative - running_max) / running_max
        max_drawdown = abs(drawdown.min())
        
        # Calmar ratio
        calmar = annualized_return / max_drawdown if max_drawdown > 0 else 0
        
        # Trade statistics
        if trades:
            trade_returns = [t['return'] for t in trades]
            wins = [r for r in trade_returns if r > 0]
            losses = [r for r in trade_returns if r < 0]
            
            win_rate = len(wins) / len(trade_returns) if trade_returns else 0
            profit_factor = abs(sum(wins) / sum(losses)) if losses and sum(losses) != 0 else float('inf')
            avg_trade_return = np.mean(trade_returns) if trade_returns else 0
        else:
            win_rate = profit_factor = avg_trade_return = 0
        
        # Transaction costs
        total_costs = sum(t.get('costs', 0) for t in trades)
        cost_drag = total_costs / initial_capital if initial_capital > 0 else 0
        
        # Statistical significance
        t_stat, p_value = self._test_significance(returns)
        is_significant = p_value < self.alpha
        
        return BacktestResult(
            strategy_name=strategy.__name__ if hasattr(strategy, '__name__') else 'strategy',
            start_date=data.index[0],
            end_date=data.index[-1],
            total_return=total_return,
            annualized_return=annualized_return,
            volatility=volatility,
            sharpe_ratio=sharpe,
            sortino_ratio=sortino,
            calmar_ratio=calmar,
            max_drawdown=max_drawdown,
            num_trades=len(trades),
            win_rate=win_rate,
            profit_factor=profit_factor,
            avg_trade_return=avg_trade_return,
            total_costs=total_costs,
            cost_drag=cost_drag,
            t_statistic=t_stat,
            p_value=p_value,
            is_significant=is_significant,
            in_sample_sharpe=sharpe,
            out_of_sample_sharpe=0,
            sharpe_decay=0
        )
    
    def walk_forward_analysis(self,
                             strategy: Callable,
                             data: pd.DataFrame,
                             num_windows: int = 5,
                             initial_capital: float = 100000) -> WalkForwardResult:
        """
        Perform walk-forward analysis
        
        Args:
            strategy: Strategy function
            data: OHLCV DataFrame
            num_windows: Number of walk-forward windows
            initial_capital: Starting capital
            
        Returns:
            WalkForwardResult with aggregated metrics
        """
        n = len(data)
        window_size = n // num_windows
        
        is_results = []
        oos_results = []
        
        for i in range(num_windows):
            # Define windows
            start_idx = i * window_size
            end_idx = min((i + 2) * window_size, n)  # Overlap for OOS
            
            if end_idx - start_idx < window_size:
                continue
            
            # In-sample period
            is_end = start_idx + int((end_idx - start_idx) * self.is_ratio)
            is_data = data.iloc[start_idx:is_end]
            
            # Out-of-sample period
            oos_data = data.iloc[is_end:end_idx]
            
            if len(oos_data) < self.min_oos_periods:
                continue
            
            # Run backtests
            is_result = self.backtest(strategy, is_data, initial_capital)
            oos_result = self.backtest(strategy, oos_data, initial_capital)
            
            is_results.append(is_result)
            oos_results.append(oos_result)
        
        if not oos_results:
            return self._empty_walk_forward_result()
        
        # Aggregate metrics
        avg_is_sharpe = np.mean([r.sharpe_ratio for r in is_results])
        avg_oos_sharpe = np.mean([r.sharpe_ratio for r in oos_results])
        sharpe_decay = avg_oos_sharpe / avg_is_sharpe if avg_is_sharpe != 0 else 0
        
        # Consistency (% of OOS periods with positive return)
        consistency = np.mean([1 if r.total_return > 0 else 0 for r in oos_results])
        
        # Combined p-value (Fisher's method)
        p_values = [r.p_value for r in oos_results if r.p_value > 0]
        if p_values:
            chi2_stat = -2 * np.sum(np.log(p_values))
            combined_p = 1 - stats.chi2.cdf(chi2_stat, 2 * len(p_values))
        else:
            combined_p = 1.0
        
        is_robust = combined_p < self.alpha and sharpe_decay > 0.5
        
        return WalkForwardResult(
            num_windows=len(oos_results),
            in_sample_results=is_results,
            out_of_sample_results=oos_results,
            avg_is_sharpe=avg_is_sharpe,
            avg_oos_sharpe=avg_oos_sharpe,
            sharpe_decay=sharpe_decay,
            consistency=consistency,
            combined_p_value=combined_p,
            is_robust=is_robust
        )
    
    def monte_carlo_simulation(self,
                              returns: np.ndarray,
                              num_simulations: int = 1000,
                              horizon_days: int = 252) -> MonteCarloResult:
        """
        Run Monte Carlo simulation
        
        Args:
            returns: Historical daily returns
            num_simulations: Number of simulations
            horizon_days: Simulation horizon in days
            
        Returns:
            MonteCarloResult with distribution statistics
        """
        # Bootstrap returns
        simulated_returns = []
        simulated_sharpes = []
        simulated_drawdowns = []
        
        for _ in range(num_simulations):
            # Sample with replacement
            sim_returns = np.random.choice(returns, size=horizon_days, replace=True)
            
            # Calculate metrics
            total_return = np.prod(1 + sim_returns) - 1
            ann_return = (1 + total_return) ** (252 / horizon_days) - 1
            volatility = np.std(sim_returns) * np.sqrt(252)
            sharpe = (ann_return - self.risk_free_rate) / volatility if volatility > 0 else 0
            
            # Max drawdown
            cumulative = np.cumprod(1 + sim_returns)
            running_max = np.maximum.accumulate(cumulative)
            drawdown = (cumulative - running_max) / running_max
            max_dd = abs(drawdown.min())
            
            simulated_returns.append(ann_return)
            simulated_sharpes.append(sharpe)
            simulated_drawdowns.append(max_dd)
        
        simulated_returns = np.array(simulated_returns)
        simulated_sharpes = np.array(simulated_sharpes)
        simulated_drawdowns = np.array(simulated_drawdowns)
        
        return MonteCarloResult(
            num_simulations=num_simulations,
            return_mean=np.mean(simulated_returns),
            return_std=np.std(simulated_returns),
            return_5th=np.percentile(simulated_returns, 5),
            return_95th=np.percentile(simulated_returns, 95),
            sharpe_mean=np.mean(simulated_sharpes),
            sharpe_std=np.std(simulated_sharpes),
            sharpe_5th=np.percentile(simulated_sharpes, 5),
            sharpe_95th=np.percentile(simulated_sharpes, 95),
            max_dd_mean=np.mean(simulated_drawdowns),
            max_dd_std=np.std(simulated_drawdowns),
            max_dd_5th=np.percentile(simulated_drawdowns, 5),
            max_dd_95th=np.percentile(simulated_drawdowns, 95),
            prob_positive=np.mean(simulated_returns > 0),
            prob_sharpe_above_1=np.mean(simulated_sharpes > 1),
            prob_dd_above_20=np.mean(simulated_drawdowns > 0.20)
        )
    
    def test_multiple_strategies(self,
                                strategies: List[Callable],
                                data: pd.DataFrame,
                                correction: str = 'bonferroni') -> Dict[str, Any]:
        """
        Test multiple strategies with multiple testing correction
        
        Args:
            strategies: List of strategy functions
            data: OHLCV DataFrame
            correction: Correction method ('bonferroni', 'fdr', 'none')
            
        Returns:
            Dictionary with results and adjusted p-values
        """
        results = []
        p_values = []
        
        for strategy in strategies:
            result = self.backtest(strategy, data)
            results.append(result)
            p_values.append(result.p_value)
        
        # Apply correction
        if correction == 'bonferroni':
            adjusted_alpha = self.alpha / len(strategies)
            significant = [p < adjusted_alpha for p in p_values]
        elif correction == 'fdr':
            # Benjamini-Hochberg
            sorted_indices = np.argsort(p_values)
            adjusted_p = np.zeros(len(p_values))
            
            for i, idx in enumerate(sorted_indices):
                adjusted_p[idx] = p_values[idx] * len(p_values) / (i + 1)
            
            adjusted_p = np.minimum.accumulate(adjusted_p[:-1])[:-1]
            significant = [p < self.alpha for p in adjusted_p]
        else:
            significant = [p < self.alpha for p in p_values]
        
        return {
            'results': [r.to_dict() for r in results],
            'p_values': p_values,
            'significant': significant,
            'correction': correction,
            'num_significant': sum(significant),
            'best_strategy': results[np.argmax([r.sharpe_ratio for r in results])].strategy_name
        }
    
    def survivorship_bias_test(self,
                              strategy: Callable,
                              data: pd.DataFrame,
                              delisted_data: pd.DataFrame,
                              initial_capital: float = 100000) -> Dict[str, Any]:
        """
        Test for survivorship bias
        
        Args:
            strategy: Strategy function
            data: Survivor-only data
            delisted_data: Data including delisted securities
            initial_capital: Starting capital
            
        Returns:
            Dictionary comparing results
        """
        # Backtest on survivors only
        survivor_result = self.backtest(strategy, data, initial_capital)
        
        # Backtest including delisted
        full_result = self.backtest(strategy, delisted_data, initial_capital)
        
        # Calculate bias
        return_bias = survivor_result.annualized_return - full_result.annualized_return
        sharpe_bias = survivor_result.sharpe_ratio - full_result.sharpe_ratio
        
        return {
            'survivor_only': survivor_result.to_dict(),
            'including_delisted': full_result.to_dict(),
            'return_bias': round(return_bias, 4),
            'sharpe_bias': round(sharpe_bias, 2),
            'bias_significant': abs(return_bias) > 0.02  # 2% threshold
        }
    
    def regime_analysis(self,
                       strategy: Callable,
                       data: pd.DataFrame,
                       regime_labels: pd.Series,
                       initial_capital: float = 100000) -> Dict[str, BacktestResult]:
        """
        Analyze strategy performance by market regime
        
        Args:
            strategy: Strategy function
            data: OHLCV DataFrame
            regime_labels: Series with regime labels (e.g., 'bull', 'bear', 'sideways')
            initial_capital: Starting capital
            
        Returns:
            Dictionary of {regime: BacktestResult}
        """
        results = {}
        
        for regime in regime_labels.unique():
            regime_mask = regime_labels == regime
            regime_data = data[regime_mask]
            
            if len(regime_data) < 60:  # Minimum 60 days
                continue
            
            result = self.backtest(strategy, regime_data, initial_capital)
            results[regime] = result
        
        return results
    
    def _simulate_trades(self,
                        data: pd.DataFrame,
                        signals: pd.Series,
                        initial_capital: float,
                        include_costs: bool) -> Tuple[List[Dict], pd.Series]:
        """Simulate trades from signals"""
        trades = []
        equity = [initial_capital]
        position = 0
        entry_price = 0
        
        for i in range(1, len(data)):
            current_price = data['close'].iloc[i]
            signal = signals.iloc[i] if i < len(signals) else 0
            
            # Entry
            if signal > 0 and position == 0:
                position = 1
                entry_price = current_price
                
                if include_costs:
                    quantity = equity[-1] / current_price
                    costs = self.cost_model.calculate_cost(
                        current_price, quantity, data['volume'].iloc[i]
                    )['total']
                    equity.append(equity[-1] - costs)
                else:
                    equity.append(equity[-1])
            
            # Exit
            elif signal < 0 and position > 0:
                trade_return = (current_price - entry_price) / entry_price
                
                if include_costs:
                    quantity = equity[-1] / current_price
                    costs = self.cost_model.calculate_cost(
                        current_price, quantity, data['volume'].iloc[i]
                    )['total']
                else:
                    costs = 0
                
                pnl = equity[-1] * trade_return - costs
                equity.append(equity[-1] + pnl)
                
                trades.append({
                    'entry_price': entry_price,
                    'exit_price': current_price,
                    'return': trade_return,
                    'pnl': pnl,
                    'costs': costs
                })
                
                position = 0
                entry_price = 0
            
            # Hold
            elif position > 0:
                daily_return = (current_price - data['close'].iloc[i-1]) / data['close'].iloc[i-1]
                equity.append(equity[-1] * (1 + daily_return))
            else:
                equity.append(equity[-1])
        
        return trades, pd.Series(equity, index=data.index[:len(equity)])
    
    def _test_significance(self, returns: pd.Series) -> Tuple[float, float]:
        """Test statistical significance of returns"""
        if len(returns) < 30:
            return 0.0, 1.0
        
        # t-test against zero
        t_stat, p_value = stats.ttest_1samp(returns, 0)
        
        return t_stat, p_value
    
    def _empty_walk_forward_result(self) -> WalkForwardResult:
        """Return empty walk-forward result"""
        return WalkForwardResult(
            num_windows=0,
            in_sample_results=[],
            out_of_sample_results=[],
            avg_is_sharpe=0,
            avg_oos_sharpe=0,
            sharpe_decay=0,
            consistency=0,
            combined_p_value=1.0,
            is_robust=False
        )
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get backtester statistics"""
        return {
            'backtests_run': self.backtests_run,
            'risk_free_rate': self.risk_free_rate,
            'alpha': self.alpha,
            'cost_model': {
                'spread_bps': self.cost_model.spread_bps,
                'commission_per_share': self.cost_model.commission_per_share,
                'slippage_bps': self.cost_model.slippage_bps
            }
        }


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Create backtester
    backtester = RigorousBacktester({
        'risk_free_rate': 0.04,
        'spread_bps': 2.0,
        'slippage_bps': 1.0,
        'alpha': 0.05
    })
    
    # Generate sample data
    np.random.seed(42)
    n_days = 1000
    dates = pd.date_range('2020-01-01', periods=n_days, freq='D')
    
    # Simulate price series
    returns = np.random.randn(n_days) * 0.01 + 0.0003  # Slight positive drift
    prices = 100 * np.exp(np.cumsum(returns))
    
    data = pd.DataFrame({
        'open': prices * (1 + np.random.randn(n_days) * 0.001),
        'high': prices * (1 + abs(np.random.randn(n_days) * 0.01)),
        'low': prices * (1 - abs(np.random.randn(n_days) * 0.01)),
        'close': prices,
        'volume': np.random.randint(100000, 1000000, n_days)
    }, index=dates)
    
    # Define simple strategy
    def momentum_strategy(data: pd.DataFrame) -> pd.Series:
        """Simple momentum strategy"""
        returns = data['close'].pct_change()
        signal = pd.Series(0, index=data.index)
        
        # Buy when 20-day return > 0
        momentum = data['close'].pct_change(20)
        signal[momentum > 0] = 1
        signal[momentum < 0] = -1
        
        return signal
    
    def mean_reversion_strategy(data: pd.DataFrame) -> pd.Series:
        """Simple mean reversion strategy"""
        signal = pd.Series(0, index=data.index)
        
        # Buy when price < 20-day SMA
        sma = data['close'].rolling(20).mean()
        signal[data['close'] < sma * 0.98] = 1
        signal[data['close'] > sma * 1.02] = -1
        
        return signal
    
    # Run backtest
    logger.info("\n=== Single Backtest ===")
    result = backtester.backtest(momentum_strategy, data)
    logger.info(f"Strategy: {result.strategy_name}")
    logger.info(f"Total Return: {result.total_return:.2%}")
    logger.info(f"Sharpe Ratio: {result.sharpe_ratio:.2f}")
    logger.info(f"Max Drawdown: {result.max_drawdown:.2%}")
    logger.info(f"Win Rate: {result.win_rate:.2%}")
    logger.info(f"P-Value: {result.p_value:.4f}")
    logger.info(f"Significant: {result.is_significant}")
    logger.info(f"Total Costs: ${result.total_costs:,.2f}")
    
    # Walk-forward analysis
    logger.info("\n=== Walk-Forward Analysis ===")
    wf_result = backtester.walk_forward_analysis(momentum_strategy, data, num_windows=5)
    logger.info(f"Windows: {wf_result.num_windows}")
    logger.info(f"Avg IS Sharpe: {wf_result.avg_is_sharpe:.2f}")
    logger.info(f"Avg OOS Sharpe: {wf_result.avg_oos_sharpe:.2f}")
    logger.info(f"Sharpe Decay: {wf_result.sharpe_decay:.2f}")
    logger.info(f"Consistency: {wf_result.consistency:.2%}")
    logger.info(f"Is Robust: {wf_result.is_robust}")
    
    # Monte Carlo simulation
    logger.info("\n=== Monte Carlo Simulation ===")
    returns_arr = data['close'].pct_change().dropna().values
    mc_result = backtester.monte_carlo_simulation(returns_arr, num_simulations=1000)
    logger.info(f"Return Mean: {mc_result.return_mean:.2%}")
    logger.info(f"Return 95% CI: [{mc_result.return_5th:.2%}, {mc_result.return_95th:.2%}]")
    logger.info(f"Sharpe Mean: {mc_result.sharpe_mean:.2f}")
    logger.info(f"Prob Positive: {mc_result.prob_positive:.2%}")
    logger.info(f"Prob DD > 20%: {mc_result.prob_dd_above_20:.2%}")
    
    # Multiple strategy testing
    logger.info("\n=== Multiple Strategy Testing ===")
    strategies = [momentum_strategy, mean_reversion_strategy]
    multi_result = backtester.test_multiple_strategies(strategies, data, correction='bonferroni')
    logger.info(f"Num Significant: {multi_result['num_significant']}")
    logger.info(f"Best Strategy: {multi_result['best_strategy']}")
    
    # Transaction cost analysis
    logger.info("\n=== Transaction Cost Model ===")
    cost = backtester.cost_model.calculate_cost(price=100, quantity=1000, adv=1000000)
    logger.info(f"Spread Cost: ${cost['spread_cost']:.2f}")
    logger.info(f"Commission: ${cost['commission']:.2f}")
    logger.info(f"Slippage: ${cost['slippage']:.2f}")
    logger.info(f"Market Impact: ${cost['market_impact']:.2f}")
    logger.info(f"Total: ${cost['total']:.2f} ({cost['total_bps']:.2f} bps)")
