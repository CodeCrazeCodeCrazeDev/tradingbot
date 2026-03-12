import logging
"""
Position Sizing Improvements - Optional Enhancements
These improvements add better position management and signal confirmation
"""

import asyncio
from datetime import datetime
from typing import Dict, Optional, Set
from loguru import logger

logger = logging.getLogger(__name__)



class PositionManager:
    """Manages open positions to prevent duplicate trades"""
    
    def __init__(self):
        self.open_positions: Dict[str, Dict] = {}
        self.last_trade_time: Dict[str, datetime] = {}
        self.min_time_between_trades: int = 60  # seconds
    
    def has_open_position(self, symbol: str) -> bool:
        """Check if symbol has an open position"""
        return symbol in self.open_positions
    
    def add_position(self, symbol: str, lot_size: float, direction: int, entry_price: float = None):
        """Add a new open position"""
        self.open_positions[symbol] = {
            'lot_size': lot_size,
            'direction': direction,
            'entry_price': entry_price,
            'entry_time': datetime.now()
        }
        self.last_trade_time[symbol] = datetime.now()
        logger.info(f"Position opened: {symbol} {lot_size} lots {'LONG' if direction > 0 else 'SHORT'}")
    
    def remove_position(self, symbol: str):
        """Remove a closed position"""
        if symbol in self.open_positions:
            del self.open_positions[symbol]
            logger.info(f"Position closed: {symbol}")
    
    def can_trade(self, symbol: str) -> bool:
        """Check if enough time has passed since last trade"""
        if symbol not in self.last_trade_time:
            return True
        
        time_since_last = (datetime.now() - self.last_trade_time[symbol]).total_seconds()
        return time_since_last >= self.min_time_between_trades
    
    def get_position(self, symbol: str) -> Optional[Dict]:
        """Get open position details"""
        return self.open_positions.get(symbol)
    
    def get_all_positions(self) -> Dict[str, Dict]:
        """Get all open positions"""
        return self.open_positions.copy()
    
    def clear_all(self):
        """Clear all positions (use with caution)"""
        self.open_positions.clear()
        logger.warning("All positions cleared from tracker")


class CandleTracker:
    """Tracks candle closes to ensure signals only on new candles"""
    
    def __init__(self):
        self.last_candle_times: Dict[str, datetime] = {}
        self.candle_data: Dict[str, Dict] = {}
    
    def is_new_candle(self, symbol: str, current_time: datetime) -> bool:
        """Check if this is a new candle"""
        if symbol not in self.last_candle_times:
            self.last_candle_times[symbol] = current_time
            return True
        
        if current_time > self.last_candle_times[symbol]:
            self.last_candle_times[symbol] = current_time
            return True
        
        return False
    
    def update_candle(self, symbol: str, candle_time: datetime, ohlc: Dict = None):
        """Update candle data"""
        self.last_candle_times[symbol] = candle_time
        if ohlc:
            self.candle_data[symbol] = {
                'time': candle_time,
                'open': ohlc.get('open'),
                'high': ohlc.get('high'),
                'low': ohlc.get('low'),
                'close': ohlc.get('close'),
                'volume': ohlc.get('volume')
            }
    
    def get_last_candle_time(self, symbol: str) -> Optional[datetime]:
        """Get last candle time for symbol"""
        return self.last_candle_times.get(symbol)
    
    def wait_for_new_candle(self, symbol: str, current_time: datetime) -> bool:
        """Determine if we should wait for new candle"""
        return not self.is_new_candle(symbol, current_time)


class TradeFrequencyLimiter:
    """Limits trade frequency to prevent overtrading"""
    
    def __init__(self, max_trades_per_hour: int = 60, max_trades_per_day: int = 500):
        self.max_trades_per_hour = max_trades_per_hour
        self.max_trades_per_day = max_trades_per_day
        self.trade_history: Dict[str, list] = {}
    
    def can_trade(self, symbol: str) -> tuple[bool, str]:
        """Check if trading is allowed based on frequency limits"""
        now = datetime.now()
        
        # Initialize history for symbol if needed
        if symbol not in self.trade_history:
            self.trade_history[symbol] = []
        
        # Clean old trades (older than 24 hours)
        self.trade_history[symbol] = [
            t for t in self.trade_history[symbol]
            if (now - t).total_seconds() < 86400
        ]
        
        # Check daily limit
        daily_trades = len(self.trade_history[symbol])
        if daily_trades >= self.max_trades_per_day:
            return False, f"Daily limit reached ({daily_trades}/{self.max_trades_per_day})"
        
        # Check hourly limit
        hourly_trades = len([
            t for t in self.trade_history[symbol]
            if (now - t).total_seconds() < 3600
        ])
        if hourly_trades >= self.max_trades_per_hour:
            return False, f"Hourly limit reached ({hourly_trades}/{self.max_trades_per_hour})"
        
        return True, "OK"
    
    def record_trade(self, symbol: str):
        """Record a trade execution"""
        if symbol not in self.trade_history:
            self.trade_history[symbol] = []
        self.trade_history[symbol].append(datetime.now())
    
    def get_stats(self, symbol: str) -> Dict:
        """Get trading frequency statistics"""
        if symbol not in self.trade_history:
            return {'hourly': 0, 'daily': 0}
        
        now = datetime.now()
        hourly = len([t for t in self.trade_history[symbol] if (now - t).total_seconds() < 3600])
        daily = len([t for t in self.trade_history[symbol] if (now - t).total_seconds() < 86400])
        
        return {
            'hourly': hourly,
            'daily': daily,
            'hourly_limit': self.max_trades_per_hour,
            'daily_limit': self.max_trades_per_day
        }


