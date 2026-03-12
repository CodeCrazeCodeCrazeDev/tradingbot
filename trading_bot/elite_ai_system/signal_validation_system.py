"""
Signal Validation System - Multi-Layer Validation Framework

Implements institutional-grade signal validation with:
- Technical validation layer
- Contextual validation layer
- Invalid signal detection
- Market manipulation detection
- Mitigation strategies
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import asyncio
import numpy

# Evolution: Added retry decorator
def retry(max_attempts=3, delay=1.0):
    """Retry decorator for resilient operations"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    if attempt < max_attempts - 1:
                        await asyncio.sleep(delay * (attempt + 1))
            raise last_error
        return wrapper
    return decorator



logger = logging.getLogger(__name__)


class ValidationLayer(Enum):
    TECHNICAL = "technical"
    CONTEXTUAL = "contextual"
    PATTERN = "pattern"
    MANIPULATION = "manipulation"
    RISK = "risk"


class ValidationStatus(Enum):
    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"
    PENDING = "pending"


@dataclass
class TechnicalValidation:
    """Technical validation results"""
    price_action_score: float = 0.0
    volume_score: float = 0.0
    market_structure_score: float = 0.0
    indicator_alignment_score: float = 0.0
    multi_timeframe_score: float = 0.0
    overall_score: float = 0.0
    passed: bool = False
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ContextualValidation:
    """Contextual validation results"""
    regime_alignment_score: float = 0.0
    liquidity_score: float = 0.0
    volatility_score: float = 0.0
    correlation_score: float = 0.0
    news_impact_score: float = 0.0
    overall_score: float = 0.0
    passed: bool = False
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ValidationResult:
    """Complete validation result"""
    signal_id: str
    symbol: str
    action: str
    technical: TechnicalValidation
    contextual: ContextualValidation
    pattern_validity: float
    manipulation_risk: float
    overall_score: float
    status: ValidationStatus
    recommendation: str
    reasons: List[str]
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'signal_id': self.signal_id,
            'symbol': self.symbol,
            'action': self.action,
            'technical_score': self.technical.overall_score,
            'contextual_score': self.contextual.overall_score,
            'pattern_validity': self.pattern_validity,
            'manipulation_risk': self.manipulation_risk,
            'overall_score': self.overall_score,
            'status': self.status.value,
            'recommendation': self.recommendation,
            'reasons': self.reasons,
            'timestamp': self.timestamp.isoformat()
        }


