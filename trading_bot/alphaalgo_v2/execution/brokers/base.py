"""
AlphaAlgo V2 Base Broker

Abstract base class for all broker adapters.
"""

import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional

from ...core.interfaces import IExecutor
from ...core.types import (
    Order,
    OrderType,
    OrderStatus,
    Position,
    ExecutionResult,
    SignalType,
)
from ...core.exceptions import ExecutionError, BrokerConnectionError
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


class BaseBroker(IExecutor):
    """
    Abstract base class for broker adapters
    
    Provides common functionality:
    - Connection management
    - Order tracking
    - Position management
    - Error handling
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self._name = self.config.get("name", "base")
        self._connected = False
        self._paper_mode = self.config.get("paper_mode", True)
        
        # Order and position tracking
        self._orders: Dict[str, Order] = {}
        self._positions: Dict[str, Position] = {}
        
        # Account info
        self._balance = self.config.get("initial_balance", 10000.0)
        self._equity = self._balance
        self._margin_used = 0.0
    
    @property
    def name(self) -> str:
        return self._name
    
    @property
    def is_connected(self) -> bool:
        return self._connected
    
    @property
    def is_paper_mode(self) -> bool:
        return self._paper_mode
    
    async def connect(self) -> bool:
        """Connect to broker"""
        try:
            self._connected = await self._do_connect()
            if self._connected:
                logger.info(f"Connected to {self._name}")
            return self._connected
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            raise BrokerConnectionError(str(e), broker=self._name)
    
    async def disconnect(self) -> None:
        """Disconnect from broker"""
        try:
            await self._do_disconnect()
            self._connected = False
            logger.info(f"Disconnected from {self._name}")
        except Exception as e:
            logger.error(f"Disconnect error: {e}")
    
    @abstractmethod
    async def _do_connect(self) -> bool:
        """Implementation-specific connection"""
        pass
    
    @abstractmethod
    async def _do_disconnect(self) -> None:
        """Implementation-specific disconnection"""
        pass
    
    @abstractmethod
    async def execute(self, order: Order) -> ExecutionResult:
        """Execute order"""
        pass
    
    @abstractmethod
    async def cancel(self, order_id: str) -> bool:
        """Cancel order"""
        pass
    
    @abstractmethod
    async def modify(
        self,
        order_id: str,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None
    ) -> bool:
        """Modify order"""
        pass
    
    async def get_position(self, symbol: str) -> Optional[Position]:
        """Get position for symbol"""
        return self._positions.get(symbol)
    
    async def get_positions(self) -> List[Position]:
        """Get all positions"""
        return list(self._positions.values())
    
    async def get_account_info(self) -> Dict[str, Any]:
        """Get account information"""
        return {
            "balance": self._balance,
            "equity": self._equity,
            "margin_used": self._margin_used,
            "margin_free": self._equity - self._margin_used,
            "margin_level": (self._equity / self._margin_used * 100) if self._margin_used > 0 else 0,
        }
    
    @abstractmethod
    async def close_position(
        self,
        symbol: str,
        volume: Optional[float] = None
    ) -> ExecutionResult:
        """Close position"""
        pass
    
    def _validate_order(self, order: Order) -> bool:
        """Validate order before execution"""
        if order.volume <= 0:
            logger.error(f"Invalid volume: {order.volume}")
            return False
        
        if order.order_type == OrderType.LIMIT and order.price is None:
            logger.error("Limit order requires price")
            return False
        
        return True
    
    def _calculate_margin(self, order: Order, price: float) -> float:
        """Calculate margin required for order"""
        leverage = self.config.get("leverage", 100)
        return (order.volume * price) / leverage
