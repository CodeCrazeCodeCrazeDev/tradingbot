"""
Recursive Self-Improvement Engine (RSIE) Core

The foundational system that enables recursive self-improvement across all dimensions.
Each improvement cycle learns from previous cycles and generates better improvements.
"""

import asyncio
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Any, Optional, Tuple, Protocol
import json
from pathlib import Path

logger = logging.getLogger(__name__)

class ImprovementTier(Enum):
    TIER_0 = 0  # Critical to profitability
    TIER_1 = 1  # Critical to intelligence
    TIER_2 = 2  # Critical to scalability
    TIER_3 = 3  # Experimental research

class ImprovementDimension(Enum):
    """Dimensions where recursive improvement can occur"""
    STRATEGY = "strategy"
    RISK_MANAGEMENT = "risk_management"
    EXECUTION = "execution"
    LEARNING = "learning"
    ARCHITECTURE = "architecture"
    DATA_PROCESSING = "data_processing"
    SIGNAL_GENERATION = "signal_generation"
    PERFORMANCE = "performance"
    INTEGRATION = "integration"
    META_IMPROVEMENT = "meta_improvement"
    EVALUATION = "evaluation"
    FEATURE = "feature"
    AGENT = "agent"
    WORKFLOW = "workflow"
    WORLD_MODEL = "world_model"

@dataclass
class ImprovementProposal:
    """Proposal for a specific improvement"""
    proposal_id: str
    dimension: ImprovementDimension
    level: int  # 0-7
    description: str
    proposed_changes: Dict[str, Any]
    reasoning: str
    expected_benefit: Dict[str, float]
    risk_analysis: Dict[str, Any]
    rollback_plan: str
    status: str = "PENDING"
    created_at: datetime = field(default_factory=datetime.utcnow)
    validation_results: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ImprovementCapability:
    """Definition of a self-improvable subsystem"""
    subsystem: str
    dimension: ImprovementDimension
    tier: ImprovementTier
    max_level: int
    required_validation: List[str]
    owner_loop: str

class ImprovementRegistry:
    """Registry of all self-improvable subsystems"""

    def __init__(self):
        self.capabilities: Dict[str, ImprovementCapability] = {}
        self._register_defaults()

    def _register_defaults(self):
        """Register the baseline capabilities from the subsystem map"""
        defaults = [
            ImprovementCapability("Validation Reliability", ImprovementDimension.EVALUATION, ImprovementTier.TIER_0, 5, ["Leakage Check", "Walk-Forward"], "EvaluationLoop"),
            ImprovementCapability("Trading Strategies", ImprovementDimension.STRATEGY, ImprovementTier.TIER_0, 5, ["OOS", "Sharpe", "MaxDD"], "StrategyLoop"),
            ImprovementCapability("Risk Management", ImprovementDimension.RISK_MANAGEMENT, ImprovementTier.TIER_0, 4, ["Robustness", "Drawdown", "VaR"], "RiskLoop"),
            ImprovementCapability("Feature Engineering", ImprovementDimension.FEATURE, ImprovementTier.TIER_0, 5, ["Stat Significance", "Stability"], "FeatureLoop"),
            ImprovementCapability("Agent Coordination", ImprovementDimension.AGENT, ImprovementTier.TIER_1, 4, ["Latency", "Accuracy"], "AgentLoop"),
            ImprovementCapability("Workflow Policies", ImprovementDimension.WORKFLOW, ImprovementTier.TIER_1, 3, ["Process Efficiency"], "WorkflowLoop"),
            ImprovementCapability("Model Architecture", ImprovementDimension.ARCHITECTURE, ImprovementTier.TIER_1, 6, ["Loss", "Accuracy"], "ModelLoop"),
            ImprovementCapability("World Model", ImprovementDimension.WORLD_MODEL, ImprovementTier.TIER_2, 5, ["Predictive Error"], "ResearchLoop"),
            ImprovementCapability("Discovery Mechanism", ImprovementDimension.META_IMPROVEMENT, ImprovementTier.TIER_1, 4, ["Meta-Hypothesis Success"], "MetaLoop"),
        ]
        for cap in defaults:
            self.capabilities[cap.subsystem] = cap

    def get_capability(self, subsystem: str) -> Optional[ImprovementCapability]:
        return self.capabilities.get(subsystem)

    def list_by_tier(self, tier: ImprovementTier) -> List[ImprovementCapability]:
        return [c for c in self.capabilities.values() if c.tier == tier]

