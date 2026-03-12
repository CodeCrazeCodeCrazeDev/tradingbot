"""
AlphaAlgo Storage Layer
=======================
Persistent storage for market events.
ClickHouse for hot data, S3 for cold archival.
"""

from __future__ import annotations

import asyncio
import logging
import time
import json
import gzip
import struct
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple, Union
from datetime import datetime, date, timedelta
from pathlib import Path
from collections import deque
import threading
from abc import ABC, abstractmethod

from .schema import MarketEvent, MarketEventType, EventEnvelope

logger = logging.getLogger(__name__)


@dataclass
class StorageConfig:
    """Configuration for storage layer"""
    # ClickHouse
    clickhouse_host: str = 'localhost'
    clickhouse_port: int = 9000
    clickhouse_database: str = 'alphaalgo'
    clickhouse_user: str = 'default'
    clickhouse_password: str = ''
    
    # S3
    s3_bucket: str = 'alphaalgo-market-data'
    s3_region: str = 'us-east-1'
    s3_access_key: str = ''
    s3_secret_key: str = ''
    s3_endpoint: str = ''  # For MinIO or other S3-compatible
    
    # Local fallback
    local_data_dir: str = './market_data'
    
    # Batching
    batch_size: int = 10000
    batch_timeout_ms: int = 1000
    
    # Compression
    compression: str = 'lz4'  # 'none', 'gzip', 'lz4', 'zstd'
    
    # Retention
    hot_retention_days: int = 7      # Keep in ClickHouse
    warm_retention_days: int = 90    # Keep in S3 standard
    cold_retention_days: int = 365   # Move to S3 Glacier
    
    # Partitioning
    partition_by: str = 'day'  # 'hour', 'day', 'week'


# ClickHouse table schemas
CLICKHOUSE_SCHEMAS = {
    'trades': """
        CREATE TABLE IF NOT EXISTS {database}.trades (
            event_id String,
            symbol LowCardinality(String),
            exchange LowCardinality(String),
            exchange_ts DateTime64(9),
            receive_ts DateTime64(9),
            process_ts DateTime64(9),
            sequence_num Int64,
            local_sequence Int64,
            quality_flags UInt8,
            price Float64,
            size Float64,
            side Enum8('UNKNOWN' = 0, 'BUY' = 1, 'SELL' = 2),
            trade_id String,
            conditions Array(UInt8),
            date Date MATERIALIZED toDate(exchange_ts)
        )
        ENGINE = MergeTree()
        PARTITION BY toYYYYMMDD(exchange_ts)
        ORDER BY (exchange, symbol, exchange_ts, sequence_num)
        TTL exchange_ts + INTERVAL {retention_days} DAY
        SETTINGS index_granularity = 8192
    """,
    
    'quotes': """
        CREATE TABLE IF NOT EXISTS {database}.quotes (
            event_id String,
            symbol LowCardinality(String),
            exchange LowCardinality(String),
            exchange_ts DateTime64(9),
            receive_ts DateTime64(9),
            process_ts DateTime64(9),
            sequence_num Int64,
            local_sequence Int64,
            quality_flags UInt8,
            bid_price Float64,
            bid_size Float64,
            ask_price Float64,
            ask_size Float64,
            bid_exchange LowCardinality(String),
            ask_exchange LowCardinality(String),
            date Date MATERIALIZED toDate(exchange_ts)
        )
        ENGINE = MergeTree()
        PARTITION BY toYYYYMMDD(exchange_ts)
        ORDER BY (exchange, symbol, exchange_ts, sequence_num)
        TTL exchange_ts + INTERVAL {retention_days} DAY
        SETTINGS index_granularity = 8192
    """,
    
    'l2_snapshots': """
        CREATE TABLE IF NOT EXISTS {database}.l2_snapshots (
            event_id String,
            symbol LowCardinality(String),
            exchange LowCardinality(String),
            exchange_ts DateTime64(9),
            receive_ts DateTime64(9),
            process_ts DateTime64(9),
            sequence_num Int64,
            local_sequence Int64,
            quality_flags UInt8,
            depth UInt16,
            is_snapshot Bool,
            bid_prices Array(Float64),
            bid_sizes Array(Float64),
            bid_counts Array(UInt32),
            ask_prices Array(Float64),
            ask_sizes Array(Float64),
            ask_counts Array(UInt32),
            imbalance Float32,
            date Date MATERIALIZED toDate(exchange_ts)
        )
        ENGINE = MergeTree()
        PARTITION BY toYYYYMMDD(exchange_ts)
        ORDER BY (exchange, symbol, exchange_ts, sequence_num)
        TTL exchange_ts + INTERVAL {retention_days} DAY
        SETTINGS index_granularity = 8192
    """,
    
    'events_raw': """
        CREATE TABLE IF NOT EXISTS {database}.events_raw (
            event_id String,
            event_type Enum8(
                'UNKNOWN' = 0, 'TRADE' = 1, 'QUOTE' = 2, 
                'L2_SNAPSHOT' = 3, 'L2_DELTA' = 4, 'HEARTBEAT' = 5,
                'STATUS' = 6, 'AUCTION' = 7, 'IMBALANCE' = 8,
                'HALT' = 9, 'RESUME' = 10
            ),
            symbol LowCardinality(String),
            exchange LowCardinality(String),
            exchange_ts DateTime64(9),
            receive_ts DateTime64(9),
            process_ts DateTime64(9),
            sequence_num Int64,
            local_sequence Int64,
            quality_flags UInt8,
            payload String,
            date Date MATERIALIZED toDate(exchange_ts)
        )
        ENGINE = MergeTree()
        PARTITION BY toYYYYMMDD(exchange_ts)
        ORDER BY (exchange, symbol, exchange_ts, sequence_num)
        TTL exchange_ts + INTERVAL {retention_days} DAY
        SETTINGS index_granularity = 8192
    """
}


