"""
Health Check Endpoints for Kubernetes and Monitoring

Provides liveness and readiness probes for container orchestration.
"""

import asyncio
import logging
import psutil
from typing import Any, Callable, Dict, Optional
from datetime import datetime, timedelta
from enum import Enum

try:
    from fastapi import FastAPI, Response, status
    from fastapi.responses import JSONResponse
except ImportError:
    FastAPI = Response = status = JSONResponse = None

logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """Health status enumeration"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class ComponentHealth:
    """Health status for a component"""
    
    def __init__(self, name: str, check_func: Optional[Callable] = None):
        self.name = name
        self.check_func = check_func
        self.status = HealthStatus.HEALTHY
        self.last_check = datetime.now()
        self.error_message = None
        self.metadata = {}
    
    async def check(self) -> bool:
        """Run health check"""
        try:
            if self.check_func:
                result = await self.check_func() if asyncio.iscoroutinefunction(self.check_func) else self.check_func()
                self.status = HealthStatus.HEALTHY if result else HealthStatus.UNHEALTHY
                self.error_message = None if result else "Check failed"
            else:
                self.status = HealthStatus.HEALTHY
            
            self.last_check = datetime.now()
            return self.status == HealthStatus.HEALTHY
            
        except Exception as e:
            self.status = HealthStatus.UNHEALTHY
            self.error_message = str(e)
            self.last_check = datetime.now()
            logger.error(f"Health check failed for {self.name}: {e}")
            return False


class HealthCheckManager:
    """Manage health checks for all components"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.components: Dict[str, ComponentHealth] = {}
        self.overall_status = HealthStatus.HEALTHY
        self.startup_time = datetime.now()
        
        # Configuration
        self.check_interval = self.config.get('check_interval', 30)  # seconds
        self.startup_grace_period = self.config.get('startup_grace_period', 60)  # seconds
        self.max_component_age = self.config.get('max_component_age', 300)  # seconds
        
    def register_component(
        self,
        name: str,
        check_func: Optional[Callable] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Register a component for health checking"""
        component = ComponentHealth(name, check_func)
        if metadata:
            component.metadata = metadata
        self.components[name] = component
        logger.info(f"Registered health check for component: {name}")
    
    async def check_all(self) -> Dict[str, Any]:
        """Check health of all components"""
        results = {}
        all_healthy = True
        
        for name, component in self.components.items():
            is_healthy = await component.check()
            results[name] = {
                'status': component.status.value,
                'last_check': component.last_check.isoformat(),
                'error': component.error_message,
                'metadata': component.metadata
            }
            
            if not is_healthy:
                all_healthy = False
        
        # Update overall status
        if all_healthy:
            self.overall_status = HealthStatus.HEALTHY
        elif any(c.status == HealthStatus.UNHEALTHY for c in self.components.values()):
            self.overall_status = HealthStatus.UNHEALTHY
        else:
            self.overall_status = HealthStatus.DEGRADED
        
        return results
    
    def is_ready(self) -> bool:
        """Check if system is ready to serve traffic"""
        # During startup grace period, always return not ready
        uptime = (datetime.now() - self.startup_time).total_seconds()
        if uptime < self.startup_grace_period:
            return False
        
        # Check critical components
        critical_components = [
            name for name, comp in self.components.items()
            if comp.metadata.get('critical', False)
        ]
        
        for name in critical_components:
            component = self.components[name]
            if component.status == HealthStatus.UNHEALTHY:
                return False
            
            # Check if component check is stale
            age = (datetime.now() - component.last_check).total_seconds()
            if age > self.max_component_age:
                return False
        
        return True
    
    def is_alive(self) -> bool:
        """Check if system is alive (basic liveness)"""
        # Simple check - if we can respond, we're alive
        return True
    
    def get_status_summary(self) -> Dict[str, Any]:
        """Get overall status summary"""
        uptime = (datetime.now() - self.startup_time).total_seconds()
        
        component_statuses = {
            name: comp.status.value
            for name, comp in self.components.items()
        }
        
        return {
            'status': self.overall_status.value,
            'uptime_seconds': uptime,
            'startup_time': self.startup_time.isoformat(),
            'components': component_statuses,
            'ready': self.is_ready(),
            'alive': self.is_alive(),
        }


def setup_health_endpoints(app: FastAPI, health_manager: HealthCheckManager):
    """Setup health check endpoints on FastAPI app"""
    
    @app.get("/health/live")
    async def liveness():
        """
        Liveness probe - indicates if the application is running
        
        Returns 200 if alive, 503 if dead
        """
        if health_manager.is_alive():
            return JSONResponse(
                content={
                    "status": "alive",
                    "timestamp": datetime.now().isoformat()
                },
                status_code=status.HTTP_200_OK
            )
        else:
            return JSONResponse(
                content={
                    "status": "dead",
                    "timestamp": datetime.now().isoformat()
                },
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE
            )
    
    @app.get("/health/ready")
    async def readiness():
        """
        Readiness probe - indicates if the application is ready to serve traffic
        
        Returns 200 if ready, 503 if not ready
        """
        is_ready = health_manager.is_ready()
        status_code = status.HTTP_200_OK if is_ready else status.HTTP_503_SERVICE_UNAVAILABLE
        
        # Get detailed component status
        component_checks = await health_manager.check_all()
        
        return JSONResponse(
            content={
                "status": "ready" if is_ready else "not_ready",
                "timestamp": datetime.now().isoformat(),
                "components": component_checks,
                "overall": health_manager.overall_status.value
            },
            status_code=status_code
        )
    
    @app.get("/health/status")
    async def health_status():
        """
        Detailed health status endpoint
        
        Returns comprehensive health information
        """
        summary = health_manager.get_status_summary()
        component_checks = await health_manager.check_all()
        
        return JSONResponse(
            content={
                **summary,
                "detailed_checks": component_checks,
                "timestamp": datetime.now().isoformat()
            },
            status_code=status.HTTP_200_OK
        )
    
    @app.get("/health")
    async def health():
        """
        Simple health check endpoint
        
        Returns basic health information
        """
        return JSONResponse(
            content={
                "status": health_manager.overall_status.value,
                "ready": health_manager.is_ready(),
                "alive": health_manager.is_alive(),
                "timestamp": datetime.now().isoformat()
            },
            status_code=status.HTTP_200_OK
        )
    
    logger.info("Health check endpoints registered")


# Example health check functions
def check_database_connection(db_connection) -> bool:
    """Example: Check database connection"""
    try:
        return db_connection is not None and hasattr(db_connection, 'is_connected')
    except Exception:
        return False


def check_broker_connection(broker_adapter) -> bool:
    """Example: Check broker connection"""
    try:
        return broker_adapter is not None and broker_adapter.connected
    except Exception:
        return False


async def check_data_freshness(data_stream, max_age_seconds: int = 60) -> bool:
    """Example: Check if data is fresh"""
    try:
        if not hasattr(data_stream, 'last_update'):
            return False
        
        age = (datetime.now() - data_stream.last_update).total_seconds()
        return age < max_age_seconds
    except Exception:
        return False


def check_memory_usage(max_memory_mb: int = 1000) -> bool:
    """Example: Check memory usage"""
    try:
        process = psutil.Process()
        memory_mb = process.memory_info().rss / 1024 / 1024
        return memory_mb < max_memory_mb
    except Exception:
        return True  # If can't check, assume OK


def check_disk_space(min_free_gb: int = 1) -> bool:
    """Example: Check disk space"""
    try:
        disk = psutil.disk_usage('/')
        free_gb = disk.free / 1024 / 1024 / 1024
        return free_gb > min_free_gb
    except Exception:
        return True  # If can't check, assume OK
