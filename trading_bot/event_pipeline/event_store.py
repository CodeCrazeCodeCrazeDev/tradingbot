"""
AlphaAlgo Event Store
======================
Append-only event storage with snapshots, streams, and queries.
Provides the foundation for event sourcing and replay.
"""

from __future__ import annotations

import asyncio
import logging
import time
import json
import hashlib
import sqlite3
import threading
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum, auto
from pathlib import Path
from typing import (
    Dict, List, Optional, Any, AsyncIterator, Iterator,
    Callable, Tuple, Union, TypeVar
)
from collections import defaultdict
import struct

from .events import (
    Event, EventType, EventMetadata, EventEnvelope,
    deserialize_event, EVENT_SCHEMA_VERSION
)

logger = logging.getLogger(__name__)


class StorageBackend(Enum):
    """Storage backend types"""
    MEMORY = auto()      # In-memory (testing/development)
    SQLITE = auto()      # SQLite (single node)
    POSTGRES = auto()    # PostgreSQL (production)
    KAFKA = auto()       # Kafka as event store
    CLICKHOUSE = auto()  # ClickHouse (analytics)


@dataclass
class EventStoreConfig:
    """Configuration for event store"""
    # Backend
    backend: StorageBackend = StorageBackend.MEMORY
    connection_string: str = ""
    
    # Storage paths
    data_dir: Path = field(default_factory=lambda: Path("event_store_data"))
    
    # Snapshots
    snapshot_interval: int = 1000          # Events between snapshots
    snapshot_retention_days: int = 30
    
    # Retention
    event_retention_days: int = 365        # Keep events for 1 year
    archive_after_days: int = 30           # Archive after 30 days
    
    # Performance
    batch_size: int = 1000
    flush_interval_ms: int = 100
    max_buffer_size: int = 10000
    
    # Compression
    compress_events: bool = True
    compression_level: int = 6
    
    # Integrity
    verify_checksums: bool = True
    enable_wal: bool = True                # Write-ahead logging


