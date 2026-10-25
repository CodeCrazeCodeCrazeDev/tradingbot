"""Reinforcement-learning advisory services — bounded, tabular, causal.

Four numpy-only RL agents, each a CSC *evidence provider* — never an
authority:

1. ``AdaptiveDecisionRL``    — contextual bandit over decision postures.
2. ``AdaptiveSpreadRL``      — market-making spread/skew policy learner.
3. ``AnalysisLensRL``        — which analytical lens is predictive *now*.
4. ``AlphaSearchRL``         — grammar mutation-operator selection.

Causal honesty
--------------
Every agent uses a deferred-label queue: a decision is recorded with the
current price/bar index, and its reward is computed ONLY after the
label horizon has elapsed on subsequent observations. No look-ahead,
no fabricated rewards, no reward from the same bar that produced the
action. Warmup bars report ``status: warming``; unresolved decisions
never leak into evidence as outcomes.

Authority boundary
------------------
Outputs are advisory dicts (direction hints, spread recommendations,
lens reliability, candidate expressions). None of them size, veto,
route, or execute anything — canonical risk and the canonical
execution service own that.
"""
from __future__ import annotations

import json
import math
import os
import re
import tempfile
from collections import deque
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any, Deque, Dict, List, Optional, Tuple

import numpy as np

# Durable checkpoint root — overridden by TB_RL_STATE_DIR for isolated
# runs/tests. Version keys bind a checkpoint to a learner+schema; a
# mismatch discards rather than silently reusing stale Q-values.
RL_STATE_DIR = Path(os.environ.get("TB_RL_STATE_DIR",
                                   "var/rl_state"))

# CHECKPOINT KEY CONTRACT: the version key passed to bind_checkpoint()
# is the only guard against loading stale Q under changed semantics.
# ANY change to a reward function, state encoding, or action space
# MUST bump the key (v2 -> v3 -> ...). Silent reuse under a changed
# formula is worse than relearning from zero.

def _pip_size(symbol: str) -> float:
    """JPY pairs price in 0.01 pips; everything else 0.0001."""
    return 0.01 if "JPY" in str(symbol).upper() else 0.0001


def _session_bucket(ts: Any) -> int:
    """Session bucket on the observation's own clock. NOTE: the
    market_data timestamps are broker server time (EET-style,
    verified by the volume-by-hour signature: liquidity trough at
    0:00 == NY close), NOT UTC — buckets are consistent but shifted
    ~2h from true UTC sessions and drift ±1h across DST. Do not
    re-interpret as UTC without de-offsetting first."""
    try:
        h = int(str(ts)[11:13])
        return 0 if h < 7 else (1 if h < 13 else 2)
    except (TypeError, ValueError, IndexError):
        return -1


def _sym_key(obs: Dict[str, Any]) -> str:
    """(symbol, timeframe) — an interleaved M15+H1 feed for the same
    instrument must not share pending-label queues."""
    return f"{obs.get('symbol') or '?'}:{obs.get('timeframe') or 'raw'}"


def _softmax(q: np.ndarray, tau: float = 1.0) -> np.ndarray:
    z = q / max(tau, 1e-6)
    z = z - float(np.max(z))
    e = np.exp(z)
    return e / float(np.sum(e))


def _soft(x: float) -> float:
    """Tail-preserving squashing: tanh keeps ordering information past
    |1| where clip(-1,1) treats a flash crash like noise."""
    return float(np.tanh(x))


def _obs_ts(obs: Dict[str, Any]) -> Optional[float]:
    """Observation timestamp as epoch seconds, or None."""
    from datetime import datetime
    t = obs.get("timestamp")
    if isinstance(t, (int, float)):
        return float(t)
    try:
        return datetime.fromisoformat(
            str(t).replace("Z", "+00:00")).timestamp()
    except (TypeError, ValueError, OSError):
        return None


def _num(v: Any) -> Optional[float]:
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    return f if math.isfinite(f) else None


