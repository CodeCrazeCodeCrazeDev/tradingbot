"""Canonical cTrader *demo-only* broker adapter (Open API / protobuf).

Implements the ``foundation.ports.BrokerAdapter`` protocol so
``CanonicalExecutionService`` can route to a cTrader demo account without
any fallback to paper execution. Uses the official Spotware SDK
(``ctrader-open-api``) over Twisted; the reactor runs in a dedicated daemon
thread behind a narrow async transport seam so the adapter itself stays
asyncio-native and testable without a network.

Safety properties:

- **Demo only.** The endpoint is hard-pinned to ``demo.ctraderapi.com:5035``;
  a configured host/port that differs is a hard failure, and after the
  account list is fetched the adapter verifies ``isLive`` is false for the
  selected ``ctidTraderAccountId``. There is no flag that widens this.
- **No implicit connection.** Client id, client secret, OAuth access token
  and account id are resolved through the canonical credential provider;
  nothing is read from the process environment directly. Missing secrets
  fail closed.
- **Profile validation.** The configured symbol must exist under exactly the
  configured name (no broker suffix substitution) and its volume grid
  (``minVolume`` / ``stepVolume`` / ``maxVolume``, expressed in venue units)
  bound every submitted order; ``lotSize`` converts canonical lots <-> venue
  units and is cross-checked against ``instrument.contract_size``.
- **Fail-closed outcomes.** A transport failure or ambiguous venue reply
  produces ``OrderStatus.UNKNOWN`` — never a silent retry. Recovery resolves
  UNKNOWN via ``ProtoOAReconcileReq`` (orders) and ``ProtoOADealListReq``
  (fills) keyed on ``clientOrderId``.

Inject the transport for tests (``transport=FakeTransport()``); production
resolves the SDK lazily inside ``connect()`` so importing this module stays
cheap on hosts without Twisted.
"""

from __future__ import annotations

import asyncio
import logging
import math
import threading
from datetime import datetime, timezone
from typing import Any, Dict, List, Mapping, Optional, Tuple

from trading_bot.foundation.contracts import (
    ExecutionReport,
    Fill,
    Instrument,
    InstrumentType,
    OrderRequest,
    OrderSide,
    OrderStatus,
    OrderType,
    OrderUpdate,
    PortfolioSnapshot,
    Position,
    ReconciliationResult,
)

logger = logging.getLogger(__name__)

DEMO_HOST = "demo.ctraderapi.com"
DEMO_PORT = 5035
ALLOWED_TIMEFRAMES = frozenset({"M15"})
# cTrader Open API serializes order/position/position-close prices as plain
# doubles; monetary auxiliaries (commission, swaps) use 10**moneyDigits.

# Model enum mirrors (payload values from OpenApiModelMessages_pb2). Resolved
# against the SDK when present so a fake transport need only shape fields.
_MODEL_DEFAULTS: Dict[str, int] = {
    "ORDER_TYPE_MARKET": 1,
    "ORDER_TYPE_LIMIT": 2,
    "ORDER_TYPE_STOP": 3,
    "TRADE_SIDE_BUY": 1,
    "TRADE_SIDE_SELL": 2,
    "TIME_IN_FORCE_GOOD_TILL_CANCEL": 2,
    "ORDER_STATUS_ACCEPTED": 1,
    "ORDER_STATUS_FILLED": 2,
    "ORDER_STATUS_REJECTED": 3,
    "ORDER_STATUS_EXPIRED": 4,
    "ORDER_STATUS_CANCELLED": 5,
    "EXECUTION_ORDER_FILLED": 3,
    "EXECUTION_ORDER_PARTIAL_FILL": 11,
    "ACCOUNT_TYPE_HEDGED": 0,
    "ACCOUNT_TYPE_NETTED": 1,
    "ACCESS_RIGHTS_FULL_ACCESS": 0,
    "TRADING_MODE_ENABLED": 0,
    "POSITION_STATUS_OPEN": 1,
    "TRENDBAR_PERIOD_M15": 7,
}


class CTraderAdapterError(RuntimeError):
    """Fail-closed adapter errors: connection, profile, or account mismatch."""


class CTraderTransportError(RuntimeError):
    """Transport-level failure; venue outcome is unknowable -> UNKNOWN."""


_ENUM_FOR = {
    "ORDER_TYPE_": "ProtoOAOrderType",
    "TRADE_SIDE_": "ProtoOATradeSide",
    "TIME_IN_FORCE_": "ProtoOATimeInForce",
    "ORDER_STATUS_": "ProtoOAOrderStatus",
    "EXECUTION_": "ProtoOAExecutionType",
    "ACCOUNT_TYPE_": "ProtoOAAccountType",
    "ACCESS_RIGHTS_": "ProtoOAAccessRights",
    "TRADING_MODE_": "ProtoOATradingMode",
    "POSITION_STATUS_": "ProtoOAPositionStatus",
    "TRENDBAR_PERIOD_": "ProtoOATrendbarPeriod",
}


def _const(name: str) -> int:
    """Resolve a model constant from the SDK when importable, else default."""
    try:
        from ctrader_open_api.messages import OpenApiModelMessages_pb2 as mm
        for prefix, enum_name in _ENUM_FOR.items():
            if name.startswith(prefix):
                value_name = name[len(prefix):]
                enum = getattr(mm, enum_name, None)
                if enum is not None:
                    for v in enum.DESCRIPTOR.values:
                        if v.name == value_name or v.name.endswith(
                                "_" + value_name):
                            return v.number
    except Exception:
        pass
    return _MODEL_DEFAULTS[name]


