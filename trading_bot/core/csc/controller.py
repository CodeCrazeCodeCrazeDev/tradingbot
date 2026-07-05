"""
Cognitive System Controller (CSC) - Authoritative Core
======================================================

Implements the Active Inference (VFE minimization) loop and
HIPIF (Hierarchical Planning with Information Folding).
"""

import logging
import asyncio
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime

from .folding import FoldingOperator
from ..unified_event_bus import decision_bus, UnifiedEvent, EventPriority
from ..alphaalgo_core_engine import CoreDecision, DecisionOutcome

logger = logging.getLogger(__name__)

class CognitiveSystemController:
    """
    The Unified 'One Brain' Controller for AlphaAlgo.
    """
    def __init__(self, world_model: Any, hms: Any, shield: Any):
        self.world_model = world_model
        self.hms = hms
        self.shield = shield
        self.folding_operator = FoldingOperator(hms)

        self.is_running = False
        self._loop_task = None

    async def start(self):
        self.is_running = True
        logger.info("CSC Core: Active Inference loop started")

    async def process_market_observation(self, observation: Dict[str, Any]) -> Optional[CoreDecision]:
        """
        The authoritative OSA-HIPIF (Observe-Simulate-Act) pipeline.
        """
        logger.info(f"CSC: Processing observation for {observation.get('symbol', 'UNKNOWN')}")

        try:
            # 1. Update Epistemic Beliefs (Active Inference)
            # z_t = argmin_z VFE(z; observation)
            latent_state = self.world_model.encoder(observation)
            self.hms.write("working", "current_latent", latent_state)

            # 2. Simulate & Plan (The Imagination Layer)
            # Find action sequence pi that minimizes Expected Free Energy (EFE)
            scenarios = self.world_model.simulator.simulate(latent_state)
            self.hms.write("episodic", f"sim_{datetime.utcnow().timestamp()}", scenarios)

            # 3. Verification Swarm Audit (Evidence-First)
            # Every simulation must be challenged
            is_valid = await self._run_verification_swarm(scenarios)
            if not is_valid:
                logger.warning("CSC: Verification swarm rejected scenarios. Inaction.")
                return None

            # 4. Decision Selection
            # Under Active Inference, we select the policy that minimizes EFE
            best_plan = self._select_best_plan(scenarios)

            # 5. Governance Check (Immutable Shield)
            shield_report = self.shield.validate_action("trade", best_plan, {"market": observation})
            if shield_report.decision.value != "APPROVED":
                logger.warning(f"CSC: Blocked by Shield: {shield_report.reason}")
                return None

            # 6. Execute via Decision Bus
            await decision_bus.publish(UnifiedEvent(
                event_type="EXECUTION_REQUEST",
                payload=best_plan,
                source="CSC",
                priority=EventPriority.HIGH
            ))

            # 7. Strategic Folding (HIPIF)
            # Every 10 steps, compress episodic history into semantic lessons
            await self.folding_operator.fold_step()

            return CoreDecision(outcome=DecisionOutcome.TRADE_APPROVED, trade_id=str(datetime.utcnow().timestamp()))

        except Exception as e:
            logger.error(f"CSC: Pipeline failure: {e}", exc_info=True)
            return None

    async def _run_verification_swarm(self, scenarios: List[Any]) -> bool:
        """Mock verifier - in production this calls trading_bot/core/verification/swarm.py"""
        return True

    def _select_best_plan(self, scenarios: List[Any]) -> Dict[str, Any]:
        """Mock selection - in production this uses the Planning Engine."""
        return {"action": "BUY", "quantity": 1.0, "symbol": "EURUSD"}
