"""Deterministic synthetic OHLCV generator for RSI engineering tests.

Produces reproducible multi-instrument, multi-regime price histories so the
recursive self-improvement evaluation pipeline can be exercised without real
market data. Results computed on these series are *engineering* evidence
only: a planted oscillation that a parameter happens to harvest is a test
fixture, not market alpha.

A ``PlantedPattern`` (sine oscillation in log-return space) creates a known,
checkable edge that a mean-reversion lookback near half the period will
capture; tests assert the pipeline *detects and gates* candidates on such
fixtures, not that trading improves.
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Mapping, Optional, Protocol, Sequence, Tuple

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class RegimeSpec:
    """One contiguous block of a synthetic series."""

    name: str                      # trend | mean_revert | high_vol | crash | flat
    n_bars: int
    drift: float = 0.0             # per-bar log drift
    vol: float = 0.001             # per-bar shock stddev (log space)
    ar1: float = 0.0               # shock autocorrelation (<0 mean-reverts)
    sine_amp: float = 0.0          # deterministic oscillation amplitude
    sine_period: int = 10          # oscillation period in bars


@dataclass(frozen=True)
class SyntheticMarketSpec:
    seed: int
    instruments: Tuple[str, ...]
    regimes: Tuple[RegimeSpec, ...]
    base_price: float = 1.10
    intra_vol_frac: float = 0.6    # high/low wick size as fraction of vol
    base_volume: float = 1000.0

    @property
    def n_bars(self) -> int:
        return sum(r.n_bars for r in self.regimes)


def fingerprint(frame: pd.DataFrame) -> str:
    """SHA-256 over the canonical serialisation of an OHLCV frame."""
    canon = frame[["timestamp", "open", "high", "low", "close", "volume"]].copy()
    canon = canon.round(10)
    payload = canon.to_csv(index=False).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def fingerprint_all(frames: Mapping[str, pd.DataFrame]) -> str:
    """Stable dataset hash across an instrument -> frame mapping."""
    payload = json.dumps(
        {k: fingerprint(v) for k, v in sorted(frames.items())},
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


class SyntheticMarketGenerator:
    """Generates deterministic OHLCV frames from a spec and seed."""

    def __init__(self, spec: SyntheticMarketSpec) -> None:
        if not spec.instruments or spec.n_bars < 3:
            raise ValueError("need at least one instrument and three bars")
        self.spec = spec

    def _instrument_seed(self, symbol: str) -> int:
        digest = hashlib.sha256(f"{self.spec.seed}:{symbol}".encode()).digest()
        return int.from_bytes(digest[:8], "big")

    def _shocks(self, rng: np.random.Generator) -> np.ndarray:
        """Per-bar log returns across all regimes."""
        pieces: List[np.ndarray] = []
        offset = 0
        prev = 0.0
        for regime in self.spec.regimes:
            eps = rng.normal(0.0, regime.vol, size=regime.n_bars)
            rets = np.empty(regime.n_bars, dtype=float)
            for i in range(regime.n_bars):
                shock = eps[i] + regime.ar1 * prev
                t = offset + i
                osc = (
                    regime.sine_amp * math.sin(2.0 * math.pi * t / regime.sine_period)
                    if regime.sine_period > 0
                    else 0.0
                )
                rets[i] = regime.drift + shock + osc
                prev = shock
            pieces.append(rets)
            offset += regime.n_bars
        return np.concatenate(pieces)

    def generate_instrument(self, symbol: str) -> pd.DataFrame:
        rng = np.random.default_rng(self._instrument_seed(symbol))
        rets = self._shocks(rng)
        n = len(rets)
        closes = self.spec.base_price * np.exp(np.cumsum(rets))
        opens = np.empty(n)
        opens[0] = self.spec.base_price
        opens[1:] = closes[:-1]
        vols = np.abs(rets)
        wick = np.maximum(vols, 1e-8) * self.spec.intra_vol_frac + 1e-9
        highs = np.maximum(opens, closes) * np.exp(np.abs(rng.normal(0.0, wick)))
        lows = np.minimum(opens, closes) * np.exp(-np.abs(rng.normal(0.0, wick)))
        volumes = np.full(n, self.spec.base_volume) * np.exp(
            rng.normal(0.0, 0.05, size=n)
        )
        return pd.DataFrame(
            {
                "timestamp": np.arange(n, dtype=float),
                "open": opens,
                "high": highs,
                "low": lows,
                "close": closes,
                "volume": volumes,
            }
        )

    def generate(self) -> Dict[str, pd.DataFrame]:
        return {s: self.generate_instrument(s) for s in self.spec.instruments}


class MarketHistorySource(Protocol):
    """Pluggable history provider: synthetic today, real data later."""

    def load(self) -> Dict[str, pd.DataFrame]:
        ...

    def dataset_hash(self) -> str:
        ...


class SyntheticSource:
    def __init__(self, spec: SyntheticMarketSpec) -> None:
        self._frames = SyntheticMarketGenerator(spec).generate()

    def load(self) -> Dict[str, pd.DataFrame]:
        return dict(self._frames)

    def dataset_hash(self) -> str:
        return fingerprint_all(self._frames)


class SqliteSource:
    """Adapter over the existing market_data.db (single-instrument today)."""

    def __init__(self, db_path: str, symbols: Sequence[str]) -> None:
        self.db_path = db_path
        self.symbols = tuple(symbols)
        self._frames: Optional[Dict[str, pd.DataFrame]] = None

    def load(self) -> Dict[str, pd.DataFrame]:
        if self._frames is None:
            import sqlite3

            frames: Dict[str, pd.DataFrame] = {}
            con = sqlite3.connect(self.db_path)
            try:
                for symbol in self.symbols:
                    df = pd.read_sql_query(
                        "SELECT timestamp, open, high, low, close, volume "
                        "FROM market_data WHERE symbol = ? ORDER BY timestamp",
                        con,
                        params=(symbol,),
                    )
                    if df.empty:
                        raise RuntimeError(f"no rows for {symbol} in {self.db_path}")
                    df["timestamp"] = np.arange(len(df), dtype=float)
                    frames[symbol] = df
            finally:
                con.close()
            self._frames = frames
        return dict(self._frames)

    def dataset_hash(self) -> str:
        return fingerprint_all(self.load())
