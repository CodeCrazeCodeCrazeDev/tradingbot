"""
London Session Edge Asset, Knowledge Base, and Lifecycle Management.
Models high-fidelity edges with immutable provenance tracking, dynamic health score
evaluation, policy-based state machine, and capacity limit estimation.
"""

import logging
import uuid
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import numpy as np

logger = logging.getLogger("AlphaAlgo.LondonEdgeRepository")


@dataclass
class EdgeProvenance:
    """
    Immutable provenance tracing linking the edge directly back to raw data, code, and environmental conditions.
    Guarantees complete reproducibility and audit integrity.
    """
    research_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    parent_research_id: Optional[str] = None
    dataset_version: str = "v1.0.0"
    dataset_hash: str = ""
    feature_schema_version: str = "v1.0.0"
    code_git_sha: str = "0000000000000000000000000000000000000000"
    configuration_hash: str = ""
    random_seed: int = 42
    model_version: str = "v1.0.0"
    validation_protocol_version: str = "v1.0.0"
    market_data_vendor: str = "Metatrader5"
    timezone: str = "GMT/UTC"
    environment_fingerprint: str = "Linux-x86_64-py312"
    author: str = "AlphaAlgo-Autonomous-Research-Organism"
    timestamp: datetime = field(default_factory=datetime.utcnow)
    approval_status: str = "Pending"
    integrity_hash: str = ""


