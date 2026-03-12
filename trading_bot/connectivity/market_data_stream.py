"""
Market Data Stream - Real-time market data streaming
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Optional, List, Callable
from enum import Enum

logger = logging.getLogger(__name__)


class StreamStatus(Enum):
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"


@dataclass
class MarketTick:
    symbol: str
    bid: float
    ask: float
    last: float
    volume: float
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


class MarketDataStream:
    """Real-time market data streaming"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.status = StreamStatus.DISCONNECTED
        self.subscribers: Dict[str, List[Callable]] = {}
        self.last_ticks: Dict[str, MarketTick] = {}
        self._running = False
    
    async def initialize(self, config: Dict[str, Any] = None) -> bool:
        if config:
            self.config.update(config)
        logger.info("MarketDataStream initialized")
        return True
    
    async def start(self) -> bool:
        self._running = True
        self.status = StreamStatus.CONNECTED
        logger.info("MarketDataStream started")
        return True
    
    async def stop(self) -> bool:
        self._running = False
        self.status = StreamStatus.DISCONNECTED
        logger.info("MarketDataStream stopped")
        return True
    
    def subscribe(self, symbol: str, callback: Callable):
        if symbol not in self.subscribers:
            self.subscribers[symbol] = []
        self.subscribers[symbol].append(callback)
    
    def unsubscribe(self, symbol: str, callback: Callable):
        if symbol in self.subscribers:
            self.subscribers[symbol].remove(callback)
    
    async def on_tick(self, tick: MarketTick):
        self.last_ticks[tick.symbol] = tick
        if tick.symbol in self.subscribers:
            for callback in self.subscribers[tick.symbol]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(tick)
                    else:
                        callback(tick)
                except Exception as e:
                    logger.error(f"Error in tick callback: {e}")
    
    def get_last_tick(self, symbol: str) -> Optional[MarketTick]:
        return self.last_ticks.get(symbol)


_stream: Optional[MarketDataStream] = None

def get_stream() -> MarketDataStream:
    global _stream
    if _stream is None:
        _stream = MarketDataStream()
    return _stream

async def initialize(config: Dict[str, Any] = None) -> bool:
    return await get_stream().initialize(config)

async def start() -> bool:
    return await get_stream().start()

async def stop() -> bool:
    return await get_stream().stop()
