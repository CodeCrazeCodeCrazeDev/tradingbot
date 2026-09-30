"""Fake-SDK conformance tests for the canonical MT5 demo adapter.

No network: every test injects a scripted MetaTrader5 client. Covered:
demo-only enforcement, USD/profile validation, netting vs hedging discovery,
volume-grid enforcement, fill/partial/reject mapping, UNKNOWN-on-uncertain,
venue-lookup recovery, and ticket-aware positions.
"""

from __future__ import annotations

import types
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import pytest

from trading_bot.brokers.mt5_demo import MT5AdapterError, MT5DemoAdapter
from trading_bot.foundation.contracts import (
    Instrument,
    InstrumentType,
    OrderRequest,
    OrderSide,
    OrderType,
    OrderStatus,
    PortfolioSnapshot,
    Position,
)


def _ns(**fields):
    return types.SimpleNamespace(**fields)


class FakeMT5:
    """Minimal scripted MetaTrader5 client."""

    def __init__(self, *, trade_mode=0, currency="USD", margin_mode=2,
                 symbol_name="EURUSD", trade_allowed=True,
                 symbol_trade_mode=4, visible=True,
                 volume_min=0.01, volume_max=100.0, volume_step=0.01,
                 tick_age_s=0.0, send_result=None, init_ok=True,
                 loose_symbol_lookup=False):
        self.account = _ns(trade_mode=trade_mode, currency=currency,
                           margin_mode=margin_mode, trade_allowed=trade_allowed,
                           login=99001122, balance=10000.0, equity=10000.0)
        self.symbol = _ns(name=symbol_name, visible=visible,
                          trade_mode=symbol_trade_mode,
                          volume_min=volume_min, volume_max=volume_max,
                          volume_step=volume_step, trade_contract_size=100000.0)
        self.tick = _ns(bid=1.1000, ask=1.1002,
                        time=datetime.now(timezone.utc).timestamp() - tick_age_s)
        self.send_result = send_result
        self.init_ok = init_ok
        self.requests: List[Dict[str, Any]] = []
        self.pending_orders: list = []
        self.history_orders: list = []
        self.history_deals: list = []
        self.open_positions: list = []
        self.login_calls: list = []
        self.shutdown_calls = 0
        self.initialized = 0
        self.loose_symbol_lookup = loose_symbol_lookup

    # SDK surface -------------------------------------------------------
    def initialize(self):
        self.initialized += 1
        return self.init_ok

    def login(self, login, password, server):
        self.login_calls.append((login, password, server))
        return True

    def shutdown(self):
        self.shutdown_calls += 1

    def last_error(self):
        return (0, "ok")

    def account_info(self):
        return self.account

    def symbol_info(self, symbol):
        if symbol == self.symbol.name or self.loose_symbol_lookup:
            return self.symbol
        return None

    def symbol_select(self, symbol, enable):
        return True

    def symbol_info_tick(self, symbol):
        return self.tick if symbol == self.symbol.name else None

    def order_send(self, request):
        self.requests.append(dict(request))
        return self.send_result

    def orders_get(self, **kwargs):
        return self.pending_orders

    def history_orders_get(self, **kwargs):
        return self.history_orders

    def history_deals_get(self, *args, **kwargs):
        return self.history_deals

    def positions_get(self, **kwargs):
        return self.open_positions


class FakeCreds:
    def __init__(self, secrets):
        self.secrets = secrets

    def get_secret(self, name):
        return self.secrets.get(name)

    def require_secret(self, name):
        value = self.secrets.get(name)
        if value is None:
            raise KeyError(name)
        return value


CREDS = FakeCreds({"MT5_LOGIN": "99001122", "MT5_PASSWORD": "s3cret",
                   "MT5_SERVER": "Broker-Demo"})


def make_adapter(client: FakeMT5, **cfg) -> MT5DemoAdapter:
    return MT5DemoAdapter(cfg, client=client, credential_provider=CREDS)


def _eurusd_order(**kw) -> OrderRequest:
    kw.setdefault("client_order_id", "cid-1")
    return OrderRequest(
        instrument=Instrument("EURUSD", InstrumentType.FX, "mt5_demo"),
        side=kw.pop("side", OrderSide.BUY),
        order_type=OrderType.MARKET,
        quantity=kw.pop("quantity", 0.10),
        decision_id="d-1", price=1.1002, **kw)


async def _connect(adapter):
    await adapter.connect()


# ----------------------------------------------------------------------
# connect-time validation
# ----------------------------------------------------------------------
async def test_refuses_real_account():
    adapter = make_adapter(FakeMT5(trade_mode=2))
    with pytest.raises(MT5AdapterError, match="not DEMO"):
        await adapter.connect()


async def test_refuses_contest_account():
    adapter = make_adapter(FakeMT5(trade_mode=1))
    with pytest.raises(MT5AdapterError):
        await adapter.connect()


async def test_refuses_non_usd_account():
    adapter = make_adapter(FakeMT5(currency="EUR"))
    with pytest.raises(MT5AdapterError, match="USD"):
        await adapter.connect()


