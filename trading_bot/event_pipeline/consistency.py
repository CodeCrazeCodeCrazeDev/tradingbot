"""
AlphaAlgo Consistency Guarantees
=================================
Idempotency, transactions, causality tracking, and sequence validation.
Ensures exactly-once semantics and data integrity.
"""

from __future__ import annotations

import asyncio
import logging
import time
import uuid
import hashlib
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum, auto
from typing import (
    Dict, List, Optional, Any, Callable, Awaitable,
    Set, Tuple, TypeVar
)
from collections import OrderedDict
import threading

from .events import Event, EventType, EventMetadata

logger = logging.getLogger(__name__)


class IdempotencyGuard:
    """
    Ensures exactly-once processing of events.
    Tracks processed idempotency keys to prevent duplicates.
    """
    
    def __init__(
        self,
        max_keys: int = 100000,
        ttl_seconds: int = 3600
    ):
        self.max_keys = max_keys
        self.ttl_seconds = ttl_seconds
        
        # Key -> (timestamp, result)
        self._processed: OrderedDict[str, Tuple[float, Any]] = OrderedDict()
        self._lock = asyncio.Lock()
        
        # Cleanup task
        self._cleanup_task: Optional[asyncio.Task] = None
    
    async def start(self):
        """Start the cleanup task"""
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
    
    async def stop(self):
        """Stop the cleanup task"""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
    
    async def _cleanup_loop(self):
        """Periodic cleanup of expired keys"""
        while True:
            try:
                await asyncio.sleep(60)  # Cleanup every minute
                await self._cleanup_expired()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Cleanup error: {e}")
    
    async def _cleanup_expired(self):
        """Remove expired keys"""
        async with self._lock:
            now = time.time()
            expired = [
                key for key, (ts, _) in self._processed.items()
                if now - ts > self.ttl_seconds
            ]
            for key in expired:
                del self._processed[key]
    
    async def check_and_set(
        self,
        key: str,
        result: Any = None
    ) -> Tuple[bool, Optional[Any]]:
        """
        Check if key was processed, set if not.
        
        Args:
            key: Idempotency key
            result: Result to store
            
        Returns:
            (is_new, previous_result) - is_new=True if first time
        """
        async with self._lock:
            if key in self._processed:
                _, prev_result = self._processed[key]
                return False, prev_result
            
            # Evict oldest if at capacity
            if len(self._processed) >= self.max_keys:
                self._processed.popitem(last=False)
            
            self._processed[key] = (time.time(), result)
            return True, None
    
    async def is_processed(self, key: str) -> bool:
        """Check if key was already processed"""
        async with self._lock:
            return key in self._processed
    
    async def get_result(self, key: str) -> Optional[Any]:
        """Get stored result for key"""
        async with self._lock:
            if key in self._processed:
                _, result = self._processed[key]
                return result
            return None
    
    async def mark_processed(self, key: str, result: Any = None):
        """Mark key as processed"""
        async with self._lock:
            if len(self._processed) >= self.max_keys:
                self._processed.popitem(last=False)
            self._processed[key] = (time.time(), result)
    
    def size(self) -> int:
        return len(self._processed)


class TransactionState(Enum):
    """Transaction states"""
    PENDING = auto()
    COMMITTED = auto()
    ABORTED = auto()
    ROLLED_BACK = auto()


@dataclass
class Transaction:
    """Represents an atomic transaction"""
    transaction_id: str
    state: TransactionState = TransactionState.PENDING
    events: List[Event] = field(default_factory=list)
    created_at_ns: int = field(default_factory=time.time_ns)
    committed_at_ns: int = 0
    
    # Rollback info
    rollback_events: List[Event] = field(default_factory=list)
    
    def add_event(self, event: Event):
        """Add event to transaction"""
        if self.state != TransactionState.PENDING:
            raise ValueError(f"Cannot add to {self.state.name} transaction")
        self.events.append(event)
    
    def commit(self):
        """Mark transaction as committed"""
        if self.state != TransactionState.PENDING:
            raise ValueError(f"Cannot commit {self.state.name} transaction")
        self.state = TransactionState.COMMITTED
        self.committed_at_ns = time.time_ns()
    
    def abort(self):
        """Mark transaction as aborted"""
        if self.state != TransactionState.PENDING:
            raise ValueError(f"Cannot abort {self.state.name} transaction")
        self.state = TransactionState.ABORTED


