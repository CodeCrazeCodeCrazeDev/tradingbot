"""
Time-Series DB
============================================================

Minimal SQLite-backed OHLCV store used by the legacy trading
system. Persists candles keyed by (symbol, timeframe, timestamp).
"""

import asyncio
import logging
import os
import sqlite3
from typing import Any, Dict, List, Optional

import pandas as pd

logger = logging.getLogger(__name__)


class TimeSeriesDB:
    """SQLite-backed time-series store for OHLCV data."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        config = config or {}
        self.db_path = config.get("path", "alphaalgo_data/time_series.db")
        os.makedirs(os.path.dirname(self.db_path) or ".", exist_ok=True)
        self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._conn.execute(
            """CREATE TABLE IF NOT EXISTS ohlcv (
                   symbol TEXT, timeframe TEXT, ts TEXT,
                   open REAL, high REAL, low REAL, close REAL, volume REAL,
                   PRIMARY KEY (symbol, timeframe, ts))"""
        )
        self._conn.commit()

    async def store(self, symbol: str, timeframe: str, data: Any) -> int:
        """Persist OHLCV rows (DataFrame or list of dicts)."""
        if isinstance(data, pd.DataFrame):
            rows = data.reset_index().to_dict("records")
        else:
            rows = list(data or [])
        n = 0
        for r in rows:
            ts = str(r.get("timestamp", r.get("time", r.get("ts", ""))))
            self._conn.execute(
                "INSERT OR REPLACE INTO ohlcv VALUES (?,?,?,?,?,?,?,?)",
                (symbol, timeframe, ts,
                 float(r.get("open", 0) or 0), float(r.get("high", 0) or 0),
                 float(r.get("low", 0) or 0), float(r.get("close", 0) or 0),
                 float(r.get("volume", 0) or 0)))
            n += 1
        self._conn.commit()
        return n

    async def fetch(self, symbol: str, timeframe: str, limit: int = 500) -> pd.DataFrame:
        cur = self._conn.execute(
            "SELECT ts, open, high, low, close, volume FROM ohlcv "
            "WHERE symbol=? AND timeframe=? ORDER BY ts DESC LIMIT ?",
            (symbol, timeframe, limit))
        rows = cur.fetchall()
        df = pd.DataFrame(rows, columns=["timestamp", "open", "high", "low", "close", "volume"])
        return df.iloc[::-1].reset_index(drop=True)

    def close(self) -> None:
        self._conn.close()
