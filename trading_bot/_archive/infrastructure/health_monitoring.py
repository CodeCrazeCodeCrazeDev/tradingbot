"""
from typing import Callable, List, Optional, Set
Health Monitoring & Endpoints

Production-ready health monitoring system:
- Kubernetes-ready health endpoints (/health/live, /health/ready)
- Component health tracking
- Metrics collection
- Alerting integration
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
import threading
from collections import deque

logger = logging.getLogger(__name__)

# Try to import FastAPI for HTTP endpoints
try:
    from fastapi import FastAPI, HTTPException, Response
    from fastapi.responses import JSONResponse
    import uvicorn
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    logger.warning("FastAPI not available. Install with: pip install fastapi uvicorn")


class HealthStatus(Enum):
    """Health status levels"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class ComponentType(Enum):
    """System component types"""
    BROKER = "broker"
    DATA_FEED = "data_feed"
    RISK_MANAGER = "risk_manager"
    SIGNAL_GENERATOR = "signal_generator"
    EXECUTION_ENGINE = "execution_engine"
    DATABASE = "database"
    CACHE = "cache"
    ML_MODEL = "ml_model"
    EXTERNAL_API = "external_api"


@dataclass
class ComponentHealth:
    """Health status of a component"""
    name: str
    component_type: ComponentType
    status: HealthStatus
    last_check: datetime
    response_time_ms: float
    error_count: int
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SystemHealth:
    """Overall system health"""
    status: HealthStatus
    components: Dict[str, ComponentHealth]
    uptime_seconds: float
    version: str
    timestamp: datetime
    
    def to_dict(self) -> Dict:
        return {
            'status': self.status.value,
            'uptime_seconds': self.uptime_seconds,
            'version': self.version,
            'timestamp': self.timestamp.isoformat(),
            'components': {
                name: {
                    'status': comp.status.value,
                    'response_time_ms': comp.response_time_ms,
                    'error_count': comp.error_count,
                    'last_check': comp.last_check.isoformat(),
                    'error_message': comp.error_message
                }
                for name, comp in self.components.items()
            }
        }


class HealthChecker:
    """
    Health checker for individual components.
    """
    
    def __init__(self, name: str, component_type: ComponentType, check_func: Callable):
        """
        Args:
            name: Component name
            component_type: Type of component
            check_func: Async function that returns (healthy: bool, metadata: dict)
        """
        self.name = name
        self.component_type = component_type
        self.check_func = check_func
        self.error_count = 0
        self.last_error: Optional[str] = None
        self.last_check: Optional[datetime] = None
        self.last_response_time: float = 0
    
    async def check(self, timeout: float = 5.0) -> ComponentHealth:
        """Run health check with timeout"""
        start_time = datetime.now()
        
        try:
            # Run check with timeout
            result = await asyncio.wait_for(
                self.check_func(),
                timeout=timeout
            )
            
            healthy, metadata = result if isinstance(result, tuple) else (result, {})
            
            response_time = (datetime.now() - start_time).total_seconds() * 1000
            self.last_response_time = response_time
            self.last_check = datetime.now()
            
            if healthy:
                self.error_count = 0
                self.last_error = None
                status = HealthStatus.HEALTHY
            else:
                self.error_count += 1
                status = HealthStatus.DEGRADED if self.error_count < 3 else HealthStatus.UNHEALTHY
            
            return ComponentHealth(
                name=self.name,
                component_type=self.component_type,
                status=status,
                last_check=self.last_check,
                response_time_ms=response_time,
                error_count=self.error_count,
                error_message=self.last_error,
                metadata=metadata
            )
            
        except asyncio.TimeoutError:
            self.error_count += 1
            self.last_error = "Health check timeout"
            self.last_check = datetime.now()
            
            return ComponentHealth(
                name=self.name,
                component_type=self.component_type,
                status=HealthStatus.UNHEALTHY,
                last_check=self.last_check,
                response_time_ms=timeout * 1000,
                error_count=self.error_count,
                error_message=self.last_error
            )
            
        except Exception as e:
            self.error_count += 1
            self.last_error = str(e)
            self.last_check = datetime.now()
            
            return ComponentHealth(
                name=self.name,
                component_type=self.component_type,
                status=HealthStatus.UNHEALTHY,
                last_check=self.last_check,
                response_time_ms=(datetime.now() - start_time).total_seconds() * 1000,
                error_count=self.error_count,
                error_message=self.last_error
            )