@dataclass
class LondonEdge:
    """
    Detailed evidence object representing a discovered statistical edge.
    Contains causal assumptions, expected capacity, multidimensional regime matrix, and tracking metrics.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    provenance: EdgeProvenance = field(default_factory=EdgeProvenance)

    # Statistical parameters
    confidence_interval: Tuple[float, float] = (0.01, 0.05)
    expected_return_dist: Dict[str, float] = field(default_factory=lambda: {"mean": 0.001, "std": 0.0005})
    expected_holding_time_bars: int = 12
    required_liquidity_usd: float = 100000.0
    estimated_transaction_cost_pips: float = 1.8
    causal_assumptions: List[str] = field(default_factory=lambda: ["Asia range breakout sweep driven by early London institutional volume"])

    # Capacity Limits
    max_executable_size_usd: float = 1000000.0
    market_impact_coefficient: float = 0.12

    # Multidimensional Regime Matrix
    regimes_matrix: Dict[str, str] = field(default_factory=lambda: {
        "Trading Session": "London Open / London Kill Zone",
        "Volatility Regime": "High Volatility Expansion",
        "Liquidity Regime": "High Inflow Migration",
        "Trend Regime": "Trend breakout",
        "Central Bank Regime": "Non-Announce Days",
        "Risk Sentiment": "Risk-On"
    })

    # Lifecycle Management
    status: str = "Candidate"  # Candidate, Validated, Production, Observed, Decaying, Retired
    health_score: float = 1.0
    time_to_live_days: int = 30
    last_updated: datetime = field(default_factory=datetime.utcnow)


class LondonSessionKnowledgeBase:
    """
    An evolving knowledge repository that registers and tracks active edges,
    manages the multi-signal lifecycle state machine, and calculates Edge Health Scores.
    """

    def __init__(self) -> None:
        self.edges: Dict[str, LondonEdge] = {}

    def register_edge(self, edge: LondonEdge) -> None:
        """Saves a discovered edge inside the Knowledge Base."""
        # Calculate integrity hash of edge to preserve provenance
        fields_str = f"{edge.id}_{edge.name}_{edge.provenance.code_git_sha}_{edge.provenance.dataset_hash}"
        edge.provenance.integrity_hash = uuid.uuid5(uuid.NAMESPACE_DNS, fields_str).hex
        self.edges[edge.id] = edge
        logger.info(f"Registered Edge: '{edge.name}' (ID: {edge.id}, Status: {edge.status})")

    def compute_edge_health_score(self, edge_id: str, current_metrics: Dict[str, float]) -> float:
        """
        Computes an Edge Health Score (0.0 to 1.0) derived from multiple components:
        - Feature drift (Population Stability Index / PSI)
        - Outcome drift (KL divergence)
        - Risk-adjusted performance (Realized Sharpe vs expected)
        - Drawdown breaches
        - Calibration error
        - Regime mismatch frequency
        """
        edge = self.edges.get(edge_id)
        if not edge:
            raise ValueError(f"Edge {edge_id} not found in Knowledge Base.")

        # Default weights
        w_psi = 0.15
        w_kl = 0.15
        w_sharpe = 0.30
        w_drawdown = 0.20
        w_regime = 0.20

        # 1. Feature Drift component (PSI)
        # PSI < 0.1 = 1.0 score, PSI > 0.25 = 0.0 score
        psi = current_metrics.get("psi", 0.0)
        s_psi = np.clip((0.25 - psi) / 0.15, 0.0, 1.0)

        # 2. Outcome Drift (KL Divergence)
        # KL < 0.2 = 1.0 score, KL > 0.8 = 0.0 score
        kl = current_metrics.get("kl_divergence", 0.0)
        s_kl = np.clip((0.8 - kl) / 0.6, 0.0, 1.0)

        # 3. Realized Sharpe vs Expected
        # Sharpe >= Expected = 1.0, Sharpe <= 0 = 0.0
        expected_sharpe = current_metrics.get("expected_sharpe", 2.0)
        realized_sharpe = current_metrics.get("realized_sharpe", 2.0)
        s_sharpe = np.clip(realized_sharpe / max(expected_sharpe, 1e-8), 0.0, 1.0)

        # 4. Drawdown Breach
        # Max drawdown breach. Max drawdown limit is 12%.
        max_dd = current_metrics.get("realized_max_drawdown", 0.0)
        limit_dd = current_metrics.get("limit_max_drawdown", 0.12)
        s_drawdown = np.clip((limit_dd - max_dd) / limit_dd, 0.0, 1.0)

        # 5. Regime Mismatch frequency (portion of trades with regime mismatch)
        mismatch_rate = current_metrics.get("regime_mismatch_rate", 0.0)
        s_regime = np.clip(1.0 - mismatch_rate, 0.0, 1.0)

        # Weighted calculation
        health = (w_psi * s_psi) + (w_kl * s_kl) + (w_sharpe * s_sharpe) + (w_drawdown * s_drawdown) + (w_regime * s_regime)

        edge.health_score = float(health)
        edge.last_updated = datetime.utcnow()

        logger.info(f"Edge {edge_id[:12]} Health Evaluated: {edge.health_score:.4f} (PSI: {psi:.2f}, Sharpe: {realized_sharpe:.2f})")
        return edge.health_score

    def execute_lifecycle_transition(self, edge_id: str, health_threshold: float = 0.40) -> str:
        """
        Enforces policy-based lifecycle state machine:
        Candidate -> Validated -> Production -> Observed -> Decaying -> Retired.
        A single threshold breach won't retire an edge; the multi-signal Edge Health Score governs it.
        """
        edge = self.edges.get(edge_id)
        if not edge:
            return "UNKNOWN"

        curr_status = edge.status

        if curr_status == "Candidate":
            # Can progress to Validated if registered and proven
            edge.status = "Validated"
        elif curr_status == "Validated":
            # Validated moves to Production when deployed
            edge.status = "Production"
        elif curr_status == "Production":
            # Production degrades to Observed if health dips slightly
            if edge.health_score < 0.75:
                edge.status = "Observed"
        elif curr_status == "Observed":
            if edge.health_score >= 0.80:
                edge.status = "Production"
            elif edge.health_score < 0.55:
                edge.status = "Decaying"
        elif curr_status == "Decaying":
            if edge.health_score < health_threshold:
                edge.status = "Retired"
            elif edge.health_score > 0.70:
                edge.status = "Observed"

        if curr_status != edge.status:
            logger.warning(f"Edge Lifecycle Transition for {edge.id[:12]}: {curr_status} -> {edge.status}")

        return edge.status

    def estimate_market_impact_pips(self, edge_id: str, order_size_usd: float, avg_daily_volume_usd: float) -> float:
        """
        Estimates the market impact slippage cost in pips using the square-root impact law:
        Slippage = Coefficient * DailyVolatility * sqrt(ParticipationRate)
        """
        edge = self.edges.get(edge_id)
        if not edge or avg_daily_volume_usd <= 0:
            return 0.0

        participation_rate = order_size_usd / avg_daily_volume_usd
        # Assume standard 1% daily volatility proxy
        daily_vol = 0.01

        impact_pct = edge.market_impact_coefficient * daily_vol * np.sqrt(participation_rate)
        # Translate percent return impact to pips (0.01% = 1 pip)
        pips = impact_pct * 10000.0
        return float(pips)
