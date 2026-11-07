"""
Multi-Hypothesis Reasoning Engine - UCA-2026 Core
================================================

Generates parallel reasoning branches and counterfactual simulations.

Every evidence node carries ``metadata.source_ref`` pointing at the actual
input it was derived from (observation field, feature, strategy signal,
retrieved memory, advisory agent artifact, or simulation result). Nodes
without a resolvable source are rejected by the verification swarm's
provenance gate — fabricated filler no longer satisfies evidence checks.
"""

import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from ..hms.models import Hypothesis, EvidenceGraph, EvidenceNode, RelationType, EvidenceEdge

logger = logging.getLogger(__name__)


@dataclass
class ReasoningBranch:
    """A parallel reasoning thread focusing on a specific market interpretation."""

    branch_id: str
    name: str  # e.g., "Bullish Breakout Team", "Liquidity Drain Team"
    hypotheses: List[Hypothesis] = field(default_factory=list)
    reasoning_trace: List[str] = field(default_factory=list)
    confidence: float = 0.9
    probability: float = 0.0
    uncertainty: float = 0.0
    causal_explanation: str = ""
    invalidation_conditions: List[str] = field(default_factory=list)
    execution_plan: Dict[str, Any] = field(default_factory=dict)
    evidence_graph: EvidenceGraph = field(default_factory=EvidenceGraph)
    # Audit metadata: probability_model, inputs_used, etc. Never trusted
    # verbatim by verifiers — it exists for the audit trail.
    metadata: Dict[str, Any] = field(default_factory=dict)


def _finite_float(value: Any) -> Optional[float]:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        import math
        f = float(value)
        return f if math.isfinite(f) else None
    return None


def _evidence_node(node_id: str, content: str, source_ref: str,
                   metadata: Optional[Dict[str, Any]] = None) -> EvidenceNode:
    meta = dict(metadata or {})
    meta["source_ref"] = source_ref
    return EvidenceNode(
        node_id=node_id, content=content, node_type="EVIDENCE",
        metadata=meta,
    )