class ImprovementMemoryInterface(Protocol):
    """Protocol for storing and retrieving improvement data"""
    async def store_proposal(self, proposal: ImprovementProposal): ...
    async def get_proposal(self, proposal_id: str) -> Optional[ImprovementProposal]: ...
    async def store_result(self, proposal_id: str, results: Dict[str, Any]): ...
    async def get_successful_patterns(self, dimension: ImprovementDimension) -> List[Dict[str, Any]]: ...

class KnowledgeGraphInterface(Protocol):
    """Protocol for interacting with the system knowledge graph"""
    async def store_insight(self, source: str, insight: Dict[str, Any]): ...
    async def query_insights(self, query: str) -> List[Dict[str, Any]]: ...

@dataclass
class ImprovementMetrics:
    """Metrics tracking improvement effectiveness"""
    dimension: ImprovementDimension
    cycle_number: int
    timestamp: datetime
    performance_before: float
    performance_after: float
    improvement_delta: float
    convergence_score: float
    stability_score: float
    generalization_score: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def is_successful(self) -> bool:
        """Check if improvement was successful"""
        return self.improvement_delta > 0 and self.stability_score > 0.7
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'dimension': self.dimension.value,
            'cycle_number': self.cycle_number,
            'timestamp': self.timestamp.isoformat(),
            'performance_before': self.performance_before,
            'performance_after': self.performance_after,
            'improvement_delta': self.improvement_delta,
            'convergence_score': self.convergence_score,
            'stability_score': self.stability_score,
            'generalization_score': self.generalization_score,
            'metadata': self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ImprovementProposal':
        """Reconstruct proposal from dictionary"""
        return ImprovementProposal(
            proposal_id=data['proposal_id'],
            dimension=ImprovementDimension(data['dimension']),
            level=data['level'],
            description=data['description'],
            proposed_changes=data['proposed_changes'],
            reasoning=data.get('reasoning', ''),
            expected_benefit=data.get('expected_benefit', {}),
            risk_analysis=data.get('risk_analysis', {}),
            rollback_plan=data.get('rollback_plan', ''),
            status=data.get('status', 'PENDING'),
            created_at=datetime.fromisoformat(data['submitted_at']) if 'submitted_at' in data else datetime.utcnow(),
            validation_results=data.get('metrics', {}),
            metadata=data.get('metadata', {})
        )

@dataclass
class ImprovementCycle:
    """Represents one cycle of recursive improvement"""
    cycle_id: str
    dimension: ImprovementDimension
    depth: int
    parent_cycle_id: Optional[str]
    start_time: datetime
    end_time: Optional[datetime] = None
    metrics: Optional[ImprovementMetrics] = None
    improvements_applied: List[str] = field(default_factory=list)
    child_cycles: List[str] = field(default_factory=list)
    status: str = "running"
    
    def complete(self, metrics: ImprovementMetrics):
        """Mark cycle as complete"""
        self.end_time = datetime.utcnow()
        self.metrics = metrics
        self.status = "completed"
    
    def fail(self, reason: str):
        """Mark cycle as failed"""
        self.end_time = datetime.utcnow()
        self.status = f"failed: {reason}"

