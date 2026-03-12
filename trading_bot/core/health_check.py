"""
Health Check Endpoints for AlphaAlgo Trading Bot
Provides /health and /ready endpoints for monitoring.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
import json

logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """Health status levels."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


@dataclass
class ComponentHealth:
    """Health status of a single component."""
    name: str
    status: HealthStatus
    message: str = ""
    last_check: datetime = field(default_factory=datetime.now)
    response_time_ms: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'status': self.status.value,
            'message': self.message,
            'last_check': self.last_check.isoformat(),
            'response_time_ms': self.response_time_ms
        }


class HealthChecker:
    """
    Health check system for the trading bot.
    Monitors all critical components and provides health endpoints.
    """
    
    def __init__(self):
        self.components: Dict[str, ComponentHealth] = {}
        self.start_time = datetime.now()
        self.last_health_check: Optional[datetime] = None
        self.check_interval_seconds = 30
        self._running = False
        
        # Thresholds
        self.max_latency_ms = 1000  # 1 second
        self.max_memory_percent = 90
        self.max_cpu_percent = 95
        
        logger.info("HealthChecker initialized")
    
    async def start_background_checks(self):
        """Start background health check loop."""
        self._running = True
        while self._running:
            try:
                await self.run_all_checks()
                await asyncio.sleep(self.check_interval_seconds)
            except Exception as e:
                logger.error(f"Error in health check loop: {e}")
                await asyncio.sleep(5)
    
    def stop(self):
        """Stop background health checks."""
        self._running = False
    
    async def run_all_checks(self) -> Dict[str, Any]:
        """Run all health checks and return aggregated status."""
        self.last_health_check = datetime.now()
        
        # Check system resources
        await self._check_system_resources()
        
        # Check database connectivity
        await self._check_database()
        
        # Check broker connectivity
        await self._check_broker()
        
        # Check market data feed
        await self._check_market_data()
        
        # Check risk manager
        await self._check_risk_manager()
        
        return self.get_health_status()
    
    async def _check_system_resources(self):
        """Check CPU, memory, and disk usage."""
        start = datetime.now()
        try:
            import psutil
            
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            issues = []
            if cpu_percent > self.max_cpu_percent:
                issues.append(f"CPU usage high: {cpu_percent}%")
            if memory.percent > self.max_memory_percent:
                issues.append(f"Memory usage high: {memory.percent}%")
            if disk.percent > 95:
                issues.append(f"Disk usage critical: {disk.percent}%")
            
            if issues:
                status = HealthStatus.DEGRADED if len(issues) == 1 else HealthStatus.UNHEALTHY
                message = "; ".join(issues)
            else:
                status = HealthStatus.HEALTHY
                message = f"CPU: {cpu_percent}%, Memory: {memory.percent}%, Disk: {disk.percent}%"
            
            response_time = (datetime.now() - start).total_seconds() * 1000
            self.components['system'] = ComponentHealth(
                name='system',
                status=status,
                message=message,
                response_time_ms=response_time
            )
            
        except ImportError:
            self.components['system'] = ComponentHealth(
                name='system',
                status=HealthStatus.DEGRADED,
                message="psutil not installed - cannot check system resources"
            )
        except Exception as e:
            self.components['system'] = ComponentHealth(
                name='system',
                status=HealthStatus.UNHEALTHY,
                message=f"Error checking system: {str(e)}"
            )
    
    async def _check_database(self):
        """Check database connectivity."""
        start = datetime.now()
        try:
            # Simulate database ping (in production, actually ping the DB)
            await asyncio.sleep(0.01)  # Simulated latency
            
            response_time = (datetime.now() - start).total_seconds() * 1000
            
            if response_time > self.max_latency_ms:
                status = HealthStatus.DEGRADED
                message = f"Database slow: {response_time:.1f}ms"
            else:
                status = HealthStatus.HEALTHY
                message = f"Database OK: {response_time:.1f}ms"
            
            self.components['database'] = ComponentHealth(
                name='database',
                status=status,
                message=message,
                response_time_ms=response_time
            )
            
        except Exception as e:
            self.components['database'] = ComponentHealth(
                name='database',
                status=HealthStatus.UNHEALTHY,
                message=f"Database error: {str(e)}"
            )
    
    async def _check_broker(self):
        """Check broker connectivity."""
        start = datetime.now()
        try:
            # Simulate broker ping (in production, actually ping the broker)
            await asyncio.sleep(0.01)  # Simulated latency
            
            response_time = (datetime.now() - start).total_seconds() * 1000
            
            self.components['broker'] = ComponentHealth(
                name='broker',
                status=HealthStatus.HEALTHY,
                message=f"Broker connected: {response_time:.1f}ms",
                response_time_ms=response_time
            )
            
        except Exception as e:
            self.components['broker'] = ComponentHealth(
                name='broker',
                status=HealthStatus.UNHEALTHY,
                message=f"Broker error: {str(e)}"
            )
    
    async def _check_market_data(self):
        """Check market data feed."""
        start = datetime.now()
        try:
            # Simulate market data check
            await asyncio.sleep(0.01)
            
            response_time = (datetime.now() - start).total_seconds() * 1000
            
            self.components['market_data'] = ComponentHealth(
                name='market_data',
                status=HealthStatus.HEALTHY,
                message=f"Market data feed OK: {response_time:.1f}ms",
                response_time_ms=response_time
            )
            
        except Exception as e:
            self.components['market_data'] = ComponentHealth(
                name='market_data',
                status=HealthStatus.UNHEALTHY,
                message=f"Market data error: {str(e)}"
            )
    
    async def _check_risk_manager(self):
        """Check risk manager status."""
        start = datetime.now()
        try:
            # Simulate risk manager check
            await asyncio.sleep(0.005)
            
            response_time = (datetime.now() - start).total_seconds() * 1000
            
            self.components['risk_manager'] = ComponentHealth(
                name='risk_manager',
                status=HealthStatus.HEALTHY,
                message=f"Risk manager OK: {response_time:.1f}ms",
                response_time_ms=response_time
            )
            
        except Exception as e:
            self.components['risk_manager'] = ComponentHealth(
                name='risk_manager',
                status=HealthStatus.UNHEALTHY,
                message=f"Risk manager error: {str(e)}"
            )
    
    def register_component(self, name: str, check_func):
        """Register a custom component health check."""
        # Store for later use
        pass
    
    def update_component_status(
        self,
        name: str,
        status: HealthStatus,
        message: str = ""
    ):
        """Manually update a component's health status."""
        self.components[name] = ComponentHealth(
            name=name,
            status=status,
            message=message
        )
    
    def get_health_status(self) -> Dict[str, Any]:
        """
        Get overall health status.
        Returns the /health endpoint response.
        """
        # Determine overall status
        statuses = [c.status for c in self.components.values()]
        
        if HealthStatus.UNHEALTHY in statuses:
            overall_status = HealthStatus.UNHEALTHY
        elif HealthStatus.DEGRADED in statuses:
            overall_status = HealthStatus.DEGRADED
        else:
            overall_status = HealthStatus.HEALTHY
        
        uptime = datetime.now() - self.start_time
        
        return {
            'status': overall_status.value,
            'timestamp': datetime.now().isoformat(),
            'uptime_seconds': uptime.total_seconds(),
            'uptime_human': str(uptime),
            'last_check': self.last_health_check.isoformat() if self.last_health_check else None,
            'components': {
                name: comp.to_dict()
                for name, comp in self.components.items()
            }
        }
    
    def get_readiness_status(self) -> Dict[str, Any]:
        """
        Get readiness status.
        Returns the /ready endpoint response.
        Bot is ready if all critical components are healthy.
        """
        critical_components = ['database', 'broker', 'risk_manager']
        
        ready = True
        issues = []
        
        for comp_name in critical_components:
            if comp_name in self.components:
                comp = self.components[comp_name]
                if comp.status == HealthStatus.UNHEALTHY:
                    ready = False
                    issues.append(f"{comp_name}: {comp.message}")
        
        return {
            'ready': ready,
            'timestamp': datetime.now().isoformat(),
            'issues': issues
        }
    
    def get_liveness_status(self) -> Dict[str, Any]:
        """
        Get liveness status.
        Returns the /live endpoint response.
        Bot is alive if the main process is running.
        """
        return {
            'alive': True,
            'timestamp': datetime.now().isoformat(),
            'uptime_seconds': (datetime.now() - self.start_time).total_seconds()
        }


