"""
Real-Time Adapter
=================

Adapter layer that converts existing modules to use real-time patterns.
Wraps legacy polling-based code with real-time streaming interfaces.

Features:
1. Wrap any data source with real-time streaming
2. Convert polling to event-driven
3. Add WebSocket support to REST APIs
4. Provide unified real-time interface
5. Backward compatibility with existing code

Author: AlphaAlgo Trading System
Version: 3.0.0
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable, Type
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from collections import deque

logger = logging.getLogger(__name__)


class RealTimeAdapter(ABC):
    """
    Base class for real-time adapters.
    Converts any data source to real-time streaming.
    """
    
    def __init__(self, name: str, config: Dict[str, Any] = None):
        self.name = name
        self.config = config or {}
        self._running = False
        self._subscribers: List[Callable] = []
        self._last_data: Optional[Any] = None
        self._update_count = 0
        
    @abstractmethod
    async def fetch_data(self) -> Any:
        """Fetch data from source - implement in subclass"""
        pass
    
    async def start_streaming(self, interval_ms: int = 100):
        """Start streaming data at specified interval"""
        self._running = True
        logger.info(f"Starting real-time adapter: {self.name}")
        
        while self._running:
            try:
                data = await self.fetch_data()
                
                if data is not None and data != self._last_data:
                    self._last_data = data
                    self._update_count += 1
                    await self._notify_subscribers(data)
                
                await asyncio.sleep(interval_ms / 1000)
                
            except Exception as e:
                logger.error(f"Adapter {self.name} error: {e}")
                await asyncio.sleep(1)
    
    async def stop_streaming(self):
        """Stop streaming"""
        self._running = False
        logger.info(f"Stopped real-time adapter: {self.name}")
    
    def subscribe(self, callback: Callable):
        """Subscribe to data updates"""
        self._subscribers.append(callback)
    
    def unsubscribe(self, callback: Callable):
        """Unsubscribe from data updates"""
        self._subscribers = [cb for cb in self._subscribers if cb != callback]
    
    async def _notify_subscribers(self, data: Any):
        """Notify all subscribers"""
        for callback in self._subscribers:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(data)
                else:
                    callback(data)
            except Exception as e:
                logger.error(f"Subscriber callback error: {e}")
    
    def get_latest(self) -> Optional[Any]:
        """Get latest data"""
        return self._last_data


class HTTPToRealtimeAdapter(RealTimeAdapter):
    """
    Converts HTTP/REST API to real-time streaming.
    """
    
    def __init__(self, name: str, url: str, config: Dict[str, Any] = None):
        super().__init__(name, config)
        self.url = url
        self._session = None
    
    async def fetch_data(self) -> Any:
        """Fetch data from HTTP endpoint"""
        try:
            import aiohttp
            
            if self._session is None:
                self._session = aiohttp.ClientSession()
            
            async with self._session.get(self.url) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.warning(f"HTTP {response.status} from {self.url}")
                    return None
                    
        except ImportError:
            pass
            # Fallback without aiohttp

        try:
            import urllib.request
            import json
            
            try:
                with urllib.request.urlopen(self.url, timeout=5) as response:
                    return json.loads(response.read().decode())
            except Exception as e:
                logger.error(f"HTTP fetch error: {e}")
                return None
        except Exception as e:
            logger.error(f"HTTP fetch error: {e}")
            return None
    
    async def stop_streaming(self):
        """Stop and cleanup"""
        await super().stop_streaming()
        if self._session:
            await self._session.close()
            self._session = None


class DatabaseToRealtimeAdapter(RealTimeAdapter):
    """
    Converts database queries to real-time streaming.
    """
    
    def __init__(self, name: str, query_func: Callable, config: Dict[str, Any] = None):
        super().__init__(name, config)
        self.query_func = query_func
    
    async def fetch_data(self) -> Any:
        """Execute query and return results"""
        try:
            if asyncio.iscoroutinefunction(self.query_func):
                return await self.query_func()
            else:
                return self.query_func()
        except Exception as e:
            logger.error(f"Database query error: {e}")
            return None


class FileToRealtimeAdapter(RealTimeAdapter):
    """
    Monitors file changes and streams updates.
    """
    
    def __init__(self, name: str, file_path: str, config: Dict[str, Any] = None):
        super().__init__(name, config)
        self.file_path = file_path
        self._last_modified = 0
    
    async def fetch_data(self) -> Any:
        """Check for file changes and read if modified"""
        import os
        
        try:
            stat = os.stat(self.file_path)
            
            if stat.st_mtime > self._last_modified:
                self._last_modified = stat.st_mtime
                
                with open(self.file_path, 'r') as f:
                    pass
                try:
                    content = f.read()
                    
                # Try to parse as JSON
                    return json.loads(content)
                except json.JSONDecodeError:
                    return content
            
            return None  # No changes
            
        except FileNotFoundError:
            return None
        except Exception as e:
            logger.error(f"File read error: {e}")
            return None


class CallableToRealtimeAdapter(RealTimeAdapter):
    """
    Wraps any callable function with real-time streaming.
    """
    
    def __init__(self, name: str, func: Callable, config: Dict[str, Any] = None):
        super().__init__(name, config)
        self.func = func
        self._args = config.get('args', ())
        self._kwargs = config.get('kwargs', {})
    
    async def fetch_data(self) -> Any:
        """Call the function and return result"""
        try:
            if asyncio.iscoroutinefunction(self.func):
                return await self.func(*self._args, **self._kwargs)
            else:
                return self.func(*self._args, **self._kwargs)
        except Exception as e:
            logger.error(f"Function call error: {e}")
            return None


class LegacyModuleAdapter:
    """
    Adapts legacy trading bot modules to real-time interfaces.
    """
    
    def __init__(self, module_name: str, config: Dict[str, Any] = None):
        self.module_name = module_name
        self.config = config or {}
        self._adapters: Dict[str, RealTimeAdapter] = {}
        self._running = False
    
    def wrap_method(self, method: Callable, name: str = None, 
                    interval_ms: int = 100) -> RealTimeAdapter:
        """Wrap a method with real-time streaming"""
        adapter_name = name or f"{self.module_name}.{method.__name__}"
        
        adapter = CallableToRealtimeAdapter(
            adapter_name, 
            method,
            {'interval_ms': interval_ms}
        )
        
        self._adapters[adapter_name] = adapter
        return adapter
    
    def wrap_http(self, url: str, name: str, interval_ms: int = 1000) -> RealTimeAdapter:
        """Wrap HTTP endpoint with real-time streaming"""
        adapter = HTTPToRealtimeAdapter(name, url)
        self._adapters[name] = adapter
        return adapter
    
    async def start_all(self):
        """Start all adapters"""
        self._running = True
        
        tasks = []
        for name, adapter in self._adapters.items():
            interval = self.config.get(f'{name}_interval_ms', 100)
            tasks.append(asyncio.create_task(adapter.start_streaming(interval)))
        
        await asyncio.gather(*tasks)
    
    async def stop_all(self):
        """Stop all adapters"""
        self._running = False
        
        for adapter in self._adapters.values():
            await adapter.stop_streaming()


class RealTimeWrapper:
    """
    Universal wrapper that makes any object real-time capable.
    """
    
    def __init__(self, obj: Any, config: Dict[str, Any] = None):
        self._obj = obj
        self.config = config or {}
        self._adapters: Dict[str, RealTimeAdapter] = {}
        self._event_bus = None
    
    def make_realtime(self, method_name: str, interval_ms: int = 100) -> RealTimeAdapter:
        """Make a specific method real-time"""
        if not hasattr(self._obj, method_name):
            raise AttributeError(f"Object has no method: {method_name}")
        
        method = getattr(self._obj, method_name)
        
        adapter = CallableToRealtimeAdapter(
            f"{type(self._obj).__name__}.{method_name}",
            method,
            {'interval_ms': interval_ms}
        )
        
        self._adapters[method_name] = adapter
        return adapter
    
    def get_adapter(self, method_name: str) -> Optional[RealTimeAdapter]:
        """Get adapter for a method"""
        return self._adapters.get(method_name)
    
    async def start(self):
        """Start all real-time adapters"""
        for name, adapter in self._adapters.items():
            interval = self.config.get(f'{name}_interval_ms', 100)
            asyncio.create_task(adapter.start_streaming(interval))
    
    async def stop(self):
        """Stop all adapters"""
        for adapter in self._adapters.values():
            await adapter.stop_streaming()
    
    def __getattr__(self, name: str):
        """Proxy attribute access to wrapped object"""
        return getattr(self._obj, name)


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def make_realtime(obj: Any, methods: List[str] = None, 
                  interval_ms: int = 100) -> RealTimeWrapper:
    """
    Make any object real-time capable.
    
    Usage:
        # Wrap existing data provider
        provider = RealMarketDataProvider()
        rt_provider = make_realtime(provider, ['get_price', 'get_orderbook'])
        
        # Subscribe to real-time updates
        rt_provider.get_adapter('get_price').subscribe(on_price_update)
        
        # Start streaming
        await rt_provider.start()
    """
    wrapper = RealTimeWrapper(obj, {'interval_ms': interval_ms})
    
    if methods:
        for method in methods:
            wrapper.make_realtime(method, interval_ms)
    
    return wrapper


def create_http_stream(url: str, name: str = "http_stream", 
                       interval_ms: int = 1000) -> HTTPToRealtimeAdapter:
    """Create a real-time stream from HTTP endpoint"""
    return HTTPToRealtimeAdapter(name, url)


def create_db_stream(query_func: Callable, name: str = "db_stream",
                     interval_ms: int = 100) -> DatabaseToRealtimeAdapter:
    """Create a real-time stream from database query"""
    return DatabaseToRealtimeAdapter(name, query_func)


def create_file_stream(file_path: str, name: str = "file_stream",
                       interval_ms: int = 1000) -> FileToRealtimeAdapter:
    """Create a real-time stream from file"""
    return FileToRealtimeAdapter(name, file_path)


# =============================================================================
# INTEGRATION HELPERS
# =============================================================================

async def integrate_existing_module(module_path: str, 
                                    methods_to_wrap: List[str],
                                    interval_ms: int = 100) -> LegacyModuleAdapter:
    """
    Integrate an existing module with real-time capabilities.
    
    Usage:
        adapter = await integrate_existing_module(
            'trading_bot.integrations.RealMarketDataProvider',
            ['get_crypto_price_binance', 'get_stock_price_yahoo']
        )
        
        adapter.wrap_method(provider.get_price, 'price_stream')
        await adapter.start_all()
    """
    # Import the module
    parts = module_path.rsplit('.', 1)
    if len(parts) == 2:
        module_name, class_name = parts
        import importlib
        module = importlib.import_module(module_name)
        cls = getattr(module, class_name)
        instance = cls()
    else:
        raise ValueError(f"Invalid module path: {module_path}")
    
    # Create adapter
    adapter = LegacyModuleAdapter(module_path)
    
    # Wrap methods
    for method_name in methods_to_wrap:
        if hasattr(instance, method_name):
            method = getattr(instance, method_name)
            adapter.wrap_method(method, method_name, interval_ms)
    
    return adapter