class MetricsCollector:
    """
    Collect and expose metrics for monitoring.
    """
    
    def __init__(self, max_history: int = 1000):
        self.metrics: Dict[str, deque] = {}
        self.max_history = max_history
        self.counters: Dict[str, int] = {}
        self.gauges: Dict[str, float] = {}
    
    def increment(self, name: str, value: int = 1, tags: Dict[str, str] = None):
        """Increment a counter"""
        key = self._make_key(name, tags)
        self.counters[key] = self.counters.get(key, 0) + value
    
    def gauge(self, name: str, value: float, tags: Dict[str, str] = None):
        """Set a gauge value"""
        key = self._make_key(name, tags)
        self.gauges[key] = value
        
        # Also store in history
        if key not in self.metrics:
            self.metrics[key] = deque(maxlen=self.max_history)
        self.metrics[key].append({
            'value': value,
            'timestamp': datetime.now().isoformat()
        })
    
    def histogram(self, name: str, value: float, tags: Dict[str, str] = None):
        """Record a histogram value"""
        key = self._make_key(name, tags)
        if key not in self.metrics:
            self.metrics[key] = deque(maxlen=self.max_history)
        self.metrics[key].append({
            'value': value,
            'timestamp': datetime.now().isoformat()
        })
    
    def _make_key(self, name: str, tags: Dict[str, str] = None) -> str:
        """Create metric key with tags"""
        if not tags:
            return name
        tag_str = ','.join(f'{k}={v}' for k, v in sorted(tags.items()))
        return f"{name}{{{tag_str}}}"
    
    def get_metrics(self) -> Dict:
        """Get all metrics"""
        return {
            'counters': dict(self.counters),
            'gauges': dict(self.gauges),
            'histograms': {k: list(v) for k, v in self.metrics.items()}
        }
    
    def get_prometheus_format(self) -> str:
        """Export metrics in Prometheus format"""
        lines = []
        
        for name, value in self.counters.items():
            lines.append(f"# TYPE {name.split('{')[0]} counter")
            lines.append(f"{name} {value}")
        
        for name, value in self.gauges.items():
            lines.append(f"# TYPE {name.split('{')[0]} gauge")
            lines.append(f"{name} {value}")
        
        return '\n'.join(lines)


class AlertManager:
    """
    Alert management for health issues.
    """
    
    def __init__(self):
        self.alerts: List[Dict] = []
        self.alert_handlers: List[Callable] = []
        self.suppressed_alerts: Dict[str, datetime] = {}
        self.suppression_duration = timedelta(minutes=15)
    
    def add_handler(self, handler: Callable):
        """Add alert handler (e.g., email, Slack, Telegram)"""
        self.alert_handlers.append(handler)
    
    async def fire_alert(
        self,
        name: str,
        severity: str,
        message: str,
        component: Optional[str] = None
    ):
        """Fire an alert"""
        # Check suppression
        alert_key = f"{name}:{component}"
        if alert_key in self.suppressed_alerts:
            if datetime.now() - self.suppressed_alerts[alert_key] < self.suppression_duration:
                logger.debug(f"Alert suppressed: {alert_key}")
                return
        
        alert = {
            'name': name,
            'severity': severity,
            'message': message,
            'component': component,
            'timestamp': datetime.now().isoformat(),
            'acknowledged': False
        }
        
        self.alerts.append(alert)
        self.suppressed_alerts[alert_key] = datetime.now()
        
        logger.warning(f"ALERT [{severity}] {name}: {message}")
        
        # Call handlers
        for handler in self.alert_handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(alert)
                else:
                    handler(alert)
            except Exception as e:
                logger.error(f"Alert handler failed: {e}")
    
    def acknowledge_alert(self, index: int):
        """Acknowledge an alert"""
        if 0 <= index < len(self.alerts):
            self.alerts[index]['acknowledged'] = True
    
    def get_active_alerts(self) -> List[Dict]:
        """Get unacknowledged alerts"""
        return [a for a in self.alerts if not a['acknowledged']]


