"""
Database Persistence Layer
===========================
Production-grade persistence with SQLite and PostgreSQL support.
Handles trades, positions, signals, and system state.
"""

import asyncio
import json
import logging
import os
import sqlite3
import threading
from abc import ABC, abstractmethod
from contextlib import contextmanager
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional, Type, TypeVar, Union
from pathlib import Path

try:
    from psycopg2.extras import RealDictCursor
except ImportError:
    RealDictCursor = None

logger = logging.getLogger(__name__)

T = TypeVar('T')


# ============================================================================
# CONFIGURATION
# ============================================================================

@dataclass
class DatabaseConfig:
    """Database configuration."""
    db_type: str = "sqlite"  # sqlite, postgresql
    host: str = "localhost"
    port: int = 5432
    database: str = "trading_bot"
    username: str = ""
    password: str = ""
    sqlite_path: str = "trading_bot.db"
    pool_size: int = 5
    max_overflow: int = 10
    echo: bool = False
    auto_migrate: bool = True


# ============================================================================
# BASE MODELS
# ============================================================================

@dataclass
class Trade:
    """Trade record."""
    trade_id: str
    order_id: str
    symbol: str
    side: str
    quantity: float
    entry_price: float
    exit_price: Optional[float] = None
    pnl: Optional[float] = None
    commission: float = 0.0
    status: str = "open"
    entry_time: datetime = field(default_factory=datetime.utcnow)
    exit_time: Optional[datetime] = None
    strategy: str = ""
    signal_id: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            'trade_id': self.trade_id,
            'order_id': self.order_id,
            'symbol': self.symbol,
            'side': self.side,
            'quantity': self.quantity,
            'entry_price': self.entry_price,
            'exit_price': self.exit_price,
            'pnl': self.pnl,
            'commission': self.commission,
            'status': self.status,
            'entry_time': self.entry_time.isoformat() if self.entry_time else None,
            'exit_time': self.exit_time.isoformat() if self.exit_time else None,
            'strategy': self.strategy,
            'signal_id': self.signal_id,
            'metadata': self.metadata,
        }


@dataclass
class PositionRecord:
    """Position record."""
    position_id: str
    symbol: str
    side: str
    quantity: float
    entry_price: float
    current_price: float
    unrealized_pnl: float
    realized_pnl: float = 0.0
    margin_used: float = 0.0
    leverage: int = 1
    opened_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SignalRecord:
    """Signal record."""
    signal_id: str
    symbol: str
    direction: str
    confidence: float
    source: str
    price_at_signal: float
    status: str = "active"
    created_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    executed_at: Optional[datetime] = None
    result: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SystemState:
    """System state record."""
    state_id: str
    component: str
    state_data: Dict[str, Any]
    version: int = 1
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class PerformanceMetric:
    """Performance metric record."""
    metric_id: str
    metric_name: str
    metric_value: float
    period: str  # daily, weekly, monthly, all_time
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


# ============================================================================
# DATABASE BACKEND
# ============================================================================

class DatabaseBackend(ABC):
    """Abstract database backend."""
    
    @abstractmethod
    def connect(self) -> bool:
        """Auto-implemented method."""
        logger.debug(f"{self.__class__.__name__}.connect called")
        return None
    
    @abstractmethod
    def disconnect(self) -> bool:
        """Auto-implemented method."""
        logger.debug(f"{self.__class__.__name__}.disconnect called")
        return None
    
    @abstractmethod
    def execute(self, query: str, params: tuple = ()) -> Any:
        """Auto-implemented method."""
        logger.debug(f"{self.__class__.__name__}.execute called")
        return None
    
    @abstractmethod
    def executemany(self, query: str, params_list: List[tuple]) -> Any:
        """Auto-implemented method."""
        logger.debug(f"{self.__class__.__name__}.executemany called")
        return None
    
    @abstractmethod
    def fetchone(self, query: str, params: tuple = ()) -> Optional[Dict]:
        """Auto-implemented method."""
        logger.debug(f"{self.__class__.__name__}.fetchone called")
        return None
    
    @abstractmethod
    def fetchall(self, query: str, params: tuple = ()) -> List[Dict]:
        """Auto-implemented method."""
        logger.debug(f"{self.__class__.__name__}.fetchall called")
        return None


