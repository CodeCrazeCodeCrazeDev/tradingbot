"""
Slippage Protection System

Monitors and protects against excessive slippage.
"""

import logging
from typing import Any, Dict, List, Optional
from datetime import datetime
from collections import deque
from dataclasses import dataclass
from typing import Set
import asyncio

# Evolution: Added retry decorator
def retry(max_attempts=3, delay=1.0):
    """Retry decorator for resilient operations"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    if attempt < max_attempts - 1:
                        await asyncio.sleep(delay * (attempt + 1))
            raise last_error
        return wrapper
    return decorator



logger = logging.getLogger(__name__)


@dataclass
class SlippageRecord:
    """Record of slippage for an order"""
    order_id: str
    symbol: str
    expected_price: float
    actual_price: float
    slippage_bps: float
    slippage_pct: float
    volume: float
    timestamp: datetime


class SlippageProtection:
    """
    Slippage monitoring and protection system
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Slippage limits
        self.max_slippage_bps = self.config.get('max_slippage_bps', 50)  # 5 pips
        self.max_slippage_pct = self.config.get('max_slippage_pct', 0.005)  # 0.5%
        
        # Tracking
        self.slippage_history = deque(maxlen=1000)
        self.symbol_slippage = {}
        
        # Statistics
        self.total_slippage_cost = 0.0
        self.rejected_orders = 0
    
    async def execute_with_protection(
        self,
        broker,
        symbol: str,
        order_type: str,
        volume: float,
        expected_price: float,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Execute order with slippage protection
        
        Args:
            broker: Broker adapter
            symbol: Trading symbol
            order_type: 'buy' or 'sell'
            volume: Order volume
            expected_price: Expected execution price
            **kwargs: Additional order parameters
        
        Returns:
            Order result
        
        Raises:
            ExcessiveSlippageError: If slippage exceeds limits
        """
        # Place order
        result = await broker.place_order(
            symbol=symbol,
            order_type=order_type,
            volume=volume,
            **kwargs
        )
        
        # Get actual fill price
        actual_price = result.get('price')
        
        if not actual_price:
            logger.warning("No fill price in result, cannot check slippage")
            return result
        
        # Calculate slippage
        slippage = self._calculate_slippage(
            expected_price=expected_price,
            actual_price=actual_price,
            order_type=order_type
        )
        
        # Record slippage
        record = SlippageRecord(
            order_id=result.get('order_id', 'unknown'),
            symbol=symbol,
            expected_price=expected_price,
            actual_price=actual_price,
            slippage_bps=slippage['bps'],
            slippage_pct=slippage['pct'],
            volume=volume,
            timestamp=datetime.now()
        )
        
        self._record_slippage(record)
        
        # Check if slippage exceeds limits
        if slippage['bps'] > self.max_slippage_bps:
            logger.critical(
                f"EXCESSIVE SLIPPAGE: {slippage['bps']:.2f} bps "
                f"(limit: {self.max_slippage_bps} bps) for {symbol}"
            )
            
            # Try to cancel if partially filled
            if result.get('status') == 'partial':
                try:
                    await broker.cancel_order(result['order_id'])
                    logger.info(f"Cancelled order due to excessive slippage")
                except Exception as e:
                    logger.error(f"Failed to cancel order: {e}")
            
            self.rejected_orders += 1
            raise ExcessiveSlippageError(
                f"Slippage {slippage['bps']:.2f} bps exceeds limit {self.max_slippage_bps} bps"
            )
        
        # Log slippage
        if slippage['bps'] > self.max_slippage_bps * 0.5:
            logger.warning(
                f"High slippage: {slippage['bps']:.2f} bps for {symbol} "
                f"(expected: {expected_price}, actual: {actual_price})"
            )
        else:
            logger.info(f"Slippage: {slippage['bps']:.2f} bps for {symbol}")
        
        return result
    
    def _calculate_slippage(
        self,
        expected_price: float,
        actual_price: float,
        order_type: str
    ) -> Dict[str, float]:
        """
        Calculate slippage in basis points and percentage
        
        Args:
            expected_price: Expected price
            actual_price: Actual fill price
            order_type: 'buy' or 'sell'
        
        Returns:
            Dict with slippage in bps and pct
        """
        # For buy orders, positive slippage means paid more
        # For sell orders, positive slippage means received less
        if order_type.lower() == 'buy':
            slippage = actual_price - expected_price
        else:
            slippage = expected_price - actual_price
        
        # Calculate in basis points (1 bp = 0.01%)
        slippage_bps = (slippage / expected_price) * 10000
        
        # Calculate in percentage
        slippage_pct = (slippage / expected_price)
        
        return {
            'bps': abs(slippage_bps),
            'pct': abs(slippage_pct),
            'raw': slippage
        }
    
    def _record_slippage(self, record: SlippageRecord):
        """Record slippage data"""
        # Add to history
        self.slippage_history.append(record)
        
        # Update symbol-specific tracking
        if record.symbol not in self.symbol_slippage:
            self.symbol_slippage[record.symbol] = deque(maxlen=100)
        
        self.symbol_slippage[record.symbol].append(record)
        
        # Update total cost
        cost = record.slippage_pct * record.expected_price * record.volume
        self.total_slippage_cost += cost
    
    def get_slippage_stats(self, symbol: Optional[str] = None) -> Dict[str, Any]:
        """
        Get slippage statistics
        
        Args:
            symbol: Optional symbol to filter by
        
        Returns:
            Slippage statistics
        """
        if symbol:
            records = list(self.symbol_slippage.get(symbol, []))
        else:
            records = list(self.slippage_history)
        
        if not records:
            return {
                'count': 0,
                'avg_slippage_bps': 0,
                'max_slippage_bps': 0,
                'min_slippage_bps': 0,
                'total_cost': 0
            }
        
        slippages = [r.slippage_bps for r in records]
        
        return {
            'count': len(records),
            'avg_slippage_bps': sum(slippages) / len(slippages),
            'max_slippage_bps': max(slippages),
            'min_slippage_bps': min(slippages),
            'median_slippage_bps': sorted(slippages)[len(slippages) // 2],
            'total_cost': sum(r.slippage_pct * r.expected_price * r.volume for r in records),
            'rejected_orders': self.rejected_orders
        }
    
    def get_symbol_slippage_report(self) -> Dict[str, Dict[str, Any]]:
        """Get slippage report by symbol"""
        report = {}
        
        for symbol in self.symbol_slippage:
            report[symbol] = self.get_slippage_stats(symbol)
        
        return report
    
    def adjust_limits_based_on_history(self):
        """Dynamically adjust slippage limits based on historical data"""
        if len(self.slippage_history) < 50:
            return  # Need more data
        
        # Calculate 95th percentile of historical slippage
        slippages = sorted([r.slippage_bps for r in self.slippage_history])
        percentile_95 = slippages[int(len(slippages) * 0.95)]
        
        # Set limit to 95th percentile + 20% buffer
        new_limit = percentile_95 * 1.2
        
        if new_limit != self.max_slippage_bps:
            logger.info(
                f"Adjusting slippage limit from {self.max_slippage_bps:.2f} "
                f"to {new_limit:.2f} bps based on historical data"
            )
            self.max_slippage_bps = new_limit


class ExcessiveSlippageError(Exception):
    """Slippage exceeds acceptable limits"""
    pass


# Export
__all__ = [
    'SlippageProtection',
    'SlippageRecord',
    'ExcessiveSlippageError'
]
