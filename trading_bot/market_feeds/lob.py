"""Level-2 order book contract and feed adapters.

LOBSnapshot is the canonical microstructure unit: normalized (price, size)
levels on each side plus derived features (mid, spread, imbalance, depth)
that the brain can consume as evidence.

Feeds:
  LOBFileFeed   — replays recorded snapshots from JSONL/CSV on disk.
  BrokerLOBFeed — polls BrokerInterface.get_order_book() for live books.

Neither fabricates liquidity: no file → FileNotFoundError; no broker →
the feed raises on construction.
"""

import csv
import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

logger = logging.getLogger(__name__)

Level = Tuple[float, float]  # (price, size)


@dataclass
class LOBSnapshot:
    """Normalized L2 order-book snapshot."""

    symbol: str
    timestamp: float
    bids: List[Level] = field(default_factory=list)
    asks: List[Level] = field(default_factory=list)

    @property
    def best_bid(self) -> Optional[float]:
        return self.bids[0][0] if self.bids else None

    @property
    def best_ask(self) -> Optional[float]:
        return self.asks[0][0] if self.asks else None

    @property
    def mid(self) -> Optional[float]:
        if self.best_bid is None or self.best_ask is None:
            return None
        return (self.best_bid + self.best_ask) / 2.0

    @property
    def spread_bps(self) -> Optional[float]:
        m = self.mid
        if m is None or m <= 0:
            return None
        return (self.best_ask - self.best_bid) / m * 1e4

    @property
    def imbalance(self) -> Optional[float]:
        """Bid-minus-ask size over total displayed size, in [-1, 1]."""
        b = sum(s for _, s in self.bids)
        a = sum(s for _, s in self.asks)
        return (b - a) / (b + a) if (b + a) > 0 else None

    def depth_within_bps(self, bps: float) -> Tuple[float, float]:
        """(bid_depth, ask_depth) within `bps` of mid."""
        m = self.mid
        if m is None:
            return 0.0, 0.0
        band = m * bps / 1e4
        bd = sum(s for p, s in self.bids if m - p <= band)
        ad = sum(s for p, s in self.asks if p - m <= band)
        return bd, ad

    def features(self, depth_bps: float = 5.0) -> Dict[str, float]:
        """Microstructure feature dict for cognition consumption."""
        bd, ad = self.depth_within_bps(depth_bps)
        return {
            "mid": self.mid or 0.0,
            "spread_bps": self.spread_bps or 0.0,
            "imbalance": self.imbalance or 0.0,
            "bid_depth": bd,
            "ask_depth": ad,
            "levels": float(len(self.bids) + len(self.asks)),
        }


class LOBFeed:
    """Feed protocol: async iterator of LOBSnapshot (None = exhausted)."""

    async def next(self) -> Optional[LOBSnapshot]:
        raise NotImplementedError


class LOBFileFeed(LOBFeed):
    """Replays recorded LOB snapshots from disk.

    JSONL format (one per line):
        {"symbol": "EURUSD", "timestamp": 123.4,
         "bids": [[px, sz], ...], "asks": [[px, sz], ...]}
    CSV format (header row): symbol,timestamp,side,price,size,level
    """

    def __init__(self, path: Path):
        self.path = Path(path)
        if not self.path.exists():
            raise FileNotFoundError(f"LOB data file not found: {self.path}")
        self._snaps = self._load()
        self._idx = 0

    def _load(self) -> List[LOBSnapshot]:
        if self.path.suffix == ".jsonl":
            snaps = [
                LOBSnapshot(
                    symbol=r["symbol"], timestamp=float(r["timestamp"]),
                    bids=[tuple(map(float, l)) for l in r.get("bids", [])],
                    asks=[tuple(map(float, l)) for l in r.get("asks", [])],
                )
                for line in self.path.read_text().splitlines()
                if line.strip() and (r := json.loads(line))
            ]
        elif self.path.suffix == ".csv":
            by_ts: Dict[float, LOBSnapshot] = {}
            with self.path.open(newline="") as fh:
                for row in csv.DictReader(fh):
                    ts = float(row["timestamp"])
                    s = by_ts.setdefault(ts, LOBSnapshot(row["symbol"], ts))
                    side = row["side"].lower()
                    (s.bids if side == "bid" else s.asks).append(
                        (float(row["price"]), float(row["size"])))
            snaps = [by_ts[k] for k in sorted(by_ts)]
        else:
            raise ValueError(f"Unsupported LOB file format: {self.path.suffix}")
        for s in snaps:
            s.bids.sort(key=lambda l: -l[0])
            s.asks.sort(key=lambda l: l[0])
        return snaps

    async def next(self) -> Optional[LOBSnapshot]:
        if self._idx >= len(self._snaps):
            return None
        s = self._snaps[self._idx]
        self._idx += 1
        return s

    def __len__(self) -> int:
        return len(self._snaps)


class BrokerLOBFeed(LOBFeed):
    """Polls a live BrokerInterface.get_order_book() into snapshots.

    Works against testnet credentials — this is the connectivity plumbing;
    it never fabricates a book.
    """

    def __init__(self, broker: Any, symbol: str, depth: int = 20,
                 last_update_ts: float = 0.0):
        if broker is None or not hasattr(broker, "get_order_book"):
            raise ValueError("BrokerLOBFeed requires a broker with get_order_book()")
        self.broker = broker
        self.symbol = symbol
        self.depth = depth

    async def next(self) -> Optional[LOBSnapshot]:
        book = await self.broker.get_order_book(self.symbol, limit=self.depth)
        if not book:
            return None
        bids = book.get("bids") or []
        asks = book.get("asks") or []
        ts = float(book.get("lastUpdateId") or book.get("timestamp") or 0.0)
        return LOBSnapshot(
            symbol=self.symbol,
            timestamp=ts,
            bids=[(float(p), float(s)) for p, s in bids],
            asks=[(float(p), float(s)) for p, s in asks],
        )
