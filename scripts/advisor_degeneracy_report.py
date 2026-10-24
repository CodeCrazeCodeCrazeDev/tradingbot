"""Per-advisor degeneracy measurement: replay real bars through every
advisory factory and count substantive vs degenerate/missing/failed
responses. Produces the evidence list for the measured-active-set cut —
a service that never produces substantive output on real data is a
degenerate advisor, removable by construction without outcome history.

Usage (hermes env):
    python scripts/advisor_degeneracy_report.py --bars 400
"""
import argparse
import asyncio
import inspect
import json
import sqlite3
import sys
from collections import Counter
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO))

from trading_bot.core.csc.advisory import DEFAULT_ADVISORY_FACTORIES  # noqa: E402


def load_bars(db_path, symbol="EURUSD", tf="M15", limit=400):
    con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        rows = con.execute(
            "SELECT timestamp,open,high,low,close,volume FROM market_data "
            "WHERE symbol=? AND timeframe=? ORDER BY timestamp DESC LIMIT ?",
            (symbol, tf, limit)).fetchall()[::-1]
    finally:
        con.close()
    return [{"timestamp": r[0], "open": r[1], "high": r[2], "low": r[3],
             "close": r[4], "price": r[4], "volume": r[5],
             "symbol": symbol} for r in rows]


_DEGENERATE = {'warming', 'no_read', 'no_data', 'missing_data',
               'no_signal', 'none', 'skipped', 'unavailable',
               'idle', 'degenerate'}


def classify(out):
    """Match the canonical funnel's classification (controller._stage)."""
    if not isinstance(out, dict):
        return "degenerate"
    if out.get("direction") in ("BUY", "SELL"):
        return "directional"
    ev = out.get("evidence")
    status = str(ev.get("status")).lower() if isinstance(ev, dict) else ""
    if status in _DEGENERATE or not ev:
        return "degenerate"
    return "substantive"


async def measure(factories, obs_list):
    report = {}
    total = len(factories)
    for i, (cap_id, factory) in enumerate(factories):
        # Progress logging: an unlogged stall previously killed this
        # report silently (Introspector's per-obs rglob walked the whole
        # repo). Print before/after each factory so a hang/crash names
        # the offender.
        print(f"[{i}/{total}] {cap_id} ...", flush=True)
        import time as _t
        t0 = _t.time()
        counts = Counter()
        try:
            svc = factory()
        except Exception as exc:
            report[cap_id] = {"error": str(exc)[:200]}
            print(f"    init error: {exc!r:.100}", flush=True)
            continue
        for obs in obs_list:
            try:
                out = svc.analyze(dict(obs))
                if inspect.isawaitable(out):
                    out = await asyncio.wait_for(out, 5.0)
                counts[classify(out)] += 1
            except Exception:
                counts["failed"] += 1
        elapsed = _t.time() - t0
        report[cap_id] = dict(counts)
        flag = " SLOW" if elapsed > 30 else ""
        print(f"    {dict(counts)} [{elapsed:.1f}s]{flag}", flush=True)
    return report


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--bars", type=int, default=400)
    p.add_argument("--symbol", default="EURUSD")
    p.add_argument("--out", default="var/reports/advisor_degeneracy.json")
    args = p.parse_args()
    obs = load_bars(_REPO / "market_data.db", args.symbol, limit=args.bars)
    print(f"measuring {len(DEFAULT_ADVISORY_FACTORIES)} advisory "
          f"factories over {len(obs)} bars")
    report = asyncio.run(measure(DEFAULT_ADVISORY_FACTORIES, obs))
    summary = {"substantive": 0, "directional": 0, "degenerate": 0,
               "failed": 0, "error": 0}
    for v in report.values():
        if "error" in v:
            summary["error"] += 1
        elif v.get("directional", 0) > 0 or v.get("substantive", 0) > 0:
            summary["substantive"] += 1
        elif v.get("failed", 0) > 0:
            summary["failed"] += 1
        else:
            summary["degenerate"] += 1
    out = {"symbol": args.symbol, "bars": len(obs),
           "factories": len(DEFAULT_ADVISORY_FACTORIES),
           "summary": summary, "per_service": report}
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(out, indent=2, sort_keys=True))
    print(json.dumps(summary, indent=2))
    print(f"-> {args.out}")


if __name__ == "__main__":
    main()
