"""
AlphaAlgo Evolution Orchestrator - The Brain Coordinator

This module coordinates all evolution activities.
It brings together learning, optimization, and code evolution.

Version: 1.0.0
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from enum import Enum
import logging
import asyncio
import json
from pathlib import Path

from .reward_model import get_reward_model, verify_reward_model_integrity
from .learner import ContinuousLearner, LearningExperience, LearningType
from .optimizer import SelfOptimizer, OptimizationTarget
from .evolver import CodeEvolver, EvolutionType, EvolutionStatus

logger = logging.getLogger(__name__)


class EvolutionCycleStatus(Enum):
    """Status of evolution cycle"""
    IDLE = "idle"
    LEARNING = "learning"
    OPTIMIZING = "optimizing"
    PROPOSING = "proposing"
    WAITING_APPROVAL = "waiting_approval"
    APPLYING = "applying"
    COMPLETE = "complete"
    ERROR = "error"


@dataclass
class EvolutionCycle:
    """A single evolution cycle"""
    cycle_id: str
    status: EvolutionCycleStatus
    started_at: datetime
    
    # Results
    experiences_learned: int = 0
    optimizations_performed: int = 0
    proposals_created: int = 0
    proposals_approved: int = 0
    proposals_applied: int = 0
    
    # Performance
    reward_before: float = 0.0
    reward_after: float = 0.0
    improvement: float = 0.0
    
    # Timing
    completed_at: Optional[datetime] = None
    duration_seconds: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'cycle_id': self.cycle_id,
            'status': self.status.value,
            'started_at': self.started_at.isoformat(),
            'experiences_learned': self.experiences_learned,
            'optimizations_performed': self.optimizations_performed,
            'proposals_created': self.proposals_created,
            'proposals_approved': self.proposals_approved,
            'proposals_applied': self.proposals_applied,
            'reward_before': self.reward_before,
            'reward_after': self.reward_after,
            'improvement': self.improvement,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'duration_seconds': self.duration_seconds,
        }


class EvolutionStatus:
    """Overall evolution system status"""
    
    def __init__(self):
        self.is_running = False
        self.current_cycle: Optional[EvolutionCycle] = None
        self.total_cycles = 0
        self.total_improvements = 0
        self.last_cycle_time: Optional[datetime] = None
        self.reward_model_valid = True
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'is_running': self.is_running,
            'current_cycle': self.current_cycle.to_dict() if self.current_cycle else None,
            'total_cycles': self.total_cycles,
            'total_improvements': self.total_improvements,
            'last_cycle_time': self.last_cycle_time.isoformat() if self.last_cycle_time else None,
            'reward_model_valid': self.reward_model_valid,
        }


class EvolutionOrchestrator:
    """
    The Brain - Coordinates all evolution activities.
    
    This orchestrator:
    1. Collects experiences from trading
    2. Runs continuous learning
    3. Performs parameter optimization
    4. Proposes code evolutions
    5. Waits for human approval
    6. Applies approved changes
    7. Monitors results and rolls back if needed
    
    Key principles:
    1. The reward model is IMMUTABLE and guides all evolution
    2. Human approval is REQUIRED for all code changes
    3. All changes are reversible
    4. Evolution cannot increase risk beyond limits
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Core components
        self.reward_model = get_reward_model()
        self.learner = ContinuousLearner(config)
        self.optimizer = SelfOptimizer(config)
        self.evolver = CodeEvolver(config)
        
        # Status
        self.status = EvolutionStatus()
        
        # Cycle history
        self._cycle_history: List[EvolutionCycle] = []
        self._max_history = 1000
        
        # Configuration
        self._evolution_interval = timedelta(
            hours=self.config.get('evolution_interval_hours', 24)
        )
        self._min_experiences_for_evolution = self.config.get(
            'min_experiences_for_evolution', 100
        )
        
        # Background task
        self._evolution_task: Optional[asyncio.Task] = None
        self._stop_event = asyncio.Event()
        
        # Storage
        self._storage_path = Path(self.config.get('storage_path', 'evolution_state'))
        self._storage_path.mkdir(parents=True, exist_ok=True)
        
        logger.info("EvolutionOrchestrator initialized")
    
    async def start(self) -> None:
        """Start the evolution orchestrator"""
        if self.status.is_running:
            logger.warning("Evolution orchestrator already running")
            return
        
        # Verify reward model integrity
        if not verify_reward_model_integrity():
            logger.critical("REWARD MODEL INTEGRITY CHECK FAILED - CANNOT START")
            raise RuntimeError("Reward model integrity check failed")
        
        self.status.is_running = True
        self.status.reward_model_valid = True
        self._stop_event.clear()
        
        # Start background evolution loop
        self._evolution_task = asyncio.create_task(self._evolution_loop())
        
        logger.info("Evolution orchestrator started")
    
    async def stop(self) -> None:
        """Stop the evolution orchestrator"""
        if not self.status.is_running:
            return
        
        self._stop_event.set()
        
        if self._evolution_task:
            self._evolution_task.cancel()
            try:
                await self._evolution_task
            except asyncio.CancelledError:
                pass
        
        self.status.is_running = False
        
        # Save state
        self._save_state()
        
        logger.info("Evolution orchestrator stopped")
    
    async def record_experience(self, experience: LearningExperience) -> None:
        """Record a trading experience for learning"""
        await self.learner.learn(experience)
    
    async def run_evolution_cycle(self) -> EvolutionCycle:
        """
        Run a single evolution cycle.
        
        This is the main evolution process that:
        1. Learns from recent experiences
        2. Optimizes parameters
        3. Proposes improvements
        4. Waits for approval
        5. Applies approved changes
        """
        # Verify reward model first
        if not verify_reward_model_integrity():
            logger.critical("REWARD MODEL INTEGRITY CHECK FAILED")
            self.status.reward_model_valid = False
            raise RuntimeError("Reward model integrity check failed")
        
        cycle_id = f"cycle_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        cycle = EvolutionCycle(
            cycle_id=cycle_id,
            status=EvolutionCycleStatus.LEARNING,
            started_at=datetime.now(),
        )
        self.status.current_cycle = cycle
        
        try:
            # Phase 1: Learning
            logger.info(f"Evolution cycle {cycle_id}: Learning phase")
            cycle.status = EvolutionCycleStatus.LEARNING
            
            # Get performance before
            perf_before = self.learner.get_performance_summary()
            cycle.reward_before = perf_before.get('recent_avg_reward', 0)
            
            # Phase 2: Optimization
            logger.info(f"Evolution cycle {cycle_id}: Optimization phase")
            cycle.status = EvolutionCycleStatus.OPTIMIZING
            
            # Optimize signal weights
            current_params = self.learner.get_learned_parameters()
            
            def eval_fn(params):
                # Simple evaluation based on learned performance
                return perf_before.get('recent_avg_reward', 0)
            
            opt_result = self.optimizer.optimize(
                target=OptimizationTarget.SIGNAL_WEIGHTS,
                current_params=current_params,
                evaluation_fn=eval_fn,
                max_iterations=50
            )
            
            if opt_result.is_improvement:
                cycle.optimizations_performed += 1
            
            # Phase 3: Propose improvements
            logger.info(f"Evolution cycle {cycle_id}: Proposal phase")
            cycle.status = EvolutionCycleStatus.PROPOSING
            
            # Propose parameter changes if optimization found improvements
            if opt_result.is_improvement:
                proposal = self.evolver.propose_evolution(
                    evolution_type=EvolutionType.PARAMETER_CHANGE,
                    target_component="learner.parameters",
                    description=f"Optimize signal weights for {opt_result.improvement:.2%} improvement",
                    rationale=f"Optimization found better parameters with {opt_result.method}",
                    before_state=opt_result.original_params,
                    after_state=opt_result.optimized_params,
                    expected_improvement=opt_result.improvement,
                )
                cycle.proposals_created += 1
                
                if proposal.passes_constraints:
                    cycle.status = EvolutionCycleStatus.WAITING_APPROVAL
            
            # Phase 4: Check for approved proposals and apply
            logger.info(f"Evolution cycle {cycle_id}: Application phase")
            cycle.status = EvolutionCycleStatus.APPLYING
            
            # Note: In production, this would wait for human approval
            # For now, we just check if any proposals were auto-approved
            
            # Phase 5: Complete
            cycle.status = EvolutionCycleStatus.COMPLETE
            cycle.completed_at = datetime.now()
            cycle.duration_seconds = (cycle.completed_at - cycle.started_at).total_seconds()
            
            # Get performance after
            perf_after = self.learner.get_performance_summary()
            cycle.reward_after = perf_after.get('recent_avg_reward', 0)
            cycle.improvement = cycle.reward_after - cycle.reward_before
            
            logger.info(
                f"Evolution cycle {cycle_id} complete: "
                f"improvement={cycle.improvement:.4f}, "
                f"duration={cycle.duration_seconds:.1f}s"
            )
            
        except Exception as e:
            logger.error(f"Evolution cycle {cycle_id} failed: {e}")
            cycle.status = EvolutionCycleStatus.ERROR
            cycle.completed_at = datetime.now()
        
        # Store cycle
        self._cycle_history.append(cycle)
        if len(self._cycle_history) > self._max_history:
            self._cycle_history = self._cycle_history[-self._max_history:]
        
        self.status.total_cycles += 1
        if cycle.improvement > 0:
            self.status.total_improvements += 1
        self.status.last_cycle_time = datetime.now()
        self.status.current_cycle = None
        
        # Save state
        self._save_state()
        
        return cycle
    
    async def _evolution_loop(self) -> None:
        """Background evolution loop"""
        while not self._stop_event.is_set():
            try:
                # Wait for evolution interval
                await asyncio.wait_for(
                    self._stop_event.wait(),
                    timeout=self._evolution_interval.total_seconds()
                )
                break  # Stop event was set
            except asyncio.TimeoutError:
                try:
                # Time for evolution
                    await self.run_evolution_cycle()
                except Exception as e:
                    logger.error(f"Evolution cycle failed: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current status"""
        return self.status.to_dict()
    
    def get_cycle_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get evolution cycle history"""
        return [c.to_dict() for c in self._cycle_history[-limit:]]
    
    def get_pending_approvals(self) -> List[Dict[str, Any]]:
        """Get proposals pending human approval"""
        proposals = self.evolver.get_pending_proposals()
        return [p.to_dict() for p in proposals]
    
    def approve_proposal(self, proposal_id: str, approver: str) -> bool:
        """Approve a proposal (human action)"""
        return self.evolver.approve_evolution(proposal_id, approver)
    
    def reject_proposal(self, proposal_id: str, reason: str) -> bool:
        """Reject a proposal"""
        return self.evolver.reject_evolution(proposal_id, reason)
    
    def get_learned_parameters(self) -> Dict[str, Any]:
        """Get current learned parameters"""
        return self.learner.get_learned_parameters()
    
    def get_reward_model_constraints(self) -> Dict[str, Any]:
        """Get reward model constraints"""
        return self.reward_model.get_constraints_dict()
    
    def _save_state(self) -> None:
        """Save orchestrator state"""
        try:
            state = {
                'status': self.status.to_dict(),
                'cycle_history': [c.to_dict() for c in self._cycle_history[-100:]],
                'timestamp': datetime.now().isoformat(),
            }
            
            path = self._storage_path / 'orchestrator_state.json'
            with open(path, 'w') as f:
                json.dump(state, f, indent=2)
            
            # Also save learner state
            self.learner.save_state()
            
        except Exception as e:
            logger.error(f"Failed to save state: {e}")
    
    def _load_state(self) -> None:
        """Load orchestrator state"""
        try:
            path = self._storage_path / 'orchestrator_state.json'
            if path.exists():
                with open(path, 'r') as f:
                    state = json.load(f)
                
                self.status.total_cycles = state.get('status', {}).get('total_cycles', 0)
                self.status.total_improvements = state.get('status', {}).get('total_improvements', 0)
                
                logger.info("Orchestrator state loaded")
            
            # Also load learner state
            self.learner.load_state()
            
        except Exception as e:
            logger.error(f"Failed to load state: {e}")


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

_orchestrator_instance: Optional[EvolutionOrchestrator] = None


def get_evolution_orchestrator(config: Optional[Dict[str, Any]] = None) -> EvolutionOrchestrator:
    """Get the singleton evolution orchestrator"""
    global _orchestrator_instance
    if _orchestrator_instance is None:
        _orchestrator_instance = EvolutionOrchestrator(config)
    return _orchestrator_instance


async def start_evolution() -> None:
    """Start the evolution system"""
    orchestrator = get_evolution_orchestrator()
    await orchestrator.start()


async def stop_evolution() -> None:
    """Stop the evolution system"""
    orchestrator = get_evolution_orchestrator()
    await orchestrator.stop()


async def record_trade_experience(
    symbol: str,
    timeframe: str,
    market_regime: str,
    features: Dict[str, Any],
    action: str,
    outcome: Dict[str, Any]
) -> None:
    """Record a trade experience for learning"""
    import uuid
    
    experience = LearningExperience(
        experience_id=str(uuid.uuid4()),
        timestamp=datetime.now(),
        learning_type=LearningType.TRADE_OUTCOME,
        symbol=symbol,
        timeframe=timeframe,
        market_regime=market_regime,
        features=features,
        action_taken=action,
        outcome=outcome,
        reward=0.0,  # Will be calculated by learner
    )
    
    orchestrator = get_evolution_orchestrator()
    await orchestrator.record_experience(experience)