def _msg_name(msg: Any) -> str:
    """Message type name ('ProtoOAExecutionEvent', 'ProtoOAErrorRes', ...)."""
    desc = getattr(msg, "DESCRIPTOR", None)
    return str(getattr(desc, "name", type(msg).__name__))


_MESSAGES: Any = None


def _messages() -> Any:
    """Lazy OpenApiMessages_pb2 module; tests monkeypatch ``_MESSAGES``."""
    global _MESSAGES
    if _MESSAGES is None:
        from ctrader_open_api.messages import OpenApiMessages_pb2
        _MESSAGES = OpenApiMessages_pb2
    return _MESSAGES


class _TwistedCTraderTransport:
    """Runs the Spotware SDK's Twisted client on a daemon-thread reactor.

    ``send`` bridges Deferred -> asyncio.Future; unsolicited messages
    (spot/depth/execution/margin events) are routed to ``set_event_handler``.
    One-shot per adapter instance: a stopped Twisted reactor cannot restart.
    """

    def __init__(self, host: str, port: int) -> None:
        self.host = host
        self.port = port
        self._client: Any = None
        self._reactor: Any = None
        self._thread: Optional[threading.Thread] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._event_handler: Any = None
        self._disconnect_reason: List[Any] = []

    def set_event_handler(self, handler: Any) -> None:
        self._event_handler = handler

    async def start(self, timeout: float = 30.0) -> None:
        from twisted.internet import reactor  # installs default reactor once

        self._loop = asyncio.get_running_loop()
        self._reactor = reactor
        if not reactor.running:
            self._thread = threading.Thread(
                target=reactor.run,
                kwargs={"installSignalHandlers": False},
                name="ctrader-reactor",
                daemon=True,
            )
            self._thread.start()

        connected = self._loop.create_future()

        def _create() -> None:
            from ctrader_open_api import Client, TcpProtocol

            client = Client(self.host, self.port, TcpProtocol)
            client.setConnectedCallback(
                lambda _c: self._loop.call_soon_threadsafe(
                    lambda: (not connected.done())
                    and connected.set_result(True)))
            client.setDisconnectedCallback(self._on_disconnected)
            client.setMessageReceivedCallback(self._on_message)
            client.startService()
            self._client = client

        self._reactor.callFromThread(_create)
        await asyncio.wait_for(connected, timeout)

    def _on_disconnected(self, _client: Any, reason: Any) -> None:
        self._disconnect_reason.append(reason)
        if self._loop is not None:
            self._loop.call_soon_threadsafe(
                logger.warning, "cTrader transport disconnected: %s", reason)

    def _on_message(self, _client: Any, message: Any) -> None:
        try:
            from ctrader_open_api import Protobuf
            payload = Protobuf.extract(message)
        except Exception:
            payload = message
        handler = self._event_handler
        if handler is not None and self._loop is not None:
            self._loop.call_soon_threadsafe(handler, payload)

    async def send(self, request: Any, timeout: float = 30.0) -> Any:
        loop = asyncio.get_running_loop()
        fut = loop.create_future()

        def _resolve(msg: Any) -> None:
            if not fut.done():
                try:
                    from ctrader_open_api import Protobuf
                    msg = Protobuf.extract(msg)
                except Exception:
                    pass
                fut.set_result(msg)

        def _reject(failure: Any) -> None:
            if not fut.done():
                fut.set_exception(CTraderTransportError(str(failure)))

        def _issue() -> None:
            try:
                d = self._client.send(request)
                d.addCallbacks(
                    lambda m: loop.call_soon_threadsafe(_resolve, m),
                    lambda f: loop.call_soon_threadsafe(_reject, f),
                )
            except Exception as exc:  # send itself blew up on the reactor
                loop.call_soon_threadsafe(_reject, exc)

        self._reactor.callFromThread(_issue)
        return await asyncio.wait_for(fut, timeout)

    async def stop(self) -> None:
        try:
            if self._client is not None:
                self._reactor.callFromThread(self._client.stopService)
        except Exception:
            pass
        if self._reactor is not None and self._reactor.running:
            try:
                self._reactor.callFromThread(self._reactor.stop)
            except Exception:
                pass
        if self._thread is not None:
            self._thread.join(timeout=5.0)


