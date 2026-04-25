"""
Autonomous Capability Distillation System
=========================================

Distills capabilities from frontier models through systematic observation,
benchmarking, behavior extraction, and controlled deployment.

Loop:
1. Observe frontier models
2. Benchmark by task
3. Extract useful behaviors
4. Invert weaknesses into controls
5. Validate in sandbox
6. Deploy selectively
7. Monitor performance
8. Keep only what improves global objective
"""

import asyncio
import json
import hashlib
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable, Tuple, Set
from enum import Enum
from pathlib import Path
import numpy as np
from collections import defaultdict
import copy

logger = logging.getLogger(__name__)


class CapabilityStatus(Enum):
    OBSERVED = "observed"
    BENCHMARKED = "benchmarked"
    EXTRACTED = "extracted"
    CONTROLLED = "controlled"
    VALIDATING = "validating"
    DEPLOYED = "deployed"
    MONITORING = "monitoring"
    RETAINED = "retained"
    REJECTED = "rejected"


@dataclass
class FrontierModel:
    """Represents a frontier model being observed"""
    model_id: str
    name: str
    provider: str
    capabilities: List[str] = field(default_factory=list)
    observed_behaviors: List[Dict[str, Any]] = field(default_factory=list)
    benchmark_scores: Dict[str, float] = field(default_factory=dict)
    weaknesses: List[str] = field(default_factory=list)
    last_observed: datetime = field(default_factory=datetime.utcnow)
    observation_count: int = 0


@dataclass
class TaskBenchmark:
    """Benchmark result for a specific task"""
    benchmark_id: str
    task_name: str
    task_category: str
    model_id: str
    score: float
    latency_ms: float
    accuracy: float
    robustness_score: float
    execution_trace: List[Dict[str, Any]] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExtractedBehavior:
    """A behavior extracted from a frontier model"""
    behavior_id: str
    name: str
    description: str
    source_model: str
    task_category: str
    implementation_pattern: Dict[str, Any]
    confidence_score: float
    performance_baseline: float
    complexity_score: float  # 0-1, lower is simpler
    dependencies: List[str] = field(default_factory=list)
    extracted_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class WeaknessControl:
    """Control mechanism derived from a weakness"""
    control_id: str
    weakness_description: str
    source_behavior: str
    control_type: str  # 'constraint', 'monitor', 'fallback', 'circuit_breaker'
    implementation: Dict[str, Any]
    detection_pattern: str
    response_action: str
    effectiveness_score: float = 0.0


@dataclass
class CapabilityPackage:
    """Complete distilled capability ready for validation"""
    package_id: str
    name: str
    behaviors: List[ExtractedBehavior]
    controls: List[WeaknessControl]
    sandbox_config: Dict[str, Any]
    global_objective_alignment: float
    created_at: datetime = field(default_factory=datetime.utcnow)
    status: CapabilityStatus = CapabilityStatus.EXTRACTED
    validation_results: List[Dict[str, Any]] = field(default_factory=list)
    deployment_metrics: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SandboxResult:
    """Results from sandbox validation"""
    result_id: str
    package_id: str
    passed: bool
    safety_score: float
    performance_score: float
    robustness_score: float
    resource_usage: Dict[str, float]
    error_logs: List[str] = field(default_factory=list)
    execution_traces: List[Dict[str, Any]] = field(default_factory=list)
    validated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class DeploymentRecord:
    """Record of a deployed capability"""
    deployment_id: str
    package_id: str
    deployed_at: datetime
    rollout_percentage: float
    performance_metrics: Dict[str, float] = field(default_factory=dict)
    error_rate: float = 0.0
    global_objective_impact: float = 0.0
    status: str = "active"  # active, paused, rolled_back


