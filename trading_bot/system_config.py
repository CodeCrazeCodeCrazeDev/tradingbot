"""
System Configuration - Centralized configuration management
Manages all system-wide configuration with environment-specific overrides
"""
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from enum import Enum
import os
from pathlib import Path


import logging

logger = logging.getLogger(__name__)

class TradingMode(Enum):
    """Trading mode"""
    SIMULATION = "simulation"
    PAPER = "paper"
    LIVE = "live"


class Environment(Enum):
    """Deployment environment"""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


@dataclass
class RiskLimits:
    """Risk management limits"""
    max_position_size_pct: float = 10.0  # Max 10% per position
    max_portfolio_risk_pct: float = 2.0  # Max 2% portfolio risk
    max_daily_loss_pct: float = 5.0  # Max 5% daily loss
    max_drawdown_pct: float = 20.0  # Max 20% drawdown
    max_leverage: float = 3.0  # Max 3x leverage
    max_correlation: float = 0.7  # Max correlation between positions
    max_sector_exposure_pct: float = 25.0  # Max 25% per sector
    position_size_method: str = "kelly"  # kelly, fixed, volatility


@dataclass
class ExecutionConfig:
    """Execution configuration"""
    default_slippage_bps: float = 5.0  # 5 basis points
    max_slippage_bps: float = 20.0  # 20 basis points
    order_timeout_seconds: int = 30
    retry_attempts: int = 3
    retry_delay_seconds: int = 2
    use_smart_routing: bool = True
    enable_dark_pools: bool = False
    enable_iceberg_orders: bool = True


@dataclass
class DataConfig:
    """Data configuration"""
    primary_data_source: str = "yahoo"
    backup_data_sources: List[str] = field(default_factory=lambda: ["coingecko", "fred"])
    data_staleness_threshold_seconds: int = 60
    enable_data_validation: bool = True
    enable_data_quarantine: bool = True
    cache_enabled: bool = True
    cache_ttl_seconds: int = 300


@dataclass
class MLConfig:
    """Machine learning configuration"""
    enable_ml: bool = True
    enable_ensemble: bool = True
    enable_meta_learning: bool = True
    enable_online_learning: bool = True
    model_update_frequency_hours: int = 24
    min_training_samples: int = 1000
    feature_importance_threshold: float = 0.01
    confidence_threshold: float = 0.7


@dataclass
class MonitoringConfig:
    """Monitoring configuration"""
    enable_metrics: bool = True
    enable_logging: bool = True
    enable_alerts: bool = True
    log_level: str = "INFO"
    metrics_retention_days: int = 90
    alert_cooldown_minutes: int = 15


@dataclass
class GovernanceConfig:
    """Governance configuration"""
    require_human_approval: bool = True
    enable_audit_logging: bool = True
    enable_compliance_checks: bool = True
    max_auto_trade_size: float = 1000.0
    require_approval_above: float = 10000.0


@dataclass
class LayerConfig:
    """Configuration for each architecture layer"""
    enabled: bool = True
    priority: int = 5
    timeout_seconds: int = 30
    retry_enabled: bool = True
    fallback_enabled: bool = True


