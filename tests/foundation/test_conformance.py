"""Wave-3 data and broker adapter conformance tests."""

from datetime import datetime, timezone

from trading_bot.foundation.conformance import (
    check_broker_adapter,
    check_market_data_adapter,
    check_market_event,
)
from trading_bot.foundation.contracts import (
    DataQuality,
    Instrument,
    InstrumentType,
    MarketEvent,
    MarketEventType,
)
from trading_bot.execution.service import PaperBrokerAdapter


def test_paper_broker_adapter_conforms_without_connecting() -> None:
    result = check_broker_adapter(PaperBrokerAdapter())

    assert result.passed is True
    assert result.missing == []


def test_market_data_shape_check_is_non_networking() -> None:
    class Adapter:
        async def connect(self): pass
        async def disconnect(self): pass
        async def snapshot(self, instrument, timeframe=None): return []
        def stream(self, instruments): return iter(())

    result = check_market_data_adapter(Adapter())

    assert result.passed is True


def test_market_event_conformance_requires_provenance_and_quality() -> None:
    event = MarketEvent(
        instrument=Instrument("EURUSD", InstrumentType.FX, "paper"),
        event_type=MarketEventType.BAR,
        source_timestamp=datetime.now(timezone.utc),
        payload={"close": 1.1},
        quality=DataQuality.VALID,
        provenance={"source": "replay"},
    )

    assert check_market_event(event).passed is True
