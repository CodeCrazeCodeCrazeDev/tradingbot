"""
AlphaAlgo Event Replay
=======================
Deterministic replay of events for backtesting, recovery, and debugging.
Supports multiple replay modes and time warping.
"""

from __future__ import annotations

import asyncio
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum, auto
from typing import (
    Dict, List, Optional, Any, Callable, Awaitable,
    AsyncIterator, Iterator, Tuple
)

from .events import Event, EventType
from .event_store import EventStore, EventQuery

logger = logging.getLogger(__name__)


class ReplayMode(Enum):
    """Replay playback modes"""
    REALTIME = auto()       # Play at original speed
    FAST = auto()           # Play as fast as possible
    STEPPED = auto()        # Step through events manually
    TIME_SCALED = auto()    # Play at scaled speed (e.g., 10x)


class ReplayState(Enum):
    """Replay engine states"""
    IDLE = auto()
    LOADING = auto()
    READY = auto()
    PLAYING = auto()
    PAUSED = auto()
    FINISHED = auto()
    ERROR = auto()


@dataclass
class ReplayConfig:
    """Configuration for replay engine"""
    # Time range
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    
    # Filtering
    event_types: List[EventType] = field(default_factory=list)
    partition_keys: List[str] = field(default_factory=list)
    sources: List[str] = field(default_factory=list)
    
    # Playback
    mode: ReplayMode = ReplayMode.REALTIME
    speed_multiplier: float = 1.0           # For TIME_SCALED mode
    
    # Batching
    batch_size: int = 1000
    prefetch_batches: int = 5
    
    # Callbacks
    on_event: Optional[Callable[[Event], Awaitable[None]]] = None
    on_progress: Optional[Callable[[float], None]] = None
    on_complete: Optional[Callable[[], Awaitable[None]]] = None


@dataclass
class ReplayProgress:
    """Tracks replay progress"""
    total_events: int = 0
    events_played: int = 0
    current_timestamp_ns: int = 0
    start_timestamp_ns: int = 0
    end_timestamp_ns: int = 0
    
    @property
    def progress(self) -> float:
        """Progress as fraction 0-1"""
        if self.total_events == 0:
            return 0.0
        return self.events_played / self.total_events
    
    @property
    def time_progress(self) -> float:
        """Time-based progress as fraction 0-1"""
        if self.end_timestamp_ns <= self.start_timestamp_ns:
            return 0.0
        return (self.current_timestamp_ns - self.start_timestamp_ns) / (
            self.end_timestamp_ns - self.start_timestamp_ns
        )


class TimeWarp:
    """
    Time warping for replay.
    Maps replay time to simulated time.
    """
    
    def __init__(self, speed_multiplier: float = 1.0):
        self.speed_multiplier = speed_multiplier
        self._start_real_ns: int = 0
        self._start_sim_ns: int = 0
        self._paused: bool = False
        self._pause_ns: int = 0
    
    def start(self, sim_start_ns: int):
        """Start time warping from simulation start time"""
        self._start_real_ns = time.time_ns()
        self._start_sim_ns = sim_start_ns
        self._paused = False
    
    def pause(self):
        """Pause time warping"""
        if not self._paused:
            self._pause_ns = time.time_ns()
            self._paused = True
    
    def resume(self):
        """Resume time warping"""
        if self._paused:
            pause_duration = time.time_ns() - self._pause_ns
            self._start_real_ns += pause_duration
            self._paused = False
    
    def get_sim_time_ns(self) -> int:
        """Get current simulated time in nanoseconds"""
        if self._paused:
            real_elapsed = self._pause_ns - self._start_real_ns
        else:
            real_elapsed = time.time_ns() - self._start_real_ns
        
        sim_elapsed = int(real_elapsed * self.speed_multiplier)
        return self._start_sim_ns + sim_elapsed
    
    async def wait_until(self, target_ns: int):
        """Wait until simulated time reaches target"""
        if self.speed_multiplier <= 0:
            return
        
        current = self.get_sim_time_ns()
        if current >= target_ns:
            return
        
        # Calculate real wait time
        sim_wait = target_ns - current
        real_wait = sim_wait / self.speed_multiplier
        
        await asyncio.sleep(real_wait / 1e9)


