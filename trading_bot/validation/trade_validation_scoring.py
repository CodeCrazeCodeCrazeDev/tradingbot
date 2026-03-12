"""Real-Time Trade Validation Scoring System.

Implements comprehensive trade validation including:
- Technical validation score (0-100)
- Market condition score (0-100)
- Risk assessment score (0-100)
- Pattern reliability score (0-100)
- Execution probability score (0-100)
- Minimum threshold requirements
- Multi-factor confluence scoring
- Trade quality grading

This module provides standardized trade quality scoring
for consistent entry/exit decision making.
"""


from __future__ import annotations
import enum
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from loguru import logger
from enum import Enum
import numpy
import pandas

import logging
logger = logging.getLogger(__name__)



class ValidationResult(enum.Enum):
    """Validation result status."""
    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"
    INSUFFICIENT_DATA = "insufficient_data"


class TradeGrade(enum.Enum):
    """Trade quality grades."""
    A_PLUS = "A+"  # 90-100
    A = "A"  # 80-89
    B = "B"  # 70-79
    C = "C"  # 60-69
    D = "D"  # 50-59
    F = "F"  # Below 50


@dataclass
class TechnicalScore:
    """Technical validation score."""
    score: float  # 0-100
    trend_alignment: float
    momentum_score: float
    support_resistance_score: float
    pattern_score: float
    volume_confirmation: float
    multi_timeframe_score: float
    details: Dict[str, Any]


@dataclass
class MarketConditionScore:
    """Market condition score."""
    score: float  # 0-100
    regime_score: float
    volatility_score: float
    liquidity_score: float
    correlation_score: float
    news_impact_score: float
    session_score: float
    details: Dict[str, Any]


@dataclass
class RiskAssessmentScore:
    """Risk assessment score."""
    score: float  # 0-100
    position_size_score: float
    stop_loss_score: float
    risk_reward_score: float
    portfolio_risk_score: float
    drawdown_score: float
    correlation_risk_score: float
    details: Dict[str, Any]


@dataclass
class PatternReliabilityScore:
    """Pattern reliability score."""
    score: float  # 0-100
    pattern_type: str
    historical_win_rate: float
    current_strength: float
    confirmation_count: int
    invalidation_distance: float
    time_validity: float
    details: Dict[str, Any]


@dataclass
class ExecutionProbabilityScore:
    """Execution probability score."""
    score: float  # 0-100
    fill_probability: float
    slippage_estimate: float
    spread_score: float
    depth_score: float
    timing_score: float
    details: Dict[str, Any]


@dataclass
class ValidationScorecard:
    """Complete validation scorecard."""
    timestamp: datetime
    symbol: str
    direction: str
    
    # Individual scores
    technical_score: TechnicalScore
    market_condition_score: MarketConditionScore
    risk_assessment_score: RiskAssessmentScore
    pattern_reliability_score: PatternReliabilityScore
    execution_probability_score: ExecutionProbabilityScore
    
    # Aggregate
    total_score: float
    grade: TradeGrade
    validation_result: ValidationResult
    
    # Thresholds
    minimum_required: float
    passed_thresholds: Dict[str, bool]
    
    # Recommendations
    strengths: List[str]
    weaknesses: List[str]
    recommendation: str
    confidence: float


