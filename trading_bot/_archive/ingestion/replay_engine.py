"""
AlphaAlgo Replay Engine
=======================
Deterministic replay of historical market data.
Supports backtesting, ML training, and visualization.
"""

from __future__ import annotations

import asyncio
import logging
import time
import struct
import gzip
try:
    import lz4.frame
    LZ4_AVAILABLE = True
except ImportError:
    lz4 = None
    LZ4_AVAILABLE = False
from dataclasses import dataclass, field
from typing import (
    Dict, List, Optional, Callable, Any, 
    AsyncIterator, Iterator, Tuple, Union
)
from datetime import datetime, date, timedelta, timezone
from enum import Enum, auto
from pathlib import Path
import json

from .schema import MarketEvent, EventEnvelope, MarketEventType

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
    symbols: List[str] = field(default_factory=list)
    exchanges: List[str] = field(default_factory=list)
    event_types: List[MarketEventType] = field(default_factory=list)
    
    # Playback
    mode: ReplayMode = ReplayMode.REALTIME
    speed_multiplier: float = 1.0           # For TIME_SCALED mode
    
    # Batching
    batch_size: int = 1000                  # Events per batch
    prefetch_batches: int = 10              # Batches to prefetch
    
    # Ordering
    enforce_ordering: bool = True           # Strict timestamp ordering
    max_out_of_order_ms: int = 100          # Max allowed out-of-order
    
    # Compression
    decompress_on_load: bool = True
    
    # Callbacks
    on_event: Optional[Callable[[MarketEvent], None]] = None
    on_batch: Optional[Callable[[List[MarketEvent]], None]] = None
    on_progress: Optional[Callable[[float], None]] = None


@dataclass
class ReplayCursor:
    """
    Cursor for tracking replay position.
    Supports seeking, bookmarking, and resumption.
    """
    # Position
    current_ts: int = 0                     # Current timestamp (ns)
    current_sequence: int = 0               # Current sequence number
    events_played: int = 0                  # Total events played
    
    # Time range
    start_ts: int = 0
    end_ts: int = 0
    
    # Progress
    @property
    def progress(self) -> float:
        """Progress as fraction 0-1"""
        if self.end_ts <= self.start_ts:
            return 0.0
        return (self.current_ts - self.start_ts) / (self.end_ts - self.start_ts)
    
    @property
    def elapsed_ns(self) -> int:
        """Elapsed time in nanoseconds"""
        return self.current_ts - self.start_ts
    
    @property
    def remaining_ns(self) -> int:
        """Remaining time in nanoseconds"""
        return self.end_ts - self.current_ts
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'current_ts': self.current_ts,
            'current_sequence': self.current_sequence,
            'events_played': self.events_played,
            'start_ts': self.start_ts,
            'end_ts': self.end_ts,
            'progress': self.progress,
        }
    
    def to_bytes(self) -> bytes:
        """Serialize cursor for persistence"""
        return struct.pack(
            '>qqqq',
            self.current_ts,
            self.current_sequence,
            self.start_ts,
            self.end_ts
        )
    
    @classmethod
    def from_bytes(cls, data: bytes) -> 'ReplayCursor':
        """Deserialize cursor"""
        current_ts, current_seq, start_ts, end_ts = struct.unpack('>qqqq', data[:32])
        return cls(
            current_ts=current_ts,
            current_sequence=current_seq,
            start_ts=start_ts,
            end_ts=end_ts
        )


class DataSource:
    """Abstract base for replay data sources"""
    
    async def get_events(
        self,
        start_ts: int,
        end_ts: int,
        symbols: Optional[List[str]] = None,
        exchanges: Optional[List[str]] = None,
        event_types: Optional[List[MarketEventType]] = None,
        limit: int = 10000
    ) -> AsyncIterator[MarketEvent]:
        """Yield events in time order"""
    
        """Get available time range (start_ts, end_ts)"""
    
    async def get_symbols(self) -> List[str]:
        """Get available symbols"""


