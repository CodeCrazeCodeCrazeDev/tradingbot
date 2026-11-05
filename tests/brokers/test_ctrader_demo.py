"""Fake-transport conformance tests for the canonical cTrader demo adapter.

No network and no SDK required: every test injects a scripted transport and
stubs the pb2 message module. Covered: demo-endpoint pinning, isLive
enforcement, credential gating, access-rights/currency validation,
volume-grid enforcement, fill/reject/UNKNOWN mapping, order recovery via
reconcile + deals, position signing, and hedging position ids.
"""

from __future__ import annotations

import types
from typing import Any, Dict, List, Optional

import pytest

import trading_bot.brokers.ctrader_demo as mod
from trading_bot.brokers.ctrader_demo import (
    CTraderAdapterError,
    CTraderDemoAdapter,
    CTraderTransportError,
)
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


# ---------------------------------------------------------------------------
# fakes
# ---------------------------------------------------------------------------

class _F:
    """Attribute bag that answers DESCRIPTOR.name like a pb2 message."""

    def __init__(self, type_name: str, **fields):
        self.DESCRIPTOR = types.SimpleNamespace(name=type_name)
        for k, v in fields.items():
            setattr(self, k, v)


def _req(**_kw):
    return types.SimpleNamespace(symbolId=[])


class FakeMessages(types.SimpleNamespace):
    """Stand-in for OpenApiMessages_pb2: request classes as factories."""

    def __init__(self):
        super().__init__()
        for name in (
            "ProtoOAApplicationAuthReq",
            "ProtoOAGetAccountListByAccessTokenReq",
            "ProtoOAAccountAuthReq",
            "ProtoOATraderReq",
            "ProtoOAAssetListReq",
            "ProtoOASymbolsListReq",
            "ProtoOASymbolByIdReq",
            "ProtoOANewOrderReq",
            "ProtoOAReconcileReq",
            "ProtoOADealListReq",
            "ProtoOACancelOrderReq",
            "ProtoOAGetTrendbarsReq",
            "ProtoOASubscribeSpotsReq",
        ):
            setattr(self, name, lambda _n=name: _req())


class FakeTransport:
    """Scripted transport: send() pops canned responses by request shape."""

    def __init__(self, responses: Optional[Dict[str, List[Any]]] = None,
                 send_error: Optional[Exception] = None):
        self.responses = responses or {}
        self.send_error = send_error
        self.started = False
        self.stopped = False
        self.sent: List[Any] = []
        self._handler = None

    def set_event_handler(self, handler) -> None:
        self._handler = handler

    async def start(self, timeout: float = 30.0) -> None:
        self.started = True

    async def stop(self) -> None:
        self.stopped = True

    async def send(self, request: Any, timeout: float = 30.0) -> Any:
        self.sent.append(request)
        if self.send_error is not None:
            raise self.send_error
        # Scripted responses are consumed in call order per request bucket.
        for key, queue in self.responses.items():
            if queue:
                return queue.pop(0)
        raise AssertionError("FakeTransport: no scripted response left")


class FakeCreds:
    def __init__(self, secrets: Optional[Dict[str, Optional[str]]] = None):
        self.secrets = secrets or {
            "CTRADER_CLIENT_ID": "cid",
            "CTRADER_CLIENT_SECRET": "sec",
            "CTRADER_ACCESS_TOKEN": "tok",
            "CTRADER_ACCOUNT_ID": "424242",
        }

    def get_secret(self, name: str):
        return self.secrets.get(name)


