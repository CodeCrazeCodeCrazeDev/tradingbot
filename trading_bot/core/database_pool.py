"""
Database Connection Pooling
Provides efficient connection management for database operations.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from contextlib import asynccontextmanager
import sqlite3
import threading
from queue import Queue, Empty
from enum import Enum

logger = logging.getLogger(__name__)


class PoolStatus(Enum):
    """Connection pool status."""
    ACTIVE = "active"
    EXHAUSTED = "exhausted"
    CLOSED = "closed"


@dataclass
class PoolStats:
    """Statistics for the connection pool."""
    total_connections: int = 0
    active_connections: int = 0
    idle_connections: int = 0
    waiting_requests: int = 0
    total_acquisitions: int = 0
    total_releases: int = 0
    total_timeouts: int = 0
    avg_wait_time_ms: float = 0.0


class ConnectionWrapper:
    """Wrapper for database connection with metadata."""
    
    def __init__(self, connection, pool: 'ConnectionPool'):
        self.connection = connection
        self.pool = pool
        self.created_at = datetime.now()
        self.last_used = datetime.now()
        self.use_count = 0
        self.in_use = False
    
    def execute(self, query: str, params: tuple = ()):
        """Execute a query."""
        self.last_used = datetime.now()
        self.use_count += 1
        cursor = self.connection.cursor()
        cursor.execute(query, params)
        return cursor
    
    def executemany(self, query: str, params_list: List[tuple]):
        """Execute a query with multiple parameter sets."""
        self.last_used = datetime.now()
        self.use_count += 1
        cursor = self.connection.cursor()
        cursor.executemany(query, params_list)
        return cursor
    
    def commit(self):
        """Commit the transaction."""
        self.connection.commit()
    
    def rollback(self):
        """Rollback the transaction."""
        self.connection.rollback()
    
    def close(self):
        """Close the underlying connection."""
        try:
            self.connection.close()
        except Exception as e:
            logger.error(f"Error closing connection: {e}")


class ConnectionPool:
    """
    Database connection pool for efficient connection management.
    
    Features:
    - Connection reuse
    - Automatic connection creation
    - Connection health checks
    - Timeout handling
    - Statistics tracking
    """
    
    def __init__(
        self,
        database_path: str = "data/trading.db",
        min_connections: int = 2,
        max_connections: int = 10,
        connection_timeout: float = 30.0,
        max_connection_age_seconds: int = 3600,
        health_check_interval: int = 60
    ):
        self.database_path = database_path
        self.min_connections = min_connections
        self.max_connections = max_connections
        self.connection_timeout = connection_timeout
        self.max_connection_age = max_connection_age_seconds
        self.health_check_interval = health_check_interval
        
        # Connection storage
        self._pool: Queue = Queue(maxsize=max_connections)
        self._all_connections: List[ConnectionWrapper] = []
        self._lock = threading.RLock()
        
        # Statistics
        self._stats = PoolStats()
        self._wait_times: List[float] = []
        self._max_wait_times = 1000
        
        # Status
        self._closed = False
        self._initialized = False
        
        logger.info(f"ConnectionPool created: min={min_connections}, max={max_connections}")
    
    async def initialize(self):
        """Initialize the pool with minimum connections."""
        if self._initialized:
            return
        
        with self._lock:
            for _ in range(self.min_connections):
                conn = self._create_connection()
                if conn:
                    self._pool.put(conn)
            
            self._initialized = True
            logger.info(f"ConnectionPool initialized with {self._pool.qsize()} connections")
    
    def _create_connection(self) -> Optional[ConnectionWrapper]:
        """Create a new database connection."""
        try:
            # Create SQLite connection with optimizations
            conn = sqlite3.connect(
                self.database_path,
                check_same_thread=False,
                timeout=self.connection_timeout
            )
            
            # Enable WAL mode for better concurrency
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA synchronous=NORMAL")
            conn.execute("PRAGMA cache_size=10000")
            
            wrapper = ConnectionWrapper(conn, self)
            self._all_connections.append(wrapper)
            self._stats.total_connections += 1
            
            logger.debug(f"Created new connection (total: {len(self._all_connections)})")
            return wrapper
            
        except Exception as e:
            logger.error(f"Error creating connection: {e}")
            return None
    
    @asynccontextmanager
    async def acquire(self):
        """
        Acquire a connection from the pool.
        
        Usage:
            async with pool.acquire() as conn:
                conn.execute("SELECT * FROM trades")
        """
        if self._closed:
            raise RuntimeError("Connection pool is closed")
        
        start_time = datetime.now()
        conn = None
        
        try:
            try:
                # Try to get from pool
                conn = self._pool.get(timeout=self.connection_timeout)
                self._stats.total_acquisitions += 1
            except Empty:
                # Pool exhausted - try to create new connection
                with self._lock:
                    if len(self._all_connections) < self.max_connections:
                        conn = self._create_connection()
                    else:
                        self._stats.total_timeouts += 1
                        raise TimeoutError("Connection pool exhausted")
            
            if conn is None:
                raise RuntimeError("Failed to acquire connection")
            
            # Check connection health
            if not self._is_connection_healthy(conn):
                conn.close()
                self._all_connections.remove(conn)
                conn = self._create_connection()
            
            conn.in_use = True
            self._stats.active_connections += 1
            
            # Track wait time
            wait_time = (datetime.now() - start_time).total_seconds() * 1000
            self._wait_times.append(wait_time)
            if len(self._wait_times) > self._max_wait_times:
                self._wait_times = self._wait_times[-500:]
            self._stats.avg_wait_time_ms = sum(self._wait_times) / len(self._wait_times)
            
            yield conn
            
        finally:
            if conn:
                self._release(conn)
    
    def _release(self, conn: ConnectionWrapper):
        """Release a connection back to the pool."""
        conn.in_use = False
        conn.last_used = datetime.now()
        self._stats.active_connections -= 1
        self._stats.total_releases += 1
        
        # Check if connection is still healthy
        if self._is_connection_healthy(conn):
            try:
                self._pool.put_nowait(conn)
            except Exception as e:
                logger.error(f"Error: {e}")
                # Pool is full, close connection
                conn.close()
                with self._lock:
                    if conn in self._all_connections:
                        self._all_connections.remove(conn)
        else:
            conn.close()
            with self._lock:
                if conn in self._all_connections:
                    self._all_connections.remove(conn)
    
    def _is_connection_healthy(self, conn: ConnectionWrapper) -> bool:
        """Check if a connection is healthy."""
        try:
            # Check age
            age = (datetime.now() - conn.created_at).total_seconds()
            if age > self.max_connection_age:
                return False
            
            # Try a simple query
            conn.execute("SELECT 1")
            return True
            
        except Exception:
            return False
    
    async def close(self):
        """Close all connections in the pool."""
        self._closed = True
        
        with self._lock:
            # Close all connections
            for conn in self._all_connections:
                try:
                    conn.close()
                except Exception as e:
                    logger.error(f"Error closing connection: {e}")
            
            self._all_connections.clear()
            
            # Empty the queue
            while not self._pool.empty():
                try:
                    self._pool.get_nowait()
                except Empty:
                    break
        
        logger.info("ConnectionPool closed")
    
    def get_stats(self) -> PoolStats:
        """Get pool statistics."""
        self._stats.idle_connections = self._pool.qsize()
        return self._stats
    
    def get_status(self) -> Dict[str, Any]:
        """Get pool status."""
        stats = self.get_stats()
        
        if self._closed:
            status = PoolStatus.CLOSED
        elif stats.idle_connections == 0 and stats.active_connections >= self.max_connections:
            status = PoolStatus.EXHAUSTED
        else:
            status = PoolStatus.ACTIVE
        
        return {
            'status': status.value,
            'total_connections': stats.total_connections,
            'active_connections': stats.active_connections,
            'idle_connections': stats.idle_connections,
            'max_connections': self.max_connections,
            'total_acquisitions': stats.total_acquisitions,
            'total_releases': stats.total_releases,
            'total_timeouts': stats.total_timeouts,
            'avg_wait_time_ms': round(stats.avg_wait_time_ms, 2)
        }


# Async wrapper for common database operations
class AsyncDatabase:
    """
    Async database wrapper using connection pooling.
    """
    
    def __init__(self, pool: ConnectionPool):
        self.pool = pool
    
    async def execute(self, query: str, params: tuple = ()) -> Any:
        """Execute a query and return cursor."""
        async with self.pool.acquire() as conn:
            cursor = conn.execute(query, params)
            conn.commit()
            return cursor
    
    async def fetch_one(self, query: str, params: tuple = ()) -> Optional[tuple]:
        """Fetch a single row."""
        async with self.pool.acquire() as conn:
            cursor = conn.execute(query, params)
            return cursor.fetchone()
    
    async def fetch_all(self, query: str, params: tuple = ()) -> List[tuple]:
        """Fetch all rows."""
        async with self.pool.acquire() as conn:
            cursor = conn.execute(query, params)
            return cursor.fetchall()
    
    async def insert(self, table: str, data: Dict[str, Any]) -> int:
        """Insert a row and return the row ID."""
        columns = ', '.join(data.keys())
        placeholders = ', '.join(['?' for _ in data])
        query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
        
        async with self.pool.acquire() as conn:
            cursor = conn.execute(query, tuple(data.values()))
            conn.commit()
            return cursor.lastrowid
    
    async def update(self, table: str, data: Dict[str, Any], where: str, params: tuple = ()) -> int:
        """Update rows and return affected count."""
        set_clause = ', '.join([f"{k} = ?" for k in data.keys()])
        query = f"UPDATE {table} SET {set_clause} WHERE {where}"
        
        async with self.pool.acquire() as conn:
            cursor = conn.execute(query, tuple(data.values()) + params)
            conn.commit()
            return cursor.rowcount
    
    async def delete(self, table: str, where: str, params: tuple = ()) -> int:
        """Delete rows and return affected count."""
        query = f"DELETE FROM {table} WHERE {where}"
        
        async with self.pool.acquire() as conn:
            cursor = conn.execute(query, params)
            conn.commit()
            return cursor.rowcount


# Singleton pool instance
_default_pool: Optional[ConnectionPool] = None


def get_connection_pool(
    database_path: str = "data/trading.db",
    **kwargs
) -> ConnectionPool:
    """Get or create the default connection pool."""
    global _default_pool
    if _default_pool is None:
        _default_pool = ConnectionPool(database_path, **kwargs)
    return _default_pool


async def get_async_database(database_path: str = "data/trading.db") -> AsyncDatabase:
    """Get an async database instance with pooling."""
    pool = get_connection_pool(database_path)
    await pool.initialize()
    return AsyncDatabase(pool)


__all__ = [
    'ConnectionPool',
    'ConnectionWrapper',
    'AsyncDatabase',
    'PoolStats',
    'PoolStatus',
    'get_connection_pool',
    'get_async_database'
]
