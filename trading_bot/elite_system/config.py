"""
Elite System Configuration Module

This module provides configuration management for the Elite Trading System,
allowing users to customize the behavior of all components through YAML files.
"""

import os
try:
    import yaml
except ImportError:
    yaml = None
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from enum import Enum
from dataclasses import dataclass, field, asdict

# Import enums from other modules for configuration
from .risk_command_center import PositionSizeMethod, RiskLevel
from .ai_ml_cortex import ModelType, PredictionHorizon

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ConfigSection(Enum):
    """Configuration Section Types"""
    GENERAL = "general"
    PRICE_ACTION = "price_action"
    MARKET_STRUCTURE = "market_structure"
    LIQUIDITY_WARFARE = "liquidity_warfare"
    ORDER_FLOW = "order_flow"
    INSTITUTIONAL = "institutional"
    AI_ML = "ai_ml"
    RISK = "risk"
    CONSCIOUSNESS = "consciousness"
    QUANTUM = "quantum"
    BLOCKCHAIN = "blockchain"
    VISUALIZATION = "visualization"

@dataclass
class GeneralConfig:
    """General configuration settings"""
    debug_mode: bool = False
    log_level: str = "INFO"
    data_directory: str = "data"
    signals_directory: str = "signals"
    max_signal_history: int = 100
    max_trade_history: int = 100
    timezone: str = "UTC"
    
    # Module activation flags
    use_price_action: bool = True
    use_market_structure: bool = True
    use_liquidity_warfare: bool = True
    use_order_flow: bool = True
    use_institutional_strategy: bool = True
    use_ai_ml_cortex: bool = True
    use_risk_command: bool = True
    use_trader_consciousness: bool = True
    use_quantum_blockchain: bool = False
    
    # Module weights for signal generation
    price_action_weight: float = 0.2
    market_structure_weight: float = 0.2
    liquidity_warfare_weight: float = 0.15
    order_flow_weight: float = 0.15
    institutional_strategy_weight: float = 0.15
    ai_ml_cortex_weight: float = 0.15

@dataclass
class PriceActionConfig:
    """Price Action Intelligence configuration"""
    quantum_analysis_enabled: bool = True
    naked_trading_enabled: bool = True
    mtf_synergy_enabled: bool = True
    markov_chain_order: int = 2
    candlestick_lookback: int = 20
    mtf_timeframes: List[str] = field(default_factory=lambda: ["1m", "5m", "15m", "1h", "4h", "1d"])
    mtf_weights: Dict[str, float] = field(default_factory=lambda: {
        "1m": 0.05, "5m": 0.1, "15m": 0.15, "1h": 0.3, "4h": 0.2, "1d": 0.2
    })
    fractal_detection_period: int = 5

@dataclass
class MarketStructureConfig:
    """Market Structure Oracle configuration"""
    bos_detection_enabled: bool = True
    choch_detection_enabled: bool = True
    smc_analysis_enabled: bool = True
    ict_silver_bullet_enabled: bool = True
    market_phase_detection_enabled: bool = True
    wavelet_transform_enabled: bool = True
    structure_lookback: int = 100
    swing_point_threshold: float = 0.001
    session_timezones: Dict[str, str] = field(default_factory=lambda: {
        "london": "Europe/London", "new_york": "America/New_York", "tokyo": "Asia/Tokyo"
    })

@dataclass
class LiquidityWarfareConfig:
    """Liquidity Warfare System configuration"""
    equal_highs_lows_detection: bool = True
    sweep_detection_enabled: bool = True
    spoofing_detection_enabled: bool = True
    trap_detection_enabled: bool = True
    time_decay_factor: float = 0.95
    liquidity_threshold: float = 0.0005
    sweep_lookback: int = 50
    liquidity_cluster_threshold: float = 0.0002

@dataclass
class OrderFlowConfig:
    """Order Flow Decryptor configuration"""
    footprint_analysis_enabled: bool = True
    participant_classification_enabled: bool = True
    iceberg_detection_enabled: bool = True
    economic_event_integration: bool = True
    delta_threshold: float = 0.6
    volume_cluster_threshold: float = 0.7
    institutional_threshold: float = 0.8
    tick_data_enabled: bool = False  # Requires tick data source

@dataclass
class InstitutionalConfig:
    """Institutional Strategy Emulator configuration"""
    wyckoff_detection_enabled: bool = True
    fvg_detection_enabled: bool = True
    market_maker_model_enabled: bool = True
    ict_power_of_3_enabled: bool = True
    wyckoff_lookback: int = 200
    fvg_validity_period: int = 50
    premium_discount_threshold: float = 0.002
    equilibrium_lookback: int = 20

