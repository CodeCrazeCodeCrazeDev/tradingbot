#!/usr/bin/env python
"""Canonical offline paper-trading runner.

Drives ``ModularMonolithRuntime`` (paper mode only — never a broker) over a
synthetic or read-only market_data.db feed. Between every cycle it drains the
operator control channel so a separate ``operator_cli.py`` process can pause,
resume, flatten, cancel-all or emergency-stop the live bot. A JSON snapshot
is published each cycle for the read-only dashboard; ``--dashboard-port``
serves it over localhost GET-only (no mutation surface exists on that server).

Usage:
    python scripts/paper_runner.py --source synthetic --cycles 200
    python scripts/paper_runner.py --source db --symbol EURUSD --interval 0.5
"""

from __future__ import annotations

import argparse
import asyncio
import dataclasses
import json
import logging
import os
import sqlite3
import sys
import time
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Tuple

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

logger = logging.getLogger("paper_runner")

DEFAULT_STATE_DIR = PROJECT_ROOT / "var" / "paper"

def stop_requested(args: argparse.Namespace) -> bool:
    path = getattr(args, "stop_file", "")
    return bool(path and Path(path).exists())


def prior_seed_rows(db_path: Path, symbol: str, timeframe: str,
                    skip: int, seed_bars: int) -> list:
    """Only the rows strictly before the selected replay window.

    Columns: close,high,low,open,volume,timestamp — the first three are
    what callers index; the extras let the rv forecaster warm its own
    32-bar window from the same strictly-prior data."""
    with sqlite3.connect(Path(db_path).resolve().as_uri() + "?mode=ro", uri=True) as con:
        return con.execute(
            "SELECT close,high,low,open,volume,timestamp FROM market_data "
            "WHERE symbol=? AND timeframe=? "
            "ORDER BY timestamp LIMIT ? OFFSET ?",
            (symbol, timeframe, max(0, min(seed_bars, skip)),
             max(0, skip - seed_bars))).fetchall()


def _load_htf_bars(db_path: Path, symbol: str, timeframe: str
                   ) -> List[Tuple[str, float]]:
    rows = _load_htf_bars_raw(db_path, symbol, timeframe)
    if not rows:
        logger.warning(
            "htf_timeframe=%s returned 0 rows for %s — htf_* features "
            "will be ABSENT, not stale (GBPUSD has no H4, e.g.)",
            timeframe, symbol)
    return rows


def _load_htf_bars_raw(db_path: Path, symbol: str, timeframe: str
                   ) -> List[Tuple[str, float]]:
    """All (timestamp, close) rows for a second timeframe — loaded once so
    the M15 replay can attach point-in-time higher-timeframe context."""
    con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        return con.execute(
            "SELECT timestamp, close FROM market_data "
            "WHERE symbol=? AND timeframe=? ORDER BY timestamp ASC",
            (symbol, timeframe)).fetchall()
    finally:
        con.close()


def db_observations(db_path: Path, symbol: str, timeframe: str,
                    skip: int = 0, htf_timeframe: str = "",
                    broker_tz_offset: float = 0.0,
                    tail: int = 0, start_ts: str = ""
                    ) -> Iterator[Dict[str, Any]]:
    """Replay market_data.db rows read-only as raw observations.

    timeframe must be filtered — the table holds M15+H1 rows for the same
    symbol; sorting all of them by timestamp interleaves cadences and
    silently corrupts return/volatility features at every seam.
    ``skip`` drops the first N matching bars so parallel runs can cover
    disjoint historical windows.

    ``htf_timeframe`` (e.g. "H1") attaches point-in-time higher-timeframe
    context to each obs: htf_close, htf_rsi14, htf_trend (return over the
    last 10 completed higher-TF bars). Only bars CLOSED at or before the
    current timestamp are used — no lookahead.
    """
    htf = _load_htf_bars(db_path, symbol, htf_timeframe) \
        if htf_timeframe else []
    htf_idx = 0          # next htf bar not yet released
    htf_closes: List[float] = []  # released closes, in order
    # Timestamps are bar OPEN times (verified: H1@23:00 close ==
    # M15@23:45 close). An HTF bar is only safe to read after it
    # closes: release when m15_ts >= htf_ts + htf_seconds. The old
    # '<=' released the still-forming bar — a 45-minute lookahead
    # into every htf_* feature.
    _HTF_SEC = {"M5": 300, "M15": 900, "M30": 1800, "H1": 3600,
                "H4": 14400, "D1": 86400}
    htf_sec = _HTF_SEC.get(htf_timeframe.upper(), 3600)         if htf_timeframe else 0

    def _ts_sec(t: str) -> float:
        from datetime import datetime
        return datetime.fromisoformat(
            t.replace("Z", "+00:00")).timestamp()
    htf_tss = [_ts_sec(r[0]) for r in htf]

    con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        if tail > 0:
            # Last-N window: DESC LIMIT reversed — used by --universe
            # auto so each selected series replays a bounded recent
            # window rather than its full history.
            _q = ("SELECT timestamp, open, high, low, close, volume FROM "
                  "(SELECT timestamp, open, high, low, close, volume FROM "
                  "market_data WHERE symbol=? AND timeframe=? "
                  "ORDER BY timestamp DESC LIMIT ?) "
                  "ORDER BY timestamp ASC")
            _params = (symbol, timeframe, tail)
        elif start_ts:
            # Resume a series strictly after the tape clock — rotating
            # universe entries join mid-replay without re-reading bars
            # the tape already covered.
            _q = ("SELECT timestamp, open, high, low, close, volume "
                  "FROM market_data WHERE symbol=? AND timeframe=? "
                  "AND timestamp > ? ORDER BY timestamp ASC")
            _params = (symbol, timeframe, start_ts)
        else:
            _q = ("SELECT timestamp, open, high, low, close, volume "
                  "FROM market_data WHERE symbol=? AND timeframe=? "
                  "ORDER BY timestamp ASC")
            _params = (symbol, timeframe)
        for ts, o, h, l, c, v in con.execute(_q, _params):
            if skip > 0:
                skip -= 1
                continue
            _ts = ts
            if broker_tz_offset:
                # De-offset broker server time to UTC: the volume-by-
                # hour signature proves an EET-style clock (trough at
                # 0:00 == NY close). DST drift (~+-1h, twice yearly)
                # is NOT corrected — a fixed offset is honest about
                # what it can't know.
                from datetime import datetime as _dd, timedelta as _td
                _ts = (_dd.fromisoformat(ts.replace("Z", "+00:00"))
                       - _td(hours=broker_tz_offset)).isoformat()
            obs = {"symbol": symbol, "timestamp": _ts, "open": o, "high": h,
                   "low": l, "close": c, "volume": v, "price": c,
                   # MT5/broker FX 'volume' is tick count, not traded
                   # volume — advisors must not calibrate on it as
                   # real size.
                   "volume_kind": "tick", "timeframe": timeframe,
                   # Source timestamps are broker server time
                   # (EET-style), NOT UTC. When broker_tz_offset is
                   # set, `timestamp` is UTC-shifted and
                   # `broker_timestamp` retains the raw value.
                   "ts_is_broker_time": True,
                   "broker_timestamp": ts}
            while (htf_idx < len(htf)
                   and htf_tss[htf_idx] + htf_sec <= _ts_sec(ts)):
                htf_closes.append(htf[htf_idx][1])
                htf_idx += 1
            if htf_closes:
                obs["htf_close"] = htf_closes[-1]
                obs["htf_bars"] = len(htf_closes)
                if len(htf_closes) > 10:
                    obs["htf_trend"] = (
                        (htf_closes[-1] - htf_closes[-11])
                        / htf_closes[-11])
                if len(htf_closes) > 14:
                    ds = [htf_closes[i] - htf_closes[i - 1]
                          for i in range(len(htf_closes) - 14,
                                         len(htf_closes))]
                    gains = sum(d for d in ds if d > 0)
                    losses = -sum(d for d in ds if d < 0)
                    obs["htf_rsi14"] = (
                        100.0 - 100.0 / (1.0 + gains / losses)
                        if losses > 0 else 100.0)
            yield obs
    finally:
        con.close()


def hl_seed_rows(coin: str, hl_tf: str, n: int) -> tuple:
    """Closed Hyperliquid candles as (close, high, low) tuples plus the
    open-time boundary (ms) of the newest seeded bar — the same honest
    warmup path prior_seed_rows provides (strictly-prior closes only).
    The boundary is what a live follow must start strictly after."""
    from scripts.hyperliquid_sync import fetch_candles, _TF_MS
    now = int(time.time() * 1000)
    candles = fetch_candles(
        coin, hl_tf, now - (n + 4) * _TF_MS[hl_tf], now) or []
    closed = [c for c in candles if int(c["T"]) <= now][-n:]
    rows = [(float(c["c"]), float(c["h"]), float(c["l"]))
            for c in closed]
    last_open = max((int(c["t"]) for c in closed), default=0)
    return rows, last_open


