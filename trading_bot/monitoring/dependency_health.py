"""
Dependency Health Monitor

Continuously monitors dependency health and auto-repairs issues.
"""

import logging
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class DependencyHealthMonitor:
    """
    Monitors dependency health and automatically repairs issues.
    
    Features:
    - Periodic dependency checks
    - Auto-repair missing dependencies
    - Alert on critical failures
    - Health metrics tracking
    """
    
    def __init__(self, check_interval: int = 3600, auto_repair: bool = True):
        """
        Initialize dependency health monitor.
        
        Args:
            check_interval: Seconds between health checks (default: 1 hour)
            auto_repair: Automatically repair issues when detected
        """
        self.check_interval = check_interval
        self.auto_repair = auto_repair
        self.running = False
        self.monitor_thread: Optional[threading.Thread] = None
        self.last_check: Optional[datetime] = None
        self.health_history: List[Dict] = []
        self.alerts: List[str] = []
        
    def start(self):
        """Start the health monitor"""
        if self.running:
            logger.warning("Health monitor already running")
            return
        
        self.running = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        logger.info(f"✅ Dependency health monitor started (interval: {self.check_interval}s)")
    
    def stop(self):
        """Stop the health monitor"""
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        logger.info("🛑 Dependency health monitor stopped")
    
    def _monitor_loop(self):
        """Main monitoring loop"""
        while self.running:
            try:
                self._perform_health_check()
            except Exception as e:
                logger.error(f"Health check error: {e}")
                self.alerts.append(f"Health check failed: {e}")
            
            # Sleep in small intervals to allow quick shutdown
            for _ in range(self.check_interval):
                if not self.running:
                    break
                time.sleep(1)
    
    def _perform_health_check(self):
        """Perform a health check"""
        try:
            from trading_bot.core.dependency_manager import AutoDependencyManager
            
            logger.info("🔍 Performing dependency health check...")
            
            manager = AutoDependencyManager(
                auto_install=self.auto_repair,
                auto_update=False
            )
            
            # Check dependencies
            status_map = manager.check_all_dependencies()
            
            # Count issues
            missing = sum(1 for s in status_map.values() if s.value == 'missing')
            failed = sum(1 for s in status_map.values() if s.value == 'failed')
            outdated = sum(1 for s in status_map.values() if s.value == 'outdated')
            
            # Record health status
            health_record = {
                'timestamp': datetime.now().isoformat(),
                'missing': missing,
                'failed': failed,
                'outdated': outdated,
                'total': len(status_map)
            }
            self.health_history.append(health_record)
            
            # Keep only last 100 records
            if len(self.health_history) > 100:
                self.health_history = self.health_history[-100:]
            
            self.last_check = datetime.now()
            
            # Auto-repair if needed
            if (missing > 0 or failed > 0) and self.auto_repair:
                logger.warning(f"⚠️  Detected {missing} missing and {failed} failed dependencies")
                logger.info("🔧 Attempting auto-repair...")
                
                success, failures = manager.install_missing_required()
                
                if failures > 0:
                    alert = f"Failed to repair {failures} dependencies"
                    self.alerts.append(alert)
                    logger.error(f"❌ {alert}")
                else:
                    logger.info(f"✅ Successfully repaired {success} dependencies")
            
            if missing == 0 and failed == 0:
                logger.info("✅ All dependencies healthy")
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            self.alerts.append(f"Health check exception: {e}")
    
    def get_health_status(self) -> Dict:
        """
        Get current health status.
        
        Returns:
            Dictionary with health metrics
        """
        if not self.health_history:
            return {
                'status': 'unknown',
                'last_check': None,
                'alerts': self.alerts
            }
        
        latest = self.health_history[-1]
        
        if latest['missing'] > 0 or latest['failed'] > 0:
            status = 'unhealthy'
        elif latest['outdated'] > 0:
            status = 'degraded'
        else:
            status = 'healthy'
        
        return {
            'status': status,
            'last_check': self.last_check.isoformat() if self.last_check else None,
            'missing': latest['missing'],
            'failed': latest['failed'],
            'outdated': latest['outdated'],
            'total': latest['total'],
            'alerts': self.alerts[-10:],  # Last 10 alerts
            'uptime': self._calculate_uptime()
        }
    
    def _calculate_uptime(self) -> Optional[float]:
        """Calculate monitor uptime in seconds"""
        if not self.health_history:
            return None
        
        first_check = datetime.fromisoformat(self.health_history[0]['timestamp'])
        return (datetime.now() - first_check).total_seconds()
    
    def force_check(self) -> Dict:
        """
        Force an immediate health check.
        
        Returns:
            Health status after check
        """
        self._perform_health_check()
        return self.get_health_status()


# Global health monitor instance
_global_monitor: Optional[DependencyHealthMonitor] = None


def get_health_monitor(auto_start: bool = True) -> DependencyHealthMonitor:
    """
    Get the global health monitor instance.
    
    Args:
        auto_start: Automatically start the monitor if not running
        
    Returns:
        DependencyHealthMonitor instance
    """
    global _global_monitor
    
    if _global_monitor is None:
        _global_monitor = DependencyHealthMonitor()
    
    if auto_start and not _global_monitor.running:
        _global_monitor.start()
    
    return _global_monitor


if __name__ == "__main__":
    # Test the health monitor
    logging.basicConfig(level=logging.INFO)
    
    monitor = DependencyHealthMonitor(check_interval=10)
    monitor.start()
    
    try:
        print("Health monitor running. Press Ctrl+C to stop...")
        while True:
            time.sleep(5)
            status = monitor.get_health_status()
            print(f"\nHealth Status: {status['status']}")
            print(f"Last Check: {status['last_check']}")
            print(f"Missing: {status['missing']}, Failed: {status['failed']}, Outdated: {status['outdated']}")
    except KeyboardInterrupt:
        print("\nStopping monitor...")
        monitor.stop()
