# Production Deployment Checklist

## Pre-Deployment Verification

### 1. Environment Setup
- [ ] Python 3.10+ installed
- [ ] All dependencies installed: `pip install -r requirements.txt`
- [ ] MT5 terminal installed and configured
- [ ] `.env` file configured with credentials

### 2. Configuration Review
- [ ] `config/alphaalgo_config.yaml` reviewed
- [ ] Risk parameters set appropriately
- [ ] Trading symbols configured
- [ ] Timeframes selected

### 3. System Validation
```bash
# Run validation
python -c "from trading_bot import *; print('All imports OK')"

# Run tests
pytest tests/ -v --tb=short

# Check system status
python CHECK_STATUS.py
```

### 4. Paper Trading Test
- [ ] Run in paper mode for at least 24 hours
- [ ] Verify signal generation
- [ ] Verify risk calculations
- [ ] Verify order simulation
- [ ] Check logs for errors

## Deployment Steps

### Step 1: Final Configuration
```bash
# Copy production config
cp config/alphaalgo_config.yaml config/production_config.yaml

# Edit production settings
# - Set mode: live
# - Verify risk limits
# - Set notification channels
```

### Step 2: Start Bot
```bash
# Using launcher
run.bat live

# Or directly
python main.py --mode live --symbol EURUSD
```

### Step 3: Monitor
- [ ] Check dashboard: `python run_dashboard.py`
- [ ] Monitor logs: `tail -f logs/trading.log`
- [ ] Set up alerts (Telegram/Email)

## Safety Checks

### Risk Limits
| Parameter | Recommended | Your Setting |
|-----------|-------------|--------------|
| Max Drawdown | 20% | ___% |
| Daily Loss Limit | 5% | ___% |
| Risk Per Trade | 1-2% | ___% |
| Max Positions | 3-5 | ___ |
| Max Lot Size | 0.1-1.0 | ___ |

### Emergency Procedures
1. **Kill Switch**: Press Ctrl+C or run `STOP_LOOP.bat`
2. **Close All Positions**: In MT5 terminal
3. **Disable Auto-Trading**: MT5 → Tools → Options → Expert Advisors

## Post-Deployment Monitoring

### Daily Checks
- [ ] Review overnight trades
- [ ] Check P&L
- [ ] Verify no errors in logs
- [ ] Check system resources

### Weekly Checks
- [ ] Review performance metrics
- [ ] Analyze losing trades
- [ ] Update strategy parameters if needed
- [ ] Backup configuration

## Rollback Procedure

If issues occur:
1. Stop the bot: `STOP_LOOP.bat`
2. Close all positions in MT5
3. Review logs for errors
4. Fix issues
5. Test in paper mode
6. Resume live trading

## Contact & Support

- Documentation: `docs/` folder
- Logs: `logs/` folder
- Configuration: `config/` folder

---

**Checklist completed by:** ________________  
**Date:** ________________  
**Approved by:** ________________
