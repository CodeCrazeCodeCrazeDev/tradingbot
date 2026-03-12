"""
Infrastructure Configuration Module
Configuration management for infrastructure components.
"""

import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class InfrastructureConfig:
    """Infrastructure configuration settings."""
    
    # Health check settings
    health_check_interval: int = 60
    health_check_timeout: int = 10
    
    # Auto-scaling settings
    auto_scaling_enabled: bool = False
    min_instances: int = 1
    max_instances: int = 10
    scale_up_threshold: float = 0.8
    scale_down_threshold: float = 0.3
    
    # Monitoring settings
    monitoring_enabled: bool = True
    metrics_interval: int = 30
    
    # Resource limits
    max_memory_mb: int = 4096
    max_cpu_percent: float = 80.0
    
    # Connection settings
    connection_pool_size: int = 10
    connection_timeout: int = 30
    
    # Retry settings
    max_retries: int = 3
    retry_delay: float = 1.0
    
    # Additional settings
    extra: Dict[str, Any] = field(default_factory=dict)


class InfrastructureConfigManager:
    """Manages infrastructure configuration."""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._config = InfrastructureConfig()
        self._initialized = True
        logger.info("InfrastructureConfigManager initialized")
    
    @property
    def config(self) -> InfrastructureConfig:
        """Get current configuration."""
        return self._config
    
    def update(self, **kwargs) -> None:
        """Update configuration settings.
        
        Args:
            **kwargs: Configuration key-value pairs
        """
        for key, value in kwargs.items():
            if hasattr(self._config, key):
                setattr(self._config, key, value)
            else:
                self._config.extra[key] = value
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value.
        
        Args:
            key: Configuration key
            default: Default value if not found
            
        Returns:
            Configuration value
        """
        if hasattr(self._config, key):
            return getattr(self._config, key)
        return self._config.extra.get(key, default)
    
    def to_dict(self) -> Dict[str, Any]:
        """Get configuration as dictionary.
        
        Returns:
            Configuration dictionary
        """
        return {
            'health_check_interval': self._config.health_check_interval,
            'health_check_timeout': self._config.health_check_timeout,
            'auto_scaling_enabled': self._config.auto_scaling_enabled,
            'min_instances': self._config.min_instances,
            'max_instances': self._config.max_instances,
            'scale_up_threshold': self._config.scale_up_threshold,
            'scale_down_threshold': self._config.scale_down_threshold,
            'monitoring_enabled': self._config.monitoring_enabled,
            'metrics_interval': self._config.metrics_interval,
            'max_memory_mb': self._config.max_memory_mb,
            'max_cpu_percent': self._config.max_cpu_percent,
            'connection_pool_size': self._config.connection_pool_size,
            'connection_timeout': self._config.connection_timeout,
            'max_retries': self._config.max_retries,
            'retry_delay': self._config.retry_delay,
            **self._config.extra
        }


# Singleton instance
_config_manager: Optional[InfrastructureConfigManager] = None


def get_infrastructure_config() -> InfrastructureConfigManager:
    """Get the infrastructure configuration manager.
    
    Returns:
        InfrastructureConfigManager instance
    """
    global _config_manager
    if _config_manager is None:
        _config_manager = InfrastructureConfigManager()
    return _config_manager


__all__ = [
    'InfrastructureConfig',
    'InfrastructureConfigManager',
    'get_infrastructure_config',
]
