"""Shared knowledge base for the advisory swarm.

Persists what the swarm learns from measured outcomes — never asserted
priors:

- per-(node, regime) Beta skill posteriors over vote correctness
- domain-pattern counts (which domain coalitions keep appearing)
- per-(regime, direction) consensus outcome records
- a bounded emergent-signal history for audit transparency

Serializable to dict/JSON so a runner can persist it beside the run
state and restore it across restarts.
"""
from __future__ import annotations

import json
import os
import tempfile
from collections import deque
from typing import Any, Dict, List, Optional


class SwarmKnowledgeBase:
    """Measured swarm memory. All entries are earned by outcomes."""

    _HISTORY_MAX = 500

    def __init__(self) -> None:
        # node_skill[agent][regime] = {"a": wins+1, "b": losses+1} (Beta)
        self.node_skill: Dict[str, Dict[str, Dict[str, float]]] = {}
        # domain_pattern[(regime, sorted-domains)] -> consensus-count
        self.domain_patterns: Dict[str, int] = {}
        # strategy_records[(regime, direction)] = {"n", "wins"}
        self.strategy_records: Dict[str, Dict[str, float]] = {}
        self.signal_history: deque = deque(maxlen=self._HISTORY_MAX)
        self.deliberations: int = 0

    # -- learning -------------------------------------------------------

    def record_node_outcome(
        self, node_id: str, regime: str, correct: bool,
    ) -> None:
        entry = self.node_skill.setdefault(str(node_id), {}).setdefault(
            regime or "unknown", {"a": 1.0, "b": 1.0})
        entry["a" if correct else "b"] += 1.0

    def record_consensus_outcome(
        self, regime: str, direction: str, correct: bool,
    ) -> None:
        if direction not in ("BUY", "SELL"):
            return
        rec = self.strategy_records.setdefault(
            f"{regime or 'unknown'}|{direction}", {"n": 0.0, "wins": 0.0})
        rec["n"] += 1.0
        rec["wins"] += 1.0 if correct else 0.0

    def observe_pattern(self, regime: str, domains: List[str]) -> int:
        """Record the domain coalition and return how often it was seen."""
        key = f"{regime or 'unknown'}|{','.join(sorted(domains))}"
        seen = self.domain_patterns.get(key, 0)
        self.domain_patterns[key] = seen + 1
        return seen

    def record_signals(self, signals: Dict[str, Any]) -> None:
        self.signal_history.append(dict(signals))

    # -- queries --------------------------------------------------------

    def node_posterior(self, node_id: str, regime: str) -> float:
        """Mean of the Beta posterior: learned vote reliability in (0,1)."""
        skills = self.node_skill.get(str(node_id)) or {}
        entry = skills.get(regime or "unknown") or skills.get("unknown")
        if not entry:
            # Fall back to the agent's pooled skill across regimes.
            a = sum(e["a"] for e in skills.values())
            b = sum(e["b"] for e in skills.values())
            if a + b <= 2.0:
                return 0.5
            return a / (a + b)
        return entry["a"] / (entry["a"] + entry["b"])

    def node_outcomes(self, node_id: str, regime: str) -> int:
        skills = self.node_skill.get(str(node_id)) or {}
        entry = skills.get(regime or "unknown") or skills.get("unknown")
        if not entry:
            return 0
        return int(entry["a"] + entry["b"] - 2.0)

    # -- persistence ----------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_skill": self.node_skill,
            "domain_patterns": self.domain_patterns,
            "strategy_records": self.strategy_records,
            "signal_history": list(self.signal_history)[-50:],
            "deliberations": self.deliberations,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SwarmKnowledgeBase":
        kb = cls()
        kb.node_skill = dict(data.get("node_skill") or {})
        kb.domain_patterns = dict(data.get("domain_patterns") or {})
        kb.strategy_records = dict(data.get("strategy_records") or {})
        for item in list(data.get("signal_history") or [])[-cls._HISTORY_MAX:]:
            kb.signal_history.append(item)
        kb.deliberations = int(data.get("deliberations") or 0)
        return kb

    def save(self, path: str) -> None:
        directory = os.path.dirname(path) or "."
        os.makedirs(directory, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=directory, suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                json.dump(self.to_dict(), fh)
            os.replace(tmp, path)
        except BaseException:
            try:
                os.unlink(tmp)
            except OSError:
                pass
            raise

    @classmethod
    def load(cls, path: str) -> "SwarmKnowledgeBase":
        try:
            with open(path, "r", encoding="utf-8") as fh:
                return cls.from_dict(json.load(fh))
        except (OSError, ValueError):
            return cls()
