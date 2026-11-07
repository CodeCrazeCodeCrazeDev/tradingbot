"""DiscoLoop coupled discrete-continuous state tracker (arXiv:2607.00341).

The reasoning recurrence emits, per transition, a discrete entity index
(the argmax dimension the latent locks onto — the loop's current
'subgoal') and a continuous hidden state. This tracker couples the two
channels into observable state:

- discrete: active entity, dwell time, churn over a sliding window
- continuous: EMA of per-step latent drift (mean |h_t - h_{t-1}|), plus a
  signed drift EMA so net displacement can be separated from gross motion
- coherence: a fragility flag for the fragmentation failure mode —
  discrete churn while the latent is barely moving (the discrete channel
  detached from the dynamics), or high gross latent motion with low net
  displacement while the discrete channel is frozen (oscillating,
  unresolved latent updates never settling into a discrete claim). Both
  are localized representation errors the gap matrix calls out.

Evidence-only: the snapshot feeds advisory_report and derived
observation features; it carries no authority over decisions.
"""

from collections import deque
from typing import Any, Dict, Optional

import numpy as np


class DiscoLoopTracker:
    """Tracks the coupled discrete/continuous state of a DiscoLoopCell
    recurrence across transitions."""

    def __init__(self, drift_alpha: float = 0.2, window: int = 64):
        self.drift_alpha = float(drift_alpha)
        self.window = int(window)
        self.seq = 0                       # transitions observed
        self.entity: Optional[int] = None  # active discrete subgoal
        self.dwell = 0                     # steps on current entity
        self.entity_changes = 0            # discrete transitions total
        self.drift = 0.0                   # EMA of mean |Δh| per step
        self.net_drift = 0.0               # EMA of signed mean Δh
        self.fragile = False               # coherence flag
        self._prev: Optional[np.ndarray] = None
        self._recent: deque = deque(maxlen=self.window)
        self._recent_drift: deque = deque(maxlen=self.window)

    def step(self, entity_idx: int, hidden: np.ndarray) -> None:
        """Record one loop transition: discrete entity + continuous state."""
        h = np.asarray(hidden, dtype=np.float64).ravel()
        d = (float(np.mean(np.abs(h - self._prev)))
             if self._prev is not None else 0.0)
        s = (float(np.mean(h - self._prev))
             if self._prev is not None else 0.0)
        self._prev = h
        self.seq += 1
        self.drift += self.drift_alpha * (d - self.drift)
        self.net_drift += self.drift_alpha * (s - self.net_drift)

        entity_idx = int(entity_idx)
        if entity_idx != self.entity:
            # Only transitions after the first lock count as changes —
            # assigning the initial entity is acquisition, not churn.
            if self.entity is not None:
                self.entity_changes += 1
            self.entity = entity_idx
            self.dwell = 1
        else:
            self.dwell += 1
        self._recent.append(entity_idx)
        self._recent_drift.append(d)
        self.fragile = self.evaluate_coherence(
            recent_drift=float(np.mean(self._recent_drift)))

    # -- coherence --------------------------------------------------------

    def _window_stats(self) -> Dict[str, float]:
        ents = list(self._recent)
        if not ents:
            return {"churn": 0.0, "n": 0}
        return {"churn": len(set(ents)) / len(ents), "n": len(ents)}

    def evaluate_coherence(self, recent_drift: float) -> bool:
        """Fragmentation check over the sliding window.

        - churn > 0.5 while recent drift is under half the running EMA:
          the discrete channel is flipping entities without latent change.
        - churn < 0.1 over a mature window while recent gross motion
          exceeds twice the net displacement EMA: the latent oscillates
          without settling — updates churn in place but never resolve
          into a new discrete claim. Motion with real net displacement
          (steady latent evolution under a stable entity) does not flag.
        """
        st = self._window_stats()
        if st["n"] < 8:
            return False
        baseline = max(self.drift, 1e-9)
        net = max(abs(self.net_drift), 1e-9)
        detached = st["churn"] > 0.5 and recent_drift < 0.5 * baseline
        unresolved = (st["churn"] < 0.1 and st["n"] >= 16
                      and recent_drift > 2.0 * net)
        return bool(detached or unresolved)

    def snapshot(self) -> Dict[str, Any]:
        st = self._window_stats()
        return {
            "seq": self.seq,
            "entity": self.entity,
            "dwell": self.dwell,
            "entity_changes": self.entity_changes,
            "churn_window": round(st["churn"], 3),
            "drift_ema": round(self.drift, 6),
            "net_drift_ema": round(self.net_drift, 6),
            "fragile": bool(self.fragile),
        }
