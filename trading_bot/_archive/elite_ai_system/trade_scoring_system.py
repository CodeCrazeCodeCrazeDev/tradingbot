"""
Trade Scoring System - Real-Time Trade Opportunity Scoring

Implements the institutional-grade trade scoring system from the
Elite Professional Trading AI System Prompt.

Features:
- Technical validation score (0-100)
- Market condition score (0-100)
- Risk assessment score (0-100)
- Pattern reliability score (0-100)
- Execution probability score (0-100)
- Minimum threshold enforcement
- Score history and learning
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
from collections import deque
import json

logger = logging.getLogger(__name__)


class ScoreCategory(Enum):
    """Main scoring categories"""
    TECHNICAL = "technical"
    MARKET_CONDITION = "market_condition"
    RISK_ASSESSMENT = "risk_assessment"
    PATTERN_RELIABILITY = "pattern_reliability"
    EXECUTION_PROBABILITY = "execution_probability"


class TradeGrade(Enum):
    """Trade quality grades"""
    A_PLUS = "A+"  # 90-100: Elite setup
    A = "A"        # 80-89: Excellent setup
    B_PLUS = "B+"  # 75-79: Very good setup
    B = "B"        # 70-74: Good setup
    C = "C"        # 60-69: Average setup
    D = "D"        # 50-59: Below average
    F = "F"        # 0-49: Fail - Do not trade


class SetupQuality(Enum):
    """Setup quality classifications"""
    ELITE = "elite"           # Top 5% of setups
    PREMIUM = "premium"       # Top 15% of setups
    STANDARD = "standard"     # Top 40% of setups
    MARGINAL = "marginal"     # Below standard
    AVOID = "avoid"           # Do not trade


@dataclass
class CategoryScore:
    """Score for a single category"""
    category: ScoreCategory
    score: float  # 0-100
    weight: float  # 0-1
    weighted_score: float
    components: Dict[str, float]
    reasoning: str
    confidence: float
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'category': self.category.value,
            'score': self.score,
            'weight': self.weight,
            'weighted_score': self.weighted_score,
            'components': self.components,
            'reasoning': self.reasoning,
            'confidence': self.confidence,
            'timestamp': self.timestamp.isoformat()
        }


@dataclass
class TradeScore:
    """Complete trade opportunity score"""
    score_id: str
    symbol: str
    direction: str
    timeframe: str
    
    # Category scores
    technical_score: float
    market_condition_score: float
    risk_assessment_score: float
    pattern_reliability_score: float
    execution_probability_score: float
    
    # Aggregate
    total_score: float
    grade: TradeGrade
    quality: SetupQuality
    
    # Details
    category_scores: List[CategoryScore]
    
    # Thresholds
    minimum_threshold: float
    passed: bool
    
    # Risk-adjusted metrics
    position_size_multiplier: float  # 0.25-1.5 based on score
    risk_per_trade_pct: float  # 0.25-1.0% based on quality
    
    # Warnings and recommendations
    warnings: List[str]
    recommendations: List[str]
    reasoning_summary: str
    
    # Meta
    timestamp: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'score_id': self.score_id,
            'symbol': self.symbol,
            'direction': self.direction,
            'timeframe': self.timeframe,
            'technical_score': self.technical_score,
            'market_condition_score': self.market_condition_score,
            'risk_assessment_score': self.risk_assessment_score,
            'pattern_reliability_score': self.pattern_reliability_score,
            'execution_probability_score': self.execution_probability_score,
            'total_score': self.total_score,
            'grade': self.grade.value,
            'quality': self.quality.value,
            'category_scores': [cs.to_dict() for cs in self.category_scores],
            'minimum_threshold': self.minimum_threshold,
            'passed': self.passed,
            'position_size_multiplier': self.position_size_multiplier,
            'risk_per_trade_pct': self.risk_per_trade_pct,
            'warnings': self.warnings,
            'recommendations': self.recommendations,
            'reasoning_summary': self.reasoning_summary,
            'timestamp': self.timestamp.isoformat(),
            'expires_at': self.expires_at.isoformat() if self.expires_at else None
        }
    
    def is_valid(self) -> bool:
        """Check if score is still valid"""
        if self.expires_at is None:
            return True
        return datetime.now() < self.expires_at


class TradeScoringSystem:
    """
    Elite Trade Scoring System
    
    Provides real-time scoring of trade opportunities with
    institutional-grade multi-factor analysis.
    """
    
    # Category weights
    DEFAULT_WEIGHTS = {
        ScoreCategory.TECHNICAL: 0.25,
        ScoreCategory.MARKET_CONDITION: 0.20,
        ScoreCategory.RISK_ASSESSMENT: 0.25,
        ScoreCategory.PATTERN_RELIABILITY: 0.15,
        ScoreCategory.EXECUTION_PROBABILITY: 0.15,
    }
    
    # Grade thresholds
    GRADE_THRESHOLDS = {
        TradeGrade.A_PLUS: 90,
        TradeGrade.A: 80,
        TradeGrade.B_PLUS: 75,
        TradeGrade.B: 70,
        TradeGrade.C: 60,
        TradeGrade.D: 50,
        TradeGrade.F: 0,
    }
    
    # Quality thresholds
    QUALITY_THRESHOLDS = {
        SetupQuality.ELITE: 90,
        SetupQuality.PREMIUM: 80,
        SetupQuality.STANDARD: 70,
        SetupQuality.MARGINAL: 60,
        SetupQuality.AVOID: 0,
    }
    
    # Position size multipliers by quality
    POSITION_MULTIPLIERS = {
        SetupQuality.ELITE: 1.5,
        SetupQuality.PREMIUM: 1.25,
        SetupQuality.STANDARD: 1.0,
        SetupQuality.MARGINAL: 0.5,
        SetupQuality.AVOID: 0.0,
    }
    
    # Risk per trade by quality
    RISK_PER_TRADE = {
        SetupQuality.ELITE: 1.0,      # 1% risk
        SetupQuality.PREMIUM: 0.75,   # 0.75% risk
        SetupQuality.STANDARD: 0.5,   # 0.5% risk
        SetupQuality.MARGINAL: 0.25,  # 0.25% risk
        SetupQuality.AVOID: 0.0,      # No trade
    }
    
    # Score validity duration by timeframe
    SCORE_VALIDITY = {
        'M1': timedelta(minutes=5),
        'M5': timedelta(minutes=15),
        'M15': timedelta(minutes=30),
        'M30': timedelta(hours=1),
        'H1': timedelta(hours=2),
        'H4': timedelta(hours=8),
        'D1': timedelta(hours=24),
        'W1': timedelta(days=7),
    }
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Custom weights
        self.weights = self.config.get('weights', self.DEFAULT_WEIGHTS.copy())
        
        # Minimum threshold
        self.minimum_threshold = self.config.get('minimum_threshold', 70.0)
        
        # Score history
        self.score_history: deque = deque(maxlen=5000)
        
        # Performance tracking
        self.score_outcomes: Dict[str, Dict[str, Any]] = {}
        
        logger.info("TradeScoringSystem initialized")
    
    def score_trade(
        self,
        symbol: str,
        direction: str,
        timeframe: str,
        market_data: Dict[str, Any],
        analysis_results: Dict[str, Any],
        entry_price: Optional[float] = None,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None
    ) -> TradeScore:
        """
        Score a trade opportunity
        
        Args:
            symbol: Trading symbol
            direction: LONG or SHORT
            timeframe: Timeframe (M1, M5, H1, etc.)
            market_data: Current market data
            analysis_results: Results from analysis modules
            entry_price: Proposed entry price
            stop_loss: Proposed stop loss
            take_profit: Proposed take profit
        
        Returns:
            TradeScore with complete analysis
        """
        import uuid
        score_id = str(uuid.uuid4())[:8]
        
        # Calculate category scores
        category_scores: List[CategoryScore] = []
        warnings: List[str] = []
        recommendations: List[str] = []
        
        # Technical Score
        tech_score = self._calculate_technical_score(
            market_data, analysis_results, direction
        )
        category_scores.append(tech_score)
        
        # Market Condition Score
        market_score = self._calculate_market_condition_score(
            market_data, analysis_results
        )
        category_scores.append(market_score)
        
        # Risk Assessment Score
        risk_score = self._calculate_risk_assessment_score(
            market_data, analysis_results, entry_price, stop_loss, take_profit
        )
        category_scores.append(risk_score)
        
        # Pattern Reliability Score
        pattern_score = self._calculate_pattern_reliability_score(
            market_data, analysis_results
        )
        category_scores.append(pattern_score)
        
        # Execution Probability Score
        exec_score = self._calculate_execution_probability_score(
            market_data, analysis_results, entry_price
        )
        category_scores.append(exec_score)
        
        # Calculate total score
        total_score = sum(cs.weighted_score for cs in category_scores)
        
        # Determine grade and quality
        grade = self._determine_grade(total_score)
        quality = self._determine_quality(total_score)
        
        # Check minimum scores
        for cs in category_scores:
            if cs.score < 50:
                warnings.append(f"{cs.category.value} score below 50: {cs.score:.1f}")
            if cs.score < 40:
                warnings.append(f"CRITICAL: {cs.category.value} score very low: {cs.score:.1f}")
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            category_scores, total_score, quality, direction
        )
        
        # Calculate position sizing
        position_multiplier = self.POSITION_MULTIPLIERS.get(quality, 1.0)
        risk_per_trade = self.RISK_PER_TRADE.get(quality, 0.5)
        
        # Determine validity
        validity_duration = self.SCORE_VALIDITY.get(timeframe, timedelta(hours=1))
        expires_at = datetime.now() + validity_duration
        
        # Generate reasoning summary
        reasoning_summary = self._generate_reasoning_summary(
            total_score, grade, quality, category_scores, direction
        )
        
        # Create score object
        trade_score = TradeScore(
            score_id=score_id,
            symbol=symbol,
            direction=direction,
            timeframe=timeframe,
            technical_score=tech_score.score,
            market_condition_score=market_score.score,
            risk_assessment_score=risk_score.score,
            pattern_reliability_score=pattern_score.score,
            execution_probability_score=exec_score.score,
            total_score=total_score,
            grade=grade,
            quality=quality,
            category_scores=category_scores,
            minimum_threshold=self.minimum_threshold,
            passed=total_score >= self.minimum_threshold,
            position_size_multiplier=position_multiplier,
            risk_per_trade_pct=risk_per_trade,
            warnings=warnings,
            recommendations=recommendations,
            reasoning_summary=reasoning_summary,
            expires_at=expires_at
        )
        
        # Store in history
        self.score_history.append(trade_score)
        
        logger.info(
            f"Trade scored: {symbol} {direction} - "
            f"Score={total_score:.1f}, Grade={grade.value}, "
            f"Quality={quality.value}, Passed={trade_score.passed}"
        )
        
        return trade_score
    
    def _calculate_technical_score(
        self,
        market_data: Dict[str, Any],
        analysis_results: Dict[str, Any],
        direction: str
    ) -> CategoryScore:
        """Calculate technical validation score"""
        components = {}
        
        # Price action (25%)
        price_action = analysis_results.get('price_action_score', 50.0)
        components['price_action'] = price_action
        
        # Market structure (25%)
        structure = analysis_results.get('market_structure_score', 50.0)
        components['market_structure'] = structure
        
        # Multi-timeframe (20%)
        mtf = analysis_results.get('mtf_alignment_score', 50.0)
        components['multi_timeframe'] = mtf
        
        # Indicators (15%)
        indicators = analysis_results.get('indicator_score', 50.0)
        components['indicators'] = indicators
        
        # Order flow (15%)
        order_flow = analysis_results.get('order_flow_score', 50.0)
        components['order_flow'] = order_flow
        
        # Calculate weighted score
        weights = [0.25, 0.25, 0.20, 0.15, 0.15]
        scores = [price_action, structure, mtf, indicators, order_flow]
        score = sum(w * s for w, s in zip(weights, scores))
        
        # Direction alignment bonus/penalty
        trend_direction = analysis_results.get('trend_direction', 'neutral')
        if (direction == 'LONG' and trend_direction == 'bullish') or \
           (direction == 'SHORT' and trend_direction == 'bearish'):
            score = min(100, score * 1.1)  # 10% bonus
        elif (direction == 'LONG' and trend_direction == 'bearish') or \
             (direction == 'SHORT' and trend_direction == 'bullish'):
            score = score * 0.85  # 15% penalty
        
        weight = self.weights[ScoreCategory.TECHNICAL]
        
        reasoning = (
            f"Technical: PA={price_action:.0f}, Structure={structure:.0f}, "
            f"MTF={mtf:.0f}, Indicators={indicators:.0f}, OF={order_flow:.0f}"
        )
        
        return CategoryScore(
            category=ScoreCategory.TECHNICAL,
            score=score,
            weight=weight,
            weighted_score=score * weight,
            components=components,
            reasoning=reasoning,
            confidence=0.8
        )
    
    def _calculate_market_condition_score(
        self,
        market_data: Dict[str, Any],
        analysis_results: Dict[str, Any]
    ) -> CategoryScore:
        """Calculate market condition score"""
        components = {}
        
        # Regime clarity (25%)
        regime_clarity = analysis_results.get('regime_clarity_score', 50.0)
        components['regime_clarity'] = regime_clarity
        
        # Volatility environment (25%)
        volatility = analysis_results.get('volatility_score', 50.0)
        components['volatility'] = volatility
        
        # Liquidity (20%)
        liquidity = analysis_results.get('liquidity_score', 50.0)
        components['liquidity'] = liquidity
        
        # Correlation alignment (15%)
        correlation = analysis_results.get('correlation_score', 50.0)
        components['correlation'] = correlation
        
        # News/event risk (15%)
        news_risk = analysis_results.get('news_risk_score', 50.0)
        components['news_risk'] = news_risk
        
        weights = [0.25, 0.25, 0.20, 0.15, 0.15]
        scores = [regime_clarity, volatility, liquidity, correlation, news_risk]
        score = sum(w * s for w, s in zip(weights, scores))
        
        weight = self.weights[ScoreCategory.MARKET_CONDITION]
        
        reasoning = (
            f"Market: Regime={regime_clarity:.0f}, Vol={volatility:.0f}, "
            f"Liq={liquidity:.0f}, Corr={correlation:.0f}"
        )
        
        return CategoryScore(
            category=ScoreCategory.MARKET_CONDITION,
            score=score,
            weight=weight,
            weighted_score=score * weight,
            components=components,
            reasoning=reasoning,
            confidence=0.75
        )
    
    def _calculate_risk_assessment_score(
        self,
        market_data: Dict[str, Any],
        analysis_results: Dict[str, Any],
        entry_price: Optional[float],
        stop_loss: Optional[float],
        take_profit: Optional[float]
    ) -> CategoryScore:
        """Calculate risk assessment score"""
        components = {}
        
        # Risk-reward ratio (35%)
        if entry_price and stop_loss and take_profit:
            if entry_price != stop_loss:
                rr_ratio = abs(take_profit - entry_price) / abs(entry_price - stop_loss)
            else:
                rr_ratio = 1.0
            rr_score = min(100, max(0, (rr_ratio - 1) * 25 + 50))
        else:
            rr_ratio = analysis_results.get('risk_reward_ratio', 1.5)
            rr_score = min(100, max(0, (rr_ratio - 1) * 25 + 50))
        components['risk_reward'] = rr_score
        
        # Stop placement quality (25%)
        stop_quality = analysis_results.get('stop_placement_score', 50.0)
        components['stop_placement'] = stop_quality
        
        # Position sizing appropriateness (20%)
        position_score = analysis_results.get('position_sizing_score', 50.0)
        components['position_sizing'] = position_score
        
        # Drawdown risk (20%)
        drawdown_risk = analysis_results.get('drawdown_risk_score', 50.0)
        components['drawdown_risk'] = drawdown_risk
        
        weights = [0.35, 0.25, 0.20, 0.20]
        scores = [rr_score, stop_quality, position_score, drawdown_risk]
        score = sum(w * s for w, s in zip(weights, scores))
        
        weight = self.weights[ScoreCategory.RISK_ASSESSMENT]
        
        reasoning = (
            f"Risk: R:R={rr_ratio:.1f}:1 ({rr_score:.0f}), "
            f"Stop={stop_quality:.0f}, Position={position_score:.0f}"
        )
        
        return CategoryScore(
            category=ScoreCategory.RISK_ASSESSMENT,
            score=score,
            weight=weight,
            weighted_score=score * weight,
            components=components,
            reasoning=reasoning,
            confidence=0.85
        )
    
    def _calculate_pattern_reliability_score(
        self,
        market_data: Dict[str, Any],
        analysis_results: Dict[str, Any]
    ) -> CategoryScore:
        """Calculate pattern reliability score"""
        components = {}
        
        # Historical win rate (40%)
        win_rate = analysis_results.get('pattern_win_rate', 50.0)
        win_rate_score = win_rate  # Already 0-100
        components['historical_win_rate'] = win_rate_score
        
        # Pattern completion (30%)
        completion = analysis_results.get('pattern_completion_pct', 50.0)
        components['pattern_completion'] = completion
        
        # Pattern age/freshness (15%)
        freshness = analysis_results.get('pattern_freshness_score', 50.0)
        components['pattern_freshness'] = freshness
        
        # Similar pattern performance (15%)
        similar_perf = analysis_results.get('similar_pattern_score', 50.0)
        components['similar_patterns'] = similar_perf
        
        weights = [0.40, 0.30, 0.15, 0.15]
        scores = [win_rate_score, completion, freshness, similar_perf]
        score = sum(w * s for w, s in zip(weights, scores))
        
        weight = self.weights[ScoreCategory.PATTERN_RELIABILITY]
        
        reasoning = (
            f"Pattern: WinRate={win_rate:.0f}%, Completion={completion:.0f}%, "
            f"Fresh={freshness:.0f}"
        )
        
        return CategoryScore(
            category=ScoreCategory.PATTERN_RELIABILITY,
            score=score,
            weight=weight,
            weighted_score=score * weight,
            components=components,
            reasoning=reasoning,
            confidence=0.7
        )
    
    def _calculate_execution_probability_score(
        self,
        market_data: Dict[str, Any],
        analysis_results: Dict[str, Any],
        entry_price: Optional[float]
    ) -> CategoryScore:
        """Calculate execution probability score"""
        components = {}
        
        # Fill probability (35%)
        fill_prob = analysis_results.get('fill_probability', 70.0)
        components['fill_probability'] = fill_prob
        
        # Slippage estimate (25%)
        slippage = analysis_results.get('expected_slippage_bps', 5.0)
        slippage_score = max(0, 100 - slippage * 5)  # 0 bps = 100, 20 bps = 0
        components['slippage_score'] = slippage_score
        
        # Market depth (20%)
        depth = analysis_results.get('market_depth_score', 50.0)
        components['market_depth'] = depth
        
        # Spread quality (20%)
        spread = analysis_results.get('spread_score', 50.0)
        components['spread_quality'] = spread
        
        weights = [0.35, 0.25, 0.20, 0.20]
        scores = [fill_prob, slippage_score, depth, spread]
        score = sum(w * s for w, s in zip(weights, scores))
        
        weight = self.weights[ScoreCategory.EXECUTION_PROBABILITY]
        
        reasoning = (
            f"Execution: Fill={fill_prob:.0f}%, Slippage={slippage:.1f}bps, "
            f"Depth={depth:.0f}, Spread={spread:.0f}"
        )
        
        return CategoryScore(
            category=ScoreCategory.EXECUTION_PROBABILITY,
            score=score,
            weight=weight,
            weighted_score=score * weight,
            components=components,
            reasoning=reasoning,
            confidence=0.75
        )
    
    def _determine_grade(self, total_score: float) -> TradeGrade:
        """Determine trade grade from score"""
        for grade, threshold in self.GRADE_THRESHOLDS.items():
            if total_score >= threshold:
                return grade
        return TradeGrade.F
    
    def _determine_quality(self, total_score: float) -> SetupQuality:
        """Determine setup quality from score"""
        for quality, threshold in self.QUALITY_THRESHOLDS.items():
            if total_score >= threshold:
                return quality
        return SetupQuality.AVOID
    
    def _generate_recommendations(
        self,
        category_scores: List[CategoryScore],
        total_score: float,
        quality: SetupQuality,
        direction: str
    ) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        # Quality-based recommendations
        if quality == SetupQuality.ELITE:
            recommendations.append("ELITE setup - Consider full position size")
            recommendations.append("High confidence entry - Execute with conviction")
        elif quality == SetupQuality.PREMIUM:
            recommendations.append("PREMIUM setup - Consider 75-100% position size")
            recommendations.append("Strong setup - Execute with standard risk")
        elif quality == SetupQuality.STANDARD:
            recommendations.append("STANDARD setup - Use 50-75% position size")
            recommendations.append("Wait for additional confirmation if possible")
        elif quality == SetupQuality.MARGINAL:
            recommendations.append("MARGINAL setup - Use reduced position (25-50%)")
            recommendations.append("Consider waiting for better setup")
        else:
            recommendations.append("AVOID - Do not trade this setup")
            recommendations.append("Wait for higher quality opportunity")
        
        # Category-specific recommendations
        for cs in category_scores:
            if cs.score < 60:
                if cs.category == ScoreCategory.TECHNICAL:
                    recommendations.append("Weak technical setup - Wait for clearer signals")
                elif cs.category == ScoreCategory.MARKET_CONDITION:
                    recommendations.append("Poor market conditions - Consider reducing size")
                elif cs.category == ScoreCategory.RISK_ASSESSMENT:
                    recommendations.append("Risk parameters suboptimal - Adjust stops/targets")
                elif cs.category == ScoreCategory.PATTERN_RELIABILITY:
                    recommendations.append("Pattern reliability low - Seek confirmation")
                elif cs.category == ScoreCategory.EXECUTION_PROBABILITY:
                    recommendations.append("Execution risk high - Use limit orders")
        
        return recommendations
    
    def _generate_reasoning_summary(
        self,
        total_score: float,
        grade: TradeGrade,
        quality: SetupQuality,
        category_scores: List[CategoryScore],
        direction: str
    ) -> str:
        """Generate human-readable reasoning summary"""
        
        # Find strongest and weakest categories
        sorted_scores = sorted(category_scores, key=lambda x: x.score, reverse=True)
        strongest = sorted_scores[0]
        weakest = sorted_scores[-1]
        
        summary = (
            f"{direction} trade scored {total_score:.1f}/100 (Grade: {grade.value}, "
            f"Quality: {quality.value}). "
            f"Strongest: {strongest.category.value} ({strongest.score:.0f}). "
            f"Weakest: {weakest.category.value} ({weakest.score:.0f}). "
        )
        
        if quality in [SetupQuality.ELITE, SetupQuality.PREMIUM]:
            summary += "Recommended for execution."
        elif quality == SetupQuality.STANDARD:
            summary += "Acceptable for execution with caution."
        else:
            summary += "Not recommended for execution."
        
        return summary
    
    def record_outcome(
        self,
        score_id: str,
        outcome: str,  # WIN, LOSS, BREAKEVEN
        pnl_pct: float,
        notes: Optional[str] = None
    ):
        """Record trade outcome for learning"""
        self.score_outcomes[score_id] = {
            'outcome': outcome,
            'pnl_pct': pnl_pct,
            'notes': notes,
            'recorded_at': datetime.now().isoformat()
        }
        
        logger.info(f"Recorded outcome for {score_id}: {outcome}, PnL={pnl_pct:.2f}%")
    
    def get_score_statistics(self) -> Dict[str, Any]:
        """Get scoring statistics"""
        if not self.score_history:
            return {'message': 'No scores recorded'}
        
        scores = [s.total_score for s in self.score_history]
        grades = [s.grade.value for s in self.score_history]
        
        return {
            'total_scores': len(scores),
            'average_score': np.mean(scores),
            'median_score': np.median(scores),
            'std_score': np.std(scores),
            'min_score': min(scores),
            'max_score': max(scores),
            'grade_distribution': {g: grades.count(g) for g in set(grades)},
            'pass_rate': sum(1 for s in self.score_history if s.passed) / len(scores) * 100
        }
    
    def get_quality_distribution(self) -> Dict[str, int]:
        """Get distribution of setup qualities"""
        if not self.score_history:
            return {}
        
        qualities = [s.quality.value for s in self.score_history]
        return {q: qualities.count(q) for q in set(qualities)}


# Convenience functions
def create_scoring_system(config: Optional[Dict[str, Any]] = None) -> TradeScoringSystem:
    """Factory function to create scoring system"""
    return TradeScoringSystem(config)


def quick_score(
    symbol: str,
    direction: str,
    analysis_results: Dict[str, Any]
) -> TradeScore:
    """Quick scoring with default configuration"""
    system = TradeScoringSystem()
    return system.score_trade(
        symbol=symbol,
        direction=direction,
        timeframe='H1',
        market_data={},
        analysis_results=analysis_results
    )
