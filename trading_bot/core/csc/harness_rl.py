"""Harness-policy optimization + stateful cognitive offloading for
the advisory RL learners. Three mechanisms, all advisory-only:

Self-HPO (H-step / P-step alternation)
    The "harness" is everything AROUND the policy: LCB penalty,
    replay epochs, holdout fraction — how the offline candidate is
    trained and judged, not the policy itself. A HarnessOptimizer
    maintains K harness candidates; each P-step trains a policy
    under its harness on the SAME experience log and scores it by
    action-matching OPE; the H-step promotes the best harness and
    regenerates the population by perturbation. Failures shape the
    next harness proposals (failure-guided, not random search).

EvoHarness-RL (cost-aware GRPO)
    Candidates are ranked by group-relative advantage:
        adv_i = (score_i - mean(scores)) / (std(scores) + eps)
        score_i = ope_mean_i - cost_weight * compute_i
    where compute_i = epochs * train_size — an honest proxy for the
    harness's real training cost. Absolute thresholds are inherited
    from the underlying lifecycle gate; GRPO only decides WHICH
    passing harness deploys.

Harness-1 (stateful cognitive offloading)
    WorkingMemory is an environment-side scratchpad: per-namespace
    bounded deques the agents write routine bookkeeping into (self-
    correction records, teacher-consult events, harness decisions)
    instead of carrying decision provenance inside the policy state.
    Optionally sinks to <RL_STATE_DIR>/harness_memory.jsonl so the
    scratchpad survives restarts and stays auditable.

Authority boundary: a winning harness may change HOW a candidate is
trained; only the gated deploy path in PolicyLifecycle may change
WHICH table an advisory voter carries.
"""

from __future__ import annotations

import json
import logging
import math
import os
import time
from collections import deque
from copy import deepcopy
from dataclasses import dataclass, field
from pathlib import Path
from statistics import mean, pstdev
from typing import Any, Deque, Dict, List, Optional, Tuple

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


# ---------------------------------------------------------------------
# Harness-1: environment-side working memory
# ---------------------------------------------------------------------
class WorkingMemory:
    """Bounded env-side scratchpad — decision bookkeeping lives OUTSIDE
    the policy, where it survives restarts and stays auditable."""

    _instances: Dict[str, "WorkingMemory"] = {}

    def __init__(self, namespace: str, maxlen: int = 512,
                 persist_path: Optional[Path] = None) -> None:
        self.namespace = namespace
        self._store: Dict[str, Deque[Dict[str, Any]]] = {}
        self._maxlen = maxlen
        self._persist = persist_path
        self.writes = 0
        self._persist_cap = _env_i("TB_WM_PERSIST_CAP", 4 << 20)

    @classmethod
    def get(cls, namespace: str, **kw) -> "WorkingMemory":
        if namespace not in cls._instances:
            cls._instances[namespace] = cls(namespace, **kw)
        return cls._instances[namespace]

    def write(self, key: str, record: Dict[str, Any]) -> None:
        rec = dict(record)
        rec["_ts"] = time.time()
        self._store.setdefault(key, deque(maxlen=self._maxlen)
                               ).append(rec)
        self.writes += 1
        if self._persist is not None:
            try:
                self._persist.parent.mkdir(parents=True, exist_ok=True)
                if (self._persist.exists()
                        and self._persist.stat().st_size
                        > self._persist_cap):
                    # Rotate: unbounded append-only growth is a disk
                    # leak on tight environments.
                    self._persist.replace(
                        self._persist.with_suffix(".jsonl.1"))
                with open(self._persist, "a", encoding="utf-8") as f:
                    f.write(json.dumps(
                        {"ns": self.namespace, "key": key,
                         "rec": rec}, default=str) + "\n")
            except OSError:
                pass

    def read(self, key: str, n: int = 0) -> List[Dict[str, Any]]:
        dq = self._store.get(key, ())
        items = list(dq)
        return items[-n:] if n else items


# ---------------------------------------------------------------------
# Self-HPO: harness candidates
# ---------------------------------------------------------------------
# The harness knobs a candidate may perturb — training scaffolding,
# never policy internals.
_HARNESS_SPACE = {
    "lcb_penalty": (0.05, 0.75),      # offline-training pessimism
    "epochs": (1, 6),                  # replay passes
    "holdout_frac": (0.10, 0.35),      # eval tail size
}


@dataclass
class HarnessCandidate:
    cfg: Dict[str, float]
    ope_mean: float = 0.0
    ope_n: int = 0
    compute: float = 0.0               # epochs * train_size proxy
    score: float = float("-inf")       # cost-adjusted
    advantage: float = 0.0             # GRPO group-relative
    evaluated: bool = False


