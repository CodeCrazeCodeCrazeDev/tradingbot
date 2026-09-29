import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, Iterable, List, Optional

import numpy as np
import torch

logger = logging.getLogger(__name__)

class PlanResult:
    def __init__(self, plan_id: str, actions: List[Dict]):
        self.plan_id = plan_id
        self.actions = actions

class ImaginationPlanner:
    """Canonical V2-compatible Imagination Planner."""
    def __init__(self, world_model: Any = None):
        self.world_model = world_model

    async def generate_plan(self, observation: Dict) -> PlanResult:
        logger.info("ImaginationPlanner: Generating plan from world model")
        return PlanResult("plan_123", [])

class CEMPlanner(ImaginationPlanner):
    """Cross-Entropy Method Planner."""
    pass

class FutureSimulator:
    """Deterministic scenario rollout for the PlanningEngine."""
    def __init__(self, n_scenarios: int = 4, horizon: int = 8):
        self.n_scenarios = n_scenarios
        self.horizon = horizon

    def simulate_scenarios(self, z_plan: torch.Tensor) -> List[Dict[str, Any]]:
        # Deterministic rollouts: mean-reverting drift with fixed seeds.
        scenarios = []
        for i in range(self.n_scenarios):
            g = torch.Generator().manual_seed(i)
            drift = (i / max(self.n_scenarios - 1, 1) - 0.5) * 0.02
            noise = torch.randn(self.horizon, *z_plan.shape, generator=g) * 0.01
            trajectory = z_plan.unsqueeze(0) + drift + noise.cumsum(dim=0)
            scenarios.append({"trajectory": trajectory, "probability": 1.0 / self.n_scenarios})
        return scenarios

class PlanningEngine:
    """
    Predictive Planning Engine.
    Evaluates candidate plans across all generated future scenarios.
    """
    def __init__(self, simulator: Optional[FutureSimulator] = None, causal_engine: Any = None):
        self.simulator = simulator or FutureSimulator()
        self.causal_engine = causal_engine

    def find_optimal_plan(self, z_t: torch.Tensor, candidates: List[Dict]) -> Dict[str, Any]:
        """
        Lookahead Search using Expected Utility across future scenarios.
        Objective: minimize Expected Free Energy (EFE).
        """
        best_plan = None
        max_utility = -float('inf')

        for plan in candidates:
            # 1. Apply intervention: do(plan)
            z_plan = self.causal_engine.do_intervention(z_t, plan)

            # 2. Simulate futures from the intervened state
            scenarios = self.simulator.simulate_scenarios(z_plan)

            # 3. Calculate Expected Utility (Weighted sum across scenarios)
            utility = 0
            for s in scenarios:
                reward = self._estimate_reward(s["trajectory"])
                utility += s["probability"] * reward

            if utility > max_utility:
                max_utility = utility
                best_plan = plan

        logger.info(f"Planner: Selected plan with Expected Utility {max_utility:.4f}")
        return best_plan

    def _estimate_reward(self, trajectory: torch.Tensor) -> float:
        # Mock: in production this uses the Risk/Alpha heads
        return float(trajectory.mean())


class AdversarialSelfPlay:
    """L3+L5+L7 loop: adversarially stress the world model and planner."""

    def __init__(self, planner: Callable[[Dict[str, Any]], Any], adversary: Callable[[Dict[str, Any]], Dict[str, Any]]) -> None:
        self.planner = planner
        self.adversary = adversary
        self.history: List[Dict[str, Any]] = []

    def run_round(self, context: Dict[str, Any]) -> Dict[str, Any]:
        attacked = self.adversary(context)
        plan = self.planner(attacked)
        score = float(attacked.get("stress", 0.0)) - float(attacked.get("resilience", 0.0))
        result = {"attacked_context": attacked, "plan": plan, "adversarial_score": score}
        self.history.append(result)
        return result


# ============================================================
# Restored: compliance/contact-mode/adversarial loop classes
# (originally in pre-merge world_model.imagination)
# ============================================================

class ContactMode(str, Enum):
    FREE = "free"
    CONTACT = "contact"
    SLIP = "slip"
    IMPACT = "impact"
    HALT = "halt"


@dataclass(frozen=True)
class ContactModeDecision:
    mode: ContactMode
    confidence: float
    reason: str