class FrontierObserver:
    """Observes and catalogs frontier models"""
    
    def __init__(self):
        self.observed_models: Dict[str, FrontierModel] = {}
        self.observation_history: List[Dict[str, Any]] = []
        self.known_providers = ["openai", "anthropic", "google", "meta", "mistral", "cohere"]
        logger.info("FrontierObserver initialized")
    
    async def observe_model(self, model_id: str, provider: str, 
                          interaction_data: List[Dict[str, Any]]) -> FrontierModel:
        """Observe a frontier model and extract initial behaviors"""
        
        model = FrontierModel(
            model_id=model_id,
            name=f"{provider}/{model_id}",
            provider=provider,
            last_observed=datetime.utcnow()
        )
        
        # Extract behaviors from interaction data
        for interaction in interaction_data:
            behavior = self._extract_behavior_from_interaction(interaction)
            if behavior:
                model.observed_behaviors.append(behavior)
                if behavior['type'] not in model.capabilities:
                    model.capabilities.append(behavior['type'])
        
        model.observation_count += 1
        self.observed_models[model_id] = model
        
        logger.info(f"Observed model {model_id}: found {len(model.observed_behaviors)} behaviors")
        return model
    
    def _extract_behavior_from_interaction(self, interaction: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract a behavior pattern from an interaction"""
        if 'response' not in interaction or 'task' not in interaction:
            return None
        
        return {
            'type': interaction.get('task_type', 'unknown'),
            'input_pattern': self._patternize(interaction['task']),
            'output_pattern': self._patternize(interaction['response']),
            'reasoning_steps': interaction.get('reasoning', []),
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def _patternize(self, text: str) -> str:
        """Convert text to a generalized pattern"""
        # Simple pattern extraction - can be enhanced with NLP
        words = text.lower().split()[:10]
        return ' '.join(words)
    
    def get_models_by_capability(self, capability: str) -> List[FrontierModel]:
        """Get all models with a specific capability"""
        return [m for m in self.observed_models.values() if capability in m.capabilities]
    
    def get_observation_report(self) -> Dict[str, Any]:
        """Generate observation report"""
        return {
            'total_models': len(self.observed_models),
            'total_behaviors': sum(len(m.observed_behaviors) for m in self.observed_models.values()),
            'capability_distribution': self._get_capability_distribution(),
            'models': {k: {
                'name': v.name,
                'capabilities': v.capabilities,
                'observation_count': v.observation_count
            } for k, v in self.observed_models.items()}
        }
    
    def _get_capability_distribution(self) -> Dict[str, int]:
        """Get distribution of capabilities across models"""
        distribution = defaultdict(int)
        for model in self.observed_models.values():
            for cap in model.capabilities:
                distribution[cap] += 1
        return dict(distribution)


class TaskBenchmarker:
    """Benchmarks models on specific tasks"""
    
    def __init__(self):
        self.benchmarks: Dict[str, TaskBenchmark] = {}
        self.task_definitions: Dict[str, Dict[str, Any]] = {}
        self.benchmark_history: List[TaskBenchmark] = []
        logger.info("TaskBenchmarker initialized")
    
    def define_task(self, task_name: str, category: str, 
                   evaluation_fn: Callable[[Any], float],
                   test_cases: List[Dict[str, Any]]):
        """Define a benchmark task"""
        self.task_definitions[task_name] = {
            'category': category,
            'evaluator': evaluation_fn,
            'test_cases': test_cases
        }
    
    async def benchmark_model(self, model: FrontierModel, 
                             task_name: str) -> TaskBenchmark:
        """Run benchmark on a model for a specific task"""
        
        if task_name not in self.task_definitions:
            raise ValueError(f"Unknown task: {task_name}")
        
        task_def = self.task_definitions[task_name]
        test_cases = task_def['test_cases']
        evaluator = task_def['evaluator']
        
        scores = []
        latencies = []
        execution_traces = []
        
        for test_case in test_cases:
            start_time = datetime.utcnow()
            
            # Simulate or execute the task
            result = await self._execute_task(model, test_case)
            
            latency = (datetime.utcnow() - start_time).total_seconds() * 1000
            score = evaluator(result)
            
            scores.append(score)
            latencies.append(latency)
            execution_traces.append({
                'test_case': test_case,
                'result': result,
                'score': score,
                'latency_ms': latency
            })
        
        benchmark = TaskBenchmark(
            benchmark_id=self._generate_id(f"bench_{model.model_id}_{task_name}"),
            task_name=task_name,
            task_category=task_def['category'],
            model_id=model.model_id,
            score=np.mean(scores),
            latency_ms=np.mean(latencies),
            accuracy=max(scores),  # Best case accuracy
            robustness_score=np.std(scores),  # Lower std = more robust
            execution_trace=execution_traces
        )
        
        self.benchmarks[benchmark.benchmark_id] = benchmark
        self.benchmark_history.append(benchmark)
        model.benchmark_scores[task_name] = benchmark.score
        
        logger.info(f"Benchmarked {model.model_id} on {task_name}: score={benchmark.score:.3f}")
        return benchmark
    
    async def _execute_task(self, model: FrontierModel, 
                           test_case: Dict[str, Any]) -> Any:
        """Execute a task with the model (placeholder for actual execution)"""
        # This would integrate with actual model APIs
        await asyncio.sleep(0.01)  # Simulate execution
        
        # Simulate result based on model's observed capabilities
        base_score = 0.7
        if test_case.get('task_type') in model.capabilities:
            base_score += 0.2
        
        return {'output': 'simulated', 'confidence': base_score + np.random.uniform(-0.1, 0.1)}
    
    def get_leaderboard(self, task_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get benchmark leaderboard"""
        benchmarks = self.benchmark_history
        if task_name:
            benchmarks = [b for b in benchmarks if b.task_name == task_name]
        
        # Sort by score descending
        sorted_benchmarks = sorted(benchmarks, key=lambda x: x.score, reverse=True)
        
        return [{
            'model_id': b.model_id,
            'task': b.task_name,
            'score': b.score,
            'latency_ms': b.latency_ms,
            'accuracy': b.accuracy,
            'timestamp': b.timestamp.isoformat()
        } for b in sorted_benchmarks[:20]]
    
    def _generate_id(self, prefix: str) -> str:
        """Generate unique ID"""
        hash_input = f"{prefix}_{datetime.utcnow().timestamp()}"
        return hashlib.md5(hash_input.encode()).hexdigest()[:16]


class BehaviorExtractor:
    """Extracts useful behaviors from benchmark results"""
    
    def __init__(self):
        self.extracted_behaviors: Dict[str, ExtractedBehavior] = {}
        self.extraction_patterns: Dict[str, Callable] = {}
        logger.info("BehaviorExtractor initialized")
    
    async def extract_behaviors(self, benchmark: TaskBenchmark,
                               model: FrontierModel) -> List[ExtractedBehavior]:
        """Extract behaviors from a successful benchmark"""
        
        behaviors = []
        
        # Only extract from high-performing runs
        if benchmark.score < 0.7:
            logger.info(f"Skipping extraction for {benchmark.model_id} - score too low")
            return behaviors
        
        # Analyze execution traces for patterns
        for trace in benchmark.execution_trace:
            if trace['score'] > 0.8:  # High-performing execution
                behavior = await self._extract_from_trace(
                    trace, benchmark, model
                )
                if behavior:
                    behaviors.append(behavior)
                    self.extracted_behaviors[behavior.behavior_id] = behavior
        
        logger.info(f"Extracted {len(behaviors)} behaviors from {benchmark.model_id}")
        return behaviors
    
    async def _extract_from_trace(self, trace: Dict[str, Any],
                                 benchmark: TaskBenchmark,
                                 model: FrontierModel) -> Optional[ExtractedBehavior]:
        """Extract a behavior from an execution trace"""
        
        # Analyze the trace to extract the pattern
        implementation = self._generalize_pattern(trace)
        
        behavior = ExtractedBehavior(
            behavior_id=self._generate_id(f"beh_{benchmark.model_id}"),
            name=f"{benchmark.task_category}_pattern_{len(self.extracted_behaviors)}",
            description=f"Extracted from {model.name} on {benchmark.task_name}",
            source_model=model.model_id,
            task_category=benchmark.task_category,
            implementation_pattern=implementation,
            confidence_score=trace['score'],
            performance_baseline=benchmark.score,
            complexity_score=self._calculate_complexity(implementation)
        )
        
        return behavior
    
    def _generalize_pattern(self, trace: Dict[str, Any]) -> Dict[str, Any]:
        """Generalize an execution trace into a reusable pattern"""
        return {
            'input_schema': self._infer_schema(trace['test_case']),
            'processing_steps': self._extract_steps(trace.get('result', {})),
            'output_schema': self._infer_schema(trace['result']),
            'success_conditions': ['score > 0.8'],
            'parameters': self._extract_parameters(trace)
        }
    
    def _infer_schema(self, data: Dict[str, Any]) -> Dict[str, str]:
        """Infer schema from data"""
        schema = {}
        for key, value in data.items():
            schema[key] = type(value).__name__
        return schema
    
    def _extract_steps(self, result: Dict[str, Any]) -> List[str]:
        """Extract processing steps from result"""
        steps = []
        if 'reasoning' in result:
            steps.extend(result['reasoning'])
        if 'intermediate_steps' in result:
            steps.extend(result['intermediate_steps'])
        return steps if steps else ['process', 'transform', 'output']
    
    def _extract_parameters(self, trace: Dict[str, Any]) -> Dict[str, Any]:
        """Extract tunable parameters from trace"""
        return {
            'threshold': 0.8,
            'max_iterations': 3,
            'timeout_ms': 1000
        }
    
    def _calculate_complexity(self, implementation: Dict[str, Any]) -> float:
        """Calculate complexity score (0-1, lower is simpler)"""
        steps = len(implementation.get('processing_steps', []))
        params = len(implementation.get('parameters', {}))
        return min(1.0, (steps + params) / 20)
    
    def get_behaviors_by_category(self, category: str) -> List[ExtractedBehavior]:
        """Get behaviors for a specific category"""
        return [b for b in self.extracted_behaviors.values() 
                if b.task_category == category]
    
    def _generate_id(self, prefix: str) -> str:
        """Generate unique ID"""
        hash_input = f"{prefix}_{datetime.utcnow().timestamp()}"
        return hashlib.md5(hash_input.encode()).hexdigest()[:16]


class WeaknessInverter:
    """Inverts weaknesses into control mechanisms"""
    
    def __init__(self):
        self.controls: Dict[str, WeaknessControl] = {}
        self.control_templates: Dict[str, Dict[str, Any]] = {
            'constraint': {
                'description': 'Hard constraint to prevent the weakness',
                'implementation_type': 'precondition_check'
            },
            'monitor': {
                'description': 'Continuous monitoring for weakness indicators',
                'implementation_type': 'runtime_monitor'
            },
            'fallback': {
                'description': 'Fallback mechanism when weakness detected',
                'implementation_type': 'backup_strategy'
            },
            'circuit_breaker': {
                'description': 'Stop execution if weakness manifests',
                'implementation_type': 'safety_cutoff'
            }
        }
        logger.info("WeaknessInverter initialized")
    
    async def invert_weakness(self, behavior: ExtractedBehavior,
                             failure_cases: List[Dict[str, Any]]) -> List[WeaknessControl]:
        """Convert weaknesses into controls"""
        
        controls = []
        
        # Analyze failure cases to identify weakness patterns
        for failure in failure_cases:
            weakness_desc = self._characterize_weakness(failure, behavior)
            
            # Create multiple types of controls for each weakness
            for control_type in ['constraint', 'monitor', 'fallback']:
                control = self._create_control(
                    weakness_desc, behavior, control_type, failure
                )
                controls.append(control)
                self.controls[control.control_id] = control
        
        logger.info(f"Created {len(controls)} controls for behavior {behavior.behavior_id}")
        return controls
    
    def _characterize_weakness(self, failure: Dict[str, Any],
                              behavior: ExtractedBehavior) -> str:
        """Characterize the weakness from a failure case"""
        failure_type = failure.get('type', 'unknown')
        
        weakness_map = {
            'timeout': f"Slow execution in {behavior.task_category}",
            'error': f"Runtime error in {behavior.task_category} pattern",
            'incorrect': f"Accuracy degradation in {behavior.task_category}",
            'hallucination': f"Unreliable outputs in {behavior.task_category}",
            'bias': f"Systematic bias detected in {behavior.task_category}"
        }
        
        return weakness_map.get(failure_type, f"General weakness in {behavior.task_category}")
    
    def _create_control(self, weakness: str, behavior: ExtractedBehavior,
                       control_type: str, failure: Dict[str, Any]) -> WeaknessControl:
        """Create a control mechanism"""
        
        template = self.control_templates[control_type]
        
        detection_pattern = self._generate_detection_pattern(failure)
        response_action = self._generate_response_action(control_type, failure)
        
        control = WeaknessControl(
            control_id=self._generate_id(f"ctrl_{behavior.behavior_id}"),
            weakness_description=weakness,
            source_behavior=behavior.behavior_id,
            control_type=control_type,
            implementation={
                'template': template,
                'checkpoints': self._generate_checkpoints(behavior),
                'recovery_steps': self._generate_recovery(failure)
            },
            detection_pattern=detection_pattern,
            response_action=response_action
        )
        
        return control
    
    def _generate_detection_pattern(self, failure: Dict[str, Any]) -> str:
        """Generate pattern to detect the weakness"""
        failure_type = failure.get('type', 'unknown')
        
        patterns = {
            'timeout': "execution_time > threshold",
            'error': "exception_raised OR error_rate > 0.1",
            'incorrect': "accuracy < 0.95 OR confidence < 0.7",
            'hallucination': "output_inconsistent_with_input",
            'bias': "systematic_deviation_detected"
        }
        
        return patterns.get(failure_type, "anomaly_detected")
    
    def _generate_response_action(self, control_type: str, 
                                  failure: Dict[str, Any]) -> str:
        """Generate response action for control type"""
        
        responses = {
            'constraint': "block_execution_and_log",
            'monitor': "alert_and_continue_with_caution",
            'fallback': "switch_to_backup_strategy",
            'circuit_breaker': "immediate_stop_and_escalate"
        }
        
        return responses.get(control_type, "log_and_continue")
    
    def _generate_checkpoints(self, behavior: ExtractedBehavior) -> List[str]:
        """Generate validation checkpoints"""
        return [
            f"pre_{behavior.task_category}_validation",
            f"mid_{behavior.task_category}_health_check",
            f"post_{behavior.task_category}_verification"
        ]
    
    def _generate_recovery(self, failure: Dict[str, Any]) -> List[str]:
        """Generate recovery steps"""
        return [
            "isolate_affected_component",
            "reset_to_last_known_good_state",
            "notify_monitoring_system"
        ]
    
    def get_controls_for_behavior(self, behavior_id: str) -> List[WeaknessControl]:
        """Get all controls for a specific behavior"""
        return [c for c in self.controls.values() if c.source_behavior == behavior_id]
    
    def _generate_id(self, prefix: str) -> str:
        """Generate unique ID"""
        hash_input = f"{prefix}_{datetime.utcnow().timestamp()}"
        return hashlib.md5(hash_input.encode()).hexdigest()[:16]


class SandboxValidator:
    """Validates capability packages in sandbox"""
    
    def __init__(self, sandbox_path: Optional[str] = None):
        self.sandbox_path = Path(sandbox_path) if sandbox_path else Path("./sandbox")
        self.validation_history: List[SandboxResult] = []
        self.test_scenarios: List[Dict[str, Any]] = []
        self.safety_threshold = 0.85
        self.performance_threshold = 0.70
        logger.info(f"SandboxValidator initialized at {self.sandbox_path}")
    
    def add_test_scenario(self, scenario: Dict[str, Any]):
        """Add a test scenario for validation"""
        self.test_scenarios.append(scenario)
    
    async def validate_package(self, package: CapabilityPackage) -> SandboxResult:
        """Validate a capability package in sandbox"""
        
        logger.info(f"Validating package {package.package_id} in sandbox")
        
        # Run safety tests
        safety_score = await self._run_safety_tests(package)
        
        # Run performance tests
        performance_score = await self._run_performance_tests(package)
        
        # Run robustness tests
        robustness_score = await self._run_robustness_tests(package)
        
        # Check resource usage
        resource_usage = await self._measure_resource_usage(package)
        
        # Collect errors
        error_logs = []
        if safety_score < self.safety_threshold:
            error_logs.append(f"Safety score {safety_score:.3f} below threshold {self.safety_threshold}")
        if performance_score < self.performance_threshold:
            error_logs.append(f"Performance score {performance_score:.3f} below threshold {self.performance_threshold}")
        
        passed = safety_score >= self.safety_threshold and performance_score >= self.performance_threshold
        
        result = SandboxResult(
            result_id=self._generate_id(f"val_{package.package_id}"),
            package_id=package.package_id,
            passed=passed,
            safety_score=safety_score,
            performance_score=performance_score,
            robustness_score=robustness_score,
            resource_usage=resource_usage,
            error_logs=error_logs
        )
        
        self.validation_history.append(result)
        package.validation_results.append(asdict(result))
        
        if passed:
            package.status = CapabilityStatus.VALIDATING
        else:
            package.status = CapabilityStatus.REJECTED
        
        logger.info(f"Validation result for {package.package_id}: passed={passed}")
        return result
    
    async def _run_safety_tests(self, package: CapabilityPackage) -> float:
        """Run safety tests"""
        scores = []
        
        # Test each control mechanism
        for control in package.controls:
            score = await self._test_control_effectiveness(control)
            scores.append(score)
        
        # Test behavior isolation
        for behavior in package.behaviors:
            score = await self._test_behavior_isolation(behavior)
            scores.append(score)
        
        return np.mean(scores) if scores else 0.0
    
    async def _test_control_effectiveness(self, control: WeaknessControl) -> float:
        """Test if control effectively prevents weakness"""
        await asyncio.sleep(0.01)
        # Simulate control test
        return 0.85 + np.random.uniform(-0.1, 0.1)
    
    async def _test_behavior_isolation(self, behavior: ExtractedBehavior) -> float:
        """Test if behavior is properly isolated"""
        await asyncio.sleep(0.01)
        return 0.90 + np.random.uniform(-0.05, 0.05)
    
    async def _run_performance_tests(self, package: CapabilityPackage) -> float:
        """Run performance tests"""
        scores = []
        
        for behavior in package.behaviors:
            # Test baseline performance
            baseline_score = await self._test_baseline_performance(behavior)
            scores.append(baseline_score)
            
            # Test under load
            load_score = await self._test_under_load(behavior)
            scores.append(load_score)
        
        return np.mean(scores) if scores else 0.0
    
    async def _test_baseline_performance(self, behavior: ExtractedBehavior) -> float:
        """Test baseline performance"""
        await asyncio.sleep(0.01)
        return behavior.performance_baseline + np.random.uniform(-0.05, 0.05)
    
    async def _test_under_load(self, behavior: ExtractedBehavior) -> float:
        """Test performance under load"""
        await asyncio.sleep(0.01)
        return behavior.performance_baseline * 0.9 + np.random.uniform(-0.05, 0.05)
    
    async def _run_robustness_tests(self, package: CapabilityPackage) -> float:
        """Run robustness tests"""
        await asyncio.sleep(0.01)
        return 0.80 + np.random.uniform(-0.1, 0.1)
    
    async def _measure_resource_usage(self, package: CapabilityPackage) -> Dict[str, float]:
        """Measure resource usage"""
        return {
            'cpu_percent': np.random.uniform(10, 40),
            'memory_mb': np.random.uniform(100, 500),
            'io_operations': np.random.uniform(50, 200)
        }
    
    def get_validation_report(self) -> Dict[str, Any]:
        """Generate validation report"""
        total = len(self.validation_history)
        passed = len([r for r in self.validation_history if r.passed])
        
        return {
            'total_validations': total,
            'passed': passed,
            'failed': total - passed,
            'pass_rate': passed / total if total > 0 else 0,
            'average_safety_score': np.mean([r.safety_score for r in self.validation_history]) if self.validation_history else 0,
            'average_performance_score': np.mean([r.performance_score for r in self.validation_history]) if self.validation_history else 0
        }
    
    def _generate_id(self, prefix: str) -> str:
        """Generate unique ID"""
        hash_input = f"{prefix}_{datetime.utcnow().timestamp()}"
        return hashlib.md5(hash_input.encode()).hexdigest()[:16]


class SelectiveDeployer:
    """Selectively deploys validated capabilities"""
    
    def __init__(self):
        self.deployed_packages: Dict[str, DeploymentRecord] = {}
        self.deployment_history: List[DeploymentRecord] = []
        self.rollout_strategies = {
            'gradual': [0.05, 0.10, 0.25, 0.50, 1.0],
            'aggressive': [0.25, 0.50, 1.0],
            'cautious': [0.01, 0.05, 0.10, 0.25, 0.50, 0.75, 1.0]
        }
        logger.info("SelectiveDeployer initialized")
    
    async def deploy(self, package: CapabilityPackage,
                    strategy: str = 'gradual') -> DeploymentRecord:
        """Deploy a capability package with rollout strategy"""
        
        if package.status != CapabilityStatus.VALIDATING:
            raise ValueError(f"Package {package.package_id} not validated")
        
        deployment_id = self._generate_id(f"deploy_{package.package_id}")
        
        # Start with initial rollout percentage
        rollout_steps = self.rollout_strategies.get(strategy, self.rollout_strategies['gradual'])
        initial_percentage = rollout_steps[0]
        
        record = DeploymentRecord(
            deployment_id=deployment_id,
            package_id=package.package_id,
            deployed_at=datetime.utcnow(),
            rollout_percentage=initial_percentage,
            status="active"
        )
        
        self.deployed_packages[package.package_id] = record
        self.deployment_history.append(record)
        package.status = CapabilityStatus.DEPLOYED
        
        logger.info(f"Deployed package {package.package_id} at {initial_percentage*100}% rollout")
        
        # Start rollout progression
        asyncio.create_task(self._progress_rollout(record, rollout_steps))
        
        return record
    
    async def _progress_rollout(self, record: DeploymentRecord, steps: List[float]):
        """Progressively increase rollout percentage"""
        for percentage in steps[1:]:  # Skip first (already deployed)
            await asyncio.sleep(60)  # Wait between steps
            
            if record.status != "active":
                break
            
            # Check metrics before increasing
            metrics = await self._get_deployment_metrics(record)
            
            if metrics['error_rate'] > 0.05 or metrics['performance_degradation'] > 0.1:
                logger.warning(f"Halting rollout for {record.package_id} due to issues")
                record.status = "paused"
                break
            
            record.rollout_percentage = percentage
            logger.info(f"Increased rollout for {record.package_id} to {percentage*100}%")
    
    async def _get_deployment_metrics(self, record: DeploymentRecord) -> Dict[str, float]:
        """Get metrics for a deployment"""
        # Simulate metrics collection
        return {
            'error_rate': np.random.uniform(0, 0.03),
            'performance_degradation': np.random.uniform(0, 0.05),
            'latency_increase': np.random.uniform(0, 0.1)
        }
    
    async def rollback(self, package_id: str) -> bool:
        """Rollback a deployment"""
        if package_id not in self.deployed_packages:
            return False
        
        record = self.deployed_packages[package_id]
        record.status = "rolled_back"
        record.rollout_percentage = 0
        
        logger.info(f"Rolled back deployment {package_id}")
        return True
    
    def get_deployment_status(self, package_id: str) -> Optional[Dict[str, Any]]:
        """Get deployment status"""
        if package_id not in self.deployed_packages:
            return None
        
        record = self.deployed_packages[package_id]
        return {
            'deployment_id': record.deployment_id,
            'package_id': record.package_id,
            'status': record.status,
            'rollout_percentage': record.rollout_percentage,
            'deployed_at': record.deployed_at.isoformat(),
            'metrics': record.performance_metrics
        }
    
    def _generate_id(self, prefix: str) -> str:
        """Generate unique ID"""
        hash_input = f"{prefix}_{datetime.utcnow().timestamp()}"
        return hashlib.md5(hash_input.encode()).hexdigest()[:16]


class PerformanceMonitor:
    """Monitors deployed capabilities and their impact"""
    
    def __init__(self):
        self.monitoring_data: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self.global_objective_fn: Optional[Callable] = None
        self.retention_threshold = 0.05  # Minimum improvement to retain
        logger.info("PerformanceMonitor initialized")
    
    def set_global_objective(self, objective_fn: Callable[[Dict[str, Any]], float]):
        """Set the global objective function"""
        self.global_objective_fn = objective_fn
    
    async def monitor_deployment(self, deployment: DeploymentRecord) -> Dict[str, Any]:
        """Monitor a deployed capability"""
        
        # Collect metrics
        metrics = await self._collect_metrics(deployment)
        
        # Calculate global objective impact
        if self.global_objective_fn:
            global_impact = self.global_objective_fn(metrics)
        else:
            global_impact = self._default_objective(metrics)
        
        deployment.global_objective_impact = global_impact
        
        # Store monitoring data
        self.monitoring_data[deployment.package_id].append({
            'timestamp': datetime.utcnow().isoformat(),
            'metrics': metrics,
            'global_impact': global_impact
        })
        
        # Decide whether to retain
        decision = self._make_retention_decision(deployment, global_impact)
        
        logger.info(f"Monitoring {deployment.package_id}: impact={global_impact:.3f}, decision={decision}")
        
        return {
            'deployment_id': deployment.deployment_id,
            'metrics': metrics,
            'global_impact': global_impact,
            'retention_decision': decision
        }
    
    async def _collect_metrics(self, deployment: DeploymentRecord) -> Dict[str, float]:
        """Collect performance metrics"""
        
        # Simulate metric collection
        return {
            'throughput': np.random.uniform(100, 1000),
            'latency_p95': np.random.uniform(10, 100),
            'error_rate': np.random.uniform(0, 0.01),
            'resource_efficiency': np.random.uniform(0.7, 0.95),
            'user_satisfaction': np.random.uniform(0.8, 0.99)
        }
    
    def _default_objective(self, metrics: Dict[str, float]) -> float:
        """Default global objective function"""
        # Weighted combination of metrics
        weights = {
            'throughput': 0.2,
            'latency_p95': -0.2,  # Lower is better
            'error_rate': -0.3,  # Lower is better
            'resource_efficiency': 0.15,
            'user_satisfaction': 0.35
        }
        
        score = 0
        for metric, weight in weights.items():
            value = metrics.get(metric, 0)
            if metric == 'latency_p95':
                value = 1 / (1 + value / 100)  # Normalize latency
            score += value * weight
        
        return score
    
    def _make_retention_decision(self, deployment: DeploymentRecord, 
                                 global_impact: float) -> str:
        """Decide whether to retain the capability"""
        
        if global_impact > self.retention_threshold:
            return "retain"
        elif global_impact < -0.05:
            return "remove"
        else:
            return "monitor"
    
    def get_monitoring_summary(self) -> Dict[str, Any]:
        """Get summary of all monitoring data"""
        summary = {}
        
        for package_id, data_points in self.monitoring_data.items():
            if not data_points:
                continue
            
            impacts = [d['global_impact'] for d in data_points]
            summary[package_id] = {
                'data_points': len(data_points),
                'avg_global_impact': np.mean(impacts),
                'trend': 'improving' if impacts[-1] > impacts[0] else 'stable' if abs(impacts[-1] - impacts[0]) < 0.01 else 'declining',
                'latest_decision': self._make_retention_decision(None, impacts[-1])
            }
        
        return summary


class CapabilityDistillationSystem:
    """
    Main orchestrator for autonomous capability distillation.
    
    Implements the full loop:
    1. Observe frontier models
    2. Benchmark by task
    3. Extract useful behaviors
    4. Invert weaknesses into controls
    5. Validate in sandbox
    6. Deploy selectively
    7. Monitor performance
    8. Keep only what improves global objective
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Initialize components
        self.observer = FrontierObserver()
        self.benchmarker = TaskBenchmarker()
        self.extractor = BehaviorExtractor()
        self.inverter = WeaknessInverter()
        self.sandbox = SandboxValidator(self.config.get('sandbox_path'))
        self.deployer = SelectiveDeployer()
        self.monitor = PerformanceMonitor()
        
        # State
        self.capability_packages: Dict[str, CapabilityPackage] = {}
        self.active_runs: Set[str] = set()
        self.is_running = False
        
        logger.info("CapabilityDistillationSystem initialized")
    
    def define_benchmark_task(self, task_name: str, category: str,
                              evaluation_fn: Callable[[Any], float],
                              test_cases: List[Dict[str, Any]]):
        """Define a benchmark task"""
        self.benchmarker.define_task(task_name, category, evaluation_fn, test_cases)
    
    def set_global_objective(self, objective_fn: Callable[[Dict[str, Any]], float]):
        """Set the global objective function for retention decisions"""
        self.monitor.set_global_objective(objective_fn)
    
    async def observe_and_benchmark(self, model_id: str, provider: str,
                                    interaction_data: List[Dict[str, Any]],
                                    task_names: List[str]) -> FrontierModel:
        """Steps 1-2: Observe and benchmark a frontier model"""
        
        # Step 1: Observe
        model = await self.observer.observe_model(model_id, provider, interaction_data)
        
        # Step 2: Benchmark
        for task_name in task_names:
            if task_name in self.benchmarker.task_definitions:
                await self.benchmarker.benchmark_model(model, task_name)
        
        return model
    
    async def extract_and_control(self, benchmark: TaskBenchmark,
                                  model: FrontierModel,
                                  failure_cases: List[Dict[str, Any]]) -> CapabilityPackage:
        """Steps 3-4: Extract behaviors and create controls"""
        
        # Step 3: Extract behaviors
        behaviors = await self.extractor.extract_behaviors(benchmark, model)
        
        if not behaviors:
            logger.info(f"No behaviors extracted from {benchmark.model_id}")
            return None
        
        # Step 4: Invert weaknesses into controls
        all_controls = []
        for behavior in behaviors:
            controls = await self.inverter.invert_weakness(behavior, failure_cases)
            all_controls.extend(controls)
        
        # Create capability package
        package = CapabilityPackage(
            package_id=self._generate_id(f"pkg_{model.model_id}"),
            name=f"Distilled capabilities from {model.name}",
            behaviors=behaviors,
            controls=all_controls,
            sandbox_config={
                'timeout_seconds': 300,
                'max_memory_mb': 512,
                'isolation_level': 'strict'
            },
            global_objective_alignment=benchmark.score
        )
        
        self.capability_packages[package.package_id] = package
        return package
    
    async def validate_and_deploy(self, package: CapabilityPackage,
                                  strategy: str = 'gradual') -> Optional[DeploymentRecord]:
        """Steps 5-6: Validate in sandbox and deploy selectively"""
        
        # Step 5: Validate in sandbox
        validation = await self.sandbox.validate_package(package)
        
        if not validation.passed:
            logger.warning(f"Package {package.package_id} failed validation")
            return None
        
        # Step 6: Deploy selectively
        deployment = await self.deployer.deploy(package, strategy)
        return deployment
    
    async def monitor_and_retain(self, deployment: DeploymentRecord) -> Dict[str, Any]:
        """Steps 7-8: Monitor and decide retention"""
        
        # Step 7: Monitor performance
        monitoring_result = await self.monitor.monitor_deployment(deployment)
        
        # Step 8: Keep only if improves global objective
        if monitoring_result['retention_decision'] == 'remove':
            await self.deployer.rollback(deployment.package_id)
            logger.info(f"Removed capability {deployment.package_id} - did not improve global objective")
        elif monitoring_result['retention_decision'] == 'retain':
            package = self.capability_packages.get(deployment.package_id)
            if package:
                package.status = CapabilityStatus.RETAINED
                logger.info(f"Retained capability {deployment.package_id}")
        
        return monitoring_result
    
    async def run_full_cycle(self, model_id: str, provider: str,
                            interaction_data: List[Dict[str, Any]],
                            task_names: List[str],
                            failure_cases: List[Dict[str, Any]],
                            deployment_strategy: str = 'gradual') -> Dict[str, Any]:
        """Run the complete distillation cycle"""
        
        run_id = self._generate_id("run")
        self.active_runs.add(run_id)
        
        logger.info(f"Starting distillation cycle {run_id} for {model_id}")
        
        try:
            # Steps 1-2: Observe and benchmark
            model = await self.observe_and_benchmark(
                model_id, provider, interaction_data, task_names
            )
            
            results = {'model_id': model_id, 'steps': {}}
            
            # Get best benchmark for extraction
            best_benchmark = None
            best_score = 0
            for task_name in task_names:
                if task_name in model.benchmark_scores:
                    score = model.benchmark_scores[task_name]
                    if score > best_score:
                        best_score = score
                        # Find the benchmark record
                        for b in self.benchmarker.benchmark_history:
                            if b.model_id == model_id and b.task_name == task_name:
                                best_benchmark = b
                                break
            
            if not best_benchmark:
                logger.warning(f"No successful benchmarks for {model_id}")
                return {'error': 'No successful benchmarks'}
            
            # Steps 3-4: Extract and control
            package = await self.extract_and_control(best_benchmark, model, failure_cases)
            
            if not package:
                return {'error': 'No behaviors extracted'}
            
            results['steps']['extracted'] = {
                'package_id': package.package_id,
                'behaviors': len(package.behaviors),
                'controls': len(package.controls)
            }
            
            # Steps 5-6: Validate and deploy
            deployment = await self.validate_and_deploy(package, deployment_strategy)
            
            if not deployment:
                results['steps']['deployed'] = {'status': 'failed_validation'}
                return results
            
            results['steps']['deployed'] = {
                'deployment_id': deployment.deployment_id,
                'rollout_percentage': deployment.rollout_percentage
            }
            
            # Steps 7-8: Monitor and retain
            monitoring = await self.monitor_and_retain(deployment)
            
            results['steps']['monitored'] = {
                'global_impact': monitoring['global_impact'],
                'decision': monitoring['retention_decision']
            }
            
            results['status'] = 'completed'
            return results
            
        finally:
            self.active_runs.discard(run_id)
    
    async def run_continuous_distillation(self, models_to_observe: List[Dict[str, Any]],
                                         check_interval_minutes: int = 60):
        """Run continuous distillation loop"""
        self.is_running = True
        
        while self.is_running:
            for model_spec in models_to_observe:
                if not self.is_running:
                    break
                
                try:
                    await self.run_full_cycle(
                        model_id=model_spec['model_id'],
                        provider=model_spec['provider'],
                        interaction_data=model_spec.get('interaction_data', []),
                        task_names=model_spec.get('task_names', []),
                        failure_cases=model_spec.get('failure_cases', []),
                        deployment_strategy=model_spec.get('strategy', 'gradual')
                    )
                except Exception as e:
                    logger.error(f"Error in distillation cycle for {model_spec['model_id']}: {e}")
            
            await asyncio.sleep(check_interval_minutes * 60)
    
    def stop(self):
        """Stop continuous distillation"""
        self.is_running = False
        logger.info("CapabilityDistillationSystem stopping")
    
    def get_system_report(self) -> Dict[str, Any]:
        """Generate comprehensive system report"""
        return {
            'observer': self.observer.get_observation_report(),
            'benchmarker': {
                'total_benchmarks': len(self.benchmarker.benchmark_history),
                'leaderboard': self.benchmarker.get_leaderboard()
            },
            'extractor': {
                'total_behaviors': len(self.extractor.extracted_behaviors),
                'by_category': {
                    cat: len(self.extractor.get_behaviors_by_category(cat))
                    for cat in set(b.task_category for b in self.extractor.extracted_behaviors.values())
                }
            },
            'inverter': {
                'total_controls': len(self.inverter.controls)
            },
            'sandbox': self.sandbox.get_validation_report(),
            'deployer': {
                'active_deployments': len([d for d in self.deployer.deployed_packages.values() 
                                         if d.status == 'active']),
                'total_deployments': len(self.deployer.deployment_history)
            },
            'monitor': self.monitor.get_monitoring_summary(),
            'packages': {
                'total': len(self.capability_packages),
                'by_status': {
                    status.value: len([p for p in self.capability_packages.values() 
                                     if p.status == status])
                    for status in CapabilityStatus
                }
            }
        }
    
    def _generate_id(self, prefix: str) -> str:
        """Generate unique ID"""
        hash_input = f"{prefix}_{datetime.utcnow().timestamp()}"
        return hashlib.md5(hash_input.encode()).hexdigest()[:16]


# Convenience function for quick setup
def create_distillation_system(sandbox_path: Optional[str] = None,
                              global_objective_fn: Optional[Callable] = None) -> CapabilityDistillationSystem:
    """Create and configure a capability distillation system"""
    
    config = {'sandbox_path': sandbox_path} if sandbox_path else {}
    system = CapabilityDistillationSystem(config)
    
    if global_objective_fn:
        system.set_global_objective(global_objective_fn)
    
    return system
