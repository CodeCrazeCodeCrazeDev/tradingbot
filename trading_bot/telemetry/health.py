"""
AlphaAlgo Health Checker - System Health Monitoring

This module provides health checking for all components.

Version: 1.0.0
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional
from enum import Enum
import logging
import asyncio

# Evolution: Added retry decorator
def retry(max_attempts=3, delay=1.0):
    """Retry decorator for resilient operations"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    if attempt < max_attempts - 1:
                        await asyncio.sleep(delay * (attempt + 1))
            raise last_error
        return wrapper
    return decorator



logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """Health status levels"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


@dataclass
class ComponentHealth:
    """Health status of a component"""
    name: str
    status: HealthStatus
    message: str = ""
    last_check: datetime = field(default_factory=datetime.now)
    response_time_ms: float = 0.0
    details: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'status': self.status.value,
            'message': self.message,
            'last_check': self.last_check.isoformat(),
            'response_time_ms': self.response_time_ms,
            'details': self.details,
        }


class HealthChecker:
    """
    System health checker.
    
    Monitors health of all components and provides overall system health.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Health check functions
        self._checks: Dict[str, Callable] = {}
        
        # Component health status
        self._component_health: Dict[str, ComponentHealth] = {}
        
        # Check intervals
        self._check_interval = timedelta(
            seconds=self.config.get('check_interval_seconds', 30)
        )
        
        # Background task
        self._check_task: Optional[asyncio.Task] = None
        self._stop_event = asyncio.Event()
        
        logger.info("HealthChecker initialized")
    
    def register_check(self, name: str, check_fn: Callable) -> None:
        """
        Register a health check function.
        
        The function should return a tuple of (status: HealthStatus, message: str, details: dict)
        """
        self._checks[name] = check_fn
        self._component_health[name] = ComponentHealth(
            name=name,
            status=HealthStatus.UNKNOWN,
            message="Not yet checked"
        )
        logger.info(f"Registered health check: {name}")
    
    async def check_component(self, name: str) -> ComponentHealth:
        """Check health of a specific component"""
        if name not in self._checks:
            return ComponentHealth(
                name=name,
                status=HealthStatus.UNKNOWN,
                message="No health check registered"
            )
        
        check_fn = self._checks[name]
        start_time = datetime.now()
        
        try:
            if asyncio.iscoroutinefunction(check_fn):
                result = await check_fn()
            else:
                result = check_fn()
            
            response_time = (datetime.now() - start_time).total_seconds() * 1000
            
            if isinstance(result, tuple):
                status, message, details = result
            else:
                status = HealthStatus.HEALTHY if result else HealthStatus.UNHEALTHY
                message = "OK" if result else "Check failed"
                details = {}
            
            health = ComponentHealth(
                name=name,
                status=status,
                message=message,
                last_check=datetime.now(),
                response_time_ms=response_time,
                details=details
            )
            
        except Exception as e:
            response_time = (datetime.now() - start_time).total_seconds() * 1000
            health = ComponentHealth(
                name=name,
                status=HealthStatus.UNHEALTHY,
                message=f"Check failed: {str(e)}",
                last_check=datetime.now(),
                response_time_ms=response_time,
                details={'error': str(e)}
            )
        
        self._component_health[name] = health
        return health
    
    async def check_all(self) -> Dict[str, ComponentHealth]:
        """Check health of all components"""
        tasks = [self.check_component(name) for name in self._checks]
        await asyncio.gather(*tasks, return_exceptions=True)
        return self._component_health.copy()
    
    def get_overall_status(self) -> HealthStatus:
        """Get overall system health status"""
        if not self._component_health:
            return HealthStatus.UNKNOWN
        
        statuses = [h.status for h in self._component_health.values()]
        
        # If any critical, overall is critical
        if HealthStatus.CRITICAL in statuses:
            return HealthStatus.CRITICAL
        
        # If any unhealthy, overall is unhealthy
        if HealthStatus.UNHEALTHY in statuses:
            return HealthStatus.UNHEALTHY
        
        # If any degraded, overall is degraded
        if HealthStatus.DEGRADED in statuses:
            return HealthStatus.DEGRADED
        
        # If any unknown, overall is degraded
        if HealthStatus.UNKNOWN in statuses:
            return HealthStatus.DEGRADED
        
        return HealthStatus.HEALTHY
    
    def get_health_report(self) -> Dict[str, Any]:
        """Get full health report"""
        return {
            'overall_status': self.get_overall_status().value,
            'timestamp': datetime.now().isoformat(),
            'components': {
                name: health.to_dict()
                for name, health in self._component_health.items()
            }
        }
    
    def is_healthy(self) -> bool:
        """Quick check if system is healthy"""
        status = self.get_overall_status()
        return status in [HealthStatus.HEALTHY, HealthStatus.DEGRADED]
    
    def is_ready(self) -> bool:
        """Check if system is ready to accept traffic"""
        # All critical components must be healthy
        critical_components = self.config.get('critical_components', [])
        
        for name in critical_components:
            if name in self._component_health:
                if self._component_health[name].status in [HealthStatus.UNHEALTHY, HealthStatus.CRITICAL]:
                    return False
        
        return True
    
    async def start_background_checks(self) -> None:
        """Start background health checks"""
        self._stop_event.clear()
        self._check_task = asyncio.create_task(self._check_loop())
        logger.info("Background health checks started")
    
    async def stop_background_checks(self) -> None:
        """Stop background health checks"""
        self._stop_event.set()
        if self._check_task:
            self._check_task.cancel()
            try:
                await self._check_task
            except asyncio.CancelledError:
                pass
        logger.info("Background health checks stopped")
    
    async def _check_loop(self) -> None:
        """Background check loop"""
        while not self._stop_event.is_set():
            try:
                await self.check_all()
            except Exception as e:
                logger.error(f"Health check loop error: {e}")
            
                await asyncio.wait_for(
                    self._stop_event.wait(),
                    timeout=self._check_interval.total_seconds()
                )
                break
            except asyncio.TimeoutError:
                continue


# =============================================================================
# SINGLETON
# =============================================================================

_health_checker_instance: Optional[HealthChecker] = None


def get_health_checker(config: Optional[Dict[str, Any]] = None) -> HealthChecker:
    """Get the singleton health checker"""
    global _health_checker_instance
    if _health_checker_instance is None:
        _health_checker_instance = HealthChecker(config)
    return _health_checker_instance


# =============================================================================
# KUBERNETES PROBES
# =============================================================================

async def liveness_probe() -> Dict[str, Any]:
    """Kubernetes liveness probe"""
    checker = get_health_checker()
    is_alive = checker.get_overall_status() != HealthStatus.CRITICAL
    return {
        'alive': is_alive,
        'status': checker.get_overall_status().value,
        'timestamp': datetime.now().isoformat(),
    }


async def readiness_probe() -> Dict[str, Any]:
    """Kubernetes readiness probe"""
    checker = get_health_checker()
    is_ready = checker.is_ready()
    return {
        'ready': is_ready,
        'status': checker.get_overall_status().value,
        'timestamp': datetime.now().isoformat(),
    }
