"""
Broker Connection Manager

Manages broker connections with:
- Automatic reconnection on disconnect
- Heartbeat/keepalive monitoring
- Connection health tracking
- Graceful degradation
- Multi-broker support
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum
import threading

logger = logging.getLogger(__name__)


class ConnectionState(Enum):
    """Broker connection state"""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"
    ERROR = "error"
    DEGRADED = "degraded"  # Connected but with issues


@dataclass
class ConnectionHealth:
    """Connection health metrics"""
    state: ConnectionState
    last_heartbeat: Optional[datetime] = None
    last_successful_request: Optional[datetime] = None
    consecutive_failures: int = 0
    total_reconnects: int = 0
    uptime_seconds: float = 0.0
    latency_ms: float = 0.0
    error_message: Optional[str] = None
    
    @property
    def is_healthy(self) -> bool:
        """Check if connection is healthy"""
        if self.state != ConnectionState.CONNECTED:
            return False
        if self.last_heartbeat:
            age = (datetime.now() - self.last_heartbeat).total_seconds()
            if age > 30:  # No heartbeat in 30 seconds
                return False
        return self.consecutive_failures < 3


@dataclass
class ReconnectionConfig:
    """Reconnection configuration"""
    max_retries: int = 10
    initial_delay: float = 1.0  # seconds
    max_delay: float = 60.0  # seconds
    backoff_multiplier: float = 2.0
    jitter: float = 0.1  # Random jitter factor


class BrokerConnectionManager:
    """
    Manages broker connections with automatic reconnection and health monitoring.
    """
    
    def __init__(
        self,
        broker_adapter,
        config: Optional[Dict[str, Any]] = None,
        on_connect: Optional[Callable] = None,
        on_disconnect: Optional[Callable] = None,
        on_error: Optional[Callable] = None
    ):
        """
        Initialize connection manager.
        
        Args:
            broker_adapter: The broker adapter to manage
            config: Configuration dictionary
            on_connect: Callback when connected
            on_disconnect: Callback when disconnected
            on_error: Callback on error
        """
        self.broker = broker_adapter
        self.config = config or {}
        
        # Callbacks
        self.on_connect = on_connect
        self.on_disconnect = on_disconnect
        self.on_error = on_error
        
        # Reconnection config
        self.reconnect_config = ReconnectionConfig(
            max_retries=self.config.get('max_retries', 10),
            initial_delay=self.config.get('initial_delay', 1.0),
            max_delay=self.config.get('max_delay', 60.0),
            backoff_multiplier=self.config.get('backoff_multiplier', 2.0),
            jitter=self.config.get('jitter', 0.1)
        )
        
        # Health tracking
        self.health = ConnectionHealth(state=ConnectionState.DISCONNECTED)
        self._connect_time: Optional[datetime] = None
        
        # Heartbeat config
        self.heartbeat_interval = self.config.get('heartbeat_interval', 10)  # seconds
        self.heartbeat_timeout = self.config.get('heartbeat_timeout', 5)  # seconds
        
        # Background tasks
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._reconnect_task: Optional[asyncio.Task] = None
        self._running = False
        
        # Lock for thread safety
        self._lock = asyncio.Lock()
        
        # Request tracking for latency
        self._request_times: List[float] = []
        self._max_request_history = 100
        
        logger.info("Broker connection manager initialized")
    
    async def connect(self) -> bool:
        """
        Connect to broker with retry logic.
        
        Returns:
            True if connected successfully
        """
        async with self._lock:
            if self.health.state == ConnectionState.CONNECTED:
                logger.info("Already connected")
                return True
            
            self.health.state = ConnectionState.CONNECTING
            
            try:
                # Attempt connection
                success = await self.broker.connect()
                
                if success:
                    self.health.state = ConnectionState.CONNECTED
                    self.health.consecutive_failures = 0
                    self.health.last_heartbeat = datetime.now()
                    self.health.last_successful_request = datetime.now()
                    self.health.error_message = None
                    self._connect_time = datetime.now()
                    
                    # Start heartbeat monitoring
                    self._running = True
                    self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
                    
                    logger.info("Connected to broker successfully")
                    
                    # Callback
                    if self.on_connect:
                        try:
                            await self._call_callback(self.on_connect)
                        except Exception as e:
                            logger.error(f"on_connect callback error: {e}")
                    
                    return True
                else:
                    self.health.state = ConnectionState.ERROR
                    self.health.error_message = "Connection failed"
                    logger.error("Failed to connect to broker")
                    return False
                    
            except Exception as e:
                self.health.state = ConnectionState.ERROR
                self.health.error_message = str(e)
                self.health.consecutive_failures += 1
                logger.error(f"Connection error: {e}")
                
                if self.on_error:
                    try:
                        await self._call_callback(self.on_error, e)
                    except Exception as cb_error:
                        logger.error(f"on_error callback error: {cb_error}")
                
                return False
    
    async def disconnect(self) -> bool:
        """
        Disconnect from broker gracefully.
        
        Returns:
            True if disconnected successfully
        """
        async with self._lock:
            self._running = False
            
            # Cancel background tasks
            if self._heartbeat_task:
                self._heartbeat_task.cancel()
                try:
                    await self._heartbeat_task
                except asyncio.CancelledError:
                    pass
            
            if self._reconnect_task:
                try:
                    self._reconnect_task.cancel()
                    try:
                        await self._reconnect_task
                    except asyncio.CancelledError:
                        pass

                    success = await self.broker.disconnect()

                    self.health.state = ConnectionState.DISCONNECTED

                    # Calculate uptime
                    if self._connect_time:
                        self.health.uptime_seconds = (datetime.now() - self._connect_time).total_seconds()

                    logger.info(f"Disconnected from broker (uptime: {self.health.uptime_seconds:.1f}s)")

                    # Callback
                    if self.on_disconnect:
                        try:
                            await self._call_callback(self.on_disconnect)
                        except Exception as e:
                            logger.error(f"on_disconnect callback error: {e}")

                    return success

                except Exception as e:
                    logger.error(f"Disconnect error: {e}")
                    self.health.state = ConnectionState.ERROR
                    self.health.error_message = str(e)
                    return False

    async def reconnect(self) -> bool:
        """
        Reconnect to broker with exponential backoff.
        
        Returns:
            True if reconnected successfully
        """
        if self.health.state == ConnectionState.RECONNECTING:
            logger.warning("Already reconnecting")
            return False
        
        self.health.state = ConnectionState.RECONNECTING
        self.health.total_reconnects += 1
        
        delay = self.reconnect_config.initial_delay
        
        for attempt in range(self.reconnect_config.max_retries):
            logger.info(f"Reconnection attempt {attempt + 1}/{self.reconnect_config.max_retries}")
            
            try:
                # Disconnect first if needed
                if self.broker.connected:
                    await self.broker.disconnect()
                
                # Wait with jitter
                import random
                jitter = delay * self.reconnect_config.jitter * random.random()
                await asyncio.sleep(delay + jitter)
                
                # Attempt connection
                success = await self.broker.connect()
                
                if success:
                    self.health.state = ConnectionState.CONNECTED
                    self.health.consecutive_failures = 0
                    self.health.last_heartbeat = datetime.now()
                    self.health.error_message = None
                    self._connect_time = datetime.now()
                    
                    logger.info(f"Reconnected successfully after {attempt + 1} attempts")
                    
                    # Restart heartbeat
                    if not self._heartbeat_task or self._heartbeat_task.done():
                        self._running = True
                        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
                    
                    # Callback
                    if self.on_connect:
                        try:
                            await self._call_callback(self.on_connect)
                        except Exception as e:
                            logger.error(f"on_connect callback error: {e}")
                    
                    return True
                    
            except Exception as e:
                logger.warning(f"Reconnection attempt {attempt + 1} failed: {e}")
                self.health.error_message = str(e)
            
            # Increase delay with backoff
            delay = min(delay * self.reconnect_config.backoff_multiplier, self.reconnect_config.max_delay)
        
        # All retries exhausted
        self.health.state = ConnectionState.ERROR
        self.health.error_message = f"Failed to reconnect after {self.reconnect_config.max_retries} attempts"
        logger.error(self.health.error_message)
        
        if self.on_error:
            try:
                await self._call_callback(self.on_error, Exception(self.health.error_message))
            except Exception as e:
                logger.error(f"on_error callback error: {e}")
        
        return False
    
    async def _heartbeat_loop(self):
        """Background heartbeat monitoring loop"""
        logger.info("Heartbeat monitoring started")
        
        while self._running:
            try:
                await asyncio.sleep(self.heartbeat_interval)
                
                if not self._running:
                    break
                
                # Send heartbeat (get account info as ping)
                start_time = time.time()
                
                try:
                    # Use a simple request as heartbeat
                    result = await asyncio.wait_for(
                        self.broker.get_account_info(),
                        timeout=self.heartbeat_timeout
                    )
                    
                    latency = (time.time() - start_time) * 1000
                    
                    if result:
                        self.health.last_heartbeat = datetime.now()
                        self.health.last_successful_request = datetime.now()
                        self.health.consecutive_failures = 0
                        self.health.latency_ms = latency
                        
                        # Track latency history
                        self._request_times.append(latency)
                        if len(self._request_times) > self._max_request_history:
                            self._request_times = self._request_times[-self._max_request_history:]
                        
                        # Check for degraded state (high latency)
                        if latency > 1000:  # > 1 second
                            if self.health.state == ConnectionState.CONNECTED:
                                self.health.state = ConnectionState.DEGRADED
                                logger.warning(f"Connection degraded - high latency: {latency:.0f}ms")
                        elif self.health.state == ConnectionState.DEGRADED:
                            self.health.state = ConnectionState.CONNECTED
                            logger.info("Connection recovered from degraded state")
                    else:
                        self._handle_heartbeat_failure("Empty response")
                        
                except asyncio.TimeoutError:
                    self._handle_heartbeat_failure("Timeout")
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Heartbeat error: {e}")
                self._handle_heartbeat_failure(str(e))
        
        logger.info("Heartbeat monitoring stopped")
    
    def _handle_heartbeat_failure(self, reason: str):
        """Handle heartbeat failure"""
        self.health.consecutive_failures += 1
        self.health.error_message = f"Heartbeat failed: {reason}"
        
        logger.warning(f"Heartbeat failure ({self.health.consecutive_failures}): {reason}")
        
        # Trigger reconnection after multiple failures
        if self.health.consecutive_failures >= 3:
            logger.error("Multiple heartbeat failures - initiating reconnection")
            self.health.state = ConnectionState.ERROR
            
            # Start reconnection in background
            if not self._reconnect_task or self._reconnect_task.done():
                self._reconnect_task = asyncio.create_task(self.reconnect())
    
    async def _call_callback(self, callback: Callable, *args):
        """Call a callback, handling both sync and async"""
        if asyncio.iscoroutinefunction(callback):
            await callback(*args)
        else:
            callback(*args)
    
    def get_health(self) -> ConnectionHealth:
        """Get current connection health"""
        # Update uptime
        if self._connect_time and self.health.state == ConnectionState.CONNECTED:
            self.health.uptime_seconds = (datetime.now() - self._connect_time).total_seconds()
        
        return self.health
    
    def get_latency_stats(self) -> Dict[str, float]:
        """Get latency statistics"""
        if not self._request_times:
            return {
                'current_ms': 0.0,
                'avg_ms': 0.0,
                'min_ms': 0.0,
                'max_ms': 0.0,
                'p95_ms': 0.0
            }
        
        sorted_times = sorted(self._request_times)
        p95_index = int(len(sorted_times) * 0.95)
        
        return {
            'current_ms': self._request_times[-1] if self._request_times else 0.0,
            'avg_ms': sum(self._request_times) / len(self._request_times),
            'min_ms': min(self._request_times),
            'max_ms': max(self._request_times),
            'p95_ms': sorted_times[p95_index] if p95_index < len(sorted_times) else sorted_times[-1]
        }
    
    async def execute_with_retry(
        self,
        operation: Callable,
        *args,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        **kwargs
    ) -> Any:
        """
        Execute an operation with automatic retry on failure.
        
        Args:
            operation: Async operation to execute
            *args: Positional arguments
            max_retries: Maximum retry attempts
            retry_delay: Delay between retries
            **kwargs: Keyword arguments
            
        Returns:
            Operation result
        """
        last_error = None
        
        for attempt in range(max_retries):
            try:
                # Check connection
                if self.health.state != ConnectionState.CONNECTED:
                    if self.health.state == ConnectionState.DEGRADED:
                        logger.warning("Executing on degraded connection")
                    else:
                        logger.warning("Not connected, attempting reconnection")
                        await self.reconnect()
                
                # Execute operation
                start_time = time.time()
                result = await operation(*args, **kwargs)
                latency = (time.time() - start_time) * 1000
                
                # Update health
                self.health.last_successful_request = datetime.now()
                self.health.consecutive_failures = 0
                self._request_times.append(latency)
                
                return result
                
            except Exception as e:
                last_error = e
                self.health.consecutive_failures += 1
                logger.warning(f"Operation failed (attempt {attempt + 1}/{max_retries}): {e}")
                
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay * (attempt + 1))
        
        # All retries failed
        if self.on_error:
            try:
                await self._call_callback(self.on_error, last_error)
            except Exception as e:
                logger.error(f"on_error callback error: {e}")
        
        raise last_error
    
    @property
    def is_connected(self) -> bool:
        """Check if connected"""
        return self.health.state in [ConnectionState.CONNECTED, ConnectionState.DEGRADED]
    
    @property
    def is_healthy(self) -> bool:
        """Check if connection is healthy"""
        return self.health.is_healthy


class MultiBrokerConnectionManager:
    """
    Manages connections to multiple brokers with failover support.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize multi-broker manager"""
        self.config = config or {}
        self.connections: Dict[str, BrokerConnectionManager] = {}
        self.primary_broker: Optional[str] = None
        self._failover_order: List[str] = []
    
    def add_broker(
        self,
        broker_id: str,
        broker_adapter,
        config: Optional[Dict[str, Any]] = None,
        is_primary: bool = False
    ) -> BrokerConnectionManager:
        """
        Add a broker to the manager.
        
        Args:
            broker_id: Unique broker identifier
            broker_adapter: Broker adapter instance
            config: Connection configuration
            is_primary: Whether this is the primary broker
            
        Returns:
            BrokerConnectionManager instance
        """
        manager = BrokerConnectionManager(broker_adapter, config)
        self.connections[broker_id] = manager
        
        if is_primary or not self.primary_broker:
            self.primary_broker = broker_id
        
        self._failover_order.append(broker_id)
        
        logger.info(f"Added broker: {broker_id} (primary: {is_primary})")
        return manager
    
    async def connect_all(self) -> Dict[str, bool]:
        """Connect to all brokers"""
        results = {}
        
        for broker_id, manager in self.connections.items():
            try:
                results[broker_id] = await manager.connect()
            except Exception as e:
                logger.error(f"Failed to connect to {broker_id}: {e}")
                results[broker_id] = False
        
        return results
    
    async def disconnect_all(self) -> Dict[str, bool]:
        """Disconnect from all brokers"""
        results = {}
        
        for broker_id, manager in self.connections.items():
            try:
                results[broker_id] = await manager.disconnect()
            except Exception as e:
                logger.error(f"Failed to disconnect from {broker_id}: {e}")
                results[broker_id] = False
        
        return results
    
    def get_primary(self) -> Optional[BrokerConnectionManager]:
        """Get primary broker connection"""
        if self.primary_broker and self.primary_broker in self.connections:
            return self.connections[self.primary_broker]
        return None
    
    def get_healthy_broker(self) -> Optional[BrokerConnectionManager]:
        """Get first healthy broker (with failover)"""
        # Try primary first
        if self.primary_broker:
            primary = self.connections.get(self.primary_broker)
            if primary and primary.is_healthy:
                return primary
        
        # Failover to others
        for broker_id in self._failover_order:
            manager = self.connections.get(broker_id)
            if manager and manager.is_healthy:
                logger.warning(f"Failing over to broker: {broker_id}")
                return manager
        
        return None
    
    def get_all_health(self) -> Dict[str, ConnectionHealth]:
        """Get health status of all brokers"""
        return {
            broker_id: manager.get_health()
            for broker_id, manager in self.connections.items()
        }
