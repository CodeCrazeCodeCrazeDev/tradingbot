"""Capability-gated institutional activity detection.

Detects order-flow and microstructure patterns *only where the supplied
data supports the claim*. Data-quality tiers:

- ``prints``: individual trade records with (price, size, ts, aggressor).
  Required for block-trade detection and true volume delta.
- ``book``: L2 market-by-price snapshots [(level, price, size) ...].
  Required for iceberg/spoofing/layering indicators.
- ``bars``: OHLCV + tick volume (MT5 default). Supports only labelled
  *inference* proxies — never claims true aggressor-side delta or
  hidden liquidity.
- ``quote``: L1 bid/ask (+sizes). Supports spread/quote-size dynamics.

Every emitted signal carries: symbol, venue, event_ts, availability_ts,
source, data_quality, evidence, uncertainty, expiry_s, detector_version.
Detectors whose prerequisites are absent report ``unavailable`` —
never fabricated detection.

OHLCV alone cannot establish spoofing, iceberg replenishment, or true
aggressor volume; MT5 tick volume is broker-local, not consolidated
institutional flow.
"""

from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass, field
from typing import Any, Deque, Dict, List, Optional, Tuple

import numpy as np

DETECTOR_VERSION = "order_flow/1.0.0"

_REQUIRED_FIELDS = ("symbol", "venue", "event_ts", "availability_ts",
                    "source", "data_quality", "evidence", "uncertainty",
                    "expiry_s", "detector_version")


def _finite(v: Any) -> bool:
    try:
        return bool(np.isfinite(float(v)))
    except (TypeError, ValueError):
        return False


def _signal(symbol: str, venue: str, kind: str, direction: Optional[str],
            strength: float, evidence: Dict[str, Any], source: str,
            event_ts: float, quality: str, uncertainty: float,
            expiry_s: float = 900.0) -> Dict[str, Any]:
    """Emit a fully-provenanced advisory signal (never authority)."""
    now = time.time()
    return {
        "kind": kind,
        "direction": direction,          # buy / sell / neutral / None
        "strength": float(np.clip(strength, 0.0, 1.0)),
        "symbol": symbol,
        "venue": venue,
        "event_ts": float(event_ts),
        "availability_ts": now,
        "source": source,
        "data_quality": quality,
        "evidence": dict(evidence),
        "uncertainty": float(np.clip(uncertainty, 0.0, 1.0)),
        "expiry_s": float(expiry_s),
        "detector_version": DETECTOR_VERSION,
        "advisory_only": True,
    }


@dataclass
class _SymState:
    closes: Deque[float] = field(default_factory=lambda: deque(maxlen=256))
    volumes: Deque[float] = field(default_factory=lambda: deque(maxlen=256))
    ranges: Deque[float] = field(default_factory=lambda: deque(maxlen=256))
    prints: Deque[Dict[str, Any]] = field(
        default_factory=lambda: deque(maxlen=2048))
    books: Deque[Tuple[float, Tuple, Tuple]] = field(
        default_factory=lambda: deque(maxlen=120))
    bar_ts: Deque[float] = field(default_factory=lambda: deque(maxlen=256))