def _connect_script(*, is_live=False, currency="USD",
                    account_type=0, access_rights=0,
                    symbol_name="EURUSD", trading_mode=0,
                    lot_size=100000.0, min_vol=1000.0,
                    max_vol=100000000.0, step_vol=1000.0):
    """Canned connect()-sequence responses in send order."""
    return {
        "seq": [
            _F("ProtoOAApplicationAuthRes"),
            _F("ProtoOAGetAccountListByAccessTokenRes",
               ctidTraderAccount=[
                   _F("ProtoOACtidTraderAccount",
                      ctidTraderAccountId=424242, isLive=is_live,
                      traderLogin=777),
               ]),
            _F("ProtoOAAccountAuthRes"),
            _F("ProtoOATraderRes",
               trader=_F("ProtoOATrader",
                         ctidTraderAccountId=424242, balance=1000000,
                         accessRights=access_rights,
                         depositAssetId=9, accountType=account_type,
                         moneyDigits=2, traderLogin=777)),
            _F("ProtoOAAssetListRes",
               asset=[_F("ProtoOAAsset", assetId=9, name=currency)]),
            _F("ProtoOASymbolsListRes",
               symbol=[_F("ProtoOALightSymbol", symbolId=41,
                          symbolName=symbol_name, enabled=True)]),
            _F("ProtoOASymbolRes",
               symbol=[_F("ProtoOASymbol", symbolId=41,
                          symbolName=symbol_name, digits=5,
                          tradingMode=trading_mode, lotSize=lot_size,
                          minVolume=min_vol, maxVolume=max_vol,
                          stepVolume=step_vol)]),
        ],
    }


def _adapter(transport: FakeTransport, creds: Optional[FakeCreds] = None,
             **config) -> CTraderDemoAdapter:
    return CTraderDemoAdapter(
        config=config or {}, transport=transport,
        credential_provider=creds or FakeCreds())


def _order(qty=0.01, side=OrderSide.BUY, otype=OrderType.MARKET,
           price=None, stop=None, coid="coid-1", **kw) -> OrderRequest:
    return OrderRequest(
        instrument=Instrument("EURUSD", InstrumentType.FX, "ctrader_demo",
                              currency="USD", contract_size=100000.0),
        side=side, order_type=otype, quantity=qty, price=price,
        stop_price=stop, client_order_id=coid, decision_id="d1",
        **kw)


@pytest.fixture(autouse=True)
def _fake_messages(monkeypatch):
    monkeypatch.setattr(mod, "_MESSAGES", FakeMessages())


# ---------------------------------------------------------------------------
# connect / validation
# ---------------------------------------------------------------------------

def test_rejects_non_demo_endpoint():
    t = FakeTransport()
    a = _adapter(t, host="live.ctraderapi.com", port=5035)
    import asyncio
    with pytest.raises(CTraderAdapterError, match="demo endpoint"):
        asyncio.run(a.connect())
    assert not t.started


def test_rejects_missing_credentials():
    t = FakeTransport()
    a = _adapter(t, creds=FakeCreds({"CTRADER_CLIENT_ID": "cid"}))
    import asyncio
    with pytest.raises(CTraderAdapterError, match="not provisioned"):
        asyncio.run(a.connect())


def test_rejects_live_account():
    import asyncio
    t = FakeTransport(_connect_script(is_live=True))
    a = _adapter(t)
    with pytest.raises(CTraderAdapterError, match="non-demo|isLive"):
        asyncio.run(a.connect())
    assert t.stopped  # connect cleans up on failure


def test_rejects_wrong_currency():
    import asyncio
    t = FakeTransport(_connect_script(currency="EUR"))
    a = _adapter(t)
    with pytest.raises(CTraderAdapterError, match="currency"):
        asyncio.run(a.connect())


def test_rejects_restricted_access():
    import asyncio
    t = FakeTransport(_connect_script(access_rights=2))
    a = _adapter(t)
    with pytest.raises(CTraderAdapterError, match="FULL_ACCESS"):
        asyncio.run(a.connect())


def test_rejects_missing_symbol():
    import asyncio
    t = FakeTransport(_connect_script(symbol_name="EURUSD.ecn"))
    a = _adapter(t)
    with pytest.raises(CTraderAdapterError, match="not found"):
        asyncio.run(a.connect())


def test_rejects_bad_timeframe():
    import asyncio
    t = FakeTransport(_connect_script())
    a = _adapter(t, timeframe="H1")
    with pytest.raises(CTraderAdapterError, match="timeframe"):
        asyncio.run(a.connect())


def test_connect_hedging_discovers_grid():
    import asyncio
    t = FakeTransport(_connect_script())
    a = _adapter(t)
    asyncio.run(a.connect())
    assert a.connected and a.account_mode == "hedging"
    assert a.ctid_trader_account_id == 424242
    assert a._symbol_id == 41 and a._lot_size == 100000.0
    assert a._volume_step == 1000.0


