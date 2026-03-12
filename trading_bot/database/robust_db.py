"""
Robust Database Module with Fallback Mechanisms
Ensures database operations are resilient to failures
"""

import asyncio
import aiosqlite
import sqlite3
import logging
import os
import json
import pandas as pd
import numpy as np
from typing import Any, Dict, List, Optional, Tuple, Union
from datetime import datetime, timedelta
from pathlib import Path
import traceback
import platform
import tempfile
import shutil
import time
import redis.asyncio
from contextlib import asynccontextmanager
from typing import Set
import numpy
import pandas

logger = logging.getLogger(__name__)


class RobustDatabaseManager:
    """
    Robust database manager with fallback mechanisms
    Features:
    - Automatic fallback to local SQLite if Redis unavailable
    - Schema version checking and migration
    - Automatic recovery from corruption
    - Connection pooling and retry logic
    - Transaction safety
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        
        # Primary database path
        self.db_path = config.get('db_path', 'market_data.db')
        
        # Backup database path
        self.backup_dir = config.get('backup_dir', 'db_backups')
        Path(self.backup_dir).mkdir(parents=True, exist_ok=True)
        
        # Redis configuration
        self.use_redis = config.get('use_redis', True)
        self.redis_url = config.get('redis_url', 'redis://localhost')
        self.redis_ttl = config.get('redis_ttl', 3600)  # 1 hour
        
        # Connection pools
        self.sqlite_pool = None
        self.redis = None
        
        # Schema version
        self.schema_version = config.get('schema_version', 1)
        
        # Feature flags
        self.features = config.get('features', {
            'use_redis': True,
            'use_backup': True,
            'auto_migrate': True,
            'auto_recover': True
        })
        
        # Retry configuration
        self.max_retries = config.get('max_retries', 3)
        self.retry_delay = config.get('retry_delay', 0.5)  # seconds
        
        # Status tracking
        self.status = {
            'sqlite_available': True,
            'redis_available': False,
            'last_backup': None,
            'recovery_attempts': 0,
            'migration_status': None
        }
        
        logger.info("Robust database manager initialized")
    
    async def initialize(self):
        """Initialize database connections with fallbacks"""
        try:
            # Try to initialize SQLite
            await self._initialize_sqlite()
        except Exception as e:
            logger.error(f"Failed to initialize SQLite: {e}")
            self.status['sqlite_available'] = False
            
            # Try to recover
            if self.features['auto_recover']:
                await self._attempt_recovery()
        
        # Try to initialize Redis if enabled
        if self.features['use_redis']:
            try:
                await self._initialize_redis()
                self.status['redis_available'] = True
            except Exception as e:
                logger.warning(f"Redis unavailable, falling back to SQLite only: {e}")
                self.status['redis_available'] = False
        
        logger.info(f"Database initialization complete. Status: {self.status}")
    
    async def _initialize_sqlite(self):
        """Initialize SQLite database with schema validation"""
        # Check if database file exists
        db_exists = Path(self.db_path).exists()
        
        # Connect to database
        self.sqlite_pool = await aiosqlite.connect(self.db_path)
        
        # Enable foreign keys
        await self.sqlite_pool.execute("PRAGMA foreign_keys = ON")
        
        # Create tables if needed
        await self._create_tables()
        
        # Check schema version
        if db_exists:
            current_version = await self._get_schema_version()
            if current_version != self.schema_version:
                if self.features['auto_migrate']:
                    await self._migrate_schema(current_version, self.schema_version)
                else:
                    logger.warning(f"Schema version mismatch: {current_version} vs {self.schema_version}")
        else:
            # Set initial schema version
            await self._set_schema_version(self.schema_version)
        
        # Create backup if needed
        if self.features['use_backup'] and db_exists:
            await self._create_backup()
    
    async def _initialize_redis(self):
        """Initialize Redis connection"""
        self.redis = await redis.asyncio.from_url(
            self.redis_url,
            decode_responses=True
        )
        # Test connection
        await self.redis.ping()
    
    async def _create_tables(self):
        """Create database tables"""
        async with self.sqlite_pool.cursor() as cursor:
            # Metadata table
            await cursor.execute("""
                CREATE TABLE IF NOT EXISTS metadata (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Market data table
            await cursor.execute("""
                CREATE TABLE IF NOT EXISTS market_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME NOT NULL,
                    symbol TEXT NOT NULL,
                    timeframe TEXT NOT NULL,
                    open REAL,
                    high REAL,
                    low REAL,
                    close REAL,
                    volume REAL,
                    partition_key TEXT GENERATED ALWAYS AS (
                        strftime('%Y%m', timestamp) || '_' || timeframe || '_' || symbol
                    ) STORED
                )
            """)
            
            # Create indexes
            await cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_market_data_lookup ON market_data(symbol, timeframe, timestamp)"
            )
            await cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_market_data_partition ON market_data(partition_key, timestamp)"
            )
            
            # Trades table
            await cursor.execute("""
                CREATE TABLE IF NOT EXISTS trades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    trade_id TEXT UNIQUE NOT NULL,
                    symbol TEXT NOT NULL,
                    direction TEXT NOT NULL,
                    entry_price REAL NOT NULL,
                    exit_price REAL,
                    size REAL NOT NULL,
                    entry_time DATETIME NOT NULL,
                    exit_time DATETIME,
                    pnl REAL,
                    status TEXT NOT NULL,
                    metadata TEXT
                )
            """)
            
            # Signals table
            await cursor.execute("""
                CREATE TABLE IF NOT EXISTS signals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    signal_id TEXT UNIQUE NOT NULL,
                    timestamp DATETIME NOT NULL,
                    symbol TEXT NOT NULL,
                    signal_type TEXT NOT NULL,
                    direction TEXT NOT NULL,
                    strength REAL NOT NULL,
                    timeframe TEXT NOT NULL,
                    metadata TEXT
                )
            """)
            
            # Performance metrics table
            await cursor.execute("""
                CREATE TABLE IF NOT EXISTS performance_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME NOT NULL,
                    metric_type TEXT NOT NULL,
                    component TEXT NOT NULL,
                    value REAL NOT NULL,
                    metadata TEXT
                )
            """)
        
        await self.sqlite_pool.commit()
    
    async def _get_schema_version(self) -> int:
        """Get current schema version from database"""
        async with self.sqlite_pool.cursor() as cursor:
            await cursor.execute("SELECT value FROM metadata WHERE key = 'schema_version'")
            result = await cursor.fetchone()
            
            if result:
                return int(result[0])
            else:
                # No version found, assume version 1
                return 1
    
    async def _set_schema_version(self, version: int):
        """Set schema version in database"""
        async with self.sqlite_pool.cursor() as cursor:
            await cursor.execute(
                "INSERT OR REPLACE INTO metadata (key, value, updated_at) VALUES (?, ?, ?)",
                ("schema_version", str(version), datetime.now())
            )
        await self.sqlite_pool.commit()
    
    async def _migrate_schema(self, from_version: int, to_version: int):
        """Migrate database schema"""
        logger.info(f"Migrating schema from version {from_version} to {to_version}")
        
        # Create backup before migration
        await self._create_backup()
        
        try:
            # Apply migrations sequentially
            for version in range(from_version + 1, to_version + 1):
                migration_method = getattr(self, f"_migrate_to_v{version}", None)
                if migration_method:
                    await migration_method()
                    logger.info(f"Migrated to schema version {version}")
                else:
                    logger.warning(f"No migration method found for version {version}")
            
            # Update schema version
            await self._set_schema_version(to_version)
            self.status['migration_status'] = "success"
            
        except Exception as e:
            logger.error(f"Schema migration failed: {e}")
            self.status['migration_status'] = "failed"
            # Restore from backup if migration fails
            await self._restore_from_backup()
            raise
    
    async def _create_backup(self):
        """Create database backup"""
        if not self.features['use_backup']:
            return
        try:
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = os.path.join(self.backup_dir, f"backup_{timestamp}.db")
            
            # Close connection temporarily
            await self.sqlite_pool.close()
            
            # Copy database file
            shutil.copy2(self.db_path, backup_path)
            
            # Reconnect
            self.sqlite_pool = await aiosqlite.connect(self.db_path)
            
            self.status['last_backup'] = timestamp
            logger.info(f"Created database backup at {backup_path}")
            
        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            # Ensure connection is reopened
            if self.sqlite_pool is None or self.sqlite_pool.closed:
                self.sqlite_pool = await aiosqlite.connect(self.db_path)
    
    async def _restore_from_backup(self):
        """Restore database from latest backup"""
        if not self.features['use_backup']:
            return
        try:
            
            # Find latest backup
            backup_files = list(Path(self.backup_dir).glob("backup_*.db"))
            if not backup_files:
                logger.error("No backup files found")
                return False
                
            latest_backup = max(backup_files, key=os.path.getctime)
            
            # Close connection
            await self.sqlite_pool.close()
            
            # Restore from backup
            shutil.copy2(latest_backup, self.db_path)
            
            # Reconnect
            self.sqlite_pool = await aiosqlite.connect(self.db_path)
            
            logger.info(f"Restored database from backup {latest_backup}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to restore from backup: {e}")
            # Ensure connection is reopened
            if self.sqlite_pool is None or self.sqlite_pool.closed:
                self.sqlite_pool = await aiosqlite.connect(self.db_path)
            return False
    
    async def _attempt_recovery(self):
        """Attempt to recover from database corruption"""
        self.status['recovery_attempts'] += 1
        
        logger.warning(f"Attempting database recovery (attempt {self.status['recovery_attempts']})")
        
        # Try to restore from backup first
        if await self._restore_from_backup():
            self.status['sqlite_available'] = True
            return
        try:
        
        # If no backup or restore failed, create a new database
            # Rename corrupted database
            corrupted_path = f"{self.db_path}.corrupted"
            if os.path.exists(self.db_path):
                os.rename(self.db_path, corrupted_path)
                logger.warning(f"Renamed corrupted database to {corrupted_path}")
            
            # Create new database
            self.sqlite_pool = await aiosqlite.connect(self.db_path)
            await self._create_tables()
            await self._set_schema_version(self.schema_version)
            
            self.status['sqlite_available'] = True
            logger.info("Created new database after recovery attempt")
            
        except Exception as e:
            logger.error(f"Recovery failed: {e}")
            self.status['sqlite_available'] = False
    
    @asynccontextmanager
    async def transaction(self):
        """Context manager for database transactions with retry logic"""
        for attempt in range(self.max_retries):
            try:
                async with self.sqlite_pool.cursor() as cursor:
                    await cursor.execute("BEGIN TRANSACTION")
                    try:
                        yield cursor
                        await self.sqlite_pool.commit()
                        break
                    except Exception as e:
                        await self.sqlite_pool.rollback()
                        logger.error(f"Transaction failed (attempt {attempt+1}/{self.max_retries}): {e}")
                        if attempt == self.max_retries - 1:
                            raise
            except Exception as e:
                if attempt == self.max_retries - 1:
                    logger.error(f"All transaction attempts failed: {e}")
                    raise
                await asyncio.sleep(self.retry_delay * (2 ** attempt))  # Exponential backoff
    
    async def write_market_data(self, 
                              data: Union[Dict, pd.DataFrame], 
                              symbol: str,
                              timeframe: str):
        """Write market data with caching and fallbacks"""
        try:
            # Convert to DataFrame if needed
            if isinstance(data, dict):
                df = pd.DataFrame([data])
            else:
                df = data
            
            # Ensure timestamp column exists
            if 'timestamp' not in df.columns:
                df['timestamp'] = datetime.now()
            
            # Try to write to SQLite
            if self.status['sqlite_available']:
                try:
                    async with self.transaction() as cursor:
                        await cursor.executemany(
                            """
                            INSERT INTO market_data (timestamp, symbol, timeframe, open, high, low, close, volume)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                            """,
                            [
                                (
                                    row.timestamp,
                                    symbol,
                                    timeframe,
                                    row.get('open', row.get('price', 0)),
                                    row.get('high', row.get('price', 0)),
                                    row.get('low', row.get('price', 0)),
                                    row.get('close', row.get('price', 0)),
                                    row.get('volume', 0)
                                )
                                for _, row in df.iterrows()
                            ]
                        )
                except Exception as e:
                    logger.error(f"Failed to write to SQLite: {e}")
                    if self.features['auto_recover']:
                        await self._attempt_recovery()
            
            # Try to write to Redis if available
            if self.status['redis_available']:
                try:
                    # Store latest data point
                    latest = df.iloc[-1].to_dict()
                    cache_key = f"{symbol}_{timeframe}_latest"
                    await self.redis.set(
                        cache_key,
                        json.dumps(latest, default=str),
                        ex=self.redis_ttl
                    )
                except Exception as e:
                    logger.warning(f"Failed to write to Redis: {e}")
                    self.status['redis_available'] = False
            
        except Exception as e:
            logger.error(f"Error writing market data: {e}")
            raise
    
    async def get_market_data(self,
                            symbol: str,
                            timeframe: str,
                            start_time: Optional[datetime] = None,
                            end_time: Optional[datetime] = None,
                            limit: Optional[int] = None) -> pd.DataFrame:
        """Get market data with caching and fallbacks"""
        cache_key = f"{symbol}_{timeframe}_{start_time}_{end_time}_{limit}"
        
        # Try Redis cache first if available
        if self.status['redis_available']:
            try:
                cached_data = await self.redis.get(cache_key)
                if cached_data:
                    return pd.DataFrame(json.loads(cached_data))
            except Exception as e:
                logger.warning(f"Redis cache retrieval failed: {e}")
                self.status['redis_available'] = False
        
        # Fall back to SQLite
        if not self.status['sqlite_available']:
            logger.error("No database available for query")
            return pd.DataFrame()
        try:
        
            # Build query
            query = """
                SELECT timestamp, open, high, low, close, volume
                FROM market_data
                WHERE symbol = ? AND timeframe = ?
            """
            params = [symbol, timeframe]
            
            if start_time:
                query += " AND timestamp >= ?"
                params.append(start_time)
            if end_time:
                query += " AND timestamp <= ?"
                params.append(end_time)
            
            query += " ORDER BY timestamp"
            if limit:
                query += f" LIMIT {limit}"
            
            # Execute query with retry logic
            for attempt in range(self.max_retries):
                try:
                    async with self.sqlite_pool.cursor() as cursor:
                        await cursor.execute(query, params)
                        rows = await cursor.fetchall()
                        
                        # Convert to DataFrame
                        df = pd.DataFrame(rows, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                        
                        # Cache in Redis if available
                        if self.status['redis_available'] and not df.empty:
                            try:
                                await self.redis.set(
                                    cache_key,
                                    json.dumps(df.to_dict('records'), default=str),
                                    ex=self.redis_ttl
                                )
                            except Exception as e:
                                logger.warning(f"Redis caching failed: {e}")
                        
                        return df
                        
                except Exception as e:
                    if attempt == self.max_retries - 1:
                        logger.error(f"All query attempts failed: {e}")
                        return pd.DataFrame()
                    await asyncio.sleep(self.retry_delay * (2 ** attempt))
            
            return pd.DataFrame()
            
        except Exception as e:
            logger.error(f"Error getting market data: {e}")
            return pd.DataFrame()
    
    async def write_trade(self, trade_data: Dict[str, Any]):
        """Write trade data to database"""
        if not self.status['sqlite_available']:
            logger.error("SQLite database unavailable for writing trade")
            return False
        try:
        
            async with self.transaction() as cursor:
                await cursor.execute(
                    """
                    INSERT INTO trades (
                        trade_id, symbol, direction, entry_price, exit_price,
                        size, entry_time, exit_time, pnl, status, metadata
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(trade_id) DO UPDATE SET
                        exit_price = excluded.exit_price,
                        exit_time = excluded.exit_time,
                        pnl = excluded.pnl,
                        status = excluded.status,
                        metadata = excluded.metadata
                    """,
                    (
                        trade_data['trade_id'],
                        trade_data['symbol'],
                        trade_data['direction'],
                        trade_data['entry_price'],
                        trade_data.get('exit_price'),
                        trade_data['size'],
                        trade_data['entry_time'],
                        trade_data.get('exit_time'),
                        trade_data.get('pnl'),
                        trade_data['status'],
                        json.dumps(trade_data.get('metadata', {}))
                    )
                )
            return True
        except Exception as e:
            logger.error(f"Error writing trade: {e}")
            return False
    
    async def get_trades(self, 
                       symbol: Optional[str] = None,
                       status: Optional[str] = None,
                       start_time: Optional[datetime] = None,
                       end_time: Optional[datetime] = None,
                       limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get trades with filtering"""
        if not self.status['sqlite_available']:
            logger.error("SQLite database unavailable for getting trades")
            return []
        try:
        
            query = "SELECT * FROM trades WHERE 1=1"
            params = []
            
            if symbol:
                query += " AND symbol = ?"
                params.append(symbol)
            
            if status:
                query += " AND status = ?"
                params.append(status)
            
            if start_time:
                query += " AND entry_time >= ?"
                params.append(start_time)
            
            if end_time:
                query += " AND entry_time <= ?"
                params.append(end_time)
            
            query += " ORDER BY entry_time DESC"
            
            if limit:
                query += f" LIMIT {limit}"
            
            async with self.sqlite_pool.cursor() as cursor:
                await cursor.execute(query, params)
                rows = await cursor.fetchall()
                
                # Get column names
                column_names = [description[0] for description in cursor.description]
                
                # Convert to list of dicts
                trades = []
                for row in rows:
                    trade = dict(zip(column_names, row))
                    if trade['metadata']:
                        trade['metadata'] = json.loads(trade['metadata'])
                    else:
                        trade['metadata'] = {}
                    trades.append(trade)
                
                return trades
                
        except Exception as e:
            logger.error(f"Error getting trades: {e}")
            return []
    
    async def write_performance_metric(self, 
                                     metric_type: str,
                                     component: str,
                                     value: float,
                                     metadata: Optional[Dict[str, Any]] = None):
        """Write performance metric to database"""
        if not self.status['sqlite_available']:
            logger.error("SQLite database unavailable for writing metric")
            return False
        try:
        
            async with self.transaction() as cursor:
                await cursor.execute(
                    """
                    INSERT INTO performance_metrics (
                        timestamp, metric_type, component, value, metadata
                    ) VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        datetime.now(),
                        metric_type,
                        component,
                        value,
                        json.dumps(metadata or {})
                    )
                )
            return True
        except Exception as e:
            logger.error(f"Error writing performance metric: {e}")
            return False
    
    async def get_performance_metrics(self,
                                    metric_type: Optional[str] = None,
                                    component: Optional[str] = None,
                                    start_time: Optional[datetime] = None,
                                    end_time: Optional[datetime] = None) -> pd.DataFrame:
        """Get performance metrics with filtering"""
        if not self.status['sqlite_available']:
            logger.error("SQLite database unavailable for getting metrics")
            return pd.DataFrame()
        try:
        
            query = "SELECT * FROM performance_metrics WHERE 1=1"
            params = []
            
            if metric_type:
                query += " AND metric_type = ?"
                params.append(metric_type)
            
            if component:
                query += " AND component = ?"
                params.append(component)
            
            if start_time:
                query += " AND timestamp >= ?"
                params.append(start_time)
            
            if end_time:
                query += " AND timestamp <= ?"
                params.append(end_time)
            
            query += " ORDER BY timestamp"
            
            async with self.sqlite_pool.cursor() as cursor:
                await cursor.execute(query, params)
                rows = await cursor.fetchall()
                
                # Get column names
                column_names = [description[0] for description in cursor.description]
                
                # Convert to DataFrame
                df = pd.DataFrame(rows, columns=column_names)
                
                # Parse metadata JSON
                if 'metadata' in df.columns and not df.empty:
                    df['metadata'] = df['metadata'].apply(lambda x: json.loads(x) if x else {})
                
                return df
                
        except Exception as e:
            logger.error(f"Error getting performance metrics: {e}")
            return pd.DataFrame()
    
    async def get_database_status(self) -> Dict[str, Any]:
        """Get database status information"""
        status = self.status.copy()
        
        if self.status['sqlite_available']:
            try:
                async with self.sqlite_pool.cursor() as cursor:
                    # Get row counts
                    tables = ['market_data', 'trades', 'signals', 'performance_metrics']
                    row_counts = {}
                    
                    for table in tables:
                        await cursor.execute(f"SELECT COUNT(*) FROM {table}")
                        count = await cursor.fetchone()
                        row_counts[table] = count[0] if count else 0
                    
                    status['row_counts'] = row_counts
                    
                    # Get database size
                    await cursor.execute("PRAGMA page_count")
                    page_count = await cursor.fetchone()
                    
                    await cursor.execute("PRAGMA page_size")
                    page_size = await cursor.fetchone()
                    
                    if page_count and page_size:
                        status['database_size_mb'] = (page_count[0] * page_size[0]) / (1024 * 1024)
                    
                    # Get schema version
                    status['schema_version'] = await self._get_schema_version()
                    
            except Exception as e:
                logger.error(f"Error getting database status: {e}")
        
        if self.status['redis_available']:
            try:
                # Get Redis info
                info = await self.redis.info()
                status['redis_info'] = {
                    'version': info.get('redis_version'),
                    'used_memory_human': info.get('used_memory_human'),
                    'connected_clients': info.get('connected_clients'),
                    'uptime_in_days': info.get('uptime_in_days')
                }
            except Exception as e:
                logger.warning(f"Error getting Redis status: {e}")
        
        return status
    
    async def cleanup(self):
        """Cleanup database connections"""
        if self.sqlite_pool:
            await self.sqlite_pool.close()
        
        if self.redis:
            await self.redis.aclose()
        
        logger.info("Database connections closed")
