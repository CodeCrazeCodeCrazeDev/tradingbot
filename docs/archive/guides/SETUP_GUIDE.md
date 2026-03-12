# 🚀 AlphaAlgo Trading Bot - Complete Setup Guide

**Last Updated**: October 20, 2025

---

## 📋 Prerequisites

### Required Software
- Python 3.9+ (3.11 recommended)
- Git
- pip (Python package manager)

### Optional Software
- MetaTrader 5 (for live trading)
- Redis (for caching)
- PostgreSQL (for production database)

---

## 🔧 Installation

### 1. Clone Repository
```bash
git clone <repository-url>
cd trading-bot
```

### 2. Create Virtual Environment
```bash
# Windows
py -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
# Core dependencies
pip install -r requirements.txt

# Development dependencies
pip install -r requirements-dev.txt

# Or install all at once
pip install -r requirements.txt pytest pytest-asyncio pytest-cov black isort flake8 mypy bandit pre-commit
```

### 4. Install Pre-commit Hooks
```bash
pre-commit install
```

---

## ⚙️ Configuration

### 1. Create Configuration File
```bash
# Copy template
copy config\alphaalgo_config.yaml.example config\alphaalgo_config.yaml

# Or create new
notepad config\alphaalgo_config.yaml
```

### 2. Configure Broker
```yaml
broker:
  type: mock  # or 'mt5' for live trading
  initial_balance: 10000.0
  leverage: 100
  commission: 0.0001
```

### 3. Configure Risk Management
```yaml
risk:
  default_risk_pct: 0.02  # 2% per trade
  max_position_size: 1000000
  min_position_size: 1000
  max_leverage: 100
```

### 4. Configure Database
```yaml
database:
  type: timeseries  # or 'memory' for testing
  persistence_dir: ./data
  max_history_length: 1000
```

---

## 🧪 Testing

### Run All Tests
```bash
# Quick test (new components only)
RUN_QUICK_TESTS.bat

# Full test suite
RUN_ALL_TESTS.bat

# Or manually
py -m pytest tests/ -v
```

### Run with Coverage
```bash
py -m pytest tests/ --cov=trading_bot --cov-report=html
# Open htmlcov/index.html to view coverage report
```

### Run Specific Tests
```bash
# Broker tests only
py -m pytest tests/test_broker_adapter.py -v

# Position sizer tests only
py -m pytest tests/test_position_sizer.py -v

# Integration tests only
py -m pytest tests/ -m integration
```

---

## ✅ Validation

### Run Complete Validation
```bash
RUN_CRITICAL_VALIDATION.bat

# Or manually
py validate_critical_fixes.py
```

### Expected Output
```
============================================
  Critical Fixes Validation
============================================

1. Import Validation
✅ PASS - Broker Adapters
✅ PASS - Position Sizer
✅ PASS - Fill Tracker
✅ PASS - Correlation Persistence
✅ PASS - Health Endpoints
✅ PASS - Database Initializer
✅ PASS - Survival Core

2. Component Initialization
✅ PASS - Mock Broker Adapter
✅ PASS - Position Sizer
✅ PASS - Fill Tracker
✅ PASS - Correlation Manager
✅ PASS - Health Check Manager
✅ PASS - Database Initializer

VALIDATION SUMMARY
Total Tests:  25
Passed:       25
Failed:       0
Pass Rate:    100.0%

🎉 ALL TESTS PASSED! System is ready for testing.
```

---

## 🎯 Usage Examples

### 1. Paper Trading with Mock Broker
```python
from trading_bot.core.survival_core import SurvivalCore

# Configure for paper trading
config = {
    'broker': {
        'type': 'mock',
        'initial_balance': 10000.0
    },
    'risk': {
        'default_risk_pct': 0.02
    }
}

# Initialize
core = SurvivalCore(config)

# Start trading
import asyncio
asyncio.run(core.start())
```

### 2. Calculate Position Size
```python
from trading_bot.risk.position_sizer import PositionSizer, SizingMethod

sizer = PositionSizer()

# Fixed risk sizing
size = sizer.calculate_position_size(
    symbol='EURUSD',
    account_equity=10000,
    risk_pct=0.02,
    stop_loss_pips=50,
    entry_price=1.1000,
    method=SizingMethod.FIXED_RISK
)

print(f"Position size: {size:,.0f} units")
# Output: Position size: 40,000 units
```

### 3. Track Order Fills
```python
from trading_bot.execution.fill_tracker import FillTracker
from trading_bot.brokers import MockBrokerAdapter

# Initialize
broker = MockBrokerAdapter({'initial_balance': 10000})
await broker.connect()

tracker = FillTracker(broker)

# Place and track order
response = await broker.place_order(
    symbol='EURUSD',
    side='buy',
    order_type='market',
    quantity=100000,
    price=1.1000
)

# Track fill
record = await tracker.track_order(
    order_id=response.order_id,
    symbol='EURUSD',
    side='buy',
    quantity=100000,
    expected_price=1.1000
)

# Wait for confirmation
confirmed = await tracker.wait_for_confirmation(response.order_id, timeout=30)

# Get slippage stats
stats = tracker.get_slippage_stats('EURUSD')
print(f"Average slippage: {stats['avg_slippage_bps']:.2f} bps")
```

