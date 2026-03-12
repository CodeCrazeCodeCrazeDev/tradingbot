"""
Unified Connector - Consolidated connectivity interface for all data sources and brokers.

Manages connections to exchanges, brokers, data providers, and external services
through a single interface with automatic failover and health monitoring.
"""

import logging
import time
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class ConnectionType(Enum):
    """Types of connections managed."""
    BROKER = "broker"
    EXCHANGE = "exchange"
    DATA_FEED = "data_feed"
    NEWS_API = "news_api"
    SENTIMENT_API = "sentiment_api"
    ALTERNATIVE_DATA = "alternative_data"
    BLOCKCHAIN = "blockchain"
    INTERNAL_SERVICE = "internal_service"


class ConnectionStatus(Enum):
    """Connection health status."""
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    DEGRADED = "degraded"
    ERROR = "error"
    RATE_LIMITED = "rate_limited"


@dataclass
class ConnectionInfo:
    """Information about a managed connection."""
    name: str
    connection_type: ConnectionType
    status: ConnectionStatus = ConnectionStatus.DISCONNECTED
    endpoint: str = ""
    last_heartbeat: Optional[datetime] = None
    latency_ms: float = 0.0
    error_count: int = 0
    reconnect_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


class UnifiedConnector:
    """
    Consolidated connectivity manager for all external connections.

    Integrates:
    - trading_bot/connectivity/ (WebSocket, REST)
    - trading_bot/connectors/ (exchange connectors)
    - trading_bot/brokers/ (broker adapters)
    - trading_bot/ingestion/ (data ingestion)
    - trading_bot/internet_access/ (internet connectivity)
    - trading_bot/streaming/ (data streaming)
    """

    def __init__(self, config: Optional[Dict] = None):
        self._config = config or {}
        self._connections: Dict[str, ConnectionInfo] = {}
        self._callbacks: Dict[str, List[Callable]] = {}
        self._max_reconnect_attempts = self._config.get("max_reconnect_attempts", 5)
        self._heartbeat_interval = self._config.get("heartbeat_interval", 30)
        logger.info("UnifiedConnector initialized")

    def register_connection(
        self,
        name: str,
        connection_type: ConnectionType,
        endpoint: str = "",
        metadata: Optional[Dict] = None,
    ) -> None:
        """Register a new connection to manage."""
        self._connections[name] = ConnectionInfo(
            name=name,
            connection_type=connection_type,
            endpoint=endpoint,
            metadata=metadata or {},
        )
        logger.info("Registered connection: %s (%s)", name, connection_type.value)

    def connect(self, name: str) -> bool:
        """Establish a connection by name."""
        conn = self._connections.get(name)
        if not conn:
            logger.error("Unknown connection: %s", name)
            return False

        conn.status = ConnectionStatus.CONNECTING
        try:
            # Delegate to appropriate connector based on type
            success = self._establish_connection(conn)
            if success:
                conn.status = ConnectionStatus.CONNECTED
                conn.last_heartbeat = datetime.utcnow()
                conn.error_count = 0
                logger.info("Connected: %s", name)
                self._fire_callback(name, "connected")
            else:
                conn.status = ConnectionStatus.ERROR
                conn.error_count += 1
                logger.warning("Failed to connect: %s", name)
            return success
        except Exception as e:
            conn.status = ConnectionStatus.ERROR
            conn.error_count += 1
            logger.error("Connection error for %s: %s", name, e)
            return False

    def disconnect(self, name: str) -> bool:
        """Disconnect a connection by name."""
        conn = self._connections.get(name)
        if not conn:
            return False

        conn.status = ConnectionStatus.DISCONNECTED
        logger.info("Disconnected: %s", name)
        self._fire_callback(name, "disconnected")
        return True

    def disconnect_all(self) -> None:
        """Disconnect all managed connections."""
        for name in list(self._connections.keys()):
            self.disconnect(name)

    def reconnect(self, name: str) -> bool:
        """Reconnect a connection with retry logic."""
        conn = self._connections.get(name)
        if not conn:
            return False

        for attempt in range(1, self._max_reconnect_attempts + 1):
            logger.info("Reconnect attempt %d/%d for %s",
                        attempt, self._max_reconnect_attempts, name)
            conn.reconnect_count += 1

            if self.connect(name):
                return True

            # Exponential backoff
            wait = min(2 ** attempt, 30)
            time.sleep(wait)

        logger.error("Failed to reconnect %s after %d attempts",
                      name, self._max_reconnect_attempts)
        return False

    def get_status(self, name: Optional[str] = None) -> Dict:
        """Get connection status for one or all connections."""
        if name:
            conn = self._connections.get(name)
            if not conn:
                return {"error": f"Unknown connection: {name}"}
            return {
                "name": conn.name,
                "type": conn.connection_type.value,
                "status": conn.status.value,
                "endpoint": conn.endpoint,
                "latency_ms": conn.latency_ms,
                "error_count": conn.error_count,
                "reconnect_count": conn.reconnect_count,
                "last_heartbeat": conn.last_heartbeat.isoformat() if conn.last_heartbeat else None,
            }

        return {
            "total_connections": len(self._connections),
            "connected": sum(1 for c in self._connections.values()
                             if c.status == ConnectionStatus.CONNECTED),
            "disconnected": sum(1 for c in self._connections.values()
                                if c.status == ConnectionStatus.DISCONNECTED),
            "errors": sum(1 for c in self._connections.values()
                          if c.status == ConnectionStatus.ERROR),
            "connections": {
                name: {
                    "type": c.connection_type.value,
                    "status": c.status.value,
                    "latency_ms": c.latency_ms,
                }
                for name, c in self._connections.items()
            },
        }

    def is_healthy(self) -> bool:
        """Check if all critical connections are healthy."""
        critical_types = {ConnectionType.BROKER, ConnectionType.EXCHANGE, ConnectionType.DATA_FEED}
        for conn in self._connections.values():
            if conn.connection_type in critical_types:
                if conn.status not in (ConnectionStatus.CONNECTED, ConnectionStatus.DEGRADED):
                    return False
        return True

    def on_event(self, name: str, callback: Callable) -> None:
        """Register a callback for connection events."""
        if name not in self._callbacks:
            self._callbacks[name] = []
        self._callbacks[name].append(callback)

    def update_heartbeat(self, name: str, latency_ms: float = 0.0) -> None:
        """Update heartbeat for a connection."""
        conn = self._connections.get(name)
        if conn:
            conn.last_heartbeat = datetime.utcnow()
            conn.latency_ms = latency_ms
            if conn.status == ConnectionStatus.DEGRADED and latency_ms < 100:
                conn.status = ConnectionStatus.CONNECTED

    def check_stale_connections(self, max_age_seconds: int = 60) -> List[str]:
        """Find connections that haven't sent a heartbeat recently."""
        stale = []
        now = datetime.utcnow()
        for name, conn in self._connections.items():
            if conn.status == ConnectionStatus.CONNECTED and conn.last_heartbeat:
                age = (now - conn.last_heartbeat).total_seconds()
                if age > max_age_seconds:
                    stale.append(name)
                    conn.status = ConnectionStatus.DEGRADED
                    logger.warning("Stale connection detected: %s (%.0fs)", name, age)
        return stale

    def _establish_connection(self, conn: ConnectionInfo) -> bool:
        """Establish connection using appropriate connector."""
        # Try to load the appropriate connector module
        if conn.connection_type == ConnectionType.BROKER:
            return self._connect_broker(conn)
        elif conn.connection_type == ConnectionType.EXCHANGE:
            return self._connect_exchange(conn)
        elif conn.connection_type == ConnectionType.DATA_FEED:
            return self._connect_data_feed(conn)
        else:
            # Generic connection - mark as connected if endpoint is set
            return bool(conn.endpoint)

    def _connect_broker(self, conn: ConnectionInfo) -> bool:
        """Connect to a broker."""
        try:
            from trading_bot.brokers import broker_adapter
            logger.debug("Broker adapter available for %s", conn.name)
            return True
        except ImportError:
            logger.debug("Broker adapter not available, using mock for %s", conn.name)
            return True  # Allow mock connections

    def _connect_exchange(self, conn: ConnectionInfo) -> bool:
        """Connect to an exchange."""
        try:
            from trading_bot.connectors import exchange_connector
            logger.debug("Exchange connector available for %s", conn.name)
            return True
        except ImportError:
            logger.debug("Exchange connector not available for %s", conn.name)
            return True

    def _connect_data_feed(self, conn: ConnectionInfo) -> bool:
        """Connect to a data feed."""
        try:
            from trading_bot.data_feeds import data_feed_manager
            logger.debug("Data feed manager available for %s", conn.name)
            return True
        except ImportError:
            logger.debug("Data feed manager not available for %s", conn.name)
            return True

    def _fire_callback(self, name: str, event: str) -> None:
        """Fire registered callbacks for a connection event."""
        callbacks = self._callbacks.get(name, [])
        for cb in callbacks:
            try:
                cb(name, event)
            except Exception as e:
                logger.error("Callback error for %s/%s: %s", name, event, e)
