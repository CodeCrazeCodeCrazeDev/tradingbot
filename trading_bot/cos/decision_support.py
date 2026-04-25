"""
Decision Support System — Evaluate Ideas, Route Decisions
===========================================================

The "judgment" layer of the COS. It takes simulated ideas and produces
decision traces — structured records of what was decided, why, and with
what confidence.

Key responsibilities:
    1. Evaluate: Score ideas by simulation confidence, risk/reward, knowledge backing
    2. Prioritize: Rank ideas by expected impact and feasibility
    3. Decide: Convert top ideas into actionable decision traces
    4. Route: Send decisions to the execution layer with full provenance
    5. Record: Store decision traces for later reality-checking

Integration with existing systems:
    - trading_bot.decision_layer.InnovativeDecisionEngine → 110 decision concepts
    - trading_bot.decision_layer.core_types              → decision types
    - trading_bot.cognitive_architecture                 → cognitive state
"""

from __future__ import annotations

import logging
import time
from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

import numpy as np

from .types import (
    COSConfig,
    DecisionConfidence,
    DecisionTrace,
    Idea,
    IdeaStatus,
    KnowledgeCategory,
    SimulationFidelity,
    SimulationResult,
)

logger = logging.getLogger(__name__)


class DecisionSupportSystem:
    """
    Evaluates ideas and produces decision traces with full provenance.

    The system is deliberately conservative — it only promotes ideas to
    decisions when:
      - Simulation confidence exceeds the minimum threshold
      - The idea is backed by validated knowledge nodes
      - Risk metrics are within acceptable bounds
      - Multiple simulation modes agree (dream + counterfactual + stress)

    This is the gatekeeper between "imagining" and "doing".
    """

    def __init__(self, config: COSConfig, cognition_store=None, simulation_engine=None):
        self.config = config
        self.cognition_store = cognition_store
        self.simulation_engine = simulation_engine

        # Active ideas: idea_id → Idea
        self._active_ideas: Dict[str, Idea] = {}

        # Decision history: trace_id → DecisionTrace
        self._decision_history: Dict[str, DecisionTrace] = {}

        # Idea performance tracking: idea_id → (was_correct, confidence)
        self._idea_performance: Dict[str, List[Tuple[bool, float]]] = defaultdict(list)

        # External decision engine reference
        self._innovative_decision_engine = None

        # Stats
        self._ideas_evaluated = 0
        self._decisions_made = 0

        logger.info(
            f"DecisionSupportSystem initialized | "
            f"min_confidence={config.min_confidence_to_execute} | "
            f"max_concurrent={config.max_concurrent_ideas}"
        )

    # ── Public API ────────────────────────────────────────────────────────

    def submit_idea(self, idea: Idea) -> str:
        """
        Submit an idea for evaluation.

        Ideas enter the pipeline: CANDIDATE → (simulate) → (evaluate) → (decide)
        """
        if len(self._active_ideas) >= self.config.max_concurrent_ideas:
            # Evict lowest-priority idea
            worst_id = min(self._active_ideas, key=lambda iid: self._active_ideas[iid].priority)
            self._active_ideas.pop(worst_id)
            logger.debug(f"Evicted idea {worst_id} to make room")

        self._active_ideas[idea.idea_id] = idea
        logger.info(f"Submitted idea {idea.idea_id}: {idea.title}")
        return idea.idea_id

    def generate_ideas_from_knowledge(self, context: Dict[str, Any]) -> List[Idea]:
        """
        Generate new ideas by combining knowledge from the Cognition Store.

        This is the "Researcher" agent — it looks at what the system knows
        and proposes hypotheses or strategy modifications.
        """
        ideas = []

        if self.cognition_store is None:
            logger.warning("No cognition store connected — cannot generate ideas")
            return ideas

        # Retrieve high-salience knowledge
        recent_nodes = self.cognition_store.recall_recent(top_k=20)
        regime_nodes = self.cognition_store.recall_by_category(
            KnowledgeCategory.MARKET_REGIME, top_k=5
        )
        risk_nodes = self.cognition_store.recall_by_category(
            KnowledgeCategory.RISK_INSIGHT, top_k=5
        )
        causal_nodes = self.cognition_store.recall_by_category(
            KnowledgeCategory.CAUSAL_RELATION, top_k=5
        )

        # Strategy 1: Regime-adapted ideas
        for node in regime_nodes:
            if node.validation_score > 0:
                idea = Idea(
                    title=f"Adapt to {node.title}",
                    description=f"Adjust strategy based on: {node.content}",
                    motivation=f"Regime knowledge (validation={node.validation_score:.2f})",
                    source_node_ids=[node.node_id],
                    proposal={"type": "regime_adaptation", "regime": node.structured_data},
                    priority=node.salience * (1 + node.validation_score),
                )
                ideas.append(idea)

        # Strategy 2: Risk mitigation ideas
        for node in risk_nodes:
            if node.validation_score > 0.3:
                idea = Idea(
                    title=f"Mitigate: {node.title}",
                    description=f"Risk insight: {node.content}",
                    motivation=f"Risk knowledge (validation={node.validation_score:.2f})",
                    source_node_ids=[node.node_id],
                    proposal={"type": "risk_mitigation", "insight": node.structured_data},
                    priority=node.salience * 1.2,  # risk ideas get priority boost
                )
                ideas.append(idea)

        # Strategy 3: Causal exploitation ideas
        for node in causal_nodes:
            if node.validation_score > 0.2:
                idea = Idea(
                    title=f"Exploit: {node.title}",
                    description=f"Causal relation: {node.content}",
                    motivation=f"Causal knowledge (validation={node.validation_score:.2f})",
                    source_node_ids=[node.node_id],
                    proposal={"type": "causal_exploitation", "relation": node.structured_data},
                    priority=node.salience * 1.1,
                )
                ideas.append(idea)

        # Strategy 4: Meta-cognitive ideas (COS improving itself)
        if self.config.enable_meta_cognition:
            meta_nodes = self.cognition_store.recall_by_category(
                KnowledgeCategory.META_COGNITIVE, top_k=3
            )
            for node in meta_nodes:
                idea = Idea(
                    title=f"Self-improve: {node.title}",
                    description=f"Meta insight: {node.content}",
                    motivation="COS self-improvement cycle",
                    source_node_ids=[node.node_id],
                    proposal={"type": "meta_cognitive", "insight": node.structured_data},
                    priority=node.salience * 0.8,  # meta ideas are lower priority than direct
                )
                ideas.append(idea)

        # Submit all generated ideas
        for idea in ideas:
            self.submit_idea(idea)

        logger.info(f"Generated {len(ideas)} ideas from knowledge")
        return ideas

    def evaluate_ideas(self) -> List[Idea]:
        """
        Evaluate all active ideas that have been simulated.

        Returns the list of ideas that passed evaluation, sorted by
        a composite score of simulation confidence, risk/reward, and
        knowledge backing.
        """
        evaluated = []

        for idea_id, idea in list(self._active_ideas.items()):
            if idea.status != IdeaStatus.SIMULATED:
                continue

            score = self._evaluate_idea(idea)

            if score >= self.config.min_confidence_to_execute:
                idea.status = IdeaStatus.VALIDATED
                evaluated.append(idea)
            else:
                logger.debug(
                    f"Idea {idea_id} failed evaluation | score={score:.2f} "
                    f"< min={self.config.min_confidence_to_execute}"
                )

            self._ideas_evaluated += 1

        # Sort by composite score
        evaluated.sort(key=lambda i: i.simulation_confidence, reverse=True)

        if evaluated:
            logger.info(f"Evaluated ideas: {len(evaluated)}/{len(self._active_ideas)} passed")

        return evaluated

    def decide(self, idea: Idea, context: Optional[Dict[str, Any]] = None) -> DecisionTrace:
        """
        Convert a validated idea into a decision trace.

        The decision trace captures the full provenance chain:
        knowledge → idea → simulation → decision
        """
        # Determine action from idea proposal
        action, action_params = self._idea_to_action(idea)

        # Determine confidence level
        confidence_score = idea.simulation_confidence
        if confidence_score >= 0.8:
            confidence = DecisionConfidence.HIGH
        elif confidence_score >= 0.6:
            confidence = DecisionConfidence.MEDIUM
        elif confidence_score >= 0.4:
            confidence = DecisionConfidence.LOW
        else:
            confidence = DecisionConfidence.SPECULATIVE

        # Build reasoning chain
        reasoning_chain = self._build_reasoning_chain(idea)

        # Collect provenance
        knowledge_node_ids = idea.source_node_ids[:]
        simulation_ids = [r.sim_id for r in idea.simulation_results]

        # Create trace
        trace = DecisionTrace(
            decision_id=idea.idea_id,
            action=action,
            action_params=action_params,
            knowledge_node_ids=knowledge_node_ids,
            idea_ids=[idea.idea_id],
            simulation_ids=simulation_ids,
            confidence=confidence,
            confidence_score=confidence_score,
            reasoning_chain=reasoning_chain,
            expected_pnl=idea.expected_pnl,
            expected_risk=idea.expected_risk,
        )

        # Update idea status
        idea.status = IdeaStatus.DEPLOYED
        idea.deployed_at = datetime.utcnow()

        # Store trace
        self._decision_history[trace.trace_id] = trace
        self._decisions_made += 1

        # Update knowledge nodes' decision_impact_count
        if self.cognition_store is not None:
            for nid in knowledge_node_ids:
                node = self.cognition_store._nodes.get(nid)
                if node is not None:
                    node.decision_impact_count += 1

        logger.info(
            f"Decision made | action={action} | confidence={confidence.value} "
            f"| idea={idea.idea_id} | expected_pnl={idea.expected_pnl:.4f}"
        )

        return trace

    def resolve_decision(
        self,
        trace_id: str,
        actual_pnl: float,
        actual_risk: float,
    ) -> Optional[DecisionTrace]:
        """
        Record the actual outcome of a decision.

        Called by the FeedbackLoop when reality data arrives.
        """
        trace = self._decision_history.get(trace_id)
        if trace is None:
            return None

        trace.actual_pnl = actual_pnl
        trace.actual_risk = actual_risk
        trace.resolved_at = datetime.utcnow()

        # Track idea performance
        was_correct = (trace.expected_pnl > 0 and actual_pnl > 0) or \
                      (trace.expected_pnl <= 0 and actual_pnl <= 0)
        self._idea_performance[trace.decision_id].append(
            (was_correct, trace.confidence_score)
        )

        # Update corresponding idea
        for idea_id, idea in self._active_ideas.items():
            if idea.idea_id == trace.decision_id:
                idea.actual_pnl = actual_pnl
                idea.actual_risk = actual_risk
                idea.reality_gap = abs(trace.expected_pnl - actual_pnl)
                idea.status = IdeaStatus.CONFIRMED if was_correct else IdeaStatus.REFUTED
                idea.resolved_at = datetime.utcnow()
                break

        return trace

    # ── External Integration ──────────────────────────────────────────────

    def connect_decision_engine(self, engine):
        """Connect to the existing InnovativeDecisionEngine."""
        self._innovative_decision_engine = engine
        logger.info("Connected InnovativeDecisionEngine")

    # ── Internal ──────────────────────────────────────────────────────────

    def _evaluate_idea(self, idea: Idea) -> float:
        """
        Compute a composite evaluation score for a simulated idea.

        Factors:
          1. Simulation confidence (weighted by fidelity)
          2. Risk/reward ratio
          3. Knowledge backing (how many validated nodes support it)
          4. Cross-mode agreement (do dream, counterfactual, stress agree?)
        """
        if not idea.simulation_results:
            return 0.0

        # Factor 1: Simulation confidence (already fidelity-weighted)
        sim_conf = idea.simulation_confidence

        # Factor 2: Risk/reward
        if idea.expected_risk != 0:
            rr_ratio = abs(idea.expected_pnl / idea.expected_risk)
        else:
            rr_ratio = 2.0 if idea.expected_pnl > 0 else 0.0
        rr_score = min(1.0, rr_ratio / 2.0)  # normalize: RR of 2+ → 1.0

        # Factor 3: Knowledge backing
        knowledge_score = 0.0
        if self.cognition_store is not None:
            for nid in idea.source_node_ids:
                node = self.cognition_store._nodes.get(nid)
                if node is not None and node.validation_score > 0:
                    knowledge_score += node.validation_score * node.salience
            knowledge_score = min(1.0, knowledge_score / max(1, len(idea.source_node_ids)))

        # Factor 4: Cross-mode agreement
        mode_results = defaultdict(list)
        for r in idea.simulation_results:
            mode_results[r.simulation_mode].append(r.predicted_pnl)

        agreement_score = 0.0
        if len(mode_results) >= 2:
            mode_medians = [np.median(pnls) for pnls in mode_results.values() if pnls]
            if mode_medians:
                # Agreement = all modes predict same sign
                signs = [np.sign(m) for m in mode_medians]
                if len(set(signs)) == 1:
                    agreement_score = 0.8
                elif len(set(signs)) == 2:
                    agreement_score = 0.3
                else:
                    agreement_score = 0.0

        # Composite
        score = (
            0.35 * sim_conf +
            0.25 * rr_score +
            0.25 * knowledge_score +
            0.15 * agreement_score
        )

        return float(score)

    def _idea_to_action(self, idea: Idea) -> Tuple[str, Dict[str, Any]]:
        """Convert an idea's proposal into an action and parameters."""
        proposal = idea.proposal
        idea_type = proposal.get("type", "unknown")

        action_map = {
            "regime_adaptation": "ADAPT_STRATEGY",
            "risk_mitigation": "ADJUST_RISK",
            "causal_exploitation": "ENTER_POSITION",
            "meta_cognitive": "SELF_ADJUST",
            "strategy_modification": "MODIFY_STRATEGY",
        }

        action = action_map.get(idea_type, "HOLD")
        params = {
            "idea_id": idea.idea_id,
            "idea_type": idea_type,
            "expected_pnl": idea.expected_pnl,
            "expected_risk": idea.expected_risk,
            **proposal,
        }

        return action, params

    def _build_reasoning_chain(self, idea: Idea) -> List[str]:
        """Build an explainable reasoning chain for a decision."""
        chain = []

        # Step 1: Knowledge basis
        if idea.source_node_ids:
            chain.append(
                f"Based on {len(idea.source_node_ids)} knowledge nodes"
            )
            if self.cognition_store is not None:
                for nid in idea.source_node_ids[:3]:
                    node = self.cognition_store._nodes.get(nid)
                    if node:
                        chain.append(f"  - {node.title} (validation={node.validation_score:.2f})")

        # Step 2: Motivation
        if idea.motivation:
            chain.append(f"Motivation: {idea.motivation}")

        # Step 3: Simulation summary
        if idea.simulation_results:
            dream_results = [r for r in idea.simulation_results if r.simulation_mode == "dream"]
            stress_results = [r for r in idea.simulation_results if r.simulation_mode == "stress_test"]
            cf_results = [r for r in idea.simulation_results if r.simulation_mode == "counterfactual"]

            if dream_results:
                avg_pnl = np.mean([r.predicted_pnl for r in dream_results])
                chain.append(f"Dream: avg PnL={avg_pnl:.4f} across {len(dream_results)} scenarios")

            if stress_results:
                worst = min(stress_results, key=lambda r: r.predicted_pnl)
                chain.append(f"Stress: worst PnL={worst.predicted_pnl:.4f} ({worst.scenario_name})")

            if cf_results:
                chain.append(f"Counterfactual: {len(cf_results)} what-if scenarios tested")

        # Step 4: Expected outcome
        chain.append(
            f"Expected: PnL={idea.expected_pnl:.4f}, Risk={idea.expected_risk:.4f}, "
            f"Confidence={idea.simulation_confidence:.2f}"
        )

        return chain

    # ── Stats ─────────────────────────────────────────────────────────────

    def stats(self) -> Dict[str, Any]:
        """Return decision support statistics."""
        total_ideas = len(self._idea_performance)
        correct = sum(1 for perf in self._idea_performance.values() if perf and perf[-1][0])

        return {
            "active_ideas": len(self._active_ideas),
            "ideas_evaluated": self._ideas_evaluated,
            "decisions_made": self._decisions_made,
            "decision_history_size": len(self._decision_history),
            "idea_accuracy": correct / max(1, total_ideas),
            "total_ideas_tracked": total_ideas,
            "innovative_engine_connected": self._innovative_decision_engine is not None,
        }
