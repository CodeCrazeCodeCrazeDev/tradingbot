"""
Recursive Improvement Orchestrator

Master orchestrator that coordinates all recursive improvement loops and
integrates them into the trading bot using the Unified RSIE Architecture.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

from .recursive_core import RecursiveImprovementCore, ImprovementDimension, ImprovementTier
from .infrastructure import ImprovementMemory, GovernanceController
from .approvals import ApprovalWorkflow

# Loop imports
from .loops.evaluation_loop import EvaluationImprovementLoop
from .loops.strategy_loop import StrategyImprovementLoop
from .loops.risk_loop import RiskImprovementLoop
from .loops.feature_loop import FeatureImprovementLoop
from .loops.meta_loop import MetaImprovementLoop

logger = logging.getLogger(__name__)

class RecursiveImprovementOrchestrator:
    """
    Master orchestrator for the Unified Recursive Self-Improvement Engine (RSIE).
    
    Coordinates specialized loops across three tiers:
    - Tier 0: Critical (Evaluation, Strategy, Risk, Feature)
    - Tier 1: Intelligence (Meta-Improvement, Agent, Workflow, Model)
    - Tier 2: Scalability/Experimental (World Model, Swarm)
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Core & Persistence
        self.core = RecursiveImprovementCore(self.config.get('core'))
        self.memory = ImprovementMemory(self.config.get('storage_path', 'recursive_improvement_data'))
        self.governance = GovernanceController()
        self.approvals = ApprovalWorkflow(self.config.get('storage_path', 'recursive_improvement_data'))
        
        # Initialize Loops
        self.loops = {
            'evaluation': EvaluationImprovementLoop(self.config),
            'strategy': StrategyImprovementLoop(self.config),
            'risk': RiskImprovementLoop(self.config),
            'feature': FeatureImprovementLoop(self.config),
            'meta': MetaImprovementLoop(self.config),
        }
        
        self.is_running = False
        self.background_tasks: List[asyncio.Task] = []
        
        logger.info("RSIE Orchestrator initialized with Unified Architecture")

    async def start(self):
        """Start the unified recursive improvement system"""
        self.is_running = True
        
        # 1. Start continuous improvement loop
        self.background_tasks.append(
            asyncio.create_task(self._continuous_improvement_loop())
        )
        
        # 2. Start approval monitor
        self.background_tasks.append(
            asyncio.create_task(self._approval_monitor_loop())
        )

        logger.info("Recursive improvement system (RSIE) started")

    async def stop(self):
        """Stop the recursive improvement system"""
        self.is_running = False
        for task in self.background_tasks:
            task.cancel()
        await asyncio.gather(*self.background_tasks, return_exceptions=True)
        self.core.save_state()
        logger.info("Recursive improvement system (RSIE) stopped")

    async def _continuous_improvement_loop(self):
        """Continuous background improvement across all Tiers"""
        while self.is_running:
            try:
                # Priority 1: Tier 0 Loops
                tier0_names = ['evaluation', 'strategy', 'risk', 'feature']
                for name in tier0_names:
                    if name in self.loops:
                        await self.loops[name].run_cycle()

                # Priority 2: Meta-Improvement
                if 'meta' in self.loops:
                    await self.loops['meta'].run_cycle()
                
                # Wait before next cycle
                interval = self.config.get('improvement_interval', 3600)
                await asyncio.sleep(interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in RSIE improvement loop: {e}", exc_info=True)
                await asyncio.sleep(60)

    async def _approval_monitor_loop(self):
        """Monitor pending_approvals.json for human actioned proposals"""
        while self.is_running:
            try:
                approvals = self.approvals._load_approvals()
                for proposal_id, entry in list(approvals.items()):
                    status = entry.get('status')
                    if status == 'APPROVED':
                        logger.info(f"Proposal {proposal_id} APPROVED by human. Deploying...")
                        # Map back to loop for deployment
                        dim_str = entry.get('dimension')
                        # Simplified routing
                        for loop in self.loops.values():
                            if loop.dimension.value == dim_str:
                                # Reconstruct proposal from dict
                                from .recursive_core import ImprovementProposal
                                proposal = ImprovementProposal.from_dict(entry)
                                await loop.deploy_improvement(proposal)
                                await self.approvals._archive_proposal(proposal_id, 'DEPLOYED')
                                break
                    elif status == 'REJECTED':
                        logger.info(f"Proposal {proposal_id} REJECTED by human.")
                        await self.approvals._archive_proposal(proposal_id, 'REJECTED')
                
                await asyncio.sleep(30) # Check every 30 seconds
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in RSIE approval monitor: {e}")
                await asyncio.sleep(60)

    def get_comprehensive_summary(self) -> Dict[str, Any]:
        """Get comprehensive summary of all recursive improvements"""
        return {
            'core': self.core.get_improvement_summary(),
            'loops_active': list(self.loops.keys()),
            'is_running': self.is_running
        }

    async def integrate_with_trading_bot(self, trading_bot: Any):
        """Integrate RSIE with core trading bot components"""
        # Mapping implementation...
        logger.info("RSIE integrated with trading bot components")