def _observation_evidence_nodes(
    market_data: Dict[str, Any],
    evidence_chain: Optional[List[Any]],
    advisory_artifacts: Optional[List[Any]],
) -> List[EvidenceNode]:
    """Build provenance-tagged evidence nodes from measured inputs only."""
    nodes: List[EvidenceNode] = []
    obs = market_data if isinstance(market_data, dict) else {}

    price = _finite_float(obs.get("price", obs.get("close")))
    if price is not None:
        nodes.append(_evidence_node(
            "ev_price", f"Observed price {price}",
            "observation:price", {"price": price}))

    volume = _finite_float(obs.get("volume"))
    if volume is not None:
        nodes.append(_evidence_node(
            "ev_volume", f"Observed volume {volume}",
            "market_data:volume", {"volume": volume}))

    volatility = _finite_float(obs.get("volatility"))
    if volatility is not None:
        nodes.append(_evidence_node(
            "ev_volatility", f"Observed volatility {volatility}",
            "feature:volatility", {"volatility": volatility}))

    trend = obs.get("trend") or obs.get("trend_direction")
    if trend:
        nodes.append(_evidence_node(
            "ev_trend", f"Observed trend {trend}",
            "observation:trend", {"trend": str(trend), "regime": str(trend)}))

    rsi = _finite_float(obs.get("rsi"))
    if rsi is not None:
        nodes.append(_evidence_node(
            "ev_rsi", f"Observed RSI {rsi}",
            "feature:rsi", {"rsi": rsi}))

    sentiment = _finite_float(obs.get("sentiment"))
    if sentiment is not None:
        nodes.append(_evidence_node(
            "ev_sentiment", f"Observed sentiment {sentiment}",
            "feature:sentiment", {"sentiment": sentiment}))

    spread = _finite_float(obs.get("spread_bps", obs.get("spread")))
    if spread is not None:
        nodes.append(_evidence_node(
            "ev_spread", f"Observed spread {spread}",
            "market_data:spread", {"spread": spread}))

    # Risk-relevant portfolio context (only when actually supplied).
    risk_meta = {
        k: _finite_float(obs.get(k))
        for k in ("exposure", "drawdown", "position_size")
    }
    risk_meta = {k: v for k, v in risk_meta.items() if v is not None}
    if risk_meta:
        nodes.append(_evidence_node(
            "ev_risk", f"Portfolio risk context {risk_meta}",
            "risk_eval:observation", risk_meta))

    rsi_sig = obs.get("rsi_signal")
    if isinstance(rsi_sig, dict) and rsi_sig.get("action"):
        nodes.append(_evidence_node(
            "ev_rsi_signal",
            f"RSI advisory signal: {rsi_sig.get('action')} "
            f"({rsi_sig.get('reason', '')})",
            "skill:rsi_signal",
            {"signal": str(rsi_sig.get("action"))}))

    for i, signal in enumerate(obs.get("strategy_signals") or []):
        sig_name = (
            signal.get("strategy_id") or signal.get("name") or f"signal_{i}"
            if isinstance(signal, dict) else str(signal)
        )
        nodes.append(_evidence_node(
            f"ev_strategy_{i}", f"Strategy signal {sig_name}: {signal}",
            f"strategy:{sig_name}",
            {"signal": signal if isinstance(signal, (str, int, float))
             else str(signal)}))

    for i, item in enumerate(evidence_chain or []):
        nodes.append(_evidence_node(
            f"ev_memory_{i}", f"Retrieved memory: {str(item)[:200]}",
            f"memory:hms:{i}", {"memory_ref": str(item)[:200]}))

    for i, artifact in enumerate(advisory_artifacts or []):
        if isinstance(artifact, dict):
            agent = str(artifact.get("agent") or artifact.get("source")
                        or artifact.get("capability_id") or f"agent_{i}")
            # Full normalized payload on the node — direction/confidence/
            # evidence stay visible to downstream audit and explainability.
            payload = {k: v for k, v in artifact.items() if k != "agent"}
            payload.setdefault("advisory_only", True)
        else:
            agent, payload = f"agent_{i}", {"advisory_only": True}
        nodes.append(_evidence_node(
            f"ev_advisory_{i}", f"Advisory artifact from {agent}",
            f"agent:{agent}", payload))

    return nodes


