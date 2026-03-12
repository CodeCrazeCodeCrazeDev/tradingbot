"""
Connection Monitor - Graceful handling of intermittent internet connectivity

This module monitors internet connectivity and implements graceful degradation
when network issues are detected, falling back to cached data and pausing
network-heavy services.
"""

import asyncio
import logging
import time
from typing import Any, Callable, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import socket

logger = logging.getLogger(__name__)


class ConnectionStatus(Enum):
    """Connection status levels."""
    ONLINE = "online"
    DEGRADED = "degraded"
    OFFLINE = "offline"
    UNKNOWN = "unknown"


@dataclass
class ConnectionMetrics:
    """Connection quality metrics."""
    status: ConnectionStatus
    last_check: datetime
    successful_checks: int = 0
    failed_checks: int = 0
    avg_latency_ms: float = 0.0
    uptime_pct: float = 100.0
    consecutive_failures: int = 0


class ConnectionMonitor:
    """
    Monitors internet connectivity and manages graceful degradation.
    
    Features:
    - Periodic connectivity checks
    - Automatic fallback to cached data
    - Service pause/resume based on connectivity
    - Connection quality metrics
    - Configurable check intervals and thresholds
    
    Usage:
        monitor = ConnectionMonitor(check_interval=30)
        await monitor.start()
        
        # Check status
        if monitor.is_online():
            # Make network requests
            pass
        else:
            # Use cached data
            pass
    """
    
    def __init__(
        self,
        check_interval: int = 30,
        check_hosts: List[str] = None,
        timeout: float = 5.0,
        max_consecutive_failures: int = 3,
        degraded_threshold: int = 2
    ):
        """
        Initialize Connection Monitor.
        
        Args:
            check_interval: Seconds between connectivity checks
            check_hosts: List of hosts to check (default: common reliable hosts)
            timeout: Timeout for connectivity checks in seconds
            max_consecutive_failures: Max failures before marking offline
            degraded_threshold: Failures before marking degraded
        """
        self.check_interval = check_interval
        self.check_hosts = check_hosts or [
            '8.8.8.8',  # Google DNS
            '1.1.1.1',  # Cloudflare DNS
            'www.google.com',
            'www.cloudflare.com'
        ]
        self.timeout = timeout
        self.max_consecutive_failures = max_consecutive_failures
        self.degraded_threshold = degraded_threshold
        
        self.metrics = ConnectionMetrics(
            status=ConnectionStatus.UNKNOWN,
            last_check=datetime.now()
        )
        
        self.is_running = False
        self.check_task = None
        
        # Callbacks for status changes
        self.on_online_callbacks: List[Callable] = []
        self.on_degraded_callbacks: List[Callable] = []
        self.on_offline_callbacks: List[Callable] = []
        
        # Services to pause when offline
        self.pausable_services: Dict[str, Any] = {}
        
        logger.info(
            f"ConnectionMonitor initialized: interval={check_interval}s, "
            f"hosts={len(self.check_hosts)}"
        )
    
    async def start(self):
        """Start connection monitoring."""
        if self.is_running:
            logger.warning("ConnectionMonitor already running")
            return
        
        self.is_running = True
        self.check_task = asyncio.create_task(self._monitoring_loop())
        logger.info("ConnectionMonitor started")
    
    async def stop(self):
        """Stop connection monitoring."""
        if not self.is_running:
            return
        
        self.is_running = False
        if self.check_task:
            self.check_task.cancel()
            try:
                await self.check_task
            except asyncio.CancelledError:
                pass
        
        logger.info("ConnectionMonitor stopped")
    
    async def _monitoring_loop(self):
        """Main monitoring loop."""
        while self.is_running:
            try:
                await self._perform_check()
                await asyncio.sleep(self.check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(self.check_interval)
    
    async def _perform_check(self):
        """Perform connectivity check."""
        start_time = time.time()
        
        # Check multiple hosts
        successful_checks = 0
        total_latency = 0.0
        
        for host in self.check_hosts:
            try:
                latency = await self._check_host(host)
                if latency is not None:
                    successful_checks += 1
                    total_latency += latency
            except Exception as e:
                logger.debug(f"Failed to check {host}: {e}")
        
        # Update metrics
        self.metrics.last_check = datetime.now()
        
        if successful_checks > 0:
            self.metrics.successful_checks += 1
            self.metrics.consecutive_failures = 0
            self.metrics.avg_latency_ms = total_latency / successful_checks
            
            # Determine status
            if successful_checks >= len(self.check_hosts) * 0.75:
                new_status = ConnectionStatus.ONLINE
            else:
                new_status = ConnectionStatus.DEGRADED
        else:
            self.metrics.failed_checks += 1
            self.metrics.consecutive_failures += 1
            
            # Determine status based on consecutive failures
            if self.metrics.consecutive_failures >= self.max_consecutive_failures:
                new_status = ConnectionStatus.OFFLINE
            elif self.metrics.consecutive_failures >= self.degraded_threshold:
                new_status = ConnectionStatus.DEGRADED
            else:
                new_status = self.metrics.status  # Keep current status
        
        # Update uptime percentage
        total_checks = self.metrics.successful_checks + self.metrics.failed_checks
        if total_checks > 0:
            self.metrics.uptime_pct = (self.metrics.successful_checks / total_checks) * 100
        
        # Handle status change
        if new_status != self.metrics.status:
            await self._handle_status_change(self.metrics.status, new_status)
            self.metrics.status = new_status
        
        # Log status
        logger.debug(
            f"Connection check: status={self.metrics.status.value}, "
            f"successful={successful_checks}/{len(self.check_hosts)}, "
            f"latency={self.metrics.avg_latency_ms:.1f}ms, "
            f"uptime={self.metrics.uptime_pct:.1f}%"
        )
    
    async def _check_host(self, host: str) -> Optional[float]:
        """
        Check connectivity to a host.
        
        Args:
            host: Hostname or IP address
        
        Returns:
            Latency in milliseconds, or None if failed
        """
        start_time = time.time()
        
        try:
            # Try DNS resolution first
            if not host.replace('.', '').isdigit():  # Not an IP address
                socket.gethostbyname(host)
            
            # Try socket connection
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            
            # Use port 80 for HTTP
            port = 80
            result = sock.connect_ex((host, port))
            sock.close()
            
            latency = (time.time() - start_time) * 1000  # Convert to ms
            
            if result == 0:
                return latency
            else:
                return None
                
        except Exception as e:
            logger.debug(f"Host check failed for {host}: {e}")
            return None
    
    async def _handle_status_change(
        self,
        old_status: ConnectionStatus,
        new_status: ConnectionStatus
    ):
        """Handle connection status change."""
        logger.info(f"Connection status changed: {old_status.value} → {new_status.value}")
        
        # Execute callbacks
        if new_status == ConnectionStatus.ONLINE:
            await self._execute_callbacks(self.on_online_callbacks)
            await self._resume_services()
        elif new_status == ConnectionStatus.DEGRADED:
            await self._execute_callbacks(self.on_degraded_callbacks)
            await self._pause_heavy_services()
        elif new_status == ConnectionStatus.OFFLINE:
            await self._execute_callbacks(self.on_offline_callbacks)
            await self._pause_all_network_services()
    
    async def _execute_callbacks(self, callbacks: List[Callable]):
        """Execute status change callbacks."""
        for callback in callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback()
                else:
                    callback()
            except Exception as e:
                logger.error(f"Error executing callback: {e}")
    
    async def _pause_heavy_services(self):
        """Pause network-heavy services."""
        logger.info("Pausing network-heavy services")
        
        for service_name, service in self.pausable_services.items():
            if hasattr(service, 'pause_heavy_operations'):
                try:
                    service.pause_heavy_operations()
                    logger.info(f"Paused heavy operations for {service_name}")
                except Exception as e:
                    logger.error(f"Error pausing {service_name}: {e}")
    
    async def _pause_all_network_services(self):
        """Pause all network services."""
        logger.warning("Pausing all network services - connection offline")
        
        for service_name, service in self.pausable_services.items():
            if hasattr(service, 'pause'):
                try:
                    service.pause()
                    logger.info(f"Paused {service_name}")
                except Exception as e:
                    logger.error(f"Error pausing {service_name}: {e}")
    
    async def _resume_services(self):
        """Resume paused services."""
        logger.info("Resuming network services - connection restored")
        
        for service_name, service in self.pausable_services.items():
            if hasattr(service, 'resume'):
                try:
                    service.resume()
                    logger.info(f"Resumed {service_name}")
                except Exception as e:
                    logger.error(f"Error resuming {service_name}: {e}")
    
    def register_service(self, name: str, service: Any):
        """
        Register a service for automatic pause/resume.
        
        Service should implement:
        - pause() - Pause all network operations
        - resume() - Resume network operations
        - pause_heavy_operations() - Pause only heavy operations (optional)
        
        Args:
            name: Service name
            service: Service instance
        """
        self.pausable_services[name] = service
        logger.info(f"Registered service: {name}")
    
    def on_online(self, callback: Callable):
        """Register callback for online status."""
        self.on_online_callbacks.append(callback)
    
    def on_degraded(self, callback: Callable):
        """Register callback for degraded status."""
        self.on_degraded_callbacks.append(callback)
    
    def on_offline(self, callback: Callable):
        """Register callback for offline status."""
        self.on_offline_callbacks.append(callback)
    
    def is_online(self) -> bool:
        """Check if connection is online."""
        return self.metrics.status == ConnectionStatus.ONLINE
    
    def is_degraded(self) -> bool:
        """Check if connection is degraded."""
        return self.metrics.status == ConnectionStatus.DEGRADED
    
    def is_offline(self) -> bool:
        """Check if connection is offline."""
        return self.metrics.status == ConnectionStatus.OFFLINE
    
    def get_status(self) -> ConnectionStatus:
        """Get current connection status."""
        return self.metrics.status
    
    def get_metrics(self) -> ConnectionMetrics:
        """Get connection metrics."""
        return self.metrics
    
    def get_status_report(self) -> Dict[str, Any]:
        """Get detailed status report."""
        return {
            'status': self.metrics.status.value,
            'last_check': self.metrics.last_check.isoformat(),
            'successful_checks': self.metrics.successful_checks,
            'failed_checks': self.metrics.failed_checks,
            'consecutive_failures': self.metrics.consecutive_failures,
            'avg_latency_ms': self.metrics.avg_latency_ms,
            'uptime_pct': self.metrics.uptime_pct,
            'registered_services': list(self.pausable_services.keys())
        }


# Convenience function for creating monitor
def create_connection_monitor(**kwargs) -> ConnectionMonitor:
    """
    Factory function to create a ConnectionMonitor.
    
    Args:
        **kwargs: Arguments for ConnectionMonitor constructor
    
    Returns:
        ConnectionMonitor instance
    """
    return ConnectionMonitor(**kwargs)
