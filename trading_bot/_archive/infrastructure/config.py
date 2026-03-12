"""
Layer 7: Infrastructure & Orchestration - Configuration Manager
Centralized configuration management with validation and defaults.
"""

import os
import json
import yaml
from typing import Dict, Any, Optional, Union
from dataclasses import dataclass, field
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


@dataclass
class TradingConfig:
    """Core trading configuration."""
    mode: str = "paper"  # paper, live, backtest
    symbol: str = "EURUSD"
    timeframe: str = "M15"
    max_risk_per_trade: float = 0.02  # 2%
    max_drawdown: float = 0.20  # 20%
    stop_loss_pips: int = 20
    take_profit_pips: int = 40


@dataclass
class DataConfig:
    """Data layer configuration."""
    sources: list = field(default_factory=lambda: ["mt5"])
    cache_enabled: bool = True
    cache_ttl_seconds: int = 300
    validation_enabled: bool = True
    max_data_age_hours: int = 24


@dataclass
class RiskConfig:
    """Risk management configuration."""
    max_positions: int = 5
    max_leverage: float = 10.0
    correlation_threshold: float = 0.7
    var_confidence: float = 0.95
    stress_test_enabled: bool = True


@dataclass
class ExecutionConfig:
    """Execution layer configuration."""
    slippage_tolerance_bps: int = 5
    max_order_retry: int = 3
    order_timeout_seconds: int = 30
    execution_algo: str = "smart"  # smart, twap, vwap


@dataclass
class MonitoringConfig:
    """Monitoring and audit configuration."""
    health_check_interval: int = 60
    metrics_enabled: bool = True
    alert_email: Optional[str] = None
    log_level: str = "INFO"


@dataclass
class SystemConfig:
    """Complete system configuration."""
    trading: TradingConfig = field(default_factory=TradingConfig)
    data: DataConfig = field(default_factory=DataConfig)
    risk: RiskConfig = field(default_factory=RiskConfig)
    execution: ExecutionConfig = field(default_factory=ExecutionConfig)
    monitoring: MonitoringConfig = field(default_factory=MonitoringConfig)
    
    # System-level settings
    environment: str = "development"  # development, staging, production
    debug: bool = False
    worker_threads: int = 4


