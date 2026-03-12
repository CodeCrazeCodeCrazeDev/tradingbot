"""
Replay System - Deterministic Event Replay for Post-Mortem Analysis
Bug reproduction and historical scenario testing
"""

import asyncio
import logging
import json
import pickle
import gzip
from typing import Any, Awaitable, Callable, Dict, Generator, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from enum import Enum
import hashlib

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


class EventType(Enum):
    """Types of recorded events"""
    MARKET_DATA = "market_data"
    ORDER = "order"
    FILL = "fill"
    SIGNAL = "signal"
    POSITION_UPDATE = "position_update"
    RISK_CHECK = "risk_check"
    ERROR = "error"
    SYSTEM = "system"
    USER_ACTION = "user_action"


class ReplaySpeed(Enum):
    """Replay speed options"""
    REALTIME = 1.0
    FAST_2X = 2.0
    FAST_5X = 5.0
    FAST_10X = 10.0
    INSTANT = float('inf')


@dataclass
class RecordedEvent:
    """Single recorded event"""
    event_id: str
    event_type: EventType
    timestamp: datetime
    data: Dict[str, Any]
    source: str
    sequence_number: int
    checksum: str = ""
    
    def __post_init__(self):
        if not self.checksum:
            self.checksum = self._calculate_checksum()
            
    def _calculate_checksum(self) -> str:
        """Calculate event checksum for integrity"""
        content = f"{self.event_id}{self.event_type.value}{self.timestamp.isoformat()}{json.dumps(self.data, sort_keys=True)}"
        return hashlib.md5(content.encode()).hexdigest()[:8]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'event_id': self.event_id,
            'event_type': self.event_type.value,
            'timestamp': self.timestamp.isoformat(),
            'data': self.data,
            'source': self.source,
            'sequence_number': self.sequence_number,
            'checksum': self.checksum
        }
    
    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> 'RecordedEvent':
        return cls(
            event_id=d['event_id'],
            event_type=EventType(d['event_type']),
            timestamp=datetime.fromisoformat(d['timestamp']),
            data=d['data'],
            source=d['source'],
            sequence_number=d['sequence_number'],
            checksum=d.get('checksum', '')
        )


@dataclass
class RecordingSession:
    """Recording session metadata"""
    session_id: str
    name: str
    description: str
    start_time: datetime
    end_time: Optional[datetime] = None
    event_count: int = 0
    symbols: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'session_id': self.session_id,
            'name': self.name,
            'description': self.description,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'event_count': self.event_count,
            'symbols': self.symbols,
            'tags': self.tags,
            'metadata': self.metadata
        }


@dataclass
class ReplayState:
    """Current replay state"""
    session_id: str
    current_index: int
    current_time: datetime
    is_playing: bool
    speed: ReplaySpeed
    events_processed: int
    errors_encountered: int


