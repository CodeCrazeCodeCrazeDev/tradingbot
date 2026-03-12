"""
Free Research & Innovation Lab ($0 Budget)
Uses free tools and local testing
"""

import numpy as np
from typing import Callable, Dict, List
from dataclasses import dataclass
from datetime import datetime
import json
import os
import numpy

import logging
logger = logging.getLogger(__name__)



@dataclass
class FreeStrategy:
    """Free experimental strategy"""
    strategy_id: str
    name: str
    code: Callable
    parameters: Dict
    performance: Dict


class FreeBacktester:
    """Free backtesting using numpy"""
    
    def __init__(self):
        self.results: Dict[str, Dict] = {}
        
    def backtest(
        self,
        strategy_func: Callable,
        prices: np.ndarray,
        initial_capital: float = 10000,
        commission: float = 0.001
    ) -> Dict:
        """Run free backtest"""
        
        # Generate signals
        signals = strategy_func(prices)
        
        # Simulate trading
        capital = initial_capital
        position = 0
        trades = []
        equity_curve = [initial_capital]
        
        for i in range(1, len(prices)):
            # Entry
            if signals[i] > 0 and position == 0:
                # Buy
                shares = (capital * 0.95) / prices[i]  # 95% of capital
                cost = shares * prices[i] * (1 + commission)
                
                if cost <= capital:
                    position = shares
                    capital -= cost
                    trades.append({
                        'type': 'buy',
                        'price': prices[i],
                        'shares': shares,
                        'index': i
                    })
            
            # Exit
            elif signals[i] < 0 and position > 0:
                # Sell
                proceeds = position * prices[i] * (1 - commission)
                capital += proceeds
                
                trades.append({
                    'type': 'sell',
                    'price': prices[i],
                    'shares': position,
                    'index': i,
                    'pnl': proceeds - trades[-1]['price'] * position
                })
                
                position = 0
            
            # Update equity
            equity = capital + (position * prices[i] if position > 0 else 0)
            equity_curve.append(equity)
        
        # Calculate metrics
        final_equity = equity_curve[-1]
        total_return = (final_equity - initial_capital) / initial_capital
        
        # Returns
        returns = np.diff(equity_curve) / equity_curve[:-1]
        
        # Sharpe ratio
        sharpe = np.mean(returns) / np.std(returns) * np.sqrt(252) if np.std(returns) > 0 else 0
        
        # Max drawdown
        peak = np.maximum.accumulate(equity_curve)
        drawdown = (np.array(equity_curve) - peak) / peak
        max_drawdown = np.min(drawdown)
        
        # Win rate
        winning_trades = [t for t in trades if t.get('pnl', 0) > 0]
        win_rate = len(winning_trades) / len(trades) if trades else 0
        
        result = {
            'total_return': total_return,
            'sharpe_ratio': sharpe,
            'max_drawdown': max_drawdown,
            'win_rate': win_rate,
            'num_trades': len(trades),
            'final_equity': final_equity,
            'equity_curve': equity_curve,
            'cost': 0  # Free
        }
        
        return result
    
    def walk_forward_test(
        self,
        strategy_func: Callable,
        prices: np.ndarray,
        train_size: int = 100,
        test_size: int = 20
    ) -> Dict:
        """Free walk-forward testing"""
        
        results = []
        
        for i in range(0, len(prices) - train_size - test_size, test_size):
            # Train period (not used in simple strategies)
            train_data = prices[i:i+train_size]
            
            # Test period
            test_data = prices[i+train_size:i+train_size+test_size]
            
            # Backtest on test period
            result = self.backtest(strategy_func, test_data, initial_capital=10000)
            results.append(result['total_return'])
        
        return {
            'avg_return': np.mean(results),
            'std_return': np.std(results),
            'num_periods': len(results),
            'consistency': 1 - np.std(results),  # Higher is better
            'cost': 0
        }


