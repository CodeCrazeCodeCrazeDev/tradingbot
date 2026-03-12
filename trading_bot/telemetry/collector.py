"""
Telemetry Collector - Collects system telemetry data
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)


@dataclass
class TelemetryEvent:
    name: str
    value: Any
    timestamp: datetime = None
    tags: Dict[str, str] = field(default_factory=dict)
    
    def __post_init__(self):
        try:
            if self.timestamp is None:
                self.timestamp = datetime.utcnow()
        except Exception as e:
            logger.error(f"Error in __post_init__: {e}")
            raise


class TelemetryCollector:
    """Collects and stores telemetry data"""
    
    def __init__(self, config: Dict[str, Any] = None):
        try:
            self.config = config or {}
            self.events: List[TelemetryEvent] = []
            self.max_events = 10000
            self._running = False
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    async def initialize(self, config: Dict[str, Any] = None) -> bool:
        try:
            if config:
                self.config.update(config)
            logger.info("TelemetryCollector initialized")
            return True
        except Exception as e:
            logger.error(f"Error in initialize: {e}")
            raise
    
    async def start(self) -> bool:
        try:
            self._running = True
            logger.info("TelemetryCollector started")
            return True
        except Exception as e:
            logger.error(f"Error in start: {e}")
            raise
    
    async def stop(self) -> bool:
        try:
            self._running = False
            logger.info("TelemetryCollector stopped")
            return True
        except Exception as e:
            logger.error(f"Error in stop: {e}")
            raise
    
    def record(self, name: str, value: Any, tags: Dict[str, str] = None):
        try:
            event = TelemetryEvent(name=name, value=value, tags=tags or {})
            self.events.append(event)
            if len(self.events) > self.max_events:
                self.events = self.events[-self.max_events:]
        except Exception as e:
            logger.error(f"Error in record: {e}")
            raise
    
    def get_events(self, name: str = None, limit: int = 100) -> List[TelemetryEvent]:
        try:
            events = self.events
            if name:
                events = [e for e in events if e.name == name]
            return events[-limit:]
        except Exception as e:
            logger.error(f"Error in get_events: {e}")
            raise


_collector: Optional[TelemetryCollector] = None

def get_collector() -> TelemetryCollector:
    try:
        global _collector
        if _collector is None:
            _collector = TelemetryCollector()
        return _collector
    except Exception as e:
        logger.error(f"Error in get_collector: {e}")
        raise

async def initialize(config: Dict[str, Any] = None) -> bool:
    return await get_collector().initialize(config)

async def start() -> bool:
    return await get_collector().start()

async def stop() -> bool:
    return await get_collector().stop()
