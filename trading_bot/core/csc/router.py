"""
SkillRouter & HASP - UCA V5 Skill Management
============================================

Orchestrates the selection and execution of Skill Programs (HASP)
and behavioral adapters (Skill-to-LoRA).
Implements 'HASP' (arXiv:2605.17734) and 'S2L' (arXiv:2606.16769).
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
    executable: Optional[Callable] = None
    adapter_id: Optional[str] = None
    metadata: Dict[str, Any] = None

class SkillRouter:
    """
    Routes agent tasks to the most efficient skill implementation:
    - HASP: Executable state-action intervention functions.
    - S2L: Lightweight LoRA adapters for behavioral archetypes.
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
        self._load_default_skills()
        self._initialized = True
        logger.info("SkillRouter initialized for UCA V5")

    def _load_default_skills(self):
        """Loads baseline skills into the registry."""
        # Example HASP Program
        self.register_skill(SkillArtifact(
            skill_id="high_vol_guardrail",
            skill_type=SkillType.HASP_PROGRAM,
            executable=self._pf_volatility_guardrail,
            metadata={"description": "Hard guardrail for high volatility"}
        ))

        # Example S2L Adapters
        self.register_skill(SkillArtifact(
            skill_id="lora_hedging_archetype",
            skill_type=SkillType.S2L_ADAPTER,
            adapter_id="hedging_v1",
            metadata={"description": "LoRA adapter for hedging behavior"}
        ))

        self.register_skill(SkillArtifact(
            skill_id="lora_arbitrage_archetype",
            skill_type=SkillType.S2L_ADAPTER,
            adapter_id="arbitrage_v1",
            metadata={"description": "LoRA adapter for arbitrage behavior"}
        ))

    def register_skill(self, artifact: SkillArtifact):
        self._registry[artifact.skill_id] = artifact
        logger.debug(f"Registered skill: {artifact.skill_id} ({artifact.skill_type.value})")

    async def route_task(self, task_type: str, context: Dict[str, Any]) -> Optional[SkillArtifact]:
        """
        Decision logic to select between HASP, S2L, or standard reasoning.
        1. Check failure-prone states for HASP intervention.
        2. Select behavioral archetype for S2L routing.
        """
        # 1. HASP Check: Failure-prone state detection
        if context.get('market', {}).get('volatility', 0) > 0.3:
            logger.warning("HASP: high volatility detected. Routing to guardrail.")
            return self._registry.get("high_vol_guardrail")

        # 2. S2L Check: Behavioral archetype matching
        if "hedge" in task_type.lower():
            return self._registry.get("lora_hedging_archetype")
        elif "arbitrage" in task_type.lower():
            return self._registry.get("lora_arbitrage_archetype")

        # 3. Fallback to registry mapping
        skill_id = self._get_mapping(task_type)
        return self._registry.get(skill_id)

    def _get_mapping(self, task_type: str) -> Optional[str]:
        mappings = {
            "execution": "vwap_hasp_v1",
            "risk_check": "compliance_gate_hasp",
            "sentiment": "sentiment_lora_v2"
        }
        return mappings.get(task_type)

    async def _pf_volatility_guardrail(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Executable PF: Hard guardrail for high volatility."""
        return {
            "status": "pf_intervention",
            "action": "override_to_hold",
            "reason": "Volatility exceeded HASP safety threshold"
        }

class HASPExecutor:
    """
    Secure execution environment for HASP (Harnessing Agents with Skill Programs).
    """
    async def execute(self, skill: SkillArtifact, state: Dict[str, Any]) -> Dict[str, Any]:
        """Executes the state-action intervention function."""
        if skill.skill_type != SkillType.HASP_PROGRAM:
            raise ValueError(f"Skill {skill.skill_id} is not a HASP program")

        if not skill.executable:
            return {"status": "failure", "error": "No executable found for HASP skill"}

        logger.info(f"HASP: Executing skill program {skill.skill_id}")
        try:
            # Check if executable is async
            if hasattr(skill.executable, '__call__'):
                import inspect
                if inspect.iscoroutinefunction(skill.executable):
                    result = await skill.executable(state)
                else:
                    result = skill.executable(state)
                return {"status": "success", "result": result}
        except Exception as e:
            logger.error(f"HASP Execution Failure: {e}")
            return {"status": "failure", "error": str(e)}

        return {"status": "failure", "error": "Unknown execution error"}
