"""
SkillRouter & HASP - UCA V5 Skill Management
=========================================

Orchestrates the selection and execution of Skill Programs (HASP)
and behavioral behaviors (Skill-to-LoRA).
Implements 'HASP' (2026) and 'S2L' (2026).
"""

import logging
import threading
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
    Routes agent tasks to the most efficient skill implementation.
    Singleton implementation for UCA V5.
    """
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(SkillRouter, cls).__new__(cls)
                cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._registry: Dict[str, SkillArtifact] = {}
        self._setup_default_skills()
        self._initialized = True
        logger.info("SkillRouter initialized for UCA V5")

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
        self._registry[artifact.skill_id] = artifact
        logger.debug(f"Registered skill: {artifact.skill_id} ({artifact.skill_type.value})")

    async def route_task(self, task_type: str, observation: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Routes task based on behavioral archetypes.
        Returns a result dictionary that can include status, intervention, etc.
        """
        # 1. HASP: Hard guardrail check (Executable Skill Programs)
        if observation.get('volatility', 0) > 0.3:
            skill = self._registry.get("high_vol_guardrail")
            if skill:
                logger.warning(f"HASP: failure-prone state detected. Activating PF: high_vol_guardrail")
                return await skill.executable(observation, context)

        # 2. S2L: Behavioral adaptation (Skill-to-LoRA)
        adapter_id = self._determine_adapter(task_type, observation)
        if adapter_id:
            logger.info(f"S2L: Activating behavior adapter: {adapter_id}")
            return {"status": "dispatched_to_adapter", "adapter": adapter_id}

        return {"status": "standard_execution"}

    def _determine_adapter(self, task_type: str, observation: Dict[str, Any]) -> Optional[str]:
        """Determines the S2L behavioral archetype for the task."""
        if "hedge" in task_type.lower():
            return "lora_hedging_v5"
        if observation.get('regime') == 'TRENDING':
            return "lora_trend_follower_v5"
        return None

    async def _pf_volatility_guardrail(self, observation: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Executable PF: Hard guardrail for high volatility."""
        return {
            "status": "pf_intervention",
            "intervention": {"action_override": "REDUCE_EXPOSURE"},
            "reason": "Volatility exceeded HASP safety threshold",
            "action": "override_to_hold"
        }

class HASPExecutor:
    """
    Secure execution environment for HASP (Harnessing Agents with Skill Programs).
    """
    async def execute(self, skill: SkillArtifact, state: Dict[str, Any]) -> Dict[str, Any]:
        """Executes the state-action intervention function."""
        if skill.skill_type != SkillType.HASP_PROGRAM:
            raise ValueError(f"Skill {skill.skill_id} is not a HASP program")

        logger.info(f"HASP: Executing skill program {skill.skill_id}")
        try:
            import inspect
            if inspect.iscoroutinefunction(skill.executable):
                result = await skill.executable(state, {})
            else:
                result = skill.executable(state, {})
            return {"status": "success", "result": result}
        except Exception as e:
            logger.error(f"HASP Execution Failure: {e}")
            return {"status": "failure", "error": str(e)}
