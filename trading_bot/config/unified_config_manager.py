"""
Unified Configuration Manager - Centralized configuration for all modules.
"""

import os
import yaml
import json
import logging
from typing import Dict, Any, Optional, List, Union
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum
import copy
from datetime import datetime

logger = logging.getLogger(__name__)

class ConfigSource(Enum):
    """Configuration source types."""
    FILE = "file"
    ENVIRONMENT = "environment"
    DATABASE = "database"
    REMOTE = "remote"
    MEMORY = "memory"

class ConfigFormat(Enum):
    """Configuration file formats."""
    YAML = "yaml"
    JSON = "json"
    TOML = "toml"
    INI = "ini"

@dataclass
class ConfigLayer:
    """A configuration layer with precedence."""
    name: str
    source: ConfigSource
    data: Dict[str, Any] = field(default_factory=dict)
    priority: int = 0  # Higher = higher precedence
    read_only: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

class ConfigValidator:
    """Configuration validation utilities."""
    
    def __init__(self):
        self.rules: Dict[str, List[callable]] = {}
    
    def add_rule(self, key: str, validator: callable) -> None:
        """Add validation rule for a config key."""
        if key not in self.rules:
            self.rules[key] = []
        self.rules[key].append(validator)
    
    def validate(self, config: Dict[str, Any]) -> List[str]:
        """Validate configuration and return list of errors."""
        errors = []
        
        for key, validators in self.rules.items():
            value = self._get_nested_value(config, key)
            
            for validator in validators:
                try:
                    if not validator(value):
                        errors.append(f"Validation failed for {key}")
                except Exception as e:
                    errors.append(f"Validation error for {key}: {e}")
        
        return errors
    
    def _get_nested_value(self, data: Dict[str, Any], key: str) -> Any:
        """Get nested value using dot notation."""
        keys = key.split('.')
        current = data
        
        for k in keys:
            if isinstance(current, dict) and k in current:
                current = current[k]
            else:
                return None
        
        return current

