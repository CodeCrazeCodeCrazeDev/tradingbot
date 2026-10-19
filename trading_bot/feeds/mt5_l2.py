"""MT5 Level-2 (Market Book) + tick-tape feed -> observation fields.

The MT5 Python SDK already connected by ``mt5_demo_runner`` exposes
``market_book_add``/``market_book_get`` — the venue's published Depth of
Market — and ``symbol_info_tick`` whose flags carry real trade direction
(TICK_FLAG_BUY/TICK_FLAG_SELL). Both are free on the demo feed.

Honest-data rule: fields are emitted only from real SDK returns. When
the venue publishes no book (some MetaQuotes-Demo symbols return empty)
the keys stay absent and the lob/order-book adapters keep abstaining.
Tick flags that aren't trade prints (quote-only updates) are not fed to
``order_flow`` — the microbiome adapter gets real prints, not quotes.
"""

from __future__ import annotations

import logging
from collections import deque
from typing import Any, Deque, Dict, List, Optional

logger = logging.getLogger(__name__)


class MT5L2Feed:
    """Per-venue L2: market_book depth snapshot + real trade prints."""

    def __init__(self, client: Any, tape_maxlen: int = 200) -> None:
        self._client = client
        self._symbols: List[str] = []
        self._tape: Dict[str, Deque[Dict[str, Any]]] = {}
        self._last_seen: Dict[str, tuple] = {}
        self._tape_maxlen = tape_maxlen
        # Trade-flag constants resolved lazily from the SDK module —
        # MetaTrader5.TICK_FLAG_BUY/SELL mark real prints.
        self._flag_buy = getattr(client, "TICK_FLAG_BUY", 32)
        self._flag_sell = getattr(client, "TICK_FLAG_SELL", 64)

    def start(self, symbols: List[str]) -> List[str]:
        """Subscribe the market book for each symbol. Returns the subset
        the venue actually feeds — symbols that fail or publish an empty
        book are dropped honestly."""
        live: List[str] = []
        for sym in symbols:
            ok = False
            try:
                ok = bool(self._client.market_book_add(sym))
            except Exception as exc:  # noqa: BLE001
                logger.debug("market_book_add %s failed: %s", sym, exc)
            if ok:
                live.append(sym)
                self._tape.setdefault(
                    sym, deque(maxlen=self._tape_maxlen))
            else:
                logger.info("market book unavailable for %s", sym)
        self._symbols = live
        if live:
            logger.info("mt5 L2 book subscribed: %s", live)
        return live

    def stop(self) -> None:
        for sym in self._symbols:
            try:
                self._client.market_book_release(sym)
            except Exception:  # noqa: BLE001
                pass
        self._symbols = []

    def snapshot(self, symbol: str) -> Dict[str, Any]:
        """Latest DOM snapshot -> order_book/bids/asks/imbalance fields."""
        try:
            book = self._client.market_book_get(symbol)
        except Exception:  # noqa: BLE001
            return {}
        if not book:
            return {}
        bids = [[float(getattr(e, "price", 0)), float(getattr(e, "volume", 0))]
                for e in book
                if "buy" in str(getattr(e, "type", "")).lower()]
        asks = [[float(getattr(e, "price", 0)), float(getattr(e, "volume", 0))]
                for e in book
                if "sell" in str(getattr(e, "type", "")).lower()]
        if not (bids and asks):
            return {}
        bids.sort(key=lambda x: x[0], reverse=True)
        asks.sort(key=lambda x: x[0])
        best_bid, best_ask = bids[0][0], asks[0][0]
        mid = (best_bid + best_ask) / 2.0
        bv = sum(v for _, v in bids)
        av = sum(v for _, v in asks)
        out: Dict[str, Any] = {
            "order_book": {"bids": bids, "asks": asks},
            "bids": bids, "asks": asks,
            "bid": best_bid, "ask": best_ask,
            "bid_volume": bv, "ask_volume": av,
            "imbalance_ratio": (bv - av) / (bv + av) if bv + av else 0.0,
            "depth_ratio": bv / av if av else None,
        }
        if mid:
            out["spread_bps"] = (best_ask - best_bid) / mid * 1e4
        return out

    def tape(self, symbol: str) -> Dict[str, Any]:
        """Poll the tick for real trade prints and emit ``order_flow``.

        A tick carries flags: quote updates (bid/ask moves) are NOT
        prints — only TICK_FLAG_BUY/SELL ticks with a real last-price +
        volume enter the tape."""
        try:
            tick = self._client.symbol_info_tick(symbol)
        except Exception:  # noqa: BLE001
            return {}
        if tick is None:
            return {}
        flags = int(getattr(tick, "flags", 0))
        last = float(getattr(tick, "last", 0) or 0)
        vol = float(getattr(tick, "volume_real", 0)
                    or getattr(tick, "volume", 0) or 0)
        seen = (float(getattr(tick, "time", 0)),
                int(getattr(tick, "time_msc", 0)), flags, last)
        q = self._tape.setdefault(
            symbol, deque(maxlen=self._tape_maxlen))
        if last and vol and seen != self._last_seen.get(symbol):
            if flags & self._flag_buy:
                q.append({"side": "buy", "price": last, "volume": vol,
                          "time_msc": seen[1]})
            elif flags & self._flag_sell:
                q.append({"side": "sell", "price": last, "volume": vol,
                          "time_msc": seen[1]})
            self._last_seen[symbol] = seen
        if not q:
            return {}
        return {"order_flow": list(q)}