class ContactModeSwitcher:
    """Selects the actor-controller contact mode from surprise/liquidity signals."""

    def __init__(
        self,
        *,
        impact_threshold: float = 0.85,
        slip_threshold: float = 0.55,
        halt_threshold: float = 0.95,
    ) -> None:
        self.impact_threshold = impact_threshold
        self.slip_threshold = slip_threshold
        self.halt_threshold = halt_threshold
        self.history: List[ContactModeDecision] = []

    def select_mode(self, signals: Dict[str, float]) -> ContactModeDecision:
        surprise = float(signals.get("surprise", 0.0))
        liquidity_gap = float(signals.get("liquidity_gap", 0.0))
        slippage = float(signals.get("slippage", 0.0))
        halt_probability = float(signals.get("halt_probability", 0.0))
        stress = max(surprise, liquidity_gap, slippage)

        if halt_probability >= self.halt_threshold:
            decision = ContactModeDecision(ContactMode.HALT, halt_probability, "halt probability above threshold")
        elif stress >= self.impact_threshold:
            decision = ContactModeDecision(ContactMode.IMPACT, stress, "impact/contact stress above threshold")
        elif slippage >= self.slip_threshold or liquidity_gap >= self.slip_threshold:
            decision = ContactModeDecision(ContactMode.SLIP, max(slippage, liquidity_gap), "slip regime detected")
        elif surprise >= self.slip_threshold:
            decision = ContactModeDecision(ContactMode.CONTACT, surprise, "surprise implies contact-mode transition")
        else:
            decision = ContactModeDecision(ContactMode.FREE, 1.0 - stress, "free mode")

        self.history.append(decision)
        return decision


@dataclass(frozen=True)
class ComplianceAction:
    approved: bool
    adjusted_action: Dict[str, Any]
    violations: List[str]
    mode: ContactMode
    risk_multiplier: float


class ComplianceController:
    """Constrains actor-controller output by contact mode and hard risk limits."""

    def __init__(
        self,
        *,
        max_notional: float = 100_000.0,
        max_leverage: float = 2.0,
        mode_risk_multipliers: Optional[Dict[ContactMode, float]] = None,
    ) -> None:
        self.max_notional = max_notional
        self.max_leverage = max_leverage
        self.mode_risk_multipliers = mode_risk_multipliers or {
            ContactMode.FREE: 1.0,
            ContactMode.CONTACT: 0.7,
            ContactMode.SLIP: 0.5,
            ContactMode.IMPACT: 0.25,
            ContactMode.HALT: 0.0,
        }

    def constrain(self, action: Dict[str, Any], mode: ContactMode) -> ComplianceAction:
        adjusted = dict(action)
        violations: List[str] = []
        multiplier = self.mode_risk_multipliers.get(mode, 0.0)

        notional = float(adjusted.get("notional", 0.0))
        leverage = float(adjusted.get("leverage", 1.0))
        if notional > self.max_notional:
            violations.append("notional_clipped")
            adjusted["notional"] = self.max_notional
        if leverage > self.max_leverage:
            violations.append("leverage_clipped")
            adjusted["leverage"] = self.max_leverage

        adjusted["notional"] = float(adjusted.get("notional", 0.0)) * multiplier
        if multiplier == 0.0:
            adjusted["decision"] = "HOLD"
            violations.append("mode_forced_hold")

        return ComplianceAction(
            approved=multiplier > 0.0,
            adjusted_action=adjusted,
            violations=violations,
            mode=mode,
            risk_multiplier=multiplier,
        )


class ResidualDiffusionRefiner:
    """Bounded residual refinement over a compliant base action."""

    def __init__(self, *, residual_scale: float = 0.05, seed: int = 7) -> None:
        self.residual_scale = residual_scale
        self.rng = np.random.default_rng(seed)

    def refine(
        self,
        action: Dict[str, Any],
        *,
        risk_multiplier: float,
        max_notional: Optional[float] = None,
    ) -> Dict[str, Any]:
        refined = dict(action)
        if "notional" in refined and risk_multiplier > 0:
            residual = self.rng.normal(0.0, self.residual_scale) * risk_multiplier
            notional = float(refined["notional"]) * (1.0 + residual)
            if max_notional is not None:
                notional = min(notional, max_notional)
            refined["notional"] = max(0.0, notional)
            refined["residual_refinement"] = residual
        return refined


# =============================================================================
# Cross-Cutting Ceiling-Pushed Loops
# =============================================================================

class DreamAndVerifyLoop:
    """L5+L10 loop: dream counterfactuals, then verify them with a shield."""

    def __init__(self, simulator: Callable[[Dict[str, Any]], Iterable[Dict[str, float]]], shield: Any) -> None:
        self.simulator = simulator
        self.shield = shield

    def run(self, seed_context: Dict[str, Any]) -> Dict[str, Any]:
        dreams = list(self.simulator(seed_context))
        decisions = [self.shield.evaluate(dream) for dream in dreams]
        accepted = [dream for dream, decision in zip(dreams, decisions) if decision.approved]
        return {
            "dreams": len(dreams),
            "accepted": len(accepted),
            "blocked": len(dreams) - len(accepted),
            "degradation_levels": [decision.degradation_level.value for decision in decisions],
        }


class CausalAgentLoop:
    """B2+B3+L7 loop: probe causal context, repair options, and re-plan."""

    def __init__(self, planner: Callable[[Dict[str, Any]], Any], repairer: Callable[[Any, Dict[str, Any]], Any]) -> None:
        self.planner = planner
        self.repairer = repairer

    def run(self, causal_context: Dict[str, Any]) -> Dict[str, Any]:
        plan = self.planner(causal_context)
        repaired = self.repairer(plan, causal_context)
        return {"plan": plan, "repaired_plan": repaired, "changed": plan != repaired}