def test_connect_netting_mode():
    import asyncio
    t = FakeTransport(_connect_script(account_type=1))
    a = _adapter(t)
    asyncio.run(a.connect())
    assert a.account_mode == "netting"


# ---------------------------------------------------------------------------
# order submission
# ---------------------------------------------------------------------------

def _connected_adapter(**cfg):
    t = FakeTransport(_connect_script(**cfg.pop("script_kw", {})))
    a = _adapter(t, **cfg)
    import asyncio
    asyncio.run(a.connect())
    return a, t


def test_submit_market_fill():
    import asyncio
    a, t = _connected_adapter()
    t.responses["seq"].append(_F(
        "ProtoOAExecutionEvent", executionType=3,
        order=_F("ProtoOAOrder", orderId=9001, orderStatus=2,
                 executedVolume=1000, executionPrice=1.1002),
        deal=_F("ProtoOADeal", dealId=5001, volume=1000,
                executionPrice=1.1002, commission=700, moneyDigits=2)))
    report = asyncio.run(a.submit_order(_order()))
    assert report.status == OrderStatus.FILLED
    assert report.fills[0].quantity == pytest.approx(0.01)
    assert report.fills[0].price == pytest.approx(1.1002)
    assert report.fills[0].commission == pytest.approx(7.0)
    assert a._order_ids["coid-1"] == 9001


def test_submit_order_error_rejected():
    import asyncio
    a, t = _connected_adapter()
    t.responses["seq"].append(_F(
        "ProtoOAOrderErrorEvent", errorCode="VOLUME_EXCEEDS_LIMIT",
        description="bad volume"))
    report = asyncio.run(a.submit_order(_order()))
    assert report.status == OrderStatus.REJECTED
    assert "VOLUME_EXCEEDS_LIMIT" in report.error


def test_submit_transport_failure_is_unknown():
    import asyncio
    t = FakeTransport(_connect_script())
    a = _adapter(t)
    asyncio.run(a.connect())
    t.send_error = CTraderTransportError("socket lost")
    report = asyncio.run(a.submit_order(_order()))
    assert report.status == OrderStatus.UNKNOWN


def test_submit_off_grid_volume_rejected():
    import asyncio
    a, _ = _connected_adapter()
    # 0.015 lots = 1500 units — not a multiple of 1000-unit step.
    report = asyncio.run(a.submit_order(_order(qty=0.015)))
    assert report.status == OrderStatus.REJECTED
    assert "not on step" in report.error


def test_submit_below_min_volume_rejected():
    import asyncio
    # step=500, min=1000: 0.005 lots = 500 units lands on grid, below min.
    a, _ = _connected_adapter(script_kw=dict(step_vol=500.0))
    report = asyncio.run(a.submit_order(_order(qty=0.005)))
    assert report.status == OrderStatus.REJECTED
    assert "below broker minimum" in report.error


def test_submit_contract_size_mismatch_rejected():
    import asyncio
    a, _ = _connected_adapter()
    order = _order()
    bad = OrderRequest(
        instrument=Instrument("EURUSD", InstrumentType.FX, "ctrader_demo",
                              contract_size=1.0),
        side=order.side, order_type=order.order_type, quantity=0.01,
        client_order_id="cs-bad", decision_id="d1")
    report = asyncio.run(a.submit_order(bad))
    assert report.status == OrderStatus.REJECTED
    assert "contract_size" in report.error


def test_submit_wrong_symbol_rejected():
    import asyncio
    a, _ = _connected_adapter()
    order = OrderRequest(
        instrument=Instrument("GBPUSD", InstrumentType.FX, "ctrader_demo",
                              contract_size=100000.0),
        side=OrderSide.BUY, order_type=OrderType.MARKET, quantity=0.01,
        client_order_id="wrong-sym", decision_id="d1")
    report = asyncio.run(a.submit_order(order))
    assert report.status == OrderStatus.REJECTED


