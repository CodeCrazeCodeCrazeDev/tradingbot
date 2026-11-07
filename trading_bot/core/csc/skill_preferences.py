"""Skill preference bank — DPO-style updates over the skill bank
(arXiv:2605.10813, NanoResearch).

The SkillRouter holds versioned skill artifacts but selects them by
static capability-count then version — no measured preference ever
reaches the bank. This module maintains per-task log-preference logits
over skills, updated from (chosen, rejected) pairs scored by realized
outcomes — the discrete analogue of direct preference optimization:

    z = logit_w - logit_l
    logit_w += lr * margin * (1 - sigma(z))
    logit_l -= lr * margin * sigma(z)

which is the Bradley-Terry pairwise loss gradient — well-learned
pairings produce small updates, mispredicted orderings large ones.

Pair sources are measured only: a skill choice that served a decision
is paired against the capability-equal candidates it beat, and the
settled position's realized return scales the update (tanh-bounded).
Evidence-only: scores surface in advisory_report and break capability
ties in _resolve_best_skill; they carry no independent authority.

State is durable: bounded logits persisted to a JSON file on update so
preference survives restarts without rebuilding from thin evidence.
"""

from __future__ import annotations

import json
import math
import os
import tempfile
from typing import Any, Dict, Iterable, List, Optional, Tuple


class SkillPreferenceBank:
    """Per-task log-preference weights over skill_ids (DPO/BT update)."""

    _LOGIT_CAP = 10.0

    def __init__(self, lr: float = 0.1, state_path: Optional[str] = None):
        self.lr = float(lr)
        self.state_path = state_path
        # task_key -> skill_id -> logit
        self.logits: Dict[str, Dict[str, float]] = {}
        self.pair_count = 0
        self._load()

    # -- DPO updates -----------------------------------------------------

    @staticmethod
    def _sigmoid(x: float) -> float:
        if x >= 0:
            return 1.0 / (1.0 + math.exp(-x))
        e = math.exp(x)
        return e / (1.0 + e)

    def record_pair(self, task: str, chosen: str, rejected: str,
                    margin: float = 1.0) -> Tuple[float, float]:
        """One pairwise preference observation. `margin` ∈ [-1, 1] scales
        the update — positive affirms the choice, negative reverses it
        (the 'chosen' skill was actually worse). Returns (logit_w,
        logit_l) after the update."""
        task = str(task)
        chosen = str(chosen)
        rejected = str(rejected)
        if not chosen or not rejected or chosen == rejected:
            return (self.logits.get(task, {}).get(chosen, 0.0),
                    self.logits.get(task, {}).get(rejected, 0.0))
        margin = max(-1.0, min(1.0, float(margin)))
        row = self.logits.setdefault(task, {})
        lw = row.get(chosen, 0.0)
        ll = row.get(rejected, 0.0)
        z = lw - ll
        step = self.lr * margin
        row[chosen] = max(-self._LOGIT_CAP,
                          min(self._LOGIT_CAP, lw + step * (1.0 - self._sigmoid(z))))
        row[rejected] = max(-self._LOGIT_CAP,
                            min(self._LOGIT_CAP, ll - step * self._sigmoid(z)))
        self.pair_count += 1
        self._save()
        return row[chosen], row[rejected]

    # -- read surface ----------------------------------------------------

    def scores(self, task: str,
               candidates: Iterable[str]) -> Dict[str, float]:
        """Softmax preference weights over the given candidate set."""
        row = self.logits.get(str(task), {})
        cands = [str(c) for c in candidates]
        if not cands:
            return {}
        mx = max(row.get(c, 0.0) for c in cands)
        exps = {c: math.exp(row.get(c, 0.0) - mx) for c in cands}
        total = sum(exps.values()) or 1.0
        return {c: v / total for c, v in exps.items()}

    def choose(self, task: str,
               candidates: Iterable[str]) -> Optional[str]:
        """Argmax preference skill, or None for empty candidate set."""
        w = self.scores(task, candidates)
        if not w:
            return None
        return max(w.items(), key=lambda kv: kv[1])[0]

    def snapshot(self) -> Dict[str, Any]:
        return {
            "tasks": sorted(self.logits),
            "pair_count": self.pair_count,
            "logits": {t: {s: round(v, 4) for s, v in row.items()}
                       for t, row in self.logits.items()},
        }

    # -- persistence -----------------------------------------------------

    def _load(self) -> None:
        if not self.state_path or not os.path.exists(self.state_path):
            return
        try:
            with open(self.state_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data.get("logits"), dict):
                self.logits = {
                    str(t): {str(s): float(v) for s, v in row.items()}
                    for t, row in data["logits"].items()
                    if isinstance(row, dict)}
            self.pair_count = int(data.get("pair_count") or 0)
        except Exception:
            # Corrupt state must never block startup — preference
            # re-learns from fresh pairs.
            self.logits = {}

    def _save(self) -> None:
        if not self.state_path:
            return
        try:
            os.makedirs(os.path.dirname(self.state_path) or ".",
                        exist_ok=True)
            payload = {"logits": self.logits,
                       "pair_count": self.pair_count}
            fd, tmp = tempfile.mkstemp(
                dir=os.path.dirname(self.state_path) or ".",
                suffix=".tmp")
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as f:
                    json.dump(payload, f)
                os.replace(tmp, self.state_path)
            except Exception:
                try:
                    os.unlink(tmp)
                except OSError:
                    pass
        except Exception:
            pass
