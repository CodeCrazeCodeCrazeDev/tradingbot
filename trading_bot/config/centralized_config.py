"""
Centralized Configuration Management
=====================================
Single source of truth for all configuration.
Supports environment variables, YAML files, and runtime overrides.
"""

import json
import logging
import os
import threading
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, TypeVar, Union
try:
    import yaml
except ImportError:
    yaml = None
from typing import Set

logger = logging.getLogger(__name__)

T = TypeVar('T')


# ============================================================================
# CONFIGURATION SECTIONS
# ============================================================================

@dataclass
class TradingConfig:
    """Trading configuration."""
    mode: str = "paper"  # paper, live
    symbols: List[str] = field(default_factory=lambda: ["EURUSD"])
    timeframes: List[str] = field(default_factory=lambda: ["M15", "H1", "H4"])
    max_positions: int = 5
    max_orders_per_symbol: int = 3
    default_lot_size: float = 0.01
    min_lot_size: float = 0.01
    max_lot_size: float = 1.0
    slippage_tolerance: float = 3.0  # pips
    spread_limit: float = 5.0  # pips


@dataclass
class RiskConfig:
    """Risk management configuration."""
    max_risk_per_trade: float = 0.02  # 2%
    max_daily_loss: float = 0.05  # 5%
    max_drawdown: float = 0.20  # 20%
    max_correlation_exposure: float = 0.30  # 30%
    max_sector_exposure: float = 0.40  # 40%
    stop_loss_atr_multiplier: float = 2.0
    take_profit_atr_multiplier: float = 3.0
    trailing_stop_enabled: bool = True
    trailing_stop_distance: float = 1.5  # ATR multiplier
    use_kelly_criterion: bool = True
    kelly_fraction: float = 0.25  # Quarter Kelly
    var_confidence: float = 0.95
    var_horizon_days: int = 1


@dataclass
class BrokerConfig:
    """Broker configuration."""
    broker_type: str = "mt5"  # mt5, alpaca, binance
    api_key: str = ""
    api_secret: str = ""
    account_id: str = ""
    server: str = ""
    login: int = 0
    password: str = ""
    terminal_path: str = ""
    is_paper: bool = True
    timeout: int = 30
    retry_attempts: int = 3
    retry_delay: float = 1.0


@dataclass
class DataConfig:
    """Data configuration."""
    primary_source: str = "mt5"  # mt5, yahoo, binance, alpaca
    fallback_sources: List[str] = field(default_factory=lambda: ["yahoo", "binance"])
    cache_enabled: bool = True
    cache_ttl_seconds: int = 60
    history_days: int = 365
    tick_data_enabled: bool = False
    staleness_threshold_seconds: int = 30
    validation_enabled: bool = True
    quarantine_enabled: bool = True


@dataclass
class MLConfig:
    """Machine learning configuration."""
    enabled: bool = True
    model_path: str = "models/"
    prediction_confidence_threshold: float = 0.7
    retrain_interval_hours: int = 24
    feature_importance_threshold: float = 0.01
    ensemble_enabled: bool = True
    ensemble_models: List[str] = field(default_factory=lambda: ["lstm", "transformer", "xgboost"])
    online_learning_enabled: bool = True
    drift_detection_enabled: bool = True


@dataclass
class SignalConfig:
    """Signal configuration."""
    min_confidence: float = 0.6
    signal_ttl_seconds: int = 300
    decay_rate: float = 0.1
    multi_timeframe_required: bool = True
    min_timeframe_agreement: int = 2
    news_gating_enabled: bool = True
    news_blackout_minutes: int = 30
    validation_required: bool = True
    min_validation_score: float = 0.7


@dataclass
class ExecutionConfig:
    """Execution configuration."""
    algorithm: str = "smart"  # market, twap, vwap, smart
    twap_duration_minutes: int = 10
    twap_slices: int = 5
    vwap_participation_rate: float = 0.1
    smart_routing_enabled: bool = True
    dark_pool_enabled: bool = False
    iceberg_enabled: bool = True
    iceberg_show_ratio: float = 0.2
    max_slippage_bps: int = 10
    retry_on_reject: bool = True
    max_retry_attempts: int = 3


@dataclass
class MonitoringConfig:
    """Monitoring configuration."""
    enabled: bool = True
    dashboard_port: int = 8050
    metrics_port: int = 9090
    health_check_interval: int = 30
    alert_channels: List[str] = field(default_factory=lambda: ["log", "telegram"])
    log_level: str = "INFO"
    log_file: str = "logs/trading_bot.log"
    log_rotation: str = "daily"
    log_retention_days: int = 30


