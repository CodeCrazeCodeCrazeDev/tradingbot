"""Regression: synthetic_observations must not crash for small --cycles.

The 8-regime spec used to compute a negative tail size
(n_bars - q*6 - max(4,q//2)) for n_bars < ~53, passing a negative
dimension to rng.normal. The block-truncation fix must keep every
RegimeSpec n_bars >= 1 for any window >= 8 bars.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.paper_runner import synthetic_observations  # noqa: E402


@pytest.mark.parametrize("n", [4, 8, 10, 40, 52, 53, 100, 200])
def test_synthetic_small_windows_generate(n):
    obs = list(synthetic_observations("EURUSD", n, seed=1))
    assert len(obs) == n
    assert all(o["close"] > 0 for o in obs)


def test_synthetic_below_generator_minimum_raises():
    with pytest.raises(ValueError):
        list(synthetic_observations("EURUSD", 2, seed=1))
