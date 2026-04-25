"""
AADS Recursive Self-Improvement Engine

The system measures its own performance component by component. When it
identifies its weakest link, it autonomously generates an improved version,
validates it, and replaces the old component — without human instruction.

Self-Improvement Loop (runs weekly):
1. BENCHMARK ALL COMPONENTS - Compute benchmark metrics over trailing 30 days
2. IDENTIFY WEAKEST LINK - Component with largest negative gap from threshold
3. GENERATE IMPROVED VERSION - Research failures, generate improvement
4. VALIDATE IMPROVEMENT - Shadow mode testing for 5 trading days
5. DEPLOY WITH ROLLBACK GUARD - Blue-green deployment with auto-rollback
6. LOG AND LEARN - Build model of "what kinds of improvements work"
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Callable, Tuple
from datetime import datetime, timedelta
from enum import Enum
import numpy as np
import logging
import json
from pathlib import Path
import uuid

logger = logging.getLogger(__name__)


class ComponentStatus(Enum):
    """Status of a system component"""
    ACTIVE = "active"
    SHADOW = "shadow"           # Running in shadow mode
    DEPRECATED = "deprecated"
    FAILED = "failed"
    IMPROVING = "improving"


class ImprovementStatus(Enum):
    """Status of an improvement cycle"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    VALIDATING = "validating"
    DEPLOYING = "deploying"
    COMPLETED = "completed"
    ROLLED_BACK = "rolled_back"
    FAILED = "failed"


@dataclass
class ComponentMetrics:
    """Performance metrics for a component"""
    component_name: str
    benchmark_name: str
    threshold: float
    current_value: float
    trailing_30d_values: List[float] = field(default_factory=list)
    
    @property
    def gap_from_threshold(self) -> float:
        """Negative gap means below threshold"""
        return self.current_value - self.threshold
    
    @property
    def is_below_threshold(self) -> bool:
        return self.current_value < self.threshold
    
    @property
    def trend(self) -> str:
        """Calculate trend direction"""
        if len(self.trailing_30d_values) < 7:
            return "insufficient_data"
        
        recent = np.mean(self.trailing_30d_values[-7:])
        older = np.mean(self.trailing_30d_values[:7])
        
        if recent > older * 1.05:
            return "improving"
        elif recent < older * 0.95:
            return "declining"
        else:
            return "stable"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'component_name': self.component_name,
            'benchmark_name': self.benchmark_name,
            'threshold': self.threshold,
            'current_value': self.current_value,
            'gap_from_threshold': self.gap_from_threshold,
            'is_below_threshold': self.is_below_threshold,
            'trend': self.trend
        }


@dataclass
class ImprovementCycle:
    """Record of a single improvement cycle"""
    cycle_id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    component_name: str = ""
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    
    # Problem identification
    initial_metric_value: float = 0.0
    threshold: float = 0.0
    failure_modes: List[str] = field(default_factory=list)
    
    # Improvement details
    improvement_type: str = ""  # "parameter_tuning", "algorithm_change", "architecture_change"
    changes_made: List[str] = field(default_factory=list)
    
    # Validation
    shadow_mode_days: int = 5
    shadow_mode_results: Dict[str, float] = field(default_factory=dict)
    validation_passed: bool = False
    
    # Deployment
    status: ImprovementStatus = ImprovementStatus.PENDING
    final_metric_value: float = 0.0
    improvement_pct: float = 0.0
    
    # Rollback info
    rollback_triggered: bool = False
    rollback_reason: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'cycle_id': self.cycle_id,
            'component_name': self.component_name,
            'started_at': self.started_at.isoformat(),
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'initial_metric_value': self.initial_metric_value,
            'threshold': self.threshold,
            'failure_modes': self.failure_modes,
            'improvement_type': self.improvement_type,
            'changes_made': self.changes_made,
            'validation_passed': self.validation_passed,
            'status': self.status.value,
            'final_metric_value': self.final_metric_value,
            'improvement_pct': self.improvement_pct,
            'rollback_triggered': self.rollback_triggered
        }


