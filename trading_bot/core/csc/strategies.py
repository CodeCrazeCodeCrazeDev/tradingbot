"""
Thinking Strategies - UCA-2026 CSC Reasoning Lenses
====================================================

Canonical reasoning strategies wired into the Cognitive System Controller's
hypothesis stage (``HypothesisGenerator.generate_competing_branches``). Each
strategy analyzes the same market observation through a distinct thinking lens
and returns a competing hypothesis:

- First-Principles: decompose the observation into irreducible drivers
  (net order-flow pressure vs. volatility cost) and rebuild the thesis
  bottom-up rather than reasoning by analogy.
- Systems Thinking: model the market as a feedback system — sentiment,
  trend and liquidity interact and their combined effect is damped by the
  volatility regime (second-order effects dominate unstable regimes).
- Analytical Thinking: statistical evidence weighting — a normalized
  composite score whose uncertainty grows with signal conflict.
- Creative Thinking: adversarial/contrarian generation covering the scenario
  the consensus lenses miss (crowded-trade traps, tail scenarios).

All strategies are pure, deterministic functions of the observation so the
12-stage pipeline stays replay-consistent.
"""

import math
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class ThinkingMode(Enum):
    FIRST_PRINCIPLES = "first_principles"
    SYSTEMS = "systems_thinking"
    ANALYTICAL = "analytical_thinking"
    CREATIVE = "creative_thinking"


def _as_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


@dataclass(frozen=True)
class ObservationFeatures:
    """Normalized numeric view of a raw market observation."""

    symbol: str
    price: float
    volume: float
    volume_signal: float  # participation proxy, squashed to (-1, 1)
    volatility: float
    sentiment: float
    trend: float
    momentum: float
    liquidity: float
    ref_price: float


def extract_features(observation: Dict[str, Any]) -> ObservationFeatures:
    """Deterministically normalize a heterogeneous observation dict."""
    obs = observation if isinstance(observation, dict) else {}
    price = _as_float(obs.get("price") or obs.get("close"))
    volume = _as_float(obs.get("volume"))
    volatility = _as_float(obs.get("volatility"), 0.02)
    sentiment = max(-1.0, min(1.0, _as_float(obs.get("sentiment"))))
    trend = max(-1.0, min(1.0, _as_float(obs.get("trend"))))
    momentum = max(-1.0, min(1.0, _as_float(obs.get("momentum"))))
    liquidity = _as_float(obs.get("liquidity"))
    return ObservationFeatures(
        symbol=str(obs.get("symbol", "unknown")),
        price=price,
        volume=volume,
        volume_signal=math.tanh(volume / 1e6) if volume > 0 else 0.0,
        volatility=volatility,
        sentiment=sentiment,
        trend=trend,
        momentum=momentum,
        liquidity=liquidity,
        ref_price=price if price > 0 else 1.0,
    )


@dataclass
class StrategyAnalysis:
    """Lens output consumed by HypothesisGenerator to build a ReasoningBranch."""

    mode: ThinkingMode
    display_name: str
    score: float  # directional conviction in [-1, 1]
    conviction: float  # raw strength used for branch confidence/probability
    uncertainty: float
    causal_explanation: str
    invalidation_conditions: List[str] = field(default_factory=list)


ACTION_THRESHOLD = 0.12


def score_to_action(score: float) -> str:
    if score > ACTION_THRESHOLD:
        return "BUY"
    if score < -ACTION_THRESHOLD:
        return "SELL"
    return "WAIT"


class ThinkingStrategy:
    """Base class for a reasoning lens. Subclasses implement ``_evaluate``."""

    mode: ThinkingMode = ThinkingMode.ANALYTICAL
    display_name: str = "Thinking Strategy"

    def analyze(self, features: ObservationFeatures) -> StrategyAnalysis:
        score, conviction, uncertainty, explanation, invalidations = self._evaluate(features)
        score = max(-1.0, min(1.0, score))
        conviction = max(0.05, min(0.95, conviction))
        uncertainty = max(0.0, min(0.95, uncertainty))
        return StrategyAnalysis(
            mode=self.mode,
            display_name=self.display_name,
            score=score,
            conviction=conviction,
            uncertainty=uncertainty,
            causal_explanation=explanation,
            invalidation_conditions=list(invalidations),
        )

    def _evaluate(self, features: ObservationFeatures):
        raise NotImplementedError


class FirstPrinciplesThinking(ThinkingStrategy):
    """Decompose to primitives: net flow pressure against volatility cost."""

    mode = ThinkingMode.FIRST_PRINCIPLES
    display_name = "First-Principles Decomposition"

    def _evaluate(self, f: ObservationFeatures):
        flow = 0.55 * f.sentiment + 0.35 * f.trend + 0.10 * f.momentum
        vol_cost = max(0.0, f.volatility - 0.03) * 8.0
        score = math.tanh(flow - 0.25 * vol_cost)
        conviction = 0.55 + 0.40 * abs(score)
        uncertainty = 0.10 + 0.15 * min(1.0, f.volatility / 0.1)
        explanation = (
            f"Decomposed {f.symbol} to primitives: net flow pressure {flow:.3f} "
            f"(sentiment {f.sentiment:+.2f}, trend {f.trend:+.2f}, momentum {f.momentum:+.2f}) "
            f"against volatility cost {vol_cost:.3f}."
        )
        invalidations = [
            "Net flow pressure flips sign against the thesis",
            f"Volatility regime expands materially above {f.volatility:.3f}",
        ]
        return score, conviction, uncertainty, explanation, invalidations


