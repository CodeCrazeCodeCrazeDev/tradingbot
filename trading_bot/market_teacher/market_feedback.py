"""
Market Feedback System
=======================
Processes market feedback at different time horizons.

Feedback Types:
- Immediate (microseconds to seconds): Execution quality, price reaction
- Short-term (minutes to hours): Directional validation, volatility
- Medium-term (hours to days): Win rate calibration, regime recognition
- Long-term (weeks to months): Structural changes, black swan learning
"""

import logging
import numpy as np
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple
from collections import deque
import numpy

logger = logging.getLogger(__name__)


class FeedbackType(Enum):
    """Types of market feedback"""
    IMMEDIATE = "immediate"          # Microseconds to seconds
    SHORT_TERM = "short_term"        # Minutes to hours
    MEDIUM_TERM = "medium_term"      # Hours to days
    LONG_TERM = "long_term"          # Weeks to months
    BLACK_SWAN = "black_swan"        # Extreme events


@dataclass
class MarketLesson:
    """A lesson learned from market feedback"""
    lesson_id: str
    feedback_type: FeedbackType
    description: str
    confidence: float
    market_event: str
    agent_action: str
    market_response: str
    extracted_knowledge: str
    proposed_adjustment: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    validated: bool = False
    
    def to_dict(self) -> Dict:
        return {
            'lesson_id': self.lesson_id,
            'feedback_type': self.feedback_type.value,
            'description': self.description,
            'confidence': self.confidence,
            'market_event': self.market_event,
            'agent_action': self.agent_action,
            'market_response': self.market_response,
            'extracted_knowledge': self.extracted_knowledge,
            'proposed_adjustment': self.proposed_adjustment,
            'timestamp': self.timestamp.isoformat(),
            'validated': self.validated
        }


class ImmediateFeedback:
    """
    Processes immediate market feedback (microseconds to seconds).
    
    Teaches about:
    - Execution quality (slippage, fill rate)
    - Immediate price reaction
    - Order book dynamics
    """
    
    def __init__(self):
        self.feedback_history: deque = deque(maxlen=10000)
        self.slippage_stats: List[float] = []
        self.fill_quality_stats: List[float] = []
        
    def process_execution_feedback(
        self,
        expected_price: float,
        actual_price: float,
        expected_size: float,
        filled_size: float,
        execution_time_ms: float
    ) -> MarketLesson:
        """Process execution quality feedback"""
        slippage = (actual_price - expected_price) / expected_price
        fill_rate = filled_size / expected_size if expected_size > 0 else 0
        
        self.slippage_stats.append(slippage)
        self.fill_quality_stats.append(fill_rate)
        
        # Determine lesson
        if slippage > 0.001:  # More than 10 bps slippage
            lesson = MarketLesson(
                lesson_id=f"imm_{datetime.now().timestamp()}",
                feedback_type=FeedbackType.IMMEDIATE,
                description="High slippage detected",
                confidence=0.8,
                market_event="Order execution",
                agent_action=f"Attempted to fill at {expected_price}",
                market_response=f"Filled at {actual_price} ({slippage*100:.2f}% slippage)",
                extracted_knowledge="Entry was aggressive/late, market moved against us",
                proposed_adjustment="Use more patient entry, reduce position size"
            )
        elif slippage < -0.001:  # Better than expected
            lesson = MarketLesson(
                lesson_id=f"imm_{datetime.now().timestamp()}",
                feedback_type=FeedbackType.IMMEDIATE,
                description="Favorable execution",
                confidence=0.8,
                market_event="Order execution",
                agent_action=f"Attempted to fill at {expected_price}",
                market_response=f"Filled at {actual_price} ({abs(slippage)*100:.2f}% improvement)",
                extracted_knowledge="Timing was excellent, market rewarded patience",
                proposed_adjustment="Reinforce current entry logic"
            )
        else:
            lesson = MarketLesson(
                lesson_id=f"imm_{datetime.now().timestamp()}",
                feedback_type=FeedbackType.IMMEDIATE,
                description="Normal execution",
                confidence=0.6,
                market_event="Order execution",
                agent_action=f"Attempted to fill at {expected_price}",
                market_response=f"Filled at {actual_price}",
                extracted_knowledge="Price prediction was accurate",
                proposed_adjustment=None
            )
        
        self.feedback_history.append(lesson)
        return lesson
    
    def process_price_reaction(
        self,
        entry_price: float,
        current_price: float,
        position_direction: str,
        seconds_elapsed: float
    ) -> MarketLesson:
        """Process immediate price reaction after entry"""
        if position_direction == "LONG":
            pnl_pct = (current_price - entry_price) / entry_price
        else:
            pnl_pct = (entry_price - current_price) / entry_price
        
        threshold = 0.001  # 10 bps
        
        if pnl_pct < -threshold:
            lesson = MarketLesson(
                lesson_id=f"imm_{datetime.now().timestamp()}",
                feedback_type=FeedbackType.IMMEDIATE,
                description="Immediate adverse price movement",
                confidence=0.7,
                market_event=f"Price moved against position within {seconds_elapsed}s",
                agent_action=f"Entered {position_direction} at {entry_price}",
                market_response=f"Price moved to {current_price} ({pnl_pct*100:.2f}%)",
                extracted_knowledge="Market disagrees with entry thesis",
                proposed_adjustment="Increase stop-loss sensitivity, reduce confidence in signal"
            )
        elif pnl_pct > threshold:
            lesson = MarketLesson(
                lesson_id=f"imm_{datetime.now().timestamp()}",
                feedback_type=FeedbackType.IMMEDIATE,
                description="Immediate favorable price movement",
                confidence=0.7,
                market_event=f"Price moved in favor within {seconds_elapsed}s",
                agent_action=f"Entered {position_direction} at {entry_price}",
                market_response=f"Price moved to {current_price} ({pnl_pct*100:.2f}%)",
                extracted_knowledge="Market agrees with entry thesis",
                proposed_adjustment="Consider adding to position, reinforce signal"
            )
        else:
            lesson = MarketLesson(
                lesson_id=f"imm_{datetime.now().timestamp()}",
                feedback_type=FeedbackType.IMMEDIATE,
                description="Price consolidation after entry",
                confidence=0.5,
                market_event=f"Price stable within {seconds_elapsed}s",
                agent_action=f"Entered {position_direction} at {entry_price}",
                market_response=f"Price at {current_price}",
                extracted_knowledge="Market is neutral/undecided",
                proposed_adjustment=None
            )
        
        self.feedback_history.append(lesson)
        return lesson
    
    def get_average_slippage(self) -> float:
        """Get average slippage"""
        if not self.slippage_stats:
            return 0.0
        return np.mean(self.slippage_stats)
    
    def get_fill_quality(self) -> float:
        """Get average fill quality"""
        if not self.fill_quality_stats:
            return 1.0
        return np.mean(self.fill_quality_stats)


