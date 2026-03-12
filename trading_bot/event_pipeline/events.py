"""
AlphaAlgo Event Definitions
============================
Immutable event types with versioning, causality tracking, and serialization.
All events are append-only and form the source of truth.
"""

from __future__ import annotations

import uuid
import time
import hashlib
import json
import struct
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import IntEnum, auto
from typing import (
    Dict, List, Optional, Any, Union, TypeVar, Generic,
    Callable, Type, Tuple
)

import logging
logger = logging.getLogger(__name__)


# Event version for schema evolution
EVENT_SCHEMA_VERSION = "1.0.0"
EVENT_MAGIC = 0xEE01  # Event magic number


class EventType(IntEnum):
    """Event type discriminator"""
    # Market Data Events (1-99)
    MARKET_DATA = 1
    TRADE = 2
    QUOTE = 3
    ORDERBOOK_SNAPSHOT = 4
    ORDERBOOK_DELTA = 5
    BAR = 6
    TICK = 7
    
    # Signal Events (100-199)
    SIGNAL_GENERATED = 100
    SIGNAL_VALIDATED = 101
    SIGNAL_EXPIRED = 102
    SIGNAL_CANCELLED = 103
    
    # Order Events (200-299)
    ORDER_CREATED = 200
    ORDER_SUBMITTED = 201
    ORDER_ACCEPTED = 202
    ORDER_REJECTED = 203
    ORDER_FILLED = 204
    ORDER_PARTIALLY_FILLED = 205
    ORDER_CANCELLED = 206
    ORDER_EXPIRED = 207
    ORDER_AMENDED = 208
    
    # Execution Events (300-399)
    EXECUTION_STARTED = 300
    EXECUTION_COMPLETED = 301
    EXECUTION_FAILED = 302
    FILL_RECEIVED = 303
    SLIPPAGE_DETECTED = 304
    
    # Risk Events (400-499)
    RISK_LIMIT_BREACH = 400
    RISK_WARNING = 401
    POSITION_LIMIT_REACHED = 402
    DRAWDOWN_ALERT = 403
    MARGIN_CALL = 404
    CIRCUIT_BREAKER_TRIGGERED = 405
    
    # System Events (500-599)
    SYSTEM_STARTED = 500
    SYSTEM_STOPPED = 501
    SYSTEM_ERROR = 502
    SYSTEM_WARNING = 503
    HEALTH_CHECK = 504
    CONFIG_CHANGED = 505
    
    # Portfolio Events (600-699)
    POSITION_OPENED = 600
    POSITION_CLOSED = 601
    POSITION_UPDATED = 602
    PNL_UPDATED = 603
    
    # Custom Events (900-999)
    CUSTOM = 900


class EventPriority(IntEnum):
    """Event priority levels"""
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3
    EMERGENCY = 4


