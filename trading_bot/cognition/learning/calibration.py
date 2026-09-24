"""Probability calibration for the cognitive decision layer.

Implements the hostile-audit recommendation (isotonic / Platt scaling) plus
an online ECE tracker. The brain's raw ``win_probability`` is a heuristic —
this module maps it toward empirical frequencies as outcomes arrive.

Usage:
    cal = ProbabilityCalibrator()
    p_cal = cal.predict(raw_win_prob)
    ...later, when the trade resolves...
    cal.update(raw_win_prob, realized_win_bool)
    cal.expected_calibration_error()  # ECE over the sample buffer
"""

import math
from collections import deque
from typing import Deque, Dict, List, Optional, Tuple

_MIN_SAMPLES_PLATT = 10
_MIN_SAMPLES_ISOTONIC = 30


def _sigmoid(z: float) -> float:
    if z >= 0:
        return 1.0 / (1.0 + math.exp(-z))
    ez = math.exp(z)
    return ez / (1.0 + ez)


def _logit(p: float) -> float:
    p = min(max(p, 1e-6), 1.0 - 1e-6)
    return math.log(p / (1.0 - p))


class PlattCalibrator:
    """Online Platt scaling: logistic regression over logit(raw_p).

    Learns (a, b) in  p_cal = sigmoid(a * logit(p) + b)  via SGD.
    """

    def __init__(self, lr: float = 0.05):
        self.a = 1.0
        self.b = 0.0
        self.lr = lr
        self.n_updates = 0

    def predict(self, p: float) -> float:
        return _sigmoid(self.a * _logit(p) + self.b)

    def update(self, p: float, y: float) -> None:
        x = _logit(p)
        pred = self.predict(p)
        err = pred - y
        # SGD on cross-entropy
        self.a -= self.lr * err * x
        self.b -= self.lr * err
        self.n_updates += 1


class IsotonicCalibrator:
    """Isotonic regression via Pool Adjacent Violators on a sample buffer."""

    def __init__(self, buffer_size: int = 500):
        self.samples: Deque[Tuple[float, float]] = deque(maxlen=buffer_size)
        self._map: List[Tuple[float, float]] = []  # sorted (p, y_iso)
        self._dirty = True

    def update(self, p: float, y: float) -> None:
        self.samples.append((float(p), float(y)))
        self._dirty = True

    def _rebuild(self) -> None:
        # Pool by unique p first — per-sample blocks make PAV leave the top
        # knot as a lone y=1 point (ties sort before ones), corrupting the map.
        acc: Dict[float, List[float]] = {}
        for p, y in self.samples:
            e = acc.setdefault(p, [0.0, 0.0])
            e[0] += y
            e[1] += 1.0
        pts = sorted((p, s / w, w) for p, (s, w) in acc.items())
        # PAV on (sum_y, weight) blocks
        blocks: List[List[float]] = [[y * w, w, p, p] for p, y, w in pts]
        i = 0
        while i < len(blocks) - 1:
            if blocks[i][0] / blocks[i][1] > blocks[i + 1][0] / blocks[i + 1][1]:
                merged = [
                    blocks[i][0] + blocks[i + 1][0],
                    blocks[i][1] + blocks[i + 1][1],
                    blocks[i][2],
                    blocks[i + 1][3],
                ]
                blocks[i:i + 2] = [merged]
                if i > 0:
                    i -= 1
            else:
                i += 1
        self._map = [(b[3], b[0] / b[1]) for b in blocks]
        self._map.sort()
        self._dirty = False

    def predict(self, p: float) -> float:
        if not self.samples:
            return p
        if self._dirty:
            self._rebuild()
        # piecewise-constant lookup: nearest knot at-or-below p, else first
        best = self._map[0][1]
        for knot, val in self._map:
            if knot <= p:
                best = val
            else:
                break
        return best


class ProbabilityCalibrator:
    """Composite calibrator: identity → Platt → isotonic as data accrues."""

    def __init__(self, buffer_size: int = 500):
        self.platt = PlattCalibrator()
        self.isotonic = IsotonicCalibrator(buffer_size)
        self._history: Deque[Tuple[float, float]] = deque(maxlen=buffer_size)

    def predict(self, raw_p: float) -> float:
        n = len(self._history)
        if n >= _MIN_SAMPLES_ISOTONIC:
            return self.isotonic.predict(raw_p)
        if n >= _MIN_SAMPLES_PLATT:
            return self.platt.predict(raw_p)
        return raw_p  # not enough data to calibrate honestly

    def update(self, raw_p: float, outcome: float) -> None:
        """Record a realized binary outcome (1.0 = prediction correct)."""
        y = 1.0 if outcome else 0.0
        self._history.append((raw_p, y))
        self.platt.update(raw_p, y)
        self.isotonic.update(raw_p, y)

    def expected_calibration_error(self, n_bins: int = 10) -> float:
        """ECE over recorded samples using *calibrated* probabilities."""
        if not self._history:
            return 0.0
        bins = [[] for _ in range(n_bins)]
        for p, y in self._history:
            cal = self.predict(p)
            bins[min(n_bins - 1, int(cal * n_bins))].append((cal, y))
        ece = 0.0
        total = len(self._history)
        for b in bins:
            if not b:
                continue
            acc = sum(y for _, y in b) / len(b)
            conf = sum(c for c, _ in b) / len(b)
            ece += (len(b) / total) * abs(acc - conf)
        return round(ece, 4)

    @property
    def sample_count(self) -> int:
        return len(self._history)
