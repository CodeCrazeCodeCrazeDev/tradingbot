"""
Phase 2: Live Module Monitoring
Continuous monitoring of all critical online modules
"""

import asyncio
import time
import logging
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import traceback
from enum import auto

logger = logging.getLogger(__name__)


class ModuleStatus(Enum):
    """Module operational status"""
    RUNNING = "running"
    DEGRADED = "degraded"
    FAILED = "failed"
    RESTARTING = "restarting"
    OFFLINE = "offline"


@dataclass
class ModuleHealth:
    """Health metrics for a module"""
    module_name: str
    status: ModuleStatus = ModuleStatus.OFFLINE
    last_success: Optional[datetime] = None
    last_failure: Optional[datetime] = None
    response_latency_ms: float = 0.0
    error_count_hourly: int = 0
    consecutive_failures: int = 0
    restart_count: int = 0
    data_validity: bool = True
    is_stale: bool = False
    uptime_pct: float = 0.0
    
    def is_healthy(self) -> bool:
        """Check if module is healthy"""
        return (
            self.status == ModuleStatus.RUNNING and
            self.consecutive_failures == 0 and
            self.data_validity and
            not self.is_stale
        )


class ModuleMonitor:
    """
    Monitors all critical online modules with auto-restart capability.
    """
    
    CRITICAL_MODULES = [
        'data_feed',
        'api_connector',
        'news_fetcher',
        'sentiment_analyzer',
        'elite_brain_model_updater'
    ]
    
    def __init__(self, config: Dict):
        self.config = config
        
        # Module health tracking
        self.module_health: Dict[str, ModuleHealth] = {}
        for module in self.CRITICAL_MODULES:
            self.module_health[module] = ModuleHealth(module_name=module)
        
        # Monitoring configuration
        self.check_interval = config.get('check_interval', 30)  # seconds
        self.stale_threshold = config.get('stale_threshold', 300)  # 5 minutes
        self.max_restart_attempts = config.get('max_restart_attempts', 3)
        self.degraded_mode_threshold = config.get('degraded_mode_threshold', 3)
        
        # Module instances (to be set externally)
        self.modules: Dict[str, Any] = {}
        
        # State
        self.is_monitoring = False
        self.monitoring_task: Optional[asyncio.Task] = None
        self.alert_callbacks: List[callable] = []
        
        logger.info("Module Monitor initialized")
    
    def register_module(self, module_name: str, module_instance: Any):
        """Register a module for monitoring"""
        if module_name not in self.CRITICAL_MODULES:
            logger.warning(f"Module {module_name} not in critical modules list")
        
        self.modules[module_name] = module_instance
        logger.info(f"Registered module: {module_name}")
    
    def register_alert_callback(self, callback: callable):
        """Register callback for alerts"""
        self.alert_callbacks.append(callback)
    
    async def check_module(self, module_name: str) -> ModuleHealth:
        """
        Check health of a specific module.
        Returns updated health metrics.
        """
        health = self.module_health[module_name]
        
        try:
            module = self.modules.get(module_name)
            
            if not module:
                health.status = ModuleStatus.OFFLINE
                health.consecutive_failures += 1
                return health
            
            # Measure response time
            start_time = time.time()
            
            # Check module health (module must implement health_check method)
            if hasattr(module, 'health_check'):
                is_healthy = await module.health_check()
            else:
                # Fallback: check if module has recent activity
                is_healthy = await self._check_module_activity(module_name, module)
            
            response_time = (time.time() - start_time) * 1000  # ms
            health.response_latency_ms = response_time
            
            if is_healthy:
                # Module is healthy
                health.status = ModuleStatus.RUNNING
                health.last_success = datetime.now()
                health.consecutive_failures = 0
                health.data_validity = True
                
                # Check if data is stale
                health.is_stale = await self._check_data_staleness(module_name, module)
                
                logger.debug(f"✓ {module_name}: healthy (latency: {response_time:.1f}ms)")
            else:
                # Module is unhealthy
                health.status = ModuleStatus.FAILED
                health.last_failure = datetime.now()
                health.consecutive_failures += 1
                health.error_count_hourly += 1
                
                logger.warning(f"✗ {module_name}: unhealthy (failures: {health.consecutive_failures})")
        
        except Exception as e:
            health.status = ModuleStatus.FAILED
            health.last_failure = datetime.now()
            health.consecutive_failures += 1
            health.error_count_hourly += 1
            
            logger.error(f"Error checking {module_name}: {e}")
            logger.debug(traceback.format_exc())
        
        return health
    
    async def _check_module_activity(self, module_name: str, module: Any) -> bool:
        """Check if module has recent activity"""
        try:
            # Check for last_update timestamp
            if hasattr(module, 'last_update'):
                last_update = module.last_update
                if isinstance(last_update, datetime):
                    age = (datetime.now() - last_update).total_seconds()
                    return age < self.stale_threshold
            
            # Check for is_running flag
            if hasattr(module, 'is_running'):
                return module.is_running
            
            # Default: assume healthy if no check available
            return True
        
        except Exception as e:
            logger.debug(f"Error checking activity for {module_name}: {e}")
            return False
    
    async def _check_data_staleness(self, module_name: str, module: Any) -> bool:
        """Check if module data is stale"""
        try:
            if hasattr(module, 'last_data_fetch'):
                last_fetch = module.last_data_fetch
                if isinstance(last_fetch, datetime):
                    age = (datetime.now() - last_fetch).total_seconds()
                    return age > self.stale_threshold
            
            return False
        
        except Exception as e:
            logger.debug(f"Error checking staleness for {module_name}: {e}")
            return False
    
    async def check_all_modules(self) -> Dict[str, ModuleHealth]:
        """Check health of all modules"""
        logger.debug("Checking all modules...")
        
        tasks = []
        for module_name in self.CRITICAL_MODULES:
            tasks.append(self.check_module(module_name))
        
        await asyncio.gather(*tasks)
        
        return self.module_health
    
    async def handle_module_failure(self, module_name: str):
        """
        Handle module failure with auto-restart and failover.
        """
        health = self.module_health[module_name]
        
        logger.warning(f"🔧 Handling failure for {module_name}")
        logger.warning(f"   Consecutive failures: {health.consecutive_failures}")
        logger.warning(f"   Restart count: {health.restart_count}")
        
        # Step 1: Attempt auto-restart
        if health.consecutive_failures == 1:
            logger.info(f"🔄 Attempting auto-restart of {module_name}...")
            success = await self._restart_module(module_name)
            
            if success:
                logger.info(f"✅ {module_name} restarted successfully")
                await self._send_alert(f"Module {module_name} restarted successfully")
                return
        
        # Step 2: Reinitialize dependencies (after 3 failures)
        elif health.consecutive_failures == self.degraded_mode_threshold:
            logger.warning(f"🔄 Reinitializing dependencies for {module_name}...")
            success = await self._reinitialize_dependencies(module_name)
            
            if success:
                logger.info(f"✅ {module_name} dependencies reinitialized")
                await self._send_alert(f"Module {module_name} dependencies reinitialized")
                return
        
        # Step 3: Enter degraded mode (after repeated failures)
        elif health.consecutive_failures > self.degraded_mode_threshold:
            logger.error(f"⚠️ {module_name} entering DEGRADED MODE")
            health.status = ModuleStatus.DEGRADED
            await self._enter_degraded_mode(module_name)
            await self._send_alert(f"CRITICAL: Module {module_name} in degraded mode", critical=True)
    
    async def _restart_module(self, module_name: str) -> bool:
        """Restart a specific module"""
        try:
            health = self.module_health[module_name]
            health.status = ModuleStatus.RESTARTING
            health.restart_count += 1
            
            module = self.modules.get(module_name)
            
            if not module:
                logger.error(f"Module {module_name} not registered")
                return False
            
            # Stop module
            if hasattr(module, 'stop'):
                await module.stop()
                await asyncio.sleep(2)
            
            # Start module
            if hasattr(module, 'start'):
                await module.start()
                await asyncio.sleep(2)
            
            # Verify restart
            is_healthy = await self._check_module_activity(module_name, module)
            
            if is_healthy:
                health.status = ModuleStatus.RUNNING
                health.consecutive_failures = 0
                return True
            else:
                health.status = ModuleStatus.FAILED
                return False
        
        except Exception as e:
            logger.error(f"Error restarting {module_name}: {e}")
            return False
    
    async def _reinitialize_dependencies(self, module_name: str) -> bool:
        """Reinitialize module dependencies"""
        try:
            logger.info(f"Reinitializing dependencies for {module_name}...")
            
            module = self.modules.get(module_name)
            
            if not module:
                return False
            
            # Clear cache
            if hasattr(module, 'clear_cache'):
                await module.clear_cache()
            
            # Refresh connections
            if hasattr(module, 'refresh_connections'):
                await module.refresh_connections()
            
            # Reinitialize
            if hasattr(module, 'initialize'):
                await module.initialize()
            
            # Wait and verify
            await asyncio.sleep(3)
            is_healthy = await self._check_module_activity(module_name, module)
            
            return is_healthy
        
        except Exception as e:
            logger.error(f"Error reinitializing dependencies for {module_name}: {e}")
            return False
    
    async def _enter_degraded_mode(self, module_name: str):
        """Enter degraded mode for a module"""
        logger.warning(f"Entering degraded mode for {module_name}")
        
        # Switch to backup data source
        if module_name == 'data_feed':
            logger.info("Switching to backup data source...")
            # Implementation: activate backup data feed
        
        elif module_name == 'news_fetcher':
            logger.info("Using cached news data...")
            # Implementation: use cached news
        
        elif module_name == 'sentiment_analyzer':
            logger.info("Using neutral sentiment assumption...")
            # Implementation: default to neutral sentiment
        
        # Activate offline mode flag
        health = self.module_health[module_name]
        health.status = ModuleStatus.DEGRADED
    
    async def _send_alert(self, message: str, critical: bool = False):
        """Send alert through registered callbacks"""
        level = "CRITICAL" if critical else "WARNING"
        alert_msg = f"[{level}] {message}"
        
        logger.warning(alert_msg)
        
        for callback in self.alert_callbacks:
            try:
                await callback(alert_msg, critical)
            except Exception as e:
                logger.error(f"Error in alert callback: {e}")
    
    async def continuous_monitoring(self):
        """Continuously monitor all modules"""
        logger.info(f"🔍 Starting continuous module monitoring (interval: {self.check_interval}s)")
        self.is_monitoring = True
        
        while self.is_monitoring:
            try:
                # Check all modules
                await self.check_all_modules()
                
                # Handle failures
                for module_name, health in self.module_health.items():
                    if health.status == ModuleStatus.FAILED:
                        await self.handle_module_failure(module_name)
                
                # Reset hourly error counts
                current_minute = datetime.now().minute
                if current_minute == 0:
                    for health in self.module_health.values():
                        health.error_count_hourly = 0
                
                # Wait before next check
                await asyncio.sleep(self.check_interval)
            
            except Exception as e:
                logger.error(f"Error in continuous monitoring: {e}")
                await asyncio.sleep(10)
    
    async def start_monitoring(self):
        """Start monitoring task"""
        if self.monitoring_task and not self.monitoring_task.done():
            logger.warning("Monitoring already running")
            return
        
        self.monitoring_task = asyncio.create_task(self.continuous_monitoring())
        logger.info("✅ Module monitoring started")
    
    async def stop_monitoring(self):
        """Stop monitoring task"""
        self.is_monitoring = False
        
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Module monitoring stopped")
    
    def get_status_report(self) -> Dict:
        """Generate comprehensive status report"""
        healthy_count = sum(1 for h in self.module_health.values() if h.is_healthy())
        total_count = len(self.module_health)
        
        return {
            'timestamp': datetime.now().isoformat(),
            'overall_health': f"{healthy_count}/{total_count} modules healthy",
            'modules': {
                name: {
                    'status': health.status.value,
                    'last_success': health.last_success.isoformat() if health.last_success else None,
                    'last_failure': health.last_failure.isoformat() if health.last_failure else None,
                    'response_latency_ms': round(health.response_latency_ms, 2),
                    'error_count_hourly': health.error_count_hourly,
                    'consecutive_failures': health.consecutive_failures,
                    'restart_count': health.restart_count,
                    'data_validity': health.data_validity,
                    'is_stale': health.is_stale,
                    'is_healthy': health.is_healthy()
                }
                for name, health in self.module_health.items()
            }
        }
    
    def all_modules_healthy(self) -> Tuple[bool, List[str]]:
        """
        Check if all modules are healthy.
        Returns (all_healthy, list_of_unhealthy_modules)
        """
        unhealthy = []
        
        for name, health in self.module_health.items():
            if not health.is_healthy():
                unhealthy.append(name)
        
        return len(unhealthy) == 0, unhealthy