class OrderFlowService:
    """Institutional-activity advisory service.

    Capability-gated: detectors activate only when the observation
    supplies their data tier. Symbols are isolated; all rolling state
    bounded; non-finite inputs rejected at intake.
    """

    MAX_SYMBOLS = 64
    DEFAULT_BLOCK_NOTIONAL_USD = 100_000.0

    def __init__(self, block_notional_usd: float = DEFAULT_BLOCK_NOTIONAL_USD,
                 vol_z_absorb: float = 2.0, range_pct_absorb: float = 0.35,
                 exhaustion_lookback: int = 4) -> None:
        self.block_notional_usd = float(block_notional_usd)
        self.vol_z_absorb = float(vol_z_absorb)
        self.range_pct_absorb = float(range_pct_absorb)
        self.exhaustion_lookback = int(exhaustion_lookback)
        self._sym: Dict[str, _SymState] = {}

    # ---------------------------------------------------------------
    def _state(self, symbol: str) -> _SymState:
        st = self._sym.get(symbol)
        if st is None:
            if len(self._sym) >= self.MAX_SYMBOLS:
                self._sym.pop(next(iter(self._sym)))
            st = self._sym[symbol] = _SymState()
        return st

    def capabilities(self, obs: Dict[str, Any]) -> Dict[str, bool]:
        return {
            "bars": _finite(obs.get("close")) and _finite(obs.get("volume")),
            "quote": _finite(obs.get("bid")) and _finite(obs.get("ask")),
            "book": isinstance(obs.get("book"), (list, tuple))
            and len(obs["book"]) >= 2,
            "prints": isinstance(obs.get("prints"), (list, tuple))
            and len(obs["prints"]) > 0,
        }

    # ---------------------------------------------------------------
    def analyze(self, obs: Dict[str, Any]) -> Dict[str, Any]:
        """Main entry — returns detector results keyed by capability."""
        symbol = str(obs.get("symbol") or "?")
        venue = str(obs.get("venue") or "unknown")
        ts = obs.get("ts") or obs.get("timestamp") or time.time()
        try:
            ts = float(ts)
        except (TypeError, ValueError):
            ts = time.time()
        if not _finite(ts):
            ts = time.time()

        caps = self.capabilities(obs)
        st = self._state(symbol)
        out: Dict[str, Any] = {"symbol": symbol, "capabilities": caps,
                               "signals": [], "unavailable": []}

        # --- ingest -------------------------------------------------
        if caps["prints"]:
            for pr in obs["prints"][-256:]:
                if isinstance(pr, dict) and _finite(pr.get("price")) \
                        and _finite(pr.get("size")):
                    st.prints.append(dict(pr))
        if caps["book"]:
            book = obs["book"]
            try:
                bids = tuple((float(l[0]), float(l[1]))
                             for l in book[0] if _finite(l[0]) and _finite(l[1]))
                asks = tuple((float(l[0]), float(l[1]))
                             for l in book[1] if _finite(l[0]) and _finite(l[1]))
                st.books.append((ts, bids, asks))
            except (TypeError, ValueError, IndexError):
                caps["book"] = False

        close = obs.get("close")
        vol = obs.get("volume")
        high = obs.get("high")
        low = obs.get("low")
        if caps["bars"]:
            st.closes.append(float(close))
            st.volumes.append(float(vol))
            rng = (float(high) - float(low)) if (
                _finite(high) and _finite(low)) else abs(
                float(close) - st.closes[-2]) if len(st.closes) > 1 else 0.0
            st.ranges.append(max(0.0, rng))
            st.bar_ts.append(ts)

        # --- detectors ----------------------------------------------
        if caps["prints"]:
            out["signals"].extend(self._block_trades(st, symbol, venue, ts))
            d = self._volume_delta_prints(st, symbol, venue, ts)
            if d:
                out["signals"].append(d)
            imp = self._market_impact(st, symbol, venue, ts)
            if imp:
                out["signals"].append(imp)
        else:
            out["unavailable"].append({
                "detector": "block_trades",
                "requires": "trade prints with size+price",
                "note": "OHLCV cannot identify individual institutional "
                        "orders"})

        if caps["book"]:
            out["signals"].extend(self._book_indicators(st, symbol, venue, ts))
        else:
            for det, req in (("iceberg", "L2 book snapshots"),
                             ("spoofing", "L2/L3 order events"),
                             ("layering", "L2 book snapshots")):
                out["unavailable"].append({"detector": det,
                                           "requires": req})

        if caps["bars"]:
            for sig in (self._absorption_bars(st, symbol, venue, ts),
                        self._exhaustion(st, symbol, venue, ts),
                        self._volume_delta_inference(st, symbol, venue, ts)):
                if sig:
                    out["signals"].append(sig)
        else:
            out["unavailable"].append(
                {"detector": "bar_proxies",
                 "requires": "finite close+volume bars"})

        return out

    # ---------------------------------------------------------------
    # prints-tier detectors
    # ---------------------------------------------------------------
    def _block_trades(self, st: _SymState, symbol: str, venue: str,
                      ts: float) -> List[Dict[str, Any]]:
        sigs = []
        recent = [p for p in st.prints if ts - float(p.get("ts", ts)) <= 60.0]
        mult = float(recent[-1].get("multiplier", 1.0)) if recent else 1.0
        for p in recent:
            notional = float(p["price"]) * float(p["size"]) * mult
            if notional >= self.block_notional_usd:
                side = p.get("aggressor")
                direction = ("buy" if str(side).lower()
                             in ("buy", "b", "1") else
                             "sell" if str(side).lower()
                             in ("sell", "s", "0") else None)
                sigs.append(_signal(
                    symbol, venue, "block_trade", direction,
                    min(1.0, notional / (self.block_notional_usd * 10)),
                    {"notional_usd": notional, "price": p["price"],
                     "size": p["size"],
                     "aggressor_known": direction is not None},
                    "trade_prints", ts, "prints",
                    0.1 if direction else 0.3, expiry_s=120.0))
        return sigs

    def _volume_delta_prints(self, st: _SymState, symbol: str, venue: str,
                             ts: float) -> Optional[Dict[str, Any]]:
        recent = [p for p in st.prints
                  if ts - float(p.get("ts", ts)) <= 300.0]
        if len(recent) < 10:
            return None
        buy = sum(float(p["size"]) for p in recent
                  if str(p.get("aggressor", "")).lower() in ("buy", "b", "1"))
        sell = sum(float(p["size"]) for p in recent
                   if str(p.get("aggressor", "")).lower()
                   in ("sell", "s", "0"))
        tot = buy + sell
        if tot <= 0:
            return None
        delta = (buy - sell) / tot
        if abs(delta) < 0.2:
            return None
        return _signal(symbol, venue, "volume_delta",
                       "buy" if delta > 0 else "sell",
                       min(1.0, abs(delta)),
                       {"delta": delta, "buy_vol": buy, "sell_vol": sell,
                        "n_prints": len(recent),
                        "inference": False},
                       "trade_prints", ts, "prints",
                       uncertainty=0.15, expiry_s=300.0)

    def _market_impact(self, st: _SymState, symbol: str, venue: str,
                       ts: float) -> Optional[Dict[str, Any]]:
        big = [p for p in st.prints
               if float(p.get("price", 0)) * float(p.get("size", 0))
               >= self.block_notional_usd]
        if len(big) < 2 or len(st.closes) < 10:
            return None
        closes = np.asarray(st.closes)
        ret = np.diff(closes)
        sd = float(np.std(ret))
        if not np.isfinite(sd) or sd <= 0:
            return None
        last_impact = (closes[-1] - closes[-2]) / sd
        return _signal(symbol, venue, "market_impact", None,
                       min(1.0, abs(last_impact) / 3.0),
                       {"impact_in_bar_sd": float(last_impact),
                        "baseline": "bar-return stddev"},
                       "trade_prints", ts, "prints",
                       uncertainty=0.35, expiry_s=300.0)

    # ---------------------------------------------------------------
    # book-tier detectors (L2 market-by-price)
    # ---------------------------------------------------------------
    def _book_indicators(self, st: _SymState, symbol: str, venue: str,
                         ts: float) -> List[Dict[str, Any]]:
        sigs: List[Dict[str, Any]] = []
        books = list(st.books)
        if len(books) < 3:
            return sigs

        # --- iceberg proxy: same price level repeatedly replenished ---
        replenish: Dict[float, int] = {}
        for i in range(1, len(books)):
            prev = {p: s for p, s in books[i - 1][2]}  # asks
            cur = {p: s for p, s in books[i][2]}
            for price, size in cur.items():
                if price in prev and size > prev[price] * 1.5:
                    replenish[price] = replenish.get(price, 0) + 1
        for price, count in replenish.items():
            if count >= 3:
                sigs.append(_signal(
                    symbol, venue, "iceberg_indicator", "sell",
                    min(1.0, count / 10.0),
                    {"price": price, "replenishments": count,
                     "hidden_size_est": "range only",
                     "note": "L2 replenishment — inference, not L3 "
                             "confirmation"},
                    "l2_book", ts, "book", 0.45, expiry_s=300.0))

        # --- spoofing indicator: large level added then cancelled ------
        first, last = books[0], books[-1]
        first_ask = {p: s for p, s in first[2]}
        last_ask = {p: s for p, s in last[2]}
        total_first = sum(first_ask.values()) or 1.0
        for price, size in first_ask.items():
            if size > 0.3 * total_first and price not in last_ask:
                sigs.append(_signal(
                    symbol, venue, "spoofing_indicator", "sell",
                    min(1.0, size / total_first),
                    {"price": price, "size_fraction": size / total_first,
                     "note": "suspicious placement+cancel pattern — "
                             "not proof of manipulation intent"},
                    "l2_book", ts, "book", 0.5, expiry_s=180.0))

        # --- imbalance --------------------------------------------------
        bids = {p: s for p, s in last[1]}
        asks = {p: s for p, s in last[2]}
        b, a = sum(bids.values()), sum(asks.values())
        if b + a > 0:
            imb = (b - a) / (b + a)
            if abs(imb) >= 0.25:
                sigs.append(_signal(
                    symbol, venue, "book_imbalance",
                    "buy" if imb > 0 else "sell",
                    min(1.0, abs(imb)),
                    {"imbalance": imb, "bid_depth": b, "ask_depth": a},
                    "l2_book", ts, "book", 0.25, expiry_s=120.0))
        return sigs

    # ---------------------------------------------------------------
    # bar-tier proxies — explicitly labelled inference
    # ---------------------------------------------------------------
    def _absorption_bars(self, st: _SymState, symbol: str, venue: str,
                         ts: float) -> Optional[Dict[str, Any]]:
        vols = np.asarray(st.volumes)
        rngs = np.asarray(st.ranges)
        if len(vols) < 20 or len(rngs) < 20:
            return None
        vz = (vols[-1] - vols[:-1].mean()) / (vols[:-1].std() + 1e-12)
        r_pct = float((rngs[:-1] > rngs[-1]).mean())  # fraction of bars larger
        if vz >= self.vol_z_absorb and r_pct >= 1.0 - self.range_pct_absorb:
            closes = np.asarray(st.closes)
            direction = "buy" if closes[-1] >= closes[-2] else "sell"
            return _signal(
                symbol, venue, "absorption_proxy", direction,
                min(1.0, vz / 5.0),
                {"vol_z": float(vz), "range_pctile": r_pct,
                 "inference": "tick_volume_high_range_small",
                 "note": "bar-level proxy — true absorption needs "
                         "prints/book"},
                "bars_tickvol", ts, "bars", 0.5, expiry_s=600.0)
        return None

    def _exhaustion(self, st: _SymState, symbol: str, venue: str,
                    ts: float) -> Optional[Dict[str, Any]]:
        k = self.exhaustion_lookback
        vols = np.asarray(st.volumes)
        closes = np.asarray(st.closes)
        if len(vols) < k + 2 or len(closes) < k + 2:
            return None
        decl = all(vols[-i - 1] < vols[-i] for i in range(1, k))
        move = closes[-1] - closes[-k - 1]
        same_dir = all(np.sign(closes[-i] - closes[-i - 1])
                       == np.sign(move) for i in range(1, k))
        if decl and same_dir and abs(move) > 0:
            return _signal(
                symbol, venue, "exhaustion_indicator",
                "sell" if move > 0 else "buy",
                0.5,
                {"declining_volume_bars": k,
                 "move_dir": int(np.sign(move)),
                 "note": "waning participation — reversal warning, "
                         "not certainty"},
                "bars_tickvol", ts, "bars", 0.5, expiry_s=600.0)
        return None

    def _volume_delta_inference(self, st: _SymState, symbol: str,
                                venue: str, ts: float
                                ) -> Optional[Dict[str, Any]]:
        """Bar-level delta inference: volume weighted by close position
        within bar range. Explicitly labelled inference — NOT true
        aggressor-side delta."""
        vols = np.asarray(st.volumes)
        rngs = np.asarray(st.ranges)
        closes = np.asarray(st.closes)
        if len(vols) < 5 or len(closes) < 2:
            return None
        n = min(5, len(vols))
        rng_safe = np.where(rngs[-n:] > 0, rngs[-n:], np.nan)
        prev = np.concatenate([[closes[-n] - (rngs[-n] if len(rngs) >= n else 0)],
                               closes[-n:-1]])
        pos = (closes[-n:] - prev) / rng_safe
        pos = np.where(np.isfinite(pos), pos, 0.0)
        signed = float((pos * vols[-n:]).sum())
        tot = float(vols[-n:].sum()) or 1.0
        delta = signed / tot
        if abs(delta) < 0.15:
            return None
        return _signal(
            symbol, venue, "volume_delta_proxy",
            "buy" if delta > 0 else "sell",
            min(1.0, abs(delta) * 1.5),
            {"delta_proxy": delta, "bars": n,
             "inference": "close_position_in_range * volume",
             "note": "bar-level estimate — not exchange aggressor "
                     "flags"},
            "bars_tickvol", ts, "bars", 0.45, expiry_s=600.0)


__all__ = ["OrderFlowService", "DETECTOR_VERSION"]