async def test_refuses_symbol_suffix_variant():
    adapter = make_adapter(FakeMT5(symbol_name="EURUSD.pro",
                                   loose_symbol_lookup=True))
    with pytest.raises(MT5AdapterError, match="exact symbol"):
        await adapter.connect()


async def test_refuses_closed_only_symbol():
    adapter = make_adapter(FakeMT5(symbol_trade_mode=3))
    with pytest.raises(MT5AdapterError, match="not FULL"):
        await adapter.connect()


async def test_refuses_missing_credentials():
    adapter = MT5DemoAdapter({}, client=FakeMT5(),
                             credential_provider=FakeCreds({}))
    with pytest.raises(MT5AdapterError, match="credentials"):
        await adapter.connect()


async def test_refuses_non_m15_profile():
    adapter = make_adapter(FakeMT5(), timeframe="H1")
    with pytest.raises(MT5AdapterError, match="M15"):
        await adapter.connect()


async def test_hedging_mode_discovered():
    adapter = make_adapter(FakeMT5(margin_mode=2))
    await adapter.connect()
    assert adapter.account_mode == "hedging"
    assert adapter.connected


async def test_netting_mode_discovered():
    adapter = make_adapter(FakeMT5(margin_mode=0))
    await adapter.connect()
    assert adapter.account_mode == "netting"


async def test_no_paper_fallback_without_sdk():
    adapter = MT5DemoAdapter({}, credential_provider=CREDS)
    with pytest.raises(MT5AdapterError):
        await adapter.connect()


# ----------------------------------------------------------------------
# order submission
# ----------------------------------------------------------------------
async def test_market_buy_fills_and_tags_client_id():
    client = FakeMT5(send_result=_ns(retcode=10009, order=555, deal=777,
                                   volume=0.10, price=1.1002, comment="Done"))
    adapter = make_adapter(client)
    await adapter.connect()
    report = await adapter.submit_order(_eurusd_order())
    assert report.status == OrderStatus.FILLED
    assert report.fills[0].quantity == 0.10
    assert report.fills[0].price == 1.1002
    req = client.requests[0]
    assert req["type"] == 0                      # ORDER_TYPE_BUY
    assert req["price"] == 1.1002                # ask
    assert req["magic"] == 234000
    assert "cid-1" in req["comment"]             # recovery tag
    assert req["type_filling"] == 1              # IOC


async def test_sell_uses_bid():
    client = FakeMT5(send_result=_ns(retcode=10009, order=1, deal=2,
                                   volume=0.05, price=1.1, comment=""))
    adapter = make_adapter(client)
    await adapter.connect()
    report = await adapter.submit_order(
        _eurusd_order(side=OrderSide.SELL, quantity=0.05))
    assert report.status == OrderStatus.FILLED
    assert client.requests[0]["price"] == 1.1000  # bid


async def test_off_step_volume_rejected():
    client = FakeMT5()
    adapter = make_adapter(client)
    await adapter.connect()
    report = await adapter.submit_order(_eurusd_order(quantity=0.015))
    assert report.status == OrderStatus.REJECTED
    assert "step" in report.error
    assert client.requests == []


async def test_below_min_volume_rejected():
    adapter = make_adapter(FakeMT5(volume_min=0.05))
    await adapter.connect()
    report = await adapter.submit_order(_eurusd_order(quantity=0.02))
    assert report.status == OrderStatus.REJECTED
    assert "minimum" in report.error


async def test_wrong_symbol_rejected():
    adapter = make_adapter(FakeMT5())
    await adapter.connect()
    order = OrderRequest(
        instrument=Instrument("GBPUSD", InstrumentType.FX, "mt5_demo"),
        side=OrderSide.BUY, order_type=OrderType.MARKET, quantity=0.1,
        client_order_id="c-x", decision_id="d", price=1.0)
    report = await adapter.submit_order(order)
    assert report.status == OrderStatus.REJECTED
    assert "outside demo profile" in report.error


async def test_stale_tick_rejected():
    adapter = make_adapter(FakeMT5(tick_age_s=3600.0))
    await adapter.connect()
    report = await adapter.submit_order(_eurusd_order())
    assert report.status == OrderStatus.REJECTED
    assert "stale" in report.error


async def test_transport_uncertainty_is_unknown_never_retried():
    client = FakeMT5(send_result=None)
    adapter = make_adapter(client)
    await adapter.connect()
    report = await adapter.submit_order(_eurusd_order())
    assert report.status == OrderStatus.UNKNOWN
    assert len(client.requests) == 1            # exactly one attempt


async def test_venue_rejection_maps_rejected():
    client = FakeMT5(send_result=_ns(retcode=10019, order=0, deal=0,
                                   volume=0, price=0, comment="no money"))
    adapter = make_adapter(client)
    await adapter.connect()
    report = await adapter.submit_order(_eurusd_order())
    assert report.status == OrderStatus.REJECTED
    assert "no money" in report.error


