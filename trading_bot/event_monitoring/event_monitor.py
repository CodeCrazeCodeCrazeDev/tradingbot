"""
Elite Trading Bot - Event Monitor

This module provides the core event monitoring functionality for the Elite Trading Bot,
enabling real-time detection and processing of market events, economic announcements,
news, and social media trends.
"""

import enum
import asyncio
import logging
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union
from dataclasses import dataclass, field

# Configure logging
logger = logging.getLogger(__name__)

class EventType(enum.Enum):
    """Types of events that can be monitored."""
    MARKET = "market"           # Price action, volume spikes, liquidity events
    ECONOMIC = "economic"       # Economic data releases, central bank announcements
    NEWS = "news"               # Financial news, company announcements
    SOCIAL_MEDIA = "social"     # Social media trends, sentiment shifts
    TECHNICAL = "technical"     # Technical indicator signals, pattern completions
    LIQUIDITY = "liquidity"     # Liquidity pool formations, sweeps, or imbalances
    VOLATILITY = "volatility"   # Volatility regime changes, spikes
    CORRELATION = "correlation" # Cross-asset correlation shifts
    CUSTOM = "custom"           # User-defined custom events


class EventPriority(enum.Enum):
    """Priority levels for events."""
    CRITICAL = 5    # Immediate action required (e.g., flash crash)
    HIGH = 4        # Urgent attention needed (e.g., major economic release)
    MEDIUM = 3      # Important but not urgent (e.g., trend change)
    LOW = 2         # Routine information (e.g., minor support/resistance test)
    INFORMATIONAL = 1  # Background information (e.g., low-impact news)


class EventSource(enum.Enum):
    """Sources of events."""
    PRICE_ACTION = "price_action"       # Direct market price movements
    ORDER_FLOW = "order_flow"           # Order book and volume analysis
    ECONOMIC_CALENDAR = "economic_calendar"  # Scheduled economic releases
    NEWS_API = "news_api"               # Financial news APIs
    SOCIAL_MEDIA_API = "social_media"   # Twitter, Reddit, StockTwits, etc.
    TECHNICAL_INDICATOR = "technical_indicator"  # Technical analysis signals
    LIQUIDITY_ANALYSIS = "liquidity_analysis"  # Liquidity analysis system
    INSTITUTIONAL_FOOTPRINT = "institutional_footprint"  # Institutional activity
    CUSTOM_SOURCE = "custom_source"     # User-defined sources


@dataclass
class Event:
    """Base class for all event types."""
    id: str
    type: EventType
    priority: EventPriority
    source: EventSource
    timestamp: datetime
    description: str
    raw_data: Dict[str, Any] = field(default_factory=dict)
    processed: bool = False
    acknowledged: bool = False
    related_events: List[str] = field(default_factory=list)
    tags: Set[str] = field(default_factory=set)
    
    def __post_init__(self):
        """Validate event data after initialization."""
        if not self.id:
            raise ValueError("Event ID cannot be empty")


@dataclass(kw_only=True)
class MarketEvent(Event):
    """Market-related events like price action, volume spikes, etc."""
    symbol: str
    price: float
    volume: Optional[float] = None
    timeframe: Optional[str] = None
    previous_price: Optional[float] = None
    price_change_pct: Optional[float] = None
    volume_change_pct: Optional[float] = None
    liquidity_impact: Optional[float] = None
    volatility_impact: Optional[float] = None
    
    def __post_init__(self):
        """Calculate derived metrics if not provided."""
        super().__post_init__()
        if self.previous_price is not None and self.price_change_pct is None:
            self.price_change_pct = (self.price / self.previous_price - 1) * 100


@dataclass(kw_only=True)
class EconomicEvent(Event):
    """Economic data releases, central bank announcements, etc."""
    indicator: str
    actual_value: Optional[float] = None
    forecast_value: Optional[float] = None
    previous_value: Optional[float] = None
    impact_level: Optional[str] = None
    country: Optional[str] = None
    currency: Optional[str] = None
    surprise_factor: Optional[float] = None
    
    def __post_init__(self):
        """Calculate surprise factor if not provided."""
        super().__post_init__()
        if (self.actual_value is not None and 
            self.forecast_value is not None and 
            self.surprise_factor is None and
            self.forecast_value != 0):
            self.surprise_factor = (self.actual_value - self.forecast_value) / abs(self.forecast_value)