@dataclass
class AIMLConfig:
    """AI/ML Cortex configuration"""
    lstm_enabled: bool = True
    economic_fusion_enabled: bool = True
    ensemble_learning_enabled: bool = True
    adaptive_model_selection: bool = True
    default_model: ModelType = ModelType.ENSEMBLE
    default_horizon: PredictionHorizon = PredictionHorizon.SHORT
    sequence_length: int = 60
    feature_count: int = 50
    training_epochs: int = 100
    batch_size: int = 32
    learning_rate: float = 0.001
    validation_split: float = 0.2
    early_stopping_patience: int = 10

@dataclass
class RiskConfig:
    """Risk Command Center configuration"""
    max_risk_per_trade: float = 0.02  # 2% max risk per trade
    max_portfolio_risk: float = 0.06  # 6% max portfolio risk
    max_correlation: float = 0.7      # Max correlation between positions
    max_sector_exposure: float = 0.3  # Max exposure per sector
    stop_loss_multiplier: float = 2.0 # ATR multiplier for stop loss
    take_profit_ratio: float = 2.0    # Risk:Reward ratio
    max_positions: int = 10           # Maximum concurrent positions
    volatility_lookback: int = 20     # Days for volatility calculation
    confidence_level: float = 0.95    # VaR confidence level
    default_position_sizing: PositionSizeMethod = PositionSizeMethod.KELLY
    kelly_fraction_limit: float = 0.25  # Maximum Kelly fraction
    black_swan_protection: bool = True

@dataclass
class ConsciousnessConfig:
    """Trader Consciousness Module configuration"""
    self_learning_enabled: bool = True
    emotional_tracking_enabled: bool = True
    bias_detection_enabled: bool = True
    adaptation_rate: float = 0.1
    journal_max_entries: int = 1000
    discipline_threshold: float = 0.7
    confidence_calibration_enabled: bool = True
    learning_mode: str = "balanced"  # exploration, exploitation, balanced

@dataclass
class QuantumConfig:
    """Quantum Computing configuration"""
    enabled: bool = False
    simulator_mode: bool = True  # Use simulator if no quantum hardware
    shots: int = 1000
    optimization_method: str = "QAOA"  # QAOA, VQE, Annealing
    portfolio_constraints: Dict[str, float] = field(default_factory=lambda: {
        "max_weight": 0.3, "min_weight": 0.0
    })
    risk_tolerance: float = 0.5

@dataclass
class BlockchainConfig:
    """Blockchain Validation configuration"""
    enabled: bool = False
    storage_path: str = "blockchain_data"
    difficulty: int = 4
    validation_interval: int = 10  # Blocks
    consensus_threshold: float = 0.7
    cryptographic_algorithm: str = "SHA256"

@dataclass
class VisualizationConfig:
    """Visualization configuration"""
    enabled: bool = True
    default_theme: str = "dark"
    chart_type: str = "candlestick"
    overlay_indicators: List[str] = field(default_factory=lambda: ["EMA", "VWAP"])
    show_liquidity_zones: bool = True
    show_order_blocks: bool = True
    show_fair_value_gaps: bool = True
    show_wyckoff_phases: bool = True
    show_signals: bool = True
    auto_save_charts: bool = False
    charts_directory: str = "charts"

