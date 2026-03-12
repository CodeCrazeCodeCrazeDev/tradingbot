"""
Multi-Broker Adapter
Unified interface with automatic failover across multiple brokers
"""

import asyncio
import logging
from typing import Any, Awaitable, Callable, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from abc import ABC, abstractmethod
import random

logger = logging.getLogger(__name__)


class BrokerStatus(Enum):
    """Broker connection status"""
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    DEGRADED = "degraded"
    MAINTENANCE = "maintenance"
    ERROR = "error"


class OrderStatus(Enum):
    """Order status"""
    PENDING = "pending"
    SUBMITTED = "submitted"
    PARTIAL = "partial"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    EXPIRED = "expired"


@dataclass
class BrokerHealth:
    """Broker health metrics"""
    broker_id: str
    status: BrokerStatus
    latency_ms: float
    success_rate: float
    last_heartbeat: datetime
    error_count: int
    order_count: int
    uptime_pct: float
    
    @property
    def health_score(self) -> float:
        """Calculate overall health score (0-100)"""
        score = 0
        
        # Status component (0-30)
        status_scores = {
            BrokerStatus.CONNECTED: 30,
            BrokerStatus.DEGRADED: 15,
            BrokerStatus.DISCONNECTED: 0,
            BrokerStatus.MAINTENANCE: 5,
            BrokerStatus.ERROR: 0
        }
        score += status_scores.get(self.status, 0)
        
        # Latency component (0-25)
        if self.latency_ms < 50:
            score += 25
        elif self.latency_ms < 100:
            score += 20
        elif self.latency_ms < 200:
            score += 15
        elif self.latency_ms < 500:
            score += 10
        else:
            score += 5
            
        # Success rate component (0-25)
        score += self.success_rate * 25
        
        # Uptime component (0-20)
        score += self.uptime_pct * 20
        
        return min(100, score)


@dataclass
class Order:
    """Order representation"""
    order_id: str
    client_order_id: str
    symbol: str
    side: str
    order_type: str
    quantity: float
    price: Optional[float]
    status: OrderStatus
    filled_quantity: float = 0
    avg_fill_price: float = 0
    broker_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'order_id': self.order_id,
            'client_order_id': self.client_order_id,
            'symbol': self.symbol,
            'side': self.side,
            'order_type': self.order_type,
            'quantity': self.quantity,
            'price': self.price,
            'status': self.status.value,
            'filled_quantity': self.filled_quantity,
            'avg_fill_price': self.avg_fill_price,
            'broker_id': self.broker_id
        }


class BrokerAdapter(ABC):
    """Abstract broker adapter interface"""
    
    @property
    @abstractmethod
    def broker_id(self) -> str:
        """Auto-implemented method."""
        logger.debug(f"{self.__class__.__name__}.broker_id called")
        return None
    
    @abstractmethod
    async def connect(self) -> bool:
        """Auto-implemented method."""
        logger.debug(f"{self.__class__.__name__}.connect called")
        return None
    
    @abstractmethod
    async def disconnect(self):
        """Auto-implemented method."""
        logger.debug(f"{self.__class__.__name__}.disconnect called")
        return None
    
    @abstractmethod
    async def get_status(self) -> BrokerStatus:
        """Auto-implemented getter."""
        return None
    
    @abstractmethod
    async def submit_order(self, order: Order) -> Order:
        """Auto-implemented method."""
        logger.debug(f"{self.__class__.__name__}.submit_order called")
        return None
    
    @abstractmethod
    async def cancel_order(self, order_id: str) -> bool:
        """Auto-implemented method."""
        logger.debug(f"{self.__class__.__name__}.cancel_order called")
        return None
    
    @abstractmethod
    async def get_order(self, order_id: str) -> Optional[Order]:
        """Auto-implemented getter."""
        return None
    
    @abstractmethod
    async def get_positions(self) -> List[Dict[str, Any]]:
        """Auto-implemented getter."""
        return None
    
    @abstractmethod
    async def get_balance(self) -> Dict[str, float]:
        """Auto-implemented getter."""
        return None