@dataclass
class SystemConfig:
    """Master system configuration"""
    
    # Environment
    environment: Environment = Environment.DEVELOPMENT
    trading_mode: TradingMode = TradingMode.SIMULATION
    
    # Core settings
    symbols: List[str] = field(default_factory=lambda: ["BTCUSDT", "ETHUSD"])
    base_currency: str = "USD"
    initial_capital: float = 100000.0
    
    # Risk limits
    risk: RiskLimits = field(default_factory=RiskLimits)
    
    # Execution
    execution: ExecutionConfig = field(default_factory=ExecutionConfig)
    
    # Data
    data: DataConfig = field(default_factory=DataConfig)
    
    # ML/AI
    ml: MLConfig = field(default_factory=MLConfig)
    
    # Monitoring
    monitoring: MonitoringConfig = field(default_factory=MonitoringConfig)
    
    # Governance
    governance: GovernanceConfig = field(default_factory=GovernanceConfig)
    
    # Layer configurations
    layers: Dict[str, LayerConfig] = field(default_factory=lambda: {
        'infrastructure': LayerConfig(enabled=True, priority=10),
        'data_foundation': LayerConfig(enabled=True, priority=9),
        'intelligence_core': LayerConfig(enabled=True, priority=8),
        'signal_generation': LayerConfig(enabled=True, priority=7),
        'risk_safety': LayerConfig(enabled=True, priority=10),  # Highest priority
        'execution': LayerConfig(enabled=True, priority=6),
        'governance': LayerConfig(enabled=True, priority=9),
        'orchestration': LayerConfig(enabled=True, priority=5),
    })
    
    # Feature flags
    features: Dict[str, bool] = field(default_factory=lambda: {
        'enable_alpha_engine': True,
        'enable_msos': True,
        'enable_cognitive_architecture': True,
        'enable_event_pipeline': True,
        'enable_hedge_fund_features': False,
        'enable_quantum_computing': False,
        'enable_blockchain': False,
        'enable_sentiment_analysis': True,
        'enable_alternative_data': True,
        'enable_self_evolution': True,
        'enable_qwen_codemender': False,
        'enable_market_student': True,
        'enable_elite_ai': True,
    })
    
    # Component registry
    enabled_components: Dict[str, List[str]] = field(default_factory=lambda: {
        'data_providers': ['yahoo_finance', 'coingecko', 'fred'],
        'signal_generators': ['alpha_engine', 'cognitive_core', 'elite_ai'],
        'risk_managers': ['msos', 'hedge_fund_safety', 'master_risk'],
        'execution_engines': ['smart_router', 'atomic_executor'],
        'intelligence_engines': ['meta_learning', 'ensemble', 'online_learning'],
        'governance_systems': ['alphaalgo_governance', 'compliance'],
        'monitoring_systems': ['metrics', 'alerts', 'health_checks'],
    })
    
    # Paths
    workspace_path: Path = field(default_factory=lambda: Path(r'c:\Users\peterson\trading bot'))
    data_path: Path = field(default_factory=lambda: Path(r'c:\Users\peterson\trading bot\data'))
    logs_path: Path = field(default_factory=lambda: Path(r'c:\Users\peterson\trading bot\logs'))
    models_path: Path = field(default_factory=lambda: Path(r'c:\Users\peterson\trading bot\models'))
    
    def get_layer_config(self, layer_name: str) -> LayerConfig:
        """Get configuration for a specific layer"""
        return self.layers.get(layer_name, LayerConfig())
    
    def is_feature_enabled(self, feature_name: str) -> bool:
        """Check if a feature is enabled"""
        return self.features.get(feature_name, False)
    
    def get_enabled_components(self, component_type: str) -> List[str]:
        """Get list of enabled components for a type"""
        return self.enabled_components.get(component_type, [])
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'environment': self.environment.value,
            'trading_mode': self.trading_mode.value,
            'symbols': self.symbols,
            'base_currency': self.base_currency,
            'initial_capital': self.initial_capital,
            'risk': {
                'max_position_size_pct': self.risk.max_position_size_pct,
                'max_portfolio_risk_pct': self.risk.max_portfolio_risk_pct,
                'max_daily_loss_pct': self.risk.max_daily_loss_pct,
                'max_drawdown_pct': self.risk.max_drawdown_pct,
                'max_leverage': self.risk.max_leverage,
            },
            'features': self.features,
            'enabled_components': self.enabled_components,
        }
    
    @classmethod
    def from_env(cls) -> 'SystemConfig':
        """Create configuration from environment variables"""
        try:
            config = cls()
        
            # Override from environment
            if env_mode := os.getenv('TRADING_MODE'):
                config.trading_mode = TradingMode(env_mode.lower())
        
            if env_env := os.getenv('ENVIRONMENT'):
                config.environment = Environment(env_env.lower())
        
            if symbols := os.getenv('SYMBOLS'):
                config.symbols = symbols.split(',')
        
            if capital := os.getenv('INITIAL_CAPITAL'):
                config.initial_capital = float(capital)
        
            return config
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in from_env: {e}")
            raise
    
    @classmethod
    def for_production(cls) -> 'SystemConfig':
        """Create production configuration"""
        try:
            config = cls()
            config.environment = Environment.PRODUCTION
            config.trading_mode = TradingMode.LIVE
            config.governance.require_human_approval = True
            config.risk.max_position_size_pct = 5.0  # More conservative
            config.risk.max_daily_loss_pct = 2.0  # More conservative
            config.monitoring.log_level = "WARNING"
            return config
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in for_production: {e}")
            raise
    
    @classmethod
    def for_paper_trading(cls) -> 'SystemConfig':
        """Create paper trading configuration"""
        try:
            config = cls()
            config.environment = Environment.STAGING
            config.trading_mode = TradingMode.PAPER
            config.governance.require_human_approval = False
            return config
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in for_paper_trading: {e}")
            raise
    
    @classmethod
    def for_simulation(cls) -> 'SystemConfig':
        """Create simulation configuration"""
        try:
            config = cls()
            config.environment = Environment.DEVELOPMENT
            config.trading_mode = TradingMode.SIMULATION
            config.governance.require_human_approval = False
            config.execution.use_smart_routing = False
            return config
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in for_simulation: {e}")
            raise


# Singleton instance
_config_instance: Optional[SystemConfig] = None


def get_config() -> SystemConfig:
    """Get global configuration instance"""
    try:
        global _config_instance
        if _config_instance is None:
            _config_instance = SystemConfig.from_env()
        return _config_instance
    except Exception as e:
        import logging as _log
        _log.getLogger(__name__).error(f"Error in get_config: {e}")
        raise


def set_config(config: SystemConfig):
    """Set global configuration instance"""
    try:
        global _config_instance
        _config_instance = config
    except Exception as e:
        import logging as _log
        _log.getLogger(__name__).error(f"Error in set_config: {e}")
        raise


def reset_config():
    """Reset configuration to default"""
    try:
        global _config_instance
        _config_instance = None
    except Exception as e:
        import logging as _log
        _log.getLogger(__name__).error(f"Error in reset_config: {e}")
        raise


__all__ = [
    'TradingMode',
    'Environment',
    'RiskLimits',
    'ExecutionConfig',
    'DataConfig',
    'MLConfig',
    'MonitoringConfig',
    'GovernanceConfig',
    'LayerConfig',
    'SystemConfig',
    'get_config',
    'set_config',
    'reset_config',
]
