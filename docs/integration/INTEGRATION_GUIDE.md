# 🔧 AlphaAlgo Integration Guide

## Step-by-Step Integration with Your Trading Bot

This guide shows how to integrate AlphaAlgo's autonomous systems into your existing trading bot.

## 🎯 Integration Overview

```
Your Trading Bot
        │
        ├─→ AlphaAlgo System Validation (Pre-launch)
        ├─→ Autonomous Trading (Runtime)
        └─→ Self-Improvement Engine (Post-trade)
```

## 📋 Step 1: Add to Your Main Trading Bot

### Option A: Integrate with Existing `main.py`

```python
# main.py
import asyncio
from trading_bot.system_health import AlphaAlgoMaster
from trading_bot.self_improvement import AutonomousOrchestrator

class YourTradingBot:
    def __init__(self, config):
        self.config = config
        
        # Initialize AlphaAlgo systems
        self.validator = AlphaAlgoMaster(config.get('system_health', {}))
        self.autonomous = AutonomousOrchestrator(config.get('autonomous', {}))
        
        # Your existing components
        self.brain = EliteBrain(config)
        self.risk_manager = RiskManager(config)
        # ... other components
    
    async def start(self):
        """Start trading bot with full validation."""
        print("=" * 80)
        print("STARTING TRADING BOT WITH ALPHAALGO VALIDATION")
        print("=" * 80)
        
        # STEP 1: Run 5-phase validation
        print("\n🔍 Running system validation...")
        validation = await self.validator.run_full_validation()
        
        if not self.validator.can_trade_live():
            print(f"❌ Validation failed: {validation['recommended_mode'].value}")
            print("Cannot start trading - fix issues first")
            return
        
        print("✅ Validation passed - starting trading")
        
        # STEP 2: Start continuous monitoring
        print("\n📊 Starting continuous monitoring...")
        asyncio.create_task(self.validator.continuous_monitoring())
        
        # STEP 3: Start your trading loop
        print("\n💹 Starting trading loop...")
        await self.trading_loop()
    
    async def trading_loop(self):
        """Main trading loop with autonomous features."""
        while True:
            try:
                # Pre-trading safety check
                safety = await self.autonomous.pre_trading_check()
                
                if not safety['safe_to_trade']:
                    print("⚠️ Pre-trading check failed - pausing")
                    await asyncio.sleep(300)
                    continue
                
                # Your existing trading logic
                signals = await self.brain.generate_signals()
                
                for signal in signals:
                    # Execute trade
                    trade = await self.execute_trade(signal)
                    
                    # If trade closed with loss
                    if trade and trade['pnl'] < 0:
                        # Trigger autonomous improvement
                        await self.handle_loss(trade)
                
                await asyncio.sleep(60)
            
            except Exception as e:
                print(f"Error in trading loop: {e}")
                await asyncio.sleep(60)
    
    async def handle_loss(self, trade):
        """Handle losing trade with autonomous improvement."""
        # Collect context
        signal_data = self._get_signal_context(trade)
        market_data = self._get_market_snapshot(trade)
        system_data = self._get_system_metrics()
        equity = self.get_account_equity()
        
        # Process through autonomous system
        result = await self.autonomous.on_trade_loss(
            trade, signal_data, market_data, system_data, equity
        )
        
        # Also record in validator for learning
        await self.validator.record_trade_loss(trade)
        
        print(f"Autonomous improvement: {result['status']}")
        
        if result['status'] == 'deployed':
            print(f"✓ Strategy improved by {result['best_improvement']:.1%}")

# Run it
if __name__ == "__main__":
    bot = YourTradingBot(config)
    asyncio.run(bot.start())
```

### Option B: Use the Launcher

```python
# Simply use run_alphaalgo.py
python run_alphaalgo.py
```

## 📋 Step 2: Update Configuration

### Merge with Existing Config

```yaml
# config/config.yaml

# Your existing config
trading:
  symbols: [EURUSD, GBPUSD]
  risk_per_trade: 0.01
  # ... your settings

# Add AlphaAlgo config
system_health:
  min_health_for_live: 95.0
  revalidation_interval_hours: 1
  health_monitor:
    max_latency_ms: 100
    max_cpu_percent: 90
    min_memory_mb: 500

autonomous:
  autonomous_fixer:
    auto_fix_enabled: true
  internet_improver:
    internet_learning_enabled: true
  mirror_tester:
    mirror_test_duration_hours: 24
  self_improvement:
    AUTO_LEARN: true
    CONF_THRESHOLD: 0.6
    AUTO_PROMOTE: false
```

## 📋 Step 3: Add Pre-Trading Validation

### Before Each Trading Session

