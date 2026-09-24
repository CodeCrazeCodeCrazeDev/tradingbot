"""
Adaptive Control Policy Engine (ACPE) - UCA V6 Core (2026)
Generic, lightweight, sub-millisecond retrieval-based control parameterizer.
Parameterizes existing subsystems inside the "One Brain" pipeline based on historical failures.

UCA-2026 Scientific Research Traceability Matrix:
- REF-01 (LogAct): Shared transactional ledger for agentic consensus (arXiv:2605.29303)
- REF-02 (SAGE): Self-Evolving Agentic Graph-Memory Engine integration (arXiv:2607.00341)
- REF-03 (AutoMem): Meta-Memory Schema Migration & Persistence (arXiv:2607.01224)
- REF-04 (HASP): Hierarchical Skill Programs with Guardrails (arXiv:2605.12061)
- REF-05 (S2L): Skill-to-LoRA Behavioral Adapters (arXiv:2605.10813)
- REF-06 (DiscoLoop): Discrete-Continuous Reasoning Loops (arXiv:2605.20025)
- REF-07 (AutoResearchClaw): Refinement & Falsification Engine (arXiv:2605.17734)
- REF-08 (DeepWeb-Bench): Real-Time Market Grounding (arXiv:2605.21482)
"""

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
import time

import numpy as np

logger = logging.getLogger(__name__)


def eksft_mask(
    policy_probs: np.ndarray,
    reference_probs: np.ndarray,
    entropy_floor: float = 0.5,
    kl_ceiling: float = 0.1,
) -> np.ndarray:
    """
    EKSFT (arXiv:2605.29303): Entropy-KL selective token masking.

    A position receives a policy update only when:
      - its predictive entropy is at or above ``entropy_floor`` (the policy is
        still uncertain there — updating preserves exploration capacity), AND
      - its KL divergence from the reference policy is at or below
        ``kl_ceiling`` (the compliance gate — prevent runaway drift).

    Positions with low entropy (already confident) or excessive KL are masked
    out, preventing distribution sharpening and policy collapse.

    Args:
        policy_probs: Current policy distribution, shape (..., vocab).
        reference_probs: Reference/frozen policy distribution, same shape.
        entropy_floor: Minimum entropy (nats) for a position to be updated.
        kl_ceiling: Maximum allowed KL(policy || reference) per position.

    Returns:
        Boolean mask, shape policy_probs.shape[:-1], True where update applies.
    """
    probs = np.clip(np.asarray(policy_probs, dtype=np.float64), 1e-12, 1.0)
    ref = np.clip(np.asarray(reference_probs, dtype=np.float64), 1e-12, 1.0)

    entropy = -np.sum(probs * np.log(probs), axis=-1)
    kl = np.sum(probs * np.log(probs / ref), axis=-1)
    return (entropy >= entropy_floor) & (kl <= kl_ceiling)

@dataclass
class HarnessConfig:
    """Type-safe parameter configuration of the 6D control surfaces."""
    # D1: Context
    prompt_template: str = "default_trading_scaffold_v5"
    retrieval_depth: int = 5
    demonstration_count: int = 3

    # D2: Tool
    active_tools: List[str] = field(default_factory=lambda: ["orderflow_obi", "execution_twap", "risk_exposure"])
    ranking_policy: str = "semantic_match"

    # D3: Generation
    temperature: float = 0.0
    max_tokens: int = 4096
    confidence_threshold: float = 0.85

    # D4: Orchestration
    max_iterations: int = 3
    debate_rounds: int = 2
    simulation_budget: int = 5

    # D5: Memory
    summarization_interval: int = 2
    max_graph_nodes: int = 500
    purge_threshold: float = 0.7

    # D6: Output
    enforce_schema: bool = True
    fallback_action: str = "HOLD"
    shield_strictness: str = "HIGH"

