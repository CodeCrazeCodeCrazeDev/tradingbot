"""
AlphaAlgo Institutional - Layer 1: Market Selection
====================================================

The Market Selection Layer is responsible for:
- Deciding which markets to trade
- Quantifying market selection criteria
- Assessing liquidity, inefficiency, and capacity
- Evaluating structural participants and data availability

This layer operates as the MARKET SELECTION COMMITTEE.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
import numpy as np
from collections import defaultdict

from .core_types import (
    MarketType, MarketState, MarketSelection, CommitteeType,
    CommitteeDecision, CommitteeVote, RiskLevel, SystemConstants
)

logger = logging.getLogger(__name__)


# =============================================================================
# MARKET CHARACTERISTICS
# =============================================================================

@dataclass
class MarketCharacteristics:
    """Quantitative characteristics of a market."""
    market_type: MarketType
    
    # Liquidity metrics
    avg_daily_volume: float = 0.0
    bid_ask_spread_bps: float = 0.0
    market_depth: float = 0.0
    volume_stability: float = 0.0  # Coefficient of variation
    
    # Inefficiency metrics
    autocorrelation: float = 0.0
    variance_ratio: float = 0.0
    hurst_exponent: float = 0.5
    information_ratio_potential: float = 0.0
    
    # Structural metrics
    retail_participation: float = 0.0
    institutional_participation: float = 0.0
    market_maker_presence: float = 0.0
    etf_flow_impact: float = 0.0
    
    # Data quality
    data_latency_ms: float = 0.0
    data_completeness: float = 0.0
    historical_depth_years: float = 0.0
    
    # Execution constraints
    trading_hours: float = 0.0  # Hours per day
    settlement_days: int = 0
    margin_requirements: float = 0.0
    regulatory_constraints: List[str] = field(default_factory=list)
    
    # Capacity
    max_capacity_usd: float = 0.0
    capacity_decay_rate: float = 0.0


@dataclass
class MarketScore:
    """Composite score for market selection."""
    market_type: MarketType
    liquidity_score: float = 0.0
    inefficiency_score: float = 0.0
    data_quality_score: float = 0.0
    execution_score: float = 0.0
    capacity_score: float = 0.0
    structural_score: float = 0.0
    composite_score: float = 0.0
    
    def compute_composite(self, weights: Dict[str, float] = None) -> float:
        """Compute weighted composite score."""
        if weights is None:
            weights = {
                'liquidity': 0.25,
                'inefficiency': 0.20,
                'data_quality': 0.15,
                'execution': 0.15,
                'capacity': 0.15,
                'structural': 0.10
            }
        
        self.composite_score = (
            weights['liquidity'] * self.liquidity_score +
            weights['inefficiency'] * self.inefficiency_score +
            weights['data_quality'] * self.data_quality_score +
            weights['execution'] * self.execution_score +
            weights['capacity'] * self.capacity_score +
            weights['structural'] * self.structural_score
        )
        return self.composite_score


# =============================================================================
# LIQUIDITY ANALYZER
# =============================================================================

class LiquidityAnalyzer:
    """Analyzes market liquidity characteristics."""
    
    def __init__(self):
        self.liquidity_thresholds = {
            'excellent': 0.8,
            'good': 0.6,
            'acceptable': 0.4,
            'poor': 0.2
        }
    
    def analyze(self, characteristics: MarketCharacteristics) -> Tuple[float, Dict[str, Any]]:
        """
        Analyze liquidity and return score with details.
        
        Returns:
            Tuple of (score 0-1, analysis details)
        """
        details = {}
        
        # Volume score (log-scaled)
        volume_score = min(1.0, np.log10(max(1, characteristics.avg_daily_volume)) / 12)
        details['volume_score'] = volume_score
        
        # Spread score (inverse relationship)
        spread_score = max(0, 1 - characteristics.bid_ask_spread_bps / 100)
        details['spread_score'] = spread_score
        
        # Depth score
        depth_score = min(1.0, characteristics.market_depth / 1e8)
        details['depth_score'] = depth_score
        
        # Stability score (lower CV is better)
        stability_score = max(0, 1 - characteristics.volume_stability)
        details['stability_score'] = stability_score
        
        # Composite liquidity score
        score = (
            0.35 * volume_score +
            0.30 * spread_score +
            0.20 * depth_score +
            0.15 * stability_score
        )
        
        details['composite'] = score
        details['rating'] = self._get_rating(score)
        
        return score, details
    
    def _get_rating(self, score: float) -> str:
        """Get liquidity rating from score."""
        if score >= self.liquidity_thresholds['excellent']:
            return 'excellent'
        elif score >= self.liquidity_thresholds['good']:
            return 'good'
        elif score >= self.liquidity_thresholds['acceptable']:
            return 'acceptable'
        elif score >= self.liquidity_thresholds['poor']:
            return 'poor'
        return 'insufficient'


# =============================================================================
# INEFFICIENCY ANALYZER
# =============================================================================

class InefficiencyAnalyzer:
    """Analyzes market inefficiency and alpha potential."""
    
    def __init__(self):
        self.min_inefficiency_threshold = 0.3
    
    def analyze(self, characteristics: MarketCharacteristics) -> Tuple[float, Dict[str, Any]]:
        """
        Analyze market inefficiency.
        
        Inefficiency sources:
        - Autocorrelation (momentum/mean-reversion)
        - Variance ratio deviations from 1
        - Hurst exponent deviations from 0.5
        - Information ratio potential
        """
        details = {}
        
        # Autocorrelation inefficiency (absolute value matters)
        autocorr_score = min(1.0, abs(characteristics.autocorrelation) * 5)
        details['autocorrelation_score'] = autocorr_score
        
        # Variance ratio inefficiency (deviation from 1)
        vr_deviation = abs(characteristics.variance_ratio - 1)
        vr_score = min(1.0, vr_deviation * 2)
        details['variance_ratio_score'] = vr_score
        
        # Hurst exponent inefficiency (deviation from 0.5)
        hurst_deviation = abs(characteristics.hurst_exponent - 0.5)
        hurst_score = min(1.0, hurst_deviation * 4)
        details['hurst_score'] = hurst_score
        
        # Information ratio potential
        ir_score = min(1.0, characteristics.information_ratio_potential)
        details['ir_potential_score'] = ir_score
        
        # Composite inefficiency score
        score = (
            0.25 * autocorr_score +
            0.25 * vr_score +
            0.25 * hurst_score +
            0.25 * ir_score
        )
        
        details['composite'] = score
        details['tradeable'] = score >= self.min_inefficiency_threshold
        details['inefficiency_type'] = self._classify_inefficiency(characteristics)
        
        return score, details
    
    def _classify_inefficiency(self, characteristics: MarketCharacteristics) -> str:
        """Classify the type of inefficiency present."""
        if characteristics.hurst_exponent > 0.55:
            return 'trending'
        elif characteristics.hurst_exponent < 0.45:
            return 'mean_reverting'
        elif abs(characteristics.autocorrelation) > 0.1:
            return 'autocorrelated'
        return 'mixed'


# =============================================================================
# STRUCTURAL ANALYZER
# =============================================================================

class StructuralAnalyzer:
    """Analyzes market structure and participant composition."""
    
    def analyze(self, characteristics: MarketCharacteristics) -> Tuple[float, Dict[str, Any]]:
        """
        Analyze market structure.
        
        Favorable structures:
        - High retail participation (potential inefficiency)
        - Moderate institutional presence (liquidity)
        - Active market makers (tight spreads)
        - Manageable ETF flows
        """
        details = {}
        
        # Retail participation (higher = more potential inefficiency)
        retail_score = characteristics.retail_participation
        details['retail_score'] = retail_score
        
        # Institutional balance (moderate is best)
        inst_score = 1 - abs(characteristics.institutional_participation - 0.5) * 2
        details['institutional_score'] = inst_score
        
        # Market maker presence (higher = better execution)
        mm_score = characteristics.market_maker_presence
        details['market_maker_score'] = mm_score
        
        # ETF flow impact (lower = less distortion)
        etf_score = max(0, 1 - characteristics.etf_flow_impact)
        details['etf_score'] = etf_score
        
        # Composite structural score
        score = (
            0.30 * retail_score +
            0.25 * inst_score +
            0.25 * mm_score +
            0.20 * etf_score
        )
        
        details['composite'] = score
        details['structure_type'] = self._classify_structure(characteristics)
        
        return score, details
    
    def _classify_structure(self, characteristics: MarketCharacteristics) -> str:
        """Classify market structure type."""
        if characteristics.retail_participation > 0.5:
            return 'retail_dominated'
        elif characteristics.institutional_participation > 0.7:
            return 'institutional_dominated'
        elif characteristics.market_maker_presence > 0.8:
            return 'market_maker_driven'
        return 'balanced'


# =============================================================================
# DATA QUALITY ANALYZER
# =============================================================================

class DataQualityAnalyzer:
    """Analyzes data availability and quality."""
    
    def analyze(self, characteristics: MarketCharacteristics) -> Tuple[float, Dict[str, Any]]:
        """Analyze data quality for quantitative research."""
        details = {}
        
        # Latency score (lower is better)
        latency_score = max(0, 1 - characteristics.data_latency_ms / 1000)
        details['latency_score'] = latency_score
        
        # Completeness score
        completeness_score = characteristics.data_completeness
        details['completeness_score'] = completeness_score
        
        # Historical depth score (log-scaled)
        depth_score = min(1.0, np.log10(max(1, characteristics.historical_depth_years * 252)) / 4)
        details['depth_score'] = depth_score
        
        # Composite data quality score
        score = (
            0.30 * latency_score +
            0.40 * completeness_score +
            0.30 * depth_score
        )
        
        details['composite'] = score
        details['sufficient_for_research'] = score >= 0.5
        
        return score, details


# =============================================================================
# EXECUTION FEASIBILITY ANALYZER
# =============================================================================

class ExecutionFeasibilityAnalyzer:
    """Analyzes execution constraints and feasibility."""
    
    def analyze(self, characteristics: MarketCharacteristics) -> Tuple[float, Dict[str, Any]]:
        """Analyze execution feasibility."""
        details = {}
        
        # Trading hours score (24h is best)
        hours_score = characteristics.trading_hours / 24
        details['hours_score'] = hours_score
        
        # Settlement score (T+0 is best)
        settlement_score = max(0, 1 - characteristics.settlement_days / 5)
        details['settlement_score'] = settlement_score
        
        # Margin requirements score (lower is better)
        margin_score = max(0, 1 - characteristics.margin_requirements)
        details['margin_score'] = margin_score
        
        # Regulatory constraints score
        reg_score = max(0, 1 - len(characteristics.regulatory_constraints) / 10)
        details['regulatory_score'] = reg_score
        
        # Composite execution score
        score = (
            0.25 * hours_score +
            0.25 * settlement_score +
            0.25 * margin_score +
            0.25 * reg_score
        )
        
        details['composite'] = score
        details['constraints'] = characteristics.regulatory_constraints
        
        return score, details


# =============================================================================
# CAPACITY ANALYZER
# =============================================================================

class CapacityAnalyzer:
    """Analyzes market capacity for capital deployment."""
    
    def __init__(self, target_capital: float = 1e8):
        self.target_capital = target_capital
    
    def analyze(self, characteristics: MarketCharacteristics) -> Tuple[float, Dict[str, Any]]:
        """Analyze capacity for target capital."""
        details = {}
        
        # Capacity ratio
        capacity_ratio = characteristics.max_capacity_usd / self.target_capital
        capacity_score = min(1.0, capacity_ratio)
        details['capacity_ratio'] = capacity_ratio
        details['capacity_score'] = capacity_score
        
        # Decay rate (lower is better)
        decay_score = max(0, 1 - characteristics.capacity_decay_rate * 10)
        details['decay_score'] = decay_score
        
        # Composite capacity score
        score = 0.7 * capacity_score + 0.3 * decay_score
        
        details['composite'] = score
        details['max_deployable'] = min(self.target_capital, characteristics.max_capacity_usd)
        details['sustainable'] = characteristics.capacity_decay_rate < 0.05
        
        return score, details


# =============================================================================
# MARKET SELECTION COMMITTEE
# =============================================================================

class MarketSelectionCommittee:
    """
    Internal committee responsible for market selection decisions.
    
    Decides:
    - Which markets to trade
    - Which markets to avoid
    
    Criteria:
    - Liquidity
    - Structural inefficiencies
    - Participant composition
    - Capacity constraints
    - Execution realism
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.committee_type = CommitteeType.MARKET_SELECTION
        
        # Initialize analyzers
        self.liquidity_analyzer = LiquidityAnalyzer()
        self.inefficiency_analyzer = InefficiencyAnalyzer()
        self.structural_analyzer = StructuralAnalyzer()
        self.data_quality_analyzer = DataQualityAnalyzer()
        self.execution_analyzer = ExecutionFeasibilityAnalyzer()
        self.capacity_analyzer = CapacityAnalyzer(
            target_capital=self.config.get('target_capital', 1e8)
        )
        
        # Selection thresholds
        self.min_composite_score = self.config.get('min_composite_score', 0.5)
        self.min_liquidity_score = self.config.get('min_liquidity_score', 0.4)
        self.min_data_quality = self.config.get('min_data_quality', 0.5)
        
        # Market database
        self.market_database: Dict[MarketType, MarketCharacteristics] = {}
        self.selection_history: List[MarketSelection] = []
        
        logger.info("MarketSelectionCommittee initialized")
    
    def register_market(self, characteristics: MarketCharacteristics):
        """Register a market with its characteristics."""
        self.market_database[characteristics.market_type] = characteristics
        logger.info(f"Registered market: {characteristics.market_type.value}")
    
    def evaluate_market(self, market_type: MarketType) -> Tuple[MarketScore, Dict[str, Any]]:
        """
        Evaluate a single market.
        
        Returns:
            Tuple of (MarketScore, detailed analysis)
        """
        if market_type not in self.market_database:
            raise ValueError(f"Market {market_type.value} not registered")
        
        characteristics = self.market_database[market_type]
        analysis = {}
        
        # Run all analyzers
        liquidity_score, liquidity_details = self.liquidity_analyzer.analyze(characteristics)
        analysis['liquidity'] = liquidity_details
        
        inefficiency_score, inefficiency_details = self.inefficiency_analyzer.analyze(characteristics)
        analysis['inefficiency'] = inefficiency_details
        
        structural_score, structural_details = self.structural_analyzer.analyze(characteristics)
        analysis['structural'] = structural_details
        
        data_score, data_details = self.data_quality_analyzer.analyze(characteristics)
        analysis['data_quality'] = data_details
        
        execution_score, execution_details = self.execution_analyzer.analyze(characteristics)
        analysis['execution'] = execution_details
        
        capacity_score, capacity_details = self.capacity_analyzer.analyze(characteristics)
        analysis['capacity'] = capacity_details
        
        # Create market score
        score = MarketScore(
            market_type=market_type,
            liquidity_score=liquidity_score,
            inefficiency_score=inefficiency_score,
            data_quality_score=data_score,
            execution_score=execution_score,
            capacity_score=capacity_score,
            structural_score=structural_score
        )
        score.compute_composite()
        
        return score, analysis
    
    def select_markets(self, 
                       available_markets: List[MarketType] = None,
                       max_markets: int = 5) -> List[MarketSelection]:
        """
        Select markets for trading.
        
        Args:
            available_markets: List of markets to consider (None = all registered)
            max_markets: Maximum number of markets to select
            
        Returns:
            List of MarketSelection decisions
        """
        if available_markets is None:
            available_markets = list(self.market_database.keys())
        
        selections = []
        evaluations = []
        
        # Evaluate all markets
        for market_type in available_markets:
            if market_type not in self.market_database:
                continue
            try:
            
                score, analysis = self.evaluate_market(market_type)
                evaluations.append((market_type, score, analysis))
            except Exception as e:
                logger.error(f"Error evaluating {market_type.value}: {e}")
        
        # Sort by composite score
        evaluations.sort(key=lambda x: x[1].composite_score, reverse=True)
        
        # Select top markets that meet criteria
        for market_type, score, analysis in evaluations:
            if len(selections) >= max_markets:
                break
            
            # Check minimum thresholds
            if score.composite_score < self.min_composite_score:
                logger.info(f"Rejecting {market_type.value}: composite score {score.composite_score:.2f} < {self.min_composite_score}")
                continue
            
            if score.liquidity_score < self.min_liquidity_score:
                logger.info(f"Rejecting {market_type.value}: liquidity score {score.liquidity_score:.2f} < {self.min_liquidity_score}")
                continue
            
            if score.data_quality_score < self.min_data_quality:
                logger.info(f"Rejecting {market_type.value}: data quality {score.data_quality_score:.2f} < {self.min_data_quality}")
                continue
            
            # Create selection
            characteristics = self.market_database[market_type]
            selection = MarketSelection(
                market_type=market_type,
                symbols=self._get_symbols_for_market(market_type),
                score=score.composite_score,
                liquidity_score=score.liquidity_score,
                inefficiency_score=score.inefficiency_score,
                data_quality_score=score.data_quality_score,
                execution_feasibility=score.execution_score,
                capacity_estimate=analysis['capacity']['max_deployable'],
                rationale=self._generate_rationale(market_type, score, analysis),
                constraints=analysis['execution'].get('constraints', [])
            )
            
            selections.append(selection)
            logger.info(f"Selected market: {market_type.value} (score: {score.composite_score:.2f})")
        
        # Store selection history
        self.selection_history.extend(selections)
        
        return selections
    
    def vote(self, market_type: MarketType) -> CommitteeVote:
        """
        Cast a committee vote on a market.
        
        Returns:
            CommitteeVote with decision and rationale
        """
        try:
            score, analysis = self.evaluate_market(market_type)
        except ValueError:
            return CommitteeVote(
                committee=self.committee_type,
                decision=CommitteeDecision.REJECT,
                confidence=1.0,
                rationale=f"Market {market_type.value} not registered"
            )
        
        # Determine decision
        if score.composite_score >= self.min_composite_score:
            decision = CommitteeDecision.APPROVE
            confidence = min(1.0, score.composite_score)
        elif score.composite_score >= self.min_composite_score * 0.8:
            decision = CommitteeDecision.CONDITIONAL
            confidence = score.composite_score
        else:
            decision = CommitteeDecision.REJECT
            confidence = 1 - score.composite_score
        
        # Generate conditions if conditional
        conditions = []
        if decision == CommitteeDecision.CONDITIONAL:
            if score.liquidity_score < self.min_liquidity_score:
                conditions.append("Improve liquidity monitoring")
            if score.data_quality_score < self.min_data_quality:
                conditions.append("Enhance data quality")
        
        # Note dissenting views
        dissenting = []
        if score.inefficiency_score < 0.3:
            dissenting.append("Low inefficiency - limited alpha potential")
        if score.capacity_score < 0.5:
            dissenting.append("Capacity constraints may limit scalability")
        
        return CommitteeVote(
            committee=self.committee_type,
            decision=decision,
            confidence=confidence,
            rationale=self._generate_rationale(market_type, score, analysis),
            conditions=conditions,
            dissenting_views=dissenting
        )
    
    def _get_symbols_for_market(self, market_type: MarketType) -> List[str]:
        """Get tradeable symbols for a market type."""
        symbol_map = {
            MarketType.EQUITY: ['SPY', 'QQQ', 'IWM', 'DIA', 'VTI'],
            MarketType.FX: ['EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD', 'USDCAD'],
            MarketType.CRYPTO: ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT', 'ADAUSDT'],
            MarketType.RATES: ['TLT', 'IEF', 'SHY', 'BND', 'GOVT'],
            MarketType.VOLATILITY: ['VXX', 'UVXY', 'SVXY', 'VIX'],
            MarketType.COMMODITIES: ['GLD', 'SLV', 'USO', 'UNG', 'DBA'],
            MarketType.CROSS_ASSET: ['SPY', 'TLT', 'GLD', 'EURUSD', 'BTCUSDT']
        }
        return symbol_map.get(market_type, [])
    
    def _generate_rationale(self, market_type: MarketType, 
                           score: MarketScore, 
                           analysis: Dict[str, Any]) -> str:
        """Generate selection rationale."""
        parts = [f"Market: {market_type.value}"]
        parts.append(f"Composite Score: {score.composite_score:.2f}")
        
        # Highlight strengths
        strengths = []
        if score.liquidity_score >= 0.7:
            strengths.append("excellent liquidity")
        if score.inefficiency_score >= 0.5:
            strengths.append(f"exploitable inefficiency ({analysis['inefficiency']['inefficiency_type']})")
        if score.data_quality_score >= 0.7:
            strengths.append("high-quality data")
        
        if strengths:
            parts.append(f"Strengths: {', '.join(strengths)}")
        
        # Note concerns
        concerns = []
        if score.liquidity_score < 0.5:
            concerns.append("liquidity constraints")
        if score.capacity_score < 0.5:
            concerns.append("limited capacity")
        if score.execution_score < 0.5:
            concerns.append("execution challenges")
        
        if concerns:
            parts.append(f"Concerns: {', '.join(concerns)}")
        
        return " | ".join(parts)