class _TabularQ:
    """Bounded tabular Q-learner / contextual bandit.

    States are quantized to tuples; the table is hard-bounded by
    ``max_states`` with oldest-entry eviction so memory cannot grow
    without limit on a hostile feature space."""

    def __init__(self, n_actions: int, *, alpha: float = 0.15,
                 gamma: float = 0.0, epsilon: float = 0.15,
                 epsilon_min: float = 0.03, epsilon_decay: float = 0.9995,
                 max_states: int = 4096, forget: float = 0.999):
        self.n_actions = n_actions
        self.alpha = float(alpha)
        self.gamma = float(gamma)
        self.epsilon = float(epsilon)
        self._eps_min = float(epsilon_min)
        self._eps_decay = float(epsilon_decay)
        self._max_states = int(max_states)
        self._q: Dict[Tuple, np.ndarray] = {}
        self._order: Deque[Tuple] = deque(maxlen=max_states)
        self._rng = np.random.default_rng(7)  # deterministic exploration
        # Forgetting: Q-values learned under an old regime must decay
        # or checkpointed tables pollute new regimes forever. Applied
        # per-update on the visited row — unrevisited states are stale
        # anyway and won't be chosen.
        self._forget = float(forget)
        self.updates = 0
        self._ckpt: Optional[Path] = None
        self._key = "tabular_v1"
        # RLSF: self-distillation teacher — an EMA of the agent's OWN
        # table plays the frozen-teacher role (SIRLC student-teacher
        # duality, no external labels or reward model). Consulted only
        # for states the student has never visited.
        self._rlsf = os.environ.get("TB_RLSF", "1") == "1"
        self._teacher: Dict[Tuple, np.ndarray] = {}
        self._teacher_beta = float(os.environ.get(
            "TB_RLSF_TEACHER_BETA", "0.05"))
        self.teacher_guided = 0
        # On-policy self-distillation (KL-matching): periodically pull
        # the student's action distribution toward the teacher's over
        # VISITED states — softmax(·/tau) matching, not empty-row
        # consults only.
        self._distill_alpha = float(os.environ.get(
            "TB_RLSF_DISTILL_ALPHA", "0.02"))
        self._distill_tau = float(os.environ.get(
            "TB_RLSF_DISTILL_TAU", "0.5"))
        self._distill_max_states = 256
        # Self-play arena stats: student vs teacher scored on exact
        # counterfactuals at resolution.
        self.selfplay = {"matches": 0, "student_wins": 0,
                         "teacher_wins": 0, "ties": 0}

    def bind_checkpoint(self, name: str, key: str) -> None:
        """Enable durable persistence under RL_STATE_DIR/<name>.json."""
        self._ckpt = RL_STATE_DIR / f"{name}.json"
        self._key = key
        self._restore()

    def _restore(self) -> None:
        if not self._ckpt or not self._ckpt.exists():
            return
        try:
            blob = json.loads(self._ckpt.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return
        if blob.get("key") != self._key:
            return  # version/schema mismatch — never reuse stale Q
        q = blob.get("q", {})
        for sk, vals in q.items():
            if len(vals) == self.n_actions and all(
                    math.isfinite(v) for v in vals):
                state = tuple(json.loads(sk))
                self._q[state] = np.asarray(vals, dtype=float)
                self._order.append(state)
        self.updates = int(blob.get("updates", 0))
        self.epsilon = max(self._eps_min,
                           float(blob.get("epsilon", self.epsilon)))

    def save(self) -> None:
        if not self._ckpt:
            return
        self._ckpt.parent.mkdir(parents=True, exist_ok=True)
        blob = {
            "key": self._key,
            "updates": self.updates,
            "epsilon": self.epsilon,
            "q": {json.dumps(list(s)): [float(v) for v in arr]
                  for s, arr in self._q.items()},
        }
        fd, tmp = tempfile.mkstemp(dir=self._ckpt.parent,
                                   suffix=".tmp")
        try:
            with os.fdopen(fd, "w") as f:
                json.dump(blob, f)
            Path(tmp).replace(self._ckpt)
        except OSError:
            try:
                Path(tmp).unlink()
            except OSError:
                pass

    def row(self, state: Tuple) -> np.ndarray:
        if state not in self._q:
            if len(self._q) >= self._max_states:
                old = self._order.popleft()
                self._q.pop(old, None)
            self._q[state] = np.zeros(self.n_actions, dtype=float)
            self._order.append(state)
        return self._q[state]

    def act(self, state: Tuple) -> Tuple[int, bool]:
        """Return (action, explored?)."""
        self.epsilon = max(self._eps_min, self.epsilon * self._eps_decay)
        if self._rng.random() < self.epsilon:
            return int(self._rng.integers(self.n_actions)), True
        q = self.row(state)
        if self._rlsf and not np.any(q):
            t = self._teacher.get(state)
            if t is not None and np.any(t):
                self.teacher_guided += 1
                return int(np.argmax(t)), False
        return int(np.argmax(q)), False

    def update(self, state: Tuple, action: int, reward: float,
               next_state: Optional[Tuple] = None) -> None:
        if not math.isfinite(reward):
            return
        q = self.row(state)
        q *= self._forget  # recency decay before the update
        target = reward
        if next_state is not None and self.gamma > 0:
            target = reward + self.gamma * float(
                np.max(self.row(next_state)))
        q[action] += self.alpha * (target - q[action])
        if self._rlsf:
            if state not in self._teacher:
                if len(self._teacher) >= self._max_states:
                    self._teacher.pop(
                        next(iter(self._teacher)), None)
                self._teacher[state] = np.zeros(
                    self.n_actions, dtype=float)
            self._teacher[state] += self._teacher_beta * (
                q - self._teacher[state])
        self.updates += 1

    def distill_step(self) -> int:
        """KL-matching pass: for visited states where the student and
        teacher disagree, pull the student's softmax policy toward the
        teacher's. Bounded to the most recent states."""
        if not self._rlsf or not self._teacher:
            return 0
        n = 0
        for s in list(self._q.keys())[-self._distill_max_states:]:
            t = self._teacher.get(s)
            if t is None:
                continue
            q = self._q[s]
            if int(np.argmax(q)) == int(np.argmax(t)):
                continue
            p_t = _softmax(t, self._distill_tau)
            p_s = _softmax(q, self._distill_tau)
            q += self._distill_alpha * (p_t - p_s)
            n += 1
        return n

    def best(self, state: Tuple) -> Tuple[int, float]:
        q = self.row(state)
        a = int(np.argmax(q))
        return a, float(q[a])


@dataclass
class _Pending:
    """A decision awaiting its deferred label."""
    state: Tuple
    action: int
    price: float
    bar_idx: int
    extra: Dict[str, Any] = field(default_factory=dict)
    ts: Optional[float] = None  # epoch seconds when emitted


class _DeferredLearner:
    """Mixin: records pending decisions, resolves them once ``horizon``
    bars have elapsed. Reward_fn(pending, current_obs) -> float."""

    def __init__(self, horizon: int, max_pending: int = 512,
                 max_label_seconds: Optional[float] = None):
        self.horizon = int(horizon)
        # Labels older than this are discarded, not scored — a
        # deferred reward resolved across a weekend gap measures gap
        # noise, not policy quality. None = bar-count-only (legacy).
        self.max_label_seconds = max_label_seconds
        # Per-(symbol,timeframe) pending queues: on an interleaved
        # feed, a EURUSD-M15 pending must not resolve against a
        # GBPUSD or EURUSD-H1 bar.
        self._pending: Dict[str, Deque[_Pending]] = {}
        self._bar_idx: Dict[str, int] = {}
        self.labels_dropped_stale = 0
        # Resolved transitions for OFFLINE RL: (state, action, reward,
        # timestamp-of-resolution). The lifecycle trainer fits
        # candidate policies on this log — bounded memory.
        self.experience_log: Deque[Tuple] = deque(maxlen=8192)

    def _stale(self, p: "_Pending", obs: Dict[str, Any]) -> bool:
        """True when this pending's label window exceeded
        max_label_seconds — resolves across gaps are dropped, not
        scored as if the market traded through them."""
        if not self.max_label_seconds or p.ts is None:
            return False
        now = _obs_ts(obs)
        if now is None:
            return False
        return (now - p.ts) > self.max_label_seconds

    def _resolve(self, obs: Dict[str, Any], reward_fn) -> int:
        """Resolve matured pendings against the CURRENT obs. Returns
        the number resolved this call."""
        resolved = 0
        still: Deque[_Pending] = deque(maxlen=self._pending.maxlen)
        for p in self._pending:
            if self._bar_idx - p.bar_idx >= self.horizon:
                r = reward_fn(p, obs)
                if r is not None and math.isfinite(r):
                    yield_item = (p, r)
                    self._apply(yield_item)
                    resolved += 1
            else:
                still.append(p)
        self._pending = still
        return resolved

    def _apply(self, pr) -> None:  # pragma: no cover - overridden
        raise NotImplementedError


# ---------------------------------------------------------------------
# 1. Adaptive decision making
# ---------------------------------------------------------------------
class AdaptiveDecisionRL(_TabularQ, _DeferredLearner):
    """Learns a decision *posture* for the current market microstate.

    Actions: 0=flatten/defensive, 1=neutral/hold, 2=long-lean,
    3=short-lean. Reward: signed forward return over ``horizon`` bars,
    direction-aligned (long-lean rewards positive moves; short-lean the
    inverse; flat rewards *low* realized absolute move — being defensive
    is only correct when nothing happens)."""

    ACTIONS = ("defensive", "neutral", "long_lean", "short_lean")

    def __init__(self, horizon: int = 8):
        _TabularQ.__init__(self, n_actions=4, epsilon=0.2)
        _DeferredLearner.__init__(
            self, horizon=horizon,
            max_label_seconds=horizon * 900 * 3)
        # Per-symbol state — an interleaved feed must not bleed one
        # instrument's returns into another's state/pending queue.
        self._prev_close: Dict[str, float] = {}
        self._ret_hist: Dict[str, Deque[float]] = {}
        self.rlsf_cf_updates = 0
        self.self_corrections = 0
        self.self_corr_delta = 0.0
        self.self_corr_n = 0
        self._rlsf_correct = os.environ.get("TB_RLSF_CORRECT", "1") == "1"
        self._correct_margin = float(os.environ.get(
            "TB_RLSF_CORRECT_MARGIN", "0.02"))

    def _state(self, obs: Dict[str, Any]) -> Tuple:
        # _ret_hist is keyed by _sym_key (symbol:timeframe) — a raw
        # symbol lookup returns () forever, collapsing every state to
        # (0,0,session). Verified live bug.
        hist = self._ret_hist.get(_sym_key(obs), ())
        # Instrument-adaptive buckets: thresholds scale by the
        # instrument's own return dispersion — fixed 1e-4/0.003
        # magnitudes are EURUSD-calibrated and mis-bucket JPY/GDP.
        scale = float(np.median(np.abs(hist))) if len(hist) >= 8 else 1e-4
        scale = max(scale, 1e-5)
        mom = 0
        if len(hist) >= 5:
            r = sum(hist) / len(hist)
            mom = 1 if r > scale else (-1 if r < -scale else 0)
        vol = 0
        if len(hist) >= 8:
            sd = float(np.std(hist))
            vol = 2 if sd > 3 * scale else (1 if sd > 1.5 * scale else 0)
        return (mom, vol, _session_bucket(obs.get("timestamp")))

    def _reward(self, p: _Pending, obs: Dict[str, Any]) -> Optional[float]:
        c = _num(obs.get("close"))
        if c is None or p.price <= 0:
            return None
        pip = _pip_size(obs.get("symbol"))
        fwd = (c - p.price) / p.price
        fwd_pips = fwd / pip  # symbol-aware: USDJPY != EURUSD scale
        # Net-of-cost: a posture that wins gross but loses after
        # spread/commission must not be reinforced.
        cost_pips = float(p.extra.get("cost_bps", 0.0)) * 1e-4 / pip
        # Intra-horizon adverse excursion: obs high/low at resolution
        # is one bar's wick — approximate excursion by the worst
        # realized move in the direction *against* the posture.
        act = self.ACTIONS[p.action]
        gross = 0.0
        if act == "long_lean":
            gross = _soft(fwd_pips * 0.05 - cost_pips * 0.05)
        elif act == "short_lean":
            gross = _soft(-fwd_pips * 0.05 - cost_pips * 0.05)
        elif act == "defensive":
            gross = _soft(0.5 - abs(fwd_pips) * 0.02)
        else:
            gross = _soft(0.1 - abs(fwd_pips) * 0.005)  # neutral
        return gross

    def _apply(self, pr) -> None:
        p, r = pr
        self.update(p.state, p.action, r)

    def analyze(self, obs: Dict[str, Any]) -> Dict[str, Any]:
        sym = _sym_key(obs)
        self._bar_idx[sym] = self._bar_idx.get(sym, 0) + 1
        bar_idx = self._bar_idx[sym]
        close = _num(obs.get("close"))
        if close is None or close <= 0:
            return {"status": "no_data"}
        prev = self._prev_close.get(sym)
        if prev and prev > 0:
            self._ret_hist.setdefault(sym, deque(maxlen=32)).append(
                close / prev - 1.0)
        self._prev_close[sym] = close

        pend = self._pending.setdefault(sym, deque(maxlen=512))
        resolved = 0
        still: Deque[_Pending] = deque(maxlen=pend.maxlen)
        for p_ in pend:
            if self._stale(p_, obs):
                self.labels_dropped_stale += 1
                continue  # gap-spanning label: discard, don't score
            if bar_idx - p_.bar_idx >= self.horizon:
                r = self._reward(p_, obs)
                if r is not None:
                    # RLSF dense feedback (SDPO-style): _reward is a
                    # pure (pending, obs) map, so every action's
                    # counterfactual reward is exact — one label yields
                    # n_actions updates + a measured self-correction
                    # delta instead of a single sparse update.
                    if self._rlsf:
                        r_all = {}
                        for a in range(self.n_actions):
                            ra = self._reward(
                                replace(p_, action=a), obs)
                            if ra is not None:
                                r_all[a] = ra
                                self.update(p_.state, a, ra)
                                self.rlsf_cf_updates += 1
                        orig = p_.extra.get("rlsf_orig_action")
                        if orig is not None and orig in r_all:
                            self.self_corr_delta += (
                                r_all[p_.action] - r_all[orig])
                            self.self_corr_n += 1
                        # Self-play arena: score student-vs-teacher
                        # picks on the SAME counterfactual rewards.
                        t = self._teacher.get(p_.state)
                        if t is not None and np.any(t):
                            self.selfplay["matches"] += 1
                            s_pick = int(np.argmax(
                                self._q[p_.state]))                                 if p_.state in self._q else p_.action
                            t_pick = int(np.argmax(t))
                            s_r = r_all.get(s_pick)
                            t_r = r_all.get(t_pick)
                            if s_r is not None and t_r is not None:
                                if s_r > t_r + 1e-9:
                                    self.selfplay["student_wins"] += 1
                                elif t_r > s_r + 1e-9:
                                    self.selfplay["teacher_wins"] += 1
                                else:
                                    self.selfplay["ties"] += 1
                    else:
                        self.update(p_.state, p_.action, r)
                    self.experience_log.append(
                        (p_.state, p_.action, r, _obs_ts(obs)))
                    resolved += 1
            else:
                still.append(p_)
        self._pending[sym] = still

        state = self._state(obs)
        action, explored = self.act(state)
        # RLSF self-correction (SCoRe): an exploratory pick the agent's
        # own table already scored badly is revised to the greedy
        # action BEFORE commit — learning from self-generated mistakes
        # with the counterfactual delta measured at resolution.
        corrected_from = None
        corr_turns = 0
        pre_gap = 0.0
        if (self._rlsf_correct and explored and self.updates >= 20):
            q = self.row(state)
            max_turns = int(os.environ.get("TB_RLSF_TURNS", "2"))
            # Turn 1: student self-critique — revise toward the
            # student's own greedy when the exploratory pick is
            # already scored badly.
            greedy = int(np.argmax(q))
            pre_gap = float(q[greedy] - q[action])
            if (greedy != action
                    and pre_gap > self._correct_margin):
                corrected_from = action
                action = greedy
                corr_turns += 1
            # Turn 2: teacher consult — when the student is still
            # uncertain (thin top-two margin) and the distilled
            # teacher has visited this state, defer to it.
            if (corr_turns < max_turns
                    and self._teacher.get(state) is not None):
                q = self.row(state)
                order = np.argsort(-q)
                if len(order) >= 2 and                         q[order[0]] - q[order[1]] < self._correct_margin:
                    t_pick = int(np.argmax(self._teacher[state]))
                    if t_pick != action:
                        if corrected_from is None:
                            corrected_from = action
                        action = t_pick
                        corr_turns += 1
            if corr_turns:
                self.self_corrections += 1
                try:
                    from .harness_rl import WorkingMemory
                    WorkingMemory.get("rlsf:decision").write(sym, {
                        "event": "self_correction", "state": state,
                        "from_action": corrected_from,
                        "to_action": action,
                        "turns": corr_turns,
                        "q_gap": pre_gap,
                        "bar_idx": bar_idx})
                except Exception:
                    pass
        still.append(_Pending(
            state, action, close, bar_idx,
            extra={"cost_bps": _num(obs.get("cost_bps")) or 0.0,
                   "rlsf_orig_action": corrected_from},
            ts=_obs_ts(obs)))
        if self.updates and self.updates % 32 == 0:
            distilled = self.distill_step()
            self.save()
        q = self.row(state)
        return {
            "status": "active" if self.updates >= 20 else "warming",
            "posture": self.ACTIONS[action],
            "explored": explored,
            "evidence_weight": 0.3 if explored else 1.0,
            "q_values": {a: round(float(q[i]), 4)
                         for i, a in enumerate(self.ACTIONS)},
            "updates": self.updates,
            "rlsf": {
                "counterfactual_updates": self.rlsf_cf_updates,
                "self_corrections": self.self_corrections,
                "self_corr_avg_delta": round(
                    self.self_corr_delta / self.self_corr_n, 5)
                if self.self_corr_n else None,
                "teacher_guided": self.teacher_guided,
                "selfplay": dict(self.selfplay),
            },
            "pending_labels": len(self._pending[sym]),
            "resolved_this_bar": resolved,
            "horizon_bars": self.horizon,
            "labels_autocorrelated": True,
            "note": "posture evidence only — canonical risk sizes "
                    "everything. Deferred rewards resolve on overlapping"
                    " windows; do not treat per-update counts as "
                    "independent samples.",
        }


# ---------------------------------------------------------------------
# 2. Market making — adaptive spread management
# ---------------------------------------------------------------------
class AdaptiveSpreadRL(_TabularQ, _DeferredLearner):
    """Learns a spread-multiplier + inventory-skew policy from observed
    microstructure. State: (volatility bucket, trend bucket,
    pseudo-inventory bucket). Actions: spread multiplier
    {0.7x, 1.0x, 1.5x, 2.2x} x skew {neutral, lean_bid, lean_ask}.

    Reward proxy on a bars-only feed: spread capture minus adverse
    selection — a tight spread that gets run over by a strong move is
    penalized; a wide spread during chop is penalized for opportunity
    cost. On a quote/fill-capable feed real capture replaces the proxy
    (the adapter passes realized spread_capture when present — the same
    code path, just real labels)."""

    SPREADS = (0.7, 1.0, 1.5, 2.2)
    SKEWS = ("neutral", "lean_bid", "lean_ask")

    def __init__(self, horizon: int = 5):
        _TabularQ.__init__(self, n_actions=12, epsilon=0.25)
        _DeferredLearner.__init__(
            self, horizon=horizon,
            max_label_seconds=horizon * 900 * 3)
        self._prev_close: Dict[str, float] = {}
        self._ret_hist: Dict[str, Deque[float]] = {}
        self._inventory_proxy: Dict[str, float] = {}

    def _state(self, obs: Dict[str, Any]) -> Tuple:
        sym_ = _sym_key(obs)
        _h = self._ret_hist.get(sym_, ())
        ip = self._inventory_proxy.get(sym_, 0.0)
        # Instrument-adaptive buckets — fixed magnitudes mis-bucket
        # instruments with different return dispersion.
        scale = float(np.median(np.abs(_h))) if len(_h) >= 8 else 1e-4
        scale = max(scale, 1e-5)
        vol = 0
        if len(_h) >= 8:
            sd = float(np.std(_h))
            vol = 2 if sd > 3 * scale else (1 if sd > 1.5 * scale else 0)
        trend = 0
        if len(_h) >= 12:
            r = sum(list(_h)[-12:])
            trend = 1 if r > 2 * scale else (
                -1 if r < -2 * scale else 0)
        inv = 1 if ip > 0.5 else (-1 if ip < -0.5 else 0)
        return (vol, trend, inv,
                _session_bucket(obs.get("timestamp")))

    def _reward(self, p: _Pending, obs: Dict[str, Any]) -> Optional[float]:
        c = _num(obs.get("close"))
        if c is None or p.price <= 0:
            return None
        s_mult = self.SPREADS[p.action // 3]
        skew = self.SKEWS[p.action % 3]
        fwd = (c - p.price) / p.price
        _h = self._ret_hist.get(_sym_key(obs), ())
        vol = float(np.std(_h)) if len(_h) >= 8 else 0.001
        # half-spread capture proxy vs adverse move
        half_spread = 0.0002 * s_mult
        adverse = max(0.0, abs(fwd) - half_spread) * 3.0
        skew_pen = abs(fwd) * 1.0 if (
            (skew == "lean_bid" and fwd < 0)
            or (skew == "lean_ask" and fwd > 0)) else 0.0
        opportunity_cost = 0.15 * s_mult if abs(fwd) < vol * 0.5 else 0.0
        r = half_spread * 800 - adverse - skew_pen - opportunity_cost
        return float(np.clip(r, -1, 1))

    def analyze(self, obs: Dict[str, Any]) -> Dict[str, Any]:
        sym = _sym_key(obs)
        self._bar_idx[sym] = self._bar_idx.get(sym, 0) + 1
        bar_idx = self._bar_idx[sym]
        close = _num(obs.get("close"))
        if close is None or close <= 0:
            return {"status": "no_data"}
        prev = self._prev_close.get(sym)
        if prev and prev > 0:
            r = close / prev - 1.0
            self._ret_hist.setdefault(sym, deque(maxlen=24)).append(r)
            ip = self._inventory_proxy.get(sym, 0.0)
            self._inventory_proxy[sym] = float(
                np.clip(ip * 0.95 + np.sign(r) * 0.1, -3, 3))
        self._prev_close[sym] = close

        pend = self._pending.setdefault(sym, deque(maxlen=512))
        resolved = 0
        still: Deque[_Pending] = deque(maxlen=pend.maxlen)
        for p_ in pend:
            if self._stale(p_, obs):
                self.labels_dropped_stale += 1
                continue  # gap-spanning label: discard, don't score
            if bar_idx - p_.bar_idx >= self.horizon:
                r = self._reward(p_, obs)
                if r is not None:
                    self.update(p_.state, p_.action, r)
                    self.experience_log.append(
                        (p_.state, p_.action, r, _obs_ts(obs)))
                    resolved += 1
            else:
                still.append(p_)
        self._pending[sym] = still

        state = self._state(obs)
        action, explored = self.act(state)
        still.append(_Pending(state, action, close, bar_idx,
                              ts=_obs_ts(obs)))
        if self.updates and self.updates % 32 == 0:
            self.save()
        mult = self.SPREADS[action // 3]
        skew = self.SKEWS[action % 3]
        q = self.row(state)
        return {
            "status": "active" if self.updates >= 20 else "warming",
            "spread_multiplier": mult,
            "quote_skew": skew,
            "explored": explored,
            "evidence_weight": 0.3 if explored else 1.0,
            "best_q": round(float(np.max(q)), 4),
            "updates": self.updates,
            "label_source": "real_fills" if obs.get(
                "realized_spread_capture") is not None else "bar_proxy",
            "note": "quote-policy evidence only — canonical execution "
                    "decides whether/how to quote",
        }


# ---------------------------------------------------------------------
# 3. Market analysis — which lens is predictive now
# ---------------------------------------------------------------------
class AnalysisLensRL(_TabularQ, _DeferredLearner):
    """Contextual bandit over analysis lenses: momentum, mean-reversion,
    vol-breakout, carry/level. Each bar it scores the lenses' last
    predictions against what actually happened; the bandit learns which
    lens deserves trust in the current microstate."""

    LENSES = ("momentum", "mean_reversion", "vol_breakout", "level")

    def __init__(self, horizon: int = 4):
        _TabularQ.__init__(self, n_actions=4, epsilon=0.2)
        _DeferredLearner.__init__(
            self, horizon=horizon,
            max_label_seconds=horizon * 900 * 3)
        self._hist: Dict[str, Deque[float]] = {}

    def _lens_forecast(self, hist: Deque[float]) -> Dict[str, float]:
        """Each lens's current directional forecast in [-1, 1],
        computed from the same real bar history."""
        if len(hist) < 8:
            return {ln: 0.0 for ln in self.LENSES}
        arr = np.asarray(hist)
        mom = float(np.clip((arr[-1] / arr[-8] - 1) * 300, -1, 1))
        sma = float(np.mean(arr[-16:])) if len(arr) >= 16 else arr[-1]
        mr = float(np.clip((sma - arr[-1]) / max(arr[-1], 1e-9) * 300,
                           -1, 1))
        vol_now = float(np.std(np.diff(arr[-8:]) / arr[-8:-1]))
        vol_hist = float(np.std(np.diff(arr) / arr[:-1])) \
            if len(arr) > 16 else vol_now
        vb = float(np.clip(np.sign(arr[-1] - arr[-2])
                           if vol_now > 2 * vol_hist else 0.0, -1, 1))
        lvl = float(np.clip(np.sign(arr[-1] - np.median(arr)) * -0.5,
                            -1, 1))
        return {"momentum": mom, "mean_reversion": mr,
                "vol_breakout": vb, "level": lvl}

    def _state(self, hist: Deque[float]) -> Tuple:
        if len(hist) < 16:
            return (0, 0)
        arr = np.asarray(hist)
        vol = float(np.std(np.diff(arr[-12:]) / arr[-12:-1]))
        regime = 2 if vol > 0.003 else (1 if vol > 0.001 else 0)
        trend = 1 if arr[-1] > np.median(arr[-24:]) else -1
        return (regime, trend)

    def analyze(self, obs: Dict[str, Any]) -> Dict[str, Any]:
        sym = _sym_key(obs)
        self._bar_idx[sym] = self._bar_idx.get(sym, 0) + 1
        bar_idx = self._bar_idx[sym]
        close = _num(obs.get("close"))
        if close is None or close <= 0:
            return {"status": "no_data"}
        hist = self._hist.setdefault(sym, deque(maxlen=64))
        hist.append(close)
        if len(hist) < 10:
            return {"status": "warming", "bars": len(hist)}

        # Resolve: each recorded forecast gets scored on the realized
        # forward move — same symbol only.
        pend = self._pending.setdefault(sym, deque(maxlen=512))
        resolved = 0
        still: Deque[_Pending] = deque(maxlen=pend.maxlen)
        for p_ in pend:
            if self._stale(p_, obs):
                self.labels_dropped_stale += 1
                continue
            if bar_idx - p_.bar_idx >= self.horizon:
                fwd = (close - p_.price) / p_.price
                for lens, f in p_.extra.get("preds", {}).items():
                    li = self.LENSES.index(lens)
                    self.update(p_.state, li, _soft(
                        np.sign(fwd) * np.sign(f) * abs(fwd) * 400))
                    resolved += 1
            else:
                still.append(p_)
        self._pending[sym] = still

        preds = self._lens_forecast(hist)
        state = self._state(hist)
        q = self.row(state)
        best_i = int(np.argmax(q))
        still.append(_Pending(state, best_i, close, bar_idx,
                              {"preds": preds}, ts=_obs_ts(obs)))
        if self.updates and self.updates % 32 == 0:
            self.save()
        return {
            "status": "active" if self.updates >= 30 else "warming",
            "trusted_lens": self.LENSES[best_i],
            "lens_reliability": {ln: round(float(q[i]), 4)
                                 for i, ln in enumerate(self.LENSES)},
            "current_forecasts": {k: round(v, 4)
                                  for k, v in preds.items()},
            "updates": self.updates,
            "resolved_forecasts": resolved,
            "note": "lens-trust evidence only — advisory weight "
                    "decisions stay with the electorate",
        }


# ---------------------------------------------------------------------
# 4. Alpha discovery — mutation operator selection
# ---------------------------------------------------------------------
class AlphaSearchRL(_TabularQ):
    """RL over the alpha-grammar's mutation operators. State: outcome
    bucket of the last applied operator. Actions: tweak_parameter,
    mutate_leaf, crossover_like, prune. Reward: measured directional
    consistency of the produced expression's signal against bars the
    candidate had no part in selecting — forward-bars-only evaluation,
    no back-referencing."""

    OPERATORS = ("tweak_parameter", "mutate_leaf", "crossover_like",
                 "prune")
    _TERMS = ("close", "open", "high", "low", "volume")

    def __init__(self, eval_horizon: int = 6, max_candidates: int = 48):
        super().__init__(n_actions=4, epsilon=0.25)
        self._eval_horizon = eval_horizon
        self._hist: Dict[str, Deque[float]] = {}
        self._vol_hist: Dict[str, Deque[float]] = {}
        # Pending window must exceed the scoring lag (eval_horizon*2 +
        # margin) or unscored candidates are evicted before they can
        # mature — which produces zero updates forever.
        self._cand_max = max(eval_horizon * 4, max_candidates)
        self._candidates: Dict[str, Deque[Dict[str, Any]]] = {}
        self._last_outcome: Dict[str, str] = {}
        self._produced = 0
        self._born_idx = 0
        # Anti-overfit guard: do not report operator advantage until
        # at least this many candidates have matured — early winners
        # on noise are indistinguishable from real signal.
        self.min_mature_for_active = 15

    def _gen_candidate(self, op: int) -> Dict[str, Any]:
        """Produce a bounded expression under the chosen operator."""
        t1 = self._TERMS[int(self._rng.integers(len(self._TERMS)))]
        t2 = self._TERMS[int(self._rng.integers(len(self._TERMS)))]
        n = int(self._rng.integers(3, 15))
        op_name = self.OPERATORS[op]
        if op_name == "tweak_parameter":
            expr = f"sma_diff({t1},{n},{2*n})"
        elif op_name == "mutate_leaf":
            expr = f"delta({t1},{n}) / (std({t2},{2*n})+1e-9)"
        elif op_name == "crossover_like":
            expr = f"sign(sma({t1},{n}) - sma({t2},{3*n}))"
        else:  # prune — simplest form
            expr = f"ret({t1},{n})"
        return {"operator": op_name, "expression": expr,
                "born_at": self._born_idx}

    def _eval_node(self, node: Any, env: Dict[str, np.ndarray]
                   ) -> Optional[np.ndarray]:
        """Recursive evaluator over the tiny expression grammar."""
        if isinstance(node, str):
            return env.get(node)
        if isinstance(node, (int, float)):
            return np.asarray(float(node))
        if not isinstance(node, tuple):
            return None
        fn, args = node[0], node[1:]
        try:
            if fn == "sma" and len(args) == 2:
                x, n = self._eval_node(args[0], env), int(args[1])
                if x is None or len(x) < n or n < 1:
                    return None
                return np.convolve(x, np.ones(n) / n, "valid")
            if fn == "std" and len(args) == 2:
                x, n = self._eval_node(args[0], env), int(args[1])
                if x is None or len(x) < n or n < 1:
                    return None
                return np.array([float(np.std(x[i - n:i]))
                                 for i in range(n, len(x) + 1)])
            if fn == "ret" and len(args) == 2:
                x, n = self._eval_node(args[0], env), int(args[1])
                if x is None or len(x) <= n or n < 1:
                    return None
                return x[n:] / np.maximum(x[:-n], 1e-12) - 1.0
            if fn == "delta" and len(args) in (1, 2):
                x = self._eval_node(args[0], env)
                n = int(args[1]) if len(args) == 2 else 1
                if x is None or n < 1 or len(x) <= n:
                    return None
                return x[n:] - x[:-n]
            if fn == "sign" and len(args) == 1:
                x = self._eval_node(args[0], env)
                return None if x is None else np.sign(x)
            if fn == "sma_diff" and len(args) == 3:
                x = self._eval_node(args[0], env)
                a, b = int(args[1]), int(args[2])
                if x is None or b <= a or len(x) < b or a < 1:
                    return None
                fast = np.convolve(x, np.ones(a) / a, "valid")
                slow = np.convolve(x, np.ones(b) / b, "valid")
                # both 'valid' windows are right-aligned — fast must
                # drop its first b-a entries to align with slow.
                return fast[b - a:] / np.maximum(slow, 1e-12) - 1.0
            if fn in ("add", "sub", "mul", "div") and len(args) == 2:
                a = self._eval_node(args[0], env)
                b = self._eval_node(args[1], env)
                if a is None or b is None:
                    return None
                a = np.atleast_1d(np.asarray(a, dtype=float))
                b = np.atleast_1d(np.asarray(b, dtype=float))
                k = min(len(a), len(b))
                a, b = a[-k:], b[-k:]
                if fn == "add":
                    return a + b
                if fn == "sub":
                    return a - b
                if fn == "mul":
                    return a * b
                return a / np.maximum(np.abs(b), 1e-9)
        except (ValueError, TypeError, ZeroDivisionError, IndexError):
            return None
        return None

    def _parse_expression(self, expr: str) -> Any:
        """Parse 'fn(a,b,c)' / arithmetic forms into tuples.
        Grammar: fn(term|num,...) | node - node | node / (node+num)."""
        expr = expr.strip()
        # top-level '-' split (sub)
        depth = 0
        for i, ch in enumerate(expr):
            if ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
            elif (ch == "-" and depth == 0 and i > 0
                  and expr[i - 1] not in "eE"):
                return ("sub", self._parse_expression(expr[:i]),
                        self._parse_expression(expr[i + 1:]))
        depth = 0
        for i, ch in enumerate(expr):
            if ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
            elif ch == "/" and depth == 0:
                return ("div", self._parse_expression(expr[:i]),
                        self._parse_expression(expr[i + 1:]))
        if expr.startswith("(") and expr.endswith(")"):
            inner = expr[1:-1].strip()
            # strip a trailing '+const' guard like (x+1e-9)
            depth = 0
            for i, ch in enumerate(inner):
                if ch == "(":
                    depth += 1
                elif ch == ")":
                    depth -= 1
                elif ch == "+" and depth == 0:
                    return ("add", self._parse_expression(inner[:i]),
                            self._parse_expression(inner[i + 1:]))
            return self._parse_expression(inner)
        m = re.match(r"^([a-zA-Z_][a-zA-Z0-9_]*)\((.*)\)$", expr)
        if m:
            fn = m.group(1)
            raw = m.group(2)
            parts, depth, last = [], 0, 0
            for i, ch in enumerate(raw):
                if ch == "(":
                    depth += 1
                elif ch == ")":
                    depth -= 1
                elif ch == "," and depth == 0:
                    parts.append(raw[last:i]); last = i + 1
            parts.append(raw[last:])
            return (fn,) + tuple(self._parse_expression(a)
                                 for a in parts if a.strip())
        try:
            return float(expr)
        except ValueError:
            return expr if re.match(r"^[a-zA-Z_]+$", expr) else None

    def _eval_expression(self, expr: str, close: np.ndarray,
                         volume: np.ndarray) -> Optional[np.ndarray]:
        """Evaluate a grammar expression against bar history. Returns
        a per-bar signal series or None if the form is unknown."""
        node = self._parse_expression(expr)
        if node is None:
            return None
        env = {t: a for t, a in
               (("close", close), ("open", close), ("high", close),
                ("low", close), ("volume", volume))}
        return self._eval_node(node, env)

    def _score(self, cand: Dict[str, Any], sym: str) -> Optional[float]:
        """Sign-consistency of the candidate's REAL signal vs realized
        forward returns, evaluated ONLY on bars born after the
        candidate. Returns None until enough fresh bars exist."""
        born = cand["born_at"]
        hist = self._hist[sym]
        n_fresh = len(hist) - born - self._eval_horizon
        if n_fresh < self._eval_horizon * 2:
            return None
        close = np.asarray(hist)
        vol = np.asarray(self._vol_hist[sym])
        sig = self._eval_expression(cand["expression"], close, vol)
        if sig is None or len(sig) < self._eval_horizon + 2:
            return None
        # signal at bar t should predict close[t+1]/close[t]-1 — the
        # tail of sig aligns with the tail of close automatically since
        # every transform trims the left edge uniformly.
        h = self._eval_horizon
        sig_tail = sig[-h - 1:-1]
        fwd = close[-h:] / np.maximum(close[-h - 1:-1], 1e-12) - 1.0
        ok = np.isfinite(sig_tail) & np.isfinite(fwd)
        if ok.sum() < h:
            return None
        score = float(np.mean(np.sign(sig_tail[ok]) * np.sign(fwd[ok])))
        return float(np.clip(score, -1, 1)) if math.isfinite(score) \
            else None

    def analyze(self, obs: Dict[str, Any]) -> Dict[str, Any]:
        sym = _sym_key(obs)
        close = _num(obs.get("close"))
        vol = _num(obs.get("volume"))
        if close is None or close <= 0:
            return {"status": "no_data"}
        hist = self._hist.setdefault(sym, deque(maxlen=256))
        hist.append(close)
        self._vol_hist.setdefault(sym, deque(maxlen=256)).append(
            vol or 0.0)
        self._born_idx = len(hist)

        # Score matured candidates, update operator Q-values.
        cands = self._candidates.setdefault(
            sym, deque(maxlen=self._cand_max))
        last_out = self._last_outcome.get(sym, "none")
        matured = 0
        for cand in list(cands):
            s = self._score(cand, sym)
            if s is not None and cand.get("scored") is not True:
                op_i = self.OPERATORS.index(cand["operator"])
                self.update((last_out,), op_i, s)
                last_out = "win" if s > 0.05 else (
                    "loss" if s < -0.05 else "flat")
                cand["scored"] = True
                matured += 1
        self._last_outcome[sym] = last_out
        self._candidates[sym] = deque(
            [c for c in cands if not c.get("scored")],
            maxlen=cands.maxlen)

        state = (last_out,)
        action, explored = self.act(state)
        cand = self._gen_candidate(action)
        cand["born_at"] = len(hist)
        self._candidates[sym].append(cand)
        self._produced += 1
        if self.updates and self.updates % 32 == 0:
            self.save()
        q = self.row(state)
        return {
            "status": "active" if self.updates >=
                self.min_mature_for_active else "warming",
            "chosen_operator": self.OPERATORS[action],
            "candidate_expression": cand["expression"],
            "operator_q": {o: round(float(q[i]), 4)
                           for i, o in enumerate(self.OPERATORS)},
            "explored": explored,
            "updates": self.updates,
            "matured_this_bar": matured,
            "pending_candidates": len(self._candidates[sym]),
            "note": "candidate expressions are evidence for the "
                    "proposal pipeline only — OOS gate + human approval "
                    "still apply",
        }
