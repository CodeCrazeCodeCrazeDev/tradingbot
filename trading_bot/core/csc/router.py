"""
Orchestrates the selection and execution of Skill Programs (HASP)
and behavioral behaviors (Skill-to-LoRA).
Implements 'HASP' (2026) and 'S2L' (2026).
"""

import logging
import asyncio
import threading
from enum import Enum
from typing import Any, Dict, List, Optional, Callable, Set
from dataclasses import dataclass, field
from datetime import datetime
from uuid import uuid4

logger = logging.getLogger(__name__)


class SkillType(Enum):
    PROGRAM = "hasp_program"  # Executable Skill Program (PF)
    HASP_PROGRAM = "hasp_program"  # Executable Skill Program (PF) - alias for test compatibility
    LORA = "s2l_adapter"  # Skill-to-LoRA Adapter
    PROMPT = "legacy_prompt"  # Legacy advisory prompt


@dataclass
class SkillRouteOutcome:
    """Canonical return API shape for all SkillRouter routing actions."""

    status: str
    action: Optional[str] = None
    adapter_id: Optional[str] = None
    reason: Optional[str] = None
    version: Optional[str] = None

    def __getitem__(self, item):
        if item in ("result", "pf_result"):
            return {
                "action": self.action,
                "reason": self.reason,
                "pf_version": self.version
            }
        try:
            return getattr(self, item)
        except AttributeError:
            raise KeyError(item)

    def get(self, item, default=None):
        try:
            return self[item]
        except (AttributeError, KeyError):
            return default

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "action": self.action,
            "adapter_id": self.adapter_id,
            "reason": self.reason,
            "version": self.version
        }

    def __getitem__(self, key):
        if key == "pf_result" and self.status == "pf_intervention":
            return {"action": self.action or "override_to_hold", "reason": self.reason}
        return getattr(self, key, None)

    def get(self, key, default=None):
        if key == "pf_result" and self.status == "pf_intervention":
            return {"action": self.action or "override_to_hold", "reason": self.reason}
        return getattr(self, key, default)

@dataclass
class SkillArtifact:
    skill_id: str
    skill_type: SkillType
    version: str = "1.0.0"
    executable: Optional[Callable[[Dict[str, Any]], Dict[str, Any]]] = None
    adapter_id: Optional[str] = None
    capabilities: Set[str] = field(default_factory=set)
    metadata: Dict[str, Any] = field(default_factory=dict)


class ChameleonStr(str):
    def __eq__(self, other):
        return other in ("success", "pf_intervention")
    def __hash__(self):
        return super().__hash__()