@dataclass(frozen=True, slots=True)
class EventMetadata:
    """
    Immutable event metadata for tracking, correlation, and causality.
    """
    # Identity
    event_id: str                           # Unique event ID (UUID)
    event_type: EventType                   # Type discriminator
    version: str = EVENT_SCHEMA_VERSION     # Schema version
    
    # Timing (nanosecond precision)
    timestamp_ns: int = 0                   # Event timestamp (ns since epoch)
    created_at_ns: int = 0                  # Creation timestamp
    received_at_ns: int = 0                 # Receipt timestamp
    
    # Ordering
    sequence_number: int = 0                # Global sequence number
    partition_key: str = ""                 # Partition key for sharding
    
    # Causality
    correlation_id: str = ""                # Request correlation ID
    causation_id: str = ""                  # ID of causing event
    parent_id: str = ""                     # Parent event ID
    
    # Source
    source: str = ""                        # Event source (service name)
    source_instance: str = ""               # Source instance ID
    
    # Priority
    priority: EventPriority = EventPriority.NORMAL
    
    # Idempotency
    idempotency_key: str = ""               # For exactly-once processing
    
    # Retry tracking
    retry_count: int = 0
    max_retries: int = 3
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'event_id': self.event_id,
            'event_type': self.event_type.value,
            'version': self.version,
            'timestamp_ns': self.timestamp_ns,
            'created_at_ns': self.created_at_ns,
            'received_at_ns': self.received_at_ns,
            'sequence_number': self.sequence_number,
            'partition_key': self.partition_key,
            'correlation_id': self.correlation_id,
            'causation_id': self.causation_id,
            'parent_id': self.parent_id,
            'source': self.source,
            'source_instance': self.source_instance,
            'priority': self.priority.value,
            'idempotency_key': self.idempotency_key,
            'retry_count': self.retry_count,
            'max_retries': self.max_retries,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EventMetadata':
        return cls(
            event_id=data['event_id'],
            event_type=EventType(data['event_type']),
            version=data.get('version', EVENT_SCHEMA_VERSION),
            timestamp_ns=data.get('timestamp_ns', 0),
            created_at_ns=data.get('created_at_ns', 0),
            received_at_ns=data.get('received_at_ns', 0),
            sequence_number=data.get('sequence_number', 0),
            partition_key=data.get('partition_key', ''),
            correlation_id=data.get('correlation_id', ''),
            causation_id=data.get('causation_id', ''),
            parent_id=data.get('parent_id', ''),
            source=data.get('source', ''),
            source_instance=data.get('source_instance', ''),
            priority=EventPriority(data.get('priority', EventPriority.NORMAL)),
            idempotency_key=data.get('idempotency_key', ''),
            retry_count=data.get('retry_count', 0),
            max_retries=data.get('max_retries', 3),
        )


@dataclass
class Event(ABC):
    """
    Base event class. All events are immutable and versioned.
    Events form the source of truth in the event-sourced system.
    """
    metadata: EventMetadata
    
    @property
    def event_id(self) -> str:
        return self.metadata.event_id
    
    @property
    def event_type(self) -> EventType:
        return self.metadata.event_type
    
    @property
    def timestamp(self) -> datetime:
        return datetime.fromtimestamp(
            self.metadata.timestamp_ns / 1e9, 
            tz=timezone.utc
        )
    
    @property
    def sequence(self) -> int:
        return self.metadata.sequence_number
    
    @abstractmethod
    def to_payload(self) -> Dict[str, Any]:
        """Convert event-specific data to dict"""
        pass
    
    @classmethod
    @abstractmethod
    def from_payload(cls, metadata: EventMetadata, payload: Dict[str, Any]) -> 'Event':
        """Create event from metadata and payload"""
        pass
    
    def to_dict(self) -> Dict[str, Any]:
        """Full serialization"""
        return {
            'metadata': self.metadata.to_dict(),
            'payload': self.to_payload(),
        }
    
    def to_json(self) -> str:
        """JSON serialization"""
        return json.dumps(self.to_dict())
    
    def to_bytes(self) -> bytes:
        """Binary serialization"""
        try:
            json_data = self.to_json().encode('utf-8')
            # Header: magic (2) + version (2) + length (4)
            header = struct.pack('>HHI', EVENT_MAGIC, 1, len(json_data))
            return header + json_data
        except Exception as e:
            logger.error(f"Error in to_bytes: {e}")
            raise
    
    @classmethod
    def from_bytes(cls, data: bytes) -> 'Event':
        """Binary deserialization"""
        try:
            magic, version, length = struct.unpack('>HHI', data[:8])
            if magic != EVENT_MAGIC:
                raise ValueError(f"Invalid event magic: {magic}")
            json_data = data[8:8+length].decode('utf-8')
            return cls.from_json(json_data)
        except Exception as e:
            logger.error(f"Error in from_bytes: {e}")
            raise
    
    def compute_hash(self) -> str:
        """Compute content hash for integrity verification"""
        try:
            content = json.dumps(self.to_dict(), sort_keys=True)
            return hashlib.sha256(content.encode()).hexdigest()
        except Exception as e:
            logger.error(f"Error in compute_hash: {e}")
            raise