class UnifiedConfigManager:
    """
    Unified configuration manager for the trading bot.
    
    Features:
    - Multiple configuration sources with precedence
    - Environment-specific configs
    - Validation and type checking
    - Hot reloading
    - Configuration templates
    - Secret management
    """
    
    def __init__(self):
        self.layers: List[ConfigLayer] = []
        self.validator = ConfigValidator()
        self.watchers: List[callable] = []
        self.cache: Dict[str, Any] = {}
        self.cache_valid = False
        
        # Default configuration paths
        self.config_paths = [
            "config.yaml",
            "config/config.yaml",
            "config/trading.yaml",
            os.path.expanduser("~/.trading_bot/config.yaml"),
            "/etc/trading_bot/config.yaml"
        ]
        
        # Environment-specific suffixes
        self.env_suffixes = {
            'development': '.dev',
            'testing': '.test',
            'staging': '.staging',
            'production': '.prod',
            'live': '.live'
        }
        
        # Add default validation rules
        self._add_default_rules()
    
    def _add_default_rules(self) -> None:
        """Add default validation rules."""
        # Trading configuration
        self.validator.add_rule('trading.mode', 
            lambda x: x in ['paper', 'simulation', 'live'])
        self.validator.add_rule('trading.risk_per_trade',
            lambda x: isinstance(x, (int, float)) and 0 < x <= 1)
        self.validator.add_rule('trading.max_positions',
            lambda x: isinstance(x, int) and x > 0)
        
        # API configuration
        self.validator.add_rule('api.timeout',
            lambda x: isinstance(x, (int, float)) and x > 0)
        self.validator.add_rule('api.retry_attempts',
            lambda x: isinstance(x, int) and x >= 0)
    
    def add_layer(self, 
                  name: str,
                  data: Dict[str, Any],
                  source: ConfigSource = ConfigSource.MEMORY,
                  priority: int = 0,
                  read_only: bool = False) -> None:
        """Add a configuration layer."""
        layer = ConfigLayer(
            name=name,
            source=source,
            data=copy.deepcopy(data),
            priority=priority,
            read_only=read_only,
            metadata={'added_at': datetime.now()}
        )
        
        self.layers.append(layer)
        self.layers.sort(key=lambda x: x.priority)
        self.cache_valid = False
        
        logger.debug(f"Added config layer: {name} (priority={priority})")
    
    def load_from_file(self, 
                       filepath: str,
                       name: str = None,
                       priority: int = 0,
                       format: ConfigFormat = None) -> bool:
        """Load configuration from file."""
        path = Path(filepath)
        
        if not path.exists():
            logger.warning(f"Config file not found: {filepath}")
            return False
        
        # Detect format if not specified
        if format is None:
            if path.suffix.lower() in ['.yaml', '.yml']:
                format = ConfigFormat.YAML
            elif path.suffix.lower() == '.json':
                format = ConfigFormat.JSON
            else:
                logger.error(f"Unknown config format: {path.suffix}")
                return False
        
        try:
            with open(path, 'r') as f:
                if format == ConfigFormat.YAML:
                    data = yaml.safe_load(f) or {}
                elif format == ConfigFormat.JSON:
                    data = json.load(f)
                else:
                    logger.error(f"Unsupported format: {format}")
                    return False
            
            self.add_layer(
                name=name or f"file:{filepath}",
                data=data,
                source=ConfigSource.FILE,
                priority=priority,
                read_only=True
            )
            
            logger.info(f"Loaded config from {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load config from {filepath}: {e}")
            return False
    
    def load_from_environment(self, 
                             prefix: str = "TRADING_",
                             priority: int = 100) -> None:
        """Load configuration from environment variables."""
        env_config = {}
        
        for key, value in os.environ.items():
            if key.startswith(prefix):
                # Remove prefix and convert to lowercase
                config_key = key[len(prefix):].lower()
                
                # Convert underscores to dots for nested keys
                config_key = config_key.replace('_', '.')
                
                # Try to parse as JSON, fallback to string
                try:
                    parsed_value = json.loads(value)
                except (json.JSONDecodeError, ValueError):
                    parsed_value = value
                
                # Set nested key
                self._set_nested_value(env_config, config_key, parsed_value)
        
        if env_config:
            self.add_layer(
                name="environment",
                data=env_config,
                source=ConfigSource.ENVIRONMENT,
                priority=priority,
                read_only=True
            )
            
            logger.info(f"Loaded {len(env_config)} config values from environment")
    
    def load(self, 
             config_path: str = None,
             environment: str = None,
             include_defaults: bool = True) -> Dict[str, Any]:
        """
        Load configuration from multiple sources.
        
        Args:
            config_path: Specific config file to load
            environment: Environment name (dev, test, prod)
            include_defaults: Whether to include default config
            
        Returns:
            Merged configuration dictionary
        """
        # Clear existing layers if starting fresh
        if include_defaults:
            self._load_defaults()
        
        # Load main config file
        if config_path:
            self.load_from_file(config_path, priority=50)
        else:
            # Try default paths
            for path in self.config_paths:
                if self.load_from_file(path, priority=50):
                    break
        
        # Load environment-specific config
        if environment and config_path:
            env_path = self._get_env_path(config_path, environment)
            self.load_from_file(env_path, priority=60)
        
        # Load environment variables
        self.load_from_environment()
        
        # Validate configuration
        config = self.get_merged_config()
        errors = self.validator.validate(config)
        
        if errors:
            logger.error(f"Configuration validation failed: {errors}")
            raise ValueError(f"Invalid configuration: {errors}")
        
        return config
    
    def _load_defaults(self) -> None:
        """Load default configuration."""
        defaults = {
            'trading': {
                'mode': 'paper',
                'risk_per_trade': 0.02,
                'max_positions': 5,
                'symbols': ['EURUSD'],
                'timeframes': ['M5', 'M15', 'H1']
            },
            'api': {
                'timeout': 30,
                'retry_attempts': 3,
                'retry_delay': 1
            },
            'logging': {
                'level': 'INFO',
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            },
            'database': {
                'url': 'sqlite:///trading_bot.db',
                'pool_size': 5
            },
            'features': {
                'enable_ai': True,
                'enable_ml': True,
                'enable_evolution': False,
                'enable_sentient': False
            }
        }
        
        self.add_layer(
            name="defaults",
            data=defaults,
            source=ConfigSource.MEMORY,
            priority=0,
            read_only=True
        )
    
    def _get_env_path(self, base_path: str, environment: str) -> str:
        """Get environment-specific config path."""
        path = Path(base_path)
        suffix = self.env_suffixes.get(environment, f'.{environment}')
        
        # Insert suffix before extension
        env_path = path.with_name(f"{path.stem}{suffix}{path.suffix}")
        return str(env_path)
    
    def _set_nested_value(self, data: Dict[str, Any], key: str, value: Any) -> None:
        """Set nested value using dot notation."""
        keys = key.split('.')
        current = data
        
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]
        
        current[keys[-1]] = value
    
    def get_merged_config(self) -> Dict[str, Any]:
        """Get merged configuration from all layers."""
        if not self.cache_valid:
            self.cache = {}
            
            # Merge layers in priority order
            for layer in sorted(self.layers, key=lambda x: x.priority):
                self._deep_merge(self.cache, layer.data)
            
            self.cache_valid = True
        
        return copy.deepcopy(self.cache)
    
    def _deep_merge(self, base: Dict[str, Any], update: Dict[str, Any]) -> None:
        """Deep merge two dictionaries."""
        for key, value in update.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = copy.deepcopy(value)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value using dot notation."""
        config = self.get_merged_config()
        return self._get_nested_value(config, key, default)
    
    def _get_nested_value(self, data: Dict[str, Any], key: str, default: Any = None) -> Any:
        """Get nested value using dot notation."""
        keys = key.split('.')
        current = data
        
        for k in keys:
            if isinstance(current, dict) and k in current:
                current = current[k]
            else:
                return default
        
        return current
    
    def set(self, key: str, value: Any, layer: str = "runtime") -> bool:
        """Set configuration value."""
        # Find or create layer
        target_layer = None
        for l in self.layers:
            if l.name == layer:
                target_layer = l
                break
        
        if target_layer is None:
            target_layer = ConfigLayer(
                name=layer,
                source=ConfigSource.MEMORY,
                priority=200  # High priority for runtime changes
            )
            self.layers.append(target_layer)
        
        if target_layer.read_only:
            logger.error(f"Cannot set value on read-only layer: {layer}")
            return False
        
        # Set value
        self._set_nested_value(target_layer.data, key, value)
        self.cache_valid = False
        
        # Notify watchers
        self._notify_watchers(key, value)
        
        return True
    
    def add_watcher(self, callback: callable) -> None:
        """Add configuration change watcher."""
        self.watchers.append(callback)
    
    def _notify_watchers(self, key: str, value: Any) -> None:
        """Notify all watchers of configuration change."""
        for watcher in self.watchers:
            try:
                watcher(key, value)
            except Exception as e:
                logger.error(f"Config watcher error: {e}")
    
    def save(self, filepath: str, format: ConfigFormat = ConfigFormat.YAML) -> bool:
        """Save current configuration to file."""
        config = self.get_merged_config()
        
        try:
            path = Path(filepath)
            path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(path, 'w') as f:
                if format == ConfigFormat.YAML:
                    yaml.dump(config, f, default_flow_style=False, indent=2)
                elif format == ConfigFormat.JSON:
                    json.dump(config, f, indent=2)
                else:
                    logger.error(f"Unsupported format: {format}")
                    return False
            
            logger.info(f"Configuration saved to {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
            return False
    
    def export_template(self, filepath: str, include_docs: bool = True) -> bool:
        """Export configuration template with documentation."""
        template = {
            'trading': {
                'mode': 'paper',  # paper, simulation, live
                'risk_per_trade': 0.02,  # 2% risk per trade
                'max_positions': 5,
                'symbols': ['EURUSD', 'GBPUSD'],
                'timeframes': ['M5', 'M15', 'H1']
            },
            'api': {
                'timeout': 30,  # seconds
                'retry_attempts': 3,
                'retry_delay': 1  # seconds
            },
            'logging': {
                'level': 'INFO',  # DEBUG, INFO, WARNING, ERROR, CRITICAL
                'file': 'logs/trading_bot.log',
                'max_size': '10MB',
                'backup_count': 5
            },
            'database': {
                'url': 'sqlite:///trading_bot.db',
                'pool_size': 5,
                'echo': False  # SQL logging
            },
            'features': {
                'enable_ai': True,
                'enable_ml': True,
                'enable_evolution': False,
                'enable_sentient': False,
                'enable_quantum': False
            },
            'brokers': {
                'mt5': {
                    'login': 123456,
                    'password': 'your_password',
                    'server': 'YourBroker-Demo',
                    'path': 'C:\\Program Files\\MetaTrader 5\\terminal64.exe'
                },
                'alpaca': {
                    'api_key': 'your_api_key',
                    'api_secret': 'your_api_secret',
                    'paper': True
                }
            }
        }
        
        if include_docs:
            # Add documentation as comments
            template['_documentation'] = {
                'trading.mode': "Trading mode: paper (no real trades), simulation (simulated fills), live (real trades)",
                'trading.risk_per_trade': "Fraction of capital to risk per trade (0.01 = 1%, 0.02 = 2%)",
                'features.enable_ai': "Enable AI-powered features",
                'features.enable_evolution': "Enable self-evolution features (experimental)",
                'features.enable_sentient': "Enable sentient AI features (experimental)"
            }
        
        return self.save(filepath.replace('.yaml', '_template.yaml'), ConfigFormat.YAML)
    
    def get_layer_info(self) -> List[Dict[str, Any]]:
        """Get information about all configuration layers."""
        return [
            {
                'name': layer.name,
                'source': layer.source.value,
                'priority': layer.priority,
                'read_only': layer.read_only,
                'keys_count': len(self._flatten_dict(layer.data)),
                'metadata': layer.metadata
            }
            for layer in self.layers
        ]
    
    def _flatten_dict(self, data: Dict[str, Any], prefix: str = '') -> Dict[str, Any]:
        """Flatten nested dictionary."""
        result = {}
        
        for key, value in data.items():
            full_key = f"{prefix}.{key}" if prefix else key
            
            if isinstance(value, dict):
                result.update(self._flatten_dict(value, full_key))
            else:
                result[full_key] = value
        
        return result

# Global instance
_config_manager = None

def get_config_manager() -> UnifiedConfigManager:
    """Get the global configuration manager."""
    global _config_manager
    if _config_manager is None:
        _config_manager = UnifiedConfigManager()
    return _config_manager
