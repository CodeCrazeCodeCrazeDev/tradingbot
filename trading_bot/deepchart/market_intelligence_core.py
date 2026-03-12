"""
DeepChart Market Intelligence Core - Data Structures and Enums

Core data structures for the unified market intelligence system.
All 15 mandatory concepts represented as typed dataclasses.

NON-NEGOTIABLE CONSTRAINTS:
- NO expensive L3 data
- NO GPU server infrastructure  
- CPU-first ML, ONNX-exportable
- <5ms inference latency per symbol
"""

import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum, auto


# =============================================================================
# ENUMS
# =============================================================================

class MarketRegime(Enum):
    """Market regime classification."""
    TRENDING_UP = auto()
    TRENDING_DOWN = auto()
    RANGING_TIGHT = auto()
    RANGING_WIDE = auto()
    VOLATILE_EXPANSION = auto()
    VOLATILE_COMPRESSION = auto()
    TRANSITION = auto()
    UNKNOWN = auto()


class FrictionZone(Enum):
    """Price friction zone types."""
    ABSORPTION = auto()      # Price absorbed by hidden liquidity
    RESISTANCE = auto()      # Price rejected
    SLIPPAGE = auto()        # High slippage zone
    VACUUM = auto()          # Liquidity void
    NEUTRAL = auto()


class ExecutionRisk(Enum):
    """Execution risk levels."""
    LOW = auto()
    MEDIUM = auto()
    HIGH = auto()
    EXTREME = auto()


class StrategyLens(Enum):
    """Strategy-specific view types."""
    MOMENTUM = auto()
    MEAN_REVERSION = auto()
    BREAKOUT = auto()
    SCALPING = auto()
    SWING = auto()


# Performance budget constants
MAX_INFERENCE_LATENCY_MS = 5.0
MAX_RAM_PER_SYMBOL_KB = 500
MAX_STORAGE_PER_DAY_MB = 20
MAX_STALENESS_MS = 100


# =============================================================================
# DATA STRUCTURES - Concept 1: Micro-Friction Map
# =============================================================================

@dataclass
class MicroFrictionPoint:
    """Single point in the micro-friction map."""
    price_level: float
    friction_coefficient: float      # [0, 1] - 0=frictionless, 1=maximum friction
    absorption_strength: float       # Volume absorbed at this level
    slippage_estimate_bps: float     # Expected slippage in basis points
    zone_type: FrictionZone
    confidence: float                # [0, 1]
    decay_factor: float              # How much this level has decayed
    last_touch_bars: int             # Bars since last price touch
    touch_count: int                 # Number of times price touched this level


# =============================================================================
# DATA STRUCTURES - Concept 2: Latent Market State
# =============================================================================

@dataclass
class LatentMarketState:
    """Latent market state from autoencoder."""
    regime: MarketRegime
    regime_confidence: float         # [0, 1]
    latent_vector: np.ndarray        # 8-dim latent representation
    regime_color: Tuple[int, int, int, int]  # RGBA for visualization
    transition_probability: float    # Probability of regime change
    regime_duration_bars: int
    regime_stability: float          # [0, 1] - how stable is current regime


# =============================================================================
# DATA STRUCTURES - Concept 3: Time-to-Move
# =============================================================================

@dataclass
class TimeToMoveEstimate:
    """Time-to-move prediction (not direction)."""
    bars_to_breakout: float          # Expected bars until breakout
    bars_to_reversion: float         # Expected bars until mean reversion
    confidence_breakout: float       # [0, 1]
    confidence_reversion: float      # [0, 1]
    volatility_forecast: float       # Expected volatility in next N bars
    compression_score: float         # [0, 1] - how compressed is price
    energy_buildup: float            # [0, 1] - accumulated energy for move


# =============================================================================
# DATA STRUCTURES - Concept 4: Synthetic Liquidity
# =============================================================================

@dataclass
class SyntheticLiquidityMap:
    """Synthetic liquidity inferred from L1 data."""
    bid_liquidity_profile: np.ndarray    # Liquidity at each price level (bid side)
    ask_liquidity_profile: np.ndarray    # Liquidity at each price level (ask side)
    hidden_bid_estimate: float           # Estimated hidden bid liquidity
    hidden_ask_estimate: float           # Estimated hidden ask liquidity
    asymmetry_score: float               # [-1, 1] - bid/ask asymmetry
    iceberg_probability: float           # [0, 1] - probability of iceberg orders
    price_levels: np.ndarray             # Price levels for the profile