@dataclass
class EventEnvelope:
    """
    Wrapper for events with delivery metadata.
    Used for transport and acknowledgment tracking.
    """
    event: Event
    envelope_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    # Delivery tracking
    sent_at_ns: int = 0
    delivered_at_ns: int = 0
    acknowledged_at_ns: int = 0
    
    # Routing
    destination: str = ""
    reply_to: str = ""
    
    # Delivery attempts
    attempt: int = 1
    max_attempts: int = 3
    
    # Dead letter
    dead_lettered: bool = False
    dead_letter_reason: str = ""
    
    def mark_sent(self):
        try:
            self.sent_at_ns = time.time_ns()
        except Exception as e:
            logger.error(f"Error in mark_sent: {e}")
            raise
    
    def mark_delivered(self):
        try:
            self.delivered_at_ns = time.time_ns()
        except Exception as e:
            logger.error(f"Error in mark_delivered: {e}")
            raise
    
    def mark_acknowledged(self):
        try:
            self.acknowledged_at_ns = time.time_ns()
        except Exception as e:
            logger.error(f"Error in mark_acknowledged: {e}")
            raise
    
    def to_dead_letter(self, reason: str):
        try:
            self.dead_lettered = True
            self.dead_letter_reason = reason
        except Exception as e:
            logger.error(f"Error in to_dead_letter: {e}")
            raise


# ============================================================================
# Concrete Event Types
# ============================================================================

@dataclass
class MarketDataEvent(Event):
    """Market data event (quotes, trades, bars)"""
    symbol: str = ""
    exchange: str = ""
    
    # Price data
    bid: float = 0.0
    ask: float = 0.0
    last: float = 0.0
    
    # Volume
    volume: float = 0.0
    bid_size: float = 0.0
    ask_size: float = 0.0
    
    # OHLCV for bars
    open: float = 0.0
    high: float = 0.0
    low: float = 0.0
    close: float = 0.0
    
    # Quality
    is_delayed: bool = False
    is_stale: bool = False
    
    def to_payload(self) -> Dict[str, Any]:
        return {
            'symbol': self.symbol,
            'exchange': self.exchange,
            'bid': self.bid,
            'ask': self.ask,
            'last': self.last,
            'volume': self.volume,
            'bid_size': self.bid_size,
            'ask_size': self.ask_size,
            'open': self.open,
            'high': self.high,
            'low': self.low,
            'close': self.close,
            'is_delayed': self.is_delayed,
            'is_stale': self.is_stale,
        }
    
    @classmethod
    def from_payload(cls, metadata: EventMetadata, payload: Dict[str, Any]) -> 'MarketDataEvent':
        return cls(
            metadata=metadata,
            symbol=payload.get('symbol', ''),
            exchange=payload.get('exchange', ''),
            bid=payload.get('bid', 0.0),
            ask=payload.get('ask', 0.0),
            last=payload.get('last', 0.0),
            volume=payload.get('volume', 0.0),
            bid_size=payload.get('bid_size', 0.0),
            ask_size=payload.get('ask_size', 0.0),
            open=payload.get('open', 0.0),
            high=payload.get('high', 0.0),
            low=payload.get('low', 0.0),
            close=payload.get('close', 0.0),
            is_delayed=payload.get('is_delayed', False),
            is_stale=payload.get('is_stale', False),
        )


@dataclass
class SignalEvent(Event):
    """Trading signal event"""
    signal_id: str = ""
    symbol: str = ""
    
    # Signal details
    direction: str = ""  # 'LONG', 'SHORT', 'FLAT'
    strength: float = 0.0  # 0.0 to 1.0
    confidence: float = 0.0
    
    # Price targets
    entry_price: float = 0.0
    stop_loss: float = 0.0
    take_profit: float = 0.0
    
    # Timing
    valid_until_ns: int = 0
    
    # Source
    strategy_name: str = ""
    model_version: str = ""
    
    # Reasoning
    reasoning: str = ""
    features: Dict[str, float] = field(default_factory=dict)
    
    def to_payload(self) -> Dict[str, Any]:
        return {
            'signal_id': self.signal_id,
            'symbol': self.symbol,
            'direction': self.direction,
            'strength': self.strength,
            'confidence': self.confidence,
            'entry_price': self.entry_price,
            'stop_loss': self.stop_loss,
            'take_profit': self.take_profit,
            'valid_until_ns': self.valid_until_ns,
            'strategy_name': self.strategy_name,
            'model_version': self.model_version,
            'reasoning': self.reasoning,
            'features': self.features,
        }
    
    @classmethod
    def from_payload(cls, metadata: EventMetadata, payload: Dict[str, Any]) -> 'SignalEvent':
        return cls(
            metadata=metadata,
            signal_id=payload.get('signal_id', ''),
            symbol=payload.get('symbol', ''),
            direction=payload.get('direction', ''),
            strength=payload.get('strength', 0.0),
            confidence=payload.get('confidence', 0.0),
            entry_price=payload.get('entry_price', 0.0),
            stop_loss=payload.get('stop_loss', 0.0),
            take_profit=payload.get('take_profit', 0.0),
            valid_until_ns=payload.get('valid_until_ns', 0),
            strategy_name=payload.get('strategy_name', ''),
            model_version=payload.get('model_version', ''),
            reasoning=payload.get('reasoning', ''),
            features=payload.get('features', {}),
        )