class ShortTermFeedback:
    """
    Processes short-term market feedback (minutes to hours).
    
    Teaches about:
    - Directional conviction validation
    - Volatility regime
    - Trade outcome patterns
    """
    
    def __init__(self):
        self.feedback_history: deque = deque(maxlen=5000)
        self.trade_outcomes: List[Dict] = []
        
    def process_trade_outcome(
        self,
        entry_price: float,
        exit_price: float,
        direction: str,
        hold_time_minutes: float,
        expected_outcome: float,
        stop_loss: float,
        take_profit: float
    ) -> MarketLesson:
        """Process trade outcome feedback"""
        if direction == "LONG":
            actual_pnl = (exit_price - entry_price) / entry_price
        else:
            actual_pnl = (entry_price - exit_price) / entry_price
        
        hit_stop = actual_pnl <= -abs(stop_loss)
        hit_target = actual_pnl >= abs(take_profit)
        
        self.trade_outcomes.append({
            'pnl': actual_pnl,
            'hold_time': hold_time_minutes,
            'hit_stop': hit_stop,
            'hit_target': hit_target
        })
        
        # Determine lesson based on outcome
        if hit_target:
            if hold_time_minutes < 30:
                lesson = MarketLesson(
                    lesson_id=f"st_{datetime.now().timestamp()}",
                    feedback_type=FeedbackType.SHORT_TERM,
                    description="Quick target hit",
                    confidence=0.85,
                    market_event="Price reached target quickly",
                    agent_action=f"Entered {direction} at {entry_price}",
                    market_response=f"Target hit at {exit_price} in {hold_time_minutes:.0f}min",
                    extracted_knowledge="Strong directional thesis, correct timing",
                    proposed_adjustment="Increase confidence in similar setups"
                )
            else:
                lesson = MarketLesson(
                    lesson_id=f"st_{datetime.now().timestamp()}",
                    feedback_type=FeedbackType.SHORT_TERM,
                    description="Target hit after grind",
                    confidence=0.7,
                    market_event="Price eventually reached target",
                    agent_action=f"Entered {direction} at {entry_price}",
                    market_response=f"Target hit at {exit_price} in {hold_time_minutes:.0f}min",
                    extracted_knowledge="Correct direction but weak conviction from market",
                    proposed_adjustment="Consider earlier profit taking in similar conditions"
                )
        elif hit_stop:
            lesson = MarketLesson(
                lesson_id=f"st_{datetime.now().timestamp()}",
                feedback_type=FeedbackType.SHORT_TERM,
                description="Stop loss hit",
                confidence=0.8,
                market_event="Price reversed to stop loss",
                agent_action=f"Entered {direction} at {entry_price}",
                market_response=f"Stopped out at {exit_price}",
                extracted_knowledge="Signal was false, direction was wrong",
                proposed_adjustment="Reduce trust in this signal type, investigate failure"
            )
        else:
            lesson = MarketLesson(
                lesson_id=f"st_{datetime.now().timestamp()}",
                feedback_type=FeedbackType.SHORT_TERM,
                description="Trade closed without target/stop",
                confidence=0.6,
                market_event="Trade closed manually or on time",
                agent_action=f"Entered {direction} at {entry_price}",
                market_response=f"Exited at {exit_price} ({actual_pnl*100:.2f}%)",
                extracted_knowledge="Market was indifferent, catalyst didn't materialize",
                proposed_adjustment="Exit earlier on boredom, tighten stops"
            )
        
        self.feedback_history.append(lesson)
        return lesson
    
    def process_volatility_feedback(
        self,
        expected_volatility: float,
        actual_volatility: float,
        position_size: float
    ) -> MarketLesson:
        """Process volatility regime feedback"""
        vol_error = actual_volatility - expected_volatility
        vol_ratio = actual_volatility / max(expected_volatility, 0.001)
        
        if vol_ratio > 1.5:
            lesson = MarketLesson(
                lesson_id=f"st_{datetime.now().timestamp()}",
                feedback_type=FeedbackType.SHORT_TERM,
                description="Volatility higher than expected",
                confidence=0.75,
                market_event=f"Realized vol {actual_volatility:.2%} vs expected {expected_volatility:.2%}",
                agent_action=f"Positioned with size {position_size}",
                market_response=f"Volatility was {vol_ratio:.1f}x expected",
                extracted_knowledge="Underestimated risk, position was too large",
                proposed_adjustment="Increase volatility model bias, reduce position sizes"
            )
        elif vol_ratio < 0.7:
            lesson = MarketLesson(
                lesson_id=f"st_{datetime.now().timestamp()}",
                feedback_type=FeedbackType.SHORT_TERM,
                description="Volatility lower than expected",
                confidence=0.75,
                market_event=f"Realized vol {actual_volatility:.2%} vs expected {expected_volatility:.2%}",
                agent_action=f"Positioned with size {position_size}",
                market_response=f"Volatility was {vol_ratio:.1f}x expected",
                extracted_knowledge="Overestimated risk, could have sized larger",
                proposed_adjustment="Decrease volatility model bias, consider larger positions"
            )
        else:
            lesson = MarketLesson(
                lesson_id=f"st_{datetime.now().timestamp()}",
                feedback_type=FeedbackType.SHORT_TERM,
                description="Volatility as expected",
                confidence=0.6,
                market_event=f"Realized vol {actual_volatility:.2%} matched expected {expected_volatility:.2%}",
                agent_action=f"Positioned with size {position_size}",
                market_response="Volatility model was calibrated correctly",
                extracted_knowledge="Risk model is accurate",
                proposed_adjustment=None
            )
        
        self.feedback_history.append(lesson)
        return lesson
    
    def get_win_rate(self) -> float:
        """Calculate recent win rate"""
        if not self.trade_outcomes:
            return 0.5
        wins = sum(1 for t in self.trade_outcomes if t['pnl'] > 0)
        return wins / len(self.trade_outcomes)


