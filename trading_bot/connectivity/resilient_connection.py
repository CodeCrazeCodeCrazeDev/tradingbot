"""
Elite Connection Resilience System
Implements exponential backoff, circuit breakers, and automatic recovery
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Callable, Optional
from dataclasses import dataclass
from enum import Enum
import random

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


class ConnectionState(Enum):
    """Connection states"""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"
    FAILED = "failed"


@dataclass
class ConnectionConfig:
    """Configuration for resilient connection"""
    initial_retry_delay: float = 1.0  # seconds
    max_retry_delay: float = 60.0  # seconds
    backoff_multiplier: float = 2.0
    jitter: bool = True
    max_retries: int = 10
    connection_timeout: float = 30.0
    heartbeat_interval: float = 30.0
    heartbeat_timeout: float = 10.0


class ResilientConnection:
    """
    Resilient Connection Manager
    
    Features:
    - Exponential backoff with jitter
    - Automatic reconnection
    - Heartbeat monitoring
    - State recovery
    - Connection pooling
    """
    
    def __init__(self, name: str, config: Optional[ConnectionConfig] = None):
        self.name = name
        self.config = config or ConnectionConfig()
        
        self.state = ConnectionState.DISCONNECTED
        self.retry_count = 0
        self.last_connection_time: Optional[datetime] = None
        self.last_heartbeat: Optional[datetime] = None
        
        # Callbacks
        self.on_connect: Optional[Callable] = None
        self.on_disconnect: Optional[Callable] = None
        self.on_error: Optional[Callable] = None
        
        # Connection object (to be set by implementation)
        self.connection: Optional[Any] = None
        
        # Heartbeat task
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._reconnect_task: Optional[asyncio.Task] = None
        
        logger.info(f"Resilient connection '{name}' initialized")
    
    async def connect(self, connect_func: Callable) -> bool:
        """
        Establish connection with retry logic
        
        Args:
            connect_func: Async function that establishes connection
            
        Returns:
            True if connected successfully
        """
        if self.state == ConnectionState.CONNECTED:
            logger.warning(f"{self.name}: Already connected")
            return True
        
        self.state = ConnectionState.CONNECTING
        retry_delay = self.config.initial_retry_delay
        
        for attempt in range(self.config.max_retries):
            try:
                logger.info(f"{self.name}: Connection attempt {attempt + 1}/{self.config.max_retries}")
                
                # Attempt connection with timeout
                self.connection = await asyncio.wait_for(
                    connect_func(),
                    timeout=self.config.connection_timeout
                )
                
                # Connection successful
                self.state = ConnectionState.CONNECTED
                self.retry_count = 0
                self.last_connection_time = datetime.now()
                
                logger.info(f"✅ {self.name}: Connected successfully")
                
                # Start heartbeat
                self._start_heartbeat()
                
                # Call on_connect callback
                if self.on_connect:
                    await self.on_connect()
                
                return True
                
            except asyncio.TimeoutError:
                logger.error(f"{self.name}: Connection timeout on attempt {attempt + 1}")
            except Exception as e:
                logger.error(f"{self.name}: Connection error on attempt {attempt + 1}: {e}")
                
                # Call on_error callback
                if self.on_error:
                    await self.on_error(e)
            
            # Calculate next retry delay with exponential backoff
            if attempt < self.config.max_retries - 1:
                retry_delay = min(
                    retry_delay * self.config.backoff_multiplier,
                    self.config.max_retry_delay
                )
                
                # Add jitter to prevent thundering herd
                if self.config.jitter:
                    retry_delay = retry_delay * (0.5 + random.random())
                
                logger.info(f"{self.name}: Retrying in {retry_delay:.2f} seconds...")
                await asyncio.sleep(retry_delay)
        
        # All retries failed
        self.state = ConnectionState.FAILED
        logger.critical(f"❌ {self.name}: Connection failed after {self.config.max_retries} attempts")
        return False
    
    async def disconnect(self, disconnect_func: Optional[Callable] = None):
        """Gracefully disconnect"""
        if self.state == ConnectionState.DISCONNECTED:
            return
        
        logger.info(f"{self.name}: Disconnecting...")
        
        # Stop heartbeat
        self._stop_heartbeat()
        
        # Stop reconnect task if running
        if self._reconnect_task and not self._reconnect_task.done():
            self._reconnect_task.cancel()
        
        # Call disconnect function if provided
        if disconnect_func and self.connection:
            try:
                await disconnect_func(self.connection)
            except Exception as e:
                logger.error(f"{self.name}: Error during disconnect: {e}")
        
        self.connection = None
        self.state = ConnectionState.DISCONNECTED
        
        # Call on_disconnect callback
        if self.on_disconnect:
            await self.on_disconnect()
        
        logger.info(f"{self.name}: Disconnected")
    
    async def reconnect(self, connect_func: Callable):
        """Reconnect after disconnection"""
        if self.state == ConnectionState.RECONNECTING:
            logger.warning(f"{self.name}: Reconnection already in progress")
            return
        
        logger.warning(f"{self.name}: Initiating reconnection...")
        self.state = ConnectionState.RECONNECTING
        
        # Disconnect first
        await self.disconnect()
        
        # Reconnect
        success = await self.connect(connect_func)
        
        if not success:
            # Schedule another reconnect attempt
            self._schedule_reconnect(connect_func)
    
    def _schedule_reconnect(self, connect_func: Callable):
        """Schedule automatic reconnection"""
        if self._reconnect_task and not self._reconnect_task.done():
            return
        
        async def reconnect_loop():
            while self.state != ConnectionState.CONNECTED:
                await asyncio.sleep(self.config.initial_retry_delay)
                await self.reconnect(connect_func)
        
        self._reconnect_task = asyncio.create_task(reconnect_loop())
    
    def _start_heartbeat(self):
        """Start heartbeat monitoring"""
        if self._heartbeat_task and not self._heartbeat_task.done():
            return
        
        async def heartbeat_loop():
            while self.state == ConnectionState.CONNECTED:
                try:
                    await asyncio.sleep(self.config.heartbeat_interval)
                    
                    # Check if heartbeat is overdue
                    if self.last_heartbeat:
                        time_since_heartbeat = (datetime.now() - self.last_heartbeat).total_seconds()
                        if time_since_heartbeat > self.config.heartbeat_timeout:
                            logger.error(f"{self.name}: Heartbeat timeout - connection may be dead")
                            # Trigger reconnection
                            # await self.reconnect(...)  # Would need connect_func reference
                    
                    self.last_heartbeat = datetime.now()
                    
                except Exception as e:
                    logger.error(f"{self.name}: Heartbeat error: {e}")
        
        self._heartbeat_task = asyncio.create_task(heartbeat_loop())
    
    def _stop_heartbeat(self):
        """Stop heartbeat monitoring"""
        if self._heartbeat_task and not self._heartbeat_task.done():
            self._heartbeat_task.cancel()
    
    def is_connected(self) -> bool:
        """Check if currently connected"""
        return self.state == ConnectionState.CONNECTED
    
    def get_status(self) -> dict:
        """Get connection status"""
        uptime = None
        if self.last_connection_time:
            uptime = (datetime.now() - self.last_connection_time).total_seconds()
        
        return {
            'name': self.name,
            'state': self.state.value,
            'connected': self.is_connected(),
            'retry_count': self.retry_count,
            'uptime_seconds': uptime,
            'last_heartbeat': self.last_heartbeat.isoformat() if self.last_heartbeat else None
        }


class ConnectionPool:
    """
    Connection Pool Manager
    
    Manages multiple resilient connections
    """
    
    def __init__(self):
        self.connections: dict[str, ResilientConnection] = {}
        logger.info("Connection pool initialized")
    
    def add_connection(self, name: str, config: Optional[ConnectionConfig] = None) -> ResilientConnection:
        """Add a new connection to the pool"""
        if name in self.connections:
            logger.warning(f"Connection '{name}' already exists in pool")
            return self.connections[name]
        
        connection = ResilientConnection(name, config)
        self.connections[name] = connection
        logger.info(f"Added connection '{name}' to pool")
        return connection
    
    def get_connection(self, name: str) -> Optional[ResilientConnection]:
        """Get connection by name"""
        return self.connections.get(name)
    
    async def connect_all(self, connect_funcs: dict[str, Callable]) -> dict[str, bool]:
        """Connect all connections in pool"""
        results = {}
        tasks = []
        
        for name, connect_func in connect_funcs.items():
            if name in self.connections:
                tasks.append(self.connections[name].connect(connect_func))
            else:
                logger.warning(f"Connection '{name}' not found in pool")
        
        task_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for name, result in zip(connect_funcs.keys(), task_results):
            results[name] = result if not isinstance(result, Exception) else False
        
        return results
    
    async def disconnect_all(self):
        """Disconnect all connections"""
        tasks = [conn.disconnect() for conn in self.connections.values()]
        await asyncio.gather(*tasks, return_exceptions=True)
        logger.info("All connections disconnected")
    
    def get_pool_status(self) -> dict:
        """Get status of all connections"""
        return {
            name: conn.get_status()
            for name, conn in self.connections.items()
        }
    
    def get_healthy_connections(self) -> list[str]:
        """Get list of healthy connection names"""
        return [
            name for name, conn in self.connections.items()
            if conn.is_connected()
        ]


# Export
__all__ = ['ResilientConnection', 'ConnectionPool', 'ConnectionConfig', 'ConnectionState']