```python
async def before_trading_session(self):
    """Run before starting daily trading."""
    # Quick health check
    safety = await self.autonomous.pre_trading_check()
    
    if not safety['safe_to_trade']:
        # Issues detected
        print("Issues found:")
        for issue in safety['issues']:
            print(f"  - {issue}")
        
        print("\nFixes applied:")
        for fix in safety['fixes_applied']:
            print(f"  - {fix}")
        
        # Re-check after fixes
        safety = await self.autonomous.pre_trading_check()
    
    return safety['safe_to_trade']
```

## 📋 Step 4: Integrate Loss Learning

### After Each Trade Closes

```python
async def on_trade_closed(self, trade):
    """Called when a trade closes."""
    # Your existing logic
    self.update_statistics(trade)
    self.log_trade(trade)
    
    # Add autonomous learning
    if trade['pnl'] < 0:  # Losing trade
        # Collect full context
        context = {
            'signal_data': {
                'indicators_used': trade.get('indicators', []),
                'model_confidence': trade.get('confidence', 0),
                'timeframe': trade.get('timeframe', 'H1'),
                'market_regime': self.brain.get_market_regime()
            },
            'market_data': {
                'candles_before': self.get_recent_candles(200),
                'atr': self.get_atr(),
                'spread': self.get_current_spread(),
                'volatility_spike': self.detect_volatility_spike()
            },
            'system_data': {
                'cpu_usage': psutil.cpu_percent(),
                'memory_usage': psutil.virtual_memory().percent,
                'latency_ms': self.get_avg_latency(),
                'errors_in_logs': self.get_recent_errors()
            }
        }
        
        # Process through autonomous system
        result = await self.autonomous.on_trade_loss(
            trade,
            context['signal_data'],
            context['market_data'],
            context['system_data'],
            self.get_account_equity()
        )
        
        # Log result
        if result['status'] == 'deployed':
            self.log_improvement(result)
```

## 📋 Step 5: Add Continuous Monitoring

### Background Task

```python
async def start_monitoring(self):
    """Start continuous monitoring in background."""
    # Start validator monitoring (re-validates every hour)
    monitor_task = asyncio.create_task(
        self.validator.continuous_monitoring()
    )
    
    # Your existing monitoring
    # ...
    
    return monitor_task
```

## 📋 Step 6: Handle Mode Changes

### React to System Health Changes

```python
async def on_mode_change(self, old_mode, new_mode):
    """Handle trading mode changes."""
    if new_mode == TradingMode.SAFE_MODE:
        # System health degraded
        print("⚠️ Entering SAFE MODE")
        
        # Close all positions
        await self.close_all_positions()
        
        # Switch to conservative strategies
        self.brain.set_conservative_mode()
        
        # Alert admin
        self.send_alert("System entered SAFE MODE")
    
    elif new_mode == TradingMode.PAPER_TRADING:
        # Degraded but not critical
        print("⚠️ Switching to PAPER TRADING")
        
        # Reduce position sizes
        self.risk_manager.reduce_risk(0.5)
        
    elif new_mode == TradingMode.LIVE_TRADING:
        # All systems healthy
        print("✅ LIVE TRADING authorized")
        
        # Resume normal operations
        self.risk_manager.restore_normal_risk()
```

## 📋 Step 7: Implement Helper Methods

### Data Collection Methods

```python
def _get_signal_context(self, trade):
    """Get signal context for a trade."""
    return {
        'indicators_used': trade.get('indicators', []),
        'indicator_values': trade.get('indicator_values', {}),
        'model_confidence': trade.get('confidence', 0),
        'timeframe': trade.get('timeframe', 'H1'),
        'market_regime': self.brain.get_market_regime(),
        'multi_tf_agreement': trade.get('mtf_agreement', False),
        'signal_drift': 0.0  # Calculate if available
    }

def _get_market_snapshot(self, trade):
    """Get market snapshot for a trade."""
    return {
        'candles_before': self.get_candles_before(trade, 200),
        'candles_after': self.get_candles_after(trade, 50),
        'atr': self.calculate_atr(trade['symbol']),
        'spread': self.get_spread(trade['symbol']),
        'volume_avg': self.get_avg_volume(trade['symbol']),
        'volatility_spike': self.detect_volatility_spike(trade['symbol']),
        'news_events': self.get_news_events(trade['entry_time'])
    }

def _get_system_metrics(self):
    """Get system metrics."""
    import psutil
    return {
        'cpu_usage': psutil.cpu_percent(),
        'memory_usage': psutil.virtual_memory().percent,
        'latency_ms': self.get_avg_latency(),
        'order_fill_type': 'full',  # or 'partial'
        'errors_in_logs': self.get_recent_errors()
    }
```

