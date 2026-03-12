"""
from typing import Any, List, Optional, Set
AlphaAlgo Tracing - Distributed Tracing

This module provides tracing for request flows.

Version: 1.0.0
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Optional, List
from contextlib import contextmanager
import logging
import uuid
import time
import functools

logger = logging.getLogger(__name__)


@dataclass
class Span:
    """A single span in a trace"""
    span_id: str
    trace_id: str
    parent_id: Optional[str]
    operation: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_ms: float = 0.0
    status: str = "ok"
    tags: Dict[str, Any] = field(default_factory=dict)
    logs: List[Dict[str, Any]] = field(default_factory=list)
    
    def finish(self, status: str = "ok") -> None:
        """Finish the span"""
        self.end_time = datetime.now()
        self.duration_ms = (self.end_time - self.start_time).total_seconds() * 1000
        self.status = status
    
    def set_tag(self, key: str, value: Any) -> None:
        """Set a tag on the span"""
        self.tags[key] = value
    
    def log(self, message: str, data: Optional[Dict[str, Any]] = None) -> None:
        """Add a log entry to the span"""
        self.logs.append({
            'timestamp': datetime.now().isoformat(),
            'message': message,
            'data': data or {}
        })
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'span_id': self.span_id,
            'trace_id': self.trace_id,
            'parent_id': self.parent_id,
            'operation': self.operation,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'duration_ms': self.duration_ms,
            'status': self.status,
            'tags': self.tags,
            'logs': self.logs,
        }


class Tracer:
    """
    Simple tracer for tracking request flows.
    """
    
    def __init__(self, service_name: str = "alphaalgo"):
        self.service_name = service_name
        self._active_spans: Dict[str, Span] = {}
        self._completed_spans: List[Span] = []
        self._max_completed = 10000
        self._current_trace_id: Optional[str] = None
        self._current_span_id: Optional[str] = None
    
    def start_trace(self, operation: str, tags: Optional[Dict[str, Any]] = None) -> Span:
        """Start a new trace"""
        trace_id = str(uuid.uuid4())
        return self.start_span(operation, trace_id=trace_id, tags=tags)
    
    def start_span(
        self,
        operation: str,
        trace_id: Optional[str] = None,
        parent_id: Optional[str] = None,
        tags: Optional[Dict[str, Any]] = None
    ) -> Span:
        """Start a new span"""
        span_id = str(uuid.uuid4())[:16]
        
        # Use current context if not provided
        if trace_id is None:
            trace_id = self._current_trace_id or str(uuid.uuid4())
        if parent_id is None:
            parent_id = self._current_span_id
        
        span = Span(
            span_id=span_id,
            trace_id=trace_id,
            parent_id=parent_id,
            operation=operation,
            start_time=datetime.now(),
            tags=tags or {}
        )
        
        span.tags['service'] = self.service_name
        
        self._active_spans[span_id] = span
        self._current_trace_id = trace_id
        self._current_span_id = span_id
        
        return span
    
    def finish_span(self, span: Span, status: str = "ok") -> None:
        """Finish a span"""
        span.finish(status)
        
        if span.span_id in self._active_spans:
            del self._active_spans[span.span_id]
        
        self._completed_spans.append(span)
        if len(self._completed_spans) > self._max_completed:
            self._completed_spans = self._completed_spans[-self._max_completed:]
        
        # Reset current span to parent
        self._current_span_id = span.parent_id
        
        # Log slow spans
        if span.duration_ms > 1000:
            logger.warning(f"Slow span: {span.operation} took {span.duration_ms:.1f}ms")
    
    @contextmanager
    def span(self, operation: str, tags: Optional[Dict[str, Any]] = None):
        """Context manager for spans"""
        span = self.start_span(operation, tags=tags)
        try:
            yield span
            self.finish_span(span, "ok")
        except Exception as e:
            span.set_tag('error', True)
            span.set_tag('error.message', str(e))
            span.log(f"Error: {e}")
            self.finish_span(span, "error")
            raise
    
    def get_active_spans(self) -> List[Dict[str, Any]]:
        """Get active spans"""
        return [s.to_dict() for s in self._active_spans.values()]
    
    def get_completed_spans(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get completed spans"""
        return [s.to_dict() for s in self._completed_spans[-limit:]]
    
    def get_trace(self, trace_id: str) -> List[Dict[str, Any]]:
        """Get all spans for a trace"""
        spans = [s for s in self._completed_spans if s.trace_id == trace_id]
        spans.extend([s for s in self._active_spans.values() if s.trace_id == trace_id])
        return [s.to_dict() for s in sorted(spans, key=lambda x: x.start_time)]


# =============================================================================
# SINGLETON
# =============================================================================

_tracer_instance: Optional[Tracer] = None


def get_tracer(service_name: str = "alphaalgo") -> Tracer:
    """Get the singleton tracer"""
    global _tracer_instance
    if _tracer_instance is None:
        _tracer_instance = Tracer(service_name)
    return _tracer_instance


# =============================================================================
# DECORATOR
# =============================================================================

def trace(operation: Optional[str] = None, tags: Optional[Dict[str, Any]] = None):
    """Decorator to trace function execution"""
    def decorator(func):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            op_name = operation or f"{func.__module__}.{func.__name__}"
            tracer = get_tracer()
            with tracer.span(op_name, tags=tags) as span:
                span.set_tag('function', func.__name__)
                return await func(*args, **kwargs)
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            op_name = operation or f"{func.__module__}.{func.__name__}"
            tracer = get_tracer()
            with tracer.span(op_name, tags=tags) as span:
                span.set_tag('function', func.__name__)
                return func(*args, **kwargs)
        
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator
