"""
RDAOS Core Types and Data Structures
=====================================
Research-Driven Alpha Operating System - Core Module

This module defines all core data structures for the RDAOS system:
- ResearchObject: Structured representation of academic research
- Hypothesis: Testable hypothesis extracted from research
- FeatureFamily: Collection of related features with regime conditions
- TestingResult: Comprehensive testing results
- AlphaDeployment: Live deployment tracking

Author: AlphaAlgo Research Team
"""

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union
import uuid

import numpy as np


import logging

logger = logging.getLogger(__name__)

class ProductionStatus(Enum):
    """Production status of a research object or feature"""
    REJECTED = "rejected"
    CANDIDATE = "candidate"
    TESTING = "testing"
    PROMOTED = "promoted"
    DEPLOYED = "deployed"
    DECAYING = "decaying"
    RETIRED = "retired"


class AssetClass(Enum):
    """Supported asset classes"""
    EQUITY = "equity"
    FOREX = "forex"
    CRYPTO = "crypto"
    FUTURES = "futures"
    OPTIONS = "options"
    FIXED_INCOME = "fixed_income"
    COMMODITIES = "commodities"
    MULTI_ASSET = "multi_asset"


class AlphaHorizon(Enum):
    """Trading horizon for alpha signals"""
    TICK = "tick"                    # < 1 second
    MICROSTRUCTURE = "microstructure"  # 1 second - 1 minute
    INTRADAY = "intraday"            # 1 minute - 1 day
    DAILY = "daily"                  # 1 day - 1 week
    WEEKLY = "weekly"                # 1 week - 1 month
    MONTHLY = "monthly"              # 1 month - 1 quarter
    QUARTERLY = "quarterly"          # 1 quarter - 1 year
    LONG_TERM = "long_term"          # > 1 year


class RegimeType(Enum):
    """Market regime types"""
    NORMAL = "normal"
    TRENDING_UP = "trending_up"
    TRENDING_DOWN = "trending_down"
    HIGH_VOLATILITY = "high_volatility"
    LOW_VOLATILITY = "low_volatility"
    CRISIS = "crisis"
    RECOVERY = "recovery"
    RANGING = "ranging"
    LIQUIDITY_CRISIS = "liquidity_crisis"
    CORRELATION_BREAKDOWN = "correlation_breakdown"


class FailureMode(Enum):
    """Known failure modes for alpha strategies"""
    REGIME_SHIFT = "regime_shift"
    ALPHA_DECAY = "alpha_decay"
    CROWDING = "crowding"
    LIQUIDITY_DRAIN = "liquidity_drain"
    CORRELATION_SPIKE = "correlation_spike"
    EXECUTION_SLIPPAGE = "execution_slippage"
    DATA_QUALITY = "data_quality"
    MODEL_DRIFT = "model_drift"
    OVERFITTING = "overfitting"
    SURVIVORSHIP_BIAS = "survivorship_bias"


class WeaknessCategory(Enum):
    """Categories of detected weaknesses"""
    DRAWDOWN = "drawdown"
    VOLATILITY = "volatility"
    CORRELATION = "correlation"
    SLIPPAGE = "slippage"
    EXECUTION = "execution"
    SIGNAL_DRIFT = "signal_drift"
    REGIME_MISMATCH = "regime_mismatch"
    CAPACITY_BREACH = "capacity_breach"


@dataclass
class CausalMechanism:
    """Causal mechanism extracted from research"""
    cause: str
    effect: str
    conditions: List[str]
    time_lag: Optional[str] = None
    confidence: float = 0.0
    evidence_strength: str = "weak"  # weak, moderate, strong
    
    def to_dict(self) -> Dict:
        return {
            "cause": self.cause,
            "effect": self.effect,
            "conditions": self.conditions,
            "time_lag": self.time_lag,
            "confidence": self.confidence,
            "evidence_strength": self.evidence_strength
        }


