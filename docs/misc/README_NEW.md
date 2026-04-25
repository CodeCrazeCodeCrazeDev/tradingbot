# AlphaAlgo Trading Bot

**Advanced Algorithmic Trading System for MetaTrader 5**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure your settings
cp .env.template .env
# Edit .env with your MT5 credentials

# 3. Run the bot
run.bat          # Windows - shows menu
python main.py   # Direct execution (paper mode)
```

## Features

### Core Trading Capabilities
- **Multi-Strategy Engine** - Technical analysis, ML predictions, sentiment analysis
- **Smart Execution** - TWAP, VWAP, smart order routing
- **Risk Management** - Position sizing, drawdown protection, circuit breakers
- **Real-time Analysis** - Market structure, liquidity, order flow

### AI/ML Integration
- **Price Prediction** - Transformer-based forecasting
- **Pattern Recognition** - CNN-based pattern detection
- **Sentiment Analysis** - News and social media sentiment
- **Reinforcement Learning** - Strategy optimization with PPO/CQL

### Safety Systems
- **Emergency Kill Switch** - Instant position closure
- **Circuit Breakers** - Automatic trading halts
- **Resource Watchdog** - Memory and CPU monitoring
- **Connectivity Monitor** - Broker connection health

## Architecture

```
trading_bot/
├── core/           # Main trading loop and orchestration
├── data/           # Market data and MT5 interface
├── strategy/       # Strategy engine and signal generation
├── execution/      # Order execution and routing
├── risk/           # Risk management (MASTER implementation)
├── ml/             # Machine learning models
├── analysis/       # Market analysis tools
├── safety/         # Safety and monitoring systems
└── unified_architecture/  # 6-layer unified system
```

### Key Modules

| Module | Description | Entry Point |
|--------|-------------|-------------|
| Risk Manager | Consolidated risk management | `trading_bot.risk.MasterRiskManager` |
| Executor | Paper/Live execution | `trading_bot.execution.PaperExecutor` |
| Strategy | Signal generation | `trading_bot.strategy.StrategyEngine` |
| Analysis | Market analysis | `trading_bot.analysis` |
| ML | Predictions | `trading_bot.ml.PricePredictor` |

## Configuration

Main configuration file: `config/alphaalgo_config.yaml`

```yaml
# Key settings
trading:
  mode: paper          # paper or live
  symbol: EURUSD
  timeframe: M15
  risk_per_trade: 1.0  # percent

risk:
  max_drawdown: 20.0   # percent
  max_daily_loss: 5.0  # percent
  max_positions: 5
```

## Usage Examples

### Paper Trading
```python
from trading_bot.core import TradingSystem

system = TradingSystem()
await system.start()
```

### Custom Strategy
```python
from trading_bot.strategy import StrategyEngine, BaseStrategy

class MyStrategy(BaseStrategy):
    def generate_signal(self, data):
        # Your logic here
        return signal

engine = StrategyEngine()
engine.add_strategy(MyStrategy())
```

### Risk Management
```python
from trading_bot.risk import MasterRiskManager

risk_manager = MasterRiskManager()
position_size = risk_manager.calculate_position_size(
    symbol='EURUSD',
    entry_price=1.1000,
    stop_loss=1.0950,
    account_balance=10000
)
```

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run specific test category
pytest tests/test_risk.py -v

# Run with coverage
pytest tests/ --cov=trading_bot --cov-report=html
```

## Documentation

| Document | Description |
|----------|-------------|
| `GETTING_STARTED.md` | Quick start guide |
| `docs/ARCHITECTURE.md` | System architecture |
| `docs/API_REFERENCE.md` | API documentation |
| `docs/CONFIGURATION.md` | Configuration guide |

## Project Status

- ✅ Core trading system
- ✅ Risk management (consolidated)
- ✅ Paper trading execution
- ✅ ML predictions
- ✅ Safety systems
- ⚠️ Live trading (requires MT5 setup)
- ⚠️ Advanced ML features (optional dependencies)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `pytest tests/`
5. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Support

- 📖 Documentation: `docs/` folder
- 🐛 Issues: GitHub Issues
- 💬 Discussions: GitHub Discussions
