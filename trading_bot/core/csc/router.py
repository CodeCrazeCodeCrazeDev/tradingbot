"""
SkillRouter & HASP - UCA V5 Skill Management (July 2026)

Orchestrates the selection and execution of Skill Programs (HASP)
and behavioral adapters (Skill-to-LoRA).
Implements 'HASP' (arXiv:2605.17734) and 'S2L' (arXiv:2606.16769).

Authoritative router for mapping strategic tasks to specialized skills and agents.
Replaces hardcoded logic in the CSC with dynamic, capability-based routing.
"""

import logging
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Callable
from dataclasses import dataclass, field
from datetime import datetime

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
        self._metrics: Dict[str, Dict[str, Any]] = {}

    def register_specialist(self, agent_id: str, domains: List[SkillDomain]):
        self._specialists[agent_id] = SpecialistCandidate(
            agent_id=agent_id,
            capabilities=set(domains)
        )
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
            "latency": 50.0,
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
        candidates = []
        for agent_id, specialist in self._specialists.items():
            if any(domain in specialist.capabilities for domain in required_domains):
                utility = self._calculate_utility(agent_id)
                candidates.append((agent_id, utility))

        candidates.sort(key=lambda x: x[1], reverse=True)
        selected = [c[0] for c in candidates[:3]]
        logger.info(f"Router: Selected specialists for {required_domains}: {selected}")
        return selected

    def _calculate_utility(self, agent_id: str) -> float:
        m = self._metrics.get(agent_id, self._get_default_metrics())
        w_performance = 0.4
        w_reliability = 0.3
        w_efficiency = 0.2
        w_quality = 0.1

        performance = (m["precision"] * 0.4 + m["recall"] * 0.4 + m["success_rate"] * 0.2)
        reliability = (1.0 - m["calibration_error"]) * 0.5 + (1.0 - m["timeout_rate"]) * 0.3 + m["recovery_rate"] * 0.2
        efficiency = 1.0 / (1.0 + m["latency"] / 100.0)
        quality = m["evidence_quality"] * 0.7 + m["historical_contribution"] * 0.3

        utility = (performance * w_performance +
                   reliability * w_reliability +
                   efficiency * w_efficiency +
                   quality * w_quality)
        return utility

    def update_metrics(self, agent_id: str, updates: Dict[str, Any]):
        if agent_id not in self._metrics:
            self._metrics[agent_id] = self._get_default_metrics()

        m = self._metrics[agent_id]
        alpha = 0.1

        for key, value in updates.items():
            if key in m:
                if isinstance(value, (int, float)):
                    m[key] = (1 - alpha) * m[key] + alpha * value
                else:
                    m[key] = value

        m["count"] += 1

    def get_agent_metrics(self, agent_id: str) -> Optional[Dict[str, Any]]:
        return self._metrics.get(agent_id)


# Primary routing mechanisms (HASP / S2L)
router = CapabilityRouter()

class SkillType(Enum):
    HASP_PROGRAM = "hasp_program"
    S2L_ADAPTER = "s2l_adapter"
    LEGACY_PROMPT = "legacy_prompt"

@dataclass
class SkillArtifact:
    skill_id: str
    skill_type: SkillType
    executable: Optional[Callable[[Dict[str, Any]], Dict[str, Any]]] = None
    adapter_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    performance_history: List[Any] = field(default_factory=list)

@dataclass
class RoutingResult:
    route: str
    status: str
    adapter: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0
    latency_ms: float = 0.0

    def __getitem__(self, item):
        if item == "route": return self.route
        elif item == "status": return self.status
        elif item == "adapter": return self.adapter
        elif item == "result": return self.result
        elif item == "metadata": return self.metadata
        elif item == "confidence": return self.confidence
        elif item == "latency_ms": return self.latency_ms
        raise KeyError(item)

    def get(self, item, default=None):
        try:
            return self[item]
        except KeyError:
            return default

class DualAwaitingResult:
    def __init__(self, value):
        self._value = value

    def __await__(self):
        async def _async_val():
            return self._value
        return _async_val().__await__()

    def __getattr__(self, name):
        return getattr(self._value, name)

    def __getitem__(self, item):
        return self._value[item]

    def get(self, item, default=None):
        return self._value.get(item, default)

