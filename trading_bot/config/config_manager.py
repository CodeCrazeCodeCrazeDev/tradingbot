"""
Config Manager Module - Compatibility Wrapper
Provides unified configuration management
"""

try:
    import yaml
except ImportError:
    yaml = None
import json
from pathlib import Path
from typing import Any, Dict, Optional
import logging
logger = logging.getLogger(__name__)
from typing import Set

class ConfigManager:
    """
    Configuration manager
    Handles loading and managing bot configuration
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize config manager
        
        Args:
            config_path: Path to configuration file (YAML or JSON)
        """
        self.config_path = config_path or "config/config.yaml"
        self.config: Dict[str, Any] = {}
        self.load_config()
    
    def load_config(self):
        """Load configuration from file"""
        config_file = Path(self.config_path)
        
        if not config_file.exists():
            logger.info(f"Warning: Config file not found: {config_file}")
            self.config = self._get_default_config()
            return
        try:
        
            with open(config_file, 'r', encoding='utf-8') as f:
                if config_file.suffix in ['.yaml', '.yml']:
                    self.config = yaml.safe_load(f) or {}
                elif config_file.suffix == '.json':
                    self.config = json.load(f)
                else:
                    raise ValueError(f"Unsupported config format: {config_file.suffix}")
            
            logger.info(f"Loaded config from: {config_file}")
            
        except Exception as e:
            logger.info(f"Error loading config: {e}")
            self.config = self._get_default_config()
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value
        
        Args:
            key: Configuration key (supports dot notation, e.g., 'risk.max_drawdown')
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default
        
        return value if value is not None else default
    
    def set(self, key: str, value: Any):
        """
        Set configuration value
        
        Args:
            key: Configuration key (supports dot notation)
            value: Value to set
        """
        keys = key.split('.')
        config = self.config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
    
    def save_config(self, output_path: Optional[str] = None):
        """
        Save configuration to file
        
        Args:
            output_path: Output file path (default: use original path)
        """
        output_file = Path(output_path or self.config_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                if output_file.suffix in ['.yaml', '.yml']:
                    yaml.dump(self.config, f, default_flow_style=False)
                elif output_file.suffix == '.json':
                    json.dump(self.config, f, indent=2)
            
            logger.info(f"Saved config to: {output_file}")
            
        except Exception as e:
            logger.info(f"Error saving config: {e}")
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration"""
        return {
            'trading': {
                'symbol': 'EURUSD',
                'timeframe': '1H',
                'paper_trading': True
            },
            'risk': {
                'max_lot_size': 1.0,
                'max_drawdown': 0.2,
                'risk_per_trade': 0.02,
                'stop_loss_pips': 50,
                'take_profit_pips': 100
            },
            'strategy': {
                'name': 'default',
                'parameters': {}
            },
            'logging': {
                'level': 'INFO',
                'file': 'logs/trading_bot.log'
            }
        }
    
    def get_all(self) -> Dict[str, Any]:
        """Get all configuration"""
        return self.config.copy()

# Export for compatibility
__all__ = ['ConfigManager']