class TransactionManager:
    """
    Manages atomic transactions across events.
    Provides commit/rollback semantics.
    """
    
    def __init__(self):
        self._transactions: Dict[str, Transaction] = {}
        self._lock = asyncio.Lock()
        
        # Callbacks
        self._on_commit: List[Callable[[Transaction], Awaitable[None]]] = []
        self._on_rollback: List[Callable[[Transaction], Awaitable[None]]] = []
    
    def on_commit(self, callback: Callable[[Transaction], Awaitable[None]]):
        """Register commit callback"""
        self._on_commit.append(callback)
    
    def on_rollback(self, callback: Callable[[Transaction], Awaitable[None]]):
        """Register rollback callback"""
        self._on_rollback.append(callback)
    
    async def begin(self) -> str:
        """Begin a new transaction"""
        async with self._lock:
            tx_id = str(uuid.uuid4())
            self._transactions[tx_id] = Transaction(transaction_id=tx_id)
            logger.debug(f"Transaction {tx_id} started")
            return tx_id
    
    async def add_event(self, tx_id: str, event: Event):
        """Add event to transaction"""
        async with self._lock:
            if tx_id not in self._transactions:
                raise ValueError(f"Unknown transaction: {tx_id}")
            self._transactions[tx_id].add_event(event)
    
    async def commit(self, tx_id: str) -> List[Event]:
        """
        Commit transaction.
        
        Returns:
            List of committed events
        """
        async with self._lock:
            if tx_id not in self._transactions:
                raise ValueError(f"Unknown transaction: {tx_id}")
            
            tx = self._transactions[tx_id]
            tx.commit()
            
            logger.debug(f"Transaction {tx_id} committed with {len(tx.events)} events")
        
        # Call callbacks outside lock
        for callback in self._on_commit:
            try:
                await callback(tx)
            except Exception as e:
                logger.error(f"Commit callback error: {e}")
        
        return tx.events
    
    async def rollback(self, tx_id: str):
        """Rollback transaction"""
        async with self._lock:
            if tx_id not in self._transactions:
                raise ValueError(f"Unknown transaction: {tx_id}")
            
            tx = self._transactions[tx_id]
            tx.abort()
            tx.state = TransactionState.ROLLED_BACK
            
            logger.debug(f"Transaction {tx_id} rolled back")
        
        # Call callbacks outside lock
        for callback in self._on_rollback:
            try:
                await callback(tx)
            except Exception as e:
                logger.error(f"Rollback callback error: {e}")
    
    async def get_transaction(self, tx_id: str) -> Optional[Transaction]:
        """Get transaction by ID"""
        async with self._lock:
            return self._transactions.get(tx_id)
    
    async def cleanup_old(self, max_age_seconds: int = 3600):
        """Cleanup old completed transactions"""
        async with self._lock:
            now = time.time_ns()
            max_age_ns = max_age_seconds * 1_000_000_000
            
            to_remove = [
                tx_id for tx_id, tx in self._transactions.items()
                if tx.state != TransactionState.PENDING
                and now - tx.created_at_ns > max_age_ns
            ]
            
            for tx_id in to_remove:
                del self._transactions[tx_id]


class CausalityTracker:
    """
    Tracks causal relationships between events.
    Ensures events are processed in causal order.
    """
    
    def __init__(self):
        # event_id -> list of caused event_ids
        self._causes: Dict[str, List[str]] = {}
        # event_id -> causation_id (what caused this event)
        self._caused_by: Dict[str, str] = {}
        # event_id -> processed
        self._processed: Set[str] = set()
        self._lock = asyncio.Lock()
    
    async def register_event(self, event: Event):
        """Register event and its causal relationship"""
        async with self._lock:
            event_id = event.event_id
            causation_id = event.metadata.causation_id
            
            if causation_id:
                self._caused_by[event_id] = causation_id
                if causation_id not in self._causes:
                    self._causes[causation_id] = []
                self._causes[causation_id].append(event_id)
    
    async def can_process(self, event: Event) -> bool:
        """Check if event can be processed (all causes processed)"""
        async with self._lock:
            causation_id = event.metadata.causation_id
            
            if not causation_id:
                return True
            
            return causation_id in self._processed
    
    async def mark_processed(self, event_id: str):
        """Mark event as processed"""
        async with self._lock:
            self._processed.add(event_id)
    
    async def get_caused_events(self, event_id: str) -> List[str]:
        """Get events caused by this event"""
        async with self._lock:
            return self._causes.get(event_id, [])
    
    async def get_cause(self, event_id: str) -> Optional[str]:
        """Get the event that caused this event"""
        async with self._lock:
            return self._caused_by.get(event_id)
    
    async def wait_for_cause(
        self,
        event: Event,
        timeout: float = 30.0
    ) -> bool:
        """Wait for cause to be processed"""
        start = time.time()
        
        while time.time() - start < timeout:
            if await self.can_process(event):
                return True
            await asyncio.sleep(0.01)
        
        return False


class SequenceGap:
    """Represents a gap in sequence"""
    def __init__(self, start: int, end: int):
        self.start = start
        self.end = end
        self.detected_at = time.time()
    
    @property
    def size(self) -> int:
        return self.end - self.start


