"""
Mythos recurrent reasoning layer.

This module keeps the historic ChainOfThoughtReasoner public API while replacing
the stub with a compact recurrent latent reasoning loop and a Verifiable Logic
Kernel (VLK) backed by the existing LogicalVerifier.
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
import math
import threading
from collections.abc import Iterable
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Sequence

try:
    from trading_bot.autonomous_financial_intelligence.verified_reasoning.logical_verifier import (
        ArgumentForm,
        LogicalVerifier,
        VerificationStatus,
    )
except Exception:  # pragma: no cover - fallback keeps core import resilient.
    ArgumentForm = None
    LogicalVerifier = None
    VerificationStatus = None

logger = logging.getLogger(__name__)


class ReasoningMode(str, Enum):
    """Reasoning domains supported by Mythos."""

    ANALYSIS = "analysis"
    TRADE = "trade"
    PROOF = "proof"
    VULNERABILITY = "vulnerability"


@dataclass
class ChainOfThoughtReasonerConfig:
    """Configuration for ChainOfThoughtReasoner."""

    enabled: bool = True
    max_reasoning_loops: int = 6
    latent_dim: int = 16
    convergence_threshold: float = 0.025
    oscillation_threshold: float = 0.015
    logic_validity_threshold: float = 0.80
    min_settledness: float = 0.55
    expert_locking_enabled: bool = True
    expert_lock_margin: float = 0.08
    red_blue_enabled: bool = True
    params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LatentThoughtState:
    """Compact internal state for one recurrent reasoning iteration."""

    iteration: int
    vector: List[float]
    energy: float
    delta: float
    settledness: float
    dead_end: bool = False
    oscillating: bool = False
    note: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ReasoningStep:
    """Human-auditable summary of one latent refinement step."""

    iteration: int
    mode: str
    expert_scores: Dict[str, float]
    conclusion: str
    confidence: float
    premises: List[str]
    settledness: float
    logic_locked: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class LogicKernelResult:
    """Output from the Verifiable Logic Kernel."""

    premises: List[str]
    conclusion: str
    status: str
    validity_score: float
    soundness_score: float
    fallacies: List[Dict[str, Any]] = field(default_factory=list)
    consistency_issues: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    verified: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class RedBlueReview:
    """Attacker/defender review for vulnerability-oriented reasoning."""

    attacker_hypothesis: str
    defender_response: str
    attack_premises: List[str]
    defense_premises: List[str]
    exploit_path: str
    exploit_verification: LogicKernelResult
    defense_verification: LogicKernelResult
    risk_score: float
    verdict: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "attacker_hypothesis": self.attacker_hypothesis,
            "defender_response": self.defender_response,
            "attack_premises": list(self.attack_premises),
            "defense_premises": list(self.defense_premises),
            "exploit_path": self.exploit_path,
            "exploit_verification": self.exploit_verification.to_dict(),
            "defense_verification": self.defense_verification.to_dict(),
            "risk_score": self.risk_score,
            "verdict": self.verdict,
        }


@dataclass
class ReasoningTrace:
    """Compact audit trace emitted after the recurrent loop settles."""

    mode: str
    states: List[LatentThoughtState]
    steps: List[ReasoningStep]
    converged: bool
    settledness_score: float
    locked_logic: Optional[LogicKernelResult] = None
    locked_expert: Optional[str] = None
    red_blue_review: Optional[RedBlueReview] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "mode": self.mode,
            "states": [state.to_dict() for state in self.states],
            "steps": [step.to_dict() for step in self.steps],
            "converged": self.converged,
            "settledness_score": self.settledness_score,
            "locked_logic": self.locked_logic.to_dict() if self.locked_logic else None,
            "locked_expert": self.locked_expert,
            "red_blue_review": self.red_blue_review.to_dict() if self.red_blue_review else None,
        }


@dataclass
class MythosReasoningResult:
    """Final public result from Mythos reasoning."""

    decision: str
    conclusion: str
    confidence: float
    explanation: str
    reasoning_chain: List[Dict[str, Any]]
    trace: ReasoningTrace
    logic_kernel_result: LogicKernelResult
    action: Optional[str] = None
    analysis_only: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "decision": self.decision,
            "action": self.action,
            "conclusion": self.conclusion,
            "confidence": self.confidence,
            "explanation": self.explanation,
            "reasoning_chain": self.reasoning_chain,
            "trace": self.trace.to_dict(),
            "logic_kernel_result": self.logic_kernel_result.to_dict(),
            "analysis_only": self.analysis_only,
        }


class ChainOfThoughtReasoner:
    """Mythos recurrent reasoner with VLK verification and safety-biased output."""

    def __init__(self, config: Optional[ChainOfThoughtReasonerConfig] = None, **kwargs: Any):
        self.config = config or ChainOfThoughtReasonerConfig()
        self.kwargs = kwargs
        self._initialized = False
        self._history: List[MythosReasoningResult] = []
        self._logic_lock: Optional[LogicKernelResult] = None
        self._expert_lock: Optional[str] = None
        self._expert_lock_streak = 0
        self._verifier = LogicalVerifier({"storage_path": kwargs.get("logic_storage_path", "logical_verifier_data")}) if LogicalVerifier else None
        logger.debug("ChainOfThoughtReasoner initialized")

    async def initialize(self):
        """Initialize the component."""
        self._initialized = True
        return self

    def process(
        self,
        problem: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        mode: ReasoningMode | str = ReasoningMode.ANALYSIS,
        analysis_only: bool = False,
    ) -> MythosReasoningResult:
        """Run recurrent latent reasoning and verify the final conclusion."""
        context = context or {}
        mode = self._coerce_mode(mode)
        problem = problem or self._default_problem(mode, context)

        if not self.config.enabled:
            logic = self._fallback_logic([], "Reasoning disabled", verified=False)
            trace = ReasoningTrace(mode.value, [], [], False, 0.0, logic)
            return MythosReasoningResult("HOLD", "Reasoning disabled", 0.0, "Reasoner disabled.", [], trace, logic, "HOLD", analysis_only)

        latent = self._encode_problem(problem, context)
        states: List[LatentThoughtState] = []
        steps: List[ReasoningStep] = []
        previous_vectors: List[List[float]] = []
        locked_logic: Optional[LogicKernelResult] = None
        conclusion = "Insufficient evidence"
        confidence = 0.0

        for iteration in range(self.config.max_reasoning_loops):
            expert_scores = self._score_experts(problem, context, latent, mode)
            locked_expert = self._update_expert_lock(expert_scores, mode)
            expert_scores = self._apply_expert_lock(expert_scores, locked_expert)
            target = self._expert_target_vector(expert_scores, len(latent))
            next_latent = self._refine_latent(latent, target, iteration)
            delta = self._distance(latent, next_latent)
            energy = self._energy(next_latent, target)
            oscillating = self._is_oscillating(next_latent, previous_vectors)
            settledness = self._settledness(delta, energy, context, oscillating)
            dead_end = iteration >= 2 and settledness < 0.20 and delta < self.config.oscillation_threshold

            conclusion, confidence = self._derive_conclusion(problem, context, expert_scores, settledness, mode)
            premises = self._build_premises(problem, context, expert_scores, conclusion, mode)
            logic_result = self.verify_conclusion(premises, conclusion)

            if logic_result.verified and logic_result.validity_score >= self.config.logic_validity_threshold:
                locked_logic = logic_result
                self._logic_lock = logic_result
            elif locked_logic and self._contradicts_locked_logic(conclusion, locked_logic):
                confidence *= 0.35
                conclusion = locked_logic.conclusion
                logic_result = locked_logic

            state = LatentThoughtState(
                iteration=iteration,
                vector=[round(v, 6) for v in next_latent],
                energy=round(energy, 6),
                delta=round(delta, 6),
                settledness=round(settledness, 6),
                dead_end=dead_end,
                oscillating=oscillating,
                note="settled" if delta < self.config.convergence_threshold else "refining",
            )
            step = ReasoningStep(
                iteration=iteration,
                mode=mode.value,
                expert_scores=expert_scores,
                conclusion=conclusion,
                confidence=round(confidence, 6),
                premises=premises,
                settledness=round(settledness, 6),
                logic_locked=logic_result.verified,
            )
            states.append(state)
            steps.append(step)
            previous_vectors.append(latent)
            latent = next_latent

            if delta < self.config.convergence_threshold or dead_end:
                break

        final_logic = locked_logic or self.verify_conclusion(steps[-1].premises if steps else [], conclusion)
        red_blue_review = self._run_red_blue_review(problem, context, steps, final_logic, mode)
        if red_blue_review and red_blue_review.verdict == "risk_confirmed":
            conclusion = red_blue_review.exploit_path
            final_logic = red_blue_review.exploit_verification
            confidence = max(confidence, red_blue_review.risk_score)
        settledness_score = states[-1].settledness if states else 0.0
        decision, action, confidence = self._finalize_decision(conclusion, confidence, final_logic, mode, analysis_only, settledness_score)
        trace = ReasoningTrace(
            mode=mode.value,
            states=states,
            steps=steps,
            converged=bool(states and states[-1].delta < self.config.convergence_threshold),
            settledness_score=settledness_score,
            locked_logic=final_logic,
            locked_expert=self._expert_lock,
            red_blue_review=red_blue_review,
        )
        result = MythosReasoningResult(
            decision=decision,
            action=action,
            conclusion=conclusion,
            confidence=round(max(0.0, min(1.0, confidence)), 6),
            explanation=self._explain(decision, conclusion, final_logic, settledness_score),
            reasoning_chain=[step.to_dict() for step in steps],
            trace=trace,
            logic_kernel_result=final_logic,
            analysis_only=analysis_only,
        )
        self._history.append(result)
        return result

    def reason_about_trade(self, market_state: Dict[str, Any]) -> Dict[str, Any]:
        """Backward-compatible trading reasoner API."""
        result = self.process(
            "Should Mythos allow a trade for the current market state?",
            market_state,
            ReasoningMode.TRADE,
        )
        return {
            "decision": result.decision,
            "confidence": result.confidence,
            "reasoning_chain": result.reasoning_chain,
            "explanation": result.explanation,
            "logic_kernel_result": result.logic_kernel_result.to_dict(),
            "trace": result.trace.to_dict(),
        }

    def verify_conclusion(self, premises: Sequence[str], conclusion: str) -> LogicKernelResult:
        """Synchronously verify a conclusion with the existing LogicalVerifier."""
        premises = [str(p) for p in premises if str(p).strip()]
        conclusion = str(conclusion or "").strip()
        if not premises or not conclusion:
            return self._fallback_logic(premises, conclusion, verified=False, status="incomplete")
        if not self._verifier or not ArgumentForm:
            return self._heuristic_verify(premises, conclusion)

        async def _verify() -> LogicKernelResult:
            structure = await self._verifier.analyze_argument(
                premises,
                conclusion,
                argument_form=ArgumentForm.MODUS_PONENS,
            )
            verification = await self._verifier.verify_logic(structure)
            return LogicKernelResult(
                premises=premises,
                conclusion=conclusion,
                status=verification.status.value,
                validity_score=float(verification.validity_score),
                soundness_score=float(verification.soundness_score),
                fallacies=[
                    {**fallacy, "type": getattr(fallacy.get("type"), "value", fallacy.get("type"))}
                    for fallacy in verification.fallacies
                ],
                consistency_issues=list(verification.consistency_issues),
                recommendations=list(verification.recommendations),
                verified=verification.status == VerificationStatus.VALID,
            )

        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(_verify())

        holder: Dict[str, Any] = {}

        def _worker() -> None:
            try:
                holder["result"] = asyncio.run(_verify())
            except Exception as exc:  # pragma: no cover - defensive thread fallback.
                holder["error"] = exc

        thread = threading.Thread(target=_worker, daemon=True)
        thread.start()
        thread.join()
        if "result" in holder:
            return holder["result"]
        logger.warning("VLK thread fallback failed: %s", holder.get("error"))
        return self._heuristic_verify(premises, conclusion)

    def reset(self) -> Dict[str, Any]:
        """Clear recurrent history and locked logic."""
        cleared = len(self._history)
        self._history.clear()
        self._logic_lock = None
        self._expert_lock = None
        self._expert_lock_streak = 0
        return {"reset": True, "cleared_history": cleared}

    def get_status(self) -> Dict[str, Any]:
        """Get component status."""
        return {
            "name": "ChainOfThoughtReasoner",
            "initialized": self._initialized,
            "enabled": self.config.enabled,
            "max_reasoning_loops": self.config.max_reasoning_loops,
            "history_size": len(self._history),
            "logic_kernel_available": self._verifier is not None,
            "logic_locked": self._logic_lock is not None,
            "locked_expert": self._expert_lock,
            "red_blue_enabled": self.config.red_blue_enabled,
        }

    async def shutdown(self):
        """Shutdown hook for lifecycle-managed callers."""
        self.reset()
        self._initialized = False
        return {"shutdown": True}

    def _coerce_mode(self, mode: ReasoningMode | str) -> ReasoningMode:
        if isinstance(mode, ReasoningMode):
            return mode
        try:
            return ReasoningMode(str(mode).lower())
        except ValueError:
            return ReasoningMode.ANALYSIS

    def _default_problem(self, mode: ReasoningMode, context: Dict[str, Any]) -> str:
        if mode == ReasoningMode.TRADE:
            return "Should Mythos allow a trade?"
        if mode == ReasoningMode.PROOF:
            return "Verify the proposed conclusion."
        if mode == ReasoningMode.VULNERABILITY:
            return "Assess whether the code or system claim indicates a vulnerability."
        return str(context.get("question", "Analyze the provided context."))

    def _encode_problem(self, problem: str, context: Dict[str, Any]) -> List[float]:
        payload = f"{problem}|{sorted(context.items(), key=lambda item: str(item[0]))}"
        digest = hashlib.sha256(payload.encode("utf-8", errors="ignore")).digest()
        vector = []
        for i in range(self.config.latent_dim):
            raw = digest[i % len(digest)] / 255.0
            vector.append((raw * 2.0) - 1.0)
        numeric = [float(v) for v in context.values() if isinstance(v, (int, float))]
        if numeric:
            scale = max(1.0, max(abs(v) for v in numeric))
            for i, value in enumerate(numeric[: len(vector)]):
                vector[i] = 0.7 * vector[i] + 0.3 * max(-1.0, min(1.0, value / scale))
        return vector

    def _score_experts(
        self,
        problem: str,
        context: Dict[str, Any],
        latent: Sequence[float],
        mode: ReasoningMode,
    ) -> Dict[str, float]:
        text = f"{problem} {context}".lower()
        volatility = float(context.get("volatility", 1.0))
        adx = float(context.get("adx", context.get("trend_strength", 0.0)))
        rsi = float(context.get("rsi", 50.0))
        macd = float(context.get("macd", 0.0))
        sma_20 = float(context.get("sma_20", context.get("price", 0.0)))
        sma_50 = float(context.get("sma_50", context.get("price", 0.0)))
        drawdown = abs(float(context.get("drawdown", 0.0)))
        correlation = abs(float(context.get("correlation", 0.0)))

        technical = self._clip01(
            0.25 * (1.0 if rsi < 35 else 0.0)
            + 0.25 * (1.0 if macd > 0 else 0.0)
            + 0.25 * (1.0 if sma_20 >= sma_50 else 0.0)
            + 0.25 * (1.0 if float(context.get("trend", adx)) > 0 else 0.0)
        )
        risk_pressure = self._clip01(0.45 * min(volatility / 3.0, 1.0) + 0.35 * min(drawdown / 0.1, 1.0) + 0.20 * correlation)
        regime = self._clip01(0.5 + 0.2 * (adx > 25) - 0.2 * (volatility > 2.5))
        evidence = self._clip01(0.4 + 0.2 * bool(context.get("source")) + 0.2 * bool(context.get("citations")) + 0.2 * ("because" in text or "evidence" in text))
        math_logic = self._clip01(
            0.3
            + (0.2 if mode == ReasoningMode.PROOF else 0.0)
            + (0.2 if any(token in text for token in ("if", "then", "therefore", "prove", "logic", "math")) else 0.0)
        )
        vulnerability = self._clip01(
            0.2
            + (0.4 if mode == ReasoningMode.VULNERABILITY else 0.0)
            + (0.2 if any(token in text for token in ("vulnerability", "exploit", "injection", "overflow", "secret", "auth")) else 0.0)
        )
        latent_balance = self._clip01(0.5 + sum(latent[:4]) / max(8.0, len(latent) * 2.0))

        scores = {
            "market_regime": self._clip01((regime + latent_balance) / 2.0),
            "technicals": technical,
            "risk": self._clip01(1.0 - risk_pressure),
            "evidence": evidence,
            "math_logic": math_logic,
            "software_vulnerability": vulnerability,
        }
        return {key: round(float(value), 6) for key, value in scores.items()}

    def _update_expert_lock(self, scores: Dict[str, float], mode: ReasoningMode) -> Optional[str]:
        """Keep recurrent refinement focused on the expert most relevant to the task."""
        if not self.config.expert_locking_enabled or not scores:
            return None

        dominant = max(scores, key=scores.get)
        top_score = scores[dominant]
        target = dominant
        if mode == ReasoningMode.VULNERABILITY:
            vuln_score = scores.get("software_vulnerability", 0.0)
            if vuln_score >= 0.45:
                target = "software_vulnerability"
        elif mode == ReasoningMode.PROOF:
            logic_score = scores.get("math_logic", 0.0)
            if logic_score + self.config.expert_lock_margin >= top_score:
                target = "math_logic"
        elif mode == ReasoningMode.TRADE and scores.get("risk", 1.0) < 0.45:
            target = "risk"

        if target == self._expert_lock:
            self._expert_lock_streak += 1
        else:
            self._expert_lock = target if scores[target] >= 0.45 else None
            self._expert_lock_streak = 1 if self._expert_lock else 0
        return self._expert_lock

    def _apply_expert_lock(self, scores: Dict[str, float], locked_expert: Optional[str]) -> Dict[str, float]:
        if not locked_expert or locked_expert not in scores:
            return scores
        focused = {}
        for expert, score in scores.items():
            if expert == locked_expert:
                focused[expert] = self._clip01(score + 0.12 + min(self._expert_lock_streak, 3) * 0.03)
            else:
                focused[expert] = self._clip01(score * 0.97)
        return {key: round(value, 6) for key, value in focused.items()}

    def _expert_target_vector(self, scores: Dict[str, float], dim: int) -> List[float]:
        values = list(scores.values())
        target = []
        for i in range(dim):
            value = values[i % len(values)]
            target.append((value * 2.0) - 1.0)
        return target

    def _refine_latent(self, latent: Sequence[float], target: Sequence[float], iteration: int) -> List[float]:
        step = 0.42 / (1.0 + 0.15 * iteration)
        refined = []
        for current, goal in zip(latent, target):
            refined.append(math.tanh((1.0 - step) * current + step * goal))
        return refined

    def _derive_conclusion(
        self,
        problem: str,
        context: Dict[str, Any],
        scores: Dict[str, float],
        settledness: float,
        mode: ReasoningMode,
    ) -> tuple[str, float]:
        if mode == ReasoningMode.TRADE:
            risk_safe = scores["risk"]
            technicals = scores["technicals"]
            if risk_safe < 0.35:
                action = "HOLD"
                reason = "risk pressure is too high"
            elif technicals >= 0.70 and settledness >= self.config.min_settledness:
                action = "BUY"
                reason = "technical evidence is bullish and settled"
            elif technicals <= 0.25 and settledness >= self.config.min_settledness:
                action = "SELL"
                reason = "technical evidence is bearish and settled"
            else:
                action = "HOLD"
                reason = "evidence is mixed or unsettled"
            confidence = 0.35 + 0.35 * abs(technicals - 0.5) * 2.0 + 0.30 * min(risk_safe, settledness)
            return f"action is {action} because {reason}", self._clip01(confidence)

        if mode == ReasoningMode.VULNERABILITY:
            vulnerable = scores["software_vulnerability"] >= 0.55 and scores["evidence"] >= 0.45
            conclusion = "vulnerability risk is present" if vulnerable else "vulnerability risk is not established"
            return conclusion, self._clip01(0.45 + 0.35 * scores["software_vulnerability"] + 0.20 * scores["evidence"])

        if mode == ReasoningMode.PROOF:
            conclusion = str(context.get("conclusion") or problem)
            return conclusion, self._clip01(0.35 + 0.40 * scores["math_logic"] + 0.25 * scores["evidence"])

        dominant = max(scores, key=scores.get)
        conclusion = f"{dominant} evidence is the dominant reasoning signal"
        return conclusion, self._clip01(0.40 + 0.40 * scores[dominant] + 0.20 * settledness)

    def _build_premises(
        self,
        problem: str,
        context: Dict[str, Any],
        scores: Dict[str, float],
        conclusion: str,
        mode: ReasoningMode,
    ) -> List[str]:
        explicit = context.get("premises")
        if isinstance(explicit, Iterable) and not isinstance(explicit, (str, bytes, dict)):
            premises = [str(item) for item in explicit if str(item).strip()]
            if premises:
                return premises

        if mode == ReasoningMode.TRADE:
            action = self._extract_action(conclusion)
            if action == "HOLD":
                return ["If risk is high or evidence is unsettled then action is HOLD", "risk is high or evidence is unsettled"]
            if action == "BUY":
                return ["If bullish evidence and low risk then action is BUY", "bullish evidence and low risk"]
            return ["If bearish evidence and low risk then action is SELL", "bearish evidence and low risk"]

        if mode == ReasoningMode.VULNERABILITY:
            return [
                "If exploit indicators and evidence are present then vulnerability risk is present",
                "exploit indicators and evidence are present" if scores["software_vulnerability"] >= 0.55 else "exploit indicators are incomplete",
            ]

        if mode == ReasoningMode.PROOF:
            return [str(problem), f"If the premises support the claim then {conclusion}"]

        return [f"If {max(scores, key=scores.get)} evidence dominates then {conclusion}", f"{max(scores, key=scores.get)} evidence dominates"]

    def _run_red_blue_review(
        self,
        problem: str,
        context: Dict[str, Any],
        steps: Sequence[ReasoningStep],
        final_logic: LogicKernelResult,
        mode: ReasoningMode,
    ) -> Optional[RedBlueReview]:
        if not self.config.red_blue_enabled or mode != ReasoningMode.VULNERABILITY:
            return None

        last_step = steps[-1] if steps else None
        evidence_score = (last_step.expert_scores.get("evidence", 0.0) if last_step else 0.0)
        vuln_score = (last_step.expert_scores.get("software_vulnerability", 0.0) if last_step else 0.0)
        attacker_hypothesis = "attacker can reach a vulnerable condition from the supplied indicators"
        defender_response = "defender requires input validation, authorization, isolation, and audit evidence before accepting the path"

        attack_premises = [
            "If exploit indicators and supporting evidence are present then vulnerability risk is present",
            "exploit indicators and supporting evidence are present"
            if vuln_score >= 0.55 and evidence_score >= 0.40
            else "exploit indicators or supporting evidence are incomplete",
        ]
        explicit_attack = context.get("attack_premises")
        if isinstance(explicit_attack, Iterable) and not isinstance(explicit_attack, (str, bytes, dict)):
            attack_premises = [str(item) for item in explicit_attack if str(item).strip()] or attack_premises

        mitigations = context.get("mitigations") or context.get("defenses") or []
        if isinstance(mitigations, str):
            mitigations = [mitigations]
        has_mitigations = bool(mitigations)
        defense_premises = [
            "If effective mitigations cover the attack surface then vulnerability risk is mitigated",
            "effective mitigations cover the attack surface" if has_mitigations else "mitigations are not established",
        ]

        exploit_path = "vulnerability risk is present"
        exploit_verification = self.verify_conclusion(attack_premises, exploit_path)
        defense_verification = (
            self.verify_conclusion(defense_premises, "vulnerability risk is mitigated")
            if has_mitigations
            else self._fallback_logic(defense_premises, "vulnerability risk is mitigated", verified=False, status="incomplete")
        )

        risk_score = self._clip01(0.25 + 0.40 * vuln_score + 0.25 * evidence_score + 0.10 * final_logic.validity_score)
        if defense_verification.verified:
            risk_score *= 0.55
        if exploit_verification.verified and not defense_verification.verified and risk_score >= 0.55:
            verdict = "risk_confirmed"
        elif defense_verification.verified:
            verdict = "risk_mitigated"
        else:
            verdict = "needs_more_evidence"

        return RedBlueReview(
            attacker_hypothesis=attacker_hypothesis,
            defender_response=defender_response,
            attack_premises=attack_premises,
            defense_premises=defense_premises,
            exploit_path=exploit_path,
            exploit_verification=exploit_verification,
            defense_verification=defense_verification,
            risk_score=round(risk_score, 6),
            verdict=verdict,
        )

    def _finalize_decision(
        self,
        conclusion: str,
        confidence: float,
        logic: LogicKernelResult,
        mode: ReasoningMode,
        analysis_only: bool,
        settledness: float,
    ) -> tuple[str, Optional[str], float]:
        verified = logic.verified and logic.validity_score >= self.config.logic_validity_threshold
        stable = settledness >= self.config.min_settledness
        confidence *= 0.65 + 0.35 * logic.validity_score
        if not stable:
            confidence *= 0.75

        if mode == ReasoningMode.TRADE:
            action = self._extract_action(conclusion)
            if analysis_only:
                return action, action, confidence
            if not verified or not stable:
                return "HOLD", "HOLD", min(confidence, 0.49)
            return action, action, confidence

        decision = "VERIFIED" if verified else "UNCERTAIN"
        if mode == ReasoningMode.VULNERABILITY and "present" in conclusion and verified:
            decision = "VULNERABILITY_RISK_PRESENT"
        return decision, None, confidence

    def _heuristic_verify(self, premises: Sequence[str], conclusion: str) -> LogicKernelResult:
        premise_terms = set(" ".join(premises).lower().replace(",", " ").split())
        conclusion_terms = set(conclusion.lower().replace(",", " ").split())
        overlap = len(premise_terms & conclusion_terms) / max(1, len(conclusion_terms))
        circular = any(p.strip().lower() == conclusion.strip().lower() for p in premises)
        status = "fallacious" if circular else ("valid" if overlap >= 0.45 else "uncertain")
        return LogicKernelResult(
            premises=list(premises),
            conclusion=conclusion,
            status=status,
            validity_score=0.35 + 0.60 * overlap,
            soundness_score=0.30 + 0.50 * overlap,
            fallacies=[{"type": "circular_reasoning", "severity": "high"}] if circular else [],
            recommendations=[] if overlap >= 0.45 and not circular else ["Add premises that directly support the conclusion"],
            verified=status == "valid",
        )

    def _fallback_logic(
        self,
        premises: Sequence[str],
        conclusion: str,
        *,
        verified: bool,
        status: str = "uncertain",
    ) -> LogicKernelResult:
        return LogicKernelResult(
            premises=list(premises),
            conclusion=conclusion,
            status=status,
            validity_score=1.0 if verified else 0.0,
            soundness_score=1.0 if verified else 0.0,
            recommendations=[] if verified else ["Provide premises and conclusion before verification"],
            verified=verified,
        )

    def _contradicts_locked_logic(self, conclusion: str, locked_logic: LogicKernelResult) -> bool:
        return self._extract_action(conclusion) != self._extract_action(locked_logic.conclusion)

    def _extract_action(self, conclusion: str) -> str:
        text = conclusion.upper()
        if "BUY" in text:
            return "BUY"
        if "SELL" in text:
            return "SELL"
        return "HOLD"

    def _settledness(self, delta: float, energy: float, context: Dict[str, Any], oscillating: bool) -> float:
        internal = self._clip01(1.0 - (delta * 8.0) - (energy * 0.5) - (0.25 if oscillating else 0.0))
        calm_signal = context.get("operator_calm", context.get("psychological_settledness", 1.0))
        if isinstance(calm_signal, str):
            calm_signal = {"calm": 1.0, "mild": 0.8, "moderate": 0.55, "high": 0.30, "critical": 0.0}.get(calm_signal.lower(), 0.7)
        return self._clip01(0.75 * internal + 0.25 * float(calm_signal))

    def _is_oscillating(self, vector: Sequence[float], previous_vectors: Sequence[Sequence[float]]) -> bool:
        if len(previous_vectors) < 2:
            return False
        return self._distance(vector, previous_vectors[-2]) < self.config.oscillation_threshold

    def _energy(self, vector: Sequence[float], target: Sequence[float]) -> float:
        return self._distance(vector, target)

    def _distance(self, left: Sequence[float], right: Sequence[float]) -> float:
        return math.sqrt(sum((a - b) ** 2 for a, b in zip(left, right)) / max(1, len(left)))

    def _clip01(self, value: Any) -> float:
        return max(0.0, min(1.0, float(value)))

    def _explain(self, decision: str, conclusion: str, logic: LogicKernelResult, settledness: float) -> str:
        return (
            f"Mythos settled on '{decision}' from conclusion '{conclusion}'. "
            f"VLK status={logic.status}, validity={logic.validity_score:.2f}, "
            f"soundness={logic.soundness_score:.2f}, settledness={settledness:.2f}."
        )


def create_chainofthoughtreasoner(
    config: Optional[ChainOfThoughtReasonerConfig] = None,
    **kwargs: Any,
) -> ChainOfThoughtReasoner:
    """Create a ChainOfThoughtReasoner instance."""
    return ChainOfThoughtReasoner(config=config, **kwargs)


_DEFAULT_REASONER = ChainOfThoughtReasoner()


async def initialize():
    return await _DEFAULT_REASONER.initialize()


def process(*args: Any, **kwargs: Any) -> MythosReasoningResult:
    return _DEFAULT_REASONER.process(*args, **kwargs)


def get_status() -> Dict[str, Any]:
    return _DEFAULT_REASONER.get_status()


def reset() -> Dict[str, Any]:
    return _DEFAULT_REASONER.reset()


async def shutdown():
    return await _DEFAULT_REASONER.shutdown()


__all__ = [
    "ChainOfThoughtReasonerConfig",
    "LatentThoughtState",
    "ReasoningStep",
    "ReasoningTrace",
    "LogicKernelResult",
    "RedBlueReview",
    "MythosReasoningResult",
    "ReasoningMode",
    "ChainOfThoughtReasoner",
    "create_chainofthoughtreasoner",
    "initialize",
    "process",
    "get_status",
    "reset",
    "shutdown",
]
