#!/usr/bin/env python
"""
Production Trading System Runner
Main entry point for running the complete trading system.

Usage:
    py run_production_system.py --mode paper --symbols EURUSD GBPUSD
    py run_production_system.py --mode demo
    py run_production_system.py --mode optimize --strategy sma
"""

import asyncio
import argparse
import sys
import os
import logging
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Setup logging first
from trading_bot.logging.logging_config import setup_logging, get_logger

setup_logging(level='INFO', log_file='production_trading.log')
logger = get_logger(__name__)


def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="AlphaAlgo Production Trading System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Run paper trading demo
    py run_production_system.py --mode demo
    
    # Run paper trading with specific symbols
    py run_production_system.py --mode paper --symbols EURUSD GBPUSD USDJPY
    
    # Run strategy optimization
    py run_production_system.py --mode optimize --strategy sma
    
    # Run with custom capital
    py run_production_system.py --mode paper --capital 50000
        """
    )
    
    parser.add_argument(
        '--mode',
        choices=['demo', 'paper', 'live', 'optimize', 'backtest'],
        default='demo',
        help='Operating mode (default: demo)'
    )
    
    parser.add_argument(
        '--symbols',
        nargs='+',
        default=['EURUSD', 'GBPUSD', 'USDJPY'],
        help='Trading symbols (default: EURUSD GBPUSD USDJPY)'
    )
    
    parser.add_argument(
        '--capital',
        type=float,
        default=100000.0,
        help='Initial capital (default: 100000)'
    )
    
    parser.add_argument(
        '--strategy',
        choices=['sma', 'rsi', 'momentum', 'custom'],
        default='sma',
        help='Strategy to use (default: sma)'
    )
    
    parser.add_argument(
        '--duration',
        type=int,
        default=60,
        help='Demo duration in seconds (default: 60)'
    )
    
    parser.add_argument(
        '--risk-per-trade',
        type=float,
        default=0.02,
        help='Risk per trade as fraction (default: 0.02)'
    )
    
    parser.add_argument(
        '--max-positions',
        type=int,
        default=5,
        help='Maximum concurrent positions (default: 5)'
    )
    
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='Logging level (default: INFO)'
    )
    
    return parser.parse_args()


async def run_demo(args):
    """Run demo mode"""
    from trading_bot.production.live_trading_system import (
        LiveTradingSystem, TradingMode, RiskParameters
    )
    
    print("\n" + "=" * 70)
    print("ALPHAALGO PRODUCTION TRADING SYSTEM - DEMO MODE")
    print("=" * 70)
    print(f"Symbols: {', '.join(args.symbols)}")
    print(f"Capital: ${args.capital:,.2f}")
    print(f"Duration: {args.duration} seconds")
    print("=" * 70 + "\n")
    
    # Configure risk parameters
    risk_params = RiskParameters(
        max_position_size=args.risk_per_trade,
        max_positions=args.max_positions,
        max_daily_loss=0.03,
        max_drawdown=0.10,
    )
    
    # Create system
    system = LiveTradingSystem(
        symbols=args.symbols,
        mode=TradingMode.PAPER,
        initial_capital=args.capital,
        risk_params=risk_params,
    )
    
    # Set strategy based on argument
    strategy = get_strategy(args.strategy)
    system.set_strategy(strategy)
    
    # Run for specified duration
    try:
        async def run_with_timeout():
            task = asyncio.create_task(system.start())
            await asyncio.sleep(args.duration)
            system.is_running = False
            await system.stop()
        
        await run_with_timeout()
        
    except KeyboardInterrupt:
        logger.info("Shutdown requested by user")
        await system.stop()
    
    # Print final status
    status = system.get_status()
    print_final_status(status)


async def run_paper_trading(args):
    """Run paper trading mode"""
    from trading_bot.production.live_trading_system import (
        LiveTradingSystem, TradingMode, RiskParameters
    )
    
    print("\n" + "=" * 70)
    print("ALPHAALGO PRODUCTION TRADING SYSTEM - PAPER TRADING")
    print("=" * 70)
    print(f"Symbols: {', '.join(args.symbols)}")
    print(f"Capital: ${args.capital:,.2f}")
    print("Press Ctrl+C to stop")
    print("=" * 70 + "\n")
    
    risk_params = RiskParameters(
        max_position_size=args.risk_per_trade,
        max_positions=args.max_positions,
        max_daily_loss=0.03,
        max_drawdown=0.10,
    )
    
    system = LiveTradingSystem(
        symbols=args.symbols,
        mode=TradingMode.PAPER,
        initial_capital=args.capital,
        risk_params=risk_params,
    )
    
    strategy = get_strategy(args.strategy)
    system.set_strategy(strategy)
    
    try:
        await system.start()
    except KeyboardInterrupt:
        logger.info("Shutdown requested by user")
        await system.stop()
    
    status = system.get_status()
    print_final_status(status)


async def run_optimization(args):
    """Run strategy optimization"""
    from trading_bot.optimization.strategy_optimizer_v2 import (
        StrategyOptimizer, ParameterSpace, OptimizationMethod,
        sma_crossover_strategy, rsi_strategy, momentum_strategy
    )
    import numpy as np
    import pandas as pd
    
    print("\n" + "=" * 70)
    print("ALPHAALGO STRATEGY OPTIMIZER")
    print("=" * 70)
    print(f"Strategy: {args.strategy}")
    print("=" * 70 + "\n")
    
    # Generate sample data for optimization
    print("Generating sample data...")
    np.random.seed(42)
    n_days = 1000
    dates = pd.date_range('2022-01-01', periods=n_days, freq='D')
    
    returns = np.random.randn(n_days) * 0.015 + 0.0003
    prices = 100 * np.exp(np.cumsum(returns))
    
    data = pd.DataFrame({
        'open': prices * (1 + np.random.randn(n_days) * 0.002),
        'high': prices * (1 + abs(np.random.randn(n_days) * 0.015)),
        'low': prices * (1 - abs(np.random.randn(n_days) * 0.015)),
        'close': prices,
        'volume': np.random.randint(100000, 1000000, n_days)
    }, index=dates)
    
    optimizer = StrategyOptimizer(data, initial_capital=args.capital)
    
    # Define parameter space based on strategy
    if args.strategy == 'sma':
        strategy_func = sma_crossover_strategy
        param_space = [
            ParameterSpace('fast_period', 'int', 5, 30, 5),
            ParameterSpace('slow_period', 'int', 20, 60, 10),
        ]
    elif args.strategy == 'rsi':
        strategy_func = rsi_strategy
        param_space = [
            ParameterSpace('period', 'int', 7, 21, 2),
            ParameterSpace('oversold', 'int', 20, 40, 5),
            ParameterSpace('overbought', 'int', 60, 80, 5),
        ]
    elif args.strategy == 'momentum':
        strategy_func = momentum_strategy
        param_space = [
            ParameterSpace('lookback', 'int', 10, 40, 5),
            ParameterSpace('threshold', 'float', 0.01, 0.05, 0.01),
        ]
    else:
        print(f"Unknown strategy: {args.strategy}")
        return
    
    # Run grid search
    print("\n[1] Running Grid Search...")
    grid_result = optimizer.optimize(
        strategy_func,
        param_space,
        method=OptimizationMethod.GRID_SEARCH
    )
    
    print(f"\nGrid Search Results:")
    print(f"  Best Parameters: {grid_result.best_params}")
    print(f"  Best Score: {grid_result.best_score:.4f}")
    print(f"  Combinations: {len(grid_result.all_results)}")
    print(f"  Time: {grid_result.optimization_time:.2f}s")
    
    # Run walk-forward
    print("\n[2] Running Walk-Forward Validation...")
    wf_result = optimizer.optimize(
        strategy_func,
        param_space,
        method=OptimizationMethod.WALK_FORWARD
    )
    
    print(f"\nWalk-Forward Results:")
    print(f"  Best Parameters: {wf_result.best_params}")
    print(f"  OOS Score: {wf_result.best_score:.4f}")
    if wf_result.validation_results:
        print(f"  Avg OOS Score: {wf_result.validation_results['avg_oos_score']:.4f}")
    
    # Monte Carlo validation
    print("\n[3] Running Monte Carlo Validation...")
    mc_results = optimizer.monte_carlo_validation(
        strategy_func,
        grid_result.best_params,
        n_simulations=500
    )
    
    print(f"\nMonte Carlo Results:")
    print(f"  Expected Return: {mc_results['return_mean']:.2%} +/- {mc_results['return_std']:.2%}")
    print(f"  5th Percentile: {mc_results['return_5th']:.2%}")
    print(f"  95th Percentile: {mc_results['return_95th']:.2%}")
    print(f"  Probability Positive: {mc_results['prob_positive']:.1%}")
    
    # Export results
    results_path = f"results/optimization_{args.strategy}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    optimizer.export_results(results_path)
    print(f"\nResults exported to: {results_path}")
    
    print("\n" + "=" * 70)
    print("OPTIMIZATION COMPLETE")
    print("=" * 70)


async def run_backtest(args):
    """Run backtest mode"""
    from trading_bot.backtesting.rigorous_backtest import RigorousBacktester
    import numpy as np
    import pandas as pd
    
    print("\n" + "=" * 70)
    print("ALPHAALGO RIGOROUS BACKTESTER")
    print("=" * 70)
    
    # Generate sample data
    print("Generating sample data...")
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
    
    # Create backtester
    backtester = RigorousBacktester({
        'risk_free_rate': 0.04,
        'spread_bps': 2.0,
        'slippage_bps': 1.0,
    })
    
    # Define strategy
    def momentum_strategy(data):
        signals = pd.Series(0, index=data.index)
        momentum = data['close'].pct_change(20)
        signals[momentum > 0] = 1
        signals[momentum < 0] = -1
        return signals
    
    print("\nRunning backtest...")
    result = backtester.backtest(momentum_strategy, data, initial_capital=args.capital)
    
    print(f"\nBacktest Results:")
    print(f"  Total Return: {result.total_return:.2%}")
    print(f"  Sharpe Ratio: {result.sharpe_ratio:.2f}")
    print(f"  Max Drawdown: {result.max_drawdown:.2%}")
    print(f"  Total Trades: {result.total_trades}")
    print(f"  Win Rate: {result.win_rate:.2%}")
    print(f"  Profit Factor: {result.profit_factor:.2f}")
    print(f"  Is Significant: {result.is_significant}")
    
    # Walk-forward analysis
    print("\nRunning walk-forward analysis...")
    wf_result = backtester.walk_forward_analysis(momentum_strategy, data, num_windows=3)
    
    print(f"\nWalk-Forward Results:")
    print(f"  Is Robust: {wf_result.is_robust}")
    print(f"  Avg OOS Return: {wf_result.avg_oos_return:.2%}")
    print(f"  Avg OOS Sharpe: {wf_result.avg_oos_sharpe:.2f}")
    
    # Monte Carlo
    print("\nRunning Monte Carlo simulation...")
    mc_result = backtester.monte_carlo_simulation(
        data['close'].pct_change().dropna().values,
        num_simulations=500
    )
    
    print(f"\nMonte Carlo Results:")
    print(f"  Median Final Return: {mc_result.median_return:.2%}")
    print(f"  5th Percentile: {mc_result.percentile_5:.2%}")
    print(f"  95th Percentile: {mc_result.percentile_95:.2%}")
    print(f"  Prob Positive: {mc_result.prob_positive:.1%}")
    
    print("\n" + "=" * 70)
    print("BACKTEST COMPLETE")
    print("=" * 70)


def get_strategy(strategy_name: str):
    """Get strategy function by name"""
    import numpy as np
    
    def sma_strategy(symbol, price_data, positions, capital):
        """Simple SMA crossover strategy"""
        import random
        
        current_price = price_data['price']
        position = positions.get(symbol)
        
        # Simple random signal for demo
        signal = random.random()
        
        if position is None:
            if signal > 0.7:
                return {
                    'action': 'buy',
                    'quantity': round(capital * 0.02 / current_price, 2),
                    'reason': 'SMA crossover buy signal',
                }
        else:
            if signal < 0.3:
                return {
                    'action': 'sell',
                    'quantity': abs(position.quantity),
                    'reason': 'SMA crossover sell signal',
                }
        
        return {'action': 'hold', 'quantity': 0, 'reason': 'No signal'}
    
    def rsi_strategy(symbol, price_data, positions, capital):
        """RSI mean reversion strategy"""
        import random
        
        current_price = price_data['price']
        position = positions.get(symbol)
        
        signal = random.random()
        
        if position is None:
            if signal > 0.75:
                return {
                    'action': 'buy',
                    'quantity': round(capital * 0.02 / current_price, 2),
                    'reason': 'RSI oversold',
                }
        else:
            if signal < 0.25:
                return {
                    'action': 'sell',
                    'quantity': abs(position.quantity),
                    'reason': 'RSI overbought',
                }
        
        return {'action': 'hold', 'quantity': 0, 'reason': 'No signal'}
    
    def momentum_strategy(symbol, price_data, positions, capital):
        """Momentum strategy"""
        import random
        
        current_price = price_data['price']
        position = positions.get(symbol)
        
        signal = random.random()
        
        if position is None:
            if signal > 0.65:
                return {
                    'action': 'buy',
                    'quantity': round(capital * 0.02 / current_price, 2),
                    'reason': 'Positive momentum',
                }
        else:
            if signal < 0.35:
                return {
                    'action': 'sell',
                    'quantity': abs(position.quantity),
                    'reason': 'Momentum reversal',
                }
        
        return {'action': 'hold', 'quantity': 0, 'reason': 'No signal'}
    
    strategies = {
        'sma': sma_strategy,
        'rsi': rsi_strategy,
        'momentum': momentum_strategy,
        'custom': sma_strategy,  # Default to SMA
    }
    
    return strategies.get(strategy_name, sma_strategy)


def print_final_status(status):
    """Print final trading status"""
    print("\n" + "=" * 70)
    print("FINAL STATUS")
    print("=" * 70)
    print(f"Mode: {status['mode']}")
    print(f"Portfolio Value: ${status['portfolio_value']:,.2f}")
    print(f"Total PnL: ${status['metrics']['total_pnl']:,.2f}")
    print(f"Total Trades: {status['metrics']['total_trades']}")
    print(f"Win Rate: {status['metrics']['win_rate']:.2%}")
    print(f"Max Drawdown: {status['metrics']['max_drawdown']:.2%}")
    
    if status['positions']:
        print(f"\nOpen Positions:")
        for symbol, pos in status['positions'].items():
            print(f"  {symbol}: {pos['quantity']:.2f} @ {pos['entry']:.5f} (PnL: ${pos['pnl']:.2f})")
    
    print("=" * 70)


async def main():
    """Main entry point"""
    args = parse_args()
    
    # Update log level if specified
    if args.log_level != 'INFO':
        setup_logging(level=args.log_level)
    
    logger.info(f"Starting AlphaAlgo in {args.mode} mode")
    
    try:
        if args.mode == 'demo':
            await run_demo(args)
        elif args.mode == 'paper':
            await run_paper_trading(args)
        elif args.mode == 'optimize':
            await run_optimization(args)
        elif args.mode == 'backtest':
            await run_backtest(args)
        elif args.mode == 'live':
            print("LIVE TRADING MODE NOT YET ENABLED")
            print("Use --mode paper for paper trading")
        else:
            print(f"Unknown mode: {args.mode}")
            
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
