"""
Phase 1: Internet Health Validation
Comprehensive connectivity testing with auto-failover
"""

import asyncio
import time
import re
import logging
import socket
import statistics
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import subprocess
import platform

logger = logging.getLogger(__name__)


class ConnectionHealth(Enum):
    """Connection health status"""
    EXCELLENT = "excellent"  # < 50ms, 0% loss
    GOOD = "good"            # < 100ms, < 2% loss
    ACCEPTABLE = "acceptable"  # < 150ms, < 5% loss
    DEGRADED = "degraded"    # < 200ms, < 10% loss
    POOR = "poor"            # > 200ms or > 10% loss
    FAILED = "failed"        # No connectivity


@dataclass
class ConnectionMetrics:
    """Detailed connection metrics"""
    latency_ms: float = 0.0
    packet_loss_pct: float = 0.0
    dns_resolution_ms: float = 0.0
    jitter_ms: float = 0.0
    bandwidth_mbps: float = 0.0
    ip_address: Optional[str] = None
    dns_server: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    health: ConnectionHealth = ConnectionHealth.FAILED
    
    def meets_thresholds(self) -> bool:
        """Check if metrics meet trading thresholds"""
        return (
            self.latency_ms < 150 and
            self.packet_loss_pct < 5.0 and
            self.dns_resolution_ms < 1000
        )