# Example usage in main.py:
"""
# Initialize at startup
position_manager = PositionManager()
candle_tracker = CandleTracker()
frequency_limiter = TradeFrequencyLimiter(max_trades_per_hour=60, max_trades_per_day=500)

# In trading loop, before executing trade:
async def execute_trade_with_checks(symbol, position, executor):
    # Check 1: No existing position
    if position_manager.has_open_position(symbol):
        logger.info(f"Skipping {symbol} - position already open")
        return False
    
    # Check 2: Enough time since last trade
    if not position_manager.can_trade(symbol):
        logger.info(f"Skipping {symbol} - minimum time between trades not met")
        return False
    
    # Check 3: Frequency limits
    can_trade, reason = frequency_limiter.can_trade(symbol)
    if not can_trade:
        logger.warning(f"Skipping {symbol} - {reason}")
        return False
    
    # Check 4: New candle (optional)
    current_candle_time = rates[-1]['time']
    if not candle_tracker.is_new_candle(symbol, current_candle_time):
        logger.debug(f"Skipping {symbol} - waiting for new candle")
        return False
    
    # All checks passed - execute trade
    try:
        await executor.execute_trade(
            symbol=symbol,
            direction=1 if position.lot > 0 else -1,
            size=abs(position.lot)
        )
        
        # Record the trade
        position_manager.add_position(symbol, position.lot, 1 if position.lot > 0 else -1)
        frequency_limiter.record_trade(symbol)
        candle_tracker.update_candle(symbol, current_candle_time)
        
        return True
    except Exception as e:
        logger.error(f"Trade execution failed: {e}")
        return False
"""


# Testing functions
def test_position_manager():
    """Test position manager functionality"""
    pm = PositionManager()
    
    # Test adding position
    assert not pm.has_open_position("EURUSD")
    pm.add_position("EURUSD", 1.0, 1, 1.1000)
    assert pm.has_open_position("EURUSD")
    
    # Test getting position
    pos = pm.get_position("EURUSD")
    assert pos['lot_size'] == 1.0
    assert pos['direction'] == 1
    
    # Test removing position
    pm.remove_position("EURUSD")
    assert not pm.has_open_position("EURUSD")
    
    print("✅ PositionManager tests passed")


def test_candle_tracker():
    """Test candle tracker functionality"""
    ct = CandleTracker()
    
    time1 = datetime(2025, 1, 1, 12, 0, 0)
    time2 = datetime(2025, 1, 1, 12, 1, 0)
    
    # First candle should be new
    assert ct.is_new_candle("EURUSD", time1)
    
    # Same time should not be new
    assert not ct.is_new_candle("EURUSD", time1)
    
    # Later time should be new
    assert ct.is_new_candle("EURUSD", time2)
    
    print("✅ CandleTracker tests passed")


def test_frequency_limiter():
    """Test frequency limiter functionality"""
    fl = TradeFrequencyLimiter(max_trades_per_hour=5, max_trades_per_day=10)
    
    # Should allow first trade
    can_trade, reason = fl.can_trade("EURUSD")
    assert can_trade
    
    # Record trades up to hourly limit
    for i in range(5):
        fl.record_trade("EURUSD")
    
    # Should block after limit
    can_trade, reason = fl.can_trade("EURUSD")
    assert not can_trade
    assert "Hourly limit" in reason
    
    print("✅ TradeFrequencyLimiter tests passed")


if __name__ == "__main__":
    print("Running position sizing improvement tests...")
    test_position_manager()
    test_candle_tracker()
    test_frequency_limiter()
    print("\n✅ All tests passed!")