class SignalValidationSystem:
    """
    Multi-Layer Signal Validation System
    
    Validates trading signals through multiple layers:
    1. Technical validation (price action, volume, structure)
    2. Contextual validation (regime, liquidity, news)
    3. Pattern validity checking
    4. Manipulation detection
    5. Risk assessment
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Validation thresholds
        self.min_technical_score = self.config.get('min_technical_score', 0.6)
        self.min_contextual_score = self.config.get('min_contextual_score', 0.5)
        self.min_overall_score = self.config.get('min_overall_score', 0.7)
        self.max_manipulation_risk = self.config.get('max_manipulation_risk', 0.3)
        
        # Validation weights
        self.weights = {
            'technical': 0.35,
            'contextual': 0.25,
            'pattern': 0.20,
            'manipulation': 0.20
        }
        
        # Validation history
        self.validation_history: List[ValidationResult] = []
        self.validation_stats = {'total': 0, 'passed': 0, 'failed': 0, 'warnings': 0}
        
        logger.info("SignalValidationSystem initialized")
    
    async def validate_signal(
        self,
        signal: Dict[str, Any],
        market_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> ValidationResult:
        """
        Validate a trading signal through all layers
        
        Args:
            signal: Trading signal with action, entry, stop_loss, etc.
            market_data: Current market data
            context: Additional context (news, sentiment, etc.)
            
        Returns:
            ValidationResult with complete validation analysis
        """
        signal_id = signal.get('signal_id', f"sig_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        symbol = signal.get('symbol', 'UNKNOWN')
        action = signal.get('action', 'HOLD')
        
        logger.info(f"Validating signal {signal_id} for {symbol}")
        
        # Layer 1: Technical Validation
        technical = await self._validate_technical(signal, market_data)
        
        # Layer 2: Contextual Validation
        contextual = await self._validate_contextual(signal, market_data, context)
        
        # Layer 3: Pattern Validity
        pattern_validity = await self._validate_patterns(signal, market_data)
        
        # Layer 4: Manipulation Detection
        manipulation_risk = await self._detect_manipulation(market_data)
        
        # Calculate overall score
        overall_score = (
            technical.overall_score * self.weights['technical'] +
            contextual.overall_score * self.weights['contextual'] +
            pattern_validity * self.weights['pattern'] +
            (1 - manipulation_risk) * self.weights['manipulation']
        )
        
        # Determine status and recommendation
        status, recommendation, reasons = self._determine_status(
            technical, contextual, pattern_validity, manipulation_risk, overall_score
        )
        
        result = ValidationResult(
            signal_id=signal_id,
            symbol=symbol,
            action=action,
            technical=technical,
            contextual=contextual,
            pattern_validity=pattern_validity,
            manipulation_risk=manipulation_risk,
            overall_score=overall_score,
            status=status,
            recommendation=recommendation,
            reasons=reasons
        )
        
        # Update stats
        self.validation_history.append(result)
        self.validation_stats['total'] += 1
        if status == ValidationStatus.PASSED:
            self.validation_stats['passed'] += 1
        elif status == ValidationStatus.FAILED:
            self.validation_stats['failed'] += 1
        else:
            self.validation_stats['warnings'] += 1
        
        logger.info(f"Validation complete: {status.value} (score: {overall_score:.2%})")
        return result
    
    async def _validate_technical(
        self,
        signal: Dict[str, Any],
        market_data: Dict[str, Any]
    ) -> TechnicalValidation:
        """Technical validation layer"""
        prices = market_data.get('prices', [])
        volumes = market_data.get('volumes', [])
        indicators = market_data.get('indicators', {})
        action = signal.get('action', 'HOLD')
        
        # Price Action Validation
        price_action_score = self._validate_price_action(prices, action)
        
        # Volume Validation
        volume_score = self._validate_volume(prices, volumes, action)
        
        # Market Structure Validation
        market_structure_score = self._validate_market_structure(prices, action)
        
        # Indicator Alignment
        indicator_score = self._validate_indicators(indicators, action)
        
        # Multi-Timeframe (simplified - would need MTF data)
        mtf_score = 0.7  # Default score
        
        # Calculate overall
        overall = (
            price_action_score * 0.25 +
            volume_score * 0.20 +
            market_structure_score * 0.25 +
            indicator_score * 0.20 +
            mtf_score * 0.10
        )
        
        return TechnicalValidation(
            price_action_score=price_action_score,
            volume_score=volume_score,
            market_structure_score=market_structure_score,
            indicator_alignment_score=indicator_score,
            multi_timeframe_score=mtf_score,
            overall_score=overall,
            passed=overall >= self.min_technical_score,
            details={
                'price_trend': 'bullish' if price_action_score > 0.6 else 'bearish',
                'volume_confirmation': volume_score > 0.5,
                'structure_valid': market_structure_score > 0.5
            }
        )
    
    async def _validate_contextual(
        self,
        signal: Dict[str, Any],
        market_data: Dict[str, Any],
        context: Optional[Dict[str, Any]]
    ) -> ContextualValidation:
        """Contextual validation layer"""
        context = context or {}
        action = signal.get('action', 'HOLD')
        
        # Regime Alignment
        regime = context.get('market_regime', 'unknown')
        regime_score = self._validate_regime_alignment(regime, action)
        
        # Liquidity Assessment
        liquidity_score = self._validate_liquidity(market_data)
        
        # Volatility Assessment
        volatility_score = self._validate_volatility(market_data, signal)
        
        # Correlation Check
        correlation_score = self._validate_correlations(context)
        
        # News Impact
        news_score = self._validate_news_impact(context)
        
        # Calculate overall
        overall = (
            regime_score * 0.25 +
            liquidity_score * 0.25 +
            volatility_score * 0.20 +
            correlation_score * 0.15 +
            news_score * 0.15
        )
        
        return ContextualValidation(
            regime_alignment_score=regime_score,
            liquidity_score=liquidity_score,
            volatility_score=volatility_score,
            correlation_score=correlation_score,
            news_impact_score=news_score,
            overall_score=overall,
            passed=overall >= self.min_contextual_score,
            details={
                'regime': regime,
                'liquidity_adequate': liquidity_score > 0.5,
                'volatility_acceptable': volatility_score > 0.4
            }
        )
    
    async def _validate_patterns(
        self,
        signal: Dict[str, Any],
        market_data: Dict[str, Any]
    ) -> float:
        """Validate pattern reliability"""
        prices = market_data.get('prices', [])
        if len(prices) < 20:
            return 0.5
        
        price_array = np.array(prices)
        action = signal.get('action', 'HOLD')
        
        validity_score = 0.5
        
        # Check for pattern completion
        recent_change = (price_array[-1] - price_array[-5]) / price_array[-5] if price_array[-5] != 0 else 0
        
        # Bullish patterns for BUY
        if action == 'BUY':
            if recent_change > 0:
                validity_score += 0.2
            # Check for higher lows
            if price_array[-1] > price_array[-3] and price_array[-3] > price_array[-5]:
                validity_score += 0.15
        
        # Bearish patterns for SELL
        elif action == 'SELL':
            if recent_change < 0:
                validity_score += 0.2
            # Check for lower highs
            if price_array[-1] < price_array[-3] and price_array[-3] < price_array[-5]:
                validity_score += 0.15
        
        # Check for false breakout risk
        volatility = np.std(np.diff(price_array) / price_array[:-1])
        if volatility > 0.03:
            validity_score -= 0.1  # High volatility = higher false breakout risk
        
        return max(0, min(1, validity_score))
    
    async def _detect_manipulation(self, market_data: Dict[str, Any]) -> float:
        """Detect potential market manipulation"""
        prices = market_data.get('prices', [])
        volumes = market_data.get('volumes', [])
        
        if len(prices) < 10:
            return 0.2  # Default low risk
        
        manipulation_score = 0.0
        
        price_array = np.array(prices)
        volume_array = np.array(volumes) if volumes else np.ones(len(prices))
        
        # Check for spoofing patterns (large volume with minimal price impact)
        if len(volume_array) >= 5:
            recent_volume = np.mean(volume_array[-5:])
            avg_volume = np.mean(volume_array)
            recent_price_change = abs(price_array[-1] - price_array[-5]) / price_array[-5]
            
            if recent_volume > avg_volume * 2 and recent_price_change < 0.002:
                manipulation_score += 0.3
        
        # Check for wash trading (unusual volume spikes)
        if len(volume_array) >= 10:
            volume_std = np.std(volume_array)
            for i in range(-5, 0):
                if volume_array[i] > np.mean(volume_array) + 3 * volume_std:
                    manipulation_score += 0.1
        
        # Check for stop hunting (price spikes and reversals)
        if len(price_array) >= 10:
            for i in range(-5, -1):
                spike = abs(price_array[i] - price_array[i-1]) / price_array[i-1]
                reversal = abs(price_array[i+1] - price_array[i]) / price_array[i]
                if spike > 0.01 and reversal > 0.008:
                    manipulation_score += 0.15
        
        return min(1.0, manipulation_score)
    
    def _validate_price_action(self, prices: List[float], action: str) -> float:
        """Validate price action alignment"""
        if len(prices) < 10:
            return 0.5
        
        price_array = np.array(prices)
        
        # Calculate trend
        sma_short = np.mean(price_array[-5:])
        sma_long = np.mean(price_array[-20:]) if len(price_array) >= 20 else np.mean(price_array)
        
        trend_up = sma_short > sma_long
        
        if action == 'BUY' and trend_up:
            return 0.8
        elif action == 'SELL' and not trend_up:
            return 0.8
        elif action == 'HOLD':
            return 0.7
        else:
            return 0.3
    
    def _validate_volume(self, prices: List[float], volumes: List[float], action: str) -> float:
        """Validate volume confirmation"""
        if not volumes or len(volumes) < 5:
            return 0.5
        
        volume_array = np.array(volumes)
        avg_volume = np.mean(volume_array)
        recent_volume = np.mean(volume_array[-5:])
        
        # Volume should confirm the move
        if recent_volume > avg_volume * 1.2:
            return 0.8
        elif recent_volume > avg_volume:
            return 0.6
        else:
            return 0.4
    
    def _validate_market_structure(self, prices: List[float], action: str) -> float:
        """Validate market structure"""
        if len(prices) < 20:
            return 0.5
        
        price_array = np.array(prices)
        
        # Find swing highs and lows
        recent_high = np.max(price_array[-10:])
        recent_low = np.min(price_array[-10:])
        prev_high = np.max(price_array[-20:-10])
        prev_low = np.min(price_array[-20:-10])
        
        # Bullish structure: HH + HL
        bullish = recent_high > prev_high and recent_low > prev_low
        # Bearish structure: LH + LL
        bearish = recent_high < prev_high and recent_low < prev_low
        
        if action == 'BUY' and bullish:
            return 0.85
        elif action == 'SELL' and bearish:
            return 0.85
        elif action == 'HOLD':
            return 0.7
        else:
            return 0.35
    
    def _validate_indicators(self, indicators: Dict[str, Any], action: str) -> float:
        """Validate indicator alignment"""
        if not indicators:
            return 0.5
        
        score = 0.5
        confirmations = 0
        
        # RSI
        rsi = indicators.get('rsi', 50)
        if action == 'BUY' and rsi < 70:
            confirmations += 1
        elif action == 'SELL' and rsi > 30:
            confirmations += 1
        
        # MACD
        macd = indicators.get('macd', {})
        macd_line = macd.get('macd', 0)
        signal_line = macd.get('signal', 0)
        if action == 'BUY' and macd_line > signal_line:
            confirmations += 1
        elif action == 'SELL' and macd_line < signal_line:
            confirmations += 1
        
        # Moving Averages
        ma_fast = indicators.get('ma_fast', 0)
        ma_slow = indicators.get('ma_slow', 0)
        if ma_fast and ma_slow:
            if action == 'BUY' and ma_fast > ma_slow:
                confirmations += 1
            elif action == 'SELL' and ma_fast < ma_slow:
                confirmations += 1
        
        score = 0.4 + (confirmations * 0.2)
        return min(1.0, score)
    
    def _validate_regime_alignment(self, regime: str, action: str) -> float:
        """Validate action alignment with market regime"""
        regime_action_map = {
            'trending_up': {'BUY': 0.9, 'SELL': 0.3, 'HOLD': 0.5},
            'trending_down': {'BUY': 0.3, 'SELL': 0.9, 'HOLD': 0.5},
            'ranging': {'BUY': 0.5, 'SELL': 0.5, 'HOLD': 0.7},
            'high_volatility': {'BUY': 0.4, 'SELL': 0.4, 'HOLD': 0.8},
            'low_volatility': {'BUY': 0.6, 'SELL': 0.6, 'HOLD': 0.6},
            'unknown': {'BUY': 0.5, 'SELL': 0.5, 'HOLD': 0.6}
        }
        
        return regime_action_map.get(regime, regime_action_map['unknown']).get(action, 0.5)
    
    def _validate_liquidity(self, market_data: Dict[str, Any]) -> float:
        """Validate market liquidity"""
        volumes = market_data.get('volumes', [])
        spread = market_data.get('spread', 0)
        
        score = 0.7  # Default
        
        if volumes:
            avg_volume = np.mean(volumes)
            recent_volume = np.mean(volumes[-5:]) if len(volumes) >= 5 else avg_volume
            
            if recent_volume > avg_volume * 1.5:
                score = 0.9
            elif recent_volume > avg_volume:
                score = 0.7
            else:
                score = 0.5
        
        # Adjust for spread
        if spread > 0:
            if spread < 0.0001:  # Tight spread
                score += 0.1
            elif spread > 0.001:  # Wide spread
                score -= 0.2
        
        return max(0, min(1, score))
    
    def _validate_volatility(self, market_data: Dict[str, Any], signal: Dict[str, Any]) -> float:
        """Validate volatility conditions"""
        prices = market_data.get('prices', [])
        if len(prices) < 10:
            return 0.5
        
        price_array = np.array(prices)
        returns = np.diff(price_array) / price_array[:-1]
        volatility = np.std(returns)
        
        # Optimal volatility range
        if 0.005 < volatility < 0.02:
            return 0.8
        elif 0.002 < volatility < 0.03:
            return 0.6
        elif volatility > 0.05:
            return 0.2  # Too volatile
        else:
            return 0.4  # Too quiet
    
    def _validate_correlations(self, context: Dict[str, Any]) -> float:
        """Validate correlation conditions"""
        correlations = context.get('correlations', {})
        if not correlations:
            return 0.6  # Neutral
        
        # Check for correlation breakdown
        breakdown = correlations.get('breakdown', False)
        if breakdown:
            return 0.3
        
        # Check correlation strength
        strength = correlations.get('strength', 0.5)
        return 0.5 + (strength * 0.5)
    
    def _validate_news_impact(self, context: Dict[str, Any]) -> float:
        """Validate news impact on trading"""
        news = context.get('news', [])
        upcoming_events = context.get('upcoming_events', [])
        
        score = 0.8  # Default - no news is good
        
        # High impact news reduces score
        for item in news:
            impact = item.get('impact', 'low')
            if impact == 'high':
                score -= 0.3
            elif impact == 'medium':
                score -= 0.1
        
        # Upcoming events
        for event in upcoming_events:
            minutes_until = event.get('minutes_until', 60)
            if minutes_until < 30:
                score -= 0.3
            elif minutes_until < 60:
                score -= 0.1
        
        return max(0, min(1, score))
    
    def _determine_status(
        self,
        technical: TechnicalValidation,
        contextual: ContextualValidation,
        pattern_validity: float,
        manipulation_risk: float,
        overall_score: float
    ) -> Tuple[ValidationStatus, str, List[str]]:
        """Determine validation status and recommendation"""
        reasons = []
        
        # Check critical failures
        if manipulation_risk > self.max_manipulation_risk:
            reasons.append(f"High manipulation risk: {manipulation_risk:.2%}")
        
        if not technical.passed:
            reasons.append(f"Technical validation failed: {technical.overall_score:.2%}")
        
        if not contextual.passed:
            reasons.append(f"Contextual validation failed: {contextual.overall_score:.2%}")
        
        if pattern_validity < 0.4:
            reasons.append(f"Low pattern validity: {pattern_validity:.2%}")
        
        # Determine status
        if manipulation_risk > 0.5 or overall_score < 0.4:
            status = ValidationStatus.FAILED
            recommendation = "REJECT - Do not execute this signal"
        elif overall_score < self.min_overall_score or len(reasons) > 1:
            status = ValidationStatus.WARNING
            recommendation = "CAUTION - Consider reducing position size"
        else:
            status = ValidationStatus.PASSED
            recommendation = "PROCEED - Signal validated"
            reasons = ["All validation criteria met"]
        
        return status, recommendation, reasons
    
    def get_validation_stats(self) -> Dict[str, Any]:
        """Get validation statistics"""
        total = self.validation_stats['total']
        return {
            'total_validations': total,
            'passed': self.validation_stats['passed'],
            'failed': self.validation_stats['failed'],
            'warnings': self.validation_stats['warnings'],
            'pass_rate': self.validation_stats['passed'] / total if total > 0 else 0,
            'fail_rate': self.validation_stats['failed'] / total if total > 0 else 0
        }