class HealthMonitoringSystem:
    """
    Complete health monitoring system.
    """
    
    def __init__(
        self,
        version: str = "1.0.0",
        check_interval: int = 30
    ):
        self.version = version
        self.check_interval = check_interval
        self.start_time = datetime.now()
        
        self.checkers: Dict[str, HealthChecker] = {}
        self.metrics = MetricsCollector()
        self.alerts = AlertManager()
        
        self._running = False
        self._check_task: Optional[asyncio.Task] = None
        
        # Last health status
        self._last_health: Optional[SystemHealth] = None
    
    def register_component(
        self,
        name: str,
        component_type: ComponentType,
        check_func: Callable
    ):
        """Register a component for health monitoring"""
        self.checkers[name] = HealthChecker(name, component_type, check_func)
        logger.info(f"Registered health checker: {name}")
    
    async def check_all(self) -> SystemHealth:
        """Run all health checks"""
        components = {}
        
        # Run checks in parallel
        tasks = {
            name: checker.check()
            for name, checker in self.checkers.items()
        }
        
        results = await asyncio.gather(*tasks.values(), return_exceptions=True)
        
        for name, result in zip(tasks.keys(), results):
            if isinstance(result, Exception):
                components[name] = ComponentHealth(
                    name=name,
                    component_type=self.checkers[name].component_type,
                    status=HealthStatus.UNHEALTHY,
                    last_check=datetime.now(),
                    response_time_ms=0,
                    error_count=1,
                    error_message=str(result)
                )
            else:
                components[name] = result
        
        # Determine overall status
        statuses = [c.status for c in components.values()]
        if all(s == HealthStatus.HEALTHY for s in statuses):
            overall_status = HealthStatus.HEALTHY
        elif any(s == HealthStatus.UNHEALTHY for s in statuses):
            overall_status = HealthStatus.UNHEALTHY
        elif any(s == HealthStatus.DEGRADED for s in statuses):
            overall_status = HealthStatus.DEGRADED
        else:
            overall_status = HealthStatus.UNKNOWN
        
        uptime = (datetime.now() - self.start_time).total_seconds()
        
        health = SystemHealth(
            status=overall_status,
            components=components,
            uptime_seconds=uptime,
            version=self.version,
            timestamp=datetime.now()
        )
        
        self._last_health = health
        
        # Update metrics
        self.metrics.gauge('system_health', 1 if overall_status == HealthStatus.HEALTHY else 0)
        self.metrics.gauge('uptime_seconds', uptime)
        
        for name, comp in components.items():
            self.metrics.gauge(
                'component_health',
                1 if comp.status == HealthStatus.HEALTHY else 0,
                tags={'component': name}
            )
            self.metrics.histogram(
                'health_check_duration_ms',
                comp.response_time_ms,
                tags={'component': name}
            )
        
        # Fire alerts for unhealthy components
        for name, comp in components.items():
            if comp.status == HealthStatus.UNHEALTHY:
                await self.alerts.fire_alert(
                    name=f"{name}_unhealthy",
                    severity="critical",
                    message=comp.error_message or "Component unhealthy",
                    component=name
                )
        
        return health
    
    async def start_monitoring(self):
        """Start background health monitoring"""
        self._running = True
        self._check_task = asyncio.create_task(self._monitoring_loop())
        logger.info("Health monitoring started")
    
    async def stop_monitoring(self):
        """Stop background health monitoring"""
        self._running = False
        if self._check_task:
            self._check_task.cancel()
            try:
                await self._check_task
            except asyncio.CancelledError:
                pass
        logger.info("Health monitoring stopped")
    
    async def _monitoring_loop(self):
        """Background monitoring loop"""
        while self._running:
            try:
                await self.check_all()
            except Exception as e:
                logger.error(f"Health check error: {e}")
            
            await asyncio.sleep(self.check_interval)
    
    def get_last_health(self) -> Optional[SystemHealth]:
        """Get last health check result"""
        return self._last_health
    
    def is_healthy(self) -> bool:
        """Quick health check"""
        if not self._last_health:
            return False
        return self._last_health.status == HealthStatus.HEALTHY
    
    def is_ready(self) -> bool:
        """Check if system is ready to serve"""
        if not self._last_health:
            return False
        return self._last_health.status in [HealthStatus.HEALTHY, HealthStatus.DEGRADED]