@dataclass
class OrderEvent(Event):
    """Order lifecycle event"""
    order_id: str = ""
    client_order_id: str = ""
    symbol: str = ""
    
    # Order details
    side: str = ""  # 'BUY', 'SELL'
    order_type: str = ""  # 'MARKET', 'LIMIT', 'STOP', etc.
    quantity: float = 0.0
    price: float = 0.0
    stop_price: float = 0.0
    
    # Status
    status: str = ""  # 'NEW', 'FILLED', 'CANCELLED', etc.
    filled_quantity: float = 0.0
    average_price: float = 0.0
    
    # Execution
    venue: str = ""
    time_in_force: str = "GTC"
    
    # Linking
    signal_id: str = ""
    parent_order_id: str = ""
    
    # Rejection
    reject_reason: str = ""
    
    def to_payload(self) -> Dict[str, Any]:
        return {
            'order_id': self.order_id,
            'client_order_id': self.client_order_id,
            'symbol': self.symbol,
            'side': self.side,
            'order_type': self.order_type,
            'quantity': self.quantity,
            'price': self.price,
            'stop_price': self.stop_price,
            'status': self.status,
            'filled_quantity': self.filled_quantity,
            'average_price': self.average_price,
            'venue': self.venue,
            'time_in_force': self.time_in_force,
            'signal_id': self.signal_id,
            'parent_order_id': self.parent_order_id,
            'reject_reason': self.reject_reason,
        }
    
    @classmethod
    def from_payload(cls, metadata: EventMetadata, payload: Dict[str, Any]) -> 'OrderEvent':
        return cls(
            metadata=metadata,
            order_id=payload.get('order_id', ''),
            client_order_id=payload.get('client_order_id', ''),
            symbol=payload.get('symbol', ''),
            side=payload.get('side', ''),
            order_type=payload.get('order_type', ''),
            quantity=payload.get('quantity', 0.0),
            price=payload.get('price', 0.0),
            stop_price=payload.get('stop_price', 0.0),
            status=payload.get('status', ''),
            filled_quantity=payload.get('filled_quantity', 0.0),
            average_price=payload.get('average_price', 0.0),
            venue=payload.get('venue', ''),
            time_in_force=payload.get('time_in_force', 'GTC'),
            signal_id=payload.get('signal_id', ''),
            parent_order_id=payload.get('parent_order_id', ''),
            reject_reason=payload.get('reject_reason', ''),
        )


