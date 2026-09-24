"""Adapters that place legacy market feeds behind MarketDataAdapter."""

from __future__ import annotations

import asyncio
from typing import AsyncIterator, Optional, Sequence

from trading_bot.connectivity.market_data_stream import MarketDataStream, MarketTick
from trading_bot.foundation.contracts import Instrument, MarketEvent
from trading_bot.foundation.ports import MarketDataAdapter

from .normalizer import MarketDataNormalizer


class LegacyMarketDataAdapter:
    """Adapt the legacy callback stream without changing its network behavior."""

    def __init__(
        self,
        stream: Optional[MarketDataStream] = None,
        normalizer: Optional[MarketDataNormalizer] = None,
    ) -> None:
        self.stream_source = stream or MarketDataStream()
        self.normalizer = normalizer or MarketDataNormalizer()

    async def connect(self) -> None:
        await self.stream_source.initialize()
        await self.stream_source.start()

    async def disconnect(self) -> None:
        await self.stream_source.stop()

    async def snapshot(self, instrument: Instrument, timeframe: Optional[str] = None):
        tick = self.stream_source.get_last_tick(instrument.symbol)
        if tick is None:
            return []
        return [self._event(instrument, tick)]

    def stream(self, instruments: Sequence[Instrument]) -> AsyncIterator[MarketEvent]:
        return self._stream(instruments)

    async def _stream(self, instruments: Sequence[Instrument]) -> AsyncIterator[MarketEvent]:
        queue: asyncio.Queue = asyncio.Queue()
        symbols = {instrument.symbol: instrument for instrument in instruments}
        callbacks = {}

        for symbol, instrument in symbols.items():
            async def callback(tick: MarketTick, instrument=instrument):
                await queue.put(self._event(instrument, tick))

            callbacks[symbol] = callback
            self.stream_source.subscribe(symbol, callback)

        try:
            while True:
                yield await queue.get()
        finally:
            for symbol, callback in callbacks.items():
                self.stream_source.unsubscribe(symbol, callback)

    def _event(self, instrument: Instrument, tick: MarketTick) -> MarketEvent:
        return self.normalizer.normalize(
            {
                "symbol": instrument.symbol,
                "timestamp": tick.timestamp,
                "bid": tick.bid,
                "ask": tick.ask,
                "last": tick.last,
                "volume": tick.volume,
                "instrument_type": instrument.instrument_type.value,
                "venue": instrument.venue,
            },
            source="legacy_market_data_stream",
        )


assert isinstance(LegacyMarketDataAdapter(), MarketDataAdapter)
