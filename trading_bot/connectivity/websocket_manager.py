"""
WebSocket Manager - Manages WebSocket connections for real-time data
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any, Optional, List, Callable
from enum import Enum

logger = logging.getLogger(__name__)


class ConnectionState(Enum):
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"
    ERROR = "error"


@dataclass
class WebSocketConnection:
    url: str
    state: ConnectionState = ConnectionState.DISCONNECTED
    reconnect_attempts: int = 0
    max_reconnects: int = 5
    last_message_time: Optional[datetime] = None


class WebSocketManager:
    """Manages WebSocket connections"""
    
    def __init__(self, config: Dict[str, Any] = None):
        try:
            self.config = config or {}
            self.connections: Dict[str, WebSocketConnection] = {}
            self.message_handlers: Dict[str, List[Callable]] = {}
            self._running = False
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    async def initialize(self, config: Dict[str, Any] = None) -> bool:
        try:
            if config:
                self.config.update(config)
            logger.info("WebSocketManager initialized")
            return True
        except Exception as e:
            logger.error(f"Error in initialize: {e}")
            raise
    
    async def start(self) -> bool:
        try:
            self._running = True
            logger.info("WebSocketManager started")
            return True
        except Exception as e:
            logger.error(f"Error in start: {e}")
            raise
    
    async def stop(self) -> bool:
        try:
            self._running = False
            for conn_id in list(self.connections.keys()):
                await self.disconnect(conn_id)
            logger.info("WebSocketManager stopped")
            return True
        except Exception as e:
            logger.error(f"Error in stop: {e}")
            raise
    
    async def connect(self, conn_id: str, url: str) -> bool:
        try:
            self.connections[conn_id] = WebSocketConnection(url=url, state=ConnectionState.CONNECTED)
            logger.info(f"Connected to {url}")
            return True
        except Exception as e:
            logger.error(f"Error in connect: {e}")
            raise
    
    async def disconnect(self, conn_id: str) -> bool:
        try:
            if conn_id in self.connections:
                self.connections[conn_id].state = ConnectionState.DISCONNECTED
                del self.connections[conn_id]
            return True
        except Exception as e:
            logger.error(f"Error in disconnect: {e}")
            raise
    
    def add_handler(self, conn_id: str, handler: Callable):
        try:
            if conn_id not in self.message_handlers:
                self.message_handlers[conn_id] = []
            self.message_handlers[conn_id].append(handler)
        except Exception as e:
            logger.error(f"Error in add_handler: {e}")
            raise
    
    def get_connection_state(self, conn_id: str) -> Optional[ConnectionState]:
        try:
            if conn_id in self.connections:
                return self.connections[conn_id].state
            return None
        except Exception as e:
            logger.error(f"Error in get_connection_state: {e}")
            raise


_manager: Optional[WebSocketManager] = None

def get_manager() -> WebSocketManager:
    try:
        global _manager
        if _manager is None:
            _manager = WebSocketManager()
        return _manager
    except Exception as e:
        logger.error(f"Error in get_manager: {e}")
        raise

async def initialize(config: Dict[str, Any] = None) -> bool:
    return await get_manager().initialize(config)

async def start() -> bool:
    return await get_manager().start()

async def stop() -> bool:
    return await get_manager().stop()
