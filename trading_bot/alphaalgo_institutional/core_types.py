"""
AlphaAlgo Institutional - Core Types and Data Structures
=========================================================

Defines all fundamental types, enums, and dataclasses used across the institutional system.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Dict, List, Optional, Any, Set, Tuple
import hashlib
import uuid


# =============================================================================
# MARKET TYPES
# =============================================================================

import logging

logger = logging.getLogger(__name__)

class MarketType(Enum):
    """Tradeable market categories."""
    EQUITY = "equity"
    FX = "fx"
    CRYPTO = "crypto"
    RATES = "rates"
    VOLATILITY = "volatility"
    COMMODITIES = "commodities"
    CROSS_ASSET = "cross_asset"


class MarketState(Enum):
    """Current market operational state."""
    OPEN = "open"
    CLOSED = "closed"
    PRE_MARKET = "pre_market"
    POST_MARKET = "post_market"
    HALTED = "halted"
    UNKNOWN = "unknown"


# =============================================================================
# REGIME TYPES
# =============================================================================

class VolatilityRegime(Enum):
    """Volatility regime classification."""
    ULTRA_LOW = "ultra_low"
    LOW = "low"
    NORMAL = "normal"
    ELEVATED = "elevated"
    HIGH = "high"
    EXTREME = "extreme"
    CRISIS = "crisis"


class CorrelationRegime(Enum):
    """Cross-asset correlation regime."""
    DECORRELATED = "decorrelated"
    NORMAL = "normal"
    ELEVATED = "elevated"
    RISK_ON = "risk_on"
    RISK_OFF = "risk_off"
    CRISIS_CORRELATION = "crisis_correlation"


class LiquidityRegime(Enum):
    """Market liquidity regime."""
    ABUNDANT = "abundant"
    NORMAL = "normal"
    THIN = "thin"
    STRESSED = "stressed"
    CRISIS = "crisis"
    FROZEN = "frozen"


class TrendRegime(Enum):
    """Trend vs mean-reversion regime."""
    STRONG_TREND = "strong_trend"
    WEAK_TREND = "weak_trend"
    RANGING = "ranging"
    MEAN_REVERTING = "mean_reverting"
    CHOPPY = "choppy"
    TRANSITIONING = "transitioning"


class MarketRegime(Enum):
    """Overall market regime classification."""
    CALM = "calm"
    NORMAL = "normal"
    VOLATILE = "volatile"
    TRENDING = "trending"
    MEAN_REVERTING = "mean_reverting"
    CRISIS = "crisis"
    RECOVERY = "recovery"
    TRANSITION = "transition"


# =============================================================================
# MODEL TYPES
# =============================================================================

class ModelFamily(Enum):
    """Quantitative model family classification."""
    # Mathematics-inspired
    STOCHASTIC = "stochastic"
    OPTIMIZATION = "optimization"
    GRAPH_THEORY = "graph_theory"
    TOPOLOGY = "topology"
    INFORMATION_THEORY = "information_theory"
    CONTROL_THEORY = "control_theory"
    GAME_THEORY = "game_theory"
    
    # Physics-inspired
    BROWNIAN = "brownian"
    DIFFUSION = "diffusion"
    PHASE_TRANSITION = "phase_transition"
    ENTROPY = "entropy"
    CHAOS = "chaos"
    RESONANCE = "resonance"
    
    # Biology-inspired
    EVOLUTIONARY = "evolutionary"
    PREDATOR_PREY = "predator_prey"
    NEURAL = "neural"
    ECOSYSTEM = "ecosystem"
    SWARM = "swarm"
    GENETIC = "genetic"
    
    # Chemistry-inspired
    REACTION_KINETICS = "reaction_kinetics"
    EQUILIBRIUM = "equilibrium"
    CATALYST = "catalyst"
    
    # Complex Systems
    FRACTAL = "fractal"
    POWER_LAW = "power_law"
    FEEDBACK = "feedback"
    EMERGENCE = "emergence"
    
    # AI (Conservative)
    ENSEMBLE = "ensemble"
    BAYESIAN = "bayesian"
    ANOMALY_DETECTION = "anomaly_detection"
    META_LEARNING = "meta_learning"


class ModelStatus(Enum):
    """Model lifecycle status."""
    HYPOTHESIS = "hypothesis"
    DEVELOPMENT = "development"
    VALIDATION = "validation"
    SANDBOX = "sandbox"
    APPROVED = "approved"
    LIVE = "live"
    DEGRADED = "degraded"
    QUARANTINED = "quarantined"
    RETIRED = "retired"
    KILLED = "killed"


class ModelDecision(Enum):
    """Validation committee decision."""
    PASS = "pass"
    KILL = "kill"
    REVISE = "revise"
    DEFER = "defer"


# =============================================================================
# RISK TYPES
# =============================================================================

class RiskLevel(Enum):
    """Risk severity level."""
    MINIMAL = 1
    LOW = 2
    MODERATE = 3
    ELEVATED = 4
    HIGH = 5
    SEVERE = 6
    CRITICAL = 7
    EXTREME = 8


class RiskType(Enum):
    """Types of risk."""
    MARKET = "market"
    CREDIT = "credit"
    LIQUIDITY = "liquidity"
    OPERATIONAL = "operational"
    MODEL = "model"
    CONCENTRATION = "concentration"
    TAIL = "tail"
    CORRELATION = "correlation"
    REGIME = "regime"
    EXECUTION = "execution"


class DrawdownState(Enum):
    """Drawdown severity state."""
    NORMAL = "normal"
    ELEVATED = "elevated"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


# =============================================================================
# EXECUTION TYPES
# =============================================================================

class OrderType(Enum):
    """Order types."""
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"
    ICEBERG = "iceberg"
    TWAP = "twap"
    VWAP = "vwap"
    POV = "pov"  # Percentage of Volume


class ExecutionUrgency(Enum):
    """Execution urgency level."""
    PASSIVE = "passive"
    NORMAL = "normal"
    URGENT = "urgent"
    AGGRESSIVE = "aggressive"
    IMMEDIATE = "immediate"


class FillStatus(Enum):
    """Order fill status."""
    PENDING = "pending"
    PARTIAL = "partial"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    EXPIRED = "expired"


# =============================================================================
# COMMITTEE TYPES
# =============================================================================

class CommitteeType(Enum):
    """Internal committee types."""
    MARKET_SELECTION = "market_selection"
    REGIME_INTELLIGENCE = "regime_intelligence"
    QUANTITATIVE_RESEARCH = "quantitative_research"
    VALIDATION_KILL = "validation_kill"
    PORTFOLIO_CAPITAL = "portfolio_capital"
    EXECUTION_INTELLIGENCE = "execution_intelligence"
    EVOLUTION_AUDIT = "evolution_audit"


class CommitteeDecision(Enum):
    """Committee decision types."""
    APPROVE = "approve"
    REJECT = "reject"
    DEFER = "defer"
    ESCALATE = "escalate"
    CONDITIONAL = "conditional"


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class MarketSelection:
    """Market selection decision."""
    market_type: MarketType
    symbols: List[str]
    score: float  # 0-1 selection score
    liquidity_score: float
    inefficiency_score: float
    data_quality_score: float
    execution_feasibility: float
    capacity_estimate: float  # Max capital deployable
    rationale: str
    constraints: List[str]
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def __post_init__(self):
        try:
            self.id = str(uuid.uuid4())[:8]
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in __post_init__: {e}")
            raise


@dataclass
class RegimeState:
    """Current regime state across dimensions."""
    volatility: VolatilityRegime
    correlation: CorrelationRegime
    liquidity: LiquidityRegime
    trend: TrendRegime
    overall: MarketRegime
    confidence: float  # 0-1
    transition_probability: float  # Probability of regime change
    detected_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'volatility': self.volatility.value,
            'correlation': self.correlation.value,
            'liquidity': self.liquidity.value,
            'trend': self.trend.value,
            'overall': self.overall.value,
            'confidence': self.confidence,
            'transition_probability': self.transition_probability,
            'detected_at': self.detected_at.isoformat()
        }


@dataclass
class ModelHypothesis:
    """Quantitative model hypothesis."""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    name: str = ""
    family: ModelFamily = ModelFamily.ENSEMBLE
    description: str = ""
    mathematical_basis: str = ""
    expected_edge: float = 0.0  # Expected Sharpe or similar
    expected_decay_rate: float = 0.0  # How fast edge decays
    failure_modes: List[str] = field(default_factory=list)
    regime_dependencies: List[MarketRegime] = field(default_factory=list)
    data_requirements: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    status: ModelStatus = ModelStatus.HYPOTHESIS
    
    def compute_hash(self) -> str:
        """Compute unique hash for model hypothesis."""
        try:
            content = f"{self.name}{self.family.value}{self.mathematical_basis}"
            return hashlib.sha256(content.encode()).hexdigest()[:16]
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in compute_hash: {e}")
            raise


@dataclass
class ModelPerformance:
    """Model performance metrics."""
    model_id: str
    sharpe_ratio: float = 0.0
    sortino_ratio: float = 0.0
    calmar_ratio: float = 0.0
    max_drawdown: float = 0.0
    win_rate: float = 0.0
    profit_factor: float = 0.0
    information_ratio: float = 0.0
    tail_ratio: float = 0.0  # Upside vs downside tail
    decay_rate: float = 0.0  # Performance decay rate
    regime_stability: float = 0.0  # Performance stability across regimes
    transaction_cost_impact: float = 0.0
    capacity_utilization: float = 0.0
    last_updated: datetime = field(default_factory=datetime.utcnow)
    
    def is_degraded(self, threshold: float = 0.5) -> bool:
        """Check if model performance is degraded."""
        return self.sharpe_ratio < threshold or self.decay_rate > 0.1


@dataclass
class CapitalAllocation:
    """Capital allocation decision."""
    model_id: str
    allocated_capital: float
    max_capital: float
    risk_budget: float  # Percentage of total risk budget
    position_limit: int
    leverage_limit: float
    drawdown_limit: float
    correlation_constraint: float
    regime_conditions: List[MarketRegime]
    approved_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    
    def is_expired(self) -> bool:
        try:
            if self.expires_at is None:
                return False
            return datetime.utcnow() > self.expires_at
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in is_expired: {e}")
            raise


@dataclass
class RiskMetrics:
    """Portfolio risk metrics."""
    total_exposure: float = 0.0
    net_exposure: float = 0.0
    gross_exposure: float = 0.0
    var_95: float = 0.0
    var_99: float = 0.0
    cvar_95: float = 0.0
    cvar_99: float = 0.0
    max_drawdown: float = 0.0
    current_drawdown: float = 0.0
    correlation_risk: float = 0.0
    concentration_risk: float = 0.0
    liquidity_risk: float = 0.0
    tail_risk: float = 0.0
    model_risk: float = 0.0
    overall_risk_level: RiskLevel = RiskLevel.MODERATE
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ExecutionPlan:
    """Execution plan for an order."""
    order_id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    symbol: str = ""
    direction: str = ""  # 'buy' or 'sell'
    quantity: float = 0.0
    order_type: OrderType = OrderType.LIMIT
    urgency: ExecutionUrgency = ExecutionUrgency.NORMAL
    limit_price: Optional[float] = None
    stop_price: Optional[float] = None
    time_horizon: int = 0  # Seconds
    max_slippage: float = 0.0
    participation_rate: float = 0.0  # For VWAP/TWAP
    expected_cost: float = 0.0
    venue_preferences: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class TradeResult:
    """Result of an executed trade."""
    order_id: str
    symbol: str
    direction: str
    requested_quantity: float
    filled_quantity: float
    average_price: float
    total_cost: float
    slippage: float
    market_impact: float
    execution_time: float  # Seconds
    fill_status: FillStatus
    venue: str
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class CommitteeVote:
    """Vote from an internal committee."""
    committee: CommitteeType
    decision: CommitteeDecision
    confidence: float
    rationale: str
    conditions: List[str] = field(default_factory=list)
    dissenting_views: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class EvolutionEvent:
    """Model evolution event."""
    event_type: str  # 'mutation', 'retirement', 'combination', 'capital_reduction'
    model_id: str
    parent_ids: List[str] = field(default_factory=list)
    reason: str = ""
    performance_before: Optional[ModelPerformance] = None
    changes_made: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)


# =============================================================================
# IDEA VECTOR CATEGORIES
# =============================================================================

class IdeaCategory(Enum):
    """Categories for 150+ idea vectors."""
    MARKET_STRUCTURE = "market_structure"
    REGIME_DYNAMICS = "regime_dynamics"
    SIGNAL_DESIGN = "signal_design"
    RISK_PORTFOLIO = "risk_portfolio"
    EXECUTION_MICROSTRUCTURE = "execution_microstructure"
    MODEL_GOVERNANCE = "model_governance"
    EVOLUTION_IMPROVEMENT = "evolution_improvement"
    CROSS_DISCIPLINARY = "cross_disciplinary"
    STRATEGIC_INTELLIGENCE = "strategic_intelligence"
    META_DECISION = "meta_decision"
    INSTITUTIONAL_CONCEPTS = "institutional_concepts"
    SYSTEM_INTEGRITY = "system_integrity"
    LONG_TERM_EVOLUTION = "long_term_evolution"
    FINAL_INTELLIGENCE = "final_intelligence"
    INSTITUTIONAL_DISCIPLINE = "institutional_discipline"


@dataclass
class IdeaVector:
    """Single idea vector constraint."""
    id: str
    category: IdeaCategory
    name: str
    description: str
    weight: float = 1.0  # Importance weight
    is_constraint: bool = True  # If True, must be satisfied
    related_vectors: List[str] = field(default_factory=list)


# =============================================================================
# SYSTEM CONSTANTS
# =============================================================================

class SystemConstants:
    """Immutable system constants."""
    
    # Risk limits (NON-NEGOTIABLE)
    MAX_POSITION_SIZE_PCT = 0.10  # 10% max per position
    MAX_POSITION_SIZE = 0.10  # Alias for backward compatibility
    MAX_SECTOR_EXPOSURE_PCT = 0.25  # 25% max per sector
    MAX_CORRELATION_EXPOSURE = 0.30  # 30% max correlated exposure
    MAX_LEVERAGE = 3.0  # 3x max leverage
    MAX_DAILY_LOSS_PCT = 0.05  # 5% max daily loss
    MAX_DRAWDOWN_PCT = 0.20  # 20% max drawdown
    MAX_DRAWDOWN_LIMIT = 0.20  # Alias for backward compatibility
    
    # Model governance
    MODEL_KILL_THRESHOLD = 0.5  # Sharpe below this = kill
    MODEL_DECAY_THRESHOLD = 0.1  # Decay rate above this = concern
    MIN_VALIDATION_PERIODS = 252  # 1 year minimum
    MAX_MODELS_LIVE = 20  # Maximum concurrent live models
    
    # Evolution
    MODEL_SURVIVAL_RATE = 0.10  # 90% of ideas must die
    MUTATION_RATE = 0.05  # 5% mutation rate
    
    # Execution
    MAX_SLIPPAGE_BPS = 50  # 50 bps max slippage
    MAX_MARKET_IMPACT_BPS = 100  # 100 bps max impact
    
    # Time constants
    REGIME_DETECTION_WINDOW = 60  # Days
    PERFORMANCE_DECAY_WINDOW = 90  # Days
    CAPITAL_REVIEW_FREQUENCY = 7  # Days


# =============================================================================
# PROHIBITION TYPES
# =============================================================================

class Prohibition(Enum):
    """Absolute prohibitions - violation = system failure."""
    BLIND_PRICE_PREDICTION = "blind_price_prediction"
    INDICATOR_STACKING = "indicator_stacking"
    SINGLE_STRATEGY_DEPENDENCE = "single_strategy_dependence"
    IGNORING_EXECUTION_COSTS = "ignoring_execution_costs"
    IGNORING_REGIME_SHIFTS = "ignoring_regime_shifts"
    CHASING_RECENT_PERFORMANCE = "chasing_recent_performance"
    NARRATIVE_LOSS_EXPLANATION = "narrative_loss_explanation"
    UNCONTROLLED_LEVERAGE = "uncontrolled_leverage"
    UNEXPLAINED_TRADES = "unexplained_trades"


@dataclass
class ProhibitionViolation:
    """Record of a prohibition violation."""
    prohibition: Prohibition
    description: str
    severity: RiskLevel
    detected_at: datetime = field(default_factory=datetime.utcnow)
    context: Dict[str, Any] = field(default_factory=dict)
    
    def __str__(self) -> str:
        return f"VIOLATION: {self.prohibition.value} - {self.description}"