class SequenceValidator:
    """
    Validates event sequence ordering.
    Detects gaps, duplicates, and out-of-order events.
    """
    
    def __init__(
        self,
        max_out_of_order: int = 100,
        gap_timeout_seconds: float = 5.0
    ):
        self.max_out_of_order = max_out_of_order
        self.gap_timeout_seconds = gap_timeout_seconds
        
        # Per-partition tracking
        self._last_sequence: Dict[str, int] = {}
        self._seen_sequences: Dict[str, Set[int]] = {}
        self._gaps: Dict[str, List[SequenceGap]] = {}
        self._out_of_order_buffer: Dict[str, List[Event]] = {}
        
        self._lock = asyncio.Lock()
        
        # Callbacks
        self._on_gap: Optional[Callable[[str, SequenceGap], Awaitable[None]]] = None
        self._on_duplicate: Optional[Callable[[Event], Awaitable[None]]] = None
    
    def on_gap(self, callback: Callable[[str, SequenceGap], Awaitable[None]]):
        """Register gap detection callback"""
        self._on_gap = callback
    
    def on_duplicate(self, callback: Callable[[Event], Awaitable[None]]):
        """Register duplicate detection callback"""
        self._on_duplicate = callback
    
    async def validate(self, event: Event) -> Tuple[bool, str]:
        """
        Validate event sequence.
        
        Returns:
            (is_valid, reason)
        """
        partition = event.metadata.partition_key or "default"
        sequence = event.metadata.sequence_number
        
        async with self._lock:
            # Initialize partition tracking
            if partition not in self._last_sequence:
                self._last_sequence[partition] = 0
                self._seen_sequences[partition] = set()
                self._gaps[partition] = []
                self._out_of_order_buffer[partition] = []
            
            last = self._last_sequence[partition]
            seen = self._seen_sequences[partition]
            
            # Check for duplicate
            if sequence in seen:
                if self._on_duplicate:
                    asyncio.create_task(self._on_duplicate(event))
                return False, "Duplicate sequence"
            
            # Check for gap
            if sequence > last + 1:
                gap = SequenceGap(last + 1, sequence)
                self._gaps[partition].append(gap)
                
                if self._on_gap:
                    asyncio.create_task(self._on_gap(partition, gap))
                
                # Buffer out-of-order event
                if len(self._out_of_order_buffer[partition]) < self.max_out_of_order:
                    self._out_of_order_buffer[partition].append(event)
                    return False, f"Gap detected: {gap.start}-{gap.end}"
            
            # Check for out-of-order (sequence < expected)
            if sequence < last + 1:
                # Might be filling a gap
                if sequence > 0:
                    seen.add(sequence)
                    self._fill_gap(partition, sequence)
                    return True, "Filled gap"
                return False, "Out of order"
            
            # Normal case: sequence == last + 1
            seen.add(sequence)
            self._last_sequence[partition] = sequence
            
            # Limit seen set size
            if len(seen) > 10000:
                min_seq = min(seen)
                seen.discard(min_seq)
            
            return True, "OK"
    
    def _fill_gap(self, partition: str, sequence: int):
        """Update gaps when sequence is filled"""
        gaps = self._gaps[partition]
        new_gaps = []
        
        for gap in gaps:
            if gap.start <= sequence < gap.end:
                # Split or shrink gap
                if sequence == gap.start:
                    if gap.end > gap.start + 1:
                        new_gaps.append(SequenceGap(gap.start + 1, gap.end))
                elif sequence == gap.end - 1:
                    if gap.end > gap.start + 1:
                        new_gaps.append(SequenceGap(gap.start, gap.end - 1))
                else:
                    new_gaps.append(SequenceGap(gap.start, sequence))
                    new_gaps.append(SequenceGap(sequence + 1, gap.end))
            else:
                new_gaps.append(gap)
        
        self._gaps[partition] = new_gaps
    
    async def get_gaps(self, partition: str = None) -> Dict[str, List[SequenceGap]]:
        """Get current gaps"""
        async with self._lock:
            if partition:
                return {partition: self._gaps.get(partition, [])}
            return dict(self._gaps)
    
    async def get_buffered_events(self, partition: str) -> List[Event]:
        """Get buffered out-of-order events"""
        async with self._lock:
            return list(self._out_of_order_buffer.get(partition, []))
    
    async def flush_buffer(self, partition: str) -> List[Event]:
        """Flush and return buffered events"""
        async with self._lock:
            events = self._out_of_order_buffer.get(partition, [])
            self._out_of_order_buffer[partition] = []
            return events
    
    def get_stats(self) -> Dict[str, Any]:
        """Get validation statistics"""
        return {
            'partitions': list(self._last_sequence.keys()),
            'last_sequences': dict(self._last_sequence),
            'gap_counts': {p: len(g) for p, g in self._gaps.items()},
            'buffer_sizes': {p: len(b) for p, b in self._out_of_order_buffer.items()},
        }
