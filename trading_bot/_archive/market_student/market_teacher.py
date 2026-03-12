"""
Market Teacher - The Market as the Ultimate Teacher
====================================================

The market teaches through:
- Price action
- Volatility shifts
- Volume patterns
- Liquidity changes
- Trend continuations and failures
- Order flow imbalances
- Macro events and news shocks
- Seasonal effects

Every candle is a lesson.
Every trend is a lecture.
Every loss is a correction.
Every win is a confirmation.

Version: 1.0.0
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum
import logging
import numpy as np
from collections import deque
import numpy

logger = logging.getLogger(__name__)


# =============================================================================
# LESSON TYPES
# =============================================================================

class LessonType(Enum):
    """Types of lessons the market teaches"""
    
    # Price Action Lessons
    PRICE_ACTION = "price_action"
    SUPPORT_RESISTANCE = "support_resistance"
    BREAKOUT = "breakout"
    REVERSAL = "reversal"
    CONTINUATION = "continuation"
    
    # Volatility Lessons
    VOLATILITY_EXPANSION = "volatility_expansion"
    VOLATILITY_CONTRACTION = "volatility_contraction"
    VOLATILITY_REGIME_CHANGE = "volatility_regime_change"
    
    # Volume Lessons
    VOLUME_CONFIRMATION = "volume_confirmation"
    VOLUME_DIVERGENCE = "volume_divergence"
    VOLUME_CLIMAX = "volume_climax"
    
    # Trend Lessons
    TREND_STRENGTH = "trend_strength"
    TREND_EXHAUSTION = "trend_exhaustion"
    TREND_FAILURE = "trend_failure"
    
    # Liquidity Lessons
    LIQUIDITY_VOID = "liquidity_void"
    LIQUIDITY_GRAB = "liquidity_grab"
    STOP_HUNT = "stop_hunt"
    
    # Order Flow Lessons
    ORDER_FLOW_IMBALANCE = "order_flow_imbalance"
    ABSORPTION = "absorption"
    INSTITUTIONAL_ACTIVITY = "institutional_activity"
    
    # Macro Lessons
    NEWS_IMPACT = "news_impact"
    ECONOMIC_EVENT = "economic_event"
    CORRELATION_SHIFT = "correlation_shift"
    
    # Timing Lessons
    SESSION_BEHAVIOR = "session_behavior"
    TIME_OF_DAY = "time_of_day"
    SEASONAL_PATTERN = "seasonal_pattern"
    
    # Risk Lessons
    DRAWDOWN_WARNING = "drawdown_warning"
    RISK_REWARD_OUTCOME = "risk_reward_outcome"
    POSITION_SIZE_FEEDBACK = "position_size_feedback"


class LessonSeverity(Enum):
    """Severity/importance of a lesson"""
    CRITICAL = "critical"      # Must learn immediately
    HIGH = "high"              # Important lesson
    MEDIUM = "medium"          # Standard lesson
    LOW = "low"                # Minor observation
    INFORMATIONAL = "info"     # Background information


# =============================================================================
# MARKET LESSON
# =============================================================================

@dataclass
class MarketLesson:
    """A lesson taught by the market"""
    
    lesson_id: str
    lesson_type: LessonType
    severity: LessonSeverity
    
    # What happened
    description: str
    market_context: Dict[str, Any]
    
    # The teaching
    what_market_showed: str
    what_ai_expected: str
    discrepancy: str
    
    # The lesson
    lesson_learned: str
    actionable_insight: str
    
    # Metrics
    confidence: float  # 0.0 to 1.0
    impact_score: float  # How impactful this lesson is
    
    # Timing
    timestamp: datetime
    symbol: str
    timeframe: str
    
    # Related data
    price_data: Dict[str, Any] = field(default_factory=dict)
    indicators: Dict[str, Any] = field(default_factory=dict)
    trade_context: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'lesson_id': self.lesson_id,
            'lesson_type': self.lesson_type.value,
            'severity': self.severity.value,
            'description': self.description,
            'what_market_showed': self.what_market_showed,
            'what_ai_expected': self.what_ai_expected,
            'discrepancy': self.discrepancy,
            'lesson_learned': self.lesson_learned,
            'actionable_insight': self.actionable_insight,
            'confidence': self.confidence,
            'impact_score': self.impact_score,
            'timestamp': self.timestamp.isoformat(),
            'symbol': self.symbol,
            'timeframe': self.timeframe,
        }


# =============================================================================
# MARKET TEACHER
# =============================================================================

class MarketTeacher:
    """
    The Market as Teacher - Extracts lessons from market behavior.
    
    The market teaches through every price movement, every volume spike,
    every trend continuation and failure. This class observes and
    extracts actionable lessons.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Lesson storage
        self._lessons: List[MarketLesson] = []
        self._lesson_buffer: deque = deque(maxlen=10000)
        
        # Pattern recognition thresholds
        self._volatility_threshold = self.config.get('volatility_threshold', 1.5)
        self._volume_threshold = self.config.get('volume_threshold', 2.0)
        self._trend_threshold = self.config.get('trend_threshold', 0.7)
        
        # Lesson counters
        self._lesson_counts: Dict[LessonType, int] = {lt: 0 for lt in LessonType}
        
        logger.info("MarketTeacher initialized - Ready to learn from the market")
    
    def observe_price_action(
        self,
        symbol: str,
        timeframe: str,
        ohlcv: Dict[str, Any],
        indicators: Dict[str, Any],
        ai_prediction: Optional[Dict[str, Any]] = None
    ) -> List[MarketLesson]:
        """
        Observe price action and extract lessons.
        
        Args:
            symbol: Trading symbol
            timeframe: Timeframe
            ohlcv: OHLCV data (open, high, low, close, volume)
            indicators: Technical indicators
            ai_prediction: What the AI predicted (if any)
            
        Returns:
            List of lessons extracted
        """
        lessons = []
        now = datetime.now()
        
        # Extract price action lessons
        lessons.extend(self._analyze_price_action(symbol, timeframe, ohlcv, indicators, ai_prediction, now))
        
        # Extract volatility lessons
        lessons.extend(self._analyze_volatility(symbol, timeframe, ohlcv, indicators, ai_prediction, now))
        
        # Extract volume lessons
        lessons.extend(self._analyze_volume(symbol, timeframe, ohlcv, indicators, ai_prediction, now))
        
        # Store lessons
        for lesson in lessons:
            self._lessons.append(lesson)
            self._lesson_buffer.append(lesson)
            self._lesson_counts[lesson.lesson_type] += 1
        
        return lessons
    
    def observe_trade_outcome(
        self,
        symbol: str,
        trade: Dict[str, Any],
        market_data: Dict[str, Any],
        signal: Dict[str, Any]
    ) -> List[MarketLesson]:
        """
        Observe a trade outcome and extract lessons.
        
        Args:
            symbol: Trading symbol
            trade: Trade data (entry, exit, pnl, etc.)
            market_data: Market data at trade time
            signal: The signal that triggered the trade
            
        Returns:
            List of lessons extracted
        """
        lessons = []
        now = datetime.now()
        
        pnl = trade.get('pnl', 0)
        entry_price = trade.get('entry_price', 0)
        exit_price = trade.get('exit_price', 0)
        direction = trade.get('direction', 'long')
        
        # Determine if trade was successful
        is_win = pnl > 0
        
        # Extract risk/reward lesson
        risk = trade.get('risk', 0)
        reward = abs(pnl)
        rr_ratio = reward / risk if risk > 0 else 0
        
        lesson_id = f"trade_{trade.get('id', now.timestamp())}"
        
        if is_win:
            # Winning trade - what did the market confirm?
            lesson = MarketLesson(
                lesson_id=lesson_id,
                lesson_type=LessonType.RISK_REWARD_OUTCOME,
                severity=LessonSeverity.MEDIUM,
                description=f"Winning {direction} trade on {symbol}",
                market_context=market_data,
                what_market_showed=f"Price moved {direction} as predicted, reaching target",
                what_ai_expected=f"Expected {direction} movement based on signal confidence {signal.get('confidence', 0):.2%}",
                discrepancy="None - prediction was correct",
                lesson_learned=f"Signal pattern with confidence {signal.get('confidence', 0):.2%} in this market context is reliable",
                actionable_insight="Continue using this signal pattern in similar conditions",
                confidence=0.8,
                impact_score=0.6,
                timestamp=now,
                symbol=symbol,
                timeframe=trade.get('timeframe', 'unknown'),
                trade_context=trade
            )
            lessons.append(lesson)
        else:
            # Losing trade - what did the market teach?
            lesson = MarketLesson(
                lesson_id=lesson_id,
                lesson_type=LessonType.RISK_REWARD_OUTCOME,
                severity=LessonSeverity.HIGH,
                description=f"Losing {direction} trade on {symbol}",
                market_context=market_data,
                what_market_showed=f"Price moved against {direction} position",
                what_ai_expected=f"Expected {direction} movement based on signal",
                discrepancy=f"Market moved opposite to prediction, loss of {abs(pnl):.2f}",
                lesson_learned=self._extract_loss_lesson(trade, market_data, signal),
                actionable_insight=self._generate_improvement_insight(trade, market_data, signal),
                confidence=0.9,  # High confidence in loss lessons
                impact_score=0.8,  # Losses are impactful lessons
                timestamp=now,
                symbol=symbol,
                timeframe=trade.get('timeframe', 'unknown'),
                trade_context=trade
            )
            lessons.append(lesson)
        
        # Store lessons
        for lesson in lessons:
            self._lessons.append(lesson)
            self._lesson_buffer.append(lesson)
            self._lesson_counts[lesson.lesson_type] += 1
        
        return lessons
    
    def observe_regime_change(
        self,
        symbol: str,
        old_regime: str,
        new_regime: str,
        market_data: Dict[str, Any]
    ) -> MarketLesson:
        """
        Observe a market regime change and extract lesson.
        
        Args:
            symbol: Trading symbol
            old_regime: Previous market regime
            new_regime: New market regime
            market_data: Current market data
            
        Returns:
            Lesson about the regime change
        """
        now = datetime.now()
        
        lesson = MarketLesson(
            lesson_id=f"regime_{now.timestamp()}",
            lesson_type=LessonType.VOLATILITY_REGIME_CHANGE,
            severity=LessonSeverity.HIGH,
            description=f"Market regime changed from {old_regime} to {new_regime}",
            market_context=market_data,
            what_market_showed=f"Regime transition: {old_regime} → {new_regime}",
            what_ai_expected="Continuation of previous regime",
            discrepancy=f"Regime changed, requiring strategy adaptation",
            lesson_learned=f"Market transitioned to {new_regime} regime - adjust strategy parameters",
            actionable_insight=self._get_regime_adaptation_insight(new_regime),
            confidence=0.85,
            impact_score=0.9,
            timestamp=now,
            symbol=symbol,
            timeframe='regime',
        )
        
        self._lessons.append(lesson)
        self._lesson_buffer.append(lesson)
        self._lesson_counts[lesson.lesson_type] += 1
        
        return lesson
    
    def observe_news_event(
        self,
        symbol: str,
        event: Dict[str, Any],
        market_reaction: Dict[str, Any]
    ) -> MarketLesson:
        """
        Observe a news event and market reaction.
        
        Args:
            symbol: Trading symbol
            event: News event data
            market_reaction: How the market reacted
            
        Returns:
            Lesson about news impact
        """
        now = datetime.now()
        
        event_type = event.get('type', 'unknown')
        impact = event.get('impact', 'medium')
        price_change = market_reaction.get('price_change_pct', 0)
        volatility_change = market_reaction.get('volatility_change', 0)
        
        lesson = MarketLesson(
            lesson_id=f"news_{now.timestamp()}",
            lesson_type=LessonType.NEWS_IMPACT,
            severity=LessonSeverity.HIGH if impact == 'high' else LessonSeverity.MEDIUM,
            description=f"{event_type} event on {symbol}",
            market_context=market_reaction,
            what_market_showed=f"Price changed {price_change:.2%}, volatility changed {volatility_change:.2%}",
            what_ai_expected="Normal market conditions",
            discrepancy=f"News event caused {impact} impact deviation",
            lesson_learned=f"{event_type} events typically cause {abs(price_change):.2%} price movement",
            actionable_insight=f"Reduce position size or avoid trading during {event_type} events",
            confidence=0.75,
            impact_score=0.7 if impact == 'high' else 0.5,
            timestamp=now,
            symbol=symbol,
            timeframe='event',
        )
        
        self._lessons.append(lesson)
        self._lesson_buffer.append(lesson)
        self._lesson_counts[lesson.lesson_type] += 1
        
        return lesson
    
    def _analyze_price_action(
        self,
        symbol: str,
        timeframe: str,
        ohlcv: Dict[str, Any],
        indicators: Dict[str, Any],
        ai_prediction: Optional[Dict[str, Any]],
        timestamp: datetime
    ) -> List[MarketLesson]:
        """Analyze price action for lessons"""
        lessons = []
        
        close = ohlcv.get('close', [])
        high = ohlcv.get('high', [])
        low = ohlcv.get('low', [])
        
        if len(close) < 2:
            return lessons
        
        # Check for breakout
        recent_high = max(high[-20:]) if len(high) >= 20 else max(high)
        recent_low = min(low[-20:]) if len(low) >= 20 else min(low)
        current_close = close[-1]
        
        if current_close > recent_high:
            lessons.append(MarketLesson(
                lesson_id=f"breakout_{timestamp.timestamp()}",
                lesson_type=LessonType.BREAKOUT,
                severity=LessonSeverity.MEDIUM,
                description=f"Bullish breakout on {symbol}",
                market_context={'recent_high': recent_high, 'current_close': current_close},
                what_market_showed="Price broke above recent resistance",
                what_ai_expected=ai_prediction.get('expected', 'unknown') if ai_prediction else 'unknown',
                discrepancy="Breakout occurred" if not ai_prediction else "",
                lesson_learned="Breakout above resistance - potential trend continuation",
                actionable_insight="Consider long positions with stops below breakout level",
                confidence=0.7,
                impact_score=0.6,
                timestamp=timestamp,
                symbol=symbol,
                timeframe=timeframe,
                price_data=ohlcv,
                indicators=indicators
            ))
        
        elif current_close < recent_low:
            lessons.append(MarketLesson(
                lesson_id=f"breakdown_{timestamp.timestamp()}",
                lesson_type=LessonType.BREAKOUT,
                severity=LessonSeverity.MEDIUM,
                description=f"Bearish breakdown on {symbol}",
                market_context={'recent_low': recent_low, 'current_close': current_close},
                what_market_showed="Price broke below recent support",
                what_ai_expected=ai_prediction.get('expected', 'unknown') if ai_prediction else 'unknown',
                discrepancy="Breakdown occurred" if not ai_prediction else "",
                lesson_learned="Breakdown below support - potential trend reversal",
                actionable_insight="Consider short positions with stops above breakdown level",
                confidence=0.7,
                impact_score=0.6,
                timestamp=timestamp,
                symbol=symbol,
                timeframe=timeframe,
                price_data=ohlcv,
                indicators=indicators
            ))
        
        return lessons
    
    def _analyze_volatility(
        self,
        symbol: str,
        timeframe: str,
        ohlcv: Dict[str, Any],
        indicators: Dict[str, Any],
        ai_prediction: Optional[Dict[str, Any]],
        timestamp: datetime
    ) -> List[MarketLesson]:
        """Analyze volatility for lessons"""
        lessons = []
        
        atr = indicators.get('atr', [])
        if len(atr) < 20:
            return lessons
        
        current_atr = atr[-1]
        avg_atr = np.mean(atr[-20:])
        
        # Volatility expansion
        if current_atr > avg_atr * self._volatility_threshold:
            lessons.append(MarketLesson(
                lesson_id=f"vol_expansion_{timestamp.timestamp()}",
                lesson_type=LessonType.VOLATILITY_EXPANSION,
                severity=LessonSeverity.HIGH,
                description=f"Volatility expansion on {symbol}",
                market_context={'current_atr': current_atr, 'avg_atr': avg_atr},
                what_market_showed=f"ATR expanded to {current_atr/avg_atr:.1f}x average",
                what_ai_expected="Normal volatility",
                discrepancy="Significant volatility increase",
                lesson_learned="High volatility environment - adjust position sizing",
                actionable_insight="Reduce position size, widen stops, or avoid trading",
                confidence=0.85,
                impact_score=0.8,
                timestamp=timestamp,
                symbol=symbol,
                timeframe=timeframe,
                indicators=indicators
            ))
        
        # Volatility contraction
        elif current_atr < avg_atr * 0.5:
            lessons.append(MarketLesson(
                lesson_id=f"vol_contraction_{timestamp.timestamp()}",
                lesson_type=LessonType.VOLATILITY_CONTRACTION,
                severity=LessonSeverity.MEDIUM,
                description=f"Volatility contraction on {symbol}",
                market_context={'current_atr': current_atr, 'avg_atr': avg_atr},
                what_market_showed=f"ATR contracted to {current_atr/avg_atr:.1f}x average",
                what_ai_expected="Normal volatility",
                discrepancy="Significant volatility decrease",
                lesson_learned="Low volatility - potential breakout setup",
                actionable_insight="Watch for breakout, prepare for volatility expansion",
                confidence=0.75,
                impact_score=0.5,
                timestamp=timestamp,
                symbol=symbol,
                timeframe=timeframe,
                indicators=indicators
            ))
        
        return lessons
    
    def _analyze_volume(
        self,
        symbol: str,
        timeframe: str,
        ohlcv: Dict[str, Any],
        indicators: Dict[str, Any],
        ai_prediction: Optional[Dict[str, Any]],
        timestamp: datetime
    ) -> List[MarketLesson]:
        """Analyze volume for lessons"""
        lessons = []
        
        volume = ohlcv.get('volume', [])
        close = ohlcv.get('close', [])
        
        if len(volume) < 20 or len(close) < 2:
            return lessons
        
        current_volume = volume[-1]
        avg_volume = np.mean(volume[-20:])
        price_change = (close[-1] - close[-2]) / close[-2] if close[-2] != 0 else 0
        
        # Volume spike
        if current_volume > avg_volume * self._volume_threshold:
            # Check if volume confirms price direction
            if (price_change > 0 and current_volume > avg_volume * 2) or \
               (price_change < 0 and current_volume > avg_volume * 2):
                lessons.append(MarketLesson(
                    lesson_id=f"vol_confirm_{timestamp.timestamp()}",
                    lesson_type=LessonType.VOLUME_CONFIRMATION,
                    severity=LessonSeverity.MEDIUM,
                    description=f"Volume confirms price movement on {symbol}",
                    market_context={'volume_ratio': current_volume/avg_volume, 'price_change': price_change},
                    what_market_showed=f"Volume {current_volume/avg_volume:.1f}x average with {price_change:.2%} price change",
                    what_ai_expected="Normal volume",
                    discrepancy="High volume confirms move",
                    lesson_learned="Volume confirmation increases move reliability",
                    actionable_insight="Trust signals with volume confirmation",
                    confidence=0.8,
                    impact_score=0.6,
                    timestamp=timestamp,
                    symbol=symbol,
                    timeframe=timeframe,
                    price_data=ohlcv
                ))
            else:
                # Volume divergence
                lessons.append(MarketLesson(
                    lesson_id=f"vol_diverge_{timestamp.timestamp()}",
                    lesson_type=LessonType.VOLUME_DIVERGENCE,
                    severity=LessonSeverity.HIGH,
                    description=f"Volume divergence on {symbol}",
                    market_context={'volume_ratio': current_volume/avg_volume, 'price_change': price_change},
                    what_market_showed=f"High volume but weak price movement",
                    what_ai_expected="Volume should confirm price",
                    discrepancy="Volume diverging from price",
                    lesson_learned="Volume divergence may signal reversal",
                    actionable_insight="Be cautious, potential trend exhaustion",
                    confidence=0.75,
                    impact_score=0.7,
                    timestamp=timestamp,
                    symbol=symbol,
                    timeframe=timeframe,
                    price_data=ohlcv
                ))
        
        return lessons
    
    def _extract_loss_lesson(
        self,
        trade: Dict[str, Any],
        market_data: Dict[str, Any],
        signal: Dict[str, Any]
    ) -> str:
        """Extract lesson from a losing trade"""
        reasons = []
        
        # Check signal confidence
        confidence = signal.get('confidence', 0)
        if confidence < 0.6:
            reasons.append(f"Signal confidence was low ({confidence:.2%})")
        
        # Check market conditions
        volatility = market_data.get('volatility', 'normal')
        if volatility == 'high':
            reasons.append("Market was in high volatility regime")
        
        # Check timing
        if market_data.get('near_news_event', False):
            reasons.append("Trade was near a news event")
        
        # Check risk management
        if trade.get('stop_hit', False):
            reasons.append("Stop loss was hit - position sizing may need adjustment")
        
        if not reasons:
            reasons.append("Market moved against prediction - review signal criteria")
        
        return "; ".join(reasons)
    
    def _generate_improvement_insight(
        self,
        trade: Dict[str, Any],
        market_data: Dict[str, Any],
        signal: Dict[str, Any]
    ) -> str:
        """Generate actionable improvement insight"""
        insights = []
        
        confidence = signal.get('confidence', 0)
        if confidence < 0.6:
            insights.append("Increase minimum confidence threshold for entries")
        
        volatility = market_data.get('volatility', 'normal')
        if volatility == 'high':
            insights.append("Reduce position size in high volatility")
        
        if market_data.get('near_news_event', False):
            insights.append("Avoid trading around major news events")
        
        if trade.get('slippage', 0) > 0.002:
            insights.append("Improve execution timing or use limit orders")
        
        if not insights:
            insights.append("Review entry criteria and market structure alignment")
        
        return "; ".join(insights)
    
    def _get_regime_adaptation_insight(self, regime: str) -> str:
        """Get adaptation insight for a market regime"""
        regime_insights = {
            'trending': "Use trend-following strategies, trail stops, let winners run",
            'ranging': "Use mean-reversion strategies, take profits at range boundaries",
            'volatile': "Reduce position size, widen stops, avoid overtrading",
            'quiet': "Reduce expectations, watch for breakout setups",
            'crisis': "Reduce exposure, prioritize capital preservation",
        }
        return regime_insights.get(regime, "Adapt strategy parameters to new regime")
    
    def get_recent_lessons(self, limit: int = 100) -> List[MarketLesson]:
        """Get recent lessons"""
        return list(self._lesson_buffer)[-limit:]
    
    def get_lessons_by_type(self, lesson_type: LessonType) -> List[MarketLesson]:
        """Get lessons of a specific type"""
        return [l for l in self._lessons if l.lesson_type == lesson_type]
    
    def get_high_impact_lessons(self, min_impact: float = 0.7) -> List[MarketLesson]:
        """Get high-impact lessons"""
        return [l for l in self._lessons if l.impact_score >= min_impact]
    
    def get_lesson_statistics(self) -> Dict[str, Any]:
        """Get lesson statistics"""
        return {
            'total_lessons': len(self._lessons),
            'lessons_by_type': {lt.value: count for lt, count in self._lesson_counts.items()},
            'avg_confidence': np.mean([l.confidence for l in self._lessons]) if self._lessons else 0,
            'avg_impact': np.mean([l.impact_score for l in self._lessons]) if self._lessons else 0,
            'high_severity_count': sum(1 for l in self._lessons if l.severity in [LessonSeverity.CRITICAL, LessonSeverity.HIGH]),
        }
    
    def get_actionable_insights(self, limit: int = 10) -> List[str]:
        """Get top actionable insights from recent lessons"""
        recent = sorted(self._lessons, key=lambda l: l.impact_score, reverse=True)[:limit]
        return [l.actionable_insight for l in recent]
