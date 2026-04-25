"""
GETS Type Definitions

Core data types and enums for the Governed Evolving Time-Series Foundation System.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple, Callable
from datetime import datetime
from enum import Enum, auto
import numpy as np


class ModelType(Enum):
    """Foundation model types in GETS."""
    KRONOS = "kronos"           # Market-sequence encoder
    TIMESFM = "timesfm"       # Long-context univariate forecaster
    MOIRAI = "moirai"         # Multivariate probability forecaster
    TTM = "ttm"               # TinyTimeMixers (fast production inference)


class ForecastHorizon(Enum):
    """Forecast horizons supported by GETS."""
    IMMEDIATE = "1m"          # 1 minute
    SHORT = "5m"              # 5 minutes
    MEDIUM = "1h"             # 1 hour
    LONG = "1d"               # 1 day
    EXTENDED = "1w"           # 1 week


class RegimeType(Enum):
    """Market regime classifications."""
    TRENDING_BULL = auto()
    TRENDING_BEAR = auto()
    RANGING = auto()
    HIGH_VOLATILITY = auto()
    LOW_VOLATILITY = auto()
    BREAKOUT = auto()
    REVERSAL = auto()
    CRISIS = auto()
    UNKNOWN = auto()


class DisagreementPattern(Enum):
    """Model disagreement patterns that signal trading opportunities."""
    KRONOS_UP_TIMESFM_DOWN = auto()      # Short-term momentum vs long-term mean reversion
    MOIRAI_HIGH_VARIANCE = auto()        # Cross-asset uncertainty elevated
    TTM_STABLE_OTHERS_VOLATILE = auto()  # Local predictability, structural uncertainty
    ALL_MODELS_CONVERGING = auto()       # High-confidence consensus (crowding warning)
    UNCERTAINTY_FAN_EXPANDING = auto()   # Information entropy increasing
    KRONOS_BLINDSPOT = auto()            # Kronos underperforming (exploit with others)
    TIMESFM_REGIME_MISMATCH = auto()     # Long-horizon regime memory conflict
    MOIRAI_CROSS_ASSET_DIVERGENCE = auto()  # Portfolio-level inconsistency


class GovernanceDecision(Enum):
    """Final governance decisions for forecast signals."""
    APPROVE = auto()
    RESIZE = auto()           # Reduce position size
    DEFER = auto()            # Wait for clarity
    REJECT = auto()
    ABSTAIN = auto()          # Do not trade


@dataclass
class MarketData:
    """Standardized market data input."""
    symbol: str
    timestamp: datetime
    ohlcv: Dict[str, float]  # open, high, low, close, volume
    
    # Extended features
    bid_ask_spread: Optional[float] = None
    depth_imbalance: Optional[float] = None
    realized_volatility: Optional[float] = None
    volume_profile: Optional[Dict[str, float]] = None
    funding_rate: Optional[float] = None  # For crypto
    open_interest: Optional[float] = None  # For crypto
    
    # Cross-asset context
    correlated_assets: Optional[Dict[str, float]] = None
    macro_flags: Optional[List[str]] = None
    session_features: Optional[Dict[str, Any]] = None


@dataclass
class FoundationForecast:
    """Forecast output from a single foundation model."""
    model_type: ModelType
    symbol: str
    timestamp: datetime
    horizon: ForecastHorizon
    
    # Point forecast
    point_prediction: float
    
    # Probabilistic forecast (quantile fan)
    quantile_05: float
    quantile_25: float
    quantile_50: float  # median
    quantile_75: float
    quantile_95: float
    
    # Uncertainty measures
    forecast_std: float
    prediction_interval_width: float
    
    # Model confidence
    model_confidence: float  # 0-1
    in_sample_calibration_error: Optional[float] = None
    
    # Embedding (for downstream use)
    latent_embedding: Optional[np.ndarray] = None
    volatility_state: Optional[float] = None
    regime_encoding: Optional[np.ndarray] = None


@dataclass
class TradingNativeHeads:
    """Multi-task trading-native predictions."""
    expected_signed_return: float  # Direction + magnitude
    volatility_forecast: float
    drawdown_risk_prob: float  # 0-1
    rank_score: float  # Cross-asset ranking
    prob_exceed_cost_threshold: float  # 0-1
    regime_label: RegimeType
    execution_difficulty_score: float  # 0-1 (higher = harder)
    
    # Edge-after-cost (primary trading signal)
    edge_after_cost: float
    tradable: bool


@dataclass
class DisagreementGeometry:
    """Computed disagreement metrics across foundation models."""
    # Raw disagreements
    directional_disagreement: float  # Sign conflict magnitude
    magnitude_disagreement: float  # Variance in point predictions
    uncertainty_disagreement: float  # Variance in confidence
    
    # Topology measures
    disagreement_pattern: Optional[DisagreementPattern]
    pattern_strength: float  # 0-1
    
    # Model-specific diagnostics
    most_bullish_model: ModelType
    most_bearish_model: ModelType
    most_uncertain_model: ModelType
    most_confident_model: ModelType
    
    # Stability measures
    cross_model_stability: float  # 0-1 (higher = more stable)
    forecast_consensus_score: float  # 0-1 (higher = more agreement)
    
    # Derived signals
    disagreement_entropy: float  # Information-theoretic measure
    model_authority_weights: Dict[ModelType, float]  # Dynamic weighting


@dataclass
class SelfDiagnosisReport:
    """Output from Layer 3 introspection."""
    # Stability tests
    forecast_stability_score: float  # 0-1
    perturbation_sensitivity: float
    stability_passed: bool
    
    # Evidence checks
    evidence_sufficiency_score: float  # 0-1
    evidence_passed: bool
    
    # Contradiction detection
    contradiction_detected: bool
    contradiction_details: List[str]
    
    # Regime mismatch
    regime_mismatch_score: float  # 0-1 (higher = more mismatch)
    regime_passed: bool
    
    # Calibration drift
    calibration_drift_detected: bool
    calibration_error: Optional[float]
    
    # Execution feasibility
    execution_feasible: bool
    execution_constraints: List[str]
    
    # Overall assessment
    overall_passed: bool
    blocking_issues: List[str]
    warnings: List[str]
    
    # Failure tracking
    failure_class: Optional[str] = None
    similar_failures_count: int = 0


@dataclass
class GETSSignal:
    """Final trading signal output from GETS."""
    symbol: str
    timestamp: datetime
    
    # Signal properties
    direction: int  # -1, 0, 1
    confidence: float  # 0-1
    expected_edge: float
    
    # Uncertainty
    uncertainty_quantile_05: float
    uncertainty_quantile_95: float
    prediction_interval: Tuple[float, float]
    
    # Governance
    governance_decision: GovernanceDecision
    decision_reasoning: str
    
    # Source tracking
    source_models: List[ModelType]
    disagreement_geometry: DisagreementGeometry
    diagnosis_report: SelfDiagnosisReport
    
    # Execution guidance
    recommended_size_scale: float  # 0-1 (position sizing)
    abstain_recommended: bool
    abstain_reason: Optional[str] = None


@dataclass
class MutationProposal:
    """Proposed mutation from Layer 4 evolution."""
    mutation_id: str
    timestamp: datetime
    
    # What changed
    mutation_type: str  # e.g., "lora_rank", "head_architecture", "fusion_weight"
    target_model: ModelType
    description: str
    
    # Motivation
    failure_pattern_addressed: str
    expected_improvement: str
    
    # Test results
    backtest_results: Dict[str, float]
    paper_trading_results: Optional[Dict[str, float]]
    statistical_significance: float  # p-value
    
    # Status
    status: str  # "proposed", "testing", "validated", "rejected", "promoted"


@dataclass
class EvolutionChampion:
    """A validated model version ready for promotion."""
    champion_id: str
    baseline_version: str
    mutation_proposals: List[str]  # IDs of incorporated mutations
    
    # Validation metrics
    ic_improvement: float
    sharpe_improvement: float
    max_drawdown_improvement: float
    
    # Coverage
    regimes_tested: List[RegimeType]
    regime_coverage_score: float
    
    # Safety
    rollback_available: bool
    promotion_timestamp: Optional[datetime] = None


@dataclass
class GETSConfig:
    """Configuration for GETS system."""
    # Foundation model settings
    kronos_enabled: bool = True
    timesfm_enabled: bool = True
    moirai_enabled: bool = True
    ttm_enabled: bool = True
    
    # Layer 2: Trading heads
    use_lora_adapters: bool = True
    lora_rank: int = 8
    lora_alpha: float = 16.0
    
    # Layer 3: Diagnosis thresholds
    stability_threshold: float = 0.7
    evidence_threshold: float = 0.6
    regime_mismatch_threshold: float = 0.8
    
    # Layer 4: Evolution
    sandbox_path: str = "./gets_sandbox"
    min_backtest_samples: int = 1000
    significance_threshold: float = 0.05
    
    # Layer 5: Governance
    require_human_promotion: bool = True
    audit_storage_path: str = "./gets_audit"
    max_drawdown_tolerance: float = 0.15
    
    # Integration
    decision_governance_integration: bool = True
