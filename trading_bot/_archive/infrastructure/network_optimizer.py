"""
Network Latency Optimizer

Reduces network latency through connection pooling, DNS caching, and request optimization.
"""

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict
import socket
from functools import lru_cache
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class NetworkOptimizer:
    """Optimize network performance and reduce latency"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Configuration
        self.max_latency_ms = self.config.get('max_latency_ms', 100)  # Target: <100ms
        self.connection_pool_size = self.config.get('connection_pool_size', 10)
        self.dns_cache_ttl = self.config.get('dns_cache_ttl', 300)  # 5 minutes
        self.enable_compression = self.config.get('enable_compression', True)
        self.enable_keepalive = self.config.get('enable_keepalive', True)
        self.timeout_seconds = self.config.get('timeout_seconds', 10)
        
        # State
        self.latency_history: Dict[str, List[float]] = defaultdict(list)
        self.dns_cache: Dict[str, str] = {}
        self.dns_cache_time: Dict[str, datetime] = {}
        self.connection_pool: Dict[str, Any] = {}
        
        logger.info(f"Network optimizer initialized - Target latency: {self.max_latency_ms}ms")
    
    @lru_cache(maxsize=1000)
    def resolve_dns(self, hostname: str) -> Optional[str]:
        """
        Resolve DNS with caching
        
        Args:
            hostname: Hostname to resolve
            
        Returns:
            IP address or None
        """
        try:
            # Check cache
            if hostname in self.dns_cache:
                cache_time = self.dns_cache_time.get(hostname)
                if cache_time and (datetime.now() - cache_time).seconds < self.dns_cache_ttl:
                    logger.debug(f"DNS cache hit: {hostname} -> {self.dns_cache[hostname]}")
                    return self.dns_cache[hostname]
            
            # Resolve DNS
            start = time.time()
            ip_address = socket.gethostbyname(hostname)
            latency = (time.time() - start) * 1000
            
            # Cache result
            self.dns_cache[hostname] = ip_address
            self.dns_cache_time[hostname] = datetime.now()
            
            logger.info(f"DNS resolved: {hostname} -> {ip_address} ({latency:.2f}ms)")
            return ip_address
            
        except Exception as e:
            logger.error(f"DNS resolution failed for {hostname}: {e}")
            return None
    
    def measure_latency(self, host: str, port: int = 80) -> float:
        """
        Measure network latency to host
        
        Args:
            host: Target host
            port: Target port
            
        Returns:
            Latency in milliseconds
        """
        try:
            start = time.time()
            
            # Create socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout_seconds)
            
            # Connect
            sock.connect((host, port))
            
            # Measure
            latency = (time.time() - start) * 1000
            
            # Close
            sock.close()
            
            # Record
            self.latency_history[host].append(latency)
            if len(self.latency_history[host]) > 100:
                self.latency_history[host] = self.latency_history[host][-100:]
            
            logger.debug(f"Latency to {host}:{port} = {latency:.2f}ms")
            return latency
            
        except Exception as e:
            logger.error(f"Latency measurement failed for {host}:{port}: {e}")
            return 9999.0  # High value to indicate failure
    
    def get_average_latency(self, host: str) -> float:
        """
        Get average latency for host
        
        Args:
            host: Target host
            
        Returns:
            Average latency in milliseconds
        """
        if host not in self.latency_history or not self.latency_history[host]:
            return 0.0
        
        return sum(self.latency_history[host]) / len(self.latency_history[host])
    
    def is_latency_acceptable(self, host: str) -> bool:
        """
        Check if latency is acceptable
        
        Args:
            host: Target host
            
        Returns:
            True if latency is acceptable
        """
        avg_latency = self.get_average_latency(host)
        return avg_latency < self.max_latency_ms
    
    def optimize_connection(self, url: str) -> Dict[str, Any]:
        """
        Get optimized connection settings
        
        Args:
            url: Target URL
            
        Returns:
            Optimized connection settings
        """
        settings = {
            'timeout': self.timeout_seconds,
            'keepalive': self.enable_keepalive,
            'compression': self.enable_compression,
            'pool_connections': self.connection_pool_size,
            'pool_maxsize': self.connection_pool_size * 2,
            'max_retries': 3,
            'backoff_factor': 0.3,
        }
        
        try:
            # Add DNS resolution
            parsed = urlparse(url)
            if parsed.hostname:
                ip = self.resolve_dns(parsed.hostname)
                if ip:
                    settings['resolved_ip'] = ip
        except Exception as e:
            logger.warning(f"URL parsing failed: {e}")
        
        return settings
    
    def get_latency_stats(self) -> Dict[str, Any]:
        """
        Get latency statistics
        
        Returns:
            Latency statistics
        """
        stats = {}
        
        for host, latencies in self.latency_history.items():
            if latencies:
                stats[host] = {
                    'avg_ms': sum(latencies) / len(latencies),
                    'min_ms': min(latencies),
                    'max_ms': max(latencies),
                    'samples': len(latencies),
                    'acceptable': sum(latencies) / len(latencies) < self.max_latency_ms
                }
        
        return stats
    
    def clear_cache(self):
        """Clear DNS cache"""
        self.dns_cache.clear()
        self.dns_cache_time.clear()
        self.resolve_dns.cache_clear()
        logger.info("DNS cache cleared")
    
    def get_optimization_recommendations(self) -> List[str]:
        """
        Get network optimization recommendations
        
        Returns:
            List of recommendations
        """
        recommendations = []
        
        stats = self.get_latency_stats()
        
        for host, stat in stats.items():
            if stat['avg_ms'] > self.max_latency_ms:
                recommendations.append(
                    f"High latency to {host}: {stat['avg_ms']:.1f}ms (target: <{self.max_latency_ms}ms)"
                )
        
        if not self.enable_keepalive:
            recommendations.append("Enable keepalive connections to reduce latency")
        
        if not self.enable_compression:
            recommendations.append("Enable compression to reduce data transfer time")
        
        if self.connection_pool_size < 10:
            recommendations.append(f"Increase connection pool size (current: {self.connection_pool_size})")
        
        return recommendations


class ConnectionPoolManager:
    """Manage connection pools for different services"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.pools: Dict[str, Any] = {}
        self.max_pool_size = self.config.get('max_pool_size', 20)
        
        logger.info(f"Connection pool manager initialized - Max pool size: {self.max_pool_size}")
    
    def get_pool(self, service: str) -> Any:
        """
        Get or create connection pool for service
        
        Args:
            service: Service name
            
        Returns:
            Connection pool
        """
        if service not in self.pools:
            self.pools[service] = {
                'connections': [],
                'created_at': datetime.now(),
                'usage_count': 0
            }
            logger.info(f"Created connection pool for {service}")
        
        self.pools[service]['usage_count'] += 1
        return self.pools[service]
    
    def close_all(self):
        """Close all connection pools"""
        for service, pool in self.pools.items():
            logger.info(f"Closing pool for {service} (used {pool['usage_count']} times)")
        
        self.pools.clear()


