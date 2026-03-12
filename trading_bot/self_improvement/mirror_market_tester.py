"""
Mirror Market Tester
Tests improved strategies in a mirror/simulated live market before deploying to real trading.
"""

import logging
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
from enum import Enum
import asyncio
import numpy as np
import numpy

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


class TestStatus(Enum):
    """Test status."""
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    INCONCLUSIVE = "inconclusive"


class MirrorMarketTester:
    """
    Tests strategies in mirror market (simulated live environment):
    1. Creates exact copy of live market conditions
    2. Runs improved strategy in parallel
    3. Compares performance vs current strategy
    4. Validates improvement before going live
    5. Provides detailed performance metrics
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize mirror market tester.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.test_duration_hours = config.get('mirror_test_duration_hours', 24)
        self.min_trades_required = config.get('min_trades_required', 30)
        self.performance_threshold = config.get('performance_threshold', 0.05)  # 5% improvement
        
        # Active tests
        self.active_tests = {}
        
        logger.info("MirrorMarketTester initialized")
    
    async def test_improved_strategy(self,
                                     improved_strategy: Dict[str, Any],
                                     current_strategy: Dict[str, Any],
                                     symbol: str) -> Dict[str, Any]:
        """
        Test improved strategy in mirror market.
        
        Args:
            improved_strategy: The improved strategy to test
            current_strategy: Current baseline strategy
            symbol: Trading symbol
            
        Returns:
            Test results with performance comparison
        """
        test_id = f"mirror_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        logger.info(f"Starting mirror market test {test_id} for {symbol}")
        
        # Create test environment
        test_env = self._create_mirror_environment(symbol)
        
        # Initialize both strategies
        baseline_trader = self._initialize_strategy(current_strategy, test_env)
        improved_trader = self._initialize_strategy(improved_strategy, test_env)
        
        # Store test info
        self.active_tests[test_id] = {
            'status': TestStatus.RUNNING,
            'start_time': datetime.now(),
            'symbol': symbol,
            'baseline_trader': baseline_trader,
            'improved_trader': improved_trader
        }
        
        # Run parallel test
        test_result = await self._run_parallel_test(
            test_id,
            baseline_trader,
            improved_trader,
            test_env
        )
        
        # Analyze results
        analysis = self._analyze_test_results(test_result)
        
        # Make decision
        decision = self._make_deployment_decision(analysis)
        
        logger.info(f"Mirror test {test_id} completed: {decision['recommendation']}")
        
        return {
            'test_id': test_id,
            'status': decision['status'],
            'recommendation': decision['recommendation'],
            'analysis': analysis,
            'baseline_performance': test_result['baseline'],
            'improved_performance': test_result['improved'],
            'improvement_pct': analysis['improvement_pct'],
            'safe_to_deploy': decision['safe_to_deploy']
        }
    
    def _create_mirror_environment(self, symbol: str) -> Dict[str, Any]:
        """Create mirror market environment with live data."""
        return {
            'symbol': symbol,
            'mode': 'mirror',
            'data_source': 'live',  # Use live market data
            'execution': 'simulated',  # Simulate order execution
            'slippage_model': 'realistic',  # Model realistic slippage
            'latency_model': 'realistic',  # Model realistic latency
            'start_time': datetime.now(),
            'initial_balance': 10000.0  # Test balance
        }
    
    def _initialize_strategy(self,
                            strategy: Dict[str, Any],
                            environment: Dict[str, Any]) -> Dict[str, Any]:
        """Initialize a strategy in the test environment."""
        return {
            'strategy': strategy,
            'environment': environment,
            'trades': [],
            'balance': environment['initial_balance'],
            'equity_curve': [],
            'signals': [],
            'metrics': {
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'total_pnl': 0.0,
                'max_drawdown': 0.0,
                'sharpe_ratio': 0.0
            }
        }
    
    async def _run_parallel_test(self,
                                 test_id: str,
                                 baseline_trader: Dict[str, Any],
                                 improved_trader: Dict[str, Any],
                                 environment: Dict[str, Any]) -> Dict[str, Any]:
        """Run both strategies in parallel on same market data."""
        
        start_time = datetime.now()
        end_time = start_time + timedelta(hours=self.test_duration_hours)
        
        logger.info(f"Running parallel test until {end_time}")
        
        # Simulate trading for test duration
        current_time = start_time
        tick_count = 0
        
        while current_time < end_time and tick_count < 10000:  # Safety limit
            # Get live market data (simulated for now)
            market_data = await self._get_live_market_data(environment['symbol'])
            
            # Process with baseline strategy
            baseline_signal = self._process_tick(baseline_trader, market_data)
            if baseline_signal:
                self._execute_trade(baseline_trader, baseline_signal, market_data)
            
            # Process with improved strategy
            improved_signal = self._process_tick(improved_trader, market_data)
            if improved_signal:
                self._execute_trade(improved_trader, improved_signal, market_data)
            
            # Update equity curves
            baseline_trader['equity_curve'].append({
                'time': current_time,
                'equity': baseline_trader['balance']
            })
            improved_trader['equity_curve'].append({
                'time': current_time,
                'equity': improved_trader['balance']
            })
            
            # Advance time (simulate)
            current_time += timedelta(minutes=1)
            tick_count += 1
            
            # Check if minimum trades reached
            if (baseline_trader['metrics']['total_trades'] >= self.min_trades_required and
                improved_trader['metrics']['total_trades'] >= self.min_trades_required):
                logger.info(f"Minimum trades reached, test can conclude early")
                break
            
            # Small delay to simulate real-time
            await asyncio.sleep(0.001)
        
        # Calculate final metrics
        self._calculate_final_metrics(baseline_trader)
        self._calculate_final_metrics(improved_trader)
        
        return {
            'baseline': baseline_trader['metrics'],
            'improved': improved_trader['metrics'],
            'duration': (current_time - start_time).total_seconds() / 3600,
            'ticks_processed': tick_count
        }
    
    async def _get_live_market_data(self, symbol: str) -> Dict[str, Any]:
        """Get live market data (simulated for demo)."""
        # In production, connect to live data feed
        # For now, generate realistic random data
        
        return {
            'symbol': symbol,
            'timestamp': datetime.now(),
            'bid': 1.1000 + np.random.normal(0, 0.0005),
            'ask': 1.1002 + np.random.normal(0, 0.0005),
            'volume': np.random.randint(100, 1000)
        }
    
    def _process_tick(self,
                     trader: Dict[str, Any],
                     market_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process market tick and generate signal if any."""
        # Simulate strategy logic
        # In production, call actual strategy
        
        # Random signal generation for demo
        if np.random.random() < 0.01:  # 1% chance of signal
            return {
                'action': 'buy' if np.random.random() > 0.5 else 'sell',
                'price': market_data['bid'],
                'size': 0.01,
                'confidence': np.random.uniform(0.6, 0.9)
            }
        
        return None
    
    def _execute_trade(self,
                      trader: Dict[str, Any],
                      signal: Dict[str, Any],
                      market_data: Dict[str, Any]):
        """Execute trade in simulated environment."""
        # Simulate trade execution with realistic slippage
        slippage = np.random.normal(0, 0.0002)  # Random slippage
        
        entry_price = signal['price'] + slippage
        
        # Simulate trade outcome (random for demo)
        # In production, this would track actual market movement
        exit_price = entry_price + np.random.normal(0.0001, 0.0010)
        
        pnl = (exit_price - entry_price) * signal['size'] * 100000  # Pip value
        
        # Update trader state
        trader['balance'] += pnl
        trader['trades'].append({
            'entry_time': market_data['timestamp'],
            'entry_price': entry_price,
            'exit_price': exit_price,
            'pnl': pnl,
            'action': signal['action']
        })
        
        # Update metrics
        trader['metrics']['total_trades'] += 1
        trader['metrics']['total_pnl'] += pnl
        
        if pnl > 0:
            trader['metrics']['winning_trades'] += 1
        else:
            trader['metrics']['losing_trades'] += 1
    
    def _calculate_final_metrics(self, trader: Dict[str, Any]):
        """Calculate final performance metrics."""
        metrics = trader['metrics']
        trades = trader['trades']
        equity_curve = trader['equity_curve']
        
        if metrics['total_trades'] > 0:
            # Win rate
            metrics['win_rate'] = metrics['winning_trades'] / metrics['total_trades']
            
            # Average PnL
            metrics['avg_pnl'] = metrics['total_pnl'] / metrics['total_trades']
            
            # Max drawdown
            if equity_curve:
                peak = equity_curve[0]['equity']
                max_dd = 0
                for point in equity_curve:
                    if point['equity'] > peak:
                        peak = point['equity']
                    dd = (peak - point['equity']) / peak
                    if dd > max_dd:
                        max_dd = dd
                metrics['max_drawdown'] = max_dd
            
            # Sharpe ratio (simplified)
            if trades:
                returns = [t['pnl'] for t in trades]
                if len(returns) > 1:
                    mean_return = np.mean(returns)
                    std_return = np.std(returns)
                    if std_return > 0:
                        metrics['sharpe_ratio'] = mean_return / std_return
    
    def _analyze_test_results(self, test_result: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze test results and compare performance."""
        baseline = test_result['baseline']
        improved = test_result['improved']
        
        # Calculate improvements
        analysis = {
            'win_rate_improvement': improved['win_rate'] - baseline['win_rate'],
            'pnl_improvement': improved['total_pnl'] - baseline['total_pnl'],
            'drawdown_improvement': baseline['max_drawdown'] - improved['max_drawdown'],
            'sharpe_improvement': improved['sharpe_ratio'] - baseline['sharpe_ratio'],
            'trades_comparison': {
                'baseline': baseline['total_trades'],
                'improved': improved['total_trades']
            }
        }
        
        # Overall improvement percentage
        if baseline['total_pnl'] != 0:
            analysis['improvement_pct'] = (improved['total_pnl'] - baseline['total_pnl']) / abs(baseline['total_pnl'])
        else:
            analysis['improvement_pct'] = 0.0
        
        # Statistical significance (simplified)
        analysis['statistically_significant'] = (
            abs(analysis['improvement_pct']) > 0.05 and
            baseline['total_trades'] >= self.min_trades_required
        )
        
        return analysis
    
    def _make_deployment_decision(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Make decision on whether to deploy improved strategy."""
        
        # Check if improvement meets threshold
        improvement_pct = analysis['improvement_pct']
        
        if improvement_pct >= self.performance_threshold:
            # Significant improvement
            if analysis['statistically_significant']:
                return {
                    'status': TestStatus.PASSED,
                    'recommendation': 'DEPLOY',
                    'safe_to_deploy': True,
                    'reason': f'Improved performance by {improvement_pct:.1%} with statistical significance'
                }
            else:
                return {
                    'status': TestStatus.INCONCLUSIVE,
                    'recommendation': 'EXTEND_TEST',
                    'safe_to_deploy': False,
                    'reason': 'Improvement shown but not statistically significant, extend test duration'
                }
        
        elif improvement_pct > 0:
            # Minor improvement
            return {
                'status': TestStatus.INCONCLUSIVE,
                'recommendation': 'MONITOR',
                'safe_to_deploy': False,
                'reason': f'Minor improvement ({improvement_pct:.1%}), continue monitoring'
            }
        
        else:
            # No improvement or degradation
            return {
                'status': TestStatus.FAILED,
                'recommendation': 'REJECT',
                'safe_to_deploy': False,
                'reason': f'Strategy did not improve performance ({improvement_pct:.1%})'
            }
    
    def get_test_status(self, test_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a running test."""
        return self.active_tests.get(test_id)
    
    async def stop_test(self, test_id: str) -> Dict[str, Any]:
        """Stop a running test."""
        if test_id in self.active_tests:
            test = self.active_tests[test_id]
            test['status'] = TestStatus.FAILED
            test['end_time'] = datetime.now()
            
            logger.info(f"Test {test_id} stopped manually")
            
            return {
                'status': 'stopped',
                'test_id': test_id,
                'duration': (test['end_time'] - test['start_time']).total_seconds()
            }
        
        return {'status': 'not_found', 'test_id': test_id}
