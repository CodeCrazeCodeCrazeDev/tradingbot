"""
AlphaAlgo Event Producers
==========================
Event producers for various data sources: market data, signals, orders, risk.
Transforms raw data into standardized events for the pipeline.
"""

from __future__ import annotations

import asyncio
import logging
import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum, auto
from typing import (
    Dict, List, Optional, Any, Callable, Awaitable,
    Union, TypeVar
)

from .events import (
    Event, EventType, EventPriority, EventMetadata,
    MarketDataEvent, SignalEvent, OrderEvent, ExecutionEvent,
    RiskEvent, SystemEvent, create_event
)
from .event_bus import EventBus

logger = logging.getLogger(__name__)


@dataclass
class ProducerConfig:
    """Configuration for event producers"""
    # Identity
    producer_id: str = ""
    source_name: str = "alphaalgo"
    
    # Batching
    batch_size: int = 100
    batch_timeout_ms: int = 50
    
    # Rate limiting
    max_events_per_second: int = 10000
    
    # Quality
    validate_events: bool = True
    add_timestamps: bool = True
    
    # Partitioning
    partition_by: str = "symbol"  # 'symbol', 'type', 'source'


class EventProducer(ABC):
    """Base class for event producers"""
    
    def __init__(
        self,
        event_bus: EventBus,
        config: ProducerConfig = None,
        topic: str = "events"
    ):
        self.event_bus = event_bus
        self.config = config or ProducerConfig()
        self.topic = topic
        
        if not self.config.producer_id:
            self.config.producer_id = str(uuid.uuid4())[:8]
        
        # Batching
        self._batch: List[Event] = []
        self._batch_lock = asyncio.Lock()
        self._flush_task: Optional[asyncio.Task] = None
        
        # Rate limiting
        self._rate_limiter = RateLimiter(self.config.max_events_per_second)
        
        # Metrics
        self.metrics = {
            'events_produced': 0,
            'events_failed': 0,
            'batches_sent': 0,
        }
        
        self._running = False
    
    async def start(self):
        """Start the producer"""
        self._running = True
        if self.config.batch_timeout_ms > 0:
            self._flush_task = asyncio.create_task(self._flush_loop())
        logger.info(f"Producer {self.config.producer_id} started")
    
    async def stop(self):
        """Stop the producer"""
        self._running = False
        if self._flush_task:
            self._flush_task.cancel()
            try:
                await self._flush_task
            except asyncio.CancelledError:
                pass
        await self._flush_batch()
        logger.info(f"Producer {self.config.producer_id} stopped")
    
    async def _flush_loop(self):
        """Periodic batch flush"""
        interval = self.config.batch_timeout_ms / 1000
        while self._running:
            await asyncio.sleep(interval)
            await self._flush_batch()
    
    async def _flush_batch(self):
        """Flush buffered events"""
        async with self._batch_lock:
            if self._batch:
                events = self._batch[:]
                self._batch.clear()
                
                count = await self.event_bus.publish_batch(self.topic, events)
                self.metrics['batches_sent'] += 1
                self.metrics['events_produced'] += count
    
    async def produce(self, event: Event, immediate: bool = False) -> bool:
        """
        Produce an event.
        
        Args:
            event: Event to produce
            immediate: Bypass batching
            
        Returns:
            True if produced successfully
        """
        # Rate limiting
        await self._rate_limiter.acquire()
        
        # Validation
        if self.config.validate_events:
            if not self._validate_event(event):
                self.metrics['events_failed'] += 1
                return False
        
        if immediate or len(self._batch) >= self.config.batch_size:
            success = await self.event_bus.publish(self.topic, event)
            if success:
                self.metrics['events_produced'] += 1
            else:
                self.metrics['events_failed'] += 1
            return success
        else:
            async with self._batch_lock:
                self._batch.append(event)
            return True
    
    def _validate_event(self, event: Event) -> bool:
        """Validate event before producing"""
        if not event.metadata.event_id:
            logger.warning("Event missing event_id")
            return False
        if not event.metadata.event_type:
            logger.warning("Event missing event_type")
            return False
        return True
    
    @abstractmethod
    async def transform(self, data: Any) -> Optional[Event]:
        """Transform raw data into event"""
        pass
    
    async def process(self, data: Any, immediate: bool = False) -> bool:
        """Transform and produce event from raw data"""
        event = await self.transform(data)
        if event:
            return await self.produce(event, immediate)
        return False
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get producer metrics"""
        return {
            **self.metrics,
            'batch_size': len(self._batch),
            'producer_id': self.config.producer_id,
        }


class RateLimiter:
    """Token bucket rate limiter"""
    
    def __init__(self, rate: int):
        self.rate = rate
        self.tokens = rate
        self.last_update = time.time()
        self._lock = asyncio.Lock()
    
    async def acquire(self):
        """Acquire a token, waiting if necessary"""
        async with self._lock:
            now = time.time()
            elapsed = now - self.last_update
            self.tokens = min(self.rate, self.tokens + elapsed * self.rate)
            self.last_update = now
            
            if self.tokens < 1:
                wait_time = (1 - self.tokens) / self.rate
                await asyncio.sleep(wait_time)
                self.tokens = 0
            else:
                self.tokens -= 1


class MarketDataProducer(EventProducer):
    """Producer for market data events"""
    
    def __init__(
        self,
        event_bus: EventBus,
        config: ProducerConfig = None
    ):
        super().__init__(event_bus, config, topic="market_data")
        self.config.source_name = self.config.source_name or "market_data"
    
    async def transform(self, data: Any) -> Optional[Event]:
        """Transform market data into event"""
        try:
            if isinstance(data, dict):
                return self._from_dict(data)
            elif hasattr(data, 'symbol'):
                return self._from_object(data)
            else:
                logger.warning(f"Unknown market data format: {type(data)}")
                return None
        except Exception as e:
            logger.error(f"Failed to transform market data: {e}")
            return None
    
    def _from_dict(self, data: Dict[str, Any]) -> MarketDataEvent:
        """Create event from dictionary"""
        symbol = data.get('symbol', '')
        
        return create_event(
            event_type=EventType.MARKET_DATA,
            source=self.config.source_name,
            partition_key=symbol,
            symbol=symbol,
            exchange=data.get('exchange', ''),
            bid=float(data.get('bid', 0)),
            ask=float(data.get('ask', 0)),
            last=float(data.get('last', data.get('price', 0))),
            volume=float(data.get('volume', 0)),
            bid_size=float(data.get('bid_size', 0)),
            ask_size=float(data.get('ask_size', 0)),
            open=float(data.get('open', 0)),
            high=float(data.get('high', 0)),
            low=float(data.get('low', 0)),
            close=float(data.get('close', 0)),
            is_delayed=data.get('is_delayed', False),
            is_stale=data.get('is_stale', False),
        )
    
    def _from_object(self, obj: Any) -> MarketDataEvent:
        """Create event from object with attributes"""
        symbol = getattr(obj, 'symbol', '')
        
        return create_event(
            event_type=EventType.MARKET_DATA,
            source=self.config.source_name,
            partition_key=symbol,
            symbol=symbol,
            exchange=getattr(obj, 'exchange', ''),
            bid=float(getattr(obj, 'bid', 0)),
            ask=float(getattr(obj, 'ask', 0)),
            last=float(getattr(obj, 'last', getattr(obj, 'price', 0))),
            volume=float(getattr(obj, 'volume', 0)),
        )
    
    async def produce_tick(
        self,
        symbol: str,
        bid: float,
        ask: float,
        last: float = None,
        volume: float = 0,
        exchange: str = "",
    ) -> bool:
        """Convenience method to produce tick data"""
        event = create_event(
            event_type=EventType.TICK,
            source=self.config.source_name,
            partition_key=symbol,
            symbol=symbol,
            exchange=exchange,
            bid=bid,
            ask=ask,
            last=last or (bid + ask) / 2,
            volume=volume,
        )
        return await self.produce(event, immediate=True)
    
    async def produce_bar(
        self,
        symbol: str,
        open: float,
        high: float,
        low: float,
        close: float,
        volume: float,
        exchange: str = "",
    ) -> bool:
        """Convenience method to produce OHLCV bar"""
        event = create_event(
            event_type=EventType.BAR,
            source=self.config.source_name,
            partition_key=symbol,
            symbol=symbol,
            exchange=exchange,
            open=open,
            high=high,
            low=low,
            close=close,
            last=close,
            volume=volume,
        )
        return await self.produce(event, immediate=True)


class SignalProducer(EventProducer):
    """Producer for trading signal events"""
    
    def __init__(
        self,
        event_bus: EventBus,
        config: ProducerConfig = None
    ):
        super().__init__(event_bus, config, topic="signals")
        self.config.source_name = self.config.source_name or "signal_engine"
    
    async def transform(self, data: Any) -> Optional[Event]:
        """Transform signal data into event"""
        try:
            if isinstance(data, dict):
                return self._from_dict(data)
            else:
                logger.warning(f"Unknown signal format: {type(data)}")
                return None
        except Exception as e:
            logger.error(f"Failed to transform signal: {e}")
            return None
    
    def _from_dict(self, data: Dict[str, Any]) -> SignalEvent:
        """Create signal event from dictionary"""
        symbol = data.get('symbol', '')
        signal_id = data.get('signal_id', str(uuid.uuid4()))
        
        return create_event(
            event_type=EventType.SIGNAL_GENERATED,
            source=self.config.source_name,
            partition_key=symbol,
            signal_id=signal_id,
            symbol=symbol,
            direction=data.get('direction', ''),
            strength=float(data.get('strength', 0)),
            confidence=float(data.get('confidence', 0)),
            entry_price=float(data.get('entry_price', 0)),
            stop_loss=float(data.get('stop_loss', 0)),
            take_profit=float(data.get('take_profit', 0)),
            valid_until_ns=data.get('valid_until_ns', 0),
            strategy_name=data.get('strategy_name', ''),
            model_version=data.get('model_version', ''),
            reasoning=data.get('reasoning', ''),
            features=data.get('features', {}),
        )
    
    async def produce_signal(
        self,
        symbol: str,
        direction: str,
        confidence: float,
        entry_price: float = 0,
        stop_loss: float = 0,
        take_profit: float = 0,
        strategy_name: str = "",
        reasoning: str = "",
    ) -> bool:
        """Convenience method to produce trading signal"""
        event = create_event(
            event_type=EventType.SIGNAL_GENERATED,
            source=self.config.source_name,
            partition_key=symbol,
            priority=EventPriority.HIGH,
            signal_id=str(uuid.uuid4()),
            symbol=symbol,
            direction=direction,
            confidence=confidence,
            strength=confidence,
            entry_price=entry_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            strategy_name=strategy_name,
            reasoning=reasoning,
        )
        return await self.produce(event, immediate=True)


class OrderProducer(EventProducer):
    """Producer for order lifecycle events"""
    
    def __init__(
        self,
        event_bus: EventBus,
        config: ProducerConfig = None
    ):
        super().__init__(event_bus, config, topic="orders")
        self.config.source_name = self.config.source_name or "order_manager"
    
    async def transform(self, data: Any) -> Optional[Event]:
        """Transform order data into event"""
        try:
            if isinstance(data, dict):
                return self._from_dict(data)
            else:
                return None
        except Exception as e:
            logger.error(f"Failed to transform order: {e}")
            return None
    
    def _from_dict(self, data: Dict[str, Any]) -> OrderEvent:
        """Create order event from dictionary"""
        symbol = data.get('symbol', '')
        event_type_str = data.get('event_type', 'ORDER_CREATED')
        
        event_type_map = {
            'ORDER_CREATED': EventType.ORDER_CREATED,
            'ORDER_SUBMITTED': EventType.ORDER_SUBMITTED,
            'ORDER_ACCEPTED': EventType.ORDER_ACCEPTED,
            'ORDER_REJECTED': EventType.ORDER_REJECTED,
            'ORDER_FILLED': EventType.ORDER_FILLED,
            'ORDER_PARTIALLY_FILLED': EventType.ORDER_PARTIALLY_FILLED,
            'ORDER_CANCELLED': EventType.ORDER_CANCELLED,
        }
        event_type = event_type_map.get(event_type_str, EventType.ORDER_CREATED)
        
        return create_event(
            event_type=event_type,
            source=self.config.source_name,
            partition_key=symbol,
            order_id=data.get('order_id', ''),
            client_order_id=data.get('client_order_id', ''),
            symbol=symbol,
            side=data.get('side', ''),
            order_type=data.get('order_type', ''),
            quantity=float(data.get('quantity', 0)),
            price=float(data.get('price', 0)),
            stop_price=float(data.get('stop_price', 0)),
            status=data.get('status', ''),
            filled_quantity=float(data.get('filled_quantity', 0)),
            average_price=float(data.get('average_price', 0)),
            venue=data.get('venue', ''),
            time_in_force=data.get('time_in_force', 'GTC'),
            signal_id=data.get('signal_id', ''),
            reject_reason=data.get('reject_reason', ''),
        )
    
    async def produce_order_created(
        self,
        order_id: str,
        symbol: str,
        side: str,
        order_type: str,
        quantity: float,
        price: float = 0,
        signal_id: str = "",
    ) -> bool:
        """Produce order created event"""
        event = create_event(
            event_type=EventType.ORDER_CREATED,
            source=self.config.source_name,
            partition_key=symbol,
            correlation_id=order_id,
            order_id=order_id,
            client_order_id=f"CLT-{order_id}",
            symbol=symbol,
            side=side,
            order_type=order_type,
            quantity=quantity,
            price=price,
            status='NEW',
            signal_id=signal_id,
        )
        return await self.produce(event, immediate=True)
    
    async def produce_order_filled(
        self,
        order_id: str,
        symbol: str,
        side: str,
        quantity: float,
        price: float,
        venue: str = "",
    ) -> bool:
        """Produce order filled event"""
        event = create_event(
            event_type=EventType.ORDER_FILLED,
            source=self.config.source_name,
            partition_key=symbol,
            correlation_id=order_id,
            priority=EventPriority.HIGH,
            order_id=order_id,
            symbol=symbol,
            side=side,
            quantity=quantity,
            filled_quantity=quantity,
            average_price=price,
            status='FILLED',
            venue=venue,
        )
        return await self.produce(event, immediate=True)


class RiskProducer(EventProducer):
    """Producer for risk management events"""
    
    def __init__(
        self,
        event_bus: EventBus,
        config: ProducerConfig = None
    ):
        super().__init__(event_bus, config, topic="risk")
        self.config.source_name = self.config.source_name or "risk_manager"
    
    async def transform(self, data: Any) -> Optional[Event]:
        """Transform risk data into event"""
        try:
            if isinstance(data, dict):
                return self._from_dict(data)
            return None
        except Exception as e:
            logger.error(f"Failed to transform risk event: {e}")
            return None
    
    def _from_dict(self, data: Dict[str, Any]) -> RiskEvent:
        """Create risk event from dictionary"""
        risk_type = data.get('risk_type', 'WARNING')
        
        event_type_map = {
            'LIMIT_BREACH': EventType.RISK_LIMIT_BREACH,
            'WARNING': EventType.RISK_WARNING,
            'DRAWDOWN': EventType.DRAWDOWN_ALERT,
            'CIRCUIT_BREAKER': EventType.CIRCUIT_BREAKER_TRIGGERED,
        }
        event_type = event_type_map.get(risk_type, EventType.RISK_WARNING)
        
        return create_event(
            event_type=event_type,
            source=self.config.source_name,
            partition_key=data.get('symbol', 'PORTFOLIO'),
            priority=EventPriority.CRITICAL if risk_type == 'LIMIT_BREACH' else EventPriority.HIGH,
            risk_type=risk_type,
            severity=data.get('severity', 'MEDIUM'),
            symbol=data.get('symbol', ''),
            portfolio_id=data.get('portfolio_id', ''),
            current_value=float(data.get('current_value', 0)),
            threshold_value=float(data.get('threshold_value', 0)),
            breach_amount=float(data.get('breach_amount', 0)),
            message=data.get('message', ''),
            recommended_action=data.get('recommended_action', ''),
            auto_action_taken=data.get('auto_action_taken', ''),
        )
    
    async def produce_risk_warning(
        self,
        message: str,
        severity: str = "MEDIUM",
        symbol: str = "",
        current_value: float = 0,
        threshold_value: float = 0,
    ) -> bool:
        """Produce risk warning event"""
        event = create_event(
            event_type=EventType.RISK_WARNING,
            source=self.config.source_name,
            partition_key=symbol or 'PORTFOLIO',
            priority=EventPriority.HIGH,
            risk_type='WARNING',
            severity=severity,
            symbol=symbol,
            current_value=current_value,
            threshold_value=threshold_value,
            message=message,
        )
        return await self.produce(event, immediate=True)
    
    async def produce_limit_breach(
        self,
        message: str,
        symbol: str = "",
        current_value: float = 0,
        threshold_value: float = 0,
        recommended_action: str = "",
    ) -> bool:
        """Produce risk limit breach event"""
        event = create_event(
            event_type=EventType.RISK_LIMIT_BREACH,
            source=self.config.source_name,
            partition_key=symbol or 'PORTFOLIO',
            priority=EventPriority.CRITICAL,
            risk_type='LIMIT_BREACH',
            severity='CRITICAL',
            symbol=symbol,
            current_value=current_value,
            threshold_value=threshold_value,
            breach_amount=abs(current_value - threshold_value),
            message=message,
            recommended_action=recommended_action,
        )
        return await self.produce(event, immediate=True)
    
    async def produce_circuit_breaker(
        self,
        message: str,
        auto_action: str = "",
    ) -> bool:
        """Produce circuit breaker triggered event"""
        event = create_event(
            event_type=EventType.CIRCUIT_BREAKER_TRIGGERED,
            source=self.config.source_name,
            partition_key='SYSTEM',
            priority=EventPriority.EMERGENCY,
            risk_type='CIRCUIT_BREAKER',
            severity='CRITICAL',
            message=message,
            auto_action_taken=auto_action,
        )
        return await self.produce(event, immediate=True)