class HypothesisGenerator:
    """
    Orchestrates the generation of competing market hypotheses and
    their associated counterfactual simulations.
    """

    def __init__(self, world_model: Any = None, simulator: Any = None):
        self.world_model = world_model
        self._simulator = simulator

    def _get_simulator(self):
        if self._simulator is None:
            from ...cognition.simulation.engine import CounterfactualSimulator
            self._simulator = CounterfactualSimulator()
        return self._simulator

    async def generate_competing_branches(
        self,
        market_data: Dict[str, Any],
        evidence_chain: Optional[List[Any]] = None,
        advisory_artifacts: Optional[List[Any]] = None,
    ) -> List[ReasoningBranch]:
        """
        Creates competing reasoning branches grounded in the observation.

        Prior probabilities come from an explicitly-labelled heuristic prior
        (``metadata["probability_model"] = "heuristic_prior"``) — they are not
        calibrated win probabilities.
        """
        market_data = market_data if isinstance(market_data, dict) else {}
        price = float(market_data.get("price", market_data.get("close", 0.0)) or 0.0)
        volatility_raw = market_data.get("volatility", 0.02)
        volatility = float(volatility_raw if isinstance(volatility_raw, (int, float)) else 0.02)
        sentiment = float(market_data.get("sentiment", 0.0) or 0.0)
        symbol = market_data.get("symbol", "unknown")

        # Observation-derived heuristic priors (labelled, not calibrated):
        # sentiment tilts directional odds; advisory signals (runtime RSI
        # skill + registered strategy adapters) carry the larger share;
        # elevated volatility raises the mean-reversion (range) prior;
        # HOLD always gets a real share.
        signal_vote, signal_count = _signal_vote(market_data)
        tilt = max(-0.45, min(0.45, sentiment * 0.20 + signal_vote * 0.45))
        p_range = min(0.55, max(0.15, 0.30 + (volatility - 0.02) * 3.0))
        p_hold = 0.15
        remainder = 1.0 - p_range - p_hold
        p_bull = remainder * (0.5 + tilt)
        p_bear = remainder * (0.5 - tilt)
        ref = price if price > 0 else 1.0

        branches = [
            ReasoningBranch(
                branch_id="branch_bull",
                name="Bull Case",
                probability=p_bull,
                uncertainty=0.15,
                causal_explanation=(
                    "Directional long thesis: observed inputs support an "
                    "upward continuation."),
                invalidation_conditions=[
                    "Price closes below recent support",
                    "Measured liquidity deteriorates materially",
                ],
                execution_plan={
                    "action": "BUY", "symbol": symbol,
                    "limit_price": round(ref * 1.002, 5),
                    # Unit-sized intent: the canonical risk stage owns
                    # absolute sizing and clamps to approved_quantity.
                    "quantity": 1.0},
            ),
            ReasoningBranch(
                branch_id="branch_bear",
                name="Bear Case",
                probability=p_bear,
                uncertainty=0.20,
                causal_explanation=(
                    "Directional short thesis: observed inputs support a "
                    "downward continuation."),
                invalidation_conditions=[f"Price breaks {round(ref * 1.01, 5)}"],
                execution_plan={
                    "action": "SELL", "symbol": symbol,
                    "limit_price": round(ref * 0.998, 5),
                    "quantity": 1.0},
            ),
            ReasoningBranch(
                branch_id="branch_range",
                name="Range Case",
                probability=p_range,
                uncertainty=0.10,
                causal_explanation=(
                    "Mean-reversion thesis: price expected to oscillate "
                    "within the observed range."),
                invalidation_conditions=["Sustained volatility expansion"],
                execution_plan={"action": "WAIT", "symbol": symbol},
            ),
            ReasoningBranch(
                branch_id="branch_hold",
                name="Hold",
                probability=p_hold,
                uncertainty=0.05,
                causal_explanation=(
                    "Insufficient edge: hold is always an available decision "
                    "when evidence does not justify exposure."),
                invalidation_conditions=[],
                execution_plan={"action": "HOLD", "symbol": symbol},
            ),
        ]

        evidence_nodes = _observation_evidence_nodes(
            market_data, evidence_chain, advisory_artifacts)

        for branch in branches:
            branch.metadata["probability_model"] = "heuristic_prior"
            hyp = Hypothesis(
                description=f"Market will follow {branch.name}: "
                            f"{branch.causal_explanation}",
                predicted_outcome=branch.name,
                probability=branch.probability,
            )
            branch.hypotheses.append(hyp)

            # Reasoning trace cites the actual inputs used — no boilerplate.
            inputs_used = [
                f"{n.metadata.get('source_ref')}={_summary_value(n)}"
                for n in evidence_nodes[:8]
            ]
            branch.metadata["signal_vote"] = signal_vote
            branch.reasoning_trace.extend([
                f"Inputs observed for {symbol}: "
                + (", ".join(inputs_used) if inputs_used else "none"),
                f"Advisory signal vote {signal_vote:+.2f} "
                f"over {signal_count} signals",
                f"Heuristic prior for {branch.name}: {branch.probability:.3f}",
                f"Thesis: {branch.causal_explanation}",
            ])

            # Real evidence graph: hypothesis node + only the evidence that
            # was actually observed, linked by SUPPORTS edges.
            hyp_node_id = f"hyp_{branch.branch_id}"
            branch.evidence_graph.add_node(EvidenceNode(
                node_id=hyp_node_id,
                content=hyp.description,
                node_type="HYPOTHESIS",
            ))
            for node in evidence_nodes:
                # Node ids are shared across branch graphs deliberately — each
                # graph is an independent snapshot of the same observed inputs.
                branch.evidence_graph.add_node(EvidenceNode(
                    node_id=node.node_id,
                    content=node.content,
                    node_type=node.node_type,
                    confidence=node.confidence,
                    metadata=dict(node.metadata),
                ))
                branch.evidence_graph.add_edge(EvidenceEdge(
                    source_id=node.node_id,
                    target_id=hyp_node_id,
                    relation=RelationType.SUPPORTS,
                ))

        logger.info(
            "HypothesisGenerator: %d branches grounded on %d evidence nodes",
            len(branches), len(evidence_nodes))
        return branches

    def _build_market_state(self, market_data: Dict[str, Any]):
        """Map the raw observation dict onto the simulator's MarketState."""
        from ...cognition.state.contracts import MarketState

        obs = market_data if isinstance(market_data, dict) else {}
        ts = _finite_float(obs.get("timestamp"))
        trend = str(obs.get("trend") or obs.get("trend_direction") or "NEUTRAL").upper()
        # Normalize producer vocabularies: the bot's enricher emits
        # UP/DOWN/FLAT; CSC derivation and fixtures emit BULLISH/BEARISH/
        # NEUTRAL. MarketState only understands the latter.
        trend = {"UP": "BULLISH", "DOWN": "BEARISH", "FLAT": "NEUTRAL",
                 "RANGING": "NEUTRAL"}.get(trend, trend)
        if trend not in ("BULLISH", "BEARISH", "NEUTRAL"):
            trend = "NEUTRAL"
        # Trend strength must be a real signal, not a constant: derive it
        # from the observation's momentum when nothing supplies one —
        # momentum is the enriched 20-bar relative price change, so
        # |momentum|/0.005 saturates at a ~0.5% move. A near-flat market
        # yields strength ~0 -> the simulator's EV correctly collapses.
        ts = _finite_float(obs.get("trend_strength"))
        if ts is None:
            momentum = _finite_float(obs.get("momentum"))
            ts = min(1.0, abs(momentum) / 0.005) if momentum is not None else 0.0
        return MarketState(
            timestamp=ts if ts is not None else time.time(),
            instrument=str(obs.get("symbol") or "unknown"),
            primary_timeframe=str(obs.get("timeframe") or "M15"),
            trend_direction=trend,
            trend_strength=float(ts),
            volatility_percentile=float(
                obs.get("volatility_percentile", 0.5) or 0.5),
            uncertainty=float(obs.get("uncertainty", 0.2) or 0.2),
            timescale_structure=obs.get("timescale_structure") or {},
        )

    async def simulate_branches(
        self,
        branches: List[ReasoningBranch],
        market_data: Optional[Dict[str, Any]] = None,
        measured_features: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Runs the counterfactual simulator for each reasoning branch and
        attaches the result as a provenance-tagged evidence node.

        Returns ``{branch_id: {win_probability, expected_value,
        failure_rate, mc_p95_drawdown, invalidation_triggers, ...}}``.
        """
        simulation_results: Dict[str, Any] = {}
        obs = market_data if isinstance(market_data, dict) else {}
        try:
            simulator = self._get_simulator()
            market_state = self._build_market_state(obs)
        except Exception as exc:
            logger.warning(f"HypothesisGen: simulator unavailable: {exc}")
            return {b.branch_id: {} for b in branches}

        from ...cognition.simulation.contracts import SimulationRequest

        def _clip(v: float, lo: float = -1.0, hi: float = 1.0) -> float:
            return max(lo, min(hi, v))

        # Measured alignment prior: the controller derives ret_autocorr
        # (lag-1 return autocorrelation) as the regime-validity
        # discriminator — negative autocorr is the chop where
        # trend-following priors measured anti-predictive. Injecting it
        # here turns the simulator's assumed +1 trend-continuation prior
        # into a measured one; ~+-0.33 autocorr saturates the prior.
        base_scen: Dict[str, Any] = {}
        ac = _finite_float(obs.get("ret_autocorr"))
        if ac is not None:
            base_scen["alignment_prior"] = _clip(ac * 3.0)

        def _weight(name: str, assumed: float) -> tuple:
            """Measured weight from settled attribution, else the small
            assumed prior. mean_realized is a per-trade return (~1e-3
            scale); x100 maps it onto the drift-weight scale and lets a
            negative earner flip sign — measured > assumed either way."""
            mf = measured_features or {}
            st = mf.get(name)
            if (isinstance(st, dict) and st.get("status") == "measured"
                    and isinstance(st.get("mean_realized"), (int, float))):
                return _clip(st["mean_realized"] * 100.0, -0.5, 0.5),                     "measured"
            return assumed, "assumed"

        def _feature_priors(action: str) -> Dict[str, Dict[str, Any]]:
            """Sign-aligned per-candidate features so EV discriminates
            between market states sharing a trend label. Weights are
            deliberately small (drift contribution is capped at +-0.4 in
            the engine) and marked 'assumed' until outcome attribution
            measures them — same provenance discipline as
            alignment_prior_source."""
            sign = {"BUY": 1.0, "SELL": -1.0}.get(action)
            if sign is None:
                return {}
            feats: Dict[str, Dict[str, Any]] = {}
            mom = _finite_float(obs.get("momentum"))
            if mom is not None:
                w, s = _weight("momentum_x_action", 0.25)
                feats["momentum_x_action"] = {
                    "value": _clip(mom / 0.005 * sign),
                    "weight": w, "source": s}
            rsi = _finite_float(obs.get("rsi"))
            if rsi is not None:
                w, s = _weight("rsi_fade", 0.2)
                feats["rsi_fade"] = {
                    "value": _clip((50.0 - rsi) / 50.0 * sign),
                    "weight": w, "source": s}
            # L2 imbalance only when the book is point-in-time valid —
            # hl_live tags the book "live" (fetched at bar-detection);
            # replay merges are tagged "anachronistic" and a book
            # attached to a historical bar is not evidence.
            if obs.get("order_book_time") == "live":
                imb = _finite_float(obs.get("imbalance_ratio"))
                if imb is not None:
                    w, s = _weight("order_imbalance", 0.3)
                    feats["order_imbalance"] = {
                        "value": _clip(imb * sign),
                        "weight": w, "source": s}
            return feats

        for branch in branches:
            plan = branch.execution_plan if isinstance(
                branch.execution_plan, dict) else {}
            action = str(plan.get("action") or "HOLD")
            size = _finite_float(
                plan.get("quantity", plan.get("position_size"))) or 0.1
            scen = dict(base_scen)
            feats = _feature_priors(action)
            if feats:
                scen["feature_priors"] = feats
            try:
                result = simulator.simulate(SimulationRequest(
                    request_id=f"{branch.branch_id}:{market_state.instrument}",
                    current_state=market_state,
                    proposed_action=action,
                    position_size=max(0.0, size),
                    scenario_adjustments=scen,
                    monte_carlo_paths=64,
                ))
                sim = {
                    "win_probability": result.win_probability,
                    "expected_value": result.expected_value,
                    "failure_rate": max(0.0, 1.0 - result.win_probability),
                    "mc_win_probability": result.mc_win_probability,
                    "mc_p95_drawdown": result.mc_p95_drawdown,
                    "invalidation_triggers": result.invalidation_triggers,
                    "mc_paths": result.mc_paths,
                    "alignment_prior_source": result.alignment_prior_source,
                    "feature_drift_source": result.feature_drift_source,
                    "feature_contributions": result.feature_contributions,
                }
            except Exception as exc:
                logger.warning(
                    f"HypothesisGen: simulation failed for "
                    f"{branch.branch_id}: {exc}")
                sim = {}
            simulation_results[branch.branch_id] = sim
            if sim:
                branch.evidence_graph.add_node(_evidence_node(
                    f"sim_{branch.branch_id}",
                    f"Counterfactual simulation of {action}: "
                    f"win_p={sim['win_probability']}, "
                    f"p95_dd={sim['mc_p95_drawdown']}",
                    f"simulation:{branch.branch_id}",
                    {"win_probability": sim["win_probability"],
                     "p95_drawdown": sim["mc_p95_drawdown"],
                     "expected_value": sim["expected_value"],
                     "mc_paths": sim["mc_paths"]},
                ))

        return simulation_results

    async def generate_alternative_branch(
        self, failed_branch: ReasoningBranch, reports: List[Any]
    ) -> Optional[ReasoningBranch]:
        """Generates a strategically distinct alternative (PIVOT)."""
        logger.info(
            f"HypothesisGen: Generating alternative to failed branch {failed_branch.branch_id}"
        )
        import copy as _copy
        plan = dict(getattr(failed_branch, "execution_plan", {}) or {})
        plan["action"] = "HOLD"  # A falsified branch pivots to no-exposure.
        return ReasoningBranch(
            branch_id=f"pivot_{failed_branch.branch_id}",
            name=f"Pivoted {failed_branch.name}",
            confidence=0.7,
            execution_plan=plan,
            causal_explanation=(
                f"Pivot from {failed_branch.name}: verifier critique "
                "invalidated the directional thesis."),
            # The measured evidence stays valid — only the action changed.
            evidence_graph=_copy.deepcopy(failed_branch.evidence_graph),
        )

    async def pivot_branch(self, branch: ReasoningBranch, reason: str) -> Optional[ReasoningBranch]:
        """AutoResearchClaw Pivot logic: strategically distinct alternative."""
        logger.info(f"HypothesisGen: Pivoting branch {branch.branch_id} due to {reason}")
        import copy as _copy
        plan = dict(getattr(branch, "execution_plan", {}) or {})
        plan["action"] = "HOLD"
        return ReasoningBranch(
            branch_id=f"pivoted_{branch.branch_id}",
            name=f"Pivoted {branch.name}",
            confidence=branch.confidence * 0.9,
            causal_explanation=(
                f"Strategic pivot from {branch.name} due to {reason}. "
                "Falls back to no exposure."),
            execution_plan=plan,
            # Preserve the evidence graph — the observations are unchanged.
            evidence_graph=_copy.deepcopy(branch.evidence_graph),
        )


def _signal_vote(market_data: Dict[str, Any]) -> "tuple[float, int]":
    """Aggregate advisory directional signals into a bounded vote in
    [-1, 1]. Returns (vote, signal_count); 0.0 vote when nothing was
    attached — priors then stand on observation features alone."""
    obs = market_data if isinstance(market_data, dict) else {}
    vote = 0.0
    count = 0

    rsi_sig = obs.get("rsi_signal")
    if isinstance(rsi_sig, dict):
        action = str(rsi_sig.get("action") or "").lower()
        if action == "buy_bias":
            vote += 0.5
        elif action == "sell_bias":
            vote -= 0.5
        if action:
            count += 1

    for signal in obs.get("strategy_signals") or []:
        if not isinstance(signal, dict):
            continue
        direction = str(
            signal.get("direction") or signal.get("action") or "").lower()
        try:
            conf = float(signal.get("confidence") or 0.5)
        except (TypeError, ValueError):
            conf = 0.5
        conf = max(0.0, min(1.0, conf))
        if direction in ("buy", "long", "buy_bias", "bullish", "strong_buy"):
            vote += conf
            count += 1
        elif direction in ("sell", "short", "sell_bias", "bearish",
                           "strong_sell"):
            vote -= conf
            count += 1
        elif direction in ("hold", "neutral", "wait", "close"):
            count += 1

    return (max(-1.0, min(1.0, vote / count)), count) if count else (0.0, 0)


def _summary_value(node: EvidenceNode) -> str:
    meta = node.metadata or {}
    for key in ("price", "volatility", "volume", "rsi", "trend", "sentiment",
                "spread", "win_probability", "signal"):
        if key in meta:
            return str(meta[key])
    return str(node.content)[:60]
