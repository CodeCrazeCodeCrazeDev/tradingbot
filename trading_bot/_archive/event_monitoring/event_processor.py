"""
from enum import Enum
Elite Trading Bot - Event Processor

This module provides event processing capabilities for the Elite Trading Bot,
enabling automated responses to detected events based on configurable strategies.
"""

import enum
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union
from dataclasses import dataclass, field

from .event_monitor import (
    EventMonitor, Event, EventType, EventPriority, EventSource,
    MarketEvent, EconomicEvent, NewsEvent, SocialMediaEvent
)

# Configure logging
logger = logging.getLogger(__name__)


class EventResponseStrategy(enum.Enum):
    """Types of response strategies for events."""
    IGNORE = "ignore"                   # Take no action
    NOTIFY = "notify"                   # Generate notification only
    ADJUST_POSITION_SIZE = "adjust_position_size"  # Modify position sizing
    ADJUST_STOP_LOSS = "adjust_stop_loss"  # Modify stop loss levels
    ADJUST_TAKE_PROFIT = "adjust_take_profit"  # Modify take profit levels
    CLOSE_POSITION = "close_position"   # Close existing positions
    ENTER_POSITION = "enter_position"   # Enter new position
    HEDGE = "hedge"                     # Create hedging position
    PAUSE_TRADING = "pause_trading"     # Temporarily pause trading
    RESUME_TRADING = "resume_trading"   # Resume trading
    CUSTOM = "custom"                   # Custom response strategy


@dataclass
class EventFilter:
    """Filter for selecting events to process."""
    event_types: Optional[Set[EventType]] = None
    event_sources: Optional[Set[EventSource]] = None
    min_priority: Optional[EventPriority] = None
    symbols: Optional[Set[str]] = None
    keywords: Optional[Set[str]] = None
    tags: Optional[Set[str]] = None
    
    def matches(self, event: Event) -> bool:
        """
        Check if an event matches this filter.
        
        Args:
            event: Event to check
            
        Returns:
            True if event matches filter, False otherwise
        """
        # Check event type
        if self.event_types and event.type not in self.event_types:
            return False
            
        # Check event source
        if self.event_sources and event.source not in self.event_sources:
            return False
            
        # Check priority
        if self.min_priority and event.priority.value < self.min_priority.value:
            return False
            
        # Check symbol (for market events)
        if self.symbols and isinstance(event, MarketEvent):
            if event.symbol not in self.symbols:
                return False
                
        # Check keywords in description
        if self.keywords:
            if not any(keyword.lower() in event.description.lower() for keyword in self.keywords):
                return False
                
        # Check tags
        if self.tags and event.tags:
            if not any(tag in event.tags for tag in self.tags):
                return False
                
        return True


@dataclass
class EventHandler:
    """Handler for processing events."""
    name: str
    filter: EventFilter
    strategy: EventResponseStrategy
    handler_func: Callable[[Event], Any]
    enabled: bool = True
    last_triggered: Optional[datetime] = None
    cooldown_seconds: int = 0
    execution_count: int = 0
    
    def can_handle(self, event: Event) -> bool:
        """
        Check if this handler can process an event.
        
        Args:
            event: Event to check
            
        Returns:
            True if handler can process event, False otherwise
        """
        if not self.enabled:
            return False
            
        # Check cooldown
        if self.last_triggered and self.cooldown_seconds > 0:
            elapsed = (datetime.now() - self.last_triggered).total_seconds()
            if elapsed < self.cooldown_seconds:
                return False
                
        # Check filter
        return self.filter.matches(event)
    
    async def handle(self, event: Event) -> Any:
        """
        Handle an event.
        
        Args:
            event: Event to handle
            
        Returns:
            Result of handler function
        """
        self.last_triggered = datetime.now()
        self.execution_count += 1
        
        try:
            return await self.handler_func(event)
        except Exception as e:
            logger.error(f"Error in event handler '{self.name}': {e}")
            return None


