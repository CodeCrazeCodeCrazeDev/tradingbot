import logging
logger = logging.getLogger(__name__)
"""
Health Monitor for Elite Trading Bot
Monitors system health and performance metrics
"""
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import asyncio
from loguru import logger
try:
    import redis
except ImportError:
    redis = None
import psutil
import numpy as np
from enum import Enum
import numpy

class HealthStatus(Enum):
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    CRITICAL = "CRITICAL"

class SystemComponent(Enum):
    MT5_CONNECTION = "MT5_CONNECTION"
    DATA_PIPELINE = "DATA_PIPELINE"
    STRATEGY_ENGINE = "STRATEGY_ENGINE"
    RISK_MANAGER = "RISK_MANAGER"
    ORDER_EXECUTOR = "ORDER_EXECUTOR"
    SENTIMENT_ANALYZER = "SENTIMENT_ANALYZER"
    DATABASE = "DATABASE"
    API_CONNECTIONS = "API_CONNECTIONS"

class HealthMonitor:
    """Monitors system health and performance metrics."""
    
    def __init__(self, 
                redis_host: str = 'localhost',
                redis_port: int = 6379,
                check_interval: int = 5):
        self.redis = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)
        self.check_interval = check_interval
        self.component_status: Dict[SystemComponent, HealthStatus] = {
            component: HealthStatus.HEALTHY for component in SystemComponent
        }
        self.metrics_history: Dict[str, List[float]] = {}
        self.alert_thresholds = {
            'cpu_usage': 80.0,  # 80% CPU usage
            'memory_usage': 85.0,  # 85% memory usage
            'latency': 1000.0,  # 1000ms latency
            'error_rate': 0.05  # 5% error rate
        }
        
    async def start_monitoring(self):
        """Start the health monitoring loop."""
        logger.info("Starting health monitoring system")
        while True:
            try:
                await self.check_system_health()
                await asyncio.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"Error in health monitoring: {e}")
                await asyncio.sleep(self.check_interval * 2)
    
    async def check_system_health(self):
        """Check health of all system components."""
        # System metrics
        cpu_usage = psutil.cpu_percent()
        memory_usage = psutil.virtual_memory().percent
        
        # Update metrics history
        self._update_metric_history('cpu_usage', cpu_usage)
        self._update_metric_history('memory_usage', memory_usage)
        
        # Check components
        await self._check_mt5_connection()
        await self._check_data_pipeline()
        await self._check_strategy_engine()
        await self._check_risk_manager()
        await self._check_order_executor()
        
        # Store health status in Redis
        self._store_health_metrics()
        
        # Generate alerts if needed
        await self._generate_alerts()
    
    def _update_metric_history(self, metric: str, value: float):
        """Update historical metrics with new value."""
        if metric not in self.metrics_history:
            self.metrics_history[metric] = []
        
        self.metrics_history[metric].append(value)
        if len(self.metrics_history[metric]) > 100:  # Keep last 100 values
            self.metrics_history[metric].pop(0)
    
    async def _check_mt5_connection(self):
        """Check MetaTrader 5 connection health."""
        try:
            ping = float(self.redis.get("mt5:ping") or 0)
            connected = self.redis.get("mt5:connected") == "1"
            
            if not connected:
                self.component_status[SystemComponent.MT5_CONNECTION] = HealthStatus.CRITICAL
            elif ping > 1000:  # 1 second ping
                self.component_status[SystemComponent.MT5_CONNECTION] = HealthStatus.DEGRADED
            else:
                self.component_status[SystemComponent.MT5_CONNECTION] = HealthStatus.HEALTHY
                
        except Exception as e:
            logger.error(f"Error checking MT5 connection: {e}")
            self.component_status[SystemComponent.MT5_CONNECTION] = HealthStatus.CRITICAL
    
    async def _check_data_pipeline(self):
        """Check data pipeline health."""
        try:
            pipeline_latency = float(self.redis.get("pipeline:latency") or 0)
            error_rate = float(self.redis.get("pipeline:error_rate") or 0)
            
            if error_rate > 0.1 or pipeline_latency > 2000:  # 10% error rate or 2s latency
                self.component_status[SystemComponent.DATA_PIPELINE] = HealthStatus.CRITICAL
            elif error_rate > 0.05 or pipeline_latency > 1000:  # 5% error rate or 1s latency
                self.component_status[SystemComponent.DATA_PIPELINE] = HealthStatus.DEGRADED
            else:
                self.component_status[SystemComponent.DATA_PIPELINE] = HealthStatus.HEALTHY
                
        except Exception as e:
            logger.error(f"Error checking data pipeline: {e}")
            self.component_status[SystemComponent.DATA_PIPELINE] = HealthStatus.CRITICAL
    
    async def _check_strategy_engine(self):
        """Check strategy engine health."""
        try:
            last_signal_time = self.redis.get("strategy:last_signal_time")
            if last_signal_time:
                last_signal = datetime.fromisoformat(last_signal_time)
                if datetime.now() - last_signal > timedelta(minutes=5):
                    self.component_status[SystemComponent.STRATEGY_ENGINE] = HealthStatus.CRITICAL
                elif datetime.now() - last_signal > timedelta(minutes=2):
                    self.component_status[SystemComponent.STRATEGY_ENGINE] = HealthStatus.DEGRADED
                else:
                    self.component_status[SystemComponent.STRATEGY_ENGINE] = HealthStatus.HEALTHY
            else:
                self.component_status[SystemComponent.STRATEGY_ENGINE] = HealthStatus.CRITICAL
                
        except Exception as e:
            logger.error(f"Error checking strategy engine: {e}")
            self.component_status[SystemComponent.STRATEGY_ENGINE] = HealthStatus.CRITICAL
    
    async def _check_risk_manager(self):
        """Check risk manager health."""
        try:
            last_check_time = self.redis.get("risk:last_check_time")
            if last_check_time:
                last_check = datetime.fromisoformat(last_check_time)
                if datetime.now() - last_check > timedelta(minutes=5):
                    self.component_status[SystemComponent.RISK_MANAGER] = HealthStatus.CRITICAL
                elif datetime.now() - last_check > timedelta(minutes=2):
                    self.component_status[SystemComponent.RISK_MANAGER] = HealthStatus.DEGRADED
                else:
                    self.component_status[SystemComponent.RISK_MANAGER] = HealthStatus.HEALTHY
            else:
                self.component_status[SystemComponent.RISK_MANAGER] = HealthStatus.CRITICAL
                
        except Exception as e:
            logger.error(f"Error checking risk manager: {e}")
            self.component_status[SystemComponent.RISK_MANAGER] = HealthStatus.CRITICAL
    
    async def _check_order_executor(self):
        """Check order executor health."""
        try:
            execution_latency = float(self.redis.get("executor:latency") or 0)
            error_rate = float(self.redis.get("executor:error_rate") or 0)
            
            if error_rate > 0.1 or execution_latency > 2000:  # 10% error rate or 2s latency
                self.component_status[SystemComponent.ORDER_EXECUTOR] = HealthStatus.CRITICAL
            elif error_rate > 0.05 or execution_latency > 1000:  # 5% error rate or 1s latency
                self.component_status[SystemComponent.ORDER_EXECUTOR] = HealthStatus.DEGRADED
            else:
                self.component_status[SystemComponent.ORDER_EXECUTOR] = HealthStatus.HEALTHY
                
        except Exception as e:
            logger.error(f"Error checking order executor: {e}")
            self.component_status[SystemComponent.ORDER_EXECUTOR] = HealthStatus.CRITICAL
    
    def _store_health_metrics(self):
        """Store health metrics in Redis."""
        metrics = {
            f"health:{component.value}": status.value
            for component, status in self.component_status.items()
        }
        metrics.update({
            "health:last_update": datetime.now().isoformat(),
            "health:cpu_usage": np.mean(self.metrics_history.get('cpu_usage', [0])),
            "health:memory_usage": np.mean(self.metrics_history.get('memory_usage', [0]))
        })
        self.redis.hmset("system:health", metrics)
    
    async def _generate_alerts(self):
        """Generate alerts for critical issues."""
        critical_components = [
            component for component, status in self.component_status.items()
            if status == HealthStatus.CRITICAL
        ]
        
        if critical_components:
            alert = {
                "timestamp": datetime.now().isoformat(),
                "level": "CRITICAL",
                "components": [comp.value for comp in critical_components],
                "message": f"Critical issues detected in {len(critical_components)} components"
            }
            self.redis.lpush("system:alerts", str(alert))
            logger.critical(f"System alert: {alert['message']}")
            
        degraded_components = [
            component for component, status in self.component_status.items()
            if status == HealthStatus.DEGRADED
        ]
        
        if degraded_components:
            alert = {
                "timestamp": datetime.now().isoformat(),
                "level": "WARNING",
                "components": [comp.value for comp in degraded_components],
                "message": f"Performance degradation in {len(degraded_components)} components"
            }
            self.redis.lpush("system:alerts", str(alert))
            logger.warning(f"System alert: {alert['message']}")
    
    def get_system_status(self) -> Dict:
        """Get current system status summary."""
        return {
            "status": {comp.value: status.value for comp, status in self.component_status.items()},
            "metrics": {
                "cpu_usage": np.mean(self.metrics_history.get('cpu_usage', [0])),
                "memory_usage": np.mean(self.metrics_history.get('memory_usage', [0])),
                "components_healthy": sum(1 for status in self.component_status.values() 
                                       if status == HealthStatus.HEALTHY),
                "components_total": len(self.component_status)
            },
            "last_update": datetime.now().isoformat()
        }