class SQLiteBackend(DatabaseBackend):
    """SQLite database backend."""
    
    def __init__(self, config: DatabaseConfig):
        self.config = config
        self.db_path = config.sqlite_path
        self._connection: Optional[sqlite3.Connection] = None
        self._lock = threading.Lock()
    
    def connect(self) -> bool:
        try:
            self._connection = sqlite3.connect(
                self.db_path,
                check_same_thread=False,
                timeout=30.0,
            )
            self._connection.row_factory = sqlite3.Row
            self._connection.execute("PRAGMA journal_mode=WAL")
            self._connection.execute("PRAGMA synchronous=NORMAL")
            self._connection.execute("PRAGMA cache_size=10000")
            logger.info(f"Connected to SQLite: {self.db_path}")
            return True
        except Exception as e:
            logger.error(f"SQLite connection error: {e}")
            return False
    
    def disconnect(self) -> bool:
        try:
            if self._connection:
                self._connection.close()
                self._connection = None
            return True
        except Exception as e:
            logger.error(f"SQLite disconnect error: {e}")
            return False
    
    @contextmanager
    def _get_cursor(self):
        with self._lock:
            cursor = self._connection.cursor()
            try:
                yield cursor
                self._connection.commit()
            except Exception:
                self._connection.rollback()
                raise
            finally:
                cursor.close()
    
    def execute(self, query: str, params: tuple = ()) -> Any:
        with self._get_cursor() as cursor:
            cursor.execute(query, params)
            return cursor.lastrowid
    
    def executemany(self, query: str, params_list: List[tuple]) -> Any:
        with self._get_cursor() as cursor:
            cursor.executemany(query, params_list)
            return cursor.rowcount
    
    def fetchone(self, query: str, params: tuple = ()) -> Optional[Dict]:
        with self._get_cursor() as cursor:
            cursor.execute(query, params)
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def fetchall(self, query: str, params: tuple = ()) -> List[Dict]:
        with self._get_cursor() as cursor:
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]


class PostgreSQLBackend(DatabaseBackend):
    """PostgreSQL database backend."""
    
    def __init__(self, config: DatabaseConfig):
        self.config = config
        self._pool = None
    
    def connect(self) -> bool:
        try:
            import psycopg2
            from psycopg2 import pool
            
            self._pool = pool.ThreadedConnectionPool(
                minconn=1,
                maxconn=self.config.pool_size,
                host=self.config.host,
                port=self.config.port,
                database=self.config.database,
                user=self.config.username,
                password=self.config.password,
            )
            logger.info(f"Connected to PostgreSQL: {self.config.host}:{self.config.port}/{self.config.database}")
            return True
        except ImportError:
            logger.error("psycopg2 not installed. Install with: pip install psycopg2-binary")
            return False
        except Exception as e:
            logger.error(f"PostgreSQL connection error: {e}")
            return False
    
    def disconnect(self) -> bool:
        try:
            if self._pool:
                self._pool.closeall()
            return True
        except Exception as e:
            logger.error(f"PostgreSQL disconnect error: {e}")
            return False
    
    @contextmanager
    def _get_connection(self):
        conn = self._pool.getconn()
        try:
            yield conn, conn.cursor(cursor_factory=RealDictCursor)
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            self._pool.putconn(conn)
    
    def execute(self, query: str, params: tuple = ()) -> Any:
        with self._get_connection() as (conn, cursor):
            cursor.execute(query, params)
            return cursor.rowcount
    
    def executemany(self, query: str, params_list: List[tuple]) -> Any:
        with self._get_connection() as (conn, cursor):
            cursor.executemany(query, params_list)
            return cursor.rowcount
    
    def fetchone(self, query: str, params: tuple = ()) -> Optional[Dict]:
        with self._get_connection() as (conn, cursor):
            cursor.execute(query, params)
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def fetchall(self, query: str, params: tuple = ()) -> List[Dict]:
        with self._get_connection() as (conn, cursor):
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]


# ============================================================================
# PERSISTENCE MANAGER
# ============================================================================

