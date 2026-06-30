"""
Improvement Orchestrator
Drives the Observe-Identify-Hypothesize-Experiment-Keep/Reject cycle.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional
from .registry import ImprovementRegistry, ImprovementType, ImprovementStatus
from .evaluator import ImprovementEvaluator
from .sandbox import VerificationSandbox

logger = logging.getLogger(__name__)

class ImprovementOrchestrator:
    """
    Orchestrates the unified self-improvement loop.
    """
    def __init__(self, registry: ImprovementRegistry, evaluator: ImprovementEvaluator, config: Optional[Dict] = None):
        self.registry = registry
        self.evaluator = evaluator
        self.sandbox = VerificationSandbox()
        self.config = config or {}
        self.running = False

    async def run_cycle(self, observations: Dict[str, Any]):
        """
        Run one iteration of the self-improvement loop.
        """
        logger.info("Starting Unified Improvement Cycle")

        # 1. Observe (Already provided via observations)

        # 2. Identify & Hypothesize
        # In a full implementation, this calls an LLM or Specialized Agent
        # to look at failures in 'observations' and propose an ImprovementRecord.

        # 3. Process Pending Candidates
        candidates = self.registry.get_by_status(ImprovementStatus.CANDIDATE)
        for cand in candidates:
            await self._process_candidate(cand)

        logger.info("Improvement Cycle Complete")

    async def _process_candidate(self, candidate: Any):
        """
        Move a candidate through the evaluation pipeline.
        """
        self.registry.update_status(candidate.improvement_id, ImprovementStatus.EVALUATING)

        try:
            if candidate.type == ImprovementType.META:
                # Meta-intelligence evaluation
                # Typically involves re-running a failed task with a new prompt/workflow
                result = await self.evaluator.evaluate_reasoning(candidate.proposal.get('trace', {}))

                if result.overall_score > 0.7:
                    self.registry.update_status(
                        candidate.improvement_id,
                        ImprovementStatus.PRODUCTION,
                        {"score": result.overall_score, "feedback": result.feedback}
                    )
                else:
                    self.registry.update_status(candidate.improvement_id, ImprovementStatus.REJECTED)

            elif candidate.type == ImprovementType.TRADING:
                # Trading intelligence evaluation
                # Triggers a backtest (mocked here)
                mock_backtest = {"sharpe": 1.5, "max_drawdown": 0.1, "p_value": 0.02, "oos_decay": 0.1}
                result = await self.evaluator.evaluate_trading_improvement(candidate.proposal, mock_backtest)

                if result['success']:
                    self.registry.update_status(
                        candidate.improvement_id,
                        ImprovementStatus.SHADOW,
                        result['metrics']
                    )
                else:
                    self.registry.update_status(candidate.improvement_id, ImprovementStatus.REJECTED, result['metrics'])

            elif candidate.type == ImprovementType.CODE:
                # Code evolution evaluation
                # Triggers the Sandbox (mocked here)
                mock_report = {"tests_passed": True, "coverage_delta": 0.02, "performance_impact": -0.01}
                result = await self.evaluator.evaluate_code_improvement(mock_report)

                if result['success']:
                    self.registry.update_status(
                        candidate.improvement_id,
                        ImprovementStatus.SHADOW,
                        result['metrics']
                    )
                else:
                    self.registry.update_status(candidate.improvement_id, ImprovementStatus.REJECTED, result['metrics'])

        except Exception as e:
            logger.error(f"Error evaluating improvement {candidate.improvement_id}: {e}")
            self.registry.update_status(candidate.improvement_id, ImprovementStatus.REJECTED, {"error": str(e)})

    async def propose_meta_improvement(self, domain: str, source: str, trace: Any, suggestion: str):
        """Helper to propose a reasoning/workflow improvement."""
        proposal = {
            "trace": trace.to_dict() if hasattr(trace, 'to_dict') else trace,
            "suggestion": suggestion
        }
        return self.registry.register_proposal(ImprovementType.META, domain, source, proposal)

    async def propose_trading_improvement(self, domain: str, source: str, logic: str, parameters: Dict):
        """Helper to propose a strategy/model improvement."""
        proposal = {
            "logic": logic,
            "parameters": parameters
        }
        return self.registry.register_proposal(ImprovementType.TRADING, domain, source, proposal)

    async def propose_code_improvement(self, domain: str, source: str, patch: str, base_file: str):
        """Helper to propose a code-level improvement."""
        proposal = {
            "patch": patch,
            "base_file": base_file
        }
        return self.registry.register_proposal(ImprovementType.CODE, domain, source, proposal)
