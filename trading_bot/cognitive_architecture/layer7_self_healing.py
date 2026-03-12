"""
Layer 7: Self-Healing & Optimization Supervisor
Monitors system health and performs automatic repairs and optimizations.
"""

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional
from enum import Enum
from datetime import datetime
import logging
import psutil
import time
from typing import Set

logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """System health status levels."""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    FAILED = "failed"


class OptimizationMode(Enum):
    """Optimization modes."""
    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"


@dataclass
class DiagnosticResult:
    """Result of a diagnostic check."""
    component: str
    status: HealthStatus
    message: str
    metrics: Dict[str, float] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class RepairAction:
    """Repair action to be taken."""
    component: str
    action: str
    priority: int
    estimated_impact: float
    executed: bool = False


class DiagnosticsMonitor:
    """
    Monitors system health and performance.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.thresholds = {
            'cpu_warning': 70.0,
            'cpu_critical': 90.0,
            'memory_warning': 70.0,
            'memory_critical': 90.0,
            'latency_warning': 100.0,  # ms
            'latency_critical': 500.0
        }
        self.history: List[DiagnosticResult] = []
        logger.info("DiagnosticsMonitor initialized")
    
    def run_diagnostics(self) -> List[DiagnosticResult]:
        """Run all diagnostic checks."""
        results = []
        
        # CPU check
        results.append(self._check_cpu())
        
        # Memory check
        results.append(self._check_memory())
        
        # Latency check
        results.append(self._check_latency())
        
        # Store in history
        self.history.extend(results)
        if len(self.history) > 1000:
            self.history = self.history[-1000:]
        
        return results
    
    def _check_cpu(self) -> DiagnosticResult:
        """Check CPU usage."""
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
        except Exception:
            cpu_percent = 0.0
        
        if cpu_percent >= self.thresholds['cpu_critical']:
            status = HealthStatus.CRITICAL
        elif cpu_percent >= self.thresholds['cpu_warning']:
            status = HealthStatus.WARNING
        else:
            status = HealthStatus.HEALTHY
        
        return DiagnosticResult(
            component='cpu',
            status=status,
            message=f"CPU usage: {cpu_percent:.1f}%",
            metrics={'usage': cpu_percent}
        )
    
    def _check_memory(self) -> DiagnosticResult:
        """Check memory usage."""
        try:
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
        except Exception:
            memory_percent = 0.0
        
        if memory_percent >= self.thresholds['memory_critical']:
            status = HealthStatus.CRITICAL
        elif memory_percent >= self.thresholds['memory_warning']:
            status = HealthStatus.WARNING
        else:
            status = HealthStatus.HEALTHY
        
        return DiagnosticResult(
            component='memory',
            status=status,
            message=f"Memory usage: {memory_percent:.1f}%",
            metrics={'usage': memory_percent}
        )
    
    def _check_latency(self) -> DiagnosticResult:
        """Check system latency."""
        start = time.perf_counter()
        # Simulate some work
        _ = sum(range(10000))
        latency_ms = (time.perf_counter() - start) * 1000
        
        if latency_ms >= self.thresholds['latency_critical']:
            status = HealthStatus.CRITICAL
        elif latency_ms >= self.thresholds['latency_warning']:
            status = HealthStatus.WARNING
        else:
            status = HealthStatus.HEALTHY
        
        return DiagnosticResult(
            component='latency',
            status=status,
            message=f"System latency: {latency_ms:.2f}ms",
            metrics={'latency_ms': latency_ms}
        )
    
    def get_overall_health(self) -> HealthStatus:
        """Get overall system health."""
        if not self.history:
            return HealthStatus.HEALTHY
        
        recent = self.history[-10:]
        statuses = [r.status for r in recent]
        
        if HealthStatus.FAILED in statuses:
            return HealthStatus.FAILED
        elif HealthStatus.CRITICAL in statuses:
            return HealthStatus.CRITICAL
        elif HealthStatus.WARNING in statuses:
            return HealthStatus.WARNING
        return HealthStatus.HEALTHY


class AutoRepairEngine:
    """
    Automatically repairs detected issues.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.repair_actions: List[RepairAction] = []
        self.repair_handlers: Dict[str, Callable] = {}
        logger.info("AutoRepairEngine initialized")
    
    def analyze_issues(self, diagnostics: List[DiagnosticResult]) -> List[RepairAction]:
        """Analyze diagnostics and generate repair actions."""
        actions = []
        
        for result in diagnostics:
            if result.status in [HealthStatus.CRITICAL, HealthStatus.FAILED]:
                action = self._generate_repair_action(result, priority=1)
                if action:
                    actions.append(action)
            elif result.status == HealthStatus.WARNING:
                action = self._generate_repair_action(result, priority=2)
                if action:
                    actions.append(action)
        
        self.repair_actions = actions
        return actions
    
    def _generate_repair_action(self, result: DiagnosticResult, priority: int) -> Optional[RepairAction]:
        """Generate repair action for a diagnostic result."""
        if result.component == 'cpu':
            return RepairAction(
                component='cpu',
                action='reduce_processing_load',
                priority=priority,
                estimated_impact=0.3
            )
        elif result.component == 'memory':
            return RepairAction(
                component='memory',
                action='clear_caches',
                priority=priority,
                estimated_impact=0.4
            )
        elif result.component == 'latency':
            return RepairAction(
                component='latency',
                action='optimize_processing',
                priority=priority,
                estimated_impact=0.2
            )
        return None
    
    def execute_repairs(self, actions: List[RepairAction]) -> List[RepairAction]:
        """Execute repair actions."""
        executed = []
        
        for action in sorted(actions, key=lambda a: a.priority):
            try:
                handler = self.repair_handlers.get(action.action)
                if handler:
                    handler()
                action.executed = True
                executed.append(action)
                logger.info(f"Executed repair: {action.action} for {action.component}")
            except Exception as e:
                logger.error(f"Repair failed: {action.action} - {e}")
        
        return executed


