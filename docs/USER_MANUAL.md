# Trading Bot User Manual

**Version:** 1.0  
**Last Updated:** {date}  
**Status:** Production Ready

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [System Requirements](#system-requirements)
3. [Installation](#installation)
4. [Configuration](#configuration)
5. [Running the Bot](#running-the-bot)
6. [Trading Modes](#trading-modes)
7. [Risk Management](#risk-management)
8. [Monitoring](#monitoring)
9. [Troubleshooting](#troubleshooting)
10. [API Reference](#api-reference)

---

## Quick Start

### 1. Clone and Setup

```bash
git clone <repository-url>
cd "trading bot"
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt  # For development
```

### 3. Configure Secrets

```bash
py -m trading_bot.security.secrets_manager
# Or set environment variables:
set TRADING_BOT_MT5_LOGIN=your_login
set TRADING_BOT_MT5_PASSWORD=your_password
set TRADING_BOT_MT5_SERVER=your_server
```

### 4. Run Paper Trading

```bash
python main.py --mode paper --symbol EURUSD
```

---

## System Requirements

### Minimum Requirements
- **OS:** Windows 10/11, Linux, macOS
- **Python:** 3.9 or higher
- **RAM:** 8 GB
- **Disk:** 2 GB free space
- **Network:** Stable internet connection

### Recommended Requirements
- **OS:** Windows 11 or Ubuntu 22.04
- **Python:** 3.11 or higher
- **RAM:** 16 GB
- **Disk:** 10 GB SSD
- **Network:** Low-latency connection

### Software Dependencies
- MetaTrader 5 terminal (for live trading)
- Docker (optional, for containerized deployment)
- PostgreSQL 15+ (for data storage)
- Redis 7+ (for caching)

---

## Installation

### Standard Installation

```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Run setup
python setup.py install
```

### Docker Installation

```bash
# Build and run with Docker Compose
docker-compose -f docker-compose.production.yml up -d

# Or use the deployment script
./scripts/deploy.sh deploy
```

---

## Configuration

### Configuration Files

Main configuration is stored in `config/config.yaml`:

```yaml
# Trading Settings
trading:
  mode: paper  # paper or live
  symbols:
    - EURUSD
    - GBPUSD
    - USDJPY
  default_timeframe: H1
  max_positions: 5

# Risk Management
risk:
  max_position_size: 0.05
  max_daily_loss: 100.0
  max_drawdown: 5.0
  stop_loss_pct: 2.0
  take_profit_pct: 4.0

# MT5 Connection
mt5:
  login: ${MT5_LOGIN}
  server: ${MT5_SERVER}
  timeout: 30

# ML/AI Settings
ml:
  enabled: true
  model_update_interval: 86400  # seconds
  min_confidence: 0.65

# Notifications
notifications:
  email:
    enabled: true
    smtp_server: smtp.gmail.com
    smtp_port: 587
    username: ${EMAIL_USER}
    password: ${EMAIL_PASS}
  telegram:
    enabled: false
    bot_token: ${TELEGRAM_TOKEN}
    chat_id: ${TELEGRAM_CHAT_ID}
```

### Environment Variables

Create `.env` file:

```env
# MT5 Credentials
MT5_LOGIN=12345678
MT5_PASSWORD=your_password
MT5_SERVER=MetaQuotes-Demo

# Database
DATABASE_URL=postgresql://trading_bot:password@localhost:5432/trading_bot
REDIS_URL=redis://localhost:6379

# API Keys (optional)
NEWS_API_KEY=your_news_api_key
SENTIMENT_API_KEY=your_sentiment_key

# Notifications
EMAIL_USER=your_email@gmail.com
EMAIL_PASS=your_app_password
```

---

## Running the Bot

### Interactive Mode

```bash
# Run with interactive menu
RUN_INTEGRATED_SYSTEM.bat
```

### Command Line

```bash
# Paper trading (default)
python main.py --mode paper --symbol EURUSD --timeframe H1

# Multiple symbols
python main.py --symbols EURUSD,GBPUSD,USDJPY --mode paper

# With ML/AI enabled
python main.py --symbol EURUSD --use-ml --use-transformer

# Live trading (requires credentials)
python main.py --mode live --symbol EURUSD

# Full integration with all features
python main.py --full-integration --symbol EURUSD --adaptive --self-improve
```

### Background Services

```bash
# Start background services
python background_services.py --start

# Stop background services
python background_services.py --stop

# Check status
python background_services.py --status
```

---

## Trading Modes

### Paper Trading (Recommended for Testing)

- Simulates trades without real money
- Uses real market data
- Tracks virtual PnL
- Validates strategies risk-free

```bash
python main.py --mode paper --symbol EURUSD
```

### Live Trading

- Executes real trades via MT5
- Requires valid credentials
- Real money at risk
- Use with extreme caution

```bash
python main.py --mode live --symbol EURUSD
```

### Backtesting

- Tests strategies on historical data
- Validates performance
- No real-time execution

```bash
python -m trading_bot.backtesting.run --strategy ml --period 90d
```

---

## Risk Management

### Automatic Protections

The bot includes multiple risk management layers:

1. **Position Size Limits**
   - Maximum position size: 5% of account (configurable)
   - Prevents over-leveraging

2. **Daily Loss Limits**
   - Maximum daily loss: $100 (configurable)
   - Trading stops when limit reached

3. **Drawdown Protection**
   - Maximum drawdown: 5% (configurable)
   - Circuit breaker at limit

4. **Stop Loss / Take Profit**
   - Automatic stop-loss: 2%
   - Take-profit targets: 4%

### Risk Configuration

Edit `config/config.yaml`:

```yaml
risk:
  max_position_size: 0.05
  max_daily_loss: 100.0
  max_drawdown: 5.0
  max_correlation_exposure: 0.04
  margin_call_level: 150
```

### Circuit Breakers

The system monitors:
- Broker connection status
- Database connectivity
- API response times
- Error rates

If thresholds are exceeded, trading is automatically paused.

---

## Monitoring

### Real-Time Dashboard

Access the monitoring dashboard:

```bash
# Start Grafana (if using Docker)
docker-compose -f docker-compose.production.yml up grafana

# Access at http://localhost:3000
# Default login: admin / admin123
```

### Metrics Available

- **Trading Metrics:** Win rate, PnL, trade count, position sizes
- **Risk Metrics:** Drawdown, margin level, exposure
- **Performance:** Latency, execution times, throughput
- **System Health:** CPU, memory, disk usage, error rates

### Prometheus Metrics

Metrics exposed at `http://localhost:9090/metrics`:

- `trading_bot_trades_executed_total`
- `trading_bot_daily_pnl`
- `trading_bot_drawdown_percent`
- `trading_bot_open_positions`
- `trading_bot_request_duration_seconds`

### Alerts

Configure alerts in `deploy/prometheus/alerts.yml`:

- High drawdown (>5%)
- Daily loss limit reached
- Broker disconnection
- High error rate (>10%)
- System resource exhaustion

---

## Troubleshooting

### Common Issues

#### MT5 Connection Failed

**Symptom:** `MT5ConnectionError: Failed to connect to terminal`

**Solutions:**
1. Ensure MT5 terminal is running
2. Check credentials in `.env` file
3. Verify server name matches exactly
4. Check firewall settings

#### Database Connection Failed

**Symptom:** `Database connection failed`

**Solutions:**
1. Start PostgreSQL: `docker-compose up postgres`
2. Check DATABASE_URL in `.env`
3. Verify database exists: `createdb trading_bot`

#### Import Errors

**Symptom:** `ModuleNotFoundError`

**Solutions:**
1. Activate virtual environment
2. Reinstall requirements: `pip install -r requirements.txt`
3. Check Python version: `python --version` (needs 3.9+)

#### High Memory Usage

**Symptom:** System running out of memory

**Solutions:**
1. Reduce max positions in config
2. Disable unused features (transformer, RL)
3. Increase swap space
4. Use `--light-mode` flag

### Logs

Check logs for detailed error information:

```bash
# View logs
tail -f logs/trading_bot.log

# View specific component logs
tail -f logs/risk.log
tail -f logs/execution.log
```

### Getting Help

1. Check documentation: `docs/INDEX.md`
2. Review troubleshooting guides: `docs/troubleshooting/`
3. Check system status: `python main.py --status`
4. Enable debug mode: `python main.py --debug`

---

## API Reference

### Core Classes

#### MT5Interface

```python
from trading_bot.data.mt5_interface import MT5Interface

with MT5Interface() as mt5:
    # Get account info
    account = mt5.account_info()
    
    # Get historical data
    rates = mt5.get_rates("EURUSD", "H1", count=100)
    
    # Place order
    result = mt5.place_order(
        symbol="EURUSD",
        side="buy",
        volume=0.01,
        price=1.0850,
        sl=1.0800,
        tp=1.0950
    )
```

#### StrategyEngine

```python
from trading_bot.strategy.strategy_engine import StrategyEngine

engine = StrategyEngine(config={
    'timeframe': 'H1',
    'symbols': ['EURUSD']
})

# Generate signals
signals = engine.generate_signals(data)
```

#### RiskManager

```python
from trading_bot.risk.risk_manager import RiskManager

risk = RiskManager(
    max_position_size=0.05,
    max_daily_loss=100.0
)

# Validate order
if risk.validate_order(order):
    # Execute order
    pass
```

### Command Line Interface

```bash
# Main entry point
python main.py [options]

Options:
  --mode {paper,live}     Trading mode
  --symbol SYMBOL         Trading symbol
  --symbols SYMBOLS       Comma-separated symbols
  --timeframe TF          Timeframe (M1, M5, M15, H1, H4, D1)
  --bars N              Number of bars to load
  --use-ml              Enable ML predictions
  --use-transformer     Enable transformer model
  --use-rl              Enable reinforcement learning
  --full-integration    Enable all integrations
  --adaptive            Enable adaptive learning
  --self-improve        Enable self-improvement
  --debug               Enable debug logging
  --help                Show help message
```

---

## Best Practices

### Before Going Live

1. **Run Paper Trading** for at least 2 weeks
2. **Validate Performance** meets your targets
3. **Test Risk Management** thoroughly
4. **Start Small** with minimal position sizes
5. **Monitor Closely** for first 72 hours

### Daily Operations

1. Check system health dashboard
2. Review overnight trades
3. Verify risk limits are active
4. Check for any alerts or warnings

### Weekly Maintenance

1. Review performance metrics
2. Update ML models if needed
3. Check logs for errors
4. Backup configuration and data

---

## Security

### Secrets Management

Use the secrets manager for secure credential storage:

```bash
python -m trading_bot.security.secrets_manager
```

### API Security

- Never commit credentials to git
- Use environment variables or secrets manager
- Rotate API keys regularly
- Enable 2FA on all accounts

### Network Security

- Use VPN when accessing remotely
- Configure firewall rules
- Enable SSL/TLS for all connections

---

## Support

### Resources

- **Documentation:** `docs/INDEX.md`
- **API Docs:** `docs/api/`
- **Architecture:** `docs/architecture/`
- **Troubleshooting:** `docs/troubleshooting/`

### Emergency Procedures

If system malfunction:

1. Stop all trading: Press Ctrl+C or run `python main.py --stop`
2. Check logs for errors
3. Contact support with log files
4. Do not restart until issue resolved

---

## License

See LICENSE file for details.

---

*This manual is automatically generated. For latest updates, check the repository.*
