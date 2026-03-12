"""
System Health Monitor - Real-time monitoring and diagnostics
Monitors all trading bot components and ensures system stability
"""

import asyncio
import logging
import psutil
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum
import json

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/health_monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """System health status levels."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    CRITICAL = "critical"
    OFFLINE = "offline"


@dataclass
class ComponentHealth:
    """Health status of a system component."""
    name: str
    status: HealthStatus
    last_check: datetime
    metrics: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class SystemHealthMonitor:
    """
    Comprehensive system health monitoring.
    
    Monitors:
    - System resources (CPU, Memory, Disk)
    - Component availability
    - Trading performance
    - Data connectivity
    - Error rates
    - Response times
    """
    
    def __init__(self, check_interval: int = 60):
        """
        Initialize health monitor.
        
        Args:
            check_interval: Seconds between health checks
        """
        self.check_interval = check_interval
        self.is_running = False
        self.components: Dict[str, ComponentHealth] = {}
        self.system_metrics: Dict[str, Any] = {}
        self.alert_history: List[Dict] = []
        
        # Thresholds
        self.cpu_threshold = 80.0  # %
        self.memory_threshold = 85.0  # %
        self.disk_threshold = 90.0  # %
        self.error_rate_threshold = 0.05  # 5%
        self.response_time_threshold = 5.0  # seconds
        
        logger.info("✅ System Health Monitor initialized")
    
    async def start(self):
        """Start health monitoring."""
        logger.info("🚀 Starting System Health Monitor")
        self.is_running = True
        
        try:
            while self.is_running:
                await self.perform_health_check()
                await asyncio.sleep(self.check_interval)
        except Exception as e:
            logger.error(f"❌ Health monitor error: {e}")
            raise
    
    def stop(self):
        """Stop health monitoring."""
        logger.info("🛑 Stopping System Health Monitor")
        self.is_running = False
    
    async def perform_health_check(self):
        """Perform comprehensive health check."""
        logger.info(f"\n{'='*80}\n🏥 HEALTH CHECK - {datetime.now().strftime('%H:%M:%S')}\n{'='*80}")
        
        # 1. System Resources
        await self.check_system_resources()
        
        # 2. Component Health
        await self.check_components()
        
        # 3. Trading Performance
        await self.check_trading_performance()
        
        # 4. Data Connectivity
        await self.check_data_connectivity()
        
        # 5. Generate Report
        self.generate_health_report()
        
        # 6. Check for alerts
        await self.check_alerts()
    
    async def check_system_resources(self):
        """Check system resource usage."""
        try:
            # CPU Usage
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory Usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            # Disk Usage
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent
            
            # Network I/O
            net_io = psutil.net_io_counters()
            
            self.system_metrics = {
                'cpu_percent': cpu_percent,
                'memory_percent': memory_percent,
                'memory_available_gb': memory.available / (1024**3),
                'disk_percent': disk_percent,
                'disk_free_gb': disk.free / (1024**3),
                'network_bytes_sent': net_io.bytes_sent,
                'network_bytes_recv': net_io.bytes_recv,
                'timestamp': datetime.now()
            }
            
            # Log metrics
            logger.info(f"💻 CPU: {cpu_percent:.1f}% | Memory: {memory_percent:.1f}% | Disk: {disk_percent:.1f}%")
            
            # Check thresholds
            if cpu_percent > self.cpu_threshold:
                self.add_alert('system', f"High CPU usage: {cpu_percent:.1f}%", 'warning')
            
            if memory_percent > self.memory_threshold:
                self.add_alert('system', f"High memory usage: {memory_percent:.1f}%", 'warning')
            
            if disk_percent > self.disk_threshold:
                self.add_alert('system', f"High disk usage: {disk_percent:.1f}%", 'critical')
            
        except Exception as e:
            logger.error(f"❌ System resource check failed: {e}")
            self.add_alert('system', f"Resource check failed: {e}", 'critical')
    
    async def check_components(self):
        """Check health of all components."""
        components_to_check = [
            'elite_system',
            'market_intelligence',
            'orchestrator',
            'opportunity_scanner',
            'execution_engine',
            'risk_manager',
            'unified_risk_manager',  # NEW
            'position_rotator',  # NEW
            'connection_monitor',  # NEW
            'offline_rl_trainer',  # NEW
            'ml_predictor',
            'data_connection'
        ]
        
        for component in components_to_check:
            try:
                health = await self.check_component_health(component)
                self.components[component] = health
                
                status_icon = {
                    HealthStatus.HEALTHY: "✅",
                    HealthStatus.DEGRADED: "⚠️",
                    HealthStatus.CRITICAL: "❌",
                    HealthStatus.OFFLINE: "🔴"
                }.get(health.status, "❓")
                
                logger.info(f"{status_icon} {component}: {health.status.value}")
                
            except Exception as e:
                logger.error(f"❌ Component check failed for {component}: {e}")
                self.components[component] = ComponentHealth(
                    name=component,
                    status=HealthStatus.OFFLINE,
                    last_check=datetime.now(),
                    errors=[str(e)]
                )
    
    async def check_component_health(self, component: str) -> ComponentHealth:
        """
        Check health of a specific component.
        
        Args:
            component: Component name
        
        Returns:
            ComponentHealth object
        """
        # Simulate component health check
        # In production, this would actually ping the component
        
        health = ComponentHealth(
            name=component,
            status=HealthStatus.HEALTHY,
            last_check=datetime.now(),
            metrics={
                'uptime_seconds': 3600,
                'requests_processed': 1000,
                'errors': 5,
                'avg_response_time': 0.5
            }
        )
        
        # Check error rate
        error_rate = health.metrics['errors'] / max(health.metrics['requests_processed'], 1)
        if error_rate > self.error_rate_threshold:
            health.status = HealthStatus.DEGRADED
            health.warnings.append(f"High error rate: {error_rate:.2%}")
        
        # Check response time
        if health.metrics['avg_response_time'] > self.response_time_threshold:
            health.status = HealthStatus.DEGRADED
            health.warnings.append(f"Slow response time: {health.metrics['avg_response_time']:.2f}s")
        
        return health
    
    async def check_trading_performance(self):
        """Check trading performance metrics."""
        try:
            # Placeholder - would integrate with actual performance tracker
            performance_metrics = {
                'total_trades': 150,
                'winning_trades': 95,
                'losing_trades': 55,
                'win_rate': 0.633,
                'total_pnl': 15000.0,
                'sharpe_ratio': 1.85,
                'max_drawdown': 0.08,
                'current_positions': 3
            }
            
            self.system_metrics['trading_performance'] = performance_metrics
            
            logger.info(f"📈 Trades: {performance_metrics['total_trades']} | "
                       f"Win Rate: {performance_metrics['win_rate']:.1%} | "
                       f"P/L: ${performance_metrics['total_pnl']:.2f}")
            
            # Check for concerning metrics
            if performance_metrics['win_rate'] < 0.45:
                self.add_alert('trading', "Low win rate detected", 'warning')
            
            if performance_metrics['max_drawdown'] > 0.15:
                self.add_alert('trading', "High drawdown detected", 'critical')
            
        except Exception as e:
            logger.error(f"❌ Trading performance check failed: {e}")
    
    async def check_data_connectivity(self):
        """Check data source connectivity."""
        data_sources = ['MT5', 'YahooFinance', 'AlphaVantage', 'NewsAPI']
        
        connectivity_status = {}
        for source in data_sources:
            try:
                # Simulate connectivity check
                is_connected = await self.ping_data_source(source)
                connectivity_status[source] = is_connected
                
                icon = "✅" if is_connected else "❌"
                logger.info(f"{icon} {source}: {'Connected' if is_connected else 'Disconnected'}")
                
                if not is_connected:
                    self.add_alert('connectivity', f"{source} disconnected", 'warning')
                
            except Exception as e:
                logger.error(f"❌ Connectivity check failed for {source}: {e}")
                connectivity_status[source] = False
        
        self.system_metrics['data_connectivity'] = connectivity_status
    
    async def ping_data_source(self, source: str) -> bool:
        """
        Ping a data source to check connectivity.
        
        Args:
            source: Data source name
        
        Returns:
            True if connected, False otherwise
        """
        # Simulate ping - in production, would actually test connection
        await asyncio.sleep(0.1)
        return True  # Assume connected for simulation
    
    def generate_health_report(self):
        """Generate comprehensive health report."""
        overall_status = self.calculate_overall_status()
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'overall_status': overall_status.value,
            'system_metrics': self.system_metrics,
            'components': {
                name: {
                    'status': comp.status.value,
                    'metrics': comp.metrics,
                    'errors': comp.errors,
                    'warnings': comp.warnings
                }
                for name, comp in self.components.items()
            },
            'recent_alerts': self.alert_history[-10:]  # Last 10 alerts
        }
        
        # Save report
        try:
            with open('logs/health_report.json', 'w') as f:
                json.dump(report, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"❌ Failed to save health report: {e}")
    
    def calculate_overall_status(self) -> HealthStatus:
        """Calculate overall system health status."""
        if not self.components:
            return HealthStatus.OFFLINE
        
        statuses = [comp.status for comp in self.components.values()]
        
        # If any critical, overall is critical
        if HealthStatus.CRITICAL in statuses or HealthStatus.OFFLINE in statuses:
            return HealthStatus.CRITICAL
        
        # If any degraded, overall is degraded
        if HealthStatus.DEGRADED in statuses:
            return HealthStatus.DEGRADED
        
        # Otherwise healthy
        return HealthStatus.HEALTHY
    
    def add_alert(self, category: str, message: str, severity: str):
        """
        Add an alert to the history.
        
        Args:
            category: Alert category
            message: Alert message
            severity: Alert severity (info/warning/critical)
        """
        alert = {
            'timestamp': datetime.now().isoformat(),
            'category': category,
            'message': message,
            'severity': severity
        }
        
        self.alert_history.append(alert)
        
        # Log based on severity
        if severity == 'critical':
            logger.error(f"🚨 CRITICAL ALERT [{category}]: {message}")
        elif severity == 'warning':
            logger.warning(f"⚠️ WARNING [{category}]: {message}")
        else:
            logger.info(f"ℹ️ INFO [{category}]: {message}")
        
        # Keep only last 100 alerts
        if len(self.alert_history) > 100:
            self.alert_history = self.alert_history[-100:]
    
    async def check_alerts(self):
        """Check for alerts that need attention."""
        # Count recent critical alerts
        recent_time = datetime.now() - timedelta(minutes=5)
        recent_critical = [
            alert for alert in self.alert_history
            if alert['severity'] == 'critical' and 
            datetime.fromisoformat(alert['timestamp']) > recent_time
        ]
        
        if len(recent_critical) > 3:
            logger.error(f"🚨 MULTIPLE CRITICAL ALERTS: {len(recent_critical)} in last 5 minutes")
            # In production, would trigger notifications (email, SMS, etc.)
    
    def get_status_summary(self) -> Dict[str, Any]:
        """Get current status summary."""
        return {
            'overall_status': self.calculate_overall_status().value,
            'system_metrics': self.system_metrics,
            'component_count': len(self.components),
            'healthy_components': sum(1 for c in self.components.values() if c.status == HealthStatus.HEALTHY),
            'degraded_components': sum(1 for c in self.components.values() if c.status == HealthStatus.DEGRADED),
            'critical_components': sum(1 for c in self.components.values() if c.status == HealthStatus.CRITICAL),
            'recent_alerts': len(self.alert_history[-10:])
        }


async def main():
    """Main entry point."""
    import os
    os.makedirs('logs', exist_ok=True)
    
    monitor = SystemHealthMonitor(check_interval=30)
    
    try:
        await monitor.start()
    except KeyboardInterrupt:
        logger.info("\n🛑 Stopping health monitor...")
        monitor.stop()


if __name__ == '__main__':
    asyncio.run(main())