class OptimizationManager:
    """
    Manages system optimizations.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.mode = OptimizationMode.MODERATE
        self.parameters: Dict[str, float] = {
            'batch_size': 32,
            'cache_size': 1000,
            'update_frequency': 1.0
        }
        logger.info("OptimizationManager initialized")
    
    def set_mode(self, mode: OptimizationMode):
        """Set optimization mode."""
        self.mode = mode
        self._apply_mode_settings()
    
    def _apply_mode_settings(self):
        """Apply settings based on mode."""
        if self.mode == OptimizationMode.CONSERVATIVE:
            self.parameters['batch_size'] = 16
            self.parameters['cache_size'] = 500
            self.parameters['update_frequency'] = 2.0
        elif self.mode == OptimizationMode.MODERATE:
            self.parameters['batch_size'] = 32
            self.parameters['cache_size'] = 1000
            self.parameters['update_frequency'] = 1.0
        elif self.mode == OptimizationMode.AGGRESSIVE:
            self.parameters['batch_size'] = 64
            self.parameters['cache_size'] = 2000
            self.parameters['update_frequency'] = 0.5
    
    def optimize(self, metrics: Dict[str, float]) -> Dict[str, Any]:
        """Optimize parameters based on metrics."""
        changes = {}
        
        # Adjust batch size based on latency
        if metrics.get('latency_ms', 0) > 100:
            new_batch = max(self.parameters['batch_size'] * 0.8, 8)
            changes['batch_size'] = new_batch
            self.parameters['batch_size'] = new_batch
        
        # Adjust cache based on memory
        if metrics.get('memory_usage', 0) > 80:
            new_cache = max(self.parameters['cache_size'] * 0.7, 100)
            changes['cache_size'] = new_cache
            self.parameters['cache_size'] = new_cache
        
        return changes


class SafetyManager:
    """
    Manages safety constraints and limits.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.limits = {
            'max_position_size': 0.02,  # 2% of portfolio
            'max_daily_loss': 0.05,     # 5% daily loss limit
            'max_drawdown': 0.20,       # 20% max drawdown
            'max_trades_per_day': 50
        }
        self.violations: List[Dict[str, Any]] = []
        logger.info("SafetyManager initialized")
    
    def check_safety(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Check if action is within safety limits."""
        violations = []
        
        position_size = action.get('position_size', 0)
        if position_size > self.limits['max_position_size']:
            violations.append({
                'limit': 'max_position_size',
                'value': position_size,
                'max': self.limits['max_position_size']
            })
        
        return {
            'safe': len(violations) == 0,
            'violations': violations,
            'adjusted_action': self._adjust_action(action, violations)
        }
    
    def _adjust_action(self, action: Dict[str, Any], violations: List[Dict]) -> Dict[str, Any]:
        """Adjust action to comply with safety limits."""
        adjusted = action.copy()
        
        for violation in violations:
            if violation['limit'] == 'max_position_size':
                adjusted['position_size'] = self.limits['max_position_size']
        
        return adjusted


class PerformanceEvaluator:
    """
    Evaluates system and trading performance.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.metrics_history: List[Dict[str, float]] = []
        logger.info("PerformanceEvaluator initialized")
    
    def evaluate(self, metrics: Dict[str, float]) -> Dict[str, Any]:
        """Evaluate performance metrics."""
        self.metrics_history.append(metrics)
        if len(self.metrics_history) > 1000:
            self.metrics_history = self.metrics_history[-1000:]
        
        # Calculate performance score
        score = self._calculate_score(metrics)
        
        return {
            'score': score,
            'metrics': metrics,
            'trend': self._calculate_trend(),
            'recommendations': self._generate_recommendations(score)
        }
    
    def _calculate_score(self, metrics: Dict[str, float]) -> float:
        """Calculate overall performance score."""
        weights = {
            'win_rate': 0.3,
            'profit_factor': 0.3,
            'sharpe_ratio': 0.2,
            'max_drawdown': 0.2
        }
        
        score = 0.0
        for metric, weight in weights.items():
            value = metrics.get(metric, 0.5)
            # Normalize to 0-1 range
            if metric == 'max_drawdown':
                normalized = 1.0 - min(value, 1.0)
            else:
                normalized = min(value, 1.0)
            score += normalized * weight
        
        return score
    
    def _calculate_trend(self) -> str:
        """Calculate performance trend."""
        if len(self.metrics_history) < 2:
            return 'stable'
        
        recent = self.metrics_history[-10:]
        scores = [self._calculate_score(m) for m in recent]
        
        if len(scores) >= 2:
            if scores[-1] > scores[0] * 1.1:
                return 'improving'
            elif scores[-1] < scores[0] * 0.9:
                return 'declining'
        
        return 'stable'
    
    def _generate_recommendations(self, score: float) -> List[str]:
        """Generate recommendations based on score."""
        recommendations = []
        
        if score < 0.3:
            recommendations.append("Consider reducing position sizes")
            recommendations.append("Review and update strategy parameters")
        elif score < 0.5:
            recommendations.append("Monitor closely for further decline")
        elif score > 0.7:
            recommendations.append("Performance is good, maintain current approach")
        
        return recommendations


class SelfHealingSupervisor:
    """
    Self-Healing Supervisor - Layer 7 of Cognitive Architecture.
    Coordinates all self-healing and optimization components.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.diagnostics = DiagnosticsMonitor(config)
        self.repair_engine = AutoRepairEngine(config)
        self.optimizer = OptimizationManager(config)
        self.safety = SafetyManager(config)
        self.evaluator = PerformanceEvaluator(config)
        logger.info("SelfHealingSupervisor initialized")
    
    def run_cycle(self) -> Dict[str, Any]:
        """Run a complete self-healing cycle."""
        # Run diagnostics
        diagnostic_results = self.diagnostics.run_diagnostics()
        
        # Analyze and repair issues
        repair_actions = self.repair_engine.analyze_issues(diagnostic_results)
        executed_repairs = self.repair_engine.execute_repairs(repair_actions)
        
        # Get metrics for optimization
        metrics = {
            'latency_ms': next((r.metrics.get('latency_ms', 0) for r in diagnostic_results if r.component == 'latency'), 0),
            'memory_usage': next((r.metrics.get('usage', 0) for r in diagnostic_results if r.component == 'memory'), 0),
            'cpu_usage': next((r.metrics.get('usage', 0) for r in diagnostic_results if r.component == 'cpu'), 0)
        }
        
        # Optimize
        optimizations = self.optimizer.optimize(metrics)
        
        return {
            'health': self.diagnostics.get_overall_health().value,
            'diagnostics': [{'component': r.component, 'status': r.status.value} for r in diagnostic_results],
            'repairs_executed': len(executed_repairs),
            'optimizations': optimizations
        }
    
    def check_action_safety(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Check if an action is safe to execute."""
        return self.safety.check_safety(action)
    
    def get_status(self) -> Dict[str, Any]:
        """Get overall supervisor status."""
        return {
            'health': self.diagnostics.get_overall_health().value,
            'optimization_mode': self.optimizer.mode.value,
            'parameters': self.optimizer.parameters
        }
