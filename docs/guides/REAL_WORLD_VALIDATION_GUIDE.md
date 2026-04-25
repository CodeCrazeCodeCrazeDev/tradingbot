# AlphaAlgo Real-World Validation Guide

## Overview

This guide covers the complete process for validating your trading bot before deploying with real capital. Follow these steps carefully to minimize risk and ensure your strategy works in live market conditions.

## Table of Contents

1. [Paper Trading Phase](#paper-trading-phase)
2. [Live Trading Phase](#live-trading-phase)
3. [Ongoing Monitoring](#ongoing-monitoring)
4. [Scaling Strategy](#scaling-strategy)
5. [Emergency Procedures](#emergency-procedures)

---

## Paper Trading Phase

### Purpose
Paper trading validates your strategy with simulated trades using realistic market conditions (slippage, spreads, latency) without risking real capital.

### Requirements to Pass
| Metric | Minimum Requirement |
|--------|---------------------|
| Total Trades | ≥ 50 |
| Trading Days | ≥ 7 |
| Win Rate | ≥ 45% |
| Profit Factor | ≥ 1.2 |
| Max Drawdown | ≤ 15% |
| Sharpe Ratio | ≥ 0.5 |
| Max Consecutive Losses | ≤ 8 |
| Average R:R Ratio | ≥ 1.5 |

### How to Start Paper Trading

```bash
# Option 1: Interactive launcher
RUN_PAPER_TRADING.bat

# Option 2: Command line
python run_paper_trading.py

# Option 3: Run demo trades for testing
python run_paper_trading.py --demo 50

# Option 4: View validation report
python run_paper_trading.py --report
```

### Paper Trading Configuration

Edit `config/paper_trading_config.yaml`:

```yaml
paper_trading:
  initial_capital: 10000.0
  simulation:
    slippage_bps: 2.0
    commission_pct: 0.001
    spread_simulation: true
    typical_spread_pips: 1.5

validation:
  min_paper_days: 7
  min_trades: 50
  thresholds:
    min_win_rate: 0.45
    min_profit_factor: 1.2
    max_drawdown: 0.15
```

### Interpreting Results

After paper trading, run:
```bash
python run_paper_trading.py --validate-only
```

This generates a comprehensive report showing:
- Performance metrics
- Validation status (PASSED/FAILED)
- Specific checks that passed/failed
- Recommendations for improvement

---

## Live Trading Phase

### Prerequisites
✅ Paper trading validation PASSED  
✅ Broker credentials configured  
✅ Risk limits reviewed and set  
✅ Emergency contacts configured  
✅ Backup systems tested  

### Capital Stages

We use progressive capital scaling to minimize risk:

| Stage | Capital | Description | Requirements |
|-------|---------|-------------|--------------|
| 1 | $100 | Initial validation | Pass paper trading |
| 2 | $250 | Confirmation | 20+ live trades, 50%+ win rate |
| 3 | $500 | Scaling | 50+ live trades, 48%+ win rate |
| 4 | $1000 | Full deployment | 100+ live trades, 45%+ win rate |

### How to Start Live Trading

```bash
# Check readiness first
python run_live_trading.py --check-only

# Dry run (mock broker)
python run_live_trading.py --stage 1 --dry-run

# Start Stage 1 live trading
python run_live_trading.py --stage 1

# Or use the launcher
RUN_LIVE_TRADING.bat
```

### Live Trading Configuration

Edit `config/live_trading_config.yaml`:

```yaml
live_trading:
  initial_capital_limit: 500.0
  
  broker:
    type: mt5
    mt5:
      login: ${MT5_LOGIN}
      password: ${MT5_PASSWORD}
      server: ${MT5_SERVER}

risk:
  max_position_size_pct: 2.0
  max_risk_per_trade_pct: 0.5
  max_daily_loss_pct: 2.0
  max_drawdown_pct: 10.0

emergency:
  kill_switch:
    enabled: true
    triggers:
      - max_consecutive_losses: 5
      - daily_loss_pct: 3.0
      - drawdown_pct: 12.0
```

### Setting Up Broker Credentials

Create a `.env` file in the project root:

```env
# MetaTrader 5
MT5_LOGIN=your_login
MT5_PASSWORD=your_password
MT5_SERVER=your_broker_server

# Alerts
ALERT_EMAIL=your@email.com
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
```

---

## Ongoing Monitoring

### Real-Time Dashboard

Start the monitoring dashboard:

```bash
python -c "from trading_bot.dashboard.realtime_dashboard import run_dashboard; run_dashboard()"
```

Access at: http://localhost:8050

Features:
- Real-time equity curve
- P&L distribution
- Open positions
- Recent trades
- Risk metrics
- System health
- Alerts

### Automated Monitoring

The `LiveMonitor` class provides:
- Trade tracking
- Performance metrics
- System health monitoring
- Automatic alerting
- Emergency stop triggers
- Daily reports

### Alert Configuration

Configure alerts in your config:

```yaml
monitoring:
  alerts:
    email:
      enabled: true
      address: your@email.com
    telegram:
      enabled: true
      bot_token: ${TELEGRAM_BOT_TOKEN}
      chat_id: ${TELEGRAM_CHAT_ID}
```

### Key Metrics to Watch

| Metric | Warning Level | Critical Level |
|--------|---------------|----------------|
| Daily Loss | 2% | 3% |
| Drawdown | 5% | 10% |
| Consecutive Losses | 5 | 8 |
| Win Rate | < 45% | < 40% |
| API Latency | > 500ms | > 1000ms |
| CPU Usage | > 80% | > 95% |

---

## Scaling Strategy

### When to Scale Up

Move to the next stage when:
1. ✅ Minimum trades completed for current stage
2. ✅ Win rate meets threshold
3. ✅ Max drawdown not exceeded
4. ✅ No critical errors
5. ✅ Consistent performance over time

### Scaling Timeline

| Stage | Minimum Duration | Minimum Trades |
|-------|------------------|----------------|
| 1 → 2 | 7 days | 20 trades |
| 2 → 3 | 14 days | 50 trades |
| 3 → 4 | 30 days | 100 trades |

### When to Scale Down

Scale down or pause if:
- ❌ Drawdown exceeds 10%
- ❌ Win rate drops below 40%
- ❌ 5+ consecutive losses
- ❌ Daily loss exceeds 3%
- ❌ System errors occur

---

## Emergency Procedures

### Kill Switch Triggers

The system automatically stops trading when:
- Daily loss exceeds limit
- Maximum drawdown exceeded
- Too many consecutive losses
- System health drops below threshold
- Connection failures

### Manual Emergency Stop

```bash
# Press Ctrl+C in the terminal
# Or use the kill switch:
python -c "from trading_bot.safety import EmergencyKillSwitch; EmergencyKillSwitch().trigger('manual')"
```

### Recovery Procedure

1. **Assess the situation**
   - Review logs in `logs/`
   - Check monitoring reports
   - Identify root cause

2. **Fix the issue**
   - Address any bugs
   - Adjust parameters if needed
   - Update risk limits

3. **Validate the fix**
   - Run paper trading again
   - Ensure issue is resolved

4. **Resume trading**
   - Start with Stage 1 again
   - Monitor closely for 24-48 hours

### Contact Information

Configure emergency contacts:
```yaml
emergency:
  contacts:
    - email: your@email.com
    - phone: +1234567890
```

---

## Quick Reference

### Commands

```bash
# Paper Trading
python run_paper_trading.py              # Start paper trading
python run_paper_trading.py --demo 50    # Run 50 demo trades
python run_paper_trading.py --report     # Generate report

# Live Trading
python run_live_trading.py --check-only  # Check readiness
python run_live_trading.py --dry-run     # Dry run
python run_live_trading.py --stage 1     # Start Stage 1

# Dashboard
python -c "from trading_bot.dashboard.realtime_dashboard import run_dashboard; run_dashboard()"
```

### Files

| File | Purpose |
|------|---------|
| `config/paper_trading_config.yaml` | Paper trading settings |
| `config/live_trading_config.yaml` | Live trading settings |
| `data/paper_trading/` | Paper trading data |
| `logs/monitoring_reports/` | Monitoring reports |
| `reports/` | Trading reports |

### Validation Checklist

Before going live:
- [ ] Paper trading validation passed
- [ ] Broker credentials configured
- [ ] Risk limits set appropriately
- [ ] Emergency contacts configured
- [ ] Backup systems tested
- [ ] Monitoring dashboard working
- [ ] Alert system tested
- [ ] Recovery procedure understood

---

## Support

For issues or questions:
1. Check the logs in `logs/`
2. Review the documentation in `docs/`
3. Run diagnostics: `python diagnostics/run_diagnostics.py`

---

*Last Updated: November 2024*
