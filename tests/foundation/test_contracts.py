"""Contract and port tests for the AlphaAlgo foundation boundary."""

import json
from datetime import datetime, timezone

import pytest

from trading_bot.core.unified_event_bus import UnifiedDecisionBus
from trading_bot.foundation import (
    DataQuality,
    Instrument,
    InstrumentType,
    MarketEvent,
    MarketEventType,
    OrderRequest,
    OrderSide,
    OrderType,
    Venue,
)


def make_instrument() -> Instrument:
    return Instrument(
        symbol="EURUSD",
        instrument_type=InstrumentType.FX,
        venue="paper",
        currency="USD",
        quantity_increment=0.01,
    )


def test_market_event_is_json_safe_and_preserves_provenance() -> None:
    event = MarketEvent(
        instrument=make_instrument(),
        event_type=MarketEventType.BAR,
        source_timestamp=datetime(2026, 1, 1, tzinfo=timezone.utc),
        payload={"open": 1.1, "close": 1.2},
        quality=DataQuality.VALID,
        provenance={"source": "replay", "dataset": "fixture-1"},
    )

    encoded = json.dumps(event.to_dict())
    decoded = json.loads(encoded)

    assert decoded["event_type"] == "bar"
    assert decoded["instrument"]["instrument_type"] == "fx"
    assert decoded["quality"] == "valid"
    assert decoded["provenance"]["source"] == "replay"


def test_order_contract_covers_universal_instrument_and_decision_identity() -> None:
    order = OrderRequest(
        instrument=make_instrument(),
        side=OrderSide.BUY,
        order_type=OrderType.LIMIT,
        quantity=1000,
        price=1.2,
        client_order_id="decision-1-order-1",
        decision_id="decision-1",
    )

    assert order.to_dict()["instrument"]["symbol"] == "EURUSD"
    assert order.to_dict()["side"] == "buy"
    assert order.to_dict()["order_type"] == "limit"


def test_contracts_fail_closed_on_invalid_values() -> None:
    with pytest.raises(ValueError, match="confidence"):
        from trading_bot.foundation.contracts import Signal

        Signal("signal-1", make_instrument(), "buy", 1.1)

    with pytest.raises(ValueError, match="quantity"):
        OrderRequest(
            instrument=make_instrument(),
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=0,
            client_order_id="order-1",
            decision_id="decision-1",
        )


def test_venue_capabilities_serialize_as_values() -> None:
    venue = Venue("paper", "Paper Venue", capabilities=frozenset({"replay", "execution"}))

    assert set(venue.to_dict()["capabilities"]) == {"replay", "execution"}


@pytest.mark.asyncio
async def test_typed_contract_can_enter_the_shared_decision_bus() -> None:
    bus = UnifiedDecisionBus()
    UnifiedDecisionBus.reset()
    bus = UnifiedDecisionBus()
    event = MarketEvent(
        instrument=make_instrument(),
        event_type=MarketEventType.QUOTE,
        source_timestamp=datetime.now(timezone.utc),
        payload={"bid": 1.1, "ask": 1.2},
        quality=DataQuality.VALID,
    )

    action = await bus.publish_contract("MARKET_EVENT", event, source="replay")
    status = await action.wait_for_decision(timeout=2.0)
    await bus.stop()

    assert status.value == "approved"
    assert action.payload["event_type"] == "quote"
    assert action.agent_id == "replay"
