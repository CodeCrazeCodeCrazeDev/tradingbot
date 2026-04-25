# Quantitative Analysis Tool - Complete Guide

## Overview

The Quantitative Analysis Tool is a comprehensive analytics module for the AlphaAlgo trading platform, providing advanced statistical analysis, performance metrics, factor analysis, and portfolio optimization capabilities.

## Features

### 1. Returns Analysis (12+ Metrics)
- **Total Return**: Cumulative return over the period
- **Annualized Return**: Annualized performance metric
- **Volatility**: Annualized standard deviation of returns
- **Sharpe Ratio**: Risk-adjusted return metric
- **Sortino Ratio**: Downside risk-adjusted return
- **Max Drawdown**: Maximum peak-to-trough decline
- **Calmar Ratio**: Return to max drawdown ratio
- **Win Rate**: Percentage of profitable periods
- **Profit Factor**: Ratio of gross profits to gross losses
- **Skewness**: Distribution asymmetry
- **Kurtosis**: Distribution tail heaviness

### 2. Benchmark Comparison
- **Alpha**: Excess return vs benchmark
- **Beta**: Systematic risk exposure
- **Information Ratio**: Active return per unit of tracking error
- **Tracking Error**: Standard deviation of active returns

### 3. Strategy Analysis
- **Trade Statistics**: Win/loss analysis, average P&L
- **Price Statistics**: Return and volatility metrics
- **Position Statistics**: Position sizing and turnover

### 4. Factor Analysis
- **Factor Exposures**: Regression-based factor loadings
- **Alpha Decomposition**: Skill vs factor-based returns
- **R-squared**: Explanatory power of factors

### 5. Portfolio Optimization
- **Mean-Variance Optimization**: Optimal weight allocation
- **Expected Return**: Portfolio-level return forecast
- **Expected Volatility**: Portfolio-level risk
- **Sharpe Ratio**: Portfolio efficiency metric

## Installation

The quant analysis tool is already integrated into the trading bot. No additional installation required.

## Usage

### Basic Usage

```python
from trading_bot.quant_analysis import QuantAnalyzer
import pandas as pd
import numpy as np

# Initialize analyzer
analyzer = QuantAnalyzer()

# Create sample returns
returns = pd.Series(np.random.normal(0.001, 0.02, 252))

# Analyze returns
results = analyzer.analyze_returns(returns)

print(f"Sharpe Ratio: {results['sharpe_ratio']:.2f}")
print(f"Max Drawdown: {results['max_drawdown']:.2%}")
```

### With Benchmark Comparison

```python
# Add benchmark for comparison
benchmark_returns = pd.Series(np.random.normal(0.0008, 0.015, 252))

results = analyzer.analyze_returns(returns, benchmark_returns)

print(f"Alpha: {results['alpha']:.4f}")
print(f"Beta: {results['beta']:.2f}")
print(f"Information Ratio: {results['information_ratio']:.2f}")
```

### Strategy Analysis

```python
# Analyze complete trading strategy
trades = pd.DataFrame({
    'timestamp': pd.date_range('2023-01-01', periods=50, freq='W'),
    'symbol': ['EURUSD'] * 50,
    'pnl': np.random.normal(100, 500, 50),
})

prices = pd.DataFrame({
    'EURUSD': np.random.uniform(1.05, 1.15, 252),
}, index=pd.date_range('2023-01-01', periods=252, freq='D'))

results = analyzer.analyze_strategy(trades, prices)
print(results['trade_statistics'])
```

### Factor Analysis

```python
# Run factor analysis
factors = pd.DataFrame({
    'market': np.random.normal(0.0008, 0.015, 252),
    'size': np.random.normal(0.0002, 0.01, 252),
    'value': np.random.normal(0.0003, 0.012, 252),
})

results = analyzer.run_factor_analysis(returns, factors)
print(f"Factor Exposures: {results['factor_exposures']}")
```

### Portfolio Optimization

```python
# Optimize portfolio weights
asset_returns = pd.DataFrame({
    'EURUSD': np.random.normal(0.0008, 0.015, 252),
    'GBPUSD': np.random.normal(0.0006, 0.018, 252),
    'USDJPY': np.random.normal(0.0005, 0.012, 252),
})

results = analyzer.optimize_portfolio(asset_returns)
print(f"Optimal Weights: {results['weights']}")
print(f"Expected Sharpe: {results['sharpe_ratio']:.2f}")
```

## Service Integration

The quant analysis tool is available as a service in the trading bot:

```python
# The service is automatically registered
# Service name: "quant_analysis"
# Dependencies: ["data"]
# Priority: NORMAL
```

### Service Configuration

Add to `config/alphaalgo_master_config.yaml`:

```yaml
services:
  quant_analysis:
    enabled: true
    interval: 300  # Analysis interval in seconds
```

## API Reference

### QuantAnalyzer Class

#### Methods

