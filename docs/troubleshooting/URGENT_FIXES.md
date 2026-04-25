# Urgent Fixes - TP/SL and Position Management

**Date:** 2025-10-09  
**Priority:** CRITICAL  
**Status:** Fixes Ready

---

## 🚨 Issues Identified

### 1. **No TP/SL Being Placed on Trades**
**Problem:** Trades are being opened without Take Profit or Stop Loss levels  
**Risk:** CRITICAL - Unlimited loss exposure

### 2. **Position Count Check Incorrect**
**Problem:** Checking `max_positions_per_symbol` instead of total `max_positions`  
**Current:** Allows 1 position per symbol (could be 100+ total positions!)  
**Expected:** Max 5 total positions across all symbols

### 3. **No Integration with Position Manager**
**Problem:** Pre-trade checks don't use the new PositionManager  
**Impact:** Position limits not enforced correctly

---

## 🔧 Fix 1: Add TP/SL to All Trades

### Update Order Execution

The issue is likely in your order execution. Here's how to fix it:

```python
# In your order execution code (likely in main.py or a strategy file)

def execute_trade(signal):
    """Execute trade with TP and SL"""
    
    # Calculate TP and SL levels
    entry_price = signal['price']
    side = signal['side']  # 'buy' or 'sell'
    
    # Get ATR for dynamic TP/SL
    atr = calculate_atr(signal['symbol'])  # You need to implement this
    
    if side == 'buy':
        # For BUY trades
        stop_loss = entry_price - (atr * 1.5)  # 1.5x ATR below entry
        take_profit = entry_price + (atr * 2.5)  # 2.5x ATR above entry (1:1.67 R:R)
    else:
        # For SELL trades
        stop_loss = entry_price + (atr * 1.5)  # 1.5x ATR above entry
        take_profit = entry_price - (atr * 2.5)  # 2.5x ATR below entry
    
    # Place order with TP and SL
    order = {
        'symbol': signal['symbol'],
        'side': side,
        'quantity': signal['size'],
        'price': entry_price,
        'stop_loss': stop_loss,  # ← THIS IS CRITICAL
        'take_profit': take_profit,  # ← THIS IS CRITICAL
        'type': 'market'
    }
    
    # Send order to broker
    result = mt5_connector.place_order(order)
    
    return result
```

### Alternative: Use Signal TP/SL

If your signals already include TP/SL:

```python
# Your logs show: "SL=1.33805, TP=1.32830"
# Make sure these are being passed to the order!

def execute_trade(signal):
    order = {
        'symbol': signal['symbol'],
        'side': signal['side'],
        'quantity': signal['size'],
        'price': signal['price'],
        'stop_loss': signal['sl'],  # ← Use from signal
        'take_profit': signal['tp'],  # ← Use from signal
        'type': 'market'
    }
    
    result = mt5_connector.place_order(order)
    return result
```

---

## 🔧 Fix 2: Correct Position Count Check

### Update pre_trade_checks.py

```python
# File: trading_bot/risk/pre_trade_checks.py

class PreTradeChecksEngine:
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Position limits
        self.max_position_size_pct = self.config.get('max_position_size_pct', 0.20)
        self.max_positions_per_symbol = self.config.get('max_positions_per_symbol', 1)
        self.max_total_positions = self.config.get('max_total_positions', 5)  # ← ADD THIS
        
        # ... rest of init ...
    
    def _check_position_count(self, order_params: Dict[str, Any],
                             portfolio_state: Dict[str, Any]) -> PreTradeCheck:
        """Check position count limits"""
        symbol = order_params.get('symbol', '')
        positions = portfolio_state.get('positions', {})
        
        # Check TOTAL positions first
        total_positions = len(positions)
        if total_positions >= self.max_total_positions:
            return PreTradeCheck(
                check_name='position_count',
                result=CheckResult.REJECTED,
                reason=f"Max total positions reached: {total_positions} >= {self.max_total_positions}"
            )
        
        # Then check per-symbol limit
        symbol_positions = sum(1 for p in positions.values() if p.get('symbol') == symbol)
        if symbol_positions >= self.max_positions_per_symbol:
            return PreTradeCheck(
                check_name='position_count',
                result=CheckResult.REJECTED,
                reason=f"Max positions for {symbol} reached: {symbol_positions}/{self.max_positions_per_symbol}"
            )
        
        return PreTradeCheck(
            check_name='position_count',
            result=CheckResult.APPROVED
        )
```

---