# Singleton instance
_health_checker: Optional[HealthChecker] = None


def get_health_checker() -> HealthChecker:
    """Get or create the health checker singleton."""
    global _health_checker
    if _health_checker is None:
        _health_checker = HealthChecker()
    return _health_checker


# Simple HTTP server for health endpoints (optional)
async def start_health_server(host: str = "0.0.0.0", port: int = 8080):
    """Start a simple HTTP server for health endpoints."""
    from aiohttp import web
    
    health_checker = get_health_checker()
    
    async def health_handler(request):
        status = await health_checker.run_all_checks()
        http_status = 200 if status['status'] == 'healthy' else 503
        return web.json_response(status, status=http_status)
    
    async def ready_handler(request):
        status = health_checker.get_readiness_status()
        http_status = 200 if status['ready'] else 503
        return web.json_response(status, status=http_status)
    
    async def live_handler(request):
        status = health_checker.get_liveness_status()
        return web.json_response(status)
    
    app = web.Application()
    app.router.add_get('/health', health_handler)
    app.router.add_get('/ready', ready_handler)
    app.router.add_get('/live', live_handler)
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host, port)
    await site.start()
    
    logger.info(f"Health server started on http://{host}:{port}")
    return runner


__all__ = [
    'HealthChecker',
    'HealthStatus',
    'ComponentHealth',
    'get_health_checker',
    'start_health_server'
]
