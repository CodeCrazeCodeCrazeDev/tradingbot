"""
Distributed Tracing - OpenTelemetry-compatible tracing for the trading system
"""

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Optional, List
from contextlib import contextmanager

logger = logging.getLogger(__name__)


@dataclass
class Span:
    trace_id: str
    span_id: str
    name: str
    parent_id: Optional[str] = None
    start_time: datetime = None
    end_time: Optional[datetime] = None
    attributes: Dict[str, Any] = field(default_factory=dict)
    events: List[Dict[str, Any]] = field(default_factory=list)
    status: str = "OK"
    
    def __post_init__(self):
        if self.start_time is None:
            self.start_time = datetime.utcnow()
    
    def end(self):
        self.end_time = datetime.utcnow()
    
    def add_event(self, name: str, attributes: Dict[str, Any] = None):
        self.events.append({
            'name': name,
            'timestamp': datetime.utcnow().isoformat(),
            'attributes': attributes or {}
        })
    
    def set_attribute(self, key: str, value: Any):
        self.attributes[key] = value


class Tracer:
    """Distributed tracing manager"""
    
    def __init__(self, service_name: str = "trading-bot"):
        self.service_name = service_name
        self.spans: Dict[str, Span] = {}
        self.active_span: Optional[Span] = None
        self._running = False
    
    async def initialize(self, config: Dict[str, Any] = None) -> bool:
        logger.info(f"Tracer initialized for service: {self.service_name}")
        return True
    
    async def start(self) -> bool:
        self._running = True
        logger.info("Tracer started")
        return True
    
    async def stop(self) -> bool:
        self._running = False
        logger.info("Tracer stopped")
        return True
    
    def start_span(self, name: str, parent: Optional[Span] = None) -> Span:
        trace_id = parent.trace_id if parent else str(uuid.uuid4())
        span = Span(
            trace_id=trace_id,
            span_id=str(uuid.uuid4()),
            name=name,
            parent_id=parent.span_id if parent else None
        )
        self.spans[span.span_id] = span
        self.active_span = span
        return span
    
    @contextmanager
    def trace(self, name: str):
        span = self.start_span(name, self.active_span)
        try:
            yield span
        except Exception as e:
            span.status = "ERROR"
            span.set_attribute("error", str(e))
            raise
        finally:
            span.end()
            if span.parent_id:
                self.active_span = self.spans.get(span.parent_id)
            else:
                self.active_span = None


_tracer: Optional[Tracer] = None

def get_tracer() -> Tracer:
    global _tracer
    if _tracer is None:
        _tracer = Tracer()
    return _tracer

async def initialize(config: Dict[str, Any] = None) -> bool:
    return await get_tracer().initialize(config)

async def start() -> bool:
    return await get_tracer().start()

async def stop() -> bool:
    return await get_tracer().stop()
