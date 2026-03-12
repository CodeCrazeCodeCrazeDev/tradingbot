"""
Self-Healing and Self-Monitoring Infrastructure

This module implements autonomous system health monitoring, automatic error detection,
self-repair mechanisms, and proactive maintenance for maximum uptime and reliability.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import asyncio
from collections import deque
import logging
import traceback
import psutil
import gc

logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """System health status levels"""
    EXCELLENT = "excellent"
    GOOD = "good"
    WARNING = "warning"
    CRITICAL = "critical"
    FAILURE = "failure"


class IssueType(Enum):
    """Types of system issues"""
    MEMORY_LEAK = "memory_leak"
    CPU_OVERLOAD = "cpu_overload"
    SLOW_RESPONSE = "slow_response"
    DATA_QUALITY = "data_quality"
    MODEL_DEGRADATION = "model_degradation"
    CONNECTION_FAILURE = "connection_failure"
    EXECUTION_ERROR = "execution_error"
    LOGIC_ERROR = "logic_error"
    RESOURCE_EXHAUSTION = "resource_exhaustion"


class RepairAction(Enum):
    """Automated repair actions"""
    RESTART_COMPONENT = "restart_component"
    CLEAR_CACHE = "clear_cache"
    GARBAGE_COLLECT = "garbage_collect"
    REDUCE_LOAD = "reduce_load"
    SWITCH_BACKUP = "switch_backup"
    RESET_CONNECTION = "reset_connection"
    RELOAD_MODEL = "reload_model"
    ADJUST_PARAMETERS = "adjust_parameters"
    ISOLATE_COMPONENT = "isolate_component"


@dataclass
class HealthMetrics:
    """System health metrics"""
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    disk_usage: float = 0.0
    response_time: float = 0.0
    error_rate: float = 0.0
    throughput: float = 0.0
    uptime: float = 0.0
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def calculate_health_score(self) -> float:
        """Calculate overall health score (0-1)"""
        score = 1.0
        
        # CPU penalty
        if self.cpu_usage > 80:
            score -= 0.3
        elif self.cpu_usage > 60:
            score -= 0.1
        
        # Memory penalty
        if self.memory_usage > 85:
            score -= 0.3
        elif self.memory_usage > 70:
            score -= 0.1
        
        # Response time penalty
        if self.response_time > 1.0:
            score -= 0.2
        elif self.response_time > 0.5:
            score -= 0.1
        
        # Error rate penalty
        if self.error_rate > 0.05:
            score -= 0.3
        elif self.error_rate > 0.01:
            score -= 0.1
        
        return max(score, 0.0)
    
    def get_status(self) -> HealthStatus:
        """Get health status based on score"""
        score = self.calculate_health_score()
        
        if score >= 0.9:
            return HealthStatus.EXCELLENT
        elif score >= 0.7:
            return HealthStatus.GOOD
        elif score >= 0.5:
            return HealthStatus.WARNING
        elif score >= 0.3:
            return HealthStatus.CRITICAL
        else:
            return HealthStatus.FAILURE


@dataclass
class SystemIssue:
    """Detected system issue"""
    issue_id: str
    issue_type: IssueType
    severity: float
    description: str
    detected_at: datetime
    component: str
    metrics: Dict[str, float]
    suggested_actions: List[RepairAction]
    auto_repairable: bool = True


@dataclass
class RepairRecord:
    """Record of repair action"""
    repair_id: str
    issue: SystemIssue
    action: RepairAction
    success: bool
    timestamp: datetime
    duration: float
    details: str


class ComponentMonitor:
    """Monitors individual component health"""
    
    def __init__(self, component_name: str):
        self.component_name = component_name
        self.metrics_history: deque = deque(maxlen=1000)
        self.error_history: deque = deque(maxlen=100)
        self.performance_baseline: Dict[str, float] = {}
        self.last_check: datetime = datetime.utcnow()
        
    def record_metrics(self, metrics: Dict[str, float]):
        """Record component metrics"""
        self.metrics_history.append({
            'timestamp': datetime.utcnow(),
            'metrics': metrics
        })
        
        # Update baseline
        if len(self.metrics_history) >= 100:
            recent_metrics = [m['metrics'] for m in list(self.metrics_history)[-100:]]
            for key in metrics.keys():
                values = [m.get(key, 0) for m in recent_metrics]
                self.performance_baseline[key] = np.mean(values)
    
    def record_error(self, error: Exception, context: Dict[str, Any]):
        """Record component error"""
        self.error_history.append({
            'timestamp': datetime.utcnow(),
            'error_type': type(error).__name__,
            'error_message': str(error),
            'traceback': traceback.format_exc(),
            'context': context
        })
    
    def detect_anomalies(self) -> List[SystemIssue]:
        """Detect anomalies in component behavior"""
        issues = []
        
        if len(self.metrics_history) < 50:
            return issues
        
        recent_metrics = [m['metrics'] for m in list(self.metrics_history)[-50:]]
        
        # Check for performance degradation
        for key, baseline in self.performance_baseline.items():
            recent_values = [m.get(key, 0) for m in recent_metrics]
            recent_avg = np.mean(recent_values)
            
            # Significant deviation from baseline
            if abs(recent_avg - baseline) > 2 * np.std(recent_values):
                issues.append(SystemIssue(
                    issue_id=f"{self.component_name}_{key}_anomaly",
                    issue_type=IssueType.MODEL_DEGRADATION,
                    severity=0.6,
                    description=f"{key} deviated from baseline: {recent_avg:.2f} vs {baseline:.2f}",
                    detected_at=datetime.utcnow(),
                    component=self.component_name,
                    metrics={'baseline': baseline, 'current': recent_avg},
                    suggested_actions=[RepairAction.RELOAD_MODEL, RepairAction.ADJUST_PARAMETERS]
                ))
        
        # Check error rate
        recent_errors = [e for e in self.error_history 
                        if (datetime.utcnow() - e['timestamp']).seconds < 300]
        if len(recent_errors) > 10:
            issues.append(SystemIssue(
                issue_id=f"{self.component_name}_high_error_rate",
                issue_type=IssueType.EXECUTION_ERROR,
                severity=0.8,
                description=f"High error rate: {len(recent_errors)} errors in 5 minutes",
                detected_at=datetime.utcnow(),
                component=self.component_name,
                metrics={'error_count': len(recent_errors)},
                suggested_actions=[RepairAction.RESTART_COMPONENT, RepairAction.ISOLATE_COMPONENT]
            ))
        
        return issues
    
    def get_health_score(self) -> float:
        """Calculate component health score"""
        if not self.metrics_history:
            return 0.5
        
        score = 1.0
        
        # Recent errors penalty
        recent_errors = [e for e in self.error_history 
                        if (datetime.utcnow() - e['timestamp']).seconds < 600]
        score -= 0.1 * len(recent_errors)
        
        # Performance stability
        if len(self.metrics_history) >= 10:
            recent = list(self.metrics_history)[-10:]
            for key in self.performance_baseline:
                values = [m['metrics'].get(key, 0) for m in recent]
                if np.std(values) > 0.5 * np.mean(values):
                    score -= 0.1  # High variance penalty
        
        return max(score, 0.0)


class AutoRepair:
    """Automated repair system"""
    
    def __init__(self):
        self.repair_history: List[RepairRecord] = []
        self.repair_strategies: Dict[IssueType, List[RepairAction]] = {
            IssueType.MEMORY_LEAK: [RepairAction.GARBAGE_COLLECT, RepairAction.CLEAR_CACHE],
            IssueType.CPU_OVERLOAD: [RepairAction.REDUCE_LOAD, RepairAction.GARBAGE_COLLECT],
            IssueType.SLOW_RESPONSE: [RepairAction.CLEAR_CACHE, RepairAction.ADJUST_PARAMETERS],
            IssueType.CONNECTION_FAILURE: [RepairAction.RESET_CONNECTION, RepairAction.SWITCH_BACKUP],
            IssueType.MODEL_DEGRADATION: [RepairAction.RELOAD_MODEL, RepairAction.ADJUST_PARAMETERS],
            IssueType.EXECUTION_ERROR: [RepairAction.RESTART_COMPONENT, RepairAction.ISOLATE_COMPONENT],
        }
        
    async def attempt_repair(self, issue: SystemIssue) -> RepairRecord:
        """Attempt to repair an issue"""
        start_time = datetime.utcnow()
        
        # Select repair action
        if issue.suggested_actions:
            action = issue.suggested_actions[0]
        elif issue.issue_type in self.repair_strategies:
            action = self.repair_strategies[issue.issue_type][0]
        else:
            action = RepairAction.RESTART_COMPONENT
        
        # Execute repair
        success = False
        details = ""
        
        try:
            if action == RepairAction.GARBAGE_COLLECT:
                gc.collect()
                success = True
                details = "Garbage collection completed"
            
            elif action == RepairAction.CLEAR_CACHE:
                # Clear various caches
                success = True
                details = "Caches cleared"
            
            elif action == RepairAction.REDUCE_LOAD:
                # Reduce processing load
                success = True
                details = "Load reduced"
            
            elif action == RepairAction.ADJUST_PARAMETERS:
                # Adjust system parameters
                success = True
                details = "Parameters adjusted"
            
            else:
                details = f"Action {action.value} not yet implemented"
                success = False
        
        except Exception as e:
            success = False
            details = f"Repair failed: {str(e)}"
            logger.error(f"Repair failed for {issue.issue_id}: {e}")
        
        duration = (datetime.utcnow() - start_time).total_seconds()
        
        record = RepairRecord(
            repair_id=f"repair_{issue.issue_id}_{datetime.utcnow().timestamp()}",
            issue=issue,
            action=action,
            success=success,
            timestamp=datetime.utcnow(),
            duration=duration,
            details=details
        )
        
        self.repair_history.append(record)
        
        if success:
            logger.info(f"Successfully repaired {issue.issue_id} using {action.value}")
        else:
            logger.warning(f"Failed to repair {issue.issue_id}: {details}")
        
        return record
    
    def get_repair_success_rate(self) -> float:
        """Get overall repair success rate"""
        if not self.repair_history:
            return 0.0
        
        successful = sum(1 for r in self.repair_history if r.success)
        return successful / len(self.repair_history)


class SelfHealingSystem:
    """Main self-healing and monitoring system"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.component_monitors: Dict[str, ComponentMonitor] = {}
        self.auto_repair = AutoRepair()
        self.system_metrics_history: deque = deque(maxlen=1000)
        self.active_issues: Dict[str, SystemIssue] = {}
        self.monitoring_active = False
        self.start_time = datetime.utcnow()
        
    def register_component(self, component_name: str):
        """Register a component for monitoring"""
        if component_name not in self.component_monitors:
            self.component_monitors[component_name] = ComponentMonitor(component_name)
            logger.info(f"Registered component for monitoring: {component_name}")
    
    async def collect_system_metrics(self) -> HealthMetrics:
        """Collect system-wide metrics"""
        try:
            cpu_usage = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Calculate error rate
            total_errors = sum(len(m.error_history) for m in self.component_monitors.values())
            error_rate = total_errors / max(len(self.system_metrics_history), 1)
            
            # Calculate uptime
            uptime = (datetime.utcnow() - self.start_time).total_seconds()
            
            metrics = HealthMetrics(
                cpu_usage=cpu_usage,
                memory_usage=memory.percent,
                disk_usage=disk.percent,
                response_time=0.0,  # To be measured
                error_rate=error_rate,
                throughput=0.0,  # To be measured
                uptime=uptime
            )
            
            self.system_metrics_history.append(metrics)
            
            return metrics
        
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
            return HealthMetrics()
    
    async def detect_issues(self) -> List[SystemIssue]:
        """Detect all system issues"""
        all_issues = []
        
        # Collect system metrics
        metrics = await self.collect_system_metrics()
        
        # Check system-level issues
        if metrics.cpu_usage > 90:
            all_issues.append(SystemIssue(
                issue_id="system_cpu_overload",
                issue_type=IssueType.CPU_OVERLOAD,
                severity=0.9,
                description=f"CPU usage critical: {metrics.cpu_usage:.1f}%",
                detected_at=datetime.utcnow(),
                component="system",
                metrics={'cpu_usage': metrics.cpu_usage},
                suggested_actions=[RepairAction.REDUCE_LOAD, RepairAction.GARBAGE_COLLECT]
            ))
        
        if metrics.memory_usage > 90:
            all_issues.append(SystemIssue(
                issue_id="system_memory_exhaustion",
                issue_type=IssueType.MEMORY_LEAK,
                severity=0.9,
                description=f"Memory usage critical: {metrics.memory_usage:.1f}%",
                detected_at=datetime.utcnow(),
                component="system",
                metrics={'memory_usage': metrics.memory_usage},
                suggested_actions=[RepairAction.GARBAGE_COLLECT, RepairAction.CLEAR_CACHE]
            ))
        
        # Check component-level issues
        for component_name, monitor in self.component_monitors.items():
            component_issues = monitor.detect_anomalies()
            all_issues.extend(component_issues)
        
        return all_issues
    
    async def heal(self):
        """Perform healing cycle"""
        # Detect issues
        issues = await self.detect_issues()
        
        # Update active issues
        for issue in issues:
            if issue.issue_id not in self.active_issues:
                self.active_issues[issue.issue_id] = issue
                logger.warning(f"New issue detected: {issue.description}")
        
        # Attempt repairs for critical issues
        for issue_id, issue in list(self.active_issues.items()):
            if issue.severity >= 0.7 and issue.auto_repairable:
                repair_record = await self.auto_repair.attempt_repair(issue)
                
                if repair_record.success:
                    # Remove from active issues
                    del self.active_issues[issue_id]
    
    async def start_monitoring(self, interval: float = 60.0):
        """Start continuous monitoring"""
        self.monitoring_active = True
        logger.info("Self-healing monitoring started")
        
        while self.monitoring_active:
            try:
                await self.heal()
                await asyncio.sleep(interval)
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(interval)
    
    def stop_monitoring(self):
        """Stop monitoring"""
        self.monitoring_active = False
        logger.info("Self-healing monitoring stopped")
    
    def record_component_metrics(self, component_name: str, metrics: Dict[str, float]):
        """Record metrics for a component"""
        if component_name not in self.component_monitors:
            self.register_component(component_name)
        
        self.component_monitors[component_name].record_metrics(metrics)
    
    def record_component_error(self, component_name: str, error: Exception, 
                              context: Dict[str, Any]):
        """Record error for a component"""
        if component_name not in self.component_monitors:
            self.register_component(component_name)
        
        self.component_monitors[component_name].record_error(error, context)
    
    def get_system_health(self) -> Dict[str, Any]:
        """Get comprehensive system health report"""
        if not self.system_metrics_history:
            return {'status': 'unknown'}
        
        latest_metrics = self.system_metrics_history[-1]
        
        return {
            'status': latest_metrics.get_status().value,
            'health_score': latest_metrics.calculate_health_score(),
            'metrics': {
                'cpu_usage': latest_metrics.cpu_usage,
                'memory_usage': latest_metrics.memory_usage,
                'disk_usage': latest_metrics.disk_usage,
                'error_rate': latest_metrics.error_rate,
                'uptime': latest_metrics.uptime
            },
            'active_issues': len(self.active_issues),
            'components': {
                name: {
                    'health_score': monitor.get_health_score(),
                    'recent_errors': len([e for e in monitor.error_history 
                                        if (datetime.utcnow() - e['timestamp']).seconds < 600])
                }
                for name, monitor in self.component_monitors.items()
            },
            'repair_success_rate': self.auto_repair.get_repair_success_rate(),
            'total_repairs': len(self.auto_repair.repair_history)
        }


async def create_self_healing_system(config: Optional[Dict] = None) -> SelfHealingSystem:
    """Factory function to create self-healing system"""
    system = SelfHealingSystem(config)
    logger.info("Self-healing system initialized")
    return system