class StorageBackend(ABC):
    """Abstract storage backend"""
    
    @abstractmethod
    async def write_events(self, events: List[MarketEvent]) -> bool:
        """Write batch of events"""
        pass
    
    @abstractmethod
    async def read_events(
        self,
        start_ts: int,
        end_ts: int,
        symbols: Optional[List[str]] = None,
        exchanges: Optional[List[str]] = None,
        event_types: Optional[List[MarketEventType]] = None,
        limit: int = 10000
    ) -> List[MarketEvent]:
        """Read events"""
        pass
    
    @abstractmethod
    async def get_stats(self) -> Dict[str, Any]:
        """Get storage statistics"""
        pass


class ClickHouseWriter(StorageBackend):
    """
    ClickHouse storage backend for hot data.
    Optimized for high-throughput writes and analytical queries.
    """
    
    def __init__(self, config: StorageConfig):
        self.config = config
        self._client = None
        self._initialized = False
        
        # Write buffer
        self._buffer: Dict[str, List[Dict]] = {
            'trades': [],
            'quotes': [],
            'l2_snapshots': [],
        }
        self._buffer_lock = asyncio.Lock()
        self._flush_task: Optional[asyncio.Task] = None
        
        # Stats
        self._events_written: int = 0
        self._bytes_written: int = 0
        self._write_errors: int = 0
        
        logger.info("ClickHouseWriter initialized")
    
    async def initialize(self):
        """Initialize ClickHouse connection and tables"""
        if self._initialized:
            return
        try:
        
            from clickhouse_driver import Client
            
            self._client = Client(
                host=self.config.clickhouse_host,
                port=self.config.clickhouse_port,
                database=self.config.clickhouse_database,
                user=self.config.clickhouse_user,
                password=self.config.clickhouse_password,
            )
            
            # Create database if not exists
            self._client.execute(
                f"CREATE DATABASE IF NOT EXISTS {self.config.clickhouse_database}"
            )
            
            # Create tables
            for table_name, schema in CLICKHOUSE_SCHEMAS.items():
                create_sql = schema.format(
                    database=self.config.clickhouse_database,
                    retention_days=self.config.hot_retention_days
                )
                self._client.execute(create_sql)
                logger.info(f"Created/verified table: {table_name}")
            
            self._initialized = True
            
            # Start flush task
            self._flush_task = asyncio.create_task(self._flush_loop())
            
            logger.info("ClickHouse initialized successfully")
            
        except ImportError:
            logger.warning("clickhouse-driver not installed, using mock")
            self._client = MockClickHouseClient()
            self._initialized = True
        except Exception as e:
            logger.error(f"ClickHouse initialization failed: {e}")
            raise
    
    async def write_events(self, events: List[MarketEvent]) -> bool:
        """Write events to ClickHouse"""
        if not self._initialized:
            await self.initialize()
        
        async with self._buffer_lock:
            for event in events:
                row = self._event_to_row(event)
                if row:
                    table = row.pop('_table')
                    self._buffer[table].append(row)
            
            # Check if buffer is full
            total_buffered = sum(len(b) for b in self._buffer.values())
            if total_buffered >= self.config.batch_size:
                await self._flush_buffer()
        
        return True
    
    def _event_to_row(self, event: MarketEvent) -> Optional[Dict]:
        """Convert event to ClickHouse row"""
        base = {
            'event_id': event.event_id,
            'symbol': event.symbol,
            'exchange': event.exchange,
            'exchange_ts': datetime.fromtimestamp(event.exchange_ts / 1e9),
            'receive_ts': datetime.fromtimestamp(event.receive_ts / 1e9),
            'process_ts': datetime.fromtimestamp(event.process_ts / 1e9),
            'sequence_num': event.sequence_num,
            'local_sequence': event.local_sequence,
            'quality_flags': event.quality_flags,
        }
        
        if event.event_type == MarketEventType.TRADE and event.trade:
            return {
                **base,
                '_table': 'trades',
                'price': event.trade.price,
                'size': event.trade.size,
                'side': event.trade.side.name,
                'trade_id': event.trade.trade_id,
                'conditions': [c.value for c in event.trade.conditions],
            }
        
        elif event.event_type == MarketEventType.QUOTE and event.quote:
            return {
                **base,
                '_table': 'quotes',
                'bid_price': event.quote.bid_price,
                'bid_size': event.quote.bid_size,
                'ask_price': event.quote.ask_price,
                'ask_size': event.quote.ask_size,
                'bid_exchange': event.quote.bid_exchange,
                'ask_exchange': event.quote.ask_exchange,
            }
        
        elif event.event_type in (MarketEventType.L2_SNAPSHOT, MarketEventType.L2_DELTA) and event.l2_book:
            return {
                **base,
                '_table': 'l2_snapshots',
                'depth': event.l2_book.depth,
                'is_snapshot': event.l2_book.is_snapshot,
                'bid_prices': [l.price for l in event.l2_book.bids],
                'bid_sizes': [l.size for l in event.l2_book.bids],
                'bid_counts': [l.order_count for l in event.l2_book.bids],
                'ask_prices': [l.price for l in event.l2_book.asks],
                'ask_sizes': [l.size for l in event.l2_book.asks],
                'ask_counts': [l.order_count for l in event.l2_book.asks],
                'imbalance': event.l2_book.imbalance,
            }
        
        return None
    
    async def _flush_loop(self):
        """Periodic buffer flush"""
        while True:
            await asyncio.sleep(self.config.batch_timeout_ms / 1000)
            async with self._buffer_lock:
                await self._flush_buffer()
    
    async def _flush_buffer(self):
        """Flush buffer to ClickHouse"""
        for table, rows in self._buffer.items():
            if not rows:
                continue
            try:
            
                # Build insert query
                columns = list(rows[0].keys())
                values = [[row[col] for col in columns] for row in rows]
                
                insert_sql = f"""
                    INSERT INTO {self.config.clickhouse_database}.{table}
                    ({', '.join(columns)}) VALUES
                """
                
                self._client.execute(insert_sql, values)
                
                self._events_written += len(rows)
                logger.debug(f"Flushed {len(rows)} rows to {table}")
                
            except Exception as e:
                logger.error(f"Failed to flush to {table}: {e}")
                self._write_errors += 1
            
            finally:
                self._buffer[table] = []
    
    async def read_events(
        self,
        start_ts: int,
        end_ts: int,
        symbols: Optional[List[str]] = None,
        exchanges: Optional[List[str]] = None,
        event_types: Optional[List[MarketEventType]] = None,
        limit: int = 10000
    ) -> List[MarketEvent]:
        """Read events from ClickHouse"""
        if not self._initialized:
            await self.initialize()
        
        # Build query
        tables = []
        if not event_types or MarketEventType.TRADE in event_types:
            tables.append('trades')
        if not event_types or MarketEventType.QUOTE in event_types:
            tables.append('quotes')
        if not event_types or MarketEventType.L2_SNAPSHOT in event_types:
            tables.append('l2_snapshots')
        
        events = []
        
        for table in tables:
            where_clauses = [
                f"exchange_ts >= toDateTime64({start_ts / 1e9}, 9)",
                f"exchange_ts <= toDateTime64({end_ts / 1e9}, 9)",
            ]
            
            if symbols:
                symbols_str = ', '.join(f"'{s}'" for s in symbols)
                where_clauses.append(f"symbol IN ({symbols_str})")
            
            if exchanges:
                exchanges_str = ', '.join(f"'{e}'" for e in exchanges)
                where_clauses.append(f"exchange IN ({exchanges_str})")
            
            query = f"""
                SELECT * FROM {self.config.clickhouse_database}.{table}
                WHERE {' AND '.join(where_clauses)}
                ORDER BY exchange_ts, sequence_num
                LIMIT {limit}
            """
            
            try:
                rows = self._client.execute(query)
                # Convert rows to events (simplified)
                for row in rows:
                    # Would need proper conversion
                    pass
            except Exception as e:
                logger.error(f"Query failed: {e}")
        
        return events
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get storage statistics"""
        return {
            'backend': 'clickhouse',
            'events_written': self._events_written,
            'bytes_written': self._bytes_written,
            'write_errors': self._write_errors,
            'buffer_size': sum(len(b) for b in self._buffer.values()),
            'initialized': self._initialized,
        }
    
    async def close(self):
        """Close connection"""
        if self._flush_task:
            self._flush_task.cancel()
        
        async with self._buffer_lock:
            await self._flush_buffer()


class S3Archiver(StorageBackend):
    """
    S3 storage backend for cold archival.
    Stores compressed event files partitioned by date.
    """
    
    def __init__(self, config: StorageConfig):
        self.config = config
        self._client = None
        self._initialized = False
        
        # Write buffer
        self._buffer: Dict[str, List[MarketEvent]] = {}  # partition_key -> events
        self._buffer_lock = asyncio.Lock()
        
        # Stats
        self._files_written: int = 0
        self._bytes_written: int = 0
        
        logger.info("S3Archiver initialized")
    
    async def initialize(self):
        """Initialize S3 client"""
        if self._initialized:
            return
        try:
        
            import boto3
            
            session_kwargs = {
                'region_name': self.config.s3_region,
            }
            
            if self.config.s3_access_key:
                session_kwargs['aws_access_key_id'] = self.config.s3_access_key
                session_kwargs['aws_secret_access_key'] = self.config.s3_secret_key
            
            session = boto3.Session(**session_kwargs)
            
            client_kwargs = {}
            if self.config.s3_endpoint:
                client_kwargs['endpoint_url'] = self.config.s3_endpoint
            
            self._client = session.client('s3', **client_kwargs)
            
            try:
                # Ensure bucket exists
                self._client.head_bucket(Bucket=self.config.s3_bucket)
            except Exception:
                self._client.create_bucket(
                    Bucket=self.config.s3_bucket,
                    CreateBucketConfiguration={
                        'LocationConstraint': self.config.s3_region
                    }
                )
            
            self._initialized = True
            logger.info("S3 initialized successfully")
            
        except ImportError:
            logger.warning("boto3 not installed, using local storage")
            self._client = None
            self._initialized = True
        except Exception as e:
            logger.error(f"S3 initialization failed: {e}")
            raise
    
    def _get_partition_key(self, event: MarketEvent) -> str:
        """Get partition key for event"""
        dt = datetime.fromtimestamp(event.exchange_ts / 1e9)
        
        if self.config.partition_by == 'hour':
            return dt.strftime('%Y/%m/%d/%H')
        elif self.config.partition_by == 'week':
            return dt.strftime('%Y/W%W')
        else:  # day
            return dt.strftime('%Y/%m/%d')
    
    def _get_s3_key(self, partition: str, exchange: str, symbol: str) -> str:
        """Get S3 object key"""
        safe_symbol = symbol.replace('/', '_')
        return f"events/{partition}/{exchange}/{safe_symbol}.events.lz4"
    
    async def write_events(self, events: List[MarketEvent]) -> bool:
        """Buffer events for S3 upload"""
        if not self._initialized:
            await self.initialize()
        
        async with self._buffer_lock:
            for event in events:
                key = f"{self._get_partition_key(event)}:{event.exchange}:{event.symbol}"
                if key not in self._buffer:
                    self._buffer[key] = []
                self._buffer[key].append(event)
        
        return True
    
    async def flush(self):
        """Flush buffer to S3"""
        async with self._buffer_lock:
            for key, events in self._buffer.items():
                if not events:
                    continue
                
                parts = key.split(':')
                partition = parts[0]
                exchange = parts[1]
                symbol = parts[2]
                
                await self._upload_events(partition, exchange, symbol, events)
            
            self._buffer.clear()
    
    async def _upload_events(
        self,
        partition: str,
        exchange: str,
        symbol: str,
        events: List[MarketEvent]
    ):
        """Upload events to S3"""
        # Serialize events
        data = b''
        for event in events:
            event_bytes = event.to_bytes()
            data += struct.pack('>I', len(event_bytes)) + event_bytes
        
        # Compress
        import lz4.frame
        compressed = lz4.frame.compress(data)
        
        s3_key = self._get_s3_key(partition, exchange, symbol)
        
        if self._client:
            try:
                self._client.put_object(
                    Bucket=self.config.s3_bucket,
                    Key=s3_key,
                    Body=compressed,
                    ContentType='application/octet-stream',
                    Metadata={
                        'event_count': str(len(events)),
                        'compression': 'lz4',
                    }
                )
                
                self._files_written += 1
                self._bytes_written += len(compressed)
                
                logger.debug(f"Uploaded {len(events)} events to s3://{self.config.s3_bucket}/{s3_key}")
                
            except Exception as e:
                logger.error(f"S3 upload failed: {e}")
        else:
            # Local fallback
            local_path = Path(self.config.local_data_dir) / s3_key
            local_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(local_path, 'wb') as f:
                f.write(compressed)
            
            self._files_written += 1
            self._bytes_written += len(compressed)
    
    async def read_events(
        self,
        start_ts: int,
        end_ts: int,
        symbols: Optional[List[str]] = None,
        exchanges: Optional[List[str]] = None,
        event_types: Optional[List[MarketEventType]] = None,
        limit: int = 10000
    ) -> List[MarketEvent]:
        """Read events from S3"""
        if not self._initialized:
            await self.initialize()
        
        events = []
        
        # Generate partition keys for date range
        start_dt = datetime.fromtimestamp(start_ts / 1e9)
        end_dt = datetime.fromtimestamp(end_ts / 1e9)
        
        current = start_dt
        while current <= end_dt:
            partition = current.strftime('%Y/%m/%d')
            
            # List objects in partition
            prefix = f"events/{partition}/"
            
            if self._client:
                try:
                    response = self._client.list_objects_v2(
                        Bucket=self.config.s3_bucket,
                        Prefix=prefix
                    )
                    
                    for obj in response.get('Contents', []):
                        # Filter by exchange/symbol from key
                        key = obj['Key']
                        parts = key.split('/')
                        if len(parts) >= 4:
                            obj_exchange = parts[-2]
                            obj_symbol = parts[-1].replace('.events.lz4', '')
                            
                            if exchanges and obj_exchange not in exchanges:
                                continue
                            if symbols and obj_symbol not in symbols:
                                continue
                            
                            # Download and parse
                            file_events = await self._download_events(key)
                            events.extend(file_events)
                            
                            if len(events) >= limit:
                                return events[:limit]
                
                except Exception as e:
                    logger.error(f"S3 read failed: {e}")
            
            current += timedelta(days=1)
        
        return events
    
    async def _download_events(self, s3_key: str) -> List[MarketEvent]:
        """Download and parse events from S3"""
        events = []
        
        try:
            response = self._client.get_object(
                Bucket=self.config.s3_bucket,
                Key=s3_key
            )
            
            compressed = response['Body'].read()
            
            data = lz4.frame.decompress(compressed)
            
            offset = 0
            while offset < len(data):
                if offset + 4 > len(data):
                    break
                
                event_len = struct.unpack('>I', data[offset:offset+4])[0]
                offset += 4
                
                if offset + event_len > len(data):
                    break
                
                event = MarketEvent.from_bytes(data[offset:offset+event_len])
                events.append(event)
                offset += event_len
        
        except Exception as e:
            logger.error(f"Failed to download {s3_key}: {e}")
        
        return events
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get storage statistics"""
        return {
            'backend': 's3',
            'bucket': self.config.s3_bucket,
            'files_written': self._files_written,
            'bytes_written': self._bytes_written,
            'buffer_size': sum(len(e) for e in self._buffer.values()),
            'initialized': self._initialized,
        }