@dataclass
class Hypothesis:
    """Testable hypothesis extracted from research"""
    hypothesis_id: str
    paper_id: str
    statement: str
    causal_mechanism: CausalMechanism
    
    required_data: List[str]
    feature_definitions: Dict[str, str]
    
    regime_sensitivity: List[RegimeType]
    failure_conditions: List[str]
    
    testable: bool = True
    test_methodology: str = ""
    expected_effect_size: float = 0.0
    
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict:
        return {
            "hypothesis_id": self.hypothesis_id,
            "paper_id": self.paper_id,
            "statement": self.statement,
            "causal_mechanism": self.causal_mechanism.to_dict(),
            "required_data": self.required_data,
            "feature_definitions": self.feature_definitions,
            "regime_sensitivity": [r.value for r in self.regime_sensitivity],
            "failure_conditions": self.failure_conditions,
            "testable": self.testable,
            "test_methodology": self.test_methodology,
            "expected_effect_size": self.expected_effect_size,
            "created_at": self.created_at.isoformat()
        }


@dataclass
class FeatureDefinition:
    """Definition of a single feature within a family"""
    feature_id: str
    name: str
    formula: str
    parameters: Dict[str, Any]
    
    time_horizon: AlphaHorizon
    lookback_period: int  # in bars
    
    normalization_method: str = "zscore"  # zscore, minmax, rank, none
    regime_conditions: List[RegimeType] = field(default_factory=list)
    
    risk_controls: Dict[str, float] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "feature_id": self.feature_id,
            "name": self.name,
            "formula": self.formula,
            "parameters": self.parameters,
            "time_horizon": self.time_horizon.value,
            "lookback_period": self.lookback_period,
            "normalization_method": self.normalization_method,
            "regime_conditions": [r.value for r in self.regime_conditions],
            "risk_controls": self.risk_controls
        }


@dataclass
class FeatureFamily:
    """
    Collection of related features derived from a hypothesis.
    
    A feature family represents a coherent set of features that:
    - Share the same underlying alpha source
    - Have similar regime sensitivities
    - Can be calculated from the same data
    """
    family_id: str
    name: str
    hypothesis_id: str
    
    features: List[FeatureDefinition]
    
    alpha_source: str
    asset_class: AssetClass
    time_horizon: AlphaHorizon
    
    regime_conditions: List[RegimeType]
    risk_controls: Dict[str, float]
    
    capacity_limit_usd: float = 0.0
    expected_decay_days: int = 0
    
    status: ProductionStatus = ProductionStatus.CANDIDATE
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict:
        return {
            "family_id": self.family_id,
            "name": self.name,
            "hypothesis_id": self.hypothesis_id,
            "features": [f.to_dict() for f in self.features],
            "alpha_source": self.alpha_source,
            "asset_class": self.asset_class.value,
            "time_horizon": self.time_horizon.value,
            "regime_conditions": [r.value for r in self.regime_conditions],
            "risk_controls": self.risk_controls,
            "capacity_limit_usd": self.capacity_limit_usd,
            "expected_decay_days": self.expected_decay_days,
            "status": self.status.value,
            "created_at": self.created_at.isoformat()
        }


@dataclass
class TestingMetrics:
    """Comprehensive testing metrics"""
    sharpe_ratio: float = 0.0
    sortino_ratio: float = 0.0
    calmar_ratio: float = 0.0
    
    total_return: float = 0.0
    annualized_return: float = 0.0
    
    max_drawdown: float = 0.0
    avg_drawdown: float = 0.0
    drawdown_duration_days: int = 0
    
    volatility: float = 0.0
    downside_volatility: float = 0.0
    
    win_rate: float = 0.0
    profit_factor: float = 0.0
    
    var_95: float = 0.0
    cvar_95: float = 0.0
    
    total_trades: int = 0
    avg_trade_duration: float = 0.0
    
    transaction_costs: float = 0.0
    slippage: float = 0.0
    market_impact: float = 0.0
    
    def to_dict(self) -> Dict:
        return {
            "sharpe_ratio": self.sharpe_ratio,
            "sortino_ratio": self.sortino_ratio,
            "calmar_ratio": self.calmar_ratio,
            "total_return": self.total_return,
            "annualized_return": self.annualized_return,
            "max_drawdown": self.max_drawdown,
            "avg_drawdown": self.avg_drawdown,
            "drawdown_duration_days": self.drawdown_duration_days,
            "volatility": self.volatility,
            "downside_volatility": self.downside_volatility,
            "win_rate": self.win_rate,
            "profit_factor": self.profit_factor,
            "var_95": self.var_95,
            "cvar_95": self.cvar_95,
            "total_trades": self.total_trades,
            "avg_trade_duration": self.avg_trade_duration,
            "transaction_costs": self.transaction_costs,
            "slippage": self.slippage,
            "market_impact": self.market_impact
        }


