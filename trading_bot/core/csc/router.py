"""
HASP (Harnessing Agents with Skill Programs) & S2L (Skill-to-LoRA) Router.
Implements the 'SkillRouter' as the authoritative tactical coordinator for UCA V5.
"""

import logging
import asyncio
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Callable
from dataclasses import dataclass

logger = logging.getLogger(__name__)

class SkillType(Enum):
    PROGRAM = "hasp_program"  # Executable Skill Program (ESP)
    LORA = "s2l_adapter"      # Skill-to-LoRA Adapter
    PROMPT = "legacy_prompt"  # Legacy advisory prompt

@dataclass
class SkillProgramResponse:
    action_final: Any
    intervention_context: Dict[str, Any]
    status: str # "PASS", "MODIFY", "VETO"

class SkillRouter:
    """
    Authoritative Router mapping task states to HASP Programs or S2L Adapters.
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
        self.programs: Dict[str, Callable[[Dict[str, Any], Any], SkillProgramResponse]] = {}
        self.adapters: Dict[str, str] = {} # Map regime -> LoRA adapter_id
        self._initialized = True
        logger.info("HASP SkillRouter initialized")

    def register_program(self, skill_id: str, program_fn: Callable):
        self.programs[skill_id] = program_fn
        logger.info(f"Registered HASP Skill Program: {skill_id}")

    def register_adapter(self, regime_id: str, adapter_id: str):
        self.adapters[regime_id] = adapter_id
        logger.info(f"Registered S2L Adapter: {adapter_id} for regime {regime_id}")

    async def route_and_execute(self, state: Dict[str, Any], proposed_action: Any) -> Tuple[Any, Dict[str, Any], str]:
        """
        Main entry point for CSC to harness agent actions.
        """
        # 1. Identify active ESPs (Guardrails)
        for pid, pfn in self.programs.items():
            try:
                res = pfn(state, proposed_action)
                if res.status != "PASS":
                    logger.warning(f"HASP: Skill Program {pid} triggered intervention: {res.status}")
                    return res.action_final, res.intervention_context, res.status
            except Exception as e:
                logger.error(f"HASP: Skill Program {pid} failed: {e}")

        # 2. Identify active S2L Adapter (Behavioral Mode)
        regime = state.get("market_regime", "UNKNOWN")
        adapter_id = self.adapters.get(regime)
        if adapter_id:
            logger.debug(f"S2L: Routing to behavioral adapter: {adapter_id}")
            return proposed_action, {"adapter_id": adapter_id}, "PASS"

        return proposed_action, {}, "PASS"

# --- Common Skill Programs (Guardrails) ---

def volatility_guardrail(state: Dict[str, Any], action: Any) -> SkillProgramResponse:
    vol = state.get("volatility", 0.0)
    if vol > 0.05:
        if action and action.get("type") == "MARKET_ORDER":
             modified_action = action.copy()
             modified_action["type"] = "LIMIT_ORDER"
             modified_action["reason"] = "HASP: Forced limit order due to high volatility"
             return SkillProgramResponse(modified_action, {"volatility": vol}, "MODIFY")
    return SkillProgramResponse(action, {}, "PASS")

def max_exposure_guardrail(state: Dict[str, Any], action: Any) -> SkillProgramResponse:
    exposure = state.get("current_exposure", 0.0)
    limit = state.get("exposure_limit", 1.0)
    if exposure > limit:
        return SkillProgramResponse(None, {"exposure": exposure, "limit": limit}, "VETO")
    return SkillProgramResponse(action, {}, "PASS")

def drawdown_guardrail(state: Dict[str, Any], action: Any) -> SkillProgramResponse:
    from ...skills.risk_management.drawdown_tracker import DrawdownDurationTracker
    import numpy as np
    equity_history = state.get("equity_history", [])
    if not equity_history:
        return SkillProgramResponse(action, {}, "PASS")
    tracker = DrawdownDurationTracker()
    res = tracker.track(np.array(equity_history))
    if res.current_drawdown < -0.15:
        return SkillProgramResponse(None, {"drawdown": res.current_drawdown}, "VETO")
    return SkillProgramResponse(action, {}, "PASS")

# Global instance
skill_router = SkillRouter()
skill_router.register_program("volatility_guard", volatility_guardrail)
skill_router.register_program("exposure_guard", max_exposure_guardrail)
skill_router.register_program("drawdown_guard", drawdown_guardrail)
