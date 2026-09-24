"""Probabilistic World Model and Counterfactual Simulator under temporal causality."""

import math
import zlib
import logging
from typing import Dict, Any, List, Optional
import numpy as np
from trading_bot.cognition.state.contracts import MarketState
from .contracts import SimulationRequest, SimulationResult, StateTrajectory

logger = logging.getLogger("alphaalgo.cognition.simulation")


class CounterfactualSimulator:
    """Evaluates candidate actions under probabilistic future market state trajectories."""

    _MC_DF = 4.0  # Student-t degrees of freedom — fat tails per hostile-audit rec

    def _per_bar_sigma(self, state: MarketState, vol_mult: float) -> float:
        """Empirical per-bar sigma: prefer observed M15 range, else map the
        volatility percentile onto a sane return-vol envelope."""
        struct = getattr(state, "timescale_structure", {}) or {}
        rng = struct.get("M15", {}).get("range")
        if isinstance(rng, (int, float)) and rng > 0:
            return float(rng) * 0.5 * vol_mult  # range ≈ 2σ heuristic
        pct = float(getattr(state, "volatility_percentile", 0.5) or 0.5)
        return (0.0002 + 0.004 * pct) * vol_mult

    def _monte_carlo(self, request: SimulationRequest, state: MarketState,
                     aligned: bool, vol_mult: float) -> Dict[str, float]:
        """Fat-tailed Monte Carlo: Student-t shocks, seeded by request_id so
        the same observation always produces the same empiricals (determinism)."""
        rng = np.random.default_rng(zlib.crc32(request.request_id.encode()))
        n = max(32, request.monte_carlo_paths)
        horizon = max(1, request.time_horizon_bars)
        sigma = self._per_bar_sigma(state, vol_mult)
        drift = 0.0002 * (1.2 if aligned else -0.8)
        sign = 1.0 if request.proposed_action == "BUY" else (-1.0 if request.proposed_action == "SELL" else 0.0)

        # Standardized Student-t (unit variance) shocks
        t_scale = math.sqrt(self._MC_DF / (self._MC_DF - 2.0))
        shocks = rng.standard_t(self._MC_DF, size=(n, horizon)) / t_scale
        path_returns = drift + sigma * shocks  # (n, horizon)

        terminal = path_returns.sum(axis=1) * sign
        # max drawdown of the action-direction cumulative path per sample
        cum = np.cumsum(path_returns * sign, axis=1)
        running_max = np.maximum.accumulate(cum, axis=1)
        max_dd = np.max(running_max - cum, axis=1)

        return {
            "mc_win_probability": float(np.mean(terminal > 0)),
            "mc_expected_value": float(np.mean(terminal)) * request.position_size,
            "mc_p95_drawdown": float(np.quantile(max_dd, 0.95)),
            "mc_paths": n,
        }

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

        # Optional fat-tailed Monte Carlo: blend empirical win prob with the
        # heuristic. MC drawdown is reported separately (mc_p95_drawdown) —
        # it is measured in different units than the heuristic gate's max_dd
        # threshold, so it informs rather than vetoes.
        mc: Dict[str, float] = {}
        if request.monte_carlo_paths > 0:
            mc = self._monte_carlo(request, state, aligned, vol_mult)
            base_win_prob = 0.5 * base_win_prob + 0.5 * mc["mc_win_probability"]

        return SimulationResult(
            request_id=request.request_id,
            proposed_action=action,
            expected_value=round(cum_ev * size, 6),
            max_drawdown_risk=round(max_dd, 6),
            win_probability=round(base_win_prob, 4),
            uncertainty_score=round(getattr(state, "uncertainty", 0.2) * vol_mult, 4),
            trajectories=trajectories,
            invalidation_triggers=invalidation,
            mc_paths=int(mc.get("mc_paths", 0)),
            mc_win_probability=mc.get("mc_win_probability"),
            mc_expected_value=mc.get("mc_expected_value"),
            mc_p95_drawdown=mc.get("mc_p95_drawdown"),
        )