## 📋 Step 8: Testing Integration

### Test Script

```python
# test_integration.py
import asyncio
from your_trading_bot import YourTradingBot

async def test_integration():
    """Test AlphaAlgo integration."""
    print("Testing AlphaAlgo integration...")
    
    # Initialize bot
    bot = YourTradingBot(config)
    
    # Test 1: Validation
    print("\n1. Testing system validation...")
    validation = await bot.validator.run_full_validation()
    assert validation['system_health'] > 0
    print(f"   ✓ System health: {validation['system_health']:.1f}%")
    
    # Test 2: Safety check
    print("\n2. Testing pre-trading safety check...")
    safety = await bot.autonomous.pre_trading_check()
    print(f"   ✓ Safe to trade: {safety['safe_to_trade']}")
    
    # Test 3: Loss handling
    print("\n3. Testing loss handling...")
    test_trade = {
        'ticket_id': 'TEST_001',
        'symbol': 'EURUSD',
        'pnl': -50.0,
        'entry_price': 1.1000,
        'exit_price': 1.0950,
        'confidence': 0.55
    }
    
    await bot.handle_loss(test_trade)
    print("   ✓ Loss handling works")
    
    print("\n✅ All integration tests passed!")

if __name__ == "__main__":
    asyncio.run(test_integration())
```

## 📋 Step 9: Deployment Checklist

Before deploying to production:

- [ ] All integration tests pass
- [ ] System validation runs successfully
- [ ] Pre-trading checks work
- [ ] Loss learning triggers correctly
- [ ] Continuous monitoring active
- [ ] Mode changes handled properly
- [ ] Logs being written correctly
- [ ] Alerts configured
- [ ] Backup/rollback tested
- [ ] Team trained on system

## 📋 Step 10: Monitoring in Production

### Daily Checks

```bash
# Check system health
cat diagnostics/system_health/validation_*.json | tail -1

# Check auto-fixes
cat diagnostics/system_health/auto_fixes.log | tail -20

# Check performance
cat diagnostics/system_health/performance_tracker.json

# Check learning
cat diagnostics/system_health/learning_history.json | tail -10
```

### Weekly Review

1. Review all validation results
2. Analyze auto-fix patterns
3. Check strategy weight evolution
4. Validate improvement effectiveness
5. Adjust thresholds if needed

## 🎯 Common Integration Patterns

### Pattern 1: Minimal Integration

```python
# Just add validation before trading
async def start(self):
    validation = await self.validator.run_full_validation()
    if self.validator.can_trade_live():
        await self.trade()
```

### Pattern 2: Full Integration

```python
# Complete autonomous system
async def start(self):
    # Validate
    await self.validator.run_full_validation()
    
    # Monitor
    asyncio.create_task(self.validator.continuous_monitoring())
    
    # Trade with safety checks
    while True:
        if await self.autonomous.pre_trading_check():
            await self.trade()
        
        # Learn from losses
        for trade in self.closed_trades:
            if trade['pnl'] < 0:
                await self.autonomous.on_trade_loss(trade, ...)
```

### Pattern 3: Gradual Integration

```python
# Week 1: Just validation
await self.validator.run_full_validation()

# Week 2: Add monitoring
asyncio.create_task(self.validator.continuous_monitoring())

# Week 3: Add safety checks
await self.autonomous.pre_trading_check()

# Week 4: Add loss learning
await self.autonomous.on_trade_loss(...)
```

## 🆘 Troubleshooting Integration

### Issue: Import Errors

```python
# Make sure paths are correct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from trading_bot.system_health import AlphaAlgoMaster
from trading_bot.self_improvement import AutonomousOrchestrator
```

### Issue: Config Not Found

```python
# Use absolute paths
config_path = Path(__file__).parent / 'config' / 'alphaalgo_config.yaml'
with open(config_path) as f:
    config = yaml.safe_load(f)
```

### Issue: Async Issues

```python
# Make sure everything is async
async def your_method(self):
    result = await self.validator.run_full_validation()
    # Not: result = self.validator.run_full_validation()
```

## 📞 Support

If you encounter issues during integration:

1. Check the logs in `diagnostics/`
2. Review `COMPLETE_SYSTEM_SUMMARY.md`
3. Run the test demos
4. Email: peterkiragu68@outlook.com

## ✅ Integration Complete

Once integrated, your trading bot will have:

- ✅ 5-phase pre-launch validation
- ✅ Continuous health monitoring
- ✅ Automatic issue fixing
- ✅ Internet-based learning
- ✅ Mirror market testing
- ✅ Loss-based improvement
- ✅ Complete safety protocols

**Your bot is now fully autonomous and self-improving!**