@dataclass
class TestingResult:
    """Complete testing results for a feature family"""
    test_id: str
    family_id: str
    
    # Out-of-sample testing
    oos_metrics: TestingMetrics = field(default_factory=TestingMetrics)
    oos_passed: bool = False
    
    # Cross-regime testing
    regime_metrics: Dict[str, TestingMetrics] = field(default_factory=dict)
    regime_passed: bool = False
    
    # Cost-adjusted testing
    cost_adjusted_metrics: TestingMetrics = field(default_factory=TestingMetrics)
    cost_adjusted_passed: bool = False
    
    # Parameter stability testing
    parameter_stability_score: float = 0.0
    parameter_stability_passed: bool = False
    
    # Data robustness testing
    data_robustness_score: float = 0.0
    data_robustness_passed: bool = False
    
    # Overall
    all_tests_passed: bool = False
    rejection_reasons: List[str] = field(default_factory=list)
    
    tested_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict:
        return {
            "test_id": self.test_id,
            "family_id": self.family_id,
            "oos_metrics": self.oos_metrics.to_dict(),
            "oos_passed": self.oos_passed,
            "regime_metrics": {k: v.to_dict() for k, v in self.regime_metrics.items()},
            "regime_passed": self.regime_passed,
            "cost_adjusted_metrics": self.cost_adjusted_metrics.to_dict(),
            "cost_adjusted_passed": self.cost_adjusted_passed,
            "parameter_stability_score": self.parameter_stability_score,
            "parameter_stability_passed": self.parameter_stability_passed,
            "data_robustness_score": self.data_robustness_score,
            "data_robustness_passed": self.data_robustness_passed,
            "all_tests_passed": self.all_tests_passed,
            "rejection_reasons": self.rejection_reasons,
            "tested_at": self.tested_at.isoformat()
        }


@dataclass
class FeatureRanking:
    """Ranking information for a feature family"""
    family_id: str
    
    risk_adjusted_return_rank: int = 0
    stability_rank: int = 0
    correlation_rank: int = 0  # Lower correlation with existing = better
    capacity_rank: int = 0
    robustness_rank: int = 0
    
    composite_score: float = 0.0
    composite_rank: int = 0
    
    promoted: bool = False
    promotion_reason: str = ""
    
    ranked_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict:
        return {
            "family_id": self.family_id,
            "risk_adjusted_return_rank": self.risk_adjusted_return_rank,
            "stability_rank": self.stability_rank,
            "correlation_rank": self.correlation_rank,
            "capacity_rank": self.capacity_rank,
            "robustness_rank": self.robustness_rank,
            "composite_score": self.composite_score,
            "composite_rank": self.composite_rank,
            "promoted": self.promoted,
            "promotion_reason": self.promotion_reason,
            "ranked_at": self.ranked_at.isoformat()
        }