class FileDataSource(DataSource):
    """
    Data source from compressed files.
    File format: YYYYMMDD_exchange_symbol.events.lz4
    """
    
    def __init__(self, data_dir: Union[str, Path]):
        self.data_dir = Path(data_dir)
        self._file_index: Dict[str, List[Path]] = {}
        self._loaded = False
    
    async def _build_index(self):
        """Build index of available files"""
        if self._loaded:
            return
        
        for file_path in self.data_dir.glob('**/*.events.*'):
            # Parse filename: YYYYMMDD_exchange_symbol.events.lz4
            name = file_path.stem
            if name.endswith('.events'):
                name = name[:-7]  # Remove .events
            
            parts = name.split('_')
            if len(parts) >= 3:
                date_str = parts[0]
                exchange = parts[1]
                symbol = '_'.join(parts[2:])
                
                key = f"{exchange}:{symbol}"
                if key not in self._file_index:
                    self._file_index[key] = []
                self._file_index[key].append(file_path)
        
        # Sort files by date
        for key in self._file_index:
            self._file_index[key].sort()
        
        self._loaded = True
        logger.info(f"Indexed {len(self._file_index)} symbol files")
    
    async def get_events(
        self,
        start_ts: int,
        end_ts: int,
        symbols: Optional[List[str]] = None,
        exchanges: Optional[List[str]] = None,
        event_types: Optional[List[MarketEventType]] = None,
        limit: int = 10000
    ) -> AsyncIterator[MarketEvent]:
        """Yield events from files"""
        await self._build_index()
        
        # Determine which files to read
        files_to_read = []
        
        for key, file_list in self._file_index.items():
            exchange, symbol = key.split(':', 1)
            
            # Filter by exchange/symbol
            if exchanges and exchange not in exchanges:
                continue
            if symbols and symbol not in symbols:
                continue
            
            files_to_read.extend(file_list)
        
        # Read and merge events
        count = 0
        for file_path in sorted(files_to_read):
            async for event in self._read_file(file_path):
                # Filter by time
                if event.exchange_ts < start_ts:
                    continue
                if event.exchange_ts > end_ts:
                    break
                
                # Filter by event type
                if event_types and event.event_type not in event_types:
                    continue
                
                yield event
                count += 1
                
                if count >= limit:
                    return
    
    async def _read_file(self, file_path: Path) -> AsyncIterator[MarketEvent]:
        """Read events from a single file"""
        try:
            # Determine compression
            if file_path.suffix == '.lz4':
                with lz4.frame.open(file_path, 'rb') as f:
                    data = f.read()
            elif file_path.suffix == '.gz':
                with gzip.open(file_path, 'rb') as f:
                    data = f.read()
            else:
                with open(file_path, 'rb') as f:
                    data = f.read()
            
            # Parse events
            offset = 0
            while offset < len(data):
                # Read event length
                if offset + 4 > len(data):
                    break
                event_len = struct.unpack('>I', data[offset:offset+4])[0]
                offset += 4
                
                if offset + event_len > len(data):
                    break
                
                event_data = data[offset:offset+event_len]
                offset += event_len
                
                try:
                    event = MarketEvent.from_bytes(event_data)
                    yield event
                except Exception as e:
                    logger.warning(f"Failed to parse event: {e}")
                    continue
        
        except Exception as e:
            logger.error(f"Failed to read file {file_path}: {e}")
    
    async def get_time_range(self) -> Tuple[int, int]:
        """Get available time range"""
        await self._build_index()
        
        if not self._file_index:
            return 0, 0
        
        # Get from first and last files
        all_files = []
        for files in self._file_index.values():
            all_files.extend(files)
        
        if not all_files:
            return 0, 0
        
        all_files.sort()
        
        # Parse dates from filenames
        first_date = self._parse_date_from_filename(all_files[0])
        last_date = self._parse_date_from_filename(all_files[-1])
        
        start_ts = int(datetime.combine(first_date, datetime.min.time()).timestamp() * 1e9)
        end_ts = int(datetime.combine(last_date, datetime.max.time()).timestamp() * 1e9)
        
        return start_ts, end_ts
    
    def _parse_date_from_filename(self, file_path: Path) -> date:
        """Parse date from filename"""
        name = file_path.stem
        if name.endswith('.events'):
            name = name[:-7]
        
        date_str = name.split('_')[0]
        return datetime.strptime(date_str, '%Y%m%d').date()
    
    async def get_symbols(self) -> List[str]:
        """Get available symbols"""
        await self._build_index()
        return list(self._file_index.keys())


