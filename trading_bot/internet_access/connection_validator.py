"""
Phase 1: Secure Connection Validation System
Tests latency, reliability, and failover for all internet connections.
"""

import asyncio
import time
import logging
import statistics
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
try:
    import aiohttp
except ImportError:
    aiohttp = None
import socket
from datetime import datetime, timedelta

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


class ConnectionStatus(Enum):
    """Connection health status"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    FAILED = "failed"
    UNSTABLE = "unstable"


@dataclass
class ConnectionMetrics:
    """Metrics for a connection endpoint"""
    endpoint: str
    latency_ms: float = 0.0
    packet_loss_pct: float = 0.0
    success_rate: float = 100.0
    last_check: datetime = field(default_factory=datetime.now)
    status: ConnectionStatus = ConnectionStatus.HEALTHY
    consecutive_failures: int = 0
    response_times: List[float] = field(default_factory=list)
    
    def update_status(self):
        """Update connection status based on metrics"""
        if self.packet_loss_pct > 5.0 or self.latency_ms > 150:
            self.status = ConnectionStatus.UNSTABLE
        elif self.success_rate < 90:
            self.status = ConnectionStatus.DEGRADED
        elif self.consecutive_failures >= 3:
            self.status = ConnectionStatus.FAILED
        else:
            self.status = ConnectionStatus.HEALTHY


@dataclass
class EndpointConfig:
    """Configuration for an endpoint to monitor"""
    name: str
    url: str
    backup_url: Optional[str] = None
    timeout: float = 5.0
    critical: bool = True  # If True, trading stops when this fails
    check_interval: int = 30  # seconds


class ConnectionValidator:
    """
    Validates and monitors all internet connections required for trading.
    Implements automatic failover and health monitoring.
    """
    
    def __init__(self, config: Dict):
        self.config = config
        self.endpoints: Dict[str, EndpointConfig] = {}
        self.metrics: Dict[str, ConnectionMetrics] = {}
        self.active_endpoints: Dict[str, str] = {}  # name -> active URL
        self.is_trading_safe = True
        self.monitoring_task: Optional[asyncio.Task] = None
        
        # Initialize endpoints
        self._initialize_endpoints()
        
    def _initialize_endpoints(self):
        """Initialize all monitored endpoints"""
        endpoints_config = self.config.get('endpoints', {})
        
        # Broker data feed
        if 'broker_feed' in endpoints_config:
            self.add_endpoint(EndpointConfig(
                name='broker_feed',
                url=endpoints_config['broker_feed'].get('url'),
                backup_url=endpoints_config['broker_feed'].get('backup_url'),
                critical=True,
                timeout=3.0
            ))
        
        # Economic indicators API
        if 'economic_api' in endpoints_config:
            self.add_endpoint(EndpointConfig(
                name='economic_api',
                url=endpoints_config['economic_api'].get('url'),
                backup_url=endpoints_config['economic_api'].get('backup_url'),
                critical=False,
                timeout=5.0
            ))
        
        # Sentiment/News API
        if 'sentiment_api' in endpoints_config:
            self.add_endpoint(EndpointConfig(
                name='sentiment_api',
                url=endpoints_config['sentiment_api'].get('url'),
                backup_url=endpoints_config['sentiment_api'].get('backup_url'),
                critical=False,
                timeout=5.0
            ))
        
        # Model update repository
        if 'model_repo' in endpoints_config:
            self.add_endpoint(EndpointConfig(
                name='model_repo',
                url=endpoints_config['model_repo'].get('url'),
                backup_url=endpoints_config['model_repo'].get('backup_url'),
                critical=False,
                timeout=10.0
            ))
    
    def add_endpoint(self, endpoint: EndpointConfig):
        """Add an endpoint to monitor"""
        self.endpoints[endpoint.name] = endpoint
        self.metrics[endpoint.name] = ConnectionMetrics(endpoint=endpoint.url)
        self.active_endpoints[endpoint.name] = endpoint.url
        logger.info(f"Added endpoint for monitoring: {endpoint.name} -> {endpoint.url}")
    
    async def check_endpoint(self, name: str) -> Tuple[bool, float]:
        """
        Check a single endpoint for connectivity and latency.
        Returns (success, latency_ms)
        """
        endpoint = self.endpoints.get(name)
        if not endpoint:
            return False, 0.0
        
        url = self.active_endpoints[name]
        start_time = time.time()
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url,
                    timeout=aiohttp.ClientTimeout(total=endpoint.timeout),
                    ssl=True  # Enforce SSL
                ) as response:
                    latency = (time.time() - start_time) * 1000  # Convert to ms
                    success = response.status == 200
                    return success, latency
        
        except asyncio.TimeoutError:
            latency = endpoint.timeout * 1000
            logger.warning(f"Timeout checking {name} at {url}")
            return False, latency
        
        except aiohttp.ClientError as e:
            latency = (time.time() - start_time) * 1000
            logger.error(f"Connection error for {name}: {e}")
            return False, latency
        
        except Exception as e:
            latency = (time.time() - start_time) * 1000
            logger.error(f"Unexpected error checking {name}: {e}")
            return False, latency
    
    async def check_all_endpoints(self) -> Dict[str, ConnectionMetrics]:
        """Check all endpoints concurrently"""
        tasks = []
        endpoint_names = []
        
        for name in self.endpoints.keys():
            tasks.append(self.check_endpoint(name))
            endpoint_names.append(name)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Update metrics
        for name, result in zip(endpoint_names, results):
            if isinstance(result, Exception):
                success, latency = False, 0.0
                logger.error(f"Exception checking {name}: {result}")
            else:
                success, latency = result
            
            self._update_metrics(name, success, latency)
        
        return self.metrics
    
    def _update_metrics(self, name: str, success: bool, latency: float):
        """Update metrics for an endpoint"""
        metrics = self.metrics[name]
        
        # Update response times (keep last 100)
        metrics.response_times.append(latency)
        if len(metrics.response_times) > 100:
            metrics.response_times.pop(0)
        
        # Calculate statistics
        if metrics.response_times:
            metrics.latency_ms = statistics.mean(metrics.response_times)
        
        # Update success tracking
        if success:
            metrics.consecutive_failures = 0
            # Calculate success rate over last 100 attempts
            recent_successes = sum(1 for rt in metrics.response_times if rt < 1000)
            metrics.success_rate = (recent_successes / len(metrics.response_times)) * 100
        else:
            metrics.consecutive_failures += 1
            metrics.success_rate = max(0, metrics.success_rate - 1)
        
        # Calculate packet loss (approximation based on failures)
        metrics.packet_loss_pct = 100 - metrics.success_rate
        
        metrics.last_check = datetime.now()
        metrics.update_status()
        
        # Log status changes
        if metrics.status != ConnectionStatus.HEALTHY:
            logger.warning(
                f"{name} status: {metrics.status.value} "
                f"(latency: {metrics.latency_ms:.1f}ms, "
                f"loss: {metrics.packet_loss_pct:.1f}%, "
                f"failures: {metrics.consecutive_failures})"
            )
    
    async def attempt_failover(self, name: str) -> bool:
        """Attempt to switch to backup endpoint"""
        endpoint = self.endpoints.get(name)
        if not endpoint or not endpoint.backup_url:
            return False
        
        current_url = self.active_endpoints[name]
        
        # Already on backup?
        if current_url == endpoint.backup_url:
            logger.error(f"Backup endpoint for {name} also failed")
            return False
        
        logger.warning(f"Attempting failover for {name} to backup: {endpoint.backup_url}")
        
        # Switch to backup
        self.active_endpoints[name] = endpoint.backup_url
        self.metrics[name] = ConnectionMetrics(endpoint=endpoint.backup_url)
        
        # Test backup
        success, latency = await self.check_endpoint(name)
        
        if success:
            logger.info(f"Failover successful for {name}")
            return True
        else:
            logger.error(f"Failover failed for {name}")
            return False
    
    def is_trading_allowed(self) -> Tuple[bool, str]:
        """
        Determine if trading should be allowed based on connection health.
        Returns (allowed, reason)
        """
        critical_failures = []
        
        for name, endpoint in self.endpoints.items():
            if not endpoint.critical:
                continue
            
            metrics = self.metrics.get(name)
            if not metrics:
                continue
            
            # Check critical thresholds
            if metrics.status == ConnectionStatus.FAILED:
                critical_failures.append(f"{name}: FAILED")
            elif metrics.latency_ms > 150:
                critical_failures.append(f"{name}: High latency ({metrics.latency_ms:.0f}ms)")
            elif metrics.packet_loss_pct > 5:
                critical_failures.append(f"{name}: Packet loss ({metrics.packet_loss_pct:.1f}%)")
        
        if critical_failures:
            reason = "Critical connection issues: " + ", ".join(critical_failures)
            return False, reason
        
        return True, "All critical connections healthy"
    
    async def monitor_connections(self):
        """Continuously monitor all connections"""
        logger.info("Starting connection monitoring...")
        
        while True:
            try:
                # Check all endpoints
                await self.check_all_endpoints()
                
                # Attempt failover for failed endpoints
                for name, metrics in self.metrics.items():
                    if metrics.status == ConnectionStatus.FAILED:
                        await self.attempt_failover(name)
                
                # Update trading safety flag
                allowed, reason = self.is_trading_allowed()
                
                if allowed != self.is_trading_safe:
                    self.is_trading_safe = allowed
                    if allowed:
                        logger.info(f"✅ Trading ENABLED: {reason}")
                    else:
                        logger.critical(f"🛑 Trading DISABLED: {reason}")
                
                # Wait before next check
                await asyncio.sleep(30)
            
            except Exception as e:
                logger.error(f"Error in connection monitoring: {e}")
                await asyncio.sleep(5)
    
    async def start_monitoring(self):
        """Start the monitoring task"""
        if self.monitoring_task and not self.monitoring_task.done():
            logger.warning("Monitoring already running")
            return
        
        self.monitoring_task = asyncio.create_task(self.monitor_connections())
        logger.info("Connection monitoring started")
    
    async def stop_monitoring(self):
        """Stop the monitoring task"""
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
            logger.info("Connection monitoring stopped")
    
    def get_status_report(self) -> Dict:
        """Generate a comprehensive status report"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'trading_allowed': self.is_trading_safe,
            'endpoints': {}
        }
        
        for name, metrics in self.metrics.items():
            endpoint = self.endpoints[name]
            report['endpoints'][name] = {
                'status': metrics.status.value,
                'active_url': self.active_endpoints[name],
                'latency_ms': round(metrics.latency_ms, 2),
                'packet_loss_pct': round(metrics.packet_loss_pct, 2),
                'success_rate': round(metrics.success_rate, 2),
                'consecutive_failures': metrics.consecutive_failures,
                'critical': endpoint.critical,
                'last_check': metrics.last_check.isoformat()
            }
        
        return report
    
    async def validate_initial_connection(self) -> bool:
        """
        Perform initial connection validation before starting trading.
        Returns True if all critical connections are healthy.
        """
        logger.info("🌐 Performing initial connection validation...")
        
        # Check all endpoints
        await self.check_all_endpoints()
        
        # Check if trading is allowed
        allowed, reason = self.is_trading_allowed()
        
        if allowed:
            logger.info(f"✅ Initial validation PASSED: {reason}")
            self.is_trading_safe = True
            return True
        else:
            logger.error(f"❌ Initial validation FAILED: {reason}")
            
            # Attempt failover for failed critical endpoints
            for name, endpoint in self.endpoints.items():
                if endpoint.critical and self.metrics[name].status == ConnectionStatus.FAILED:
                    logger.info(f"Attempting failover for critical endpoint: {name}")
                    await self.attempt_failover(name)
            
            # Re-check after failover attempts
            await self.check_all_endpoints()
            allowed, reason = self.is_trading_allowed()
            
            if allowed:
                logger.info(f"✅ Validation PASSED after failover: {reason}")
                self.is_trading_safe = True
                return True
            else:
                logger.critical(f"❌ Validation FAILED even after failover: {reason}")
                self.is_trading_safe = False
                return False