class StorageManager:
    """
    Unified storage manager coordinating ClickHouse and S3.
    Handles tiered storage and lifecycle management.
    """
    
    def __init__(self, config: Optional[StorageConfig] = None):
        self.config = config or StorageConfig()
        
        # Backends
        self.clickhouse = ClickHouseWriter(self.config)
        self.s3 = S3Archiver(self.config)
        
        # Write buffer
        self._buffer: List[MarketEvent] = []
        self._buffer_lock = asyncio.Lock()
        
        # Background tasks
        self._archive_task: Optional[asyncio.Task] = None
        
        logger.info("StorageManager initialized")
    
    async def initialize(self):
        """Initialize all backends"""
        await self.clickhouse.initialize()
        await self.s3.initialize()
        
        # Start archival task
        self._archive_task = asyncio.create_task(self._archive_loop())
    
    async def write(self, events: List[MarketEvent]):
        """Write events to storage"""
        # Write to ClickHouse (hot storage)
        await self.clickhouse.write_events(events)
        
        # Buffer for S3 archival
        async with self._buffer_lock:
            self._buffer.extend(events)
            
            if len(self._buffer) >= self.config.batch_size:
                await self._archive_buffer()
    
    async def _archive_buffer(self):
        """Archive buffer to S3"""
        if not self._buffer:
            return
        
        events = self._buffer
        self._buffer = []
        
        await self.s3.write_events(events)
        await self.s3.flush()
    
    async def _archive_loop(self):
        """Periodic archival"""
        while True:
            await asyncio.sleep(60)  # Every minute
            async with self._buffer_lock:
                await self._archive_buffer()
    
    async def read(
        self,
        start_ts: int,
        end_ts: int,
        symbols: Optional[List[str]] = None,
        exchanges: Optional[List[str]] = None,
        event_types: Optional[List[MarketEventType]] = None,
        limit: int = 10000
    ) -> List[MarketEvent]:
        """Read events from storage"""
        # Determine which backend to use based on time range
        now_ts = int(time.time() * 1e9)
        hot_threshold = now_ts - (self.config.hot_retention_days * 24 * 60 * 60 * 1e9)
        
        events = []
        
        if end_ts >= hot_threshold:
            # Read from ClickHouse
            ch_events = await self.clickhouse.read_events(
                max(start_ts, hot_threshold),
                end_ts,
                symbols,
                exchanges,
                event_types,
                limit
            )
            events.extend(ch_events)
        
        if start_ts < hot_threshold and len(events) < limit:
            # Read from S3
            s3_events = await self.s3.read_events(
                start_ts,
                min(end_ts, hot_threshold),
                symbols,
                exchanges,
                event_types,
                limit - len(events)
            )
            events.extend(s3_events)
        
        # Sort by timestamp
        events.sort(key=lambda e: (e.exchange_ts, e.sequence_num))
        
        return events[:limit]
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get storage statistics"""
        return {
            'clickhouse': await self.clickhouse.get_stats(),
            's3': await self.s3.get_stats(),
            'buffer_size': len(self._buffer),
        }
    
    async def close(self):
        """Close all backends"""
        if self._archive_task:
            self._archive_task.cancel()
        
        async with self._buffer_lock:
            await self._archive_buffer()
        
        await self.clickhouse.close()


class MockClickHouseClient:
    """Mock ClickHouse client for testing"""
    
    def __init__(self):
        self.data: Dict[str, List] = {}
    
    def execute(self, query: str, params=None):
        if query.strip().upper().startswith('SELECT'):
            return []
        return None