class MockBrokerAdapter(BrokerAdapter):
    """Mock broker for testing"""
    
    def __init__(self, broker_id: str, config: Optional[Dict] = None):
        self._broker_id = broker_id
        self.config = config or {}
        self._connected = False
        self._orders: Dict[str, Order] = {}
        self._positions: Dict[str, Dict] = {}
        self._balance = {'USD': 100000, 'BTC': 0, 'ETH': 0}
        
        # Simulate latency and failures
        self._latency_ms = self.config.get('latency_ms', 50)
        self._failure_rate = self.config.get('failure_rate', 0.01)
        
    @property
    def broker_id(self) -> str:
        return self._broker_id
    
    async def connect(self) -> bool:
        await asyncio.sleep(self._latency_ms / 1000)
        self._connected = True
        return True
    
    async def disconnect(self):
        self._connected = False
    
    async def get_status(self) -> BrokerStatus:
        if not self._connected:
            return BrokerStatus.DISCONNECTED
        return BrokerStatus.CONNECTED
    
    async def submit_order(self, order: Order) -> Order:
        await asyncio.sleep(self._latency_ms / 1000)
        
        # Simulate random failures
        if random.random() < self._failure_rate:
            order.status = OrderStatus.REJECTED
            return order
            
        order.status = OrderStatus.FILLED
        order.filled_quantity = order.quantity
        order.avg_fill_price = order.price or 100.0
        order.broker_id = self._broker_id
        
        self._orders[order.order_id] = order
        return order
    
    async def cancel_order(self, order_id: str) -> bool:
        await asyncio.sleep(self._latency_ms / 1000)
        
        if order_id in self._orders:
            self._orders[order_id].status = OrderStatus.CANCELLED
            return True
        return False
    
    async def get_order(self, order_id: str) -> Optional[Order]:
        return self._orders.get(order_id)
    
    async def get_positions(self) -> List[Dict[str, Any]]:
        return list(self._positions.values())
    
    async def get_balance(self) -> Dict[str, float]:
        return self._balance.copy()