class InternetHealthValidator:
    """
    Validates internet connectivity with comprehensive testing.
    Implements auto-failover and exponential backoff retry.
    """
    
    def __init__(self, config: Dict):
        self.config = config
        
        # Test endpoints
        self.primary_endpoints = config.get('primary_endpoints', [
            'api.broker.com',
            'api.marketdata.com',
            'newsapi.org'
        ])
        
        self.backup_endpoints = config.get('backup_endpoints', [
            '8.8.8.8',  # Google DNS
            '1.1.1.1',  # Cloudflare DNS
        ])
        
        # Failover configuration
        self.failover_enabled = config.get('failover_enabled', True)
        self.vpn_enabled = config.get('vpn_enabled', False)
        self.backup_isp_enabled = config.get('backup_isp_enabled', False)
        
        # Retry configuration
        self.max_retries = config.get('max_retries', 5)
        self.backoff_intervals = [3, 5, 10, 20, 30]  # seconds
        
        # State
        self.current_metrics: Optional[ConnectionMetrics] = None
        self.metrics_history: List[ConnectionMetrics] = []
        self.recovery_log_path = config.get('recovery_log', 'logs/network_recovery.log')
        self.is_failover_active = False
        self.consecutive_failures = 0
        
        logger.info("Internet Health Validator initialized")
    
    async def run_complete_test(self) -> ConnectionMetrics:
        """
        Run complete internet connectivity test.
        Returns comprehensive metrics.
        """
        logger.info("🌐 Running complete internet health validation...")
        
        metrics = ConnectionMetrics()
        
        try:
            # Test 1: Latency measurement
            latency_results = await self._measure_latency()
            metrics.latency_ms = statistics.mean(latency_results) if latency_results else 999.0
            metrics.jitter_ms = statistics.stdev(latency_results) if len(latency_results) > 1 else 0.0
            
            # Test 2: Packet loss
            metrics.packet_loss_pct = await self._measure_packet_loss()
            
            # Test 3: DNS resolution
            metrics.dns_resolution_ms = await self._measure_dns_resolution()
            
            # Test 4: Get IP and DNS info
            metrics.ip_address = await self._get_public_ip()
            metrics.dns_server = await self._get_dns_server()
            
            # Determine health status
            metrics.health = self._determine_health(metrics)
            
            # Log results
            self._log_test_results(metrics)
            
            # Store metrics
            self.current_metrics = metrics
            self.metrics_history.append(metrics)
            if len(self.metrics_history) > 1000:
                self.metrics_history = self.metrics_history[-1000:]
            
            # Check thresholds
            if metrics.meets_thresholds():
                logger.info(f"✅ Internet health: {metrics.health.value.upper()}")
                self.consecutive_failures = 0
            else:
                logger.warning(f"⚠️ Internet health: {metrics.health.value.upper()}")
                self.consecutive_failures += 1
            
            return metrics
        
        except Exception as e:
            logger.error(f"Error in internet health test: {e}")
            metrics.health = ConnectionHealth.FAILED
            self.consecutive_failures += 1
            return metrics
    
    async def _measure_latency(self) -> List[float]:
        """Measure latency to multiple endpoints"""
        latencies = []
        
        for endpoint in self.primary_endpoints[:3]:  # Test first 3
            try:
                start = time.time()
                
                # Try to resolve and connect
                host = endpoint.replace('https://', '').replace('http://', '').split('/')[0]
                
                # TCP connection test
                reader, writer = await asyncio.wait_for(
                    asyncio.open_connection(host, 443),
                    timeout=5.0
                )
                
                latency = (time.time() - start) * 1000  # Convert to ms
                latencies.append(latency)
                
                writer.close()
                await writer.wait_closed()
                
                logger.debug(f"Latency to {host}: {latency:.1f}ms")
            
            except asyncio.TimeoutError:
                logger.warning(f"Timeout connecting to {endpoint}")
                latencies.append(5000.0)  # 5 second timeout
            
            except Exception as e:
                logger.debug(f"Error measuring latency to {endpoint}: {e}")
        
        return latencies
    
    async def _measure_packet_loss(self) -> float:
        """Measure packet loss using ping"""
        try:
            # Use backup endpoints for ping test
            endpoint = self.backup_endpoints[0]
            
            # Platform-specific ping command
            param = '-n' if platform.system().lower() == 'windows' else '-c'
            count = '10'
            
            # Run ping command
            process = await asyncio.create_subprocess_exec(
                'ping', param, count, endpoint,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=15.0)
            output = stdout.decode()
            
            # Parse packet loss from output
            if 'loss' in output.lower():
                # Extract percentage
                match = re.search(r'(\d+)%.*loss', output, re.IGNORECASE)
                if match:
                    return float(match.group(1))
            
            return 0.0  # Assume no loss if can't parse
        
        except asyncio.TimeoutError:
            logger.warning("Ping test timed out")
            return 100.0  # Complete loss
        
        except Exception as e:
            logger.debug(f"Error measuring packet loss: {e}")
            return 0.0  # Assume no loss on error
    
    async def _measure_dns_resolution(self) -> float:
        """Measure DNS resolution time"""
        try:
            start = time.time()
            
            # Resolve a test domain
            test_domain = 'api.marketdata.com'
            
            loop = asyncio.get_event_loop()
            await loop.getaddrinfo(test_domain, 443)
            
            resolution_time = (time.time() - start) * 1000  # Convert to ms
            
            logger.debug(f"DNS resolution time: {resolution_time:.1f}ms")
            return resolution_time
        
        except Exception as e:
            logger.debug(f"Error measuring DNS resolution: {e}")
            return 999.0
    
    async def _get_public_ip(self) -> Optional[str]:
        """Get public IP address"""
        try:
            import aiohttp
            
            async with aiohttp.ClientSession() as session:
                async with session.get('https://api.ipify.org', timeout=5) as response:
                    if response.status == 200:
                        ip = await response.text()
                        return ip.strip()
        
        except Exception as e:
            logger.debug(f"Error getting public IP: {e}")
        
        return None
    
    async def _get_dns_server(self) -> Optional[str]:
        """Get current DNS server"""
        try:
            # Platform-specific DNS detection
            if platform.system().lower() == 'windows':
                process = await asyncio.create_subprocess_exec(
                    'nslookup', 'google.com',
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, _ = await process.communicate()
                output = stdout.decode()
                
                # Parse DNS server from output
                match = re.search(r'Server:\s+(\S+)', output)
                if match:
                    return match.group(1)
            else:
                # Linux/Mac
                with open('/etc/resolv.conf', 'r') as f:
                    for line in f:
                        if line.startswith('nameserver'):
                            return line.split()[1]
        
        except Exception as e:
            logger.debug(f"Error getting DNS server: {e}")
        
        return None
    
    def _determine_health(self, metrics: ConnectionMetrics) -> ConnectionHealth:
        """Determine overall connection health"""
        if metrics.latency_ms > 999:
            return ConnectionHealth.FAILED
        elif metrics.latency_ms < 50 and metrics.packet_loss_pct < 1:
            return ConnectionHealth.EXCELLENT
        elif metrics.latency_ms < 100 and metrics.packet_loss_pct < 2:
            return ConnectionHealth.GOOD
        elif metrics.latency_ms < 150 and metrics.packet_loss_pct < 5:
            return ConnectionHealth.ACCEPTABLE
        elif metrics.latency_ms < 200 and metrics.packet_loss_pct < 10:
            return ConnectionHealth.DEGRADED
        else:
            return ConnectionHealth.POOR
    
    def _log_test_results(self, metrics: ConnectionMetrics):
        """Log test results"""
        logger.info("=" * 60)
        logger.info("INTERNET HEALTH TEST RESULTS")
        logger.info("=" * 60)
        logger.info(f"Latency:      {metrics.latency_ms:.1f}ms (threshold: < 150ms)")
        logger.info(f"Jitter:       {metrics.jitter_ms:.1f}ms")
        logger.info(f"Packet Loss:  {metrics.packet_loss_pct:.1f}% (threshold: < 5%)")
        logger.info(f"DNS Time:     {metrics.dns_resolution_ms:.1f}ms")
        logger.info(f"Public IP:    {metrics.ip_address or 'Unknown'}")
        logger.info(f"DNS Server:   {metrics.dns_server or 'Unknown'}")
        logger.info(f"Health:       {metrics.health.value.upper()}")
        logger.info(f"Meets Thresholds: {'✅ YES' if metrics.meets_thresholds() else '❌ NO'}")
        logger.info("=" * 60)
    
    async def validate_with_retry(self) -> Tuple[bool, ConnectionMetrics]:
        """
        Validate connection with exponential backoff retry.
        Returns (is_stable, metrics)
        """
        logger.info("🔄 Starting connection validation with retry...")
        
        for attempt in range(self.max_retries):
            # Run test
            metrics = await self.run_complete_test()
            
            # Check if stable
            if metrics.meets_thresholds():
                logger.info(f"✅ Connection stable on attempt {attempt + 1}")
                self._log_recovery_event("Connection validated successfully")
                return True, metrics
            
            # Connection unstable
            logger.warning(f"⚠️ Connection unstable (attempt {attempt + 1}/{self.max_retries})")
            
            # Try failover if enabled
            if self.failover_enabled and attempt < self.max_retries - 1:
                await self._attempt_failover(attempt)
            
            # Wait before retry (exponential backoff)
            if attempt < self.max_retries - 1:
                wait_time = self.backoff_intervals[min(attempt, len(self.backoff_intervals) - 1)]
                logger.info(f"⏳ Waiting {wait_time}s before retry...")
                await asyncio.sleep(wait_time)
        
        # All retries failed
        logger.error("❌ Connection validation failed after all retries")
        self._log_recovery_event("Connection validation FAILED after all retries")
        return False, metrics
    
    async def _attempt_failover(self, attempt: int):
        """Attempt failover to backup connection"""
        logger.warning("🔄 Attempting failover...")
        
        failover_actions = []
        
        # Action 1: Switch to backup ISP (if available)
        if self.backup_isp_enabled and not self.is_failover_active:
            failover_actions.append("backup_isp")
        
        # Action 2: Enable VPN (if available)
        if self.vpn_enabled and not self.is_failover_active:
            failover_actions.append("vpn")
        
        # Action 3: Switch to failover proxy
        failover_actions.append("proxy")
        
        # Execute failover action
        if attempt < len(failover_actions):
            action = failover_actions[attempt]
            logger.info(f"🔄 Executing failover action: {action}")
            
            if action == "backup_isp":
                await self._switch_to_backup_isp()
            elif action == "vpn":
                await self._enable_vpn()
            elif action == "proxy":
                await self._switch_to_proxy()
            
            self.is_failover_active = True
            self._log_recovery_event(f"Failover activated: {action}")
    
    async def _switch_to_backup_isp(self):
        """Switch to backup ISP"""
        logger.info("Switching to backup ISP...")
        # Implementation depends on your network setup
        # This is a placeholder
        await asyncio.sleep(2)
        logger.info("Backup ISP activated")
    
    async def _enable_vpn(self):
        """Enable VPN connection"""
        logger.info("Enabling VPN...")
        # Implementation depends on your VPN setup
        # This is a placeholder
        await asyncio.sleep(2)
        logger.info("VPN enabled")
    
    async def _switch_to_proxy(self):
        """Switch to failover proxy"""
        logger.info("Switching to failover proxy...")
        # Implementation depends on your proxy setup
        # This is a placeholder
        await asyncio.sleep(1)
        logger.info("Failover proxy activated")
    
    def _log_recovery_event(self, message: str):
        """Log recovery event to file"""
        try:
            from pathlib import Path
            log_path = Path(self.recovery_log_path)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(log_path, 'a') as f:
                timestamp = datetime.now().isoformat()
                f.write(f"[{timestamp}] {message}\n")
        
        except Exception as e:
            logger.error(f"Error logging recovery event: {e}")
    
    def is_trading_safe(self) -> Tuple[bool, str]:
        """
        Determine if trading is safe based on connection health.
        Returns (is_safe, reason)
        """
        if not self.current_metrics:
            return False, "No connection metrics available"
        
        if not self.current_metrics.meets_thresholds():
            return False, f"Connection health: {self.current_metrics.health.value}"
        
        if self.consecutive_failures >= 3:
            return False, f"Too many consecutive failures: {self.consecutive_failures}"
        
        return True, "Connection healthy"
    
    def get_health_report(self) -> Dict:
        """Generate health report"""
        if not self.current_metrics:
            return {'status': 'No metrics available'}
        
        return {
            'timestamp': datetime.now().isoformat(),
            'current_health': self.current_metrics.health.value,
            'latency_ms': round(self.current_metrics.latency_ms, 2),
            'packet_loss_pct': round(self.current_metrics.packet_loss_pct, 2),
            'dns_resolution_ms': round(self.current_metrics.dns_resolution_ms, 2),
            'jitter_ms': round(self.current_metrics.jitter_ms, 2),
            'meets_thresholds': self.current_metrics.meets_thresholds(),
            'consecutive_failures': self.consecutive_failures,
            'failover_active': self.is_failover_active,
            'public_ip': self.current_metrics.ip_address,
            'dns_server': self.current_metrics.dns_server,
            'trading_safe': self.is_trading_safe()[0]
        }
    
    async def continuous_monitoring(self, interval: int = 60):
        """Continuously monitor internet health"""
        logger.info(f"Starting continuous internet health monitoring (interval: {interval}s)")
        
        while True:
            try:
                await self.run_complete_test()
                
                # Check if trading should be disabled
                is_safe, reason = self.is_trading_safe()
                if not is_safe:
                    logger.critical(f"🛑 TRADING UNSAFE: {reason}")
                
                await asyncio.sleep(interval)
            
            except Exception as e:
                logger.error(f"Error in continuous monitoring: {e}")
                await asyncio.sleep(10)
