"""
AAMIS Master Orchestrator (Compatibility Shim)

Provides backward compatibility for the consolidated AAMIS v3.0 stack.
The original implementation depended on `intelligence_layers` and
`critical_systems` subpackages that were consolidated during the UCA merge.

This shim preserves the public contract (`AAMISMasterOrchestrator`,
`AAMISDecision`, `AAMISReport`, `analyze_market`) so dependent systems
(`superintelligence_orchestrator`, `elite_master_system`, `complete_integrator`)
remain importable and receive a safe, conservative abstention decision.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class AAMISDecision:
    """Complete AAMIS trading decision"""
    action: str  # BUY, SELL, HOLD
    conviction: float  # 0-100
    position_size_multiplier: float  # 0-1.5

    # Entry/Exit levels
    entry_price: float
    stop_loss: float
    take_profit_1: float
    take_profit_2: float

    # Risk assessment
    risk_level: str
    max_position_risk: float

    # Intelligence synthesis
    primary_signal: str
    confluence_score: float
    dimension_breakdown: Dict[str, Any]

    # Confidence & validity
    confidence_assessment: Any
    context_recognition: Any

    # Timing
    optimal_timeframe: str
    entry_windows: List[Tuple[datetime, datetime]]

    # Defense
    manipulation_detected: bool
    defense_mode: str

    # Reasoning
    causal_chains: List[str]
    reasoning_narrative: str
    warnings: List[str]

    # Metadata
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class AAMISReport:
    """Comprehensive intelligence report"""
    executive_summary: str
    decision: AAMISDecision
    detailed_analysis: Dict[str, Any]
    risk_factors: List[str]
    opportunities: List[str]
    recommendations: List[str]
    confidence_level: str
    timestamp: datetime = field(default_factory=datetime.now)


class AAMISMasterOrchestrator:
    """
    Compatibility shim for the consolidated AAMIS v3.0 master orchestrator.

    Returns a conservative HOLD report from `analyze_market`. Callers that
    fold the report into a larger consensus (e.g. superintelligence
    orchestrator phase-4 input) receive a neutral, non-authoritative input
    rather than a fabricated alpha signal.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.decision_history: List[AAMISDecision] = []
        self.performance_metrics: Dict[str, float] = {}
        logger.warning(
            "AAMISMasterOrchestrator compatibility shim active — "
            "consolidated engine replaced by conservative abstention. "
            "Route primary cognition through the canonical brain."
        )

    async def analyze_market(self, market_data: Dict[str, Any]) -> AAMISReport:
        price = float(market_data.get("price") or market_data.get("close") or 0.0)
        decision = AAMISDecision(
            action="HOLD",
            conviction=0.0,
            position_size_multiplier=0.0,
            entry_price=price,
            stop_loss=price,
            take_profit_1=price,
            take_profit_2=price,
            risk_level="unknown",
            max_position_risk=0.0,
            primary_signal="consolidated_shim",
            confluence_score=0.0,
            dimension_breakdown={},
            confidence_assessment=None,
            context_recognition=None,
            optimal_timeframe="N/A",
            entry_windows=[],
            manipulation_detected=False,
            defense_mode="abstain",
            causal_chains=[],
            reasoning_narrative=(
                "AAMIS v3.0 stack was consolidated; this shim abstains rather "
                "than fabricate intelligence."
            ),
            warnings=["aamis_shim_active"],
        )
        self.decision_history.append(decision)
        return AAMISReport(
            executive_summary="AAMIS consolidated shim — abstaining.",
            decision=decision,
            detailed_analysis={"shim": True, "market_data_keys": list(market_data.keys())},
            risk_factors=[],
            opportunities=[],
            recommendations=[],
            confidence_level="none",
        )

    def get_status(self) -> Dict[str, Any]:
        return {
            "state": "shim",
            "decisions": len(self.decision_history),
            "authoritative": False,
        }


__all__ = [
    "AAMISDecision",
    "AAMISReport",
    "AAMISMasterOrchestrator",
]
