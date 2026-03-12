"""
Time-Series Database Manager
Optimized for high-performance market data storage and retrieval
"""

import asyncio
import aiosqlite
import numpy as np
import pandas as pd
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timedelta
import logging
from pathlib import Path
import pyarrow as pa
import pyarrow.parquet as pq
from concurrent.futures import ThreadPoolExecutor
import json
import redis.asyncio
import numpy
import pandas

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

class TimeSeriesDB:
    """
    High-performance time-series database optimized for market data
    Features:
    - Async I/O operations
    - Efficient data compression
    - Multi-level caching
    - Partitioned storage
    - Auto-optimization
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.db_path = config.get('db_path', 'market_data.db')
        self.parquet_dir = config.get('parquet_dir', 'market_data_archive')
        
        # Ensure directories exist
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        Path(self.parquet_dir).mkdir(parents=True, exist_ok=True)
        
        # Connection pool
        self.pool = None
        
        # Redis cache
        self.redis = None
        
        # Memory cache
        self.cache: Dict[str, Any] = {}
        self.cache_ttl: Dict[str, datetime] = {}
        
        # Thread pool for background tasks
        self.executor = ThreadPoolExecutor(
            max_workers=config.get('max_workers', 4)
        )
        
        # Performance metrics
        self.metrics = {
            'queries': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'write_ops': 0,
            'compression_ratio': 0.0
        }
        
        logger.info("TimeSeriesDB initialized")
    
    async def initialize(self):
        """Initialize database and connections"""
        # Initialize SQLite connection pool
        self.pool = await aiosqlite.connect(self.db_path)
        await self._create_tables()
        
        # Initialize Redis connection
        if self.config.get('use_redis', True):
            self.redis = await redis.asyncio.from_url(
                self.config.get('redis_url', 'redis://localhost'),
                decode_responses=True
            )
        
        # Start background optimization task
        asyncio.create_task(self._background_optimization())
        
        logger.info("Database connections initialized")
    
    async def _create_tables(self):
        """Create optimized tables for time-series data"""
        async with self.pool.cursor() as cursor:
            # Market data table with partitioning
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
        
        await self.pool.commit()
    
    async def write_market_data(self, 
                              data: Union[Dict, pd.DataFrame], 
                              symbol: str,
                              timeframe: str):
        """Write market data with automatic partitioning"""
        try:
            if isinstance(data, dict):
                df = pd.DataFrame([data])
            else:
                df = data
            
            # Convert timestamp if needed
            if 'timestamp' not in df.columns:
                df['timestamp'] = datetime.now()
            
            # Write to database
            async with self.pool.cursor() as cursor:
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
            
            await self.pool.commit()
            
            # Update cache
            cache_key = f"{symbol}_{timeframe}_latest"
            await self._update_cache(cache_key, df.iloc[-1].to_dict())
            
            # Update metrics
            self.metrics['write_ops'] += len(df)
            
            # Archive old data if needed
            await self._check_archival_needs(symbol, timeframe)
            
        except Exception as e:
            logger.error(f"Error writing market data: {e}")
            raise
    
    async def get_market_data(self,
                            symbol: str,
                            timeframe: str,
                            start_time: Optional[datetime] = None,
                            end_time: Optional[datetime] = None,
                            limit: Optional[int] = None) -> pd.DataFrame:
        """Get market data with caching"""
        cache_key = f"{symbol}_{timeframe}_{start_time}_{end_time}"
        
        # Try cache first
        cached_data = await self._get_from_cache(cache_key)
        if cached_data is not None:
            self.metrics['cache_hits'] += 1
            return pd.DataFrame(cached_data)
        
        self.metrics['cache_misses'] += 1
        
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
        
        # Execute query
        async with self.pool.cursor() as cursor:
            await cursor.execute(query, params)
            rows = await cursor.fetchall()
        
        # Convert to DataFrame
        df = pd.DataFrame(rows, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        
        # Cache results
        await self._update_cache(cache_key, df.to_dict('records'))
        
        self.metrics['queries'] += 1
        return df
    
    async def _get_from_cache(self, key: str) -> Optional[Any]:
        """Get data from cache hierarchy"""
        # Check memory cache
        if key in self.cache and datetime.now() < self.cache_ttl.get(key, datetime.min):
            return self.cache[key]
        
        # Check Redis cache
        if self.redis:
            cached = await self.redis.get(key)
            if cached:
                data = json.loads(cached)
                # Update memory cache
                self.cache[key] = data
                self.cache_ttl[key] = datetime.now() + timedelta(minutes=5)
                return data
        
        return None
    
    async def _update_cache(self, key: str, data: Any):
        """Update cache hierarchy"""
        # Update memory cache
        self.cache[key] = data
        self.cache_ttl[key] = datetime.now() + timedelta(minutes=5)
        
        # Update Redis cache
        if self.redis:
            await self.redis.set(
                key,
                json.dumps(data),
                expire=3600  # 1 hour TTL
            )
    
    async def _check_archival_needs(self, symbol: str, timeframe: str):
        """Check if data needs to be archived"""
        async with self.pool.cursor() as cursor:
            # Check oldest data
            await cursor.execute(
                """
                SELECT MIN(timestamp) FROM market_data
                WHERE symbol = ? AND timeframe = ?
                """,
                (symbol, timeframe)
            )
            oldest = await cursor.fetchone()
            
            if oldest and oldest[0]:
                oldest_date = datetime.fromisoformat(oldest[0])
                if datetime.now() - oldest_date > timedelta(days=30):
                    # Archive old data
                    await self._archive_old_data(symbol, timeframe, oldest_date)
    
    async def _archive_old_data(self, symbol: str, timeframe: str, before_date: datetime):
        """Archive old data to Parquet files"""
        async with self.pool.cursor() as cursor:
            # Get data to archive
            await cursor.execute(
                """
                SELECT * FROM market_data
                WHERE symbol = ? AND timeframe = ? AND timestamp < ?
                """,
                (symbol, timeframe, before_date)
            )
            rows = await cursor.fetchall()
            
            if rows:
                # Convert to DataFrame
                df = pd.DataFrame(rows, columns=['id', 'timestamp', 'symbol', 'timeframe', 
                                               'open', 'high', 'low', 'close', 'volume', 
                                               'partition_key'])
                
                # Save to Parquet
                parquet_path = Path(self.parquet_dir) / f"{symbol}_{timeframe}_{before_date.strftime('%Y%m')}.parquet"
                
                await asyncio.get_event_loop().run_in_executor(
                    self.executor,
                    pq.write_table,
                    pa.Table.from_pandas(df),
                    parquet_path
                )
                
                # Delete archived data
                await cursor.execute(
                    """
                    DELETE FROM market_data
                    WHERE symbol = ? AND timeframe = ? AND timestamp < ?
                    """,
                    (symbol, timeframe, before_date)
                )
                
                await self.pool.commit()
                
                logger.info(f"Archived data to {parquet_path}")
    
    async def _background_optimization(self):
        """Background task for database optimization"""
        while True:
            try:
                await asyncio.sleep(3600)  # Run every hour
                
                async with self.pool.cursor() as cursor:
                    # Analyze tables
                    await cursor.execute("ANALYZE market_data")
                    
                    # Optimize indexes
                    await cursor.execute("REINDEX idx_market_data_lookup")
                    await cursor.execute("REINDEX idx_market_data_partition")
                    
                    # Vacuum database
                    await cursor.execute("VACUUM")
                
                await self.pool.commit()
                
                logger.info("Database optimization completed")
                
            except Exception as e:
                logger.error(f"Error in background optimization: {e}")
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get database performance metrics"""
        return {
            'queries_per_second': self.metrics['queries'] / 3600,
            'cache_hit_ratio': self.metrics['cache_hits'] / 
                             (self.metrics['cache_hits'] + self.metrics['cache_misses'])
                             if (self.metrics['cache_hits'] + self.metrics['cache_misses']) > 0 
                             else 0,
            'write_ops_per_second': self.metrics['write_ops'] / 3600,
            'compression_ratio': self.metrics['compression_ratio']
        }
    
    async def cleanup(self):
        """Cleanup database connections"""
        if self.pool:
            await self.pool.close()
        
        if self.redis:
            await self.redis.aclose()
        
        self.executor.shutdown()
        logger.info("Database connections closed")