class RecursiveImprovementCore:
    """
    Core recursive self-improvement engine.
    
    Implements recursive improvement where:
    1. Each improvement cycle analyzes current performance
    2. Generates improvements based on learned patterns
    3. Applies improvements and measures results
    4. Uses results to improve the improvement process itself (meta-recursion)
    5. Spawns child cycles for deeper optimization
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.max_recursion_depth = self.config.get('max_recursion_depth', 5)
        self.convergence_threshold = self.config.get('convergence_threshold', 0.01)
        self.min_improvement_delta = self.config.get('min_improvement_delta', 0.001)
        
        self.registry = ImprovementRegistry()
        self.cycles: Dict[str, ImprovementCycle] = {}
        self.metrics_history: List[ImprovementMetrics] = []
        self.improvement_patterns: Dict[ImprovementDimension, List[Dict]] = {}
        self.meta_learnings: List[Dict[str, Any]] = []
        
        self.storage_path = Path(self.config.get('storage_path', 'recursive_improvement_data'))
        self.storage_path.mkdir(exist_ok=True)
        
        self._initialize_improvement_patterns()
        logger.info("RecursiveImprovementCore initialized with RSIE Architecture")
    
    def _initialize_improvement_patterns(self):
        """Initialize improvement patterns for each dimension"""
        for dimension in ImprovementDimension:
            self.improvement_patterns[dimension] = []
    
    async def start_improvement_cycle(
        self,
        dimension: ImprovementDimension,
        depth: int = 0,
        parent_cycle_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Start a new improvement cycle.
        """
        if depth >= self.max_recursion_depth:
            logger.warning(f"Max recursion depth {self.max_recursion_depth} reached")
            return None
        
        cycle_id = f"{dimension.value}_{depth}_{datetime.utcnow().timestamp()}"
        cycle = ImprovementCycle(
            cycle_id=cycle_id,
            dimension=dimension,
            depth=depth,
            parent_cycle_id=parent_cycle_id,
            start_time=datetime.utcnow()
        )
        
        self.cycles[cycle_id] = cycle
        
        if parent_cycle_id and parent_cycle_id in self.cycles:
            self.cycles[parent_cycle_id].child_cycles.append(cycle_id)
        
        logger.info(f"Started improvement cycle {cycle_id} at depth {depth}")
        
        return cycle_id
    
    def get_improvement_summary(self) -> Dict[str, Any]:
        """Get summary of all improvements"""
        return {
            'total_cycles': len(self.cycles),
            'successful_cycles': sum(1 for c in self.cycles.values() 
                                    if c.status == "completed" and 
                                    c.metrics and c.metrics.is_successful()),
            'dimensions_improved': list(set(c.dimension for c in self.cycles.values())),
            'total_improvement': sum(m.improvement_delta for m in self.metrics_history),
            'meta_learnings_count': len(self.meta_learnings),
            'current_recursion_depth': self.max_recursion_depth,
        }

    def save_state(self):
        """Save improvement state to disk"""
        state = {
            'cycles': {k: {
                'cycle_id': v.cycle_id,
                'dimension': v.dimension.value,
                'depth': v.depth,
                'status': v.status,
                'improvements_applied': v.improvements_applied,
            } for k, v in self.cycles.items()},
            'metrics_history': [m.to_dict() for m in self.metrics_history],
            'meta_learnings': self.meta_learnings,
        }
        
        state_file = self.storage_path / 'recursive_improvement_state.json'
        with open(state_file, 'w') as f:
            json.dump(state, f, indent=2)
        
        logger.info(f"Saved state to {state_file}")

    def load_state(self):
        """Load improvement state from disk with robust error handling (Day 1 Guard)."""
        state_file = self.storage_path / 'recursive_improvement_state.json'
        if not state_file.exists():
            logger.info("No previous state found. Initializing new state.")
            return
        
        try:
            with open(state_file, 'r') as f:
                state = json.load(f)

            self.meta_learnings = state.get('meta_learnings', [])

            # Restore cycles (limited to prevent memory bloat)
            cycle_data = state.get('cycles', {})
            for k, v in list(cycle_data.items())[-100:]:  # Keep last 100 cycles in memory
                self.cycles[k] = ImprovementCycle(
                    cycle_id=v['cycle_id'],
                    dimension=ImprovementDimension(v['dimension']),
                    depth=v['depth'],
                    parent_cycle_id=v.get('parent_cycle_id'),
                    start_time=datetime.fromisoformat(v['start_time']) if 'start_time' in v else datetime.utcnow(),
                    status=v['status'],
                    improvements_applied=v['improvements_applied']
                )

            logger.info(f"Loaded state from {state_file} (Restored {len(self.cycles)} recent cycles)")
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.error(f"Failed to load state file {state_file}: {e}. Creating backup and starting fresh.")
            if state_file.exists():
                state_file.rename(state_file.with_suffix('.json.bak'))