@dataclass
class AlphaDeathClock:
    """Tracking alpha decay and retirement"""
    family_id: str
    
    deployment_date: datetime
    expected_decay_date: datetime
    
    initial_sharpe: float = 0.0
    current_sharpe: float = 0.0
    sharpe_decay_rate: float = 0.0  # per day
    
    initial_capacity: float = 0.0
    current_capacity: float = 0.0
    
    days_deployed: int = 0
    days_until_expected_decay: int = 0
    
    decay_detected: bool = False
    decay_detection_date: Optional[datetime] = None
    
    regime_mismatch_detected: bool = False
    
    auto_retirement_triggered: bool = False
    retirement_date: Optional[datetime] = None
    retirement_reason: str = ""
    
    replacement_family_id: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            "family_id": self.family_id,
            "deployment_date": self.deployment_date.isoformat(),
            "expected_decay_date": self.expected_decay_date.isoformat(),
            "initial_sharpe": self.initial_sharpe,
            "current_sharpe": self.current_sharpe,
            "sharpe_decay_rate": self.sharpe_decay_rate,
            "initial_capacity": self.initial_capacity,
            "current_capacity": self.current_capacity,
            "days_deployed": self.days_deployed,
            "days_until_expected_decay": self.days_until_expected_decay,
            "decay_detected": self.decay_detected,
            "decay_detection_date": self.decay_detection_date.isoformat() if self.decay_detection_date else None,
            "regime_mismatch_detected": self.regime_mismatch_detected,
            "auto_retirement_triggered": self.auto_retirement_triggered,
            "retirement_date": self.retirement_date.isoformat() if self.retirement_date else None,
            "retirement_reason": self.retirement_reason,
            "replacement_family_id": self.replacement_family_id
        }


@dataclass
class WeaknessDetection:
    """Detected weakness in live performance"""
    detection_id: str
    family_id: str
    
    category: WeaknessCategory
    severity: str  # low, medium, high, critical
    
    description: str
    root_cause: str
    
    metrics_at_detection: Dict[str, float]
    
    new_hypothesis_generated: bool = False
    new_hypothesis_id: Optional[str] = None
    
    detected_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict:
        return {
            "detection_id": self.detection_id,
            "family_id": self.family_id,
            "category": self.category.value,
            "severity": self.severity,
            "description": self.description,
            "root_cause": self.root_cause,
            "metrics_at_detection": self.metrics_at_detection,
            "new_hypothesis_generated": self.new_hypothesis_generated,
            "new_hypothesis_id": self.new_hypothesis_id,
            "detected_at": self.detected_at.isoformat()
        }