class KafkaDataSource(DataSource):
    """
    Data source from Kafka/Redpanda topics.
    Reads from beginning or specific offset.
    """
    
    def __init__(
        self,
        bootstrap_servers: List[str],
        topics: List[str],
        group_id: str = 'replay-engine'
    ):
        self.bootstrap_servers = bootstrap_servers
        self.topics = topics
        self.group_id = group_id
        self._consumer = None
    
    async def _init_consumer(self):
        """Initialize Kafka consumer"""
        if self._consumer:
            return
        try:
        
            from confluent_kafka import Consumer
            
            config = {
                'bootstrap.servers': ','.join(self.bootstrap_servers),
                'group.id': self.group_id,
                'auto.offset.reset': 'earliest',
                'enable.auto.commit': False,
            }
            
            self._consumer = Consumer(config)
            self._consumer.subscribe(self.topics)
            
        except ImportError:
            logger.error("confluent-kafka not installed")
            raise
    
    async def get_events(
        self,
        start_ts: int,
        end_ts: int,
        symbols: Optional[List[str]] = None,
        exchanges: Optional[List[str]] = None,
        event_types: Optional[List[MarketEventType]] = None,
        limit: int = 10000
    ) -> AsyncIterator[MarketEvent]:
        """Yield events from Kafka"""
        await self._init_consumer()
        
        count = 0
        while count < limit:
            msg = self._consumer.poll(timeout=1.0)
            
            if msg is None:
                continue
            
            if msg.error():
                logger.error(f"Kafka error: {msg.error()}")
                continue
            try:
            
                envelope = EventEnvelope.from_bytes(msg.value())
                
                for event in envelope.events:
                    # Filter by time
                    if event.exchange_ts < start_ts:
                        continue
                    if event.exchange_ts > end_ts:
                        return
                    
                    # Filter by symbol/exchange
                    if symbols and event.symbol not in symbols:
                        continue
                    if exchanges and event.exchange not in exchanges:
                        continue
                    if event_types and event.event_type not in event_types:
                        continue
                    
                    yield event
                    count += 1
                    
                    if count >= limit:
                        return
            
            except Exception as e:
                logger.error(f"Failed to parse message: {e}")
    
    async def get_time_range(self) -> Tuple[int, int]:
        """Get time range from Kafka"""
        # Would need to scan topics - return placeholder
        return 0, int(time.time() * 1e9)
    
    async def get_symbols(self) -> List[str]:
        """Get symbols from Kafka"""
        # Would need to scan topics
        return []