class EventRecorder:
    """
    Records events for later replay
    """
    
    def __init__(self, storage_path: str = "replay_data"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self.current_session: Optional[RecordingSession] = None
        self.events: List[RecordedEvent] = []
        self.sequence_counter = 0
        self.is_recording = False
        
        logger.info(f"Event recorder initialized, storage: {self.storage_path}")
        
    def start_recording(
        self,
        name: str,
        description: str = "",
        symbols: List[str] = None,
        tags: List[str] = None,
        metadata: Dict[str, Any] = None
    ) -> RecordingSession:
        """Start a new recording session"""
        session_id = f"REC_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        self.current_session = RecordingSession(
            session_id=session_id,
            name=name,
            description=description,
            start_time=datetime.now(),
            symbols=symbols or [],
            tags=tags or [],
            metadata=metadata or {}
        )
        
        self.events = []
        self.sequence_counter = 0
        self.is_recording = True
        
        logger.info(f"Started recording session: {name} ({session_id})")
        return self.current_session
    
    def record_event(
        self,
        event_type: EventType,
        data: Dict[str, Any],
        source: str = "system"
    ) -> Optional[RecordedEvent]:
        """Record a single event"""
        if not self.is_recording or not self.current_session:
            return None
            
        event = RecordedEvent(
            event_id=f"{self.current_session.session_id}_{self.sequence_counter}",
            event_type=event_type,
            timestamp=datetime.now(),
            data=data,
            source=source,
            sequence_number=self.sequence_counter
        )
        
        self.events.append(event)
        self.sequence_counter += 1
        self.current_session.event_count = len(self.events)
        
        return event
    
    def record_market_data(self, symbol: str, data: Dict[str, Any]):
        """Convenience method for market data"""
        return self.record_event(
            EventType.MARKET_DATA,
            {'symbol': symbol, **data},
            source='market_data'
        )
    
    def record_order(self, order_data: Dict[str, Any]):
        """Convenience method for orders"""
        return self.record_event(EventType.ORDER, order_data, source='order_manager')
    
    def record_fill(self, fill_data: Dict[str, Any]):
        """Convenience method for fills"""
        return self.record_event(EventType.FILL, fill_data, source='execution')
    
    def record_signal(self, signal_data: Dict[str, Any]):
        """Convenience method for signals"""
        return self.record_event(EventType.SIGNAL, signal_data, source='strategy')
    
    def record_error(self, error_data: Dict[str, Any]):
        """Convenience method for errors"""
        return self.record_event(EventType.ERROR, error_data, source='error_handler')
    
    def stop_recording(self) -> Optional[str]:
        """Stop recording and save session"""
        if not self.is_recording or not self.current_session:
            return None
            
        self.current_session.end_time = datetime.now()
        self.is_recording = False
        
        # Save to file
        filepath = self._save_session()
        
        logger.info(f"Stopped recording: {self.current_session.event_count} events saved to {filepath}")
        
        session_id = self.current_session.session_id
        self.current_session = None
        
        return filepath
    
    def _save_session(self) -> str:
        """Save session to file"""
        if not self.current_session:
            return ""
            
        filepath = self.storage_path / f"{self.current_session.session_id}.replay"
        
        data = {
            'session': self.current_session.to_dict(),
            'events': [e.to_dict() for e in self.events]
        }
        
        # Compress and save
        with gzip.open(filepath, 'wt', encoding='utf-8') as f:
            json.dump(data, f)
            
        return str(filepath)
    
    def list_sessions(self) -> List[RecordingSession]:
        """List all saved sessions"""
        sessions = []
        
        for filepath in self.storage_path.glob("*.replay"):
            try:
                with gzip.open(filepath, 'rt', encoding='utf-8') as f:
                    data = json.load(f)
                    session_data = data['session']
                    session_data['start_time'] = datetime.fromisoformat(session_data['start_time'])
                    if session_data['end_time']:
                        session_data['end_time'] = datetime.fromisoformat(session_data['end_time'])
                    sessions.append(RecordingSession(**session_data))
            except Exception as e:
                logger.warning(f"Failed to load session {filepath}: {e}")
                
        return sorted(sessions, key=lambda s: s.start_time, reverse=True)


