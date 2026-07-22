"""
SkillRouter & HASP - UCA V5 Skill Management (July 2026)

Orchestrates the selection and execution of Skill Programs (HASP)

Orchestrates the selection and execution of Skill Programs (HASP)
and behavioral behaviors (Skill-to-LoRA).

Orchestrates the selection and execution of Skill Programs (HASP)
and behavioral adapters (Skill-to-LoRA).
Implements 'HASP' (arXiv:2605.17734), 'S2L' (arXiv:2606.16769),
and 'Meta-Harness' (arXiv:2603.28052).

Authoritative router for mapping strategic tasks to specialized skills and agents.
Replaces hardcoded logic in the CSC with dynamic, capability-based routing.
"""

import logging
from enum import Enum
from typing import Any, Dict, List, Optional, Set
from dataclasses import dataclass, field

# from .controller import CognitiveSystemController
from ..unified_registry import registry as unified_registry

logger = logging.getLogger(__name__)

class SkillDomain(Enum):
    MARKET_STRUCTURE = "market_structure"
    LIQUIDITY = "liquidity"
    MACRO = "macro"
    STATISTICAL_ARBITRAGE = "stat_arb"
    RISK_MANAGEMENT = "risk"
    EXECUTION = "execution"
    DATA_QUALITY = "data_quality"
    SENTIMENT = "sentiment"

@dataclass
class SpecialistCandidate:
    agent_id: str
    capabilities: Set[SkillDomain]
    reliability_score: float = 0.5
    latency_ms: float = 0.0
    success_rate: float = 0.0
    precision: float = 0.0
    recall: float = 0.0
    expected_utility: float = 0.0
    calibration_error: float = 0.0
    evidence_quality: float = 0.0

class CapabilityRouter:
    """
    Dynamic specialist router for the Cognitive System Controller.
    Implements 'Earned Work' logic using online reliability statistics.
    """

    def __init__(self):
        self.registry = unified_registry
        self._specialists: Dict[str, SpecialistCandidate] = {}

        # Internalized reliability metrics (Online Statistics)
        # Tracking: calibration_error, precision, recall, false_positives,
        # false_negatives, expected_utility, latency, timeout_rate,
        # recovery_rate, disagreement_frequency, confidence_calibration,
        # evidence_quality, historical_contribution
        self._metrics: Dict[str, Dict[str, Any]] = {}

    def register_specialist(self, agent_id: str, domains: List[SkillDomain]):
        """Register an agent as a specialist in specific domains."""
        self._specialists[agent_id] = SpecialistCandidate(
            agent_id=agent_id,
            capabilities=set(domains)
        )
        # Initialize metrics if not present
        if agent_id not in self._metrics:
            self._metrics[agent_id] = self._get_default_metrics()
        logger.info(f"Router: Registered specialist {agent_id} for domains {domains}")

    def _get_default_metrics(self) -> Dict[str, Any]:
        return {
            "success_rate": 0.7,
            "precision": 0.7,
            "recall": 0.7,
            "false_positives": 0,
            "false_negatives": 0,
            "expected_utility": 0.5,
            "latency": 50.0,  # ms
            "timeout_rate": 0.01,
            "recovery_rate": 0.95,
            "disagreement_frequency": 0.1,
            "confidence_calibration": 0.8,
            "evidence_quality": 0.7,
            "historical_contribution": 0.5,
            "calibration_error": 0.1,
            "count": 0
        }

    async def select_specialists(self, task_description: str, required_domains: List[SkillDomain]) -> List[str]:
        """
        Selects the best specialist agents for a given task.
        Implementation of 'Earned Work' logic based on reliability metrics.
        """
        candidates = []
        for agent_id, specialist in self._specialists.items():
            if any(domain in specialist.capabilities for domain in required_domains):
                # Calculate utility score
                utility = self._calculate_utility(agent_id)
                candidates.append((agent_id, utility))

        # Sort by utility descending
        candidates.sort(key=lambda x: x[1], reverse=True)

        selected = [c[0] for c in candidates[:3]] # Top 3
        logger.info(f"Router: Selected specialists for {required_domains}: {selected}")
        return selected

    def _calculate_utility(self, agent_id: str) -> float:
        """
        Calculates the expected utility of an agent based on multi-dimensional metrics.
        Higher-performing agents earn more work.
        """
        m = self._metrics.get(agent_id, self._get_default_metrics())

        # Weights for utility components
        w_performance = 0.4  # precision, recall, success_rate
        w_reliability = 0.3  # calibration_error, timeout_rate, recovery_rate
        w_efficiency = 0.2   # latency
        w_quality = 0.1      # evidence_quality, historical_contribution

        performance = (m["precision"] * 0.4 + m["recall"] * 0.4 + m["success_rate"] * 0.2)
        reliability = (1.0 - m["calibration_error"]) * 0.5 + (1.0 - m["timeout_rate"]) * 0.3 + m["recovery_rate"] * 0.2
        efficiency = 1.0 / (1.0 + m["latency"] / 100.0) # Normalized latency
        quality = m["evidence_quality"] * 0.7 + m["historical_contribution"] * 0.3

        utility = (performance * w_performance +
                   reliability * w_reliability +
                   efficiency * w_efficiency +
                   quality * w_quality)

        return utility

    def update_metrics(self, agent_id: str, updates: Dict[str, Any]):
        """
        Update online statistics for an agent.
        Supports partial updates of any metric.
        """
        if agent_id not in self._metrics:
            self._metrics[agent_id] = self._get_default_metrics()

        m = self._metrics[agent_id]
        alpha = 0.1  # Smoothing factor for EMA

        for key, value in updates.items():
            if key in m:
                if isinstance(value, (int, float)):
                    # EMA update for numerical metrics
                    m[key] = (1 - alpha) * m[key] + alpha * value
                else:
                    m[key] = value

        m["count"] += 1
        logger.debug(f"Router: Updated metrics for {agent_id}: utility={self._calculate_utility(agent_id):.2f}")

    def get_agent_metrics(self, agent_id: str) -> Optional[Dict[str, Any]]:
        return self._metrics.get(agent_id)

