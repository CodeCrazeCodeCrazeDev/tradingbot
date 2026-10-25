"""Offline-RL policy lifecycle: train -> validate -> gate -> deploy ->
monitor -> rollback.

Each advisory RL learner (``AdaptiveDecisionRL``, ``AdaptiveSpreadRL``,
…) logs its resolved transitions to ``agent.experience_log`` as
``(state, action, reward, ts)``. The lifecycle periodically:

1. Fits a CANDIDATE Q-table offline on the log's head (oldest 80%),
   with a lower-confidence-bound penalty so under-visited
   (state, action) pairs score pessimistically, not optimistically.
2. Evaluates candidate AND incumbent on the held-out tail via
   action-matching off-policy evaluation: the policy earns a logged
   reward only where its greedy action equals the logged action —
   a coarse but honest OPE proxy.
3. Applies the safety gate: minimum holdout coverage, CVaR(5%) floor,
   max-drawdown cap, improvement margin over the incumbent.
4. Deploys ONLY on a pass — swapping the agent's live Q-table and
   persisting through its existing atomic checkpoint path. The
   previous table is retained as the rollback target.
5. Monitors a rolling window of post-deployment rewards; >20%
   degradation vs the deploy-time holdout mean auto-rolls back.

Authority boundary: this only decides WHICH Q-table an advisory voter
carries. Every proposal still traverses the canonical
CSC -> verification -> risk -> shield -> governance pipeline.
"""

from __future__ import annotations

import logging
import math
import os
from collections import deque
from statistics import mean, pstdev
from typing import Any, Deque, Dict, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)


def _env_f(name: str, default: float) -> float:
    try:
        return float(os.environ.get(name, str(default)))
    except ValueError:
        return default


def _env_i(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, str(default)))
    except ValueError:
        return default


def _cvar(rewards, alpha: float = 0.05) -> float:
    """Expected shortfall — mean of the worst ``alpha`` fraction."""
    if not rewards:
        return 0.0
    srt = sorted(rewards)
    k = max(1, int(len(srt) * alpha))
    return mean(srt[:k])


def _max_drawdown(rewards) -> float:
    """Worst peak-to-trough decline of the cumulative reward path."""
    peak = run = mdd = 0.0
    for r in rewards:
        run += r
        peak = max(peak, run)
        mdd = max(mdd, peak - run)
    return mdd