class FreePaperTrading:
    """Free paper trading simulator"""
    
    def __init__(self):
        self.trades: List[Dict] = []
        self.positions: Dict[str, Dict] = {}
        self.capital = 10000
        self.initial_capital = 10000
        
    def execute_trade(
        self,
        symbol: str,
        side: str,
        quantity: float,
        price: float
    ) -> Dict:
        """Execute paper trade (free)"""
        
        trade_id = f"paper_{len(self.trades) + 1}"
        
        if side == 'buy':
            cost = quantity * price
            if cost <= self.capital:
                self.capital -= cost
                self.positions[symbol] = {
                    'quantity': quantity,
                    'entry_price': price,
                    'entry_time': datetime.now()
                }
                
                trade = {
                    'trade_id': trade_id,
                    'symbol': symbol,
                    'side': side,
                    'quantity': quantity,
                    'price': price,
                    'cost': cost,
                    'timestamp': datetime.now(),
                    'status': 'filled'
                }
                self.trades.append(trade)
                return trade
            else:
                return {'error': 'Insufficient capital'}
        
        elif side == 'sell':
            if symbol in self.positions:
                pos = self.positions[symbol]
                proceeds = quantity * price
                pnl = (price - pos['entry_price']) * quantity
                
                self.capital += proceeds
                del self.positions[symbol]
                
                trade = {
                    'trade_id': trade_id,
                    'symbol': symbol,
                    'side': side,
                    'quantity': quantity,
                    'price': price,
                    'proceeds': proceeds,
                    'pnl': pnl,
                    'return': pnl / (pos['entry_price'] * quantity),
                    'timestamp': datetime.now(),
                    'status': 'filled'
                }
                self.trades.append(trade)
                return trade
            else:
                return {'error': 'No position to sell'}
    
    def get_performance(self) -> Dict:
        """Get paper trading performance"""
        
        total_pnl = sum(t.get('pnl', 0) for t in self.trades if 'pnl' in t)
        total_return = total_pnl / self.initial_capital
        
        winning_trades = [t for t in self.trades if t.get('pnl', 0) > 0]
        win_rate = len(winning_trades) / len(self.trades) if self.trades else 0
        
        return {
            'total_pnl': total_pnl,
            'total_return': total_return,
            'win_rate': win_rate,
            'num_trades': len(self.trades),
            'current_capital': self.capital,
            'open_positions': len(self.positions),
            'cost': 0
        }


class FreeABTesting:
    """Free A/B testing framework"""
    
    def __init__(self):
        self.experiments: Dict[str, Dict] = {}
        
    def create_experiment(
        self,
        name: str,
        control_strategy: Callable,
        test_strategy: Callable
    ) -> str:
        """Create A/B test (free)"""
        
        experiment_id = f"exp_{name.lower().replace(' ', '_')}"
        
        self.experiments[experiment_id] = {
            'name': name,
            'control': control_strategy,
            'test': test_strategy,
            'control_results': [],
            'test_results': [],
            'created': datetime.now()
        }
        
        return experiment_id
    
    def run_experiment(
        self,
        experiment_id: str,
        test_data: np.ndarray,
        num_runs: int = 10
    ) -> Dict:
        """Run A/B test (free)"""
        
        if experiment_id not in self.experiments:
            return {'error': 'Experiment not found'}
        
        exp = self.experiments[experiment_id]
        backtester = FreeBacktester()
        
        # Run control
        for _ in range(num_runs):
            result = backtester.backtest(exp['control'], test_data)
            exp['control_results'].append(result['total_return'])
        
        # Run test
        for _ in range(num_runs):
            result = backtester.backtest(exp['test'], test_data)
            exp['test_results'].append(result['total_return'])
        
        # Analyze
        control_mean = np.mean(exp['control_results'])
        test_mean = np.mean(exp['test_results'])
        
        improvement = (test_mean - control_mean) / abs(control_mean) if control_mean != 0 else 0
        
        # Simple significance test
        significant = abs(improvement) > 0.05  # 5% threshold
        
        return {
            'experiment_id': experiment_id,
            'control_mean': control_mean,
            'test_mean': test_mean,
            'improvement': improvement,
            'significant': significant,
            'winner': 'test' if test_mean > control_mean else 'control',
            'cost': 0
        }


class FreeStrategyLibrary:
    """Free strategy library"""
    
    @staticmethod
    def simple_ma_crossover(prices: np.ndarray, fast: int = 10, slow: int = 30) -> np.ndarray:
        """Simple moving average crossover (free)"""
        signals = np.zeros(len(prices))
        
        if len(prices) < slow:
            return signals
        
        # Calculate MAs
        fast_ma = np.convolve(prices, np.ones(fast)/fast, mode='valid')
        slow_ma = np.convolve(prices, np.ones(slow)/slow, mode='valid')
        
        # Align arrays
        min_len = min(len(fast_ma), len(slow_ma))
        fast_ma = fast_ma[:min_len]
        slow_ma = slow_ma[:min_len]
        
        # Generate signals
        for i in range(1, min_len):
            if fast_ma[i] > slow_ma[i] and fast_ma[i-1] <= slow_ma[i-1]:
                signals[i + slow - 1] = 1  # Buy
            elif fast_ma[i] < slow_ma[i] and fast_ma[i-1] >= slow_ma[i-1]:
                signals[i + slow - 1] = -1  # Sell
        
        return signals
    
    @staticmethod
    def momentum_strategy(prices: np.ndarray, lookback: int = 20, threshold: float = 0.02) -> np.ndarray:
        """Momentum strategy (free)"""
        signals = np.zeros(len(prices))
        
        for i in range(lookback, len(prices)):
            returns = (prices[i] - prices[i-lookback]) / prices[i-lookback]
            
            if returns > threshold:
                signals[i] = 1  # Buy
            elif returns < -threshold:
                signals[i] = -1  # Sell
        
        return signals
    
    @staticmethod
    def mean_reversion(prices: np.ndarray, window: int = 20, std_dev: float = 2.0) -> np.ndarray:
        """Mean reversion strategy (free)"""
        signals = np.zeros(len(prices))
        
        for i in range(window, len(prices)):
            window_data = prices[i-window:i]
            mean = np.mean(window_data)
            std = np.std(window_data)
            
            z_score = (prices[i] - mean) / std if std > 0 else 0
            
            if z_score < -std_dev:
                signals[i] = 1  # Buy (oversold)
            elif z_score > std_dev:
                signals[i] = -1  # Sell (overbought)
        
        return signals