## 🔧 Fix 3: Integrate Position Manager

### Update Your Main Trading Loop

```python
# In your main trading loop (main.py or similar)

from trading_bot.position_manager import PositionManager, Position

# Initialize
position_manager = PositionManager({
    'max_positions': 5,
    'max_positions_per_symbol': 1,
    'confidence_shift_threshold': 0.6,
    'low_confidence_threshold': 0.3,
    'max_position_age_hours': 24
})

# Before executing new trade
async def process_signal(signal):
    # 1. Check if can open new position
    can_open, reason = position_manager.can_open_new_position(signal['symbol'])
    
    if not can_open:
        logger.warning(f"Cannot open position: {reason}")
        
        # If max positions reached, close weakest
        if "Max positions reached" in reason:
            weakest = position_manager.get_weakest_position()
            if weakest:
                logger.info(f"Closing weakest position: {weakest.symbol}")
                await close_position(weakest.ticket_id)
                position_manager.remove_position(weakest.ticket_id)
        
        return
    
    # 2. Execute trade WITH TP/SL
    order = {
        'symbol': signal['symbol'],
        'side': signal['side'],
        'quantity': signal['size'],
        'price': signal['price'],
        'stop_loss': signal['sl'],  # ← CRITICAL
        'take_profit': signal['tp'],  # ← CRITICAL
        'type': 'market'
    }
    
    result = mt5_connector.place_order(order)
    
    if result['success']:
        # 3. Add to position manager
        position = Position(
            ticket_id=result['ticket_id'],
            symbol=signal['symbol'],
            side=signal['side'],
            entry_price=signal['price'],
            current_price=signal['price'],
            size=signal['size'],
            stop_loss=signal['sl'],
            take_profit=signal['tp'],
            entry_time=datetime.now(),
            entry_confidence=signal['confidence'],
            current_confidence=signal['confidence'],
            unrealized_pnl=0.0
        )
        
        position_manager.add_position(position)
        logger.info(f"Position opened: {signal['symbol']} {signal['side']}")

# Periodic position update (every 60 seconds)
async def update_positions_loop():
    while True:
        for ticket_id, position in list(position_manager.positions.items()):
            # Get current price
            current_price = await get_current_price(position.symbol)
            
            # Get current confidence (re-analyze)
            signal = await analyze_symbol(position.symbol)
            
            # Update position
            position_manager.update_position(
                ticket_id,
                current_price,
                signal['confidence']
            )
            
            # Check if should close
            should_close, reason = position_manager.should_close_position(
                position,
                signal['confidence'],
                signal['action']
            )
            
            if should_close:
                logger.info(f"Auto-closing {ticket_id}: {reason}")
                await close_position(ticket_id)
                position_manager.remove_position(ticket_id)
        
        await asyncio.sleep(60)  # Check every 60 seconds
```

---

## 🔧 Fix 4: Update Configuration

### Add to config/config.yaml

```yaml
# Pre-trade checks
pre_trade_checks:
  max_leverage: 10.0
  max_position_size_pct: 0.20  # 20% of portfolio per position
  max_positions_per_symbol: 1  # 1 position per symbol
  max_total_positions: 5  # ← ADD THIS - Max 5 total positions
  max_orders_per_minute: 10
  
  # TP/SL requirements
  require_stop_loss: true  # ← ADD THIS - Reject orders without SL
  require_take_profit: true  # ← ADD THIS - Reject orders without TP
  min_risk_reward_ratio: 1.0  # ← ADD THIS - Minimum 1:1 R:R

# Position management
position_manager:
  max_positions: 5
  max_positions_per_symbol: 1
  confidence_shift_threshold: 0.6
  low_confidence_threshold: 0.3
  max_position_age_hours: 24
  aged_position_confidence_threshold: 0.5
  check_interval_seconds: 60

# Risk management
risk:
  default_stop_loss_atr_multiplier: 1.5  # SL = 1.5x ATR
  default_take_profit_atr_multiplier: 2.5  # TP = 2.5x ATR
  min_risk_reward_ratio: 1.5  # Minimum 1.5:1 reward:risk
```

---

## 🔧 Fix 5: Add TP/SL Validation

### Add to pre_trade_checks.py

