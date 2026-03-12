"""
Live Order Router - Production-Ready Order Routing System

Unified order routing across multiple brokers:
- Smart order routing
- Failover handling
- Order reconciliation
- Execution quality tracking
- Audit logging
"""

import asyncio
import logging
import uuid
from typing import Any, Callable, Dict, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict
import json

logger = logging.getLogger(__name__)

try:
    from trading_bot.brokers.broker_adapter import (
        BrokerAdapter, Position, OrderResponse, OrderStatus, OrderSide, OrderType
    )
except ImportError:
    pass

try:
    from dataclasses import dataclass
    
    class OrderStatus(Enum):
        PENDING = "pending"
        FILLED = "filled"
        PARTIALLY_FILLED = "partially_filled"
        CANCELLED = "cancelled"
        REJECTED = "rejected"
    
    class OrderSide(Enum):
        BUY = "buy"
        SELL = "sell"
    
    class OrderType(Enum):
        MARKET = "market"
        LIMIT = "limit"
        STOP = "stop"
        STOP_LIMIT = "stop_limit"
    
    @dataclass
    class OrderResponse:
        order_id: str
        status: OrderStatus
        filled_quantity: float
        average_fill_price: float
        commission: float
        timestamp: datetime
        metadata: Dict[str, Any]
    
    class BrokerAdapter:
        pass


except Exception:
    pass
class RoutingStrategy(Enum):
    """Order routing strategies"""
    PRIMARY_ONLY = "primary_only"
    FAILOVER = "failover"
    BEST_PRICE = "best_price"
    SPLIT = "split"
    ROUND_ROBIN = "round_robin"


