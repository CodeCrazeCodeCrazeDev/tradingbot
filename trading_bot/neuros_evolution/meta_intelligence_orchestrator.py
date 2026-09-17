import logging
import warnings
from typing import Dict, List, Any, Optional, Callable
from trading_bot.neuros_evolution.unified_meta_intelligence import UnifiedMetaIntelligence

logger = logging.getLogger(__name__)

class TaskOutput:
    def __init__(self, task_id: str, success: bool, output: Any, routing: Any, execution: Any, metadata: Optional[Dict] = None):
        self.task_id = task_id
        self.success = success
        self.output = output
        self.routing = routing
        self.execution = execution
        self.metadata = metadata or {}

class SystemHealth:
    def __init__(self, status: str, registry_health: Dict, router_health: Dict, distillation_status: Dict, synthesis_status: Dict, meta_learning_status: Dict):
        self.status = status
        self.registry_health = registry_health
        self.router_health = router_health
        self.distillation_status = distillation_status
        self.synthesis_status = synthesis_status
        self.meta_learning_status = meta_learning_status
        import datetime
        self.timestamp = datetime.datetime.utcnow().isoformat()

class MetaIntelligenceOrchestrator:
    """
    DEPRECATED: Legacy Meta-Intelligence Orchestrator.
    Delegates task execution to UnifiedMetaIntelligence.
    """
    def __init__(self, data_dir: str = "./meta_intelligence_data", global_objective_fn: Optional[Callable[[Dict[str, Any]], float]] = None):
        warnings.warn(
            "MetaIntelligenceOrchestrator is deprecated and has been consolidated into UnifiedMetaIntelligence.",
            DeprecationWarning,
            stacklevel=2
        )
        self.unified = UnifiedMetaIntelligence(data_dir=data_dir, custom_objective=global_objective_fn)
        self.is_running = False

    async def start(self):
        self.is_running = True

    async def stop(self):
        self.is_running = False

    async def process_task(self,
                          task_type: str,
                          input_data: Dict[str, Any],
                          task_category: Optional[str] = None,
                          tags: Optional[List[str]] = None,
                          timeout_ms: int = 5000,
                          priority: int = 5) -> TaskOutput:
        result = await self.unified.process(
            task_type=task_type,
            input_data=input_data,
            category_hint=task_category,
            tags=tags,
            max_latency_ms=float(timeout_ms)
        )

        class DummyRouting:
            def __init__(self, res):
                self.selected_capability = res.capability_used
                self.frontier_model = res.frontier_model_used
                self.confidence = 0.9

        class DummyExecution:
            def __init__(self, res):
                self.success = res.success
                self.output = res.output
                self.latency_ms = res.total_latency_ms

        return TaskOutput(
            task_id=result.task_id,
            success=result.success,
            output=result.output,
            routing=DummyRouting(result),
            execution=DummyExecution(result),
            metadata={"economic_score": result.economic_score}
        )

    def register_implementation(self, capability_id: str, implementation: Callable):
        self.unified.register_capability(capability_id, implementation, "general")

    def get_system_health(self) -> SystemHealth:
        stats = self.unified.get_stats()
        return SystemHealth(
            status="healthy",
            registry_health={},
            router_health=stats["router"],
            distillation_status={},
            synthesis_status={},
            meta_learning_status={}
        )

    def get_comprehensive_report(self) -> Dict[str, Any]:
        return self.unified.get_stats()

def create_meta_intelligence_layer(
    data_dir: str = "./meta_intelligence_data",
    global_objective_fn: Optional[Callable[[Dict[str, Any]], float]] = None
) -> MetaIntelligenceOrchestrator:
    return MetaIntelligenceOrchestrator(data_dir, global_objective_fn)