def _bar_features(closes) -> Dict[str, Any]:
    """Measured per-bar features from a rolling close window.

    Returns volatility (stdev of log returns), ret_autocorr (lag-1),
    rsi (Wilder-14 approx), momentum (5-bar ROC), and a trend label —
    all computed from real bars; empty dict until the window has
    enough data rather than fabricated values.
    """
    import math
    from statistics import fmean, pstdev
    cs = list(closes)
    if len(cs) < 21:
        return {}
    rets = [math.log(cs[i] / cs[i - 1]) for i in range(1, len(cs))
            if cs[i - 1] > 0]
    f: Dict[str, Any] = {}
    w = rets[-20:]
    if len(w) >= 2:
        f["volatility"] = pstdev(w)
    r = rets[-30:]
    if len(r) >= 10:
        m = fmean(r)
        den = sum((x - m) ** 2 for x in r)
        if den > 0:
            f["ret_autocorr"] = sum(
                (r[i] - m) * (r[i - 1] - m)
                for i in range(1, len(r))) / den
    if len(rets) >= 14:
        ag = fmean([max(x, 0.0) for x in rets[-14:]])
        al = fmean([max(-x, 0.0) for x in rets[-14:]])
        f["rsi"] = 100.0 if al == 0 else 100.0 - 100.0 / (1.0 + ag / al)
    if len(cs) >= 6 and cs[-6] > 0:
        f["momentum"] = (cs[-1] - cs[-6]) / cs[-6]
    sma = fmean(cs[-20:])
    f["trend"] = ("up" if cs[-1] > sma * 1.0005 else
                  "down" if cs[-1] < sma * 0.9995 else "flat")
    return f


def order_book_time_label(source: str) -> str:
    """Point-in-time tag for an L2 book merged onto an observation.
    Only hl_live fetches the book at bar-detection time; on replay the
    merged book is current state over a historical bar — anachronistic
    evidence that must never enter simulation drift."""
    return "live" if source == "hl_live" else "anachronistic"


def hl_live_observations(coin: str, symbol: str, hl_tf: str = "15m",
                         timeframe_label: str = "M15",
                         poll_s: float = 15.0,
                         start_after_open: int = 0
                         ) -> Iterator[Dict[str, Any]]:
    """Follow Hyperliquid live: yield one obs per newly CLOSED candle.

    Each emitted bar gets the L2 book fetched at detection time —
    point-in-time-valid order flow, unlike --hl-l2 on a replay which
    attaches the current book to historical bars (anachronistic).
    HL perp volume is real traded volume on a centralized venue, not
    a broker tick count: volume_kind="real" preserves that distinction.
    Polls every poll_s seconds; a failed poll logs and retries.
    ``start_after_open`` (ms open-time boundary from hl_seed_rows) skips
    every candle the seeded warmup already covered, so warmup never
    contains bars later than the first processed observation.
    """
    from datetime import datetime as _dt, timezone as _tz
    from collections import deque
    from scripts.hyperliquid_sync import fetch_candles, _TF_MS
    from trading_bot.feeds import hl_l2
    tf_ms = _TF_MS[hl_tf]
    last_open = int(start_after_open)
    # Rolling close window for MEASURED features (volatility/rsi/
    # momentum/ret_autocorr/trend). Primed from already-closed bars
    # before the live boundary so the first emitted obs is fully
    # featured — all values are computed from real candles, never
    # assumed. Without these keys the MarketStructureVerifier
    # falsifies 100% of directional branches (no structure evidence).
    closes: "deque[float]" = deque(maxlen=96)
    try:
        primed = fetch_candles(coin, hl_tf,
                               max(0, last_open - 120 * tf_ms) or
                               int(time.time() * 1000) - 120 * tf_ms,
                               int(time.time() * 1000))
        for c in primed or []:
            if int(c["t"]) <= last_open and int(c["T"]) <= int(
                    time.time() * 1000):
                closes.append(float(c["c"]))
    except Exception as exc:  # noqa: BLE001
        logger.warning("hl_live feature prime failed: %s", exc)
    while True:
        now = int(time.time() * 1000)
        try:
            candles = fetch_candles(coin, hl_tf, now - 4 * tf_ms, now)
        except Exception as exc:  # noqa: BLE001
            logger.warning("hl_live candle poll failed: %s", exc)
            candles = []
        emitted = False
        for c in candles or []:
            t_open = int(c["t"])
            t_close = int(c["T"])
            if t_open <= last_open or t_close > now:
                continue  # already seen, or still forming
            obs = {"symbol": symbol,
                   "timestamp": _dt.fromtimestamp(
                       t_open / 1000, tz=_tz.utc).isoformat(),
                   "open": float(c["o"]), "high": float(c["h"]),
                   "low": float(c["l"]), "close": float(c["c"]),
                   "volume": float(c["v"]), "price": float(c["c"]),
                   "timeframe": timeframe_label,
                   "volume_kind": "real",
                   "data_source": "hyperliquid_live",
                   "ts_is_broker_time": False}
            closes.append(float(c["c"]))
            obs.update(_bar_features(closes))
            try:
                obs.update(hl_l2.snapshot(coin))
                obs["order_book_time"] = "live"
            except Exception:  # noqa: BLE001 — book absent, not faked
                pass
            last_open = t_open
            emitted = True
            yield obs
        if not emitted:
            time.sleep(poll_s)


def _detect_broker_tz_offset(db_path: Path, symbol: str,
                             timeframe: str = "M15") -> float:
    """Detect broker-server-tz -> UTC offset from the liquidity
    signature: FX tick volume troughs at NY close (~22:00 UTC).
    Trough at hour H means server clock = UTC + (H-22 mod 24).
    Returns 0.0 on insufficient data (caller treats 0 as UTC).
    """
    from collections import defaultdict
    con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        v = defaultdict(float); c = defaultdict(int)
        for ts, vol in con.execute(
                "SELECT timestamp, volume FROM market_data "
                "WHERE symbol=? AND timeframe=? LIMIT 50000",
                (symbol, timeframe)):
            h = int(str(ts)[11:13])
            v[h] += float(vol or 0); c[h] += 1
        if not v:
            return 0.0
        avg = {h: v[h] / max(c[h], 1) for h in v}
        trough = min(avg, key=avg.get)
        off = (trough - 22) % 24
        # plausible offsets: -2..+12; a trough at 22:xx means already UTC
        if off > 12:
            off = 0.0
        logger.info(
            "broker tz detected: volume trough at %02d:00 server "
            "-> UTC offset +%.0fh", trough, off)
        return float(off)
    finally:
        con.close()


def cross_observations(db_path: Path, num_symbol: str, den_symbol: str,
                       timeframe: str, skip: int = 0
                       ) -> Iterator[Dict[str, Any]]:
    """Derived cross rate: close = num/den on joined timestamps.

    EURGBP = EURUSD/GBPUSD is real market data — the canonical cross
    is defined this way — computed from bars we already have. Breaks
    the USD-leg correlation every eval pair shares. Only bars that
    exist in BOTH series are emitted (no forward-fill fabrication).
    """
    con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        num = {ts: (o, h, l, c, v) for ts, o, h, l, c, v in con.execute(
            "SELECT timestamp, open, high, low, close, volume "
            "FROM market_data WHERE symbol=? AND timeframe=? "
            "ORDER BY timestamp", (num_symbol, timeframe))}
        den = {ts: (o, h, l, c, v) for ts, o, h, l, c, v in con.execute(
            "SELECT timestamp, open, high, low, close, volume "
            "FROM market_data WHERE symbol=? AND timeframe=? "
            "ORDER BY timestamp", (den_symbol, timeframe))}
        n = 0
        for ts in sorted(num):
            if ts not in den:
                continue
            if skip > 0:
                skip -= 1
                continue
            n += 1
            no, nh, nl, nc, nv = num[ts]
            do, dh, dl, dc, dv = den[ts]
            yield {"symbol": f"{num_symbol[:3]}{den_symbol[:3]}",
                   "timestamp": ts,
                   "open": no / do, "high": nh / dl,
                   "low": nl / dh, "close": nc / dc,
                   "volume": min(nv, dv), "price": nc / dc,
                   "volume_kind": "tick", "timeframe": timeframe,
                   "ts_is_broker_time": True,
                   "cross_derived": True}
        logger.info("cross %s/%s: %d joined bars",
                    num_symbol, den_symbol, n)
    finally:
        con.close()