def test_submit_idempotent_replay():
    import asyncio
    a, t = _connected_adapter()
    t.responses["seq"].append(_F(
        "ProtoOAExecutionEvent", executionType=3,
        order=_F("ProtoOAOrder", orderId=9001, orderStatus=2,
                 executedVolume=1000, executionPrice=1.1),
        deal=_F("ProtoOADeal", dealId=1, volume=1000,
                executionPrice=1.1, commission=0, moneyDigits=2)))
    order = _order()
    r1 = asyncio.run(a.submit_order(order))
    r2 = asyncio.run(a.submit_order(order))
    assert r1 is r2


def test_submit_limit_builds_gtc_limit():
    import asyncio
    a, t = _connected_adapter()
    t.responses["seq"].append(_F(
        "ProtoOAExecutionEvent", executionType=2,
        order=_F("ProtoOAOrder", orderId=9002, orderStatus=1,
                 executedVolume=0, executionPrice=0.0),
        deal=_F("ProtoOADeal", volume=0)))
    report = asyncio.run(a.submit_order(
        _order(otype=OrderType.LIMIT, price=1.0950)))
    assert report.status == OrderStatus.ACCEPTED
    req = t.sent[-1]
    assert req.orderType == 2 and req.limitPrice == 1.0950
    assert req.timeInForce == 2  # GOOD_TILL_CANCEL
    assert req.clientOrderId == "coid-1"


def test_position_ticket_maps_to_position_id():
    import asyncio
    a, t = _connected_adapter()
    t.responses["seq"].append(_F(
        "ProtoOAExecutionEvent", executionType=3,
        order=_F("ProtoOAOrder", orderId=9003, orderStatus=2,
                 executedVolume=1000, executionPrice=1.1),
        deal=_F("ProtoOADeal", volume=1000, executionPrice=1.1,
                commission=0, moneyDigits=2)))
    order = _order(metadata={"position_ticket": 31337})
    asyncio.run(a.submit_order(order))
    assert t.sent[-1].positionId == 31337


# ---------------------------------------------------------------------------
# recovery / positions / reconciliation
# ---------------------------------------------------------------------------

def test_get_order_recovers_from_reconcile():
    import asyncio
    a, t = _connected_adapter()
    a._order_ids["lost-1"] = 4242
    t.responses["seq"].append(_F(
        "ProtoOAReconcileRes",
        order=[_F("ProtoOAOrder", orderId=4242, orderStatus=2,
                  clientOrderId="lost-1")],
        position=[]))
    report = asyncio.run(a.get_order("lost-1"))
    assert report.status == OrderStatus.FILLED


def test_get_order_unknown_when_absent():
    import asyncio
    a, t = _connected_adapter()
    t.responses["seq"].extend([
        _F("ProtoOAReconcileRes", order=[], position=[]),
        _F("ProtoOADealListRes", deal=[], hasMore=False),
    ])
    report = asyncio.run(a.get_order("ghost"))
    assert report.status == OrderStatus.UNKNOWN


def test_positions_signed_and_aggregated():
    import asyncio
    a, t = _connected_adapter()
    t.responses["seq"].append(_F(
        "ProtoOAReconcileRes", order=[],
        position=[
            _F("ProtoOAPosition", positionId=11, positionStatus=1,
               price=1.10, moneyDigits=2,
               tradeData=_F("ProtoOATradeData", symbolId=41, volume=2000,
                            tradeSide=1)),
            _F("ProtoOAPosition", positionId=12, positionStatus=1,
               price=1.09, moneyDigits=2,
               tradeData=_F("ProtoOATradeData", symbolId=41, volume=1000,
                            tradeSide=2)),
            _F("ProtoOAPosition", positionId=13, positionStatus=2,  # closed
               price=1.0, moneyDigits=2,
               tradeData=_F("ProtoOATradeData", symbolId=41, volume=9999,
                            tradeSide=1)),
        ]))
    positions = asyncio.run(a.get_positions())
    assert len(positions) == 2
    assert positions[0].quantity == pytest.approx(0.02)
    assert positions[1].quantity == pytest.approx(-0.01)
    assert positions[0].instrument.metadata["ctrader_position_id"] == 11