**`analyze_returns(returns, benchmark_returns=None)`**
- Comprehensive returns analysis with 12+ metrics
- Args:
  - `returns`: pd.Series or np.ndarray of strategy returns
  - `benchmark_returns`: Optional benchmark returns for comparison
- Returns: Dict with all metrics

**`analyze_strategy(trades, prices, positions=None)`**
- Complete strategy analysis
- Args:
  - `trades`: pd.DataFrame with trade history
  - `prices`: pd.DataFrame with price data
  - `positions`: Optional position history
- Returns: Dict with trade, price, and position statistics

**`run_factor_analysis(returns, factors)`**
- Factor decomposition analysis
- Args:
  - `returns`: pd.Series of strategy returns
  - `factors`: pd.DataFrame of factor returns
- Returns: Dict with factor exposures and alpha

**`optimize_portfolio(returns, constraints=None)`**
- Portfolio weight optimization
- Args:
  - `returns`: pd.DataFrame of asset returns
  - `constraints`: Optional constraints dict
- Returns: Dict with optimal weights and metrics

**`get_report()`**
- Get comprehensive analyzer status
- Returns: Dict with capabilities and status

## Examples

Run the comprehensive demo:

```bash
python examples/quant_analysis_demo.py
```

This demonstrates:
1. Returns analysis with benchmark comparison
2. Strategy analysis (trades, prices)
3. Factor analysis
4. Portfolio optimization
5. Comprehensive reporting

## Performance Metrics Reference

### Risk-Adjusted Returns

- **Sharpe Ratio**: (Return - RiskFreeRate) / Volatility
  - > 1.0: Good
  - > 2.0: Excellent
  - > 3.0: Outstanding

- **Sortino Ratio**: (Return - RiskFreeRate) / DownsideVolatility
  - Focuses on downside risk only
  - Generally higher than Sharpe

- **Calmar Ratio**: AnnualizedReturn / MaxDrawdown
  - Measures return per unit of worst loss
  - > 1.0 is desirable

### Risk Metrics

- **Max Drawdown**: Largest peak-to-trough decline
  - < 10%: Low risk
  - 10-20%: Moderate risk
  - > 20%: High risk

- **Volatility**: Annualized standard deviation
  - Measures return variability
  - Lower is generally better

### Trading Metrics

- **Win Rate**: Percentage of profitable trades
  - 50%+: Breakeven or better
  - 60%+: Strong
  - 70%+: Excellent

- **Profit Factor**: GrossProfits / GrossLosses
  - > 1.0: Profitable
  - > 1.5: Good
  - > 2.0: Excellent

## Integration with Main Trading Loop

The quant analysis service automatically processes:
- Market data updates
- Trade executions
- Performance metrics

Access via event bus:

```python
# Subscribe to analysis events
event_bus.subscribe(
    "my_component",
    [EventTypes.ANALYSIS_COMPLETE],
    callback
)
```

## Best Practices

1. **Regular Analysis**: Run analysis at least daily
2. **Multiple Timeframes**: Analyze over different periods
3. **Benchmark Comparison**: Always compare to relevant benchmark
4. **Factor Attribution**: Understand sources of returns
5. **Risk Monitoring**: Track drawdowns and volatility continuously
6. **Portfolio Review**: Reoptimize weights periodically

## Troubleshooting

### Issue: Import Error
```python
# Solution: Ensure module is in PYTHONPATH
import sys
sys.path.append('c:/Users/peterson/trading bot')
from trading_bot.quant_analysis import QuantAnalyzer
```

### Issue: Insufficient Data
```python
# Solution: Ensure minimum data points
if len(returns) < 30:
    print("Warning: Insufficient data for reliable analysis")
```

### Issue: NaN Values
```python
# Solution: Clean data before analysis
returns = returns.dropna()
```

## Advanced Features (Coming Soon)

- Statistical hypothesis testing
- Advanced risk models (VaR, CVaR)
- Market microstructure analysis
- Performance attribution
- Backtest analytics
- Monte Carlo simulation

## Support

For issues or questions:
1. Check the demo: `examples/quant_analysis_demo.py`
2. Review this guide
3. Check service logs for errors

## Files Created

1. `trading_bot/quant_analysis/__init__.py` - Module exports
2. `trading_bot/quant_analysis/quant_analyzer.py` - Main analyzer (350+ lines)
3. `trading_bot/services/quant_analysis_service.py` - Service wrapper
4. `examples/quant_analysis_demo.py` - Comprehensive demo
5. `QUANT_ANALYSIS_TOOL_GUIDE.md` - This guide

## Summary

The Quantitative Analysis Tool provides institutional-grade analytics for your trading strategies:

- **12+ Performance Metrics**: Comprehensive returns analysis
- **Benchmark Comparison**: Alpha, beta, information ratio
- **Factor Analysis**: Understand return sources
- **Portfolio Optimization**: Optimal weight allocation
- **Service Integration**: Automatic analysis in main loop
- **Production Ready**: Tested and documented

Start using it today to gain deeper insights into your trading performance!
