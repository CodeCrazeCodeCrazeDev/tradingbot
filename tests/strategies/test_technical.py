"""Tests for the canonical lightweight indicators in strategies.technical."""

import numpy as np

from trading_bot.strategies.technical import wilder_rsi


def _reference_rsi(prices, period):
    """Independent list-based implementation of the same Wilder definition."""
    n = len(prices)
    out = [0.0] * n
    if n < period + 1:
        return np.array(out)
    deltas = [prices[i] - prices[i - 1] for i in range(1, n)]
    gains = [d if d > 0 else 0.0 for d in deltas]
    losses = [-d if d < 0 else 0.0 for d in deltas]
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period
    out[period] = 100.0 if avg_loss == 0 else 100.0 - 100.0 / (1.0 + avg_gain / avg_loss)
    for i in range(period + 1, n):
        avg_gain = (avg_gain * (period - 1) + gains[i - 1]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i - 1]) / period
        out[i] = 100.0 if avg_loss == 0 else 100.0 - 100.0 / (1.0 + avg_gain / avg_loss)
    return np.array(out)


def test_hand_computed_values():
    # prices 1,2,1,2,1 with period 2:
    #   out[2]: avg_gain=avg_loss=0.5 -> rs=1 -> 50
    #   out[3]: avg_gain=0.75, avg_loss=0.25 -> rs=3 -> 75
    #   out[4]: avg_gain=0.375, avg_loss=0.625 -> rs=0.6 -> 37.5
    np.testing.assert_allclose(
        wilder_rsi(np.array([1.0, 2.0, 1.0, 2.0, 1.0]), 2),
        np.array([0.0, 0.0, 50.0, 75.0, 37.5]),
    )


def test_matches_reference_on_synthetic_series():
    rng = np.random.RandomState(7)
    prices = 1.1 * np.exp(np.cumsum(rng.normal(0.0, 0.003, 200)))
    np.testing.assert_allclose(
        wilder_rsi(prices, 14), _reference_rsi(prices.tolist(), 14),
        rtol=1e-12, atol=1e-12,
    )


def test_insufficient_history_returns_zeros():
    prices = np.linspace(1.0, 1.1, 10)
    np.testing.assert_array_equal(wilder_rsi(prices, 14), np.zeros(10))


def test_monotonic_rise_saturates_at_100():
    prices = np.linspace(1.0, 2.0, 30)
    assert wilder_rsi(prices, 14)[-1] == 100.0


def test_monotonic_fall_saturates_at_0():
    prices = np.linspace(2.0, 1.0, 30)
    assert wilder_rsi(prices, 14)[-1] == 0.0


def test_range_bounds():
    rng = np.random.RandomState(3)
    prices = 100.0 + np.cumsum(rng.normal(0.0, 1.0, 300))
    rsi = wilder_rsi(prices, 14)
    assert np.all(rsi[14:] >= 0.0)
    assert np.all(rsi[14:] <= 100.0)


def test_enrichment_path_uses_last_value():
    """Mirror unified_bot.enrich_observation: only the final value is consumed."""
    prices = np.linspace(1.1, 1.2, 15)
    assert wilder_rsi(prices, 14)[-1] == 100.0  # strictly rising -> overbought reachable
