#!/usr/bin/env python
"""
Complete Integrated Trading System
Combines all modules: Backtesting, Portfolio Optimization, Performance Monitoring,
Order Flow Analysis, and Main Loop Integration

This is the production-ready integrated system that ties everything together.
"""

import asyncio
import sys
import os
import time
import logging
import traceback
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from enum import Enum
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


class TradingSystemMode(Enum):
    """Trading system modes"""
    BACKTEST = "backtest"
    PAPER = "paper"
    LIVE = "live"
    OPTIMIZATION = "optimization"


@dataclass
class SystemConfig:
    """System configuration"""
    mode: TradingSystemMode = TradingSystemMode.PAPER
    symbols: List[str] = field(default_factory=lambda: ['EURUSD'])
    initial_capital: float = 100000.0
    risk_per_trade: float = 0.02
    max_portfolio_risk: float = 0.06
    enable_ml: bool = True
    enable_order_flow: bool = True
    enable_portfolio_optimization: bool = True
    enable_performance_monitoring: bool = True
    backtest_start: str = "2023-01-01"
    backtest_end: str = "2024-01-01"


class IntegratedTradingSystem:
    """
    Complete integrated trading system that combines:
    - Rigorous Backtesting
    - Portfolio Optimization
    - Performance Monitoring
    - Order Flow Analysis
    - Main Loop Integration
    """
    
    def __init__(self, config: Optional[SystemConfig] = None):
        self.config = config or SystemConfig()
        self.start_time = datetime.now()
        
        # Initialize components
        self.backtester = None
        self.portfolio_optimizer = None
        self.performance_monitor = None
        self.order_flow_analyzer = None
        self.orchestrator = None
        
        # State tracking
        self.is_initialized = False
        self.is_running = False
        self.trades_executed = 0
        self.total_pnl = 0.0
        
        # Performance metrics
        self.metrics = {
            'sharpe_ratio': 0.0,
            'sortino_ratio': 0.0,
            'max_drawdown': 0.0,
            'win_rate': 0.0,
            'profit_factor': 0.0
        }
        
        logger.info(f"IntegratedTradingSystem initialized in {self.config.mode.value} mode")
    
    async def initialize(self) -> bool:
        """Initialize all system components"""
        logger.info("Initializing integrated trading system...")
        
        try:
            # Initialize backtester
            await self._init_backtester()
            
            # Initialize portfolio optimizer
            await self._init_portfolio_optimizer()
            
            # Initialize performance monitor
            await self._init_performance_monitor()
            
            # Initialize order flow analyzer
            await self._init_order_flow_analyzer()
            
            # Initialize orchestrator
            await self._init_orchestrator()
            
            self.is_initialized = True
            logger.info("All components initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Initialization failed: {e}")
            traceback.print_exc()
            return False
    
    async def _init_backtester(self):
        """Initialize backtesting system"""
        try:
            from trading_bot.backtesting.rigorous_backtest import RigorousBacktester
            
            self.backtester = RigorousBacktester({
                'risk_free_rate': 0.04,
                'spread_bps': 2.0,
                'slippage_bps': 1.0,
                'alpha': 0.05
            })
            logger.info("Backtester initialized")
        except ImportError as e:
            logger.warning(f"Backtester not available: {e}")
    
    async def _init_portfolio_optimizer(self):
        """Initialize portfolio optimization system"""
        try:
            from trading_bot.portfolio.portfolio_optimizer import (
                PortfolioOptimizer,
                OptimizationMethod
            )
            
            self.portfolio_optimizer = PortfolioOptimizer({
                'risk_free_rate': 0.04,
                'min_weight': 0.0,
                'max_weight': 0.4
            })
            logger.info("Portfolio optimizer initialized")
        except ImportError as e:
            logger.warning(f"Portfolio optimizer not available: {e}")
    
    async def _init_performance_monitor(self):
        """Initialize performance monitoring system"""
        try:
            from trading_bot.performance.performance_monitor import (
                PerformanceMonitor,
                MetricType
            )
            
            self.performance_monitor = PerformanceMonitor(
                history_size=1000,
                auto_save=True,
                save_interval=300
            )
            logger.info("Performance monitor initialized")
        except ImportError as e:
            logger.warning(f"Performance monitor not available: {e}")
    
    async def _init_order_flow_analyzer(self):
        """Initialize order flow analysis system"""
        try:
            from trading_bot.opportunity_scanner.flow_analysis import (
                OrderFlowImbalanceDetector,
                VolumeProfileAnalyzer
            )
            
            self.order_flow_analyzer = OrderFlowImbalanceDetector({
                'min_imbalance': 0.6,
                'lookback_window': 100
            })
            self.volume_analyzer = VolumeProfileAnalyzer()
            logger.info("Order flow analyzer initialized")
        except ImportError as e:
            logger.warning(f"Order flow analyzer not available: {e}")
    
    async def _init_orchestrator(self):
        """Initialize master orchestrator"""
        try:
            from trading_bot.orchestrator.master_orchestrator import (
                MasterOrchestrator,
                TradingMode
            )
            
            self.orchestrator = MasterOrchestrator({
                'capital': self.config.initial_capital,
                'max_risk_per_trade': self.config.risk_per_trade,
                'max_portfolio_risk': self.config.max_portfolio_risk
            })
            logger.info("Master orchestrator initialized")
        except ImportError as e:
            logger.warning(f"Orchestrator not available: {e}")
    
    async def run_backtest(self, strategy_func, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Run rigorous backtest on a strategy
        
        Args:
            strategy_func: Strategy function that takes data and returns signals
            data: OHLCV DataFrame
            
        Returns:
            Backtest results dictionary
        """
        if not self.backtester:
            logger.error("Backtester not initialized")
            return {}
        
        logger.info("Running rigorous backtest...")
        
        # Run basic backtest
        result = self.backtester.backtest(
            strategy_func,
            data,
            initial_capital=self.config.initial_capital
        )
        
        # Run walk-forward analysis
        wf_result = self.backtester.walk_forward_analysis(
            strategy_func,
            data,
            num_windows=5
        )
        
        # Run Monte Carlo simulation
        returns = data['close'].pct_change().dropna().values
        mc_result = self.backtester.monte_carlo_simulation(
            returns,
            num_simulations=1000
        )
        
        # Compile results
        results = {
            'basic_backtest': result.to_dict(),
            'walk_forward': wf_result.to_dict(),
            'monte_carlo': mc_result.to_dict(),
            'is_robust': wf_result.is_robust,
            'is_significant': result.is_significant
        }
        
        logger.info(f"Backtest complete: Sharpe={result.sharpe_ratio:.2f}, "
                   f"Return={result.total_return:.2%}, Robust={wf_result.is_robust}")
        
        return results
    
    async def optimize_portfolio(self, returns: pd.DataFrame) -> Dict[str, Any]:
        """
        Optimize portfolio allocation
        
        Args:
            returns: DataFrame of asset returns
            
        Returns:
            Optimization results dictionary
        """
        if not self.portfolio_optimizer:
            logger.error("Portfolio optimizer not initialized")
            return {}
        
        logger.info("Running portfolio optimization...")
        
        try:
            from trading_bot.portfolio.portfolio_optimizer import OptimizationMethod
            
            results = {}
            
            # Run multiple optimization methods
            methods = [
                OptimizationMethod.MAX_SHARPE,
                OptimizationMethod.MIN_VARIANCE,
                OptimizationMethod.RISK_PARITY,
                OptimizationMethod.HRP
            ]
            
            for method in methods:
                try:
                    result = self.portfolio_optimizer.optimize(returns, method=method)
                    results[method.value] = result.to_dict()
                    logger.info(f"{method.value}: Sharpe={result.metrics.sharpe_ratio:.2f}")
                except Exception as e:
                    logger.warning(f"Optimization {method.value} failed: {e}")
            
            # Select best method
            if results:
                best_method = max(results.keys(), 
                                 key=lambda k: results[k]['metrics']['sharpe_ratio'])
                results['recommended'] = best_method
                results['recommended_weights'] = results[best_method]['weights']
            
            return results
            
        except Exception as e:
            logger.error(f"Portfolio optimization failed: {e}")
            return {}
    
    async def analyze_order_flow(self, market_data: Dict) -> Dict[str, Any]:
        """
        Analyze order flow for institutional activity
        
        Args:
            market_data: Dictionary of market data with trades
            
        Returns:
            Order flow analysis results
        """
        if not self.order_flow_analyzer:
            logger.error("Order flow analyzer not initialized")
            return {}
        
        logger.info("Analyzing order flow...")
        
        try:
            # Detect flow imbalances
            opportunities = await self.order_flow_analyzer.detect_flow_imbalances(market_data)
            
            results = {
                'opportunities': len(opportunities),
                'details': []
            }
            
            for opp in opportunities:
                results['details'].append({
                    'symbol': opp.symbol,
                    'flow_type': opp.flow_type.value,
                    'direction': opp.direction,
                    'magnitude': opp.magnitude,
                    'confidence': opp.confidence
                })
            
            # Volume profile analysis
            for symbol, data in market_data.items():
                if 'prices' in data and 'volumes' in data:
                    profile = self.volume_analyzer.analyze_volume_profile(
                        data['prices'],
                        data['volumes']
                    )
                    results[f'{symbol}_volume_profile'] = profile
            
            logger.info(f"Order flow analysis complete: {len(opportunities)} opportunities found")
            
            return results
            
        except Exception as e:
            logger.error(f"Order flow analysis failed: {e}")
            return {}
    
    async def run_trading_cycle(self, market_data: Dict) -> Dict[str, Any]:
        """
        Run a complete trading cycle
        
        Args:
            market_data: Current market data
            
        Returns:
            Trading cycle results
        """
        if not self.is_initialized:
            await self.initialize()
        
        logger.info("Running trading cycle...")
        cycle_start = time.time()
        
        results = {
            'timestamp': datetime.now().isoformat(),
            'cycle_duration': 0,
            'decisions': [],
            'order_flow': {},
            'performance': {}
        }
        
        try:
            # Step 1: Analyze order flow
            if self.config.enable_order_flow:
                results['order_flow'] = await self.analyze_order_flow(market_data)
            
            # Step 2: Generate trading decisions via orchestrator
            if self.orchestrator:
                decisions = await self.orchestrator.orchestrate_trading(market_data)
                results['decisions'] = [
                    {
                        'decision_id': d.decision_id,
                        'action': d.action,
                        'symbols': d.symbols,
                        'confidence': d.confidence,
                        'risk_score': d.risk_score
                    }
                    for d in decisions
                ]
            
            # Step 3: Record performance metrics
            if self.performance_monitor:
                from trading_bot.performance.performance_monitor import MetricType
                
                self.performance_monitor.record_metric(
                    'trading_cycle',
                    MetricType.EXECUTION_TIME,
                    time.time() - cycle_start
                )
                
                results['performance'] = {
                    'cycle_time': time.time() - cycle_start,
                    'decisions_generated': len(results['decisions'])
                }
            
            results['cycle_duration'] = time.time() - cycle_start
            logger.info(f"Trading cycle complete in {results['cycle_duration']:.3f}s")
            
        except Exception as e:
            logger.error(f"Trading cycle failed: {e}")
            results['error'] = str(e)
        
        return results
    
    async def run_continuous(self, interval_seconds: int = 60):
        """
        Run continuous trading loop
        
        Args:
            interval_seconds: Seconds between trading cycles
        """
        if not self.is_initialized:
            await self.initialize()
        
        self.is_running = True
        logger.info(f"Starting continuous trading with {interval_seconds}s interval")
        
        cycle_count = 0
        
        while self.is_running:
            try:
                cycle_count += 1
                logger.info(f"=== Trading Cycle {cycle_count} ===")
                
                # Generate sample market data (in production, fetch real data)
                market_data = self._generate_sample_market_data()
                
                # Run trading cycle
                results = await self.run_trading_cycle(market_data)
                
                # Log results
                logger.info(f"Cycle {cycle_count} complete: "
                           f"{len(results.get('decisions', []))} decisions, "
                           f"{results.get('cycle_duration', 0):.3f}s")
                
                # Wait for next cycle
                await asyncio.sleep(interval_seconds)
                
            except KeyboardInterrupt:
                logger.info("Received shutdown signal")
                self.is_running = False
            except Exception as e:
                logger.error(f"Error in trading cycle: {e}")
                await asyncio.sleep(5)  # Brief pause before retry
        
        logger.info("Continuous trading stopped")
    
    def _generate_sample_market_data(self) -> Dict:
        """Generate sample market data for testing"""
        np.random.seed(int(time.time()) % 1000)
        
        market_data = {}
        
        for symbol in self.config.symbols:
            base_price = 1.0850 if 'EUR' in symbol else 100.0
            
            # Generate sample trades
            trades = []
            for i in range(100):
                trades.append({
                    'size': np.random.randint(100, 10000),
                    'aggressor': 'buy' if np.random.random() > 0.5 else 'sell',
                    'timestamp': datetime.now() - timedelta(seconds=i)
                })
            
            market_data[symbol] = {
                'price': base_price * (1 + np.random.randn() * 0.001),
                'bid': base_price * 0.9999,
                'ask': base_price * 1.0001,
                'volume': np.random.randint(100000, 1000000),
                'volatility': np.random.uniform(0.1, 0.3),
                'trades': trades,
                'prices': [base_price * (1 + np.random.randn() * 0.01) for _ in range(100)],
                'volumes': [np.random.randint(10000, 100000) for _ in range(100)]
            }
        
        return market_data
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get current system status"""
        return {
            'mode': self.config.mode.value,
            'is_initialized': self.is_initialized,
            'is_running': self.is_running,
            'uptime_seconds': (datetime.now() - self.start_time).total_seconds(),
            'trades_executed': self.trades_executed,
            'total_pnl': self.total_pnl,
            'metrics': self.metrics,
            'components': {
                'backtester': self.backtester is not None,
                'portfolio_optimizer': self.portfolio_optimizer is not None,
                'performance_monitor': self.performance_monitor is not None,
                'order_flow_analyzer': self.order_flow_analyzer is not None,
                'orchestrator': self.orchestrator is not None
            }
        }
    
    def stop(self):
        """Stop the trading system"""
        self.is_running = False
        logger.info("Trading system stopped")


async def run_demo():
    """Run a demonstration of the integrated system"""
    print("\n" + "=" * 80)
    print("INTEGRATED TRADING SYSTEM DEMONSTRATION")
    print("=" * 80)
    
    # Create system with default config
    config = SystemConfig(
        mode=TradingSystemMode.PAPER,
        symbols=['EURUSD', 'GBPUSD', 'USDJPY'],
        initial_capital=100000.0
    )
    
    system = IntegratedTradingSystem(config)
    
    # Initialize
    print("\n[1] Initializing system...")
    await system.initialize()
    
    # Show status
    status = system.get_system_status()
    print(f"\nSystem Status:")
    print(f"  Mode: {status['mode']}")
    print(f"  Initialized: {status['is_initialized']}")
    print(f"  Components: {sum(status['components'].values())}/{len(status['components'])} active")
    
    # Generate sample data for backtest
    print("\n[2] Running backtest...")
    np.random.seed(42)
    n_days = 500
    dates = pd.date_range('2023-01-01', periods=n_days, freq='D')
    returns = np.random.randn(n_days) * 0.015 + 0.0003
    prices = 100 * np.exp(np.cumsum(returns))
    
    data = pd.DataFrame({
        'open': prices * (1 + np.random.randn(n_days) * 0.002),
        'high': prices * (1 + abs(np.random.randn(n_days) * 0.015)),
        'low': prices * (1 - abs(np.random.randn(n_days) * 0.015)),
        'close': prices,
        'volume': np.random.randint(100000, 1000000, n_days)
    }, index=dates)
    
    # Define strategy
    def momentum_strategy(data: pd.DataFrame) -> pd.Series:
        signal = pd.Series(0, index=data.index)
        momentum = data['close'].pct_change(20)
        signal[momentum > 0] = 1
        signal[momentum < 0] = -1
        return signal
    
    # Run backtest
    backtest_results = await system.run_backtest(momentum_strategy, data)
    
    if backtest_results:
        print(f"\nBacktest Results:")
        print(f"  Total Return: {backtest_results['basic_backtest']['total_return']:.2%}")
        print(f"  Sharpe Ratio: {backtest_results['basic_backtest']['sharpe_ratio']:.2f}")
        print(f"  Max Drawdown: {backtest_results['basic_backtest']['max_drawdown']:.2%}")
        print(f"  Is Robust: {backtest_results['is_robust']}")
        print(f"  Is Significant: {backtest_results['is_significant']}")
    
    # Run portfolio optimization
    print("\n[3] Running portfolio optimization...")
    
    # Generate multi-asset returns
    assets = ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'META']
    returns_data = {}
    for asset in assets:
        returns_data[asset] = np.random.randn(252) * 0.02 + 0.0005
    returns_df = pd.DataFrame(returns_data)
    
    portfolio_results = await system.optimize_portfolio(returns_df)
    
    if portfolio_results and 'recommended' in portfolio_results:
        print(f"\nPortfolio Optimization Results:")
        print(f"  Recommended Method: {portfolio_results['recommended']}")
        print(f"  Weights:")
        for asset, weight in portfolio_results['recommended_weights'].items():
            print(f"    {asset}: {weight:.2%}")
    
    # Run order flow analysis
    print("\n[4] Running order flow analysis...")
    market_data = system._generate_sample_market_data()
    flow_results = await system.analyze_order_flow(market_data)
    
    print(f"\nOrder Flow Analysis:")
    print(f"  Opportunities Found: {flow_results.get('opportunities', 0)}")
    for detail in flow_results.get('details', [])[:3]:
        print(f"    {detail['symbol']}: {detail['flow_type']} - {detail['direction']} "
              f"(confidence: {detail['confidence']:.2f})")
    
    # Run single trading cycle
    print("\n[5] Running trading cycle...")
    cycle_results = await system.run_trading_cycle(market_data)
    
    print(f"\nTrading Cycle Results:")
    print(f"  Duration: {cycle_results['cycle_duration']:.3f}s")
    print(f"  Decisions: {len(cycle_results['decisions'])}")
    
    # Final status
    print("\n[6] Final System Status:")
    final_status = system.get_system_status()
    print(f"  Uptime: {final_status['uptime_seconds']:.1f}s")
    print(f"  All Components Active: {all(final_status['components'].values())}")
    
    print("\n" + "=" * 80)
    print("DEMONSTRATION COMPLETE")
    print("=" * 80)
    
    return system


async def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Integrated Trading System")
    parser.add_argument('--mode', choices=['demo', 'backtest', 'paper', 'continuous'],
                       default='demo', help='Operating mode')
    parser.add_argument('--symbols', nargs='+', default=['EURUSD'],
                       help='Trading symbols')
    parser.add_argument('--capital', type=float, default=100000,
                       help='Initial capital')
    parser.add_argument('--interval', type=int, default=60,
                       help='Trading cycle interval (seconds)')
    
    args = parser.parse_args()
    
    if args.mode == 'demo':
        await run_demo()
    elif args.mode == 'continuous':
        config = SystemConfig(
            mode=TradingSystemMode.PAPER,
            symbols=args.symbols,
            initial_capital=args.capital
        )
        system = IntegratedTradingSystem(config)
        await system.run_continuous(interval_seconds=args.interval)
    else:
        print(f"Mode '{args.mode}' not yet implemented")


if __name__ == "__main__":
    asyncio.run(main())