# Singleton instances
_network_optimizer: Optional[NetworkOptimizer] = None
_pool_manager: Optional[ConnectionPoolManager] = None


def get_network_optimizer(config: Optional[Dict[str, Any]] = None) -> NetworkOptimizer:
    """Get singleton network optimizer instance"""
    global _network_optimizer
    if _network_optimizer is None:
        _network_optimizer = NetworkOptimizer(config)
    return _network_optimizer


def get_pool_manager(config: Optional[Dict[str, Any]] = None) -> ConnectionPoolManager:
    """Get singleton pool manager instance"""
    global _pool_manager
    if _pool_manager is None:
        _pool_manager = ConnectionPoolManager(config)
    return _pool_manager


# Utility functions
def optimize_request_settings() -> Dict[str, Any]:
    """Get optimized request settings"""
    return {
        'timeout': 10,
        'allow_redirects': True,
        'verify': True,
        'stream': False,
        'headers': {
            'Connection': 'keep-alive',
            'Accept-Encoding': 'gzip, deflate',
            'User-Agent': 'AlphaAlgo-TradingBot/2.0'
        }
    }


def measure_endpoint_latency(url: str) -> float:
    """
    Quick latency measurement for endpoint
    
    Args:
        url: Endpoint URL
        
    Returns:
        Latency in milliseconds
    """
    optimizer = get_network_optimizer()
    
    try:
        parsed = urlparse(url)
        host = parsed.hostname or 'localhost'
        port = parsed.port or (443 if parsed.scheme == 'https' else 80)
        
        return optimizer.measure_latency(host, port)
    except Exception as e:
        logger.error(f"Latency measurement failed: {e}")
        return 9999.0
