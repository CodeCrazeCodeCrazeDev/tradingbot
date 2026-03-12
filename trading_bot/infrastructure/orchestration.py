"""
Infrastructure Orchestration Module
Coordinates infrastructure components and services.
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class InfrastructureStatus:
    """Status of infrastructure components."""
    component: str
    status: str
    health: float
    last_check: datetime
    details: Dict[str, Any] = field(default_factory=dict)


class InfrastructureOrchestrator:
    """Orchestrates infrastructure components and services."""
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize the infrastructure orchestrator.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.components: Dict[str, Any] = {}
        self.status: Dict[str, InfrastructureStatus] = {}
        self.running = False
        
        logger.info("InfrastructureOrchestrator initialized")
    
    async def start(self):
        """Start infrastructure services."""
        logger.info("Starting infrastructure services...")
        self.running = True
        
        try:
            # Initialize monitoring
            await self._initialize_monitoring()
            
            # Initialize health checks
            await self._initialize_health_checks()
            
            # Initialize auto-scaling
            await self._initialize_auto_scaling()
            
            logger.info("[OK] Infrastructure services started")
            
        except Exception as e:
            logger.error(f"[FAIL] Failed to start infrastructure: {e}")
            raise
    
    async def stop(self):
        """Stop infrastructure services."""
        logger.info("Stopping infrastructure services...")
        self.running = False
        
        try:
            # Stop all components
            for component_name, component in self.components.items():
                if hasattr(component, 'stop'):
                    await component.stop()
                    logger.info(f"[OK] Stopped {component_name}")
            
            logger.info("[OK] Infrastructure services stopped")
            
        except Exception as e:
            logger.error(f"[FAIL] Failed to stop infrastructure: {e}")
    
    async def health_check(self) -> Dict[str, Any]:
        """Check infrastructure health.
        
        Returns:
            Dictionary with health status
        """
        health_status = {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'components': {},
            'overall_health': 100.0
        }
        
        try:
            # Check each component
            total_health = 0.0
            component_count = 0
            
            for component_name, component in self.components.items():
                if hasattr(component, 'health_check'):
                    component_health = await component.health_check()
                    health_status['components'][component_name] = component_health
                    
                    # Calculate health score
                    if isinstance(component_health, dict):
                        health_score = component_health.get('health', 100.0)
                    else:
                        health_score = 100.0
                    
                    total_health += health_score
                    component_count += 1
            
            # Calculate overall health
            if component_count > 0:
                health_status['overall_health'] = total_health / component_count
            
            # Determine status
            if health_status['overall_health'] < 50:
                health_status['status'] = 'critical'
            elif health_status['overall_health'] < 75:
                health_status['status'] = 'degraded'
            else:
                health_status['status'] = 'healthy'
            
            return health_status
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    async def _initialize_monitoring(self):
        """Initialize monitoring components."""
        try:
            from .monitoring import PerformanceMonitor
            
            monitor = PerformanceMonitor()
            self.components['monitoring'] = monitor
            
            logger.info("[OK] Monitoring initialized")
            
        except ImportError as e:
            logger.warning(f"Monitoring not available: {e}")
        except Exception as e:
            logger.error(f"Failed to initialize monitoring: {e}")
    
    async def _initialize_health_checks(self):
        """Initialize health check components."""
        try:
            from .health_check import HealthCheck
            
            health_check = HealthCheck()
            self.components['health_check'] = health_check
            
            logger.info("[OK] Health checks initialized")
            
        except ImportError as e:
            logger.warning(f"Health checks not available: {e}")
        except Exception as e:
            logger.error(f"Failed to initialize health checks: {e}")
    
    async def _initialize_auto_scaling(self):
        """Initialize auto-scaling components."""
        try:
            from .auto_scaling import AutoScaler
            
            scaler = AutoScaler(self.config)
            self.components['auto_scaler'] = scaler
            
            logger.info("[OK] Auto-scaling initialized")
            
        except ImportError as e:
            logger.warning(f"Auto-scaling not available: {e}")
        except Exception as e:
            logger.error(f"Failed to initialize auto-scaling: {e}")
    
    async def get_metrics(self) -> Dict[str, Any]:
        """Get infrastructure metrics.
        
        Returns:
            Dictionary with metrics
        """
        metrics = {
            'timestamp': datetime.now().isoformat(),
            'components': {}
        }
        
        for component_name, component in self.components.items():
            if hasattr(component, 'get_metrics'):
                try:
                    component_metrics = await component.get_metrics()
                    metrics['components'][component_name] = component_metrics
                except Exception as e:
                    logger.error(f"Failed to get metrics from {component_name}: {e}")
        
        return metrics
    
    async def scale(self, target_instances: int):
        """Scale infrastructure.
        
        Args:
            target_instances: Target number of instances
        """
        if 'auto_scaler' in self.components:
            scaler = self.components['auto_scaler']
            if hasattr(scaler, 'scale'):
                await scaler.scale(target_instances)
                logger.info(f"[OK] Scaled to {target_instances} instances")
        else:
            logger.warning("Auto-scaler not available")
    
    def get_status(self) -> Dict[str, Any]:
        """Get orchestrator status.
        
        Returns:
            Status dictionary
        """
        return {
            'running': self.running,
            'components': list(self.components.keys()),
            'component_count': len(self.components),
            'timestamp': datetime.now().isoformat()
        }


# Factory function for easy creation
def create_infrastructure_orchestrator(config: Optional[Dict] = None) -> InfrastructureOrchestrator:
    """Create an infrastructure orchestrator instance.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        InfrastructureOrchestrator instance
    """
    return InfrastructureOrchestrator(config)


# Alias for backward compatibility
SystemOrchestrator = InfrastructureOrchestrator


__all__ = [
    'InfrastructureOrchestrator',
    'SystemOrchestrator',
    'InfrastructureStatus',
    'create_infrastructure_orchestrator',
]