class ReplayEngine:
    """
    Main replay engine for deterministic playback.
    """
    
    def __init__(
        self,
        data_source: DataSource,
        config: Optional[ReplayConfig] = None
    ):
        self.data_source = data_source
        self.config = config or ReplayConfig()
        
        # State
        self.state = ReplayState.IDLE
        self.cursor = ReplayCursor()
        
        # Event buffer
        self._buffer: List[MarketEvent] = []
        self._buffer_lock = asyncio.Lock()
        
        # Playback control
        self._play_task: Optional[asyncio.Task] = None
        self._pause_event = asyncio.Event()
        self._pause_event.set()  # Start unpaused
        
        # Stats
        self._events_replayed: int = 0
        self._start_wall_time: float = 0
        self._last_event_ts: int = 0
        
        logger.info("ReplayEngine initialized")
    
    async def load(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        symbols: Optional[List[str]] = None,
        exchanges: Optional[List[str]] = None
    ):
        """Load data for replay"""
        self.state = ReplayState.LOADING
        
        # Use config or parameters
        start = start_time or self.config.start_time
        end = end_time or self.config.end_time
        syms = symbols or self.config.symbols
        exs = exchanges or self.config.exchanges
        
        # Convert to timestamps
        if start:
            start_ts = int(start.timestamp() * 1e9)
        else:
            start_ts, _ = await self.data_source.get_time_range()
        
        if end:
            end_ts = int(end.timestamp() * 1e9)
        else:
            _, end_ts = await self.data_source.get_time_range()
        
        # Initialize cursor
        self.cursor = ReplayCursor(
            current_ts=start_ts,
            start_ts=start_ts,
            end_ts=end_ts
        )
        
        # Store filter params
        self._symbols = syms
        self._exchanges = exs
        
        self.state = ReplayState.READY
        logger.info(f"Loaded replay: {start_ts} to {end_ts}")
    
    async def play(self):
        """Start or resume playback"""
        if self.state not in (ReplayState.READY, ReplayState.PAUSED):
            logger.warning(f"Cannot play in state {self.state}")
            return
        
        self.state = ReplayState.PLAYING
        self._pause_event.set()
        
        if self._play_task is None or self._play_task.done():
            self._play_task = asyncio.create_task(self._playback_loop())
            self._start_wall_time = time.time()
    
    async def pause(self):
        """Pause playback"""
        if self.state != ReplayState.PLAYING:
            return
        
        self.state = ReplayState.PAUSED
        self._pause_event.clear()
    
    async def stop(self):
        """Stop playback"""
        self.state = ReplayState.IDLE
        
        if self._play_task:
            self._play_task.cancel()
            self._play_task = None
        
        self._pause_event.set()
    
    async def seek(self, timestamp: int):
        """Seek to specific timestamp"""
        was_playing = self.state == ReplayState.PLAYING
        
        if was_playing:
            await self.pause()
        
        self.cursor.current_ts = timestamp
        self._buffer.clear()
        
        if was_playing:
            await self.play()
    
    async def seek_relative(self, offset_ns: int):
        """Seek relative to current position"""
        new_ts = self.cursor.current_ts + offset_ns
        new_ts = max(self.cursor.start_ts, min(new_ts, self.cursor.end_ts))
        await self.seek(new_ts)
    
    async def step(self) -> Optional[MarketEvent]:
        """Step to next event (for STEPPED mode)"""
        if self.state not in (ReplayState.READY, ReplayState.PAUSED):
            return None
        
        # Get next event
        event = await self._get_next_event()
        
        if event:
            self._process_event(event)
            return event
        
        self.state = ReplayState.FINISHED
        return None
    
    async def _playback_loop(self):
        """Main playback loop"""
        try:
            async for event in self.data_source.get_events(
                start_ts=self.cursor.current_ts,
                end_ts=self.cursor.end_ts,
                symbols=self._symbols,
                exchanges=self._exchanges,
                event_types=self.config.event_types or None
            ):
                # Check for pause
                await self._pause_event.wait()
                
                if self.state not in (ReplayState.PLAYING,):
                    break
                
                # Handle timing based on mode
                if self.config.mode == ReplayMode.REALTIME:
                    await self._wait_realtime(event)
                elif self.config.mode == ReplayMode.TIME_SCALED:
                    await self._wait_scaled(event)
                # FAST mode: no waiting
                
                # Process event
                self._process_event(event)
                
                # Update cursor
                self.cursor.current_ts = event.exchange_ts
                self.cursor.current_sequence = event.local_sequence
                self.cursor.events_played += 1
                
                # Progress callback
                if self.config.on_progress:
                    self.config.on_progress(self.cursor.progress)
            
            self.state = ReplayState.FINISHED
            logger.info(f"Replay finished: {self.cursor.events_played} events")
        
        except asyncio.CancelledError:
            logger.info("Replay cancelled")
        except Exception as e:
            logger.error(f"Replay error: {e}")
            self.state = ReplayState.ERROR
    
    async def _wait_realtime(self, event: MarketEvent):
        """Wait to maintain realtime playback"""
        if self._last_event_ts == 0:
            self._last_event_ts = event.exchange_ts
            return
        
        # Calculate how long to wait
        event_delta_ns = event.exchange_ts - self._last_event_ts
        event_delta_s = event_delta_ns / 1e9
        
        if event_delta_s > 0:
            await asyncio.sleep(event_delta_s)
        
        self._last_event_ts = event.exchange_ts
    
    async def _wait_scaled(self, event: MarketEvent):
        """Wait with time scaling"""
        if self._last_event_ts == 0:
            self._last_event_ts = event.exchange_ts
            return
        
        event_delta_ns = event.exchange_ts - self._last_event_ts
        event_delta_s = event_delta_ns / 1e9
        
        # Scale the wait time
        scaled_wait = event_delta_s / self.config.speed_multiplier
        
        if scaled_wait > 0:
            await asyncio.sleep(scaled_wait)
        
        self._last_event_ts = event.exchange_ts
    
    async def _get_next_event(self) -> Optional[MarketEvent]:
        """Get next event from buffer or source"""
        if self._buffer:
            return self._buffer.pop(0)
        
        # Fetch more events
        async for event in self.data_source.get_events(
            start_ts=self.cursor.current_ts,
            end_ts=self.cursor.end_ts,
            symbols=self._symbols,
            exchanges=self._exchanges,
            limit=1
        ):
            return event
        
        return None
    
    def _process_event(self, event: MarketEvent):
        """Process a single event"""
        self._events_replayed += 1
        
        # Call event callback
        if self.config.on_event:
            try:
                self.config.on_event(event)
            except Exception as e:
                logger.error(f"Event callback error: {e}")
    
    def get_cursor(self) -> ReplayCursor:
        """Get current cursor"""
        return self.cursor
    
    def get_stats(self) -> Dict[str, Any]:
        """Get replay statistics"""
        elapsed = time.time() - self._start_wall_time if self._start_wall_time else 0
        
        return {
            'state': self.state.name,
            'events_replayed': self._events_replayed,
            'cursor': self.cursor.to_dict(),
            'elapsed_wall_time': elapsed,
            'events_per_second': self._events_replayed / elapsed if elapsed > 0 else 0,
            'mode': self.config.mode.name,
            'speed_multiplier': self.config.speed_multiplier,
        }


