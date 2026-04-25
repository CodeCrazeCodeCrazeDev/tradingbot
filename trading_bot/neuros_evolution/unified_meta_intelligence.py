"""
Unified Meta-Intelligence Orchestrator
========================================

Complete integration of all meta-intelligence components:
- Universal Model Connector (any frontier model)
- Economic Objectives (PNL, Sharpe, risk-adjusted, latency, throughput)
- Fast Router (millisecond latency)
- Generic Categories (any task type)
- Capability Registry (SQLite storage)
- Behavior Synthesis
- Meta-Learning

Millisecond-scale routing with model-agnostic frontier model support.
"""

import asyncio
import time
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable, Union
from pathlib import Path
import json

# Import all components
from .capability_registry import CapabilityRegistry, CapabilityRecord, create_registry
from .capability_distillation import CapabilityDistillationSystem, create_distillation_system
from .universal_model_connector import (
    UniversalModelConnector, ModelConfig, ModelProvider,
    ModelRequest, ModelResponse, create_universal_connector
)
from .economic_objectives import (
    EconomicObjectiveLibrary, ObjectiveOptimizer,
    TradingMetrics, create_trading_metrics_from_dict,
    get_objective
)
from .fast_router import FastRouter, FastRoutingResult, create_fast_router
from .generic_categories import (
    GenericCategoryManager, TaskCategory,
    get_category_manager, detect_category, register_category
)
from .behavior_synthesis import BehaviorSynthesizer, create_synthesizer
from .meta_learning_loop import MetaLearningLoop, create_meta_learner

logger = logging.getLogger(__name__)


@dataclass
class MillisecondTaskRequest:
    """Task request optimized for millisecond processing"""
    task_id: str
    task_type: str
    input_data: Dict[str, Any]
    category_hint: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    max_latency_ms: float = 10.0  # Default 10ms for routing decision
    priority: int = 5
    allow_frontier_fallback: bool = True


@dataclass
class MillisecondTaskResult:
    """Task result with full performance metrics"""
    task_id: str
    success: bool
    output: Any
    capability_used: Optional[str]
    frontier_model_used: Optional[str]
    routing_time_ms: float
    total_latency_ms: float
    economic_score: float
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


