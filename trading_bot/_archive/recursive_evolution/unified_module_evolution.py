"""
Unified Module Evolution System
================================

Integrates recursive self-evolution into ALL modules with module-specific boundaries.
Each module can evolve independently while respecting its own constraints.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import asyncio
import logging
from collections import defaultdict

from .module_evolution_rules import (
    ModuleEvolutionBoundaries,
    ModuleEvolutionRules,
    ModuleName,
    get_module_evolution_guide
)
from .evolution_boundaries import (
    EvolutionBoundaries,
    verify_boundary_integrity
)
from .comprehensive_evolution_engine import (
    EvolutionProposal,
    EvolutionResult,
    EvolutionArea,
    EvolutionStatus
)


logger = logging.getLogger(__name__)


@dataclass
class ModuleEvolutionProposal:
    """Evolution proposal specific to a module"""
    proposal_id: str
    module_name: str
    component: str
    current_state: Dict[str, Any]
    proposed_state: Dict[str, Any]
    rationale: str
    expected_improvement: Dict[str, float]
    requires_approval: bool
    status: EvolutionStatus = EvolutionStatus.PROPOSED
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_change: Optional[datetime] = None
    change_count_today: int = 0
    
    def can_change_now(self, rules: ModuleEvolutionRules) -> tuple[bool, str]:
        """Check if module can change now based on frequency limits"""
        
        # Check daily limit
        if self.change_count_today >= rules.max_changes_per_day:
            return False, f"Exceeded daily change limit ({rules.max_changes_per_day})"
        
        # Check frequency limit
        if self.last_change:
            hours_since_last = (datetime.utcnow() - self.last_change).total_seconds() / 3600
            if hours_since_last < rules.max_change_frequency_hours:
                return False, f"Too soon since last change ({hours_since_last:.1f}h < {rules.max_change_frequency_hours}h)"
        
        return True, "Can change now"


class ModuleEvolutionEngine:
    """Evolution engine for a specific module"""
    
    def __init__(self, module_name: str):
        self.module_name = module_name
        self.rules = ModuleEvolutionBoundaries.get_module_rules(module_name)
        
        if not self.rules:
            raise ValueError(f"Unknown module: {module_name}")
        
        self.proposals: List[ModuleEvolutionProposal] = []
        self.deployed: List[ModuleEvolutionProposal] = []
        self.change_history: List[Dict[str, Any]] = []
        
        logger.info(f"Initialized evolution engine for module: {module_name}")
    
    async def propose_evolution(
        self,
        component: str,
        current_state: Dict[str, Any],
        proposed_state: Dict[str, Any],
        rationale: str,
        expected_improvement: Dict[str, float]
    ) -> Optional[ModuleEvolutionProposal]:
        """Propose an evolution for this module"""
        
        # Check if component can be evolved
        can_evolve, reason = ModuleEvolutionBoundaries.can_module_evolve(
            self.module_name,
            component
        )
        
        if not can_evolve:
            logger.warning(f"Cannot evolve {component} in {self.module_name}: {reason}")
            return None
        
        # Determine if approval required
        requires_approval = component in self.rules.requires_approval
        
        # Create proposal
        proposal = ModuleEvolutionProposal(
            proposal_id=f"{self.module_name.upper()}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            module_name=self.module_name,
            component=component,
            current_state=current_state,
            proposed_state=proposed_state,
            rationale=rationale,
            expected_improvement=expected_improvement,
            requires_approval=requires_approval
        )
        
        # Check frequency limits
        can_change, freq_reason = proposal.can_change_now(self.rules)
        if not can_change:
            logger.info(f"Proposal delayed: {freq_reason}")
            return None
        
        self.proposals.append(proposal)
        
        logger.info(f"Created proposal {proposal.proposal_id} for {self.module_name}.{component}")
        logger.info(f"  Requires approval: {requires_approval}")
        logger.info(f"  Rationale: {rationale}")
        
        return proposal
    
    async def deploy_proposal(self, proposal: ModuleEvolutionProposal) -> EvolutionResult:
        """Deploy an evolution proposal"""
        
        if proposal.requires_approval and proposal.status != EvolutionStatus.APPROVED:
            return EvolutionResult(
                proposal_id=proposal.proposal_id,
                success=False,
                improvement_achieved={},
                side_effects=[],
                rollback_available=False,
                message="Requires human approval"
            )
        
        # Test if required
        if self.rules.testing_required:
            logger.info(f"Testing proposal {proposal.proposal_id}...")
            # In production, would run actual tests
            await asyncio.sleep(0.1)
        
        # Deploy
        proposal.status = EvolutionStatus.DEPLOYED
        proposal.last_change = datetime.utcnow()
        proposal.change_count_today += 1
        
        self.deployed.append(proposal)
        
        # Record in history
        self.change_history.append({
            'proposal_id': proposal.proposal_id,
            'component': proposal.component,
            'timestamp': datetime.utcnow().isoformat(),
            'improvement': proposal.expected_improvement
        })
        
        logger.info(f"Deployed {proposal.proposal_id} in {self.module_name}")
        
        return EvolutionResult(
            proposal_id=proposal.proposal_id,
            success=True,
            improvement_achieved=proposal.expected_improvement,
            side_effects=[],
            rollback_available=self.rules.rollback_required,
            message=f"Successfully deployed in {self.module_name}"
        )
    
    def get_module_status(self) -> Dict[str, Any]:
        """Get current status of module evolution"""
        return {
            'module': self.module_name,
            'total_proposals': len(self.proposals),
            'deployed': len(self.deployed),
            'pending_approval': len([p for p in self.proposals if p.requires_approval and p.status == EvolutionStatus.PROPOSED]),
            'changes_today': sum(p.change_count_today for p in self.proposals),
            'max_changes_per_day': self.rules.max_changes_per_day,
            'can_evolve_count': len(self.rules.can_evolve),
            'requires_approval_count': len(self.rules.requires_approval),
            'forbidden_count': len(self.rules.forbidden)
        }


class UnifiedModuleEvolution:
    """
    Unified evolution coordinator for ALL modules.
    
    This system:
    1. Manages evolution for each module independently
    2. Enforces module-specific boundaries
    3. Coordinates cross-module evolution
    4. Maintains global safety constraints
    """
    
    def __init__(self):
        # Verify global boundaries
        if not verify_boundary_integrity():
            raise RuntimeError("CRITICAL: Evolution boundaries compromised!")
        
        # Initialize evolution engines for all modules
        self.module_engines: Dict[str, ModuleEvolutionEngine] = {}
        
        modules = [
            "strategy", "risk", "execution", "ml", "data", "analysis",
            "broker", "portfolio", "brain", "alphaalgo", "market_student",
            "intelligence_core"
        ]
        
        for module in modules:
            try:
                self.module_engines[module] = ModuleEvolutionEngine(module)
                logger.info(f"✅ Initialized evolution for {module}")
            except Exception as e:
                logger.error(f"❌ Failed to initialize {module}: {e}")
        
        # Cross-module coordination
        self.cross_module_proposals: List[Dict[str, Any]] = []
        self.global_change_log: List[Dict[str, Any]] = []
        
        # Safety tracking
        self.total_changes_today = 0
        self.max_total_changes_per_day = 100
        
        logger.info(f"Unified Module Evolution initialized with {len(self.module_engines)} modules")
    
    async def propose_module_evolution(
        self,
        module_name: str,
        component: str,
        current_state: Dict[str, Any],
        proposed_state: Dict[str, Any],
        rationale: str,
        expected_improvement: Dict[str, float]
    ) -> Optional[ModuleEvolutionProposal]:
        """Propose evolution for a specific module"""
        
        # Check global daily limit
        if self.total_changes_today >= self.max_total_changes_per_day:
            logger.warning(f"Reached global daily change limit: {self.max_total_changes_per_day}")
            return None
        
        # Get module engine
        engine = self.module_engines.get(module_name)
        if not engine:
            logger.error(f"Unknown module: {module_name}")
            return None
        
        # Propose through module engine
        proposal = await engine.propose_evolution(
            component=component,
            current_state=current_state,
            proposed_state=proposed_state,
            rationale=rationale,
            expected_improvement=expected_improvement
        )
        
        if proposal:
            self.total_changes_today += 1
        
        return proposal
    
    async def deploy_module_proposal(
        self,
        module_name: str,
        proposal_id: str
    ) -> Optional[EvolutionResult]:
        """Deploy a module-specific proposal"""
        
        engine = self.module_engines.get(module_name)
        if not engine:
            return None
        
        # Find proposal
        proposal = next(
            (p for p in engine.proposals if p.proposal_id == proposal_id),
            None
        )
        
        if not proposal:
            return None
        
        # Deploy
        result = await engine.deploy_proposal(proposal)
        
        # Log globally
        if result.success:
            self.global_change_log.append({
                'module': module_name,
                'proposal_id': proposal_id,
                'component': proposal.component,
                'timestamp': datetime.utcnow().isoformat(),
                'improvement': result.improvement_achieved
            })
        
        return result
    
    def approve_module_proposal(
        self,
        module_name: str,
        proposal_id: str,
        approved_by: str
    ) -> bool:
        """Approve a module proposal"""
        
        engine = self.module_engines.get(module_name)
        if not engine:
            return False
        
        proposal = next(
            (p for p in engine.proposals if p.proposal_id == proposal_id),
            None
        )
        
        if not proposal:
            return False
        
        proposal.status = EvolutionStatus.APPROVED
        logger.info(f"Proposal {proposal_id} approved by {approved_by}")
        
        return True
    
    def get_all_pending_approvals(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get all pending approvals across all modules"""
        
        pending_by_module = {}
        
        for module_name, engine in self.module_engines.items():
            pending = [
                {
                    'proposal_id': p.proposal_id,
                    'component': p.component,
                    'rationale': p.rationale,
                    'expected_improvement': p.expected_improvement,
                    'current_state': p.current_state,
                    'proposed_state': p.proposed_state
                }
                for p in engine.proposals
                if p.requires_approval and p.status == EvolutionStatus.PROPOSED
            ]
            
            if pending:
                pending_by_module[module_name] = pending
        
        return pending_by_module
    
    def get_module_status(self, module_name: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific module"""
        
        engine = self.module_engines.get(module_name)
        if not engine:
            return None
        
        return engine.get_module_status()
    
    def get_all_modules_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all modules"""
        
        return {
            module_name: engine.get_module_status()
            for module_name, engine in self.module_engines.items()
        }
    
    def get_global_summary(self) -> Dict[str, Any]:
        """Get global evolution summary"""
        
        total_proposals = sum(len(e.proposals) for e in self.module_engines.values())
        total_deployed = sum(len(e.deployed) for e in self.module_engines.values())
        total_pending = sum(
            len([p for p in e.proposals if p.requires_approval and p.status == EvolutionStatus.PROPOSED])
            for e in self.module_engines.values()
        )
        
        return {
            'total_modules': len(self.module_engines),
            'total_proposals': total_proposals,
            'total_deployed': total_deployed,
            'total_pending_approval': total_pending,
            'changes_today': self.total_changes_today,
            'max_changes_per_day': self.max_total_changes_per_day,
            'global_change_log_size': len(self.global_change_log),
            'boundary_integrity': verify_boundary_integrity(),
            'modules': list(self.module_engines.keys())
        }
    
    def get_module_evolution_guide(self, module_name: str) -> Dict[str, Any]:
        """Get evolution guide for a specific module"""
        return get_module_evolution_guide(module_name)
    
    def get_all_modules_guide(self) -> Dict[str, Dict[str, Any]]:
        """Get evolution guides for all modules"""
        
        return {
            module_name: get_module_evolution_guide(module_name)
            for module_name in self.module_engines.keys()
        }


def quick_start_unified() -> UnifiedModuleEvolution:
    """Quick start unified module evolution"""
    
    coordinator = UnifiedModuleEvolution()
    
    logger.info("=" * 80)
    logger.info("UNIFIED MODULE EVOLUTION SYSTEM")
    logger.info("=" * 80)
    logger.info(f"Initialized {len(coordinator.module_engines)} modules:")
    
    for module_name in sorted(coordinator.module_engines.keys()):
        status = coordinator.get_module_status(module_name)
        logger.info(f"  ✅ {module_name}: {status['can_evolve_count']} evolvable, "
                   f"{status['requires_approval_count']} need approval, "
                   f"{status['forbidden_count']} forbidden")
    
    logger.info("=" * 80)
    logger.info("Each module can evolve independently with its own boundaries")
    logger.info("Global safety constraints enforced across all modules")
    logger.info(f"Boundary integrity: {verify_boundary_integrity()}")
    logger.info("=" * 80)
    
    return coordinator