# =============================================================================
# MARKET SELECTION LAYER
# =============================================================================

class MarketSelectionLayer:
    """
    Layer 1: Market Selection Layer
    
    Responsible for:
    - Market universe definition
    - Quantitative market evaluation
    - Selection committee coordination
    - Market monitoring and re-evaluation
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.committee = MarketSelectionCommittee(self.config)
        
        # Layer state
        self.selected_markets: List[MarketSelection] = []
        self.rejected_markets: List[MarketType] = []
        self.last_evaluation: Optional[datetime] = None
        self.evaluation_frequency = timedelta(days=self.config.get('evaluation_frequency_days', 7))
        
        # Initialize default markets
        self._initialize_default_markets()
        
        logger.info("MarketSelectionLayer initialized")
    
    def _initialize_default_markets(self):
        """Initialize default market characteristics."""
        # Equity markets
        self.committee.register_market(MarketCharacteristics(
            market_type=MarketType.EQUITY,
            avg_daily_volume=5e11,
            bid_ask_spread_bps=1.0,
            market_depth=1e10,
            volume_stability=0.3,
            autocorrelation=0.02,
            variance_ratio=1.05,
            hurst_exponent=0.52,
            information_ratio_potential=0.4,
            retail_participation=0.25,
            institutional_participation=0.60,
            market_maker_presence=0.85,
            etf_flow_impact=0.15,
            data_latency_ms=10,
            data_completeness=0.99,
            historical_depth_years=30,
            trading_hours=6.5,
            settlement_days=2,
            margin_requirements=0.25,
            regulatory_constraints=['PDT', 'RegT'],
            max_capacity_usd=1e10,
            capacity_decay_rate=0.01
        ))
        
        # FX markets
        self.committee.register_market(MarketCharacteristics(
            market_type=MarketType.FX,
            avg_daily_volume=6.6e12,
            bid_ask_spread_bps=0.5,
            market_depth=1e11,
            volume_stability=0.2,
            autocorrelation=0.01,
            variance_ratio=1.02,
            hurst_exponent=0.48,
            information_ratio_potential=0.3,
            retail_participation=0.10,
            institutional_participation=0.75,
            market_maker_presence=0.95,
            etf_flow_impact=0.02,
            data_latency_ms=1,
            data_completeness=0.999,
            historical_depth_years=40,
            trading_hours=24,
            settlement_days=2,
            margin_requirements=0.02,
            regulatory_constraints=['CFTC'],
            max_capacity_usd=1e11,
            capacity_decay_rate=0.005
        ))
        
        # Crypto markets
        self.committee.register_market(MarketCharacteristics(
            market_type=MarketType.CRYPTO,
            avg_daily_volume=1e11,
            bid_ask_spread_bps=5.0,
            market_depth=1e8,
            volume_stability=0.6,
            autocorrelation=0.08,
            variance_ratio=1.15,
            hurst_exponent=0.58,
            information_ratio_potential=0.6,
            retail_participation=0.60,
            institutional_participation=0.25,
            market_maker_presence=0.70,
            etf_flow_impact=0.05,
            data_latency_ms=50,
            data_completeness=0.95,
            historical_depth_years=10,
            trading_hours=24,
            settlement_days=0,
            margin_requirements=0.10,
            regulatory_constraints=['Varies by jurisdiction'],
            max_capacity_usd=1e9,
            capacity_decay_rate=0.03
        ))
        
        # Rates markets
        self.committee.register_market(MarketCharacteristics(
            market_type=MarketType.RATES,
            avg_daily_volume=1e12,
            bid_ask_spread_bps=0.5,
            market_depth=1e10,
            volume_stability=0.25,
            autocorrelation=0.15,
            variance_ratio=1.08,
            hurst_exponent=0.55,
            information_ratio_potential=0.35,
            retail_participation=0.05,
            institutional_participation=0.85,
            market_maker_presence=0.90,
            etf_flow_impact=0.10,
            data_latency_ms=5,
            data_completeness=0.99,
            historical_depth_years=50,
            trading_hours=23,
            settlement_days=1,
            margin_requirements=0.02,
            regulatory_constraints=['FINRA', 'SEC'],
            max_capacity_usd=1e11,
            capacity_decay_rate=0.005
        ))
        
        # Volatility markets
        self.committee.register_market(MarketCharacteristics(
            market_type=MarketType.VOLATILITY,
            avg_daily_volume=1e9,
            bid_ask_spread_bps=10.0,
            market_depth=1e7,
            volume_stability=0.5,
            autocorrelation=0.20,
            variance_ratio=1.25,
            hurst_exponent=0.60,
            information_ratio_potential=0.5,
            retail_participation=0.30,
            institutional_participation=0.55,
            market_maker_presence=0.75,
            etf_flow_impact=0.20,
            data_latency_ms=20,
            data_completeness=0.98,
            historical_depth_years=15,
            trading_hours=6.5,
            settlement_days=1,
            margin_requirements=0.50,
            regulatory_constraints=['Complex product rules'],
            max_capacity_usd=5e8,
            capacity_decay_rate=0.05
        ))
        
        # Commodities markets
        self.committee.register_market(MarketCharacteristics(
            market_type=MarketType.COMMODITIES,
            avg_daily_volume=5e10,
            bid_ask_spread_bps=3.0,
            market_depth=1e9,
            volume_stability=0.35,
            autocorrelation=0.05,
            variance_ratio=1.10,
            hurst_exponent=0.53,
            information_ratio_potential=0.4,
            retail_participation=0.15,
            institutional_participation=0.70,
            market_maker_presence=0.80,
            etf_flow_impact=0.08,
            data_latency_ms=15,
            data_completeness=0.97,
            historical_depth_years=40,
            trading_hours=23,
            settlement_days=2,
            margin_requirements=0.10,
            regulatory_constraints=['CFTC', 'Position limits'],
            max_capacity_usd=5e9,
            capacity_decay_rate=0.02
        ))
    
    def run_selection(self, max_markets: int = 5) -> List[MarketSelection]:
        """
        Run market selection process.
        
        Returns:
            List of selected markets
        """
        logger.info("Running market selection process")
        
        self.selected_markets = self.committee.select_markets(max_markets=max_markets)
        self.last_evaluation = datetime.utcnow()
        
        # Track rejected markets
        all_markets = set(self.committee.market_database.keys())
        selected_types = {s.market_type for s in self.selected_markets}
        self.rejected_markets = list(all_markets - selected_types)
        
        logger.info(f"Selected {len(self.selected_markets)} markets, rejected {len(self.rejected_markets)}")
        
        return self.selected_markets
    
    def needs_reevaluation(self) -> bool:
        """Check if markets need re-evaluation."""
        if self.last_evaluation is None:
            return True
        return datetime.utcnow() - self.last_evaluation > self.evaluation_frequency
    
    def get_selected_markets(self) -> List[MarketSelection]:
        """Get currently selected markets."""
        return self.selected_markets
    
    def get_market_vote(self, market_type: MarketType) -> CommitteeVote:
        """Get committee vote for a specific market."""
        return self.committee.vote(market_type)
    
    def update_market_characteristics(self, characteristics: MarketCharacteristics):
        """Update characteristics for a market."""
        self.committee.register_market(characteristics)
        logger.info(f"Updated characteristics for {characteristics.market_type.value}")
    
    def get_layer_state(self) -> Dict[str, Any]:
        """Get current layer state."""
        return {
            'selected_markets': [
                {
                    'market': s.market_type.value,
                    'score': s.score,
                    'symbols': s.symbols,
                    'capacity': s.capacity_estimate
                }
                for s in self.selected_markets
            ],
            'rejected_markets': [m.value for m in self.rejected_markets],
            'last_evaluation': self.last_evaluation.isoformat() if self.last_evaluation else None,
            'needs_reevaluation': self.needs_reevaluation()
        }