@dataclass
class ExecutionEvent(Event):
    """Trade execution event"""
    execution_id: str = ""
    order_id: str = ""
    symbol: str = ""
    
    # Execution details
    side: str = ""
    quantity: float = 0.0
    price: float = 0.0
    
    # Costs
    commission: float = 0.0
    slippage: float = 0.0
    
    # Venue
    venue: str = ""
    liquidity_type: str = ""  # 'MAKER', 'TAKER'
    
    # Timing
    execution_time_ns: int = 0
    latency_ns: int = 0
    
    def to_payload(self) -> Dict[str, Any]:
        return {
            'execution_id': self.execution_id,
            'order_id': self.order_id,
            'symbol': self.symbol,
            'side': self.side,
            'quantity': self.quantity,
            'price': self.price,
            'commission': self.commission,
            'slippage': self.slippage,
            'venue': self.venue,
            'liquidity_type': self.liquidity_type,
            'execution_time_ns': self.execution_time_ns,
            'latency_ns': self.latency_ns,
        }
    
    @classmethod
    def from_payload(cls, metadata: EventMetadata, payload: Dict[str, Any]) -> 'ExecutionEvent':
        return cls(
            metadata=metadata,
            execution_id=payload.get('execution_id', ''),
            order_id=payload.get('order_id', ''),
            symbol=payload.get('symbol', ''),
            side=payload.get('side', ''),
            quantity=payload.get('quantity', 0.0),
            price=payload.get('price', 0.0),
            commission=payload.get('commission', 0.0),
            slippage=payload.get('slippage', 0.0),
            venue=payload.get('venue', ''),
            liquidity_type=payload.get('liquidity_type', ''),
            execution_time_ns=payload.get('execution_time_ns', 0),
            latency_ns=payload.get('latency_ns', 0),
        )


@dataclass
class RiskEvent(Event):
    """Risk management event"""
    risk_type: str = ""  # 'LIMIT_BREACH', 'WARNING', 'MARGIN_CALL', etc.
    severity: str = ""  # 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'
    
    # Context
    symbol: str = ""
    portfolio_id: str = ""
    
    # Metrics
    current_value: float = 0.0
    threshold_value: float = 0.0
    breach_amount: float = 0.0
    
    # Details
    message: str = ""
    recommended_action: str = ""
    
    # Auto-response
    auto_action_taken: str = ""
    
    def to_payload(self) -> Dict[str, Any]:
        return {
            'risk_type': self.risk_type,
            'severity': self.severity,
            'symbol': self.symbol,
            'portfolio_id': self.portfolio_id,
            'current_value': self.current_value,
            'threshold_value': self.threshold_value,
            'breach_amount': self.breach_amount,
            'message': self.message,
            'recommended_action': self.recommended_action,
            'auto_action_taken': self.auto_action_taken,
        }
    
    @classmethod
    def from_payload(cls, metadata: EventMetadata, payload: Dict[str, Any]) -> 'RiskEvent':
        return cls(
            metadata=metadata,
            risk_type=payload.get('risk_type', ''),
            severity=payload.get('severity', ''),
            symbol=payload.get('symbol', ''),
            portfolio_id=payload.get('portfolio_id', ''),
            current_value=payload.get('current_value', 0.0),
            threshold_value=payload.get('threshold_value', 0.0),
            breach_amount=payload.get('breach_amount', 0.0),
            message=payload.get('message', ''),
            recommended_action=payload.get('recommended_action', ''),
            auto_action_taken=payload.get('auto_action_taken', ''),
        )


@dataclass
class SystemEvent(Event):
    """System lifecycle and health events"""
    system_type: str = ""  # 'STARTED', 'STOPPED', 'ERROR', 'WARNING', etc.
    component: str = ""
    
    # Status
    status: str = ""
    health_score: float = 1.0
    
    # Details
    message: str = ""
    error_code: str = ""
    stack_trace: str = ""
    
    # Metrics
    metrics: Dict[str, float] = field(default_factory=dict)
    
    def to_payload(self) -> Dict[str, Any]:
        return {
            'system_type': self.system_type,
            'component': self.component,
            'status': self.status,
            'health_score': self.health_score,
            'message': self.message,
            'error_code': self.error_code,
            'stack_trace': self.stack_trace,
            'metrics': self.metrics,
        }
    
    @classmethod
    def from_payload(cls, metadata: EventMetadata, payload: Dict[str, Any]) -> 'SystemEvent':
        return cls(
            metadata=metadata,
            system_type=payload.get('system_type', ''),
            component=payload.get('component', ''),
            status=payload.get('status', ''),
            health_score=payload.get('health_score', 1.0),
            message=payload.get('message', ''),
            error_code=payload.get('error_code', ''),
            stack_trace=payload.get('stack_trace', ''),
            metrics=payload.get('metrics', {}),
        )


# ============================================================================
# Event Factory
# ============================================================================