# =============================================================================
# DATA STRUCTURES - Concept 5: Volume Entropy
# =============================================================================

@dataclass
class VolumeEntropyState:
    """Volume entropy and information content."""
    entropy: float                   # Shannon entropy of volume distribution
    information_ratio: float         # Signal vs noise ratio
    noise_floor: float               # Estimated noise level
    informed_trading_prob: float     # Probability of informed trading
    volume_clustering: float         # Degree of volume clustering
    entropy_trend: float             # Rising/falling entropy


# =============================================================================
# DATA STRUCTURES - Concept 6: Market Memory
# =============================================================================

@dataclass
class MarketMemoryLevel:
    """A price level with memory decay."""
    price: float
    initial_strength: float          # Original strength when created
    current_strength: float          # Decayed strength
    creation_time: float             # Timestamp of creation
    last_reaction_time: float        # Last time price reacted
    reaction_count: int              # Number of reactions
    reaction_probability: float      # Learned probability of reaction
    volatility_at_creation: float    # Volatility when level was created
    memory_half_life_bars: int       # Half-life in bars
    level_type: str = "support"      # 'support' or 'resistance'
    strength_decay: float = 0.0      # Current decay factor


# =============================================================================
# DATA STRUCTURES - Concept 7: Execution Quality
# =============================================================================

@dataclass
class ExecutionQualityForecast:
    """Execution quality prediction."""
    expected_slippage_bps: float     # Expected slippage in basis points
    fill_probability: float          # [0, 1] - probability of fill
    time_to_fill_ms: float           # Expected time to fill
    adverse_selection_risk: float    # [0, 1] - risk of adverse selection
    market_impact_estimate: float    # Expected market impact
    execution_risk: ExecutionRisk
    optimal_order_size: float        # Suggested order size for minimal impact
    confidence: float


# =============================================================================
# DATA STRUCTURES - Concept 8: Micro-Trend Vectors
# =============================================================================

@dataclass
class MicroTrendVector:
    """Micro-trend as a vector field element."""
    price: float
    time_index: int
    direction: float                 # [-1, 1] - direction component
    magnitude: float                 # [0, 1] - strength component
    acceleration: float              # Rate of change of direction
    divergence: float                # Divergence from macro trend
    curl: float                      # Rotational component (trend reversal indicator)
    confidence: float


# =============================================================================
# DATA STRUCTURES - Concept 9: Liquidity Vacuum
# =============================================================================

@dataclass
class LiquidityVacuum:
    """Detected liquidity vacuum (gap risk)."""
    price_start: float
    price_end: float
    vacuum_strength: float           # [0, 1] - how empty is this zone
    jump_risk: float                 # [0, 1] - probability of price jumping through
    time_detected: float
    persistence: int                 # Bars this vacuum has existed


# =============================================================================
# DATA STRUCTURES - Concept 10: Model Disagreement
# =============================================================================

@dataclass
class ModelDisagreement:
    """Model disagreement metrics."""
    disagreement_score: float        # [0, 1] - overall disagreement
    model_predictions: Dict[str, float]  # Individual model predictions
    variance: float                  # Variance across models
    entropy: float                   # Entropy of prediction distribution
    confidence_adjusted: float       # Disagreement-adjusted confidence


# =============================================================================
# DATA STRUCTURES - Concept 11: Price Response Curvature
# =============================================================================

@dataclass
class PriceResponseCurve:
    """Non-linear price response to volume."""
    volume_levels: np.ndarray        # Volume input levels
    price_response: np.ndarray       # Expected price response
    curvature: float                 # Curvature of response function
    linearity_score: float           # [0, 1] - how linear is response
    saturation_point: float          # Volume at which response saturates
    elasticity: float                # Price elasticity to volume


# =============================================================================
# DATA STRUCTURES - Concept 12: Learned Support/Resistance
# =============================================================================

@dataclass
class LearnedSupportResistance:
    """ML-learned support/resistance level."""
    price: float
    level_type: str                  # 'support' or 'resistance'
    reaction_probability: float      # [0, 1] - probability of price reaction
    expected_reaction_magnitude: float  # Expected size of reaction
    confidence: float
    historical_reactions: int        # Number of historical reactions
    last_test_bars: int              # Bars since last test
    strength_decay: float            # Current decay factor