class TradeValidationScorer:
    """Real-Time Trade Validation Scoring Engine.
    
    Provides comprehensive multi-factor validation scoring
    for trade quality assessment.
    """
    
    # Default thresholds
    DEFAULT_THRESHOLDS = {
        'technical': 60,
        'market_condition': 50,
        'risk_assessment': 70,
        'pattern_reliability': 55,
        'execution_probability': 60,
        'total': 65
    }
    
    # Score weights
    DEFAULT_WEIGHTS = {
        'technical': 0.25,
        'market_condition': 0.20,
        'risk_assessment': 0.25,
        'pattern_reliability': 0.15,
        'execution_probability': 0.15
    }
    
    def __init__(
        self,
        thresholds: Optional[Dict[str, float]] = None,
        weights: Optional[Dict[str, float]] = None,
        strict_mode: bool = False
    ):
        """Initialize Trade Validation Scorer.
        
        Args:
            thresholds: Custom score thresholds
            weights: Custom score weights
            strict_mode: If True, all thresholds must pass
        """
        try:
            self.thresholds = thresholds or self.DEFAULT_THRESHOLDS
            self.weights = weights or self.DEFAULT_WEIGHTS
            self.strict_mode = strict_mode
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    def validate_trade(
        self,
        symbol: str,
        direction: str,
        entry_price: float,
        stop_loss: float,
        take_profit: float,
        position_size: float,
        market_data: pd.DataFrame,
        pattern_type: Optional[str] = None,
        additional_context: Optional[Dict[str, Any]] = None
    ) -> ValidationScorecard:
        """Validate a trade setup and generate scorecard.
        
        Args:
            symbol: Trading symbol
            direction: 'long' or 'short'
            entry_price: Planned entry price
            stop_loss: Stop loss price
            take_profit: Take profit price
            position_size: Position size
            market_data: OHLCV DataFrame
            pattern_type: Type of pattern (optional)
            additional_context: Additional context data
            
        Returns:
            ValidationScorecard with complete analysis
        """
        try:
            context = additional_context or {}
        
            # Calculate individual scores
            technical = self._calculate_technical_score(
                market_data, direction, entry_price, context
            )
        
            market_condition = self._calculate_market_condition_score(
                market_data, context
            )
        
            risk_assessment = self._calculate_risk_assessment_score(
                entry_price, stop_loss, take_profit, position_size, context
            )
        
            pattern_reliability = self._calculate_pattern_reliability_score(
                market_data, pattern_type, direction, context
            )
        
            execution_probability = self._calculate_execution_probability_score(
                market_data, entry_price, context
            )
        
            # Calculate total score
            total_score = (
                technical.score * self.weights['technical'] +
                market_condition.score * self.weights['market_condition'] +
                risk_assessment.score * self.weights['risk_assessment'] +
                pattern_reliability.score * self.weights['pattern_reliability'] +
                execution_probability.score * self.weights['execution_probability']
            )
        
            # Check thresholds
            passed_thresholds = {
                'technical': technical.score >= self.thresholds['technical'],
                'market_condition': market_condition.score >= self.thresholds['market_condition'],
                'risk_assessment': risk_assessment.score >= self.thresholds['risk_assessment'],
                'pattern_reliability': pattern_reliability.score >= self.thresholds['pattern_reliability'],
                'execution_probability': execution_probability.score >= self.thresholds['execution_probability'],
                'total': total_score >= self.thresholds['total']
            }
        
            # Determine validation result
            if self.strict_mode:
                all_passed = all(passed_thresholds.values())
                validation_result = ValidationResult.PASSED if all_passed else ValidationResult.FAILED
            else:
                if total_score >= self.thresholds['total'] and risk_assessment.score >= self.thresholds['risk_assessment']:
                    validation_result = ValidationResult.PASSED
                elif total_score >= self.thresholds['total'] * 0.8:
                    validation_result = ValidationResult.WARNING
                else:
                    validation_result = ValidationResult.FAILED
                
            # Determine grade
            grade = self._get_grade(total_score)
        
            # Generate strengths and weaknesses
            strengths, weaknesses = self._analyze_strengths_weaknesses(
                technical, market_condition, risk_assessment,
                pattern_reliability, execution_probability
            )
        
            # Generate recommendation
            recommendation = self._generate_recommendation(
                validation_result, total_score, strengths, weaknesses
            )
        
            # Calculate confidence
            confidence = self._calculate_confidence(
                technical, market_condition, risk_assessment,
                pattern_reliability, execution_probability
            )
        
            return ValidationScorecard(
                timestamp=datetime.now(),
                symbol=symbol,
                direction=direction,
                technical_score=technical,
                market_condition_score=market_condition,
                risk_assessment_score=risk_assessment,
                pattern_reliability_score=pattern_reliability,
                execution_probability_score=execution_probability,
                total_score=total_score,
                grade=grade,
                validation_result=validation_result,
                minimum_required=self.thresholds['total'],
                passed_thresholds=passed_thresholds,
                strengths=strengths,
                weaknesses=weaknesses,
                recommendation=recommendation,
                confidence=confidence
            )
        except Exception as e:
            logger.error(f"Error in validate_trade: {e}")
            raise
        
    def _calculate_technical_score(
        self,
        df: pd.DataFrame,
        direction: str,
        entry_price: float,
        context: Dict[str, Any]
    ) -> TechnicalScore:
        """Calculate technical validation score."""
        try:
            if len(df) < 20:
                return TechnicalScore(
                    score=50, trend_alignment=50, momentum_score=50,
                    support_resistance_score=50, pattern_score=50,
                    volume_confirmation=50, multi_timeframe_score=50,
                    details={'error': 'Insufficient data'}
                )
            
            # Trend alignment (0-100)
            sma_20 = df['close'].rolling(20).mean().iloc[-1]
            sma_50 = df['close'].rolling(50).mean().iloc[-1] if len(df) >= 50 else sma_20
            current_price = df['close'].iloc[-1]
        
            if direction == 'long':
                trend_alignment = 100 if current_price > sma_20 > sma_50 else (
                    70 if current_price > sma_20 else 40
                )
            else:
                trend_alignment = 100 if current_price < sma_20 < sma_50 else (
                    70 if current_price < sma_20 else 40
                )
            
            # Momentum score (RSI-based)
            delta = df['close'].diff()
            gain = delta.where(delta > 0, 0).rolling(14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs)).iloc[-1]
        
            if direction == 'long':
                momentum_score = 100 if 30 <= rsi <= 50 else (80 if 50 < rsi <= 70 else 50)
            else:
                momentum_score = 100 if 50 <= rsi <= 70 else (80 if 30 <= rsi < 50 else 50)
            
            # Support/Resistance score
            recent_high = df['high'].iloc[-20:].max()
            recent_low = df['low'].iloc[-20:].min()
        
            if direction == 'long':
                # Good if near support
                distance_to_support = (entry_price - recent_low) / recent_low * 100
                support_resistance_score = max(0, 100 - distance_to_support * 10)
            else:
                # Good if near resistance
                distance_to_resistance = (recent_high - entry_price) / entry_price * 100
                support_resistance_score = max(0, 100 - distance_to_resistance * 10)
            
            # Pattern score (from context or default)
            pattern_score = context.get('pattern_score', 70)
        
            # Volume confirmation
            if 'volume' in df.columns:
                recent_vol = df['volume'].iloc[-5:].mean()
                avg_vol = df['volume'].iloc[-20:].mean()
                vol_ratio = recent_vol / avg_vol if avg_vol > 0 else 1
                volume_confirmation = min(100, 50 + vol_ratio * 25)
            else:
                volume_confirmation = 50
            
            # Multi-timeframe score (from context or default)
            multi_timeframe_score = context.get('mtf_score', 60)
        
            # Calculate total
            total = (
                trend_alignment * 0.25 +
                momentum_score * 0.20 +
                support_resistance_score * 0.20 +
                pattern_score * 0.15 +
                volume_confirmation * 0.10 +
                multi_timeframe_score * 0.10
            )
        
            return TechnicalScore(
                score=total,
                trend_alignment=trend_alignment,
                momentum_score=momentum_score,
                support_resistance_score=support_resistance_score,
                pattern_score=pattern_score,
                volume_confirmation=volume_confirmation,
                multi_timeframe_score=multi_timeframe_score,
                details={
                    'sma_20': sma_20,
                    'sma_50': sma_50,
                    'rsi': rsi,
                    'current_price': current_price
                }
            )
        except Exception as e:
            logger.error(f"Error in _calculate_technical_score: {e}")
            raise
        
    def _calculate_market_condition_score(
        self,
        df: pd.DataFrame,
        context: Dict[str, Any]
    ) -> MarketConditionScore:
        """Calculate market condition score."""
        try:
            if len(df) < 20:
                return MarketConditionScore(
                    score=50, regime_score=50, volatility_score=50,
                    liquidity_score=50, correlation_score=50,
                    news_impact_score=50, session_score=50,
                    details={'error': 'Insufficient data'}
                )
            
            # Regime score (trending vs ranging)
            returns = df['close'].pct_change().dropna()
            trend_strength = abs(returns.mean()) / returns.std() if returns.std() > 0 else 0
            regime_score = min(100, trend_strength * 100)
        
            # Volatility score (moderate is best)
            atr = self._calculate_atr(df, 14)
            avg_price = df['close'].mean()
            atr_pct = (atr / avg_price) * 100
        
            # Optimal ATR% is 1-2%
            if 1 <= atr_pct <= 2:
                volatility_score = 100
            elif 0.5 <= atr_pct < 1 or 2 < atr_pct <= 3:
                volatility_score = 70
            else:
                volatility_score = 40
            
            # Liquidity score (from context or volume-based)
            if 'volume' in df.columns:
                avg_vol = df['volume'].iloc[-20:].mean()
                liquidity_score = min(100, 50 + np.log10(avg_vol + 1) * 10)
            else:
                liquidity_score = context.get('liquidity_score', 60)
            
            # Correlation score (from context)
            correlation_score = context.get('correlation_score', 70)
        
            # News impact score (from context)
            news_impact_score = context.get('news_impact_score', 80)
        
            # Session score (from context)
            session_score = context.get('session_score', 70)
        
            # Calculate total
            total = (
                regime_score * 0.20 +
                volatility_score * 0.25 +
                liquidity_score * 0.20 +
                correlation_score * 0.15 +
                news_impact_score * 0.10 +
                session_score * 0.10
            )
        
            return MarketConditionScore(
                score=total,
                regime_score=regime_score,
                volatility_score=volatility_score,
                liquidity_score=liquidity_score,
                correlation_score=correlation_score,
                news_impact_score=news_impact_score,
                session_score=session_score,
                details={
                    'atr_pct': atr_pct,
                    'trend_strength': trend_strength
                }
            )
        except Exception as e:
            logger.error(f"Error in _calculate_market_condition_score: {e}")
            raise
        
    def _calculate_risk_assessment_score(
        self,
        entry_price: float,
        stop_loss: float,
        take_profit: float,
        position_size: float,
        context: Dict[str, Any]
    ) -> RiskAssessmentScore:
        """Calculate risk assessment score."""
        # Position size score
        try:
            max_position = context.get('max_position_size', position_size * 2)
            position_ratio = position_size / max_position
            position_size_score = max(0, 100 - position_ratio * 100)
        
            # Stop loss score (tighter is better, but not too tight)
            if entry_price > 0:
                stop_distance_pct = abs(entry_price - stop_loss) / entry_price * 100
                if 0.5 <= stop_distance_pct <= 2:
                    stop_loss_score = 100
                elif 0.3 <= stop_distance_pct < 0.5 or 2 < stop_distance_pct <= 3:
                    stop_loss_score = 70
                else:
                    stop_loss_score = 40
            else:
                stop_loss_score = 50
            
            # Risk-reward score
            risk = abs(entry_price - stop_loss)
            reward = abs(take_profit - entry_price)
            rr_ratio = reward / risk if risk > 0 else 0
        
            if rr_ratio >= 3:
                risk_reward_score = 100
            elif rr_ratio >= 2:
                risk_reward_score = 85
            elif rr_ratio >= 1.5:
                risk_reward_score = 70
            elif rr_ratio >= 1:
                risk_reward_score = 50
            else:
                risk_reward_score = 30
            
            # Portfolio risk score (from context)
            portfolio_risk_score = context.get('portfolio_risk_score', 70)
        
            # Drawdown score (from context)
            current_drawdown = context.get('current_drawdown_pct', 0)
            drawdown_score = max(0, 100 - current_drawdown * 5)
        
            # Correlation risk score (from context)
            correlation_risk_score = context.get('correlation_risk_score', 70)
        
            # Calculate total
            total = (
                position_size_score * 0.15 +
                stop_loss_score * 0.20 +
                risk_reward_score * 0.30 +
                portfolio_risk_score * 0.15 +
                drawdown_score * 0.10 +
                correlation_risk_score * 0.10
            )
        
            return RiskAssessmentScore(
                score=total,
                position_size_score=position_size_score,
                stop_loss_score=stop_loss_score,
                risk_reward_score=risk_reward_score,
                portfolio_risk_score=portfolio_risk_score,
                drawdown_score=drawdown_score,
                correlation_risk_score=correlation_risk_score,
                details={
                    'stop_distance_pct': stop_distance_pct if entry_price > 0 else 0,
                    'risk_reward_ratio': rr_ratio
                }
            )
        except Exception as e:
            logger.error(f"Error in _calculate_risk_assessment_score: {e}")
            raise
        
    def _calculate_pattern_reliability_score(
        self,
        df: pd.DataFrame,
        pattern_type: Optional[str],
        direction: str,
        context: Dict[str, Any]
    ) -> PatternReliabilityScore:
        """Calculate pattern reliability score."""
        # Historical win rate (from context or default)
        try:
            historical_win_rate = context.get('pattern_win_rate', 55)
        
            # Current strength (from context or calculated)
            current_strength = context.get('pattern_strength', 60)
        
            # Confirmation count
            confirmation_count = context.get('confirmation_count', 2)
            confirmation_score = min(100, confirmation_count * 25)
        
            # Invalidation distance
            invalidation_price = context.get('invalidation_price', 0)
            if invalidation_price > 0 and df['close'].iloc[-1] > 0:
                invalidation_distance = abs(df['close'].iloc[-1] - invalidation_price) / df['close'].iloc[-1] * 100
                invalidation_score = min(100, invalidation_distance * 20)
            else:
                invalidation_distance = 0
                invalidation_score = 50
            
            # Time validity (patterns have expiration)
            time_validity = context.get('pattern_time_validity', 70)
        
            # Calculate total
            total = (
                historical_win_rate * 0.30 +
                current_strength * 0.25 +
                confirmation_score * 0.20 +
                invalidation_score * 0.15 +
                time_validity * 0.10
            )
        
            return PatternReliabilityScore(
                score=total,
                pattern_type=pattern_type or 'unknown',
                historical_win_rate=historical_win_rate,
                current_strength=current_strength,
                confirmation_count=confirmation_count,
                invalidation_distance=invalidation_distance,
                time_validity=time_validity,
                details={}
            )
        except Exception as e:
            logger.error(f"Error in _calculate_pattern_reliability_score: {e}")
            raise
        
    def _calculate_execution_probability_score(
        self,
        df: pd.DataFrame,
        entry_price: float,
        context: Dict[str, Any]
    ) -> ExecutionProbabilityScore:
        """Calculate execution probability score."""
        try:
            current_price = df['close'].iloc[-1] if len(df) > 0 else entry_price
        
            # Fill probability (based on distance from current price)
            price_distance_pct = abs(entry_price - current_price) / current_price * 100
            if price_distance_pct < 0.1:
                fill_probability = 95
            elif price_distance_pct < 0.5:
                fill_probability = 80
            elif price_distance_pct < 1:
                fill_probability = 60
            else:
                fill_probability = 40
            
            # Slippage estimate (from context or calculated)
            avg_spread = context.get('avg_spread_pct', 0.05)
            slippage_estimate = avg_spread * 2
            slippage_score = max(0, 100 - slippage_estimate * 100)
        
            # Spread score
            spread_score = max(0, 100 - avg_spread * 200)
        
            # Depth score (from context)
            depth_score = context.get('order_book_depth_score', 70)
        
            # Timing score (from context)
            timing_score = context.get('timing_score', 70)
        
            # Calculate total
            total = (
                fill_probability * 0.30 +
                slippage_score * 0.25 +
                spread_score * 0.20 +
                depth_score * 0.15 +
                timing_score * 0.10
            )
        
            return ExecutionProbabilityScore(
                score=total,
                fill_probability=fill_probability,
                slippage_estimate=slippage_estimate,
                spread_score=spread_score,
                depth_score=depth_score,
                timing_score=timing_score,
                details={
                    'price_distance_pct': price_distance_pct
                }
            )
        except Exception as e:
            logger.error(f"Error in _calculate_execution_probability_score: {e}")
            raise
        
    def _calculate_atr(self, df: pd.DataFrame, period: int) -> float:
        """Calculate ATR."""
        try:
            high = df['high']
            low = df['low']
            close = df['close']
        
            tr1 = high - low
            tr2 = abs(high - close.shift())
            tr3 = abs(low - close.shift())
        
            tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
            atr = tr.rolling(period).mean().iloc[-1]
        
            return float(atr) if not pd.isna(atr) else 0
        except Exception as e:
            logger.error(f"Error in _calculate_atr: {e}")
            raise
        
    def _get_grade(self, score: float) -> TradeGrade:
        """Convert score to grade."""
        try:
            if score >= 90:
                return TradeGrade.A_PLUS
            elif score >= 80:
                return TradeGrade.A
            elif score >= 70:
                return TradeGrade.B
            elif score >= 60:
                return TradeGrade.C
            elif score >= 50:
                return TradeGrade.D
            else:
                return TradeGrade.F
        except Exception as e:
            logger.error(f"Error in _get_grade: {e}")
            raise
            
    def _analyze_strengths_weaknesses(
        self,
        technical: TechnicalScore,
        market_condition: MarketConditionScore,
        risk_assessment: RiskAssessmentScore,
        pattern_reliability: PatternReliabilityScore,
        execution_probability: ExecutionProbabilityScore
    ) -> Tuple[List[str], List[str]]:
        """Analyze strengths and weaknesses."""
        try:
            strengths = []
            weaknesses = []
        
            # Technical
            if technical.score >= 80:
                strengths.append("Strong technical setup")
            elif technical.score < 60:
                weaknesses.append("Weak technical confirmation")
            
            if technical.trend_alignment >= 80:
                strengths.append("Excellent trend alignment")
            elif technical.trend_alignment < 50:
                weaknesses.append("Poor trend alignment")
            
            # Market condition
            if market_condition.score >= 80:
                strengths.append("Favorable market conditions")
            elif market_condition.score < 50:
                weaknesses.append("Unfavorable market conditions")
            
            if market_condition.volatility_score >= 80:
                strengths.append("Optimal volatility")
            elif market_condition.volatility_score < 50:
                weaknesses.append("Suboptimal volatility")
            
            # Risk assessment
            if risk_assessment.score >= 80:
                strengths.append("Excellent risk management")
            elif risk_assessment.score < 60:
                weaknesses.append("Risk management concerns")
            
            if risk_assessment.risk_reward_score >= 80:
                strengths.append("Favorable risk-reward ratio")
            elif risk_assessment.risk_reward_score < 50:
                weaknesses.append("Poor risk-reward ratio")
            
            # Pattern reliability
            if pattern_reliability.score >= 80:
                strengths.append("High pattern reliability")
            elif pattern_reliability.score < 50:
                weaknesses.append("Low pattern reliability")
            
            # Execution
            if execution_probability.score >= 80:
                strengths.append("High execution probability")
            elif execution_probability.score < 50:
                weaknesses.append("Execution concerns")
            
            return strengths, weaknesses
        except Exception as e:
            logger.error(f"Error in _analyze_strengths_weaknesses: {e}")
            raise
        
    def _generate_recommendation(
        self,
        result: ValidationResult,
        score: float,
        strengths: List[str],
        weaknesses: List[str]
    ) -> str:
        """Generate trade recommendation."""
        try:
            if result == ValidationResult.PASSED:
                if score >= 85:
                    return "STRONG ENTRY - High-quality setup, proceed with full position"
                elif score >= 75:
                    return "GOOD ENTRY - Solid setup, proceed with standard position"
                else:
                    return "ACCEPTABLE ENTRY - Proceed with reduced position size"
            elif result == ValidationResult.WARNING:
                return f"CAUTION - Consider addressing: {', '.join(weaknesses[:2])}"
            else:
                return f"DO NOT TRADE - Key issues: {', '.join(weaknesses[:3])}"
        except Exception as e:
            logger.error(f"Error in _generate_recommendation: {e}")
            raise
            
    def _calculate_confidence(
        self,
        technical: TechnicalScore,
        market_condition: MarketConditionScore,
        risk_assessment: RiskAssessmentScore,
        pattern_reliability: PatternReliabilityScore,
        execution_probability: ExecutionProbabilityScore
    ) -> float:
        """Calculate overall confidence in the validation."""
        try:
            scores = [
                technical.score,
                market_condition.score,
                risk_assessment.score,
                pattern_reliability.score,
                execution_probability.score
            ]
        
            # Confidence based on score consistency
            std = np.std(scores)
            mean = np.mean(scores)
        
            # Lower std = higher confidence
            consistency_factor = max(0, 1 - std / 50)
        
            # Higher mean = higher confidence
            level_factor = mean / 100
        
            confidence = (consistency_factor * 0.4 + level_factor * 0.6) * 100
        
            return min(100, max(0, confidence))
        except Exception as e:
            logger.error(f"Error in _calculate_confidence: {e}")
            raise


# Convenience functions
def validate_trade(
    symbol: str,
    direction: str,
    entry: float,
    stop: float,
    target: float,
    size: float,
    data: pd.DataFrame
) -> Dict[str, Any]:
    """Quick function to validate a trade."""
    try:
        scorer = TradeValidationScorer()
        scorecard = scorer.validate_trade(
            symbol, direction, entry, stop, target, size, data
        )
    
        return {
            'total_score': scorecard.total_score,
            'grade': scorecard.grade.value,
            'result': scorecard.validation_result.value,
            'recommendation': scorecard.recommendation,
            'confidence': scorecard.confidence
        }
    except Exception as e:
        logger.error(f"Error in validate_trade: {e}")
        raise


def get_trade_grade(score: float) -> str:
    """Quick function to get grade from score."""
    try:
        if score >= 90:
            return "A+"
        elif score >= 80:
            return "A"
        elif score >= 70:
            return "B"
        elif score >= 60:
            return "C"
        elif score >= 50:
            return "D"
        else:
            return "F"
    except Exception as e:
        logger.error(f"Error in get_trade_grade: {e}")
        raise
