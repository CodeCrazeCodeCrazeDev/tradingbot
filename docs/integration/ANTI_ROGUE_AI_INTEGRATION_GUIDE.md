# Anti-Rogue AI System - Integration Guide

## Quick Integration Steps

### Step 1: Import the System

```python
from trading_bot.anti_rogue_ai import quick_start, OversightLevel
```

### Step 2: Initialize in Your Main Trading Loop

```python
# In your main.py or trading engine initialization
from trading_bot.anti_rogue_ai import quick_start

class TradingEngine:
    def __init__(self, config):
        # ... existing initialization ...
        
        # Initialize anti-rogue AI system
        self.anti_rogue = quick_start({
            'oversight_level': 'moderate'  # or 'minimal', 'high', 'maximum'
        })
        
        logger.info("Anti-Rogue AI System initialized")
```

### Step 3: Wrap Your Trade Execution

```python
def execute_trade(self, signal):
    """Execute trade with anti-rogue validation."""
    
    # Prepare action details
    action = {
        'symbol': signal['symbol'],
        'direction': signal['direction'],
        'quantity': signal['quantity'],
        'risk_pct': signal.get('risk_pct', 1.0),
        'leverage': signal.get('leverage', 1.0),
        'position_size_pct': signal.get('position_size_pct', 5.0),
        'size_usd': signal.get('size_usd', 0)
    }
    
    # Get reasoning (AI must explain!)
    reasoning = signal.get('reasoning', '')
    if not reasoning:
        logger.error("No reasoning provided - AI must explain decisions!")
        return None
    
    # Get market data for understanding check
    market_data = self.get_market_data(signal['symbol'])
    
    # Get system metrics
    metrics = {
        'complexity_score': self.get_complexity_score(),
        'decision_depth': signal.get('decision_depth', 0),
        'state_variables': self.get_state_variable_count()
    }
    
    # VALIDATE WITH ANTI-ROGUE SYSTEM
    check = self.anti_rogue.validate_action(
        action_type='trade',
        action=action,
        reasoning=reasoning,
        market_data=market_data,
        metrics=metrics
    )
    
    # Check if safe to proceed
    if not check.can_proceed:
        logger.warning(
            "Trade BLOCKED by anti-rogue system: %s",
            ', '.join(check.issues)
        )
        return None
    
    # Log warnings if any
    if check.warnings:
        logger.info(
            "Trade approved with warnings: %s",
            ', '.join(check.warnings)
        )
    
    # Execute trade (original logic)
    logger.info("Trade APPROVED - Executing...")
    return self._execute_trade_internal(signal)
```

### Step 4: Provide Market Data Helper

```python
def get_market_data(self, symbol):
    """Get comprehensive market data for understanding check."""
    
    # Get OHLCV data
    df = self.data_provider.get_data(symbol, timeframe='1H', bars=100)
    
    # Get additional context
    sentiment = self.sentiment_analyzer.get_sentiment(symbol)
    order_flow = self.order_flow_analyzer.get_flow(symbol)
    
    return {
        'symbol': symbol,
        'prices': df['close'].tolist(),
        'volumes': df['volume'].tolist(),
        'retail_sentiment': sentiment.get('retail', 'neutral'),
        'institutional_sentiment': sentiment.get('institutional', 'neutral'),
        'fear_greed': sentiment.get('fear_greed_index', 50),
        'order_flow': order_flow.get('direction', 'balanced'),
        'liquidity': order_flow.get('liquidity', 'normal'),
        'spread': order_flow.get('spread', 'normal'),
        'volatility': df['atr'].iloc[-1] if 'atr' in df else None
    }
```

### Step 5: Handle Approval Requests

```python
def check_pending_approvals(self):
    """Check and handle pending approval requests."""
    
    pending = self.anti_rogue.get_pending_approvals()
    
    if pending:
        logger.info(f"Pending approvals: {len(pending)}")
        
        for request in pending:
            # Display to user/admin
            self.notify_approval_required(request)
            
            # In automated mode, you might auto-approve low-risk trades
            if request['risk_level'] == 'low':
                self.anti_rogue.approve_pending_request(
                    request_id=request['request_id'],
                    approver='AutoApproval',
                    notes='Low risk trade auto-approved'
                )
```

### Step 6: Monitor System Health