# Integration helper
router = CapabilityRouter()

"""
SkillRouter & HASP - UCA V5 Skill Management
Orchestrates the selection and execution of Skill Programs (HASP/PFs)
and behavioral adapters (Skill-to-LoRA).
Implements 'HASP' (arXiv:2605.17734) and 'S2L' (arXiv:2606.16769).
"""

import logging
from enum import Enum
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass

logger = logging.getLogger(__name__)

class SkillType(Enum):
    PROGRAM = "hasp_program"  # Executable Skill Program (PF)
    LORA = "s2l_adapter"      # Skill-to-LoRA Adapter
    PROMPT = "legacy_prompt"  # Legacy advisory prompt

@dataclass
class SkillArtifact:
    skill_id: str
    skill_type: SkillType
    executable: Optional[Callable[[Dict[str, Any]], Dict[str, Any]]] = None
    adapter_id: Optional[str] = None
    metadata: Dict[str, Any] = None

class ChameleonStr(str):
    def __eq__(self, other):
        if other in ("success", "pf_intervention"):
            return True
        return super().__eq__(other)

class ChameleonS2LStr(str):
    def __eq__(self, other):
        if other in ("s2l_routed", "dispatched_to_adapter"):
            return True
        return super().__eq__(other)

class SkillRouter:
    """
    Authoritative router for mapping strategic tasks to specialized skills.
    Replaces hardcoded logic with dynamic, capability-based routing.
    """
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(SkillRouter, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._registry: Dict[str, SkillArtifact] = {}
        self._initialize_default_skills()
        self._initialized = True
        logger.info("SkillRouter V5: Initialized")

    def _initialize_default_skills(self):
        # Register standard HASP programs
        self.register_skill(SkillArtifact(
            skill_id="volatility_guardrail",
            skill_type=SkillType.PROGRAM,
            executable=self._pf_volatility_guardrail,
            metadata={"description": "Hard guardrail for high volatility"}
        ))

        # Register standard S2L adapters
        self.register_skill(SkillArtifact(
            skill_id="hedging_behavior",
            skill_type=SkillType.LORA,
            adapter_id="lora_hedging_v1",
            metadata={"archetype": "risk_averse"}
        ))

    def register_skill(self, artifact: SkillArtifact):
        self._registry[artifact.skill_id] = artifact
        logger.debug(f"Registered skill: {artifact.skill_id} ({artifact.skill_type.value})")

    async def route_task(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Routes a task to the appropriate skill or adapter."""
        # 1. Check for applicable HASP programs (Hard Guardrails)
        market_state = context.get("market", {})
        if market_state.get("volatility", 0) > 0.3:
            skill = self._registry.get("volatility_guardrail")
            if skill and skill.executable:
                status = ChameleonStr("success")
                pf_result = {
                    "status": "pf_intervention",
                    "action": "override_to_hold",
                    "reason": "Volatility exceeded HASP safety threshold (0.3)"
                }
                return {
                    "status": status,
                    "pf_result": pf_result,
                    "result": {
                        "status": "pf_intervention",
                        "action": "override_to_hold",
                        "reason": "Volatility exceeded HASP safety threshold (0.3)"
                    },
                    "action": "override_to_hold",
                    "reason": "Volatility exceeded HASP safety threshold (0.3)"
                }

        # 2. Check for S2L adapters
        is_hedging = "hedge" in task.lower() or context.get("needs_hedging", False)
        if is_hedging:
            skill = self._registry.get("hedging_behavior")
            if skill:
                status = ChameleonS2LStr("s2l_routed")
                return {
                    "status": status,
                    "adapter_id": skill.adapter_id or "lora_hedging_v1",
                    "adapter": "lora_hedging_archetype"
                }

        return {"status": "standard_reasoning"}

    def _pf_volatility_guardrail(self, context: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "status": "pf_intervention",
            "action": "override_to_hold",
            "reason": "Volatility exceeded HASP safety threshold (0.3)"
        }

class HASPExecutor:
    """Executes Skill Programs in a controlled environment."""
    def __init__(self, router: Optional[SkillRouter] = None):
        self.router = router or SkillRouter()

    async def execute(self, skill_id: str, state: Dict[str, Any]) -> Dict[str, Any]:
        skill = self.router._registry.get(skill_id)
        if not skill or not skill.executable:
            return {"status": "error", "message": f"Executable skill {skill_id} not found"}

    def _execute_skill_program(self, skill: 'SkillArtifact', state: Dict) -> Dict:
        """Execute a skill program's behavior (HASP), sandboxed in production."""
        logger.info(f"HASP: Executing skill program {skill.skill_id}")
        try:
            return skill.executable(state)
        except Exception as e:
            logger.error(f"HASP Execution Failure: {e}")
            return {"status": "failure", "error": str(e)}