def create_health_app(monitor: HealthMonitoringSystem) -> Optional[Any]:
    """
    Create FastAPI app with health endpoints.
    
    Endpoints:
    - GET /health/live - Liveness probe (is the process running?)
    - GET /health/ready - Readiness probe (is the system ready to serve?)
    - GET /health - Full health status
    - GET /metrics - Prometheus metrics
    """
    if not FASTAPI_AVAILABLE:
        logger.warning("FastAPI not available, health endpoints disabled")
        return None
    
    app = FastAPI(title="Trading Bot Health", version=monitor.version)
    
    @app.get("/health/live")
    async def liveness():
        """Kubernetes liveness probe"""
        return {"status": "alive"}
    
    @app.get("/health/ready")
    async def readiness():
        """Kubernetes readiness probe"""
        if monitor.is_ready():
            return {"status": "ready"}
        raise HTTPException(status_code=503, detail="Not ready")
    
    @app.get("/health")
    async def health():
        """Full health status"""
        health = await monitor.check_all()
        status_code = 200 if health.status == HealthStatus.HEALTHY else 503
        return JSONResponse(content=health.to_dict(), status_code=status_code)
    
    @app.get("/metrics")
    async def metrics():
        """Prometheus metrics"""
        return Response(
            content=monitor.metrics.get_prometheus_format(),
            media_type="text/plain"
        )
    
    @app.get("/alerts")
    async def alerts():
        """Active alerts"""
        return {"alerts": monitor.alerts.get_active_alerts()}
    
    return app


async def run_health_server(monitor: HealthMonitoringSystem, port: int = 8080):
    """Run health check HTTP server"""
    app = create_health_app(monitor)
    if app:
        config = uvicorn.Config(app, host="0.0.0.0", port=port, log_level="warning")
        server = uvicorn.Server(config)
        await server.serve()


# Example health check functions
async def check_broker_health(broker) -> tuple:
    """Example broker health check"""
    try:
        if broker and hasattr(broker, 'connected') and broker.connected:
            account = await broker.get_account_info()
            return True, {'equity': account.get('equity', 0)}
        return False, {'error': 'Not connected'}
    except Exception as e:
        return False, {'error': str(e)}


async def check_database_health(db_connection) -> tuple:
    """Example database health check"""
    try:
        # Execute simple query
        # await db_connection.execute("SELECT 1")
        return True, {}
    except Exception as e:
        return False, {'error': str(e)}


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    async def main():
        # Create monitoring system
        monitor = HealthMonitoringSystem(version="1.0.0", check_interval=10)
        
        # Register mock components
        async def mock_healthy():
            return True, {'status': 'ok'}
        
        async def mock_unhealthy():
            return False, {'error': 'Connection failed'}
        
        monitor.register_component("broker", ComponentType.BROKER, mock_healthy)
        monitor.register_component("data_feed", ComponentType.DATA_FEED, mock_healthy)
        monitor.register_component("database", ComponentType.DATABASE, mock_unhealthy)
        
        # Run health check
        health = await monitor.check_all()
        
        print("\n" + "="*60)
        logger.info("HEALTH CHECK RESULTS")
        print("="*60)
        logger.info(f"Overall Status: {health.status.value}")
        logger.info(f"Uptime: {health.uptime_seconds:.0f}s")
        logger.info(f"\nComponents:")
        for name, comp in health.components.items():
            logger.info(f"  {name}: {comp.status.value} ({comp.response_time_ms:.1f}ms)")
            if comp.error_message:
                logger.info(f"    Error: {comp.error_message}")
        print("="*60)
        
        # Print metrics
        logger.info(f"\nMetrics:\n{json.dumps(monitor.metrics.get_metrics(), indent=2)}")
    
    asyncio.run(main())
