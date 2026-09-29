"""
Research & Innovation Lab
Implements experimental strategies, A/B testing, backtesting framework, paper trading
"""

import numpy as np
from typing import Callable, Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import asyncio
from collections import defaultdict
import random
import numpy

import logging

# Evolution: Added retry decorator
def retry(max_attempts=3, delay=1.0):
    """Retry decorator for resilient operations"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    if attempt < max_attempts - 1:
                        await asyncio.sleep(delay * (attempt + 1))
            raise last_error
        return wrapper
    return decorator


logger = logging.getLogger(__name__)



@dataclass
class ExperimentalStrategy:
    """Experimental trading strategy"""
    strategy_id: str
    name: str
    description: str
    code: Callable
    parameters: Dict
    risk_level: str  # 'low', 'medium', 'high'
    status: str  # 'draft', 'testing', 'approved', 'rejected'
    created_at: datetime
    performance: Optional[Dict] = None


@dataclass
class ABTestVariant:
    """A/B test variant"""
    variant_id: str
    name: str
    strategy: ExperimentalStrategy
    allocation: float  # 0-1
    traffic_percentage: float
    metrics: Dict


@dataclass
class BacktestResult:
    """Backtest result"""
    strategy_id: str
    start_date: datetime
    end_date: datetime
    total_return: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    num_trades: int
    avg_trade_duration: float
    profit_factor: float


@dataclass
class PaperTrade:
    """Paper trading record"""
    trade_id: str
    strategy_id: str
    symbol: str
    direction: str
    entry_price: float
    exit_price: Optional[float]
    size: float
    entry_time: datetime
    exit_time: Optional[datetime]
    pnl: Optional[float]
    status: str  # 'open', 'closed'


class ExperimentalStrategyLab:
    """Laboratory for experimental trading strategies"""
    
    def __init__(self):
        self.strategies: Dict[str, ExperimentalStrategy] = {}
        self.experiment_results: Dict[str, List[Dict]] = defaultdict(list)
        
    def register_strategy(
        self,
        name: str,
        description: str,
        code: Callable,
        parameters: Dict,
        risk_level: str = 'medium'
    ) -> str:
        """Register new experimental strategy"""
        
        strategy_id = f"exp_{name.lower().replace(' ', '_')}_{int(datetime.now().timestamp())}"
        
        strategy = ExperimentalStrategy(
            strategy_id=strategy_id,
            name=name,
            description=description,
            code=code,
            parameters=parameters,
            risk_level=risk_level,
            status='draft',
            created_at=datetime.now()
        )
        
        self.strategies[strategy_id] = strategy
        return strategy_id
    
    async def test_strategy(
        self,
        strategy_id: str,
        market_data: np.ndarray,
        initial_capital: float = 10000
    ) -> Dict:
        """Test experimental strategy on data"""
        
        if strategy_id not in self.strategies:
            return {'error': 'Strategy not found'}
        
        strategy = self.strategies[strategy_id]
        
        # Run strategy
        try:
            signals = strategy.code(market_data, **strategy.parameters)
            
            # Simulate trading
            capital = initial_capital
            positions = []
            trades = []
            
            for i, signal in enumerate(signals):
                if signal > 0 and len(positions) == 0:  # Buy
                    positions.append({
                        'entry_price': market_data[i],
                        'entry_idx': i,
                        'size': capital * 0.1  # 10% position
                    })
                elif signal < 0 and len(positions) > 0:  # Sell
                    for pos in positions:
                        pnl = (market_data[i] - pos['entry_price']) * pos['size'] / pos['entry_price']
                        capital += pnl
                        trades.append({
                            'entry': pos['entry_price'],
                            'exit': market_data[i],
                            'pnl': pnl,
                            'duration': i - pos['entry_idx']
                        })
                    positions = []
            
            # Calculate metrics
            total_return = (capital - initial_capital) / initial_capital
            win_rate = sum(1 for t in trades if t['pnl'] > 0) / len(trades) if trades else 0
            
            result = {
                'strategy_id': strategy_id,
                'total_return': total_return,
                'final_capital': capital,
                'num_trades': len(trades),
                'win_rate': win_rate,
                'trades': trades
            }
            
            # Store result
            self.experiment_results[strategy_id].append(result)
            strategy.performance = result
            
            return result
            
        except Exception as e:
            return {'error': str(e)}
    
    def compare_strategies(
        self,
        strategy_ids: List[str]
    ) -> Dict:
        """Compare multiple experimental strategies"""
        
        comparison = {}
        
        for strategy_id in strategy_ids:
            if strategy_id not in self.strategies:
                continue
            
            strategy = self.strategies[strategy_id]
            results = self.experiment_results.get(strategy_id, [])
            
            if results:
                avg_return = np.mean([r['total_return'] for r in results])
                avg_win_rate = np.mean([r['win_rate'] for r in results])
                
                comparison[strategy_id] = {
                    'name': strategy.name,
                    'avg_return': avg_return,
                    'avg_win_rate': avg_win_rate,
                    'num_tests': len(results),
                    'risk_level': strategy.risk_level
                }
        
        # Rank strategies
        ranked = sorted(
            comparison.items(),
            key=lambda x: x[1]['avg_return'],
            reverse=True
        )
        
        return {
            'comparison': comparison,
            'ranked': ranked,
            'best_strategy': ranked[0][0] if ranked else None
        }
    
    def approve_strategy(self, strategy_id: str) -> bool:
        """Approve strategy for production"""
        if strategy_id in self.strategies:
            self.strategies[strategy_id].status = 'approved'
            return True
        return False


class ABTestingFramework:
    """A/B testing framework for strategies"""
    
    def __init__(self):
        self.experiments: Dict[str, Dict] = {}
        self.variants: Dict[str, List[ABTestVariant]] = defaultdict(list)
        self.results: Dict[str, Dict] = defaultdict(dict)
        
    def create_experiment(
        self,
        experiment_name: str,
        control_strategy: ExperimentalStrategy,
        test_strategies: List[ExperimentalStrategy],
        duration_days: int = 30
    ) -> str:
        """Create A/B test experiment"""
        
        experiment_id = f"exp_{experiment_name.lower().replace(' ', '_')}"
        
        # Create control variant
        control = ABTestVariant(
            variant_id=f"{experiment_id}_control",
            name="Control",
            strategy=control_strategy,
            allocation=0.5,
            traffic_percentage=50.0,
            metrics={}
        )
        
        # Create test variants
        test_allocation = 0.5 / len(test_strategies)
        test_variants = []
        
        for i, strategy in enumerate(test_strategies):
            variant = ABTestVariant(
                variant_id=f"{experiment_id}_test_{i}",
                name=f"Test {i+1}",
                strategy=strategy,
                allocation=test_allocation,
                traffic_percentage=test_allocation * 100,
                metrics={}
            )
            test_variants.append(variant)
        
        # Store experiment
        self.experiments[experiment_id] = {
            'name': experiment_name,
            'start_date': datetime.now(),
            'end_date': datetime.now() + timedelta(days=duration_days),
            'status': 'running'
        }
        
        self.variants[experiment_id] = [control] + test_variants
        
        return experiment_id
    
    async def route_trade(
        self,
        experiment_id: str,
        trade: Dict
    ) -> str:
        """Route trade to variant based on allocation"""
        
        if experiment_id not in self.variants:
            return 'control'
        
        variants = self.variants[experiment_id]
        
        # Random assignment based on allocation
        rand = random.random()
        cumulative = 0
        
        for variant in variants:
            cumulative += variant.allocation
            if rand <= cumulative:
                return variant.variant_id
        
        return variants[0].variant_id  # Default to control
    
    async def record_result(
        self,
        experiment_id: str,
        variant_id: str,
        metrics: Dict
    ):
        """Record experiment result"""
        
        if experiment_id not in self.results:
            self.results[experiment_id] = defaultdict(list)
        
        self.results[experiment_id][variant_id].append({
            'metrics': metrics,
            'timestamp': datetime.now()
        })
    
    def analyze_experiment(
        self,
        experiment_id: str
    ) -> Dict:
        """Analyze A/B test results"""
        
        if experiment_id not in self.results:
            return {'error': 'No results found'}
        
        analysis = {}
        
        for variant_id, results in self.results[experiment_id].items():
            if not results:
                continue
            
            # Aggregate metrics
            returns = [r['metrics'].get('return', 0) for r in results]
            win_rates = [r['metrics'].get('win_rate', 0) for r in results]
            
            analysis[variant_id] = {
                'num_samples': len(results),
                'avg_return': np.mean(returns),
                'std_return': np.std(returns),
                'avg_win_rate': np.mean(win_rates),
                'confidence_95': 1.96 * np.std(returns) / np.sqrt(len(returns))
            }
        
        # Determine winner
        winner = max(
            analysis.items(),
            key=lambda x: x[1]['avg_return']
        )[0] if analysis else None
        
        # Statistical significance test (simplified)
        if len(analysis) >= 2:
            variants = list(analysis.keys())
            control_return = analysis[variants[0]]['avg_return']
            test_return = analysis[variants[1]]['avg_return']
            
            improvement = (test_return - control_return) / abs(control_return) if control_return != 0 else 0
            
            analysis['statistical_significance'] = {
                'improvement': improvement,
                'significant': abs(improvement) > 0.05  # 5% threshold
            }
        
        return {
            'experiment_id': experiment_id,
            'analysis': analysis,
            'winner': winner,
            'timestamp': datetime.now()
        }


class AdvancedBacktester:
    """Advanced backtesting framework"""
    
    def __init__(self):
        self.backtest_results: Dict[str, BacktestResult] = {}
        
    async def run_backtest(
        self,
        strategy: ExperimentalStrategy,
        historical_data: np.ndarray,
        start_date: datetime,
        end_date: datetime,
        initial_capital: float = 100000,
        commission: float = 0.001
    ) -> BacktestResult:
        """Run comprehensive backtest"""
        
        # Generate signals
        signals = strategy.code(historical_data, **strategy.parameters)
        
        # Simulate trading
        capital = initial_capital
        positions = []
        trades = []
        equity_curve = [initial_capital]
        
        for i in range(len(signals)):
            # Entry logic
            if signals[i] > 0 and len(positions) == 0:
                size = capital * 0.1  # 10% position
                entry_price = historical_data[i]
                entry_cost = size * commission
                
                positions.append({
                    'entry_price': entry_price,
                    'entry_idx': i,
                    'size': size,
                    'entry_cost': entry_cost
                })
                capital -= entry_cost
            
            # Exit logic
            elif signals[i] < 0 and len(positions) > 0:
                for pos in positions:
                    exit_price = historical_data[i]
                    exit_cost = pos['size'] * commission
                    
                    pnl = (exit_price - pos['entry_price']) * pos['size'] / pos['entry_price']
                    pnl -= (pos['entry_cost'] + exit_cost)
                    
                    capital += pnl
                    
                    trades.append({
                        'entry_price': pos['entry_price'],
                        'exit_price': exit_price,
                        'pnl': pnl,
                        'duration': i - pos['entry_idx'],
                        'return': pnl / pos['size']
                    })
                
                positions = []
            
            equity_curve.append(capital)
        
        # Calculate performance metrics
        returns = np.diff(equity_curve) / equity_curve[:-1]
        
        total_return = (capital - initial_capital) / initial_capital
        sharpe_ratio = np.mean(returns) / np.std(returns) * np.sqrt(252) if np.std(returns) > 0 else 0
        
        # Max drawdown
        peak = np.maximum.accumulate(equity_curve)
        drawdown = (np.array(equity_curve) - peak) / peak
        max_drawdown = np.min(drawdown)
        
        # Win rate
        winning_trades = [t for t in trades if t['pnl'] > 0]
        win_rate = len(winning_trades) / len(trades) if trades else 0
        
        # Profit factor
        gross_profit = sum(t['pnl'] for t in trades if t['pnl'] > 0)
        gross_loss = abs(sum(t['pnl'] for t in trades if t['pnl'] < 0))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0
        
        # Average trade duration
        avg_duration = np.mean([t['duration'] for t in trades]) if trades else 0
        
        result = BacktestResult(
            strategy_id=strategy.strategy_id,
            start_date=start_date,
            end_date=end_date,
            total_return=total_return,
            sharpe_ratio=sharpe_ratio,
            max_drawdown=max_drawdown,
            win_rate=win_rate,
            num_trades=len(trades),
            avg_trade_duration=avg_duration,
            profit_factor=profit_factor
        )
        
        self.backtest_results[strategy.strategy_id] = result
        return result
    
    def walk_forward_analysis(
        self,
        strategy: ExperimentalStrategy,
        data: np.ndarray,
        train_window: int = 252,
        test_window: int = 63
    ) -> Dict:
        """Walk-forward optimization analysis"""
        
        results = []
        
        for i in range(0, len(data) - train_window - test_window, test_window):
            # Training period
            train_data = data[i:i+train_window]
            
            # Optimize parameters on training data
            # (simplified - would do actual optimization)
            
            # Test period
            test_data = data[i+train_window:i+train_window+test_window]
            
            # Test on out-of-sample data
            signals = strategy.code(test_data, **strategy.parameters)
            
            # Calculate return
            returns = np.diff(test_data) / test_data[:-1]
            strategy_return = np.sum(returns * signals[:-1])
            
            results.append({
                'period': i,
                'return': strategy_return,
                'sharpe': strategy_return / np.std(returns) if np.std(returns) > 0 else 0
            })
        
        return {
            'results': results,
            'avg_return': np.mean([r['return'] for r in results]),
            'avg_sharpe': np.mean([r['sharpe'] for r in results]),
            'consistency': np.std([r['return'] for r in results])
        }


class PaperTradingSimulator:
    """Paper trading simulator"""
    
    def __init__(self):
        self.paper_trades: Dict[str, PaperTrade] = {}
        self.strategy_performance: Dict[str, Dict] = defaultdict(lambda: {
            'total_pnl': 0,
            'num_trades': 0,
            'win_rate': 0,
            'open_positions': []
        })
        
    async def execute_paper_trade(
        self,
        strategy_id: str,
        symbol: str,
        direction: str,
        price: float,
        size: float
    ) -> str:
        """Execute paper trade"""
        
        trade_id = f"paper_{strategy_id}_{int(datetime.now().timestamp())}"
        
        trade = PaperTrade(
            trade_id=trade_id,
            strategy_id=strategy_id,
            symbol=symbol,
            direction=direction,
            entry_price=price,
            exit_price=None,
            size=size,
            entry_time=datetime.now(),
            exit_time=None,
            pnl=None,
            status='open'
        )
        
        self.paper_trades[trade_id] = trade
        self.strategy_performance[strategy_id]['open_positions'].append(trade_id)
        
        return trade_id
    
    async def close_paper_trade(
        self,
        trade_id: str,
        exit_price: float
    ) -> Dict:
        """Close paper trade"""
        
        if trade_id not in self.paper_trades:
            return {'error': 'Trade not found'}
        
        trade = self.paper_trades[trade_id]
        
        # Calculate P&L
        if trade.direction == 'long':
            pnl = (exit_price - trade.entry_price) * trade.size
        else:
            pnl = (trade.entry_price - exit_price) * trade.size
        
        # Update trade
        trade.exit_price = exit_price
        trade.exit_time = datetime.now()
        trade.pnl = pnl
        trade.status = 'closed'
        
        # Update strategy performance
        perf = self.strategy_performance[trade.strategy_id]
        perf['total_pnl'] += pnl
        perf['num_trades'] += 1
        perf['open_positions'].remove(trade_id)
        
        # Update win rate
        closed_trades = [
            t for t in self.paper_trades.values()
            if t.strategy_id == trade.strategy_id and t.status == 'closed'
        ]
        winning_trades = [t for t in closed_trades if t.pnl > 0]
        perf['win_rate'] = len(winning_trades) / len(closed_trades) if closed_trades else 0
        
        return {
            'trade_id': trade_id,
            'pnl': pnl,
            'return': pnl / (trade.entry_price * trade.size),
            'duration': (trade.exit_time - trade.entry_time).total_seconds() / 3600
        }
    
    def get_strategy_performance(self, strategy_id: str) -> Dict:
        """Get paper trading performance for strategy"""
        return dict(self.strategy_performance[strategy_id])


class ResearchInnovationHub:
    """Unified research and innovation hub"""
    
    def __init__(self):
        self.strategy_lab = ExperimentalStrategyLab()
        self.ab_testing = ABTestingFramework()
        self.backtester = AdvancedBacktester()
        self.paper_trading = PaperTradingSimulator()
        
    async def research_pipeline(
        self,
        strategy: ExperimentalStrategy,
        historical_data: np.ndarray
    ) -> Dict:
        """Complete research pipeline for new strategy"""
        
        # 1. Initial testing
        test_result = await self.strategy_lab.test_strategy(
            strategy.strategy_id,
            historical_data
        )
        
        # 2. Backtesting
        backtest_result = await self.backtester.run_backtest(
            strategy,
            historical_data,
            datetime.now() - timedelta(days=365),
            datetime.now()
        )
        
        # 3. Walk-forward analysis
        wf_result = self.backtester.walk_forward_analysis(
            strategy,
            historical_data
        )
        
        # 4. Decision
        approved = (
            backtest_result.sharpe_ratio > 1.0 and
            backtest_result.win_rate > 0.5 and
            backtest_result.max_drawdown > -0.2
        )
        
        if approved:
            self.strategy_lab.approve_strategy(strategy.strategy_id)
        
        return {
            'strategy_id': strategy.strategy_id,
            'test_result': test_result,
            'backtest_result': backtest_result,
            'walk_forward': wf_result,
            'approved': approved,
            'recommendation': 'deploy' if approved else 'reject'
        }