```python
def monitor_anti_rogue_system(self):
    """Monitor anti-rogue system health."""
    
    status = self.anti_rogue.get_comprehensive_status()
    
    # Check for kill switch
    if status['kill_switch_activated']:
        logger.critical("KILL SWITCH ACTIVATED - All trading stopped!")
        self.stop_all_trading()
        return
    
    # Check for constraint violations
    if status['constraints']['total_violations'] > 0:
        logger.error(
            "Constraint violations detected: %d",
            status['constraints']['total_violations']
        )
    
    # Check for rogue behavior
    if status['rogue_prevention']['critical_detections'] > 0:
        logger.critical(
            "Critical rogue behavior detected: %d",
            status['rogue_prevention']['critical_detections']
        )
        # Consider activating kill switch
        self.anti_rogue.activate_kill_switch(
            reason="Critical rogue behavior detected",
            activated_by="AutoMonitor"
        )
    
    # Log status
    logger.info(
        "Anti-Rogue Status: Checks=%d, Blocked=%d, Pending=%d",
        status['total_checks'],
        status['blocked_actions'],
        status['oversight']['pending_approvals']
    )
```

---

## Integration Patterns

### Pattern 1: Pre-Trade Validation

```python
# Check market understanding BEFORE generating signals
context = self.anti_rogue.understanding.analyze_market_context(
    symbol='EURUSD',
    market_data=market_data
)

# Only generate signals if we understand the market
can_trade, reason = self.anti_rogue.understanding.can_trade('EURUSD')

if can_trade:
    signal = self.strategy.generate_signal(context)
    # ... validate and execute
else:
    logger.info(f"Skipping {symbol}: {reason}")
```

### Pattern 2: Post-Signal Validation

```python
# Generate signal first
signal = self.strategy.generate_signal(market_data)

# Then validate with anti-rogue system
check = self.anti_rogue.validate_action(
    action_type='trade',
    action=signal,
    reasoning=signal['reasoning'],
    market_data=market_data,
    metrics=metrics
)

if check.can_proceed:
    self.execute_trade(signal)
```

### Pattern 3: Strategy Change Validation

```python
# Validate strategy changes
check = self.anti_rogue.validate_action(
    action_type='strategy_change',
    action={
        'old_strategy': 'trend_following',
        'new_strategy': 'mean_reversion',
        'reason': 'Market regime changed'
    },
    reasoning="Market shifted from trending to ranging",
    metrics=metrics
)

if check.can_proceed:
    self.switch_strategy('mean_reversion')
```

---

## Emergency Procedures Integration

### Kill Switch Integration

```python
# Add kill switch to your emergency handler
def emergency_shutdown(self, reason):
    """Emergency shutdown procedure."""
    
    # Activate anti-rogue kill switch
    self.anti_rogue.activate_kill_switch(
        reason=reason,
        activated_by="EmergencyHandler"
    )
    
    # Close all positions
    self.close_all_positions()
    
    # Stop trading engine
    self.stop_trading()
    
    # Send alerts
    self.send_alert(f"EMERGENCY SHUTDOWN: {reason}")
```

### Human Override Integration

```python
# Allow traders to override AI decisions
def override_ai_decision(self, decision_id, new_decision, trader_name, reason):
    """Allow human override of AI decision."""
    
    self.anti_rogue.override_decision(
        decision_id=decision_id,
        new_decision=new_decision,
        overridden_by=trader_name,
        reason=reason
    )
    
    # Execute new decision
    self.execute_decision(new_decision)
```

---

## Configuration Examples

### Conservative Configuration

```python
config = {
    'oversight_level': 'high',  # Approve all trades
    'trade_size_usd': 5000,     # Lower approval threshold
    'risk_per_trade_pct': 0.5,  # Stricter risk limits
    'min_understanding_level': 'excellent',  # Higher understanding required
    'max_complexity_increase_per_day': 0.02  # Slower evolution
}
```

### Moderate Configuration (Default)

```python
config = {
    'oversight_level': 'moderate',
    'trade_size_usd': 10000,
    'risk_per_trade_pct': 1.0,
    'min_understanding_level': 'good',
    'max_complexity_increase_per_day': 0.05
}
```

### Aggressive Configuration

```python
config = {
    'oversight_level': 'minimal',
    'trade_size_usd': 25000,
    'risk_per_trade_pct': 2.0,
    'min_understanding_level': 'partial',
    'max_complexity_increase_per_day': 0.10
}
```

---

## Testing Integration

### Unit Test Example