class MediumTermFeedback:
    """
    Processes medium-term market feedback (hours to days).
    
    Teaches about:
    - Win rate calibration
    - Strategy effectiveness
    - Market regime recognition
    """
    
    def __init__(self):
        self.feedback_history: deque = deque(maxlen=1000)
        self.strategy_performance: Dict[str, List[float]] = {}
        self.regime_performance: Dict[str, Dict[str, float]] = {}
        
    def calibrate_win_rate(
        self,
        strategy_name: str,
        expected_win_rate: float,
        actual_trades: List[Dict],
        window: int = 50
    ) -> MarketLesson:
        """Calibrate win rate expectations based on actual performance"""
        if len(actual_trades) < window:
            return None
        
        recent_trades = actual_trades[-window:]
        actual_win_rate = sum(1 for t in recent_trades if t.get('pnl', 0) > 0) / len(recent_trades)
        
        calibration_error = actual_win_rate - expected_win_rate
        
        if abs(calibration_error) > 0.1:
            if actual_win_rate < 0.5:
                lesson = MarketLesson(
                    lesson_id=f"mt_{datetime.now().timestamp()}",
                    feedback_type=FeedbackType.MEDIUM_TERM,
                    description=f"Strategy {strategy_name} underperforming",
                    confidence=0.8,
                    market_event=f"Win rate {actual_win_rate:.1%} vs expected {expected_win_rate:.1%}",
                    agent_action=f"Using strategy {strategy_name}",
                    market_response=f"Strategy is now unprofitable (win rate < 50%)",
                    extracted_knowledge="Market conditions have changed, strategy edge has degraded",
                    proposed_adjustment=f"Deprecate strategy, reduce usage by 50%"
                )
            else:
                lesson = MarketLesson(
                    lesson_id=f"mt_{datetime.now().timestamp()}",
                    feedback_type=FeedbackType.MEDIUM_TERM,
                    description=f"Strategy {strategy_name} expectations off",
                    confidence=0.7,
                    market_event=f"Win rate {actual_win_rate:.1%} vs expected {expected_win_rate:.1%}",
                    agent_action=f"Using strategy {strategy_name}",
                    market_response=f"Actual performance differs from expectation",
                    extracted_knowledge="Need to recalibrate expectations",
                    proposed_adjustment=f"Update expected win rate to {0.7*expected_win_rate + 0.3*actual_win_rate:.1%}"
                )
        else:
            lesson = MarketLesson(
                lesson_id=f"mt_{datetime.now().timestamp()}",
                feedback_type=FeedbackType.MEDIUM_TERM,
                description=f"Strategy {strategy_name} well-calibrated",
                confidence=0.6,
                market_event=f"Win rate {actual_win_rate:.1%} matches expected {expected_win_rate:.1%}",
                agent_action=f"Using strategy {strategy_name}",
                market_response="Performance matches expectations",
                extracted_knowledge="Model is well-calibrated",
                proposed_adjustment=None
            )
        
        self.feedback_history.append(lesson)
        return lesson
    
    def learn_regime_performance(
        self,
        strategy_name: str,
        regime: str,
        performance: float
    ) -> MarketLesson:
        """Learn which strategies work in which regimes"""
        if strategy_name not in self.regime_performance:
            self.regime_performance[strategy_name] = {}
        
        if regime not in self.regime_performance[strategy_name]:
            self.regime_performance[strategy_name][regime] = []
        
        self.regime_performance[strategy_name][regime].append(performance)
        
        # Calculate regime-specific performance
        regime_perf = self.regime_performance[strategy_name][regime]
        avg_perf = np.mean(regime_perf) if regime_perf else 0
        
        if len(regime_perf) >= 10:
            if avg_perf > 0.6:
                affinity = "HIGH"
                adjustment = f"Use {strategy_name} more in {regime} regime"
            elif avg_perf < 0.4:
                affinity = "LOW"
                adjustment = f"Avoid {strategy_name} in {regime} regime"
            else:
                affinity = "NEUTRAL"
                adjustment = None
            
            lesson = MarketLesson(
                lesson_id=f"mt_{datetime.now().timestamp()}",
                feedback_type=FeedbackType.MEDIUM_TERM,
                description=f"Regime-strategy affinity learned",
                confidence=0.75,
                market_event=f"Observed {strategy_name} in {regime} regime",
                agent_action=f"Deployed {strategy_name} during {regime}",
                market_response=f"Average performance: {avg_perf:.1%}",
                extracted_knowledge=f"{strategy_name} has {affinity} affinity for {regime}",
                proposed_adjustment=adjustment
            )
            
            self.feedback_history.append(lesson)
            return lesson
        
        return None


