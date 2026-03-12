"""
Self-Healing Architecture with Auto-Repair
Automatic error detection, diagnosis, and recovery
"""

import asyncio
import logging
import traceback
import gc
from typing import Any, Callable, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import psutil
import sys
import os

logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """System health status"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    CRITICAL = "critical"
    FAILED = "failed"
    RECOVERING = "recovering"


class ErrorSeverity(Enum):
    """Error severity levels"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class SystemError:
    """System error record"""
    error_id: str
    component: str
    error_type: str
    message: str
    severity: ErrorSeverity
    timestamp: datetime
    traceback: str
    context: Dict[str, Any] = field(default_factory=dict)
    resolved: bool = False
    resolution_time: Optional[datetime] = None
    resolution_method: Optional[str] = None


@dataclass
class HealthMetrics:
    """System health metrics"""
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    network_latency: float
    error_rate: float
    uptime: float
    timestamp: datetime


class SelfHealingSystem:
    """
    Self-healing architecture with automatic error detection and recovery
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Error tracking
        self.errors: List[SystemError] = []
        self.error_patterns: Dict[str, int] = {}
        
        # Health monitoring
        self.health_status = HealthStatus.HEALTHY
        self.health_history: List[HealthMetrics] = []
        
        # Auto-repair strategies
        self.repair_strategies: Dict[str, Callable] = {}
        self.register_default_strategies()
        
        # Circuit breakers
        self.circuit_breakers: Dict[str, Dict] = {}
        
        # Redundancy
        self.backup_systems: Dict[str, Any] = {}
        self.failover_enabled = self.config.get('failover_enabled', True)
        
        # Monitoring
        self.monitoring_interval = self.config.get('monitoring_interval', 60)
        self.monitoring_task = None
        
        # Recovery
        self.max_recovery_attempts = self.config.get('max_recovery_attempts', 3)
        self.recovery_attempts: Dict[str, int] = {}
        
        # Start time
        self.start_time = datetime.now()
        
        logger.info("Self-healing system initialized")
        
    def register_default_strategies(self):
        """Register default repair strategies"""
        self.repair_strategies.update({
            'connection_error': self._repair_connection,
            'memory_leak': self._repair_memory_leak,
            'deadlock': self._repair_deadlock,
            'timeout': self._repair_timeout,
            'data_corruption': self._repair_data_corruption,
            'resource_exhaustion': self._repair_resource_exhaustion,
            'configuration_error': self._repair_configuration,
        })
        
    def register_repair_strategy(self, error_type: str, strategy: Callable):
        """Register custom repair strategy"""
        self.repair_strategies[error_type] = strategy
        logger.info(f"Registered repair strategy for: {error_type}")
        
    async def detect_error(self, component: str, error: Exception, 
                          context: Optional[Dict] = None) -> SystemError:
        """Detect and log system error"""
        error_type = type(error).__name__
        severity = self._classify_severity(error_type, str(error))
        
        system_error = SystemError(
            error_id=f"{component}_{datetime.now().timestamp()}",
            component=component,
            error_type=error_type,
            message=str(error),
            severity=severity,
            timestamp=datetime.now(),
            traceback=traceback.format_exc(),
            context=context or {}
        )
        
        self.errors.append(system_error)
        
        # Track error patterns
        pattern_key = f"{component}:{error_type}"
        self.error_patterns[pattern_key] = self.error_patterns.get(pattern_key, 0) + 1
        
        # Update health status
        self._update_health_status()
        
        logger.error(f"Error detected: {system_error.error_id} - {system_error.message}")
        
        # Trigger auto-repair
        if severity.value >= ErrorSeverity.HIGH.value:
            await self.auto_repair(system_error)
            
        return system_error
        
    def _classify_severity(self, error_type: str, message: str) -> ErrorSeverity:
        """Classify error severity"""
        critical_keywords = ['fatal', 'critical', 'crash', 'corruption']
        high_keywords = ['timeout', 'connection', 'deadlock', 'memory']
        
        message_lower = message.lower()
        
        if any(kw in message_lower for kw in critical_keywords):
            return ErrorSeverity.CRITICAL
        elif any(kw in message_lower for kw in high_keywords):
            return ErrorSeverity.HIGH
        elif error_type in ['ConnectionError', 'TimeoutError', 'MemoryError']:
            return ErrorSeverity.HIGH
        else:
            return ErrorSeverity.MEDIUM
            
    async def auto_repair(self, error: SystemError) -> bool:
        """
        Automatically attempt to repair the error
        """
        logger.info(f"Attempting auto-repair for: {error.error_id}")
        
        # Check recovery attempts
        if self.recovery_attempts.get(error.error_id, 0) >= self.max_recovery_attempts:
            logger.error(f"Max recovery attempts reached for: {error.error_id}")
            return False
            
        self.recovery_attempts[error.error_id] = self.recovery_attempts.get(error.error_id, 0) + 1
        
        # Find appropriate repair strategy
        repair_strategy = None
        
        # Try exact match
        if error.error_type in self.repair_strategies:
            repair_strategy = self.repair_strategies[error.error_type]
        else:
            # Try pattern matching
            for pattern, strategy in self.repair_strategies.items():
                if pattern.lower() in error.error_type.lower() or pattern.lower() in error.message.lower():
                    repair_strategy = strategy
                    break
                    
        if repair_strategy is None:
            logger.warning(f"No repair strategy found for: {error.error_type}")
            return False
        try:
            
            # Execute repair
            self.health_status = HealthStatus.RECOVERING
            success = await repair_strategy(error)
            
            if success:
                error.resolved = True
                error.resolution_time = datetime.now()
                error.resolution_method = repair_strategy.__name__
                logger.info(f"Successfully repaired: {error.error_id}")
                self.health_status = HealthStatus.HEALTHY
                return True
            else:
                logger.warning(f"Repair failed for: {error.error_id}")
                return False
                
        except Exception as e:
            logger.error(f"Repair strategy failed: {e}")
            return False
            
    async def _repair_connection(self, error: SystemError) -> bool:
        """Repair connection errors"""
        logger.info("Repairing connection error...")
        
        # Retry with exponential backoff
        for attempt in range(3):
            await asyncio.sleep(2 ** attempt)
            try:
                # Attempt reconnection (placeholder)
                logger.info(f"Reconnection attempt {attempt + 1}")
                # In production: reconnect to broker, database, etc.
                return True
            except Exception as e:
                logger.warning(f"Reconnection failed: {e}")
                
        return False
        
    async def _repair_memory_leak(self, error: SystemError) -> bool:
        """Repair memory leak"""
        logger.info("Repairing memory leak...")
        
        try:
            # Force garbage collection
            gc.collect()
            
            # Clear caches
            # In production: clear specific caches based on error context
            
            return True
        except Exception as e:
            logger.error(f"Memory repair failed: {e}")
            return False
            
    async def _repair_deadlock(self, error: SystemError) -> bool:
        """Repair deadlock"""
        logger.info("Repairing deadlock...")
        
        try:
            # Reset locks (placeholder)
            # In production: identify and break deadlock
            return True
        except Exception as e:
            logger.error(f"Deadlock repair failed: {e}")
            return False
            
    async def _repair_timeout(self, error: SystemError) -> bool:
        """Repair timeout"""
        logger.info("Repairing timeout...")
        
        try:
            # Increase timeout or retry
            await asyncio.sleep(1)
            return True
        except Exception as e:
            logger.error(f"Timeout repair failed: {e}")
            return False
            
    async def _repair_data_corruption(self, error: SystemError) -> bool:
        """Repair data corruption"""
        logger.info("Repairing data corruption...")
        
        try:
            # Restore from backup
            # In production: restore corrupted data from backup
            return True
        except Exception as e:
            logger.error(f"Data repair failed: {e}")
            return False
            
    async def _repair_resource_exhaustion(self, error: SystemError) -> bool:
        """Repair resource exhaustion"""
        logger.info("Repairing resource exhaustion...")
        
        try:
            # Free resources
            gc.collect()
            
            # Scale resources if possible
            # In production: trigger auto-scaling
            
            return True
        except Exception as e:
            logger.error(f"Resource repair failed: {e}")
            return False
            
    async def _repair_configuration(self, error: SystemError) -> bool:
        """Repair configuration error"""
        logger.info("Repairing configuration error...")
        
        try:
            # Reload configuration
            # In production: reload from backup or defaults
            return True
        except Exception as e:
            logger.error(f"Configuration repair failed: {e}")
            return False
            
    def _update_health_status(self):
        """Update overall health status"""
        recent_errors = [e for e in self.errors if 
                        (datetime.now() - e.timestamp).total_seconds() < 300]
        
        critical_errors = [e for e in recent_errors if e.severity == ErrorSeverity.CRITICAL]
        high_errors = [e for e in recent_errors if e.severity == ErrorSeverity.HIGH]
        
        if len(critical_errors) > 0:
            self.health_status = HealthStatus.CRITICAL
        elif len(high_errors) > 2:
            self.health_status = HealthStatus.CRITICAL
        elif len(recent_errors) > 5:
            self.health_status = HealthStatus.DEGRADED
        else:
            self.health_status = HealthStatus.HEALTHY
            
    async def monitor_health(self):
        """Continuously monitor system health"""
        while True:
            try:
                metrics = HealthMetrics(
                    cpu_usage=psutil.cpu_percent(),
                    memory_usage=psutil.virtual_memory().percent,
                    disk_usage=psutil.disk_usage('/').percent,
                    network_latency=0.0,  # Placeholder
                    error_rate=len([e for e in self.errors if 
                                  (datetime.now() - e.timestamp).total_seconds() < 60]) / 60.0,
                    uptime=(datetime.now() - self.start_time).total_seconds(),
                    timestamp=datetime.now()
                )
                
                self.health_history.append(metrics)
                
                # Keep only recent history
                if len(self.health_history) > 1000:
                    self.health_history = self.health_history[-1000:]
                    
                # Check thresholds
                if metrics.cpu_usage > 90:
                    logger.warning(f"High CPU usage: {metrics.cpu_usage}%")
                if metrics.memory_usage > 90:
                    logger.warning(f"High memory usage: {metrics.memory_usage}%")
                    
                await asyncio.sleep(self.monitoring_interval)
                
            except Exception as e:
                logger.error(f"Health monitoring error: {e}")
                await asyncio.sleep(self.monitoring_interval)
                
    async def start_monitoring(self):
        """Start health monitoring"""
        if self.monitoring_task is None:
            self.monitoring_task = asyncio.create_task(self.monitor_health())
            logger.info("Health monitoring started")
            
    async def stop_monitoring(self):
        """Stop health monitoring"""
        if self.monitoring_task is not None:
            self.monitoring_task.cancel()
            self.monitoring_task = None
            logger.info("Health monitoring stopped")
            
    def get_health_report(self) -> Dict[str, Any]:
        """Get comprehensive health report"""
        recent_errors = [e for e in self.errors if 
                        (datetime.now() - e.timestamp).total_seconds() < 3600]
        
        return {
            'status': self.health_status.value,
            'uptime_seconds': (datetime.now() - self.start_time).total_seconds(),
            'total_errors': len(self.errors),
            'recent_errors': len(recent_errors),
            'resolved_errors': len([e for e in self.errors if e.resolved]),
            'error_patterns': self.error_patterns,
            'latest_metrics': self.health_history[-1].__dict__ if self.health_history else None,
            'recovery_success_rate': len([e for e in self.errors if e.resolved]) / max(len(self.errors), 1)
        }
