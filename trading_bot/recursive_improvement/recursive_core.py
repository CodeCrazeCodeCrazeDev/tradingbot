"""
Recursive Self-Improvement Core

The foundational system that enables recursive self-improvement across all dimensions.
Each improvement cycle learns from previous cycles and generates better improvements.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Any, Optional, Callable
import json
from pathlib import Path

logger = logging.getLogger(__name__)


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
        
        self.cycles: Dict[str, ImprovementCycle] = {}
        self.metrics_history: List[ImprovementMetrics] = []
        self.improvement_patterns: Dict[ImprovementDimension, List[Dict]] = {}
        self.meta_learnings: List[Dict[str, Any]] = []
        
        self.storage_path = Path(self.config.get('storage_path', 'recursive_improvement_data'))
        self.storage_path.mkdir(exist_ok=True)
        
        self._initialize_improvement_patterns()
        logger.info("RecursiveImprovementCore initialized")
    
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
        
        Args:
            dimension: Which dimension to improve
            depth: Current recursion depth
            parent_cycle_id: ID of parent cycle if this is a recursive call
            context: Additional context for improvement
            
        Returns:
            Cycle ID
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
        
        try:
            await self._execute_improvement_cycle(cycle, context or {})
        except Exception as e:
            logger.error(f"Improvement cycle {cycle_id} failed: {e}")
            cycle.fail(str(e))
        
        return cycle_id
    
    async def _execute_improvement_cycle(
        self,
        cycle: ImprovementCycle,
        context: Dict[str, Any]
    ):
        """Execute one improvement cycle"""
        
        # Step 1: Analyze current performance
        performance_before = await self._measure_performance(cycle.dimension, context)
        
        # Step 2: Learn from historical patterns
        patterns = self._learn_from_history(cycle.dimension)
        
        # Step 3: Generate improvements using learned patterns
        improvements = await self._generate_improvements(
            cycle.dimension,
            patterns,
            context
        )
        
        # Step 4: Apply improvements
        applied_improvements = await self._apply_improvements(
            cycle.dimension,
            improvements,
            context
        )
        cycle.improvements_applied = applied_improvements
        
        # Step 5: Measure new performance
        performance_after = await self._measure_performance(cycle.dimension, context)
        
        # Step 6: Calculate metrics
        metrics = ImprovementMetrics(
            dimension=cycle.dimension,
            cycle_number=len([c for c in self.cycles.values() 
                            if c.dimension == cycle.dimension]),
            timestamp=datetime.utcnow(),
            performance_before=performance_before,
            performance_after=performance_after,
            improvement_delta=performance_after - performance_before,
            convergence_score=self._calculate_convergence(cycle.dimension),
            stability_score=self._calculate_stability(cycle.dimension),
            generalization_score=self._calculate_generalization(cycle.dimension),
            metadata=context
        )
        
        cycle.complete(metrics)
        self.metrics_history.append(metrics)
        
        # Step 7: Store successful patterns
        if metrics.is_successful():
            self._store_improvement_pattern(cycle.dimension, {
                'improvements': applied_improvements,
                'delta': metrics.improvement_delta,
                'context': context,
                'timestamp': datetime.utcnow().isoformat()
            })
        
        # Step 8: Decide if we should recurse deeper
        if await self._should_recurse(cycle, metrics):
            await self._spawn_child_cycles(cycle, context)
        
        # Step 9: Meta-learning - improve the improvement process
        await self._meta_improve(cycle, metrics)
        
        logger.info(f"Cycle {cycle.cycle_id} completed with delta {metrics.improvement_delta}")
    
    async def _measure_performance(
        self,
        dimension: ImprovementDimension,
        context: Dict[str, Any]
    ) -> float:
        """Measure current performance for a dimension"""
        # This would integrate with actual performance measurement systems
        # For now, return a placeholder
        return context.get('current_performance', 0.5)
    
    def _learn_from_history(
        self,
        dimension: ImprovementDimension
    ) -> List[Dict]:
        """Learn patterns from historical improvements"""
        patterns = self.improvement_patterns.get(dimension, [])
        
        # Sort by effectiveness
        sorted_patterns = sorted(
            patterns,
            key=lambda p: p.get('delta', 0),
            reverse=True
        )
        
        return sorted_patterns[:10]  # Top 10 patterns
    
    async def _generate_improvements(
        self,
        dimension: ImprovementDimension,
        patterns: List[Dict],
        context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate improvements based on learned patterns"""
        improvements = []
        
        # Use historical patterns to generate new improvements
        for pattern in patterns:
            # Adapt pattern to current context
            adapted = self._adapt_pattern_to_context(pattern, context)
            if adapted:
                improvements.append(adapted)
        
        # Generate novel improvements
        novel = await self._generate_novel_improvements(dimension, context)
        improvements.extend(novel)
        
        return improvements
    
    def _adapt_pattern_to_context(
        self,
        pattern: Dict,
        context: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Adapt a historical pattern to current context"""
        # Simple adaptation - in production this would be more sophisticated
        return {
            'type': 'adapted_pattern',
            'original_pattern': pattern,
            'context': context,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    async def _generate_novel_improvements(
        self,
        dimension: ImprovementDimension,
        context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate novel improvements through exploration"""
        # This would use ML/optimization to generate new improvements
        return [
            {
                'type': 'novel_improvement',
                'dimension': dimension.value,
                'context': context,
                'timestamp': datetime.utcnow().isoformat()
            }
        ]
    
    async def _apply_improvements(
        self,
        dimension: ImprovementDimension,
        improvements: List[Dict[str, Any]],
        context: Dict[str, Any]
    ) -> List[str]:
        """Apply improvements and return list of what was applied"""
        applied = []
        
        for improvement in improvements:
            try:
                # Apply improvement (would integrate with actual systems)
                improvement_id = f"{dimension.value}_{len(applied)}"
                applied.append(improvement_id)
                logger.info(f"Applied improvement {improvement_id}")
            except Exception as e:
                logger.error(f"Failed to apply improvement: {e}")
        
        return applied
    
    def _calculate_convergence(self, dimension: ImprovementDimension) -> float:
        """Calculate convergence score (how close to optimal)"""
        recent_metrics = [m for m in self.metrics_history[-10:] 
                         if m.dimension == dimension]
        
        if len(recent_metrics) < 2:
            return 0.0
        
        # Check if improvements are getting smaller (converging)
        deltas = [m.improvement_delta for m in recent_metrics]
        if all(abs(d) < self.convergence_threshold for d in deltas[-3:]):
            return 1.0
        
        return 0.5
    
    def _calculate_stability(self, dimension: ImprovementDimension) -> float:
        """Calculate stability score (consistency of improvements)"""
        recent_metrics = [m for m in self.metrics_history[-10:] 
                         if m.dimension == dimension]
        
        if len(recent_metrics) < 2:
            return 0.5
        
        # Check variance in improvements
        deltas = [m.improvement_delta for m in recent_metrics]
        variance = sum((d - sum(deltas)/len(deltas))**2 for d in deltas) / len(deltas)
        
        # Lower variance = higher stability
        return max(0.0, 1.0 - variance)
    
    def _calculate_generalization(self, dimension: ImprovementDimension) -> float:
        """Calculate generalization score (works across contexts)"""
        # Would measure performance across different market conditions
        return 0.7  # Placeholder
    
    def _store_improvement_pattern(
        self,
        dimension: ImprovementDimension,
        pattern: Dict[str, Any]
    ):
        """Store a successful improvement pattern"""
        if dimension not in self.improvement_patterns:
            self.improvement_patterns[dimension] = []
        
        self.improvement_patterns[dimension].append(pattern)
        
        # Keep only top 100 patterns
        self.improvement_patterns[dimension] = sorted(
            self.improvement_patterns[dimension],
            key=lambda p: p.get('delta', 0),
            reverse=True
        )[:100]
    
    async def _should_recurse(
        self,
        cycle: ImprovementCycle,
        metrics: ImprovementMetrics
    ) -> bool:
        """Decide if we should spawn child cycles for deeper optimization"""
        # Recurse if:
        # 1. We haven't hit max depth
        # 2. Improvement was successful
        # 3. Haven't converged yet
        return (
            cycle.depth < self.max_recursion_depth - 1 and
            metrics.is_successful() and
            metrics.convergence_score < 0.9
        )
    
    async def _spawn_child_cycles(
        self,
        parent_cycle: ImprovementCycle,
        context: Dict[str, Any]
    ):
        """Spawn child improvement cycles for deeper optimization"""
        # Spawn cycles for related dimensions
        related_dimensions = self._get_related_dimensions(parent_cycle.dimension)
        
        tasks = []
        for dimension in related_dimensions:
            task = self.start_improvement_cycle(
                dimension=dimension,
                depth=parent_cycle.depth + 1,
                parent_cycle_id=parent_cycle.cycle_id,
                context=context
            )
            tasks.append(task)
        
        if tasks:
            await asyncio.gather(*tasks)
    
    def _get_related_dimensions(
        self,
        dimension: ImprovementDimension
    ) -> List[ImprovementDimension]:
        """Get dimensions related to the given dimension"""
        relations = {
            ImprovementDimension.STRATEGY: [
                ImprovementDimension.SIGNAL_GENERATION,
                ImprovementDimension.RISK_MANAGEMENT
            ],
            ImprovementDimension.EXECUTION: [
                ImprovementDimension.PERFORMANCE,
                ImprovementDimension.RISK_MANAGEMENT
            ],
            ImprovementDimension.LEARNING: [
                ImprovementDimension.META_IMPROVEMENT,
                ImprovementDimension.STRATEGY
            ],
        }
        
        return relations.get(dimension, [])
    
    async def _meta_improve(
        self,
        cycle: ImprovementCycle,
        metrics: ImprovementMetrics
    ):
        """
        Meta-improvement: Improve the improvement process itself.
        
        This is the recursive part - we analyze how well the improvement
        process worked and improve it.
        """
        meta_learning = {
            'cycle_id': cycle.cycle_id,
            'dimension': cycle.dimension.value,
            'depth': cycle.depth,
            'success': metrics.is_successful(),
            'improvement_delta': metrics.improvement_delta,
            'timestamp': datetime.utcnow().isoformat(),
            'insights': []
        }
        
        # Analyze what worked and what didn't
        if metrics.is_successful():
            meta_learning['insights'].append({
                'type': 'success_pattern',
                'pattern': 'improvements_applied',
                'value': cycle.improvements_applied
            })
        else:
            meta_learning['insights'].append({
                'type': 'failure_pattern',
                'reason': 'low_improvement_delta',
                'value': metrics.improvement_delta
            })
        
        self.meta_learnings.append(meta_learning)
        
        # Use meta-learnings to adjust improvement parameters
        await self._adjust_improvement_parameters()
    
    async def _adjust_improvement_parameters(self):
        """Adjust improvement parameters based on meta-learnings"""
        if len(self.meta_learnings) < 10:
            return
        
        recent_learnings = self.meta_learnings[-10:]
        success_rate = sum(1 for l in recent_learnings if l['success']) / len(recent_learnings)
        
        # Adjust recursion depth based on success rate
        if success_rate > 0.8:
            self.max_recursion_depth = min(10, self.max_recursion_depth + 1)
        elif success_rate < 0.3:
            self.max_recursion_depth = max(2, self.max_recursion_depth - 1)
        
        logger.info(f"Adjusted max_recursion_depth to {self.max_recursion_depth}")
    
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
            'improvement_patterns': {
                k.value: v for k, v in self.improvement_patterns.items()
            },
            'meta_learnings': self.meta_learnings,
        }
        
        state_file = self.storage_path / 'recursive_improvement_state.json'
        with open(state_file, 'w') as f:
            json.dump(state, f, indent=2)
        
        logger.info(f"Saved state to {state_file}")
    
    def load_state(self):
        """Load improvement state from disk"""
        state_file = self.storage_path / 'recursive_improvement_state.json'
        if not state_file.exists():
            return
        
        with open(state_file, 'r') as f:
            state = json.load(f)
        
        self.meta_learnings = state.get('meta_learnings', [])
        
        logger.info(f"Loaded state from {state_file}")