@dataclass
class ResearchObject:
    """
    Structured representation of academic research.
    
    This is the primary output format for every paper processed by RDAOS.
    """
    paper_id: str
    
    # Metadata
    title: str
    authors: List[str]
    source: str  # arXiv, SSRN, NBER, etc.
    url: str
    publication_date: Optional[datetime] = None
    
    # Alpha characteristics
    alpha_source: str = ""
    horizon: AlphaHorizon = AlphaHorizon.DAILY
    asset_class: AssetClass = AssetClass.MULTI_ASSET
    
    # Requirements
    required_data: List[str] = field(default_factory=list)
    
    # Assumptions and constraints
    assumptions: List[str] = field(default_factory=list)
    failure_modes: List[FailureMode] = field(default_factory=list)
    
    # Decay and capacity
    expected_decay: str = ""
    expected_decay_days: int = 0
    capacity_limit: str = ""
    capacity_limit_usd: float = 0.0
    
    # Key equations
    key_equations: Dict[str, str] = field(default_factory=dict)
    key_variables: Dict[str, str] = field(default_factory=dict)
    
    # Extracted content
    hypotheses: List[Hypothesis] = field(default_factory=list)
    feature_families: List[FeatureFamily] = field(default_factory=list)
    
    # Testing
    testing_results: Dict[str, TestingResult] = field(default_factory=dict)
    
    # Status
    production_status: ProductionStatus = ProductionStatus.CANDIDATE
    rejection_reason: str = ""
    
    # Timestamps
    ingested_at: datetime = field(default_factory=datetime.utcnow)
    last_updated: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary format as specified in output format"""
        return {
            "paper_id": self.paper_id,
            "title": self.title,
            "authors": self.authors,
            "source": self.source,
            "url": self.url,
            "publication_date": self.publication_date.isoformat() if self.publication_date else None,
            "alpha_source": self.alpha_source,
            "horizon": self.horizon.value,
            "asset_class": self.asset_class.value,
            "required_data": self.required_data,
            "assumptions": self.assumptions,
            "failure_modes": [f.value for f in self.failure_modes],
            "expected_decay": self.expected_decay,
            "capacity_limit": self.capacity_limit,
            "hypotheses": [h.to_dict() for h in self.hypotheses],
            "feature_families": [f.to_dict() for f in self.feature_families],
            "testing_results": {k: v.to_dict() for k, v in self.testing_results.items()},
            "production_status": self.production_status.value
        }
    
    def generate_hash(self) -> str:
        """Generate unique hash for this research object"""
        try:
            content = json.dumps({
                "title": self.title,
                "authors": self.authors,
                "source": self.source
            }, sort_keys=True)
            return hashlib.sha256(content.encode()).hexdigest()[:16]
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in generate_hash: {e}")
            raise


@dataclass
class HardLimits:
    """
    Immutable hard limits for the RDAOS system.
    
    These limits CANNOT be overridden by any component.
    """
    # Cost constraints
    MIN_SHARPE_AFTER_COSTS: float = 0.5
    MAX_TRANSACTION_COST_BPS: float = 50.0  # 50 bps
    MAX_SLIPPAGE_BPS: float = 30.0  # 30 bps
    MAX_MARKET_IMPACT_BPS: float = 20.0  # 20 bps
    
    # Capacity constraints
    MIN_CAPACITY_USD: float = 1_000_000.0  # $1M minimum
    MAX_POSITION_PCT_ADV: float = 5.0  # 5% of average daily volume
    
    # Risk constraints
    MAX_DRAWDOWN_PCT: float = 20.0  # 20% max drawdown
    MAX_LEVERAGE: float = 3.0
    MAX_CORRELATION_WITH_EXISTING: float = 0.7
    
    # Testing constraints
    MIN_OOS_PERIODS: int = 3
    MIN_REGIME_COVERAGE: int = 4  # Must work in at least 4 regimes
    MIN_PARAMETER_STABILITY: float = 0.7
    
    # Decay constraints
    MAX_SHARPE_DECAY_RATE: float = 0.01  # 1% per day
    AUTO_RETIRE_SHARPE_THRESHOLD: float = 0.3
    
    # Execution constraints
    MAX_LATENCY_MS: float = 100.0
    MIN_FILL_RATE: float = 0.95
    
    def validate_feature(self, metrics: TestingMetrics) -> Tuple[bool, List[str]]:
        """Validate a feature against hard limits"""
        try:
            violations = []
        
            if metrics.sharpe_ratio < self.MIN_SHARPE_AFTER_COSTS:
                violations.append(f"Sharpe {metrics.sharpe_ratio:.2f} < min {self.MIN_SHARPE_AFTER_COSTS}")
        
            if metrics.transaction_costs > self.MAX_TRANSACTION_COST_BPS:
                violations.append(f"Transaction costs {metrics.transaction_costs:.1f}bps > max {self.MAX_TRANSACTION_COST_BPS}bps")
        
            if metrics.slippage > self.MAX_SLIPPAGE_BPS:
                violations.append(f"Slippage {metrics.slippage:.1f}bps > max {self.MAX_SLIPPAGE_BPS}bps")
        
            if metrics.market_impact > self.MAX_MARKET_IMPACT_BPS:
                violations.append(f"Market impact {metrics.market_impact:.1f}bps > max {self.MAX_MARKET_IMPACT_BPS}bps")
        
            if metrics.max_drawdown > self.MAX_DRAWDOWN_PCT:
                violations.append(f"Max drawdown {metrics.max_drawdown:.1f}% > max {self.MAX_DRAWDOWN_PCT}%")
        
            return len(violations) == 0, violations
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in validate_feature: {e}")
            raise


# Global hard limits instance
HARD_LIMITS = HardLimits()


def generate_id(prefix: str = "") -> str:
    """Generate a unique ID with optional prefix"""
    try:
        uid = str(uuid.uuid4())[:8]
        return f"{prefix}_{uid}" if prefix else uid
    except Exception as e:
        import logging as _log
        _log.getLogger(__name__).error(f"Error in generate_id: {e}")
        raise