@dataclass(kw_only=True)
class NewsEvent(Event):
    """Financial news, company announcements, etc."""
    headline: str
    url: Optional[str] = None
    source: Optional[str] = None
    sentiment_score: Optional[float] = None
    relevance_score: Optional[float] = None
    entities: Dict[str, List[str]] = field(default_factory=dict)
    keywords: List[str] = field(default_factory=list)
    summary: Optional[str] = None


@dataclass(kw_only=True)
class SocialMediaEvent(Event):
    """Social media trends, sentiment shifts, etc."""
    platform: str
    topic: str
    sentiment_score: Optional[float] = None
    volume: Optional[int] = None
    trend_direction: Optional[str] = None
    influential_users: List[str] = field(default_factory=list)
    related_symbols: List[str] = field(default_factory=list)
    sample_posts: List[Dict[str, Any]] = field(default_factory=list)


class EventMonitor:
    """
    Core event monitoring system that detects, processes, and manages events
    from various sources in real-time.
from enum import Enum
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the event monitor.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self.events: Dict[str, Event] = {}
        self.active_sources: Set[EventSource] = set()
        self.event_handlers: Dict[EventType, List[Callable[[Event], None]]] = {}
        self.event_filters: List[Callable[[Event], bool]] = []
        self.running = False
        self.event_queue = asyncio.Queue()
        self.last_processed_timestamp: Dict[EventSource, datetime] = {}
        
        # Initialize default configuration
        self._init_default_config()
        
        logger.info("EventMonitor initialized")
    
    def _init_default_config(self):
        """Initialize default configuration if not provided."""
        defaults = {
            "max_events_stored": 1000,
            "default_priority_threshold": EventPriority.LOW,
            "auto_acknowledge_events": False,
            "event_retention_seconds": 3600,  # 1 hour
            "enable_all_sources": False
        }
        
        for key, value in defaults.items():
            if key not in self.config:
                self.config[key] = value
    
    def register_event_handler(self, event_type: EventType, handler: Callable[[Event], None]):
        """
        Register a handler function for a specific event type.
        
        Args:
            event_type: Type of event to handle
            handler: Function to call when event occurs
        """
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        
        self.event_handlers[event_type].append(handler)
        logger.debug(f"Registered handler for {event_type.value} events")
    
    def register_event_filter(self, filter_func: Callable[[Event], bool]):
        """
        Register a filter function to determine if events should be processed.
        
        Args:
            filter_func: Function that returns True if event should be processed
        """
        self.event_filters.append(filter_func)
        logger.debug("Registered event filter")
    
    def enable_source(self, source: EventSource):
        """
        Enable monitoring for a specific event source.
        
        Args:
            source: Event source to enable
        """
        self.active_sources.add(source)
        logger.info(f"Enabled event source: {source.value}")
    
    def disable_source(self, source: EventSource):
        """
        Disable monitoring for a specific event source.
        
        Args:
            source: Event source to disable
        """
        if source in self.active_sources:
            self.active_sources.remove(source)
            logger.info(f"Disabled event source: {source.value}")
    
    async def add_event(self, event: Event) -> bool:
        """
        Add a new event to the monitoring system.
        
        Args:
            event: Event to add
            
        Returns:
            bool: True if event was added, False if filtered out
        """
        # Check if source is enabled
        if event.source not in self.active_sources:
            logger.debug(f"Event from disabled source {event.source.value} ignored")
            return False
        
        # Apply filters
        for filter_func in self.event_filters:
            if not filter_func(event):
                logger.debug(f"Event {event.id} filtered out")
                return False
        
        # Add to queue for processing
        await self.event_queue.put(event)
        logger.debug(f"Added event {event.id} to queue")
        return True
    
    def get_event(self, event_id: str) -> Optional[Event]:
        """
        Get an event by its ID.
        
        Args:
            event_id: ID of the event to retrieve
            
        Returns:
            Event or None if not found
        """
        return self.events.get(event_id)
    
    def get_events_by_type(self, event_type: EventType) -> List[Event]:
        """
        Get all events of a specific type.
        
        Args:
            event_type: Type of events to retrieve
            
        Returns:
            List of events
        """
        return [event for event in self.events.values() if event.type == event_type]
    
    def get_events_by_priority(self, priority: EventPriority) -> List[Event]:
        """
        Get all events with a specific priority.
        
        Args:
            priority: Priority level of events to retrieve
            
        Returns:
            List of events
        """
        return [event for event in self.events.values() if event.priority == priority]
    
    def acknowledge_event(self, event_id: str) -> bool:
        """
        Mark an event as acknowledged.
        
        Args:
            event_id: ID of the event to acknowledge
            
        Returns:
            bool: True if event was found and acknowledged, False otherwise
        """
        if event_id in self.events:
            self.events[event_id].acknowledged = True
            logger.debug(f"Event {event_id} acknowledged")
            return True
        return False
    
    async def _process_event(self, event: Event):
        """
        Process an event by storing it and calling appropriate handlers.
        
        Args:
            event: Event to process
        """
        # Store event
        self.events[event.id] = event
        self.last_processed_timestamp[event.source] = event.timestamp
        
        # Auto-acknowledge if configured
        if self.config["auto_acknowledge_events"]:
            event.acknowledged = True
        
        # Call handlers
        if event.type in self.event_handlers:
            for handler in self.event_handlers[event.type]:
                try:
                    handler(event)
                except Exception as e:
                    logger.error(f"Error in event handler for {event.id}: {e}")
        
        # Mark as processed
        event.processed = True
        logger.info(f"Processed {event.type.value} event: {event.description}")
        
        # Clean up old events
        await self._cleanup_old_events()
    
    async def _cleanup_old_events(self):
        """Remove old events to prevent memory issues."""
        now = datetime.now()
        retention_seconds = self.config["event_retention_seconds"]
        max_events = self.config["max_events_stored"]
        
        # Remove events older than retention period
        old_events = [
            event_id for event_id, event in self.events.items()
            if (now - event.timestamp).total_seconds() > retention_seconds
        ]
        
        for event_id in old_events:
            del self.events[event_id]
        
        # If still too many events, remove oldest acknowledged events
        if len(self.events) > max_events:
            acknowledged_events = [
                (event_id, event.timestamp) 
                for event_id, event in self.events.items()
                if event.acknowledged
            ]
            
            acknowledged_events.sort(key=lambda x: x[1])  # Sort by timestamp
            
            # Remove oldest events to get under the limit
            events_to_remove = acknowledged_events[:len(self.events) - max_events]
            for event_id, _ in events_to_remove:
                del self.events[event_id]
    
    async def _event_processor_loop(self):
        """Background task to process events from the queue."""
        logger.info("Event processor loop started")
        while self.running:
            try:
                event = await self.event_queue.get()
                await self._process_event(event)
                self.event_queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in event processor loop: {e}")
        logger.info("Event processor loop stopped")
    
    async def start(self):
        """Start the event monitoring system."""
        if self.running:
            logger.warning("Event monitor is already running")
            return
        
        self.running = True
        
        # Enable all sources if configured
        if self.config["enable_all_sources"]:
            for source in EventSource:
                self.active_sources.add(source)
        
        # Start event processor task
        asyncio.create_task(self._event_processor_loop())
        logger.info("Event monitor started")
    
    async def stop(self):
        """Stop the event monitoring system."""
        if not self.running:
            logger.warning("Event monitor is not running")
            return
        
        self.running = False
        logger.info("Event monitor stopped")
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get the current status of the event monitoring system.
        
        Returns:
            Dict with status information
        """
        return {
            "running": self.running,
            "active_sources": [source.value for source in self.active_sources],
            "event_count": len(self.events),
            "unacknowledged_events": sum(1 for event in self.events.values() if not event.acknowledged),
            "queue_size": self.event_queue.qsize(),
            "last_processed": {
                source.value: timestamp.isoformat() 
                for source, timestamp in self.last_processed_timestamp.items()
            }
        }
