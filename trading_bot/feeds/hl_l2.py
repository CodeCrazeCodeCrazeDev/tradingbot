"""Hyperliquid L2 (order book) feed — keyless public endpoint.

POST /info {"type":"l2Book","coin":<SYM>} returns 20x20 levels.
snapshot(symbol) maps it to the same observation fields
ctrader_l2.py produces — the order-flow/institutional advisory
adapters consume them identically (order_book, bids, asks,
imbalance_ratio, depth_ratio, spread_bps, bid_volume/ask_volume).

No credentials needed: market data is public on Hyperliquid.
"""

from __future__ import annotations

import json
import logging
import urllib.request
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

_API = "https://api.hyperliquid.xyz/info"
_TIMEOUT = 15


def fetch_l2(coin: str) -> Optional[Dict[str, Any]]:
    try:
        req = urllib.request.Request(
            _API,
            data=json.dumps({"type": "l2Book", "coin": coin}).encode(),
            headers={"Content-Type": "application/json"}, method="POST")
        return json.loads(
            urllib.request.urlopen(req, timeout=_TIMEOUT).read())
    except Exception as e:  # noqa: BLE001
        logger.warning("hl l2 fetch failed: %s", e)
        return None


def snapshot(coin: str, depth: int = 10) -> Dict[str, Any]:
    """Enrichment fields for one coin's book — same contract as
    CTraderL2Feed.snapshot: real data only, absent on failure."""
    d = fetch_l2(coin)
    if not d:
        return {}
    try:
        bids, asks = d["levels"][0], d["levels"][1]
        # Normalize to [[price, size], ...] pairs — the same level shape
        # ctrader_l2.py and mt5_l2.py emit. Raw HL dicts break every
        # pair-unpacking consumer (e.g. upgrades LiquidityAnalyzer).
        bids = [[float(l["px"]), float(l["sz"])] for l in bids[:depth]]
        asks = [[float(l["px"]), float(l["sz"])] for l in asks[:depth]]
        if not bids or not asks:
            return {}
        bb = sum(l[1] for l in bids)
        ba = sum(l[1] for l in asks)
        best_bid = bids[0][0]
        best_ask = asks[0][0]
        mid = (best_bid + best_ask) / 2.0
        spread_bps = (best_ask - best_bid) / mid * 1e4 if mid else None
        out = {
            "order_book": {"bids": bids, "asks": asks},
            "bids": bids, "asks": asks,
            "bid": best_bid, "ask": best_ask,
            "bid_volume": bb, "ask_volume": ba,
            "imbalance_ratio": (bb - ba) / max(1e-9, bb + ba),
            "depth_ratio": bb / max(1e-9, ba),
        }
        if spread_bps is not None:
            out["spread_bps"] = spread_bps
        return out
    except (KeyError, IndexError, ValueError, TypeError) as e:
        logger.warning("hl l2 parse failed: %s", e)
        return {}