class ReplaySession:
    """
    High-level replay session manager.
    Handles multiple replay engines, bookmarks, and state persistence.
    """
    
    def __init__(self, session_id: str, data_dir: Union[str, Path]):
        self.session_id = session_id
        self.data_dir = Path(data_dir)
        
        self._engines: Dict[str, ReplayEngine] = {}
        self._bookmarks: Dict[str, ReplayCursor] = {}
        
        logger.info(f"ReplaySession created: {session_id}")
    
    def create_engine(
        self,
        engine_id: str,
        data_source: DataSource,
        config: Optional[ReplayConfig] = None
    ) -> ReplayEngine:
        """Create a new replay engine"""
        engine = ReplayEngine(data_source, config)
        self._engines[engine_id] = engine
        return engine
    
    def get_engine(self, engine_id: str) -> Optional[ReplayEngine]:
        """Get replay engine by ID"""
        return self._engines.get(engine_id)
    
    def save_bookmark(self, name: str, engine_id: str):
        """Save current position as bookmark"""
        engine = self._engines.get(engine_id)
        if engine:
            self._bookmarks[name] = ReplayCursor(
                current_ts=engine.cursor.current_ts,
                current_sequence=engine.cursor.current_sequence,
                start_ts=engine.cursor.start_ts,
                end_ts=engine.cursor.end_ts
            )
    
    async def restore_bookmark(self, name: str, engine_id: str):
        """Restore position from bookmark"""
        if name not in self._bookmarks:
            return
        
        engine = self._engines.get(engine_id)
        if engine:
            bookmark = self._bookmarks[name]
            await engine.seek(bookmark.current_ts)
    
    def save_state(self, file_path: Union[str, Path]):
        """Save session state to file"""
        state = {
            'session_id': self.session_id,
            'engines': {
                eid: engine.cursor.to_dict()
                for eid, engine in self._engines.items()
            },
            'bookmarks': {
                name: cursor.to_dict()
                for name, cursor in self._bookmarks.items()
            }
        }
        
        with open(file_path, 'w') as f:
            json.dump(state, f, indent=2)
    
    def load_state(self, file_path: Union[str, Path]):
        """Load session state from file"""
        with open(file_path, 'r') as f:
            state = json.load(f)
        
        # Restore bookmarks
        for name, cursor_dict in state.get('bookmarks', {}).items():
            self._bookmarks[name] = ReplayCursor(
                current_ts=cursor_dict['current_ts'],
                current_sequence=cursor_dict['current_sequence'],
                start_ts=cursor_dict['start_ts'],
                end_ts=cursor_dict['end_ts']
            )
