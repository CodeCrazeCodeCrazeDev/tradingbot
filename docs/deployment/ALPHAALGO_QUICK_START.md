# ⚡ AlphaAlgo Quick Start Guide

## 🎯 Get Started in 5 Minutes

### Step 1: Run the Test Suite (2 minutes)

```bash
cd "c:\Users\peterson\trading bot"
python test_complete_system.py
```

**Expected Output:**
```
🎉 ALL TESTS PASSED - SYSTEM READY FOR PRODUCTION
```

### Step 2: Run System Validation Demo (3 minutes)

```bash
python examples/alphaalgo_system_validation.py
```

**What it does:**
- ✅ Runs 5-phase validation
- ✅ Tests all components
- ✅ Shows system health
- ✅ Demonstrates learning

### Step 3: Run Autonomous Trading Demo (5 minutes)

```bash
python examples/autonomous_trading_demo.py
```

**What it does:**
- ✅ Pre-trading safety checks
- ✅ Auto-fix demonstrations
- ✅ Internet learning simulation
- ✅ Mirror testing overview

## 🚀 Launch AlphaAlgo

### Option 1: Use the Launcher (Recommended)

```bash
python run_alphaalgo.py
```

This runs the complete system with:
- 5-phase validation
- Continuous monitoring
- Autonomous trading
- Self-improvement

### Option 2: Integrate with Your Bot

See `INTEGRATION_GUIDE.md` for detailed integration steps.

## 📋 Quick Configuration

Edit `config/alphaalgo_config.yaml`:

```yaml
# Minimum settings
system_health:
  min_health_for_live: 95.0

autonomous:
  autonomous_fixer:
    auto_fix_enabled: true
  
  internet_improver:
    internet_learning_enabled: true

trading:
  risk:
    max_risk_per_trade: 0.01
```

## 🔍 Check System Status

### View Logs

```bash
# Latest validation
cat diagnostics/system_health/validation_*.json | tail -1

# Auto-fixes applied
cat diagnostics/system_health/auto_fixes.log

# Performance tracker
cat diagnostics/system_health/performance_tracker.json

# Learning history
cat diagnostics/system_health/learning_history.json
```

### Monitor Health

```python
from trading_bot.system_health import AlphaAlgoMaster

master = AlphaAlgoMaster(config)
status = master.get_status()

print(f"Mode: {status['current_mode']}")
print(f"Health: {status['system_health']:.1f}%")
print(f"Can Trade: {master.can_trade_live()}")
```

## 📚 Next Steps

1. **Read Documentation**
   - `README_ALPHAALGO.md` - Complete guide
   - `INTEGRATION_GUIDE.md` - Integration steps
   - `COMPLETE_SYSTEM_SUMMARY.md` - Full summary

2. **Configure for Your Environment**
   - Edit `config/alphaalgo_config.yaml`
   - Add API keys (optional)
   - Set risk parameters

3. **Test in Paper Mode**
   - Run with `AUTO_PROMOTE: false`
   - Monitor for 1 week
   - Review all improvements manually

4. **Deploy to Live**
   - Ensure health ≥ 95%
   - Enable continuous monitoring
   - Start with small positions

## 🆘 Troubleshooting

### Tests Fail

```bash
# Check Python version (3.8+)
python --version

# Install dependencies
pip install -r requirements.txt

# Check logs
cat diagnostics/system_health/*.json
```

### Import Errors

```python
# Add to your script
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
```

### Config Not Found

```bash
# Check file exists
ls config/alphaalgo_config.yaml

# Use absolute path
config_path = Path(__file__).parent / 'config' / 'alphaalgo_config.yaml'
```

## ✅ Verification Checklist

Before going live:

- [ ] All tests pass (`test_complete_system.py`)
- [ ] System health ≥ 95%
- [ ] All demos run successfully
- [ ] Configuration customized
- [ ] Logs being written
- [ ] Monitoring active
- [ ] Alerts configured
- [ ] Team trained

## 📞 Support

- **Documentation**: See `docs/` folder
- **Examples**: See `examples/` folder
- **Email**: peterkiragu68@outlook.com

## 🎉 You're Ready!

Your AlphaAlgo system is now:

✅ **Validated** - 5-phase system check
✅ **Self-Healing** - Auto-fix issues
✅ **Learning** - Improves from losses
✅ **Safe** - Never trades if unhealthy
✅ **Autonomous** - Self-managing 24/7

**Start trading with confidence!**
