"""
Multi-Factor Confirmation Matrix - Elite Signal Validation

Implements the institutional-grade multi-factor confirmation system
from the Elite Professional Trading AI System Prompt.

Features:
- 10+ weighted validation factors
- Dynamic weight adjustment based on market regime
- Minimum threshold enforcement
- Factor contribution breakdown
- Real-time scoring (0-100 per factor)
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
from collections import deque

logger = logging.getLogger(__name__)


class ConfirmationFactor(Enum):
    """All confirmation factors in the matrix"""
    # Technical Factors
    PRICE_ACTION = "price_action"
    VOLUME_CONFIRMATION = "volume_confirmation"
    MARKET_STRUCTURE = "market_structure"
    MULTI_TIMEFRAME = "multi_timeframe"
    INDICATOR_ALIGNMENT = "indicator_alignment"
    
    # Order Flow Factors
    ORDER_FLOW_IMBALANCE = "order_flow_imbalance"
    INSTITUTIONAL_FOOTPRINT = "institutional_footprint"
    LIQUIDITY_ANALYSIS = "liquidity_analysis"
    
    # Context Factors
    MARKET_REGIME = "market_regime"
    VOLATILITY_ENVIRONMENT = "volatility_environment"
    CORRELATION_ALIGNMENT = "correlation_alignment"
    
    # Psychology Factors
    SENTIMENT_ALIGNMENT = "sentiment_alignment"
    SMART_MONEY_POSITIONING = "smart_money_positioning"
    
    # Risk Factors
    RISK_REWARD_RATIO = "risk_reward_ratio"
    PATTERN_RELIABILITY = "pattern_reliability"
    EXECUTION_PROBABILITY = "execution_probability"


class MarketRegime(Enum):
    """Market regime classifications"""
    TRENDING_BULLISH = "trending_bullish"
    TRENDING_BEARISH = "trending_bearish"
    RANGING = "ranging"
    HIGH_VOLATILITY = "high_volatility"
    LOW_VOLATILITY = "low_volatility"
    TRANSITIONAL = "transitional"
    CRISIS = "crisis"


@dataclass
class FactorScore:
    """Individual factor score with metadata"""
    factor: ConfirmationFactor
    raw_score: float  # 0-100
    weight: float  # 0-1
    weighted_score: float  # raw_score * weight
    confidence: float  # 0-1
    reasoning: str
    sub_factors: Dict[str, float] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'factor': self.factor.value,
            'raw_score': self.raw_score,
            'weight': self.weight,
            'weighted_score': self.weighted_score,
            'confidence': self.confidence,
            'reasoning': self.reasoning,
            'sub_factors': self.sub_factors,
            'timestamp': self.timestamp.isoformat()
        }


@dataclass
class ConfirmationResult:
    """Complete confirmation matrix result"""
    result_id: str
    symbol: str
    direction: str  # LONG, SHORT, NEUTRAL
    
    # Scores
    total_score: float  # 0-100
    factor_scores: List[FactorScore]
    
    # Thresholds
    minimum_threshold: float
    passed_threshold: bool
    
    # Analysis
    strongest_factors: List[str]
    weakest_factors: List[str]
    warnings: List[str]
    
    # Recommendation
    recommendation: str  # STRONG_BUY, BUY, HOLD, SELL, STRONG_SELL
    confidence: float
    reasoning_summary: str
    
    # Meta
    regime: MarketRegime
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'result_id': self.result_id,
            'symbol': self.symbol,
            'direction': self.direction,
            'total_score': self.total_score,
            'factor_scores': [f.to_dict() for f in self.factor_scores],
            'minimum_threshold': self.minimum_threshold,
            'passed_threshold': self.passed_threshold,
            'strongest_factors': self.strongest_factors,
            'weakest_factors': self.weakest_factors,
            'warnings': self.warnings,
            'recommendation': self.recommendation,
            'confidence': self.confidence,
            'reasoning_summary': self.reasoning_summary,
            'regime': self.regime.value,
            'timestamp': self.timestamp.isoformat()
        }


class MultiFactorConfirmationMatrix:
    """
    Elite Multi-Factor Confirmation Matrix
    
    Combines 16 validation factors with dynamic weighting
    based on market regime for institutional-grade signal confirmation.
    """
    
    # Default weights for each factor (sum to 1.0)
    DEFAULT_WEIGHTS = {
        ConfirmationFactor.PRICE_ACTION: 0.10,
        ConfirmationFactor.VOLUME_CONFIRMATION: 0.08,
        ConfirmationFactor.MARKET_STRUCTURE: 0.10,
        ConfirmationFactor.MULTI_TIMEFRAME: 0.08,
        ConfirmationFactor.INDICATOR_ALIGNMENT: 0.05,
        ConfirmationFactor.ORDER_FLOW_IMBALANCE: 0.10,
        ConfirmationFactor.INSTITUTIONAL_FOOTPRINT: 0.08,
        ConfirmationFactor.LIQUIDITY_ANALYSIS: 0.08,
        ConfirmationFactor.MARKET_REGIME: 0.06,
        ConfirmationFactor.VOLATILITY_ENVIRONMENT: 0.05,
        ConfirmationFactor.CORRELATION_ALIGNMENT: 0.04,
        ConfirmationFactor.SENTIMENT_ALIGNMENT: 0.04,
        ConfirmationFactor.SMART_MONEY_POSITIONING: 0.06,
        ConfirmationFactor.RISK_REWARD_RATIO: 0.04,
        ConfirmationFactor.PATTERN_RELIABILITY: 0.02,
        ConfirmationFactor.EXECUTION_PROBABILITY: 0.02,
    }
    
    # Regime-specific weight adjustments
    REGIME_WEIGHT_ADJUSTMENTS = {
        MarketRegime.TRENDING_BULLISH: {
            ConfirmationFactor.MARKET_STRUCTURE: 1.3,
            ConfirmationFactor.MULTI_TIMEFRAME: 1.2,
            ConfirmationFactor.INDICATOR_ALIGNMENT: 1.2,
        },
        MarketRegime.TRENDING_BEARISH: {
            ConfirmationFactor.MARKET_STRUCTURE: 1.3,
            ConfirmationFactor.MULTI_TIMEFRAME: 1.2,
            ConfirmationFactor.INDICATOR_ALIGNMENT: 1.2,
        },
        MarketRegime.RANGING: {
            ConfirmationFactor.LIQUIDITY_ANALYSIS: 1.4,
            ConfirmationFactor.ORDER_FLOW_IMBALANCE: 1.3,
            ConfirmationFactor.PRICE_ACTION: 1.2,
        },
        MarketRegime.HIGH_VOLATILITY: {
            ConfirmationFactor.VOLATILITY_ENVIRONMENT: 1.5,
            ConfirmationFactor.RISK_REWARD_RATIO: 1.4,
            ConfirmationFactor.EXECUTION_PROBABILITY: 1.3,
        },
        MarketRegime.LOW_VOLATILITY: {
            ConfirmationFactor.ORDER_FLOW_IMBALANCE: 1.3,
            ConfirmationFactor.INSTITUTIONAL_FOOTPRINT: 1.3,
            ConfirmationFactor.SMART_MONEY_POSITIONING: 1.2,
        },
        MarketRegime.TRANSITIONAL: {
            ConfirmationFactor.MARKET_REGIME: 1.5,
            ConfirmationFactor.CORRELATION_ALIGNMENT: 1.3,
            ConfirmationFactor.SENTIMENT_ALIGNMENT: 1.2,
        },
        MarketRegime.CRISIS: {
            ConfirmationFactor.VOLATILITY_ENVIRONMENT: 1.6,
            ConfirmationFactor.RISK_REWARD_RATIO: 1.5,
            ConfirmationFactor.EXECUTION_PROBABILITY: 1.4,
            ConfirmationFactor.LIQUIDITY_ANALYSIS: 1.3,
        },
    }
    
    # Minimum thresholds by regime
    REGIME_THRESHOLDS = {
        MarketRegime.TRENDING_BULLISH: 65.0,
        MarketRegime.TRENDING_BEARISH: 65.0,
        MarketRegime.RANGING: 70.0,
        MarketRegime.HIGH_VOLATILITY: 75.0,
        MarketRegime.LOW_VOLATILITY: 60.0,
        MarketRegime.TRANSITIONAL: 72.0,
        MarketRegime.CRISIS: 85.0,
    }
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Custom weights override
        self.weights = self.config.get('weights', self.DEFAULT_WEIGHTS.copy())
        
        # Minimum individual factor scores
        self.min_factor_scores = self.config.get('min_factor_scores', {
            ConfirmationFactor.RISK_REWARD_RATIO: 50.0,
            ConfirmationFactor.MARKET_STRUCTURE: 40.0,
            ConfirmationFactor.LIQUIDITY_ANALYSIS: 40.0,
        })
        
        # History for learning
        self.result_history: deque = deque(maxlen=1000)
        
        # Factor analyzers (to be connected to existing modules)
        self._analyzers: Dict[ConfirmationFactor, Any] = {}
        
        logger.info("MultiFactorConfirmationMatrix initialized")
    
    def get_regime_adjusted_weights(
        self,
        regime: MarketRegime
    ) -> Dict[ConfirmationFactor, float]:
        """Get weights adjusted for current market regime"""
        adjusted = self.weights.copy()
        
        if regime in self.REGIME_WEIGHT_ADJUSTMENTS:
            adjustments = self.REGIME_WEIGHT_ADJUSTMENTS[regime]
            for factor, multiplier in adjustments.items():
                if factor in adjusted:
                    adjusted[factor] *= multiplier
        
        # Normalize to sum to 1.0
        total = sum(adjusted.values())
        return {k: v / total for k, v in adjusted.items()}
    
    def calculate_factor_score(
        self,
        factor: ConfirmationFactor,
        market_data: Dict[str, Any],
        analysis_results: Dict[str, Any]
    ) -> FactorScore:
        """Calculate score for a single factor"""
        
        # Default implementation - override with actual analyzers
        score = 50.0
        confidence = 0.5
        reasoning = "Default score"
        sub_factors = {}
        
        if factor == ConfirmationFactor.PRICE_ACTION:
            score, confidence, reasoning, sub_factors = self._analyze_price_action(
                market_data, analysis_results
            )
        elif factor == ConfirmationFactor.VOLUME_CONFIRMATION:
            score, confidence, reasoning, sub_factors = self._analyze_volume(
                market_data, analysis_results
            )
        elif factor == ConfirmationFactor.MARKET_STRUCTURE:
            score, confidence, reasoning, sub_factors = self._analyze_market_structure(
                market_data, analysis_results
            )
        elif factor == ConfirmationFactor.MULTI_TIMEFRAME:
            score, confidence, reasoning, sub_factors = self._analyze_multi_timeframe(
                market_data, analysis_results
            )
        elif factor == ConfirmationFactor.INDICATOR_ALIGNMENT:
            score, confidence, reasoning, sub_factors = self._analyze_indicators(
                market_data, analysis_results
            )
        elif factor == ConfirmationFactor.ORDER_FLOW_IMBALANCE:
            score, confidence, reasoning, sub_factors = self._analyze_order_flow(
                market_data, analysis_results
            )
        elif factor == ConfirmationFactor.INSTITUTIONAL_FOOTPRINT:
            score, confidence, reasoning, sub_factors = self._analyze_institutional(
                market_data, analysis_results
            )
        elif factor == ConfirmationFactor.LIQUIDITY_ANALYSIS:
            score, confidence, reasoning, sub_factors = self._analyze_liquidity(
                market_data, analysis_results
            )
        elif factor == ConfirmationFactor.MARKET_REGIME:
            score, confidence, reasoning, sub_factors = self._analyze_regime(
                market_data, analysis_results
            )
        elif factor == ConfirmationFactor.VOLATILITY_ENVIRONMENT:
            score, confidence, reasoning, sub_factors = self._analyze_volatility(
                market_data, analysis_results
            )
        elif factor == ConfirmationFactor.CORRELATION_ALIGNMENT:
            score, confidence, reasoning, sub_factors = self._analyze_correlations(
                market_data, analysis_results
            )
        elif factor == ConfirmationFactor.SENTIMENT_ALIGNMENT:
            score, confidence, reasoning, sub_factors = self._analyze_sentiment(
                market_data, analysis_results
            )
        elif factor == ConfirmationFactor.SMART_MONEY_POSITIONING:
            score, confidence, reasoning, sub_factors = self._analyze_smart_money(
                market_data, analysis_results
            )
        elif factor == ConfirmationFactor.RISK_REWARD_RATIO:
            score, confidence, reasoning, sub_factors = self._analyze_risk_reward(
                market_data, analysis_results
            )
        elif factor == ConfirmationFactor.PATTERN_RELIABILITY:
            score, confidence, reasoning, sub_factors = self._analyze_pattern_reliability(
                market_data, analysis_results
            )
        elif factor == ConfirmationFactor.EXECUTION_PROBABILITY:
            score, confidence, reasoning, sub_factors = self._analyze_execution_probability(
                market_data, analysis_results
            )
        
        return FactorScore(
            factor=factor,
            raw_score=score,
            weight=0.0,  # Will be set later with regime adjustment
            weighted_score=0.0,
            confidence=confidence,
            reasoning=reasoning,
            sub_factors=sub_factors
        )
    
    def evaluate(
        self,
        symbol: str,
        direction: str,
        market_data: Dict[str, Any],
        analysis_results: Dict[str, Any],
        regime: Optional[MarketRegime] = None
    ) -> ConfirmationResult:
        """
        Evaluate all factors and produce confirmation result
        
        Args:
            symbol: Trading symbol
            direction: LONG, SHORT, or NEUTRAL
            market_data: Current market data
            analysis_results: Results from other analysis modules
            regime: Current market regime (auto-detected if None)
        
        Returns:
            ConfirmationResult with complete analysis
        """
        import uuid
        result_id = str(uuid.uuid4())[:8]
        
        # Auto-detect regime if not provided
        if regime is None:
            regime = self._detect_regime(market_data, analysis_results)
        
        # Get regime-adjusted weights
        weights = self.get_regime_adjusted_weights(regime)
        
        # Calculate all factor scores
        factor_scores: List[FactorScore] = []
        warnings: List[str] = []
        
        for factor in ConfirmationFactor:
            try:
                score = self.calculate_factor_score(factor, market_data, analysis_results)
                score.weight = weights.get(factor, 0.0)
                score.weighted_score = score.raw_score * score.weight
                factor_scores.append(score)
                
                # Check minimum thresholds
                if factor in self.min_factor_scores:
                    if score.raw_score < self.min_factor_scores[factor]:
                        warnings.append(
                            f"{factor.value} below minimum: {score.raw_score:.1f} < {self.min_factor_scores[factor]}"
                        )
            except Exception as e:
                logger.error(f"Error calculating {factor.value}: {e}")
                # Add default score on error
                factor_scores.append(FactorScore(
                    factor=factor,
                    raw_score=50.0,
                    weight=weights.get(factor, 0.0),
                    weighted_score=50.0 * weights.get(factor, 0.0),
                    confidence=0.0,
                    reasoning=f"Error: {str(e)}"
                ))
        
        # Calculate total score
        total_score = sum(fs.weighted_score for fs in factor_scores) * 100
        
        # Get threshold for regime
        threshold = self.REGIME_THRESHOLDS.get(regime, 70.0)
        passed = total_score >= threshold
        
        # Identify strongest and weakest factors
        sorted_factors = sorted(factor_scores, key=lambda x: x.raw_score, reverse=True)
        strongest = [f.factor.value for f in sorted_factors[:3]]
        weakest = [f.factor.value for f in sorted_factors[-3:]]
        
        # Generate recommendation
        recommendation, confidence = self._generate_recommendation(
            total_score, threshold, direction, warnings
        )
        
        # Generate reasoning summary
        reasoning_summary = self._generate_reasoning_summary(
            total_score, threshold, strongest, weakest, regime, direction
        )
        
        result = ConfirmationResult(
            result_id=result_id,
            symbol=symbol,
            direction=direction,
            total_score=total_score,
            factor_scores=factor_scores,
            minimum_threshold=threshold,
            passed_threshold=passed,
            strongest_factors=strongest,
            weakest_factors=weakest,
            warnings=warnings,
            recommendation=recommendation,
            confidence=confidence,
            reasoning_summary=reasoning_summary,
            regime=regime
        )
        
        # Store in history
        self.result_history.append(result)
        
        logger.info(
            f"Confirmation result for {symbol} {direction}: "
            f"Score={total_score:.1f}, Threshold={threshold}, "
            f"Passed={passed}, Recommendation={recommendation}"
        )
        
        return result
    
    # ==================== Factor Analysis Methods ====================
    
    def _analyze_price_action(
        self,
        market_data: Dict[str, Any],
        analysis_results: Dict[str, Any]
    ) -> Tuple[float, float, str, Dict[str, float]]:
        """Analyze price action patterns"""
        sub_factors = {}
        
        # Candlestick patterns
        candle_score = analysis_results.get('candlestick_score', 50.0)
        sub_factors['candlestick_patterns'] = candle_score
        
        # Support/resistance proximity
        sr_score = analysis_results.get('sr_proximity_score', 50.0)
        sub_factors['sr_proximity'] = sr_score
        
        # Trend alignment
        trend_score = analysis_results.get('trend_alignment_score', 50.0)
        sub_factors['trend_alignment'] = trend_score
        
        # Momentum
        momentum_score = analysis_results.get('momentum_score', 50.0)
        sub_factors['momentum'] = momentum_score
        
        # Calculate weighted average
        weights = [0.3, 0.25, 0.25, 0.2]
        scores = [candle_score, sr_score, trend_score, momentum_score]
        score = sum(w * s for w, s in zip(weights, scores))
        
        confidence = min(1.0, sum(1 for s in scores if s > 0) / len(scores))
        
        reasoning = f"Price action: Candles={candle_score:.0f}, S/R={sr_score:.0f}, Trend={trend_score:.0f}"
        
        return score, confidence, reasoning, sub_factors
    
    def _analyze_volume(
        self,
        market_data: Dict[str, Any],
        analysis_results: Dict[str, Any]
    ) -> Tuple[float, float, str, Dict[str, float]]:
        """Analyze volume confirmation"""
        sub_factors = {}
        
        # Volume vs average
        vol_ratio = analysis_results.get('volume_ratio', 1.0)
        vol_score = min(100, max(0, 50 + (vol_ratio - 1) * 50))
        sub_factors['volume_ratio'] = vol_score
        
        # Volume trend
        vol_trend = analysis_results.get('volume_trend_score', 50.0)
        sub_factors['volume_trend'] = vol_trend
        
        # Volume profile alignment
        vp_score = analysis_results.get('volume_profile_score', 50.0)
        sub_factors['volume_profile'] = vp_score
        
        score = (vol_score * 0.4 + vol_trend * 0.3 + vp_score * 0.3)
        confidence = 0.7 if vol_ratio > 0 else 0.3
        
        reasoning = f"Volume: Ratio={vol_ratio:.2f}x, Trend={vol_trend:.0f}, Profile={vp_score:.0f}"
        
        return score, confidence, reasoning, sub_factors
    
    def _analyze_market_structure(
        self,
        market_data: Dict[str, Any],
        analysis_results: Dict[str, Any]
    ) -> Tuple[float, float, str, Dict[str, float]]:
        """Analyze market structure"""
        sub_factors = {}
        
        # BOS/CHoCH
        structure_score = analysis_results.get('structure_score', 50.0)
        sub_factors['structure_breaks'] = structure_score
        
        # Swing structure
        swing_score = analysis_results.get('swing_structure_score', 50.0)
        sub_factors['swing_structure'] = swing_score
        
        # Order blocks
        ob_score = analysis_results.get('order_block_score', 50.0)
        sub_factors['order_blocks'] = ob_score
        
        score = (structure_score * 0.4 + swing_score * 0.3 + ob_score * 0.3)
        confidence = 0.8 if structure_score > 60 else 0.5
        
        reasoning = f"Structure: BOS/CHoCH={structure_score:.0f}, Swing={swing_score:.0f}, OB={ob_score:.0f}"
        
        return score, confidence, reasoning, sub_factors
    
    def _analyze_multi_timeframe(
        self,
        market_data: Dict[str, Any],
        analysis_results: Dict[str, Any]
    ) -> Tuple[float, float, str, Dict[str, float]]:
        """Analyze multi-timeframe alignment"""
        sub_factors = {}
        
        # HTF alignment
        htf_score = analysis_results.get('htf_alignment_score', 50.0)
        sub_factors['htf_alignment'] = htf_score
        
        # LTF confirmation
        ltf_score = analysis_results.get('ltf_confirmation_score', 50.0)
        sub_factors['ltf_confirmation'] = ltf_score
        
        # Timeframe confluence
        confluence_score = analysis_results.get('tf_confluence_score', 50.0)
        sub_factors['tf_confluence'] = confluence_score
        
        score = (htf_score * 0.4 + ltf_score * 0.3 + confluence_score * 0.3)
        confidence = 0.9 if htf_score > 70 and ltf_score > 60 else 0.5
        
        reasoning = f"MTF: HTF={htf_score:.0f}, LTF={ltf_score:.0f}, Confluence={confluence_score:.0f}"
        
        return score, confidence, reasoning, sub_factors
    
    def _analyze_indicators(
        self,
        market_data: Dict[str, Any],
        analysis_results: Dict[str, Any]
    ) -> Tuple[float, float, str, Dict[str, float]]:
        """Analyze indicator alignment"""
        sub_factors = {}
        
        # RSI
        rsi_score = analysis_results.get('rsi_score', 50.0)
        sub_factors['rsi'] = rsi_score
        
        # MACD
        macd_score = analysis_results.get('macd_score', 50.0)
        sub_factors['macd'] = macd_score
        
        # Moving averages
        ma_score = analysis_results.get('ma_alignment_score', 50.0)
        sub_factors['moving_averages'] = ma_score
        
        score = (rsi_score * 0.35 + macd_score * 0.35 + ma_score * 0.3)
        confidence = 0.6
        
        reasoning = f"Indicators: RSI={rsi_score:.0f}, MACD={macd_score:.0f}, MA={ma_score:.0f}"
        
        return score, confidence, reasoning, sub_factors
    
    def _analyze_order_flow(
        self,
        market_data: Dict[str, Any],
        analysis_results: Dict[str, Any]
    ) -> Tuple[float, float, str, Dict[str, float]]:
        """Analyze order flow imbalances"""
        sub_factors = {}
        
        # Delta
        delta_score = analysis_results.get('delta_score', 50.0)
        sub_factors['delta'] = delta_score
        
        # Absorption
        absorption_score = analysis_results.get('absorption_score', 50.0)
        sub_factors['absorption'] = absorption_score
        
        # Imbalance
        imbalance_score = analysis_results.get('imbalance_score', 50.0)
        sub_factors['imbalance'] = imbalance_score
        
        score = (delta_score * 0.4 + absorption_score * 0.3 + imbalance_score * 0.3)
        confidence = 0.75
        
        reasoning = f"Order Flow: Delta={delta_score:.0f}, Absorption={absorption_score:.0f}"
        
        return score, confidence, reasoning, sub_factors
    
    def _analyze_institutional(
        self,
        market_data: Dict[str, Any],
        analysis_results: Dict[str, Any]
    ) -> Tuple[float, float, str, Dict[str, float]]:
        """Analyze institutional footprint"""
        sub_factors = {}
        
        # Institutional order blocks
        iob_score = analysis_results.get('institutional_ob_score', 50.0)
        sub_factors['institutional_ob'] = iob_score
        
        # Dark pool activity
        dp_score = analysis_results.get('dark_pool_score', 50.0)
        sub_factors['dark_pool'] = dp_score
        
        # Block trades
        block_score = analysis_results.get('block_trade_score', 50.0)
        sub_factors['block_trades'] = block_score
        
        score = (iob_score * 0.4 + dp_score * 0.35 + block_score * 0.25)
        confidence = 0.7
        
        reasoning = f"Institutional: OB={iob_score:.0f}, DarkPool={dp_score:.0f}, Blocks={block_score:.0f}"
        
        return score, confidence, reasoning, sub_factors
    
    def _analyze_liquidity(
        self,
        market_data: Dict[str, Any],
        analysis_results: Dict[str, Any]
    ) -> Tuple[float, float, str, Dict[str, float]]:
        """Analyze liquidity conditions"""
        sub_factors = {}
        
        # Liquidity pools
        pool_score = analysis_results.get('liquidity_pool_score', 50.0)
        sub_factors['liquidity_pools'] = pool_score
        
        # Spread analysis
        spread_score = analysis_results.get('spread_score', 50.0)
        sub_factors['spread'] = spread_score
        
        # Market depth
        depth_score = analysis_results.get('market_depth_score', 50.0)
        sub_factors['market_depth'] = depth_score
        
        score = (pool_score * 0.4 + spread_score * 0.3 + depth_score * 0.3)
        confidence = 0.8
        
        reasoning = f"Liquidity: Pools={pool_score:.0f}, Spread={spread_score:.0f}, Depth={depth_score:.0f}"
        
        return score, confidence, reasoning, sub_factors
    
    def _analyze_regime(
        self,
        market_data: Dict[str, Any],
        analysis_results: Dict[str, Any]
    ) -> Tuple[float, float, str, Dict[str, float]]:
        """Analyze market regime compatibility"""
        sub_factors = {}
        
        # Regime clarity
        clarity_score = analysis_results.get('regime_clarity_score', 50.0)
        sub_factors['regime_clarity'] = clarity_score
        
        # Strategy alignment
        alignment_score = analysis_results.get('strategy_regime_alignment', 50.0)
        sub_factors['strategy_alignment'] = alignment_score
        
        score = (clarity_score * 0.5 + alignment_score * 0.5)
        confidence = clarity_score / 100
        
        reasoning = f"Regime: Clarity={clarity_score:.0f}, Alignment={alignment_score:.0f}"
        
        return score, confidence, reasoning, sub_factors
    
    def _analyze_volatility(
        self,
        market_data: Dict[str, Any],
        analysis_results: Dict[str, Any]
    ) -> Tuple[float, float, str, Dict[str, float]]:
        """Analyze volatility environment"""
        sub_factors = {}
        
        # ATR percentile
        atr_score = analysis_results.get('atr_percentile_score', 50.0)
        sub_factors['atr_percentile'] = atr_score
        
        # Volatility regime
        vol_regime_score = analysis_results.get('volatility_regime_score', 50.0)
        sub_factors['volatility_regime'] = vol_regime_score
        
        # IV vs HV
        iv_hv_score = analysis_results.get('iv_hv_score', 50.0)
        sub_factors['iv_vs_hv'] = iv_hv_score
        
        score = (atr_score * 0.4 + vol_regime_score * 0.35 + iv_hv_score * 0.25)
        confidence = 0.7
        
        reasoning = f"Volatility: ATR={atr_score:.0f}, Regime={vol_regime_score:.0f}"
        
        return score, confidence, reasoning, sub_factors
    
    def _analyze_correlations(
        self,
        market_data: Dict[str, Any],
        analysis_results: Dict[str, Any]
    ) -> Tuple[float, float, str, Dict[str, float]]:
        """Analyze cross-asset correlations"""
        sub_factors = {}
        
        # Correlation alignment
        corr_score = analysis_results.get('correlation_alignment_score', 50.0)
        sub_factors['correlation_alignment'] = corr_score
        
        # Lead-lag signals
        lead_lag_score = analysis_results.get('lead_lag_score', 50.0)
        sub_factors['lead_lag'] = lead_lag_score
        
        score = (corr_score * 0.6 + lead_lag_score * 0.4)
        confidence = 0.6
        
        reasoning = f"Correlations: Alignment={corr_score:.0f}, Lead-Lag={lead_lag_score:.0f}"
        
        return score, confidence, reasoning, sub_factors
    
    def _analyze_sentiment(
        self,
        market_data: Dict[str, Any],
        analysis_results: Dict[str, Any]
    ) -> Tuple[float, float, str, Dict[str, float]]:
        """Analyze sentiment alignment"""
        sub_factors = {}
        
        # Social sentiment
        social_score = analysis_results.get('social_sentiment_score', 50.0)
        sub_factors['social_sentiment'] = social_score
        
        # News sentiment
        news_score = analysis_results.get('news_sentiment_score', 50.0)
        sub_factors['news_sentiment'] = news_score
        
        # Fear/Greed
        fg_score = analysis_results.get('fear_greed_score', 50.0)
        sub_factors['fear_greed'] = fg_score
        
        score = (social_score * 0.35 + news_score * 0.35 + fg_score * 0.3)
        confidence = 0.5
        
        reasoning = f"Sentiment: Social={social_score:.0f}, News={news_score:.0f}, F&G={fg_score:.0f}"
        
        return score, confidence, reasoning, sub_factors
    
    def _analyze_smart_money(
        self,
        market_data: Dict[str, Any],
        analysis_results: Dict[str, Any]
    ) -> Tuple[float, float, str, Dict[str, float]]:
        """Analyze smart money positioning"""
        sub_factors = {}
        
        # COT positioning
        cot_score = analysis_results.get('cot_score', 50.0)
        sub_factors['cot_positioning'] = cot_score
        
        # Options flow
        options_score = analysis_results.get('options_flow_score', 50.0)
        sub_factors['options_flow'] = options_score
        
        # Whale activity
        whale_score = analysis_results.get('whale_activity_score', 50.0)
        sub_factors['whale_activity'] = whale_score
        
        score = (cot_score * 0.35 + options_score * 0.35 + whale_score * 0.3)
        confidence = 0.65
        
        reasoning = f"Smart Money: COT={cot_score:.0f}, Options={options_score:.0f}, Whales={whale_score:.0f}"
        
        return score, confidence, reasoning, sub_factors
    
    def _analyze_risk_reward(
        self,
        market_data: Dict[str, Any],
        analysis_results: Dict[str, Any]
    ) -> Tuple[float, float, str, Dict[str, float]]:
        """Analyze risk-reward ratio"""
        sub_factors = {}
        
        # R:R ratio
        rr_ratio = analysis_results.get('risk_reward_ratio', 1.0)
        rr_score = min(100, max(0, (rr_ratio - 1) * 33 + 50))  # 1:1 = 50, 1:3 = 100
        sub_factors['rr_ratio'] = rr_score
        
        # Expected value
        ev_score = analysis_results.get('expected_value_score', 50.0)
        sub_factors['expected_value'] = ev_score
        
        score = (rr_score * 0.6 + ev_score * 0.4)
        confidence = 0.9 if rr_ratio >= 2 else 0.5
        
        reasoning = f"Risk/Reward: Ratio={rr_ratio:.1f}:1, EV Score={ev_score:.0f}"
        
        return score, confidence, reasoning, sub_factors
    
    def _analyze_pattern_reliability(
        self,
        market_data: Dict[str, Any],
        analysis_results: Dict[str, Any]
    ) -> Tuple[float, float, str, Dict[str, float]]:
        """Analyze pattern reliability"""
        sub_factors = {}
        
        # Historical win rate
        win_rate_score = analysis_results.get('pattern_win_rate_score', 50.0)
        sub_factors['historical_win_rate'] = win_rate_score
        
        # Pattern completion
        completion_score = analysis_results.get('pattern_completion_score', 50.0)
        sub_factors['pattern_completion'] = completion_score
        
        score = (win_rate_score * 0.6 + completion_score * 0.4)
        confidence = win_rate_score / 100
        
        reasoning = f"Pattern: WinRate={win_rate_score:.0f}, Completion={completion_score:.0f}"
        
        return score, confidence, reasoning, sub_factors
    
    def _analyze_execution_probability(
        self,
        market_data: Dict[str, Any],
        analysis_results: Dict[str, Any]
    ) -> Tuple[float, float, str, Dict[str, float]]:
        """Analyze execution probability"""
        sub_factors = {}
        
        # Fill probability
        fill_score = analysis_results.get('fill_probability_score', 50.0)
        sub_factors['fill_probability'] = fill_score
        
        # Slippage estimate
        slippage_score = analysis_results.get('slippage_score', 50.0)
        sub_factors['slippage_estimate'] = slippage_score
        
        # Market impact
        impact_score = analysis_results.get('market_impact_score', 50.0)
        sub_factors['market_impact'] = impact_score
        
        score = (fill_score * 0.4 + slippage_score * 0.35 + impact_score * 0.25)
        confidence = 0.7
        
        reasoning = f"Execution: Fill={fill_score:.0f}, Slippage={slippage_score:.0f}"
        
        return score, confidence, reasoning, sub_factors
    
    # ==================== Helper Methods ====================
    
    def _detect_regime(
        self,
        market_data: Dict[str, Any],
        analysis_results: Dict[str, Any]
    ) -> MarketRegime:
        """Auto-detect current market regime"""
        regime_str = analysis_results.get('market_regime', 'ranging')
        
        regime_map = {
            'trending_bullish': MarketRegime.TRENDING_BULLISH,
            'trending_bearish': MarketRegime.TRENDING_BEARISH,
            'bullish': MarketRegime.TRENDING_BULLISH,
            'bearish': MarketRegime.TRENDING_BEARISH,
            'ranging': MarketRegime.RANGING,
            'high_volatility': MarketRegime.HIGH_VOLATILITY,
            'low_volatility': MarketRegime.LOW_VOLATILITY,
            'transitional': MarketRegime.TRANSITIONAL,
            'crisis': MarketRegime.CRISIS,
        }
        
        return regime_map.get(regime_str.lower(), MarketRegime.RANGING)
    
    def _generate_recommendation(
        self,
        total_score: float,
        threshold: float,
        direction: str,
        warnings: List[str]
    ) -> Tuple[str, float]:
        """Generate trading recommendation"""
        
        # Adjust for warnings
        warning_penalty = len(warnings) * 5
        adjusted_score = total_score - warning_penalty
        
        if direction == "LONG":
            if adjusted_score >= 85:
                return "STRONG_BUY", 0.95
            elif adjusted_score >= threshold:
                return "BUY", 0.75
            elif adjusted_score >= threshold - 10:
                return "HOLD", 0.5
            else:
                return "AVOID", 0.3
        elif direction == "SHORT":
            if adjusted_score >= 85:
                return "STRONG_SELL", 0.95
            elif adjusted_score >= threshold:
                return "SELL", 0.75
            elif adjusted_score >= threshold - 10:
                return "HOLD", 0.5
            else:
                return "AVOID", 0.3
        else:
            return "HOLD", 0.5
    
    def _generate_reasoning_summary(
        self,
        total_score: float,
        threshold: float,
        strongest: List[str],
        weakest: List[str],
        regime: MarketRegime,
        direction: str
    ) -> str:
        """Generate human-readable reasoning summary"""
        
        status = "PASSED" if total_score >= threshold else "FAILED"
        
        summary = (
            f"{direction} signal {status} confirmation matrix. "
            f"Total score: {total_score:.1f}/100 (threshold: {threshold}). "
            f"Market regime: {regime.value}. "
            f"Strongest factors: {', '.join(strongest)}. "
            f"Weakest factors: {', '.join(weakest)}."
        )
        
        return summary
    
    def get_factor_breakdown(self, result: ConfirmationResult) -> Dict[str, Any]:
        """Get detailed factor breakdown for analysis"""
        breakdown = {
            'total_score': result.total_score,
            'threshold': result.minimum_threshold,
            'passed': result.passed_threshold,
            'factors': {}
        }
        
        for fs in result.factor_scores:
            breakdown['factors'][fs.factor.value] = {
                'raw_score': fs.raw_score,
                'weight': fs.weight,
                'weighted_score': fs.weighted_score,
                'confidence': fs.confidence,
                'sub_factors': fs.sub_factors
            }
        
        return breakdown


# Convenience function
def create_confirmation_matrix(config: Optional[Dict[str, Any]] = None) -> MultiFactorConfirmationMatrix:
    """Factory function to create confirmation matrix"""
    return MultiFactorConfirmationMatrix(config)