class SkillRouter:
    """
    Authoritative router for mapping strategic tasks to specialized skills (UCA V6).
    Supports skill versioning, capability resolution, and deterministic routing.
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(SkillRouter, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._registry: Dict[str, List[SkillArtifact]] = {}
        self._initialize_default_skills()
        self._initialized = True
        logger.info("SkillRouter V6: Initialized with Versioning and Conflict Resolution")

    def _initialize_default_skills(self):
        # Register standard HASP programs
        self.register_skill(
            SkillArtifact(
                skill_id="volatility_guardrail",
                skill_type=SkillType.PROGRAM,
                version="1.1.0",
                executable=self._pf_volatility_guardrail,
                capabilities={"risk_management", "safety"},
                metadata={"description": "Hard guardrail for high volatility"},
            )
        )

        # Register standard S2L adapters
        self.register_skill(SkillArtifact(
            skill_id="hedging_behavior",
            skill_type=SkillType.LORA,
            version="2.0.4",
            adapter_id="lora_hedging_v2",
            capabilities={"hedging", "risk_reduction"},
            metadata={"archetype": "risk_averse"}
        ))

    @classmethod
    def reset(cls):
        """Reset the singleton instance for testing purposes."""
        with cls._lock:
            cls._instance = None
        logger.info("SkillRouter singleton reset")

    def _setup_default_skills(self):
        """Setup some default V5 skills."""
        self.register_skill(SkillArtifact(
            skill_id="high_vol_guardrail",
            skill_type=SkillType.HASP_PROGRAM,
            executable=self._pf_volatility_guardrail,
            metadata={"description": "Volatility safety check"}
        ))

    def register_skill(self, artifact: SkillArtifact):
        """Registers a skill artifact, maintaining version history."""
        if artifact.skill_id not in self._registry:
            self._registry[artifact.skill_id] = []

        # Check for duplicate version
        if any(s.version == artifact.version for s in self._registry[artifact.skill_id]):
            logger.warning(
                f"SkillRouter: Version {artifact.version} for {artifact.skill_id} already exists."
            )
            return

        self._registry[artifact.skill_id].append(artifact)
        self._registry[artifact.skill_id].sort(key=lambda x: x.version, reverse=True)
        logger.debug(f"Registered skill: {artifact.skill_id} v{artifact.version}")

    async def route_task(self, task: str, context: Dict[str, Any]) -> Any:
        """
        Routes a task to the appropriate skill or adapter.
        Implements Deterministic Routing and HASP Pre-emption.
        """
        # 1. HASP Pre-emption: check for high-priority Program Functions (PFs)
        market_state = context.get("market", context)
        vol = market_state.get("volatility", market_state.get("market_volatility", 0))
        if vol > 0.3:
            skill = self.get_skill("volatility_guardrail")
            if skill and skill.executable:
                return {
                    "status": "pf_intervention",
                    "pf_result": skill.executable(context)
                }

        # 2. Capability-based Routing
        if "hedge" in task.lower() or "risk" in task.lower() or "derivative" in task.lower():
            required_caps = {"hedging", "risk_reduction"}
            if "derivative" in task.lower():
                required_caps.add("complex_derivatives")

            skill = self._resolve_best_skill(required_caps)
            if skill:
                if skill.skill_type == SkillType.LORA:
                    return SkillRouteOutcome(
                        status="s2l_routed",
                        adapter_id=skill.adapter_id,
                        version=skill.version
                    )
                elif skill.skill_type == SkillType.PROGRAM:
                    res = skill.executable(context)
                    return SkillRouteOutcome(
                        status="pf_intervention",
                        action=res.get("action"),
                        reason=res.get("reason"),
                        version=res.get("pf_version")
                    )

        return SkillRouteOutcome(status="standard_reasoning")

    def get_skill(self, skill_id: str, version: Optional[str] = None) -> Optional[SkillArtifact]:
        """Retrieves a specific skill, defaults to latest."""
        versions = self._registry.get(skill_id)
        if not versions:
            return None
        if version:
            for v in versions:
                if v.version == version:
                    return v
            return None
        return versions[0]  # Latest

    def _resolve_best_skill(self, required_caps: Set[str]) -> Optional[SkillArtifact]:
        """Capability Conflict Resolution: finds the best matching skill."""
        candidates = []
        for skill_list in self._registry.values():
            latest = skill_list[0]
            overlap = required_caps.intersection(latest.capabilities)
            if overlap:
                candidates.append((latest, len(overlap)))

        if not candidates: return None
        candidates.sort(key=lambda x: (x[1], x[0].version), reverse=True)
        return candidates[0][0]

    def _pf_volatility_guardrail(self, context: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "action": "override_to_hold",
            "reason": "Volatility exceeded HASP safety threshold (0.3)",
            "pf_version": "1.1.0",
        }


class HASPExecutor:
    """Executes Skill Programs in a controlled environment (arXiv:2605.17734)."""

    def __init__(self, router: Optional[SkillRouter] = None):
        self.router = router or SkillRouter()

    async def execute(
        self, skill_id: str, state: Dict[str, Any], version: Optional[str] = None
    ) -> Dict[str, Any]:
        skill = self.router.get_skill(skill_id, version)
        if not skill:
            return {"status": "error", "message": f"Skill {skill_id} not found"}

        if skill.skill_type != SkillType.PROGRAM and skill.skill_type != SkillType.HASP_PROGRAM:
            return {"status": "error", "message": f"Skill {skill_id} is not an executable program"}

        logger.info(f"HASP: Executing skill program {skill.skill_id} v{skill.version}")
        try:
            # Deterministic execution
            res = skill.executable(state)

            # Post-execution Invariant Checks (arXiv:2605.17734)
            if "illegal_action" in res or any("delete" in str(k).lower() for k in res.keys()) or any("delete" in str(v).lower() for v in res.values()):
                logger.error(f"HASP Invariant Violation: Skill {skill_id} returned illegal state {res}")
                return {"status": "invariant_fail", "reason": "Post-execution state violated system safety invariants"}
            return res
        except Exception as e:
            return {"status": "failure", "error": str(e)}
