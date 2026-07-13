"""
SkillRouter & HASP - UCA V5 Skill Management
==========================================

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
    Authoritative Skill Router for UCA V5.
    Routes tasks to either executable Program Functions (HASP) or LoRA adapters (S2L).
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SkillRouter, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._registry: Dict[str, SkillArtifact] = {}
        self._load_default_skills()
        self._initialized = True
        logger.info("SkillRouter initialized for UCA V5")

    def _load_default_skills(self):
        """Loads mandatory HASP guardrails."""
        self.register_skill(SkillArtifact(
            skill_id="high_vol_guardrail",
            skill_type=SkillType.HASP_PROGRAM,
            executable=self._pf_volatility_guardrail,
            metadata={"description": "Intercepts actions during high volatility"}
        ))

    def register_skill(self, artifact: SkillArtifact):
        self._registry[artifact.skill_id] = artifact
        logger.debug(f"Registered skill: {artifact.skill_id} ({artifact.skill_type.value})")

    async def route_task(self, agent_id: str, task_type: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main entry point for routing agent tasks.
        Implements HASP intervention logic.
        """
        # 1. Check for failure-prone states (HASP Intervention)
        if context.get('market', {}).get('volatility', 0) > 0.3:
            skill = self._registry.get("high_vol_guardrail")
            if skill:
                logger.warning(f"HASP: High volatility detected. Intervening with {skill.skill_id}")
                return await self._execute_hasp(skill, context)

        # 2. Skill-to-LoRA (S2L) Routing
        adapter_id = self._determine_adapter(task_type)
        if adapter_id:
            logger.info(f"S2L: Routing to behavior adapter: {adapter_id}")
            return {"status": "dispatched_to_adapter", "adapter_id": adapter_id}

        return {"status": "standard_execution"}

    def _determine_adapter(self, task_type: str) -> Optional[str]:
        if "hedge" in task_type.lower(): return "lora_hedging_archetype"
        if "arbitrage" in task_type.lower(): return "lora_arbitrage_archetype"
        return None

    async def _execute_hasp(self, skill: SkillArtifact, context: Dict[str, Any]) -> Dict[str, Any]:
        try:
            if asyncio.iscoroutinefunction(skill.executable):
                return await skill.executable(context)
            return skill.executable(context)
        except Exception as e:
            logger.error(f"HASP Execution Error in {skill.skill_id}: {e}")
            return {"status": "error", "error": str(e)}

    async def _pf_volatility_guardrail(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Executable PF: Hard guardrail for high volatility."""
        return {
            "status": "pf_intervention",
            "action": "override_to_hold",
            "reason": "Volatility exceeded HASP safety threshold",
            "metadata": {"volatility": context.get('market', {}).get('volatility')}
        }

import asyncio