class LongTermFeedback:
    """
    Processes long-term market feedback (weeks to months).
    
    Teaches about:
    - Structural market changes
    - Strategy decay
    - Edge degradation
    """
    
    def __init__(self):
        self.feedback_history: deque = deque(maxlen=500)
        self.strategy_sharpe_history: Dict[str, List[Tuple[datetime, float]]] = {}
        
    def detect_structural_change(
        self,
        strategy_name: str,
        historical_sharpe: float,
        recent_sharpe: float,
        window_days: int = 90
    ) -> Optional[MarketLesson]:
        """Detect structural market changes affecting strategy"""
        sharpe_degradation = historical_sharpe - recent_sharpe
        
        if sharpe_degradation > 1.0:
            lesson = MarketLesson(
                lesson_id=f"lt_{datetime.now().timestamp()}",
                feedback_type=FeedbackType.LONG_TERM,
                description=f"Strategy {strategy_name} edge has degraded",
                confidence=0.85,
                market_event=f"Sharpe dropped from {historical_sharpe:.2f} to {recent_sharpe:.2f}",
                agent_action=f"Continued using {strategy_name}",
                market_response="Market structure has fundamentally changed",
                extracted_knowledge="This edge no longer exists. Find a new one.",
                proposed_adjustment=f"Deprecate {strategy_name}, trigger research sprint"
            )
            
            self.feedback_history.append(lesson)
            return lesson
        
        return None
    
    def track_strategy_evolution(
        self,
        strategy_name: str,
        current_sharpe: float
    ):
        """Track strategy performance over time"""
        if strategy_name not in self.strategy_sharpe_history:
            self.strategy_sharpe_history[strategy_name] = []
        
        self.strategy_sharpe_history[strategy_name].append(
            (datetime.now(), current_sharpe)
        )
        
        # Keep only last 365 days
        cutoff = datetime.now() - timedelta(days=365)
        self.strategy_sharpe_history[strategy_name] = [
            (dt, sharpe) for dt, sharpe in self.strategy_sharpe_history[strategy_name]
            if dt > cutoff
        ]


