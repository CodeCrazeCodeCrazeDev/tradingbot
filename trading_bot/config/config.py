"""
Configuration Module
Central configuration management for the trading bot.
"""

import logging
import os
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

# Default configuration
DEFAULT_CONFIG = {
    'trading': {
        'mode': 'paper',
        'symbols': ['EURUSD'],
        'timeframe': 'H1',
        'max_positions': 5,
        'max_risk_per_trade': 0.02,
        'max_daily_loss': 0.05,
        'max_drawdown': 0.20,
    },
    'broker': {
        'name': 'mt5',
        'server': '',
        'login': 0,
        'password': '',
    },
    'risk': {
        'max_position_size': 0.10,
        'max_leverage': 5,
        'stop_loss_pips': 50,
        'take_profit_pips': 100,
    },
    'data': {
        'cache_enabled': True,
        'cache_ttl': 300,
        'history_bars': 1000,
    },
    'logging': {
        'level': 'INFO',
        'file': 'logs/trading_bot.log',
    }
}


class Config:
    """Central configuration class."""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._config: Dict[str, Any] = DEFAULT_CONFIG.copy()
        self._initialized = True
        logger.info("Config initialized with defaults")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by dot-notation key.
        
        Args:
            key: Configuration key (e.g., 'trading.mode')
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any) -> None:
        """Set configuration value by dot-notation key.
        
        Args:
            key: Configuration key (e.g., 'trading.mode')
            value: Value to set
        """
        keys = key.split('.')
        config = self._config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
    
    def load_from_dict(self, config_dict: Dict[str, Any]) -> None:
        """Load configuration from dictionary.
        
        Args:
            config_dict: Configuration dictionary
        """
        self._deep_update(self._config, config_dict)
        logger.info("Config loaded from dictionary")
    
    def load_from_yaml(self, filepath: str) -> bool:
        """Load configuration from YAML file.
        
        Args:
            filepath: Path to YAML file
            
        Returns:
            True if successful
        """
        try:
            import yaml
            with open(filepath, 'r') as f:
                config_dict = yaml.safe_load(f)
            
            if config_dict:
                self._deep_update(self._config, config_dict)
                logger.info(f"Config loaded from: {filepath}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Failed to load config from {filepath}: {e}")
            return False
    
    def _deep_update(self, base: Dict, update: Dict) -> Dict:
        """Deep update dictionary."""
        for key, value in update.items():
            if isinstance(value, dict) and key in base and isinstance(base[key], dict):
                self._deep_update(base[key], value)
            else:
                base[key] = value
        return base
    
    def to_dict(self) -> Dict[str, Any]:
        """Get full configuration as dictionary.
        
        Returns:
            Configuration dictionary
        """
        return self._config.copy()
    
    @property
    def trading_mode(self) -> str:
        return self.get('trading.mode', 'paper')
    
    @property
    def symbols(self) -> list:
        return self.get('trading.symbols', ['EURUSD'])
    
    @property
    def max_risk_per_trade(self) -> float:
        return self.get('trading.max_risk_per_trade', 0.02)
    
    @property
    def max_daily_loss(self) -> float:
        return self.get('trading.max_daily_loss', 0.05)


# Singleton instance
_config: Optional[Config] = None


def get_config() -> Config:
    """Get the global configuration instance.
    
    Returns:
        Config instance
    """
    global _config
    if _config is None:
        _config = Config()
    return _config


def load_config(filepath: str = None) -> Config:
    """Load configuration from file.
    
    Args:
        filepath: Path to config file (default: config/config.yaml)
        
    Returns:
        Config instance
    """
    config = get_config()
    
    if filepath is None:
        filepath = os.path.join('config', 'config.yaml')
    
    if os.path.exists(filepath):
        config.load_from_yaml(filepath)
    
    return config


def get(key: str, default: Any = None) -> Any:
    """Convenience function to get config value.
    
    Args:
        key: Configuration key (dot-notation)
        default: Default value if not found
        
    Returns:
        Configuration value
    """
    return get_config().get(key, default)


__all__ = [
    'Config',
    'DEFAULT_CONFIG',
    'get_config',
    'load_config',
    'get',
]
