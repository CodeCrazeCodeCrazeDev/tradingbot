"""
Institutional-Grade Market World State Governance Structure
==========================================================

Defines the standardized WorldState structure required for hierarchical
governance and intelligence-core compliance.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any
from datetime import datetime


class VolatilityRegime(Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    EXTREME = "extreme"


class LiquidityCondition(Enum):
    DEEP = "deep"
    NORMAL = "normal"
    THIN = "thin"
    ILLIQUID = "illiquid"


class SystemMode(Enum):
    EXPLORE = "explore"
    EXPLOIT = "exploit"
    NORMAL = "normal"
    REDUCED_RISK = "reduced_risk"
    DEFENSIVE = "defensive"
    OBSERVE_ONLY = "observe_only"
    HALT = "halt"


@dataclass(frozen=True)
class MarketWorldState:
    """
    Standardized WorldState structure for governance.
    This object is the mandatory output of the World Model before any prediction.
    """
    timestamp: float = field(default_factory=lambda: datetime.utcnow().timestamp())
    symbol: str = "EURUSD"

    # Core Regime Classification
    volatility_regime: VolatilityRegime = VolatilityRegime.NORMAL
    liquidity_condition: LiquidityCondition = LiquidityCondition.NORMAL

    # Stability and Pressure Metrics
    trend_stability: float = 0.5  # 0.0 (chaotic) to 1.0 (stable)
    participation_pressure: float = 0.0  # -1.0 (sell) to 1.0 (buy)
    systemic_risk_level: float = 0.1  # 0.0 (safe) to 1.0 (crisis)

    # Uncertainty and Entropy
    regime_entropy: float = 0.0  # Uncertainty in regime classification
    state_confidence: float = 1.0  # 0.0 to 1.0, overall confidence in this state

    # Uncertainty Decomposition
    epistemic_uncertainty: float = 0.0  # Model ignorance (knowledge gap)
    aleatoric_uncertainty: float = 0.0  # Market randomness (noise)

    # Institutional-Grade Metrics
    tail_risk_probability: float = 0.01  # Estimated prob of >3-sigma move
    correlation_regime: float = 0.0  # Average cross-asset correlation (0 to 1)
    sentiment_drift: float = 0.0  # Rate of change in market sentiment
    causal_attribution: Dict[str, float] = field(default_factory=dict)  # Key drivers

    # Governance Integration
    ignorance_score: float = 0.0  # Unified 0.0 to 1.0 ignorance score
    recommended_mode: SystemMode = SystemMode.NORMAL

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "symbol": self.symbol,
            "volatility_regime": self.volatility_regime.value,
            "liquidity_condition": self.liquidity_condition.value,
            "trend_stability": self.trend_stability,
            "participation_pressure": self.participation_pressure,
            "systemic_risk_level": self.systemic_risk_level,
            "regime_entropy": self.regime_entropy,
            "state_confidence": self.state_confidence,
            "epistemic_uncertainty": self.epistemic_uncertainty,
            "aleatoric_uncertainty": self.aleatoric_uncertainty,
            "ignorance_score": self.ignorance_score,
            "recommended_mode": self.recommended_mode.value
        }


@dataclass(frozen=True)
class ScenarioRollout:
    """A simulated trajectory of the future."""
    scenario_id: str
    action_sequence: List[str]  # e.g. ["BUY", "HOLD", "SELL"]
    predicted_states: List[MarketWorldState]  # Step-by-step simulated states
    predicted_prices: Dict[str, List[float]]  # asset -> list of prices
    expected_rewards: List[float]  # Step-by-step rewards
    cumulative_reward: float
    probability: float  # Estimated probability of this scenario
    uncertainty: float  # Rollout-level uncertainty

    def to_dict(self) -> Dict[str, Any]:
        return {
            "scenario_id": self.scenario_id,
            "action_sequence": self.action_sequence,
            "predicted_states": [s.to_dict() for s in self.predicted_states],
            "predicted_prices": self.predicted_prices,
            "expected_rewards": self.expected_rewards,
            "cumulative_reward": self.cumulative_reward,
            "probability": self.probability,
            "uncertainty": self.uncertainty
        }


@dataclass(frozen=True)
class CounterfactualScenario:
    """Results of a counterfactual simulation."""
    question: str  # e.g., "What if volatility doubles?"
    intervention: Dict[str, Any]  # e.g., {"volatility_multiplier": 2.0}
    predicted_states: List[MarketWorldState]
    predicted_prices: Dict[str, List[float]]
    expected_utility: float
    causal_effect: float  # Change in outcome relative to baseline

    def to_dict(self) -> Dict[str, Any]:
        return {
            "question": self.question,
            "intervention": self.intervention,
            "predicted_states": [s.to_dict() for s in self.predicted_states],
            "predicted_prices": self.predicted_prices,
            "expected_utility": self.expected_utility,
            "causal_effect": self.causal_effect
        }


@dataclass(frozen=True)
class ReasoningTrace:
    """
    Structured reasoning trace representing the model's internal cognitive flow.
    Follows: Observation -> Hypothesis -> Evidence -> Causal assumptions -> Rollouts -> Counterfactuals -> Utility estimates -> Chosen policy -> Confidence
    """
    observation: str
    hypothesis: str
    evidence: str
    causal_assumptions: str
    rollouts: str
    counterfactuals: str
    utility_estimates: str
    chosen_policy: str
    confidence: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "observation": self.observation,
            "hypothesis": self.hypothesis,
            "evidence": self.evidence,
            "causal_assumptions": self.causal_assumptions,
            "rollouts": self.rollouts,
            "counterfactuals": self.counterfactuals,
            "utility_estimates": self.utility_estimates,
            "chosen_policy": self.chosen_policy,
            "confidence": self.confidence
        }


@dataclass(frozen=True)
class WorldModelPrediction:
    """
    The canonical prediction object generated by the UnifiedWorldModel.
    Consolidated public output structure of the cognitive planning core.
    """
    latent_state: Any  # Shared latent market representation (e.g., torch.Tensor)
    predicted_states: Dict[str, ScenarioRollout]  # scenario name -> rollout (e.g. Scenario A, B, C)
    counterfactuals: Dict[str, CounterfactualScenario]  # question -> counterfactual
    probabilities: Dict[str, float]  # scenario probability distribution

    # Uncertainty decomposition
    epistemic_uncertainty: float
    aleatoric_uncertainty: float
    calibration_score: float

    causal_graph: Dict[str, Any]  # Causal graph structure/SCM coefficients
    expected_rewards: Dict[str, float]  # action -> expected reward
    policy_logits: Dict[str, float]  # action -> recommendation score
    reasoning_trace: ReasoningTrace

    recommended_action: str
    expected_confidence: float

    # Deterministic replay and reproducibility metadata
    model_version: str = "2.0.0"
    configuration_hash: str = ""
    feature_version: str = "1.0"
    training_dataset_version: str = "1.0"
    random_seed: int = 42
    inference_timestamp: float = field(default_factory=lambda: datetime.utcnow().timestamp())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "predicted_states": {k: v.to_dict() for k, v in self.predicted_states.items()},
            "counterfactuals": {k: v.to_dict() for k, v in self.counterfactuals.items()},
            "probabilities": self.probabilities,
            "epistemic_uncertainty": self.epistemic_uncertainty,
            "aleatoric_uncertainty": self.aleatoric_uncertainty,
            "calibration_score": self.calibration_score,
            "causal_graph": self.causal_graph,
            "expected_rewards": self.expected_rewards,
            "policy_logits": self.policy_logits,
            "reasoning_trace": self.reasoning_trace.to_dict(),
            "recommended_action": self.recommended_action,
            "expected_confidence": self.expected_confidence,
            "model_version": self.model_version,
            "configuration_hash": self.configuration_hash,
            "feature_version": self.feature_version,
            "training_dataset_version": self.training_dataset_version,
            "random_seed": self.random_seed,
            "inference_timestamp": self.inference_timestamp
        }