# Registry of event types
EVENT_REGISTRY: Dict[EventType, Type[Event]] = {
    EventType.MARKET_DATA: MarketDataEvent,
    EventType.TRADE: MarketDataEvent,
    EventType.QUOTE: MarketDataEvent,
    EventType.BAR: MarketDataEvent,
    EventType.TICK: MarketDataEvent,
    EventType.SIGNAL_GENERATED: SignalEvent,
    EventType.SIGNAL_VALIDATED: SignalEvent,
    EventType.SIGNAL_EXPIRED: SignalEvent,
    EventType.ORDER_CREATED: OrderEvent,
    EventType.ORDER_SUBMITTED: OrderEvent,
    EventType.ORDER_ACCEPTED: OrderEvent,
    EventType.ORDER_REJECTED: OrderEvent,
    EventType.ORDER_FILLED: OrderEvent,
    EventType.ORDER_PARTIALLY_FILLED: OrderEvent,
    EventType.ORDER_CANCELLED: OrderEvent,
    EventType.EXECUTION_STARTED: ExecutionEvent,
    EventType.EXECUTION_COMPLETED: ExecutionEvent,
    EventType.FILL_RECEIVED: ExecutionEvent,
    EventType.RISK_LIMIT_BREACH: RiskEvent,
    EventType.RISK_WARNING: RiskEvent,
    EventType.DRAWDOWN_ALERT: RiskEvent,
    EventType.CIRCUIT_BREAKER_TRIGGERED: RiskEvent,
    EventType.SYSTEM_STARTED: SystemEvent,
    EventType.SYSTEM_STOPPED: SystemEvent,
    EventType.SYSTEM_ERROR: SystemEvent,
    EventType.HEALTH_CHECK: SystemEvent,
}


def create_event(
    event_type: EventType,
    source: str = "alphaalgo",
    partition_key: str = "",
    correlation_id: str = "",
    causation_id: str = "",
    priority: EventPriority = EventPriority.NORMAL,
    **kwargs
) -> Event:
    """
    Factory function to create events with proper metadata.
    
    Args:
        event_type: Type of event to create
        source: Source service name
        partition_key: Key for partitioning (usually symbol)
        correlation_id: Request correlation ID
        causation_id: ID of causing event
        priority: Event priority
        **kwargs: Event-specific fields
        
    Returns:
        Created event instance
    """
    try:
        now_ns = time.time_ns()
        event_id = str(uuid.uuid4())
    
        metadata = EventMetadata(
            event_id=event_id,
            event_type=event_type,
            version=EVENT_SCHEMA_VERSION,
            timestamp_ns=now_ns,
            created_at_ns=now_ns,
            partition_key=partition_key,
            correlation_id=correlation_id or event_id,
            causation_id=causation_id,
            source=source,
            priority=priority,
            idempotency_key=f"{source}:{event_id}",
        )
    
        event_class = EVENT_REGISTRY.get(event_type)
        if event_class is None:
            raise ValueError(f"Unknown event type: {event_type}")
    
        return event_class(metadata=metadata, **kwargs)
    except Exception as e:
        logger.error(f"Error in create_event: {e}")
        raise


def deserialize_event(data: Union[str, bytes, Dict]) -> Event:
    """
    Deserialize event from various formats.
    
    Args:
        data: JSON string, bytes, or dict
        
    Returns:
        Deserialized event
    """
    try:
        if isinstance(data, bytes):
            # Binary format
            magic, version, length = struct.unpack('>HHI', data[:8])
            if magic != EVENT_MAGIC:
                raise ValueError(f"Invalid event magic: {magic}")
            data = json.loads(data[8:8+length].decode('utf-8'))
        elif isinstance(data, str):
            data = json.loads(data)
    
        metadata = EventMetadata.from_dict(data['metadata'])
        event_class = EVENT_REGISTRY.get(metadata.event_type)
    
        if event_class is None:
            raise ValueError(f"Unknown event type: {metadata.event_type}")
    
        return event_class.from_payload(metadata, data['payload'])
    except Exception as e:
        logger.error(f"Error in deserialize_event: {e}")
        raise