class EventReplayer:
    """
    Replays recorded events for analysis and testing
    """
    
    def __init__(self, storage_path: str = "replay_data"):
        self.storage_path = Path(storage_path)
        
        self.current_session: Optional[RecordingSession] = None
        self.events: List[RecordedEvent] = []
        self.state: Optional[ReplayState] = None
        
        # Event handlers
        self.handlers: Dict[EventType, List[Callable]] = {
            event_type: [] for event_type in EventType
        }
        
        # Replay control
        self._stop_requested = False
        self._pause_requested = False
        
        logger.info("Event replayer initialized")
        
    def load_session(self, session_id: str) -> bool:
        """Load a recorded session"""
        filepath = self.storage_path / f"{session_id}.replay"
        
        if not filepath.exists():
            logger.error(f"Session file not found: {filepath}")
            return False
        try:
            
            with gzip.open(filepath, 'rt', encoding='utf-8') as f:
                data = json.load(f)
                
            # Load session metadata
            session_data = data['session']
            session_data['start_time'] = datetime.fromisoformat(session_data['start_time'])
            if session_data['end_time']:
                session_data['end_time'] = datetime.fromisoformat(session_data['end_time'])
            self.current_session = RecordingSession(**session_data)
            
            # Load events
            self.events = [RecordedEvent.from_dict(e) for e in data['events']]
            
            logger.info(f"Loaded session {session_id}: {len(self.events)} events")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load session: {e}")
            return False
    
    def register_handler(
        self,
        event_type: EventType,
        handler: Callable[[RecordedEvent], Any]
    ):
        """Register event handler"""
        self.handlers[event_type].append(handler)
        
    def register_async_handler(
        self,
        event_type: EventType,
        handler: Callable[[RecordedEvent], Awaitable[Any]]
    ):
        """Register async event handler"""
        self.handlers[event_type].append(handler)
    
    async def replay(
        self,
        speed: ReplaySpeed = ReplaySpeed.INSTANT,
        start_index: int = 0,
        end_index: Optional[int] = None,
        event_filter: Optional[Callable[[RecordedEvent], bool]] = None
    ) -> ReplayState:
        """
        Replay events
        
        Args:
            speed: Replay speed
            start_index: Starting event index
            end_index: Ending event index (None = all)
            event_filter: Optional filter function
        """
        if not self.events:
            raise ValueError("No session loaded")
            
        end_idx = end_index or len(self.events)
        
        self.state = ReplayState(
            session_id=self.current_session.session_id if self.current_session else "",
            current_index=start_index,
            current_time=self.events[start_index].timestamp if self.events else datetime.now(),
            is_playing=True,
            speed=speed,
            events_processed=0,
            errors_encountered=0
        )
        
        self._stop_requested = False
        self._pause_requested = False
        
        logger.info(f"Starting replay at {speed.name} speed, events {start_index} to {end_idx}")
        
        prev_timestamp = None
        
        for i in range(start_index, end_idx):
            if self._stop_requested:
                break
                
            while self._pause_requested:
                await asyncio.sleep(0.1)
                if self._stop_requested:
                    break
                    
            event = self.events[i]
            
            # Apply filter
            if event_filter and not event_filter(event):
                continue
                
            # Calculate delay for realistic replay
            if speed != ReplaySpeed.INSTANT and prev_timestamp:
                delay = (event.timestamp - prev_timestamp).total_seconds()
                if delay > 0:
                    await asyncio.sleep(delay / speed.value)
                    
            prev_timestamp = event.timestamp
            
            # Process event
            try:
                await self._process_event(event)
                self.state.events_processed += 1
            except Exception as e:
                logger.error(f"Error processing event {event.event_id}: {e}")
                self.state.errors_encountered += 1
                
            self.state.current_index = i
            self.state.current_time = event.timestamp
            
        self.state.is_playing = False
        logger.info(f"Replay complete: {self.state.events_processed} events processed, {self.state.errors_encountered} errors")
        
        return self.state
    
    async def _process_event(self, event: RecordedEvent):
        """Process a single event"""
        handlers = self.handlers.get(event.event_type, [])
        
        for handler in handlers:
            if asyncio.iscoroutinefunction(handler):
                await handler(event)
            else:
                handler(event)
    
    def pause(self):
        """Pause replay"""
        self._pause_requested = True
        if self.state:
            self.state.is_playing = False
            
    def resume(self):
        """Resume replay"""
        self._pause_requested = False
        if self.state:
            self.state.is_playing = True
            
    def stop(self):
        """Stop replay"""
        self._stop_requested = True
        self._pause_requested = False
        
    def seek(self, index: int):
        """Seek to specific event index"""
        if self.state and 0 <= index < len(self.events):
            self.state.current_index = index
            self.state.current_time = self.events[index].timestamp
            
    def get_events_by_type(self, event_type: EventType) -> List[RecordedEvent]:
        """Get all events of a specific type"""
        return [e for e in self.events if e.event_type == event_type]
    
    def get_events_in_range(
        self,
        start_time: datetime,
        end_time: datetime
    ) -> List[RecordedEvent]:
        """Get events in time range"""
        return [e for e in self.events if start_time <= e.timestamp <= end_time]
    
    def find_errors(self) -> List[RecordedEvent]:
        """Find all error events"""
        return self.get_events_by_type(EventType.ERROR)
    
    def get_event_timeline(self) -> Dict[str, List[RecordedEvent]]:
        """Get events grouped by type"""
        timeline = {et.value: [] for et in EventType}
        for event in self.events:
            timeline[event.event_type.value].append(event)
        return timeline
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate replay analysis report"""
        if not self.current_session:
            return {}
            
        timeline = self.get_event_timeline()
        errors = self.find_errors()
        
        # Calculate statistics
        duration = (self.events[-1].timestamp - self.events[0].timestamp).total_seconds() if self.events else 0
        
        return {
            'session': self.current_session.to_dict(),
            'statistics': {
                'total_events': len(self.events),
                'duration_seconds': duration,
                'events_per_second': len(self.events) / duration if duration > 0 else 0,
                'by_type': {k: len(v) for k, v in timeline.items()},
                'error_count': len(errors)
            },
            'errors': [e.to_dict() for e in errors[:10]],  # First 10 errors
            'first_event': self.events[0].to_dict() if self.events else None,
            'last_event': self.events[-1].to_dict() if self.events else None
        }


class ReplaySystem:
    """
    Combined recording and replay system
    """
    
    def __init__(self, storage_path: str = "replay_data"):
        self.recorder = EventRecorder(storage_path)
        self.replayer = EventReplayer(storage_path)
        
    def start_recording(self, name: str, **kwargs) -> RecordingSession:
        return self.recorder.start_recording(name, **kwargs)
    
    def stop_recording(self) -> Optional[str]:
        return self.recorder.stop_recording()
    
    def record(self, event_type: EventType, data: Dict[str, Any], source: str = "system"):
        return self.recorder.record_event(event_type, data, source)
    
    def load_session(self, session_id: str) -> bool:
        return self.replayer.load_session(session_id)
    
    async def replay(self, **kwargs) -> ReplayState:
        return await self.replayer.replay(**kwargs)
    
    def list_sessions(self) -> List[RecordingSession]:
        return self.recorder.list_sessions()
    
    def register_handler(self, event_type: EventType, handler: Callable):
        self.replayer.register_handler(event_type, handler)
