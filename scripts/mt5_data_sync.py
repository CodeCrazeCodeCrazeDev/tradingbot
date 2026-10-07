#!/usr/bin/env python3
"""Pull real OHLCV history from the running MT5 terminal into market_data.db.

READ-ONLY: attaches to the terminal's active session via initialize()
(no credentials, no orders — copy_rates only). Dedupes on
(symbol, timeframe, timestamp) so re-runs are idempotent.

Usage:
    python scripts/mt5_data_sync.py --symbols EURUSD --timeframes M15
    python scripts/mt5_data_sync.py --symbols EURUSD,GBPUSD --timeframes M15,H1 --max-bars 65000
"""

import argparse
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
_TF = {
    "M1": 1, "M5": 5, "M15": 15, "M30": 30,
    "H1": 16385, "H4": 16388, "D1": 16408,
}


def _terminal_path() -> str:
    for candidate in (
        r"C:\Program Files\MetaTrader 5\terminal64.exe",
        r"C:\Program Files (x86)\MetaTrader 5\terminal64.exe",
    ):
        if Path(candidate).exists():
            return candidate
    return ""


def sync(db_path: str, symbols, timeframes, max_bars: int = 65000) -> dict:
    import MetaTrader5 as mt5

    if not mt5.initialize(path=_terminal_path() or None):
        raise RuntimeError(f"MT5 initialize failed: {mt5.last_error()}")
    report = {}
    try:
        conn = sqlite3.connect(db_path)
        for symbol in symbols:
            for tf_name in timeframes:
                tf_const = getattr(mt5, f"TIMEFRAME_{tf_name}", None)
                if tf_const is None:
                    report[f"{symbol}:{tf_name}"] = {"error": "unknown tf"}
                    continue
                rates = mt5.copy_rates_from_pos(symbol, tf_const, 0, max_bars)
                if rates is None or len(rates) == 0:
                    report[f"{symbol}:{tf_name}"] = {
                        "error": str(mt5.last_error())}
                    continue
                existing = {
                    r[0] for r in conn.execute(
                        "SELECT timestamp FROM market_data "
                        "WHERE symbol=? AND timeframe=?",
                        (symbol, tf_name))}
                inserted = 0
                for row in rates:
                    ts = datetime.fromtimestamp(
                        int(row["time"]), tz=timezone.utc
                    ).isoformat()
                    if ts in existing:
                        continue
                    conn.execute(
                        "INSERT INTO market_data (timestamp, symbol, "
                        "timeframe, open, high, low, close, volume) "
                        "VALUES (?,?,?,?,?,?,?,?)",
                        (ts, symbol, tf_name, float(row["open"]),
                         float(row["high"]), float(row["low"]),
                         float(row["close"]), float(row["tick_volume"])))
                    inserted += 1
                conn.commit()
                report[f"{symbol}:{tf_name}"] = {
                    "fetched": len(rates), "inserted": inserted,
                    "skipped_existing": len(rates) - inserted}
        conn.close()
    finally:
        mt5.shutdown()
    return report


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--db", default=str(_REPO / "market_data.db"))
    p.add_argument("--symbols", default="EURUSD")
    p.add_argument("--timeframes", default="M15")
    p.add_argument("--max-bars", type=int, default=65000)
    args = p.parse_args(argv)
    report = sync(args.db, args.symbols.split(","),
                  args.timeframes.split(","), args.max_bars)
    for k, v in report.items():
        print(f"{k}: {v}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