# =============================================================================
# DATA STRUCTURES - Concept 13: Information Flow
# =============================================================================

@dataclass
class InformationFlowState:
    """Information flow and price discovery metrics."""
    discovery_efficiency: float      # [0, 1] - how efficiently price discovers info
    information_share: float         # Share of price discovery
    lead_lag_score: float            # [-1, 1] - leading or lagging
    noise_ratio: float               # Noise in price discovery
    speed_of_adjustment: float       # How fast price adjusts to new info
    information_asymmetry: float     # Degree of information asymmetry


# =============================================================================
# DATA STRUCTURES - Concept 14: Strategy Views
# =============================================================================

@dataclass
class StrategyView:
    """Strategy-specific view of market state."""
    lens: StrategyLens
    signal_strength: float           # [-1, 1] - strategy-specific signal
    confidence: float                # [0, 1]
    key_levels: List[float]          # Important levels for this strategy
    risk_reward: float               # Estimated risk/reward
    entry_quality: float             # [0, 1] - quality of entry opportunity
    timing_score: float              # [0, 1] - timing quality


# =============================================================================
# DATA STRUCTURES - Concept 15: Confidence-Weighted Overlay
# =============================================================================

@dataclass
class ConfidenceWeightedOverlay:
    """Confidence-weighted visualization overlay."""
    overlay_type: str
    data: Dict[str, Any]
    confidence: float                # [0, 1] - controls opacity
    opacity: float                   # Computed opacity from confidence
    z_index: int
    visible: bool
    staleness_ms: float              # How stale is this overlay


# =============================================================================
# UNIFIED OUTPUT
# =============================================================================

@dataclass
class UnifiedMarketIntelligence:
    """Complete unified market intelligence state."""
    symbol: str
    timestamp: float
    
    # Core components (all 15 concepts)
    friction_map: List[MicroFrictionPoint]
    latent_state: LatentMarketState
    time_to_move: TimeToMoveEstimate
    liquidity_map: SyntheticLiquidityMap
    volume_entropy: VolumeEntropyState
    memory_levels: List[MarketMemoryLevel]
    execution_forecast: ExecutionQualityForecast
    micro_trends: List[MicroTrendVector]
    liquidity_vacuums: List[LiquidityVacuum]
    model_disagreement: ModelDisagreement
    price_response: PriceResponseCurve
    learned_sr: List[LearnedSupportResistance]
    information_flow: InformationFlowState
    strategy_views: Dict[StrategyLens, StrategyView]
    overlays: List[ConfidenceWeightedOverlay]
    
    # Aggregated metrics
    overall_confidence: float
    market_quality_score: float      # [0, 1] - overall market quality
    tradability_score: float         # [0, 1] - how tradable is this market
    
    # Performance metrics
    inference_latency_ms: float
    feature_staleness_ms: float


# =============================================================================
# CONFIGURATION
# =============================================================================

@dataclass
class MarketIntelligenceConfig:
    """Configuration for market intelligence system."""
    # Feature extraction
    friction_levels: int = 20            # Number of friction levels to track
    memory_decay_halflife: int = 100     # Half-life for memory decay (bars)
    liquidity_profile_levels: int = 10   # Levels in liquidity profile
    
    # Model settings
    latent_dim: int = 8                  # Latent state dimension
    micro_trend_window: int = 20         # Window for micro-trend calculation
    entropy_window: int = 50             # Window for entropy calculation
    
    # Time-to-move predictor
    ttm_horizons: List[int] = field(default_factory=lambda: [10, 20, 50, 100])
    
    # Execution quality
    slippage_lookback: int = 100         # Bars for slippage estimation
    
    # Memory management
    max_friction_points: int = 50        # Max friction points to track
    max_memory_levels: int = 30          # Max memory levels to track
    max_vacuums: int = 10                # Max vacuums to track
    
    # Update frequencies
    fast_update_bars: int = 1            # Every bar
    medium_update_bars: int = 5          # Every 5 bars
    slow_update_bars: int = 20           # Every 20 bars
    
    # Confidence thresholds
    min_confidence_display: float = 0.3  # Min confidence to display overlay
    confidence_decay_rate: float = 0.95  # Confidence decay per bar
    
    # Performance budget
    max_inference_ms: float = 5.0
    max_ram_kb: float = 500.0
