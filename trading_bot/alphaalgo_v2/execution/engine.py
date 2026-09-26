"""
AlphaAlgo V2 Execution Engine

Main execution engine coordinating order execution.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
import uuid

from ..core.interfaces import IExecutor
from ..core.types import (
    Signal,
    SignalType,
    Order,
    OrderType,
    OrderStatus,
    Position,
    ExecutionResult,
)
from ..core.exceptions import ExecutionError
from .brokers.base import BaseBroker
from .brokers.paper import PaperBroker
from .algorithms.smart import SmartOrderRouter, ExecutionPlan

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


class ExecutionEngine:
    """
    Main execution engine
    
    Coordinates:
    - Broker connections
    - Order routing
    - Execution algorithms
    - Fill tracking
    - Slippage monitoring
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Broker
        self._broker: Optional[BaseBroker] = None
        
        # Smart order router
        self._router = SmartOrderRouter(self.config.get("router", {}))
        
        # Order tracking
        self._pending_orders: Dict[str, Order] = {}
        self._executed_orders: Dict[str, ExecutionResult] = {}
        
        # Statistics
        self._total_orders = 0
        self._successful_orders = 0
        self._total_slippage = 0.0
    
    async def initialize(self, broker: Optional[BaseBroker] = None) -> bool:
        """
        Initialize execution engine
        
        Args:
            broker: Broker to use (defaults to paper broker)
            
        Returns:
            True if initialization successful
        """
        try:
            # Use provided broker or create paper broker
            self._broker = broker or PaperBroker(self.config.get("broker", {}))
            
            # Connect to broker
            if not self._broker.is_connected:
                await self._broker.connect()
            
            logger.info(f"Execution engine initialized with {self._broker.name}")
            return True
            
        except Exception as e:
            logger.error(f"Execution engine initialization failed: {e}")
            return False
    
    async def shutdown(self) -> None:
        """Shutdown execution engine"""
        if self._broker:
            await self._broker.disconnect()
        logger.info("Execution engine shutdown")
    
    async def execute_signal(
        self,
        signal: Signal,
        position_size: float,
        market_conditions: Optional[Dict] = None
    ) -> ExecutionResult:
        """
        Execute a trading signal
        
        Args:
            signal: Trading signal
            position_size: Position size to execute
            market_conditions: Current market conditions
            
        Returns:
            ExecutionResult
        """
        if not self._broker or not self._broker.is_connected:
            return ExecutionResult(
                success=False,
                order_id="",
                message="Broker not connected",
            )
        
        # Create order from signal
        order = self._create_order_from_signal(signal, position_size)
        
        # Get execution plan
        plan = self._router.create_execution_plan(order, market_conditions)
        
        logger.info(
            f"Executing signal: {signal.signal_type.value} {signal.symbol} "
            f"size={position_size} algo={plan.algorithm.value}"
        )
        
        # Execute based on plan
        if plan.slices > 1:
            return await self._execute_sliced(order, plan)
        else:
            return await self._execute_single(order)
    
    async def _execute_single(self, order: Order) -> ExecutionResult:
        """Execute single order"""
        self._total_orders += 1
        self._pending_orders[order.id] = order
        
        try:
            result = await self._broker.execute(order)
            
            if result.success:
                self._successful_orders += 1
                self._total_slippage += result.slippage
            
            self._executed_orders[order.id] = result
            del self._pending_orders[order.id]
            
            return result
            
        except Exception as e:
            logger.error(f"Execution failed: {e}")
            del self._pending_orders[order.id]
            return ExecutionResult(
                success=False,
                order_id=order.id,
                message=str(e),
            )
    
    async def _execute_sliced(
        self,
        order: Order,
        plan: ExecutionPlan
    ) -> ExecutionResult:
        """Execute order in slices"""
        child_orders = self._router.slice_order(order, plan)
        
        results = []
        total_filled = 0.0
        total_cost = 0.0
        
        for i, child in enumerate(child_orders):
            # Execute slice
            result = await self._execute_single(child)
            results.append(result)
            
            if result.success and result.fill_volume:
                total_filled += result.fill_volume
                total_cost += result.fill_price * result.fill_volume
            
            # Wait between slices
            if i < len(child_orders) - 1:
                await asyncio.sleep(plan.interval_seconds)
        
        # Aggregate results
        success = total_filled > 0
        avg_price = total_cost / total_filled if total_filled > 0 else 0
        
        return ExecutionResult(
            success=success,
            order_id=order.id,
            fill_price=avg_price,
            fill_volume=total_filled,
            slippage=sum(r.slippage for r in results if r.success) / len(results),
            latency_ms=sum(r.latency_ms for r in results),
            message=f"Executed {len([r for r in results if r.success])}/{len(results)} slices",
            metadata={
                "slices": len(child_orders),
                "algorithm": plan.algorithm.value,
            },
        )
    
    def _create_order_from_signal(
        self,
        signal: Signal,
        position_size: float
    ) -> Order:
        """Create order from signal"""
        return Order(
            id=str(uuid.uuid4()),
            symbol=signal.symbol,
            order_type=OrderType.MARKET,
            side=signal.signal_type,
            volume=position_size,
            price=signal.price,
            stop_loss=signal.stop_loss,
            take_profit=signal.take_profit,
            signal_id=signal.id,
            metadata={
                "source": signal.source,
                "confidence": signal.confidence,
            },
        )
    
    async def cancel_order(self, order_id: str) -> bool:
        """Cancel pending order"""
        if not self._broker:
            return False
        return await self._broker.cancel(order_id)
    
    async def modify_order(
        self,
        order_id: str,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None
    ) -> bool:
        """Modify order SL/TP"""
        if not self._broker:
            return False
        return await self._broker.modify(order_id, stop_loss, take_profit)
    
    async def close_position(
        self,
        symbol: str,
        volume: Optional[float] = None
    ) -> ExecutionResult:
        """Close position"""
        if not self._broker:
            return ExecutionResult(
                success=False,
                order_id="",
                message="Broker not connected",
            )
        return await self._broker.close_position(symbol, volume)
    
    async def close_all_positions(self) -> List[ExecutionResult]:
        """Close all positions"""
        if not self._broker:
            return []
        
        positions = await self._broker.get_positions()
        results = []
        
        for position in positions:
            result = await self._broker.close_position(position.symbol)
            results.append(result)
        
        return results
    
    async def get_position(self, symbol: str) -> Optional[Position]:
        """Get position for symbol"""
        if not self._broker:
            return None
        return await self._broker.get_position(symbol)
    
    async def get_positions(self) -> List[Position]:
        """Get all positions"""
        if not self._broker:
            return []
        return await self._broker.get_positions()
    
    async def get_account_info(self) -> Dict[str, Any]:
        """Get account information"""
        if not self._broker:
            return {}
        return await self._broker.get_account_info()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get execution statistics"""
        success_rate = (
            self._successful_orders / self._total_orders
            if self._total_orders > 0 else 0.0
        )
        avg_slippage = (
            self._total_slippage / self._successful_orders
            if self._successful_orders > 0 else 0.0
        )
        
        return {
            "total_orders": self._total_orders,
            "successful_orders": self._successful_orders,
            "success_rate": success_rate,
            "pending_orders": len(self._pending_orders),
            "avg_slippage_pips": avg_slippage,
            "broker": self._broker.name if self._broker else None,
            "paper_mode": self._broker.is_paper_mode if self._broker else True,
        }