class BlackSwanLearner:
    """
    Learns from black swan events (extreme, unexpected events).
    
    "You didn't know I could do THIS. Now you do."
    
    Examples:
    - 2008: Subprime crash
    - 2010: Flash crash
    - 2015: Swiss franc unpeg
    - 2020: COVID crash
    """
    
    def __init__(self):
        self.black_swan_memory: List[Dict] = []
        self.stress_tests: List[Dict] = []
        
    def learn_from_black_swan(
        self,
        event_description: str,
        event_type: str,
        portfolio_loss: float,
        market_conditions: Dict
    ) -> MarketLesson:
        """
        Learn from a black swan event.
        
        Black swans are expensive but invaluable lessons.
        The market just taught you something you DIDN'T KNOW WAS POSSIBLE.
        """
        # Document the lesson
        self.black_swan_memory.append({
            'date': datetime.now().isoformat(),
            'description': event_description,
            'type': event_type,
            'loss': portfolio_loss,
            'conditions': market_conditions,
            'lesson': 'What we thought was impossible, happened'
        })
        
        # Create stress test based on event
        self.stress_tests.append({
            'name': f"stress_test_{event_type}",
            'based_on': event_description,
            'created': datetime.now().isoformat()
        })
        
        # Determine protective measures
        if event_type == "liquidity_crisis":
            adjustment = "Increase cash buffer 2x, add liquidity monitors"
        elif event_type == "correlation_breakdown":
            adjustment = "Reduce correlation assumptions, increase hedges"
        elif event_type == "regime_shift":
            adjustment = "Improve regime detection sensitivity, add circuit breakers"
        elif event_type == "flash_crash":
            adjustment = "Add flash crash detection, implement trading halts"
        else:
            adjustment = "Add tail risk scenario to risk models"
        
        lesson = MarketLesson(
            lesson_id=f"bs_{datetime.now().timestamp()}",
            feedback_type=FeedbackType.BLACK_SWAN,
            description=f"Black Swan: {event_description}",
            confidence=0.95,
            market_event=event_description,
            agent_action="Normal trading operations",
            market_response=f"Extreme event caused {portfolio_loss*100:.1f}% loss",
            extracted_knowledge="Market can do things we never imagined. Stay humble.",
            proposed_adjustment=adjustment
        )
        
        logger.critical(f"🦢 BLACK SWAN LEARNED: {event_description}")
        logger.critical(f"Loss: {portfolio_loss*100:.1f}%")
        logger.critical(f"Lesson: {lesson.extracted_knowledge}")
        
        return lesson
    
    def get_stress_tests(self) -> List[Dict]:
        """Get all stress tests created from black swan events"""
        return self.stress_tests.copy()
    
    def get_black_swan_history(self) -> List[Dict]:
        """Get history of black swan events"""
        return self.black_swan_memory.copy()


