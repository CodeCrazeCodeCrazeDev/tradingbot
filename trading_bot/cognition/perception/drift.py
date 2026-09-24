"""Online distribution-drift detection (hostile-audit recommendation).

Page-Hinkley is the deterministic, parameter-light CUSUM-style detector:
it alarms when the cumulative deviation of a stream (e.g. per-bar returns)
from its running mean exceeds a threshold — i.e. the market's data-generating
process has shifted and learned state estimates may be stale.
"""

import math
from typing import Optional


class PageHinkley:
    """Page-Hinkley drift detector over a scalar stream.

    update(x) -> True when drift is detected. `statistic` exposes the current
    PH value for monitoring/calibration dashboards.
    """

    def __init__(self, delta: float = 0.0001, threshold: float = 0.02, min_observations: int = 30):
        self.delta = delta
        self.threshold = threshold
        self.min_observations = min_observations
        self.reset()

    def reset(self) -> None:
        self.n = 0
        self._mean = 0.0
        self._cum = 0.0
        self._min_cum = 0.0
        self.statistic = 0.0
        self.detected = False
        self.detection_index: int = -1

    def update(self, x: float) -> bool:
        x = float(x)
        self.n += 1
        self._mean += (x - self._mean) / self.n
        self._cum += x - self._mean - self.delta
        self._min_cum = min(self._min_cum, self._cum)
        self.statistic = self._cum - self._min_cum

        if self.n >= self.min_observations and self.statistic > self.threshold:
            if not self.detected:
                self.detected = True
                self.detection_index = self.n
            return True
        return False


class DriftMonitor:
    """Per-instrument drift monitoring facade for the brain.

    With ``standardize=True`` (default) the stream is normalized by its own
    running standard deviation before Page-Hinkley — raw PH thresholds are
    absolute-unit and cannot fire on real return scales (~1e-4 for FX).
    PH params then live in sigma units (delta=0.5, threshold=3.0 ≈ a
    sustained half-sigma mean shift).
    """

    def __init__(self, standardize: Optional[bool] = None, stats_warmup: int = 20, **ph_kwargs):
        self._detectors: dict = {}
        self._stats: dict = {}  # instrument -> (n, mean, M2)
        # Auto: standardize unless the caller passed explicit PH params —
        # absolute-unit thresholds (delta/threshold) imply raw-unit control.
        self.standardize = (not ph_kwargs) if standardize is None else standardize
        self.stats_warmup = stats_warmup
        if self.standardize and not ph_kwargs:
            ph_kwargs = {"delta": 0.5, "threshold": 4.0}
        self._ph_kwargs = ph_kwargs

    def _zscore(self, instrument: str, x: float) -> float:
        n, mean, m2 = self._stats.get(instrument, (0, 0.0, 0.0))
        n += 1
        delta = x - mean
        mean += delta / n
        m2 += delta * (x - mean)
        self._stats[instrument] = (n, mean, m2)
        # Neutral until the baseline stabilizes — tiny-sample std produces
        # spurious z-scores that contaminate the PH cumulative sum.
        if n < self.stats_warmup or m2 <= 0:
            return 0.0
        std = math.sqrt(m2 / (n - 1))
        return (x - mean) / std if std > 0 else 0.0

    def update(self, instrument: str, value: float) -> bool:
        det = self._detectors.get(instrument)
        if det is None:
            det = self._detectors[instrument] = PageHinkley(**self._ph_kwargs)
        x = self._zscore(instrument, value) if self.standardize else value
        return det.update(x)

    def is_drifting(self, instrument: str) -> bool:
        det = self._detectors.get(instrument)
        return bool(det and det.detected)

    def statistic(self, instrument: str) -> float:
        det = self._detectors.get(instrument)
        return det.statistic if det else 0.0
