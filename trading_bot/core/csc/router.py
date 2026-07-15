"""
SkillRouter & HASP - UCA V5 Skill Management (July 2026)

Orchestrates the selection and execution of Skill Programs (HASP)
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
                return skill.executable(context)

        # 2. Check for S2L adapters
        if "hedge" in task.lower():
            skill = self._registry.get("hedging_behavior")
            if skill:
                return {"status": "s2l_routed", "adapter_id": skill.adapter_id}

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

        try:
            return skill.executable(state)
        except Exception as e:
            logger.error(f"HASP Execution Failure: {e}")
            return {"status": "failure", "error": str(e)}