```python
def _check_tp_sl_required(self, order_params: Dict[str, Any]) -> PreTradeCheck:
    """Check if TP and SL are provided"""
    require_sl = self.config.get('require_stop_loss', True)
    require_tp = self.config.get('require_take_profit', True)
    
    stop_loss = order_params.get('stop_loss')
    take_profit = order_params.get('take_profit')
    
    if require_sl and not stop_loss:
        return PreTradeCheck(
            check_name='tp_sl_required',
            result=CheckResult.REJECTED,
            reason="Stop loss is required but not provided"
        )
    
    if require_tp and not take_profit:
        return PreTradeCheck(
            check_name='tp_sl_required',
            result=CheckResult.REJECTED,
            reason="Take profit is required but not provided"
        )
    
    # Check risk:reward ratio
    if stop_loss and take_profit:
        entry_price = order_params.get('price', 0)
        side = order_params.get('side', 'buy')
        
        if side == 'buy':
            risk = entry_price - stop_loss
            reward = take_profit - entry_price
        else:
            risk = stop_loss - entry_price
            reward = entry_price - take_profit
        
        if risk > 0:
            rr_ratio = reward / risk
            min_rr = self.config.get('min_risk_reward_ratio', 1.0)
            
            if rr_ratio < min_rr:
                return PreTradeCheck(
                    check_name='tp_sl_required',
                    result=CheckResult.REJECTED,
                    reason=f"Risk:Reward ratio {rr_ratio:.2f} below minimum {min_rr}"
                )
    
    return PreTradeCheck(
        check_name='tp_sl_required',
        result=CheckResult.APPROVED
    )

# Add to run_all_checks():
def run_all_checks(self, order_params: Dict[str, Any], 
                  portfolio_state: Dict[str, Any]) -> List[PreTradeCheck]:
    checks = []
    
    # ... existing checks ...
    
    # 10. TP/SL required check
    checks.append(self._check_tp_sl_required(order_params))  # ← ADD THIS
    
    return checks
```

---

## 📋 Implementation Checklist

### Immediate (Do Now):
- [ ] **CRITICAL:** Ensure all orders include `stop_loss` and `take_profit`
- [ ] **CRITICAL:** Update `_check_position_count()` to check total positions
- [ ] **CRITICAL:** Add `max_total_positions: 5` to config
- [ ] Test with paper trading

### Short-term (This Week):
- [ ] Integrate PositionManager into main trading loop
- [ ] Add TP/SL validation to pre-trade checks
- [ ] Implement auto-close for weak positions
- [ ] Add position monitoring loop

### Medium-term (Next Week):
- [ ] Add ATR-based dynamic TP/SL calculation
- [ ] Implement trailing stops
- [ ] Add position scaling (partial exits)
- [ ] Enhanced risk management

---

## 🧪 Testing

### Test 1: Verify TP/SL Placement

```python
# Check MT5 positions
import MetaTrader5 as mt5

positions = mt5.positions_get()
for pos in positions:
    print(f"Symbol: {pos.symbol}")
    print(f"  Entry: {pos.price_open}")
    print(f"  SL: {pos.sl}")  # ← Should NOT be 0.0
    print(f"  TP: {pos.tp}")  # ← Should NOT be 0.0
    print(f"  Current: {pos.price_current}")
    print()
```

### Test 2: Verify Position Limits

```python
# Should reject when 5 positions open
positions = mt5.positions_get()
print(f"Current positions: {len(positions)}")

if len(positions) >= 5:
    print("✓ Max positions reached - new signals should be rejected")
else:
    print(f"✗ Only {len(positions)} positions - can open more")
```

### Test 3: Verify Auto-Close

```python
# Monitor position manager
status = position_manager.get_status()
print(f"Active: {status['active_positions']}")
print(f"Auto-closes today: {status['auto_closes_today']}")
print(f"Avg confidence: {status['avg_confidence']:.2f}")
```

---

## 🚨 Emergency Stop

If trades are running without TP/SL:

```python
# EMERGENCY: Close all positions
import MetaTrader5 as mt5

positions = mt5.positions_get()
for pos in positions:
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": pos.symbol,
        "volume": pos.volume,
        "type": mt5.ORDER_TYPE_SELL if pos.type == 0 else mt5.ORDER_TYPE_BUY,
        "position": pos.ticket,
        "magic": 234000,
        "comment": "Emergency close - no TP/SL",
    }
    result = mt5.order_send(request)
    print(f"Closed {pos.symbol}: {result.comment}")
```

---

## 📞 Support

If issues persist:
1. Check logs in `diagnostics/` directory
2. Verify MT5 connection
3. Check config files
4. Review order execution code

**Status:** 🔴 CRITICAL - Fix immediately before continuing trading!
