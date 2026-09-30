"""Dependency-light technical indicators shared by the canonical runtime.

``trading_bot.indicators.vectorized_indicators`` provides numba-JIT variants,
but importing it costs ~15s (numba+pandas) — too heavy for the unified bot's
hot enrichment path and for replay tests. These pure-NumPy implementations
are the canonical lightweight equivalents; they follow the same Wilder
smoothing convention as ``rsi_fast`` so runtime enrichment and any causal
replay produce identical values.
"""

from __future__ import annotations

import numpy as np


def wilder_rsi(prices: np.ndarray, period: int = 14) -> np.ndarray:
    """RSI via Wilder smoothing — bit-compatible with ``rsi_fast``.

    Returns a zero-padded array: entries before ``period`` carry no signal.
    For ``len(prices) <= period`` the result is all zeros (insufficient data).
    """
    prices = np.asarray(prices, dtype=np.float64)
    n = prices.shape[0]
    rsi = np.zeros(n)
    if period < 1 or n < period + 1:
        return rsi

    deltas = np.diff(prices)
    gains = np.where(deltas > 0, deltas, 0.0)
    losses = np.where(deltas < 0, -deltas, 0.0)

    avg_gain = float(np.mean(gains[:period]))
    avg_loss = float(np.mean(losses[:period]))

    rsi[period] = 100.0 if avg_loss == 0 else 100.0 - (100.0 / (1.0 + avg_gain / avg_loss))
    for i in range(period + 1, n):
        avg_gain = (avg_gain * (period - 1) + gains[i - 1]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i - 1]) / period
        rsi[i] = 100.0 if avg_loss == 0 else 100.0 - (100.0 / (1.0 + avg_gain / avg_loss))

    return rsi
