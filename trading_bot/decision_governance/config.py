"""
DGS Configuration System

Advanced configuration management with YAML/JSON support,
environment-specific configs, and validation.
"""

from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from pathlib import Path
import yaml
import json
import logging

logger = logging.getLogger(__name__)


@dataclass
class LayerConfig:
    """Configuration for a governance layer"""
    enabled: bool = True
    timeout_ms: float = 50.0
    strict_mode: bool = True
    custom_params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ValidationConfig:
    """Signal validation configuration"""
    max_signal_age_seconds: float = 300.0
    min_confidence: float = 0.0
    max_confidence: float = 1.0
    required_fields: List[str] = field(default_factory=lambda: ['direction', 'confidence', 'symbol'])
    enable_ml_anomaly_detection: bool = False
    anomaly_threshold: float = 0.95


@dataclass
class RiskConfig:
    """Risk management configuration"""
    max_position_size_pct: float = 0.10
    max_daily_loss_pct: float = 0.02
    max_portfolio_heat: int = 5
    max_correlation: float = 0.7
    max_drawdown_pct: float = 0.10
    max_sector_exposure_pct: float = 0.30
    max_volatility_exposure: float = 0.20
    max_margin_utilization: float = 0.50
    enable_portfolio_var: bool = True
    var_confidence: float = 0.95
    var_time_horizon_days: int = 1
    enable_stress_testing: bool = True
    stress_scenarios: List[str] = field(default_factory=lambda: [
        'market_crash_2008', 'covid_crash_2020', 'flash_crash_2010'
    ])


@dataclass
class ExecutionConfig:
    """Execution engine configuration"""
    max_acceptable_slippage_bps: float = 50.0
    max_acceptable_impact_bps: float = 30.0
    min_fill_probability: float = 0.8
    enable_smart_order_routing: bool = True
    routing_venues: List[str] = field(default_factory=lambda: ['primary', 'dark_pool', 'ats'])
    enable_twap: bool = True
    twap_slices: int = 5
    twap_duration_minutes: int = 30
    enable_vwap: bool = False


@dataclass
class AuditConfig:
    """Audit logging configuration"""
    log_path: str = "audit_log.jsonl"
    enable_hash_chain: bool = True
    retention_days: int = 365
    compress_after_days: int = 30
    export_format: str = "jsonl"
    enable_real_time_streaming: bool = False
    streaming_endpoint: Optional[str] = None


@dataclass
class SafetyConfig:
    """Safety enforcement configuration"""
    enforce_live_execution_protection: bool = True
    enforce_risk_control_protection: bool = True
    enforce_capital_limit_protection: bool = True
    enforce_governance_threshold_protection: bool = True
    enforce_contaminated_label_protection: bool = True
    enforce_sample_size_protection: bool = True
    min_promotion_sample_size: int = 30
    min_promotion_regimes: int = 2
    max_daily_violations_before_lockout: int = 5
    auto_lockout_duration_hours: int = 24


@dataclass
class MetaLearningConfig:
    """Meta-learning configuration"""
    enable_auto_optimization: bool = True
    analysis_window_days: int = 30
    min_samples_for_pattern_detection: int = 10
    enable_prompt_optimization: bool = True
    enable_workflow_optimization: bool = True
    enable_system_optimization: bool = False  # Requires manual approval
    optimization_frequency_hours: int = 24
    max_simultaneous_proposals: int = 3


@dataclass
class RealtimePlaneConfig:
    """Real-time plane configuration"""
    max_latency_ms: float = 100.0
    enable_parallel_processing: bool = True
    max_workers: int = 4
    cache_ttl_seconds: float = 60.0
    enable_circuit_breaker: bool = True
    circuit_breaker_threshold: int = 10
    circuit_breaker_timeout_seconds: float = 300.0


@dataclass
class OfflinePlaneConfig:
    """Offline plane configuration"""
    analysis_schedule: str = "0 2 * * *"  # Daily at 2 AM
    enable_counterfactual_deep_analysis: bool = True
    adversarial_depth: int = 5
    counterfactual_scenarios: int = 10
    enable_failure_clustering: bool = True
    min_cluster_size: int = 3
    enable_capability_gap_analysis: bool = True