@dataclass
class ComponentDefinition:
    """Definition of a system component for self-improvement"""
    name: str
    benchmark_name: str
    threshold: float
    measure_fn: Optional[Callable[[], float]] = None
    improve_fn: Optional[Callable[[List[str]], Any]] = None
    description: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'benchmark_name': self.benchmark_name,
            'threshold': self.threshold,
            'description': self.description
        }


class ComponentRegistry:
    """
    Registry of all system components that can be self-improved.
    
    Each component has:
    - A benchmark metric
    - A threshold for acceptable performance
    - Functions to measure and improve
    """
    
    # Default component definitions
    DEFAULT_COMPONENTS = {
        "research_agent": {
            "benchmark": "hypothesis_quality_score",
            "threshold": 0.70,
            "description": "Quality of generated alpha hypotheses"
        },
        "backtest_engine": {
            "benchmark": "oos_prediction_accuracy",
            "threshold": 0.65,
            "description": "Out-of-sample prediction accuracy"
        },
        "risk_model": {
            "benchmark": "portfolio_vol_tracking",
            "threshold": 0.90,
            "description": "Accuracy of volatility predictions"
        },
        "execution_algo": {
            "benchmark": "slippage_vs_estimate_bps",
            "threshold": 5.0,
            "description": "Actual vs estimated slippage (lower is better)"
        },
        "sentiment_model": {
            "benchmark": "direction_accuracy_1d",
            "threshold": 0.55,
            "description": "1-day direction prediction accuracy"
        },
        "clip_vision_model": {
            "benchmark": "visual_signal_precision",
            "threshold": 0.60,
            "description": "Precision of visual signal classification"
        },
        "causal_model": {
            "benchmark": "counterfactual_accuracy",
            "threshold": 0.65,
            "description": "Accuracy of causal counterfactual predictions"
        },
        "swarm_consensus": {
            "benchmark": "consensus_signal_accuracy",
            "threshold": 0.58,
            "description": "Accuracy of swarm consensus signals"
        },
        "evolution_engine": {
            "benchmark": "fitness_improvement_rate",
            "threshold": 0.02,
            "description": "Rate of fitness improvement per generation"
        },
        "decision_engine": {
            "benchmark": "decision_quality_score",
            "threshold": 0.70,
            "description": "Quality of trade decisions"
        }
    }
    
    def __init__(self):
        self.components: Dict[str, ComponentDefinition] = {}
        self.metrics_history: Dict[str, List[Tuple[datetime, float]]] = {}
        
        # Initialize default components
        self._initialize_defaults()
        
        logger.info(f"ComponentRegistry initialized with {len(self.components)} components")
    
    def _initialize_defaults(self) -> None:
        """Initialize default component definitions"""
        for name, config in self.DEFAULT_COMPONENTS.items():
            self.register_component(ComponentDefinition(
                name=name,
                benchmark_name=config["benchmark"],
                threshold=config["threshold"],
                description=config["description"]
            ))
    
    def register_component(self, component: ComponentDefinition) -> None:
        """Register a component for self-improvement"""
        self.components[component.name] = component
        self.metrics_history[component.name] = []
    
    def record_metric(self, component_name: str, value: float) -> None:
        """Record a metric value for a component"""
        if component_name in self.metrics_history:
            self.metrics_history[component_name].append((datetime.now(), value))
            
            # Keep only last 90 days
            cutoff = datetime.now() - timedelta(days=90)
            self.metrics_history[component_name] = [
                (t, v) for t, v in self.metrics_history[component_name]
                if t > cutoff
            ]
    
    def get_component_metrics(self, component_name: str) -> Optional[ComponentMetrics]:
        """Get current metrics for a component"""
        if component_name not in self.components:
            return None
        
        component = self.components[component_name]
        history = self.metrics_history.get(component_name, [])
        
        # Get trailing 30 days
        cutoff = datetime.now() - timedelta(days=30)
        recent_values = [v for t, v in history if t > cutoff]
        
        current_value = recent_values[-1] if recent_values else 0.0
        
        return ComponentMetrics(
            component_name=component_name,
            benchmark_name=component.benchmark_name,
            threshold=component.threshold,
            current_value=current_value,
            trailing_30d_values=recent_values
        )
    
    def get_all_metrics(self) -> List[ComponentMetrics]:
        """Get metrics for all components"""
        return [
            self.get_component_metrics(name)
            for name in self.components
            if self.get_component_metrics(name) is not None
        ]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'components': {name: comp.to_dict() for name, comp in self.components.items()},
            'metrics_count': {name: len(hist) for name, hist in self.metrics_history.items()}
        }


