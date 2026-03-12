"""
Quantitative Analysis Tool Demo
================================

Demonstrates the capabilities of the quant analysis tool.
"""

import asyncio
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

from trading_bot.quant_analysis import QuantAnalyzer


async def demo_returns_analysis():
    """Demo: Analyze strategy returns."""
    print("\n" + "="*60)
    print("DEMO 1: Returns Analysis")
    print("="*60)
    
    # Create sample returns data
    np.random.seed(42)
    dates = pd.date_range(start='2023-01-01', periods=252, freq='D')
    returns = pd.Series(np.random.normal(0.001, 0.02, 252), index=dates)
    benchmark_returns = pd.Series(np.random.normal(0.0008, 0.015, 252), index=dates)
    
    # Initialize analyzer
    analyzer = QuantAnalyzer()
    
    # Analyze returns
    results = analyzer.analyze_returns(returns, benchmark_returns)
    
    print("\nReturns Analysis Results:")
    print(f"  Total Return: {results['total_return']:.2%}")
    print(f"  Annualized Return: {results['annualized_return']:.2%}")
    print(f"  Volatility: {results['volatility']:.2%}")
    print(f"  Sharpe Ratio: {results['sharpe_ratio']:.2f}")
    print(f"  Sortino Ratio: {results['sortino_ratio']:.2f}")
    print(f"  Max Drawdown: {results['max_drawdown']:.2%}")
    print(f"  Calmar Ratio: {results['calmar_ratio']:.2f}")
    print(f"  Win Rate: {results['win_rate']:.2%}")
    print(f"  Profit Factor: {results['profit_factor']:.2f}")
    print(f"  Skewness: {results['skewness']:.2f}")
    print(f"  Kurtosis: {results['kurtosis']:.2f}")
    
    if 'alpha' in results:
        print(f"\nBenchmark Comparison:")
        print(f"  Alpha: {results['alpha']:.4f}")
        print(f"  Beta: {results['beta']:.2f}")
        print(f"  Information Ratio: {results['information_ratio']:.2f}")
        print(f"  Tracking Error: {results['tracking_error']:.2%}")


async def demo_strategy_analysis():
    """Demo: Analyze trading strategy."""
    print("\n" + "="*60)
    print("DEMO 2: Strategy Analysis")
    print("="*60)
    
    # Create sample trade data
    trades = pd.DataFrame({
        'timestamp': pd.date_range(start='2023-01-01', periods=50, freq='W'),
        'symbol': ['EURUSD'] * 50,
        'side': np.random.choice(['buy', 'sell'], 50),
        'quantity': np.random.uniform(1000, 10000, 50),
        'price': np.random.uniform(1.05, 1.15, 50),
        'pnl': np.random.normal(100, 500, 50),
    })
    
    # Create sample price data
    prices = pd.DataFrame({
        'EURUSD': np.random.uniform(1.05, 1.15, 252),
        'GBPUSD': np.random.uniform(1.20, 1.30, 252),
    }, index=pd.date_range(start='2023-01-01', periods=252, freq='D'))
    
    # Initialize analyzer
    analyzer = QuantAnalyzer()
    
    # Analyze strategy
    results = analyzer.analyze_strategy(trades, prices)
    
    print("\nStrategy Analysis Results:")
    print(f"\n  Trade Statistics:")
    trade_stats = results['trade_statistics']
    print(f"    Total Trades: {trade_stats['total_trades']}")
    print(f"    Winning Trades: {trade_stats['winning_trades']}")
    print(f"    Losing Trades: {trade_stats['losing_trades']}")
    print(f"    Avg Trade P&L: ${trade_stats['avg_trade_pnl']:.2f}")
    print(f"    Avg Win: ${trade_stats['avg_win']:.2f}")
    print(f"    Avg Loss: ${trade_stats['avg_loss']:.2f}")
    
    print(f"\n  Price Statistics:")
    price_stats = results['price_statistics']
    print(f"    Mean Return: {price_stats['mean_return']:.4f}")
    print(f"    Volatility: {price_stats['volatility']:.4f}")
    print(f"    Min Price: {price_stats['min_price']:.4f}")
    print(f"    Max Price: {price_stats['max_price']:.4f}")