def parse_universe(spec: str) -> List[Tuple[str, str, str, int]]:
    """Parse --universe 'db:sym1,sym2:tf:skip;db2:sym3:tf2:skip2' into
    (db_path, symbol, timeframe, skip) rows. The 4th field is optional
    (default 0) — per-source skip exists because each store's history
    depth differs and a single global --skip cannot align their
    replay windows."""
    rows: List[Tuple[str, str, str, int]] = []
    for chunk in str(spec or "").split(";"):
        chunk = chunk.strip()
        if not chunk:
            continue
        parts = chunk.split(":")
        if len(parts) < 3:
            raise SystemExit(
                f"--universe: bad spec chunk {chunk!r} "
                "(want db:sym1,sym2:tf[:skip])")
        db, syms, tf = parts[0], parts[1], parts[2]
        skip = int(parts[3]) if len(parts) > 3 else 0
        for s in syms.split(","):
            s = s.strip().upper()
            if s:
                rows.append((db, s, tf, skip))
    if not rows:
        raise SystemExit("--universe: empty spec")
    return rows


def _load_data_catalog(max_age_s: float = 86400.0):
    """var/data_catalog.json fast path — the scanner consumes the same
    shape DataResourceInventory.scan() produces, so a fresh catalog
    file skips re-probing every DB. Returns None if missing/stale —
    live scan remains the fallback."""
    import json as _json
    p = Path("var/data_catalog.json")
    try:
        cat = _json.loads(p.read_text())
        if time.time() - float(cat.get("generated_at", 0)) > max_age_s:
            logger.info("data catalog stale (>%.0fh) — live probing",
                        max_age_s / 3600)
            return None
        return cat
    except Exception:  # noqa: BLE001
        return None


def auto_universe(top: int = 6, tail: int = 4000
                  ) -> List[Tuple[str, str, str, int]]:
    """Autonomous instrument selection: probe every onboarded
    market_data store, rank each series by measured structure
    (autocorrelation + sign-persistence distance from a coin-flip
    walk), dedupe by symbol and return the top `top` picks as
    (db, symbol, timeframe, tail) rows for merged replay.

    The ranking is real and logged — but it is a prioritization hint,
    not evidence of tradeable edge (the scanner itself says so)."""
    from trading_bot.expansion.inventory import DataResourceInventory
    from trading_bot.expansion.scanner import OpportunityScanner
    inv = DataResourceInventory(PROJECT_ROOT)
    catalog = _load_data_catalog()
    scan = (OpportunityScanner(inv).scan_all(catalog=catalog)
            if catalog else OpportunityScanner(inv).scan_all())
    opps = scan.get("opportunities") or []
    seen: set = set()
    picks: List[Tuple[str, str, str, int]] = []
    for rec in opps:
        sym = rec["symbol"]
        if sym in seen:
            continue  # one series per symbol — best-scored wins
        seen.add(sym)
        picks.append((rec["source"], sym, rec["timeframe"], tail))
        if len(picks) >= top:
            break
    logger.info(
        "auto universe: %d series scanned, %d ranked with "
        "structure>=0.3; selected=%s",
        scan.get("series_scanned", 0), len(opps),
        [(f"{s}@{t}", round(next(
            r["structure_score"] for r in opps if r["symbol"] == s), 3))
         for _, s, t, _ in picks])
    if not picks:
        raise SystemExit(
            "--universe auto: no series passed the structure gate")
    return picks


def _closes_for_rank(db_path: Path, symbol: str, timeframe: str,
                     until_ts: str, limit: int) -> List[float]:
    """Closes strictly at/before `until_ts` (or the first `limit` bars
    when until is empty — the pre-tape research window)."""
    con = sqlite3.connect(
        f"file:{db_path.resolve()}?mode=ro", uri=True)
    try:
        if until_ts:
            rows = con.execute(
                "SELECT close FROM (SELECT close, timestamp FROM "
                "market_data WHERE symbol=? AND timeframe=? AND "
                "timestamp<=? ORDER BY timestamp DESC LIMIT ?) "
                "ORDER BY timestamp",
                (symbol, timeframe, until_ts, limit)).fetchall()
        else:
            rows = con.execute(
                "SELECT close FROM market_data WHERE symbol=? AND "
                "timeframe=? ORDER BY timestamp ASC LIMIT ?",
                (symbol, timeframe, limit)).fetchall()
        return [float(r[0]) for r in rows
                if r[0] is not None and float(r[0]) > 0]
    finally:
        con.close()


def rotating_universe_observations(
        args: Any, btz_for: Any,
        top: int = 6, rank_window: int = 1000,
        lookback: int = 500, refresh_every: int = 500
        ) -> Iterator[Dict[str, Any]]:
    """Point-in-time rotating universe.

    The watchlist is re-ranked every `refresh_every` emitted bars using
    closes strictly BEFORE the tape clock — no lookahead, so a rotation
    decision at replay-time T only uses data that existed at T. On
    static stores the ranking still moves because the lookback window
    slides through regime changes. Symbols that rotate out stop
    emitting; new entries join at the current clock (start_ts), never
    replaying covered history.
    """
    import heapq
    from trading_bot.expansion.inventory import DataResourceInventory
    from trading_bot.expansion.scanner import series_stats

    catalog = (_load_data_catalog()
               or DataResourceInventory(PROJECT_ROOT).scan())
    series = [(src, e["symbol"], e["timeframe"])
              for src, s in catalog["sources"].items()
              for e in s.get("series", ())]

    def _tail_start(db: str, sym: str, tf: str) -> str:
        con = sqlite3.connect(
            f"file:{(PROJECT_ROOT / db).resolve()}?mode=ro", uri=True)
        try:
            r = con.execute(
                "SELECT MIN(timestamp) FROM (SELECT timestamp FROM "
                "market_data WHERE symbol=? AND timeframe=? "
                "ORDER BY timestamp DESC LIMIT ?)",
                (sym, tf, args.universe_tail)).fetchone()
            return str(r[0]) if r and r[0] else ""
        finally:
            con.close()

    def _rank(as_of: str, gate: float = 0.3
              ) -> "List[Tuple[float, str, str, str]]":
        scored = []
        for db, sym, tf in series:
            try:
                # Tape start (""): rank on history strictly BEFORE each
                # series' own replay window — zero lookahead. Later
                # re-ranks use `lookback` closes ending at the clock.
                until = as_of or _tail_start(db, sym, tf)
                st = series_stats(_closes_for_rank(
                    PROJECT_ROOT / db, sym, tf, until,
                    as_of and lookback or rank_window))
            except Exception:  # noqa: BLE001 — one bad series mustn't stall the tape
                continue
            if st and st.get("structure_score", 0) >= gate:
                scored.append(
                    (st["structure_score"], db, sym, tf))
        scored.sort(key=lambda r: r[0], reverse=True)
        return scored[:top]

    clock = ""
    active: Dict[Tuple[str, str, str], Iterator[Dict[str, Any]]] = {}
    first = True
    while True:
        ranked = _rank(clock)
        relaxed = False
        if not ranked:
            # Nothing met the scanner's 0.3 structure floor — take the
            # best available below it, and say so rather than silently
            # feeding an unqualified tape (or no tape at all).
            ranked = _rank(clock, gate=0.0)
            relaxed = bool(ranked)
        want = {(db, sym, tf): sc for sc, db, sym, tf in ranked}
        dropped = [k for k in active if k not in want]
        for k in dropped:
            active.pop(k, None)
        for (db, sym, tf) in want:
            key = (db, sym, tf)
            if key in active:
                continue
            if first:
                # Initial watchlist replays each series' last
                # --universe-tail bars; ranking used only earlier data.
                active[key] = db_observations(
                    PROJECT_ROOT / db, sym, tf, 0,
                    args.htf_timeframe,
                    broker_tz_offset=btz_for(db),
                    tail=args.universe_tail)
            else:
                active[key] = db_observations(
                    PROJECT_ROOT / db, sym, tf, 0,
                    args.htf_timeframe,
                    broker_tz_offset=btz_for(db),
                    start_ts=clock)
        logger.info(
            "universe re-rank @%s: watchlist=%s dropped=%s%s",
            clock or "<tape start>",
            [(f"{s}@{t}", round(sc, 3))
             for sc, _, s, t in ranked],
            [f"{s}@{t}" for _, s, t in dropped],
            " (below 0.3 structure floor)" if relaxed else "")
        if not active:
            break
        merged = heapq.merge(
            *active.values(),
            key=lambda o: str(o.get("timestamp") or ""))
        emitted = 0
        for obs in merged:
            clock = str(obs.get("timestamp") or clock)
            yield obs
            emitted += 1
            if emitted >= refresh_every:
                break
        if emitted == 0:
            break  # nothing left after the tape clock in any active series
        first = False