async def test_partial_fill_distinct_status_and_quantity():
    client = FakeMT5(send_result=_ns(retcode=10010, order=9, deal=10,
                                   volume=0.04, price=1.1002, comment="partial"))
    adapter = make_adapter(client)
    await adapter.connect()
    report = await adapter.submit_order(_eurusd_order(quantity=0.10))
    assert report.status == OrderStatus.PARTIALLY_FILLED
    assert report.fills[0].quantity == 0.04


async def test_idempotent_resubmit_returns_cached_report():
    client = FakeMT5(send_result=_ns(retcode=10009, order=1, deal=2,
                                   volume=0.10, price=1.1002, comment=""))
    adapter = make_adapter(client)
    await adapter.connect()
    order = _eurusd_order()
    first = await adapter.submit_order(order)
    second = await adapter.submit_order(order)
    assert first is second
    assert len(client.requests) == 1


async def test_hedging_targeted_close_sets_position_field():
    client = FakeMT5(send_result=_ns(retcode=10009, order=2, deal=3,
                                   volume=0.10, price=1.1, comment=""))
    adapter = make_adapter(client)              # margin_mode=2 hedging
    await adapter.connect()
    order = _eurusd_order(side=OrderSide.SELL,
                          metadata={"position_ticket": 4242})
    report = await adapter.submit_order(order)
    assert report.status == OrderStatus.FILLED
    assert client.requests[0]["position"] == 4242


# ----------------------------------------------------------------------
# recovery + positions + reconciliation
# ----------------------------------------------------------------------
async def test_get_order_recovers_via_comment_and_magic():
    client = FakeMT5()
    adapter = make_adapter(client)
    await adapter.connect()
    client.history_orders = [
        _ns(ticket=99, magic=234000, comment="aalg-cid-77", state=4)]
    report = await adapter.get_order("cid-77")
    assert report.status == OrderStatus.FILLED
    assert report.updates[0].venue_order_id == "99"


async def test_get_order_unknown_when_absent():
    adapter = make_adapter(FakeMT5())
    await adapter.connect()
    report = await adapter.get_order("never-submitted")
    assert report.status == OrderStatus.UNKNOWN


async def test_positions_carry_ticket_in_hedging_mode():
    client = FakeMT5(margin_mode=2)
    client.open_positions = [
        _ns(ticket=111, symbol="EURUSD", type=0, volume=0.10,
            price_open=1.09, price_current=1.10, profit=10.0, magic=234000,
            sl=0.0, tp=0.0, time=1700000000, comment="aalg-cid-1"),
        _ns(ticket=222, symbol="EURUSD", type=1, volume=0.05,
            price_open=1.11, price_current=1.10, profit=5.0, magic=234000,
            sl=0.0, tp=0.0, time=1700000001, comment="aalg-cid-2"),
    ]
    adapter = make_adapter(client)
    await adapter.connect()
    positions = await adapter.get_positions()
    assert len(positions) == 2
    assert positions[0].quantity == 0.10
    assert positions[1].quantity == -0.05
    assert positions[0].instrument.metadata["mt5_ticket"] == 111
    assert positions[1].instrument.metadata["mt5_ticket"] == 222


async def test_positions_net_signed_quantities():
    client = FakeMT5(margin_mode=0)
    client.open_positions = [
        _ns(ticket=1, symbol="EURUSD", type=0, volume=0.10,
            price_open=1.09, price_current=1.10, profit=1.0, magic=234000,
            sl=0.0, tp=0.0, time=1700000000, comment=""),
    ]
    adapter = make_adapter(client)
    await adapter.connect()
    positions = await adapter.get_positions()
    assert positions[0].quantity == 0.10
    assert "mt5_ticket" not in positions[0].instrument.metadata


async def test_reconcile_detects_drift():
    client = FakeMT5()
    client.open_positions = [
        _ns(ticket=1, symbol="EURUSD", type=0, volume=0.10,
            price_open=1.09, price_current=1.10, profit=1.0, magic=234000,
            sl=0.0, tp=0.0, time=1700000000, comment=""),
    ]
    adapter = make_adapter(client)
    await adapter.connect()
    expected = PortfolioSnapshot(
        account_id="demo", equity=10000.0, cash=10000.0,
        positions=[Position(
            instrument=Instrument("EURUSD", InstrumentType.FX, "mt5_demo"),
            quantity=0.05, average_price=1.09)])
    result = await adapter.reconcile(expected)
    assert not result.matched
    assert "EURUSD" in result.position_differences
    ok = await adapter.reconcile(PortfolioSnapshot(
        account_id="demo", equity=1.0, cash=1.0,
        positions=[Position(
            instrument=Instrument("EURUSD", InstrumentType.FX, "mt5_demo"),
            quantity=0.10, average_price=1.09)]))
    assert ok.matched


async def test_not_connected_submit_fails_closed():
    adapter = make_adapter(FakeMT5())
    report = await adapter.submit_order(_eurusd_order())
    assert report.status == OrderStatus.REJECTED
    assert "not connected" in report.error