class SystemsThinking(ThinkingStrategy):
    """Feedback-system view: interacting drivers damped by regime stability."""

    mode = ThinkingMode.SYSTEMS
    display_name = "Systems-Feedback Analysis"

    def _evaluate(self, f: ObservationFeatures):
        raw = (
            0.40 * f.sentiment
            + 0.30 * f.trend
            + 0.30 * math.tanh(f.liquidity)
        )
        # Volatility regime acts as negative feedback on every driver; in
        # unstable regimes the system's second-order effects dominate.
        feedback = 1.0 + 3.0 * max(0.0, f.volatility)
        score = raw / feedback
        conviction = 0.50 + 0.35 * abs(raw)
        uncertainty = 0.15 + 0.20 * min(1.0, f.volatility / 0.1)
        explanation = (
            f"System view of {f.symbol}: coupled drivers (sentiment {f.sentiment:+.2f}, "
            f"trend {f.trend:+.2f}, liquidity {f.liquidity:+.2f}) produce raw flow {raw:.3f}, "
            f"damped {feedback:.2f}x by the {f.volatility:.3f} volatility regime."
        )
        invalidations = [
            "Volatility feedback regime shifts (expansion or collapse)",
            "Liquidity inflow reverses into a drain (>20% drop)",
        ]
        return score, conviction, uncertainty, explanation, invalidations


class AnalyticalThinking(ThinkingStrategy):
    """Statistical evidence weighting with conflict-driven uncertainty."""

    mode = ThinkingMode.ANALYTICAL
    display_name = "Analytical Evidence Weighting"

    WEIGHTS = {"sentiment": 0.5, "momentum": 0.3, "participation": 0.2}

    def _evaluate(self, f: ObservationFeatures):
        parts = {
            "sentiment": f.sentiment,
            "momentum": f.momentum,
            "participation": f.volume_signal,
        }
        score = sum(self.WEIGHTS[k] * v for k, v in parts.items())
        denom = sum(self.WEIGHTS[k] * abs(v) for k, v in parts.items())
        conflict = 1.0 - (abs(score) / denom) if denom > 0 else 1.0
        conviction = 0.50 + 0.45 * abs(score) * (1.0 - 0.5 * conflict)
        uncertainty = 0.10 + 0.30 * conflict
        explanation = (
            f"Weighted evidence for {f.symbol}: sentiment {f.sentiment:+.2f} (w=0.5), "
            f"momentum {f.momentum:+.2f} (w=0.3), participation {f.volume_signal:+.2f} (w=0.2) "
            f"-> composite {score:.3f} with signal conflict {conflict:.2f}."
        )
        invalidations = [
            "Composite signal decays below the action threshold",
            "Evidence conflict rises as indicators diverge",
        ]
        return score, conviction, uncertainty, explanation, invalidations


class CreativeThinking(ThinkingStrategy):
    """Adversarial hypothesis: contrarian trap or exploratory tail scenario."""

    mode = ThinkingMode.CREATIVE
    display_name = "Creative Contrarian Analysis"

    def _evaluate(self, f: ObservationFeatures):
        consensus = 0.6 * f.sentiment + 0.4 * f.trend
        if abs(consensus) > 0.25:
            # Crowded read: hypothesize the trap — direction opposite consensus.
            score = -0.65 * consensus
            explanation = (
                f"Contrarian read on {f.symbol}: consensus {consensus:+.3f} looks crowded; "
                f"hypothesize the trap/liquidation move in the opposite direction."
            )
            invalidations = [
                "Consensus positioning unwinds without a squeeze",
                "Contrarian tail fails to attract follow-through flow",
            ]
        else:
            # No crowd to fade: exploratory tail scenario from participation.
            score = 0.3 * f.volume_signal + 0.2 * f.sentiment
            explanation = (
                f"Exploratory tail scenario for {f.symbol}: no crowded consensus "
                f"({consensus:+.3f}); participation {f.volume_signal:+.2f} may front-run "
                f"a regime break the consensus lenses underweight."
            )
            invalidations = [
                "Participation signal fades back to baseline",
                "A crowded consensus forms, invalidating the tail read",
            ]
        conviction = 0.45 + 0.30 * abs(consensus)
        uncertainty = 0.35
        return score, conviction, uncertainty, explanation, invalidations


def default_thinking_strategies() -> List[ThinkingStrategy]:
    """The canonical lens set wired into the CSC hypothesis stage."""
    return [
        FirstPrinciplesThinking(),
        SystemsThinking(),
        AnalyticalThinking(),
        CreativeThinking(),
    ]