def merged_symbol_observations(
        sources: Dict[str, Iterator[Dict[str, Any]]],
        align: bool = True
        ) -> Iterator[Dict[str, Any]]:
    """k-way merge per-symbol observation streams by bar timestamp so a
    multi-instrument session advances whichever instrument's next bar is
    chronologically earliest. Streams are first aligned to a common
    start — the latest series's first available bar — so a --skip that
    lands on different dates per symbol cannot silently run
    single-symbol for thousands of cycles."""
    import heapq
    heads: Dict[str, Dict[str, Any]] = {}
    for s, it in sources.items():
        try:
            heads[s] = next(it)
        except StopIteration:
            pass
    if not heads:
        return
    start = max(str(h.get("timestamp") or "") for h in heads.values()) \
        if align else ""
    logger.info(
        "multi-symbol feed: %d streams, common start=%s (heads=%s)",
        len(heads), start or "<unaligned>",
        {s: str(h.get("timestamp") or "") for s, h in heads.items()})
    streams = []
    for s, it in sources.items():
        def _stream(it: Iterator[Dict[str, Any]] = it,
                    head: Optional[Dict[str, Any]] = heads.get(s)
                    ) -> Iterator[Dict[str, Any]]:
            if head is not None and str(
                    head.get("timestamp") or "") >= start:
                yield head
            for obs in it:
                if str(obs.get("timestamp") or "") >= start:
                    yield obs
        streams.append(_stream())
    yield from heapq.merge(
        *streams, key=lambda item: str(item.get("timestamp") or ""))


def synthetic_observations(symbol: str, n_bars: int, seed: int,
                           symbols: Tuple[str, ...] = ()
                           ) -> Iterator[Dict[str, Any]]:
    from trading_bot.evaluation.synthetic_market import (
        RegimeSpec, SyntheticMarketGenerator, SyntheticMarketSpec)

    # Multi-regime: a single mean-reverting sine teaches regime-specific
    # behavior that does not transfer to real FX. Rotate trend, chop,
    # high-vol and a crash so learned state sees distribution shift.
    # Short runs truncate blocks in order so total bars == n_bars; a
    # small --cycles diagnostic must not produce a negative tail.
    q = max(8, n_bars // 8)
    blocks = [
        RegimeSpec("trend", q, drift=0.0004, vol=0.0006),
        RegimeSpec("mean_revert", q, vol=0.0003, ar1=-0.25,
                   sine_amp=0.008, sine_period=12),
        RegimeSpec("high_vol", q, drift=-0.0001, vol=0.002),
        RegimeSpec("flat", q, vol=0.0001),
        RegimeSpec("crash", max(4, q // 2), drift=-0.006, vol=0.003),
        RegimeSpec("mean_revert", q, vol=0.0004, ar1=-0.15,
                   sine_amp=0.005, sine_period=20),
        RegimeSpec("trend", q, drift=-0.0003, vol=0.0007),
        # tail fills the remainder so n_bars is respected
        RegimeSpec("high_vol", q, vol=0.001),
    ]
    regimes: List[RegimeSpec] = []
    used = 0
    for block in blocks:
        take = min(block.n_bars, n_bars - used)
        if take <= 0:
            break
        regimes.append(dataclasses.replace(block, n_bars=take))
        used += take
    if used < n_bars:
        # Blocks exhausted before n_bars (q quantized below n_bars/8):
        # the remainder becomes an explicit high-vol tail.
        regimes.append(RegimeSpec("high_vol", n_bars - used, vol=0.001))
    instruments = tuple(symbols) if symbols else (symbol,)
    spec = SyntheticMarketSpec(
        seed=seed, instruments=instruments, regimes=tuple(regimes))
    frames = SyntheticMarketGenerator(spec).generate()
    rows_by_sym = {s: frames[s].to_dict("records") for s in instruments}
    # Same-index bars are simultaneous across instruments: emit each
    # symbol's bar per step so a multi-symbol session sees them in
    # lockstep (synthetic bar-index 'timestamps' can't be merged).
    for i in range(n_bars):
        for s in instruments:
            rows = rows_by_sym[s]
            if i >= len(rows):
                continue
            row = rows[i]
            yield {**row, "symbol": s, "price": row.get("close")}


def publish_snapshot(state_dir: Path, snapshot: Dict[str, Any]) -> None:
    state_dir.mkdir(parents=True, exist_ok=True)
    tmp = state_dir / ".snapshot.tmp"
    tmp.write_text(json.dumps(snapshot, default=str), encoding="utf-8")
    target = state_dir / "snapshot.json"
    for _ in range(3):
        try:
            tmp.replace(target)
            return
        except OSError:
            # Windows AV/indexer/readers can hold the target briefly.
            time.sleep(0.2)
    # Last resort: overwrite in place (loses atomicity, keeps the run).
    target.write_text(tmp.read_text(encoding="utf-8"), encoding="utf-8")
    tmp.unlink(missing_ok=True)


def serve_dashboard(state_dir: Path, port: int) -> None:
    """GET-only snapshot server; there is no request body to mutate with."""
    import threading
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

    snapshot_path = state_dir / "snapshot.json"

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):  # noqa: N802 - stdlib hook name
            path = self.path.rstrip("/")
            if path == "":
                from trading_bot.core.csc.extended_capabilities import (
                    MOBILE_DASHBOARD_HTML)
                body = MOBILE_DASHBOARD_HTML.encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type",
                                 "text/html; charset=utf-8")
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                self.wfile.write(body)
                return
            if path not in ("/snapshot", "/snapshot.json"):
                self.send_error(404)
                return
            try:
                body = snapshot_path.read_bytes()
            except OSError:
                body = b'{"status": "no snapshot published yet"}'
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args):  # silence per-request logging
            pass

    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    logger.info("read-only dashboard on http://127.0.0.1:%d/", port)


