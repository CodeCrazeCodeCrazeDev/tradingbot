"""Sentiment provisioning — real published sentiment metrics into
``sentiment_history.db`` (which has the schema but zero rows).

Sources are real, public, and require no credentials:

- alternative.me Fear & Greed Index (crypto market sentiment)

Every row records its source and method. Scope is honest: this covers
crypto market sentiment; FX macro sentiment has no free public feed and
is reported as unprovisioned, not faked.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def fetch_fng() -> list:
    url = "https://api.alternative.me/fng/?limit=10"
    req = urllib.request.Request(
        url, headers={"User-Agent": "sentiment-collector/1.0"})
    d = json.loads(urllib.request.urlopen(req, timeout=20).read())
    rows = []
    for e in d.get("data", []):
        val = float(e["value"])  # 0 extreme fear .. 100 extreme greed
        rows.append({
            "source": "alternative_me_fng",
            "symbol": "CRYPTO_MARKET",
            "sentiment_score": (val - 50.0) / 50.0,  # -1..+1
            "confidence": 0.8,
            "impact_weight": 1.0,
            "timestamp": datetime.fromtimestamp(
                int(e["timestamp"]), tz=timezone.utc).isoformat(),
            "raw_data": json.dumps(e),
            "keywords": e.get("value_classification", ""),
        })
    return rows


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="sentiment_history.db")
    args = ap.parse_args()
    rows = fetch_fng()
    con = sqlite3.connect(ROOT / args.db)
    n = 0
    for r in rows:
        con.execute(
            "INSERT INTO sentiment_history (source, symbol, "
            "sentiment_score, confidence, impact_weight, timestamp, "
            "raw_data, keywords) VALUES (?,?,?,?,?,?,?,?)",
            (r["source"], r["symbol"], r["sentiment_score"],
             r["confidence"], r["impact_weight"], r["timestamp"],
             r["raw_data"], r["keywords"]))
        n += 1
    con.commit()
    total = con.execute(
        "SELECT COUNT(*) FROM sentiment_history").fetchone()[0]
    con.close()
    print(f"inserted {n} real sentiment rows; table now {total}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