class SkillRouter:
    """
    Authoritative router for mapping strategic tasks to specialized skills.
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
        self._mappings: Dict[str, str] = {}
        self._initialize_default_skills()
        self._initialized = True
        logger.info("SkillRouter V5: Initialized")

    def _initialize_default_skills(self):
        # Register standard HASP programs
        self.register_skill(SkillArtifact(
            skill_id="volatility_guardrail",
            skill_type=SkillType.HASP_PROGRAM,
            executable=self._pf_volatility_guardrail,
            metadata={"description": "Hard guardrail for high volatility"}
        ))

        # Register standard S2L adapters
        self.register_skill(SkillArtifact(
            skill_id="hedging_behavior",
            skill_type=SkillType.S2L_ADAPTER,
            adapter_id="lora_hedging_archetype",
            metadata={"archetype": "risk_averse"}
        ))

    def register_skill(self, artifact: SkillArtifact):
        self._registry[artifact.skill_id] = artifact
        logger.debug(f"Registered skill: {artifact.skill_id} ({artifact.skill_type.value})")

    def update_mapping(self, task: str, skill_id: str):
        self._mappings[task] = skill_id

    def route_task(self, task: str, context: Dict[str, Any]) -> DualAwaitingResult:
        """Routes a task to the appropriate skill or adapter."""
        # 1. Check direct task registry or mapping first
        target_id = self._mappings.get(task, task)
        if target_id in self._registry:
            return DualAwaitingResult(self._registry[target_id])

        # Fallback for compliance check if compliance_gate_hasp is registered
        if task == "risk_check" and "compliance_gate_hasp" in self._registry:
            return DualAwaitingResult(self._registry["compliance_gate_hasp"])

        market_state = context.get("market", {})
        volatility = context.get("market_volatility", market_state.get("volatility", 0))

        # 2. High/Low volatility execution task routing rules
        if task == "execution" and "market_volatility" in context:
            if volatility > 0.3:
                target = "risk_averse_hasp"
                if target in self._registry:
                    return DualAwaitingResult(self._registry[target])
                return DualAwaitingResult(None)
            else:
                target = "vwap_hasp_v1"
                if target in self._registry:
                    return DualAwaitingResult(self._registry[target])
                return DualAwaitingResult(None)

        # 3. Check for S2L adapters
        if "hedge" in task.lower() or context.get("needs_hedging"):
            skill = self._registry.get("hedging_behavior")
            if skill:
                return DualAwaitingResult(RoutingResult(
                    route="hedging_behavior",
                    status="dispatched_to_adapter",
                    adapter=skill.adapter_id,
                    metadata={"archetype": "risk_averse"},
                    confidence=0.9
                ))

        # 4. Default fallback volatility guardrail for csc process observation (where context contains market and vol)
        if volatility > 0.3 and "market" in context:
            skill = self._registry.get("volatility_guardrail")
            if skill and skill.executable:
                res_dict = skill.executable(context)
                return DualAwaitingResult(RoutingResult(
                    route="volatility_guardrail",
                    status="pf_intervention",
                    result=res_dict,
                    metadata={"description": "Volatility guardrail trigger"},
                    confidence=1.0
                ))

        # 5. Fallback standard reasoning
        return DualAwaitingResult(RoutingResult(
            route="standard",
            status="standard_reasoning",
            metadata={"description": "Standard inference pathway"},
            confidence=1.0
        ))

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

    def execute(self, skill_or_id: Any, state: Dict[str, Any]) -> Dict[str, Any]:
        if isinstance(skill_or_id, str):
            skill = self.router._registry.get(skill_or_id)
        else:
            skill = skill_or_id

        if not skill or not skill.executable:
            return {"status": "error", "message": f"Executable skill not found"}

        try:
            res = skill.executable(state)
            skill.performance_history.append({"timestamp": datetime.utcnow().isoformat(), "result": res})
            return {"status": "success", "result": res}
        except Exception as e:
            return {"status": "failure", "error": str(e)}