class FreeResearchLab:
    """Free unified research lab"""
    
    def __init__(self):
        self.backtester = FreeBacktester()
        self.paper_trading = FreePaperTrading()
        self.ab_testing = FreeABTesting()
        self.strategy_library = FreeStrategyLibrary()
        self.results_dir = './research_results'
        
        # Create results directory
        os.makedirs(self.results_dir, exist_ok=True)
        
    def test_strategy(
        self,
        strategy_name: str,
        strategy_func: Callable,
        test_data: np.ndarray
    ) -> Dict:
        """Complete strategy testing (free)"""
        
        # 1. Backtest
        backtest_result = self.backtester.backtest(strategy_func, test_data)
        
        # 2. Walk-forward test
        wf_result = self.backtester.walk_forward_test(strategy_func, test_data)
        
        # 3. Decision
        approved = (
            backtest_result['sharpe_ratio'] > 1.0 and
            backtest_result['win_rate'] > 0.5 and
            backtest_result['max_drawdown'] > -0.25
        )
        
        result = {
            'strategy_name': strategy_name,
            'backtest': backtest_result,
            'walk_forward': wf_result,
            'approved': approved,
            'recommendation': 'deploy' if approved else 'reject',
            'cost': 0,
            'timestamp': datetime.now()
        }
        
        # Save results
        self._save_results(strategy_name, result)
        
        return result
    
    def compare_strategies(
        self,
        strategies: Dict[str, Callable],
        test_data: np.ndarray
    ) -> Dict:
        """Compare multiple strategies (free)"""
        
        results = {}
        
        for name, strategy_func in strategies.items():
            backtest_result = self.backtester.backtest(strategy_func, test_data)
            results[name] = {
                'return': backtest_result['total_return'],
                'sharpe': backtest_result['sharpe_ratio'],
                'win_rate': backtest_result['win_rate']
            }
        
        # Rank by Sharpe ratio
        ranked = sorted(results.items(), key=lambda x: x[1]['sharpe'], reverse=True)
        
        return {
            'results': results,
            'ranked': ranked,
            'best_strategy': ranked[0][0] if ranked else None,
            'cost': 0
        }
    
    def _save_results(self, strategy_name: str, results: Dict):
        """Save results to file (free)"""
        
        filename = f"{strategy_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = os.path.join(self.results_dir, filename)
        
        # Convert numpy arrays to lists for JSON serialization
        def convert(obj):
            if isinstance(obj, np.ndarray):
                return obj.tolist()
            elif isinstance(obj, datetime):
                return obj.isoformat()
            return obj
        
        with open(filepath, 'w') as f:
            json.dump(results, f, indent=2, default=convert)


# Example usage
if __name__ == '__main__':
    # Initialize free research lab
    lab = FreeResearchLab()
    
    # Generate test data
    np.random.seed(42)
    test_prices = np.cumsum(np.random.randn(500) * 0.01) + 100
    
    # Test strategies
    strategies = {
        'MA Crossover': lambda p: lab.strategy_library.simple_ma_crossover(p),
        'Momentum': lambda p: lab.strategy_library.momentum_strategy(p),
        'Mean Reversion': lambda p: lab.strategy_library.mean_reversion(p)
    }
    
    logger.info("Free Research Lab Results:\n")
    
    # Compare strategies
    comparison = lab.compare_strategies(strategies, test_prices)
    
    logger.info("Strategy Comparison:")
    for rank, (name, metrics) in enumerate(comparison['ranked'], 1):
        logger.info(f"\n{rank}. {name}")
        logger.info(f"   Return: {metrics['return']:.2%}")
        logger.info(f"   Sharpe: {metrics['sharpe']:.2f}")
        logger.info(f"   Win Rate: {metrics['win_rate']:.2%}")
    
    logger.info(f"\nBest Strategy: {comparison['best_strategy']}")
    logger.info(f"Total Cost: ${comparison['cost']}")
    
    # Test best strategy
    best_strategy = strategies[comparison['best_strategy']]
    result = lab.test_strategy(comparison['best_strategy'], best_strategy, test_prices)
    
    logger.info(f"\nDetailed Test - {comparison['best_strategy']}:")
    logger.info(f"  Approved: {result['approved']}")
    logger.info(f"  Recommendation: {result['recommendation']}")
    logger.info(f"  Walk-Forward Avg Return: {result['walk_forward']['avg_return']:.2%}")
    logger.info(f"  Consistency: {result['walk_forward']['consistency']:.2%}")