class CTraderDemoAdapter:
    """Typed cTrader demo-account adapter behind the canonical boundary.

    ``quantity`` on ``OrderRequest`` is interpreted in lots; the adapter
    converts to venue units via the symbol's ``lotSize`` and validates
    against the broker volume grid before submitting.
    """

    venue_id = "ctrader_demo"

    def __init__(self, config: Optional[Mapping[str, Any]] = None,
                 *, transport: Any = None,
                 credential_provider: Any = None) -> None:
        self.config: Dict[str, Any] = dict(config or {})
        self.symbol = str(self.config.get("symbol", "EURUSD"))
        self.timeframe = str(self.config.get("timeframe", "M15"))
        self.account_currency = str(
            self.config.get("account_currency", "USD")).upper()
        self.host = str(self.config.get("host", DEMO_HOST))
        self.port = int(self.config.get("port", DEMO_PORT))
        self._transport = transport
        self._credentials = credential_provider
        self.connected = False
        self.session_mode: Optional[str] = None
        self.account_mode: Optional[str] = None        # "netting" | "hedging"
        self.ctid_trader_account_id: Optional[int] = None
        self.trader_login: Optional[int] = None
        self._access_token: Optional[str] = None
        self._money_digits = 2
        self._symbol_id: Optional[int] = None
        self._lot_size = 0.0                           # units per lot
        self._volume_min = 0.0                         # venue units
        self._volume_max = math.inf                    # venue units
        self._volume_step = 0.0                        # venue units
        self._digits = 5
        # symbolId -> {"name","lotSize","digits"} for cross-symbol positions
        self._symbol_meta: Dict[int, Dict[str, Any]] = {}
        # symbol name -> symbolId from the last light-symbol list
        self._light_symbols: Dict[str, int] = {}
        # symbolId -> {"bid","ask","ts"} latest ProtoOASpotEvent (subscribed)
        self._spot_quotes: Dict[int, Dict[str, Any]] = {}
        self._balance = 0.0
        self._order_ids: Dict[str, int] = {}           # client_order_id -> id
        self._reports: Dict[str, ExecutionReport] = {}
        self._exec_events: Dict[int, List[Any]] = {}   # orderId -> events

    # ------------------------------------------------------------------
    # credentials + connection
    # ------------------------------------------------------------------
    def _resolve_secret(self, config_key: str, env_default: str) -> Optional[str]:
        name = str(self.config.get(config_key, env_default))
        provider = self._credentials
        if provider is None:
            from trading_bot.security.canonical_provider import get_credential_provider
            provider = get_credential_provider()
        return provider.get_secret(name)

    def _load_transport(self) -> Any:
        if self._transport is not None:
            return self._transport
        try:
            import ctrader_open_api  # noqa: F401 - presence check only
            import twisted  # noqa: F401
        except ImportError as exc:
            raise CTraderAdapterError(
                "ctrader-open-api/Twisted are not installed; cTrader demo "
                "execution is unavailable (no paper fallback)") from exc
        self._transport = _TwistedCTraderTransport(self.host, self.port)
        return self._transport

    async def _request(self, request: Any, timeout: float = 30.0) -> Any:
        """Send a request and return the typed response, fail-closed on
        venue-level error payloads."""
        response = await self._transport.send(request, timeout=timeout)
        name = _msg_name(response)
        if name == "ProtoOAErrorRes":
            raise CTraderAdapterError(
                f"venue error {getattr(response, 'errorCode', '?')}: "
                f"{getattr(response, 'description', '')}")
        return response

    async def connect(self) -> None:
        transport = self._load_transport()
        if self.host != DEMO_HOST or self.port != DEMO_PORT:
            raise CTraderAdapterError(
                f"endpoint {self.host}:{self.port} is not the demo endpoint "
                f"{DEMO_HOST}:{DEMO_PORT}; refusing non-demo venue")
        if self.timeframe not in ALLOWED_TIMEFRAMES:
            raise CTraderAdapterError(
                f"timeframe {self.timeframe!r} outside the demo profile "
                f"{sorted(ALLOWED_TIMEFRAMES)}")
        client_id = self._resolve_secret("client_id_env", "CTRADER_CLIENT_ID")
        client_secret = self._resolve_secret(
            "client_secret_env", "CTRADER_CLIENT_SECRET")
        access_token = self._resolve_secret(
            "access_token_env", "CTRADER_ACCESS_TOKEN")
        account_id_raw = self._resolve_secret(
            "account_id_env", "CTRADER_ACCOUNT_ID")
        if not all((client_id, client_secret, access_token, account_id_raw)):
            raise CTraderAdapterError(
                "cTrader demo credentials not provisioned (expected env "
                "secrets CTRADER_CLIENT_ID / CTRADER_CLIENT_SECRET / "
                "CTRADER_ACCESS_TOKEN / CTRADER_ACCOUNT_ID or configured "
                "*_env names)")
        try:
            self.ctid_trader_account_id = int(str(account_id_raw))
        except (TypeError, ValueError):
            raise CTraderAdapterError(
                "CTRADER_ACCOUNT_ID is not an integer account id")
        self._access_token = str(access_token)

        msgs = _messages()
        ProtoOAApplicationAuthReq = msgs.ProtoOAApplicationAuthReq
        ProtoOAGetAccountListByAccessTokenReq = (
            msgs.ProtoOAGetAccountListByAccessTokenReq)
        ProtoOAAccountAuthReq = msgs.ProtoOAAccountAuthReq
        ProtoOATraderReq = msgs.ProtoOATraderReq
        ProtoOAAssetListReq = msgs.ProtoOAAssetListReq
        ProtoOASymbolsListReq = msgs.ProtoOASymbolsListReq

        try:
            await transport.start()
            transport.set_event_handler(self._on_event)
            req = ProtoOAApplicationAuthReq()
            req.clientId = str(client_id)
            req.clientSecret = str(client_secret)
            await self._request(req)

            req = ProtoOAGetAccountListByAccessTokenReq()
            req.accessToken = self._access_token
            accounts = await self._request(req)
            self._validate_account(accounts)

            req = ProtoOAAccountAuthReq()
            req.ctidTraderAccountId = self.ctid_trader_account_id
            req.accessToken = self._access_token
            await self._request(req)

            req = ProtoOATraderReq()
            req.ctidTraderAccountId = self.ctid_trader_account_id
            trader = await self._request(req)
            self._validate_trader(trader)

            req = ProtoOAAssetListReq()
            req.ctidTraderAccountId = self.ctid_trader_account_id
            await self._validate_currency(await self._request(req))

            req = ProtoOASymbolsListReq()
            req.ctidTraderAccountId = self.ctid_trader_account_id
            await self._resolve_symbol(await self._request(req))
        except Exception:
            await transport.stop()
            raise

        self.connected = True
        self.session_mode = "oauth"
        logger.info(
            "cTrader demo adapter connected: account=%s login=%s mode=%s "
            "symbol=%s(%s) tf=%s", self.ctid_trader_account_id,
            self.trader_login, self.account_mode, self.symbol,
            self._symbol_id, self.timeframe)

    def _validate_account(self, accounts_res: Any) -> None:
        """Fail closed unless the configured account exists and is demo."""
        matched = None
        for acct in getattr(accounts_res, "ctidTraderAccount", ()):
            if int(getattr(acct, "ctidTraderAccountId", -1)) == (
                    self.ctid_trader_account_id):
                matched = acct
                break
        if matched is None:
            raise CTraderAdapterError(
                f"account {self.ctid_trader_account_id} not in the access "
                "token's account list — token/account mismatch")
        if bool(getattr(matched, "isLive", True)):
            raise CTraderAdapterError(
                f"account {self.ctid_trader_account_id} isLive=True; "
                "refusing non-demo account")
        self.trader_login = int(getattr(matched, "traderLogin", 0)) or None

    def _validate_trader(self, trader_res: Any) -> None:
        trader = getattr(trader_res, "trader", None)
        if trader is None:
            raise CTraderAdapterError("ProtoOATraderRes carried no trader")
        rights = int(getattr(trader, "accessRights", -1))
        if rights != _const("ACCESS_RIGHTS_FULL_ACCESS"):
            raise CTraderAdapterError(
                f"account accessRights={rights} is not FULL_ACCESS "
                f"({_const('ACCESS_RIGHTS_FULL_ACCESS')})")
        account_type = int(getattr(trader, "accountType", -1))
        if account_type == _const("ACCOUNT_TYPE_HEDGED"):
            self.account_mode = "hedging"
        elif account_type == _const("ACCOUNT_TYPE_NETTED"):
            self.account_mode = "netting"
        else:
            raise CTraderAdapterError(
                f"unrecognized accountType={account_type}")
        self._money_digits = int(getattr(trader, "moneyDigits", 2) or 2)
        self._deposit_asset_id = int(getattr(trader, "depositAssetId", 0))
        # ProtoOATrader.balance is scaled by 10**moneyDigits.
        self._balance = (float(getattr(trader, "balance", 0.0) or 0.0)
                         / (10 ** self._money_digits))

    async def _validate_currency(self, assets_res: Any) -> None:
        name = None
        for asset in getattr(assets_res, "asset", ()):
            if int(getattr(asset, "assetId", -1)) == self._deposit_asset_id:
                name = str(getattr(asset, "name", ""))
                break
        if name is None:
            raise CTraderAdapterError(
                f"deposit asset {self._deposit_asset_id} not in asset list")
        if name.upper() != self.account_currency:
            raise CTraderAdapterError(
                f"account currency {name!r} != required "
                f"{self.account_currency!r}")

    async def _resolve_symbol(self, symbols_res: Any) -> None:
        self._light_symbols = {
            str(getattr(light, "symbolName", "")):
            int(getattr(light, "symbolId", 0))
            for light in getattr(symbols_res, "symbol", ())
            if bool(getattr(light, "enabled", True))
        }
        symbol_id = None
        for light in getattr(symbols_res, "symbol", ()):
            if (str(getattr(light, "symbolName", "")) == self.symbol
                    and bool(getattr(light, "enabled", True))):
                symbol_id = int(getattr(light, "symbolId", 0))
                break
        if symbol_id is None:
            raise CTraderAdapterError(
                f"symbol {self.symbol!r} not found/enabled on this account "
                "(exact name required; suffix variants are different "
                "contracts)")
        meta = await self._symbol_by_id(symbol_id)
        if int(getattr(meta, "tradingMode", -1)) != _const(
                "TRADING_MODE_ENABLED"):
            raise CTraderAdapterError(
                f"symbol {self.symbol} tradingMode="
                f"{getattr(meta, 'tradingMode', '?')} is not ENABLED")
        self._symbol_id = symbol_id
        self._digits = int(getattr(meta, "digits", 5))
        self._lot_size = float(getattr(meta, "lotSize", 0.0))
        self._volume_min = float(getattr(meta, "minVolume", 0.0))
        self._volume_max = float(getattr(meta, "maxVolume", 0.0) or math.inf)
        self._volume_step = float(getattr(meta, "stepVolume", 0.0))
        if self._lot_size <= 0 or self._volume_step <= 0 or (
                self._volume_min <= 0):
            raise CTraderAdapterError(
                f"symbol {self.symbol} reports invalid volume grid "
                f"(lotSize={self._lot_size}, min={self._volume_min}, "
                f"step={self._volume_step})")

    async def _symbol_by_id(self, symbol_id: int) -> Any:
        cached = self._symbol_meta.get(symbol_id)
        if cached is not None:
            return cached["proto"]
        req = _messages().ProtoOASymbolByIdReq()
        req.ctidTraderAccountId = self.ctid_trader_account_id
        req.symbolId.append(symbol_id)
        res = await self._request(req)
        for sym in getattr(res, "symbol", ()):
            if int(getattr(sym, "symbolId", -1)) == symbol_id:
                self._symbol_meta[symbol_id] = {
                    "proto": sym,
                    "name": str(getattr(sym, "symbolName", "")),
                    "lotSize": float(getattr(sym, "lotSize", 100000.0)),
                    "digits": int(getattr(sym, "digits", 5)),
                }
                return sym
        raise CTraderAdapterError(
            f"symbolId {symbol_id} absent from ProtoOASymbolByIdRes")

    async def disconnect(self) -> None:
        if self._transport is not None and self.connected:
            await self._transport.stop()
        self.connected = False

    def _on_event(self, payload: Any) -> None:
        """Async-venue events routed from the transport thread."""
        name = _msg_name(payload)
        if name == "ProtoOAExecutionEvent":
            order = getattr(payload, "order", None)
            order_id = getattr(order, "orderId", None)
            if order_id is not None:
                self._exec_events.setdefault(int(order_id), []).append(payload)
        elif name == "ProtoOASpotEvent":
            symbol_id = int(getattr(payload, "symbolId", -1))
            digits = self._symbol_meta.get(symbol_id, {}).get(
                "digits", self._digits)
            scale = 10 ** digits
            self._spot_quotes[symbol_id] = {
                "bid": float(getattr(payload, "bid", 0.0)) / scale,
                "ask": float(getattr(payload, "ask", 0.0)) / scale,
                "ts": float(getattr(payload, "timestamp", 0.0)),
            }

    # ------------------------------------------------------------------
    # read-only account / market-data surfaces for risk state + runners
    # ------------------------------------------------------------------
    async def account_info(self) -> Any:
        """Live equity/balance for VenueBackedStateProvider (re-fetched)."""
        import types as _t
        req = _messages().ProtoOATraderReq()
        req.ctidTraderAccountId = self.ctid_trader_account_id
        res = await self._request(req)
        trader = getattr(res, "trader", None)
        if trader is None:
            raise CTraderAdapterError("ProtoOATraderRes carried no trader")
        self._balance = (float(getattr(trader, "balance", 0.0) or 0.0)
                         / (10 ** self._money_digits))
        return _t.SimpleNamespace(
            equity=self._balance, balance=self._balance)

    async def symbol_id_for(self, name: str) -> Optional[int]:
        """symbolId for an exact enabled symbol name, or None."""
        return self._light_symbols.get(name)

    async def subscribe_spots(self, symbol_ids: List[int]) -> None:
        """Subscribe ProtoOASpotEvent for the given symbolIds (read-only)."""
        if not symbol_ids:
            return
        req = _messages().ProtoOASubscribeSpotsReq()
        req.ctidTraderAccountId = self.ctid_trader_account_id
        req.symbolId.extend(int(s) for s in symbol_ids)
        await self._request(req)

    def latest_quote(self, symbol_id: int) -> Optional[Dict[str, Any]]:
        """Most recent subscribed spot quote for a symbolId, or None."""
        return self._spot_quotes.get(int(symbol_id))

    # ------------------------------------------------------------------
    # order submission
    # ------------------------------------------------------------------
    def _check_volume(self, lots: float) -> Tuple[int, Optional[str]]:
        """Convert canonical lots -> venue units and validate the grid.

        Returns (units_int, error). A quantity that does not land on the
        step grid is rejected rather than silently resized, because the
        approved quantity is part of the risk decision.
        """
        if lots <= 0 or not math.isfinite(lots):
            return 0, "non-positive volume"
        units = lots * self._lot_size
        snapped = round(round(units / self._volume_step)
                        * self._volume_step)
        if abs(snapped - units) > max(1e-6, self._volume_step * 1e-6):
            return int(snapped), (
                f"volume {lots} lots ({units} units) not on step "
                f"{self._volume_step}")
        if snapped < self._volume_min - 1e-9:
            return int(snapped), (
                f"volume {snapped} units below broker minimum "
                f"{self._volume_min}")
        if snapped > self._volume_max + 1e-9:
            return int(snapped), (
                f"volume {snapped} units above broker maximum "
                f"{self._volume_max}")
        return int(snapped), None

    async def submit_order(self, order: OrderRequest) -> ExecutionReport:
        if not self.connected:
            return ExecutionReport(
                client_order_id=order.client_order_id,
                status=OrderStatus.REJECTED,
                error="adapter not connected")
        existing = self._reports.get(order.client_order_id)
        if existing is not None:
            return existing
        if order.instrument.symbol != self.symbol:
            report = ExecutionReport(
                client_order_id=order.client_order_id,
                status=OrderStatus.REJECTED,
                error=f"symbol {order.instrument.symbol!r} outside demo "
                      f"profile {self.symbol!r}")
            self._reports[order.client_order_id] = report
            return report

        # The upstream risk decision is only valid if the proposal's
        # instrument spec matches the venue contract.
        req_cs = float(getattr(order.instrument, "contract_size", 0.0) or 0.0)
        if abs(req_cs - self._lot_size) > 1e-8:
            report = ExecutionReport(
                client_order_id=order.client_order_id,
                status=OrderStatus.REJECTED,
                error=f"instrument contract_size {req_cs} != venue lotSize "
                      f"{self._lot_size} — risk evaluated wrong notional")
            self._reports[order.client_order_id] = report
            return report

        units, volume_error = self._check_volume(order.quantity)
        if volume_error:
            report = ExecutionReport(
                client_order_id=order.client_order_id,
                status=OrderStatus.REJECTED,
                error=volume_error)
            self._reports[order.client_order_id] = report
            return report

        try:
            request = self._build_request(order, units)
        except CTraderAdapterError as exc:
            report = ExecutionReport(
                client_order_id=order.client_order_id,
                status=OrderStatus.REJECTED, error=str(exc))
            self._reports[order.client_order_id] = report
            return report

        try:
            response = await self._transport.send(request)
        except Exception as exc:
            # Venue outcome unknowable — durable UNKNOWN, never auto-retry.
            report = ExecutionReport(
                client_order_id=order.client_order_id,
                status=OrderStatus.UNKNOWN,
                error=f"send failed: {exc}")
            self._reports[order.client_order_id] = report
            return report

        report = self._map_result(order, response, units)
        self._reports[order.client_order_id] = report
        return report

    def _build_request(self, order: OrderRequest, units: int) -> Any:
        req = _messages().ProtoOANewOrderReq()
        req.ctidTraderAccountId = self.ctid_trader_account_id
        req.symbolId = self._symbol_id
        req.tradeSide = (_const("TRADE_SIDE_BUY")
                         if order.side is OrderSide.BUY
                         else _const("TRADE_SIDE_SELL"))
        req.volume = int(units)
        req.clientOrderId = str(order.client_order_id)[:50]
        req.comment = f"aalg-{order.client_order_id}"[:120]
        req.label = f"aalg-{order.client_order_id}"[:120]
        position_id = order.metadata.get("position_ticket")
        if position_id is not None:
            req.positionId = int(position_id)

        if order.order_type is OrderType.MARKET:
            req.orderType = _const("ORDER_TYPE_MARKET")
        elif order.order_type is OrderType.LIMIT and order.price is not None:
            req.orderType = _const("ORDER_TYPE_LIMIT")
            req.limitPrice = float(order.price)
            req.timeInForce = _const("TIME_IN_FORCE_GOOD_TILL_CANCEL")
        elif order.order_type is OrderType.STOP and (
                order.stop_price is not None):
            req.orderType = _const("ORDER_TYPE_STOP")
            req.stopPrice = float(order.stop_price)
            req.timeInForce = _const("TIME_IN_FORCE_GOOD_TILL_CANCEL")
        else:
            raise CTraderAdapterError(
                f"unsupported order type {order.order_type.value} for "
                "cTrader demo")
        return req

    def _map_result(self, order: OrderRequest, response: Any,
                    units: int) -> ExecutionReport:
        name = _msg_name(response)
        if name in ("ProtoOAOrderErrorEvent", "ProtoOAErrorRes"):
            return ExecutionReport(
                client_order_id=order.client_order_id,
                status=OrderStatus.REJECTED,
                error=f"venue error "
                      f"{getattr(response, 'errorCode', '?')}: "
                      f"{getattr(response, 'description', '')}")
        if name != "ProtoOAExecutionEvent":
            # Unrecognized reply — the venue may have accepted it.
            return ExecutionReport(
                client_order_id=order.client_order_id,
                status=OrderStatus.UNKNOWN,
                error=f"unexpected venue reply {name!r}")

        venue_order = getattr(response, "order", None)
        order_id = getattr(venue_order, "orderId", None)
        if order_id is not None:
            self._order_ids[order.client_order_id] = int(order_id)
        order_status = int(getattr(venue_order, "orderStatus", 0) or 0)
        deal = getattr(response, "deal", None)
        filled_units = float(
            getattr(venue_order, "executedVolume", 0.0)
            or getattr(deal, "filledVolume", 0.0)
            or getattr(deal, "volume", 0.0) or 0.0)
        filled_lots = filled_units / self._lot_size if self._lot_size else 0.0
        fill_price = float(
            getattr(deal, "executionPrice", 0.0)
            or getattr(venue_order, "executionPrice", 0.0) or 0.0)

        if order_status == _const("ORDER_STATUS_FILLED") or (
                deal is not None and filled_units > 0):
            status = OrderStatus.FILLED
            if 0 < filled_units < units - 1e-9:
                status = OrderStatus.PARTIALLY_FILLED
            fills: List[Fill] = []
            if filled_lots > 0 and fill_price > 0:
                md = int(getattr(deal, "moneyDigits", self._money_digits)
                         or self._money_digits)
                fills.append(Fill(
                    client_order_id=order.client_order_id,
                    venue_order_id=str(
                        getattr(deal, "dealId", order_id or "")),
                    instrument=order.instrument,
                    side=order.side,
                    quantity=filled_lots,
                    price=fill_price,
                    commission=(float(getattr(deal, "commission", 0.0) or 0.0)
                                / (10 ** md)),
                ))
            expected = order.price if order.price else fill_price
            return ExecutionReport(
                client_order_id=order.client_order_id,
                status=status,
                updates=[OrderUpdate(
                    client_order_id=order.client_order_id,
                    status=status,
                    venue_order_id=str(order_id) if order_id else None,
                    filled_quantity=filled_lots,
                    average_price=fill_price or None,
                )],
                fills=fills,
                expected_price=expected,
                slippage_bps=(abs(fill_price - expected) / expected * 1e4
                              if expected and fill_price else None),
            )
        if order_status in (
            _const("ORDER_STATUS_REJECTED"),
            _const("ORDER_STATUS_EXPIRED"),
            _const("ORDER_STATUS_CANCELLED"),
        ):
            status = {
                _const("ORDER_STATUS_REJECTED"): OrderStatus.REJECTED,
                _const("ORDER_STATUS_EXPIRED"): OrderStatus.EXPIRED,
                _const("ORDER_STATUS_CANCELLED"): OrderStatus.CANCELLED,
            }[order_status]
            return ExecutionReport(
                client_order_id=order.client_order_id,
                status=status,
                error=f"venue orderStatus={order_status}")
        # ACCEPTED pending (limit/stop resting) or anything else ambiguous.
        if order_status == _const("ORDER_STATUS_ACCEPTED"):
            return ExecutionReport(
                client_order_id=order.client_order_id,
                status=OrderStatus.ACCEPTED,
                updates=[OrderUpdate(
                    client_order_id=order.client_order_id,
                    status=OrderStatus.ACCEPTED,
                    venue_order_id=str(order_id) if order_id else None,
                )])
        return ExecutionReport(
            client_order_id=order.client_order_id,
            status=OrderStatus.UNKNOWN,
            error=f"execution event without resolvable status "
                  f"(orderStatus={order_status})")

    # ------------------------------------------------------------------
    # order lookup / recovery
    # ------------------------------------------------------------------
    async def get_order(self, client_order_id: str) -> ExecutionReport:
        cached = self._reports.get(client_order_id)
        if cached is not None and cached.status in (
            OrderStatus.FILLED, OrderStatus.CANCELLED,
            OrderStatus.REJECTED, OrderStatus.EXPIRED,
        ):
            return cached
        report = await self._lookup_venue_order(client_order_id)
        if report is not None:
            self._reports[client_order_id] = report
            return report
        return cached or ExecutionReport(
            client_order_id=client_order_id, status=OrderStatus.UNKNOWN)

    async def _lookup_venue_order(
            self, client_order_id: str) -> Optional[ExecutionReport]:
        """Reconstruct an order's state from the venue without resubmitting."""
        order_id = self._order_ids.get(client_order_id)

        def matches_order(o: Any) -> bool:
            if order_id is not None and int(
                    getattr(o, "orderId", -1)) == order_id:
                return True
            return str(getattr(o, "clientOrderId", "") or "") == (
                str(client_order_id)[:50])

        try:
            msgs = _messages()
            ProtoOAReconcileReq = msgs.ProtoOAReconcileReq
            ProtoOADealListReq = msgs.ProtoOADealListReq

            req = ProtoOAReconcileReq()
            req.ctidTraderAccountId = self.ctid_trader_account_id
            rec = await self._request(req)
            for o in getattr(rec, "order", ()):
                if not matches_order(o):
                    continue
                status = self._order_status_map(
                    int(getattr(o, "orderStatus", 0) or 0))
                return ExecutionReport(
                    client_order_id=client_order_id,
                    status=status,
                    updates=[OrderUpdate(
                        client_order_id=client_order_id,
                        status=status,
                        venue_order_id=str(getattr(o, "orderId", "")),
                    )])

            # Not pending — check staged execution events then deal history.
            if order_id is not None:
                import types as _t
                stub_order = _t.SimpleNamespace(
                    client_order_id=client_order_id,
                    instrument=Instrument(
                        self.symbol, InstrumentType.FX, self.venue_id),
                    side=OrderSide.BUY, price=None)
                for ev in self._exec_events.get(order_id, ()):
                    staged = self._map_result(stub_order, ev, 0)
                    if staged.status in (
                        OrderStatus.FILLED, OrderStatus.PARTIALLY_FILLED,
                        OrderStatus.REJECTED, OrderStatus.CANCELLED,
                        OrderStatus.EXPIRED, OrderStatus.ACCEPTED,
                    ):
                        return staged

            now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
            req = ProtoOADealListReq()
            req.ctidTraderAccountId = self.ctid_trader_account_id
            req.fromTimestamp = now_ms - 7 * 24 * 3600 * 1000
            req.toTimestamp = now_ms
            req.maxRows = 100
            deals = await self._request(req)
            fills = []
            for d in getattr(deals, "deal", ()):
                if order_id is not None and int(
                        getattr(d, "orderId", -1)) != order_id:
                    continue
                if order_id is None:
                    continue  # deals carry no clientOrderId — needs order id
                meta = self._symbol_meta.get(int(getattr(d, "symbolId", -1)), {})
                md = int(getattr(d, "moneyDigits", self._money_digits)
                         or self._money_digits)
                fills.append(Fill(
                    client_order_id=client_order_id,
                    venue_order_id=str(getattr(d, "dealId", "")),
                    instrument=Instrument(
                        meta.get("name", self.symbol), InstrumentType.FX,
                        self.venue_id,
                        contract_size=meta.get("lotSize", self._lot_size)),
                    side=(OrderSide.BUY
                          if int(getattr(d, "tradeSide", -1))
                          == _const("TRADE_SIDE_BUY") else OrderSide.SELL),
                    quantity=(float(getattr(d, "volume", 0.0))
                              / (meta.get("lotSize") or self._lot_size or 1)),
                    price=float(getattr(d, "executionPrice", 0.0)),
                    commission=(float(getattr(d, "commission", 0.0) or 0.0)
                                / (10 ** md)),
                ))
            if fills:
                return ExecutionReport(
                    client_order_id=client_order_id,
                    status=OrderStatus.FILLED, fills=fills)
        except Exception as exc:
            logger.warning(
                "cTrader venue lookup failed for %s: %s", client_order_id, exc)
            return None
        return None

    @staticmethod
    def _order_status_map(order_status: int) -> OrderStatus:
        mapping = {
            _const("ORDER_STATUS_ACCEPTED"): OrderStatus.ACCEPTED,
            _const("ORDER_STATUS_FILLED"): OrderStatus.FILLED,
            _const("ORDER_STATUS_REJECTED"): OrderStatus.REJECTED,
            _const("ORDER_STATUS_EXPIRED"): OrderStatus.EXPIRED,
            _const("ORDER_STATUS_CANCELLED"): OrderStatus.CANCELLED,
        }
        return mapping.get(order_status, OrderStatus.UNKNOWN)

    async def cancel_order(self, client_order_id: str) -> bool:
        if not self.connected:
            return False
        order_id = self._order_ids.get(client_order_id)
        if order_id is None:
            # Recover the venue id from pending orders matching clientOrderId.
            try:
                req = _messages().ProtoOAReconcileReq()
                req.ctidTraderAccountId = self.ctid_trader_account_id
                rec = await self._request(req)
                for o in getattr(rec, "order", ()):
                    if str(getattr(o, "clientOrderId", "") or "") == (
                            str(client_order_id)[:50]):
                        order_id = int(getattr(o, "orderId"))
                        break
            except Exception:
                return False
        if order_id is None:
            return False
        req = _messages().ProtoOACancelOrderReq()
        req.ctidTraderAccountId = self.ctid_trader_account_id
        req.orderId = order_id
        try:
            response = await self._request(req)
        except Exception:
            return False
        ok = (_msg_name(response) == "ProtoOAExecutionEvent"
              and int(getattr(getattr(response, "order", None),
                              "orderStatus", 0) or 0)
              == _const("ORDER_STATUS_CANCELLED"))
        if ok:
            self._reports[client_order_id] = ExecutionReport(
                client_order_id=client_order_id, status=OrderStatus.CANCELLED)
        return ok

    # ------------------------------------------------------------------
    # positions + reconciliation
    # ------------------------------------------------------------------
    async def get_positions(self) -> List[Position]:
        if not self.connected:
            return []
        req = _messages().ProtoOAReconcileReq()
        req.ctidTraderAccountId = self.ctid_trader_account_id
        rec = await self._request(req)
        positions: List[Position] = []
        for pos in getattr(rec, "position", ()):
            if int(getattr(pos, "positionStatus", -1)) != _const(
                    "POSITION_STATUS_OPEN"):
                continue
            td = getattr(pos, "tradeData", None)
            symbol_id = int(getattr(td, "symbolId", -1))
            try:
                meta = (self._symbol_meta.get(symbol_id)
                        or {"name": "", "lotSize": self._lot_size})
                if symbol_id not in self._symbol_meta:
                    await self._symbol_by_id(symbol_id)
                    meta = self._symbol_meta[symbol_id]
            except CTraderAdapterError:
                meta = {"name": f"UNKNOWN_{symbol_id}",
                        "lotSize": self._lot_size or 100000.0}
            lot_size = meta.get("lotSize") or self._lot_size or 100000.0
            units = float(getattr(td, "volume", 0.0))
            lots = units / lot_size
            signed = (lots if int(getattr(td, "tradeSide", -1))
                      == _const("TRADE_SIDE_BUY") else -lots)
            md = int(getattr(pos, "moneyDigits", self._money_digits)
                     or self._money_digits)
            metadata: Dict[str, Any] = {}
            position_id = getattr(pos, "positionId", None)
            if self.account_mode == "hedging" and position_id is not None:
                metadata["ctrader_position_id"] = int(position_id)
            positions.append(Position(
                instrument=Instrument(
                    meta.get("name") or f"UNKNOWN_{symbol_id}",
                    InstrumentType.FX, self.venue_id,
                    currency=self.account_currency,
                    contract_size=lot_size,
                    metadata=metadata),
                quantity=signed,
                average_price=float(getattr(pos, "price", 0.0)),
                unrealized_pnl=0.0,   # venue PnL needs quote conversion
            ))
        return positions

    async def reconcile(
            self, portfolio: Optional[PortfolioSnapshot] = None
    ) -> ReconciliationResult:
        venue_positions = await self.get_positions()
        actual: Dict[str, float] = {}
        for p in venue_positions:
            sym = p.instrument.symbol
            actual[sym] = actual.get(sym, 0.0) + float(p.quantity)
        expected: Dict[str, float] = {}
        for p in (portfolio.positions if portfolio else []):
            sym = p.instrument.symbol
            expected[sym] = expected.get(sym, 0.0) + float(p.quantity)
        differences = [
            sym for sym in sorted(set(expected) | set(actual))
            if abs(expected.get(sym, 0.0) - actual.get(sym, 0.0)) > 1e-8
        ]
        return ReconciliationResult(
            venue=self.venue_id,
            checked_at=datetime.now(timezone.utc),
            matched=not differences,
            position_differences=differences,
        )
