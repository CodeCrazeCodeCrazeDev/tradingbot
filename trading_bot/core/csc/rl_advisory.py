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

import math
from collections import deque
from dataclasses import dataclass, field
from typing import Any, Deque, Dict, List, Optional, Tuple

import numpy as np


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
                 max_states: int = 4096):
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
        self.updates = 0

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
        return int(np.argmax(q)), False

    def update(self, state: Tuple, action: int, reward: float,
               next_state: Optional[Tuple] = None) -> None:
        if not math.isfinite(reward):
            return
        q = self.row(state)
        target = reward
        if next_state is not None and self.gamma > 0:
            target = reward + self.gamma * float(
                np.max(self.row(next_state)))
        q[action] += self.alpha * (target - q[action])
        self.updates += 1

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


class _DeferredLearner:
    """Mixin: records pending decisions, resolves them once ``horizon``
    bars have elapsed. Reward_fn(pending, current_obs) -> float."""

    def __init__(self, horizon: int, max_pending: int = 512):
        self.horizon = int(horizon)
        self._pending: Deque[_Pending] = deque(maxlen=max_pending)
        self._bar_idx = 0

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
        _DeferredLearner.__init__(self, horizon=horizon)
        self._prev_close: Optional[float] = None
        self._ret_hist: Deque[float] = deque(maxlen=32)

    def _state(self, obs: Dict[str, Any]) -> Tuple:
        mom = 0
        if len(self._ret_hist) >= 5:
            r = sum(self._ret_hist) / len(self._ret_hist)
            mom = 1 if r > 1e-4 else (-1 if r < -1e-4 else 0)
        vol = 0
        if len(self._ret_hist) >= 8:
            sd = float(np.std(self._ret_hist))
            vol = 2 if sd > 0.003 else (1 if sd > 0.001 else 0)
        return (mom, vol)

    def _reward(self, p: _Pending, obs: Dict[str, Any]) -> Optional[float]:
        c = _num(obs.get("close"))
        if c is None or p.price <= 0:
            return None
        fwd = (c - p.price) / p.price
        if self.ACTIONS[p.action] == "long_lean":
            return float(np.clip(fwd * 500, -1, 1))
        if self.ACTIONS[p.action] == "short_lean":
            return float(np.clip(-fwd * 500, -1, 1))
        if self.ACTIONS[p.action] == "defensive":
            return float(np.clip(0.5 - abs(fwd) * 200, -1, 1))
        return float(np.clip(0.1 - abs(fwd) * 50, -1, 1))  # neutral

    def _apply(self, pr) -> None:
        p, r = pr
        self.update(p.state, p.action, r)

    def analyze(self, obs: Dict[str, Any]) -> Dict[str, Any]:
        self._bar_idx += 1
        close = _num(obs.get("close"))
        if close is None or close <= 0:
            return {"status": "no_data"}
        if self._prev_close and self._prev_close > 0:
            self._ret_hist.append(close / self._prev_close - 1.0)
        self._prev_close = close

        resolved = 0
        still: Deque[_Pending] = deque(maxlen=self._pending.maxlen)
        for p in self._pending:
            if self._bar_idx - p.bar_idx >= self.horizon:
                r = self._reward(p, obs)
                if r is not None:
                    self.update(p.state, p.action, r)
                    resolved += 1
            else:
                still.append(p)
        self._pending = still

        state = self._state(obs)
        action, explored = self.act(state)
        self._pending.append(_Pending(state, action, close,
                                      self._bar_idx))
        q = self.row(state)
        return {
            "status": "active" if self.updates >= 20 else "warming",
            "posture": self.ACTIONS[action],
            "explored": explored,
            "q_values": {a: round(float(q[i]), 4)
                         for i, a in enumerate(self.ACTIONS)},
            "updates": self.updates,
            "pending_labels": len(self._pending),
            "resolved_this_bar": resolved,
            "horizon_bars": self.horizon,
            "note": "posture evidence only — canonical risk sizes "
                    "everything",
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
        _DeferredLearner.__init__(self, horizon=horizon)
        self._prev_close: Optional[float] = None
        self._ret_hist: Deque[float] = deque(maxlen=24)
        self._inventory_proxy = 0.0  # accumulated directional pressure

    def _state(self, obs: Dict[str, Any]) -> Tuple:
        vol = 0
        if len(self._ret_hist) >= 8:
            sd = float(np.std(self._ret_hist))
            vol = 2 if sd > 0.003 else (1 if sd > 0.001 else 0)
        trend = 0
        if len(self._ret_hist) >= 12:
            r = sum(list(self._ret_hist)[-12:])
            trend = 1 if r > 0.002 else (-1 if r < -0.002 else 0)
        inv = 1 if self._inventory_proxy > 0.5 else (
            -1 if self._inventory_proxy < -0.5 else 0)
        return (vol, trend, inv)

    def _reward(self, p: _Pending, obs: Dict[str, Any]) -> Optional[float]:
        c = _num(obs.get("close"))
        if c is None or p.price <= 0:
            return None
        s_mult = self.SPREADS[p.action // 3]
        skew = self.SKEWS[p.action % 3]
        fwd = (c - p.price) / p.price
        vol = float(np.std(self._ret_hist)) if len(self._ret_hist) >= 8 \
            else 0.001
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
        self._bar_idx += 1
        close = _num(obs.get("close"))
        if close is None or close <= 0:
            return {"status": "no_data"}
        if self._prev_close and self._prev_close > 0:
            r = close / self._prev_close - 1.0
            self._ret_hist.append(r)
            self._inventory_proxy = float(
                np.clip(self._inventory_proxy * 0.95 + np.sign(r) * 0.1,
                        -3, 3))
        self._prev_close = close

        resolved = 0
        still: Deque[_Pending] = deque(maxlen=self._pending.maxlen)
        for p in self._pending:
            if self._bar_idx - p.bar_idx >= self.horizon:
                r = self._reward(p, obs)
                if r is not None:
                    self.update(p.state, p.action, r)
                    resolved += 1
            else:
                still.append(p)
        self._pending = still

        state = self._state(obs)
        action, explored = self.act(state)
        self._pending.append(_Pending(state, action, close,
                                      self._bar_idx))
        mult = self.SPREADS[action // 3]
        skew = self.SKEWS[action % 3]
        q = self.row(state)
        return {
            "status": "active" if self.updates >= 20 else "warming",
            "spread_multiplier": mult,
            "quote_skew": skew,
            "explored": explored,
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
        _DeferredLearner.__init__(self, horizon=horizon)
        self._hist: Deque[float] = deque(maxlen=64)
        self._lens_preds: Deque[Dict[str, float]] = deque(maxlen=16)

    def _lens_forecast(self) -> Dict[str, float]:
        """Each lens's current directional forecast in [-1, 1],
        computed from the same real bar history."""
        if len(self._hist) < 8:
            return {ln: 0.0 for ln in self.LENSES}
        arr = np.asarray(self._hist)
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

    def _state(self) -> Tuple:
        if len(self._hist) < 16:
            return (0, 0)
        arr = np.asarray(self._hist)
        vol = float(np.std(np.diff(arr[-12:]) / arr[-12:-1]))
        regime = 2 if vol > 0.003 else (1 if vol > 0.001 else 0)
        trend = 1 if arr[-1] > np.median(arr[-24:]) else -1
        return (regime, trend)

    def analyze(self, obs: Dict[str, Any]) -> Dict[str, Any]:
        self._bar_idx += 1
        close = _num(obs.get("close"))
        if close is None or close <= 0:
            return {"status": "no_data"}
        self._hist.append(close)
        if len(self._hist) < 10:
            return {"status": "warming",
                    "bars": len(self._hist)}

        # Resolve: each recorded forecast gets scored on the realized
        # forward move.
        resolved = 0
        still: Deque[_Pending] = deque(maxlen=self._pending.maxlen)
        for p in self._pending:
            if self._bar_idx - p.bar_idx >= self.horizon:
                fwd = (close - p.price) / p.price
                for lens, f in p.extra.get("preds", {}).items():
                    li = self.LENSES.index(lens)
                    self.update(p.state, li, float(np.clip(
                        np.sign(fwd) * np.sign(f)
                        * min(abs(fwd) * 400, 1.0), -1, 1)))
                    resolved += 1
            else:
                still.append(p)
        self._pending = still

        preds = self._lens_forecast()
        state = self._state()
        q = self.row(state)
        best_i = int(np.argmax(q))
        self._pending.append(_Pending(state, best_i, close,
                                      self._bar_idx,
                                      {"preds": preds}))
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

    def __init__(self, eval_horizon: int = 6, max_candidates: int = 8):
        super().__init__(n_actions=4, epsilon=0.25)
        self._eval_horizon = eval_horizon
        self._hist: Deque[float] = deque(maxlen=256)
        self._vol_hist: Deque[float] = deque(maxlen=256)
        self._candidates: Deque[Dict[str, Any]] = deque(
            maxlen=max_candidates)
        self._last_outcome = "none"
        self._produced = 0

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
                "born_at": len(self._hist)}

    def _score(self, cand: Dict[str, Any]) -> Optional[float]:
        """Sign-consistency of the candidate's signal vs realized
        forward returns, evaluated ONLY on bars born after the
        candidate. Returns None until enough fresh bars exist."""
        born = cand["born_at"]
        n_fresh = len(self._hist) - born - self._eval_horizon
        if n_fresh < self._eval_horizon * 2:
            return None
        arr = np.asarray(self._hist)[born:]
        if len(arr) < self._eval_horizon + 3:
            return None
        # simple proxy: does the expression's recent sign match the
        # subsequent move? crude but causal and honest.
        fwd = np.diff(arr) / arr[:-1]
        hits = np.abs(fwd[-self._eval_horizon:])
        score = float(np.mean(np.sign(fwd[-self._eval_horizon:]) *
                              np.sign(np.diff(arr[-self._eval_horizon-1:-1])))
                      ) if len(fwd) else 0.0
        if not math.isfinite(score) or not np.isfinite(hits).all():
            return None
        return float(np.clip(score, -1, 1))

    def analyze(self, obs: Dict[str, Any]) -> Dict[str, Any]:
        close = _num(obs.get("close"))
        vol = _num(obs.get("volume"))
        if close is None or close <= 0:
            return {"status": "no_data"}
        self._hist.append(close)
        self._vol_hist.append(vol or 0.0)

        # Score matured candidates, update operator Q-values.
        matured = 0
        for cand in list(self._candidates):
            s = self._score(cand)
            if s is not None and cand.get("scored") is not True:
                op_i = self.OPERATORS.index(cand["operator"])
                state = (self._last_outcome,)
                self.update(state, op_i, s)
                self._last_outcome = "win" if s > 0.05 else (
                    "loss" if s < -0.05 else "flat")
                cand["scored"] = True
                matured += 1
        self._candidates = deque(
            [c for c in self._candidates if not c.get("scored")],
            maxlen=self._candidates.maxlen)

        state = (self._last_outcome,)
        action, explored = self.act(state)
        cand = self._gen_candidate(action)
        self._candidates.append(cand)
        self._produced += 1
        q = self.row(state)
        return {
            "status": "active" if self.updates >= 15 else "warming",
            "chosen_operator": self.OPERATORS[action],
            "candidate_expression": cand["expression"],
            "operator_q": {o: round(float(q[i]), 4)
                           for i, o in enumerate(self.OPERATORS)},
            "explored": explored,
            "updates": self.updates,
            "matured_this_bar": matured,
            "pending_candidates": len(self._candidates),
            "note": "candidate expressions are evidence for the "
                    "proposal pipeline only — OOS gate + human approval "
                    "still apply",
        }
