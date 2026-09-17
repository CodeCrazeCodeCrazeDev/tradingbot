"""World Model and Counterfactual Simulation Engine contracts."""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional


@dataclass
class SimulationRequest:
    """Request for counterfactual trajectory evaluation."""
    request_id: str
    current_state: Any
    proposed_action: str  # e.g., BUY, SELL, HOLD, WAIT, REDUCE
    position_size: float
    time_horizon_bars: int = 10
    scenario_adjustments: Dict[str, Any] = field(default_factory=dict)
    # e.g., {"volatility_multiplier": 1.5, "spread_expansion": 2.0}


@dataclass
class StateTrajectory:
    """Simulated trajectory $P(S_{t+1} \\mid S_t, \\text{action})$."""
    step: int
    expected_price_change: float
    volatility_expansion: float
    drawdown_probability: float
    liquidity_impact: float
    regime_shift_probability: float


@dataclass
class SimulationResult:
    """Output of counterfactual simulation."""
    request_id: str
    proposed_action: str
    expected_value: float
    max_drawdown_risk: float
    win_probability: float
    uncertainty_score: float
    trajectories: List[StateTrajectory]
    invalidation_triggers: List[str] = field(default_factory=list)