class UnifiedMetaIntelligence:
    """
    Complete meta-intelligence layer for millisecond-scale operations.
    
    Features:
    - Connects to ANY frontier model (OpenAI, Anthropic, Google, etc.)
    - Millisecond routing decisions with pre-computed indices
    - Economic objectives: PNL, Sharpe, risk-adjusted, latency, throughput
    - SQLite storage for capabilities
    - Generic task categories (any type)
    - Continuous learning and improvement
    """
    
    def __init__(self,
                 data_dir: str = "./meta_intelligence",
                 objective_preset: str = "comprehensive",
                 custom_objective: Optional[Callable[[Dict[str, Any]], float]] = None):
        """
        Initialize unified meta-intelligence layer.
        
        Args:
            data_dir: Directory for SQLite database and data
            objective_preset: 'comprehensive', 'hft', 'alpha', 'risk_parity', 'throughput', 'latency'
            custom_objective: Override with custom objective function
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup objective function
        if custom_objective:
            self.objective_fn = custom_objective
        else:
            self.objective_fn = get_objective(objective_preset)
        
        self.objective_optimizer = ObjectiveOptimizer(self.objective_fn)
        
        # Initialize components
        self.registry = create_registry(str(self.data_dir / "capabilities.db"))
        self.connector = create_universal_connector()
        self.router = create_fast_router(self.registry, cache_size=50000, adaptive=True)
        self.category_manager = get_category_manager()
        self.distillation = create_distillation_system(
            sandbox_path=str(self.data_dir / "sandbox"),
            global_objective_fn=self.objective_fn
        )
        self.synthesizer = create_synthesizer(self.registry)
        self.meta_learner = create_meta_learner(
            self.registry, None, self.synthesizer, self.objective_fn
        )
        
        # Capability implementations (loaded at runtime)
        self._implementations: Dict[str, Callable] = {}
        
        # Frontier model configurations
        self._frontier_configs: Dict[str, ModelConfig] = {}
        
        # Performance tracking
        self._task_times: List[float] = []
        self._is_running = False
        
        logger.info(f"UnifiedMetaIntelligence initialized at {data_dir}")
        logger.info(f"Objective preset: {objective_preset}")
    
    # ==================== Frontier Model Management ====================
    
    def add_frontier_model(self,
                          provider: str,
                          model_id: str,
                          api_key: Optional[str] = None,
                          base_url: Optional[str] = None,
                          default_for_categories: Optional[List[str]] = None,
                          rate_limit_rpm: int = 60):
        """
        Add ANY frontier model to the system.
        
        Supports: openai, anthropic, google, cohere, mistral, groq, together, local, custom
        
        Example:
            meta.add_frontier_model(
                provider="openai",
                model_id="gpt-4o",
                api_key="sk-...",
                default_for_categories=["analysis", "generation"]
            )
        """
        try:
            provider_enum = ModelProvider(provider.lower())
        except ValueError:
            provider_enum = ModelProvider.CUSTOM
        
        config = ModelConfig(
            provider=provider_enum,
            model_id=model_id,
            api_key=api_key,
            base_url=base_url,
            rate_limit_rpm=rate_limit_rpm
        )
        
        connector_id = self.connector.register_model(config)
        self._frontier_configs[connector_id] = config
        
        # Register with router
        self.router.register_frontier_model(
            connector_id,
            default_for=default_for_categories
        )
        
        logger.info(f"Added frontier model: {connector_id}")
        return connector_id
    
    async def call_frontier_model(self,
                                  connector_id: str,
                                  messages: List[Dict[str, str]],
                                  temperature: float = 0.7,
                                  **kwargs) -> ModelResponse:
        """Call a registered frontier model"""
        return await self.connector.generate(connector_id, messages, temperature, **kwargs)
    
    # ==================== Task Processing (Millisecond Scale) ====================
    
    async def process(self,
                     task_type: str,
                     input_data: Dict[str, Any],
                     category_hint: Optional[str] = None,
                     tags: Optional[List[str]] = None,
                     max_latency_ms: float = 10.0,
                     allow_frontier_fallback: bool = True) -> MillisecondTaskResult:
        """
        Process a task with millisecond-scale routing.
        
        Flow:
        1. Detect/identify category (< 1ms)
        2. Route to best capability/model (< 1ms cached, < 5ms uncached)
        3. Execute (< remaining latency budget)
        4. Record metrics and update objective
        
        Total target: < 10ms for routing + execution decision
        """
        task_id = f"t{int(time.time() * 1000000)}"
        start_time = time.perf_counter()
        
        # Step 1: Detect category
        if category_hint:
            category = category_hint
            confidence = 1.0
        else:
            detected = detect_category(task_type, input_data)
            category = detected[0][0] if detected else "general"
            confidence = detected[0][1] if detected else 0.5
        
        # Step 2: Route (millisecond scale)
        task_hash = f"{category}:{hash(str(input_data)) % 1000000}"
        
        routing = await self.router.route(
            task_hash=task_hash,
            task_category=category,
            tags=tags or [],
            max_latency_ms=max_latency_ms * 0.5,  # Reserve 50% for execution
            required_tags=set(tags) if tags else None
        )
        
        routing_time = routing.decision_time_ms
        
        # Step 3: Execute
        execution_start = time.perf_counter()
        success = False
        output = None
        capability_used = None
        frontier_used = None
        
        if routing.capability_id and routing.capability_id in self._implementations:
            # Use distilled capability
            capability_used = routing.capability_id
            impl = self._implementations[routing.capability_id]
            
            try:
                if asyncio.iscoroutinefunction(impl):
                    output = await asyncio.wait_for(
                        impl(input_data),
                        timeout=max_latency_ms / 1000
                    )
                else:
                    output = impl(input_data)
                success = True
            except Exception as e:
                logger.warning(f"Capability execution failed: {e}")
                success = False
                output = None
        
        elif allow_frontier_fallback and routing.frontier_model:
            # Use frontier model
            frontier_used = routing.frontier_model
            
            try:
                messages = [
                    {"role": "system", "content": f"Execute task: {task_type} for category: {category}"},
                    {"role": "user", "content": json.dumps(input_data)}
                ]
                
                response = await asyncio.wait_for(
                    self.connector.generate(routing.frontier_model, messages, temperature=0.3),
                    timeout=max_latency_ms / 1000
                )
                
                output = response.content
                success = True
            except Exception as e:
                logger.warning(f"Frontier model call failed: {e}")
                success = False
                output = None
        
        total_time = (time.perf_counter() - start_time) * 1000
        
        # Step 4: Record and optimize
        metrics = {
            'latency_ms': total_time,
            'success': 1.0 if success else 0.0,
            'routing_confidence': routing.confidence,
            'throughput': 1000.0 / max(total_time, 1),  # Tasks per second
            'error_rate': 0.0 if success else 1.0
        }
        
        economic_score = self.objective_optimizer.evaluate(metrics)
        
        if capability_used:
            self.router.record_outcome(capability_used, success)
        
        # Track task time
        self._task_times.append(total_time)
        if len(self._task_times) > 10000:
            self._task_times = self._task_times[-5000:]
        
        return MillisecondTaskResult(
            task_id=task_id,
            success=success,
            output=output,
            capability_used=capability_used,
            frontier_model_used=frontier_used,
            routing_time_ms=routing_time,
            total_latency_ms=total_time,
            economic_score=economic_score
        )
    
    def register_capability(self, 
                         capability_id: str,
                         implementation: Callable,
                         category: str,
                         performance_score: float = 0.8,
                         latency_ms: float = 5.0):
        """
        Register a distilled capability implementation.
        
        This connects the capability registry to actual executable code.
        """
        self._implementations[capability_id] = implementation
        
        # Register with synthesizer
        self.synthesizer.register_implementation(capability_id, implementation)
        
        # Create registry record
        record = CapabilityRecord(
            capability_id=capability_id,
            name=capability_id,
            task_category=category,
            task_tags=['distilled'],
            source_model='manual',
            behaviors=[],
            controls=[],
            performance_score=performance_score,
            latency_ms=latency_ms,
            reliability_score=0.9
        )
        
        self.registry.register_capability(record)
        
        # Invalidate router cache for this category
        self.router.invalidate_cache(pattern=category)
        
        logger.info(f"Registered capability: {capability_id} ({category})")
    
    # ==================== Category Management ====================
    
    def define_category(self,
                       name: str,
                       input_schema: Dict[str, str],
                       output_schema: Dict[str, str],
                       description: str = "",
                       parent: Optional[str] = None):
        """
        Define a custom task category.
        
        Categories are completely generic - any task type is supported.
        """
        category = TaskCategory(
            name=name,
            description=description,
            input_schema=input_schema,
            output_schema=output_schema
        )
        
        register_category(category, parent)
        logger.info(f"Defined category: {name}")
    
    # ==================== Distillation ====================
    
    async def distill_from_interactions(self,
                                       model_connector_id: str,
                                       interaction_data: List[Dict[str, Any]],
                                       task_names: List[str],
                                       failure_cases: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Distill capabilities from frontier model interactions.
        
        Runs the 8-step distillation loop:
        1. Observe frontier models
        2. Benchmark by task
        3. Extract useful behaviors
        4. Invert weaknesses into controls
        5. Validate in sandbox
        6. Deploy selectively
        7. Monitor performance
        8. Keep only what improves global objective
        """
        config = self._frontier_configs.get(model_connector_id)
        if not config:
            return {'error': f'Unknown model: {model_connector_id}'}
        
        # Run distillation
        results = await self.distillation.run_full_cycle(
            model_id=config.model_id,
            provider=config.provider.value,
            interaction_data=interaction_data,
            task_names=task_names,
            failure_cases=failure_cases or [],
            deployment_strategy='gradual'
        )
        
        # Register successful distillations
        if results.get('status') == 'completed':
            await self._register_distilled_capabilities(results)
        
        return results
    
    async def _register_distilled_capabilities(self, results: Dict[str, Any]):
        """Register distilled capabilities to the system"""
        for package_id, package in self.distillation.capability_packages.items():
            if package.status.value in ['validated', 'deployed', 'monitoring', 'retained']:
                # Create implementations (would need to be generated/loaded)
                # For now, register metadata only
                
                category = package.behaviors[0].task_category if package.behaviors else 'general'
                
                record = CapabilityRecord(
                    capability_id=package_id,
                    name=package.name,
                    task_category=category,
                    task_tags=['distilled', 'validated'],
                    source_model=package.behaviors[0].source_model if package.behaviors else 'unknown',
                    behaviors=[],
                    controls=[],
                    performance_score=package.global_objective_alignment,
                    latency_ms=50,  # Estimated
                    reliability_score=0.85,
                    metadata={'distilled': True}
                )
                
                self.registry.register_capability(record)
    
    # ==================== Synthesis ====================
    
    async def create_ensemble(self,
                             name: str,
                             category: str,
                             capability_ids: List[str]) -> str:
        """Create ensemble synthesis from multiple capabilities"""
        synthesis = await self.synthesizer.create_ensemble(
            name=name,
            task_category=category,
            capability_ids=capability_ids
        )
        
        # Register implementations
        for comp in synthesis.components:
            if comp.capability_id in self._implementations:
                self.synthesizer.register_implementation(
                    comp.capability_id,
                    self._implementations[comp.capability_id]
                )
        
        return synthesis.synthesis_id
    
    async def execute_synthesis(self,
                               synthesis_id: str,
                               input_data: Dict[str, Any],
                               timeout_ms: int = 100) -> Dict[str, Any]:
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
            'confidence': result.confidence
        }
    
    # ==================== Monitoring ====================
    
    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive system statistics"""
        return {
            'objective': self.objective_optimizer.get_statistics(),
            'router': self.router.get_stats(),
            'connector': self.connector.get_connector_stats(),
            'categories': {
                'total': len(self.category_manager.get_all_categories()),
                'popular': self.category_manager.get_popular_categories(5)
            },
            'performance': {
                'avg_task_time_ms': sum(self._task_times) / max(1, len(self._task_times)),
                'p95_task_time_ms': sorted(self._task_times)[int(len(self._task_times) * 0.95)] if len(self._task_times) > 20 else 0,
                'total_tasks': len(self._task_times)
            }
        }
    
    def get_recommendations(self) -> List[str]:
        """Get system optimization recommendations"""
        recs = []
        stats = self.get_stats()
        
        # Router recommendations
        router_stats = stats['router']
        if router_stats['cache_hit_rate'] < 0.8:
            recs.append("Consider increasing router cache size for better hit rate")
        
        if router_stats['avg_decision_time_ms'] > 2:
            recs.append("Router decision time exceeding 2ms - review index optimization")
        
        # Performance recommendations
        perf = stats['performance']
        if perf['avg_task_time_ms'] > 50:
            recs.append("Average task time > 50ms - optimize capability implementations")
        
        # Objective recommendations
        obj = stats['objective']
        if obj.get('samples', 0) > 100 and obj.get('trend') == 'declining':
            recs.append("Objective performance declining - consider retraining capabilities")
        
        return recs


def create_meta_intelligence(
    data_dir: str = "./meta_intelligence",
    objective_preset: str = "comprehensive",
    custom_objective: Optional[Callable[[Dict[str, Any]], float]] = None
) -> UnifiedMetaIntelligence:
    """
    Factory function to create complete meta-intelligence layer.
    
    Example:
        meta = create_meta_intelligence(
            data_dir="./my_trading_ai",
            objective_preset="hft"  # Or 'alpha', 'risk_parity', etc.
        )
        
        # Add frontier models
        meta.add_frontier_model("openai", "gpt-4o", api_key="sk-...")
        meta.add_frontier_model("anthropic", "claude-3-opus", api_key="...")
        
        # Process task
        result = await meta.process(
            task_type="generate_signal",
            input_data={"symbol": "BTC/USD", "timeframe": "1m"},
            max_latency_ms=5  # 5ms deadline
        )
    """
    return UnifiedMetaIntelligence(data_dir, objective_preset, custom_objective)
