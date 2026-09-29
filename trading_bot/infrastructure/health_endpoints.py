"""
Health check REST endpoints for monitoring
"""

import warnings
import logging
from typing import Dict
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import psutil

logger = logging.getLogger(__name__)


class HealthEndpoints:
    """
    REST API endpoints for health monitoring.
    """
    
    def __init__(self, app: FastAPI, system_components: Dict):
        self.app = app
        self.components = system_components
        
        # Register endpoints
        self._register_endpoints()
        
        logger.info("✅ Health endpoints registered")
    
    def _register_endpoints(self):
        """Register health check endpoints."""
        
        @self.app.get("/health")
        async def health_check():
            """Basic health check."""
            return {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "service": "AlphaAlgo 2.0"
            }
        
        @self.app.get("/health/detailed")
        async def detailed_health():
            """Detailed health check with component status."""
            try:
                status = {
                    "status": "healthy",
                    "timestamp": datetime.now().isoformat(),
                    "components": {}
                }
                
                # Check each component
                for name, component in self.components.items():
                    try:
                        if hasattr(component, 'get_health'):
                            component_health = component.get_health()
                        else:
                            component_health = {"status": "unknown"}
                        
                        status["components"][name] = component_health
                    except Exception as e:
                        status["components"][name] = {
                            "status": "unhealthy",
                            "error": str(e)
                        }
                        status["status"] = "degraded"
                
                return status
                
            except Exception as e:
                logger.error(f"❌ Health check error: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/health/system")
        async def system_health():
            """System resource health check."""
            try:
                # CPU usage
                cpu_percent = psutil.cpu_percent(interval=1)
                
                # Memory usage
                memory = psutil.virtual_memory()
                
                # Disk usage
                disk = psutil.disk_usage('/')
                
                # Network
                net_io = psutil.net_io_counters()
                
                status = {
                    "status": "healthy",
                    "timestamp": datetime.now().isoformat(),
                    "system": {
                        "cpu": {
                            "usage_percent": cpu_percent,
                            "count": psutil.cpu_count(),
                            "status": "healthy" if cpu_percent < 80 else "warning"
                        },
                        "memory": {
                            "total_gb": memory.total / (1024**3),
                            "available_gb": memory.available / (1024**3),
                            "used_percent": memory.percent,
                            "status": "healthy" if memory.percent < 80 else "warning"
                        },
                        "disk": {
                            "total_gb": disk.total / (1024**3),
                            "free_gb": disk.free / (1024**3),
                            "used_percent": disk.percent,
                            "status": "healthy" if disk.percent < 80 else "warning"
                        },
                        "network": {
                            "bytes_sent": net_io.bytes_sent,
                            "bytes_recv": net_io.bytes_recv,
                            "packets_sent": net_io.packets_sent,
                            "packets_recv": net_io.packets_recv
                        }
                    }
                }
                
                # Overall status
                if cpu_percent > 90 or memory.percent > 90 or disk.percent > 90:
                    status["status"] = "critical"
                elif cpu_percent > 80 or memory.percent > 80 or disk.percent > 80:
                    status["status"] = "warning"
                
                return status
                
            except Exception as e:
                logger.error(f"❌ System health check error: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/health/trading")
        async def trading_health():
            """Trading system health check."""
            try:
                status = {
                    "status": "healthy",
                    "timestamp": datetime.now().isoformat(),
                    "trading": {}
                }
                
                # Check position manager
                if 'position_manager' in self.components:
                    pm = self.components['position_manager']
                    summary = pm.get_position_summary()
                    
                    status["trading"]["positions"] = {
                        "count": summary['num_positions'],
                        "total_exposure": summary['total_exposure'],
                        "current_capital": summary['current_capital'],
                        "return_pct": summary['return_pct'],
                        "status": "healthy" if summary['num_positions'] < 10 else "warning"
                    }
                
                # Check execution engine
                if 'execution_engine' in self.components:
                    ee = self.components['execution_engine']
                    if hasattr(ee, 'get_stats'):
                        exec_stats = ee.get_stats()
                        status["trading"]["execution"] = exec_stats
                
                # Check broker connection
                if 'broker' in self.components:
                    broker = self.components['broker']
                    if hasattr(broker, 'is_connected'):
                        connected = broker.is_connected()
                        status["trading"]["broker"] = {
                            "connected": connected,
                            "status": "healthy" if connected else "critical"
                        }
                        
                        if not connected:
                            status["status"] = "critical"
                
                return status
                
            except Exception as e:
                logger.error(f"❌ Trading health check error: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/health/ml")
        async def ml_health():
            """Machine learning system health check."""
            try:
                status = {
                    "status": "healthy",
                    "timestamp": datetime.now().isoformat(),
                    "ml": {}
                }
                
                # Check model status
                if 'ml_pipeline' in self.components:
                    pipeline = self.components['ml_pipeline']
                    if hasattr(pipeline, 'get_model_status'):
                        model_status = pipeline.get_model_status()
                        status["ml"]["models"] = model_status
                
                # Check prediction latency
                if 'predictor' in self.components:
                    predictor = self.components['predictor']
                    if hasattr(predictor, 'get_latency_stats'):
                        latency = predictor.get_latency_stats()
                        status["ml"]["latency"] = latency
                        
                        if latency.get('avg_ms', 0) > 1000:
                            status["status"] = "warning"
                
                return status
                
            except Exception as e:
                logger.error(f"❌ ML health check error: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/health/data")
        async def data_health():
            """Data pipeline health check."""
            try:
                status = {
                    "status": "healthy",
                    "timestamp": datetime.now().isoformat(),
                    "data": {}
                }
                
                # Check market data stream
                if 'market_data' in self.components:
                    md = self.components['market_data']
                    if hasattr(md, 'get_stream_status'):
                        stream_status = md.get_stream_status()
                        status["data"]["stream"] = stream_status
                        
                        if not stream_status.get('connected', False):
                            status["status"] = "critical"
                
                # Check data quality
                if 'data_validator' in self.components:
                    validator = self.components['data_validator']
                    if hasattr(validator, 'get_quality_metrics'):
                        quality = validator.get_quality_metrics()
                        status["data"]["quality"] = quality
                        
                        if quality.get('error_rate', 0) > 0.05:
                            status["status"] = "warning"
                
                return status
                
            except Exception as e:
                logger.error(f"❌ Data health check error: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/health/risk")
        async def risk_health():
            """Risk management health check."""
            try:
                status = {
                    "status": "healthy",
                    "timestamp": datetime.now().isoformat(),
                    "risk": {}
                }
                
                # Check risk metrics
                if 'position_manager' in self.components:
                    pm = self.components['position_manager']
                    metrics = pm.portfolio_metrics
                    
                    status["risk"]["metrics"] = {
                        "total_exposure": metrics['total_exposure'],
                        "total_risk": metrics['total_risk'],
                        "sharpe_ratio": metrics['sharpe_ratio'],
                        "max_drawdown": metrics['max_drawdown']
                    }
                    
                    # Check thresholds
                    if metrics['max_drawdown'] > 0.15:
                        status["status"] = "critical"
                    elif metrics['max_drawdown'] > 0.10:
                        status["status"] = "warning"
                
                # Check compliance
                if 'compliance_monitor' in self.components:
                    cm = self.components['compliance_monitor']
                    if hasattr(cm, 'get_summary'):
                        compliance = cm.get_summary()
                        status["risk"]["compliance"] = compliance
                        
                        if compliance.get('by_severity', {}).get('CRITICAL', 0) > 0:
                            status["status"] = "critical"
                
                return status
                
            except Exception as e:
                logger.error(f"❌ Risk health check error: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/metrics")
        async def metrics():
            """Prometheus-style metrics endpoint."""
            try:
                metrics_text = []
                
                # System metrics
                cpu_percent = psutil.cpu_percent()
                memory = psutil.virtual_memory()
                
                metrics_text.append(f"# HELP system_cpu_usage_percent CPU usage percentage")
                metrics_text.append(f"# TYPE system_cpu_usage_percent gauge")
                metrics_text.append(f"system_cpu_usage_percent {cpu_percent}")
                
                metrics_text.append(f"# HELP system_memory_usage_percent Memory usage percentage")
                metrics_text.append(f"# TYPE system_memory_usage_percent gauge")
                metrics_text.append(f"system_memory_usage_percent {memory.percent}")
                
                # Trading metrics
                if 'position_manager' in self.components:
                    pm = self.components['position_manager']
                    summary = pm.get_position_summary()
                    
                    metrics_text.append(f"# HELP trading_positions_count Number of open positions")
                    metrics_text.append(f"# TYPE trading_positions_count gauge")
                    metrics_text.append(f"trading_positions_count {summary['num_positions']}")
                    
                    metrics_text.append(f"# HELP trading_capital_current Current trading capital")
                    metrics_text.append(f"# TYPE trading_capital_current gauge")
                    metrics_text.append(f"trading_capital_current {summary['current_capital']}")
                
                return JSONResponse(
                    content="\n".join(metrics_text),
                    media_type="text/plain"
                )
                
            except Exception as e:
                logger.error(f"❌ Metrics error: {e}")
                raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# Kubernetes/monitoring health-check API (restored in-tree; previously a
# compat re-export of trading_bot._archive.infrastructure.health_endpoints,
# which violated the production-code no-_archive-import boundary).
# ---------------------------------------------------------------------------

import asyncio
from typing import Any, Callable, Optional
from enum import Enum


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
        warnings.warn("HealthCheckManager is a legacy/quarantined component: loop/capital surface outside the canonical runtime. It carries no production authority.", DeprecationWarning, stacklevel=2)
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
                status_code=200
            )
        else:
            return JSONResponse(
                content={
                    "status": "dead",
                    "timestamp": datetime.now().isoformat()
                },
                status_code=503
            )

    @app.get("/health/ready")
    async def readiness():
        """
        Readiness probe - indicates if the application is ready to serve traffic

        Returns 200 if ready, 503 if not ready
        """
        is_ready = health_manager.is_ready()
        status_code = 200 if is_ready else 503

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
            status_code=200
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
            status_code=200
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