class PersistenceManager:
    """
    Main persistence manager.
    Handles all database operations for the trading bot.
    """
    
    def __init__(self, config: Optional[DatabaseConfig] = None):
        self.config = config or DatabaseConfig()
        self._backend: Optional[DatabaseBackend] = None
        self._initialized = False
    
    def initialize(self) -> bool:
        """Initialize database connection and schema."""
        # Create backend
        if self.config.db_type == "sqlite":
            self._backend = SQLiteBackend(self.config)
        elif self.config.db_type == "postgresql":
            self._backend = PostgreSQLBackend(self.config)
        else:
            raise ValueError(f"Unsupported database type: {self.config.db_type}")
        
        # Connect
        if not self._backend.connect():
            return False
        
        # Create schema
        if self.config.auto_migrate:
            self._create_schema()
        
        self._initialized = True
        return True
    
    def _create_schema(self):
        """Create database schema."""
        # Trades table
        self._backend.execute("""
            CREATE TABLE IF NOT EXISTS trades (
                trade_id TEXT PRIMARY KEY,
                order_id TEXT NOT NULL,
                symbol TEXT NOT NULL,
                side TEXT NOT NULL,
                quantity REAL NOT NULL,
                entry_price REAL NOT NULL,
                exit_price REAL,
                pnl REAL,
                commission REAL DEFAULT 0,
                status TEXT DEFAULT 'open',
                entry_time TEXT NOT NULL,
                exit_time TEXT,
                strategy TEXT,
                signal_id TEXT,
                metadata TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Positions table
        self._backend.execute("""
            CREATE TABLE IF NOT EXISTS positions (
                position_id TEXT PRIMARY KEY,
                symbol TEXT NOT NULL,
                side TEXT NOT NULL,
                quantity REAL NOT NULL,
                entry_price REAL NOT NULL,
                current_price REAL NOT NULL,
                unrealized_pnl REAL NOT NULL,
                realized_pnl REAL DEFAULT 0,
                margin_used REAL DEFAULT 0,
                leverage INTEGER DEFAULT 1,
                opened_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                metadata TEXT
            )
        """)
        
        # Signals table
        self._backend.execute("""
            CREATE TABLE IF NOT EXISTS signals (
                signal_id TEXT PRIMARY KEY,
                symbol TEXT NOT NULL,
                direction TEXT NOT NULL,
                confidence REAL NOT NULL,
                source TEXT NOT NULL,
                price_at_signal REAL NOT NULL,
                status TEXT DEFAULT 'active',
                created_at TEXT NOT NULL,
                expires_at TEXT,
                executed_at TEXT,
                result TEXT,
                metadata TEXT
            )
        """)
        
        # System state table
        self._backend.execute("""
            CREATE TABLE IF NOT EXISTS system_state (
                state_id TEXT PRIMARY KEY,
                component TEXT NOT NULL,
                state_data TEXT NOT NULL,
                version INTEGER DEFAULT 1,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        
        # Performance metrics table
        self._backend.execute("""
            CREATE TABLE IF NOT EXISTS performance_metrics (
                metric_id TEXT PRIMARY KEY,
                metric_name TEXT NOT NULL,
                metric_value REAL NOT NULL,
                period TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                metadata TEXT
            )
        """)
        
        # OHLCV data table
        self._backend.execute("""
            CREATE TABLE IF NOT EXISTS ohlcv_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                timeframe TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                open REAL NOT NULL,
                high REAL NOT NULL,
                low REAL NOT NULL,
                close REAL NOT NULL,
                volume REAL NOT NULL,
                UNIQUE(symbol, timeframe, timestamp)
            )
        """)
        
        # Create indexes
        self._backend.execute("CREATE INDEX IF NOT EXISTS idx_trades_symbol ON trades(symbol)")
        self._backend.execute("CREATE INDEX IF NOT EXISTS idx_trades_status ON trades(status)")
        self._backend.execute("CREATE INDEX IF NOT EXISTS idx_trades_entry_time ON trades(entry_time)")
        self._backend.execute("CREATE INDEX IF NOT EXISTS idx_positions_symbol ON positions(symbol)")
        self._backend.execute("CREATE INDEX IF NOT EXISTS idx_signals_symbol ON signals(symbol)")
        self._backend.execute("CREATE INDEX IF NOT EXISTS idx_signals_status ON signals(status)")
        self._backend.execute("CREATE INDEX IF NOT EXISTS idx_ohlcv_symbol_tf ON ohlcv_data(symbol, timeframe)")
        
        logger.info("Database schema created/verified")
    
    def close(self):
        """Close database connection."""
        if self._backend:
            self._backend.disconnect()
    
    # ========================================================================
    # TRADE OPERATIONS
    # ========================================================================
    
    def save_trade(self, trade: Trade) -> bool:
        """Save or update trade."""
        try:
            self._backend.execute("""
                INSERT OR REPLACE INTO trades (
                    trade_id, order_id, symbol, side, quantity, entry_price,
                    exit_price, pnl, commission, status, entry_time, exit_time,
                    strategy, signal_id, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                trade.trade_id,
                trade.order_id,
                trade.symbol,
                trade.side,
                trade.quantity,
                trade.entry_price,
                trade.exit_price,
                trade.pnl,
                trade.commission,
                trade.status,
                trade.entry_time.isoformat() if trade.entry_time else None,
                trade.exit_time.isoformat() if trade.exit_time else None,
                trade.strategy,
                trade.signal_id,
                json.dumps(trade.metadata),
            ))
            return True
        except Exception as e:
            logger.error(f"Failed to save trade: {e}")
            return False
    
    def get_trade(self, trade_id: str) -> Optional[Trade]:
        """Get trade by ID."""
        row = self._backend.fetchone(
            "SELECT * FROM trades WHERE trade_id = ?",
            (trade_id,)
        )
        if row:
            return self._row_to_trade(row)
        return None
    
    def get_trades(
        self,
        symbol: Optional[str] = None,
        status: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[Trade]:
        """Get trades with filters."""
        conditions = []
        params = []
        
        if symbol:
            conditions.append("symbol = ?")
            params.append(symbol)
        if status:
            conditions.append("status = ?")
            params.append(status)
        if start_time:
            conditions.append("entry_time >= ?")
            params.append(start_time.isoformat())
        if end_time:
            conditions.append("entry_time <= ?")
            params.append(end_time.isoformat())
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        rows = self._backend.fetchall(
            f"SELECT * FROM trades WHERE {where_clause} ORDER BY entry_time DESC LIMIT ?",
            tuple(params) + (limit,)
        )
        
        return [self._row_to_trade(row) for row in rows]
    
    def _row_to_trade(self, row: Dict) -> Trade:
        """Convert database row to Trade object."""
        return Trade(
            trade_id=row['trade_id'],
            order_id=row['order_id'],
            symbol=row['symbol'],
            side=row['side'],
            quantity=row['quantity'],
            entry_price=row['entry_price'],
            exit_price=row['exit_price'],
            pnl=row['pnl'],
            commission=row['commission'],
            status=row['status'],
            entry_time=datetime.fromisoformat(row['entry_time']) if row['entry_time'] else None,
            exit_time=datetime.fromisoformat(row['exit_time']) if row['exit_time'] else None,
            strategy=row['strategy'],
            signal_id=row['signal_id'],
            metadata=json.loads(row['metadata']) if row['metadata'] else {},
        )
    
    # ========================================================================
    # POSITION OPERATIONS
    # ========================================================================
    
    def save_position(self, position: PositionRecord) -> bool:
        """Save or update position."""
        try:
            self._backend.execute("""
                INSERT OR REPLACE INTO positions (
                    position_id, symbol, side, quantity, entry_price, current_price,
                    unrealized_pnl, realized_pnl, margin_used, leverage, opened_at,
                    updated_at, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                position.position_id,
                position.symbol,
                position.side,
                position.quantity,
                position.entry_price,
                position.current_price,
                position.unrealized_pnl,
                position.realized_pnl,
                position.margin_used,
                position.leverage,
                position.opened_at.isoformat(),
                position.updated_at.isoformat(),
                json.dumps(position.metadata),
            ))
            return True
        except Exception as e:
            logger.error(f"Failed to save position: {e}")
            return False
    
    def get_positions(self, symbol: Optional[str] = None) -> List[PositionRecord]:
        """Get all positions."""
        if symbol:
            rows = self._backend.fetchall(
                "SELECT * FROM positions WHERE symbol = ?",
                (symbol,)
            )
        else:
            rows = self._backend.fetchall("SELECT * FROM positions")
        
        return [self._row_to_position(row) for row in rows]
    
    def delete_position(self, position_id: str) -> bool:
        """Delete position."""
        try:
            self._backend.execute(
                "DELETE FROM positions WHERE position_id = ?",
                (position_id,)
            )
            return True
        except Exception as e:
            logger.error(f"Failed to delete position: {e}")
            return False
    
    def _row_to_position(self, row: Dict) -> PositionRecord:
        """Convert database row to PositionRecord."""
        return PositionRecord(
            position_id=row['position_id'],
            symbol=row['symbol'],
            side=row['side'],
            quantity=row['quantity'],
            entry_price=row['entry_price'],
            current_price=row['current_price'],
            unrealized_pnl=row['unrealized_pnl'],
            realized_pnl=row['realized_pnl'],
            margin_used=row['margin_used'],
            leverage=row['leverage'],
            opened_at=datetime.fromisoformat(row['opened_at']),
            updated_at=datetime.fromisoformat(row['updated_at']),
            metadata=json.loads(row['metadata']) if row['metadata'] else {},
        )
    
    # ========================================================================
    # SIGNAL OPERATIONS
    # ========================================================================
    
    def save_signal(self, signal: SignalRecord) -> bool:
        """Save signal."""
        try:
            self._backend.execute("""
                INSERT OR REPLACE INTO signals (
                    signal_id, symbol, direction, confidence, source, price_at_signal,
                    status, created_at, expires_at, executed_at, result, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                signal.signal_id,
                signal.symbol,
                signal.direction,
                signal.confidence,
                signal.source,
                signal.price_at_signal,
                signal.status,
                signal.created_at.isoformat(),
                signal.expires_at.isoformat() if signal.expires_at else None,
                signal.executed_at.isoformat() if signal.executed_at else None,
                signal.result,
                json.dumps(signal.metadata),
            ))
            return True
        except Exception as e:
            logger.error(f"Failed to save signal: {e}")
            return False
    
    def get_signals(
        self,
        symbol: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
    ) -> List[SignalRecord]:
        """Get signals with filters."""
        conditions = []
        params = []
        
        if symbol:
            conditions.append("symbol = ?")
            params.append(symbol)
        if status:
            conditions.append("status = ?")
            params.append(status)
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        rows = self._backend.fetchall(
            f"SELECT * FROM signals WHERE {where_clause} ORDER BY created_at DESC LIMIT ?",
            tuple(params) + (limit,)
        )
        
        return [self._row_to_signal(row) for row in rows]
    
    def _row_to_signal(self, row: Dict) -> SignalRecord:
        """Convert database row to SignalRecord."""
        return SignalRecord(
            signal_id=row['signal_id'],
            symbol=row['symbol'],
            direction=row['direction'],
            confidence=row['confidence'],
            source=row['source'],
            price_at_signal=row['price_at_signal'],
            status=row['status'],
            created_at=datetime.fromisoformat(row['created_at']),
            expires_at=datetime.fromisoformat(row['expires_at']) if row['expires_at'] else None,
            executed_at=datetime.fromisoformat(row['executed_at']) if row['executed_at'] else None,
            result=row['result'],
            metadata=json.loads(row['metadata']) if row['metadata'] else {},
        )
    
    # ========================================================================
    # SYSTEM STATE OPERATIONS
    # ========================================================================
    
    def save_state(self, component: str, state_data: Dict, state_id: Optional[str] = None) -> bool:
        """Save system state."""
        try:
            import uuid
            state_id = state_id or str(uuid.uuid4())
            now = datetime.utcnow().isoformat()
            
            self._backend.execute("""
                INSERT OR REPLACE INTO system_state (
                    state_id, component, state_data, version, created_at, updated_at
                ) VALUES (?, ?, ?, 1, ?, ?)
            """, (
                state_id,
                component,
                json.dumps(state_data),
                now,
                now,
            ))
            return True
        except Exception as e:
            logger.error(f"Failed to save state: {e}")
            return False
    
    def get_state(self, component: str) -> Optional[Dict]:
        """Get latest state for component."""
        row = self._backend.fetchone(
            "SELECT * FROM system_state WHERE component = ? ORDER BY updated_at DESC LIMIT 1",
            (component,)
        )
        if row:
            return json.loads(row['state_data'])
        return None
    
    # ========================================================================
    # PERFORMANCE METRICS
    # ========================================================================
    
    def save_metric(self, metric: PerformanceMetric) -> bool:
        """Save performance metric."""
        try:
            self._backend.execute("""
                INSERT INTO performance_metrics (
                    metric_id, metric_name, metric_value, period, timestamp, metadata
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                metric.metric_id,
                metric.metric_name,
                metric.metric_value,
                metric.period,
                metric.timestamp.isoformat(),
                json.dumps(metric.metadata),
            ))
            return True
        except Exception as e:
            logger.error(f"Failed to save metric: {e}")
            return False
    
    def get_metrics(
        self,
        metric_name: Optional[str] = None,
        period: Optional[str] = None,
        start_time: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[PerformanceMetric]:
        """Get performance metrics."""
        conditions = []
        params = []
        
        if metric_name:
            conditions.append("metric_name = ?")
            params.append(metric_name)
        if period:
            conditions.append("period = ?")
            params.append(period)
        if start_time:
            conditions.append("timestamp >= ?")
            params.append(start_time.isoformat())
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        rows = self._backend.fetchall(
            f"SELECT * FROM performance_metrics WHERE {where_clause} ORDER BY timestamp DESC LIMIT ?",
            tuple(params) + (limit,)
        )
        
        return [PerformanceMetric(
            metric_id=row['metric_id'],
            metric_name=row['metric_name'],
            metric_value=row['metric_value'],
            period=row['period'],
            timestamp=datetime.fromisoformat(row['timestamp']),
            metadata=json.loads(row['metadata']) if row['metadata'] else {},
        ) for row in rows]
    
    # ========================================================================
    # OHLCV DATA
    # ========================================================================
    
    def save_ohlcv(
        self,
        symbol: str,
        timeframe: str,
        data: List[Dict],
    ) -> int:
        """Save OHLCV data."""
        try:
            params = [
                (symbol, timeframe, d['timestamp'], d['open'], d['high'], d['low'], d['close'], d['volume'])
                for d in data
            ]
            
            self._backend.executemany("""
                INSERT OR REPLACE INTO ohlcv_data (
                    symbol, timeframe, timestamp, open, high, low, close, volume
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, params)
            
            return len(params)
        except Exception as e:
            logger.error(f"Failed to save OHLCV data: {e}")
            return 0
    
    def get_ohlcv(
        self,
        symbol: str,
        timeframe: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 1000,
    ) -> List[Dict]:
        """Get OHLCV data."""
        conditions = ["symbol = ?", "timeframe = ?"]
        params = [symbol, timeframe]
        
        if start_time:
            conditions.append("timestamp >= ?")
            params.append(start_time.isoformat())
        if end_time:
            conditions.append("timestamp <= ?")
            params.append(end_time.isoformat())
        
        where_clause = " AND ".join(conditions)
        
        rows = self._backend.fetchall(
            f"SELECT * FROM ohlcv_data WHERE {where_clause} ORDER BY timestamp ASC LIMIT ?",
            tuple(params) + (limit,)
        )
        
        return [{
            'timestamp': row['timestamp'],
            'open': row['open'],
            'high': row['high'],
            'low': row['low'],
            'close': row['close'],
            'volume': row['volume'],
        } for row in rows]
    
    # ========================================================================
    # STATISTICS
    # ========================================================================
    
    def get_statistics(self) -> Dict:
        """Get database statistics."""
        stats = {}
        
        # Trade stats
        row = self._backend.fetchone("SELECT COUNT(*) as count FROM trades")
        stats['total_trades'] = row['count'] if row else 0
        
        row = self._backend.fetchone("SELECT COUNT(*) as count FROM trades WHERE status = 'open'")
        stats['open_trades'] = row['count'] if row else 0
        
        row = self._backend.fetchone("SELECT SUM(pnl) as total FROM trades WHERE pnl IS NOT NULL")
        stats['total_pnl'] = row['total'] if row and row['total'] else 0
        
        # Position stats
        row = self._backend.fetchone("SELECT COUNT(*) as count FROM positions")
        stats['total_positions'] = row['count'] if row else 0
        
        # Signal stats
        row = self._backend.fetchone("SELECT COUNT(*) as count FROM signals")
        stats['total_signals'] = row['count'] if row else 0
        
        row = self._backend.fetchone("SELECT COUNT(*) as count FROM signals WHERE status = 'active'")
        stats['active_signals'] = row['count'] if row else 0
        
        return stats


# ============================================================================
# GLOBAL INSTANCE
# ============================================================================

_persistence_manager: Optional[PersistenceManager] = None


def get_persistence_manager(config: Optional[DatabaseConfig] = None) -> PersistenceManager:
    """Get global persistence manager instance."""
    global _persistence_manager
    if _persistence_manager is None:
        _persistence_manager = PersistenceManager(config)
        _persistence_manager.initialize()
    return _persistence_manager


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    'DatabaseConfig', 'Trade', 'PositionRecord', 'SignalRecord',
    'SystemState', 'PerformanceMetric', 'DatabaseBackend',
    'SQLiteBackend', 'PostgreSQLBackend', 'PersistenceManager',
    'get_persistence_manager',
]