class EventPrioritizer:
    """Prioritizes events for processing."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize event prioritizer.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self._init_default_config()
        
    def _init_default_config(self):
        """Initialize default configuration if not provided."""
        defaults = {
            "max_events_per_batch": 10,
            "priority_weights": {
                EventPriority.CRITICAL.value: 5.0,
                EventPriority.HIGH.value: 2.0,
                EventPriority.MEDIUM.value: 1.0,
                EventPriority.LOW.value: 0.5,
                EventPriority.INFORMATIONAL.value: 0.1
            },
            "recency_weight": 0.5,  # Weight for recency in scoring
            "recency_window_seconds": 300  # 5 minutes
        }
        
        for key, value in defaults.items():
            if key not in self.config:
                self.config[key] = value
    
    def prioritize(self, events: List[Event]) -> List[Event]:
        """
        Prioritize events for processing.
        
        Args:
            events: List of events to prioritize
            
        Returns:
            Prioritized list of events
        """
        if not events:
            return []
            
        # Calculate scores
        now = datetime.now()
        scored_events = []
        
        for event in events:
            # Base score from priority
            priority_weight = self.config["priority_weights"].get(
                event.priority.value, 1.0
            )
            
            # Recency score
            age_seconds = (now - event.timestamp).total_seconds()
            recency_score = max(0, 1.0 - (age_seconds / self.config["recency_window_seconds"]))
            
            # Combined score
            score = (priority_weight + 
                    self.config["recency_weight"] * recency_score)
            
            scored_events.append((event, score))
        
        # Sort by score (descending)
        scored_events.sort(key=lambda x: x[1], reverse=True)
        
        # Limit to max events per batch
        max_events = self.config["max_events_per_batch"]
        return [event for event, _ in scored_events[:max_events]]


class EventProcessor:
    """
    Event processing system that handles events from the event monitor
    and executes appropriate responses based on configured strategies.
    """
    
    def __init__(self, 
                 event_monitor: EventMonitor,
                 config: Optional[Dict[str, Any]] = None):
        """
        Initialize event processor.
        
        Args:
            event_monitor: Event monitoring system
            config: Optional configuration dictionary
        """
        self.event_monitor = event_monitor
        self.config = config or {}
        self._init_default_config()
        
        # Initialize components
        self.prioritizer = EventPrioritizer(self.config.get("prioritizer_config"))
        
        # Event handlers
        self.handlers: Dict[str, EventHandler] = {}
        
        # Processing state
        self.running = False
        self.processed_events: Set[str] = set()
        self.processing_queue = asyncio.Queue()
        
        logger.info("EventProcessor initialized")
    
    def _init_default_config(self):
        """Initialize default configuration if not provided."""
        defaults = {
            "processing_interval_seconds": 1,
            "max_concurrent_handlers": 5,
            "auto_acknowledge_processed": True,
            "retry_failed_handlers": True,
            "max_retries": 3,
            "retry_delay_seconds": 5
        }
        
        for key, value in defaults.items():
            if key not in self.config:
                self.config[key] = value
    
    def register_handler(self, handler: EventHandler) -> str:
        """
        Register an event handler.
        
        Args:
            handler: Handler to register
            
        Returns:
            Handler name
        """
        self.handlers[handler.name] = handler
        logger.info(f"Registered event handler: {handler.name}")
        return handler.name
    
    def unregister_handler(self, name: str) -> bool:
        """
        Unregister an event handler.
        
        Args:
            name: Handler name
            
        Returns:
            True if handler was unregistered, False if not found
        """
        if name in self.handlers:
            del self.handlers[name]
            logger.info(f"Unregistered event handler: {name}")
            return True
        return False
    
    def enable_handler(self, name: str) -> bool:
        """
        Enable an event handler.
        
        Args:
            name: Handler name
            
        Returns:
            True if handler was enabled, False if not found
        """
        if name in self.handlers:
            self.handlers[name].enabled = True
            logger.info(f"Enabled event handler: {name}")
            return True
        return False
    
    def disable_handler(self, name: str) -> bool:
        """
        Disable an event handler.
        
        Args:
            name: Handler name
            
        Returns:
            True if handler was disabled, False if not found
        """
        if name in self.handlers:
            self.handlers[name].enabled = False
            logger.info(f"Disabled event handler: {name}")
            return True
        return False
    
    async def process_event(self, event: Event) -> List[Tuple[str, Any]]:
        """
        Process a single event with all matching handlers.
        
        Args:
            event: Event to process
            
        Returns:
            List of (handler_name, result) tuples
        """
        if event.id in self.processed_events:
            return []
            
        # Find matching handlers
        matching_handlers = [
            handler for handler in self.handlers.values()
            if handler.can_handle(event)
        ]
        
        if not matching_handlers:
            logger.debug(f"No handlers found for event {event.id}")
            return []
            
        # Process with each handler
        results = []
        
        for handler in matching_handlers:
            try:
                result = await handler.handle(event)
                results.append((handler.name, result))
                logger.info(f"Handler '{handler.name}' processed event {event.id}")
            except Exception as e:
                logger.error(f"Error processing event {event.id} with handler '{handler.name}': {e}")
        
        # Mark as processed
        self.processed_events.add(event.id)
        
        # Auto-acknowledge if configured
        if self.config["auto_acknowledge_processed"]:
            self.event_monitor.acknowledge_event(event.id)
        
        return results
    
    async def _event_processor_loop(self):
        """Background task to process events from the queue."""
        logger.info("Event processor loop started")
        
        while self.running:
            try:
                # Get unprocessed events
                unprocessed_events = [
                    event for event in self.event_monitor.events.values()
                    if event.id not in self.processed_events and event.processed
                ]
                
                if not unprocessed_events:
                    await asyncio.sleep(self.config["processing_interval_seconds"])
                    continue
                
                # Prioritize events
                prioritized_events = self.prioritizer.prioritize(unprocessed_events)
                
                # Process events with concurrency limit
                tasks = []
                semaphore = asyncio.Semaphore(self.config["max_concurrent_handlers"])
                
                async def process_with_semaphore(event):
                    async with semaphore:
                        return await self.process_event(event)
                
                for event in prioritized_events:
                    tasks.append(asyncio.create_task(process_with_semaphore(event)))
                
                if tasks:
                    await asyncio.gather(*tasks)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in event processor loop: {e}")
                await asyncio.sleep(1)  # Avoid tight loop on error
                
        logger.info("Event processor loop stopped")
    
    async def start(self):
        """Start the event processor."""
        if self.running:
            logger.warning("Event processor is already running")
            return
        
        self.running = True
        
        # Start processor loop
        asyncio.create_task(self._event_processor_loop())
        logger.info("Event processor started")
    
    async def stop(self):
        """Stop the event processor."""
        if not self.running:
            logger.warning("Event processor is not running")
            return
        
        self.running = False
        logger.info("Event processor stopped")
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get the current status of the event processor.
        
        Returns:
            Dict with status information
        """
        return {
            "running": self.running,
            "handlers": {
                name: {
                    "enabled": handler.enabled,
                    "execution_count": handler.execution_count,
                    "last_triggered": handler.last_triggered.isoformat() if handler.last_triggered else None,
                    "strategy": handler.strategy.value
                }
                for name, handler in self.handlers.items()
            },
            "processed_events_count": len(self.processed_events)
        }
    
    def create_standard_handlers(self) -> List[str]:
        """
        Create a set of standard event handlers.
        
        Returns:
            List of created handler names
        """
        handler_names = []
        
        # High priority market events handler
        high_priority_market = EventHandler(
            name="high_priority_market",
            filter=EventFilter(
                event_types={EventType.MARKET, EventType.VOLATILITY, EventType.LIQUIDITY},
                min_priority=EventPriority.HIGH
            ),
            strategy=EventResponseStrategy.NOTIFY,
            handler_func=self._handle_high_priority_market
        )
        handler_names.append(self.register_handler(high_priority_market))
        
        # Economic events handler
        economic_events = EventHandler(
            name="economic_events",
            filter=EventFilter(
                event_types={EventType.ECONOMIC},
                min_priority=EventPriority.MEDIUM
            ),
            strategy=EventResponseStrategy.NOTIFY,
            handler_func=self._handle_economic_event
        )
        handler_names.append(self.register_handler(economic_events))
        
        # News events handler
        news_events = EventHandler(
            name="news_events",
            filter=EventFilter(
                event_types={EventType.NEWS},
                min_priority=EventPriority.MEDIUM
            ),
            strategy=EventResponseStrategy.NOTIFY,
            handler_func=self._handle_news_event
        )
        handler_names.append(self.register_handler(news_events))
        
        # Volatility spike handler
        volatility_spike = EventHandler(
            name="volatility_spike",
            filter=EventFilter(
                event_types={EventType.VOLATILITY},
                tags={"significant_increase"}
            ),
            strategy=EventResponseStrategy.ADJUST_POSITION_SIZE,
            handler_func=self._handle_volatility_spike
        )
        handler_names.append(self.register_handler(volatility_spike))
        
        # Liquidity drop handler
        liquidity_drop = EventHandler(
            name="liquidity_drop",
            filter=EventFilter(
                event_types={EventType.LIQUIDITY},
                tags={"significant_decrease"}
            ),
            strategy=EventResponseStrategy.ADJUST_POSITION_SIZE,
            handler_func=self._handle_liquidity_drop
        )
        handler_names.append(self.register_handler(liquidity_drop))
        
        # Correlation breakdown handler
        correlation_breakdown = EventHandler(
            name="correlation_breakdown",
            filter=EventFilter(
                event_types={EventType.CORRELATION}
            ),
            strategy=EventResponseStrategy.NOTIFY,
            handler_func=self._handle_correlation_breakdown
        )
        handler_names.append(self.register_handler(correlation_breakdown))
        
        return handler_names
    
    async def _handle_high_priority_market(self, event: Event) -> Dict[str, Any]:
        """Handle high priority market events."""
        logger.info(f"Handling high priority market event: {event.description}")
        
        # This is a placeholder implementation
        # In a real system, this would integrate with the trading logic
        
        return {
            "event_id": event.id,
            "action": "notify",
            "message": f"High priority market event detected: {event.description}",
            "timestamp": datetime.now().isoformat()
        }
    
    async def _handle_economic_event(self, event: EconomicEvent) -> Dict[str, Any]:
        """Handle economic events."""
        logger.info(f"Handling economic event: {event.description}")
        
        # This is a placeholder implementation
        # In a real system, this would integrate with the trading logic
        
        # Calculate impact score based on surprise factor
        impact_score = abs(event.surprise_factor) if event.surprise_factor is not None else 0.5
        
        return {
            "event_id": event.id,
            "action": "notify",
            "message": f"Economic event detected: {event.description}",
            "impact_score": impact_score,
            "timestamp": datetime.now().isoformat()
        }
    
    async def _handle_news_event(self, event: NewsEvent) -> Dict[str, Any]:
        """Handle news events."""
        logger.info(f"Handling news event: {event.description}")
        
        # This is a placeholder implementation
        # In a real system, this would integrate with the trading logic
        
        return {
            "event_id": event.id,
            "action": "notify",
            "message": f"News event detected: {event.headline}",
            "sentiment": event.sentiment_score,
            "timestamp": datetime.now().isoformat()
        }
    
    async def _handle_volatility_spike(self, event: MarketEvent) -> Dict[str, Any]:
        """Handle volatility spike events."""
        logger.info(f"Handling volatility spike: {event.description}")
        
        # This is a placeholder implementation
        # In a real system, this would integrate with the trading logic
        
        # Calculate position size adjustment based on volatility impact
        adjustment_factor = max(0.25, 1.0 - event.volatility_impact)
        
        return {
            "event_id": event.id,
            "action": "adjust_position_size",
            "symbol": event.symbol,
            "adjustment_factor": adjustment_factor,
            "message": f"Reducing position size to {adjustment_factor:.2f}x due to volatility spike",
            "timestamp": datetime.now().isoformat()
        }
    
    async def _handle_liquidity_drop(self, event: MarketEvent) -> Dict[str, Any]:
        """Handle liquidity drop events."""
        logger.info(f"Handling liquidity drop: {event.description}")
        
        # This is a placeholder implementation
        # In a real system, this would integrate with the trading logic
        
        # Calculate position size adjustment based on liquidity impact
        adjustment_factor = max(0.25, 1.0 - event.liquidity_impact)
        
        return {
            "event_id": event.id,
            "action": "adjust_position_size",
            "symbol": event.symbol,
            "adjustment_factor": adjustment_factor,
            "message": f"Reducing position size to {adjustment_factor:.2f}x due to liquidity drop",
            "timestamp": datetime.now().isoformat()
        }
    
    async def _handle_correlation_breakdown(self, event: MarketEvent) -> Dict[str, Any]:
        """Handle correlation breakdown events."""
        logger.info(f"Handling correlation breakdown: {event.description}")
        
        # This is a placeholder implementation
        # In a real system, this would integrate with the trading logic
        
        return {
            "event_id": event.id,
            "action": "notify",
            "message": f"Correlation breakdown detected: {event.description}",
            "timestamp": datetime.now().isoformat()
        }