class PolicyLifecycle:
    """Safety-gated lifecycle manager for one advisory RL agent.

    The agent must be a ``_TabularQ`` subclass carrying
    ``experience_log`` (i.e. a ``_DeferredLearner``)."""

    def __init__(self, agent: Any, name: str) -> None:
        self.agent = agent
        self.name = name
        self.min_train = _env_i("TB_POLICY_MIN_TRAIN", 200)
        self.min_holdout = _env_i("TB_POLICY_MIN_HOLDOUT", 40)
        self.holdout_frac = _env_f("TB_POLICY_HOLDOUT_FRAC", 0.2)
        self.epochs = _env_i("TB_POLICY_EPOCHS", 3)
        self.lcb_penalty = _env_f("TB_POLICY_LCB", 0.25)
        self.cvar_floor = _env_f("TB_POLICY_CVAR_FLOOR", -0.02)
        self.max_dd = _env_f("TB_POLICY_MAX_DD", 0.5)
        self.improvement_margin = _env_f("TB_POLICY_IMPROVE", 0.10)
        self.rollback_window = _env_i("TB_POLICY_ROLLBACK_WINDOW", 100)
        self.rollback_degradation = _env_f("TB_POLICY_ROLLBACK_DD", 0.20)

        self._deployed_since = 0           # total-seen at last deploy
        self._backup: Optional[Dict[Tuple, np.ndarray]] = None
        self._baseline_mean = 0.0          # holdout mean at deploy
        self.rolling: Deque[float] = deque(maxlen=self.rollback_window)
        self._seen = 0                     # deque index consumed
        self._total_seen = 0               # monotonic — deque maxlen
        # wraparound drops oldest rows but len() stays capped; index-
        # based gates would freeze at 8192 forever.

        self.deploys = 0
        self.rollbacks = 0
        self.rejected_candidates = 0
        self.last_gate_reason = "no_data"

    # ------------------------------------------------------------------
    # Offline training + action-matching OPE
    # ------------------------------------------------------------------
    def _train_candidate(self, train) -> Dict[Tuple, np.ndarray]:
        """Conservative offline Q: replay the log ``epochs`` times, then
        subtract an LCB penalty inversely proportional to sqrt(visits)
        so thinly-sampled cells are pessimistic."""
        table: Dict[Tuple, np.ndarray] = {}
        visits: Dict[Tuple, int] = {}
        a, g = self.agent.alpha, self.agent.gamma
        for _ in range(self.epochs):
            for rec in train:
                s, act, r = rec[0], rec[1], rec[2]
                if not (isinstance(act, (int, np.integer))
                        and math.isfinite(r)):
                    continue
                row = table.setdefault(
                    s, np.zeros(self.agent.n_actions, dtype=float))
                row[act] += a * (r - row[act])       # bandit target
                visits[(s, act)] = visits.get((s, act), 0) + 1
        for s, row in table.items():
            for act in range(len(row)):
                n = visits.get((s, act), 0)
                row[act] -= self.lcb_penalty / max(1.0, math.sqrt(n))
        return table

    @staticmethod
    def _greedy(row) -> int:
        return int(np.argmax(row))

    def _evaluate(self, table: Dict[Tuple, np.ndarray],
                  holdout) -> Dict[str, float]:
        """OPE on logged transitions. When a transition carries the
        full counterfactual reward vector (5-tuple: every action's
        reward is exact because _reward is pure), score the policy's
        greedy pick DIRECTLY — full-coverage eval, no matching needed.
        Falls back to action-matching for legacy 4-tuples."""
        matched = []
        for rec in holdout:
            s, act, r = rec[0], rec[1], rec[2]
            cf = rec[4] if len(rec) > 4 else None
            row = table.get(s)
            if row is None:
                continue
            if isinstance(cf, dict) and cf:
                pick = self._greedy(row)
                if pick in cf:
                    matched.append(cf[pick])
            elif self._greedy(row) == act:
                matched.append(r)
        sd = pstdev(matched) if len(matched) > 1 else 0.0
        return {
            "n": float(len(matched)),
            "mean": mean(matched) if matched else 0.0,
            "sharpe": (mean(matched) / sd) if sd > 0 else 0.0,
            "cvar5": _cvar(matched, 0.05),
            "max_dd": _max_drawdown(matched),
        }

    def _gate(self, cand: Dict[str, float], inc: Dict[str, float],
              n_holdout: int) -> Tuple[bool, str]:
        if n_holdout < self.min_holdout:
            return False, "holdout_undersampled"
        if cand["n"] < self.min_holdout:
            return False, "candidate_no_action_match"
        if cand["cvar5"] < self.cvar_floor:
            return False, f"cvar5_{cand['cvar5']:.4f}<{self.cvar_floor}"
        if cand["max_dd"] > self.max_dd:
            return False, f"max_dd_{cand['max_dd']:.4f}>{self.max_dd}"
        if inc["n"] >= self.min_holdout and cand["mean"] < (
                inc["mean"] * (1.0 + self.improvement_margin)):
            return False, "no_improvement_over_incumbent"
        return True, "pass"

    # ------------------------------------------------------------------
    # Lifecycle step — cheap no-op when nothing new has resolved
    # ------------------------------------------------------------------
    def maybe_update(self) -> Optional[str]:
        log = self.agent.experience_log
        if self._seen > len(log) or (
                len(log) == log.maxlen and self._seen >= len(log)):
            # deque wrapped — rescan the tail; a few entries may
            # re-count but the monitor stays honest and live.
            self._seen = max(0, len(log) - self.rollback_window)
            self.rolling.clear()
        while self._seen < len(log):
            self.rolling.append(log[self._seen][2])
            self._seen += 1
            self._total_seen += 1

        # Rollback monitor: needs a deployed policy + full window.
        if self._backup is not None and \
                len(self.rolling) == self.rollback_window:
            base, cur = self._baseline_mean, mean(self.rolling)
            if abs(base) > 1e-9 and \
                    cur < base * (1.0 - self.rollback_degradation):
                self._rollback(f"rolling_mean {cur:.4f} vs base {base:.4f}")
                return "rolled_back"

        if len(log) < self.min_train + self.min_holdout:
            self.last_gate_reason = "insufficient_data"
            return None
        if self._total_seen - self._deployed_since < self.min_train:
            self.last_gate_reason = "no_new_data"
            return None

        n_hold = max(self.min_holdout,
                     int(len(log) * self.holdout_frac))
        seq = list(log)
        train, holdout = seq[:-n_hold], seq[-n_hold:]

        cand_table = self._train_candidate(train)
        cand_m = self._evaluate(cand_table, holdout)
        inc_m = self._evaluate(self.agent._q, holdout)

        ok, reason = self._gate(cand_m, inc_m, len(holdout))
        self.last_gate_reason = reason
        if not ok:
            self.rejected_candidates += 1
            return None

        self._deploy(cand_table, cand_m)
        return "deployed"

    def _deploy(self, table: Dict[Tuple, np.ndarray],
                metrics: Dict[str, float]) -> None:
        self._backup = {s: arr.copy() for s, arr in self.agent._q.items()}
        self.agent._q = {s: arr.copy() for s, arr in table.items()}
        self._deployed_since = self._total_seen
        self._baseline_mean = metrics["mean"]
        self.rolling.clear()
        self.agent.save()
        self.deploys += 1
        logger.info(
            "policy_lifecycle %s DEPLOYED candidate (n=%.0f mean=%.4f "
            "cvar5=%.4f sharpe=%.2f)", self.name, metrics["n"],
            metrics["mean"], metrics["cvar5"], metrics["sharpe"])

    def _rollback(self, reason: str) -> None:
        if self._backup is None:
            return
        self.agent._q = self._backup
        self._backup = None
        self._deployed_since = 0
        self.rolling.clear()
        self.agent.save()
        self.rollbacks += 1
        logger.warning(
            "policy_lifecycle %s ROLLED BACK: %s", self.name, reason)

    def status(self) -> Dict[str, Any]:
        return {
            "deploys": self.deploys,
            "rollbacks": self.rollbacks,
            "rejected_candidates": self.rejected_candidates,
            "last_gate_reason": self.last_gate_reason,
            "has_backup": self._backup is not None,
            "rolling_n": len(self.rolling),
        }
