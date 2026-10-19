"""cTrader Level-2 (Depth of Market) feed -> observation enrichment.

Connects the existing ``trading_bot.ctrader`` Open API connector,
subscribes depth quotes for the selected symbols, and exposes
``snapshot(symbol)`` which maps the live ``DepthOfMarket`` cache to the
observation fields the conditional advisory adapters consume
(``order_book``, ``bids``/``asks``, ``imbalance_ratio``, ``depth_ratio``,
``bid_volume``/``ask_volume``, ``bid``/``ask``, ``spread_bps``).

Honest-data rule: ``snapshot`` returns only fields derived from a real
ProtoOADepthEvent. Depth is a book, not a trade tape — ``order_flow``
therefore stays absent so the tape-dependent adapters keep abstaining.

Credentials resolve through the canonical provider:
``CTRADER_CLIENT_ID``, ``CTRADER_CLIENT_SECRET`` and
``CTRADER_ACCESS_TOKEN`` (free cTrader Open API app + demo account).
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class CTraderL2Feed:
    """Background cTrader depth feed. Zero-cost: demo Open API only."""

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        self.config = config or {}
        self._integration = None
        self._symbols: List[str] = []

    async def start(self, symbols: List[str]) -> bool:
        """Connect and subscribe depth for ``symbols``. Returns False on
        any failure — callers treat the feed as absent."""
        try:
            from trading_bot.ctrader.ctrader_integration import (
                CTraderIntegration)
        except Exception as exc:  # noqa: BLE001
            logger.warning("ctrader integration import failed: %s", exc)
            return False
        try:
            self._integration = CTraderIntegration(dict(self.config))
            if not await self._integration.connect():
                return False
            await self._integration.market_data.subscribe_depth(
                list(symbols))
            self._symbols = list(symbols)
            logger.info("ctrader L2 depth subscribed: %s", symbols)
            return True
        except Exception as exc:  # noqa: BLE001 - optional feed
            logger.warning("ctrader L2 connect failed: %s", exc)
            self._integration = None
            return False

    async def stop(self) -> None:
        if self._integration is not None:
            try:
                await self._integration.disconnect()
            except Exception:  # noqa: BLE001
                pass
            self._integration = None

    def snapshot(self, symbol: str) -> Dict[str, Any]:
        """Observation fields from the latest real DOM snapshot, or {}."""
        if self._integration is None:
            return {}
        dom = self._integration.get_dom(symbol)
        if dom is None or not (dom.bids and dom.asks):
            return {}
        bids = [[float(e.price), float(e.volume)] for e in dom.bids]
        asks = [[float(e.price), float(e.volume)] for e in dom.asks]
        best_bid, best_ask = bids[0][0], asks[0][0]
        mid = (best_bid + best_ask) / 2.0
        bv = sum(v for _, v in bids)
        av = sum(v for _, v in asks)
        out: Dict[str, Any] = {
            "order_book": {"bids": bids, "asks": asks},
            "bids": bids, "asks": asks,
            "bid": best_bid, "ask": best_ask,
            "bid_volume": bv, "ask_volume": av,
            "imbalance_ratio": float(getattr(dom, "imbalance", 0.0) or 0.0),
            "depth_ratio": bv / av if av else None,
            "l2_timestamp": dom.timestamp.isoformat()
            if getattr(dom, "timestamp", None) is not None else None,
        }
        if mid:
            out["spread_bps"] = (best_ask - best_bid) / mid * 1e4
        return out