```python
import unittest
from trading_bot.anti_rogue_ai import quick_start

class TestAntiRogueIntegration(unittest.TestCase):
    
    def setUp(self):
        self.anti_rogue = quick_start()
    
    def test_safe_trade_approved(self):
        """Test that safe trades are approved."""
        
        check = self.anti_rogue.validate_action(
            action_type='trade',
            action={
                'symbol': 'EURUSD',
                'direction': 'buy',
                'risk_pct': 1.0
            },
            reasoning="Strong uptrend with good liquidity",
            market_data={
                'prices': [1.1000] * 20,
                'volumes': [1000] * 20,
                'order_flow': 'buying'
            },
            metrics={'complexity_score': 40}
        )
        
        self.assertTrue(check.can_proceed)
        self.assertTrue(check.constraints_ok)
    
    def test_excessive_risk_blocked(self):
        """Test that excessive risk is blocked."""
        
        check = self.anti_rogue.validate_action(
            action_type='trade',
            action={
                'symbol': 'EURUSD',
                'risk_pct': 10.0  # Exceeds limit
            },
            reasoning="High conviction"
        )
        
        self.assertFalse(check.can_proceed)
        self.assertFalse(check.constraints_ok)
```

---

## Monitoring Dashboard Integration

```python
def get_anti_rogue_metrics(self):
    """Get metrics for monitoring dashboard."""
    
    status = self.anti_rogue.get_comprehensive_status()
    
    return {
        'kill_switch_active': status['kill_switch_activated'],
        'total_validations': status['total_checks'],
        'blocked_actions': status['blocked_actions'],
        'block_rate': status['blocked_actions'] / max(status['total_checks'], 1),
        'constraint_violations': status['constraints']['total_violations'],
        'rogue_detections': status['rogue_prevention']['total_detections'],
        'pending_approvals': status['oversight']['pending_approvals'],
        'tracked_symbols': len(status['understanding']['tracked_symbols'])
    }
```

---

## Complete Integration Example

```python
# main.py
from trading_bot.anti_rogue_ai import quick_start
import logging

logger = logging.getLogger(__name__)

class SafeTradingEngine:
    """Trading engine with anti-rogue AI integration."""
    
    def __init__(self, config):
        self.config = config
        
        # Initialize anti-rogue system
        self.anti_rogue = quick_start({
            'oversight_level': config.get('oversight_level', 'moderate')
        })
        
        logger.info("Safe Trading Engine initialized")
    
    async def run(self):
        """Main trading loop with safety checks."""
        
        while True:
            # Check kill switch
            if self.anti_rogue.oversight.is_kill_switch_activated():
                logger.critical("Kill switch activated - stopping")
                break
            
            # Get market data
            for symbol in self.symbols:
                market_data = self.get_market_data(symbol)
                
                # Check if we understand the market
                can_trade, reason = self.anti_rogue.understanding.can_trade(symbol)
                
                if not can_trade:
                    logger.info(f"Skipping {symbol}: {reason}")
                    continue
                
                # Generate signal
                signal = self.strategy.generate_signal(symbol, market_data)
                
                if signal:
                    # Validate with anti-rogue system
                    check = self.anti_rogue.validate_action(
                        action_type='trade',
                        action=signal,
                        reasoning=signal['reasoning'],
                        market_data=market_data,
                        metrics=self.get_metrics()
                    )
                    
                    if check.can_proceed:
                        # Execute trade
                        self.execute_trade(signal)
                    else:
                        logger.warning(f"Trade blocked: {check.issues}")
            
            # Check pending approvals
            self.check_pending_approvals()
            
            # Monitor system health
            self.monitor_health()
            
            await asyncio.sleep(60)  # 1 minute interval
    
    def get_market_data(self, symbol):
        """Get comprehensive market data."""
        # Implementation from Step 4
        pass
    
    def get_metrics(self):
        """Get system metrics."""
        return {
            'complexity_score': 45,
            'decision_depth': 3,
            'state_variables': 20
        }
    
    def check_pending_approvals(self):
        """Check pending approvals."""
        # Implementation from Step 5
        pass
    
    def monitor_health(self):
        """Monitor system health."""
        # Implementation from Step 6
        pass

# Run
if __name__ == "__main__":
    config = {'oversight_level': 'moderate'}
    engine = SafeTradingEngine(config)
    asyncio.run(engine.run())
```

---

## Summary

✅ **Integration is simple:**
1. Import `quick_start`
2. Initialize in your trading engine
3. Validate actions before execution
4. Provide market data for understanding
5. Handle approvals and monitor health

✅ **Benefits:**
- AI cannot go rogue
- AI must understand markets
- Humans remain in control
- All actions are transparent
- Emergency kill switch available

✅ **Zero disruption:**
- Wraps existing code
- No major refactoring needed
- Can be enabled/disabled
- Configurable strictness levels

**Your trading AI is now safe and controllable!** 🎉
