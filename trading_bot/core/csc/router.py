"""
SkillRouter & HASP - UCA V5 Skill Management
Orchestrates the selection and execution of Skill Programs (HASP)
and behavioral behaviors (Skill-to-LoRA).
Implements 'HASP' (2026) and 'S2L' (2026).
"""

import logging
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class SkillType(Enum):
    HASP_PROGRAM = "hasp_program"
    S2L_ADAPTER = "s2l_adapter"
    REASONING_CHAIN = "reasoning_chain"

@dataclass
class SkillArtifact:
    skill_id: str
    skill_type: SkillType
    executable: Any
    metadata: Dict[str, Any]

class SkillRouter:
    """
    Routes agent tasks to either lightweight LoRA adapters (S2L)
    or executable Skill Programs (HASP/PFs).
    """

    def __init__(self):
        self._registry: Dict[str, SkillArtifact] = {}
        self._init_standard_skills()
        logger.info("SkillRouter initialized for UCA V5")

    def _init_standard_skills(self):
        # Register standard HASP programs
        self.register_skill(SkillArtifact(
            skill_id="high_vol_guardrail",
            skill_type=SkillType.HASP_PROGRAM,
            executable=self._pf_volatility_guardrail,
            metadata={"description": "Hard guardrail for high volatility"}
        ))

        self.register_skill(SkillArtifact(
            skill_id="compliance_checker",
            skill_type=SkillType.HASP_PROGRAM,
            executable=self._pf_compliance_checker,
            metadata={"description": "Institutional compliance gate"}
        ))

        # Register standard S2L adapters (behavioral archetypes)
        self.register_skill(SkillArtifact(
            skill_id="lora_hedging_archetype",
            skill_type=SkillType.S2L_ADAPTER,
            executable=None,
            metadata={"description": "Specialized hedging behavior"}
        ))

        self.register_skill(SkillArtifact(
            skill_id="lora_arbitrage_archetype",
            skill_type=SkillType.S2L_ADAPTER,
            executable=None,
            metadata={"description": "Specialized arbitrage behavior"}
        ))

    def register_skill(self, artifact: SkillArtifact):
        self._registry[artifact.skill_id] = artifact
        logger.debug(f"Registered skill: {artifact.skill_id} ({artifact.skill_type.value})")

    async def route_task(self, task_type: str, context: Dict[str, Any], reasoning_context: Optional[Dict] = None) -> Dict:
        """
        Functional routing logic for S2L and HASP.
        """
        # 1. Mandatory HASP Checks (Guardrails)
        if context.get('market', {}).get('volatility', 0) > 0.3:
            skill = self._registry.get("high_vol_guardrail")
            if skill: return await self.execute_hasp(skill, context)

        # 2. Compliance Check (HASP)
        if task_type == "trade_proposal":
            skill = self._registry.get("compliance_checker")
            if skill:
                res = await self.execute_hasp(skill, context)
                if res.get("status") == "pf_intervention" and res.get("result", {}).get("action") == "REJECT":
                    return res

        # 3. Behavioral Routing (S2L)
        adapter_id = self._determine_adapter(task_type, context)
        if adapter_id:
            logger.info(f"S2L: Routing to behavioral adapter: {adapter_id}")
            return {"status": "dispatched_to_adapter", "adapter": adapter_id}

        return {"status": "standard_execution"}

    def _determine_adapter(self, task_type: str, context: Dict) -> Optional[str]:
        """Functional adapter selection logic."""
        if "hedge" in task_type.lower() or context.get("needs_hedging"):
            return "lora_hedging_archetype"
        if "arbitrage" in task_type.lower() or context.get("opportunity_type") == "ARBITRAGE":
            return "lora_arbitrage_archetype"
        return None

    async def execute_hasp(self, skill: SkillArtifact, state: Dict[str, Any]) -> Dict[str, Any]:
        """Secure execution of a HASP program snippets."""
        try:
            result = await skill.executable(state)
            return {"status": "pf_intervention", "result": result, "reason": result.get("reason")}
        except Exception as e:
            logger.error(f"HASP Execution Failure: {e}")
            return {"status": "failure", "error": str(e)}

    async def _pf_volatility_guardrail(self, context: Dict) -> Dict:
        return {"action": "override_to_hold", "reason": "Volatility exceeded HASP safety threshold"}

    async def _pf_compliance_checker(self, context: Dict) -> Dict:
        # Functional check against institutional compliance rules
        if context.get("quantity", 0) > 10.0:
            return {"action": "REJECT", "reason": "Trade size exceeds compliance limit"}
        return {"action": "APPROVE"}

class HASPExecutor:
    def __init__(self, router: SkillRouter):
        self.router = router

    async def execute(self, skill_id: str, state: Dict[str, Any]) -> Dict[str, Any]:
        skill = self.router._registry.get(skill_id)
        if not skill: return {"status": "error", "message": f"Skill {skill_id} not found"}
        return await self.router.execute_hasp(skill, state)