class BrokerHealth(Enum):
    """Broker health status"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    OFFLINE = "offline"


@dataclass
class BrokerStatus:
    """Broker status tracking"""
    broker_id: str
    health: BrokerHealth
    last_check: datetime
    latency_ms: float = 0.0
    success_rate: float = 1.0
    consecutive_failures: int = 0
    total_orders: int = 0
    failed_orders: int = 0
    
    def to_dict(self) -> Dict:
        return {
            'broker_id': self.broker_id,
            'health': self.health.value,
            'last_check': self.last_check.isoformat(),
            'latency_ms': self.latency_ms,
            'success_rate': self.success_rate,
            'consecutive_failures': self.consecutive_failures
        }


@dataclass
class OrderRecord:
    """Complete order record for audit"""
    order_id: str
    client_order_id: str
    broker_id: str
    symbol: str
    side: OrderSide
    order_type: OrderType
    quantity: float
    price: Optional[float]
    stop_price: Optional[float]
    status: OrderStatus
    filled_quantity: float
    average_fill_price: float
    commission: float
    created_at: datetime
    updated_at: datetime
    filled_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            'order_id': self.order_id,
            'client_order_id': self.client_order_id,
            'broker_id': self.broker_id,
            'symbol': self.symbol,
            'side': self.side.value,
            'order_type': self.order_type.value,
            'quantity': self.quantity,
            'price': self.price,
            'stop_price': self.stop_price,
            'status': self.status.value,
            'filled_quantity': self.filled_quantity,
            'average_fill_price': self.average_fill_price,
            'commission': self.commission,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'filled_at': self.filled_at.isoformat() if self.filled_at else None,
            'error_message': self.error_message,
            'metadata': self.metadata
        }


@dataclass
class ExecutionQuality:
    """Execution quality metrics"""
    order_id: str
    expected_price: float
    executed_price: float
    slippage_bps: float
    latency_ms: float
    fill_rate: float
    timestamp: datetime


class LiveOrderRouter:
    """
    Production-ready order router with multi-broker support.
    
    Features:
    - Multiple broker support
    - Smart routing strategies
    - Automatic failover
    - Order reconciliation
    - Execution quality tracking
    - Complete audit trail
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Brokers
        self.brokers: Dict[str, BrokerAdapter] = {}
        self.broker_status: Dict[str, BrokerStatus] = {}
        self.primary_broker: Optional[str] = None
        
        # Routing
        self.routing_strategy = RoutingStrategy(
            self.config.get('routing_strategy', 'failover')
        )
        self.max_retries = self.config.get('max_retries', 3)
        self.retry_delay = self.config.get('retry_delay', 1.0)
        
        # Order tracking
        self.orders: Dict[str, OrderRecord] = {}
        self.pending_orders: Dict[str, OrderRecord] = {}
        self.execution_quality: List[ExecutionQuality] = []
        
        # Callbacks
        self.on_order_update: Optional[Callable] = None
        self.on_fill: Optional[Callable] = None
        self.on_error: Optional[Callable] = None
        
        # Health check
        self.health_check_interval = self.config.get('health_check_interval', 30)
        self._health_check_task: Optional[asyncio.Task] = None
        
        # Reconciliation
        self.reconciliation_interval = self.config.get('reconciliation_interval', 60)
        self._reconciliation_task: Optional[asyncio.Task] = None
        
        # Audit log
        self.audit_log: List[Dict] = []
        self.max_audit_entries = self.config.get('max_audit_entries', 10000)
        
        logger.info("LiveOrderRouter initialized")
    
    def register_broker(
        self,
        broker_id: str,
        broker: BrokerAdapter,
        is_primary: bool = False
    ):
        """Register a broker"""
        self.brokers[broker_id] = broker
        self.broker_status[broker_id] = BrokerStatus(
            broker_id=broker_id,
            health=BrokerHealth.HEALTHY,
            last_check=datetime.now()
        )
        
        if is_primary or self.primary_broker is None:
            self.primary_broker = broker_id
        
        self._log_audit('broker_registered', {'broker_id': broker_id, 'is_primary': is_primary})
        logger.info(f"Broker registered: {broker_id} (primary={is_primary})")
    
    def unregister_broker(self, broker_id: str):
        """Unregister a broker"""
        if broker_id in self.brokers:
            del self.brokers[broker_id]
            del self.broker_status[broker_id]
            
            if self.primary_broker == broker_id:
                self.primary_broker = next(iter(self.brokers.keys()), None)
            
            self._log_audit('broker_unregistered', {'broker_id': broker_id})
            logger.info(f"Broker unregistered: {broker_id}")
    
    async def connect_all(self) -> Dict[str, bool]:
        """Connect to all brokers"""
        results = {}
        
        for broker_id, broker in self.brokers.items():
            try:
                success = await broker.connect()
                results[broker_id] = success
                
                if success:
                    self.broker_status[broker_id].health = BrokerHealth.HEALTHY
                else:
                    self.broker_status[broker_id].health = BrokerHealth.OFFLINE
                
            except Exception as e:
                logger.error(f"Failed to connect broker {broker_id}: {e}")
                results[broker_id] = False
                self.broker_status[broker_id].health = BrokerHealth.OFFLINE
        
        self._log_audit('connect_all', {'results': results})
        return results
    
    async def disconnect_all(self):
        """Disconnect from all brokers"""
        for broker_id, broker in self.brokers.items():
            try:
                await broker.disconnect()
            except Exception as e:
                logger.error(f"Failed to disconnect broker {broker_id}: {e}")
        
        self._log_audit('disconnect_all', {})
    
    async def start(self):
        """Start the order router"""
        # Start health check
        self._health_check_task = asyncio.create_task(self._health_check_loop())
        
        # Start reconciliation
        self._reconciliation_task = asyncio.create_task(self._reconciliation_loop())
        
        logger.info("LiveOrderRouter started")
    
    async def stop(self):
        """Stop the order router"""
        if self._health_check_task:
            self._health_check_task.cancel()
        
        if self._reconciliation_task:
            self._reconciliation_task.cancel()
        
        logger.info("LiveOrderRouter stopped")
    
    def _select_broker(self, symbol: str = None) -> Optional[str]:
        """Select broker based on routing strategy"""
        healthy_brokers = [
            bid for bid, status in self.broker_status.items()
            if status.health in [BrokerHealth.HEALTHY, BrokerHealth.DEGRADED]
        ]
        
        if not healthy_brokers:
            return None
        
        if self.routing_strategy == RoutingStrategy.PRIMARY_ONLY:
            if self.primary_broker in healthy_brokers:
                return self.primary_broker
            return None
        
        elif self.routing_strategy == RoutingStrategy.FAILOVER:
            if self.primary_broker in healthy_brokers:
                return self.primary_broker
            return healthy_brokers[0]
        
        elif self.routing_strategy == RoutingStrategy.ROUND_ROBIN:
            # Simple round-robin based on order count
            min_orders = min(
                self.broker_status[bid].total_orders
                for bid in healthy_brokers
            )
            for bid in healthy_brokers:
                if self.broker_status[bid].total_orders == min_orders:
                    return bid
        
        elif self.routing_strategy == RoutingStrategy.BEST_PRICE:
            # Would need price comparison - default to primary
            if self.primary_broker in healthy_brokers:
                return self.primary_broker
            return healthy_brokers[0]
        
        return healthy_brokers[0] if healthy_brokers else None
    
    async def place_order(
        self,
        symbol: str,
        side: OrderSide,
        order_type: OrderType,
        quantity: float,
        price: Optional[float] = None,
        stop_price: Optional[float] = None,
        client_order_id: Optional[str] = None,
        **kwargs
    ) -> Optional[OrderRecord]:
        """
        Place an order with automatic routing and failover.
        
        Args:
            symbol: Trading symbol
            side: Buy or sell
            order_type: Order type
            quantity: Order quantity
            price: Limit price
            stop_price: Stop price
            client_order_id: Client order ID
            **kwargs: Additional parameters
        
        Returns:
            OrderRecord if successful, None otherwise
        """
        client_order_id = client_order_id or str(uuid.uuid4())
        
        # Create order record
        order_record = OrderRecord(
            order_id='',
            client_order_id=client_order_id,
            broker_id='',
            symbol=symbol,
            side=side,
            order_type=order_type,
            quantity=quantity,
            price=price,
            stop_price=stop_price,
            status=OrderStatus.PENDING,
            filled_quantity=0.0,
            average_fill_price=0.0,
            commission=0.0,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            metadata=kwargs
        )
        
        # Try to place order with retries
        last_error = None
        attempted_brokers = []
        
        for attempt in range(self.max_retries):
            # Select broker
            broker_id = self._select_broker(symbol)
            
            if not broker_id:
                last_error = "No healthy brokers available"
                break
            
            if broker_id in attempted_brokers and len(self.brokers) > len(attempted_brokers):
                # Try a different broker
                for bid in self.brokers.keys():
                    if bid not in attempted_brokers:
                        broker_id = bid
                        break
            
            attempted_brokers.append(broker_id)
            broker = self.brokers[broker_id]
            
            try:
                start_time = datetime.now()
                
                # Place order
                response = await broker.place_order(
                    symbol=symbol,
                    side=side,
                    order_type=order_type,
                    quantity=quantity,
                    price=price,
                    stop_price=stop_price,
                    client_order_id=client_order_id,
                    **kwargs
                )
                
                latency = (datetime.now() - start_time).total_seconds() * 1000
                
                if response and response.success:
                    # Update order record
                    order_record.order_id = response.order_id
                    order_record.broker_id = broker_id
                    order_record.status = response.status
                    order_record.filled_quantity = response.filled_quantity
                    order_record.average_fill_price = response.average_fill_price
                    order_record.commission = response.commission
                    order_record.updated_at = datetime.now()
                    
                    if response.status == OrderStatus.FILLED:
                        order_record.filled_at = datetime.now()
                    
                    # Store order
                    self.orders[order_record.order_id] = order_record
                    if response.status == OrderStatus.PENDING:
                        self.pending_orders[order_record.order_id] = order_record
                    
                    # Update broker stats
                    self._update_broker_stats(broker_id, True, latency)
                    
                    # Track execution quality
                    if price and response.average_fill_price:
                        slippage = abs(response.average_fill_price - price) / price * 10000
                        self.execution_quality.append(ExecutionQuality(
                            order_id=response.order_id,
                            expected_price=price,
                            executed_price=response.average_fill_price,
                            slippage_bps=slippage,
                            latency_ms=latency,
                            fill_rate=response.filled_quantity / quantity,
                            timestamp=datetime.now()
                        ))
                    
                    # Audit log
                    self._log_audit('order_placed', order_record.to_dict())
                    
                    # Callback
                    if self.on_order_update:
                        await self._safe_callback(self.on_order_update, order_record)
                    
                    if response.status == OrderStatus.FILLED and self.on_fill:
                        await self._safe_callback(self.on_fill, order_record)
                    
                    logger.info(f"Order placed: {order_record.order_id} via {broker_id}")
                    return order_record
                
                else:
                    last_error = f"Order rejected by {broker_id}"
                    self._update_broker_stats(broker_id, False, latency)
                
            except Exception as e:
                last_error = str(e)
                logger.error(f"Order placement failed on {broker_id}: {e}")
                self._update_broker_stats(broker_id, False, 0)
            
            # Wait before retry
            if attempt < self.max_retries - 1:
                await asyncio.sleep(self.retry_delay)
        
        # All attempts failed
        order_record.status = OrderStatus.REJECTED
        order_record.error_message = last_error
        order_record.updated_at = datetime.now()
        
        self._log_audit('order_failed', {
            'client_order_id': client_order_id,
            'error': last_error,
            'attempted_brokers': attempted_brokers
        })
        
        if self.on_error:
            await self._safe_callback(self.on_error, order_record, last_error)
        
        logger.error(f"Order failed after {self.max_retries} attempts: {last_error}")
        return None
    
    async def cancel_order(self, order_id: str) -> bool:
        """Cancel an order"""
        if order_id not in self.orders:
            logger.warning(f"Order not found: {order_id}")
            return False
        
        order_record = self.orders[order_id]
        broker = self.brokers.get(order_record.broker_id)
        
        if not broker:
            logger.error(f"Broker not found: {order_record.broker_id}")
            return False
        try:
        
            success = await broker.cancel_order(order_id)
            
            if success:
                order_record.status = OrderStatus.CANCELLED
                order_record.cancelled_at = datetime.now()
                order_record.updated_at = datetime.now()
                
                self.pending_orders.pop(order_id, None)
                
                self._log_audit('order_cancelled', {'order_id': order_id})
                
                if self.on_order_update:
                    await self._safe_callback(self.on_order_update, order_record)
                
                logger.info(f"Order cancelled: {order_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to cancel order {order_id}: {e}")
            return False
    
    async def get_order_status(self, order_id: str) -> Optional[OrderRecord]:
        """Get order status"""
        if order_id not in self.orders:
            return None
        
        order_record = self.orders[order_id]
        broker = self.brokers.get(order_record.broker_id)
        
        if not broker:
            return order_record
        try:
        
            response = await broker.get_order_status(order_id)
            
            if response:
                order_record.status = response.status
                order_record.filled_quantity = response.filled_quantity
                order_record.average_fill_price = response.average_fill_price
                order_record.commission = response.commission
                order_record.updated_at = datetime.now()
                
                if response.status == OrderStatus.FILLED:
                    order_record.filled_at = datetime.now()
                    self.pending_orders.pop(order_id, None)
            
            return order_record
            
        except Exception as e:
            logger.error(f"Failed to get order status {order_id}: {e}")
            return order_record
    
    async def get_positions(self, broker_id: Optional[str] = None) -> List[Position]:
        """Get positions from broker(s)"""
        positions = []
        
        brokers_to_check = [broker_id] if broker_id else list(self.brokers.keys())
        
        for bid in brokers_to_check:
            broker = self.brokers.get(bid)
            if broker:
                try:
                    broker_positions = await broker.get_positions()
                    positions.extend(broker_positions)
                except Exception as e:
                    logger.error(f"Failed to get positions from {bid}: {e}")
        
        return positions
    
    async def close_all_positions(self, broker_id: Optional[str] = None) -> bool:
        """Close all positions"""
        success = True
        
        brokers_to_close = [broker_id] if broker_id else list(self.brokers.keys())
        
        for bid in brokers_to_close:
            broker = self.brokers.get(bid)
            if broker:
                try:
                    if hasattr(broker, 'close_all_positions'):
                        result = await broker.close_all_positions()
                        if not result:
                            success = False
                except Exception as e:
                    logger.error(f"Failed to close positions on {bid}: {e}")
                    success = False
        
        self._log_audit('close_all_positions', {'success': success})
        return success
    
    def _update_broker_stats(self, broker_id: str, success: bool, latency_ms: float):
        """Update broker statistics"""
        status = self.broker_status.get(broker_id)
        if not status:
            return
        
        status.total_orders += 1
        status.last_check = datetime.now()
        
        if success:
            status.consecutive_failures = 0
            # Exponential moving average for latency
            status.latency_ms = 0.9 * status.latency_ms + 0.1 * latency_ms
        else:
            status.failed_orders += 1
            status.consecutive_failures += 1
        
        # Calculate success rate
        status.success_rate = 1 - (status.failed_orders / status.total_orders)
        
        # Update health
        if status.consecutive_failures >= 5:
            status.health = BrokerHealth.UNHEALTHY
        elif status.consecutive_failures >= 2 or status.success_rate < 0.9:
            status.health = BrokerHealth.DEGRADED
        else:
            status.health = BrokerHealth.HEALTHY
    
    async def _health_check_loop(self):
        """Periodic health check"""
        while True:
            try:
                await asyncio.sleep(self.health_check_interval)
                
                for broker_id, broker in self.brokers.items():
                    try:
                        start = datetime.now()
                        
                        # Simple health check - get account info
                        if hasattr(broker, 'get_account_info'):
                            info = await broker.get_account_info()
                            
                            latency = (datetime.now() - start).total_seconds() * 1000
                            status = self.broker_status[broker_id]
                            status.latency_ms = latency
                            status.last_check = datetime.now()
                            
                            if info:
                                if status.health == BrokerHealth.OFFLINE:
                                    status.health = BrokerHealth.HEALTHY
                                    status.consecutive_failures = 0
                            else:
                                status.consecutive_failures += 1
                                if status.consecutive_failures >= 3:
                                    status.health = BrokerHealth.UNHEALTHY
                        
                    except Exception as e:
                        logger.error(f"Health check failed for {broker_id}: {e}")
                        self.broker_status[broker_id].health = BrokerHealth.UNHEALTHY
                        self.broker_status[broker_id].consecutive_failures += 1
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health check loop error: {e}")
    
    async def _reconciliation_loop(self):
        """Periodic order reconciliation"""
        while True:
            try:
                await asyncio.sleep(self.reconciliation_interval)
                
                # Check pending orders
                for order_id in list(self.pending_orders.keys()):
                    try:
                        order_record = await self.get_order_status(order_id)
                        
                        if order_record and order_record.status in [
                            OrderStatus.FILLED,
                            OrderStatus.CANCELLED,
                            OrderStatus.REJECTED
                        ]:
                            self.pending_orders.pop(order_id, None)
                            
                            if order_record.status == OrderStatus.FILLED and self.on_fill:
                                await self._safe_callback(self.on_fill, order_record)
                        
                    except Exception as e:
                        logger.error(f"Reconciliation failed for {order_id}: {e}")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Reconciliation loop error: {e}")
    
    async def _safe_callback(self, callback: Callable, *args):
        """Safely execute callback"""
        try:
            if asyncio.iscoroutinefunction(callback):
                await callback(*args)
            else:
                callback(*args)
        except Exception as e:
            logger.error(f"Callback error: {e}")
    
    def _log_audit(self, action: str, data: Dict):
        """Log audit entry"""
        entry = {
            'timestamp': datetime.now().isoformat(),
            'action': action,
            'data': data
        }
        
        self.audit_log.append(entry)
        
        # Trim if needed
        if len(self.audit_log) > self.max_audit_entries:
            self.audit_log = self.audit_log[-self.max_audit_entries:]
    
    def get_broker_status(self) -> Dict[str, Dict]:
        """Get status of all brokers"""
        return {
            broker_id: status.to_dict()
            for broker_id, status in self.broker_status.items()
        }
    
    def get_execution_stats(self) -> Dict[str, Any]:
        """Get execution quality statistics"""
        if not self.execution_quality:
            return {}
        
        slippages = [eq.slippage_bps for eq in self.execution_quality]
        latencies = [eq.latency_ms for eq in self.execution_quality]
        fill_rates = [eq.fill_rate for eq in self.execution_quality]
        
        return {
            'total_orders': len(self.execution_quality),
            'avg_slippage_bps': sum(slippages) / len(slippages),
            'max_slippage_bps': max(slippages),
            'avg_latency_ms': sum(latencies) / len(latencies),
            'max_latency_ms': max(latencies),
            'avg_fill_rate': sum(fill_rates) / len(fill_rates)
        }
    
    def get_audit_log(self, limit: int = 100) -> List[Dict]:
        """Get recent audit log entries"""
        return self.audit_log[-limit:]
    
    def export_orders(self) -> List[Dict]:
        """Export all orders"""
        return [order.to_dict() for order in self.orders.values()]


# Export
__all__ = [
    'LiveOrderRouter',
    'RoutingStrategy',
    'BrokerHealth',
    'BrokerStatus',
    'OrderRecord',
    'ExecutionQuality'
]