@dataclass
class EliteConfig:
    """Complete Elite System configuration"""
    general: GeneralConfig = field(default_factory=GeneralConfig)
    price_action: PriceActionConfig = field(default_factory=PriceActionConfig)
    market_structure: MarketStructureConfig = field(default_factory=MarketStructureConfig)
    liquidity_warfare: LiquidityWarfareConfig = field(default_factory=LiquidityWarfareConfig)
    order_flow: OrderFlowConfig = field(default_factory=OrderFlowConfig)
    institutional: InstitutionalConfig = field(default_factory=InstitutionalConfig)
    ai_ml: AIMLConfig = field(default_factory=AIMLConfig)
    risk: RiskConfig = field(default_factory=RiskConfig)
    consciousness: ConsciousnessConfig = field(default_factory=ConsciousnessConfig)
    quantum: QuantumConfig = field(default_factory=QuantumConfig)
    blockchain: BlockchainConfig = field(default_factory=BlockchainConfig)
    visualization: VisualizationConfig = field(default_factory=VisualizationConfig)
    
    @classmethod
    def load(cls, config_path: str) -> 'EliteConfig':
        """Load configuration from YAML file"""
        try:
            if not os.path.exists(config_path):
                logger.warning(f"Config file {config_path} not found. Using default configuration.")
                return cls()
            
            with open(config_path, 'r') as file:
                config_dict = yaml.safe_load(file)
            
            # Create default config
            config = cls()
            
            # Update with values from file
            if config_dict:
                # Process each section
                for section_name, section_data in config_dict.items():
                    if hasattr(config, section_name) and section_data:
                        section_instance = getattr(config, section_name)
                        
                        # Handle enum values
                        for key, value in section_data.items():
                            if hasattr(section_instance, key):
                                attr_value = getattr(section_instance, key)
                                
                                # Convert string to enum if needed
                                if isinstance(attr_value, Enum) and isinstance(value, str):
                                    enum_class = attr_value.__class__
                                    try:
                                        enum_value = enum_class(value)
                                        section_data[key] = enum_value
                                    except ValueError:
                                        logger.warning(f"Invalid enum value {value} for {key}")
                        
                        # Update section with processed values
                        for key, value in section_data.items():
                            if hasattr(section_instance, key):
                                setattr(section_instance, key, value)
            
            return config
            
        except Exception as e:
            logger.error(f"Error loading configuration from {config_path}: {e}")
            return cls()
    
    def save(self, config_path: str) -> bool:
        """Save configuration to YAML file"""
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(os.path.abspath(config_path)), exist_ok=True)
            
            # Convert config to dict
            config_dict = {}
            
            for section_name, section in self.__dict__.items():
                section_dict = {}
                
                for key, value in section.__dict__.items():
                    # Convert enum to string
                    if isinstance(value, Enum):
                        section_dict[key] = value.value
                    else:
                        section_dict[key] = value
                
                config_dict[section_name] = section_dict
            
            # Save to YAML
            with open(config_path, 'w') as file:
                yaml.dump(config_dict, file, default_flow_style=False)
            
            logger.info(f"Configuration saved to {config_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving configuration to {config_path}: {e}")
            return False
    
    def get_section(self, section: ConfigSection) -> Any:
        """Get a specific configuration section"""
        section_map = {
            ConfigSection.GENERAL: self.general,
            ConfigSection.PRICE_ACTION: self.price_action,
            ConfigSection.MARKET_STRUCTURE: self.market_structure,
            ConfigSection.LIQUIDITY_WARFARE: self.liquidity_warfare,
            ConfigSection.ORDER_FLOW: self.order_flow,
            ConfigSection.INSTITUTIONAL: self.institutional,
            ConfigSection.AI_ML: self.ai_ml,
            ConfigSection.RISK: self.risk,
            ConfigSection.CONSCIOUSNESS: self.consciousness,
            ConfigSection.QUANTUM: self.quantum,
            ConfigSection.BLOCKCHAIN: self.blockchain,
            ConfigSection.VISUALIZATION: self.visualization
        }
        
        return section_map.get(section)
    
    def update_section(self, section: ConfigSection, updates: Dict[str, Any]) -> bool:
        """Update a specific configuration section"""
        section_instance = self.get_section(section)
        
        if not section_instance:
            return False
        try:
        
            for key, value in updates.items():
                if hasattr(section_instance, key):
                    # Handle enum conversion
                    attr_value = getattr(section_instance, key)
                    if isinstance(attr_value, Enum) and isinstance(value, str):
                        enum_class = attr_value.__class__
                        try:
                            value = enum_class(value)
                        except ValueError:
                            logger.warning(f"Invalid enum value {value} for {key}")
                            continue
                    
                    setattr(section_instance, key, value)
                else:
                    logger.warning(f"Unknown configuration key: {key}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error updating configuration section {section.value}: {e}")
            return False

def create_default_config(config_path: str) -> bool:
    """Create a default configuration file"""
    try:
        # Create default config
        config = EliteConfig()
        
        # Save to file
        return config.save(config_path)
        
    except Exception as e:
        logger.error(f"Error creating default configuration: {e}")
        return False

# Example usage
if __name__ == "__main__":
    # Create default configuration
    default_config_path = "elite_config.yaml"
    create_default_config(default_config_path)
    
    # Load configuration
    config = EliteConfig.load(default_config_path)
    
    # Modify configuration
    config.general.debug_mode = True
    config.risk.max_risk_per_trade = 0.01
    
    # Save modified configuration
    config.save("modified_config.yaml")
    
    logger.info("Configuration system test completed successfully!")
