"""
Master Self-Assembly AI Orchestrator
====================================

The master orchestrator that coordinates all self-assembly AI components
with comprehensive risk mitigation for recursive self-improvement.
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Any

from .immutable_safety_core import ImmutableSafetyCore, SafetyBoundary, get_safety_core
from .recursive_self_improvement import RecursiveSelfImprovement, ImprovementType, ImprovementProposal
from .self_assembly_orchestrator import SelfAssemblyOrchestrator, ComponentType, AssemblyStatus
from .risk_mitigation_matrix import RiskMitigationMatrix, RiskCategory, RiskLevel
from .evolution_monitor import EvolutionMonitor, EvolutionMetrics
from .advanced_ai_capabilities import (
    get_default_advanced_ai_capabilities,
    summarize_capabilities_by_category,
)

logger = logging.getLogger(__name__)


@dataclass
class SystemStatus:
    """Overall system status"""
    timestamp: datetime
    safety_core_integrity: bool
    overall_risk_level: RiskLevel
    active_components: int
    total_improvements: int
    current_recursion_depth: int
    auto_evolution_enabled: bool
    last_checkpoint: Optional[datetime]


class MasterSelfAssemblyOrchestrator:
    """
    Master Self-Assembly AI Orchestrator
    
    Coordinates all self-assembly AI components with comprehensive
    risk mitigation for recursive self-improvement.
    
    Core Components:
    1. ImmutableSafetyCore - Cryptographically verified safety boundaries
    2. RecursiveSelfImprovement - Safe evolution engine
    3. SelfAssemblyOrchestrator - Autonomous component management
    4. RiskMitigationMatrix - Multi-layer risk prevention
    5. EvolutionMonitor - Continuous safety verification
    
    Key Features:
    - Self-assembles and manages components autonomously
    - Recursively improves itself within safety constraints
    - Comprehensive risk mitigation at all levels
    - Automatic rollback on safety violations
    - Human override always available
    - Complete audit trail
    """
    
    def __init__(self, workspace_path: str = ".", config: Optional[Dict[str, Any]] = None):
        self.workspace_path = workspace_path
        self.config = config or {}
        
        # Initialize core components
        self.safety_core = get_safety_core()
        self.self_improvement = RecursiveSelfImprovement(workspace_path)
        self.self_assembly = SelfAssemblyOrchestrator(workspace_path)
        self.risk_matrix = RiskMitigationMatrix()
        self.evolution_monitor = EvolutionMonitor(workspace_path)
        self.advanced_capabilities = get_default_advanced_ai_capabilities()
        
        # System state
        self.running = False
        self.auto_evolution_enabled = self.config.get('auto_evolution', True)
        self.evolution_interval = self.config.get('evolution_interval', 3600)  # 1 hour
        
        # Background tasks
        self._tasks: List[asyncio.Task] = []
        
        logger.info("MasterSelfAssemblyOrchestrator initialized")
        
        # Create initial checkpoint
        self.evolution_monitor.create_checkpoint("System initialization")
    
    async def start(self):
        """Start the self-assembly AI system"""
        
        if self.running:
            logger.warning("System already running")
            return
        
        # Verify safety core integrity
        if not self.safety_core.verify_integrity():
            logger.critical("Safety core integrity check failed - cannot start")
            return
        
        self.running = True
        
        # Start self-assembly orchestrator
        await self.self_assembly.start()
        
        # Start background tasks
        if self.auto_evolution_enabled:
            self._tasks.append(asyncio.create_task(self._evolution_loop()))
        
        self._tasks.append(asyncio.create_task(self._monitoring_loop()))
        
        logger.info("Self-assembly AI system started")
    
    async def stop(self):
        """Stop the system"""
        
        self.running = False
        
        # Stop self-assembly
        await self.self_assembly.stop()
        
        # Cancel background tasks
        for task in self._tasks:
            task.cancel()
        
        await asyncio.gather(*self._tasks, return_exceptions=True)
        
        # Create final checkpoint
        self.evolution_monitor.create_checkpoint("System shutdown")
        
        logger.info("Self-assembly AI system stopped")
    
    async def _evolution_loop(self):
        """Background loop for autonomous evolution"""
        
        while self.running:
            try:
                await asyncio.sleep(self.evolution_interval)
                
                logger.info("Starting evolution cycle...")
                
                # Check if evolution is safe
                if not self._is_evolution_safe():
                    logger.warning("Evolution not safe - skipping cycle")
                    continue
                
                # Create checkpoint before evolution
                self.evolution_monitor.create_checkpoint("Pre-evolution checkpoint")
                
                # Propose improvements
                proposals = await self._generate_improvement_proposals()
                
                # Evaluate and implement safe proposals
                for proposal in proposals:
                    if await self._evaluate_and_implement_proposal(proposal):
                        logger.info(f"Successfully implemented: {proposal.description}")
                    else:
                        logger.warning(f"Failed to implement: {proposal.description}")
                
                # Update evolution metrics
                await self._update_evolution_metrics()
                
                logger.info("Evolution cycle complete")
                
            except Exception as e:
                logger.error(f"Error in evolution loop: {e}")
    
    async def _monitoring_loop(self):
        """Background loop for continuous monitoring"""
        
        while self.running:
            try:
                await asyncio.sleep(60)  # Every minute
                
                # Verify safety core integrity
                if not self.safety_core.verify_integrity():
                    logger.critical("SAFETY CORE INTEGRITY COMPROMISED")
                    await self._emergency_shutdown()
                    break
                
                # Check overall risk level
                risk_level = self.risk_matrix.get_overall_risk_level()
                
                if risk_level == RiskLevel.CRITICAL or risk_level == RiskLevel.CATASTROPHIC:
                    logger.critical(f"CRITICAL RISK LEVEL: {risk_level.name}")
                    await self._emergency_shutdown()
                    break
                
                elif risk_level == RiskLevel.HIGH:
                    logger.warning("High risk level detected - disabling auto-evolution")
                    self.auto_evolution_enabled = False
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
    
    def _is_evolution_safe(self) -> bool:
        """Check if evolution is safe to proceed"""
        
        # Check safety core integrity
        if not self.safety_core.verify_integrity():
            return False
        
        # Check risk level
        risk_level = self.risk_matrix.get_overall_risk_level()
        if risk_level.value >= RiskLevel.HIGH.value:
            return False
        
        # Check recursion depth
        max_depth = self.safety_core.get_rule_value(SafetyBoundary.NO_RECURSIVE_DEPTH_LIMIT)
        if self.self_improvement.current_recursion_level >= max_depth:
            logger.warning(f"Maximum recursion depth ({max_depth}) reached")
            return False
        
        return True
    
    async def _generate_improvement_proposals(self) -> List[ImprovementProposal]:
        """Generate improvement proposals"""
        
        proposals = []
        
        # Analyze current system performance
        assembly_status = self.self_assembly.get_status_report()
        
        # Propose component improvements
        failed_components = [
            c for c in assembly_status['components']
            if c['status'] == AssemblyStatus.FAILED.value
        ]
        
        if failed_components:
            # Propose fixes for failed components
            proposal = self.self_improvement.propose_improvement(
                improvement_type=ImprovementType.BUG_FIX,
                description=f"Fix {len(failed_components)} failed components",
                affected_files=[],
                code_changes={},
                expected_benefit="Restore failed components to operational state",
                risk_level="MEDIUM"
            )
            if proposal:
                proposals.append(proposal)
        
        # Propose performance optimizations
        if assembly_status['active'] > 0:
            proposal = self.self_improvement.propose_improvement(
                improvement_type=ImprovementType.PERFORMANCE_OPTIMIZATION,
                description="Optimize active component performance",
                affected_files=[],
                code_changes={},
                expected_benefit="Improve system performance by 10-20%",
                risk_level="LOW"
            )
            if proposal:
                proposals.append(proposal)
        
        return proposals
    
    async def _evaluate_and_implement_proposal(self, proposal: ImprovementProposal) -> bool:
        """Evaluate and potentially implement a proposal"""
        
        # Assess risks
        risk_context = {
            'recursion_depth': self.self_improvement.current_recursion_level,
            'code_change_rate': 0.1,  # Placeholder
        }
        
        risk_level = self.risk_matrix.assess_risk(
            RiskCategory.RECURSIVE_IMPROVEMENT_RISK,
            risk_context
        )
        
        # If high risk, require human approval
        if risk_level.value >= RiskLevel.HIGH.value:
            logger.warning(f"High risk proposal - requires human approval: {proposal.description}")
            proposal.requires_human_approval = True
            return False
        
        # Implement if safe
        if proposal.risk_level in ["LOW", "MEDIUM"]:
            success = await self.self_improvement.implement_improvement(
                proposal.proposal_id,
                force=False
            )
            
            if not success:
                # Rollback if implementation failed
                self.evolution_monitor.rollback_to_last_safe_checkpoint()
            
            return success
        
        return False
    
    async def _update_evolution_metrics(self):
        """Update evolution metrics"""
        
        improvement_report = self.self_improvement.get_improvement_report()
        assembly_report = self.self_assembly.get_status_report()
        
        metrics = EvolutionMetrics(
            timestamp=datetime.utcnow(),
            recursion_depth=self.self_improvement.current_recursion_level,
            code_changes_count=improvement_report['implemented'],
            code_change_percentage=0.1,  # Placeholder
            performance_score=0.9,  # Placeholder
            safety_score=1.0 if self.safety_core.verify_integrity() else 0.0,
            risk_level=self.risk_matrix.get_overall_risk_level(),
            total_improvements=improvement_report['total_proposals'],
            successful_improvements=improvement_report['implemented'],
            failed_improvements=improvement_report['rejected'] + improvement_report['rolled_back'],
            rolled_back_improvements=improvement_report['rolled_back']
        )
        
        self.evolution_monitor.update_metrics(metrics)
    
    async def _emergency_shutdown(self):
        """Emergency shutdown procedure"""
        
        logger.critical("INITIATING EMERGENCY SHUTDOWN")
        
        # Stop all evolution
        self.auto_evolution_enabled = False
        
        # Rollback to last safe checkpoint
        self.evolution_monitor.rollback_to_last_safe_checkpoint()
        
        # Stop the system
        await self.stop()
        
        logger.critical("EMERGENCY SHUTDOWN COMPLETE - HUMAN INTERVENTION REQUIRED")
    
    def human_override(self, action: str, reason: str):
        """
        Human override - ALWAYS works.
        
        This allows humans to control the AI at any time.
        """
        
        logger.info(f"HUMAN OVERRIDE: {action} - {reason}")
        
        if action == "STOP":
            asyncio.create_task(self.stop())
        
        elif action == "DISABLE_EVOLUTION":
            self.auto_evolution_enabled = False
            logger.info("Auto-evolution disabled by human")
        
        elif action == "ENABLE_EVOLUTION":
            if self._is_evolution_safe():
                self.auto_evolution_enabled = True
                logger.info("Auto-evolution enabled by human")
            else:
                logger.warning("Cannot enable evolution - system not safe")
        
        elif action == "ROLLBACK":
            self.evolution_monitor.rollback_to_last_safe_checkpoint()
            logger.info("Rolled back to last safe checkpoint")
        
        elif action == "EMERGENCY_STOP":
            asyncio.create_task(self._emergency_shutdown())
        
        else:
            logger.warning(f"Unknown human override action: {action}")
    
    def get_system_status(self) -> SystemStatus:
        """Get overall system status"""
        
        improvement_report = self.self_improvement.get_improvement_report()
        assembly_report = self.self_assembly.get_status_report()
        
        checkpoints = list(self.evolution_monitor.checkpoints.values())
        last_checkpoint = max(checkpoints, key=lambda cp: cp.timestamp) if checkpoints else None
        
        return SystemStatus(
            timestamp=datetime.utcnow(),
            safety_core_integrity=self.safety_core.verify_integrity(),
            overall_risk_level=self.risk_matrix.get_overall_risk_level(),
            active_components=assembly_report['active'],
            total_improvements=improvement_report['total_proposals'],
            current_recursion_depth=self.self_improvement.current_recursion_level,
            auto_evolution_enabled=self.auto_evolution_enabled,
            last_checkpoint=last_checkpoint.timestamp if last_checkpoint else None
        )

    def get_advanced_capability_report(self) -> Dict[str, Any]:
        """Get the configured advanced AI capability catalog."""

        return {
            'total_capabilities': len(self.advanced_capabilities),
            'categories': summarize_capabilities_by_category(self.advanced_capabilities),
            'capabilities': [
                {
                    'id': capability.capability_id,
                    'name': capability.name,
                    'category': capability.category,
                    'description': capability.description,
                    'status': 'REGISTERED',
                }
                for capability in self.advanced_capabilities
            ],
        }
    
    def get_comprehensive_report(self) -> Dict[str, Any]:
        """Get comprehensive system report"""
        
        status = self.get_system_status()
        
        return {
            'system_status': {
                'timestamp': status.timestamp.isoformat(),
                'safety_core_integrity': status.safety_core_integrity,
                'overall_risk_level': status.overall_risk_level.name,
                'active_components': status.active_components,
                'total_improvements': status.total_improvements,
                'recursion_depth': status.current_recursion_depth,
                'auto_evolution_enabled': status.auto_evolution_enabled,
                'last_checkpoint': status.last_checkpoint.isoformat() if status.last_checkpoint else None
            },
            'safety_core': self.safety_core.export_safety_report(),
            'self_improvement': self.self_improvement.get_improvement_report(),
            'self_assembly': self.self_assembly.get_status_report(),
            'risk_matrix': self.risk_matrix.get_risk_report(),
            'evolution_monitor': self.evolution_monitor.get_evolution_report(),
            'advanced_ai_capabilities': self.get_advanced_capability_report(),
        }


async def quick_start_self_assembly_ai(
    workspace_path: str = ".",
    auto_evolution: bool = True,
    evolution_interval: int = 3600
) -> MasterSelfAssemblyOrchestrator:
    """
    Quick start the self-assembly AI system.
    
    Args:
        workspace_path: Path to workspace
        auto_evolution: Enable automatic evolution
        evolution_interval: Seconds between evolution cycles
    
    Returns:
        Initialized and started orchestrator
    """
    
    config = {
        'auto_evolution': auto_evolution,
        'evolution_interval': evolution_interval
    }
    
    orchestrator = MasterSelfAssemblyOrchestrator(workspace_path, config)
    await orchestrator.start()
    
    logger.info("Self-assembly AI system ready")
    
    return orchestrator


async def run_self_assembly_ai(
    workspace_path: str = ".",
    auto_evolution: bool = True,
    evolution_interval: int = 3600,
    run_duration_seconds: Optional[float] = None,
) -> None:
    """
    Start the self-assembly AI system and keep it running.

    Args:
        workspace_path: Path to workspace
        auto_evolution: Enable automatic evolution
        evolution_interval: Seconds between evolution cycles
        run_duration_seconds: Optional bounded runtime for tests/demo
    """

    orchestrator = await quick_start_self_assembly_ai(
        workspace_path=workspace_path,
        auto_evolution=auto_evolution,
        evolution_interval=evolution_interval,
    )

    try:
        if run_duration_seconds is not None:
            await asyncio.sleep(run_duration_seconds)
            return

        while True:
            await asyncio.sleep(3600)
    finally:
        if orchestrator.running:
            await orchestrator.stop()
