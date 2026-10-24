"""SwarmIntelligenceService — the CSC's advisory deliberation chamber.

Advisory services are the nodes; their per-cycle directional calls are
the ballots. This service aggregates them under four voting mechanisms,
emerges the aggregate-only signals, learns per-node skill from measured
outcomes, and produces one ``SwarmConsensus`` evidence artifact.

Authority: none. The consensus is advisory evidence consumed by the CSC
the same way any advisor output is — it cannot authorize, size, veto, or
execute a trade.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from .aggregation import aggregate_all
from .knowledge import SwarmKnowledgeBase
from .models import (EmergentSignals, SwarmConsensus, SwarmVote,
                     VotingMethod)

logger = logging.getLogger(__name__)

# Expertise domains — a node's capability_id maps to one domain; the
# cross-domain agreement signal only has meaning if domains differ.
_DOMAIN_KEYWORDS = {
    "trend": ("trend", "momentum", "moving_average", "ema", "macd", "adx",
              "ichimoku", "supertrend"),
    "mean_reversion": ("mean_reversion", "reversion", "rsi", "bollinger",
                       "zscore", "stochastic", "oscillator"),
    "volatility": ("volatil", "vol_", "atr", "variance", "garch", "vix"),
    "volume_liquidity": ("volume", "liquidity", "order_flow", "depth",
                         "vwap", "obv", "flow"),
    "sentiment": ("sentiment", "news", "nlp", "social", "headline"),
    "regime_macro": ("regime", "macro", "economic", "session", "calendar",
                     "correlation"),
    "pattern": ("pattern", "chart", "candle", "harmonic", "elliott",
                "wave", "fibonacci", "divergence"),
    "risk": ("risk", "drawdown", "var_", "exposure", "tamic", "survival",
             "msos"),
    "execution": ("execution", "cost", "slippage", "spread",
                  "microstructure", "latency"),
}

# Confidence modifiers — bounded, transparent, applied to the weighted
# consensus only. Never enough to manufacture conviction alone.
_METHOD_AGREEMENT_FLOOR = 0.6
_ALIGNMENT_FLOOR = 0.8
_MIN_VOTERS = 2           # fewer directional voters than this -> HOLD
_CLUSTER_MIN_NODES = 3
_CLUSTER_MIN_CONF = 0.7


def domain_for(capability_id: str) -> str:
    low = str(capability_id or "").lower()
    for domain, keywords in _DOMAIN_KEYWORDS.items():
        if any(k in low for k in keywords):
            return domain
    return "other"


class SwarmIntelligenceService:
    """Advisory-only swarm deliberation for the CSC."""

    capability_id = "swarm_intelligence"

    def __init__(
        self,
        reliability_tracker: Any = None,
        knowledge: Optional[SwarmKnowledgeBase] = None,
        persistence_path: Optional[str] = None,
    ) -> None:
        self._tracker = reliability_tracker
        self.kb = knowledge or SwarmKnowledgeBase()
        self._persistence_path = persistence_path
        self._pending_votes: Dict[str, List[SwarmVote]] = {}
        self._pending_meta: Dict[str, Dict[str, str]] = {}

    # -- persistence ----------------------------------------------------

    def set_persistence(self, path: str) -> None:
        self._persistence_path = path
        self.kb = SwarmKnowledgeBase.load(path)

    def _persist(self) -> None:
        if not self._persistence_path:
            return
        try:
            self.kb.save(self._persistence_path)
        except OSError as exc:
            logger.warning("swarm knowledge persist failed: %s", exc)

    # -- deliberation ---------------------------------------------------

    def deliberate(
        self,
        calls: List[Dict[str, Any]],
        regime: str = "unknown",
        symbol: str = "",
    ) -> SwarmConsensus:
        """Aggregate this cycle's advisory calls into one consensus.

        ``calls`` are the normalized dicts the CSC builds from advisory
        artifacts: {capability_id, direction, confidence}.
        """
        regime = regime or "unknown"
        votes: List[SwarmVote] = []
        for c in calls or ():
            direction = str(c.get("direction") or "").upper()
            if direction not in ("BUY", "SELL", "HOLD"):
                continue
            aid = str(c.get("capability_id") or "unknown")
            try:
                conf = float(c.get("confidence") or 0.5)
            except (TypeError, ValueError):
                conf = 0.5
            weight = 1.0
            if self._tracker is not None:
                try:
                    weight = float(self._tracker.get_agent_weight(
                        aid, regime))
                except Exception:  # noqa: BLE001
                    weight = 1.0
            votes.append(SwarmVote(
                node_id=aid, direction=direction,
                confidence=max(0.0, min(1.0, conf)),
                domain=domain_for(aid), weight=weight,
                reasoning=str(c.get("reasoning") or "")[:120]))

        directional = [v for v in votes if v.direction in ("BUY", "SELL")]
        reliabilities = {
            v.node_id: self.kb.node_posterior(v.node_id, regime)
            for v in directional
        }
        methods = aggregate_all(votes, reliabilities)

        # Effective consensus: performance-weighted aggregation modulated
        # by cross-method agreement and alignment — bounded modifiers, so
        # a split swarm can only produce LOW confidence, never veto.
        weighted = methods["weighted"]
        if len(directional) < _MIN_VOTERS:
            direction, confidence = "HOLD", 0.0
        else:
            direction = weighted.direction
            agreeing = sum(
                1 for m in methods.values() if m.direction == direction)
            method_agreement = agreeing / max(1, len(methods))
            confidence = weighted.confidence * (
                _METHOD_AGREEMENT_FLOOR
                + (1.0 - _METHOD_AGREEMENT_FLOOR) * method_agreement)

        emergent = self._emerge(votes, methods, direction, regime)

        consensus = SwarmConsensus(
            direction=direction, confidence=confidence, votes=votes,
            methods=methods, emergent=emergent, regime=regime,
            symbol=symbol)

        self.kb.deliberations += 1
        self.kb.record_signals(consensus.feature_dict())
        if symbol:
            if symbol not in self._pending_votes and                     len(self._pending_votes) >= 64:
                # bound pending deliberations — an unbounded symbol feed
                # would otherwise leak one entry per unseen symbol
                self._pending_votes.pop(next(iter(self._pending_votes)))
                self._pending_meta.pop(
                    next(iter(self._pending_meta)), None)
            self._pending_votes[symbol] = votes
            self._pending_meta[symbol] = {"regime": regime,
                                          "direction": direction}
        return consensus

    def _emerge(
        self,
        votes: List[SwarmVote],
        methods: Dict[str, Any],
        direction: str,
        regime: str,
    ) -> EmergentSignals:
        directional = [v for v in votes if v.direction in ("BUY", "SELL")]

        # Alignment: 1 - normalized dispersion of signed weighted mass.
        signed = [v.weight * v.confidence * (1.0 if v.direction == "BUY"
                  else -1.0) for v in directional]
        if signed:
            total = sum(abs(s) for s in signed)
            alignment = abs(sum(signed)) / total if total > 0 else 0.0
        else:
            alignment = 0.0

        # Cross-domain agreement: fraction of expert domains whose
        # plurality agrees with the consensus direction.
        domains: Dict[str, List[SwarmVote]] = {}
        for v in directional:
            domains.setdefault(v.domain, []).append(v)
        if domains and direction in ("BUY", "SELL"):
            agreeing = 0
            for dvotes in domains.values():
                mass = {}
                for v in dvotes:
                    mass[v.direction] = mass.get(v.direction, 0.0) + (
                        v.weight * v.confidence)
                if max(mass, key=mass.get) == direction:
                    agreeing += 1
            cross_domain = agreeing / len(domains)
        else:
            cross_domain = 0.0

        # High-confidence cluster: weight share of the largest block of
        # >= _CLUSTER_MIN_NODES same-direction voters at conf >= 0.7.
        clusters: Dict[str, float] = {}
        total_w = sum(v.weight for v in directional) or 1.0
        for v in directional:
            if v.confidence >= _CLUSTER_MIN_CONF:
                clusters[v.direction] = clusters.get(
                    v.direction, 0.0) + v.weight
        strong = {d: sum(1 for v in directional
                         if v.direction == d and v.confidence
                         >= _CLUSTER_MIN_CONF) for d in clusters}
        cluster_strength = 0.0
        for d, w in clusters.items():
            if strong.get(d, 0) >= _CLUSTER_MIN_NODES:
                cluster_strength = max(cluster_strength, w / total_w)

        methods_agreeing = sum(
            1 for m in methods.values() if m.direction == direction)
        method_agreement = methods_agreeing / max(1, len(methods))

        # Pattern novelty: has this domain coalition been seen before?
        seen = self.kb.observe_pattern(regime, list(domains.keys()))
        pattern_novelty = seen < 2

        dominant = [v.node_id for v in sorted(
            directional, key=lambda v: v.weight * v.confidence,
            reverse=True)[:3]]

        return EmergentSignals(
            alignment=alignment, cross_domain_agreement=cross_domain,
            cluster_strength=cluster_strength,
            method_agreement=method_agreement,
            pattern_novelty=pattern_novelty, dominant_nodes=dominant)

    # -- learning -------------------------------------------------------

    def record_node_outcome(
        self, node_id: str, regime: str, correct: bool,
    ) -> None:
        """Score one node's vote against a settled outcome."""
        self.kb.record_node_outcome(node_id, regime, correct)
        self._persist()

    def record_consensus_outcome(
        self, regime: str, direction: str, correct: bool,
    ) -> None:
        """Score the consensus direction itself against a settled outcome."""
        self.kb.record_consensus_outcome(regime, direction, correct)
        self._persist()

    def record_outcome(
        self, symbol: str, realized_direction: str, regime: str,
    ) -> None:
        """Score the whole pending deliberation for a settled position."""
        votes = self._pending_votes.pop(symbol, None)
        meta = self._pending_meta.pop(symbol, {})
        if votes is None:
            return
        regime = meta.get("regime") or regime or "unknown"
        for v in votes:
            if v.direction in ("BUY", "SELL"):
                self.kb.record_node_outcome(
                    v.node_id, regime, v.direction == realized_direction)
        self.kb.record_consensus_outcome(
            regime, meta.get("direction", "HOLD"),
            meta.get("direction") == realized_direction)
        self._persist()

    # -- transparency ---------------------------------------------------

    def report(self) -> Dict[str, Any]:
        return {
            "deliberations": self.kb.deliberations,
            "nodes_measured": len(self.kb.node_skill),
            "patterns_seen": len(self.kb.domain_patterns),
            "strategy_records": dict(self.kb.strategy_records),
            "pending_symbols": sorted(self._pending_votes.keys()),
        }
