"""
Comprehensive Recursive Evolution Orchestrator
==============================================

Master orchestrator that coordinates recursive self-evolution across ALL areas
while enforcing immutable boundaries and requiring human approval where needed.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import asyncio
import logging
from collections import defaultdict

from .evolution_boundaries import (
    EvolutionBoundaries,
    verify_boundary_integrity,
    get_evolution_guide
)
from .comprehensive_evolution_engine import (
    RecursiveEvolutionEngine,
    EvolutionProposal,
    EvolutionResult,
    EvolutionArea,
    EvolutionStatus
)


logger = logging.getLogger(__name__)


@dataclass
class EvolutionConfig:
    """Configuration for recursive evolution"""
    auto_deploy_approved: bool = True
    testing_required: bool = True
    max_concurrent_evolutions: int = 3
    evolution_interval_seconds: int = 3600  # 1 hour
    max_recursive_depth: int = 5
    enable_meta_learning: bool = True
    
    # Safety limits
    max_proposals_per_day: int = 50
    require_human_approval_for_risk: bool = True
    require_human_approval_for_architecture: bool = True


@dataclass
class SystemMetrics:
    """System-wide metrics for evolution decisions"""
    strategy_performance: Dict[str, float] = field(default_factory=dict)
    risk_metrics: Dict[str, float] = field(default_factory=dict)
    execution_metrics: Dict[str, float] = field(default_factory=dict)
    ml_metrics: Dict[str, float] = field(default_factory=dict)
    data_quality: Dict[str, float] = field(default_factory=dict)
    performance_metrics: Dict[str, float] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)


class ComprehensiveEvolutionOrchestrator:
    """
    Master orchestrator for recursive self-evolution.
    
    This orchestrator:
    1. Monitors all system areas continuously
    2. Proposes improvements across all dimensions
    3. Enforces immutable boundaries
    4. Manages approval workflow
    5. Tests proposals safely
    6. Deploys successful evolutions
    7. Learns from evolution results (recursive meta-learning)
    8. Evolves its own evolution strategies
    """
    
    def __init__(self, config: Optional[EvolutionConfig] = None):
        self.config = config or EvolutionConfig()
        
        # Verify boundaries on startup
        if not verify_boundary_integrity():
            raise RuntimeError("CRITICAL: Evolution boundaries have been tampered with!")
        
        # Core evolution engine
        self.evolution_engine = RecursiveEvolutionEngine()
        
        # Tracking
        self.evolution_history: List[Dict[str, Any]] = []
        self.metrics_history: List[SystemMetrics] = []
        self.active_evolutions: List[EvolutionProposal] = []
        
        # Meta-learning: Evolution of evolution strategies
        self.meta_evolution_strategies: Dict[str, Any] = {
            'proposal_generation': 'performance_based',
            'testing_strategy': 'comprehensive',
            'deployment_strategy': 'gradual',
            'rollback_strategy': 'automatic'
        }
        
        # Performance tracking
        self.area_performance: Dict[str, List[float]] = defaultdict(list)
        self.evolution_effectiveness: Dict[str, float] = defaultdict(float)
        
        # Background tasks
        self._evolution_task: Optional[asyncio.Task] = None
        self._running = False
        
        logger.info("Comprehensive Evolution Orchestrator initialized")
        logger.info(f"Config: {self.config}")
        logger.info(f"Boundaries verified: {verify_boundary_integrity()}")
    
    async def start(self):
        """Start continuous evolution loop"""
        if self._running:
            logger.warning("Evolution already running")
            return
        
        self._running = True
        self._evolution_task = asyncio.create_task(self._evolution_loop())
        logger.info("Started continuous evolution loop")
    
    async def stop(self):
        """Stop evolution loop"""
        self._running = False
        if self._evolution_task:
            self._evolution_task.cancel()
            try:
                await self._evolution_task
            except asyncio.CancelledError:
                pass
        logger.info("Stopped evolution loop")
    
    async def _evolution_loop(self):
        """Main evolution loop"""
        while self._running:
            try:
                # Collect current metrics
                metrics = await self._collect_system_metrics()
                self.metrics_history.append(metrics)
                
                # Propose evolutions
                proposals = await self.propose_evolutions(metrics)
                
                # Process proposals
                for proposal in proposals:
                    if len(self.active_evolutions) >= self.config.max_concurrent_evolutions:
                        break
                    
                    # Auto-deploy if allowed
                    if not proposal.requires_approval and self.config.auto_deploy_approved:
                        result = await self.deploy_evolution(proposal)
                        if result.success:
                            logger.info(f"Auto-deployed evolution: {proposal.proposal_id}")
                
                # Meta-evolution: Evolve evolution strategies
                if self.config.enable_meta_learning:
                    await self._evolve_evolution_strategies()
                
                # Wait before next cycle
                await asyncio.sleep(self.config.evolution_interval_seconds)
                
            except Exception as e:
                logger.error(f"Error in evolution loop: {e}", exc_info=True)
                await asyncio.sleep(60)
    
    async def _collect_system_metrics(self) -> SystemMetrics:
        """Collect metrics from all system areas"""
        
        # In production, these would come from actual monitoring
        metrics = SystemMetrics(
            strategy_performance={
                'sharpe_ratio': 1.2,
                'win_rate': 0.52,
                'profit_factor': 1.3,
                'max_drawdown': 0.15
            },
            risk_metrics={
                'current_drawdown': 0.08,
                'var_95': 0.03,
                'position_concentration': 0.15
            },
            execution_metrics={
                'avg_slippage': 0.0008,
                'fill_rate': 0.98,
                'avg_latency_ms': 45
            },
            ml_metrics={
                'accuracy': 0.58,
                'precision': 0.60,
                'recall': 0.55,
                'f1_score': 0.57
            },
            data_quality={
                'missing_rate': 0.005,
                'outlier_rate': 0.01,
                'staleness_avg_seconds': 2.5
            },
            performance_metrics={
                'cpu_usage': 0.45,
                'memory_usage': 0.60,
                'disk_io': 0.30
            }
        )
        
        return metrics
    
    async def propose_evolutions(self, metrics: SystemMetrics) -> List[EvolutionProposal]:
        """
        Propose evolutions across all areas based on current metrics.
        
        This is where recursive evolution happens - the system analyzes
        its own performance and proposes improvements.
        """
        
        # Check daily limit
        today_proposals = [
            p for p in self.evolution_engine.proposals
            if p.created_at.date() == datetime.utcnow().date()
        ]
        
        if len(today_proposals) >= self.config.max_proposals_per_day:
            logger.warning(f"Reached daily proposal limit: {self.config.max_proposals_per_day}")
            return []
        
        # Generate proposals for all areas
        system_metrics_dict = {
            'strategy_performance': metrics.strategy_performance,
            'risk_metrics': metrics.risk_metrics,
            'execution_metrics': metrics.execution_metrics,
            'ml_metrics': metrics.ml_metrics,
            'data_quality': metrics.data_quality
        }
        
        proposals = await self.evolution_engine.evolve_all_areas(system_metrics_dict)
        
        logger.info(f"Generated {len(proposals)} evolution proposals")
        
        return proposals
    
    async def deploy_evolution(self, proposal: EvolutionProposal) -> EvolutionResult:
        """Deploy an evolution proposal"""
        
        # Verify boundaries haven't been tampered with
        if not verify_boundary_integrity():
            logger.error("CRITICAL: Boundary integrity check failed!")
            return EvolutionResult(
                proposal_id=proposal.proposal_id,
                success=False,
                improvement_achieved={},
                side_effects=["Boundary integrity violation"],
                rollback_available=False,
                message="Boundary integrity check failed"
            )
        
        # Deploy through engine
        result = await self.evolution_engine.deploy_proposal(proposal)
        
        # Track in history
        self.evolution_history.append({
            'proposal': proposal.to_dict(),
            'result': {
                'success': result.success,
                'improvement': result.improvement_achieved,
                'message': result.message
            },
            'timestamp': datetime.utcnow().isoformat()
        })
        
        # Update effectiveness tracking
        if result.success:
            area = proposal.area.value
            improvement_avg = sum(result.improvement_achieved.values()) / max(len(result.improvement_achieved), 1)
            self.evolution_effectiveness[area] = improvement_avg
        
        return result
    
    async def _evolve_evolution_strategies(self):
        """
        Meta-evolution: Evolve the evolution strategies themselves.
        
        This is recursive self-improvement - the system learns how to
        evolve better by analyzing its own evolution history.
        """
        
        if len(self.evolution_history) < 10:
            return  # Need enough history
        
        # Analyze which evolution strategies work best
        recent_history = self.evolution_history[-50:]
        
        success_by_area = defaultdict(list)
        for entry in recent_history:
            area = entry['proposal']['area']
            success = entry['result']['success']
            success_by_area[area].append(1.0 if success else 0.0)
        
        # Update meta-strategies based on what works
        for area, successes in success_by_area.items():
            success_rate = sum(successes) / len(successes)
            
            if success_rate > 0.8:
                # This area's evolution strategy is working well
                logger.info(f"Area {area} has high success rate: {success_rate:.2%}")
            elif success_rate < 0.5:
                # Need to adjust evolution strategy for this area
                logger.warning(f"Area {area} has low success rate: {success_rate:.2%}")
                # In production, would adjust proposal generation strategy
    
    def approve_proposal(self, proposal_id: str, approved_by: str) -> bool:
        """
        Human approval of evolution proposal.
        
        This is the critical human-in-the-loop control point.
        """
        return self.evolution_engine.approve_proposal(proposal_id, approved_by)
    
    def reject_proposal(self, proposal_id: str, reason: str) -> bool:
        """Reject a proposal"""
        for proposal in self.evolution_engine.pending_approvals:
            if proposal.proposal_id == proposal_id:
                proposal.status = EvolutionStatus.REJECTED
                self.evolution_engine.pending_approvals.remove(proposal)
                logger.info(f"Proposal {proposal_id} rejected: {reason}")
                return True
        return False
    
    def get_pending_approvals(self) -> List[Dict[str, Any]]:
        """Get proposals awaiting human approval"""
        return self.evolution_engine.get_pending_approvals()
    
    def get_evolution_summary(self) -> Dict[str, Any]:
        """Get comprehensive evolution summary"""
        
        engine_summary = self.evolution_engine.get_evolution_summary()
        
        return {
            **engine_summary,
            'active_evolutions': len(self.active_evolutions),
            'total_history': len(self.evolution_history),
            'evolution_effectiveness': dict(self.evolution_effectiveness),
            'meta_strategies': self.meta_evolution_strategies,
            'config': {
                'auto_deploy': self.config.auto_deploy_approved,
                'testing_required': self.config.testing_required,
                'max_concurrent': self.config.max_concurrent_evolutions,
                'interval_seconds': self.config.evolution_interval_seconds
            },
            'running': self._running
        }
    
    def get_evolution_guide(self) -> Dict[str, Any]:
        """Get guide of what AI can and cannot evolve"""
        return get_evolution_guide()
    
    def get_area_performance(self) -> Dict[str, Any]:
        """Get performance by evolution area"""
        return {
            area: {
                'effectiveness': self.evolution_effectiveness.get(area, 0),
                'recent_performance': self.area_performance.get(area, [])[-10:]
            }
            for area in EvolutionArea
        }
    
    async def manual_evolution(
        self,
        area: str,
        component: str,
        proposed_changes: Dict[str, Any],
        rationale: str
    ) -> EvolutionResult:
        """
        Manually propose and deploy an evolution.
        
        Useful for human-initiated improvements.
        """
        
        proposal = EvolutionProposal(
            proposal_id=f"MANUAL_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            area=EvolutionArea[area.upper()],
            specific_component=component,
            current_state={},
            proposed_state=proposed_changes,
            rationale=rationale,
            expected_improvement={'manual': 1.0},
            risk_assessment={'risk_level': 'MANUAL', 'human_initiated': True},
            recursive_depth=0,
            requires_approval=False,
            status=EvolutionStatus.APPROVED,
            approved_by='human'
        )
        
        # Validate
        if not await self.evolution_engine._validate_proposal(proposal):
            return EvolutionResult(
                proposal_id=proposal.proposal_id,
                success=False,
                improvement_achieved={},
                side_effects=[],
                rollback_available=False,
                message="Validation failed"
            )
        
        # Deploy
        return await self.deploy_evolution(proposal)


def quick_start(config: Optional[Dict[str, Any]] = None) -> ComprehensiveEvolutionOrchestrator:
    """Quick start function for easy initialization"""
    
    evolution_config = EvolutionConfig()
    
    if config:
        for key, value in config.items():
            if hasattr(evolution_config, key):
                setattr(evolution_config, key, value)
    
    orchestrator = ComprehensiveEvolutionOrchestrator(evolution_config)
    
    logger.info("Quick start: Comprehensive Evolution Orchestrator ready")
    logger.info("=" * 80)
    logger.info("WHAT AI CAN EVOLVE:")
    logger.info("- Strategy parameters, combinations, weights")
    logger.info("- ML models, hyperparameters, features")
    logger.info("- Data processing, cleaning, transformations")
    logger.info("- Execution routing, timing, optimization")
    logger.info("- Analysis methods, patterns, regimes")
    logger.info("=" * 80)
    logger.info("WHAT AI CANNOT EVOLVE:")
    logger.info("- Risk limits (max 2% per trade, 5% daily, 20% drawdown)")
    logger.info("- Safety systems (emergency stop, circuit breakers)")
    logger.info("- Governance rules (human approval, audit requirements)")
    logger.info("- Evolution boundaries themselves")
    logger.info("=" * 80)
    logger.info(f"Boundary integrity: {verify_boundary_integrity()}")
    logger.info("=" * 80)
    
    return orchestrator
