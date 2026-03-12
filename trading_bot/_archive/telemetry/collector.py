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
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


class TelemetryCollector:
    """Collects and stores telemetry data"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.events: List[TelemetryEvent] = []
        self.max_events = 10000
        self._running = False
    
    async def initialize(self, config: Dict[str, Any] = None) -> bool:
        if config:
            self.config.update(config)
        logger.info("TelemetryCollector initialized")
        return True
    
    async def start(self) -> bool:
        self._running = True
        logger.info("TelemetryCollector started")
        return True
    
    async def stop(self) -> bool:
        self._running = False
        logger.info("TelemetryCollector stopped")
        return True
    
    def record(self, name: str, value: Any, tags: Dict[str, str] = None):
        event = TelemetryEvent(name=name, value=value, tags=tags or {})
        self.events.append(event)
        if len(self.events) > self.max_events:
            self.events = self.events[-self.max_events:]
    
    def get_events(self, name: str = None, limit: int = 100) -> List[TelemetryEvent]:
        events = self.events
        if name:
            events = [e for e in events if e.name == name]
        return events[-limit:]


_collector: Optional[TelemetryCollector] = None

def get_collector() -> TelemetryCollector:
    global _collector
    if _collector is None:
        _collector = TelemetryCollector()
    return _collector

async def initialize(config: Dict[str, Any] = None) -> bool:
    return await get_collector().initialize(config)

async def start() -> bool:
    return await get_collector().start()

async def stop() -> bool:
    return await get_collector().stop()
