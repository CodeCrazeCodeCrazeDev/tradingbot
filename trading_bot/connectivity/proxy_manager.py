"""
from pathlib import Path
Elite Trading Bot - Proxy Manager

This module provides proxy management and IP rotation capabilities for the
Elite Trading Bot's internet connectivity, helping to avoid rate limits and IP bans.
"""

import asyncio
import json
import logging
import random
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple
import os
try:
    import aiohttp
except ImportError:
    aiohttp = None

try:
    import requests
except ImportError:
    requests = None
import pathlib

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


class ProxyStatus:
    """Status information for a proxy."""
    
    def __init__(self):
        """Initialize proxy status."""
        self.last_used = 0.0
        self.success_count = 0
        self.failure_count = 0
        self.last_latency = 0.0
        self.avg_latency = 0.0
        self.banned_until = None
        self.last_checked = 0.0
    
    def record_success(self, latency: float):
        """
        Record a successful request.
        
        Args:
            latency: Request latency in seconds
        """
        self.last_used = time.time()
        self.success_count += 1
        self.last_latency = latency
        
        # Update average latency
        if self.avg_latency == 0.0:
            self.avg_latency = latency
        else:
            self.avg_latency = 0.9 * self.avg_latency + 0.1 * latency
    
    def record_failure(self):
        """Record a failed request."""
        self.last_used = time.time()
        self.failure_count += 1
    
    def mark_banned(self, duration_minutes: int = 30):
        """
        Mark proxy as banned for a duration.
        
        Args:
            duration_minutes: Ban duration in minutes
        """
        self.banned_until = datetime.now() + timedelta(minutes=duration_minutes)
        logger.warning(f"Proxy marked as banned until {self.banned_until}")
    
    def is_banned(self) -> bool:
        """
        Check if proxy is currently banned.
        
        Returns:
            True if banned, False otherwise
        """
        if self.banned_until is None:
            return False
        
        return datetime.now() < self.banned_until
    
    def get_success_rate(self) -> float:
        """
        Get success rate of the proxy.
        
        Returns:
            Success rate (0.0 to 1.0)
        """
        total = self.success_count + self.failure_count
        if total == 0:
            return 1.0
        
        return self.success_count / total
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert status to dictionary.
        
        Returns:
            Dictionary representation
        """
        return {
            "last_used": self.last_used,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "last_latency": self.last_latency,
            "avg_latency": self.avg_latency,
            "banned_until": self.banned_until.isoformat() if self.banned_until else None,
            "last_checked": self.last_checked,
            "success_rate": self.get_success_rate()
        }


class ProxyManager:
    """
    Manager for proxy servers with IP rotation capabilities.
    
    Features:
    - Multiple proxy providers support
    - Proxy health monitoring
    - Automatic IP rotation
    - Proxy testing and validation
    - Ban detection and avoidance
    """
    
    def __init__(self, 
                 proxies: Optional[List[Dict[str, Any]]] = None,
                 proxy_file: Optional[str] = None,
                 test_url: str = "https://httpbin.org/ip",
                 min_rotation_interval: int = 10,
                 auto_test: bool = True):
        """
        Initialize the proxy manager.
        
        Args:
            proxies: List of proxy configurations
            proxy_file: Path to proxy configuration file
            test_url: URL for testing proxies
            min_rotation_interval: Minimum interval between rotations (seconds)
            auto_test: Whether to automatically test proxies on initialization
        """
        self.proxies: List[Dict[str, Any]] = []
        self.proxy_status: Dict[str, ProxyStatus] = {}
        self.test_url = test_url
        self.min_rotation_interval = min_rotation_interval
        self.last_rotation = 0.0
        self.current_proxy: Optional[Dict[str, Any]] = None
        
        # Load proxies
        if proxies:
            self.proxies = proxies
        elif proxy_file and os.path.exists(proxy_file):
            self._load_proxies_from_file(proxy_file)
        
        # Initialize status for each proxy
        for proxy in self.proxies:
            proxy_id = self._get_proxy_id(proxy)
            self.proxy_status[proxy_id] = ProxyStatus()
        
        # Test proxies if requested
        if auto_test and self.proxies:
            asyncio.create_task(self.test_all_proxies())
        
        logger.info(f"ProxyManager initialized with {len(self.proxies)} proxies")
    
    def _load_proxies_from_file(self, file_path: str):
        """
        Load proxies from a JSON file.
        
        Args:
            file_path: Path to proxy configuration file
        """
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                
                if isinstance(data, list):
                    self.proxies = data
                elif isinstance(data, dict) and 'proxies' in data:
                    self.proxies = data['proxies']
                else:
                    logger.error(f"Invalid proxy file format: {file_path}")
                    
        except Exception as e:
            logger.error(f"Error loading proxies from {file_path}: {str(e)}")
    
    def _get_proxy_id(self, proxy: Dict[str, Any]) -> str:
        """
        Get unique identifier for a proxy.
        
        Args:
            proxy: Proxy configuration
            
        Returns:
            Proxy identifier
        """
        if 'id' in proxy:
            return proxy['id']
        
        if 'host' in proxy and 'port' in proxy:
            return f"{proxy['host']}:{proxy['port']}"
        
        if 'url' in proxy:
            return proxy['url']
        
        return str(hash(json.dumps(proxy, sort_keys=True)))
    
    def _get_proxy_url(self, proxy: Dict[str, Any]) -> str:
        """
        Get proxy URL.
        
        Args:
            proxy: Proxy configuration
            
        Returns:
            Proxy URL
        """
        if 'url' in proxy:
            return proxy['url']
        
        if 'host' in proxy and 'port' in proxy:
            protocol = proxy.get('protocol', 'http')
            auth = ""
            if 'username' in proxy and 'password' in proxy:
                auth = f"{proxy['username']}:{proxy['password']}@"
            
            return f"{protocol}://{auth}{proxy['host']}:{proxy['port']}"
        
        return ""
    
    def _get_requests_format(self, proxy: Dict[str, Any]) -> Dict[str, str]:
        """
        Get proxy in requests format.
        
        Args:
            proxy: Proxy configuration
            
        Returns:
            Proxy in requests format
        """
        url = self._get_proxy_url(proxy)
        if not url:
            return {}
        
        return {
            'http': url,
            'https': url
        }
    
    def _get_aiohttp_format(self, proxy: Dict[str, Any]) -> str:
        """
        Get proxy in aiohttp format.
        
        Args:
            proxy: Proxy configuration
            
        Returns:
            Proxy in aiohttp format
        """
        return self._get_proxy_url(proxy)
    
    async def test_proxy(self, proxy: Dict[str, Any]) -> bool:
        """
        Test if a proxy is working.
        
        Args:
            proxy: Proxy configuration
            
        Returns:
            True if proxy is working, False otherwise
        """
        proxy_id = self._get_proxy_id(proxy)
        proxy_url = self._get_proxy_url(proxy)
        
        if not proxy_url:
            logger.error(f"Invalid proxy configuration: {proxy}")
            return False
        
        logger.debug(f"Testing proxy {proxy_id}")
        
        try:
            start_time = time.time()
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    self.test_url,
                    proxy=proxy_url,
                    timeout=10
                ) as response:
                    if response.status == 200:
                        latency = time.time() - start_time
                        
                        # Update status
                        if proxy_id in self.proxy_status:
                            self.proxy_status[proxy_id].record_success(latency)
                            self.proxy_status[proxy_id].last_checked = time.time()
                        
                        logger.debug(f"Proxy {proxy_id} is working (latency: {latency:.2f}s)")
                        return True
                    else:
                        logger.warning(f"Proxy {proxy_id} returned status {response.status}")
                        
                        # Update status
                        if proxy_id in self.proxy_status:
                            self.proxy_status[proxy_id].record_failure()
                            self.proxy_status[proxy_id].last_checked = time.time()
                        
                        return False
                        
        except asyncio.TimeoutError:
            logger.warning(f"Proxy {proxy_id} timed out")
            
            # Update status
            if proxy_id in self.proxy_status:
                self.proxy_status[proxy_id].record_failure()
                self.proxy_status[proxy_id].last_checked = time.time()
            
            return False
            
        except Exception as e:
            logger.error(f"Error testing proxy {proxy_id}: {str(e)}")
            
            # Update status
            if proxy_id in self.proxy_status:
                self.proxy_status[proxy_id].record_failure()
                self.proxy_status[proxy_id].last_checked = time.time()
            
            return False
    
    async def test_all_proxies(self) -> Dict[str, bool]:
        """
        Test all proxies.
        
        Returns:
            Dictionary of proxy IDs to test results
        """
        if not self.proxies:
            logger.warning("No proxies to test")
            return {}
        
        logger.info(f"Testing {len(self.proxies)} proxies")
        
        results = {}
        for proxy in self.proxies:
            proxy_id = self._get_proxy_id(proxy)
            result = await self.test_proxy(proxy)
            results[proxy_id] = result
        
        working_count = sum(1 for r in results.values() if r)
        logger.info(f"Proxy test completed: {working_count}/{len(results)} working")
        
        return results
    
    def get_proxy(self, force_rotation: bool = False) -> Optional[Dict[str, Any]]:
        """
        Get a proxy to use.
        
        Args:
            force_rotation: Whether to force rotation to a new proxy
            
        Returns:
            Proxy configuration or None if no proxies available
        """
        if not self.proxies:
            return None
        
        # Check if we need to rotate
        current_time = time.time()
        should_rotate = (
            force_rotation or
            self.current_proxy is None or
            current_time - self.last_rotation >= self.min_rotation_interval
        )
        
        if not should_rotate and self.current_proxy:
            return self.current_proxy
        
        # Get working proxies
        working_proxies = []
        for proxy in self.proxies:
            proxy_id = self._get_proxy_id(proxy)
            
            # Skip banned proxies
            if proxy_id in self.proxy_status and self.proxy_status[proxy_id].is_banned():
                continue
            
            # Skip current proxy if forcing rotation
            if force_rotation and self.current_proxy and proxy_id == self._get_proxy_id(self.current_proxy):
                continue
            
            # Prefer proxies with higher success rate
            if proxy_id in self.proxy_status and self.proxy_status[proxy_id].get_success_rate() < 0.5:
                # Only include if we have few options
                if len(self.proxies) > 3:
                    continue
            
            working_proxies.append(proxy)
        
        if not working_proxies:
            logger.warning("No working proxies available")
            return None
        
        # Select a proxy
        self.current_proxy = random.choice(working_proxies)
        self.last_rotation = current_time
        
        proxy_id = self._get_proxy_id(self.current_proxy)
        logger.info(f"Rotated to proxy {proxy_id}")
        
        return self.current_proxy
    
    def mark_current_proxy_failed(self):
        """Mark the current proxy as failed."""
        if not self.current_proxy:
            return
        
        proxy_id = self._get_proxy_id(self.current_proxy)
        
        if proxy_id in self.proxy_status:
            self.proxy_status[proxy_id].record_failure()
            
            # Ban proxy if too many failures
            if self.proxy_status[proxy_id].failure_count > 5 and self.proxy_status[proxy_id].get_success_rate() < 0.3:
                self.proxy_status[proxy_id].mark_banned()
                logger.warning(f"Proxy {proxy_id} banned due to too many failures")
        
        # Force rotation on next get_proxy call
        self.current_proxy = None
    
    def mark_current_proxy_banned(self, duration_minutes: int = 30):
        """
        Mark the current proxy as banned.
        
        Args:
            duration_minutes: Ban duration in minutes
        """
        if not self.current_proxy:
            return
        
        proxy_id = self._get_proxy_id(self.current_proxy)
        
        if proxy_id in self.proxy_status:
            self.proxy_status[proxy_id].mark_banned(duration_minutes)
        
        # Force rotation on next get_proxy call
        self.current_proxy = None
    
    def get_proxy_for_requests(self) -> Dict[str, str]:
        """
        Get current proxy in requests format.
        
        Returns:
            Proxy in requests format
        """
        proxy = self.get_proxy()
        if not proxy:
            return {}
        
        return self._get_requests_format(proxy)
    
    def get_proxy_for_aiohttp(self) -> str:
        """
        Get current proxy in aiohttp format.
        
        Returns:
            Proxy in aiohttp format
        """
        proxy = self.get_proxy()
        if not proxy:
            return ""
        
        return self._get_aiohttp_format(proxy)
    
    def add_proxy(self, proxy: Dict[str, Any]):
        """
        Add a new proxy.
        
        Args:
            proxy: Proxy configuration
        """
        proxy_id = self._get_proxy_id(proxy)
        
        # Check if proxy already exists
        for existing in self.proxies:
            if self._get_proxy_id(existing) == proxy_id:
                return
        
        self.proxies.append(proxy)
        self.proxy_status[proxy_id] = ProxyStatus()
        
        logger.info(f"Added new proxy {proxy_id}")
    
    def remove_proxy(self, proxy_id: str) -> bool:
        """
        Remove a proxy.
        
        Args:
            proxy_id: Proxy identifier
            
        Returns:
            True if proxy was removed, False otherwise
        """
        for i, proxy in enumerate(self.proxies):
            if self._get_proxy_id(proxy) == proxy_id:
                self.proxies.pop(i)
                
                if proxy_id in self.proxy_status:
                    del self.proxy_status[proxy_id]
                
                logger.info(f"Removed proxy {proxy_id}")
                return True
        
        return False
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get proxy manager status.
        
        Returns:
            Status information
        """
        proxy_stats = {}
        for proxy in self.proxies:
            proxy_id = self._get_proxy_id(proxy)
            
            if proxy_id in self.proxy_status:
                proxy_stats[proxy_id] = self.proxy_status[proxy_id].to_dict()
        
        return {
            "proxy_count": len(self.proxies),
            "working_count": sum(1 for p in proxy_stats.values() if p["success_rate"] > 0.5),
            "banned_count": sum(1 for p in proxy_stats.values() if p.get("banned_until")),
            "current_proxy": self._get_proxy_id(self.current_proxy) if self.current_proxy else None,
            "last_rotation": self.last_rotation,
            "proxies": proxy_stats
        }


# Example proxy configurations
EXAMPLE_PROXIES = [
    {
        "host": "proxy1.example.com",
        "port": 8080,
        "protocol": "http",
        "username": "user1",
        "password": "pass1"
    },
    {
        "host": "proxy2.example.com",
        "port": 8080,
        "protocol": "http"
    },
    {
        "url": "http://user3:pass3@proxy3.example.com:8080"
    }
]