@dataclass
class DatabaseConfig:
    """Database configuration."""
    db_type: str = "sqlite"  # sqlite, postgresql
    host: str = "localhost"
    port: int = 5432
    database: str = "trading_bot"
    username: str = ""
    password: str = ""
    sqlite_path: str = "trading_bot.db"
    pool_size: int = 5
    auto_migrate: bool = True


@dataclass
class TelegramConfig:
    """Telegram bot configuration."""
    enabled: bool = False
    bot_token: str = ""
    chat_id: str = ""
    admin_ids: List[str] = field(default_factory=list)
    notification_types: List[str] = field(default_factory=lambda: ["trade", "alert", "error"])


@dataclass
class APIConfig:
    """External API configuration."""
    alpha_vantage_key: str = ""
    news_api_key: str = ""
    fred_api_key: str = ""
    twitter_bearer_token: str = ""
    reddit_client_id: str = ""
    reddit_client_secret: str = ""


@dataclass
class RateLimitConfig:
    """Rate limiting configuration."""
    enabled: bool = True
    default_requests_per_minute: int = 60
    default_requests_per_second: int = 5
    burst_allowance: int = 10
    backoff_multiplier: float = 2.0
    max_backoff_seconds: int = 300


@dataclass
class PerformanceConfig:
    """Performance configuration."""
    parallel_processing: bool = True
    max_workers: int = 4
    memory_limit_mb: int = 1024
    cache_size_mb: int = 256
    gc_interval_seconds: int = 300
    profiling_enabled: bool = False
    profiling_interval: int = 60


# ============================================================================
# MAIN CONFIGURATION CLASS
# ============================================================================

@dataclass
class AppConfig:
    """Main application configuration."""
    trading: TradingConfig = field(default_factory=TradingConfig)
    risk: RiskConfig = field(default_factory=RiskConfig)
    broker: BrokerConfig = field(default_factory=BrokerConfig)
    data: DataConfig = field(default_factory=DataConfig)
    ml: MLConfig = field(default_factory=MLConfig)
    signal: SignalConfig = field(default_factory=SignalConfig)
    execution: ExecutionConfig = field(default_factory=ExecutionConfig)
    monitoring: MonitoringConfig = field(default_factory=MonitoringConfig)
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    telegram: TelegramConfig = field(default_factory=TelegramConfig)
    api: APIConfig = field(default_factory=APIConfig)
    rate_limit: RateLimitConfig = field(default_factory=RateLimitConfig)
    performance: PerformanceConfig = field(default_factory=PerformanceConfig)


# ============================================================================
# CONFIGURATION MANAGER
# ============================================================================