class MarketFeedbackSystem:
    """
    Master system that coordinates all feedback processors.
    
    The market teaches through:
    - Immediate feedback (execution quality)
    - Short-term feedback (trade outcomes)
    - Medium-term feedback (strategy calibration)
    - Long-term feedback (structural changes)
    - Black swan events (extreme lessons)
    """
    
    def __init__(self):
        self.immediate = ImmediateFeedback()
        self.short_term = ShortTermFeedback()
        self.medium_term = MediumTermFeedback()
        self.long_term = LongTermFeedback()
        self.black_swan = BlackSwanLearner()
        
        self.all_lessons: deque = deque(maxlen=50000)
        self.lesson_callbacks: List[Callable] = []
        
        logger.info("MarketFeedbackSystem initialized - Ready to learn from market")
    
    def register_lesson_callback(self, callback: Callable):
        """Register callback for new lessons"""
        self.lesson_callbacks.append(callback)
    
    def _notify_lesson(self, lesson: MarketLesson):
        """Notify callbacks of new lesson"""
        self.all_lessons.append(lesson)
        
        for callback in self.lesson_callbacks:
            try:
                callback(lesson)
            except Exception as e:
                logger.error(f"Lesson callback failed: {e}")
    
    def process_execution(self, **kwargs) -> MarketLesson:
        """Process execution feedback"""
        lesson = self.immediate.process_execution_feedback(**kwargs)
        self._notify_lesson(lesson)
        return lesson
    
    def process_price_reaction(self, **kwargs) -> MarketLesson:
        """Process immediate price reaction"""
        lesson = self.immediate.process_price_reaction(**kwargs)
        self._notify_lesson(lesson)
        return lesson
    
    def process_trade_outcome(self, **kwargs) -> MarketLesson:
        """Process trade outcome"""
        lesson = self.short_term.process_trade_outcome(**kwargs)
        self._notify_lesson(lesson)
        return lesson
    
    def process_volatility(self, **kwargs) -> MarketLesson:
        """Process volatility feedback"""
        lesson = self.short_term.process_volatility_feedback(**kwargs)
        self._notify_lesson(lesson)
        return lesson
    
    def calibrate_strategy(self, **kwargs) -> Optional[MarketLesson]:
        """Calibrate strategy win rate"""
        lesson = self.medium_term.calibrate_win_rate(**kwargs)
        if lesson:
            self._notify_lesson(lesson)
        return lesson
    
    def learn_regime_performance(self, **kwargs) -> Optional[MarketLesson]:
        """Learn regime-strategy performance"""
        lesson = self.medium_term.learn_regime_performance(**kwargs)
        if lesson:
            self._notify_lesson(lesson)
        return lesson
    
    def detect_structural_change(self, **kwargs) -> Optional[MarketLesson]:
        """Detect structural market changes"""
        lesson = self.long_term.detect_structural_change(**kwargs)
        if lesson:
            self._notify_lesson(lesson)
        return lesson
    
    def learn_black_swan(self, **kwargs) -> MarketLesson:
        """Learn from black swan event"""
        lesson = self.black_swan.learn_from_black_swan(**kwargs)
        self._notify_lesson(lesson)
        return lesson
    
    def get_recent_lessons(self, count: int = 100) -> List[Dict]:
        """Get recent lessons"""
        lessons = list(self.all_lessons)[-count:]
        return [l.to_dict() for l in lessons]
    
    def get_lesson_summary(self) -> Dict:
        """Get summary of all lessons learned"""
        lessons = list(self.all_lessons)
        
        by_type = {}
        for lesson in lessons:
            ft = lesson.feedback_type.value
            if ft not in by_type:
                by_type[ft] = 0
            by_type[ft] += 1
        
        return {
            'total_lessons': len(lessons),
            'by_type': by_type,
            'average_slippage': self.immediate.get_average_slippage(),
            'fill_quality': self.immediate.get_fill_quality(),
            'recent_win_rate': self.short_term.get_win_rate(),
            'black_swan_events': len(self.black_swan.black_swan_memory),
            'stress_tests_created': len(self.black_swan.stress_tests)
        }


# Export all classes
__all__ = [
    'FeedbackType',
    'MarketLesson',
    'ImmediateFeedback',
    'ShortTermFeedback',
    'MediumTermFeedback',
    'LongTermFeedback',
    'BlackSwanLearner',
    'MarketFeedbackSystem'
]