async def demo_factor_analysis():
    """Demo: Factor analysis."""
    print("\n" + "="*60)
    print("DEMO 3: Factor Analysis")
    print("="*60)
    
    # Create sample returns and factors
    np.random.seed(42)
    dates = pd.date_range(start='2023-01-01', periods=252, freq='D')
    
    returns = pd.Series(np.random.normal(0.001, 0.02, 252), index=dates)
    
    factors = pd.DataFrame({
        'market': np.random.normal(0.0008, 0.015, 252),
        'size': np.random.normal(0.0002, 0.01, 252),
        'value': np.random.normal(0.0003, 0.012, 252),
        'momentum': np.random.normal(0.0005, 0.018, 252),
    }, index=dates)
    
    # Initialize analyzer
    analyzer = QuantAnalyzer()
    
    # Run factor analysis
    results = analyzer.run_factor_analysis(returns, factors)
    
    print("\nFactor Analysis Results:")
    print(f"  Alpha: {results['alpha']:.6f}")
    print(f"  R-squared: {results['r_squared']:.4f}")
    print(f"\n  Factor Exposures:")
    for factor, exposure in results['factor_exposures'].items():
        print(f"    {factor}: {exposure:.4f}")


async def demo_portfolio_optimization():
    """Demo: Portfolio optimization."""
    print("\n" + "="*60)
    print("DEMO 4: Portfolio Optimization")
    print("="*60)
    
    # Create sample asset returns
    np.random.seed(42)
    dates = pd.date_range(start='2023-01-01', periods=252, freq='D')
    
    returns = pd.DataFrame({
        'EURUSD': np.random.normal(0.0008, 0.015, 252),
        'GBPUSD': np.random.normal(0.0006, 0.018, 252),
        'USDJPY': np.random.normal(0.0005, 0.012, 252),
        'AUDUSD': np.random.normal(0.0007, 0.020, 252),
    }, index=dates)
    
    # Initialize analyzer
    analyzer = QuantAnalyzer()
    
    # Optimize portfolio
    results = analyzer.optimize_portfolio(returns)
    
    print("\nPortfolio Optimization Results:")
    print(f"  Expected Return: {results['expected_return']:.4f}")
    print(f"  Expected Volatility: {results['expected_volatility']:.4f}")
    print(f"  Sharpe Ratio: {results['sharpe_ratio']:.2f}")
    print(f"\n  Optimal Weights:")
    for asset, weight in results['weights'].items():
        print(f"    {asset}: {weight:.2%}")


async def demo_comprehensive_report():
    """Demo: Get comprehensive report."""
    print("\n" + "="*60)
    print("DEMO 5: Comprehensive Report")
    print("="*60)
    
    # Initialize analyzer
    analyzer = QuantAnalyzer()
    
    # Get report
    report = analyzer.get_report()
    
    print("\nQuant Analyzer Report:")
    print(f"  Timestamp: {report['timestamp']}")
    print(f"  Analyzer: {report['analyzer']}")
    print(f"  Status: {report['status']}")
    print(f"\n  Capabilities:")
    for capability in report['capabilities']:
        print(f"    - {capability}")


async def main():
    """Run all demos."""
    print("\n" + "="*70)
    print("QUANTITATIVE ANALYSIS TOOL DEMONSTRATION")
    print("="*70)
    
    await demo_returns_analysis()
    await demo_strategy_analysis()
    await demo_factor_analysis()
    await demo_portfolio_optimization()
    await demo_comprehensive_report()
    
    print("\n" + "="*70)
    print("All demos completed successfully!")
    print("="*70)
    print("\nThe quant analysis tool provides:")
    print("  - Returns analysis with 12+ metrics")
    print("  - Strategy analysis (trades, prices, positions)")
    print("  - Factor analysis and decomposition")
    print("  - Portfolio optimization")
    print("  - Risk analytics")
    print("  - Performance attribution")
    print("\nIntegrate with your trading system for comprehensive quantitative insights!")
    print("="*70 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
