"""
Meta-Intelligence Orchestrator
==============================

Main orchestrator for the meta-intelligence layer.
Ties together all components into a cohesive system.

Provides the main interface for:
- Processing tasks with intelligent routing
- Managing capability distillation pipeline
- Running meta-learning loops
- Monitoring system performance
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable
from pathlib import Path
import json

from .capability_registry import CapabilityRegistry, create_registry
from .capability_distillation import CapabilityDistillationSystem, create_distillation_system
from .task_router import TaskRouter, TaskRequest, RoutingResult, ExecutionResult, create_router
from .behavior_synthesis import BehaviorSynthesizer, SynthesizedCapability, create_synthesizer
from .meta_learning_loop import MetaLearningLoop, create_meta_learner

logger = logging.getLogger(__name__)


@dataclass
class TaskOutput:
    """Output from task processing"""
    task_id: str
    success: bool
    output: Any
    routing: RoutingResult
    execution: ExecutionResult
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SystemHealth:
    """Health status of the meta-intelligence system"""
    status: str  # healthy, degraded, critical
    registry_health: Dict[str, Any]
    router_health: Dict[str, Any]
    distillation_status: Dict[str, Any]
    synthesis_status: Dict[str, Any]
    meta_learning_status: Dict[str, Any]
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


class MetaIntelligenceOrchestrator:
    """
    Main orchestrator for the model-agnostic meta-intelligence layer.
    
    This is the primary interface that applications use to:
    1. Submit tasks for intelligent routing and execution
    2. Configure the capability distillation pipeline
    3. Access synthesized composite capabilities
    4. Monitor system health and performance
    
    The orchestrator ensures the system continuously improves by:
    - Observing frontier models
    - Benchmarking and extracting behaviors
    - Validating in sandbox
    - Deploying selectively
    - Monitoring and retaining only what improves the global objective
    """
    
    def __init__(self, 
                 data_dir: str = "./meta_intelligence_data",
                 global_objective_fn: Optional[Callable[[Dict[str, Any]], float]] = None):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.global_objective_fn = global_objective_fn
        
        # Initialize components
        self.registry = create_registry(str(self.data_dir / "capability_registry.db"))
        self.distillation = create_distillation_system(
            sandbox_path=str(self.data_dir / "sandbox"),
            global_objective_fn=global_objective_fn
        )
        self.router = create_router(self.registry)
        self.synthesizer = create_synthesizer(self.registry)
        self.meta_learner = create_meta_learner(
            self.registry, self.router, self.synthesizer, global_objective_fn
        )
        
        # State
        self.is_running = False
        self.implementations: Dict[str, Callable] = {}
        
        # Background tasks
        self._background_tasks: List[asyncio.Task] = []
        
        logger.info(f"MetaIntelligenceOrchestrator initialized at {data_dir}")
    
    # ==================== Task Processing ====================
    
    async def process_task(self, 
                          task_type: str,
                          input_data: Dict[str, Any],
                          task_category: Optional[str] = None,
                          tags: Optional[List[str]] = None,
                          timeout_ms: int = 5000,
                          priority: int = 5) -> TaskOutput:
        """
        Process a task through the meta-intelligence layer.
        
        Flow:
        1. Classify and route to best capability/model
        2. Execute (distilled capability or frontier model)
        3. Record performance for learning
        4. Return result
        """
        task_id = f"task_{datetime.utcnow().timestamp()}"
        
        # Create task request
        request = TaskRequest(
            task_id=task_id,
            task_type=task_type,
            task_category=task_category or "",
            input_data=input_data,
            tags=tags or [],
            priority=priority,
            timeout_ms=timeout_ms
        )
        
        # Route the task
        routing = await self.router.route(request)
        
        # Execute based on routing decision
        if routing.selected_capability:
            # Use distilled capability
            impl = self.implementations.get(routing.selected_capability)
            if impl:
                execution = await self.router.execute_with_capability(
                    routing, request, impl
                )
            else:
                # Capability exists but no implementation loaded
                logger.warning(f"No implementation for {routing.selected_capability}, using fallback")
                execution = await self.router.execute_with_model(routing, request)
        else:
            # Use frontier model
            execution = await self.router.execute_with_model(routing, request)
        
        # Calculate global objective impact if function provided
        if self.global_objective_fn and execution.success:
            metrics = {
                'latency_ms': execution.latency_ms,
                'success': 1.0 if execution.success else 0.0,
                'routing_confidence': routing.confidence
            }
            global_impact = self.global_objective_fn(metrics)
        else:
            global_impact = None
        
        return TaskOutput(
            task_id=task_id,
            success=execution.success,
            output=execution.output,
            routing=routing,
            execution=execution,
            metadata={
                'global_objective_impact': global_impact,
                'processing_timestamp': datetime.utcnow().isoformat()
            }
        )
    
    def register_implementation(self, capability_id: str, implementation: Callable):
        """
        Register an implementation for a distilled capability.
        
        This connects the registry (which stores metadata) to actual code.
        """
        self.implementations[capability_id] = implementation
        self.synthesizer.register_implementation(capability_id, implementation)
        
        logger.info(f"Registered implementation for {capability_id}")
    
    # ==================== Capability Distillation ====================
    
    async def distill_from_model(self,
                                model_id: str,
                                provider: str,
                                interaction_data: List[Dict[str, Any]],
                                task_names: List[str],
                                failure_cases: List[Dict[str, Any]],
                                deployment_strategy: str = 'gradual') -> Dict[str, Any]:
        """
        Run a full capability distillation cycle from a frontier model.
        
        This runs the 8-step loop:
        1. Observe frontier models
        2. Benchmark by task
        3. Extract useful behaviors
        4. Invert weaknesses into controls
        5. Validate in sandbox
        6. Deploy selectively
        7. Monitor performance
        8. Keep only what improves global objective
        """
        # Define benchmark tasks if not already defined
        for task_name in task_names:
            if task_name not in self.distillation.benchmarker.task_definitions:
                # Create default evaluator
                def default_evaluator(result):
                    return result.get('confidence', 0.5)
                
                self.distillation.define_benchmark_task(
                    task_name=task_name,
                    category=task_name,
                    evaluation_fn=default_evaluator,
                    test_cases=[
                        {'input_type': task_name, 'scenario': 'default'}
                    ]
                )
        
        # Run distillation cycle
        results = await self.distillation.run_full_cycle(
            model_id=model_id,
            provider=provider,
            interaction_data=interaction_data,
            task_names=task_names,
            failure_cases=failure_cases,
            deployment_strategy=deployment_strategy
        )
        
        # Register distilled capabilities to registry
        if results.get('status') == 'completed':
            await self._register_distilled_capabilities(results)
        
        return results
    
    async def _register_distilled_capabilities(self, distillation_results: Dict[str, Any]):
        """Register distilled capabilities from distillation to the registry"""
        # Get packages that reached validation
        for package_id, package in self.distillation.capability_packages.items():
            if package.status.value in ['validated', 'deployed', 'monitoring', 'retained']:
                # Create registry record
                from .capability_registry import CapabilityRecord
                
                record = CapabilityRecord(
                    capability_id=package.package_id,
                    name=package.name,
                    task_category=package.behaviors[0].task_category if package.behaviors else 'general',
                    task_tags=['distilled', 'validated'],
                    source_model=package.behaviors[0].source_model if package.behaviors else 'unknown',
                    behaviors=[{
                        'behavior_id': b.behavior_id,
                        'name': b.name,
                        'complexity': b.complexity_score
                    } for b in package.behaviors],
                    controls=[{
                        'control_id': c.control_id,
                        'type': c.control_type
                    } for c in package.controls],
                    performance_score=package.global_objective_alignment,
                    latency_ms=100,  # Estimated
                    reliability_score=0.85,
                    metadata={
                        'distillation_date': package.created_at.isoformat(),
                        'validation_count': len(package.validation_results)
                    }
                )
                
                self.registry.register_capability(record)
    
    async def run_continuous_distillation(self, 
                                         models_to_observe: List[Dict[str, Any]],
                                         check_interval_minutes: int = 60):
        """Run continuous capability distillation in background"""
        task = asyncio.create_task(
            self.distillation.run_continuous_distillation(
                models_to_observe=models_to_observe,
                check_interval_minutes=check_interval_minutes
            )
        )
        self._background_tasks.append(task)
    
    # ==================== Behavior Synthesis ====================
    
    async def create_ensemble_capability(self,
                                      name: str,
                                      task_category: str,
                                      capability_ids: List[str],
                                      aggregation_fn: str = "weighted_avg") -> str:
        """
        Create an ensemble capability from multiple existing capabilities.
        
        Returns the synthesis_id which can be used to execute the ensemble.
        """
        synthesis = await self.synthesizer.create_ensemble(
            name=name,
            task_category=task_category,
            capability_ids=capability_ids,
            aggregation_fn=aggregation_fn
        )
        
        return synthesis.synthesis_id
    
    async def create_chain_capability(self,
                                     name: str,
                                     task_category: str,
                                     capability_ids: List[str],
                                     stage_names: Optional[List[str]] = None) -> str:
        """
        Create a chained capability where outputs feed into next stage.
        
        Returns the synthesis_id which can be used to execute the chain.
        """
        synthesis = await self.synthesizer.create_chain(
            name=name,
            task_category=task_category,
            capability_ids=capability_ids,
            stage_names=stage_names
        )
        
        return synthesis.synthesis_id
    
    async def execute_synthesized_capability(self,
                                            synthesis_id: str,
                                            input_data: Dict[str, Any],
                                            timeout_ms: int = 10000) -> Dict[str, Any]:
        """Execute a synthesized capability"""
        result = await self.synthesizer.execute_synthesis(
            synthesis_id=synthesis_id,
            input_data=input_data,
            timeout_ms=timeout_ms
        )
        
        return {
            'success': result.success,
            'output': result.output,
            'latency_ms': result.latency_ms,
            'confidence': result.confidence,
            'component_results': result.component_results
        }
    
    async def validate_and_register_synthesis(self,
                                             synthesis_id: str,
                                             test_cases: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate a synthesis and register to capability registry if successful"""
        # Validate
        validation = await self.synthesizer.validate_synthesis(
            synthesis_id=synthesis_id,
            test_cases=test_cases
        )
        
        # Register if validated
        if validation['status'] == 'validated':
            registered_id = self.synthesizer.register_to_registry(synthesis_id)
            validation['registered_capability_id'] = registered_id
        
        return validation
    
    # ==================== Meta-Learning ====================
    
    async def run_meta_learning_cycle(self) -> Dict[str, Any]:
        """Run a single meta-learning cycle"""
        cycle = await self.meta_learner.run_learning_cycle()
        
        return {
            'cycle_id': cycle.cycle_id,
            'status': cycle.status,
            'improvements_made': len(cycle.improvements_made),
            'discoveries': len(cycle.discoveries),
            'performance_delta': cycle.performance_delta,
            'improvements': cycle.improvements_made,
            'duration_seconds': (cycle.end_time - cycle.start_time).total_seconds() if cycle.end_time else None
        }
    
    async def run_continuous_meta_learning(self, interval_minutes: int = 60):
        """Run continuous meta-learning in background"""
        task = asyncio.create_task(
            self.meta_learner.run_continuous_learning(
                interval_minutes=interval_minutes
            )
        )
        self._background_tasks.append(task)
    
    # ==================== Monitoring & Health ====================
    
    def get_system_health(self) -> SystemHealth:
        """Get comprehensive system health status"""
        return SystemHealth(
            status=self._determine_overall_health(),
            registry_health={
                'total_capabilities': len(self.registry.get_all_capabilities()),
                'active_capabilities': len(self.registry.get_all_capabilities(status='active')),
                'summary': self.registry.get_registry_summary()
            },
            router_health=self.router.get_routing_stats(),
            distillation_status=self.distillation.get_system_report(),
            synthesis_status=self.synthesizer.get_synthesis_stats(),
            meta_learning_status=self.meta_learner.get_learning_summary()
        )
    
    def _determine_overall_health(self) -> str:
        """Determine overall system health"""
        # Simple health check logic
        registry_summary = self.registry.get_registry_summary()
        
        if registry_summary['by_status'].get('active', 0) < 3:
            return "critical" if registry_summary['total_capabilities'] == 0 else "degraded"
        
        routing_stats = self.router.get_routing_stats()
        if routing_stats.get('success_rate', 1.0) < 0.5:
            return "degraded"
        
        return "healthy"
    
    def get_capability_leaderboard(self, 
                                  task_category: Optional[str] = None,
                                  limit: int = 10) -> List[Dict[str, Any]]:
        """Get leaderboard of best capabilities"""
        return self.registry.get_leaderboard(task_category)[:limit]
    
    def get_comprehensive_report(self) -> Dict[str, Any]:
        """Generate comprehensive system report"""
        health = self.get_system_health()
        
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'system_status': health.status,
            'capabilities': {
                'total': health.registry_health['total_capabilities'],
                'active': health.registry_health['active_capabilities'],
                'leaderboard': self.get_capability_leaderboard(limit=5)
            },
            'routing': {
                'total_routes': health.router_health.get('total_routes', 0),
                'success_rate': health.router_health.get('success_rate', 0),
                'exploration_rate': health.router_health.get('exploration_rate', 0)
            },
            'distillation': {
                'packages': health.distillation_status.get('packages', {}),
                'behaviors': health.distillation_status.get('extractor', {}),
                'controls': health.distillation_status.get('inverter', {})
            },
            'synthesis': health.synthesis_status,
            'meta_learning': health.meta_learning_status,
            'recommendations': self._generate_recommendations(health)
        }
    
    def _generate_recommendations(self, health: SystemHealth) -> List[str]:
        """Generate system recommendations based on health"""
        recommendations = []
        
        # Check capability coverage
        if health.registry_health['active_capabilities'] < 5:
            recommendations.append("Run capability distillation to build capability inventory")
        
        # Check routing performance
        if health.router_health.get('success_rate', 1.0) < 0.7:
            recommendations.append("Review routing strategy - high failure rate detected")
        
        # Check exploration rate
        if health.router_health.get('exploration_rate', 0) > 0.3:
            recommendations.append("High exploration rate may impact consistency - consider tuning")
        
        # Check synthesis opportunities
        if health.synthesis_status.get('total_syntheses', 0) == 0 and health.registry_health['active_capabilities'] > 3:
            recommendations.append("Consider creating ensemble syntheses from multiple capabilities")
        
        return recommendations
    
    # ==================== Lifecycle ====================
    
    async def start(self):
        """Start the meta-intelligence orchestrator"""
        self.is_running = True
        logger.info("MetaIntelligenceOrchestrator started")
    
    async def stop(self):
        """Stop the orchestrator and background tasks"""
        self.is_running = False
        
        # Cancel background tasks
        for task in self._background_tasks:
            task.cancel()
        
        # Wait for cancellation
        if self._background_tasks:
            await asyncio.gather(*self._background_tasks, return_exceptions=True)
        
        self.distillation.stop()
        self.meta_learner.stop()
        
        logger.info("MetaIntelligenceOrchestrator stopped")
    
    def export_state(self, filepath: str):
        """Export system state to file"""
        report = self.get_comprehensive_report()
        
        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        logger.info(f"Exported system state to {filepath}")


def create_meta_intelligence_layer(
    data_dir: str = "./meta_intelligence_data",
    global_objective_fn: Optional[Callable[[Dict[str, Any]], float]] = None
) -> MetaIntelligenceOrchestrator:
    """
    Factory function to create the complete meta-intelligence layer.
    
    Example:
        def my_objective(metrics):
            return 0.4 * metrics.get('pnl', 0) + 0.3 * metrics.get('sharpe', 0)
        
        layer = create_meta_intelligence_layer(
            data_dir="./my_data",
            global_objective_fn=my_objective
        )
        
        # Process a task
        result = await layer.process_task(
            task_type="signal_generation",
            input_data={"symbol": "BTC/USD", "timeframe": "1h"}
        )
    """
    return MetaIntelligenceOrchestrator(data_dir, global_objective_fn)