@dataclass
class Snapshot:
    """
    Point-in-time snapshot of aggregate state.
    Enables fast recovery without replaying all events.
    """
    snapshot_id: str
    aggregate_id: str
    aggregate_type: str
    version: int
    timestamp_ns: int
    state: Dict[str, Any]
    checksum: str = ""
    
    def compute_checksum(self) -> str:
        content = json.dumps({
            'aggregate_id': self.aggregate_id,
            'version': self.version,
            'state': self.state,
        }, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()
    
    def verify(self) -> bool:
        return self.checksum == self.compute_checksum()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'snapshot_id': self.snapshot_id,
            'aggregate_id': self.aggregate_id,
            'aggregate_type': self.aggregate_type,
            'version': self.version,
            'timestamp_ns': self.timestamp_ns,
            'state': self.state,
            'checksum': self.checksum,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Snapshot':
        return cls(
            snapshot_id=data['snapshot_id'],
            aggregate_id=data['aggregate_id'],
            aggregate_type=data['aggregate_type'],
            version=data['version'],
            timestamp_ns=data['timestamp_ns'],
            state=data['state'],
            checksum=data.get('checksum', ''),
        )


@dataclass
class EventStream:
    """
    A stream of events for a specific aggregate or topic.
    Supports iteration, filtering, and subscription.
    """
    stream_id: str
    stream_type: str                       # 'aggregate', 'topic', 'category'
    
    # Position tracking
    current_position: int = 0
    start_position: int = 0
    end_position: int = -1                 # -1 = unbounded
    
    # Filtering
    event_types: List[EventType] = field(default_factory=list)
    partition_keys: List[str] = field(default_factory=list)
    
    # Metadata
    created_at_ns: int = 0
    last_event_ns: int = 0
    event_count: int = 0


@dataclass
class EventQuery:
    """Query specification for event retrieval"""
    # Time range
    start_time_ns: Optional[int] = None
    end_time_ns: Optional[int] = None
    
    # Sequence range
    start_sequence: Optional[int] = None
    end_sequence: Optional[int] = None
    
    # Filtering
    event_types: List[EventType] = field(default_factory=list)
    partition_keys: List[str] = field(default_factory=list)
    correlation_ids: List[str] = field(default_factory=list)
    sources: List[str] = field(default_factory=list)
    
    # Pagination
    limit: int = 1000
    offset: int = 0
    
    # Ordering
    ascending: bool = True
    
    def matches(self, event: Event) -> bool:
        """Check if event matches query criteria"""
        meta = event.metadata
        
        if self.start_time_ns and meta.timestamp_ns < self.start_time_ns:
            return False
        if self.end_time_ns and meta.timestamp_ns > self.end_time_ns:
            return False
        if self.start_sequence and meta.sequence_number < self.start_sequence:
            return False
        if self.end_sequence and meta.sequence_number > self.end_sequence:
            return False
        if self.event_types and meta.event_type not in self.event_types:
            return False
        if self.partition_keys and meta.partition_key not in self.partition_keys:
            return False
        if self.correlation_ids and meta.correlation_id not in self.correlation_ids:
            return False
        if self.sources and meta.source not in self.sources:
            return False
        
        return True


class EventStoreBackend(ABC):
    """Abstract base class for event store backends"""
    
    @abstractmethod
    async def append(self, event: Event) -> int:
        """Append event, return sequence number"""
        pass
    
    @abstractmethod
    async def append_batch(self, events: List[Event]) -> List[int]:
        """Append batch of events, return sequence numbers"""
        pass
    
    @abstractmethod
    async def get(self, sequence: int) -> Optional[Event]:
        """Get event by sequence number"""
        pass
    
    @abstractmethod
    async def query(self, query: EventQuery) -> List[Event]:
        """Query events"""
        pass
    
    @abstractmethod
    async def stream(self, query: EventQuery) -> AsyncIterator[Event]:
        """Stream events matching query"""
        pass
    
    @abstractmethod
    async def save_snapshot(self, snapshot: Snapshot) -> None:
        """Save aggregate snapshot"""
        pass
    
    @abstractmethod
    async def get_snapshot(self, aggregate_id: str) -> Optional[Snapshot]:
        """Get latest snapshot for aggregate"""
        pass
    
    @abstractmethod
    async def get_stream_position(self, stream_id: str) -> int:
        """Get current position of stream"""
        pass
    
    @abstractmethod
    async def close(self) -> None:
        """Close backend connection"""
        pass


class InMemoryBackend(EventStoreBackend):
    """In-memory event store backend for testing"""
    
    def __init__(self):
        self.events: List[Event] = []
        self.snapshots: Dict[str, Snapshot] = {}
        self.stream_positions: Dict[str, int] = {}
        self.sequence_counter = 0
        self._lock = asyncio.Lock()
    
    async def append(self, event: Event) -> int:
        async with self._lock:
            self.sequence_counter += 1
            # Update sequence in metadata (create new metadata since frozen)
            new_metadata = EventMetadata(
                event_id=event.metadata.event_id,
                event_type=event.metadata.event_type,
                version=event.metadata.version,
                timestamp_ns=event.metadata.timestamp_ns,
                created_at_ns=event.metadata.created_at_ns,
                received_at_ns=time.time_ns(),
                sequence_number=self.sequence_counter,
                partition_key=event.metadata.partition_key,
                correlation_id=event.metadata.correlation_id,
                causation_id=event.metadata.causation_id,
                parent_id=event.metadata.parent_id,
                source=event.metadata.source,
                source_instance=event.metadata.source_instance,
                priority=event.metadata.priority,
                idempotency_key=event.metadata.idempotency_key,
                retry_count=event.metadata.retry_count,
                max_retries=event.metadata.max_retries,
            )
            event.metadata = new_metadata
            self.events.append(event)
            return self.sequence_counter
    
    async def append_batch(self, events: List[Event]) -> List[int]:
        sequences = []
        for event in events:
            seq = await self.append(event)
            sequences.append(seq)
        return sequences
    
    async def get(self, sequence: int) -> Optional[Event]:
        if 0 < sequence <= len(self.events):
            return self.events[sequence - 1]
        return None
    
    async def query(self, query: EventQuery) -> List[Event]:
        results = []
        events = self.events if query.ascending else reversed(self.events)
        
        for event in events:
            if query.matches(event):
                results.append(event)
                if len(results) >= query.limit:
                    break
        
        return results[query.offset:query.offset + query.limit]
    
    async def stream(self, query: EventQuery) -> AsyncIterator[Event]:
        for event in self.events:
            if query.matches(event):
                yield event
    
    async def save_snapshot(self, snapshot: Snapshot) -> None:
        snapshot.checksum = snapshot.compute_checksum()
        self.snapshots[snapshot.aggregate_id] = snapshot
    
    async def get_snapshot(self, aggregate_id: str) -> Optional[Snapshot]:
        return self.snapshots.get(aggregate_id)
    
    async def get_stream_position(self, stream_id: str) -> int:
        return self.stream_positions.get(stream_id, 0)
    


class SQLiteBackend(EventStoreBackend):
    """SQLite event store backend for single-node deployments"""
    
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._local = threading.local()
        self._init_schema()
    
    def _get_conn(self) -> sqlite3.Connection:
        if not hasattr(self._local, 'conn'):
            self._local.conn = sqlite3.connect(
                str(self.db_path),
                check_same_thread=False
            )
            self._local.conn.row_factory = sqlite3.Row
        return self._local.conn
    
    def _init_schema(self):
        conn = self._get_conn()
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS events (
                sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id TEXT UNIQUE NOT NULL,
                event_type INTEGER NOT NULL,
                timestamp_ns INTEGER NOT NULL,
                partition_key TEXT,
                correlation_id TEXT,
                causation_id TEXT,
                source TEXT,
                priority INTEGER,
                payload TEXT NOT NULL,
                checksum TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp_ns);
            CREATE INDEX IF NOT EXISTS idx_events_type ON events(event_type);
            CREATE INDEX IF NOT EXISTS idx_events_partition ON events(partition_key);
            CREATE INDEX IF NOT EXISTS idx_events_correlation ON events(correlation_id);
            
            CREATE TABLE IF NOT EXISTS snapshots (
                snapshot_id TEXT PRIMARY KEY,
                aggregate_id TEXT NOT NULL,
                aggregate_type TEXT NOT NULL,
                version INTEGER NOT NULL,
                timestamp_ns INTEGER NOT NULL,
                state TEXT NOT NULL,
                checksum TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE INDEX IF NOT EXISTS idx_snapshots_aggregate ON snapshots(aggregate_id);
            
            CREATE TABLE IF NOT EXISTS stream_positions (
                stream_id TEXT PRIMARY KEY,
                position INTEGER NOT NULL,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
        """)
        conn.commit()
    
    async def append(self, event: Event) -> int:
        conn = self._get_conn()
        meta = event.metadata
        payload = json.dumps(event.to_payload())
        checksum = event.compute_hash()
        
        cursor = conn.execute("""
            INSERT INTO events (
                event_id, event_type, timestamp_ns, partition_key,
                correlation_id, causation_id, source, priority,
                payload, checksum
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            meta.event_id, meta.event_type.value, meta.timestamp_ns,
            meta.partition_key, meta.correlation_id, meta.causation_id,
            meta.source, meta.priority.value, payload, checksum
        ))
        conn.commit()
        return cursor.lastrowid
    
    async def append_batch(self, events: List[Event]) -> List[int]:
        conn = self._get_conn()
        sequences = []
        
        for event in events:
            meta = event.metadata
            payload = json.dumps(event.to_payload())
            checksum = event.compute_hash()
            
            cursor = conn.execute("""
                INSERT INTO events (
                    event_id, event_type, timestamp_ns, partition_key,
                    correlation_id, causation_id, source, priority,
                    payload, checksum
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                meta.event_id, meta.event_type.value, meta.timestamp_ns,
                meta.partition_key, meta.correlation_id, meta.causation_id,
                meta.source, meta.priority.value, payload, checksum
            ))
            sequences.append(cursor.lastrowid)
        
        conn.commit()
        return sequences
    
    async def get(self, sequence: int) -> Optional[Event]:
        conn = self._get_conn()
        cursor = conn.execute(
            "SELECT * FROM events WHERE sequence = ?",
            (sequence,)
        )
        row = cursor.fetchone()
        if row:
            return self._row_to_event(row)
        return None
    
    def _row_to_event(self, row: sqlite3.Row) -> Event:
        from .events import EVENT_REGISTRY, EventPriority
        
        metadata = EventMetadata(
            event_id=row['event_id'],
            event_type=EventType(row['event_type']),
            timestamp_ns=row['timestamp_ns'],
            sequence_number=row['sequence'],
            partition_key=row['partition_key'] or '',
            correlation_id=row['correlation_id'] or '',
            causation_id=row['causation_id'] or '',
            source=row['source'] or '',
            priority=EventPriority(row['priority']),
        )
        
        payload = json.loads(row['payload'])
        event_class = EVENT_REGISTRY.get(metadata.event_type)
        
        if event_class:
            return event_class.from_payload(metadata, payload)
        raise ValueError(f"Unknown event type: {metadata.event_type}")
    
    async def query(self, query: EventQuery) -> List[Event]:
        conn = self._get_conn()
        
        sql = "SELECT * FROM events WHERE 1=1"
        params = []
        
        if query.start_time_ns:
            sql += " AND timestamp_ns >= ?"
            params.append(query.start_time_ns)
        if query.end_time_ns:
            sql += " AND timestamp_ns <= ?"
            params.append(query.end_time_ns)
        if query.start_sequence:
            sql += " AND sequence >= ?"
            params.append(query.start_sequence)
        if query.end_sequence:
            sql += " AND sequence <= ?"
            params.append(query.end_sequence)
        if query.event_types:
            placeholders = ','.join('?' * len(query.event_types))
            sql += f" AND event_type IN ({placeholders})"
            params.extend(et.value for et in query.event_types)
        if query.partition_keys:
            placeholders = ','.join('?' * len(query.partition_keys))
            sql += f" AND partition_key IN ({placeholders})"
            params.extend(query.partition_keys)
        if query.correlation_ids:
            placeholders = ','.join('?' * len(query.correlation_ids))
            sql += f" AND correlation_id IN ({placeholders})"
            params.extend(query.correlation_ids)
        if query.sources:
            placeholders = ','.join('?' * len(query.sources))
            sql += f" AND source IN ({placeholders})"
            params.extend(query.sources)
        
        order = "ASC" if query.ascending else "DESC"
        sql += f" ORDER BY sequence {order} LIMIT ? OFFSET ?"
        params.extend([query.limit, query.offset])
        
        cursor = conn.execute(sql, params)
        return [self._row_to_event(row) for row in cursor.fetchall()]
    
    async def stream(self, query: EventQuery) -> AsyncIterator[Event]:
        events = await self.query(query)
        for event in events:
            yield event
    
    async def save_snapshot(self, snapshot: Snapshot) -> None:
        conn = self._get_conn()
        snapshot.checksum = snapshot.compute_checksum()
        
        conn.execute("""
            INSERT OR REPLACE INTO snapshots (
                snapshot_id, aggregate_id, aggregate_type, version,
                timestamp_ns, state, checksum
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            snapshot.snapshot_id, snapshot.aggregate_id,
            snapshot.aggregate_type, snapshot.version,
            snapshot.timestamp_ns, json.dumps(snapshot.state),
            snapshot.checksum
        ))
        conn.commit()
    
    async def get_snapshot(self, aggregate_id: str) -> Optional[Snapshot]:
        conn = self._get_conn()
        cursor = conn.execute(
            "SELECT * FROM snapshots WHERE aggregate_id = ? ORDER BY version DESC LIMIT 1",
            (aggregate_id,)
        )
        row = cursor.fetchone()
        if row:
            return Snapshot(
                snapshot_id=row['snapshot_id'],
                aggregate_id=row['aggregate_id'],
                aggregate_type=row['aggregate_type'],
                version=row['version'],
                timestamp_ns=row['timestamp_ns'],
                state=json.loads(row['state']),
                checksum=row['checksum'],
            )
        return None
    
    async def get_stream_position(self, stream_id: str) -> int:
        conn = self._get_conn()
        cursor = conn.execute(
            "SELECT position FROM stream_positions WHERE stream_id = ?",
            (stream_id,)
        )
        row = cursor.fetchone()
        return row['position'] if row else 0
    
    async def close(self) -> None:
        if hasattr(self._local, 'conn'):
            self._local.conn.close()


class EventStore:
    """
    Main event store interface.
    Provides append-only storage with snapshots and queries.
    """
    
    def __init__(self, config: EventStoreConfig):
        self.config = config
        self.backend: EventStoreBackend = self._create_backend()
        
        # Metrics
        self.metrics = {
            'events_appended': 0,
            'events_queried': 0,
            'snapshots_saved': 0,
            'snapshots_loaded': 0,
        }
        
        # Buffer for batching
        self._buffer: List[Event] = []
        self._buffer_lock = asyncio.Lock()
        self._flush_task: Optional[asyncio.Task] = None
        
        logger.info(f"EventStore initialized with {config.backend.name} backend")
    
    def _create_backend(self) -> EventStoreBackend:
        if self.config.backend == StorageBackend.MEMORY:
            return InMemoryBackend()
        elif self.config.backend == StorageBackend.SQLITE:
            db_path = self.config.data_dir / "events.db"
            return SQLiteBackend(db_path)
        else:
            # Default to in-memory for unsupported backends
            logger.warning(f"Backend {self.config.backend} not implemented, using MEMORY")
            return InMemoryBackend()
    
    async def start(self):
        """Start the event store"""
        if self.config.flush_interval_ms > 0:
            self._flush_task = asyncio.create_task(self._flush_loop())
        logger.info("EventStore started")
    
    async def stop(self):
        """Stop the event store"""
        if self._flush_task:
            self._flush_task.cancel()
            try:
                await self._flush_task
            except asyncio.CancelledError:
                pass
        
        # Flush remaining buffer
        await self._flush_buffer()
        await self.backend.close()
        logger.info("EventStore stopped")
    
    async def _flush_loop(self):
        """Periodic buffer flush"""
        interval = self.config.flush_interval_ms / 1000
        while True:
            await asyncio.sleep(interval)
            await self._flush_buffer()
    
    async def _flush_buffer(self):
        """Flush buffered events to storage"""
        async with self._buffer_lock:
            if self._buffer:
                events = self._buffer[:]
                self._buffer.clear()
                await self.backend.append_batch(events)
    
    async def append(self, event: Event, immediate: bool = False) -> int:
        """
        Append event to store.
        
        Args:
            event: Event to append
            immediate: If True, bypass buffer and write immediately
            
        Returns:
            Sequence number
        """
        if immediate or len(self._buffer) >= self.config.max_buffer_size:
            sequence = await self.backend.append(event)
        else:
            async with self._buffer_lock:
                self._buffer.append(event)
                sequence = len(self._buffer)  # Approximate
        
        self.metrics['events_appended'] += 1
        return sequence
    
    async def append_batch(self, events: List[Event]) -> List[int]:
        """Append batch of events"""
        sequences = await self.backend.append_batch(events)
        self.metrics['events_appended'] += len(events)
        return sequences
    
    async def get(self, sequence: int) -> Optional[Event]:
        """Get event by sequence number"""
        return await self.backend.get(sequence)
    
    async def query(self, query: EventQuery) -> List[Event]:
        """Query events"""
        events = await self.backend.query(query)
        self.metrics['events_queried'] += len(events)
        return events
    
    async def stream(self, query: EventQuery) -> AsyncIterator[Event]:
        """Stream events matching query"""
        async for event in self.backend.stream(query):
            yield event
    
    async def get_events_for_aggregate(
        self,
        aggregate_id: str,
        after_version: int = 0
    ) -> List[Event]:
        """Get all events for an aggregate after a version"""
        query = EventQuery(
            partition_keys=[aggregate_id],
            start_sequence=after_version + 1,
            ascending=True,
        )
        return await self.query(query)
    
    async def save_snapshot(self, snapshot: Snapshot) -> None:
        """Save aggregate snapshot"""
        await self.backend.save_snapshot(snapshot)
        self.metrics['snapshots_saved'] += 1
    
    async def get_snapshot(self, aggregate_id: str) -> Optional[Snapshot]:
        """Get latest snapshot for aggregate"""
        snapshot = await self.backend.get_snapshot(aggregate_id)
        if snapshot:
            self.metrics['snapshots_loaded'] += 1
        return snapshot
    
    async def rebuild_aggregate(
        self,
        aggregate_id: str,
        apply_event: Callable[[Any, Event], Any],
        initial_state: Any = None
    ) -> Tuple[Any, int]:
        """
        Rebuild aggregate state from events.
        
        Args:
            aggregate_id: Aggregate ID
            apply_event: Function to apply event to state
            initial_state: Initial state (or from snapshot)
            
        Returns:
            (final_state, version)
        """
        # Try to load snapshot first
        snapshot = await self.get_snapshot(aggregate_id)
        if snapshot:
            state = snapshot.state
            after_version = snapshot.version
        else:
            state = initial_state
            after_version = 0
        
        # Apply events after snapshot
        events = await self.get_events_for_aggregate(aggregate_id, after_version)
        for event in events:
            state = apply_event(state, event)
        
        version = after_version + len(events)
        return state, version
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get store metrics"""
        return {
            **self.metrics,
            'buffer_size': len(self._buffer),
        }