class EventReplay:
    """
    Deterministic event replay engine.
    Replays events from the event store for backtesting or recovery.
    """
    
    def __init__(
        self,
        event_store: EventStore,
        config: ReplayConfig = None
    ):
        self.event_store = event_store
        self.config = config or ReplayConfig()
        
        # State
        self.state = ReplayState.IDLE
        self.progress = ReplayProgress()
        
        # Time warping
        self.time_warp = TimeWarp(self.config.speed_multiplier)
        
        # Event buffer
        self._buffer: List[Event] = []
        self._buffer_index: int = 0
        
        # Control
        self._step_event = asyncio.Event()
        self._stop_requested = False
        
        # Metrics
        self.metrics = {
            'events_replayed': 0,
            'replay_duration_ms': 0,
            'avg_event_delay_ms': 0,
        }
        
        logger.info("EventReplay initialized")
    
    async def load(self) -> int:
        """
        Load events for replay.
        
        Returns:
            Number of events loaded
        """
        self.state = ReplayState.LOADING
        
        # Build query
        query = EventQuery(
            event_types=self.config.event_types,
            partition_keys=self.config.partition_keys,
            sources=self.config.sources,
            ascending=True,
            limit=100000,  # Load in chunks
        )
        
        if self.config.start_time:
            query.start_time_ns = int(self.config.start_time.timestamp() * 1e9)
        if self.config.end_time:
            query.end_time_ns = int(self.config.end_time.timestamp() * 1e9)
        
        # Load events
        self._buffer = await self.event_store.query(query)
        self._buffer_index = 0
        
        # Update progress
        self.progress.total_events = len(self._buffer)
        self.progress.events_played = 0
        
        if self._buffer:
            self.progress.start_timestamp_ns = self._buffer[0].metadata.timestamp_ns
            self.progress.end_timestamp_ns = self._buffer[-1].metadata.timestamp_ns
        
        self.state = ReplayState.READY
        logger.info(f"Loaded {len(self._buffer)} events for replay")
        
        return len(self._buffer)
    
    async def play(self):
        """Start or resume replay"""
        if self.state == ReplayState.IDLE:
            await self.load()
        
        if self.state not in (ReplayState.READY, ReplayState.PAUSED):
            logger.warning(f"Cannot play in state {self.state}")
            return
        
        self.state = ReplayState.PLAYING
        self._stop_requested = False
        
        # Start time warp
        if self._buffer:
            self.time_warp.start(self._buffer[0].metadata.timestamp_ns)
        
        start_time = time.time()
        
        try:
            await self._replay_loop()
        finally:
            elapsed = (time.time() - start_time) * 1000
            self.metrics['replay_duration_ms'] = elapsed
            
            if self.state == ReplayState.PLAYING:
                self.state = ReplayState.FINISHED
    
    async def _replay_loop(self):
        """Main replay loop"""
        while self._buffer_index < len(self._buffer):
            if self._stop_requested:
                break
            
            if self.state == ReplayState.PAUSED:
                await asyncio.sleep(0.1)
                continue
            
            event = self._buffer[self._buffer_index]
            
            # Handle replay mode
            if self.config.mode == ReplayMode.STEPPED:
                # Wait for step signal
                await self._step_event.wait()
                self._step_event.clear()
            
            elif self.config.mode == ReplayMode.REALTIME:
                # Wait for real time
                await self.time_warp.wait_until(event.metadata.timestamp_ns)
            
            elif self.config.mode == ReplayMode.TIME_SCALED:
                # Wait for scaled time
                await self.time_warp.wait_until(event.metadata.timestamp_ns)
            
            # FAST mode: no waiting
            
            # Dispatch event
            await self._dispatch_event(event)
            
            # Update progress
            self._buffer_index += 1
            self.progress.events_played = self._buffer_index
            self.progress.current_timestamp_ns = event.metadata.timestamp_ns
            self.metrics['events_replayed'] += 1
            
            # Progress callback
            if self.config.on_progress:
                self.config.on_progress(self.progress.progress)
        
        # Completion callback
        if self.config.on_complete and not self._stop_requested:
            await self.config.on_complete()
    
    async def _dispatch_event(self, event: Event):
        """Dispatch event to handler"""
        if self.config.on_event:
            try:
                await self.config.on_event(event)
            except Exception as e:
                logger.error(f"Error dispatching event {event.event_id}: {e}")
    
    async def pause(self):
        """Pause replay"""
        if self.state == ReplayState.PLAYING:
            self.state = ReplayState.PAUSED
            self.time_warp.pause()
            logger.info("Replay paused")
    
    async def resume(self):
        """Resume replay"""
        if self.state == ReplayState.PAUSED:
            self.state = ReplayState.PLAYING
            self.time_warp.resume()
            logger.info("Replay resumed")
    
    async def stop(self):
        """Stop replay"""
        self._stop_requested = True
        self.state = ReplayState.IDLE
        logger.info("Replay stopped")
    
    def step(self):
        """Step to next event (for STEPPED mode)"""
        if self.config.mode == ReplayMode.STEPPED:
            self._step_event.set()
    
    async def seek(self, position: float):
        """
        Seek to position in replay.
        
        Args:
            position: Position as fraction 0-1
        """
        if not self._buffer:
            return
        
        target_index = int(position * len(self._buffer))
        target_index = max(0, min(target_index, len(self._buffer) - 1))
        
        self._buffer_index = target_index
        self.progress.events_played = target_index
        
        if target_index < len(self._buffer):
            event = self._buffer[target_index]
            self.progress.current_timestamp_ns = event.metadata.timestamp_ns
            self.time_warp.start(event.metadata.timestamp_ns)
        
        logger.info(f"Seeked to position {position:.2%}")
    
    async def seek_to_time(self, target_time: datetime):
        """Seek to specific time"""
        target_ns = int(target_time.timestamp() * 1e9)
        
        # Binary search for target time
        left, right = 0, len(self._buffer) - 1
        
        while left < right:
            mid = (left + right) // 2
            if self._buffer[mid].metadata.timestamp_ns < target_ns:
                left = mid + 1
            else:
                right = mid
        
        self._buffer_index = left
        self.progress.events_played = left
        
        if left < len(self._buffer):
            self.progress.current_timestamp_ns = self._buffer[left].metadata.timestamp_ns
            self.time_warp.start(self._buffer[left].metadata.timestamp_ns)
        
        logger.info(f"Seeked to time {target_time}")
    
    def set_speed(self, multiplier: float):
        """Set replay speed multiplier"""
        self.config.speed_multiplier = multiplier
        self.time_warp.speed_multiplier = multiplier
        logger.info(f"Replay speed set to {multiplier}x")
    
    def get_current_event(self) -> Optional[Event]:
        """Get current event"""
        if 0 <= self._buffer_index < len(self._buffer):
            return self._buffer[self._buffer_index]
        return None
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get replay metrics"""
        return {
            **self.metrics,
            'state': self.state.name,
            'progress': self.progress.progress,
            'time_progress': self.progress.time_progress,
            'total_events': self.progress.total_events,
            'events_played': self.progress.events_played,
            'speed': self.config.speed_multiplier,
        }


class ReplaySession:
    """
    Manages a complete replay session with state persistence.
    Supports checkpointing and resumption.
    """
    
    def __init__(
        self,
        session_id: str,
        event_store: EventStore,
        config: ReplayConfig = None
    ):
        self.session_id = session_id
        self.event_store = event_store
        self.config = config or ReplayConfig()
        
        self.replay = EventReplay(event_store, config)
        
        # Checkpoints
        self._checkpoints: Dict[str, int] = {}
        
        # Session state
        self._created_at = datetime.now(timezone.utc)
        self._started_at: Optional[datetime] = None
        self._finished_at: Optional[datetime] = None
    
    async def start(self):
        """Start the replay session"""
        self._started_at = datetime.now(timezone.utc)
        await self.replay.load()
        await self.replay.play()
        self._finished_at = datetime.now(timezone.utc)
    
    def create_checkpoint(self, name: str):
        """Create a named checkpoint at current position"""
        self._checkpoints[name] = self.replay._buffer_index
        logger.info(f"Checkpoint '{name}' created at position {self.replay._buffer_index}")
    
    async def restore_checkpoint(self, name: str) -> bool:
        """Restore to a named checkpoint"""
        if name not in self._checkpoints:
            return False
        
        position = self._checkpoints[name]
        await self.replay.seek(position / max(1, self.replay.progress.total_events))
        logger.info(f"Restored to checkpoint '{name}'")
        return True
    
    def get_session_info(self) -> Dict[str, Any]:
        """Get session information"""
        return {
            'session_id': self.session_id,
            'created_at': self._created_at.isoformat(),
            'started_at': self._started_at.isoformat() if self._started_at else None,
            'finished_at': self._finished_at.isoformat() if self._finished_at else None,
            'state': self.replay.state.name,
            'progress': self.replay.progress.progress,
            'checkpoints': list(self._checkpoints.keys()),
            'metrics': self.replay.get_metrics(),
        }
