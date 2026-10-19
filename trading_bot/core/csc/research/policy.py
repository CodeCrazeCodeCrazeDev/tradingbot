"""Research policy — the loop optimizes itself.

After enough experiments the system knows which question types produce
real knowledge and which methods are reliable. The policy records
per-method outcomes and nudges question priority accordingly — bounded:
it adjusts ordering weights only; it can never authorize, promote, or
mutate a contract.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class MethodStats:
    attempts: int = 0
    supported: int = 0
    falsified: int = 0
    inconclusive: int = 0

    @property
    def yield_rate(self) -> float:
        """Fraction of investigations that produced a usable verdict."""
        if not self.attempts:
            return 0.5
        return (self.supported + self.falsified) / self.attempts

    @property
    def support_rate(self) -> float:
        """How often theses survive verification — low support_rate on a
        method means its hypotheses are usually wrong (or too weak to
        test), which is itself knowledge."""
        return self.supported / self.attempts if self.attempts else 0.5


class ResearchPolicy:
    def __init__(self) -> None:
        self.method_stats: Dict[str, MethodStats] = {}
        self.reward_stats: Dict[str, List[float]] = {}
        self._reward_evidence: set = set()

    def record_reward(self, method: str, reward: Dict[str, Any]) -> None:
        """Once per identical experiment, including after KG replay.

        Repeated runs, renamed questions and changing compute timings cannot
        inflate knowledge credit. Unknown/simulated origins earn no credit.
        """
        counts = self.reward_stats.setdefault(method, [0.0, 0.0])
        identity = (method, reward.get("evidence_id"), reward.get("origin"),
                    reward.get("policy_version"))
        if (not identity[1] or identity in self._reward_evidence
                or reward.get("blockers")):
            return
        values = {o["name"]: o["value"] for o in reward.get("objectives", ())}
        credit = values.get("resolved_question")
        if credit not in (0.0, 1.0):
            return
        self._reward_evidence.add(identity)
        counts[0] += 1
        counts[1] += credit

    def record(self, method: str, verdict: str) -> None:
        s = self.method_stats.setdefault(method, MethodStats())
        s.attempts += 1
        if verdict == "CONFIRMED":
            s.supported += 1
        elif verdict == "FALSIFIED":
            s.falsified += 1
        else:
            s.inconclusive += 1

    def estimate_info_gain(self, topic_hint: str) -> float:
        """Learned VoI input: methods/topics that historically produced
        verdicts (supported OR falsified — a decisive answer is information)
        earn a higher prior; <3 attempts stays at the uninformative 0.5."""
        measured = self.reward_stats.get(topic_hint)
        if measured is not None:
            return measured[1] / measured[0] if measured[0] >= 3 else 0.5
        stats = self.method_stats.get(topic_hint)
        if stats is None or stats.attempts < 3:
            return 0.5
        return stats.yield_rate

    def priority_adjustment(self, topic_hint: str) -> float:
        """Bounded ±0.15 nudge toward methods that produce verdicts.
        Never a gate — only ordering."""
        measured = self.reward_stats.get(topic_hint)
        if measured is not None:
            return (max(-0.15, min(0.15, measured[1] / measured[0] - 0.5))
                    if measured[0] >= 3 else 0.0)
        stats = self.method_stats.get(topic_hint)
        if stats is None or stats.attempts < 3:
            return 0.0
        return max(-0.15, min(0.15, stats.yield_rate - 0.5))

    def rank_questions(self, questions: List[Any]) -> List[Any]:
        for q in questions:
            q.priority = float(q.priority) + self.priority_adjustment(
                q.topic)
        return sorted(questions, key=lambda q: q.priority, reverse=True)

    def snapshot(self) -> Dict[str, Dict[str, Any]]:
        return {k: {"attempts": v.attempts, "supported": v.supported,
                    "falsified": v.falsified, "inconclusive": v.inconclusive,
                    "yield_rate": round(v.yield_rate, 3),
                    "reward_experiments": int(self.reward_stats.get(k, [0, 0])[0]),
                    "resolved_credit": self.reward_stats.get(k, [0, 0])[1]}
                for k, v in self.method_stats.items()}
