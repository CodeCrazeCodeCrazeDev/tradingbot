"""
Meta-Learning Loop
==================

Continuously improves the meta-intelligence layer itself.
Updates routing strategies, optimizes extraction, discovers new task categories.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from enum import Enum
import numpy as np
from collections import defaultdict

from .capability_registry import CapabilityRegistry
from .task_router import TaskRouter, RoutingStrategy
from .behavior_synthesis import BehaviorSynthesizer

logger = logging.getLogger(__name__)


class OptimizationTarget(Enum):
    """What aspect of the system to optimize"""
    ROUTING_ACCURACY = "routing_accuracy"
    LATENCY = "latency"
    RELIABILITY = "reliability"
    THROUGHPUT = "throughput"
    GLOBAL_OBJECTIVE = "global_objective"


@dataclass
class LearningCycle:
    """A single meta-learning cycle"""
    cycle_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    improvements_made: List[Dict[str, Any]] = field(default_factory=list)
    discoveries: List[str] = field(default_factory=list)
    performance_delta: float = 0.0
    status: str = "running"  # running, completed, failed


@dataclass
class RoutingOptimization:
    """Optimization for routing strategy"""
    task_category: str
    old_strategy: str
    new_strategy: str
    reason: str
    expected_improvement: float
    confidence: float


@dataclass
class ThresholdAdjustment:
    """Adjustment to decision thresholds"""
    parameter: str
    old_value: float
    new_value: float
    reason: str
    metric_improved: str


class MetaLearningLoop:
    """
    Meta-learning system that improves the meta-intelligence layer.
    
    Responsibilities:
    1. Analyze routing performance and optimize strategy per category
    2. Detect new task categories from traffic patterns
    3. Optimize exploration vs exploitation rates
    4. Adjust deployment thresholds based on market conditions
    5. Discover opportunities for behavior synthesis
    """
    
    def __init__(self, 
                 registry: CapabilityRegistry,
                 router: TaskRouter,
                 synthesizer: BehaviorSynthesizer,
                 global_objective_fn: Optional[Callable[[Dict[str, Any]], float]] = None):
        self.registry = registry
        self.router = router
        self.synthesizer = synthesizer
        self.global_objective_fn = global_objective_fn
        
        # Learning state
        self.cycles: List[LearningCycle] = []
        self.is_running = False
        self.current_cycle: Optional[LearningCycle] = None
        
        # Optimization settings
        self.min_routing_samples = 50
        self.improvement_threshold = 0.05
        self.exploration_decay = 0.99
        
        # Category discovery
        self.known_categories: set = set()
        self.discovered_patterns: Dict[str, int] = defaultdict(int)
        
        logger.info("MetaLearningLoop initialized")
    
    async def run_learning_cycle(self) -> LearningCycle:
        """Run a complete meta-learning cycle"""
        cycle_id = f"ml_cycle_{datetime.utcnow().timestamp()}"
        
        self.current_cycle = LearningCycle(
            cycle_id=cycle_id,
            start_time=datetime.utcnow()
        )
        self.cycles.append(self.current_cycle)
        
        logger.info(f"Starting meta-learning cycle {cycle_id}")
        
        try:
            # 1. Analyze routing performance
            routing_improvements = await self._optimize_routing_strategies()
            self.current_cycle.improvements_made.extend(routing_improvements)
            
            # 2. Discover new task categories
            new_categories = await self._discover_task_categories()
            self.current_cycle.discoveries.extend(new_categories)
            
            # 3. Adjust exploration rates
            exploration_adjustment = await self._adjust_exploration_rates()
            if exploration_adjustment:
                self.current_cycle.improvements_made.append(exploration_adjustment)
            
            # 4. Identify synthesis opportunities
            synthesis_opportunities = await self._find_synthesis_opportunities()
            for opp in synthesis_opportunities:
                self.current_cycle.discoveries.append(f"Synthesis opportunity: {opp}")
            
            # 5. Optimize deployment thresholds
            threshold_adjustments = await self._optimize_thresholds()
            self.current_cycle.improvements_made.extend(threshold_adjustments)
            
            # 6. Calculate overall improvement
            self.current_cycle.performance_delta = await self._calculate_performance_delta()
            
            self.current_cycle.end_time = datetime.utcnow()
            self.current_cycle.status = "completed"
            
            logger.info(f"Completed meta-learning cycle {cycle_id} with "
                       f"{len(self.current_cycle.improvements_made)} improvements")
            
        except Exception as e:
            logger.error(f"Error in meta-learning cycle {cycle_id}: {e}")
            self.current_cycle.status = "failed"
            self.current_cycle.end_time = datetime.utcnow()
        
        return self.current_cycle
    
    async def _optimize_routing_strategies(self) -> List[Dict[str, Any]]:
        """Analyze and optimize routing strategies per category"""
        improvements = []
        
        # Get routing history
        routing_history = self.registry.get_routing_history(limit=1000)
        
        if len(routing_history) < self.min_routing_samples:
            logger.info("Insufficient routing history for optimization")
            return improvements
        
        # Group by category
        by_category = defaultdict(list)
        for decision in routing_history:
            if decision.task_category:
                by_category[decision.task_category].append(decision)
        
        # Analyze each category
        for category, decisions in by_category.items():
            if len(decisions) < 20:
                continue
            
            # Calculate success rate for current strategy
            success_rate = sum(1 for d in decisions if d.success) / len(decisions)
            avg_confidence = np.mean([d.confidence for d in decisions])
            avg_latency = np.mean([d.latency_ms for d in decisions])
            
            # Determine if strategy change would help
            current_strategy = self._infer_current_strategy(decisions)
            
            recommendation = self._recommend_strategy(
                category, success_rate, avg_confidence, avg_latency, len(decisions)
            )
            
            if recommendation and recommendation != current_strategy:
                # Record the optimization
                optimization = {
                    'type': 'routing_strategy',
                    'task_category': category,
                    'old_strategy': current_strategy,
                    'new_strategy': recommendation,
                    'reason': self._get_strategy_reason(success_rate, avg_confidence),
                    'expected_improvement': self._estimate_improvement(
                        current_strategy, recommendation, success_rate
                    )
                }
                improvements.append(optimization)
                
                logger.info(f"Routing optimization for {category}: "
                           f"{current_strategy} -> {recommendation}")
        
        return improvements
    
    def _infer_current_strategy(self, decisions: List[Any]) -> str:
        """Infer current routing strategy from decisions"""
        # Check exploration rate from variance in selections
        capabilities_used = set()
        for d in decisions:
            if d.selected_capability:
                capabilities_used.add(d.selected_capability)
        
        # High variety suggests exploration
        if len(capabilities_used) > len(decisions) * 0.3:
            return "epsilon_greedy"
        
        return "greedy"
    
    def _recommend_strategy(self, category: str, success_rate: float, 
                           confidence: float, latency: float, 
                           sample_count: int) -> Optional[str]:
        """Recommend a routing strategy based on metrics"""
        
        # High success with low confidence suggests UCB would help
        if success_rate > 0.7 and confidence < 0.6 and sample_count > 50:
            return "ucb"
        
        # Low success with any sample size - increase exploration
        if success_rate < 0.5:
            return "epsilon_greedy"
        
        # Very high success - can be more greedy
        if success_rate > 0.9 and sample_count > 100:
            return "greedy"
        
        return None
    
    def _get_strategy_reason(self, success_rate: float, confidence: float) -> str:
        """Generate reason for strategy recommendation"""
        if success_rate > 0.7 and confidence < 0.6:
            return "High success but low confidence suggests need for better uncertainty handling"
        elif success_rate < 0.5:
            return "Low success rate suggests need for more exploration"
        elif success_rate > 0.9:
            return "Consistent high success allows for greedy optimization"
        return "Balanced performance"
    
    def _estimate_improvement(self, old_strategy: str, new_strategy: str, 
                             current_success: float) -> float:
        """Estimate improvement from strategy change"""
        # Rough estimates based on typical performance
        strategy_potential = {
            'greedy': 0.85,
            'epsilon_greedy': 0.80,
            'ucb': 0.88,
            'similarity': 0.82
        }
        
        old_potential = strategy_potential.get(old_strategy, 0.75)
        new_potential = strategy_potential.get(new_strategy, 0.75)
        
        # Estimate improvement as fraction of gap to potential
        gap = new_potential - current_success
        return gap * 0.5  # Conservative estimate
    
    async def _discover_task_categories(self) -> List[str]:
        """Discover new task categories from traffic patterns"""
        discoveries = []
        
        # Get recent routing decisions
        recent = self.registry.get_routing_history(limit=500)
        
        # Extract unique categories
        seen_categories = set()
        for decision in recent:
            if decision.task_category:
                seen_categories.add(decision.task_category)
        
        # Check for new categories
        for category in seen_categories:
            if category not in self.known_categories:
                self.known_categories.add(category)
                discoveries.append(f"New task category: {category}")
                
                # Initialize routing for new category
                logger.info(f"Discovered new task category: {category}")
        
        return discoveries
    
    async def _adjust_exploration_rates(self) -> Optional[Dict[str, Any]]:
        """Adjust exploration rates based on recent performance"""
        
        # Get recent routing stats
        stats = self.router.get_routing_stats()
        
        if stats['total_routes'] < 50:
            return None
        
        current_exploration = self.router.learner.exploration_rate
        recent_success = stats['success_rate']
        
        # Adjust based on success rate
        if recent_success > 0.85:
            # Doing well, can explore more to find even better options
            new_exploration = min(0.25, current_exploration * 1.1)
            reason = "High success rate allows for increased exploration"
        elif recent_success < 0.6:
            # Struggling, reduce exploration and exploit what works
            new_exploration = max(0.05, current_exploration * 0.8)
            reason = "Low success rate requires focus on known good options"
        else:
            # Stable, slight decay
            new_exploration = max(0.05, current_exploration * 0.98)
            reason = "Stable performance, gradual exploration reduction"
        
        # Update the router
        self.router.learner.exploration_rate = new_exploration
        
        return {
            'type': 'exploration_rate',
            'old_value': current_exploration,
            'new_value': new_exploration,
            'reason': reason,
            'metric_improved': 'exploration_efficiency'
        }
    
    async def _find_synthesis_opportunities(self) -> List[str]:
        """Find opportunities for behavior synthesis"""
        opportunities = []
        
        # Get all capabilities by category
        all_capabilities = self.registry.get_all_capabilities(status='active')
        
        # Group by category
        by_category = defaultdict(list)
        for cap in all_capabilities:
            by_category[cap.task_category].append(cap)
        
        # Look for categories with multiple similar-performing capabilities
        for category, caps in by_category.items():
            if len(caps) < 2:
                continue
            
            # Check for similar performance (ensemble opportunity)
            performances = [c.performance_score for c in caps]
            if max(performances) - min(performances) < 0.15:
                # Similar performers - ensemble might help
                opportunities.append(
                    f"{category}: {len(caps)} similar performers suggest ensemble opportunity"
                )
            
            # Check for complementary capabilities (chain opportunity)
            if len(caps) >= 3:
                # Look for preprocessing, processing, postprocessing pattern
                names = [c.name.lower() for c in caps]
                has_preprocess = any('pre' in n or 'input' in n for n in names)
                has_process = any('process' in n or 'analyze' in n or 'detect' in n for n in names)
                has_postprocess = any('post' in n or 'output' in n or 'refine' in n for n in names)
                
                if has_preprocess and has_process:
                    opportunities.append(
                        f"{category}: Preprocessing + processing chain possible"
                    )
        
        return opportunities
    
    async def _optimize_thresholds(self) -> List[Dict[str, Any]]:
        """Optimize decision thresholds"""
        adjustments = []
        
        # Analyze capability deprecation rate
        all_caps = self.registry.get_all_capabilities()
        deprecated = [c for c in all_caps if c.status == 'deprecated']
        active = [c for c in all_caps if c.status == 'active']
        
        if not active:
            return adjustments
        
        deprecation_rate = len(deprecated) / (len(deprecated) + len(active))
        
        # Adjust validation threshold based on deprecation rate
        if deprecation_rate > 0.3:
            # Too many deprecated - raise validation bar
            adjustment = {
                'type': 'threshold',
                'parameter': 'validation_score_threshold',
                'old_value': 0.7,
                'new_value': 0.75,
                'reason': f'High deprecation rate ({deprecation_rate:.1%}) requires stricter validation',
                'metric_improved': 'capability_quality'
            }
            adjustments.append(adjustment)
        elif deprecation_rate < 0.1 and len(active) > 10:
            # Few deprecations with many active - can be more lenient
            adjustment = {
                'type': 'threshold',
                'parameter': 'validation_score_threshold',
                'old_value': 0.7,
                'new_value': 0.65,
                'reason': 'Low deprecation rate allows for more capability exploration',
                'metric_improved': 'capability_discovery'
            }
            adjustments.append(adjustment)
        
        return adjustments
    
    async def _calculate_performance_delta(self) -> float:
        """Calculate overall performance improvement from this cycle"""
        # Get recent performance
        recent_routing = self.registry.get_routing_history(limit=100)
        
        if len(recent_routing) < 20:
            return 0.0
        
        # Calculate success rate trend
        recent_success = sum(1 for d in recent_routing[:50] if d.success) / min(50, len(recent_routing))
        older_success = sum(1 for d in recent_routing[50:] if d.success) / max(1, len(recent_routing) - 50)
        
        return recent_success - older_success
    
    async def run_continuous_learning(self, interval_minutes: int = 60):
        """Run continuous meta-learning"""
        self.is_running = True
        
        while self.is_running:
            try:
                cycle = await self.run_learning_cycle()
                
                if cycle.status == "completed":
                    logger.info(f"Meta-learning cycle completed: "
                               f"{len(cycle.improvements_made)} improvements, "
                               f"delta={cycle.performance_delta:+.3f}")
                
                await asyncio.sleep(interval_minutes * 60)
                
            except Exception as e:
                logger.error(f"Error in continuous learning: {e}")
                await asyncio.sleep(60)  # Retry sooner on error
    
    def stop(self):
        """Stop continuous learning"""
        self.is_running = False
    
    def get_learning_summary(self) -> Dict[str, Any]:
        """Get summary of learning activities"""
        if not self.cycles:
            return {'total_cycles': 0}
        
        total_improvements = sum(len(c.improvements_made) for c in self.cycles)
        total_discoveries = sum(len(c.discoveries) for c in self.cycles)
        
        completed = [c for c in self.cycles if c.status == 'completed']
        
        avg_delta = np.mean([c.performance_delta for c in completed]) if completed else 0
        
        return {
            'total_cycles': len(self.cycles),
            'completed_cycles': len(completed),
            'failed_cycles': len([c for c in self.cycles if c.status == 'failed']),
            'total_improvements': total_improvements,
            'total_discoveries': total_discoveries,
            'average_performance_delta': avg_delta,
            'known_categories': len(self.known_categories),
            'recent_improvements': self.cycles[-1].improvements_made if self.cycles else [],
            'current_exploration_rate': self.router.learner.exploration_rate if self.router else 0
        }


def create_meta_learner(registry: CapabilityRegistry,
                       router: TaskRouter,
                       synthesizer: BehaviorSynthesizer,
                       global_objective_fn: Optional[Callable] = None) -> MetaLearningLoop:
    """Factory function to create a meta-learning loop"""
    return MetaLearningLoop(registry, router, synthesizer, global_objective_fn)