async def run(args: argparse.Namespace) -> int:
    from trading_bot.foundation.runtime import ModularMonolithRuntime
    from trading_bot.interfaces.control import ControlChannel, OperatorConsole

    state_dir = Path(args.state_dir)
    channel = ControlChannel(state_dir / "control")

    # Determinism: RL advisors seed their own RNGs, but the wider
    # advisory/verification stack calls np.random unseeded — pin the
    # global stream so replayed runs are reproducible.
    import numpy as _np
    _np.random.seed(args.seed)

    # Per-run RL checkpoint isolation: two concurrent runners sharing
    # var/rl_state silently discard each other's learned updates.
    os.environ.setdefault(
        "TB_RL_STATE_DIR", str(state_dir / "rl"))

    # Bounded exploration: without this the epistemic-uncertainty floor
    # (u=1.0 at cold start) zeroes every quantity forever — the
    # abstention trap. Must be set before the CSC reads it at
    # construction inside the runtime.
    if args.explore_budget:
        os.environ["TB_CSC_EXPLORE_BUDGET"] = str(args.explore_budget)

    # Macro-event gate: NFP/CPI/central-bank windows are the dominant
    # FX hazard — obs inside a declared window is skipped, not
    # analyzed. Window file is data-driven, not hardcoded.
    event_windows = []
    if args.event_windows:
        try:
            from datetime import datetime as _dt
            def _iso(s):
                return _dt.fromisoformat(
                    str(s).replace("Z", "+00:00")).timestamp()
            for w in json.loads(Path(args.event_windows).read_text()):
                event_windows.append((_iso(w["start"]),
                                      _iso(w["end"]),
                                      str(w.get("reason", "event"))))
            logger.info("loaded %d event windows", len(event_windows))
        except (OSError, KeyError, json.JSONDecodeError) as exc:
            logger.warning("event windows load failed: %s", exc)

    if args.strategy_id:
        # Register before start so the first enriched cycle already sees
        # strategy_signals; the registry is otherwise empty and the
        # strategy_id config string would resolve to [] forever.
        from trading_bot.strategies.adapter import build_builtin_strategy
        _builtin_strategy = build_builtin_strategy(args.strategy_id)
    else:
        _builtin_strategy = None

    runtime = ModularMonolithRuntime({
        "execution_mode": "paper",
        "symbol": args.symbol,
        "account_id": "paper",
        "trading_state_path": str(state_dir / "trading_state.db"),
        "decision_log_path": str(state_dir / "decision_log.jsonl"),
        # Live-dims world model (FX=64 / latent 256); load is advisory-only —
        # a dim mismatch warns and falls back to scaffold weights, never dies.
        "world_model_checkpoint": str(PROJECT_ROOT / "var" / "world_model_v2.pt"),
        "strategy_id": args.strategy_id,
        "cognitive_assembly": {
            "enabled": True,
            "research_interval": args.research_interval,
            "discover_advisors": args.discover_advisors,
        },
    })
    await runtime.start()
    if _builtin_strategy is not None:
        runtime.bot.register_strategy_adapter(_builtin_strategy)
        logger.info("strategy_signals fed by %s", args.strategy_id)
    console = OperatorConsole(runtime.bot)
    await console.restore_state()  # paused/emergency flags survive restart
    if console.override.emergency_stop.is_triggered or stop_requested(args):
        logger.error("runner stopped before replay: emergency active or stop requested")
        await runtime.stop()
        return 2

    # Seed the derived-feature windows from the durable history file so a
    # restart does not re-lock directional decisions for a warmup period.
    history_path = state_dir / "market_history.json"
    histories: Dict[str, list] = {}
    try:
        _hist_raw = json.loads(history_path.read_text(encoding="utf-8"))
        if isinstance(_hist_raw, dict):
            histories = {str(k): [float(x) for x in v if isinstance(
                x, (int, float))][-64:]
                for k, v in _hist_raw.items() if isinstance(v, list)}
        elif isinstance(_hist_raw, list):
            # Legacy single-symbol format: attribute to the primary.
            histories = {args.symbol: [
                float(x) for x in _hist_raw
                if isinstance(x, (int, float))][-64:]}
    except (OSError, json.JSONDecodeError):
        histories = {}
    history: list = histories.get(args.symbol, [])
    seed_hl = []
    seed_boundary = 0  # ms open-time of newest seeded bar (hl_live only)
    _hl_needs = args.seed_bars > 0
    if args.seed_bars > 0:
        # Warm the feature windows from strictly-prior bars — the
        # same data source the replay reads, so provenance is honest.
        if args.source == "hl_live":
            rows, seed_boundary = hl_seed_rows(
                args.hl_coin or args.symbol, args.hl_tf, args.seed_bars)
        else:
            rows = prior_seed_rows(
                PROJECT_ROOT / args.db_path, args.symbol,
                args.timeframe, args.skip, args.seed_bars)
        history = [r[0] for r in rows]
        histories[args.symbol] = history
        seed_hl = [(r[1], r[2]) for r in rows]
        logger.info("seed-bars: %d strictly prior closes (replacing saved history)", len(history))
    csc = getattr(runtime.bot, "csc", None)
    if csc is not None:
        if _hl_needs:
            hlq = getattr(csc, "_hl_history", None)
            if isinstance(hlq, dict) and not hlq.get(args.symbol):
                # State dir had closes but no HL bars — warm path_risk
                # from the same seed rows so it isn't absent ~20 bars in.
                for hh, ll in seed_hl:
                    if isinstance(hh, (int, float)) and isinstance(ll, (int, float)):
                        from collections import deque as _dq
                        hlq.setdefault(args.symbol, _dq(maxlen=64)).append(
                            (float(hh), float(ll)))
        # Position closes must hit the ledger, not just CSC bookkeeping —
        # wire the canonical execution service so horizon/adverse/reversal
        # exits submit real opposing orders. This must NOT be gated on
        # --seed-bars: without it every close is mark-only and the venue
        # ledger keeps exposure the brain believes is flat.
        csc.configure_execution_service(runtime.bot.execution_service)
        # Swarm knowledge base persists beside the run state — learned
        # node skill and patterns survive restarts.
        csc.configure_swarm_state(
            str(Path(args.state_dir) / "swarm_kb.json"))
        # Self-wiring inventory likewise — measured node states persist.
        csc.configure_self_wiring_state(
            str(Path(args.state_dir) / "self_wiring.json"))
        # Opt-in voice alerts on critical events (estop / circuit
        # breaker); silent by default.
        if getattr(args, "voice_alerts", False):
            try:
                from trading_bot.core.csc.extended_capabilities import (
                    VoiceAlerter)
                csc.configure_voice_alerter(VoiceAlerter(enabled=True))
            except Exception as exc:  # noqa: BLE001
                logger.warning("voice alerts unavailable: %s", exc)
        # Session-gate self-validation: the bot must verify its own
        # safety chain before the first real observation — the probe
        # can never dispatch an order. Fails closed unless --no-preflight.
        if not getattr(args, "no_preflight", False):
            try:
                report = await csc.preflight_self_check()
            except Exception as exc:  # noqa: BLE001
                report = {"all_passed": False,
                          "blocking": [f"preflight_error:{exc}"]}
            if not report.get("all_passed"):
                logger.error(
                    "preflight self-check FAILED: %s — refusing to run",
                    report.get("blocking"))
                return 2
            logger.info("preflight self-check passed (%d checks)",
                        len(report.get("checks", [])))
    if args.decision_stride > 1 and csc is not None:
        csc._decision_stride = args.decision_stride
        logger.info("decision_stride=%d applied to CSC (cadenced decisions)",
                    args.decision_stride)
    if args.research_log and csc is not None:
        csc._research_log = True
        logger.info("research_log enabled — investigations echo to console")
    if histories:
        if csc is not None:
            for _hsym, _hhist in histories.items():
                csc.seed_observation_history(_hsym, _hhist)
                # Advisory services keep internal bar windows — replay
                # the same closes through them so they emit from cycle 1
                # instead of 'warming' for 50-70 live cycles.
                if hasattr(csc, "seed_advisory_history"):
                    try:
                        await csc.seed_advisory_history([
                            {"symbol": _hsym, "close": float(c),
                             "price": float(c), "volume": 0.0}
                            for c in _hhist
                            if isinstance(c, (int, float))])
                    except Exception:  # noqa: BLE001
                        pass
        _pw = getattr(runtime.bot, "_price_windows", None)
        if isinstance(_pw, dict):
            # Per-symbol windows (multi-instrument feeds): seed every
            # persisted symbol's deque, not one shared window.
            from collections import deque as _deque
            for _s, _h in histories.items():
                _d = _pw.get(_s)
                if _d is None:
                    _d = _pw[_s] = _deque(
                        maxlen=runtime.bot._price_window.maxlen)
                _d.extend(
                    float(c) for c in _h if isinstance(c, (int, float)))
        else:
            runtime.bot._price_window.extend(
                float(c) for c in history if isinstance(c, (int, float)))
        logger.info("seeded %d historical closes into feature windows",
                    len(history))
        # Restore open positions from the prior session — without this a
        # restart orphans persisted fills: ledger holds exposure the CSC
        # forgot, so it never settles and never scores those predictions.
        pos_state_path = state_dir / "open_positions.json"
        if pos_state_path.exists():
            try:
                n = csc.import_open_positions(json.loads(
                    pos_state_path.read_text(encoding="utf-8")))
                if n:
                    logger.info("restored %d open positions", n)
            except Exception as exc:
                logger.warning("open-position restore failed: %s", exc)

    # Honest fill costs: paper fills at raw bar price would overstate every
    # edge the outcome scorer learns from. Defaults are the measured
    # MetaQuotes-Demo EURUSD figures (spread ~2bps, slip ~1.25bps from the
    # real fill on 2026-10-07); commission 0 matches that venue.
    adapter = getattr(
        getattr(runtime.bot, "execution_service", None), "adapter", None)
    for attr, val in (("spread_bps", args.spread_bps),
                      ("slippage_bps", args.slippage_bps),
                      ("commission_per_unit", args.commission),
                      ("market_data_source", args.source)):
        if adapter is not None and hasattr(adapter, attr):
            setattr(adapter, attr, val)
    if adapter is not None:
        logger.info("paper cost model: spread=%.2fbps slip=%.2fbps comm=%.4f",
                    args.spread_bps, args.slippage_bps, args.commission)

    # Maker mode: swap the venue for the resting-order adapter and point
    # the bridge at passive LIMIT entry pricing. service.py is protected
    # — the swap happens here, never by modifying the protected file.
    _maker_adapter = None
    if args.paper_order_style == "maker":
        from trading_bot.brokers.maker_paper_adapter import (
            MakerPaperAdapter)
        exec_svc = getattr(runtime.bot, "execution_service", None)
        old_ad = getattr(exec_svc, "adapter", None) if exec_svc else None
        _maker_adapter = MakerPaperAdapter(
            spread_bps=0.0, slippage_bps=0.0, commission_per_unit=0.0,
            maker_fee_bps=args.maker_fee_bps,
            # 3 marks per bar (low/high/close) — TTL bars -> marks
            resting_ttl_marks=args.maker_ttl_bars * 3)
        _maker_adapter.market_data_source = args.source
        if old_ad is not None:  # preserve venue state across the swap
            _maker_adapter._marks = dict(getattr(old_ad, "_marks", {}))
            _maker_adapter._resting = dict(
                getattr(old_ad, "_resting", {}))
            _maker_adapter._reports = dict(
                getattr(old_ad, "_reports", {}))
            _maker_adapter._pending_market = list(
                getattr(old_ad, "_pending_market", []))
            _maker_adapter._positions = dict(
                getattr(old_ad, "_positions", {}))
            _maker_adapter.connected = getattr(old_ad, "connected", False)
        if exec_svc is not None:
            exec_svc.adapter = _maker_adapter
            adapter = _maker_adapter
        bridge = getattr(runtime.bot, "bridge", None)
        if bridge is not None:
            bridge.order_style = "maker"
            bridge.maker_offset_bps = args.maker_offset_bps
        logger.info(
            "maker paper mode: offset=%.2fbps ttl=%dbars fee=%.2fbps/side",
            args.maker_offset_bps, args.maker_ttl_bars, args.maker_fee_bps)

    # Resting->filled transitions happen inside on_mark, long after
    # submit persisted ACCEPTED. Push terminal venue outcomes into the
    # durable ledger or fills would never reach settlement accounting.
    _maker_synced: set = set()

    async def _sync_maker_reports():
        if _maker_adapter is None:
            return
        svc = getattr(runtime.bot, "execution_service", None)
        repo = getattr(svc, "repository", None) if svc else None
        if repo is None:
            return
        terminal = {"filled", "expired", "cancelled", "rejected"}
        for coid, rep in getattr(_maker_adapter, "_reports", {}).items():
            if coid in _maker_synced:
                continue
            if getattr(rep.status, "value", rep.status) not in terminal:
                continue
            order = getattr(svc, "_orders", {}).get(coid)
            if order is None:
                continue
            try:
                await repo.record_execution(order, rep)
                _maker_synced.add(coid)
            except Exception as exc:  # noqa: BLE001
                logger.warning("maker report sync failed %s: %s",
                               coid, exc)

    from trading_bot.execution.paper_feedback import PaperSettlementFeedback
    feedback = PaperSettlementFeedback(
        runtime.bot.execution_service.repository, csc) if csc is not None else None
    feedback_status = {}

    async def sync_economic_feedback():
        if feedback is None:
            return {}
        try:
            return await feedback.sync()
        except Exception as exc:
            # Missing or conflicting receipts must never become positive
            # reward; retain the durable fills for investigation/replay.
            logger.error("paper settlement feedback unavailable: %s", exc)
            return {"status": "unavailable", "reason": str(exc)}

    feedback_status = await sync_economic_feedback()

    if args.dashboard_port:
        serve_dashboard(state_dir, args.dashboard_port)

    rv_forecaster = None
    rv_last = None
    if args.rv_forecast:
        try:
            from trading_bot.world_model.rv_forecaster import (
                RVBlendForecaster)
            rv_forecaster = RVBlendForecaster(
                PROJECT_ROOT / args.rv_forecast, timeframe=args.timeframe,
                quantile_path=(PROJECT_ROOT / args.rv_quantile)
                if args.rv_quantile else None)
            logger.info("rv forecaster armed (advisory): %s quantiles=%s",
                        args.rv_forecast, args.rv_quantile)
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "rv forecaster unavailable (%s) — running without", exc)
    # Warm the forecaster's 32-bar window from the same strictly-prior
    # seed rows the CSC windows use — without this the first ~32 replay
    # cycles produce "warming" status instead of forecasts.
    if rv_forecaster is not None and args.seed_bars > 0 \
            and args.source != "hl_live":
        _warmed = 0
        for r in rows:
            try:
                rv_forecaster.update({
                    "timestamp": r[5], "broker_timestamp": r[5],
                    "symbol": args.symbol,
                    "open": r[3], "high": r[1], "low": r[2],
                    "close": r[0],
                    "volume": r[4] if r[4] is not None else 0.0})
                _warmed += 1
            except Exception:  # noqa: BLE001
                pass
        logger.info("rv forecaster warmed on %d/%d seed bars",
                    _warmed, len(rows))
    rv_log_path = state_dir / "rv_forecast_log.jsonl"

    if args.source == "db":
        _btz = args.broker_tz_offset
        if str(_btz).lower() in ("auto", ""):
            _btz = _detect_broker_tz_offset(
                PROJECT_ROOT / args.db_path, args.symbol,
                args.timeframe)
        elif str(_btz).lower() in ("utc", "none"):
            _btz = 0.0
        else:
            _btz = float(_btz)
        if args.universe:
            _auto = str(args.universe).strip().lower() == "auto"
            if _auto and args.universe_refresh > 0:
                # Rotating universe: the watchlist is re-ranked
                # point-in-time every --universe-refresh bars.
                def _btz_of(db):
                    return _btz if Path(db).name == \
                        Path(args.db_path).name else 0.0
                source = rotating_universe_observations(
                    args, _btz_of,
                    top=args.universe_top,
                    refresh_every=args.universe_refresh)
                _db_sources = None
            else:
                _rows = getattr(args, "_universe_rows", None) \
                    or parse_universe(args.universe)
                _db_sources = {}
                for _db, _sym, _tf, _sk in _rows:
                    # Broker-time de-offset is a MetaTrader-export quirk —
                    # apply it only to the configured db; exchange exports
                    # (binance/kraken/hl) are already UTC.
                    _sbtz = _btz if Path(_db).name == \
                        Path(args.db_path).name else 0.0
                    if _auto:
                        # Auto rows carry a tail (last-N bars each); the
                        # merge aligns all series to a common start so the
                        # replay window is genuinely simultaneous. A series
                        # whose window doesn't overlap simply emits nothing —
                        # visible as absence in the feed-mix log.
                        _db_sources[f"{_db}:{_sym}:{_tf}"] = \
                            db_observations(
                                PROJECT_ROOT / _db, _sym, _tf, 0,
                                args.htf_timeframe,
                                broker_tz_offset=_sbtz, tail=_sk)
                    else:
                        _db_sources[f"{_db}:{_sym}:{_tf}"] = \
                            db_observations(
                                PROJECT_ROOT / _db, _sym, _tf, _sk,
                                args.htf_timeframe,
                                broker_tz_offset=_sbtz)
                source = merged_symbol_observations(_db_sources)
        else:
            _db_sources = {
                s: db_observations(
                    PROJECT_ROOT / args.db_path,
                    s, args.timeframe, args.skip,
                    args.htf_timeframe,
                    broker_tz_offset=_btz)
                for s in args.symbols}
            source = next(iter(_db_sources.values())) \
                if len(_db_sources) == 1 \
                else merged_symbol_observations(_db_sources)
    elif args.source == "cross":
        source = cross_observations(
            PROJECT_ROOT / args.db_path, args.symbol,
            args.cross_denominator, args.timeframe, args.skip)
    elif args.source == "hl_live":
        source = hl_live_observations(
            args.hl_coin or args.symbol, args.symbol,
            hl_tf=args.hl_tf, timeframe_label=args.timeframe,
            poll_s=args.hl_poll_s, start_after_open=seed_boundary)
    else:
        source = synthetic_observations(
            args.symbol, args.cycles or 200, args.seed,
            symbols=args.symbols)

    processed = 0
    emergency = False
    _sym_counts: Dict[str, int] = {}
    try:
        for obs in source:
            if stop_requested(args):
                logger.info("supervisor requested end of paper session")
                break
            if event_windows:
                from datetime import datetime as _dt
                try:
                    _o_ts = _dt.fromisoformat(
                        str(obs.get("timestamp", "")).replace(
                            "Z", "+00:00")).timestamp()
                except (TypeError, ValueError):
                    _o_ts = 0.0
                _in_ev = next(
                    (w for w in event_windows
                     if w[0] <= _o_ts <= w[1]), None)
                if _in_ev is not None:
                    logger.info("cycle skipped — event window: %s",
                                _in_ev[2])
                    continue
            # Backpressure: a live obs older than the staleness budget
            # is dropped — deciding on stale prices is worse than
            # missing a bar. Only applies when obs time is within a
            # day of wall clock (a real feed), not historical replay.
            if args.stale_drop_seconds > 0:
                try:
                    from datetime import datetime as _ds
                    _o = _ds.fromisoformat(
                        str(obs.get("timestamp", "")).replace(
                            "Z", "+00:00")).timestamp()
                    _age = time.time() - _o
                    if 0 < _age < 86400 and _age > args.stale_drop_seconds:
                        logger.warning(
                            "dropping stale obs (%.0fs > %ss budget)",
                            _age, args.stale_drop_seconds)
                        continue
                except (TypeError, ValueError):
                    pass
            for command in channel.drain():
                outcome = await console.apply(command)
                logger.info("operator command %s -> %s",
                            command.get("action"), outcome)
                if command.get("action") == "emergency_stop":
                    emergency = True
            if args.hl_l2 and "order_book_time" not in obs:
                # Live book merged onto each obs. On replay sources this
                # is the CURRENT book, not the bar's historical book —
                # flagged "anachronistic" so simulation/advisory code
                # cannot mistake it for point-in-time evidence.
                # (hl_live attaches a truly point-in-time book upstream.)
                try:
                    from trading_bot.feeds import hl_l2 as _hl_l2
                    obs.update(_hl_l2.snapshot(str(obs.get("symbol")
                                                   or args.symbol)))
                    obs["order_book_time"] = order_book_time_label(
                        args.source)
                except Exception:  # noqa: BLE001
                    obs["order_book"] = None
            if args.hl_archive:
                # Point-in-time orderflow history: one JSONL row per
                # processed obs (bar + book as-seen). On hl_live this is
                # real per-bar evidence; on replay the anachronistic tag
                # is preserved so archived rows cannot masquerade.
                try:
                    with open(args.hl_archive, "a", encoding="utf-8") as _af:
                        _af.write(json.dumps(obs, default=str) + "\n")
                except Exception:  # noqa: BLE001
                    logger.warning("hl archive write failed",
                                   exc_info=True)
            price = obs.get("price", obs.get("close"))
            if price is not None:
                symbol = str(obs.get("symbol") or args.symbol)
                console.last_price[symbol] = float(price)
                # Feed the venue mark so resting/limit/delayed orders can
                # fill on this bar — fills never use a mark older than the
                # bar that produced them.
                adapter = getattr(
                    getattr(runtime.bot, "execution_service", None),
                    "adapter", None)
                if hasattr(adapter, "on_mark"):
                    # Feed the bar range so resting LIMITs can fill on
                    # intra-bar touches; pending market orders still
                    # settle at the last mark (the close).
                    _lo, _hi = obs.get("low"), obs.get("high")
                    if _lo:
                        adapter.on_mark(symbol, float(_lo))
                    if _hi:
                        adapter.on_mark(symbol, float(_hi))
                    adapter.on_mark(symbol, float(price))
                    await _sync_maker_reports()
                _ph = histories.setdefault(symbol, [])
                _ph.append(float(price))
                histories[symbol] = _ph[-64:]
                if symbol == args.symbol:
                    history = histories[symbol]
                try:
                    tmp = history_path.with_suffix(".tmp")
                    tmp.write_text(json.dumps(histories), encoding="utf-8")
                    tmp.replace(history_path)
                except OSError:
                    logger.warning("market history persistence failed")
            if rv_forecaster is not None:
                # Shadow-mode advisory: the forecast rides obs as rvf_*
                # fields (never consulted for decisions) and lands in an
                # append-only JSONL log for later outcome analysis.
                try:
                    rv_last = rv_forecaster.update(obs)
                except Exception as exc:  # noqa: BLE001
                    rv_last = {"ready": False, "status": "error",
                               "error": str(exc)}
                if rv_last and rv_last.get("ready"):
                    for _k in rv_last["log_ratio"]:
                        obs[f"rvf_log_{_k}"] = rv_last["log_ratio"][_k]
                        obs[f"rvf_mult_{_k}"] = rv_last["vol_mult"][_k]
                    for _k, _qs in (rv_last.get("quantile_mult")
                                    or {}).items():
                        for _tag, _m in _qs.items():
                            obs[f"rvf_{_tag}mult_{_k}"] = _m
                    obs["rvf_source"] = "rv_blend_forecaster"
                try:
                    with open(rv_log_path, "a", encoding="utf-8") as _rf:
                        _rf.write(json.dumps({
                            "timestamp": obs.get("broker_timestamp")
                            or obs.get("timestamp"),
                            "symbol": symbol,
                            "close": float(price),
                            "forecast": rv_last}, default=str) + "\n")
                except OSError:
                    logger.warning("rv forecast log write failed")
            if not emergency:
                # Run the cycle as a cancellable task and poll the
                # control channel mid-cycle — under load a single
                # cycle can take minutes, and an estop that waits for
                # the cycle boundary is not a safety control.
                task = asyncio.ensure_future(runtime.bot.run_cycle(obs))
                _completed = True
                while not task.done():
                    for command in channel.drain():
                        outcome = await console.apply(command)
                        if command.get("action") == "emergency_stop":
                            emergency = True
                    if stop_requested(args) or emergency or getattr(
                            console.override.emergency_stop,
                            "is_triggered", False):
                        task.cancel()
                        try:
                            await task
                        except (asyncio.CancelledError, Exception):
                            pass
                        _completed = False
                        break
                    await asyncio.sleep(0.25)
                if _completed:
                    await task  # surface cycle failures instead of counting them as success
                    processed += 1
                    _sym_counts[str(obs.get("symbol") or "?")] = (
                        _sym_counts.get(str(obs.get("symbol") or "?"), 0)
                        + 1)
                    if processed % 10 == 0:
                        logger.info("feed mix after %d cycles: %s",
                                    processed, _sym_counts)
            feedback_status = await sync_economic_feedback()
            publish_snapshot(state_dir, {
                "as_of": time.time(),
                "cycles": processed,
                "control": console.control_state(),
                "mode": "paper",
                # Data provenance: 'paper' mode alone is ambiguous —
                # synthetic bars and real market_data.db replay produce
                # identical-looking snapshots without the source label.
                "data_source": args.source,
                "economic_rewards": feedback_status,
                "data_timeframe": args.timeframe if args.source == "db"
                else None,
                "symbol": args.symbol,
                "symbols": list(args.symbols),
                # Shadow vol-change forecast (advisory only — rvf_*
                # fields on the obs carry the same values downstream).
                "rv_forecast": rv_last,
                # Read-only advisory standing — which advisors contribute
                # and their measured weight/precision per regime.
                "advisors": csc.advisory_report() if csc is not None
                and hasattr(csc, "advisory_report") else None,
                # Per-feature outcome attribution — assumed weights
                # become measured once settled trades accumulate.
                "feature_attribution": (
                    csc.feature_attribution_report()
                    if csc is not None and hasattr(
                        csc, "feature_attribution_report") else None),
                # Ordered stage-funnel counts — where each observation's
                # decision terminated (verification veto, net-cost,
                # governance, consensus) or abstained.
                "funnel": csc.funnel_report() if csc is not None
                and hasattr(csc, "funnel_report") else None,
                # Autonomy + evolution supervisor state — ops decisions,
                # experience counts, learning cadence, connectivity.
                "autonomy": csc.autonomy_report() if csc is not None
                and hasattr(csc, "autonomy_report") else None,
                # Read-only AI-stack planes (state/evidence/selection)
                # — one-line summaries per DOCS/CANONICAL_RUNTIME_DATAFLOW §4.
                "ai_stack": runtime.ai_stack.explain()
                if getattr(runtime, "ai_stack", None) is not None else None,
            })
            if emergency or console.override.emergency_stop.is_triggered or stop_requested(args):
                break
            if args.cycles and processed >= args.cycles:
                break
            if args.interval > 0:
                await asyncio.sleep(args.interval)
    finally:
        # Settle every open position at last marks and persist the
        # remainder — kills are instant, so anything still open here
        # would otherwise vanish from CSC bookkeeping while its fills
        # stay in the ledger (orphan exposure).
        if csc is not None:
            try:
                marks = {s: p for s, p in console.last_price.items()
                         if isinstance(p, (int, float)) and p > 0}
                realized = await csc.close_all_positions(marks)
                if realized:
                    logger.info("end-of-run forecast flush settled: %s",
                                list(realized))
                tmp = (state_dir / "open_positions.json")
                tmp.write_text(json.dumps(
                    csc.export_open_positions(), default=str),
                    encoding="utf-8")
            except Exception as exc:
                logger.warning("position flush/persist failed: %s", exc)
        await sync_economic_feedback()
        await runtime.stop()
    logger.info("runner finished: %d cycles processed", processed)
    return 0