class ConfigManager:
    """
    Centralized configuration management.
    
    Responsibilities:
    - Load configuration from multiple sources
    - Validate configuration values
    - Provide environment-specific overrides
    - Ensure safe defaults
    """
    
    _instance: Optional['ConfigManager'] = None
    _config: Optional[SystemConfig] = None
    
    def __new__(cls) -> 'ConfigManager':
        """Singleton pattern for global config access."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    def load(cls, config_path: Optional[Union[str, Path]] = None) -> SystemConfig:
        """Load configuration from file or environment."""
        instance = cls()
        
        if instance._config is not None:
            return instance._config
            
        # Start with defaults
        config = SystemConfig()
        
        # Load from file if provided
        if config_path:
            file_config = instance._load_from_file(config_path)
            config = instance._merge_configs(config, file_config)
            
        # Override with environment variables
        env_config = instance._load_from_environment()
        config = instance._merge_configs(config, env_config)
        
        # Validate configuration
        instance._validate_config(config)
        
        instance._config = config
        logger.info(f"Configuration loaded: mode={config.trading.mode}, env={config.environment}")
        
        return config
    
    def _load_from_file(self, config_path: Union[str, Path]) -> Dict[str, Any]:
        """Load configuration from YAML or JSON file."""
        path = Path(config_path)
        
        if not path.exists():
            logger.warning(f"Config file not found: {path}")
            return {}
        try:
            
            with open(path, 'r') as f:
                if path.suffix.lower() in ['.yaml', '.yml']:
                    return yaml.safe_load(f) or {}
                elif path.suffix.lower() == '.json':
                    return json.load(f) or {}
                else:
                    logger.error(f"Unsupported config file format: {path.suffix}")
                    return {}
                    
        except Exception as e:
            logger.error(f"Failed to load config file {path}: {e}")
            return {}
    
    def _load_from_environment(self) -> Dict[str, Any]:
        """Load configuration from environment variables."""
        env_config = {}
        
        # Trading configuration
        if os.getenv('TRADING_MODE'):
            env_config.setdefault('trading', {})['mode'] = os.getenv('TRADING_MODE')
        if os.getenv('TRADING_SYMBOL'):
            env_config.setdefault('trading', {})['symbol'] = os.getenv('TRADING_SYMBOL')
        if os.getenv('MAX_RISK_PER_TRADE'):
            env_config.setdefault('trading', {})['max_risk_per_trade'] = float(os.getenv('MAX_RISK_PER_TRADE'))
            
        # System configuration
        if os.getenv('ENVIRONMENT'):
            env_config['environment'] = os.getenv('ENVIRONMENT')
        if os.getenv('DEBUG'):
            env_config['debug'] = os.getenv('DEBUG').lower() in ['true', '1', 'yes']
        if os.getenv('LOG_LEVEL'):
            env_config.setdefault('monitoring', {})['log_level'] = os.getenv('LOG_LEVEL')
            
        return env_config
    
    def _merge_configs(self, base_config: SystemConfig, override_dict: Dict[str, Any]) -> SystemConfig:
        """Merge configuration dictionary into SystemConfig object."""
        # Convert SystemConfig to dict for merging
        base_dict = self._config_to_dict(base_config)
        
        # Deep merge
        merged_dict = self._deep_merge(base_dict, override_dict)
        
        # Convert back to SystemConfig
        return self._dict_to_config(merged_dict)
    
    def _config_to_dict(self, config: SystemConfig) -> Dict[str, Any]:
        """Convert SystemConfig to dictionary."""
        return {
            'trading': {
                'mode': config.trading.mode,
                'symbol': config.trading.symbol,
                'timeframe': config.trading.timeframe,
                'max_risk_per_trade': config.trading.max_risk_per_trade,
                'max_drawdown': config.trading.max_drawdown,
                'stop_loss_pips': config.trading.stop_loss_pips,
                'take_profit_pips': config.trading.take_profit_pips,
            },
            'data': {
                'sources': config.data.sources,
                'cache_enabled': config.data.cache_enabled,
                'cache_ttl_seconds': config.data.cache_ttl_seconds,
                'validation_enabled': config.data.validation_enabled,
                'max_data_age_hours': config.data.max_data_age_hours,
            },
            'risk': {
                'max_positions': config.risk.max_positions,
                'max_leverage': config.risk.max_leverage,
                'correlation_threshold': config.risk.correlation_threshold,
                'var_confidence': config.risk.var_confidence,
                'stress_test_enabled': config.risk.stress_test_enabled,
            },
            'execution': {
                'slippage_tolerance_bps': config.execution.slippage_tolerance_bps,
                'max_order_retry': config.execution.max_order_retry,
                'order_timeout_seconds': config.execution.order_timeout_seconds,
                'execution_algo': config.execution.execution_algo,
            },
            'monitoring': {
                'health_check_interval': config.monitoring.health_check_interval,
                'metrics_enabled': config.monitoring.metrics_enabled,
                'alert_email': config.monitoring.alert_email,
                'log_level': config.monitoring.log_level,
            },
            'environment': config.environment,
            'debug': config.debug,
            'worker_threads': config.worker_threads,
        }
    
    def _dict_to_config(self, config_dict: Dict[str, Any]) -> SystemConfig:
        """Convert dictionary to SystemConfig."""
        return SystemConfig(
            trading=TradingConfig(**config_dict.get('trading', {})),
            data=DataConfig(**config_dict.get('data', {})),
            risk=RiskConfig(**config_dict.get('risk', {})),
            execution=ExecutionConfig(**config_dict.get('execution', {})),
            monitoring=MonitoringConfig(**config_dict.get('monitoring', {})),
            environment=config_dict.get('environment', 'development'),
            debug=config_dict.get('debug', False),
            worker_threads=config_dict.get('worker_threads', 4),
        )
    
    def _deep_merge(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Deep merge two dictionaries."""
        result = base.copy()
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
                
        return result
    
    def _validate_config(self, config: SystemConfig) -> None:
        """Validate configuration values."""
        # Trading validation
        if config.trading.mode not in ['paper', 'live', 'backtest']:
            raise ValueError(f"Invalid trading mode: {config.trading.mode}")
            
        if config.trading.max_risk_per_trade <= 0 or config.trading.max_risk_per_trade > 0.1:
            raise ValueError(f"Invalid max_risk_per_trade: {config.trading.max_risk_per_trade}")
            
        if config.trading.max_drawdown <= 0 or config.trading.max_drawdown > 0.5:
            raise ValueError(f"Invalid max_drawdown: {config.trading.max_drawdown}")
            
        # Risk validation
        if config.risk.max_positions <= 0 or config.risk.max_positions > 100:
            raise ValueError(f"Invalid max_positions: {config.risk.max_positions}")
            
        if config.risk.max_leverage <= 0 or config.risk.max_leverage > 500:
            raise ValueError(f"Invalid max_leverage: {config.risk.max_leverage}")
            
        # System validation
        if config.environment not in ['development', 'staging', 'production']:
            raise ValueError(f"Invalid environment: {config.environment}")
            
        logger.info("Configuration validation passed")
    
    @classmethod
    def get_config(cls) -> SystemConfig:
        """Get current configuration (must be loaded first)."""
        instance = cls()
        if instance._config is None:
            raise RuntimeError("Configuration not loaded. Call ConfigManager.load() first.")
        return instance._config
    
    @classmethod
    def reset(cls) -> None:
        """Reset configuration (for testing)."""
        instance = cls()
        instance._config = None