class HarnessOptimizer:
    """Alternates H-step/P-step over a PolicyLifecycle.

    P-step: every candidate trains a policy on the same experience log
    under its own harness config and is scored by the lifecycle's OPE
    minus a compute-cost penalty.
    H-step: the best-scoring candidate's harness becomes active; the
    population regenerates by perturbing the winner, biased by which
    knob moved (failure-guided: losing directions shrink)."""

    def __init__(self, lifecycle, name: str,
                 population: int = None) -> None:
        self.lifecycle = lifecycle
        self.name = name
        self.population = population or _env_i(
            "TB_HPO_POPULATION", 4)
        self.cost_weight = _env_f("TB_HPO_COST_WEIGHT", 1e-4)
        self._rng_state = int(_env_f("TB_HPO_SEED", 7))
        self.candidates: List[HarnessCandidate] = []
        self.active_cfg: Dict[str, float] = {
            "lcb_penalty": lifecycle.lcb_penalty,
            "epochs": float(lifecycle.epochs),
            "holdout_frac": lifecycle.holdout_frac,
        }
        # Anchor: the ORIGINAL harness stays in every population so a
        # bad H-step can never strand the lifecycle on drifted knobs —
        # the population can always re-elect the baseline.
        self._base_cfg: Dict[str, float] = dict(self.active_cfg)
        self.generations = 0
        self.h_steps = 0
        self.memory = WorkingMemory.get(
            f"hpo:{name}",
            persist_path=self._memory_path())
        self._seed_population()

    # -- env-side memory path (Harness-1) -------------------------------
    def _memory_path(self) -> Optional[Path]:
        try:
            from .rl_advisory import RL_STATE_DIR
            return RL_STATE_DIR / "harness_memory.jsonl"
        except Exception:
            return None

    def _rand(self) -> float:
        # deterministic LCG — seeded runs stay reproducible
        self._rng_state = (1103515245 * self._rng_state + 12345) % (2**31)
        return self._rng_state / 2**31

    def _perturb(self, cfg: Dict[str, float]) -> Dict[str, float]:
        out = {}
        for k, (lo, hi) in _HARNESS_SPACE.items():
            span = hi - lo
            v = cfg[k] + (self._rand() - 0.5) * 0.6 * span
            out[k] = min(hi, max(lo, v))
        return out

    def _seed_population(self) -> None:
        self.candidates = [HarnessCandidate(dict(self.active_cfg)),
                           HarnessCandidate(dict(self._base_cfg))]
        while len(self.candidates) < self.population:
            self.candidates.append(
                HarnessCandidate(self._perturb(self.active_cfg)))

    # -- P-step -------------------------------------------------------
    def _score_candidate(self, cand: HarnessCandidate,
                         train, holdout) -> None:
        """Train + evaluate under the candidate's harness, without
        touching the live agent."""
        lc = self.lifecycle
        saved = (lc.lcb_penalty, lc.epochs, lc.holdout_frac)
        try:
            lc.lcb_penalty = cand.cfg["lcb_penalty"]
            lc.epochs = max(1, int(round(cand.cfg["epochs"])))
            table = lc._train_candidate(train)
            m = lc._evaluate(table, holdout)
        finally:
            lc.lcb_penalty, lc.epochs, lc.holdout_frac = saved
        cand.ope_mean = m["mean"]
        cand.ope_n = int(m["n"])
        cand.compute = float(cand.cfg["epochs"]) * max(1, len(train))
        cand.score = cand.ope_mean - self.cost_weight * cand.compute
        cand.evaluated = True

    def _grpo_advantages(self) -> None:
        scores = [c.score for c in self.candidates if c.evaluated]
        if not scores:
            return
        mu = mean(scores)
        sd = pstdev(scores) if len(scores) > 1 else 0.0
        for c in self.candidates:
            if c.evaluated:
                c.advantage = (c.score - mu) / (sd + 1e-9)

    # -- alternation entry point --------------------------------------
    def maybe_update(self) -> Optional[str]:
        """H-step before P-step: pick the harness, THEN let the
        lifecycle train/evaluate/deploy under it."""
        lc = self.lifecycle
        log = lc.agent.experience_log
        if len(log) >= lc.min_train + lc.min_holdout:
            n_hold = max(lc.min_holdout,
                         int(len(log) * lc.holdout_frac))
            seq = list(log)
            train, holdout = seq[:-n_hold], seq[-n_hold:]

            # P-step eval: score every harness candidate on the same
            # split; GRPO ranks them relative to the group.
            for c in self.candidates:
                if not c.evaluated:
                    self._score_candidate(c, train, holdout)
            self._grpo_advantages()

            winner = max(
                self.candidates,
                key=lambda c: c.score if c.evaluated else -1e18)
            if winner.evaluated:
                # H-step: activate the winner's harness, log to env-
                # side memory, regenerate population around it.
                prev = dict(self.active_cfg)
                if winner.cfg != self.active_cfg:
                    self.active_cfg = dict(winner.cfg)
                    lc.lcb_penalty = winner.cfg["lcb_penalty"]
                    lc.epochs = max(1, int(round(
                        winner.cfg["epochs"])))
                    lc.holdout_frac = winner.cfg["holdout_frac"]
                self.h_steps += 1
                self.memory.write(self.name, {
                    "event": "h_step",
                    "generation": self.generations,
                    "winner_cfg": winner.cfg,
                    "prev_cfg": prev,
                    "cfg_changed": winner.cfg != prev,
                    "ope_mean": winner.ope_mean,
                    "score": winner.score,
                    "advantage": winner.advantage,
                    "compute": winner.compute,
                })
                self.generations += 1
                self._seed_population()

        # Policy update runs under the active harness.
        return lc.maybe_update()

    def status(self) -> Dict[str, Any]:
        return {
            "generations": self.generations,
            "h_steps": self.h_steps,
            "active_cfg": self.active_cfg,
            "population": len(self.candidates),
            "cost_weight": self.cost_weight,
        }