class SelfImprovementEngine:
    """
    Recursive Self-Improvement Engine.
    
    Autonomously identifies weak components, generates improvements,
    validates them, and deploys with rollback guards.
    """
    
    def __init__(
        self,
        registry: Optional[ComponentRegistry] = None,
        improvement_generator: Optional[Callable] = None,
        save_directory: str = "self_improvement_logs"
    ):
        self.registry = registry or ComponentRegistry()
        self.improvement_generator = improvement_generator
        self.save_dir = Path(save_directory)
        self.save_dir.mkdir(parents=True, exist_ok=True)
        
        # Improvement tracking
        self.improvement_cycles: List[ImprovementCycle] = []
        self.active_cycle: Optional[ImprovementCycle] = None
        
        # Learning from improvements
        self.improvement_patterns: Dict[str, List[Dict]] = {}
        
        # Shadow mode tracking
        self.shadow_components: Dict[str, Any] = {}
        
        logger.info("SelfImprovementEngine initialized")
    
    def run_weekly_improvement_cycle(self) -> Optional[ImprovementCycle]:
        """
        Run the complete weekly self-improvement cycle.
        
        Steps:
        1. Benchmark all components
        2. Identify weakest link
        3. Generate improved version
        4. Validate improvement
        5. Deploy with rollback guard
        6. Log and learn
        """
        logger.info("Starting weekly self-improvement cycle")
        
        # Step 1: Benchmark all components
        metrics = self._benchmark_all_components()
        
        # Step 2: Identify weakest link
        weakest = self._identify_weakest_link(metrics)
        
        if weakest is None:
            logger.info("All components above threshold, no improvement needed")
            return None
        
        logger.info(f"Identified weakest component: {weakest.component_name} "
                   f"(gap: {weakest.gap_from_threshold:.3f})")
        
        # Step 3: Generate improved version
        cycle = self._start_improvement_cycle(weakest)
        self.active_cycle = cycle
        
        # Analyze failure modes
        failure_modes = self._analyze_failure_modes(weakest.component_name)
        cycle.failure_modes = failure_modes
        
        # Generate improvement
        improvement = self._generate_improvement(weakest.component_name, failure_modes)
        cycle.improvement_type = improvement.get('type', 'unknown')
        cycle.changes_made = improvement.get('changes', [])
        
        # Step 4: Validate improvement (would run async in production)
        validation_result = self._validate_improvement(cycle)
        cycle.validation_passed = validation_result['passed']
        cycle.shadow_mode_results = validation_result['metrics']
        
        if not cycle.validation_passed:
            cycle.status = ImprovementStatus.FAILED
            logger.warning(f"Improvement validation failed for {weakest.component_name}")
            self._save_cycle(cycle)
            return cycle
        
        # Step 5: Deploy with rollback guard
        deployment_result = self._deploy_with_rollback_guard(cycle)
        
        if deployment_result['success']:
            cycle.status = ImprovementStatus.COMPLETED
            cycle.final_metric_value = deployment_result['final_metric']
            cycle.improvement_pct = (
                (cycle.final_metric_value - cycle.initial_metric_value) /
                abs(cycle.initial_metric_value) if cycle.initial_metric_value != 0 else 0
            )
        else:
            cycle.status = ImprovementStatus.ROLLED_BACK
            cycle.rollback_triggered = True
            cycle.rollback_reason = deployment_result.get('reason', 'Unknown')
        
        cycle.completed_at = datetime.now()
        
        # Step 6: Log and learn
        self._log_and_learn(cycle)
        self._save_cycle(cycle)
        
        self.improvement_cycles.append(cycle)
        self.active_cycle = None
        
        return cycle
    
    def _benchmark_all_components(self) -> List[ComponentMetrics]:
        """Step 1: Benchmark all components"""
        metrics = []
        
        for component_name in self.registry.components:
            # Simulate metric measurement (in production, call actual measure functions)
            simulated_value = self._simulate_metric_measurement(component_name)
            self.registry.record_metric(component_name, simulated_value)
            
            component_metrics = self.registry.get_component_metrics(component_name)
            if component_metrics:
                metrics.append(component_metrics)
        
        logger.info(f"Benchmarked {len(metrics)} components")
        return metrics
    
    def _simulate_metric_measurement(self, component_name: str) -> float:
        """Simulate metric measurement (placeholder)"""
        component = self.registry.components.get(component_name)
        if not component:
            return 0.0
        
        # Simulate around threshold with some variance
        base = component.threshold
        noise = np.random.normal(0, base * 0.15)
        return max(0, base + noise)
    
    def _identify_weakest_link(self, metrics: List[ComponentMetrics]) -> Optional[ComponentMetrics]:
        """Step 2: Identify component with largest negative gap from threshold"""
        below_threshold = [m for m in metrics if m.is_below_threshold]
        
        if not below_threshold:
            return None
        
        # Sort by gap (most negative first)
        below_threshold.sort(key=lambda m: m.gap_from_threshold)
        
        return below_threshold[0]
    
    def _start_improvement_cycle(self, metrics: ComponentMetrics) -> ImprovementCycle:
        """Start a new improvement cycle"""
        return ImprovementCycle(
            component_name=metrics.component_name,
            initial_metric_value=metrics.current_value,
            threshold=metrics.threshold,
            status=ImprovementStatus.IN_PROGRESS
        )
    
    def _analyze_failure_modes(self, component_name: str) -> List[str]:
        """Analyze failure modes from logs"""
        # In production, analyze actual logs and error patterns
        failure_modes = [
            f"Suboptimal parameter configuration for {component_name}",
            f"Edge cases not handled in {component_name}",
            f"Data quality issues affecting {component_name}"
        ]
        return failure_modes
    
    def _generate_improvement(
        self,
        component_name: str,
        failure_modes: List[str]
    ) -> Dict[str, Any]:
        """Step 3: Generate improved version"""
        if self.improvement_generator:
            return self.improvement_generator(component_name, failure_modes)
        
        # Default improvement generation
        improvement_types = [
            "parameter_tuning",
            "algorithm_optimization",
            "feature_engineering",
            "ensemble_addition"
        ]
        
        improvement_type = np.random.choice(improvement_types)
        
        changes = {
            "parameter_tuning": [
                "Adjusted learning rate by 10%",
                "Increased regularization strength",
                "Modified threshold parameters"
            ],
            "algorithm_optimization": [
                "Replaced linear model with gradient boosting",
                "Added feature selection step",
                "Implemented early stopping"
            ],
            "feature_engineering": [
                "Added momentum features",
                "Included cross-asset correlations",
                "Added regime indicators"
            ],
            "ensemble_addition": [
                "Added secondary model for edge cases",
                "Implemented model averaging",
                "Added confidence weighting"
            ]
        }
        
        return {
            'type': improvement_type,
            'changes': changes.get(improvement_type, [])
        }
    
    def _validate_improvement(self, cycle: ImprovementCycle) -> Dict[str, Any]:
        """Step 4: Validate improvement in shadow mode"""
        cycle.status = ImprovementStatus.VALIDATING
        
        # Simulate shadow mode validation
        # In production, run actual shadow mode for 5 trading days
        
        # Simulate improvement (5% improvement on average)
        improvement_factor = np.random.uniform(0.95, 1.15)
        shadow_metric = cycle.initial_metric_value * improvement_factor
        
        # Check if improvement meets criteria
        improvement_pct = (shadow_metric - cycle.initial_metric_value) / abs(cycle.initial_metric_value)
        passed = improvement_pct >= 0.05  # Require 5% improvement
        
        # Check for regressions (simplified)
        no_regression = np.random.random() > 0.1  # 10% chance of regression
        
        return {
            'passed': passed and no_regression,
            'metrics': {
                'shadow_metric': shadow_metric,
                'improvement_pct': improvement_pct,
                'no_regression': no_regression
            }
        }
    
    def _deploy_with_rollback_guard(self, cycle: ImprovementCycle) -> Dict[str, Any]:
        """Step 5: Deploy with blue-green deployment and rollback guard"""
        cycle.status = ImprovementStatus.DEPLOYING
        
        # Simulate deployment
        # In production:
        # 1. Deploy new version to handle 10% of decisions
        # 2. Monitor for 3 days
        # 3. If underperforms by 2σ, auto-rollback
        # 4. If matches or beats, full traffic shift
        
        # Simulate deployment outcome
        deployment_success = np.random.random() > 0.15  # 85% success rate
        
        if deployment_success:
            # Simulate final metric after deployment
            final_metric = cycle.shadow_mode_results.get('shadow_metric', cycle.initial_metric_value)
            return {
                'success': True,
                'final_metric': final_metric
            }
        else:
            return {
                'success': False,
                'reason': "New version underperformed by 2σ over 3 days"
            }
    
    def _log_and_learn(self, cycle: ImprovementCycle) -> None:
        """Step 6: Log improvement and learn from it"""
        # Record what worked
        if cycle.status == ImprovementStatus.COMPLETED:
            pattern = {
                'component': cycle.component_name,
                'improvement_type': cycle.improvement_type,
                'changes': cycle.changes_made,
                'improvement_pct': cycle.improvement_pct,
                'timestamp': datetime.now().isoformat()
            }
            
            if cycle.component_name not in self.improvement_patterns:
                self.improvement_patterns[cycle.component_name] = []
            
            self.improvement_patterns[cycle.component_name].append(pattern)
            
            logger.info(f"Learned from successful improvement: {cycle.improvement_type} "
                       f"achieved {cycle.improvement_pct:.1%} improvement")
        else:
            logger.info(f"Improvement cycle failed/rolled back: {cycle.rollback_reason}")
    
    def _save_cycle(self, cycle: ImprovementCycle) -> None:
        """Save improvement cycle to disk"""
        filepath = self.save_dir / f"cycle_{cycle.cycle_id}.json"
        with open(filepath, 'w') as f:
            json.dump(cycle.to_dict(), f, indent=2)
    
    def get_improvement_history(self) -> List[Dict[str, Any]]:
        """Get history of all improvement cycles"""
        return [cycle.to_dict() for cycle in self.improvement_cycles]
    
    def get_component_health_report(self) -> Dict[str, Any]:
        """Generate health report for all components"""
        metrics = self.registry.get_all_metrics()
        
        healthy = [m for m in metrics if not m.is_below_threshold]
        unhealthy = [m for m in metrics if m.is_below_threshold]
        
        return {
            'total_components': len(metrics),
            'healthy_components': len(healthy),
            'unhealthy_components': len(unhealthy),
            'health_rate': len(healthy) / len(metrics) if metrics else 0,
            'components': {
                m.component_name: {
                    'status': 'healthy' if not m.is_below_threshold else 'unhealthy',
                    'current_value': m.current_value,
                    'threshold': m.threshold,
                    'gap': m.gap_from_threshold,
                    'trend': m.trend
                }
                for m in metrics
            },
            'improvement_cycles_completed': len(self.improvement_cycles),
            'successful_improvements': sum(
                1 for c in self.improvement_cycles
                if c.status == ImprovementStatus.COMPLETED
            )
        }
    
    def get_learned_patterns(self) -> Dict[str, Any]:
        """Get patterns learned from successful improvements"""
        return {
            'patterns_by_component': self.improvement_patterns,
            'total_patterns': sum(len(p) for p in self.improvement_patterns.values()),
            'most_effective_types': self._get_most_effective_improvement_types()
        }
    
    def _get_most_effective_improvement_types(self) -> List[Dict[str, Any]]:
        """Analyze which improvement types are most effective"""
        type_stats: Dict[str, List[float]] = {}
        
        for patterns in self.improvement_patterns.values():
            for pattern in patterns:
                imp_type = pattern.get('improvement_type', 'unknown')
                imp_pct = pattern.get('improvement_pct', 0)
                
                if imp_type not in type_stats:
                    type_stats[imp_type] = []
                type_stats[imp_type].append(imp_pct)
        
        results = []
        for imp_type, improvements in type_stats.items():
            results.append({
                'type': imp_type,
                'count': len(improvements),
                'avg_improvement': np.mean(improvements) if improvements else 0,
                'max_improvement': max(improvements) if improvements else 0
            })
        
        results.sort(key=lambda x: x['avg_improvement'], reverse=True)
        return results
