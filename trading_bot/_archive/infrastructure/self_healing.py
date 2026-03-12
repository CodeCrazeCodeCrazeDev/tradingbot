import logging
logger = logging.getLogger(__name__)
"""Self-Healing and Auto-Scaling Infrastructure Module

This module implements automated infrastructure management including
health monitoring, failure detection, recovery mechanisms, and auto-scaling.
"""

import psutil
import threading
import time
import subprocess
from typing import Any, Callable, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
import json
import os
from loguru import logger


class ComponentStatus(Enum):
    """Status of system components."""
    HEALTHY = auto()
    WARNING = auto()
    CRITICAL = auto()
    FAILED = auto()
    RECOVERING = auto()


class ScalingAction(Enum):
    """Auto-scaling actions."""
    SCALE_UP = auto()
    SCALE_DOWN = auto()
    MAINTAIN = auto()


@dataclass
class HealthMetrics:
    """System health metrics."""
    timestamp: datetime
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    network_io: Dict[str, float]
    process_count: int
    response_time: float
    error_rate: float
    throughput: float


@dataclass
class ComponentHealth:
    """Health status of a system component."""
    name: str
    status: ComponentStatus
    last_check: datetime
    metrics: HealthMetrics
    error_count: int = 0
    recovery_attempts: int = 0
    uptime: float = 0.0


@dataclass
class RecoveryAction:
    """Recovery action for failed components."""
    component: str
    action_type: str
    command: str
    timeout: int = 30
    max_retries: int = 3
    success_callback: Optional[Callable] = None