@dataclass
class EvolutionPlaneConfig:
    """Evolution plane configuration"""
    enable_auto_validation: bool = True
    sandbox_duration_days: int = 30
    min_statistical_significance: float = 0.05
    min_improvement_threshold: float = 0.05
    min_robustness_score: float = 0.6
    max_drawdown_increase: float = 0.02
    min_calibration_quality: float = 0.6
    min_backtest_months: int = 6
    require_manual_approval_for_system_changes: bool = True
    enable_rollback_hooks: bool = True


@dataclass
class DGSConfig:
    """Complete DGS configuration"""
    
    # Environment
    environment: str = "development"  # development, staging, production
    
    # Component configs
    layers: Dict[str, LayerConfig] = field(default_factory=lambda: {
        f"layer_{i}": LayerConfig() for i in range(1, 8)
    })
    validation: ValidationConfig = field(default_factory=ValidationConfig)
    risk: RiskConfig = field(default_factory=RiskConfig)
    execution: ExecutionConfig = field(default_factory=ExecutionConfig)
    audit: AuditConfig = field(default_factory=AuditConfig)
    safety: SafetyConfig = field(default_factory=SafetyConfig)
    meta_learning: MetaLearningConfig = field(default_factory=MetaLearningConfig)
    
    # Plane configs
    realtime_plane: RealtimePlaneConfig = field(default_factory=RealtimePlaneConfig)
    offline_plane: OfflinePlaneConfig = field(default_factory=OfflinePlaneConfig)
    evolution_plane: EvolutionPlaneConfig = field(default_factory=EvolutionPlaneConfig)
    
    # Storage
    storage_path: str = "./dgs_data"
    database_url: Optional[str] = None
    
    # Monitoring
    enable_metrics: bool = True
    metrics_endpoint: Optional[str] = None
    enable_alerting: bool = False
    alert_webhook: Optional[str] = None
    
    # Feature flags
    features: Dict[str, bool] = field(default_factory=lambda: {
        'multi_hypothesis': True,
        'multi_agent_validation': True,
        'causal_attribution': True,
        'statistical_validation': True,
        'cost_expectancy': True,
        'diagnostic_introspection': True,
        'safety_enforcement': True,
        'meta_learning': True
    })
    
    @classmethod
    def from_yaml(cls, path: str) -> 'DGSConfig':
        """Load configuration from YAML file"""
        with open(path, 'r') as f:
            data = yaml.safe_load(f)
        return cls._from_dict(data)
    
    @classmethod
    def from_json(cls, path: str) -> 'DGSConfig':
        """Load configuration from JSON file"""
        with open(path, 'r') as f:
            data = json.load(f)
        return cls._from_dict(data)
    
    @classmethod
    def _from_dict(cls, data: Dict) -> 'DGSConfig':
        """Create config from dictionary"""
        # Convert nested dicts to dataclasses
        if 'layers' in data:
            data['layers'] = {
                k: LayerConfig(**v) if isinstance(v, dict) else v
                for k, v in data['layers'].items()
            }
        
        for key in ['validation', 'risk', 'execution', 'audit', 'safety', 
                    'meta_learning', 'realtime_plane', 'offline_plane', 'evolution_plane']:
            if key in data and isinstance(data[key], dict):
                dataclass_type = globals()[key.replace('_plane', '').replace('_', ' ').title().replace(' ', '') + 'Config']
                if key in ['realtime_plane', 'offline_plane', 'evolution_plane']:
                    dataclass_type = globals()[key.replace('_', ' ').title().replace(' ', '') + 'Config']
                data[key] = dataclass_type(**data[key])
        
        return cls(**data)
    
    def to_yaml(self, path: str) -> None:
        """Save configuration to YAML file"""
        with open(path, 'w') as f:
            yaml.dump(self.to_dict(), f, default_flow_style=False)
    
    def to_json(self, path: str) -> None:
        """Save configuration to JSON file"""
        with open(path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
    
    def to_dict(self) -> Dict:
        """Convert config to dictionary"""
        from dataclasses import asdict
        return asdict(self)
    
    def validate(self) -> List[str]:
        """Validate configuration and return list of errors"""
        errors = []
        
        # Validate risk limits
        if self.risk.max_position_size_pct > 0.5:
            errors.append("max_position_size_pct > 50% is dangerous")
        
        if self.risk.max_daily_loss_pct > 0.05:
            errors.append("max_daily_loss_pct > 5% is high risk")
        
        # Validate execution
        if self.execution.max_acceptable_slippage_bps > 100:
            errors.append("slippage tolerance > 100 bps is very loose")
        
        # Validate safety
        if not self.safety.enforce_risk_control_protection:
            errors.append("WARNING: Risk control protection disabled")
        
        if not self.safety.enforce_live_execution_protection:
            errors.append("WARNING: Live execution protection disabled")
        
        # Validate meta-learning
        if self.meta_learning.enable_system_optimization and not self.evolution_plane.require_manual_approval_for_system_changes:
            errors.append("CRITICAL: Auto system optimization without manual approval")
        
        return errors
    
    def get_environment_config(self, environment: str) -> 'DGSConfig':
        """Get configuration for specific environment"""
        # Create base config
        config = self
        
        # Apply environment-specific overrides
        if environment == "production":
            config.safety.enforce_live_execution_protection = True
            config.safety.enforce_risk_control_protection = True
            config.audit.enable_hash_chain = True
            config.audit.enable_real_time_streaming = True
            config.meta_learning.enable_system_optimization = False
            config.evolution_plane.require_manual_approval_for_system_changes = True
        elif environment == "staging":
            config.safety.enforce_live_execution_protection = True
            config.safety.enforce_risk_control_protection = True
            config.meta_learning.enable_system_optimization = False
        elif environment == "development":
            config.realtime_plane.max_latency_ms = 500.0  # More relaxed
            config.execution.enable_smart_order_routing = False
        
        return config


class ConfigurationManager:
    """Manages DGS configuration with hot-reloading support"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path
        self.current_config: Optional[DGSConfig] = None
        self.last_load_time: Optional[float] = None
        
        if config_path:
            self.load()
    
    def load(self) -> DGSConfig:
        """Load configuration from file"""
        if not self.config_path:
            self.current_config = DGSConfig()
            return self.current_config
        
        path = Path(self.config_path)
        
        if not path.exists():
            logger.warning(f"Config file {path} not found, using defaults")
            self.current_config = DGSConfig()
            return self.current_config
        
        # Load based on extension
        if path.suffix == '.yaml' or path.suffix == '.yml':
            self.current_config = DGSConfig.from_yaml(str(path))
        elif path.suffix == '.json':
            self.current_config = DGSConfig.from_json(str(path))
        else:
            raise ValueError(f"Unsupported config format: {path.suffix}")
        
        self.last_load_time = path.stat().st_mtime
        
        # Validate
        errors = self.current_config.validate()
        if errors:
            for error in errors:
                logger.warning(f"Config validation: {error}")
        
        logger.info(f"Loaded configuration from {path}")
        return self.current_config
    
    def reload_if_changed(self) -> bool:
        """Reload configuration if file has changed"""
        if not self.config_path:
            return False
        
        path = Path(self.config_path)
        if not path.exists():
            return False
        
        current_mtime = path.stat().st_mtime
        if current_mtime > (self.last_load_time or 0):
            self.load()
            return True
        
        return False
    
    def save(self, path: Optional[str] = None) -> None:
        """Save current configuration"""
        save_path = path or self.config_path
        if not save_path:
            raise ValueError("No path specified for saving")
        
        path_obj = Path(save_path)
        
        if path_obj.suffix == '.yaml' or path_obj.suffix == '.yml':
            self.current_config.to_yaml(save_path)
        elif path_obj.suffix == '.json':
            self.current_config.to_json(save_path)
        else:
            raise ValueError(f"Unsupported config format: {path_obj.suffix}")
        
        logger.info(f"Saved configuration to {save_path}")
    
    def get(self) -> DGSConfig:
        """Get current configuration"""
        if self.current_config is None:
            self.load()
        return self.current_config
