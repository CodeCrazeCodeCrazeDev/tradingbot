"""Canonical MetaTrader 5 *demo-only* broker adapter.

Implements the ``foundation.ports.BrokerAdapter`` protocol so
``CanonicalExecutionService`` can route to an MT5 demo account without any
fallback to paper execution. Safety properties:

- **Demo only.** ``connect()`` verifies ``account_info().trade_mode`` is the
  terminal's DEMO account mode and refuses anything else. There is no config
  flag that widens this; a REAL or CONTEST account is a hard failure.
- **No implicit connection.** Credentials are resolved through the canonical
  credential provider (env names are configurable); nothing is read from the
  process environment directly.
- **Profile validation.** The configured symbol must exist, must be exactly
  the configured name (no silent ``EURUSD.pro`` suffix substitution), must
  permit full trading, and its volume step/min/max bound every submitted lot.
- **Netting + hedging.** The account margin mode is discovered at connect.
  In hedging mode individual tickets are tracked (``instrument.metadata``
  carries ``mt5_ticket``) and a targeted close is requested via
  ``order.metadata["position_ticket"]``. In netting mode opposite-direction
  orders net against the symbol position naturally.
- **Fail-closed outcomes.** A missing/ambiguous venue reply produces
  ``OrderStatus.UNKNOWN`` — never a silent retry. Recovery resolves UNKNOWN
  via ``get_order()`` lookups keyed on the client order id embedded in the
  order comment + magic number.

Inject the SDK client for tests (``client=FakeMT5()``); production resolves
``MetaTrader5`` lazily inside ``connect()`` so importing this module stays
cheap on non-Windows hosts.
"""

from __future__ import annotations

import logging
import math
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

# MT5 numeric constants (mirrored so a fake client need only provide the
# attribute subset it uses; the real SDK's module attributes win).
_CONST_DEFAULTS: Dict[str, int] = {
    "ORDER_TYPE_BUY": 0,
    "ORDER_TYPE_SELL": 1,
    "ORDER_TYPE_BUY_LIMIT": 2,
    "ORDER_TYPE_SELL_LIMIT": 3,
    "ORDER_TYPE_BUY_STOP": 4,
    "ORDER_TYPE_SELL_STOP": 5,
    "TRADE_ACTION_DEAL": 1,
    "TRADE_ACTION_REMOVE": 2,
    "TRADE_ACTION_PENDING": 5,
    "ORDER_TIME_GTC": 0,
    "ORDER_FILLING_IOC": 1,
    "TRADE_RETCODE_DONE": 10009,
    "TRADE_RETCODE_DONE_PARTIAL": 10010,
    "TRADE_RETCODE_REQUOTE": 10004,
    "TRADE_RETCODE_REJECT": 10006,
    "TRADE_RETCODE_CANCEL": 10007,
    "TRADE_RETCODE_INVALID_VOLUME": 10014,
    "TRADE_RETCODE_INVALID_PRICE": 10015,
    "TRADE_RETCODE_NO_MONEY": 10019,
    "TRADE_RETCODE_PRICE_OFF": 10021,
    "TRADE_RETCODE_CONNECTION": 10031,
    "TRADE_RETCODE_TIMEOUT": 10012,
    "ACCOUNT_TRADE_MODE_DEMO": 0,
    "ACCOUNT_TRADE_MODE_CONTEST": 1,
    "ACCOUNT_TRADE_MODE_REAL": 2,
    "ACCOUNT_MARGIN_MODE_RETAIL_NETTING": 0,
    "ACCOUNT_MARGIN_MODE_EXCHANGE": 1,
    "ACCOUNT_MARGIN_MODE_RETAIL_HEDGING": 2,
    "SYMBOL_TRADE_MODE_DISABLED": 0,
    "SYMBOL_TRADE_MODE_LONGONLY": 1,
    "SYMBOL_TRADE_MODE_SHORTONLY": 2,
    "SYMBOL_TRADE_MODE_CLOSEONLY": 3,
    "SYMBOL_TRADE_MODE_FULL": 4,
    "ORDER_STATE_STARTED": 0,
    "ORDER_STATE_PLACED": 1,
    "ORDER_STATE_CANCELED": 2,
    "ORDER_STATE_PARTIAL": 3,
    "ORDER_STATE_FILLED": 4,
    "ORDER_STATE_REJECTED": 5,
    "ORDER_STATE_EXPIRED": 6,
    "ORDER_STATE_REQUEST_ADD": 7,
    "ORDER_STATE_REQUEST_MODIFY": 8,
    "ORDER_STATE_REQUEST_CANCEL": 9,
    "POSITION_TYPE_BUY": 0,
    "POSITION_TYPE_SELL": 1,
    "DEAL_TYPE_BUY": 0,
    "DEAL_TYPE_SELL": 1,
    "DEAL_ENTRY_IN": 0,
    "DEAL_ENTRY_OUT": 1,
}

