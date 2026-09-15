"""Probabilistic World Model and Counterfactual Simulator under temporal causality."""

import math
import logging
from typing import Dict, Any, List, Optional
from trading_bot.cognition.state.contracts import MarketState
from .contracts import SimulationRequest, SimulationResult, StateTrajectory

logger = logging.getLogger("alphaalgo.cognition.simulation")


class CounterfactualSimulator:
    """Evaluates candidate actions under probabilistic future market state trajectories."""

    def simulate(self, request: SimulationRequest) -> SimulationResult:
        state: MarketState = request.current_state
        action = request.proposed_action
        size = request.position_size

        vol_mult = request.scenario_adjustments.get("volatility_multiplier", 1.0)
        spread_mult = request.scenario_adjustments.get("spread_expansion", 1.0)

        trajectories = []
        cum_ev = 0.0
        max_dd = 0.0

        trend_dir = getattr(state, "trend_direction", "NEUTRAL")
        trend_str = getattr(state, "trend_strength", 0.5)

        # Action alignment with trend
        aligned = (action == "BUY" and trend_dir == "BULLISH") or (action == "SELL" and trend_dir == "BEARISH")
        opposed = (action == "BUY" and trend_dir == "BEARISH") or (action == "SELL" and trend_dir == "BULLISH")

        base_win_prob = 0.55 if aligned else (0.35 if opposed else 0.45)
        base_win_prob /= max(1.0, (vol_mult * 0.2 + spread_mult * 0.1))

        for step in range(1, request.time_horizon_bars + 1):
            step_return = (0.0002 * step * (1.2 if aligned else -0.8)) / math.sqrt(step)
            step_vol = 0.001 * vol_mult * math.sqrt(step)
            step_dd = max(0.0, step_vol * 1.5 - step_return)

            trajectories.append(
                StateTrajectory(
                    step=step,
                    expected_price_change=round(step_return, 6),
                    volatility_expansion=round(step_vol, 6),
                    drawdown_probability=round(min(0.99, step_dd * 100), 4),
                    liquidity_impact=round(0.0001 * size * spread_mult, 6),
                    regime_shift_probability=round(min(0.50, 0.05 * step * vol_mult), 4)
                )
            )
            cum_ev += step_return
            if step_dd > max_dd:
                max_dd = step_dd

        invalidation = []
        if max_dd > 0.005:
            invalidation.append("Maximum acceptable drawdown threshold exceeded")
        if spread_mult > 1.5:
            invalidation.append("Severe spread expansion scenario detected")

        return SimulationResult(
            request_id=request.request_id,
            proposed_action=action,
            expected_value=round(cum_ev * size, 6),
            max_drawdown_risk=round(max_dd, 6),
            win_probability=round(base_win_prob, 4),
            uncertainty_score=round(getattr(state, "uncertainty", 0.2) * vol_mult, 4),
            trajectories=trajectories,
            invalidation_triggers=invalidation
        )