def main(argv: Optional[list] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db-path", default="market_data.db",
                        help="db/cross source: SQLite path with a "
                             "market_data table (default market_data.db; "
                             "use lse_data.db for LSE-synced data)")
    parser.add_argument("--universe", default="",
                        help="multi-asset db feed: 'db:sym1,sym2:tf[:skip];"
                             "db2:sym3:tf2[:skip2]' — e.g. "
                             "'market_data.db:EURUSD,GBPUSD:M15:64000;"
                             "binance_data.db:BTC,ETH:15m:15900'. "
                             "Overrides --symbols/--timeframe/--skip; "
                             "streams align to a common start timestamp "
                             "and merge chronologically. 'auto' selects "
                             "the universe itself: every onboarded "
                             "market_data store is probed and the top "
                             "--universe-top series by measured "
                             "structure_score are replayed (last "
                             "--universe-tail bars each)")
    parser.add_argument("--universe-top", type=int, default=6)
    parser.add_argument("--universe-tail", type=int, default=4000,
                        help="auto universe only: bars per selected "
                             "series (default 4000)")
    parser.add_argument("--universe-refresh", type=int, default=0,
                        help="auto universe only: >0 rotates the "
                             "watchlist mid-run — every N bars the "
                             "series ranking is recomputed on closes "
                             "strictly BEFORE the tape clock (no "
                             "lookahead); new entries join at the "
                             "current clock, dropped ones stop emitting")
    parser.add_argument("--source",
                        choices=("synthetic", "db", "cross", "hl_live"),
                        default="synthetic")
    parser.add_argument("--symbol", default="EURUSD")
    parser.add_argument("--symbols", default="",
                        help="comma-separated instrument list overriding "
                             "--symbol for db/synthetic sources — the "
                             "feed emits every symbol (db: merged by bar "
                             "timestamp; synthetic: lockstep same-index "
                             "bars), so cognition analyzes a real "
                             "multi-instrument market instead of one pair")
    parser.add_argument("--cross-denominator", default="GBPUSD",
                        help="for --source cross: denominator leg")
    parser.add_argument("--timeframe", default="M15",
                        help="db source only: market_data.db holds M15+H1; "
                             "unfiltered replay interleaves cadences")
    parser.add_argument("--seed-bars", type=int, default=0,
                        help="bootstrap feature windows from the N bars "
                             "strictly BEFORE the replay start — the "
                             "verifier needs ~21 bars of measured "
                             "structure or it vetoes every hypothesis "
                             "for ~21 cold-start cycles")
    parser.add_argument("--skip", type=int, default=0,
                        help="db source only: drop the first N bars of the "
                             "filtered timeframe (segments parallel runs)")
    parser.add_argument("--htf-timeframe", default="",
                        help="db source only: attach point-in-time higher-"
                             "timeframe context (htf_close/htf_trend/htf_rsi14) "
                             "from this timeframe's closed bars — e.g. H1")
    parser.add_argument("--cycles", type=int, default=200)
    parser.add_argument("--spread-bps", type=float, default=2.0)
    parser.add_argument("--slippage-bps", type=float, default=1.25)
    parser.add_argument("--commission", type=float, default=0.0)
    # Maker execution: entries become passive LIMITs resting on the
    # paper venue (position_close stays MARKET). Measures fillable edge
    # instead of charging taker cost on every hypothetical.
    parser.add_argument("--paper-order-style",
                        choices=("market", "maker"), default="market")
    parser.add_argument("--maker-offset-bps", type=float, default=2.0,
                        help="passive distance off mark for entry LIMITs")
    parser.add_argument("--maker-ttl-bars", type=int, default=4,
                        help="bars a resting order may live before expiry")
    parser.add_argument("--maker-fee-bps", type=float, default=2.0,
                        help="bps-of-notional commission per maker fill")
    parser.add_argument("--interval", type=float, default=0.0,
                        help="seconds between cycles (0 = as fast as possible)")
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--broker-tz-offset", default="auto",
                        help="'auto' detects via the volume-trough "
                             "signature; a number overrides; '0'/'utc' "
                             "means timestamps are already UTC. DST "
                             "drift is NOT corrected either way")
    parser.add_argument("--stale-drop-seconds", type=float, default=0,
                        help="drop obs whose timestamp is more than N "
                             "seconds older than wall clock; live-feed "
                             "backpressure policy (0=off; leave off for "
                             "replay — historical bars are always 'stale')")
    parser.add_argument("--event-windows", default="",
                        help="JSON file with [{start,end,reason}] ISO "
                             "intervals; cycles inside a window are "
                             "skipped (macro-event no-trade gate)")
    parser.add_argument("--rl-state-dir", default="",
                        help="checkpoint dir for RL advisors; defaults "
                             "to <state-dir>/rl so concurrent runs "
                             "don't race on shared checkpoints")
    parser.add_argument("--state-dir", default=str(DEFAULT_STATE_DIR))
    parser.add_argument("--dashboard-port", type=int, default=0,
                        help="serve the read-only snapshot on 127.0.0.1:PORT")
    parser.add_argument("--research-log", action="store_true",
                        help="echo research questions/verdicts/KG writes "
                             "to the console as they happen (audit trail "
                             "is always written regardless)")
    parser.add_argument("--research-interval", type=int, default=100,
                        help="observations between automatic research "
                             "cycles (0 disables cycles; the engine "
                             "still ingests forward outcomes)")
    parser.add_argument("--decision-stride", type=int, default=1,
                        help="CSC decides every Nth observation "
                             "(replicated-OOS evidence supports 4+)")
    parser.add_argument("--discover-advisors", action="store_true",
                        help="auto-scan quarantined AI packages for "
                             "observation-callable analyzers and attach "
                             "them as advisory services (probe-gated, "
                             "timeout-bounded; default off)")
    parser.add_argument("--voice-alerts", action="store_true",
                        help="speak critical events via Windows SAPI "
                             "(opt-in; silent default)")
    parser.add_argument("--no-preflight", action="store_true",
                        help="skip the session-gate self-check (default: "
                             "runner fails closed on preflight failure)")
    parser.add_argument("--strategy-id", default=None,
                        help="optional registered strategy capability id")
    parser.add_argument("--log-level", default="INFO")
    parser.add_argument("--stop-file", default="",
                        help="supervisor-owned stop request; checked between and during cycles")
    parser.add_argument("--hl-coin", default="",
                        help="hl_live: Hyperliquid coin name (default "
                             "= --symbol)")
    parser.add_argument("--hl-tf", default="15m",
                        help="hl_live: API interval (1m/5m/15m/1h/4h/1d)")
    parser.add_argument("--hl-poll-s", type=float, default=15.0,
                        help="hl_live: seconds between candle polls")
    parser.add_argument("--hl-l2", action="store_true",
                        help="merge the LIVE Hyperliquid L2 order book onto "
                             "each observation (keyless; tagged "
                             "order_book_time='live' only on hl_live — "
                             "replay merges are 'anachronistic': current "
                             "state, NOT point-in-time evidence)")
    parser.add_argument("--hl-archive", default="",
                        help="append each processed observation (bar + book) "
                             "to this JSONL path — point-in-time orderflow "
                             "history for later backtesting")
    parser.add_argument("--rv-forecast", nargs="?", metavar="PATH",
                        const="var/rv_blend_forecaster.pt", default=None,
                        help="vol-change forecaster: attach rvf_* fields "
                             "to each obs + append "
                             "<state-dir>/rv_forecast_log.jsonl (PATH "
                             "defaults to the blend checkpoint; needs "
                             "torch — hermes env). The CSC consumes "
                             "rvf_mult_rv16 as a bounded down-only "
                             "sizing scalar (see rv_vol_size_factor); "
                             "the risk service remains the sizing "
                             "authority.")
    parser.add_argument("--rv-quantile", nargs="?", metavar="PATH",
                        const="var/rv_quantile_forecaster.joblib",
                        default=None,
                        help="optional GBM quantile heads "
                             "(P50/P80/P95) alongside --rv-forecast: "
                             "emits rvf_q*mult_* fields; rvf_q95mult_rv16 "
                             "then drives the sizing scalar instead of "
                             "the mean (needs joblib — hermes env).")
    parser.add_argument("--explore-budget", type=int, default=0,
                        metavar="N",
                        help="allow N exploratory trades at ~10%% size so "
                             "real fills can decay the cold-start "
                             "epistemic-uncertainty floor (default 0 = "
                             "fail-closed abstention; sets "
                             "TB_CSC_EXPLORE_BUDGET before bot start)")
    args = parser.parse_args(argv)
    args.symbols = tuple(
        s.strip().upper() for s in str(args.symbols or "").split(",")
        if s.strip()) or (args.symbol,)
    if args.universe:
        # Snapshot/status should show the actual universe, not --symbols.
        _is_auto = str(args.universe).strip().lower() == "auto"
        if _is_auto and args.universe_refresh > 0:
            args.symbols = ("<rotating auto>",)
            args._universe_rows = []
        else:
            args._universe_rows = auto_universe(
                args.universe_top, args.universe_tail) \
                if _is_auto else parse_universe(args.universe)
            args.symbols = tuple(dict.fromkeys(
                s for _, s, _, _ in args._universe_rows))
    logging.basicConfig(level=args.log_level,
                        format="%(asctime)s %(name)s %(levelname)s %(message)s")
    from trading_bot.interfaces.operator_reset import runner_lock
    with runner_lock(Path(args.state_dir)):
        return asyncio.run(run(args))


if __name__ == "__main__":
    raise SystemExit(main())