def test_reconcile_aggregates_hedged_tickets():
    import asyncio
    a, t = _connected_adapter()
    t.responses["seq"].append(_F(
        "ProtoOAReconcileRes", order=[],
        position=[
            _F("ProtoOAPosition", positionId=11, positionStatus=1,
               price=1.10, moneyDigits=2,
               tradeData=_F("ProtoOATradeData", symbolId=41, volume=1000,
                            tradeSide=1)),
            _F("ProtoOAPosition", positionId=12, positionStatus=1,
               price=1.09, moneyDigits=2,
               tradeData=_F("ProtoOATradeData", symbolId=41, volume=1000,
                            tradeSide=1)),
        ]))
    inst = Instrument("EURUSD", InstrumentType.FX, "ctrader_demo",
                      contract_size=100000.0)
    snap = PortfolioSnapshot(
        account_id="preflight", equity=10000.0, cash=10000.0,
        positions=[Position(instrument=inst, quantity=0.02,
                            average_price=1.1)])
    result = asyncio.run(a.reconcile(snap))
    assert result.matched


def test_reconcile_flags_difference():
    import asyncio
    a, t = _connected_adapter()
    t.responses["seq"].append(_F(
        "ProtoOAReconcileRes", order=[], position=[]))
    inst = Instrument("EURUSD", InstrumentType.FX, "ctrader_demo",
                      contract_size=100000.0)
    snap = PortfolioSnapshot(
        account_id="preflight", equity=10000.0, cash=10000.0,
        positions=[Position(instrument=inst, quantity=0.05,
                            average_price=1.1)])
    result = asyncio.run(a.reconcile(snap))
    assert not result.matched
    assert result.position_differences == ["EURUSD"]


def test_cancel_order():
    import asyncio
    a, t = _connected_adapter()
    a._order_ids["coid-x"] = 8128
    t.responses["seq"].append(_F(
        "ProtoOAExecutionEvent", executionType=5,
        order=_F("ProtoOAOrder", orderId=8128, orderStatus=5),
        deal=_F("ProtoOADeal", volume=0)))
    assert asyncio.run(a.cancel_order("coid-x")) is True
    req = t.sent[-1]
    assert req.orderId == 8128


def test_submit_when_disconnected_rejected():
    import asyncio
    a = _adapter(FakeTransport())
    report = asyncio.run(a.submit_order(_order()))
    assert report.status == OrderStatus.REJECTED
    assert "not connected" in report.error


# ---------------------------------------------------------------------------
# read-only account / market-data surfaces
# ---------------------------------------------------------------------------

def test_account_info_refreshes_balance():
    import asyncio
    a, t = _connected_adapter()
    t.responses["seq"].append(_F(
        "ProtoOATraderRes",
        trader=_F("ProtoOATrader", balance=2500000, moneyDigits=2)))
    info = asyncio.run(a.account_info())
    assert info.balance == pytest.approx(25000.0)
    assert info.equity == pytest.approx(25000.0)


def test_symbol_id_for_uses_light_list():
    import asyncio
    t = FakeTransport(_connect_script())
    a = _adapter(t)
    asyncio.run(a.connect())
    assert asyncio.run(a.symbol_id_for("EURUSD")) == 41
    assert asyncio.run(a.symbol_id_for("BTCUSD")) is None


def test_spot_event_updates_latest_quote():
    import asyncio
    a, t = _connected_adapter()
    assert a._transport._handler is not None  # event handler registered
    a._on_event(_F("ProtoOASpotEvent", symbolId=41,
                   bid=110010, ask=110030, timestamp=1793625000000))
    q = a.latest_quote(41)
    assert q["bid"] == pytest.approx(1.1001)
    assert q["ask"] == pytest.approx(1.1003)


def test_subscribe_spots_sends_request():
    import asyncio
    a, t = _connected_adapter()
    t.responses["seq"].append(_F("ProtoOASubscribeSpotsRes"))
    asyncio.run(a.subscribe_spots([41]))
    req = t.sent[-1]
    assert list(req.symbolId) == [41]
    assert req.ctidTraderAccountId == 424242


def test_execution_event_staged_for_recovery():
    import asyncio
    a, _ = _connected_adapter()
    a._on_event(_F("ProtoOAExecutionEvent",
                   order=_F("ProtoOAOrder", orderId=777, orderStatus=2)))
    assert 777 in a._exec_events