class SelfHealingSystem:
    """Self-healing and auto-scaling infrastructure management."""
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize the self-healing system.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self._init_default_config()
        
        # Component tracking
        self.components: Dict[str, ComponentHealth] = {}
        self.recovery_actions: Dict[str, List[RecoveryAction]] = {}
        self.health_history: List[HealthMetrics] = []
        
        # Monitoring thread
        self.monitoring_thread = None
        self.running = False
        
        # Scaling parameters
        self.current_instances = 1
        self.target_instances = 1
        
        logger.info("SelfHealingSystem initialized")
    
    def _init_default_config(self):
        """Initialize default configuration."""
        defaults = {
            "check_interval": 30,  # seconds
            "cpu_threshold_warning": 70.0,
            "cpu_threshold_critical": 90.0,
            "memory_threshold_warning": 80.0,
            "memory_threshold_critical": 95.0,
            "disk_threshold_warning": 85.0,
            "disk_threshold_critical": 95.0,
            "response_time_threshold": 5.0,  # seconds
            "error_rate_threshold": 0.05,  # 5%
            "max_recovery_attempts": 3,
            "recovery_cooldown": 300,  # seconds
            "scaling_cooldown": 600,  # seconds
            "min_instances": 1,
            "max_instances": 10,
            "scale_up_threshold": 80.0,
            "scale_down_threshold": 30.0
        }
        
        for key, value in defaults.items():
            if key not in self.config:
                self.config[key] = value
    
    def start_monitoring(self):
        """Start the health monitoring system."""
        if self.monitoring_thread and self.monitoring_thread.is_alive():
            logger.warning("Monitoring already running")
            return
        
        self.running = True
        self.monitoring_thread = threading.Thread(
            target=self._monitoring_loop,
            daemon=True,
            name="HealthMonitor"
        )
        self.monitoring_thread.start()
        logger.info("Health monitoring started")
    
    def stop_monitoring(self):
        """Stop the health monitoring system."""
        self.running = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5.0)
        logger.info("Health monitoring stopped")
    
    def _monitoring_loop(self):
        """Main monitoring loop."""
        while self.running:
            try:
                # Collect system metrics
                metrics = self._collect_system_metrics()
                self.health_history.append(metrics)
                
                # Keep only recent history
                cutoff_time = datetime.now() - timedelta(hours=24)
                self.health_history = [
                    m for m in self.health_history 
                    if m.timestamp >= cutoff_time
                ]
                
                # Check component health
                self._check_component_health(metrics)
                
                # Perform recovery actions if needed
                self._perform_recovery_actions()
                
                # Check scaling requirements
                self._check_scaling_requirements(metrics)
                
                # Sleep until next check
                time.sleep(self.config["check_interval"])
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(5)
    
    def _collect_system_metrics(self) -> HealthMetrics:
        """Collect current system metrics."""
        try:
            # CPU usage
            cpu_usage = psutil.cpu_percent(interval=1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_usage = memory.percent
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_usage = disk.percent
            
            # Network I/O
            network = psutil.net_io_counters()
            network_io = {
                'bytes_sent': network.bytes_sent,
                'bytes_recv': network.bytes_recv,
                'packets_sent': network.packets_sent,
                'packets_recv': network.packets_recv
            }
            
            # Process count
            process_count = len(psutil.pids())
            
            # Simulate application-specific metrics
            response_time = self._measure_response_time()
            error_rate = self._calculate_error_rate()
            throughput = self._calculate_throughput()
            
            return HealthMetrics(
                timestamp=datetime.now(),
                cpu_usage=cpu_usage,
                memory_usage=memory_usage,
                disk_usage=disk_usage,
                network_io=network_io,
                process_count=process_count,
                response_time=response_time,
                error_rate=error_rate,
                throughput=throughput
            )
            
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
            return HealthMetrics(
                timestamp=datetime.now(),
                cpu_usage=0.0,
                memory_usage=0.0,
                disk_usage=0.0,
                network_io={},
                process_count=0,
                response_time=0.0,
                error_rate=0.0,
                throughput=0.0
            )
    
    def _measure_response_time(self) -> float:
        """Measure application response time."""
        # Simulate response time measurement
        # In a real implementation, this would ping the application endpoints
        return 0.5  # 500ms
    
    def _calculate_error_rate(self) -> float:
        """Calculate current error rate."""
        # Simulate error rate calculation
        # In a real implementation, this would check application logs
        return 0.01  # 1%
    
    def _calculate_throughput(self) -> float:
        """Calculate current throughput."""
        # Simulate throughput calculation
        # In a real implementation, this would measure requests/trades per second
        return 100.0  # 100 operations per second
    
    def _check_component_health(self, metrics: HealthMetrics):
        """Check health of system components."""
        # Check system component
        system_status = self._determine_system_status(metrics)
        
        self.components["system"] = ComponentHealth(
            name="system",
            status=system_status,
            last_check=datetime.now(),
            metrics=metrics,
            uptime=time.time() - psutil.boot_time()
        )
        
        # Check trading bot components (simulated)
        self._check_trading_components(metrics)
    
    def _determine_system_status(self, metrics: HealthMetrics) -> ComponentStatus:
        """Determine system status based on metrics."""
        # Critical conditions
        if (metrics.cpu_usage >= self.config["cpu_threshold_critical"] or
            metrics.memory_usage >= self.config["memory_threshold_critical"] or
            metrics.disk_usage >= self.config["disk_threshold_critical"]):
            return ComponentStatus.CRITICAL
        
        # Warning conditions
        if (metrics.cpu_usage >= self.config["cpu_threshold_warning"] or
            metrics.memory_usage >= self.config["memory_threshold_warning"] or
            metrics.disk_usage >= self.config["disk_threshold_warning"] or
            metrics.response_time >= self.config["response_time_threshold"] or
            metrics.error_rate >= self.config["error_rate_threshold"]):
            return ComponentStatus.WARNING
        
        return ComponentStatus.HEALTHY
    
    def _check_trading_components(self, metrics: HealthMetrics):
        """Check health of trading bot components."""
        components = [
            "data_feed",
            "strategy_engine",
            "risk_manager",
            "order_executor",
            "portfolio_manager"
        ]
        
        for component in components:
            # Simulate component health checks
            status = self._simulate_component_health(component, metrics)
            
            if component not in self.components:
                self.components[component] = ComponentHealth(
                    name=component,
                    status=status,
                    last_check=datetime.now(),
                    metrics=metrics
                )
            else:
                self.components[component].status = status
                self.components[component].last_check = datetime.now()
                self.components[component].metrics = metrics
    
    def _simulate_component_health(self, component: str, metrics: HealthMetrics) -> ComponentStatus:
        """Simulate component health check."""
        # Simple simulation based on system metrics
        if metrics.cpu_usage > 85 or metrics.memory_usage > 90:
            return ComponentStatus.WARNING
        elif metrics.error_rate > 0.1:
            return ComponentStatus.CRITICAL
        else:
            return ComponentStatus.HEALTHY
    
    def _perform_recovery_actions(self):
        """Perform recovery actions for failed components."""
        for component_name, component in self.components.items():
            if component.status in [ComponentStatus.CRITICAL, ComponentStatus.FAILED]:
                # Check if recovery is needed and allowed
                if self._should_attempt_recovery(component):
                    self._attempt_component_recovery(component_name, component)
    
    def _should_attempt_recovery(self, component: ComponentHealth) -> bool:
        """Determine if recovery should be attempted."""
        # Check recovery attempts
        if component.recovery_attempts >= self.config["max_recovery_attempts"]:
            return False
        
        # Check cooldown period
        cooldown_end = component.last_check + timedelta(seconds=self.config["recovery_cooldown"])
        if datetime.now() < cooldown_end:
            return False
        
        return True
    
    def _attempt_component_recovery(self, component_name: str, component: ComponentHealth):
        """Attempt to recover a failed component."""
        logger.warning(f"Attempting recovery for component: {component_name}")
        
        component.status = ComponentStatus.RECOVERING
        component.recovery_attempts += 1
        
        # Get recovery actions for this component
        actions = self.recovery_actions.get(component_name, [])
        
        if not actions:
            # Default recovery actions
            actions = self._get_default_recovery_actions(component_name)
        
        # Execute recovery actions
        for action in actions:
            try:
                success = self._execute_recovery_action(action)
                if success:
                    component.status = ComponentStatus.HEALTHY
                    component.error_count = 0
                    logger.info(f"Successfully recovered component: {component_name}")
                    
                    if action.success_callback:
                        action.success_callback()
                    break
                    
            except Exception as e:
                logger.error(f"Recovery action failed for {component_name}: {e}")
                component.error_count += 1
        
        # If all recovery actions failed
        if component.status == ComponentStatus.RECOVERING:
            component.status = ComponentStatus.FAILED
            logger.error(f"Failed to recover component: {component_name}")
    
    def _get_default_recovery_actions(self, component_name: str) -> List[RecoveryAction]:
        """Get default recovery actions for a component."""
        if component_name == "system":
            return [
                RecoveryAction(
                    component=component_name,
                    action_type="cleanup",
                    command="python -c \"import gc; gc.collect()\"",
                    timeout=10
                ),
                RecoveryAction(
                    component=component_name,
                    action_type="restart_services",
                    command="echo 'Restarting services'",
                    timeout=30
                )
            ]
        else:
            return [
                RecoveryAction(
                    component=component_name,
                    action_type="restart",
                    command=f"echo 'Restarting {component_name}'",
                    timeout=20
                )
            ]
    
    def _execute_recovery_action(self, action: RecoveryAction) -> bool:
        """Execute a recovery action."""
        try:
            logger.info(f"Executing recovery action: {action.action_type} for {action.component}")
            
            # Execute command with timeout
            result = subprocess.run(
                action.command,
                shell=True,
                timeout=action.timeout,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                logger.info(f"Recovery action succeeded: {action.action_type}")
                return True
            else:
                logger.error(f"Recovery action failed with code {result.returncode}: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error(f"Recovery action timed out: {action.action_type}")
            return False
        except Exception as e:
            logger.error(f"Error executing recovery action: {e}")
            return False
    
    def _check_scaling_requirements(self, metrics: HealthMetrics):
        """Check if scaling is required."""
        # Calculate average load over recent history
        if len(self.health_history) < 3:
            return
        
        recent_metrics = self.health_history[-5:]  # Last 5 measurements
        avg_cpu = sum(m.cpu_usage for m in recent_metrics) / len(recent_metrics)
        avg_memory = sum(m.memory_usage for m in recent_metrics) / len(recent_metrics)
        avg_response_time = sum(m.response_time for m in recent_metrics) / len(recent_metrics)
        
        # Determine scaling action
        scaling_action = self._determine_scaling_action(avg_cpu, avg_memory, avg_response_time)
        
        if scaling_action != ScalingAction.MAINTAIN:
            self._execute_scaling_action(scaling_action, metrics)
    
    def _determine_scaling_action(self, avg_cpu: float, avg_memory: float, avg_response_time: float) -> ScalingAction:
        """Determine required scaling action."""
        # Scale up conditions
        if (avg_cpu >= self.config["scale_up_threshold"] or
            avg_memory >= self.config["scale_up_threshold"] or
            avg_response_time >= self.config["response_time_threshold"] * 2):
            
            if self.current_instances < self.config["max_instances"]:
                return ScalingAction.SCALE_UP
        
        # Scale down conditions
        elif (avg_cpu <= self.config["scale_down_threshold"] and
              avg_memory <= self.config["scale_down_threshold"] and
              avg_response_time <= self.config["response_time_threshold"] * 0.5):
            
            if self.current_instances > self.config["min_instances"]:
                return ScalingAction.SCALE_DOWN
        
        return ScalingAction.MAINTAIN
    
    def _execute_scaling_action(self, action: ScalingAction, metrics: HealthMetrics):
        """Execute scaling action."""
        if action == ScalingAction.SCALE_UP:
            new_instances = min(self.current_instances + 1, self.config["max_instances"])
            logger.info(f"Scaling up from {self.current_instances} to {new_instances} instances")
            
            # Simulate scaling up
            if self._scale_instances(new_instances):
                self.current_instances = new_instances
                
        elif action == ScalingAction.SCALE_DOWN:
            new_instances = max(self.current_instances - 1, self.config["min_instances"])
            logger.info(f"Scaling down from {self.current_instances} to {new_instances} instances")
            
            # Simulate scaling down
            if self._scale_instances(new_instances):
                self.current_instances = new_instances
    
    def _scale_instances(self, target_instances: int) -> bool:
        """Scale to target number of instances."""
        try:
            # In a real implementation, this would interact with container orchestration
            # or cloud auto-scaling services
            logger.info(f"Scaling to {target_instances} instances")
            
            # Simulate scaling delay
            time.sleep(1)
            
            self.target_instances = target_instances
            return True
            
        except Exception as e:
            logger.error(f"Failed to scale instances: {e}")
            return False
    
    def register_component(self, name: str, recovery_actions: List[RecoveryAction] = None):
        """Register a component for monitoring."""
        self.components[name] = ComponentHealth(
            name=name,
            status=ComponentStatus.HEALTHY,
            last_check=datetime.now(),
            metrics=self._collect_system_metrics()
        )
        
        if recovery_actions:
            self.recovery_actions[name] = recovery_actions
        
        logger.info(f"Registered component for monitoring: {name}")
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get current health status of all components."""
        return {
            "timestamp": datetime.now().isoformat(),
            "overall_status": self._get_overall_status(),
            "components": {
                name: {
                    "status": component.status.name,
                    "last_check": component.last_check.isoformat(),
                    "error_count": component.error_count,
                    "recovery_attempts": component.recovery_attempts,
                    "uptime": component.uptime
                }
                for name, component in self.components.items()
            },
            "system_metrics": {
                "cpu_usage": self.components.get("system", ComponentHealth("", ComponentStatus.HEALTHY, datetime.now(), self._collect_system_metrics())).metrics.cpu_usage,
                "memory_usage": self.components.get("system", ComponentHealth("", ComponentStatus.HEALTHY, datetime.now(), self._collect_system_metrics())).metrics.memory_usage,
                "disk_usage": self.components.get("system", ComponentHealth("", ComponentStatus.HEALTHY, datetime.now(), self._collect_system_metrics())).metrics.disk_usage,
                "response_time": self.components.get("system", ComponentHealth("", ComponentStatus.HEALTHY, datetime.now(), self._collect_system_metrics())).metrics.response_time,
                "error_rate": self.components.get("system", ComponentHealth("", ComponentStatus.HEALTHY, datetime.now(), self._collect_system_metrics())).metrics.error_rate
            },
            "scaling_info": {
                "current_instances": self.current_instances,
                "target_instances": self.target_instances,
                "min_instances": self.config["min_instances"],
                "max_instances": self.config["max_instances"]
            }
        }
    
    def _get_overall_status(self) -> str:
        """Get overall system status."""
        if not self.components:
            return "unknown"
        
        statuses = [component.status for component in self.components.values()]
        
        if ComponentStatus.FAILED in statuses:
            return "failed"
        elif ComponentStatus.CRITICAL in statuses:
            return "critical"
        elif ComponentStatus.WARNING in statuses:
            return "warning"
        elif ComponentStatus.RECOVERING in statuses:
            return "recovering"
        else:
            return "healthy"
    
    def force_recovery(self, component_name: str) -> bool:
        """Force recovery attempt for a specific component."""
        if component_name not in self.components:
            logger.error(f"Component not found: {component_name}")
            return False
        
        component = self.components[component_name]
        
        # Reset recovery attempts to allow forced recovery
        component.recovery_attempts = 0
        
        # Attempt recovery
        self._attempt_component_recovery(component_name, component)
        
        return component.status == ComponentStatus.HEALTHY
    
    def get_performance_report(self, hours: int = 24) -> Dict[str, Any]:
        """Get performance report for the specified time period."""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_metrics = [m for m in self.health_history if m.timestamp >= cutoff_time]
        
        if not recent_metrics:
            return {"error": "No metrics available for the specified period"}
        
        # Calculate statistics
        cpu_values = [m.cpu_usage for m in recent_metrics]
        memory_values = [m.memory_usage for m in recent_metrics]
        response_times = [m.response_time for m in recent_metrics]
        error_rates = [m.error_rate for m in recent_metrics]
        
        return {
            "period_hours": hours,
            "metrics_count": len(recent_metrics),
            "cpu_usage": {
                "average": sum(cpu_values) / len(cpu_values),
                "max": max(cpu_values),
                "min": min(cpu_values)
            },
            "memory_usage": {
                "average": sum(memory_values) / len(memory_values),
                "max": max(memory_values),
                "min": min(memory_values)
            },
            "response_time": {
                "average": sum(response_times) / len(response_times),
                "max": max(response_times),
                "min": min(response_times)
            },
            "error_rate": {
                "average": sum(error_rates) / len(error_rates),
                "max": max(error_rates),
                "min": min(error_rates)
            },
            "uptime_percentage": self._calculate_uptime_percentage(recent_metrics),
            "scaling_events": self._count_scaling_events(hours)
        }
    
    def _calculate_uptime_percentage(self, metrics: List[HealthMetrics]) -> float:
        """Calculate uptime percentage based on metrics."""
        if not metrics:
            return 0.0
        
        healthy_count = sum(1 for m in metrics if m.error_rate < 0.05)
        return (healthy_count / len(metrics)) * 100
    
    def _count_scaling_events(self, hours: int) -> int:
        """Count scaling events in the specified period."""
        # In a real implementation, this would track actual scaling events
        return 0
