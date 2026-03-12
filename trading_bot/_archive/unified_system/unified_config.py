"""
Unified Configuration - Centralized configuration management

Provides a single source of truth for all system configuration.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from enum import Enum
import os
import json
import yaml
import logging

from .unified_types import TradingMode, OperationMode, MarketRegime

logger = logging.getLogger(__name__)


@dataclass
class LayerConfig:
    """Configuration for a single layer"""
    enabled: bool = True
    priority: int = 0
    timeout_seconds: float = 30.0
    retry_count: int = 3
    custom: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RiskConfig:
    """Risk management configuration"""
    # Position limits
    max_position_size: float = 0.10          # 10% of capital
    max_total_exposure: float = 0.50         # 50% of capital
    max_correlation_exposure: float = 0.30   # 30% correlated exposure
    
    # Loss limits
    max_risk_per_trade: float = 0.02         # 2% per trade
    max_daily_loss: float = 0.05             # 5% daily loss limit
    max_weekly_loss: float = 0.10            # 10% weekly loss limit
    max_drawdown: float = 0.20               # 20% max drawdown
    
    # Leverage
    max_leverage: float = 5.0                # 5x max leverage
    
    # Circuit breakers
    circuit_breaker_threshold: float = 0.03  # 3% triggers circuit breaker
    circuit_breaker_cooldown: int = 3600     # 1 hour cooldown
    
    # Kill switch
    kill_switch_drawdown: float = 0.25       # 25% triggers kill switch


@dataclass
class ExecutionConfig:
    """Execution configuration"""
    # Order types
    default_order_type: str = "limit"
    default_algorithm: str = "adaptive"
    
    # Slippage
    max_slippage: float = 0.001              # 0.1% max slippage
    slippage_protection: bool = True
    
    # Timing
    order_timeout_seconds: float = 30.0
    fill_timeout_seconds: float = 60.0
    
    # Retry
    max_retries: int = 3
    retry_delay_seconds: float = 1.0
    
    # Venues
    preferred_venues: List[str] = field(default_factory=list)
    dark_pool_enabled: bool = False


@dataclass
class IntelligenceConfig:
    """Intelligence/ML configuration"""
    # Models
    ensemble_enabled: bool = True
    num_experts: int = 10
    top_k_experts: int = 3
    
    # Regime detection
    regime_detection_enabled: bool = True
    regime_lookback: int = 100
    
    # Online learning
    online_learning_enabled: bool = True
    learning_rate: float = 0.001
    
    # Meta-learning
    meta_learning_enabled: bool = True
    adaptation_steps: int = 5


@dataclass
class SignalConfig:
    """Signal generation configuration"""
    # Thresholds
    min_confidence: float = 0.6
    min_strength: float = 0.5
    
    # Verification
    verification_enabled: bool = True
    min_verification_score: float = 0.7
    
    # Blending
    signal_blending: str = "weighted"        # weighted, voting, stacking
    
    # TTL
    signal_ttl_seconds: int = 300            # 5 minutes


@dataclass
class GovernanceConfig:
    """Governance configuration"""
    # Mode
    operation_mode: OperationMode = OperationMode.SEMI_AUTONOMOUS
    
    # Approval
    require_human_approval: bool = False
    approval_timeout_seconds: int = 300
    auto_approve_threshold: float = 0.9
    
    # Audit
    audit_enabled: bool = True
    audit_retention_days: int = 365
    
    # Kill switch
    kill_switch_enabled: bool = True


@dataclass
class UnifiedConfig:
    """
    Master configuration for the unified trading system
    
    Consolidates all configuration into a single structure.
    """
    
    # System identification
    system_name: str = "AlphaAlgo"
    system_version: str = "3.0.0"
    environment: str = "development"         # development, staging, production
    
    # Trading mode
    trading_mode: TradingMode = TradingMode.PAPER
    
    # Symbols
    symbols: List[str] = field(default_factory=lambda: ["BTCUSDT"])
    timeframes: List[str] = field(default_factory=lambda: ["1m", "5m", "15m", "1h"])
    
    # Capital
    initial_capital: float = 10000.0
    currency: str = "USD"
    
    # Layer configurations
    layer_configs: Dict[int, LayerConfig] = field(default_factory=dict)
    
    # Subsystem configurations
    risk: RiskConfig = field(default_factory=RiskConfig)
    execution: ExecutionConfig = field(default_factory=ExecutionConfig)
    intelligence: IntelligenceConfig = field(default_factory=IntelligenceConfig)
    signal: SignalConfig = field(default_factory=SignalConfig)
    governance: GovernanceConfig = field(default_factory=GovernanceConfig)
    
    # Broker configuration
    broker: str = "simulation"               # simulation, alpaca, binance, mt5
    broker_config: Dict[str, Any] = field(default_factory=dict)
    
    # Data configuration
    data_sources: List[str] = field(default_factory=lambda: ["yahoo", "binance"])
    historical_days: int = 365
    
    # Logging
    log_level: str = "INFO"
    log_to_file: bool = True
    log_dir: str = "logs"
    
    # Performance
    max_workers: int = 4
    use_gpu: bool = False
    memory_limit_mb: int = 4096
    
    # Feature flags
    features: Dict[str, bool] = field(default_factory=dict)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UnifiedConfig':
        """Create config from dictionary"""
        config = cls()
        
        # Simple fields
        for key in ['system_name', 'system_version', 'environment', 'broker',
                    'initial_capital', 'currency', 'log_level', 'log_to_file',
                    'log_dir', 'max_workers', 'use_gpu', 'memory_limit_mb',
                    'historical_days']:
            if key in data:
                setattr(config, key, data[key])
        
        # Trading mode
        if 'trading_mode' in data:
            config.trading_mode = TradingMode(data['trading_mode'])
        
        # Lists
        if 'symbols' in data:
            config.symbols = data['symbols']
        if 'timeframes' in data:
            config.timeframes = data['timeframes']
        if 'data_sources' in data:
            config.data_sources = data['data_sources']
        
        # Nested configs
        if 'risk' in data:
            config.risk = RiskConfig(**data['risk'])
        if 'execution' in data:
            config.execution = ExecutionConfig(**data['execution'])
        if 'intelligence' in data:
            config.intelligence = IntelligenceConfig(**data['intelligence'])
        if 'signal' in data:
            config.signal = SignalConfig(**data['signal'])
        if 'governance' in data:
            config.governance = GovernanceConfig(**data['governance'])
        
        # Broker config
        if 'broker_config' in data:
            config.broker_config = data['broker_config']
        
        # Features
        if 'features' in data:
            config.features = data['features']
        
        return config
    
    @classmethod
    def from_yaml(cls, path: str) -> 'UnifiedConfig':
        """Load config from YAML file"""
        with open(path, 'r') as f:
            data = yaml.safe_load(f)
        return cls.from_dict(data)
    
    @classmethod
    def from_json(cls, path: str) -> 'UnifiedConfig':
        """Load config from JSON file"""
        with open(path, 'r') as f:
            data = json.load(f)
        return cls.from_dict(data)
    
    @classmethod
    def from_env(cls) -> 'UnifiedConfig':
        """Load config from environment variables"""
        config = cls()
        
        # Trading mode
        mode = os.getenv('TRADING_MODE', 'paper')
        config.trading_mode = TradingMode(mode)
        
        # Symbols
        symbols = os.getenv('TRADING_SYMBOLS', 'BTCUSDT')
        config.symbols = [s.strip() for s in symbols.split(',')]
        
        # Capital
        config.initial_capital = float(os.getenv('INITIAL_CAPITAL', '10000'))
        
        # Broker
        config.broker = os.getenv('BROKER', 'simulation')
        
        # Risk
        config.risk.max_risk_per_trade = float(os.getenv('MAX_RISK_PER_TRADE', '0.02'))
        config.risk.max_daily_loss = float(os.getenv('MAX_DAILY_LOSS', '0.05'))
        config.risk.max_drawdown = float(os.getenv('MAX_DRAWDOWN', '0.20'))
        
        # Log level
        config.log_level = os.getenv('LOG_LEVEL', 'INFO')
        
        return config
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary"""
        return {
            'system_name': self.system_name,
            'system_version': self.system_version,
            'environment': self.environment,
            'trading_mode': self.trading_mode.value,
            'symbols': self.symbols,
            'timeframes': self.timeframes,
            'initial_capital': self.initial_capital,
            'currency': self.currency,
            'broker': self.broker,
            'broker_config': self.broker_config,
            'data_sources': self.data_sources,
            'historical_days': self.historical_days,
            'log_level': self.log_level,
            'log_to_file': self.log_to_file,
            'log_dir': self.log_dir,
            'max_workers': self.max_workers,
            'use_gpu': self.use_gpu,
            'memory_limit_mb': self.memory_limit_mb,
            'features': self.features,
            'risk': {
                'max_position_size': self.risk.max_position_size,
                'max_total_exposure': self.risk.max_total_exposure,
                'max_risk_per_trade': self.risk.max_risk_per_trade,
                'max_daily_loss': self.risk.max_daily_loss,
                'max_weekly_loss': self.risk.max_weekly_loss,
                'max_drawdown': self.risk.max_drawdown,
                'max_leverage': self.risk.max_leverage,
            },
            'execution': {
                'default_order_type': self.execution.default_order_type,
                'default_algorithm': self.execution.default_algorithm,
                'max_slippage': self.execution.max_slippage,
            },
            'signal': {
                'min_confidence': self.signal.min_confidence,
                'min_strength': self.signal.min_strength,
                'verification_enabled': self.signal.verification_enabled,
            },
            'governance': {
                'operation_mode': self.governance.operation_mode.value,
                'require_human_approval': self.governance.require_human_approval,
            },
        }
    
    def save_yaml(self, path: str) -> None:
        """Save config to YAML file"""
        with open(path, 'w') as f:
            yaml.dump(self.to_dict(), f, default_flow_style=False)
    
    def save_json(self, path: str) -> None:
        """Save config to JSON file"""
        with open(path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
    
    def validate(self) -> tuple[bool, List[str]]:
        """Validate configuration"""
        errors = []
        
        # Risk validation
        if self.risk.max_risk_per_trade > 0.05:
            errors.append("max_risk_per_trade should not exceed 5%")
        if self.risk.max_daily_loss > 0.10:
            errors.append("max_daily_loss should not exceed 10%")
        if self.risk.max_drawdown > 0.30:
            errors.append("max_drawdown should not exceed 30%")
        if self.risk.max_leverage > 10:
            errors.append("max_leverage should not exceed 10x")
        
        # Signal validation
        if self.signal.min_confidence < 0.5:
            errors.append("min_confidence should be at least 0.5")
        
        # Capital validation
        if self.initial_capital <= 0:
            errors.append("initial_capital must be positive")
        
        # Symbols validation
        if not self.symbols:
            errors.append("At least one symbol must be specified")
        
        return len(errors) == 0, errors


# Singleton config instance
_config: Optional[UnifiedConfig] = None


def get_config() -> UnifiedConfig:
    """Get or create the config singleton"""
    global _config
    if _config is None:
        _config = UnifiedConfig()
    return _config


def set_config(config: UnifiedConfig) -> None:
    """Set the config singleton"""
    global _config
    _config = config


def load_config(path: Optional[str] = None) -> UnifiedConfig:
    """
    Load configuration from file or environment
    
    Args:
        path: Optional path to config file (YAML or JSON)
        
    Returns:
        Loaded configuration
    """
    global _config
    
    if path:
        if path.endswith('.yaml') or path.endswith('.yml'):
            _config = UnifiedConfig.from_yaml(path)
        elif path.endswith('.json'):
            _config = UnifiedConfig.from_json(path)
        else:
            raise ValueError(f"Unsupported config format: {path}")
    else:
        # Try to load from default locations
        default_paths = [
            'config/unified_config.yaml',
            'config/unified_config.json',
            'unified_config.yaml',
            'unified_config.json',
        ]
        
        for default_path in default_paths:
            if os.path.exists(default_path):
                return load_config(default_path)
        
        # Fall back to environment variables
        _config = UnifiedConfig.from_env()
    
    return _config