class MultiBrokerAdapter:
    """
    Multi-broker adapter with automatic failover
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Registered brokers
        self.brokers: Dict[str, BrokerAdapter] = {}
        self.broker_health: Dict[str, BrokerHealth] = {}
        
        # Primary and fallback configuration
        self.primary_broker: Optional[str] = None
        self.fallback_order: List[str] = []
        
        # Routing configuration
        self.routing_strategy = self.config.get('routing_strategy', 'primary_with_failover')
        self.max_retries = self.config.get('max_retries', 3)
        self.retry_delay_ms = self.config.get('retry_delay_ms', 100)
        
        # Health monitoring
        self.health_check_interval = self.config.get('health_check_interval', 30)
        self._health_check_task: Optional[asyncio.Task] = None
        
        # Statistics
        self.stats = {
            'total_orders': 0,
            'successful_orders': 0,
            'failed_orders': 0,
            'failovers': 0,
            'by_broker': {}
        }
        
        # Callbacks
        self.on_failover: Optional[Callable[[str, str], Awaitable[None]]] = None
        
        logger.info("Multi-broker adapter initialized")
        
    def register_broker(
        self,
        adapter: BrokerAdapter,
        is_primary: bool = False,
        fallback_priority: int = 0
    ):
        """Register a broker adapter"""
        broker_id = adapter.broker_id
        self.brokers[broker_id] = adapter
        
        # Initialize health
        self.broker_health[broker_id] = BrokerHealth(
            broker_id=broker_id,
            status=BrokerStatus.DISCONNECTED,
            latency_ms=0,
            success_rate=1.0,
            last_heartbeat=datetime.now(),
            error_count=0,
            order_count=0,
            uptime_pct=1.0
        )
        
        # Initialize stats
        self.stats['by_broker'][broker_id] = {
            'orders': 0,
            'successes': 0,
            'failures': 0
        }
        
        if is_primary:
            self.primary_broker = broker_id
            
        # Update fallback order
        if broker_id not in self.fallback_order:
            self.fallback_order.append(broker_id)
            self.fallback_order.sort(key=lambda x: fallback_priority if x == broker_id else 999)
            
        logger.info(f"Registered broker: {broker_id} (primary: {is_primary})")
        
    async def connect_all(self) -> Dict[str, bool]:
        """Connect to all registered brokers"""
        results = {}
        
        for broker_id, adapter in self.brokers.items():
            try:
                start_time = datetime.now()
                success = await adapter.connect()
                latency = (datetime.now() - start_time).total_seconds() * 1000
                
                results[broker_id] = success
                
                if success:
                    self.broker_health[broker_id].status = BrokerStatus.CONNECTED
                    self.broker_health[broker_id].latency_ms = latency
                    self.broker_health[broker_id].last_heartbeat = datetime.now()
                else:
                    self.broker_health[broker_id].status = BrokerStatus.ERROR
                    
            except Exception as e:
                logger.error(f"Failed to connect to {broker_id}: {e}")
                results[broker_id] = False
                self.broker_health[broker_id].status = BrokerStatus.ERROR
                
        # Start health monitoring
        if not self._health_check_task:
            self._health_check_task = asyncio.create_task(self._health_check_loop())
            
        return results
    
    async def disconnect_all(self):
        """Disconnect from all brokers"""
        if self._health_check_task:
            self._health_check_task.cancel()
            
        for adapter in self.brokers.values():
            try:
                await adapter.disconnect()
            except Exception as e:
                logger.warning(f"Error disconnecting: {e}")
                
    async def _health_check_loop(self):
        """Periodic health check"""
        while True:
            try:
                await asyncio.sleep(self.health_check_interval)
                await self._check_all_health()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health check error: {e}")
                
    async def _check_all_health(self):
        """Check health of all brokers"""
        for broker_id, adapter in self.brokers.items():
            try:
                start_time = datetime.now()
                status = await adapter.get_status()
                latency = (datetime.now() - start_time).total_seconds() * 1000
                
                health = self.broker_health[broker_id]
                health.status = status
                health.latency_ms = latency
                health.last_heartbeat = datetime.now()
                
            except Exception as e:
                logger.warning(f"Health check failed for {broker_id}: {e}")
                self.broker_health[broker_id].status = BrokerStatus.ERROR
                self.broker_health[broker_id].error_count += 1
                
    def _select_broker(self, exclude: Optional[List[str]] = None) -> Optional[str]:
        """Select best available broker"""
        exclude = exclude or []
        
        if self.routing_strategy == 'primary_with_failover':
            # Try primary first
            if self.primary_broker and self.primary_broker not in exclude:
                health = self.broker_health.get(self.primary_broker)
                if health and health.status == BrokerStatus.CONNECTED:
                    return self.primary_broker
                    
            # Fallback to others
            for broker_id in self.fallback_order:
                if broker_id in exclude:
                    continue
                health = self.broker_health.get(broker_id)
                if health and health.status == BrokerStatus.CONNECTED:
                    return broker_id
                    
        elif self.routing_strategy == 'best_health':
            # Select broker with best health score
            best_broker = None
            best_score = -1
            
            for broker_id, health in self.broker_health.items():
                if broker_id in exclude:
                    continue
                if health.status == BrokerStatus.CONNECTED:
                    score = health.health_score
                    if score > best_score:
                        best_score = score
                        best_broker = broker_id
                        
            return best_broker
            
        elif self.routing_strategy == 'round_robin':
            # Simple round robin
            available = [
                b for b in self.fallback_order
                if b not in exclude and 
                self.broker_health.get(b, BrokerHealth(b, BrokerStatus.DISCONNECTED, 0, 0, datetime.now(), 0, 0, 0)).status == BrokerStatus.CONNECTED
            ]
            if available:
                return available[self.stats['total_orders'] % len(available)]
                
        return None
    
    async def submit_order(self, order: Order) -> Order:
        """
        Submit order with automatic failover
        """
        self.stats['total_orders'] += 1
        tried_brokers: List[str] = []
        last_error = None
        
        for attempt in range(self.max_retries):
            broker_id = self._select_broker(exclude=tried_brokers)
            
            if not broker_id:
                logger.error("No available brokers")
                order.status = OrderStatus.REJECTED
                self.stats['failed_orders'] += 1
                return order
                
            tried_brokers.append(broker_id)
            adapter = self.brokers[broker_id]
            
            try:
                start_time = datetime.now()
                result = await adapter.submit_order(order)
                latency = (datetime.now() - start_time).total_seconds() * 1000
                
                # Update health
                health = self.broker_health[broker_id]
                health.latency_ms = (health.latency_ms + latency) / 2
                health.order_count += 1
                
                # Update stats
                self.stats['by_broker'][broker_id]['orders'] += 1
                
                if result.status in [OrderStatus.FILLED, OrderStatus.PARTIAL, OrderStatus.SUBMITTED]:
                    self.stats['successful_orders'] += 1
                    self.stats['by_broker'][broker_id]['successes'] += 1
                    
                    # Update success rate
                    stats = self.stats['by_broker'][broker_id]
                    health.success_rate = stats['successes'] / stats['orders']
                    
                    return result
                else:
                    # Order rejected, try failover
                    logger.warning(f"Order rejected by {broker_id}, attempting failover")
                    self.stats['failovers'] += 1
                    
                    if self.on_failover and len(tried_brokers) > 1:
                        await self.on_failover(tried_brokers[-2], broker_id)
                        
            except Exception as e:
                last_error = e
                logger.error(f"Order submission failed on {broker_id}: {e}")
                
                # Update health
                self.broker_health[broker_id].error_count += 1
                self.stats['by_broker'][broker_id]['failures'] += 1
                
                # Retry delay
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay_ms / 1000)
                    
        # All retries exhausted
        self.stats['failed_orders'] += 1
        order.status = OrderStatus.REJECTED
        logger.error(f"Order failed after {self.max_retries} attempts: {last_error}")
        
        return order
    
    async def cancel_order(self, order_id: str, broker_id: Optional[str] = None) -> bool:
        """Cancel order on specific or all brokers"""
        if broker_id:
            adapter = self.brokers.get(broker_id)
            if adapter:
                return await adapter.cancel_order(order_id)
            return False
            
        # Try all brokers
        for adapter in self.brokers.values():
            try:
                if await adapter.cancel_order(order_id):
                    return True
            except Exception:
                pass
                
        return False
    
    async def get_order(self, order_id: str) -> Optional[Order]:
        """Get order from any broker"""
        for adapter in self.brokers.values():
            try:
                order = await adapter.get_order(order_id)
                if order:
                    return order
            except Exception:
                pass
        return None
    
    async def get_all_positions(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get positions from all brokers"""
        positions = {}
        
        for broker_id, adapter in self.brokers.items():
            try:
                positions[broker_id] = await adapter.get_positions()
            except Exception as e:
                logger.warning(f"Failed to get positions from {broker_id}: {e}")
                positions[broker_id] = []
                
        return positions
    
    async def get_all_balances(self) -> Dict[str, Dict[str, float]]:
        """Get balances from all brokers"""
        balances = {}
        
        for broker_id, adapter in self.brokers.items():
            try:
                balances[broker_id] = await adapter.get_balance()
            except Exception as e:
                logger.warning(f"Failed to get balance from {broker_id}: {e}")
                balances[broker_id] = {}
                
        return balances
    
    def get_broker_health(self) -> Dict[str, Dict[str, Any]]:
        """Get health status of all brokers"""
        return {
            broker_id: {
                'status': health.status.value,
                'latency_ms': health.latency_ms,
                'success_rate': health.success_rate,
                'health_score': health.health_score,
                'error_count': health.error_count,
                'order_count': health.order_count,
                'last_heartbeat': health.last_heartbeat.isoformat()
            }
            for broker_id, health in self.broker_health.items()
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get adapter statistics"""
        return {
            **self.stats,
            'success_rate': self.stats['successful_orders'] / max(1, self.stats['total_orders']),
            'failover_rate': self.stats['failovers'] / max(1, self.stats['total_orders']),
            'broker_count': len(self.brokers),
            'connected_brokers': sum(
                1 for h in self.broker_health.values() 
                if h.status == BrokerStatus.CONNECTED
            )
        }
