"""Swarm-intelligence models — advisory deliberation under CSC authority.

The swarm is a deliberation substrate, not a brain: advisory services are
the nodes, their directional calls are votes, and this layer aggregates
them into one ``SwarmConsensus`` evidence artifact. It carries no order,
risk, veto, or execution authority — the CSC decides.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

DIRECTIONS = ("BUY", "SELL", "HOLD")
_DIRECTIONAL = ("BUY", "SELL")


class VotingMethod(str, Enum):
    MAJORITY = "majority"
    WEIGHTED = "weighted"
    BAYESIAN = "bayesian"
    BORDA = "borda"


@dataclass
class SwarmVote:
    """One node's ballot for a decision cycle."""

    node_id: str
    direction: str = "HOLD"          # BUY / SELL / HOLD
    confidence: float = 0.5          # 0..1 declared conviction
    domain: str = "other"            # expertise domain tag
    weight: float = 1.0              # measured performance weight
    reasoning: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_id": self.node_id,
            "direction": self.direction,
            "confidence": self.confidence,
            "domain": self.domain,
            "weight": self.weight,
            "reasoning": self.reasoning[:120],
        }


@dataclass
class MethodResult:
    """Outcome of one voting mechanism over the same ballots."""

    method: str
    direction: str = "HOLD"
    confidence: float = 0.0          # method-specific conviction 0..1
    detail: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "method": self.method,
            "direction": self.direction,
            "confidence": round(self.confidence, 6),
            "detail": self.detail,
        }


@dataclass
class EmergentSignals:
    """Signals that exist only in the aggregate — no single node emits them."""

    alignment: float = 0.0               # 1 - normalized vote dispersion
    cross_domain_agreement: float = 0.0  # domains whose plurality concurs
    cluster_strength: float = 0.0        # weight share of top high-conf cluster
    method_agreement: float = 0.0        # fraction of methods agreeing
    pattern_novelty: Optional[bool] = None  # knowledge-base: unseen pattern?
    dominant_nodes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "alignment": round(self.alignment, 6),
            "cross_domain_agreement": round(self.cross_domain_agreement, 6),
            "cluster_strength": round(self.cluster_strength, 6),
            "method_agreement": round(self.method_agreement, 6),
            "pattern_novelty": self.pattern_novelty,
            "dominant_nodes": list(self.dominant_nodes),
        }


@dataclass
class SwarmConsensus:
    """The swarm's advisory verdict for one cycle.

    ``direction``/``confidence`` are the effective consensus (performance-
    weighted aggregation modulated by method agreement). ``methods`` keeps
    every mechanism's result for transparency and audit.
    """

    direction: str = "HOLD"
    confidence: float = 0.0
    votes: List[SwarmVote] = field(default_factory=list)
    methods: Dict[str, MethodResult] = field(default_factory=dict)
    emergent: EmergentSignals = field(default_factory=EmergentSignals)
    regime: str = "unknown"
    symbol: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "direction": self.direction,
            "confidence": round(self.confidence, 6),
            "votes": [v.to_dict() for v in self.votes],
            "methods": {k: m.to_dict() for k, m in self.methods.items()},
            "emergent": self.emergent.to_dict(),
            "regime": self.regime,
            "symbol": self.symbol,
        }

    def feature_dict(self) -> Dict[str, float]:
        """Point-in-time-safe features for the NEXT observation (stored
        prior, consumed later — never this cycle's inputs)."""
        signed = {"BUY": 1.0, "SELL": -1.0}.get(self.direction, 0.0)
        return {
            "swarm_signed_direction": signed,
            "swarm_consensus_confidence": float(self.confidence),
            "swarm_alignment": float(self.emergent.alignment),
            "swarm_method_agreement": float(self.emergent.method_agreement),
            "swarm_cross_domain": float(self.emergent.cross_domain_agreement),
            "swarm_cluster_strength": float(self.emergent.cluster_strength),
            "swarm_voter_count": float(len(self.votes)),
        }
