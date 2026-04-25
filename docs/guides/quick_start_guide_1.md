# Elite Trading Bot Quick Start Guide

This guide will help you quickly get started with the Elite Trading Bot, including its advanced ML capabilities, execution optimization algorithms, and emotional tracking features.

## Prerequisites

1. Python 3.8+ installed
2. MetaTrader 5 installed and configured
3. Required packages installed: `pip install -r requirements.txt`

## Basic Usage

### Command Line Interface

The simplest way to use the trading bot is through the command line interface:

```bash
# Basic usage with traditional strategy
python main.py --mode paper --symbol EURUSD --timeframe M15 --bars 300

# Using ML-enhanced strategy
python main.py --mode paper --symbol EURUSD --timeframe M15 --bars 300 --use-ml

# Using ML strategy with Smart Order Router execution
python main.py --mode paper --symbol EURUSD --timeframe M15 --bars 300 --use-ml --execution-algo smart

# Full-featured setup with emotional tracking and sentiment analysis
python main.py --mode paper --symbol EURUSD --timeframe M15 --bars 300 --use-ml --execution-algo smart --track-emotions --use-sentiment
```

### Configuration

The bot uses a configuration file located at `trading_bot/config/config.yaml`. You should update this file with your MT5 credentials and preferences:

```yaml
mt5:
  username: "your_username"
  password: "your_password"
  server: "your_broker_server"
  path: "C:/Program Files/MetaTrader 5/terminal64.exe"  # Adjust path as needed

risk:
  max_risk_percent: 1.0
  default_stop_loss_pips: 50
  default_take_profit_pips: 100
```

## Advanced Features

### ML-Enhanced Strategy

The ML strategy engine combines traditional technical analysis with machine learning models:

```python
from trading_bot.strategy.ml_strategy import MLStrategyEngine
from trading_bot.data import MT5Interface

mt5 = MT5Interface()
mt5.connect()

# Initialize ML strategy with all features
strategy = MLStrategyEngine(
    mt5,
    symbol="EURUSD",
    use_price_prediction=True,
    use_pattern_recognition=True,
    use_sentiment=True
)

# Analyze market data
df = mt5.get_ohlc("EURUSD", "M15", 300)
signals = strategy.analyse(df)
```

### Execution Optimization

Choose from different execution algorithms to optimize your order execution:

```python
from trading_bot.execution.paper_executor import PaperExecutor
from trading_bot.execution.algorithms import TWAPExecutor, VWAPExecutor, SmartOrderRouter
from trading_bot.risk import RiskManager

# Initialize base executor
risk = RiskManager(mt5)
base_executor = PaperExecutor(mt5, risk)

# Choose an execution algorithm
executor = SmartOrderRouter(base_executor)  # or TWAPExecutor or VWAPExecutor

# Execute signals
current_price = mt5.get_current_price("EURUSD")
trades = executor.process(signals, current_price)
```

### Emotional Tracking

Track and analyze the emotional impact on trading performance:

```python
from trading_bot.analytics.emotional_tracker import EmotionalStateTracker
from trading_bot.analytics.enhanced_performance import EnhancedPerformanceAnalytics

# Initialize emotional tracker
emotional_tracker = EmotionalStateTracker()

# Record emotional states before and after trading
emotional_tracker.record_state({
    'confidence': 0.7,
    'fear': 0.3,
    'excitement': 0.5
})

# After trading, analyze performance with emotional insights
analytics = EnhancedPerformanceAnalytics(trades, emotional_tracker)
summary = analytics.summary()
```

## Example Scripts

The `examples/` directory contains ready-to-use example scripts:

1. `advanced_trading_example.py` - Demonstrates all features in a single script
2. `library_usage_example.py` - Shows how to use the trading bot as a library in a custom application

To run an example:

```bash
python examples/advanced_trading_example.py
```

## Testing

Run the test suite to verify everything is working correctly:

```bash
# Run all tests
python -m pytest

# Run specific test categories
python -m pytest -m ml
python -m pytest -m execution
python -m pytest -m emotional
python -m pytest -m end_to_end

# Use the custom test runner
python trading_bot/tests/run_tests.py
python trading_bot/tests/run_tests.py end_to_end
```

## Next Steps

1. Explore the `docs/` directory for detailed documentation
2. Check out the integration tests in `trading_bot/tests/` to understand how components work together
3. Review the README for a complete overview of all features and capabilities

## Troubleshooting

If you encounter issues:

1. Check your MT5 connection and credentials
2. Verify that all dependencies are installed correctly
3. Look for error logs in the `logs/` directory
4. Run the tests to identify any component failures

For more detailed information, refer to the full documentation in the README and `docs/` directory.