### 4. Health Monitoring
```python
from fastapi import FastAPI
from trading_bot.infrastructure.health_endpoints import (
    HealthCheckManager,
    setup_health_endpoints
)

app = FastAPI()
health_manager = HealthCheckManager()

# Register components
health_manager.register_component(
    'database',
    check_func=lambda: db.is_connected(),
    metadata={'critical': True}
)

health_manager.register_component(
    'broker',
    check_func=lambda: broker.connected,
    metadata={'critical': True}
)

# Setup endpoints
setup_health_endpoints(app, health_manager)

# Start server
# uvicorn main:app --host 0.0.0.0 --port 8000

# Access endpoints:
# http://localhost:8000/health/live
# http://localhost:8000/health/ready
# http://localhost:8000/health/status
```

---

## 🔍 Troubleshooting

### Issue: Python command not recognized
**Solution**: Use `py` instead of `python` on Windows
```bash
py -m pip install -r requirements.txt
py -m pytest tests/
```

### Issue: Import errors
**Solution**: Ensure virtual environment is activated
```bash
# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### Issue: Tests failing
**Solution**: Install test dependencies
```bash
pip install pytest pytest-asyncio pytest-cov
```

### Issue: Pre-commit hooks failing
**Solution**: Run hooks manually to see errors
```bash
pre-commit run --all-files
```

### Issue: MT5 connection failed
**Solution**: 
1. Ensure MT5 is installed
2. Check credentials in config
3. Use mock broker for testing:
```yaml
broker:
  type: mock
```

---

## 📊 Monitoring

### View Test Coverage
```bash
py -m pytest tests/ --cov=trading_bot --cov-report=html
start htmlcov\index.html
```

### View Health Status
```bash
# Start health server
py -m uvicorn main:app --host 0.0.0.0 --port 8000

# Check health
curl http://localhost:8000/health/status
```

### View Logs
```bash
# Trading logs
type logs\trading.log

# Error logs
type logs\error.log

# System logs
type logs\system.log
```

---

## 🚀 Deployment

### 1. Staging Environment
```bash
# Set environment
set ENVIRONMENT=staging

# Run with staging config
py main.py --config config/staging_config.yaml
```

### 2. Production Environment
```bash
# Set environment
set ENVIRONMENT=production

# Run with production config
py main.py --config config/production_config.yaml --live
```

### 3. Docker Deployment
```bash
# Build image
docker build -t alphaalgo-bot .

# Run container
docker run -d \
  --name alphaalgo \
  -v $(pwd)/config:/app/config \
  -v $(pwd)/logs:/app/logs \
  -p 8000:8000 \
  alphaalgo-bot
```

---

## 📚 Additional Resources

### Documentation
- [Complete Fix Report](ALL_ISSUES_FIXED_COMPLETE.md)
- [Usage Guide](CRITICAL_FIXES_USAGE_GUIDE.md)
- [Issue Scan](COMPREHENSIVE_ISSUE_SCAN_2025.md)
- [Quick Reference](QUICK_ISSUE_SUMMARY.md)

### Scripts
- `RUN_ALL_TESTS.bat` - Run full test suite
- `RUN_QUICK_TESTS.bat` - Run quick tests
- `RUN_CRITICAL_VALIDATION.bat` - Validate all fixes
- `validate_critical_fixes.py` - Validation script

### Configuration Files
- `pytest.ini` - Test configuration
- `.pre-commit-config.yaml` - Pre-commit hooks
- `.github/workflows/ci.yml` - CI/CD pipeline
- `trading_bot/constants.py` - System constants

---

## 🎯 Quick Start Checklist

- [ ] Python 3.9+ installed
- [ ] Virtual environment created and activated
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] Pre-commit hooks installed (`pre-commit install`)
- [ ] Configuration file created (`config/alphaalgo_config.yaml`)
- [ ] Tests passing (`RUN_ALL_TESTS.bat`)
- [ ] Validation passing (`RUN_CRITICAL_VALIDATION.bat`)
- [ ] Health checks working (if using FastAPI)
- [ ] Logs directory created
- [ ] Ready to trade! 🚀

---

## 💡 Tips

1. **Always test in paper trading first**
   ```yaml
   broker:
     type: mock
   ```

2. **Monitor health endpoints regularly**
   ```bash
   curl http://localhost:8000/health/status
   ```

3. **Check logs frequently**
   ```bash
   tail -f logs/trading.log
   ```

4. **Run tests before deploying**
   ```bash
   RUN_ALL_TESTS.bat
   ```

5. **Use constants instead of magic numbers**
   ```python
   from trading_bot.constants import DEFAULT_RISK_PERCENTAGE
   ```

---

## 🆘 Support

### Common Commands
```bash
# Install dependencies
pip install -r requirements.txt

# Run tests
py -m pytest tests/ -v

# Run validation
py validate_critical_fixes.py

# Setup pre-commit
pre-commit install

# Run pre-commit
pre-commit run --all-files

# Start trading
py main.py --config config/alphaalgo_config.yaml
```

### Getting Help
1. Check documentation in `docs/` folder
2. Review error logs in `logs/` folder
3. Run validation script to identify issues
4. Check test results for failures

---

**Your AlphaAlgo trading bot is ready!** 🎉

Start with paper trading, monitor performance, and gradually transition to live trading after 1-2 weeks of successful paper trading.

Good luck! 📈
