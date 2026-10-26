"""Sync TradingView OHLCV bars into a market_data-shaped sqlite db.

Uses tvdatafeed (TradingView websocket, keyless for public symbols) —
same table schema as lse_data.db so paper_runner --source db and
edge_baseline.py work unchanged.

Hermes env: python scripts/tv_sync.py --symbol EURUSD --exchange OANDA \
    --timeframes M15,H1 --bars 5000 --db tv_data.db
"""

import argparse
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

_TF = {
    "M1": "in_1_minute", "M5": "in_5_minute", "M15": "in_15_minute",
    "M30": "in_30_minute", "M45": "in_45_minute",
    "H1": "in_1_hour", "H4": "in_4_hour",
    "D": "in_daily", "W": "in_weekly",
}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--symbol", default="EURUSD")
    ap.add_argument("--exchange", default="OANDA")
    ap.add_argument("--timeframes", default="M15,H1")
    ap.add_argument("--bars", type=int, default=5000)
    ap.add_argument("--db", default="tv_data.db")
    args = ap.parse_args()

    from tvDatafeed import TvDatafeed, Interval
    tv = TvDatafeed()  # keyless — public symbols only

    con = sqlite3.connect(args.db)
    con.execute(
        "CREATE TABLE IF NOT EXISTS market_data ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT,"
        "timestamp DATETIME NOT NULL, symbol TEXT NOT NULL,"
        "timeframe TEXT NOT NULL, open REAL, high REAL, low REAL,"
        "close REAL, volume REAL,"
        "UNIQUE(symbol, timeframe, timestamp))")
    for tf in args.timeframes.split(","):
        iv = getattr(Interval, _TF[tf.strip()])
        df = tv.get_hist(symbol=args.symbol, exchange=args.exchange,
                         interval=iv, n_bars=args.bars)
        if df is None or df.empty:
            print(f"{tf}: no data returned")
            continue
        ins = 0
        for idx, r in df.iterrows():
            ts = idx.tz_convert("UTC") if idx.tzinfo else idx
            con.execute(
                "INSERT OR REPLACE INTO market_data "
                "(timestamp, symbol, timeframe, open, high, low,"
                " close, volume) VALUES (?,?,?,?,?,?,?,?)",
                (ts.strftime("%Y-%m-%dT%H:%M:%S+00:00"),
                 args.symbol, tf.strip(),
                 float(r.open), float(r.high), float(r.low),
                 float(r.close), float(r.volume or 0.0)))
            ins += 1
        con.commit()
        print(f"{tf}: {ins} bars -> {args.db} "
              f"({df.index[0]} .. {df.index[-1]})")
    con.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