class ConfigManager:
    """
    Centralized configuration manager.
    Handles loading, validation, and runtime updates.
    """
    
    _instance: Optional['ConfigManager'] = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._config: AppConfig = AppConfig()
        self._config_file: Optional[Path] = None
        self._env_prefix = "TRADING_BOT_"
        self._callbacks: List[Callable] = []
        self._overrides: Dict[str, Any] = {}
        self._lock = threading.Lock()
        self._initialized = True
    
    def load(
        self,
        config_file: Optional[str] = None,
        env_prefix: str = "TRADING_BOT_",
    ) -> AppConfig:
        """
        Load configuration from multiple sources.
        Priority: Runtime overrides > Environment > Config file > Defaults
        """
        self._env_prefix = env_prefix
        
        # Start with defaults
        self._config = AppConfig()
        
        # Load from file
        if config_file:
            self._load_from_file(config_file)
        else:
            # Try default locations
            for path in ["config.yaml", "config/config.yaml", "trading_bot/config/config.yaml"]:
                if Path(path).exists():
                    self._load_from_file(path)
                    break
        
        # Load from environment
        self._load_from_env()
        
        # Apply overrides
        self._apply_overrides()
        
        # Validate
        self._validate()
        
        logger.info("Configuration loaded successfully")
        return self._config
    
    def _load_from_file(self, file_path: str):
        """Load configuration from YAML file."""
        try:
            path = Path(file_path)
            if not path.exists():
                logger.warning(f"Config file not found: {file_path}")
                return
            
            with open(path, 'r') as f:
                data = yaml.safe_load(f)
            
            if not data:
                return
            
            self._config_file = path
            self._apply_dict_to_config(data)
            logger.info(f"Loaded config from: {file_path}")
            
        except Exception as e:
            logger.error(f"Failed to load config file: {e}")
    
    def _load_from_env(self):
        """Load configuration from environment variables."""
        env_mappings = {
            # Trading
            f"{self._env_prefix}MODE": ("trading", "mode"),
            f"{self._env_prefix}SYMBOLS": ("trading", "symbols"),
            f"{self._env_prefix}MAX_POSITIONS": ("trading", "max_positions"),
            
            # Risk
            f"{self._env_prefix}MAX_RISK_PER_TRADE": ("risk", "max_risk_per_trade"),
            f"{self._env_prefix}MAX_DAILY_LOSS": ("risk", "max_daily_loss"),
            f"{self._env_prefix}MAX_DRAWDOWN": ("risk", "max_drawdown"),
            
            # Broker
            f"{self._env_prefix}BROKER_TYPE": ("broker", "broker_type"),
            f"{self._env_prefix}BROKER_API_KEY": ("broker", "api_key"),
            f"{self._env_prefix}BROKER_API_SECRET": ("broker", "api_secret"),
            f"{self._env_prefix}BROKER_ACCOUNT_ID": ("broker", "account_id"),
            f"{self._env_prefix}MT5_LOGIN": ("broker", "login"),
            f"{self._env_prefix}MT5_PASSWORD": ("broker", "password"),
            f"{self._env_prefix}MT5_SERVER": ("broker", "server"),
            
            # Database
            f"{self._env_prefix}DB_TYPE": ("database", "db_type"),
            f"{self._env_prefix}DB_HOST": ("database", "host"),
            f"{self._env_prefix}DB_PORT": ("database", "port"),
            f"{self._env_prefix}DB_NAME": ("database", "database"),
            f"{self._env_prefix}DB_USER": ("database", "username"),
            f"{self._env_prefix}DB_PASSWORD": ("database", "password"),
            
            # Telegram
            f"{self._env_prefix}TELEGRAM_TOKEN": ("telegram", "bot_token"),
            f"{self._env_prefix}TELEGRAM_CHAT_ID": ("telegram", "chat_id"),
            
            # APIs
            f"{self._env_prefix}ALPHA_VANTAGE_KEY": ("api", "alpha_vantage_key"),
            f"{self._env_prefix}NEWS_API_KEY": ("api", "news_api_key"),
            f"{self._env_prefix}FRED_API_KEY": ("api", "fred_api_key"),
            
            # Monitoring
            f"{self._env_prefix}LOG_LEVEL": ("monitoring", "log_level"),
            f"{self._env_prefix}DASHBOARD_PORT": ("monitoring", "dashboard_port"),
        }
        
        for env_var, (section, key) in env_mappings.items():
            value = os.environ.get(env_var)
            if value is not None:
                self._set_config_value(section, key, value)
    
    def _apply_dict_to_config(self, data: Dict):
        """Apply dictionary to configuration."""
        for section, values in data.items():
            if hasattr(self._config, section) and isinstance(values, dict):
                section_config = getattr(self._config, section)
                for key, value in values.items():
                    if hasattr(section_config, key):
                        setattr(section_config, key, value)
    
    def _set_config_value(self, section: str, key: str, value: Any):
        """Set a configuration value."""
        if hasattr(self._config, section):
            section_config = getattr(self._config, section)
            if hasattr(section_config, key):
                # Type conversion
                current_value = getattr(section_config, key)
                if isinstance(current_value, bool):
                    value = value.lower() in ('true', '1', 'yes') if isinstance(value, str) else bool(value)
                elif isinstance(current_value, int):
                    value = int(value)
                elif isinstance(current_value, float):
                    value = float(value)
                elif isinstance(current_value, list) and isinstance(value, str):
                    value = [v.strip() for v in value.split(',')]
                
                setattr(section_config, key, value)
    
    def _apply_overrides(self):
        """Apply runtime overrides."""
        for key, value in self._overrides.items():
            parts = key.split('.')
            if len(parts) == 2:
                self._set_config_value(parts[0], parts[1], value)
    
    def _validate(self):
        """Validate configuration."""
        errors = []
        
        # Risk validation
        if self._config.risk.max_risk_per_trade > 0.05:
            errors.append("max_risk_per_trade should not exceed 5%")
        
        if self._config.risk.max_daily_loss > 0.10:
            errors.append("max_daily_loss should not exceed 10%")
        
        if self._config.risk.max_drawdown > 0.30:
            errors.append("max_drawdown should not exceed 30%")
        
        # Trading validation
        if self._config.trading.mode == "live" and self._config.broker.is_paper:
            errors.append("Cannot use paper broker in live mode")
        
        # Log warnings
        for error in errors:
            logger.warning(f"Config validation: {error}")
    
    def set(self, key: str, value: Any):
        """Set a configuration value at runtime."""
        with self._lock:
            self._overrides[key] = value
            parts = key.split('.')
            if len(parts) == 2:
                self._set_config_value(parts[0], parts[1], value)
            
            # Notify callbacks
            for callback in self._callbacks:
                try:
                    callback(key, value)
                except Exception as e:
                    logger.error(f"Config callback error: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value."""
        parts = key.split('.')
        if len(parts) == 2:
            section, attr = parts
            if hasattr(self._config, section):
                section_config = getattr(self._config, section)
                if hasattr(section_config, attr):
                    return getattr(section_config, attr)
        return default
    
    def on_change(self, callback: Callable):
        """Register configuration change callback."""
        self._callbacks.append(callback)
    
    @property
    def config(self) -> AppConfig:
        """Get current configuration."""
        return self._config
    
    @property
    def trading(self) -> TradingConfig:
        return self._config.trading
    
    @property
    def risk(self) -> RiskConfig:
        return self._config.risk
    
    @property
    def broker(self) -> BrokerConfig:
        return self._config.broker
    
    @property
    def data(self) -> DataConfig:
        return self._config.data
    
    @property
    def ml(self) -> MLConfig:
        return self._config.ml
    
    @property
    def signal(self) -> SignalConfig:
        return self._config.signal
    
    @property
    def execution(self) -> ExecutionConfig:
        return self._config.execution
    
    @property
    def monitoring(self) -> MonitoringConfig:
        return self._config.monitoring
    
    @property
    def database(self) -> DatabaseConfig:
        return self._config.database
    
    @property
    def telegram(self) -> TelegramConfig:
        return self._config.telegram
    
    @property
    def api(self) -> APIConfig:
        return self._config.api
    
    @property
    def rate_limit(self) -> RateLimitConfig:
        return self._config.rate_limit
    
    @property
    def performance(self) -> PerformanceConfig:
        return self._config.performance
    
    def to_dict(self) -> Dict:
        """Convert configuration to dictionary."""
        return {
            'trading': asdict(self._config.trading),
            'risk': asdict(self._config.risk),
            'broker': {k: v for k, v in asdict(self._config.broker).items() if k not in ['password', 'api_secret']},
            'data': asdict(self._config.data),
            'ml': asdict(self._config.ml),
            'signal': asdict(self._config.signal),
            'execution': asdict(self._config.execution),
            'monitoring': asdict(self._config.monitoring),
            'database': {k: v for k, v in asdict(self._config.database).items() if k != 'password'},
            'telegram': {k: v for k, v in asdict(self._config.telegram).items() if k != 'bot_token'},
            'rate_limit': asdict(self._config.rate_limit),
            'performance': asdict(self._config.performance),
        }
    
    def save(self, file_path: Optional[str] = None):
        """Save configuration to file."""
        path = Path(file_path) if file_path else self._config_file
        if not path:
            try:
                path = Path("config.yaml")

                with open(path, 'w') as f:
                    yaml.dump(self.to_dict(), f, default_flow_style=False)
                logger.info(f"Configuration saved to: {path}")
            except Exception as e:
                logger.error(f"Failed to save configuration: {e}")


# ============================================================================
# GLOBAL ACCESS
# ============================================================================

def get_config() -> ConfigManager:
    """Get global configuration manager."""
    return ConfigManager()


def load_config(config_file: Optional[str] = None) -> AppConfig:
    """Load and return configuration."""
    return get_config().load(config_file)


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    'TradingConfig', 'RiskConfig', 'BrokerConfig', 'DataConfig',
    'MLConfig', 'SignalConfig', 'ExecutionConfig', 'MonitoringConfig',
    'DatabaseConfig', 'TelegramConfig', 'APIConfig', 'RateLimitConfig',
    'PerformanceConfig', 'AppConfig', 'ConfigManager', 'get_config', 'load_config',
]