class AdaptiveControlPolicyEngine:
    """
    Sub-millisecond retrieval-based control parameterizer (ACPE / Evolution Gate).
    Enforces safe default fallbacks and adapts parameters based on market volatility and error counts.

    Scientific Traceability:
    - HASP (arXiv:2605.12061): Prescriptive guardrail bounds and strict safety gates
    - AutoResearchClaw (arXiv:2605.17734): Multi-metric protected evolutionary gate
    """
    def __init__(self, hms: Any = None):
        self.hms = hms
        # Pre-compiled high-performance policy cache (SQLite or in-memory dictionary lookup)
        self._policy_cache: Dict[str, HarnessConfig] = {
            "default": HarnessConfig(),
            "high_volatility": HarnessConfig(
                retrieval_depth=8,
                temperature=0.0,
                max_iterations=5,
                debate_rounds=3,
                simulation_budget=8,
                shield_strictness="CRITICAL",
                fallback_action="HOLD"
            ),
            "low_volatility": HarnessConfig(
                retrieval_depth=3,
                demonstration_count=1,
                max_iterations=2,
                debate_rounds=1,
                shield_strictness="NORMAL"
            ),
            "high_errors": HarnessConfig(
                retrieval_depth=10,
                demonstration_count=5,
                max_iterations=5,
                enforce_schema=True,
                shield_strictness="CRITICAL"
            )
        }

    def parameterize_pipeline(self, observation: Dict[str, Any]) -> HarnessConfig:
        """
        Determines and returns the HarnessConfig inside a strict sub-millisecond bound.
        """
        t0 = time.perf_counter()

        try:
            # 1. Inspect nested volatility from observation
            market_data = observation.get("market", observation)
            volatility = market_data.get("volatility", observation.get("volatility", 0.0))
            recent_errors = observation.get("features", {}).get("recent_errors", 0) if isinstance(observation.get("features"), dict) else 0

            # 2. Select appropriate pre-compiled policy template
            if volatility > 0.3:
                config = self._policy_cache["high_volatility"]
                logger.info(f"ACPE: Dynamic parameterization selected [high_volatility] policy based on volatility={volatility:.2f}")
            elif recent_errors > 2:
                config = self._policy_cache["high_errors"]
                logger.info("ACPE: Dynamic parameterization selected [high_errors] policy based on recent_errors count")
            elif volatility < 0.05 and volatility > 0.0:
                config = self._policy_cache["low_volatility"]
                logger.info("ACPE: Dynamic parameterization selected [low_volatility] policy")
            else:
                config = self._policy_cache["default"]

            latency_ms = (time.perf_counter() - t0) * 1000
            logger.debug(f"ACPE: Pipeline parameterized in {latency_ms:.4f}ms")
            return config

        except Exception as e:
            logger.error(f"ACPE: Error during parameterization, falling back to default harness config: {e}")
            return self._policy_cache["default"]

    def masked_policy_update(
        self,
        policy_probs: np.ndarray,
        reference_probs: np.ndarray,
        update: np.ndarray,
        entropy_floor: float = 0.5,
        kl_ceiling: float = 0.1,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Applies the EKSFT selective mask to a candidate policy update.

        Returns (masked_update, mask): updates are zeroed wherever the mask is
        False, preserving exploration and enforcing the KL compliance gate.
        """
        mask = eksft_mask(policy_probs, reference_probs, entropy_floor, kl_ceiling)
        update = np.asarray(update, dtype=np.float64)
        # The mask is per-position; expand over trailing vocab dims of the update.
        expanded = mask
        while expanded.ndim < update.ndim:
            expanded = np.expand_dims(expanded, axis=-1)
        masked = np.where(expanded, update, 0.0)
        kept = int(mask.sum())
        total = int(mask.size)
        logger.debug(f"ACPE: EKSFT mask kept {kept}/{total} update positions "
                     f"(entropy_floor={entropy_floor}, kl_ceiling={kl_ceiling})")
        return masked, mask