ALLOWED_TIMEFRAMES = frozenset({"M15"})
COMMENT_PREFIX = "aalg-"        # client_order_id embedded in order comments
MAX_COMMENT_LEN = 31


class MT5AdapterError(RuntimeError):
    """Fail-closed adapter errors: connection, profile, or account mismatch."""


def _const(client: Any, name: str) -> int:
    """Resolve an MT5 constant from the client, else the mirrored default."""
    return int(getattr(client, name, _CONST_DEFAULTS[name]))


def _comment(client_order_id: str) -> str:
    return (COMMENT_PREFIX + client_order_id)[:MAX_COMMENT_LEN]


class MT5DemoAdapter:
    """Typed MT5 demo-account adapter behind the canonical execution boundary.

    ``quantity`` on ``OrderRequest`` is interpreted in lots and must land on
    the broker's volume step within [volume_min, volume_max].
    """

    venue_id = "mt5_demo"

    def __init__(self, config: Optional[Mapping[str, Any]] = None,
                 *, client: Any = None,
                 credential_provider: Any = None) -> None:
        self.config: Dict[str, Any] = dict(config or {})
        self.symbol = str(self.config.get("symbol", "EURUSD"))
        self.timeframe = str(self.config.get("timeframe", "M15"))
        self.account_currency = str(self.config.get("account_currency", "USD")).upper()
        self.magic = int(self.config.get("magic", 234000))
        self.deviation = int(self.config.get("deviation", 20))
        self._client = client
        self._credentials = credential_provider
        self.connected = False
        self.account_mode: Optional[str] = None    # "netting" | "hedging"
        self.account_login: Optional[int] = None
        self._volume_min = 0.0
        self._volume_max = math.inf
        self._volume_step = 0.01
        self._contract_size = 100000.0
        self._order_tickets: Dict[str, int] = {}    # client_order_id -> ticket
        self._reports: Dict[str, ExecutionReport] = {}

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

    def _load_client(self) -> Any:
        if self._client is not None:
            return self._client
        try:
            import MetaTrader5 as mt5  # noqa: N813 - SDK module name
        except ImportError as exc:
            raise MT5AdapterError(
                "MetaTrader5 package is not installed; MT5 demo execution is "
                "unavailable (no paper fallback)") from exc
        self._client = mt5
        return mt5

    async def connect(self) -> None:
        client = self._load_client()
        if self.timeframe not in ALLOWED_TIMEFRAMES:
            raise MT5AdapterError(
                f"timeframe {self.timeframe!r} outside the demo profile "
                f"{sorted(ALLOWED_TIMEFRAMES)}")
        if not client.initialize():
            raise MT5AdapterError(f"MT5 initialize failed: {client.last_error()}")

        login = self._resolve_secret("login_env", "MT5_LOGIN")
        password = self._resolve_secret("password_env", "MT5_PASSWORD")
        server = self._resolve_secret("server_env", "MT5_SERVER")
        if not login or not password or not server:
            client.shutdown()
            raise MT5AdapterError(
                "MT5 demo credentials not provisioned (expected env secrets "
                "MT5_LOGIN / MT5_PASSWORD / MT5_SERVER or configured *_env names)")
        if not client.login(int(login), password, server):
            client.shutdown()
            raise MT5AdapterError(f"MT5 login failed: {client.last_error()}")

        try:
            self._validate_account(client)
            self._validate_symbol(client)
        except Exception:
            client.shutdown()
            raise
        self.connected = True
        logger.info(
            "MT5 demo adapter connected: login=%s mode=%s symbol=%s tf=%s",
            self.account_login, self.account_mode, self.symbol, self.timeframe)

    def _validate_account(self, client: Any) -> None:
        info = client.account_info()
        if info is None:
            raise MT5AdapterError("account_info() unavailable after login")
        trade_mode = int(getattr(info, "trade_mode", -1))
        if trade_mode != _const(client, "ACCOUNT_TRADE_MODE_DEMO"):
            raise MT5AdapterError(
                f"account trade_mode={trade_mode} is not DEMO "
                f"({_const(client, 'ACCOUNT_TRADE_MODE_DEMO')}); refusing "
                "non-demo account")
        currency = str(getattr(info, "currency", "")).upper()
        if currency != self.account_currency:
            raise MT5AdapterError(
                f"account currency {currency!r} != required {self.account_currency!r}")
        margin_mode = int(getattr(info, "margin_mode", -1))
        if margin_mode == _const(client, "ACCOUNT_MARGIN_MODE_RETAIL_HEDGING"):
            self.account_mode = "hedging"
        elif margin_mode in (
            _const(client, "ACCOUNT_MARGIN_MODE_RETAIL_NETTING"),
            _const(client, "ACCOUNT_MARGIN_MODE_EXCHANGE"),
        ):
            self.account_mode = "netting"
        else:
            raise MT5AdapterError(f"unrecognized account margin_mode={margin_mode}")
        if not getattr(info, "trade_allowed", True):
            raise MT5AdapterError("account trade_allowed is false")
        self.account_login = int(getattr(info, "login", 0)) or None

    def _validate_symbol(self, client: Any) -> None:
        info = client.symbol_info(self.symbol)
        if info is None:
            raise MT5AdapterError(f"symbol {self.symbol!r} not found on this account")
        if getattr(info, "name", None) != self.symbol:
            raise MT5AdapterError(
                f"broker resolved {self.symbol!r} to {getattr(info, 'name', None)!r}; "
                "exact symbol required (suffix variants are a different contract)")
        if not getattr(info, "visible", True):
            if not client.symbol_select(self.symbol, True):
                raise MT5AdapterError(f"cannot select symbol {self.symbol!r}")
            info = client.symbol_info(self.symbol)
        trade_mode = int(getattr(info, "trade_mode", -1))
        if trade_mode != _const(client, "SYMBOL_TRADE_MODE_FULL"):
            raise MT5AdapterError(
                f"symbol {self.symbol} trade_mode={trade_mode} is not FULL")
        self._volume_min = float(getattr(info, "volume_min", 0.01))
        self._volume_max = float(getattr(info, "volume_max", 500.0))
        self._volume_step = float(getattr(info, "volume_step", 0.01))
        self._contract_size = float(getattr(info, "trade_contract_size", 100000.0))
        if self._volume_step <= 0 or self._volume_min <= 0:
            raise MT5AdapterError(
                f"symbol {self.symbol} reports invalid volume grid "
                f"(min={self._volume_min}, step={self._volume_step})")

    async def disconnect(self) -> None:
        if self._client is not None and self.connected:
            self._client.shutdown()
        self.connected = False

    # ------------------------------------------------------------------
    # order submission
    # ------------------------------------------------------------------
    def _check_volume(self, volume: float) -> Tuple[float, Optional[str]]:
        """Validate a requested lot quantity against the broker volume grid.

        Returns (snapped_volume, error). The snapped value equals the
        requested quantity within fp noise — a quantity that does not land on
        the step grid is rejected rather than silently resized, because the
        approved quantity is part of the risk decision.
        """
        if volume <= 0 or not math.isfinite(volume):
            return 0.0, "non-positive volume"
        snapped = round(round(volume / self._volume_step) * self._volume_step, 8)
        if abs(snapped - volume) > 1e-8:
            return snapped, (
                f"volume {volume} not on step {self._volume_step}")
        if snapped < self._volume_min - 1e-12:
            return snapped, (
                f"volume {snapped} below broker minimum {self._volume_min}")
        if snapped > self._volume_max + 1e-12:
            return snapped, (
                f"volume {snapped} above broker maximum {self._volume_max}")
        return snapped, None

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
                error=f"symbol {order.instrument.symbol!r} outside demo profile "
                      f"{self.symbol!r}")
            self._reports[order.client_order_id] = report
            return report

        volume, volume_error = self._check_volume(order.quantity)
        if volume_error:
            report = ExecutionReport(
                client_order_id=order.client_order_id,
                status=OrderStatus.REJECTED,
                error=volume_error)
            self._reports[order.client_order_id] = report
            return report

        client = self._client
        request = self._build_request(order, volume)
        if isinstance(request, ExecutionReport):
            self._reports[order.client_order_id] = request
            return request

        result = client.order_send(request)
        if result is None:
            # Venue outcome unknowable — durable UNKNOWN, never auto-retry.
            report = ExecutionReport(
                client_order_id=order.client_order_id,
                status=OrderStatus.UNKNOWN,
                error=f"order_send returned no result: {client.last_error()}")
            self._reports[order.client_order_id] = report
            return report

        retcode = int(getattr(result, "retcode", -1))
        venue_order_id = getattr(result, "order", None)
        if venue_order_id:
            self._order_tickets[order.client_order_id] = int(venue_order_id)
        report = self._map_result(order, result, retcode, volume)
        self._reports[order.client_order_id] = report
        return report

    def _build_request(self, order: OrderRequest, volume: float) -> Any:
        client = self._client
        tick = client.symbol_info_tick(self.symbol)
        if tick is None:
            return ExecutionReport(
                client_order_id=order.client_order_id,
                status=OrderStatus.REJECTED,
                error=f"no current tick for {self.symbol}")
        now = getattr(tick, "time", 0)
        if now and (datetime.now(timezone.utc).timestamp() - float(now)) > 60.0:
            return ExecutionReport(
                client_order_id=order.client_order_id,
                status=OrderStatus.REJECTED,
                error="stale market tick (>60s) — refusing to price")

        base = {
            "symbol": self.symbol,
            "volume": volume,
            "deviation": self.deviation,
            "magic": self.magic,
            "comment": _comment(order.client_order_id),
            "type_time": _const(client, "ORDER_TIME_GTC"),
            "type_filling": _const(client, "ORDER_FILLING_IOC"),
        }
        position_ticket = order.metadata.get("position_ticket")
        if position_ticket is not None:
            base["position"] = int(position_ticket)

        buy = order.side is OrderSide.BUY
        if order.order_type is OrderType.MARKET:
            return {
                **base,
                "action": _const(client, "TRADE_ACTION_DEAL"),
                "type": _const(client, "ORDER_TYPE_BUY") if buy
                        else _const(client, "ORDER_TYPE_SELL"),
                "price": float(tick.ask if buy else tick.bid),
            }
        if order.order_type is OrderType.LIMIT and order.price is not None:
            return {
                **base,
                "action": _const(client, "TRADE_ACTION_PENDING"),
                "type": _const(client, "ORDER_TYPE_BUY_LIMIT") if buy
                        else _const(client, "ORDER_TYPE_SELL_LIMIT"),
                "price": float(order.price),
            }
        if order.order_type is OrderType.STOP and order.stop_price is not None:
            return {
                **base,
                "action": _const(client, "TRADE_ACTION_PENDING"),
                "type": _const(client, "ORDER_TYPE_BUY_STOP") if buy
                        else _const(client, "ORDER_TYPE_SELL_STOP"),
                "price": float(order.stop_price),
            }
        return ExecutionReport(
            client_order_id=order.client_order_id,
            status=OrderStatus.REJECTED,
            error=f"unsupported order type {order.order_type.value} for MT5 demo")

    def _map_result(self, order: OrderRequest, result: Any,
                    retcode: int, volume: float) -> ExecutionReport:
        client = self._client
        comment = str(getattr(result, "comment", "") or "")
        filled_volume = float(getattr(result, "volume", 0.0) or 0.0)
        fill_price = float(getattr(result, "price", 0.0) or 0.0)
        venue_order_id = getattr(result, "order", None)
        venue_deal_id = getattr(result, "deal", None)

        if retcode in (
            _const(client, "TRADE_RETCODE_DONE"),
            _const(client, "TRADE_RETCODE_DONE_PARTIAL"),
        ):
            fills: List[Fill] = []
            status = OrderStatus.FILLED
            if retcode == _const(client, "TRADE_RETCODE_DONE_PARTIAL") or (
                filled_volume and filled_volume < volume - 1e-12
            ):
                status = OrderStatus.PARTIALLY_FILLED
            if filled_volume > 0 and fill_price > 0:
                fills.append(Fill(
                    client_order_id=order.client_order_id,
                    venue_order_id=str(venue_deal_id or venue_order_id or ""),
                    instrument=order.instrument,
                    side=order.side,
                    quantity=filled_volume,
                    price=fill_price,
                ))
            expected = order.price if order.price else fill_price
            slippage_bps = (
                abs(fill_price - expected) / expected * 1e4
                if expected and fill_price else None
            )
            return ExecutionReport(
                client_order_id=order.client_order_id,
                status=status,
                updates=[OrderUpdate(
                    client_order_id=order.client_order_id,
                    status=status,
                    venue_order_id=str(venue_order_id) if venue_order_id else None,
                    filled_quantity=filled_volume,
                    average_price=fill_price or None,
                )],
                fills=fills,
                expected_price=expected,
                slippage_bps=slippage_bps,
            )
        if retcode in (
            _const(client, "TRADE_RETCODE_CONNECTION"),
            _const(client, "TRADE_RETCODE_TIMEOUT"),
        ):
            return ExecutionReport(
                client_order_id=order.client_order_id,
                status=OrderStatus.UNKNOWN,
                error=f"retcode {retcode}: {comment or 'transport uncertain'}")
        return ExecutionReport(
            client_order_id=order.client_order_id,
            status=OrderStatus.REJECTED,
            error=f"retcode {retcode}: {comment or 'venue rejection'}")

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
        report = self._lookup_venue_order(client_order_id)
        if report is not None:
            self._reports[client_order_id] = report
            return report
        return cached or ExecutionReport(
            client_order_id=client_order_id, status=OrderStatus.UNKNOWN)

    def _lookup_venue_order(self, client_order_id: str) -> Optional[ExecutionReport]:
        """Reconstruct an order's state from the venue without resubmitting."""
        client = self._client
        ticket = self._order_tickets.get(client_order_id)
        tag = _comment(client_order_id)

        def matches(obj: Any) -> bool:
            if ticket is not None and int(getattr(obj, "ticket", -1)) == ticket:
                return True
            return (int(getattr(obj, "magic", -1)) == self.magic
                    and str(getattr(obj, "comment", "") or "") == tag)

        try:
            for pending in client.orders_get() or ():
                if matches(pending):
                    return ExecutionReport(
                        client_order_id=client_order_id,
                        status=OrderStatus.ACCEPTED,
                        updates=[OrderUpdate(
                            client_order_id=client_order_id,
                            status=OrderStatus.ACCEPTED,
                            venue_order_id=str(getattr(pending, "ticket", "")),
                        )])
            history = client.history_orders_get() or ()
            for hist in history:
                if matches(hist):
                    status = self._order_state_status(client, getattr(hist, "state", None))
                    return ExecutionReport(
                        client_order_id=client_order_id,
                        status=status,
                        updates=[OrderUpdate(
                            client_order_id=client_order_id,
                            status=status,
                            venue_order_id=str(getattr(hist, "ticket", "")),
                        )])
            deals = client.history_deals_get() or ()
            fills = [
                Fill(
                    client_order_id=client_order_id,
                    venue_order_id=str(getattr(d, "order", getattr(d, "ticket", ""))),
                    instrument=Instrument(self.symbol, InstrumentType.FX, self.venue_id),
                    side=(OrderSide.BUY
                          if int(getattr(d, "type", -1)) == _const(client, "DEAL_TYPE_BUY")
                          else OrderSide.SELL),
                    quantity=float(getattr(d, "volume", 0.0)),
                    price=float(getattr(d, "price", 0.0)),
                    commission=float(getattr(d, "commission", 0.0) or 0.0),
                )
                for d in deals if matches(d)
            ]
            if fills:
                return ExecutionReport(
                    client_order_id=client_order_id,
                    status=OrderStatus.FILLED,
                    fills=fills)
        except Exception as exc:
            logger.warning("MT5 venue lookup failed for %s: %s", client_order_id, exc)
            return None
        return None

    @staticmethod
    def _order_state_status(client: Any, state: Any) -> OrderStatus:
        mapping = {
            _const(client, "ORDER_STATE_PLACED"): OrderStatus.ACCEPTED,
            _const(client, "ORDER_STATE_CANCELED"): OrderStatus.CANCELLED,
            _const(client, "ORDER_STATE_PARTIAL"): OrderStatus.PARTIALLY_FILLED,
            _const(client, "ORDER_STATE_FILLED"): OrderStatus.FILLED,
            _const(client, "ORDER_STATE_REJECTED"): OrderStatus.REJECTED,
            _const(client, "ORDER_STATE_EXPIRED"): OrderStatus.EXPIRED,
            _const(client, "ORDER_STATE_STARTED"): OrderStatus.SUBMITTED,
            _const(client, "ORDER_STATE_REQUEST_ADD"): OrderStatus.SUBMITTED,
            _const(client, "ORDER_STATE_REQUEST_MODIFY"): OrderStatus.ACCEPTED,
            _const(client, "ORDER_STATE_REQUEST_CANCEL"): OrderStatus.CANCEL_PENDING,
        }
        return mapping.get(state, OrderStatus.UNKNOWN)

    async def cancel_order(self, client_order_id: str) -> bool:
        if not self.connected:
            return False
        ticket = self._order_tickets.get(client_order_id)
        if ticket is None:
            for pending in self._client.orders_get() or ():
                if str(getattr(pending, "comment", "") or "") == _comment(client_order_id):
                    ticket = int(getattr(pending, "ticket"))
                    break
        if ticket is None:
            return False
        result = self._client.order_send({
            "action": _const(self._client, "TRADE_ACTION_REMOVE"),
            "order": ticket,
        })
        if result is None:
            return False
        ok = int(getattr(result, "retcode", -1)) == _const(self._client, "TRADE_RETCODE_DONE")
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
        positions = []
        for pos in self._client.positions_get() or ():
            pos_type = int(getattr(pos, "type", -1))
            volume = float(getattr(pos, "volume", 0.0))
            signed = volume if pos_type == _const(self._client, "POSITION_TYPE_BUY") else -volume
            metadata: Dict[str, Any] = {}
            ticket = getattr(pos, "ticket", None)
            if self.account_mode == "hedging" and ticket is not None:
                metadata["mt5_ticket"] = int(ticket)
            positions.append(Position(
                instrument=Instrument(
                    str(getattr(pos, "symbol", self.symbol)),
                    InstrumentType.FX, self.venue_id,
                    currency=self.account_currency,
                    contract_size=self._contract_size,
                    metadata=metadata),
                quantity=signed,
                average_price=float(getattr(pos, "price_open", 0.0)),
                unrealized_pnl=float(getattr(pos, "profit", 0.0) or 0.0),
            ))
        return positions

    async def reconcile(self, portfolio: Optional[PortfolioSnapshot] = None) -> ReconciliationResult:
        venue_positions = await self.get_positions()
        actual = {p.instrument.symbol: p.quantity for p in venue_positions}
        expected = {
            p.instrument.symbol: p.quantity
            for p in (portfolio.positions if portfolio else [])
        }
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
